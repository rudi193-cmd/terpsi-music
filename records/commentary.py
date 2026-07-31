"""§9 item 9 — Adjudication: the commentary primitive, the guest who writes it,
and the seam a transcript arrives through.

§8.1's *commentary is the primitive* is marked **Open** in §14's component map.
This is that item, built against the pieces that already exist rather than
beside them: `records/marking.py` owns the anchor, `records/sealing.py` owns the
cascade, `records/disclosure.py` owns the chain the exit reconciliation filters,
`records/inference.py` owns refusal 1, and `records/dispatch.py` is the gate
anything leaves through. Nothing here re-derives any of them.

**Four things this module is, and one it deliberately is not.**

1. **A remark is a `Mark` with words on it.** §8.1 asks for an anchor that is a
   score position *and not wall-clock alone*; §18 item 7 already decided how —
   the tap is `P1 measured`, the position is `P3 fitted`, and `drift()` is the
   middle. So a `Remark` carries a `Mark` and adds nothing to it. A commentary
   type that stored its own `at_ms` would be the second spelling of a location
   that `marking.py` exists to prevent.

2. **A remark about several students is several remarks** (W-1, W-3, rule 8).
   :func:`fan_out` is the only constructor that takes more than one anchor, and
   it returns a **tuple of lane-scoped remarks sharing one referent**. There is
   no field anywhere in this module that holds a list of students, so the roster
   column W-1 forbids is not refused — it is unwritable.

3. **A remark binds to one event and cannot become a rating** (refusal 4,
   `SA-3`). See *The score that cannot exist*, below.

4. **A guest session is narrated, and its exit reconciliation is a filter over
   the disclosure chain** — never a second summary kept for the purpose. §7.2's
   knock, and `docs/RECONCILE-JUDGE.md` J6's reason: *"a guest whose
   reconciliation came from a separate summary could be shown a different
   history from the one the institution keeps."*

**What it is not: a judgement about prose.** `docs/RECONCILE-JUDGE.md`
demonstrates that a regex over a judge's sentences lands in the wrong place —
*"a suggested score is a ranking whether or not it is ever spelled out in one"*
— so nothing here inspects a remark's words. The refusals are on the *type*.

---

**The score that cannot exist.** `SA-3` is a prohibited scope, *invalid even
fully signed by root*, and §13 records the correction that put adjudicator
calibration inside it. The enforcement here is structural in the shape
`records/conflict.py` established:

* a `Remark` holds exactly one `Mark`, which holds exactly one `referent`. There
  is no `events`, no `season`, no `history`, and no `score` — a rating that
  travels between events has nowhere to live.
* reaching for one **raises with the clause attached** rather than returning
  `None`, because a caller who gets `None` writes `getattr(..., 0)` and moves
  on. :attr:`Remark.rating`, :attr:`Remark.score` and
  :attr:`Remark.calibration` are properties that raise :class:`StandingScore`.
* :func:`refuse_standing_score` gives the refusal one spelling, so a call site
  that wants it cannot quietly grow its own.

**What `SA-3` does not forbid** is worth stating, because a refusal that also
refuses to be useful gets routed around: §8.1's *"query every comment about
brass balance across a full season"* reads remarks across events and is fine.
Reducing them to a durable number about a person is the prohibited act. This
module offers the first shape and none of the second.

---

**Rung (rule 13).** `docs/RECONCILE-JUDGE.md`'s module sweep is explicit that
*"which rung adjudication commentary lands at is not decided in this file or
anywhere else it cites."* It is still not decided. So :func:`release` takes a
`Rung` and **has no default**: absence surfaces as a refusal naming the open
question, never as a rung this module picked while nobody was looking.

**Thirteen fields (rule 17).** §7.2's knock is *"thirteen fields declaring
intent on entry, thirteen declaring outcome on exit."* **Their names are not in
this tree**, and §14 marks that component `UNVERIFIED`. So :class:`Declaration`
declares what this application knows to declare and asserts no count;
:data:`KNOCK_FIELD_NAMES_KNOWN` records that the shape is `unknown`. A type here
claiming to be the thirteen would be a figure quoted from prose.

Stdlib only. No audio, no model, no network, no store: this module never builds
a request. It is handed what a call returned, and decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Sequence, Tuple

from .conflict import refuse_to_rank
from .dispatch import Dispatch, dispatch
from .disclosure import Ledger
from .inference import Answer, through
from .marking import (P_CITED, P_FITTED, P_MEASURED, Mark, outranks as
                      p_outranks)
from .rungs import Rung, compose
from .sealing import Record, State, authored_by, draft
from .serving import Edge, Field, Outcome, Principal, Serving, _WILDCARDS

# --- what the clauses say, verbatim ----------------------------------------

#: `SA-3` at source, as §13 quotes `PROTECTED_AGENTS.md` Schedule A. Stamped on
#: every refusal this module raises for it, the way `inference.CLAUSE` is: a
#: refusal is only re-checkable against the clause in force when it was made.
#:
#: **Rule 12.** Quoting a clause that also lives in `docs/ARCHITECTURE.md` is a
#: pair, so it gets a middle in this commit —
#: `tests/test_commentary.py::test_the_sa3_clause_here_is_the_documents_clause`
#: reads §13 and fails when the two drift.
SA3_CLAUSE = (
    "any durable rating of an agent carried between contexts or offices; the "
    "durable form of compounded offices (I-4)"
)

#: What a person may be shown when this module refuses. No fleet noun, no
#: scope code, no provider or host: those are operator facts and belong in the
#: exception text (`CLAUDE.md`, *Working here*).
NARRATION = {
    "standing_score": (
        "Refused: this program does not keep a running rating of a person "
        "across events. A remark belongs to the performance it was made about."),
    "ordering": (
        "Refused: nothing here ranks one student against another. The system "
        "presents what was observed and a named person decides."),
    "unsealed": (
        "Not yet shown: nobody has confirmed these words as theirs. A machine's "
        "draft is not a record until the person who spoke seals it."),
    "unlaned": (
        "Refused: this remark names no student, so there is no record of a "
        "student's to attach it to."),
    "rung_undecided": (
        "No answer: how sensitive adjudication commentary is has not been "
        "settled, so it cannot be shown to be releasable."),
}

#: §7.2's knock is thirteen fields in and thirteen out. **This tree does not
#: record their names** — §14 marks the component `UNVERIFIED` — so nothing here
#: validates a declaration against them and nothing here counts to thirteen.
#: Rule 13: the shape is `unknown`, and `unknown` is stated rather than guessed.
KNOCK_FIELD_NAMES_KNOWN = False

#: The §6 classes a judge's dictation over a performance touches. §8.2:
#: *"a recording of a judge's voice over a performance by identifiable minors is
#: `MEDIA_MINOR` twice over."* Both are declared **whatever the remark
#: addresses**, on purpose: the audio contains identifiable students whether or
#: not the sentence names one, and letting an "ensemble" remark drop
#: `PII_MINOR` would declassify the same recording by relabelling the text.
TRANSCRIPT_CLASSES = ("MEDIA_MINOR", "PII_MINOR")

#: `docs/SENSITIVITY.md`'s class-to-rung table puts `PII_MINOR` at `L3` and
#: `MEDIA_MINOR` at `L4`; composition is `max`. Derived by :func:`compose`
#: rather than written as `Rung.L4`, so a change to either rung reaches here.
TRANSCRIPT_RUNG = compose(Rung.L3, Rung.L4)


# --- the refusals ----------------------------------------------------------


class StandingScore(Exception):
    """Raised where a caller reached for a rating that travels (refusal 4).

    Carries `SA3_CLAUSE`, because a refusal without its clause is a preference.
    """

    def __init__(self, detail: str):
        super().__init__(f"SA-3: {detail} — {SA3_CLAUSE}")
        self.clause = SA3_CLAUSE
        self.narration = NARRATION["standing_score"]


class Unsealed(Exception):
    """A draft was offered where only a sealed record may go (§8.2).

    Distinct from a permission refusal: the principal may well be entitled to
    the remark. What does not exist yet is a remark — only a machine's guess at
    one, or a judge's unsigned note.
    """

    def __init__(self, detail: str):
        super().__init__(detail)
        self.narration = NARRATION["unsealed"]


class Unlaned(Exception):
    """A remark that names no student was offered where a lane is required.

    Not an error in the remark: commentary about the work, addressed to nobody
    in particular, is the ordinary adjudication case. It is an error at a call
    site that assumed every remark has a student's record behind it.
    """

    def __init__(self, detail: str):
        super().__init__(detail)
        self.narration = NARRATION["unlaned"]


def refuse_standing_score(what: str, about: str = "") -> None:
    """Call this where a durable cross-event rating was requested. Always raises.

    One spelling, for `conflict.refuse_to_rank`'s reason: an inline `raise`
    repeated at each call site is how one of them ends up returning a number on
    a busy afternoon.
    """
    raise StandingScore(
        f"{what} would be a rating of {about or 'a person'} carried beyond the "
        "event it was observed at. A remark binds to one performance; there is "
        "no field here for a score that travels, and adding one would be "
        "invalid even signed by root"
    )


def compare(a: "Remark", b: "Remark") -> None:
    """Order two remarks about two students. Always raises (refusal 6).

    Present for the same reason `refuse_to_rank` is: the judge surface is the
    one persona whose *job* is to produce an order, so the refusal has to have a
    name at the point somebody reaches for it. The ranking a judge legitimately
    produces is *their claim*, recorded by :class:`Remark`; a ranking this
    system computed is the violation.
    """
    subjects = [s for s in (a.subject_id, b.subject_id) if s]
    refuse_to_rank("comparing two adjudication remarks", subjects)


# --- how a remark was captured ---------------------------------------------


class Capture(Enum):
    """How the words arrived, which is the same question as their provenance.

    §18 item 7's asymmetry, extended one step: the *tap* is what was observed,
    and the words are a separate claim about it. A judge speaking during the
    show and a judge typing a note in the car park produce the same sentence and
    are not the same evidence.
    """

    LIVE_TAP = "live_tap"    # spoken or typed at the moment — P1 measured
    POST_HOC = "post_hoc"    # written afterwards, by the person — P2 cited
    MACHINE = "machine"      # a transcription — P3 fitted, and never a person's


#: The one place the mapping is written. Never a bare integer (rule 14), and
#: never re-spelled: the rungs are `marking.py`'s constants, imported.
_PROVENANCE_OF = {
    Capture.LIVE_TAP: P_MEASURED,
    Capture.POST_HOC: P_CITED,
    Capture.MACHINE: P_FITTED,
}


class Addressed(Enum):
    """Who a remark is about. §8.1's `addresses`, with the roster removed."""

    LANE = "lane"   # names one student; lane-scoped (W-1)
    WORK = "work"   # about the performance, naming nobody


