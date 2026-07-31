"""D-4 — who gets a drop: the dated-guardianship predicate, on the prepare path.

`docs/PLAN-DROP.md` D-4. A drop is prepared for whoever `records/sending.py`
derives as reachable, and for nobody else. This module reuses that predicate
whole (§16 — a second who-may-be-told would be the pair this project forbids):
`recipients()` applies §7.1's dated guardianship and the `ContactRestriction`,
and this decides *for whom a drop is prepared* by consuming its answer.

**No `to` parameter, and it must never grow one (D-4's forbidden act).** Like
`records/sending.py::deliver`, `prepare()` takes a subject and derives the set;
there is nowhere to hand it a restricted or lapsed guardian, so preparing a drop
for one is not a runtime refusal but an unrepresentable request.
`tests/test_drop_preparing.py` asserts that over the signature, the way
`test_sending.py` asserts G4.

**A restricted or lapsed guardian is absent from the prepared set** — because
`recipients()` excludes them, and this consumes the **allowed** list, never the
suppressed one. Reintroducing the suppressed is the mutation the suite catches.

**Fail-closed on an unknown source (rule 13).** If the restriction or
guardianship source could not be consulted, `recipients()` returns `UNKNOWN`, and
a `Prepared` set built from it iterates as a *refusal*, never as an empty set —
the `records/sending.py::SendList` shape, carried one layer up. A drop prepared
for nobody because a backend was down must not be indistinguishable from a
student with no reachable guardians.

Stdlib and `records/`. No network, no store, no model, no filesystem.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.sending import ContactRestriction, Standing, recipients  # noqa: E402
from records.serving import Edge  # noqa: E402


@dataclass(frozen=True)
class Prepared:
    """One drop, prepared for one reachable guardian about one student.

    Carries the guardian it is for and the sealed payload the producer made for
    them (`drop/producer.py`). It does **not** carry a mailbox address a caller
    chose — reachability decided the guardian, and the guardian decides the
    mailbox downstream; there is no `to` for a caller to override.
    """

    guardian_id: str
    payload: object  # a drop/producer.Production, or whatever seal_for returns


@dataclass(frozen=True)
class PreparedDrops:
    """The prepared set. **Empty is meaningful only when the state is DERIVED.**

    `records/sending.py::SendList` for drops: iterating an `UNKNOWN` set raises
    rather than yielding nothing, so a caller looping `for d in prepare(...)`
    cannot silently prepare no drops because a backend was down.
    """

    state: Standing
    drops: tuple
    suppressed: tuple
    reason: str

    def __iter__(self):
        if self.state is not Standing.DERIVED:
            raise RuntimeError(
                f"the prepared set is {self.state.value}, not derived: "
                f"{self.reason}. An unknown set is not an empty one (rule 13)")
        return iter(self.drops)


def prepare(subject_id: str, edges: Sequence[Edge],
            restrictions: Sequence[ContactRestriction] | Callable,
            at: datetime, *, seal_for: Callable[[str], object]) -> PreparedDrops:
    """Prepare a drop for every guardian reachable about `subject_id` at `at`.

    **No recipient parameter, and none may be added** (D-4's forbidden act,
    checked statically by the suite). The reachable set is derived here, at the
    point of preparing, from `recipients()` — so there is no window between
    deriving and using in which an order could arrive, and no `to` a caller could
    supply to reach past the predicate.

    `seal_for(guardian_id)` produces the payload for one reachable guardian
    (`drop/producer.py::produce` bound to that guardian's view). It is called
    only for guardians the predicate allowed; a suppressed guardian never reaches
    it, which is why *the producer cannot be handed a restricted recipient*.
    """
    who = recipients(subject_id, edges, restrictions, at)
    if who.state is not Standing.DERIVED:
        # Fail-closed: the source could not be consulted. Carry the UNKNOWN up so
        # the set refuses to iterate, rather than preparing an empty set that
        # reads as "no reachable guardians" (rule 13).
        return PreparedDrops(who.state, (), (), who.reason)
    reachable = tuple(who)                       # allowed only; never the suppressed
    drops = tuple(Prepared(guardian_id, seal_for(guardian_id))
                  for guardian_id in reachable)
    return PreparedDrops(Standing.DERIVED, drops, who.suppressed, who.reason)
