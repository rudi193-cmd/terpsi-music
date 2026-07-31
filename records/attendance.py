"""Attendance — a roll as N lane entries, an absence as a dated ask, and the
one seam where a record could reach a carrier.

Three clauses meet in this module and each is enforced by a different mechanism,
which is why they are listed rather than summarised:

* **W-3 — a shared event is two lane entries with one referent.** A rehearsal
  attended by 150 students is 150 rows against one `Referent`, never one row
  with a roster column. `docs/LANE-MODEL.md` states the cost plainly and says
  the emptiness of `referent` *is* the schema rule, so this module's `Referent`
  has no participant field and `take_roll()` returns a tuple whose length is the
  number of students marked.

* **Rule 15 — every ask gets a dated disposition.** An absence *request* is
  `records/dispositions.py`, not a second queue. What this module adds is the
  binding to the event and the *tri-state* answer: a request source that was
  never consulted reads `UNKNOWN`, never *unexcused*, because an unexcused
  absence is a disciplinary fact and inventing one from a missing lookup is
  rule 13's harm in the register that gets a student benched.

* **Refusal 7 — never put a record on SMS.** §4.1: *"SMS carries signals —
  times, changes, acknowledgments. Never health, balances, grades, discipline,
  or a location tied to a named student."*

## The signal/record split, and why it is a shape rather than a filter

The seam is `records/sending.py`'s `Payload`, whose only content field is a
`body: str`. A filter over that string — *reject bodies containing "absent"* —
is a guard that a paraphrase walks through, and it fails in the quiet direction.

So the split is made where the strings come from instead:

| | built from | rung, per `migrations/001_lanes.sql` |
|---|---|---|
| **Signal** | `referent.label`, `referent.occurs_at` | `PUBLIC` / `L1` |
| **Record** | `lane_entry.kind`, `lane_entry.payload` | `PII_MINOR` / `L3`, `HEALTH` / `L4` |

`Signal` has **no free-text field**. Its body is rendered from a closed
vocabulary of three kinds over the referent's two published columns, so there is
nowhere in a signal to put a presence, a pattern, a reason or a name — not
because those are stripped, but because the constructor takes a `Referent` and
an instant and nothing else. `notify()` accepts a `Signal` and refuses anything
else by type. `AttendanceEntry` appears nowhere in the send path, and
`tests/test_attendance.py` asserts that statically over the source, the way
`test_sending.py` asserts G4 over `deliver()`'s signature.

**Its limit, stated rather than discovered.** `sending.Payload` is public and a
caller outside this module can still format an entry into a string and hand it
over. What is closed here is the path a reasonable caller would take and every
path this module provides; what is not closed is Python. The store-side answer
is the same one §7 gives for the read predicate — one send method, compiled —
and there is no store.

## What is deliberately absent

**No reason field on the roll mark.** *"She's sick tonight"* is health-adjacent
(`L4`) and *"suspended"* is discipline (`L4`); a mark is `L3`. Putting either on
the mark composes the row up a rung by `max` and drags it toward every surface
that renders attendance. The reason lives as its own lane entry and the request
carries a **pointer** to it, never the text.

**No excused/unexcused on the mark either.** What was observed and what was
decided about it are two facts with two dates and two authors. Collapsing them
means a mark changes when an office answers, and the record of what the roll
actually showed is gone.

## Retention — recorded, not built

§10's row is a *season-boundary purge job*, and it is not built here. What the
types carry so it can be written without a migration: a `season` on `Referent`,
`AttendanceEntry` and `AbsenceRequest`, and dates on everything — `created_at`
(learned), `at`/`valid_at` (true in the world), `invalid_at` (ended, never
deleted). A purge is then a predicate over `season` and `invalid_at` rather than
a join across three tables to work out which season a row belonged to.

Stdlib only. No network, no store, no model.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Sequence, Tuple

from .classify import aggregate
from .conflict import one_lane, refuse_to_rank
from .dispositions import Disposition, Request, ask, state_at
from .rungs import Rung
from .sending import Payload, deliver


class NotSendable(Exception):
    """Raised where a record was offered to the send path (refusal 7).

    Its own exception rather than `TypeError`, because the caller needs the
    clause and not a type name: *SMS carries signals, never records.*
    """


class NoRoster(Exception):
    """A participant list was asked of a referent. There is not one (W-3)."""


# --- what was observed -----------------------------------------------------


class Presence(Enum):
    """What the roll showed. Observation only — no judgement about it.

    `EXCUSED` is deliberately not a member. Whether an absence was excused is a
    *disposition*, dated and answered by a named office, and it is derived at an
    instant by `excusal()` rather than written onto the observation.
    """

    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    LEFT_EARLY = "left_early"


@dataclass(frozen=True)
class Referent:
    """The shared object of a shared event. **Its emptiness is the rule.**

    `docs/LANE-MODEL.md`: *"`referent` is what remains once the roster is
    removed: the shared object with no participants on it. Anything later added
    to `referent` that names or counts participants reintroduces exactly the
    partition W-1 forbids."*

    `label` and `occurs_at` are `PUBLIC`/`L1` in the classification registry —
    *"Regional Championship · Oct 12 · Memorial Stadium"* is on a poster — and
    that is precisely why the signal path may read them and only them.
    """

    referent_id: str
    kind: str          # Rehearsal | Sectional | Event | ...
    label: str
    occurs_at: datetime
    season: str        # retention's axis; see the module docstring
    created_at: datetime = _field(kw_only=True)
    valid_at: Optional[datetime] = _field(default=None, kw_only=True)
    invalid_at: Optional[datetime] = _field(default=None, kw_only=True)

    def __post_init__(self):
        if not (self.label or "").strip():
            raise ValueError("a referent with no label cannot be published or named")
        if not (self.season or "").strip():
            raise ValueError(
                "a referent with no season cannot be retained or purged (§10)"
            )


@dataclass(frozen=True)
class AttendanceEntry:
    """One student's presence at one referent, in that student's lane.

    W-1's *from the first write*: `lane_id` is required and there is no
    constructor that takes a list of students. A shared event is N of these.

    **No `reason`, no `note`, no `excused`.** See the module docstring; the test
    asserts the absence rather than trusting this paragraph.
    """

    lane_id: str
    subject_id: str
    referent_id: str
    presence: Presence
    at: datetime                          # when it was observed
    author_id: str                        # who marked it
    season: str
    created_at: datetime = _field(kw_only=True)
    invalid_at: Optional[datetime] = _field(default=None, kw_only=True)
    #: Who corrected this mark, when one was corrected. Set by `correct()`
    #: alongside `invalid_at`; a correction supersedes, it never overwrites
    #: (refusal 3). The replacement is the entry created at the same instant —
    #: an ending nobody can answer for is the half of refusal 3 a bare date
    #: does not carry (`records/orders.py`'s `ended_by`, same argument).
    corrected_by: Optional[str] = _field(default=None, kw_only=True)

    def live_at(self, when: datetime) -> bool:
        return self.invalid_at is None or when < self.invalid_at


def take_roll(referent: Referent, marks: Sequence[Tuple[str, str, Presence]], *,
              author_id: str, at: datetime,
              created_at: Optional[datetime] = None) -> Tuple[AttendanceEntry, ...]:
    """One referent in, **one entry per student** out.

    `marks` is `(lane_id, subject_id, presence)`. The return is a tuple as long
    as `marks`, and there is no other shape available: the normalized instinct
    — one `Rehearsal` row with a roster column, joined — is what W-3 forbids,
    and the reason is partitioning rather than storage. A roster column is a
    shared partition wearing a foreign key, and every query over it returns
    other wards' rows by default.

    A student marked twice on one roll is refused rather than deduplicated. Two
    marks disagreeing about one student is a fact about the roll, and picking
    one silently is how the loser stops existing.
    """
    seen = set()
    for lane_id, subject_id, presence in marks:
        if not (lane_id or "").strip():
            raise ValueError(
                f"{subject_id!r} was marked with no lane; W-1 says a lane from the "
                "first write, so there is no such thing as a mark outside one"
            )
        if not isinstance(presence, Presence):
            raise TypeError(f"{presence!r} is not a Presence")
        if subject_id in seen:
            raise ValueError(
                f"{subject_id!r} appears twice on one roll; two marks disagreeing "
                "about one student is a fact, and choosing one here would discard it"
            )
        seen.add(subject_id)
    return tuple(
        AttendanceEntry(lane_id, subject_id, referent.referent_id, presence, at,
                        author_id, referent.season,
                        created_at=created_at if created_at is not None else at)
        for lane_id, subject_id, presence in marks
    )


def correct(entry: AttendanceEntry, presence: Presence, *, by: str, at: datetime,
            created_at: Optional[datetime] = None
            ) -> Tuple[AttendanceEntry, AttendanceEntry]:
    """Fix a mark by **dating the old one closed and writing a new one**.

    Refusal 3 in attendance's clothes, and rule 16's other half: a roll that can
    be silently rewritten is a roll that cannot answer *"what did the sheet say
    on the night, and who changed it."* Returns `(superseded, replacement)`;
    nothing is mutated and nothing is removed.
    """
    if entry.invalid_at is not None:
        raise ValueError("this mark was already superseded; correct the live one")
    later = replace(entry, presence=presence, author_id=by,
                    created_at=created_at if created_at is not None else at,
                    invalid_at=None, corrected_by=None)
    closed = replace(entry, invalid_at=at, corrected_by=by)
    return closed, later


# --- the ask, and the answer that is never invented ------------------------


@dataclass(frozen=True)
class AbsenceRequest:
    """An absence request, bound to the event it is about.

    The clock lives on `request` (`records/dispositions.py`), which refuses to
    construct without a timebound declared at issuance. What is added here is
    `referent_id` — an absence is from *something* — and `reason_entry_id`,
    which is a **pointer to a lane entry and never the reason itself**.
    """

    request: Request
    referent_id: str
    season: str
    reason_entry_id: Optional[str] = None


def request_absence(subject_id: str, referent: Referent, *, asked_by: str,
                    asked_at: datetime, within: timedelta, office: str,
                    escalates_to: str,
                    reason_entry_id: Optional[str] = None) -> AbsenceRequest:
    """Ask to be absent. `within` is required and has no default here either.

    A wrapper that supplied a default timebound would defeat `dispositions.ask`
    from the outside — I-6's *"no system-wide default is proposed, because a
    default would let issuers stop declaring"* survives only if every caller in
    front of it also declines to have one.
    """
    return AbsenceRequest(
        ask(subject_id, "absence", asked_by=asked_by, asked_at=asked_at,
            within=within, office=office, escalates_to=escalates_to),
        referent.referent_id, referent.season, reason_entry_id)


class Excusal(Enum):
    EXCUSED = "excused"
    NOT_EXCUSED = "not_excused"
    UNKNOWN = "unknown"     # nobody was asked; NOT unexcused (rule 13)
    AWAITED = "awaited"     # asked, within its timebound, unanswered


def excusal(entry: AttendanceEntry, requests: Optional[Sequence[AbsenceRequest]],
            at: datetime) -> Excusal:
    """Whether this absence was excused, **at an instant**.

    `requests=None` means *no request source was consulted* and returns
    `UNKNOWN`; `()` means *consulted, and there is no request*, which is
    `NOT_EXCUSED`. The two point in opposite directions and a single sentinel
    would merge them — `serving.serve()`'s `grants` argument, in the register
    where the wrong answer gets a student benched for a bereavement nobody
    logged.

    An open request past its declared timebound reads as `EXCUSED`, because
    `dispositions.state_at` escalates it: silence is not an answer, and it is
    not a refusal either.

    A `PRESENT` mark answers `EXCUSED` rather than raising, so a caller counting
    unexcused absences over a mixed set of marks does not have to filter first —
    the failure mode of requiring the filter is a surface that counts every
    present student as unexcused.
    """
    if entry.presence is Presence.PRESENT:
        return Excusal.EXCUSED
    if requests is None:
        return Excusal.UNKNOWN
    mine = [r for r in requests
            if r.request.subject_id == entry.subject_id
            and r.referent_id == entry.referent_id]
    if not mine:
        return Excusal.NOT_EXCUSED
    for r in mine:
        now = state_at(r.request, at)
        if now.disposition in (Disposition.GRANTED, Disposition.ESCALATED):
            return Excusal.EXCUSED
    if any(state_at(r.request, at).disposition is Disposition.OPEN for r in mine):
        return Excusal.AWAITED
    return Excusal.NOT_EXCUSED


# --- own-lane statistics ---------------------------------------------------


@dataclass(frozen=True)
class OwnAttendance:
    """One student's own attendance. Every field reads that lane alone."""

    lane_id: str
    events: int
    present: int
    absent: int
    late: int

    @property
    def rate(self) -> float:
        return self.present / self.events if self.events else 0.0


