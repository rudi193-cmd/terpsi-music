"""Guardian receipts: the only witness whose interest is adverse to the institution's.

§18 item 15 asks who witnesses the anchor. Every external candidate — a
timestamp authority, a public chain, certified mail — is a *neutral* party. This
one is not neutral, and that is the point: **a guardian's interest is
structurally opposed to the institution's**, and a receipt in a parent's hands
cannot be collected back.

**What a receipt is.** When something is written into a student's lane, every
guardian with live standing gets a small artifact naming the lane, the position
in that lane's chain, the entry digest and the time. They keep it. Nothing
about the entry's *content* travels — the digest is opaque, and the receipt is
about the fact of a record existing.

**What makes it strong, and it is stronger than a neutral witness in one way.**
Positions are per-lane (`Ledger`, §5's partitioning), so a position means *"the
nth thing about your child"*. A guardian holding receipts for positions 1, 2, 3
and 5 can see that **4 is missing** — without the institution's cooperation,
without a third party, and without knowing anything about any other student.
Sequence gaps are detectable *by the counterparty*, which is not true of any
anchor.

**What makes it weak, and it is fatal on its own.** An entry the institution
never wrote produces no receipt, and its absence is invisible: a guardian
holding 1..N cannot tell whether N is everything. Receipts detect *removal*,
never *omission*. They corroborate; they do not stand alone.

**On authenticity.** Issuance is HMAC-tagged so the institution can verify its
own receipts and a mismatch between a held receipt and the institution's log is
a contradiction it must explain. This is deliberately *not* a signature a third
party can attribute — the stdlib has no asymmetric primitive, and claiming
non-repudiation from an HMAC would be the overclaim this repository keeps
catching. A real deployment wants Ed25519 here; the evidentiary weight until
then comes from **distribution and adversity**, not from unforgeable maths.

Stdlib only. No network.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence, Tuple

from .disclosure import Entry, Ledger, Log
from .serving import Edge


@dataclass(frozen=True)
class GuardianReceipt:
    """What a guardian keeps. Opaque about content, precise about existence."""

    lane_id: str
    position: int          # 1-based, within this lane only
    entry_digest: str
    issued_at: datetime
    to_guardian: str
    tag: str               # HMAC over the above; see the module note

    def matches(self, entry: Entry) -> bool:
        return entry.digest == self.entry_digest


def _tag(key: bytes, lane_id: str, position: int, digest: str,
         issued_at: datetime, to_guardian: str) -> str:
    material = "\x1f".join([lane_id, str(position), digest,
                            issued_at.isoformat(), to_guardian])
    return hmac.new(key, material.encode("utf-8"), hashlib.sha256).hexdigest()


def issue(ledger: Ledger, lane_id: str, subject_id: str, edges: Sequence[Edge],
          at: datetime, key: bytes) -> Tuple[GuardianReceipt, ...]:
    """Receipts for the newest entry in `lane_id`, to guardians with standing.

    **Standing, not reachability.** A guardian under a contact restriction may
    not be *messaged* (`records/sending.py`), and that is a question about
    delivery. Whether they still hold records standing is a different question
    with a different answer, and conflating them here would let a contact
    restriction quietly revoke someone's ability to audit their own child's
    record. Delivery is the caller's problem; this decides who is owed one.
    """
    log = ledger.log_for(lane_id)
    if not log.entries:
        return ()
    position = len(log.entries)
    entry = log.entries[-1]
    out = []
    for e in edges:
        if e.kind != "guardian_of" or e.subject_id != subject_id:
            continue
        if not e.live_at(at):
            continue
        out.append(GuardianReceipt(
            lane_id, position, entry.digest, at, e.principal_id,
            _tag(key, lane_id, position, entry.digest, at, e.principal_id)))
    return tuple(out)


def authentic(receipt: GuardianReceipt, key: bytes) -> bool:
    """Whether this receipt carries a tag this issuer would have produced."""
    return hmac.compare_digest(
        receipt.tag,
        _tag(key, receipt.lane_id, receipt.position, receipt.entry_digest,
             receipt.issued_at, receipt.to_guardian))


def held_by(receipts: Sequence[GuardianReceipt], guardian_id: str,
            lane_id: Optional[str] = None) -> Tuple[GuardianReceipt, ...]:
    return tuple(sorted(
        (r for r in receipts
         if r.to_guardian == guardian_id and (lane_id is None or r.lane_id == lane_id)),
        key=lambda r: r.position))


def gaps(receipts: Sequence[GuardianReceipt]) -> Tuple[int, ...]:
    """Positions missing from a guardian's own sequence.

    **The property no anchor gives.** Holding 1, 2, 3, 5 proves 4 existed and
    is gone, without the institution's cooperation and without learning
    anything about any other student. Detectable by the counterparty, which is
    what makes an adverse witness worth having.

    Requires the receipts to be for one lane and one guardian; mixing either
    would compare sequences that are not sequences.
    """
    if not receipts:
        return ()
    lanes = {r.lane_id for r in receipts}
    holders = {r.to_guardian for r in receipts}
    if len(lanes) > 1 or len(holders) > 1:
        raise ValueError(
            "gaps() needs one lane and one guardian; positions are per-lane and "
            "a mixed sequence has no meaningful holes"
        )
    seen = {r.position for r in receipts}
    return tuple(p for p in range(1, max(seen) + 1) if p not in seen)


def contradictions(log: Log, receipts: Sequence[GuardianReceipt]) -> Tuple[str, ...]:
    """Where a guardian's held receipts disagree with the institution's log.

    Three shapes, and the first is the one that matters: a receipt for a
    position the log no longer reaches means an entry was removed after it was
    receipted.
    """
    out = []
    for r in sorted(receipts, key=lambda r: r.position):
        if r.position > len(log.entries):
            out.append(f"position {r.position} was receipted and the log now ends at "
                       f"{len(log.entries)}")
            continue
        entry = log.entries[r.position - 1]
        if not r.matches(entry):
            out.append(f"position {r.position} holds a different entry than the "
                       "receipt issued for it")
    return tuple(out)
