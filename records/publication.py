"""§18 item 15, the weekly half: everything around the call that leaves.

The composite is decided — a public timestamp weekly, a legible deposit
annually, guardian receipts continuously — and `records/witness.py` supplies the
anchor. What was missing is the *publication*: the payload that crosses, the
record that it crossed, the proof that came back, and the states in between.

**Nothing here opens a socket, and the omission is the design.** §6's core/seam
partition, in `records/export.py`'s words: the core returns what the caller
transmits. `payload_for()` hands back thirty-two bytes; a deployment's seam
submits them and hands back a `Proof`. That is why the actual timestamp call is
a deployment act and this module is everything up to and after it.

**What may cross, and the ceiling.** An anchor carries a digest, a count and a
time, and `permitted()` is the gate that says so — not as a convention but by
reading the type. Anything else on the object is refused at the boundary rather
than published and regretted, because a publication is irrevocable in a way a
disclosure is not: it is on somebody else's calendar server.

**What actually goes on the wire is narrower still.** The thirty-two bytes are
a commitment over the three fields, not the chain head itself, and that is not
tidiness — two quiet weeks produce the *same* head and count, so a head-only
submission lets one proof stand in for both and a skipped publication becomes
invisible. Binding the slot into the commitment gives every week its own
digest, and binds the time we claim to the time the witness attests.

**Cadence comes from the calendar and the gate enforces it.** `corpus-lens`:
*"content redaction does not scrub the shape of a week."* An anchor published
because something happened publishes that something happened, so `payload_for()`
requires a `Cadence` and refuses an anchor whose time the calendar does not
name. There is no way through this module to publish off-schedule.

**A submission with no proof back is its own state.** Rule 13: it is not
witnessed, it is not fine, and it is not silently dropped from the register —
`AWAITING_PROOF` becomes `OVERDUE` when the redemption window passes, and
neither yields a `witness.Receipt`. Only `PROVEN` does.

Rule 12's pair is submission-and-proof, and `reconcile()` is its middle: it
reports one state per slot rather than presenting whichever half the caller
happened to read. The two artifacts share a filename stem for the same reason —
a proof names the submission it answers.

Stdlib only. No network, no filesystem.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields as _fields
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Sequence, Tuple

from .export import Artifact
from .witness import (Anchor, Independence, Receipt, anchor_for_ledger,
                      ledger_derivation, missing, schedule)

#: The whole of what an anchor may carry, and therefore the whole of what may
#: cross the egress boundary here. Read off `Anchor` by the gate below rather
#: than trusted to stay true.
MAY_CROSS = ("head", "count", "at")


class NotPublishable(ValueError):
    """Refused at the boundary: this may not be published as it stands.

    Raised rather than returned, and rather than published-with-a-warning,
    because a publication cannot be recalled. The caller gets no payload.
    """


# --- the gate ---------------------------------------------------------------


def permitted(anchor) -> Tuple[bool, str]:
    """Whether this object may cross, and why.

    Three ways something arrives here carrying more than it should, and all
    three are refused:

    * **a subclass with another field** — `Anchor` is a frozen dataclass and
      subclassing one to hang a subject id off it costs four lines
    * **an attribute set on the instance** — frozen blocks assignment, and
      `object.__setattr__` does not care
    * **something that is not an anchor at all** — `Ledger.anchors()` returns
      one `(head, count)` per lane, and publishing those is a per-student
      activity series wearing an anchor's clothes
    """
    if not isinstance(anchor, Anchor):
        return (False, f"not an anchor: {type(anchor).__name__}. Only an anchor "
                       "may be published, because only an anchor is incapable of "
                       "carrying a name")
    declared = tuple(f.name for f in _fields(type(anchor)))
    extra = [n for n in declared if n not in MAY_CROSS]
    if extra:
        return (False, f"{type(anchor).__name__} declares {', '.join(extra)} "
                       "beyond a digest, a count and a time; that is a disclosure, "
                       "not an anchor")
    missing_fields = [n for n in MAY_CROSS if n not in declared]
    if missing_fields:
        return (False, f"an anchor without {', '.join(missing_fields)} cannot be "
                       "redeemed later")
    hung = sorted(k for k in getattr(anchor, "__dict__", {}) if k not in MAY_CROSS)
    if hung:
        return (False, f"{', '.join(hung)} was set on the instance; the type says "
                       "three fields and the object carries more")
    return (True, "a digest, a count and a time; nothing else")


# --- cadence ----------------------------------------------------------------


@dataclass(frozen=True)
class Cadence:
    """When publications are due, derived from the calendar and nothing else.

    Deliberately holds no log, no ledger and no activity: a schedule computed
    from what happened publishes what happened. The tolerance exists because a
    job that runs at 03:00:07 is on time, and it is capped below half a period
    because a tolerance that admits every moment is not a cadence at all.
    """

    start: datetime
    every: timedelta = timedelta(days=7)
    tolerance: timedelta = timedelta(hours=1)

    def __post_init__(self):
        if self.every <= timedelta(0):
            raise ValueError("a cadence must be positive")
        if self.tolerance < timedelta(0):
            raise ValueError("a tolerance cannot be negative")
        if self.tolerance * 2 >= self.every:
            raise ValueError(
                "a tolerance of half a period or more admits every moment, which "
                "is the activity-driven cadence this class exists to prevent"
            )

    def slots(self, through: datetime) -> Tuple[datetime, ...]:
        """Every due time up to `through`. One implementation, in `witness`."""
        return schedule(self.start, through, self.every)

    def is_slot(self, at: datetime) -> bool:
        tol = self.tolerance.total_seconds()
        if at < self.start - self.tolerance:
            return False
        return any(abs((at - due).total_seconds()) <= tol
                   for due in self.slots(at + self.tolerance))


# --- what crosses -----------------------------------------------------------


def _commitment(head: str, count: int, at: datetime) -> bytes:
    return hashlib.sha256(
        "\x1f".join([head, str(count), at.isoformat()]).encode("utf-8")).digest()


@dataclass(frozen=True)
class Payload:
    """What the seam transmits. Three fields, and one of them goes on the wire.

    The count and the time stay on this box: they are what makes the anchor
    redeemable later (§5's emptied-is-not-absent), and a *published series of
    counts* would be a volume signal — the shape of a week arriving through the
    one field nobody thought of as content.
    """

    head: str
    count: int
    at: datetime

    @property
    def commitment(self) -> bytes:
        """The thirty-two bytes. Nothing else is transmitted."""
        return _commitment(self.head, self.count, self.at)

    @property
    def over(self) -> str:
        return self.commitment.hex()


def payload_for(anchor: Anchor, cadence: Cadence) -> Payload:
    """The only way to obtain something publishable.

    Takes the calendar rather than defaulting to none, so publishing
    off-schedule is not an option a caller can decline to pass.
    """
    ok, why = permitted(anchor)
    if not ok:
        raise NotPublishable(why)
    if not cadence.is_slot(anchor.at):
        raise NotPublishable(
            f"{anchor.at.isoformat()} is not a time the calendar names. An anchor "
            "published because something happened publishes that something "
            "happened, which is the shape-of-a-week leak the cadence exists to "
            "close"
        )
    return Payload(anchor.head, anchor.count, anchor.at)


def payloads_for(anchors: Sequence[Anchor], cadence: Cadence) -> Tuple[Payload, ...]:
    """A batch, refused if two anchors land in one slot.

    One slot with several anchors is several chains, and a weekly series of
    per-chain anchors is per-lane volume published on a public calendar. The
    program publishes one anchor per slot or it publishes its roster's shape.
    """
    out = [payload_for(a, cadence) for a in anchors]
    seen = {}
    for p in out:
        key = p.at.isoformat()
        if key in seen:
            raise NotPublishable(
                f"two anchors for the slot at {key}; a slot carrying more than one "
                "anchor publishes how many chains there are and how each grew"
            )
        seen[key] = p
    return tuple(out)


# --- the record of a publication -------------------------------------------


@dataclass(frozen=True)
class Submission:
    """That a payload was handed to a witness, and when.

    Carries the anchor rather than the payload so the derivation stays
    checkable, and re-runs the gate at construction: a submission built around
    something that could not have been published is a record of an act that
    should not have happened.
    """

    anchor: Anchor
    submitted_at: datetime
    kind: str = "opentimestamps"

    def __post_init__(self):
        ok, why = permitted(self.anchor)
        if not ok:
            raise NotPublishable(why)

    @property
    def over(self) -> str:
        """The commitment this submission is redeemed by."""
        return _commitment(self.anchor.head, self.anchor.count,
                           self.anchor.at).hex()


@dataclass(frozen=True)
class Proof:
    """What came back. The thing that is worth something two years out.

    `attested_at` is `None` until the witness commits to a time — a public
    timestamp is a promise first and a proof afterwards — and that gap is a
    state rather than a detail, because a promise is not a proof.
    """

    over: str
    ref: str
    received_at: datetime
    attested_at: Optional[datetime] = None
    kind: str = "opentimestamps"

    def __post_init__(self):
        if len(self.over) != 64 or any(c not in "0123456789abcdef" for c in self.over):
            raise ValueError("a proof must name the digest it commits to")
        if not self.ref.strip():
            raise ValueError(
                "a proof with no external reference redeems nothing; it is a note "
                "to self"
            )


# --- states -----------------------------------------------------------------


class Publication(Enum):
    """Every state a scheduled publication can be in. None of them is 'fine'."""

    NOT_SUBMITTED = "not_submitted"    # the calendar said so and nothing was sent
    AWAITING_PROOF = "awaiting_proof"  # sent; the witness has not committed yet
    OVERDUE = "overdue"                # awaiting past the redemption window
    PROVEN = "proven"                  # a proof, for this digest, with a time
    MISMATCHED = "mismatched"          # a proof that contradicts what it answers
    UNSOLICITED = "unsolicited"        # a proof for nothing this program sent
    OFF_CALENDAR = "off_calendar"      # published at a moment the calendar omits


@dataclass(frozen=True)
class Status:
    """One line of the register. `is_witness` is true for exactly one state."""

    state: Publication
    at: datetime
    reason: str
    submission: Optional[Submission] = None
    proof: Optional[Proof] = None

    @property
    def is_witness(self) -> bool:
        return self.state is Publication.PROVEN


def reconcile(submissions: Sequence[Submission], proofs: Sequence[Proof],
              cadence: Cadence, *, through: datetime,
              as_of: Optional[datetime] = None,
              window: timedelta = timedelta(days=1)) -> Tuple[Status, ...]:
    """Rule 12's middle for the submission/proof pair.

    A caller reading the submissions alone sees a diligent programme; a caller
    reading the proofs alone sees the ones that worked. Neither half answers
    *is this record witnessed*, so this reports every slot the calendar named,
    every submission that was made, and every proof that arrived — including
    the ones that answer nothing.
    """
    now = as_of if as_of is not None else through
    out = []

    gaps = missing(submissions, cadence.start, through, cadence.every,
                   tolerance=cadence.tolerance)
    for due in gaps:
        out.append(Status(
            Publication.NOT_SUBMITTED, due,
            "the calendar named this slot and nothing was submitted; a witness "
            "log with holes nobody notices is the same as none"))

    answered = set()
    for sub in sorted(submissions, key=lambda s: s.anchor.at):
        if not cadence.is_slot(sub.anchor.at):
            out.append(Status(
                Publication.OFF_CALENDAR, sub.anchor.at,
                "published at a moment the calendar does not name; a series that "
                "tracks activity publishes the activity", sub))
            continue
        for_this = [p for p in proofs if p.over == sub.over]
        answered.update(id(p) for p in for_this)
        best = next((p for p in for_this if p.attested_at is not None),
                    for_this[0] if for_this else None)
        if best is None:
            waited = now - sub.submitted_at
            if waited > window:
                out.append(Status(
                    Publication.OVERDUE, sub.anchor.at,
                    f"submitted {sub.submitted_at.isoformat()} and no proof has "
                    f"come back; the redemption window was {window}", sub))
            else:
                out.append(Status(
                    Publication.AWAITING_PROOF, sub.anchor.at,
                    "submitted; the witness has not returned a proof yet. This is "
                    "not a witnessed anchor", sub))
            continue
        if best.attested_at is None:
            waited = now - sub.submitted_at
            state = (Publication.OVERDUE if waited > window
                     else Publication.AWAITING_PROOF)
            out.append(Status(
                state, sub.anchor.at,
                "the witness returned a reference and no time; a promise of a "
                "timestamp is not a timestamp", sub, best))
            continue
        if best.attested_at < sub.anchor.at:
            out.append(Status(
                Publication.MISMATCHED, sub.anchor.at,
                f"the proof attests {best.attested_at.isoformat()}, before the "
                "entries it covers existed", sub, best))
            continue
        out.append(Status(
            Publication.PROVEN, sub.anchor.at,
            f"witnessed by {best.kind}, attested {best.attested_at.isoformat()}, "
            f"redeemable at {best.ref}", sub, best))

    for p in proofs:
        if id(p) not in answered:
            out.append(Status(
                Publication.UNSOLICITED, p.received_at,
                f"a proof for {p.over[:12]}, which this programme has no record of "
                "submitting; either the submission record was lost or the proof "
                "answers something else", None, p))

    return tuple(sorted(out, key=lambda s: (s.at, s.state.value)))


def receipts(statuses: Sequence[Status]) -> Tuple[Receipt, ...]:
    """`witness.Receipt` for the proven ones, and only those.

    The join into `witness.standing()`, and the place rule 13 has to hold: a
    pending submission that produced a receipt here would make an unwitnessed
    log read as witnessed, which is the exact failure `standing()` is written to
    make impossible.
    """
    return tuple(
        Receipt(s.submission.anchor, s.proof.kind, s.proof.ref,
                s.proof.attested_at, Independence.EVIDENTIARY)
        for s in statuses if s.state is Publication.PROVEN)


def unpublished(submissions: Sequence[Submission], cadence: Cadence,
                through: datetime) -> Tuple[datetime, ...]:
    """Slots with nothing submitted. Delegates, deliberately.

    A second implementation of the cadence would be the pair this repository
    keeps recording: two schedules that agree until one is edited.
    """
    return missing(submissions, cadence.start, through, cadence.every,
                   tolerance=cadence.tolerance)


# --- artifacts --------------------------------------------------------------
#
# The caller writes these; nothing here touches a filesystem (§6, and
# `records/export.py` for the same argument at the exit).


def _stem(over: str) -> str:
    return f"anchor-{over[:12]}"


def submission_artifact(sub: Submission) -> Artifact:
    """What was handed over, kept as a file so the act has a record.

    Shares a stem with the proof that answers it: `anchor-3f9a….submission.txt`
    and `anchor-3f9a….proof.txt` are two halves of one publication, and a
    directory listing shows which half is missing.
    """
    lines = [
        "ANCHOR SUBMISSION",
        "=================",
        "",
        f"submitted    {sub.submitted_at.isoformat()}",
        f"witness      {sub.kind}",
        f"for the day  {sub.anchor.at.isoformat()}",
        "",
        "WHAT WAS SENT",
        "-------------",
        f"  {sub.over}",
        "",
        "Thirty-two bytes and nothing else. They are computed from the three",
        "values below, so anyone holding this file can recompute them and see",
        "that they match — and cannot work backwards from them to a record, a",
        "name, or a number of anything.",
        "",
        f"  fingerprint of the record  {sub.anchor.head}",
        f"  entries covered           {sub.anchor.count}",
        f"  as at                     {sub.anchor.at.isoformat()}",
        "",
        "WHAT IS STILL MISSING FROM THIS PAIR",
        "------------------------------------",
        "The proof. Until the matching proof file sits beside this one, this",
        "submission is a claim that something was sent and not evidence that",
        "anyone received it.",
        "",
    ]
    return Artifact(f"{_stem(sub.over)}.submission.txt", "text/plain",
                    "\n".join(lines))


def proof_artifact(proof: Proof) -> Artifact:
    """The half that is worth something. Kept beside the submission it answers."""
    attested = (proof.attested_at.isoformat() if proof.attested_at
                else "NOT YET — the witness has returned a reference and no time")
    lines = [
        "ANCHOR PROOF",
        "============",
        "",
        f"answers      {proof.over}",
        f"witness      {proof.kind}",
        f"received     {proof.received_at.isoformat()}",
        f"attested     {attested}",
        "",
        "HOW THIS IS REDEEMED",
        "--------------------",
        f"  {proof.ref}",
        "",
        "This reference is the whole of the proof's value. A proof whose",
        "reference cannot be checked by somebody outside this programme is a",
        "note this programme wrote to itself.",
        "",
    ]
    return Artifact(f"{_stem(proof.over)}.proof.txt", "text/plain",
                    "\n".join(lines))


_WORDS = {
    Publication.PROVEN: "PUBLISHED, PROOF HELD",
    Publication.AWAITING_PROOF: "SENT, NO PROOF BACK YET",
    Publication.OVERDUE: "SENT, NO PROOF BACK — OVERDUE",
    Publication.NOT_SUBMITTED: "NOTHING WAS SENT",
    Publication.MISMATCHED: "PROOF DISAGREES WITH WHAT IT ANSWERS",
    Publication.UNSOLICITED: "A PROOF FOR SOMETHING NOT SENT",
    Publication.OFF_CALENDAR: "SENT OFF THE SCHEDULE",
}


def register(statuses: Sequence[Status], cadence: Cadence, *,
             through: datetime) -> Artifact:
    """The publication register: every scheduled week, in words, in order.

    This is the page a person reads — and the page the annual deposit prints
    (`docs/WITNESS-DEPOSIT.md`). So it says *what* each line means without
    requiring anybody to know what a digest is, and it never renders a missing
    proof as a blank: a line nobody can read as an outcome is rule 13's failure
    in a document rather than in a function.

    It is built out of statuses, which are built out of anchors, so there is no
    lane, no name and no student in it — not by redaction but because none of
    those is a parameter anything here takes.
    """
    tally = {}
    for s in statuses:
        tally[s.state] = tally.get(s.state, 0) + 1
    ordered = sorted(tally.items(), key=lambda kv: kv[0].value)

    lines = [
        "PUBLICATION REGISTER",
        "====================",
        "",
        f"period       {cadence.start.date().isoformat()} to "
        f"{through.date().isoformat()}",
        f"schedule     one publication every {cadence.every.days} day(s), on the "
        "calendar, whether or not anything was written",
        f"lines        {len(statuses)} (counted from the entries below)",
        "",
        "WHAT THIS IS",
        "------------",
        "Each line below is one scheduled day. On that day a short code is",
        "computed from the programme's records as they stood, and that code is",
        "sent to an outside service which records the date it received it. Any",
        "later change to those records — a word, a row, a deletion — produces a",
        "different code, so a record altered afterwards can be shown to have",
        "been altered. The code reveals nothing about the records themselves:",
        "it cannot be turned back into a name, a note or a number.",
        "",
        "A line that does not read PUBLISHED, PROOF HELD has not been witnessed.",
        "It is not a small omission and it is not the same as a quiet week: the",
        "schedule runs whether or not anything happened, so a missing line is a",
        "missing publication and nothing else.",
        "",
        "SUMMARY",
        "-------",
    ]
    for state, n in ordered:
        lines.append(f"  {n:>4}  {_WORDS[state]}")
    lines += ["", "THE WEEKS", "---------"]
    for s in statuses:
        lines.append(f"{s.at.date().isoformat()}   {_WORDS[s.state]}")
        if s.submission is not None:
            lines.append(f"    entries covered   {s.submission.anchor.count}")
            lines.append(f"    code sent         {s.submission.over}")
        if s.proof is not None:
            lines.append(f"    redeem with       {s.proof.ref}")
            if s.proof.attested_at is not None:
                lines.append(f"    dated by witness  "
                             f"{s.proof.attested_at.isoformat()}")
        lines.append(f"    note              {s.reason}")
        lines.append("")
    lines += [
        "WHAT THIS DOES NOT SHOW",
        "-----------------------",
        "That the records are complete. This shows that what was written was",
        "written by the date given and has not changed since. It cannot show",
        "that everything which happened was written down.",
        "",
    ]
    return Artifact(
        f"publication-register-{through.date().isoformat()}.txt",
        "text/plain", "\n".join(lines))


def derivation_artifact(ledger, anchor: Anchor) -> Artifact:
    """**Local only.** How a whole-programme anchor was arrived at.

    A ledger anchor is one digest over every lane's head and count, so
    re-deriving it later needs those per-lane figures — and they are exactly
    what must never be published or deposited: a weekly series of per-lane
    counts is one student's activity, week by week, in a file. So this artifact
    exists, and it stays on the box.

    The register and the two publication artifacts are built from anchors and
    cannot contain this; that is the split, and `tests/test_publication.py`
    asserts it rather than trusting it.
    """
    rows = ledger_derivation(ledger)
    lines = [
        "ANCHOR DERIVATION — LOCAL RECORD, NOT FOR PUBLICATION OR DEPOSIT",
        "================================================================",
        "",
        "This file names every lane and how many entries it held. It is how the",
        "published code can be recomputed and checked. It is also, line by line,",
        "how much was written about each student that week — so it stays where",
        "the records are. Nothing in it crosses; the published code carries none",
        "of it.",
        "",
        f"as at    {anchor.at.isoformat()}",
        f"code     {anchor.head}",
        f"entries  {anchor.count}",
        "",
        "LANE  HEAD  COUNT",
    ]
    for lane_id, head, count in rows:
        lines.append(f"  {lane_id}  {head}  {count}")
    lines.append("")
    return Artifact(f"{_stem(anchor.head)}.derivation.local.txt", "text/plain",
                    "\n".join(lines))


__all__ = [
    "MAY_CROSS", "NotPublishable", "permitted", "Cadence", "Payload",
    "payload_for", "payloads_for", "Submission", "Proof", "Publication",
    "Status", "reconcile", "receipts", "unpublished", "submission_artifact",
    "proof_artifact", "register", "derivation_artifact", "anchor_for_ledger",
]