def own(entries: Sequence[AttendanceEntry], *,
        at: Optional[datetime] = None) -> OwnAttendance:
    """Aggregate one student's marks. One lane in, one summary out.

    Superseded marks are excluded at `at` rather than deleted, so a corrected
    roll counts once and the original is still answerable for.
    """
    lane = one_lane(entries, "an attendance statistic spanning lanes")
    live = [e for e in entries if at is None or e.live_at(at)]
    return OwnAttendance(
        lane, len(live),
        sum(1 for e in live if e.presence is Presence.PRESENT),
        sum(1 for e in live if e.presence is Presence.ABSENT),
        sum(1 for e in live if e.presence is Presence.LATE))


@dataclass(frozen=True)
class Headcount:
    """A count at a referent, carrying the rung it was classified at.

    §7's worked `L3` example gives the judge *"a count, a section, a chair
    number with no name on it"* — so the derived form is real and wanted. What
    it is not is automatically `L2`: a count over a section of three is not
    anonymous, which is `classify.aggregate`'s whole subject.
    """

    referent_id: str
    present: int
    marked: int
    rung: Optional[Rung]
    reason: str

    @property
    def servable(self) -> bool:
        """`L2` only. Anything else inherited a rung and is not a public count."""
        return self.rung is Rung.L2


