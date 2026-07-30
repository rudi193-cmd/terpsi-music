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