# --- the primitive ---------------------------------------------------------


@dataclass(frozen=True)
class Remark:
    """A judge's words, anchored to a moment and a seat.

    The anchor is a whole :class:`~records.marking.Mark` rather than a copy of
    its parts, so `at_ms`, `seat`, the optional derived `ScorePosition` and the
    `P1`/`P3` refusal in `align()` all continue to hold. `drift()` still
    reconciles the two halves; nothing here re-implements it.

    **There is no field for a student's quality, a caption number, a placement,
    or a second student.** That is the enforcement — not a check that runs and
    could be skipped, but a shape with nowhere to put the forbidden thing.
    """

    anchor: Mark
    body: str
    by: str                       # the named person who said it; "" for MACHINE
    capture: Capture

    def __post_init__(self):
        if not (self.body or "").strip():
            raise ValueError(
                "a remark with no words is not a remark; an empty body is "
                "absence, and absence is not a result (rule 13)"
            )
        if not isinstance(self.capture, Capture):
            raise ValueError(
                f"{self.capture!r} is not a Capture; how the words arrived is "
                "what their provenance is derived from and cannot be omitted"
            )
        name = (self.by or "").strip()
        if self.capture is Capture.MACHINE:
            if name:
                raise ValueError(
                    f"a machine transcription cannot be attributed to {self.by!r}; "
                    "§8.2 — the transcript is the machine's guess at what a "
                    "person said, and it carries their name only once they have "
                    "sealed it"
                )
        elif not name:
            raise ValueError(
                "a remark a person made names that person; an unattributed "
                "remark is a machine draft and must say so (Capture.MACHINE)"
            )
        # The words may never claim stronger evidence than the tap they hang
        # on. `align()` refuses the same shape for a derived position; this is
        # that rule applied to the other derived half.
        if p_outranks(_PROVENANCE_OF[self.capture], self.anchor.provenance):
            raise ValueError(
                f"a {self.capture.value} remark ({_PROVENANCE_OF[self.capture]}) "
                f"cannot outrank the observation it hangs on "
                f"({self.anchor.provenance})"
            )

    # --- what it is -------------------------------------------------------

    @property
    def provenance(self) -> str:
        """The `P`-rung of the *words*, which is not the anchor's.

        A post-hoc note about a live tap is `P2` words on a `P1` moment. Both
        are true and the pair is the point: the tap is still what happened.
        """
        return _PROVENANCE_OF[self.capture]

    @property
    def addresses(self) -> Addressed:
        """`LANE` when the anchor names a student, `WORK` otherwise.

        Derived rather than stored, because a stored copy could disagree with
        the anchor and `marking.Mark` already refuses a half-named one.
        """
        return Addressed.LANE if self.anchor.subject_id else Addressed.WORK

    @property
    def referent(self) -> str:
        """The moment, shared across lanes (W-3). One event, always."""
        return self.anchor.referent

    @property
    def lane_id(self) -> Optional[str]:
        return self.anchor.lane_id

    @property
    def subject_id(self) -> Optional[str]:
        return self.anchor.subject_id

    # --- what it is not ---------------------------------------------------

    @property
    def rating(self):
        """There is none, and asking is the error (refusal 4, `SA-3`)."""
        refuse_standing_score("Remark.rating", self.subject_id or "this performer")

    @property
    def score(self):
        """There is none, and asking is the error (refusal 4, `SA-3`).

        A caption score is a judge's claim about *one performance* and belongs
        to the sheet, not to a person. `docs/RECONCILE-JUDGE.md` J2: the system
        records a claim and never computes one.
        """
        refuse_standing_score("Remark.score", self.subject_id or "this performer")

    @property
    def calibration(self):
        """There is none, and asking is the error (refusal 4, `SA-3`).

        §13 corrected adjudicator calibration into the prohibited scope. What
        survives is *the judge running their own ledger, owner == subject*, and
        that ledger is not this program's to hold — `docs/RECONCILE-JUDGE.md`
        J7, *needs a human 2*.
        """
        refuse_standing_score("Remark.calibration", self.by or "this adjudicator")