def headcount(entries: Sequence[AttendanceEntry], referent: Referent, *,
              floor: int) -> Headcount:
    """How many were present, with the re-identification check applied.

    **This is the one function here that reads across lanes on purpose**, and it
    is allowed to because it produces no per-student value and no ordering: N
    rows in, two integers out, no subject list. The protection it needs is not
    the lane seal but the suppression floor, which is `floor` and which the
    caller declares — there is no default (see `classify.aggregate`).
    """
    marks = [e for e in entries if e.referent_id == referent.referent_id]
    cohort = len({e.subject_id for e in marks})
    # `lane_entry.kind` is PII_MINOR/L3 in the registry; a count of marks is
    # derived from it, so L3 is what it inherits until the check passes.
    c = aggregate("headcount", over=(Rung.L3,), cohort=cohort, floor=floor)
    return Headcount(referent.referent_id,
                     sum(1 for e in marks if e.presence is Presence.PRESENT),
                     len(marks), c.rung, c.reason)


def patterns(entries: Sequence[AttendanceEntry]) -> None:
    """The early-warning signal of §19 — refused in the cross-lane form.

    The capability map proposes *"attendance patterns as an early-warning
    signal"*, and the useful version of it reads one lane: this student has
    missed three Tuesdays. The version that arrives by accident reads every lane
    and sorts, which is a priority between students (refusal 6) with a
    pastoral name on it. `own()` is the sanctioned shape; this exists so the
    other one is findable by name rather than reimplemented locally.
    """
    refuse_to_rank("an attendance pattern across students",
                   [e.subject_id for e in entries])


