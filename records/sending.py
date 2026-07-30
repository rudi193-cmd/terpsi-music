"""Who may be told, derived at an instant and never stored.

`docs/PLAN-GUARDIANSHIP.md` specifies eleven acceptance gates for §7.1's dated
predicate. This is that predicate on the **send** path, which §4.1 calls *"the
sharpest argument in this document for building §7.1 early"*: a read gate that
does not also derive the send list is not protecting the thing that actually
leaves.

**The send list is derived, never stored.** There is no `recipients` field, no
cached list, no `notify_parents` column. A stored list is a second copy of the
truth and it drifts the moment an order arrives — §16's pair, with a human
remembering as its only middle.

**And the handler takes no recipient at all** (G4). `deliver()` accepts a
payload carrying a student and an instant. It has no `to` parameter and cannot
be given one, so you cannot send to a restricted guardian because there is
nowhere to put one. That is a property of the source rather than of behaviour
at runtime, which is why G4 and G7 are the two gates that hold when everything
else is forgotten.

Two facts are modelled separately because they are separate:

* **standing** — a `guardian_of` edge, which says who this person *is* to the
  student. Ends by `invalid_at`, never by deletion (refusal 3).
* **reachability** — a `ContactRestriction`, which says they may not be
  *messaged* even while their standing continues. A court order restricting
  contact does not necessarily end guardianship, and conflating the two would
  make the software unable to express the most common protective order.

Stdlib only. No network, no store, no model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Sequence

from .serving import Edge


class Standing(Enum):
    DERIVED = "derived"  # the list is complete and this is it
    UNKNOWN = "unknown"  # a source could not be consulted; NOT "no restrictions"


@dataclass(frozen=True)
class ContactRestriction:
    """A dated suppression of reachability, distinct from standing.

    `valid_at` is when the restriction became true in the world; `created_at`
    is when this system learned of it. G5 turns on both being retrievable: an
    order dated in March and delivered in October means a June disclosure was
    correct on what was known and wrong on what was true, and an audit has to
    be able to say which.
    """

    principal_id: str
    subject_id: str
    valid_at: datetime
    created_at: datetime
    invalid_at: Optional[datetime] = None  # lifted, not deleted (G8)
    authority: str = ""

    def live_at(self, when: datetime) -> bool:
        if when < self.valid_at:
            return False
        return self.invalid_at is None or when < self.invalid_at

    def known_at(self, when: datetime) -> bool:
        """Whether the system had learned of it by `when` (G5's other axis)."""
        return when >= self.created_at


@dataclass(frozen=True)
class SendList:
    state: Standing
    guardians: tuple  # empty is meaningful ONLY when state is DERIVED
    reason: str
    suppressed: tuple = ()  # who was excluded, and why — for G10, never for sending

    def __iter__(self):
        """Iterating an UNKNOWN list raises rather than yielding nothing.

        Rule 13, made structural. The failure this prevents is a caller writing
        `for g in recipients(...)` and silently sending to nobody because a
        consent backend was down — indistinguishable, from the loop alone, from
        a student with no guardians.
        """
        if self.state is not Standing.DERIVED:
            raise RuntimeError(
                f"send list is {self.state.value}, not derived: {self.reason}. "
                "An unknown recipient set is not an empty one (G11)."
            )
        return iter(self.guardians)


def recipients(
    subject_id: str,
    edges: Sequence[Edge],
    restrictions: Sequence[ContactRestriction] | Callable[[], Sequence[ContactRestriction]],
    at: datetime,
    known_as_of: Optional[datetime] = None,
) -> SendList:
    """Guardians who may be messaged about `subject_id` at instant `at`.

    `restrictions` may be a sequence or a callable. A callable that raises
    yields `UNKNOWN` — G11: *"a consent or guardianship backend that errored
    surfaces as `unknown`, never as 'no restrictions'."* Returning an empty
    list on error is the failure this signature exists to make impossible.

    `known_as_of` restricts the restriction set to what the system had learned
    by that instant, leaving `at` to mean what was true in the world (G5).
    Defaults to `at`, which is the ordinary case.
    """
    if callable(restrictions):
        try:
            found = tuple(restrictions())
        except Exception as exc:  # noqa: BLE001 — any failure is unknown, not empty
            return SendList(Standing.UNKNOWN, (), f"restriction source failed: {exc!r}")
    else:
        found = tuple(restrictions)

    horizon = known_as_of if known_as_of is not None else at

    standing = [
        e for e in edges
        if e.kind == "guardian_of" and e.subject_id == subject_id and e.live_at(at)
    ]

    allowed, suppressed = [], []
    for e in standing:
        block = next(
            (r for r in found
             if r.principal_id == e.principal_id
             and r.subject_id == subject_id
             and r.live_at(at)
             and r.known_at(horizon)),
            None,
        )
        if block is None:
            allowed.append(e.principal_id)
        else:
            suppressed.append((e.principal_id, block.authority or "restriction"))

    return SendList(
        Standing.DERIVED,
        tuple(allowed),
        f"{len(allowed)} of {len(standing)} guardians with live standing are reachable at {at.isoformat()}",
        tuple(suppressed),
    )


# --- the send path ---------------------------------------------------------


@dataclass(frozen=True)
class Payload:
    """What a student-scoped message carries. Note what it does not carry."""

    subject_id: str
    at: datetime
    body: str


def deliver(
    payload: Payload,
    edges: Sequence[Edge],
    restrictions,
    transport: Callable[[str, str], None],
) -> SendList:
    """Send `payload` to whoever is derivable, and return who that was.

    **G4: this function has no recipient parameter and must never grow one.**
    `tests/test_sending.py` asserts that statically over this module's source,
    because a signature is a thing a future edit can widen and a comment is
    not. The derivation happens here, at the point of sending, so there is no
    window between deriving and using in which an order could arrive.
    """
    who = recipients(payload.subject_id, edges, restrictions, payload.at)
    for guardian_id in who:  # raises if UNKNOWN — see SendList.__iter__
        transport(guardian_id, payload.body)
    return who


def who_could_see(
    subject_id: str,
    edges: Sequence[Edge],
    restrictions: Sequence[ContactRestriction],
    at: datetime,
) -> tuple:
    """G10: answer with a reason, as a query rather than an investigation.

    Returns `(principal_id, reachable, reason)` for every principal with
    standing — including the suppressed, because *"who could see this"* that
    silently omits the restricted party cannot be used to check a restriction
    is working.
    """
    out = []
    for e in edges:
        if e.subject_id != subject_id or not e.live_at(at):
            continue
        block = next(
            (r for r in restrictions
             if r.principal_id == e.principal_id and r.subject_id == subject_id
             and r.live_at(at) and r.known_at(at)),
            None,
        )
        if block is None:
            out.append((e.principal_id, True, f"live {e.kind} edge, no restriction"))
        else:
            out.append((e.principal_id, False,
                        f"live {e.kind} edge, suppressed by {block.authority or 'restriction'}"))
    return tuple(out)
