"""§7.1's dated guardianship, bound to the thing that ends it.

**The mechanism existed and nothing was attached to it.** §14's row is exact:
*"`valid_at`/`invalid_at` — VERIFIED at `4147013`, 17 tables… **Mechanism
exists**; binding guardianship to it does not."* `records/serving.py` has
carried the dated `Edge` since the first commit and every predicate reads
`live_at`; what no module had was the **act** — the arrival of a court order,
mid-season, from outside, against one guardian and not the other.

Without it, ending a guardianship in this tree meant hand-building an `Edge`
with an `invalid_at` on it. That works and it is also the whole problem: the
date arrives with no authority recorded, no second clock, and nothing checking
what the lane looks like afterwards. A hand-built ending is indistinguishable
from a typo.

**Four properties, each of which is a refusal somewhere below.**

* **It ends by date, never by removal** (refusal 3, §7.1). :func:`end_guardianship`
  returns a graph that is **never shorter** than the one it was given — the same
  rows, one of them dated closed. The count is asserted rather than intended.
* **The order is the authority.** `Edge.ended_by` is set from the order and an
  ending with no authority is refused at issuance. *"Who could see Ben's medical
  form on October 12, and why"* has to answer for the ending too, not only for
  the standing.
* **Both clocks.** The order dated 14 March and delivered 2 October sets
  `invalid_at` to **March** and `ended_known_at` to **October**. A June
  disclosure was compliant on what was known and wrong on what was true, and
  `Edge.live_as_known_at` is how an audit asks the second question without
  losing the first.
* **The lane is never left in silence** (I-6, and task 3's asymmetry). After
  any ending the lane holds either a live `guardian_of` edge or an explicit,
  named, dated :class:`NoGuardian` declaration. *No guardian and nobody said so*
  is `UNKNOWN`, and `UNKNOWN` is not a state a court order may leave behind.

**What an `Order` deliberately cannot hold.** Its findings. `docs/LANE-MODEL.md`
step 5: *"The order's contents are `L5` — enforced, never rendered, including to
the director. The system stores the effect. Nobody in a band program needs the
findings."* There is no `contents`, `findings`, `text` or `body` field here and
`tests/test_orders.py` asserts their absence, because the way this field arrives
is somebody helpfully pasting the PDF.

Stdlib only. No network, no store.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence, Tuple

from .crossing import _NOT_A_PERSON
from .serving import Edge

GUARDIAN_OF = "guardian_of"


class OrderKind(Enum):
    ENDS = "ends_guardianship"
    SUPERSEDES = "supersedes_guardianship"


@dataclass(frozen=True)
class NoGuardian:
    """The explicit named state a lane with no live guardian must carry.

    I-6's *"silence is not a disposition"* applied to a lane rather than to a
    request. A student whose only guardian's standing has ended is in a real
    situation — a ward of the state, a transfer between households, an
    eighteenth birthday that has not arrived — and every one of those is a
    thing somebody can name. What must not exist is the fourth case: no
    guardian, and no record of why.
    """

    subject_id: str
    reason: str
    declared_by: str
    declared_at: datetime

    def __post_init__(self):
        if not (self.reason or "").strip():
            raise ValueError(
                "a lane left with no guardian and no reason is silence, not a state (I-6)"
            )
        name = (self.declared_by or "").strip()
        if not name or name.lower() in _NOT_A_PERSON:
            raise ValueError(
                f"{self.declared_by!r} is not a person; a lane's state is declared "
                "by somebody, not by a role"
            )


@dataclass(frozen=True)
class Order:
    """A court order, as its effect. Never as its contents.

    `effective_at` and `received_at` are §7.1's two axes and neither is derived
    from the other. **No ordering is imposed between them**, and that is
    deliberate in both directions: an order dated in March and delivered in
    October has `effective_at < received_at`, and a restriction that takes
    effect at the end of term has `effective_at > received_at`. A CHECK
    forbidding either would forbid a real order.
    """

    order_id: str
    authority: str          # the issuing instrument, named. Never a machine.
    subject_id: str
    principal_id: str       # whose guardianship this order ends
    effective_at: datetime  # when it took effect in the world
    received_at: datetime   # when this system learned of it
    kind: OrderKind = OrderKind.ENDS
    successor_id: Optional[str] = None
    declares: Optional[NoGuardian] = None

    def __post_init__(self):
        name = (self.authority or "").strip()
        if not name or name.lower() in _NOT_A_PERSON:
            raise ValueError(
                f"{self.authority!r} is not an authority; an ending with none recorded "
                "is a date nobody can answer for (§7.1, refusal 3)"
            )
        if not (self.subject_id or "").strip():
            raise ValueError("an order names the ward whose lane it reaches (W-2)")
        if not (self.principal_id or "").strip():
            raise ValueError("an order names the guardian whose standing it ends")
        if self.principal_id == self.subject_id:
            raise ValueError(
                "this ends a guardianship, and a subject is not their own guardian; "
                "a self edge ends by its own act, not by an order against a guardian"
            )
        if self.kind is OrderKind.SUPERSEDES and not (self.successor_id or "").strip():
            raise ValueError(
                "a superseding order names the guardianship that replaces the one it "
                "ends; supersession by nobody is an ending (I-7)"
            )
        if self.successor_id is not None:
            if self.successor_id == self.principal_id:
                raise ValueError(
                    "an order cannot supersede a guardianship with itself"
                )
            if self.successor_id == self.subject_id:
                raise ValueError(
                    "a ward is not their own successor guardian (W-4)"
                )
        if self.declares is not None and self.declares.subject_id != self.subject_id:
            raise ValueError(
                "the declared state names a different lane than the order does"
            )


# --- the result -------------------------------------------------------------


class Ended(Enum):
    APPLIED = "applied"
    REFUSED = "refused"
    UNKNOWN = "unknown"   # not an ending, and not a no-op (rule 13)


class GuardianshipState(Enum):
    GUARDED = "guarded"
    UNGUARDED = "unguarded"   # explicitly, with a named reason and a namer
    UNKNOWN = "unknown"       # nobody said; not a state (rule 13, I-6)


@dataclass(frozen=True)
class Guardianship:
    """Who holds guardianship of one lane at one instant, or why nobody does."""

    state: GuardianshipState
    guardians: Tuple[str, ...]
    reason: str
    declared_by: str = ""

    def __iter__(self):
        """Iterating an `UNKNOWN` guardianship raises rather than yielding nothing.

        `sending.SendList`'s shape, for the same reason: *no guardians* and *we
        could not tell* must not both arrive as `()`, because the loop that
        consumes them cannot distinguish an orphaned lane from a quiet one.
        """
        if self.state is GuardianshipState.UNKNOWN:
            raise RuntimeError(
                f"guardianship of this lane is unknown, not empty: {self.reason}"
            )
        return iter(self.guardians)


@dataclass(frozen=True)
class Ending:
    """What an order did, and the graph it produced.

    `after` is reachable only through iteration, and iteration raises unless the
    order applied — the same discipline `SendList` uses. A caller that ignores a
    `REFUSED` ending and carries on with its old edge list is doing the thing
    this type exists to make noisy.
    """

    state: Ended
    order: Order
    ended: Tuple[Edge, ...]
    after: Tuple[Edge, ...]
    standing: Guardianship
    reason: str

    @property
    def applied(self) -> bool:
        return self.state is Ended.APPLIED

    def __iter__(self):
        if self.state is not Ended.APPLIED:
            raise RuntimeError(
                f"this order is {self.state.value}, not applied: {self.reason}"
            )
        return iter(self.after)


# --- the predicates ---------------------------------------------------------


def guardianship_of(edges: Sequence[Edge], subject_id: str, at: datetime,
                    declarations: Sequence[NoGuardian] = ()) -> Guardianship:
    """Who guards this lane at `at` — or the named reason nobody does.

    The third answer is the point. A lane with no live `guardian_of` edge and no
    declaration is `UNKNOWN`, which is neither *guarded* nor *unguarded*: it is
    a lane somebody stopped answering about. I-7's supersession asymmetry is
    what makes that reachable — an office may end its own standing, and if
    ending it were allowed to leave nothing behind, the office could dissolve
    the record of its own exercise by walking away from the lane.
    """
    live = tuple(sorted({
        e.principal_id for e in edges
        if e.kind == GUARDIAN_OF and e.subject_id == subject_id and e.live_at(at)
    }))
    if live:
        return Guardianship(
            GuardianshipState.GUARDED, live,
            f"{len(live)} guardian(s) with live standing at {at.isoformat()}")

    said = [d for d in declarations
            if d.subject_id == subject_id and d.declared_at <= at]
    if said:
        latest = max(said, key=lambda d: d.declared_at)
        return Guardianship(
            GuardianshipState.UNGUARDED, (),
            f"no live guardian, declared: {latest.reason}", latest.declared_by)

    return Guardianship(
        GuardianshipState.UNKNOWN, (),
        "this lane has no live guardian and no declared state; silence is not a "
        "state (I-6), and a lane nobody answers for is not an unguarded one")


def end_guardianship(edges: Sequence[Edge], order: Order) -> Ending:
    """Apply `order` — set `invalid_at`, record the authority, keep every row.

    The forbidden alternative is one line shorter and this function exists so
    that nobody writes it: dropping the guardian's row leaves no dated record,
    and *"who could see this on October 12, and why"* becomes unanswerable for
    the one case where a court may actually ask (§7.1).

    Three refusals, in order:

    * **an order against a guardianship this graph does not hold** is `UNKNOWN`,
      not a no-op. A caller receiving `()` from a delete-shaped API cannot tell
      *ended* from *never existed*, and here the second is a data problem
      somebody must look at rather than a job well done.
    * **an order against a standing that already ended** is `UNKNOWN` for the
      same reason, and does not silently move the earlier date. Moving it would
      be the ledger lying about when the restriction began.
    * **an ending that would leave the lane in `UNKNOWN`** is `REFUSED`. The
      order must carry a :class:`NoGuardian` declaration, or leave at least one
      live guardian behind.
    """
    ended, after = [], []
    for e in edges:
        matches = (e.kind == GUARDIAN_OF
                   and e.principal_id == order.principal_id
                   and e.subject_id == order.subject_id
                   and e.invalid_at is None)
        if matches:
            closed = dataclasses.replace(
                e,
                invalid_at=order.effective_at,
                ended_by=f"{order.authority} ({order.order_id})",
                ended_known_at=order.received_at,
            )
            ended.append(closed)
            after.append(closed)
        else:
            after.append(e)

    # Refusal 3, asserted rather than intended. Every row that went in comes
    # out; one of them changed shape.
    if len(after) != len(edges):
        raise AssertionError(
            "an ending changed the size of the graph; standing ends by date "
            "and never by removal (refusal 3)"
        )

    if not ended:
        return Ending(
            Ended.UNKNOWN, order, (), tuple(after),
            guardianship_of(edges, order.subject_id, order.effective_at,
                            (order.declares,) if order.declares else ()),
            f"no live guardian_of edge from {order.principal_id} to "
            f"{order.subject_id}; this order names a guardianship this graph does "
            "not hold, which is a fact to look at rather than a no-op")

    declarations = (order.declares,) if order.declares is not None else ()
    standing = guardianship_of(after, order.subject_id, order.effective_at,
                               declarations)
    if standing.state is GuardianshipState.UNKNOWN:
        return Ending(
            Ended.REFUSED, order, (), tuple(edges), standing,
            "this order would leave the lane with no live guardian and no declared "
            "state; a lane is never left in silence (I-6). Carry a NoGuardian "
            "declaration on the order, or name a successor")

    return Ending(
        Ended.APPLIED, order, tuple(ended), tuple(after), standing,
        f"{len(ended)} guardian_of edge(s) dated closed at "
        f"{order.effective_at.isoformat()} under {order.authority}, learned "
        f"{order.received_at.isoformat()}; {standing.reason}")


def supersede(edges: Sequence[Edge], order: Order, *,
              successor_valid_at: Optional[datetime] = None) -> Ending:
    """A superseding order: one guardianship ends and another begins.

    **I-7's supersession asymmetry, worked.** The invariant is not *"guardianship
    may not end"* — it ends all the time, and W-6 says a guardianship that
    cannot end was never guardianship. What I-7 forbids is an office ending its
    own standing in a way that **erases the record of its own exercise**, and
    the shape that does that is the orphan: the last guardian's edge dated
    closed, no successor, no declaration, and a lane nobody answers for. The
    ex-guardian's past exercise is then recorded against a lane with no live
    party who can be asked about it.

    So supersession has to land the successor **in the same act**. The successor
    edge is added before the lane's state is computed, which is why this cannot
    be *"end, then remember to add"*: a two-step version leaves the lane in
    `UNKNOWN` between the steps, and that window is a crash away from being
    permanent.

    The successor's standing begins at the order's `effective_at` unless the
    order says otherwise, and its `created_at` is the order's `received_at` —
    both clocks, on the new edge as on the old one.
    """
    if order.kind is not OrderKind.SUPERSEDES:
        return Ending(
            Ended.REFUSED, order, (), tuple(edges),
            guardianship_of(edges, order.subject_id, order.effective_at),
            f"supersede() takes a {OrderKind.SUPERSEDES.value} order; this one is "
            f"{order.kind.value}")

    begins = successor_valid_at if successor_valid_at is not None else order.effective_at
    successor = Edge(
        GUARDIAN_OF, order.successor_id, order.subject_id, begins,
        created_at=order.received_at)
    first = end_guardianship(tuple(edges) + (successor,), order)
    if not first.applied:
        return first
    return dataclasses.replace(
        first,
        reason=first.reason + f"; superseded by {order.successor_id} from "
                              f"{begins.isoformat()}")


def past_exercise(edges: Sequence[Edge], principal_id: str,
                  subject_id: str) -> Tuple[Edge, ...]:
    """Every edge recording this principal's standing over this lane, ended or not.

    I-7 read from the other side: *"entries authored by the governed about the
    office are as durable as entries authored by the office about the
    governed."* An ex-guardian's exercise of guardianship is itself a record
    about the office, so it survives the ending — and this is the query that
    proves it survived. It takes no `at`, because the whole point is that it
    does not go away.
    """
    return tuple(e for e in edges
                 if e.kind == GUARDIAN_OF and e.principal_id == principal_id
                 and e.subject_id == subject_id)
