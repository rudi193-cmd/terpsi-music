"""§10's season-boundary purge — the *when* of erasure, not the *how*.

§9 item 8's note names this and does not build it: *"the purge itself"* does not
exist, only the fields it would read — a `season` on every record and the three
dates (`created_at` learned, `valid_at`/`at` true-in-the-world, `invalid_at`
ended-and-never-deleted). This module is that predicate, and it is deliberately
**only** the predicate: which records a season boundary has carried past their
retention, expressed as a dated decision. The erasure it drives is
`records/atrest.py`'s `destroy()` — per-subject, crypto, and already built (§9
foundation 3). Nothing here encrypts, and nothing here deletes.

**A purge here is not a delete, and that is the whole point.** Refusal 3 is
*never revoke by deleting*; `atrest.py` says the same in its own words — *"refusal
3 is not violated by destroying key material… the `Erasure` row survives it: who
destroyed it, when, why, and which key ids."* So a purge is two durable things,
never a `DELETE`:

* the record's sealed payload becomes **unreadable** (its lane key's wrappings
  are dropped by `atrest.destroy`), and
* a `Disposition` — dated, attributed, reasoned — **takes its place and stays**.

The row a purge touches keeps its skeleton: its id, its season, its dates. What
leaves is only what a key opened. A reader afterwards learns *this was purged,
by whom, when, and why*, which is the difference between an erasure and a loss —
the §5 test `atrest.py` is built around.

**Four refusals are structural, and each has a test that attempts the act.**

1. **A record inside its retention is not due, and forcing it raises** — you
   cannot purge early. `due()` returns only records a boundary has carried past
   the horizon *and* that are already closed (`invalid_at` set); a live record —
   a fee still owed, an enrolment still current — is never erased.
2. **The record of a purge is not itself purgeable** (rule 16 / I-7: *a
   student's entries are as durable as entries about them; no role's authority
   extends to deleting the record of its own exercise*). A `Disposition` handed
   back to `due()` or `dispose()` raises; the tombstone a purge leaves cannot be
   erased by the next purge.
3. **Absence is `unknown`, never a licence** (rule 13). A record with no season
   raises rather than being swept; a record kind with no policy raises rather
   than defaulting to *keep forever* or *purge now*. A missing calendar or a
   missing policy fails closed — nothing is due when the rule cannot be read.
4. **A record-scoped decision never drives a student-scoped erasure** (rule 8:
   one lane is one student). `purge()` will not erase a lane it has not been
   shown to hold *nothing but* due records: the caller hands it the lane's full
   record set, every entry must assess `DUE`, and a lane the caller cannot
   enumerate is `UNKNOWN` — refused, never assumed empty (rule 13).

**Why refusal 4 exists, stated plainly: the two layers are not scoped alike.**
`assess()`/`due()`/`dispose()` decide about *one record* — a season, a kind, a
horizon. `atrest.destroy` acts on *one lane*, dropping every wrapping under it
in every generation; it filters on `lane_id` alone, so key rotation does not
narrow it. `purge()` used to join the two directly, which made a `Disposition`
scoped to one aged-out attendance record destroy the key opening that student's
every sealed payload, in every season, of every kind — including ones `assess()`
had just called `LIVE`. **Refusal 3 was never violated by this**: nothing was
deleted, the rows stayed, the `Erasure` outlived what it erased. That is exactly
why nothing caught it — the isolation test compared one lane against another,
and the forbidden act was *within* a lane.

**This is the conservative half of the fix and the deeper half is open.** The
repair here gives `purge()` the fact it was missing and refuses without it. The
repair it does not attempt is sealing per `(lane, season)`, so a season's
erasure has a key of its own and `destroy` takes a season — a change to the key
hierarchy, the migrations and the sealing plan, carried as §18 item 19 rather
than taken quietly here.

**No retention period is invented here.** Like §9 item 10's refusal to ship a
default `k`, this module carries the *mechanism* and takes the *durations* from
its caller: a `Calendar` says when a season ended, a `Policy` says how long each
kind is kept past that. What the law requires is a decision the maintainer
makes; encoding a guess as a constant would be the fiction rule 17 forbids.

The named middle (rule 12): `records/atrest.py` owns erasure and this owns the
schedule; `purge()` is the only place they meet, and it is where the difference
in scope between them is reconciled rather than assumed away.
`test_retention.py` asserts both halves — that `purge()` calls `destroy()` for
exactly the lanes `due()` named and no others, and that a lane holding one
not-due record is refused whole rather than erased around.

Stdlib only. No network, no writes, no deletes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable


class NoSeason(Exception):
    """A record with no season cannot be placed on the retention axis (rule 13).

    Mirrors `attendance.Referent`'s own `__post_init__` — a season is the axis a
    purge is a predicate over, and a record without one cannot be classified as
    retained or due. Refused, never swept."""


class UnknownKind(Exception):
    """A record kind with no policy entry (rule 13). The safe answer is neither
    *keep forever* nor *purge now* — it is *unknown*, and unknown fails closed:
    the record is not due, and asking to dispose it raises rather than guessing a
    retention the maintainer never set."""


class NotDue(Exception):
    """An attempt to purge a record a boundary has not carried past its
    retention — or one still live. There is no early purge and no purge of a
    record still true in the world; `dispose()` refuses both."""


class Indelible(Exception):
    """The record of a purge cannot itself be purged (rule 16 / I-7). A role's
    authority to erase does not reach the dated record of its having erased."""


class LaneNotDue(Exception):
    """A lane still holding a record that is not `DUE` is not erased, whatever
    the disposition in hand says about one record inside it (rule 8: a lane is
    one student).

    `atrest.destroy` is lane-scoped and a `Disposition` is record-scoped, so the
    record a boundary correctly carried past its horizon and the one correctly
    still `LIVE` are sealed under the same key. This is the refusal that stops
    the narrower decision from authorising the wider act. It is not a permission
    somebody may hold: `purge()` has no parameter that overrides it, because
    removing the *ability* survives a careless edit and removing the
    *permission* does not (`docs/CROSSINGS.md`, crossing one)."""


class UnknownLane(Exception):
    """A purge was asked for a lane whose records the caller did not enumerate,
    or enumerated as holding nothing (rule 13).

    An unenumerable lane is *unknown*, not empty, and unknown fails closed: a
    caller who cannot say what a lane holds must not be answered as though it
    holds nothing, when the act being authorised covers everything in it. The
    empty enumeration is refused for the same reason rather than as a
    formality — a missing key and an empty sequence are the two cheapest ways
    past `LaneNotDue`, and a lane a `Disposition` was just written against holds
    at least the record that disposition names."""


@runtime_checkable
class Retainable(Protocol):
    """What a purge needs from a record and nothing more. Every dated record
    type in `records/` (`attendance.Referent`/`AttendanceEntry`/`AbsenceRequest`,
    `fees.FeeGroup`/`Charge`/`Payment`) already satisfies it, so the purge reads
    them without importing any of them — the roster column W-1 forbids has no way
    in here, and neither does any one module's shape."""

    season: str
    created_at: datetime
    invalid_at: Optional[datetime]