def capture(anchor: Mark, body: str, *, by: str = "",
            mode: Capture = Capture.LIVE_TAP) -> Remark:
    """One remark against one anchor.

    `mode` has a default and `by` does not have a meaningful one: a live tap is
    what this surface is for, and a person's name is what makes it theirs.
    """
    return Remark(anchor, body, by, mode)


def fan_out(marks: Sequence[Mark], body: str, *, by: str = "",
            mode: Capture = Capture.LIVE_TAP) -> Tuple[Remark, ...]:
    """One sentence about a moment involving several students → several remarks.

    *"A shared event is two lane entries with one referent"* (rule 8, W-3). This
    is that, at the point of capture, and it is the **only** constructor here
    that accepts more than one anchor. It returns a tuple; it does not merge,
    and there is no function in this module that produces a single remark with a
    participant list, because that list is the roster column W-1 forbids.

    **Every mark must share one referent.** Marks from two moments are two
    remarks about two things, and letting them through here would produce a
    fan-out whose members are not the same remark — the exact shape that makes
    an adjudication record worthless in a dispute.
    """
    if not marks:
        raise ValueError(
            "a fan-out over no marks is not a shared moment; W-3's crossing is "
            "between lanes that exist"
        )
    referents = {m.referent for m in marks}
    if len(referents) != 1:
        raise ValueError(
            f"a fan-out shares one referent; got {sorted(referents)}. Two moments "
            "are two remarks, and one row covering both is the roster column W-1 "
            "forbids wearing a timestamp"
        )
    lanes = [m.lane_id for m in marks]
    if len(set(lanes)) != len(lanes):
        raise ValueError(
            "two anchors in one fan-out name the same lane; that is one lane "
            "entry written twice, not a shared moment"
        )
    return tuple(Remark(m, body, by, mode) for m in marks)


