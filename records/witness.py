"""Where the anchor lives, and who has to believe it.

§5 specifies the count anchor and stops: *"a **surviving** anchor beside missing
rows reads as tampered, not absent."* Surviving where? An anchor in the same
vault as the chain dies with it, and one act makes the log read as
never-written. The architecture has the anchor and not the anchoring.

**The property this buys is anteriority.** Not confidentiality, not integrity —
the chain already gives those. This is the narrower and harder claim that *an
entry existed on a date and could not have been written later*, which is the
only thing that survives an institution saying *"that's his log, he built it,
he can make it say anything."*

**An anchor is a digest, a count and a time.** There is nothing in it to leak —
no name, no rung, no subject — which is why this is the one operation in the
design that may legitimately cross the egress boundary. The core decides *what*
to anchor and *when*; a seam does the publishing, per §6's core/seam partition.
Nothing in this module opens a socket.

**Cadence is fixed, not activity-driven.** `corpus-lens` is the argument:
*"content redaction does not scrub the shape of a week."* Anchors published
whenever something happens are a metadata channel — a count that jumps the week
of an incident is a signal. So the schedule comes from the calendar and anchors
are due whether or not anything was written, exactly as §4.2 already requires of
the drop.

**What this does not prove** is written down in `tests/test_witness.py` rather
than left for someone to discover: anchoring proves what was written existed.
It cannot prove everything was written.

Stdlib only. No network.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Protocol, Sequence, Tuple

from .disclosure import Log


@dataclass(frozen=True)
class Anchor:
    """What gets published. Deliberately incapable of carrying anything else."""

    head: str
    count: int
    at: datetime

    def __post_init__(self):
        if len(self.head) != 64 or any(c not in "0123456789abcdef" for c in self.head):
            raise ValueError("an anchor's head must be a sha256 digest")
        if self.count < 0:
            raise ValueError("an anchor's count cannot be negative")


def anchor_for(log: Log, at: datetime) -> Anchor:
    head, count = log.anchor()
    return Anchor(head, count, at)


class Independence(Enum):
    """Whether a witness's receipt is worth anything against an adversary."""

    EVIDENTIARY = "evidentiary"          # outside the author's control
    NON_EVIDENTIARY = "non_evidentiary"  # useful in development, proves nothing


@dataclass(frozen=True)
class Receipt:
    """Proof a witness accepted an anchor. The thing you keep."""

    anchor: Anchor
    witness_kind: str
    witness_ref: str          # OTS proof path, TSA serial, certified-mail number
    accepted_at: datetime
    independence: Independence = Independence.EVIDENTIARY


class Witness(Protocol):
    """The publication seam. Implementations live outside the core (§6)."""

    kind: str
    independence: Independence

    def publish(self, anchor: Anchor) -> Receipt: ...


@dataclass
class RecordingWitness:
    """A witness that keeps receipts in memory. **Proves nothing.**

    Present so the cadence and standing logic can be exercised without a
    network, and marked `NON_EVIDENTIARY` so it cannot be counted as
    corroboration by accident — which is the failure mode a convenient test
    double invites.
    """

    kind: str = "local"
    independence: Independence = Independence.NON_EVIDENTIARY
    receipts: list = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.receipts is None:
            self.receipts = []

    def publish(self, anchor: Anchor) -> Receipt:
        r = Receipt(anchor, self.kind, f"local:{len(self.receipts)}",
                    anchor.at, self.independence)
        self.receipts.append(r)
        return r


# --- cadence ---------------------------------------------------------------


def schedule(start: datetime, end: datetime, every: timedelta) -> Tuple[datetime, ...]:
    """Anchor times between `start` and `end`, derived from the calendar.

    Deliberately takes no log. A schedule computed from activity is the leak
    `corpus-lens` describes; this one is the same whether the program had a
    championship or a quiet fortnight.
    """
    if every <= timedelta(0):
        raise ValueError("a cadence must be positive")
    out, t = [], start
    while t <= end:
        out.append(t)
        t += every
    return tuple(out)


def missing(receipts: Sequence[Receipt], start: datetime, end: datetime,
            every: timedelta, *, tolerance: Optional[timedelta] = None) -> Tuple[datetime, ...]:
    """Scheduled anchors with no receipt near them.

    A gap is evidentiarily meaningful in both directions: either nothing was
    anchored, or an anchor was suppressed. Reporting it is the point — a
    witness log with holes that nobody notices is the same as none.
    """
    tol = tolerance if tolerance is not None else every / 2
    times = [r.anchor.at for r in receipts]
    return tuple(due for due in schedule(start, end, every)
                 if not any(abs((t - due).total_seconds()) <= tol.total_seconds()
                            for t in times))


# --- standing --------------------------------------------------------------


class Standing(Enum):
    UNWITNESSED = "unwitnessed"  # a log nobody outside has ever seen
    WITNESSED = "witnessed"
    TAMPERED = "tampered"        # the log contradicts a receipt
    GAPPED = "gapped"            # witnessed, with scheduled anchors missing


@dataclass(frozen=True)
class Evidence:
    standing: Standing
    reason: str
    witnessed_to: int = 0        # entries covered by the strongest receipt
    corroborating_witnesses: int = 0

    @property
    def is_evidence(self) -> bool:
        return self.standing is Standing.WITNESSED and self.corroborating_witnesses > 0


def standing(log: Log, receipts: Sequence[Receipt], *,
             start: Optional[datetime] = None, end: Optional[datetime] = None,
             every: Optional[timedelta] = None) -> Evidence:
    """What this log is worth against someone who says you wrote it yesterday.

    **An unwitnessed log is not evidence and must not read as fine.** Rule 13's
    shape: there is no path through this function that returns `WITNESSED` for a
    log nobody outside has ever seen.
    """
    ok, why = log.verify()
    if not ok:
        return Evidence(Standing.TAMPERED, f"the chain itself: {why}")

    evidentiary = [r for r in receipts
                   if r.independence is Independence.EVIDENTIARY]
    if not evidentiary:
        held = "no receipts at all" if not receipts else (
            f"{len(receipts)} receipt(s), all non-evidentiary")
        return Evidence(Standing.UNWITNESSED,
                        f"{held}; a record its author controls proves nothing about when "
                        "it was written")

    for r in evidentiary:
        if len(log.entries) < r.anchor.count:
            return Evidence(Standing.TAMPERED,
                            f"{r.witness_kind} witnessed {r.anchor.count} entries; "
                            f"{len(log.entries)} remain")
        if r.anchor.count and log.entries[r.anchor.count - 1].digest != r.anchor.head:
            return Evidence(Standing.TAMPERED,
                            f"the entry {r.witness_kind} witnessed is no longer at "
                            "that position")

    best = max(r.anchor.count for r in evidentiary)
    kinds = len({r.witness_kind for r in evidentiary})

    if start is not None and end is not None and every is not None:
        gaps = missing(evidentiary, start, end, every)
        if gaps:
            return Evidence(Standing.GAPPED,
                            f"{len(gaps)} scheduled anchor(s) have no receipt; the first "
                            f"is {gaps[0].isoformat()}", best, kinds)

    return Evidence(Standing.WITNESSED,
                    f"{best} entries witnessed by {kinds} independent witness(es)",
                    best, kinds)