class Calendar:
    """When each season ended. A `season` is a label (`"2025-fall"`), not a date;
    the caller owns the mapping from label to the moment it closed, because a
    program's calendar is a fact about that program, not about this code.

    A label with no end date is `unknown` (rule 13): a season that has not been
    told when it ended cannot have carried anything past a horizon, so its
    records are never due — silence is not a purge licence."""

    def __init__(self, ended: Mapping[str, datetime]) -> None:
        for label, when in ended.items():
            if when.tzinfo is None:
                raise ValueError(
                    f"season {label!r} ended at a naive datetime; a boundary "
                    "without a timezone is a wish, not a deadline")
        self._ended: Dict[str, datetime] = dict(ended)

    def ended_at(self, season: str) -> Optional[datetime]:
        """When `season` closed, or `None` if this calendar cannot say — which
        makes every record in that season *not due*, never *due by default*."""
        return self._ended.get(season)


@dataclass(frozen=True)
class Policy:
    """How long each record kind is kept past the end of its season. The
    durations are the caller's; this type only refuses to guess one it was not
    given (`UnknownKind`). A `kind` is a plain string the caller assigns
    (`"attendance"`, `"charge"`, `"absence_request"`) — this module does not
    reach into a record's class, so no record type is privileged here."""

    horizons: Mapping[str, timedelta]

    def horizon(self, kind: str) -> timedelta:
        try:
            return self.horizons[kind]
        except KeyError:
            raise UnknownKind(
                f"no retention horizon for kind {kind!r} — a purge will not "
                "invent one; add it to the policy or the record stays") from None


class Standing(Enum):
    """Where a record sits against its retention, always named, never a bare
    boolean — a caller that gets `True` forgets which direction it meant."""

    LIVE = "live"          # `invalid_at` is None: still true in the world; kept
    RETAINED = "retained"  # closed, but inside the horizon: kept, on the clock
    DUE = "due"            # closed and past the horizon: a boundary has carried it
    UNKNOWN = "unknown"    # the calendar cannot place its season (rule 13)


@dataclass(frozen=True)
class Assessment:
    """One record judged against the policy — the standing plus the facts the
    judgement rests on, so the reason a record is or is not due is legible rather
    than only its verdict."""

    kind: str
    season: str
    standing: Standing
    horizon: Optional[timedelta]
    retain_until: Optional[datetime]