# --- the seal cascade ------------------------------------------------------

#: `lane_entry.kind` for adjudication commentary. The DDL's `kind` column is
#: free text and CI already writes `'commentary'` into it; this is that spelling
#: with the module's name on it so a later reader can tell adjudication
#: commentary from any other kind of note.
KIND = "adjudication.commentary"


def to_draft(remark: Remark) -> Record:
    """Enter the remark into §8.2's cascade as a `draft`.

    **A machine transcription is attributed to nobody**, which is `sealing`'s
    `author_id=None` — *"a transcription nobody authored is the office's to
    reject."* A judge's own words are :func:`~records.sealing.authored_by`
    theirs, and I-7's supersession asymmetry then applies to them without this
    module knowing anything about it.

    **Nothing here seals.** `seal()` requires a named human and has no default;
    a convenience wrapper that supplied one would be the auto-seal path §8.2
    says does not exist. Call `records.sealing.seal` directly.

    The record's `subject_id` is the student for a `LANE` remark and the
    **referent** for a `WORK` one. Those are different kinds of identifier and
    conflating them would normally be the defect; it is safe in exactly this
    direction because I-7's predicate turns on `author_id == subject_id`, and a
    referent is never a person — so a `WORK` remark can never accidentally
    acquire the durability the clause reserves for a student's own account.
    """
    subject = remark.subject_id if remark.addresses is Addressed.LANE \
        else remark.referent
    if remark.capture is Capture.MACHINE:
        return draft(subject, KIND, remark.body)
    return authored_by(subject, remark.by, KIND, remark.body)


# --- the gate commentary leaves through ------------------------------------


def _render(remark: "Remark", serving) -> str:
    """The sentence a remark leaves as. **Its provenance travels with it.**

    Found by routing this module through the gate: `voice.py` refuses a served
    value whose prose carries no `P`-rung — *"the answer is not withheld for
    being weak, it is shown with its weakness"* (§15). So a judge's words cannot
    leave as bare prose, and that is right rather than an obstacle: a `P3`
    machine guess and a `P1` thing a person said at the moment read identically
    once the qualifier is stripped, and the reader is the one who needs the
    difference.

    The qualifier is **appended to the rendered sentence, never to the body**.
    The seal is over the body; a render that edited it would produce text whose
    digest no longer matched what was sealed, which is the inheritance
    `sealing.py` exists to prevent.

    The serving's provenance is preferred where the predicate set one, so a
    derived instruction is labelled with the rung the read path decided rather
    than with the remark's.
    """
    body = serving.value if serving.value is not None else remark.body
    return f"{body} [{serving.provenance or remark.provenance}]"


