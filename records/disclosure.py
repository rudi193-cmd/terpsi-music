"""The disclosure log: what left, when, to whom, and under what authority.

§7.2's *gate the export, narrate the read*, and FERPA §99.32's disclosure
record. Append-only and hash-chained, because PR #3 found by executing the DDL
that a table described as append-only in a comment was `UPDATE`-able and
`DELETE`-able — *"three of the four are the same defect: a declaration with no
enforcement."*

**Two things this log must get right that are easy to get wrong.**

First, **append-only is enforced, not asserted.** `append()` returns a new log;
there is no method that rewrites or removes an entry, and the chain makes a
silent edit detectable rather than merely forbidden.

Second — and this is the subtle one — **the log must not defeat §7's
indistinguishability guarantee.** A refusal and an absence produce the same
rows, the same count and the same subject list *on the surface*; if the log
records `REFUSED` for the student who declined and nothing at all for the
student with nothing to decline, then the log has re-created the signal the
guarantee exists to suppress, and the audit trail becomes the leak. So a read
that returned no payload is recorded **by rung and outcome, never by whether a
value existed**.

Stdlib only. No network, no store.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from .rungs import Rung
from .serving import Outcome, Serving

GENESIS = "0" * 64


@dataclass(frozen=True)
class Entry:
    """One disclosure. Immutable, and its hash covers its predecessor."""

    occurred_at: datetime
    principal_id: str
    subject_id: str
    field_name: str
    rung: Optional[Rung]
    outcome: Outcome
    authority: str
    prev: str
    digest: str

    @property
    def disclosed(self) -> bool:
        return self.outcome is Outcome.PAYLOAD


def _digest(occurred_at, principal_id, subject_id, field_name, rung, outcome,
            authority, prev) -> str:
    # The payload is deliberately NOT hashed and deliberately not stored. A log
    # that carries what was disclosed is a second copy of the thing it is
    # auditing, at the same rung, in a table people treat as safe because it is
    # "just the audit trail".
    material = "\x1f".join([
        occurred_at.isoformat(), principal_id, subject_id, field_name,
        str(rung) if rung else "-", outcome.value, authority, prev,
    ])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Log:
    """An append-only chain. Every operation returns a new `Log`."""

    entries: tuple = ()

    @property
    def head(self) -> str:
        return self.entries[-1].digest if self.entries else GENESIS

    def record(self, serving: Serving, *, principal_id: str, subject_id: str,
               field_name: str, at: datetime, authority: str = "") -> "Log":
        """Append one decision.

        **Every outcome is recorded, including refusals and unknowns.** An
        audit trail that logs only disclosures cannot answer *"was this
        restriction working"*, and rule 10 is explicit that an audit trail
        which logs only agreement is not one.
        """
        prev = self.head
        e = Entry(
            occurred_at=at, principal_id=principal_id, subject_id=subject_id,
            field_name=field_name, rung=serving.rung, outcome=serving.outcome,
            authority=authority or (serving.via_edge or ""), prev=prev,
            digest=_digest(at, principal_id, subject_id, field_name,
                           serving.rung, serving.outcome, authority or (serving.via_edge or ""),
                           prev),
        )
        return Log(self.entries + (e,))

    # --- verification ------------------------------------------------------

    def verify(self) -> tuple:
        """`(ok, reason)`. Detects edit, reorder, and truncation.

        Truncation is the one a chain alone misses: lopping entries off the end
        leaves a perfectly valid shorter chain. PR #3's count anchor is the
        answer — the length is part of what an external observer pins — so
        :meth:`anchor` exists and :func:`verify_against` uses it.
        """
        prev = GENESIS
        for i, e in enumerate(self.entries):
            if e.prev != prev:
                return (False, f"entry {i} does not follow its predecessor")
            expected = _digest(e.occurred_at, e.principal_id, e.subject_id,
                               e.field_name, e.rung, e.outcome, e.authority, e.prev)
            if e.digest != expected:
                return (False, f"entry {i} has been altered")
            prev = e.digest
        return (True, f"{len(self.entries)} entries, chain intact")

    def anchor(self) -> tuple:
        """`(head, count)` — what an external observer pins periodically."""
        return (self.head, len(self.entries))


def verify_against(log: Log, anchor: tuple) -> tuple:
    """Verify a log against a previously published anchor.

    Catches the truncation a self-consistent chain cannot: a log shortened to
    hide a disclosure still verifies internally, and fails here because the
    count no longer matches what was anchored.
    """
    ok, why = log.verify()
    if not ok:
        return (False, why)
    head, count = anchor
    if len(log.entries) < count:
        return (False, f"truncated: {count} entries were anchored, {len(log.entries)} remain")
    if count and log.entries[count - 1].digest != head:
        return (False, "the anchored entry is no longer at that position")
    return (True, "chain intact and consistent with the anchor")


# --- per-lane partitioning (§5, W-1) ---------------------------------------


class UnknownLane(LookupError):
    """Asked for the chain of a lane this ledger has never heard of.

    *Empty* and *unknown* are different facts: an empty chain says nobody has
    read this lane; an unknown lane says the ledger cannot speak for it at
    all. Answering the second with the first is how a student gets told nobody
    has read them by a ledger that was never asked (rule 13; §18 item 16,
    decided strict 2026-07-31)."""


@dataclass(frozen=True)
class Ledger:
    """One chain per lane, because §5 says so and the first version did not.

    *"Any new chained artifact in this system — **the disclosure log**, the
    egress log of §6, adjudication commentary — inherits all three
    requirements: **per-subject partitioning**, fail-closed on unscoped access,
    and an anchor that distinguishes emptied from never-written."*

    The first `Log` here was a single global chain carrying a `subject_id` per
    entry, which satisfies none of that. Two things go wrong with it:

    * **W-1 requires a separate audit trail per lane**, not one trail with a
      column naming which student a row is about. That is rule 8's
      roster-column shape in the audit table.
    * **Positions leak.** A guardian holding receipts for global positions 5,
      12 and 40 learns there were thirty-four entries about other children in
      between. Per-lane chains make a position mean *"the nth thing about your
      child"* and nothing else, which is what makes a receipt safe to hand over.

    Found by building `records/receipts.py`, two hours after shipping the
    global version.
    """

    lanes: tuple = ()  # ((lane_id, Log), ...) — a tuple so the Ledger stays frozen

    def _index(self) -> dict:
        return dict(self.lanes)

    def log_for(self, lane_id: str) -> Log:
        """The lane's chain. A lane with no entries yet is an empty chain, not
        an error — but a lane this ledger has *never heard of* is neither, and
        until 2026-07-31 the two returned the same object.

        **Strict by maintainer decision (§18 item 16).** The empty answer was
        served rather than refused: `own_log` rendered it GRANTED and complete,
        so a lane missing from the ledger read as *nobody has ever read you* —
        told by a ledger that was never asked — and `receipts.issue` handed a
        guardian nothing without saying so. Absence surfaces as its own state
        (rule 13), so an unknown lane raises rather than answering.
        """
        index = self._index()
        if lane_id not in index:
            raise UnknownLane(
                f"this ledger has no chain for lane {lane_id!r}. A lane with no "
                "entries is an empty chain; a lane the ledger never heard of is "
                "not an answer, and serving an empty log for it would render "
                "absence as 'nobody has ever read you'")
        return index[lane_id]

    def knows(self, lane_id: str) -> bool:
        """Whether this ledger carries a chain for the lane — the question a
        caller asks before `log_for`, so *unknown* is handled where it can be
        told apart from *empty*, not swallowed where it cannot."""
        return lane_id in self._index()

    def record(self, serving, *, lane_id: str, principal_id: str, subject_id: str,
               field_name: str, at: datetime, authority: str = "") -> "Ledger":
        by_lane = self._index()
        # The write path is the one place an unknown lane is legitimate: W-1
        # opens the lane at the first write. Reads stay strict.
        by_lane[lane_id] = by_lane.get(lane_id, Log()).record(
            serving, principal_id=principal_id, subject_id=subject_id,
            field_name=field_name, at=at, authority=authority)
        return Ledger(tuple(sorted(by_lane.items())))

    def verify(self) -> tuple:
        for lane_id, log in self.lanes:
            ok, why = log.verify()
            if not ok:
                return (False, f"lane {lane_id}: {why}")
        return (True, f"{len(self.lanes)} lane(s), all chains intact")

    def anchors(self) -> tuple:
        """One anchor per lane. Publishing these individually would leak which
        lanes exist; the caller anchors the *ledger*, not the lanes."""
        return tuple((lane_id, log.anchor()) for lane_id, log in self.lanes)