def _season_of(record: Retainable) -> str:
    season = (getattr(record, "season", "") or "").strip()
    if not season:
        raise NoSeason(
            "a record with no season cannot be retained or purged (§10); it is "
            "refused here rather than swept into or out of a boundary")
    return season


def _require_aware(dt: datetime, what: str) -> datetime:
    """A naive datetime is refused the same way `Calendar` and `Disposition`
    refuse one — a boundary comparison against a datetime with no timezone would
    silently mean whatever the process's clock happened to be, or raise a bare
    `TypeError` deep in a comparison. Rule 13's spirit: an ambiguous input is an
    error stated plainly, not a crash and not a guess."""
    if dt.tzinfo is None:
        raise ValueError(
            f"{what} is a naive datetime; a retention boundary needs a timezone "
            "so 'past the horizon' means one thing, not the local clock's guess")
    return dt


def assess(record: Retainable, kind: str, calendar: Calendar, policy: Policy,
           now: datetime) -> Assessment:
    """One record's standing. Raises `NoSeason`/`UnknownKind` rather than
    guessing; returns `UNKNOWN` when the calendar cannot place the season; and
    refuses a naive `now` or a naive `invalid_at` (`ValueError`) rather than
    comparing across timezone-awareness."""
    if isinstance(record, Disposition):
        raise Indelible(
            "a purge disposition is the record of an erasure and is not itself "
            "retainable — rule 16: no role deletes the record of its own act")
    season = _season_of(record)
    horizon = policy.horizon(kind)   # raises UnknownKind before anything else
    _require_aware(now, "now")
    ended = calendar.ended_at(season)
    if ended is None:
        return Assessment(kind, season, Standing.UNKNOWN, horizon, None)
    if record.invalid_at is None:
        return Assessment(kind, season, Standing.LIVE, horizon, None)
    _require_aware(record.invalid_at, "invalid_at")
    retain_until = ended + horizon
    standing = Standing.DUE if now >= retain_until else Standing.RETAINED
    return Assessment(kind, season, standing, horizon, retain_until)


def due(records: Sequence[Tuple[Retainable, str]], calendar: Calendar,
        policy: Policy, now: datetime) -> Tuple[Tuple[Retainable, str], ...]:
    """The `(record, kind)` pairs a season boundary has carried past retention.

    Only `DUE` — closed *and* past the horizon — is returned. `LIVE`, `RETAINED`
    and `UNKNOWN` are kept, which is the fail-closed direction: a record is
    erased only when the rule positively says its time is up, never because the
    rule could not be read. Raises on a no-season record, an unknown kind, or a
    disposition handed back in — none is silently skipped."""
    out = []
    for record, kind in records:
        if assess(record, kind, calendar, policy, now).standing is Standing.DUE:
            out.append((record, kind))
    return tuple(out)


@dataclass(frozen=True)
class Disposition:
    """The durable record of one purge — the tombstone that outlives what it
    erased (rule 16, and `atrest.py`'s `Erasure` in the key layer). It carries
    *why this will not open* — the lane, the key ids destroyed, the season, the
    date, the person, the reason — and never the content, which is exactly what
    was made unreadable. It is not `Retainable`: `assess()`/`dispose()` refuse
    it, so no later purge can erase the evidence of an earlier one."""

    lane_id: str
    season: str
    kind: str
    at: datetime
    by: str
    reason: str
    key_ids: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not (self.by or "").strip():
            raise ValueError("an unattributed purge is not a disposition (rule 15)")
        if not (self.reason or "").strip():
            raise ValueError("a purge with no reason is not a disposition (rule 15)")
        if self.at.tzinfo is None:
            raise ValueError("a purge disposition needs a timezone-aware date")


def dispose(record: Retainable, kind: str, *, lane_id: str, calendar: Calendar,
            policy: Policy, now: datetime, by: str, reason: str,
            key_ids: Sequence[str] = ()) -> Disposition:
    """Decide to purge one due record, and record the decision (rule 15: every
    ask gets a dated disposition). Refuses a record that is not `DUE` —
    `NotDue` — so there is no early purge and no purge of a live record; refuses a
    disposition (`Indelible`) and a no-season/unknown-kind record for the same
    reasons `assess()` does. Does not erase anything itself — `purge()` drives
    `atrest.destroy` — it only makes the dated, attributed tombstone."""
    standing = assess(record, kind, calendar, policy, now).standing
    if standing is not Standing.DUE:
        raise NotDue(
            f"record in season {_season_of(record)!r} is {standing.value}, not "
            "due; a purge waits for a boundary to carry it past retention and "
            "never erases a live or still-retained record")
    return Disposition(lane_id=lane_id, season=_season_of(record), kind=kind,
                       at=now, by=by, reason=reason, key_ids=tuple(key_ids))