def release(
    remark: Remark,
    record: Record,
    principal: Principal,
    edges: Sequence[Edge],
    at: datetime,
    *,
    rung: Optional[Rung],
    lane_id: Optional[str] = None,
    known_as_of: Optional[datetime] = None,
    envelopes: Sequence = (),
    threshold: Optional[datetime] = None,
    widenings: Sequence = (),
    grants: Optional[Sequence] = None,
    log=None,
    authority: str = "",
) -> Dispatch:
    """Serve a sealed remark to somebody, through the one gate everything uses.

    `records/dispatch.py` decides, renders, gates and records, in that order.
    This adds the two questions that are commentary's rather than the read
    path's, and then gets out of the way:

    * **Only a sealed record leaves.** §8.2: *"a `draft` can inform; only a
      `sealed` remark should be quoted back to a student or shown to a parent."*
      `Record.servable` is the existing predicate and it also checks the digest,
      so tightened prose cannot leave wearing the original's signature.
    * **The record must be this remark's.** A sealed record for some other body
      would otherwise pass `servable` and be rendered under this anchor.

    **The rung has no default** (rule 13). Which rung adjudication commentary
    lands at is an open question `docs/RECONCILE-JUDGE.md`'s module sweep names
    and no document answers; a default here would be this module quietly
    answering it.

    **Every argument `dispatch()` takes is forwarded as given**, `grants=None`
    included, for the reason stated there: `None` and `()` are different
    instructions to the predicate.
    """
    if rung is None:
        raise ValueError(
            "release() needs a rung and there is no default: which rung "
            "adjudication commentary lands at is not decided in any document "
            "in this tree (docs/RECONCILE-JUDGE.md, the module sweep's "
            "rungs.py row). Absence is unknown, and unknown does not serve"
        )
    if remark.addresses is not Addressed.LANE:
        raise Unlaned(
            "release() serves a remark from a student's lane; this remark names "
            "no student, so there is no lane to serve it from. Commentary about "
            "the work, addressed to nobody, leaves by a surface §18 item 4 has "
            "not landed"
        )
    if record.body != remark.body:
        raise Unsealed(
            "the sealed record's body is not this remark's; a seal names what "
            "was sealed, and rendering other text under this anchor would be "
            "the inheritance sealing.py's digest exists to prevent"
        )
    if not record.servable:
        raise Unsealed(
            f"this remark is {record.state.value}, not sealed. A machine answer "
            "is a draft until a named human seals it (rule 10, §8.2), and a "
            "rejected one stays rejected"
        )

    return dispatch(
        Field(lane_id=remark.lane_id, subject_id=remark.subject_id,
              name=KIND, rung=rung, payload=remark.body,
              provenance=remark.provenance),
        principal, edges, at,
        lambda serving: _render(remark, serving),
        lane_id=lane_id if lane_id is not None else remark.lane_id,
        known_as_of=known_as_of, envelopes=envelopes, threshold=threshold,
        widenings=widenings, grants=grants, log=log, authority=authority,
    )


# --- §7.2's knock, for the least-trusted session ---------------------------


@dataclass(frozen=True)
class Declaration:
    """What a guest said, at the door, they came to do.

    The `declared` half of `reconciled_session`. §7.2's worked example is this
    persona exactly — *"declares Event 42, these captions, this window."*

    **No trust level.** §7.2: a claimed `trust_level` is capped at a registered
    ceiling upstream, *"so 'Elder' is not a text field anyone can type."* A
    field for one here would be that text field, at the one door where it
    matters most.

    **No group.** `lanes` holds lane identifiers and there is no `section`,
    `ensemble` or `part` field, because *"the drumline" is not a scope; a name
    is* (refusal 5, W-2). A wildcard lane is refused at construction, using the
    same list `serve()` and `widens()` refuse one with.

    **It does not claim to be the thirteen.** See `KNOCK_FIELD_NAMES_KNOWN`.
    """

    principal_id: str
    purpose: str
    event_id: str
    lanes: Tuple[str, ...]
    opened_at: datetime

    def __post_init__(self):
        if not (self.principal_id or "").strip():
            raise ValueError("a knock names who is knocking")
        if not (self.purpose or "").strip():
            raise ValueError(
                "a session with no declared purpose is not a knock; §7.2's "
                "reconciliation diffs the declaration against what happened, "
                "and there is nothing to diff against an empty one"
            )
        if not (self.event_id or "").strip():
            raise ValueError(
                "a guest grant is to an event, not to a roster (§4); a "
                "declaration with no event has no window to expire with"
            )
        bad = [ln for ln in self.lanes
               if not (ln or "").strip() or ln.strip().lower() in _WILDCARDS]
        if bad:
            raise ValueError(
                f"{bad!r} is not a lane; a wildcard or a section is a group grant "
                "over students and is invalid at issuance (refusal 5, W-2)"
            )
        if len(set(self.lanes)) != len(self.lanes):
            raise ValueError("a lane declared twice is one lane declared once")


