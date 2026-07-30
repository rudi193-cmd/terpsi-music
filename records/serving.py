"""One read predicate: what a principal may be served about a student, and why.

The first code in this repository that touches the domain. Everything before it
analysed text or checked documents against documents; this decides what happens
to a record about a person, which is the thing the whole design is for.

**Deliberately narrow.** One student, one lane, one field, one instant. No
surface, no transport, no store — the caller supplies rows and this returns a
decision. That keeps it buildable before §18 item 4 says what a surface is, and
keeps the predicate the single place the rules live (§7's resolver shape:
*"one predicate, compiled once, funnelled through the single read method"*).

**The wrong answer is unrepresentable, not merely refused.** `serve()` returns a
`Serving`, and the only way to obtain a payload is for this function to have
decided to hand one over. There is no `Optional[str]` a caller can unwrap by
accident, which is `willow-grove`'s constraint 1 — *"the renderer must be unable
to display 'clear' without having actually received an answer"* — applied to a
payload rather than to a health indicator.

**Every decision carries its provenance.** A `Serving` says which rung, which
edge and which purpose produced it, so a caller can assert on the reason rather
than on the shape, and §7.2's *narrate the read* has something to narrate. Same
argument as `kartikeya.resolve_sandbox_config` returning `(config, source)`.

Stdlib only. No network, no store, no model.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence

from .rungs import DERIVE_AT, NEVER_SERVED, Rung, at_least

# --- the inputs, as the lane model shapes them -----------------------------


@dataclass(frozen=True)
class Edge:
    """A dated relationship (§7.1). Terminated by `invalid_at`, never deleted.

    **Three dates, not two.** `valid_at`/`invalid_at` say when the relationship
    was true in the world; `created_at` says when this system learned of it, and
    §7.1 requires it explicitly — *"keep `created_at` immutable alongside the
    pair, and never update it"* — for the case that proves it: a court order
    dated in March and delivered in October. A disclosure made in June was
    compliant or not depending on which axis you ask about.

    `created_at` was missing from this class until the send predicate needed it,
    which is the second slice finding a defect in the first. It is **keyword-only
    and required**, so no existing positional call silently absorbs it into
    `invalid_at` — a five-argument `Edge(...)` now fails loudly rather than
    quietly meaning something else.
    """

    kind: str  # self, guardian_of, staff_of, director_of, judge_at, clinician_for
    principal_id: str
    subject_id: str
    valid_at: datetime
    invalid_at: Optional[datetime] = None
    created_at: datetime = _field(kw_only=True)

    def live_at(self, when: datetime) -> bool:
        """True in the world at `when`, regardless of when we learned it."""
        if when < self.valid_at:
            return False
        return self.invalid_at is None or when < self.invalid_at

    def known_at(self, when: datetime) -> bool:
        """Whether this system had learned of the edge by `when` (§7.1's second axis)."""
        return when >= self.created_at


@dataclass(frozen=True)
class Field:
    """One classified fact in one student's lane (W-1)."""

    lane_id: str
    subject_id: str
    name: str
    rung: Optional[Rung]  # None models an unclassified field — see below
    category: Optional[str] = None  # health, money, discipline, likeness, protected_status
    payload: Optional[str] = None
    instruction: Optional[str] = None  # the derived form; what L4 normally serves
    #: The **P-ladder** rung of the value (§15): `P1` measured … `P5` assumed.
    #: A field had no provenance until `records/dispatch.py` routed the voice
    #: gate, whose `no_provenance` rule refuses a served value that does not
    #: carry one. The renderer needs this; the predicate does not use it.
    provenance: Optional[str] = None


@dataclass(frozen=True)
class Principal:
    id: str
    purposes: frozenset = _field(default_factory=frozenset)


# --- the outcome -----------------------------------------------------------


class Outcome(Enum):
    PAYLOAD = "payload"          # the fact itself
    INSTRUCTION = "instruction"  # the derived form; the fact never left
    REFUSED = "refused"          # enforced, and correctly invisible
    UNKNOWN = "unknown"          # we could not decide; not a result (rule 13)


@dataclass(frozen=True)
class Serving:
    """A decision, with the reason that produced it."""

    outcome: Outcome
    value: Optional[str]
    rung: Optional[Rung]
    reason: str
    via_edge: Optional[str] = None
    via_purpose: Optional[str] = None
    provenance: Optional[str] = None

    @property
    def disclosed(self) -> bool:
        """True only when the underlying fact left the system (§7.2)."""
        return self.outcome is Outcome.PAYLOAD


# --- the predicate ---------------------------------------------------------


def serve(
    fld: Field,
    principal: Principal,
    edges: Sequence[Edge],
    at: datetime,
    lane_id: Optional[str] = None,
    known_as_of: Optional[datetime] = None,
    envelopes: Sequence = (),
    *,
    threshold: Optional[datetime] = None,
    widenings: Sequence = (),
) -> Serving:
    """Decide what `principal` is served for `fld` at instant `at`.

    Order matters and is the order the rules are written in `SENSITIVITY.md`:
    absence first, then the never-served rung, then the lane seal, then the
    entitlement edge, then the declared purpose.

    `threshold` is the date W-6's threshold falls for this subject — derived
    from a birthdate or a graduation date, never a flag. It governs only the
    `self` edge's cap (see `records/standing.py`); `None` means not yet reached,
    which is the fail-closed direction. `widenings` are guardian signatures that
    lift that cap per category. Both are keyword-only, so no existing positional
    call absorbs one into `envelopes` — the lesson `Edge.created_at` taught.
    """
    # Rule 13. An unclassified field is a build failure; if one reaches here
    # anyway it reads as unknown and is not served. Never L1 by default.
    if fld.rung is None:
        return Serving(Outcome.UNKNOWN, None, None,
                       "field carries no classification; refusing rather than guessing")

    # L5 is enforcement-only: never rendered, to anyone, under any grant —
    # including the holder of a live edge, and including the subject.
    if fld.rung is NEVER_SERVED:
        return Serving(Outcome.REFUSED, None, fld.rung,
                       "L5 is never served to any principal under any grant")

    # W-3: lanes are mutually sealed. A read naming a lane must name this
    # field's lane. Crossing requires a guardian-signed envelope, which has no
    # table yet (see docs/LANE-MODEL.md) — so a crossing is refused, not waved.
    if lane_id is not None and lane_id != fld.lane_id:
        from .crossing import permits
        env = permits(envelopes, from_lane=lane_id, to_lane=fld.lane_id, at=at,
                      signer_edges=edges, subject_id=fld.subject_id)
        if env is None:
            return Serving(Outcome.REFUSED, None, fld.rung,
                           "W-3: read names a different lane; a crossing needs a "
                           "guardian-signed envelope naming both lanes, purpose and expiry")
        # A permitted crossing does not widen anything else: the rung, the
        # entitlement edge and the declared purpose all still apply below.
        crossing_note = f"; crossing permitted by envelope for {env.purpose!r}"

    else:
        crossing_note = ""

    # Below the derive floor, the payload is the normal serving mode.
    if not at_least(fld.rung, DERIVE_AT):
        return Serving(Outcome.PAYLOAD, fld.payload, fld.rung,
                       f"{fld.rung} is below the derive floor" + crossing_note,
                       provenance=fld.provenance)

    # §18 item 1a, decided scoped: entitlement is an edge to *this subject*,
    # live at *this instant*. An expired edge is not an edge.
    edge = _entitling_edge(fld.subject_id, principal.id, edges, at,
                           known_as_of if known_as_of is not None else at)
    if edge is None:
        return _derived_or_refused(
            fld, "no live entitlement edge to this subject at this instant")

    # L4 additionally requires a purpose declared for the category on entry
    # (§7.2's knock). Even for an entitled principal the instruction is the
    # normal mode and the payload is the exception.
    if at_least(fld.rung, Rung.L4):
        from .standing import SELF, SELF_CAP, past_threshold, widens

        # §18 item 12. A `self` edge is capped at L3 until the threshold; above
        # it, only a guardian's signature widens — and `principal.purposes` is
        # deliberately NOT consulted, because a ward declaring a purpose over
        # its own record is the ward authorizing itself (W-4).
        if edge.kind == SELF and not past_threshold(at, threshold):
            w = widens(widenings, subject_id=fld.subject_id,
                       category=fld.category, at=at, signer_edges=edges)
            if w is None:
                return _derived_or_refused(
                    fld,
                    f"{fld.rung} is above the self edge's {SELF_CAP} cap before the "
                    f"W-6 threshold; a guardian's signature widens it per category (W-5)",
                    edge=edge)
            return Serving(Outcome.PAYLOAD, fld.payload, fld.rung,
                           f"{fld.rung} to the subject, widened by {w.signed_by}'s "
                           f"signature for {w.category!r}" + crossing_note,
                           via_edge=edge.kind, via_purpose=w.category,
                           provenance=fld.provenance)

        if fld.category and fld.category in principal.purposes:
            return Serving(Outcome.PAYLOAD, fld.payload, fld.rung,
                           f"{fld.rung} with edge and declared purpose" + crossing_note,
                           via_edge=edge.kind, via_purpose=fld.category,
                           provenance=fld.provenance)
        return _derived_or_refused(
            fld, f"{fld.rung} without a declared purpose for {fld.category!r}",
            edge=edge)

    return Serving(Outcome.PAYLOAD, fld.payload, fld.rung,
                   f"{fld.rung} with a live entitlement edge" + crossing_note,
                   via_edge=edge.kind, provenance=fld.provenance)


def _entitling_edge(
    subject_id: str, principal_id: str, edges: Sequence[Edge],
    at: datetime, horizon: datetime,
) -> Optional[Edge]:
    """The live, *known* edge from this principal to this subject.

    Two clocks, symmetric with `sending.recipients` (§7.1). An edge the system
    had not yet learned of cannot have entitled a read that already happened —
    which is the read-path half of G5's March-order-delivered-in-October case,
    and the question an audit asks about a disclosure that already went out.
    """
    for e in edges:
        if e.kind == "self" and e.principal_id != e.subject_id:
            # A row claiming `self` for somebody who is not the subject is not a
            # weaker edge; it is not an edge. The kind names a relationship and
            # nothing else here was checking that the relationship held, so
            # `Edge("self", "staff-nguyen", "student-ben", …)` would otherwise
            # entitle a staff member through the subject's own door.
            continue
        if (e.subject_id == subject_id and e.principal_id == principal_id
                and e.live_at(at) and e.known_at(horizon)):
            return e
    return None


def _derived_or_refused(fld: Field, why: str, edge: Optional[Edge] = None) -> Serving:
    """Serve the instruction if one was authored; refuse if not.

    The absence of an instruction is **not** a licence to serve the payload,
    and it is not an error either — it is the ordinary case for a field nobody
    has written a derived form for yet. §7's indistinguishability guarantee
    means this must look the same as a field that has no instruction *and* no
    payload.
    """
    if fld.instruction is not None:
        return Serving(Outcome.INSTRUCTION, fld.instruction, fld.rung, why,
                       via_edge=edge.kind if edge else None)
    return Serving(Outcome.REFUSED, None, fld.rung, why + "; no derived instruction authored",
                   via_edge=edge.kind if edge else None)