def _holdings(lane_id: str,
              lane_records: Mapping[str, Sequence[Tuple[Retainable, str]]],
              ) -> Tuple[Tuple[Retainable, str], ...]:
    """What the caller says the lane holds — never `None`, never `()`.

    Two refusals, not one, because the two absences are different mistakes and
    both fail closed to the same place (`UnknownLane`, rule 13): a lane absent
    from the mapping is one the caller did not enumerate, and a lane present
    with nothing in it is one the caller enumerated wrongly, since a lane a
    `Disposition` was just written against holds at least that record."""
    held = lane_records.get(lane_id)
    if held is None:
        raise UnknownLane(
            f"lane {lane_id!r} was not enumerated for this purge; a lane whose "
            "records cannot be listed is unknown, not empty, and the erasure "
            "being authorised covers every record in it (rule 13)")
    held = tuple(held)
    if not held:
        raise UnknownLane(
            f"lane {lane_id!r} was enumerated as holding nothing, and a lane a "
            "disposition names holds at least that record; an empty listing is "
            "a caller that cannot see the lane, not a lane with nothing in it")
    return held


def _refuse_unless_wholly_due(dispositions: Sequence[Disposition], *,
                              lane_records: Mapping[str, Sequence[Tuple[Retainable, str]]],
                              calendar: Calendar, policy: Policy,
                              now: datetime) -> None:
    """Every lane a disposition names must hold nothing but due records.

    Raises `UnknownLane` for a lane the caller could not enumerate and
    `LaneNotDue` for one still holding a record that is `LIVE`, `RETAINED` or
    `UNKNOWN`. Anything `assess()` refuses outright — a seasonless record, a
    kind with no horizon, an earlier purge's `Disposition` handed back in —
    raises from there, in the same direction: a lane that cannot be assessed
    whole is not erased. It answers no question and returns nothing; the only
    thing it does is refuse."""
    for lane_id in dict.fromkeys(d.lane_id for d in dispositions):
        for record, kind in _holdings(lane_id, lane_records):
            assessed = assess(record, kind, calendar, policy, now)
            if assessed.standing is not Standing.DUE:
                raise LaneNotDue(
                    f"lane {lane_id!r} holds a {kind!r} record from season "
                    f"{assessed.season!r} that is {assessed.standing.value}; "
                    "destroying the lane's key would take that record too, and "
                    "one record's disposition does not reach a whole student "
                    "(rule 8). Purge the lane when all of it is due, or seal "
                    "the season apart (§18 item 19)")


def purge(keyring, dispositions: Sequence[Disposition], *,
          lane_records: Mapping[str, Sequence[Tuple[Retainable, str]]],
          calendar: Calendar, policy: Policy, now: datetime):
    """Drive `atrest.destroy` for each disposition and return the new keyring
    with the same dispositions (the tombstones that survive).

    This is the named middle (rule 12): the only place the schedule (`this`) and
    the erasure (`atrest`) meet. It performs **no delete** — `atrest.destroy`
    drops key wrappings and leaves an `Erasure` — and it re-drives nothing it was
    not handed a `Disposition` for, so `due()` remains the sole authority on
    *what* is purged. Import is local so this module carries no hard dependency
    on the one that needs `cryptography`.

    **`lane_records` is required, keyword-only, and has no default, and that is
    the fix rather than a signature preference.** The erasure this drives is
    lane-scoped while every decision above it is record-scoped, so a `purge()`
    that took only dispositions could not tell whether the lane it was about to
    make unreadable held anything else — and it always did, because a lane is a
    student and a student has more than one record. The missing fact is now an
    argument the caller cannot omit: a caller that cannot enumerate the lane
    gets `UnknownLane`, and one whose lane holds a record that is not `DUE` gets
    `LaneNotDue`. Neither is overridable here (`docs/CROSSINGS.md`, crossing
    one). `lane_records` maps a lane id to the `(record, kind)` pairs that lane
    holds — the same shape `due()` takes, per lane.

    The refusals run over every disposition before any key is destroyed. The
    keyring is immutable, so a raise partway could not have handed back a
    half-purged one either; the separate pass is so that the order of the
    dispositions is not part of what the refusal means."""
    from . import atrest
    for d in dispositions:
        if not isinstance(d, Disposition):
            raise TypeError(
                "purge() drives only dated dispositions; a bare lane id would "
                "erase without a record of why (rule 15)")
    _refuse_unless_wholly_due(dispositions, lane_records=lane_records,
                              calendar=calendar, policy=policy, now=now)
    live = keyring
    for d in dispositions:
        live = atrest.destroy(live, lane_id=d.lane_id, at=d.at, by=d.by,
                              reason=d.reason)
    return live