@dataclass(frozen=True)
class GuestSession:
    """A knock, and its close. The `reconciled_session` row, as a type.

    **This is not a second session model.** The columns are the DDL's —
    `opened_at`, `closed_at`, `principal_id`, `declared`, `observed`, `diff` —
    and the observed and diff halves are *computed* by :func:`observed` and
    :func:`reconcile_exit` from the disclosure chain rather than stored here.
    A guest whose reconciliation came from a separate summary could be shown a
    different history from the one the institution keeps.
    """

    declared: Declaration
    closed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.closed_at is not None and self.closed_at < self.declared.opened_at:
            raise ValueError("a session cannot close before it opened")

    @property
    def open(self) -> bool:
        return self.closed_at is None

    def within(self, when: datetime) -> bool:
        """Whether `when` falls inside the session's window.

        An open session has no upper bound *yet*; it is not unbounded forever,
        which is why :func:`reconcile_exit` refuses to reconcile one.
        """
        if when < self.declared.opened_at:
            return False
        return self.closed_at is None or when <= self.closed_at


def knock(principal_id: str, *, purpose: str, event_id: str,
          lanes: Sequence[str] = (), at: datetime) -> GuestSession:
    """Open a guest session with a declared purpose (§7.2)."""
    return GuestSession(Declaration(principal_id, purpose, event_id,
                                    tuple(lanes), at))


def close(session: GuestSession, at: datetime) -> GuestSession:
    """Close the session. Returns a new one; nothing is mutated."""
    return GuestSession(session.declared, at)


def log_capture(ledger: Ledger, session: GuestSession, remark: Remark, *,
                at: datetime, rung: Optional[Rung] = None,
                authority: str = "") -> Ledger:
    """Write one capture to the subject's lane chain (§7.2, J6).

    **The existing `Ledger`, not a second log.** §5 is explicit that
    *"adjudication commentary"* inherits the disclosure log's three
    requirements, and the one that bites is per-subject partitioning: a single
    chain with a lane column is rule 8's roster shape in the audit table.

    **Two honest notes about the shape.**

    *The outcome vocabulary is read-shaped and a capture is a write.*
    `Outcome` has `PAYLOAD`, `INSTRUCTION`, `REFUSED` and `UNKNOWN`; none of
    them means *"a guest wrote here."* This records `PAYLOAD`, so
    `Entry.disclosed` reads true for a row where nothing left the system. That
    is over-reporting, which is the safe direction for the audit trail of the
    least-trusted session: it can never under-report a lane the guest touched,
    and the exit reconciliation is exactly a question about what they touched.
    Inventing a second log with a write vocabulary would be the pair §16
    forbids. Recorded as a finding rather than papered over.

    *A `WORK` remark writes nothing here*, because it names no lane. A guest
    who only ever spoke about the ensemble touched no student's record, and a
    chain entry saying otherwise would be false.
    """
    if remark.addresses is not Addressed.LANE:
        return ledger
    if not session.within(at):
        raise ValueError(
            f"a capture at {at.isoformat()} falls outside the session that "
            "declared it; a grant is time-boxed to its event window (§4) and a "
            "capture outside it is the reconciliation failure, not a row"
        )
    serving = Serving(
        Outcome.PAYLOAD, None, rung,
        f"adjudication commentary captured into this lane at "
        f"{remark.anchor.at_ms}ms, seat {remark.anchor.seat}",
        via_purpose=session.declared.purpose,
    )
    return ledger.record(
        serving, lane_id=remark.lane_id, principal_id=session.declared.principal_id,
        subject_id=remark.subject_id, field_name=KIND, at=at,
        authority=authority or f"declared purpose: {session.declared.purpose}",
    )


@dataclass(frozen=True)
class Observed:
    """What the chain says the guest actually touched. A filter, not a record."""

    principal_id: str
    lanes: Tuple[str, ...]
    entries: int

    @property
    def touched_nothing(self) -> bool:
        return not self.lanes


def observed(ledger: Ledger, session: GuestSession) -> Observed:
    """The `observed` half, derived from the disclosure chain (J6).

    *"The exit reconciliation is a filter over that chain, not a second record
    kept for the purpose."* This is that filter, and it is the whole
    implementation: there is no second store to disagree with.

    Only entries by **this** principal, inside **this** session's window, count.
    A lane another principal read during the same evening is not something this
    guest touched, and a session that has not closed is filtered to its open
    upper bound — which is why :func:`reconcile_exit` refuses one.
    """
    lanes, count = [], 0
    for lane_id, log in ledger.lanes:
        hit = [e for e in log.entries
               if e.principal_id == session.declared.principal_id
               and session.within(e.occurred_at)]
        if hit:
            lanes.append(lane_id)
            count += len(hit)
    return Observed(session.declared.principal_id, tuple(sorted(lanes)), count)