def roster(referent: Referent) -> None:
    """There is none, and the absence is the schema rule (W-3).

    Present for `practice.standings`'s reason: a missing name reads as *not
    built yet* and invites a local reimplementation, while an `ImportError`
    invites the same. This raises with the clause attached.
    """
    raise NoRoster(
        f"W-3: {referent.kind} {referent.label!r} has no roster. A shared event is "
        "N lane entries with one referent; a participant list on the referent is "
        "the shared partition W-1 forbids, wearing a foreign key."
    )


# --- the send path: signals only -------------------------------------------


class SignalKind(Enum):
    """The three §4.1 classes SMS may carry, and no fourth.

    §4.1's table: notification ~80%, acknowledgment ~15%, transactional ~5%.
    The first two are these three kinds; the third *"stays on the interactive
    surface"* and has no member here, because a member is how it would get sent.
    """

    TIME = "time"                      # "call time is 5:15"
    CHANGE = "change"                  # "moved from 3:30 to 5:15"
    ACKNOWLEDGMENT = "acknowledgment"  # "got it"


def _clock(t: datetime) -> str:
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}"


def _day(t: datetime) -> str:
    return f"{t.strftime('%a')} {t.day} {t.strftime('%b')}"


@dataclass(frozen=True)
class Signal:
    """What may go on a carrier. **There is no field to put a record in.**

    Every field here is either the kind, or a column the classification registry
    marks `PUBLIC`/`L1`: `referent.label` and `referent.occurs_at`. `body()`
    renders from those and from nothing else, so the body is *derived* rather
    than supplied — a caller has no parameter through which to pass a presence,
    a pattern, a balance or a reason.

    `was` carries the previous time for a `CHANGE`, which is a time and not a
    record.
    """

    kind: SignalKind
    referent_id: str
    label: str
    occurs_at: datetime
    was: Optional[datetime] = None

    def body(self) -> str:
        """The message text, in plain language, naming no student.

        Guardian-facing (CLAUDE.md, *Working here*): no fleet nouns, no rung
        codes, no internal identifiers, no abbreviations only staff would know.
        The student is not named because the audience is *"whoever holds the
        phone"* (§4.1) — including the student, on a lock screen, with no
        authentication.

        Formatted by hand rather than with `%-I`/`%-d`, which are a glibc
        extension: a `ValueError` from a format code is a crash on the one path
        that carries a weather hold.
        """
        when = f"{_day(self.occurs_at)}, {_clock(self.occurs_at)}"
        if self.kind is SignalKind.TIME:
            return f"{self.label}: {when}."
        if self.kind is SignalKind.CHANGE:
            if self.was is None:
                return f"{self.label}: changed. New time {when}."
            return f"{self.label}: moved from {_clock(self.was)} to {when}."
        return f"Thanks — we have your reply about {self.label}."


