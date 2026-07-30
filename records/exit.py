"""W-6: a lane opened without a written exit is invalidly opened.

The clause, at source in `Willow`'s `PROTECTED_AGENTS.md` Part III (`c8c96b4`):

> *"At the threshold written into the office at entry — majority, graduation,
> transfer, retirement — keys to the lane issue to its subject or named
> successor, full history intact; the guardian's standing ends or reduces to
> what the new owner grants back. An agent retired is retired **with** its
> record. **A lane opened without a written exit is invalidly opened.**"*

**The exit is enforced at opening, not at graduation.** That sentence is the
whole design: by the time a student graduates it is far too late to discover
nobody wrote down what leaving means. So `open_lane()` requires `exit_terms`
and a threshold, and there is no way to construct a `Lane` without them.

§18 item 5 records that the program-level exit line is still unwritten and
§11.1 requires it before the first install. This is the *per-graduate* half,
which W-6 additionally requires and which §7.4 calls the harder of the two —
*"a system that can export a whole program but cannot hand one graduate their
own past has satisfied the smaller obligation and missed the larger one."*

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence, Tuple

from .rungs import Rung
from .serving import Edge


class Threshold(Enum):
    MAJORITY = "majority"
    GRADUATION = "graduation"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"


@dataclass(frozen=True)
class Lane:
    """A student's lane (W-1), which cannot exist without its exit."""

    lane_id: str
    subject_id: str
    opened_at: datetime
    threshold: Threshold
    exit_terms: str

    def __post_init__(self):
        if not (self.exit_terms or "").strip():
            raise ValueError(
                "a lane opened without a written exit is invalidly opened (W-6)"
            )


def open_lane(lane_id: str, subject_id: str, *, at: datetime,
              threshold: Threshold, exit_terms: str) -> Lane:
    """Open a lane. Both exit arguments are required and keyword-only."""
    return Lane(lane_id, subject_id, at, threshold, exit_terms)


@dataclass(frozen=True)
class Transfer:
    """What leaves at the threshold, and what happens to the old standing."""

    lane_id: str
    to_whom: str
    at: datetime
    threshold: Threshold
    entries: Tuple          # the whole history, unredacted
    highest_rung: Optional[Rung]
    ended_edges: Tuple      # standing that ends, as (kind, principal), never deleted
    exit_terms: str

    @property
    def complete(self) -> bool:
        return bool(self.entries) and bool(self.exit_terms.strip())


def transfer(lane: Lane, *, entries: Sequence, edges: Sequence[Edge],
             at: datetime, to: Optional[str] = None) -> Transfer:
    """Issue the lane to its subject (or a named successor) at the threshold.

    **Full history intact.** Nothing is filtered by rung on the way out: the
    subject is receiving their own past, and a "safe subset" export is the
    thing W-6 exists to forbid — *an agent retired is retired with its record.*

    **Standing ends; it is not deleted.** The returned `ended_edges` are what
    the caller must terminate by setting `invalid_at` (refusal 3). This function
    does not mutate them, because a transfer that silently rewrote the edge
    table would leave no dated record of the handover.
    """
    if not entries:
        raise ValueError(
            "a transfer with no history is not a transfer; W-6 requires the record"
        )
    recipient = to or lane.subject_id
    ending = tuple(
        (e.kind, e.principal_id) for e in edges
        if e.subject_id == lane.subject_id
        and e.principal_id != recipient
        and e.live_at(at)
    )
    rungs = [getattr(x, "rung", None) for x in entries]
    highest = max((r for r in rungs if r is not None),
                  key=lambda r: ("L1", "L2", "L3", "L4", "L5").index(str(r)),
                  default=None)
    return Transfer(lane.lane_id, recipient, at, lane.threshold, tuple(entries),
                    highest, ending, lane.exit_terms)