class ExitState(Enum):
    RECONCILED = "reconciled"  # what was declared covers what was done
    DIVERGED = "diverged"      # the guest touched what they did not declare
    UNKNOWN = "unknown"        # the session has not closed; not a pass (rule 13)


@dataclass(frozen=True)
class ExitReconciliation:
    """Declared against observed — the `diff` column, computed.

    **A reconciliation is not a permission decision.** §7.2: *"a guest who
    declared score ensemble 7 and touched forty members' medical records
    generates a reconciliation failure even if the grant technically permitted
    it."* So `DIVERGED` says what happened; it does not claim the grant was
    exceeded, and nothing here revokes anything.
    """

    state: ExitState
    declared: Declaration
    seen: Observed
    undeclared: Tuple[str, ...]   # touched, never declared — the failure §7.2 names
    unvisited: Tuple[str, ...]    # declared, never touched — routine, and recorded
    reason: str

    @property
    def reconciled(self) -> bool:
        """True only for `RECONCILED`. An `UNKNOWN` is not a yes (rule 13)."""
        return self.state is ExitState.RECONCILED

    @property
    def narration(self) -> str:
        """What the guest is shown, and it is shown to them (J6).

        *"A narration the guest reads is louder than one filed where only staff
        look, and it costs nothing to show a person their own audit trail."*
        Names no lane identifier: the guest is being told the shape of their own
        session, and a lane id is another student's key.
        """
        if self.state is ExitState.UNKNOWN:
            return ("This session is still open, so there is nothing to "
                    "reconcile yet.")
        said = (f"You said you were here to {self.declared.purpose}.")
        did = (f"You added notes in {len(self.seen.lanes)} student record(s), "
               f"{self.seen.entries} entr(y/ies) in all.")
        if self.state is ExitState.RECONCILED:
            return f"{said} {did} That matches what you declared."
        return (f"{said} {did} {len(self.undeclared)} of those record(s) were "
                "not part of what you declared, and this has been recorded.")


def reconcile_exit(session: GuestSession, ledger: Ledger) -> ExitReconciliation:
    """Diff the declaration against the chain (§7.2).

    **An open session reconciles to `UNKNOWN`, never to `RECONCILED`.** A guest
    who has not left has not finished, and answering *"that matches"* to a
    session still in progress is absence rendered as a result (rule 13). It is
    also the direction that matters: the reconciliation is the half that
    protects anyone, and a premature pass is the one failure mode that would
    make it decorative.
    """
    seen = observed(ledger, session)
    if session.open:
        return ExitReconciliation(
            ExitState.UNKNOWN, session.declared, seen, (), (),
            "the session has not closed; a reconciliation of a session still in "
            "progress is not an answer")
    declared = set(session.declared.lanes)
    touched = set(seen.lanes)
    undeclared = tuple(sorted(touched - declared))
    unvisited = tuple(sorted(declared - touched))
    if undeclared:
        return ExitReconciliation(
            ExitState.DIVERGED, session.declared, seen, undeclared, unvisited,
            f"{len(undeclared)} lane(s) were written to that the declaration did "
            "not name; §7.2 records this whether or not the grant permitted it")
    return ExitReconciliation(
        ExitState.RECONCILED, session.declared, seen, (), unvisited,
        f"{len(touched)} lane(s) touched, all declared"
        + (f"; {len(unvisited)} declared lane(s) were not touched" if unvisited else ""))


# --- the transcription seam ------------------------------------------------


class TranscriptState(Enum):
    """§8.2's table, as the states this seam can be in.

    `DRAFT`, `SEALED` and `REJECTED` are `sealing.State`'s and are not
    duplicated — :class:`Transcript` holds a `Record` and reads them off it.
    `PENDING` is the one this seam adds a *reason* to: §8.2's *"alignment or
    transcription produced nothing usable — said plainly, not guessed at."*
    """

    PENDING = "pending"
    DRAFT = "draft"