def signal(referent: Referent, kind: SignalKind, *,
           was: Optional[datetime] = None) -> Signal:
    """Build a signal from a referent. **A record cannot be passed here.**

    The type check is not defensive programming, it is the seam: an
    `AttendanceEntry` has a `referent_id` and would duck-type its way through
    an attribute-based version of this function, carrying a presence into the
    only object this module lets near a carrier.
    """
    if not isinstance(referent, Referent):
        raise NotSendable(
            f"{type(referent).__name__} is not a referent. SMS carries signals — a "
            "time, a change, an acknowledgment — and never a record (§4.1, "
            "refusal 7)."
        )
    if not isinstance(kind, SignalKind):
        raise NotSendable(f"{kind!r} is not one of the three signal kinds")
    return Signal(kind, referent.referent_id, referent.label, referent.occurs_at, was)


def notify(sig: Signal, subject_id: str, *, at: datetime, edges, restrictions,
           transport: Callable[[str, str], None]):
    """Send a signal about `subject_id`, to whoever `sending.py` derives.

    No recipient parameter, because `deliver()` has none (G4) and adding one
    here would defeat it one call earlier. The payload's body is `sig.body()`
    and there is no override: this function has no `body`, `text` or `message`
    parameter and must never grow one, which `tests/test_attendance.py` asserts
    over the signature.
    """
    if not isinstance(sig, Signal):
        raise NotSendable(
            f"{type(sig).__name__} is not a signal. Only a signal reaches the "
            "carrier; a record — a presence, a pattern, a reason — has no route "
            "here (refusal 7)."
        )
    return deliver(Payload(subject_id, at, sig.body()), edges, restrictions, transport)


def send_attendance(entry: AttendanceEntry, *_args, **_kwargs) -> None:
    """The function someone will look for. It refuses, by name.

    *"Ben was marked absent from tonight's rehearsal"* is a record: it is a
    grade-adjacent fact about a named minor, retained by the SMSC, rendered on a
    lock screen, and synced into two cloud backups. §4.1 allows the signal that
    rehearsal *happened* and never the mark.
    """
    raise NotSendable(
        f"a {entry.presence.value} mark for {entry.subject_id!r} is a record, not a "
        "signal. §4.1: SMS carries times, changes and acknowledgments. Send a "
        "signal about the event; the mark stays on the interactive surface."
    )