@dataclass(frozen=True)
class Transcript:
    """A machine's guess at what a judge said, anchored, and sealed by nobody.

    **Attributed to the machine, never to the judge.** The wrapped `Record` is
    `sealing.draft`'s, whose `author_id` is `None` — *"a transcription nobody
    authored."* Constructing one with a `Record` that names an author is
    refused: that record is a person's own words and this is not.
    """

    record: Record
    anchor: Mark
    by_machine: str               # the transcriber's identifier — an operator fact
    provenance: str = P_FITTED

    def __post_init__(self):
        if self.record.state is not State.DRAFT:
            raise ValueError(
                f"a transcript arrives as a draft, not {self.record.state.value}; "
                "the seal is a later act by a named human (§8.2)"
            )
        if self.record.author_id is not None:
            raise ValueError(
                f"this record is authored by {self.record.author_id!r}; a "
                "transcript is the machine's guess at a person's words and is "
                "attributed to the machine until that person seals it (rule 10)"
            )
        if not (self.by_machine or "").strip():
            raise ValueError(
                "a transcript names what produced it; an unattributed machine "
                "answer cannot be told from a person's note"
            )
        if p_outranks(self.provenance, self.anchor.provenance):
            raise ValueError(
                f"a transcript ({self.provenance}) cannot outrank the tap it was "
                f"anchored to ({self.anchor.provenance})"
            )

    @property
    def state(self) -> TranscriptState:
        return TranscriptState.DRAFT

    @property
    def servable(self) -> bool:
        """Never. A draft informs; only its sealed successor is served (§8.2)."""
        return False

    @property
    def said_by(self):
        """There is none, and asking is the error.

        A property rather than an absent attribute, for `conflict.py`'s reason.
        The judge is the *speaker*; the transcript is a model's answer about
        them, and a caller that treats the two as one is doing the thing §8.2
        says leaves *"a machine transcription of a human's words looking like
        the human's words."*
        """
        raise NotImplementedError(
            "a transcript is not attributed to the person who spoke; it is a "
            "draft until they seal it by name (rule 10, §8.2) — use "
            "records.sealing.seal(), which refuses a role and a machine"
        )

    def as_remark(self) -> Remark:
        """The remark this transcript is a draft of. `Capture.MACHINE`, always.

        Built rather than stored, so a transcript can never carry a remark
        attributed to a person while its own record is attributed to nobody.
        """
        return Remark(self.anchor, self.record.body, "", Capture.MACHINE)


@dataclass(frozen=True)
class Pending:
    """§8.2's third state: nothing usable was produced, said plainly.

    Carries the refusal that produced it, so *"the local model did not answer"*
    and *"a third party answered"* stay the two different facts refusal 1 is
    made of. This is **not** a `Transcript` and has no body: rule 13, absence
    surfaces as its own state and never as an empty string a surface could
    render as a remark.
    """

    anchor: Mark
    reason: str
    narration: str

    @property
    def state(self) -> TranscriptState:
        return TranscriptState.PENDING

    @property
    def servable(self) -> bool:
        return False

    @property
    def body(self):
        """There is none, and asking is the error (rule 13)."""
        raise NotImplementedError(
            "nothing usable was transcribed. There is no text here, and an "
            "empty one would render as a remark nobody made — absence is "
            "'unavailable', never 'no findings'"
        )


def transcribe(call: Callable[[], object], anchor: Mark, *, endpoint: str,
               by_machine: str, subject_id: Optional[str] = None) -> Transcript:
    """Run a transcription and land its answer as an unsealed draft.

    **The only way audio becomes text in this module**, and it is a seam: no
    audio, no model, no client, no request. `call` closes over the caller's own
    prompt, model and client and returns the `(response_text, provider_used)`
    pair the upstream router returns; everything about *whether that answer may
    exist* is `records/inference.through`'s, called here and not re-derived.

    **The tagging is this module's contribution.** A caller supplying its own
    `classes` could tag a judge's dictation `PUBLIC` and pass; here the classes
    are `TRANSCRIPT_CLASSES` and the rung is `TRANSCRIPT_RUNG`, both derived
    from §8.2 and `SENSITIVITY.md` rather than accepted from the call site.
    There is no `classes=` parameter to override them with.

    **Everything the guard refuses, this refuses**, by not catching it: an
    unclassified call, an unknown provider, a third party, the local label at
    another machine, and a local model that did not answer all arrive at the
    caller as `InferenceRefused` subclasses carrying refusal 1's clause. Use
    :func:`pending_from` to turn one into §8.2's `pending` state where a surface
    needs to record that nothing usable came back.

    `subject_id` defaults to the anchor's, and falls back to the referent for a
    mark that names no student — the same rule :func:`to_draft` uses, for the
    same reason.
    """
    answer: Answer = through(call, classes=TRANSCRIPT_CLASSES,
                             endpoint=endpoint, rung=TRANSCRIPT_RUNG)
    subject = subject_id or anchor.subject_id or anchor.referent
    return Transcript(draft(subject, KIND, answer.text), anchor, by_machine)


def pending_from(exc: Exception, anchor: Mark) -> Pending:
    """Turn a refusal into §8.2's `pending`, keeping which refusal it was.

    Deliberately **not** what :func:`transcribe` does on failure. A function
    that swallowed its own refusal into a quiet state would make a stopped local
    model and a cloud model answering look the same on the surface, which is the
    distinction refusal 1's last sentence is made of. The caller catches, and
    calls this if it has somewhere to record the fact.
    """
    narration = getattr(exc, "narration", None) or (
        "No answer: nothing usable was produced, and nothing was guessed at.")
    return Pending(anchor, f"{type(exc).__name__}: {exc}", narration)
