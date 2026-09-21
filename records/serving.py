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
from typing import Callable, Optional, Sequence

from .rungs import DERIVE_AT, NEVER_SERVED, Rung, at_least, compose

#: Strings that are not a name. `docs/LANE-MODEL.md`'s W-2 reading — *"'the
#: drumline' is not a scope; a name is"* — needs the same list in two places
#: (a grant's lane, a widening's category), so it lives once, here, in the
#: module both import from. It was `records/standing.py`'s private copy until
#: `Grant` needed it; §16 rule 1 says name the middle rather than make a pair.
_WILDCARDS = frozenset({"*", "all", "any", "every", ""})

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
    #: The authority under which `invalid_at` was set — an order, a threshold, a
    #: withdrawal. Set by `records/orders.py`, never by hand: an ending nobody
    #: can answer for is the half of refusal 3 that a bare date does not carry.
    #: `None` on an edge that has not ended, and on legacy rows dated by hand.
    ended_by: Optional[str] = _field(default=None, kw_only=True)
    #: When this system learned of the **ending** — §7.1's second axis, applied
    #: to the second event. `created_at` says when the edge was learned;
    #: nothing said when its termination was, so the March-order-delivered-in-
    #: October case could be *recorded* and not *asked about*.
    ended_known_at: Optional[datetime] = _field(default=None, kw_only=True)

    def live_at(self, when: datetime) -> bool:
        """True in the world at `when`, regardless of when we learned it."""
        if when < self.valid_at:
            return False
        return self.invalid_at is None or when < self.invalid_at

    def known_at(self, when: datetime) -> bool:
        """Whether this system had learned of the edge by `when` (§7.1's second axis)."""
        return when >= self.created_at

    def live_as_known_at(self, when: datetime, horizon: datetime) -> bool:
        """True in the world at `when`, **on what was known by** `horizon`.

        §7.1's ordinary case, asked in the tense an audit asks it in: a
        disclosure made in June, under an order dated in March and delivered in
        October, was *compliant on what was known* and *wrong on what was true*.
        `live_at` answers the second. This answers the first, and both have to
        be retrievable from the same row or the answer is a reconstruction.

        An ending with no `ended_known_at` behaves exactly as `live_at`, which
        is the fail-closed direction: an ending whose learning date nobody
        recorded is treated as always known rather than as never known.
        """
        if when < self.valid_at:
            return False
        if self.invalid_at is None:
            return True
        if self.ended_known_at is not None and horizon < self.ended_known_at:
            return True
        return when < self.invalid_at


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


@dataclass(frozen=True)
class Grant:
    """One authorization over one lane — `access_grant`, as a type.

    **Edges are facts; grants authorize.** `docs/LANE-MODEL.md`: *"the drumline
    edge is recorded because it is true, and it authorizes nothing until one
    grant per lane is issued against it, each naming a single lane."* `serve()`
    decided on the edge alone until this existed, which is why the ceiling was
    on the stated-and-unenforced list.

    Every constraint the DDL puts on `access_grant` is repeated here as a
    construction-time refusal, because a type that accepts what the table
    rejects is a second spelling of the rule (§16):

    * **`L5` is absent from `access_grant_max_rung`**, so a grant purporting to
      serve it fails at write time. Here it fails at construction.
    * **`lane_id` is a single `NOT NULL` column** with no join table and no
      scope pattern — W-2, and refusal 5. A wildcard lane is refused rather
      than being silently a name.
    * **`access_grant_l4_needs_purpose`.** `L4` without a declared purpose is
      not a grant.
    * **`expires_at` is `NOT NULL`.** A grant with no future expiry is the
      standing grant W-5 forbids, and it is `Envelope`'s rule under another
      name.

    The one constraint **not** repeated here is the signer's standing, which is
    a fact about a second row (the signer's `guardian_of` edge) that a value
    type cannot see. `migrations/001_lanes.sql`'s `access_grant_signer_has_standing`
    trigger enforces it at the store: the signer holds a live `guardian_of` edge
    over the lane at issuance, is not the grant's own holder (I-2), and a
    self-signed grant is refused outright — the one the charter would allow, a
    graduate past W-6's threshold re-admitting their guardian, needs a threshold
    this layer does not carry and is deferred (`docs/PART-III-READ.md` item 3).
    """

    holder_id: str
    lane_id: str
    max_rung: Rung
    signed_by: str
    valid_at: datetime
    expires_at: datetime
    created_at: datetime = _field(kw_only=True)
    purpose: Optional[str] = _field(default=None, kw_only=True)
    invalid_at: Optional[datetime] = _field(default=None, kw_only=True)

    def __post_init__(self):
        if self.max_rung is NEVER_SERVED:
            raise ValueError(
                f"{self.max_rung} is unreachable through a grant; the ladder's top "
                "rung is absent from access_grant_max_rung by construction"
            )
        lane = (self.lane_id or "").strip()
        if not lane or lane.lower() in _WILDCARDS:
            raise ValueError(
                f"{self.lane_id!r} is not a lane; a grant names one (W-2, refusal 5)"
            )
        if not (self.holder_id or "").strip():
            raise ValueError("a grant with no holder is not a grant")
        if not (self.signed_by or "").strip():
            raise ValueError("an unsigned grant is refused, as it is by CHECK (§7)")
        if self.max_rung is Rung.L4 and not (self.purpose or "").strip():
            raise ValueError(
                "L4 without a declared purpose is not a grant "
                "(access_grant_l4_needs_purpose)"
            )
        if self.expires_at <= self.valid_at:
            raise ValueError(
                "a grant without a future expiry is a standing grant (W-5)"
            )

    def live_at(self, when: datetime) -> bool:
        """Live in the world at `when`. Ended by `invalid_at`, never deleted."""
        if when < self.valid_at or when >= self.expires_at:
            return False
        return self.invalid_at is None or when < self.invalid_at


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


def _consulted(source, what: str):
    """`(rows, None)` for a source that answered; `(None, why)` for one that did not.

    **The callable-or-sequence shape, arriving on the read path.**
    `records/sending.py::recipients` has carried it since it was written — *"a
    consent or guardianship backend that errored surfaces as `unknown`, never as
    'no restrictions'"* — and this predicate did not, which is what put
    `entitlement_store` and `envelope_store` on
    `tests/test_rule13_acceptance.py`'s `CANNOT_DISTINGUISH` list: an edge store
    that errored and a principal with no edge both arrived here as `()`, and
    both were REFUSED with the same reason.

    A sequence still means *consulted, and this is what there was*. Only a
    callable can fail, and it fails to `UNKNOWN` rather than to empty.
    """
    if not callable(source):
        return tuple(source), None
    try:
        return tuple(source()), None
    except Exception as exc:  # noqa: BLE001 — any failure is unknown, not empty
        return None, f"the {what} source failed: {exc!r}"


def serve(
    fld: Field,
    principal: Principal,
    edges: Sequence[Edge] | Callable[[], Sequence[Edge]],
    at: datetime,
    lane_id: Optional[str] = None,
    known_as_of: Optional[datetime] = None,
    envelopes: Sequence | Callable[[], Sequence] = (),
    *,
    threshold: Optional[datetime] = None,
    widenings: Sequence | Callable[[], Sequence] = (),
    grants: Optional[Sequence[Grant]] = None,
) -> Serving:
    """Decide what `principal` is served for `fld` at instant `at`.

    Order matters and is the order the rules are written in `SENSITIVITY.md`:
    absence first, then the never-served rung, then the lane seal, then the
    entitlement edge, then the grant's ceiling, then the declared purpose.

    `threshold` is the date W-6's threshold falls for this subject — derived
    from a birthdate or a graduation date, never a flag. It governs only the
    `self` edge's cap (see `records/standing.py`); `None` means not yet reached,
    which is the fail-closed direction. `widenings` are guardian signatures that
    lift that cap per category. Both are keyword-only, so no existing positional
    call absorbs one into `envelopes` — the lesson `Edge.created_at` taught.

    **`grants` distinguishes an empty grant table from no grant table**, which
    is rule 13 in a signature. `None` means *no grant source was consulted* and
    the decision rests on the edge alone, exactly as it did before the ceiling
    existed; `()` means *consulted, and this principal holds nothing*, which
    denies at `L3` and above. A caller cannot get the permissive answer by
    passing an empty list, and cannot get the ceiling by forgetting the
    argument — the two failures point in opposite directions and a single
    sentinel would have merged them.

    **`edges`, `envelopes` and `widenings` take a sequence or a callable.** A
    callable that raises makes the whole decision `UNKNOWN` — the store could not
    say who was entitled, which is not the same fact as nobody being entitled.
    `store/reading.py`'s `Reading` is callable for exactly this, so a store that
    went down mid-read reaches this predicate as an unknown rather than as a
    refusal for a reason nobody established.
    """
    edges, why = _consulted(edges, "entitlement")
    if edges is None:
        return Serving(Outcome.UNKNOWN, None, fld.rung,
                       f"{why}; an entitlement source that errored is not a "
                       "principal with no edge (rule 13)")
    envelopes, why = _consulted(envelopes, "envelope")
    if envelopes is None:
        return Serving(Outcome.UNKNOWN, None, fld.rung,
                       f"{why}; a crossing nobody signed and a crossing nobody "
                       "could look up are different facts (rule 13)")
    widenings, why = _consulted(widenings, "widening")
    if widenings is None:
        return Serving(Outcome.UNKNOWN, None, fld.rung,
                       f"{why}; an unwidened category and a widening store that "
                       "failed are different facts (rule 13)")

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

    # W-3: lanes are mutually sealed. **Two ways the seal is crossed, and this
    # predicate enforced one of them.**
    #
    #   (a) the read *names* a different lane — checked since the first version
    #   (b) the reader *is* another ward — not checked at all, and (b) is the
    #       clause's own opening words: *"Between wards, default deny."*
    #
    # (b) is `docs/LANE-MODEL.md`'s stated-and-unenforced *"W-3's default deny
    # — the schema partitions; it does not enforce that a query stays in its
    # lane."* The forbidden act slipped through in two places at once: a read
    # that passes no `lane_id` never reached the seal at all, and a field below
    # the derive floor needs no entitlement edge, so Ben was served Ana's `L2`
    # call time with nothing consulted. The seal is not rung-shaped — it is
    # about the partition, not the sensitivity — so this sits above the floor
    # and applies at every rung a rung-check has not already refused.
    ward = _acting_ward(principal.id, edges, at)
    crossing_note = ""
    if (lane_id is not None and lane_id != fld.lane_id) or (
            ward is not None and ward != fld.subject_id):
        if lane_id is None:
            # An unnamed origin is unknown, not a wildcard (rule 13). An
            # envelope names *both* lanes; a crossing whose origin nobody
            # stated cannot be the one a guardian signed.
            return Serving(Outcome.REFUSED, None, fld.rung,
                           "W-3: between wards, default deny — this principal is a ward "
                           "of another lane and the read names no origin lane, so no "
                           "envelope can name both")
        from .crossing import permits
        env = permits(envelopes, from_lane=lane_id, to_lane=fld.lane_id, at=at,
                      signer_edges=edges, subject_id=fld.subject_id)
        if env is None:
            return Serving(Outcome.REFUSED, None, fld.rung,
                           "W-3: read crosses a lane seal; a crossing needs a "
                           "guardian-signed envelope naming both lanes, purpose and expiry")
        # A permitted crossing does not widen anything else: the rung, the
        # entitlement edge and the declared purpose all still apply below.
        crossing_note = f"; crossing permitted by envelope for {env.purpose!r}"

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

    # The rung ceiling. `access_grant.max_rung` recorded it and nothing
    # performed the comparison at serving time, which is what made the column
    # a ledger (`docs/LANE-MODEL.md`, and §7.2's *say which*). It sits beside
    # the edge check because the DDL puts it there — `basis_edge_id` is NOT
    # NULL, so a grant without a live edge under it authorizes nothing, and an
    # edge without a grant over it authorizes nothing either.
    if grants is not None:
        cap = _ceiling(grants, principal.id, fld.lane_id, at)
        if cap is None:
            return _derived_or_refused(
                fld, "no live grant over this lane; an edge is a fact and a grant "
                     "is the authorization (W-2)", edge=edge)
        if not at_least(cap, fld.rung):
            return _derived_or_refused(
                fld, f"{fld.rung} is above this principal's grant ceiling of {cap}",
                edge=edge)

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


def _acting_ward(principal_id: str, edges: Sequence[Edge],
                 at: datetime) -> Optional[str]:
    """The lane subject this principal *is*, if they are a ward at all.

    Encodes the first half of W-3 — *"Between wards, default deny"* — by
    answering the question the seal turns on: **is the reader themselves in a
    lane?** A principal holding a live, genuine `self` edge is; a director is
    not; a guardian is not.

    `is_self_edge` rather than `e.kind == SELF`, so a forged row cannot make
    somebody a ward — which here would be a *restriction* rather than a
    widening, and letting a forgery decide either direction is the same defect.

    **Its limit, stated rather than discovered.** This reads the edges the
    caller supplied. A caller who omits the reader's own `self` edge gets no
    ward seal, exactly as a caller who omits a guardianship edge gets no
    entitlement — this module's contract throughout is that the caller supplies
    the rows and the predicate decides. The store-side answer is the same
    predicate compiled into the single read method (§7's resolver shape), and
    there is no store.
    """
    from .standing import is_self_edge

    for e in edges:
        if is_self_edge(e) and e.principal_id == principal_id and e.live_at(at):
            return e.subject_id
    return None


def _ceiling(grants: Sequence[Grant], principal_id: str, lane_id: str,
             at: datetime) -> Optional[Rung]:
    """The highest rung this principal's live grants reach on this lane.

    `None` means *no live grant*, which is not `L1` and is not a ceiling of
    nothing — the caller refuses on it. Composition is `max` and it is
    `rungs.compose`, not a second implementation of the same rule.
    """
    live = [g for g in grants
            if g.holder_id == principal_id and g.lane_id == lane_id
            and g.live_at(at)]
    if not live:
        return None
    return compose(*[g.max_rung for g in live])


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
    from .standing import SELF

    for e in edges:
        if e.kind == SELF and e.principal_id != e.subject_id:
            # A row claiming `self` for somebody who is not the subject is not a
            # weaker edge; it is not an edge. The kind names a relationship and
            # nothing else here was checking that the relationship held, so
            # `Edge("self", "staff-nguyen", "student-ben", …)` would otherwise
            # entitle a staff member through the subject's own door.
            #
            # `standing.SELF`, not the literal `"self"`, which this line used to
            # hardcode while `serve()` twenty lines up used the constant. Two
            # spellings of one concept in one file: renaming the constant would
            # have silently retired this filter, and the ablation entry pinned
            # the literal too, so the guard would have gone on passing while
            # being dead in production.
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

    **The instruction carries the field's provenance; the refusal does not**,
    and the asymmetry is deliberate. An instruction is a value that leaves the
    system, and this module's stated contract is that every decision carries the
    provenance of what it served — without it a caller cannot distinguish a
    provenance dropped in transit from a field that never had one, which is
    absence rendered as a result in the module whose subject is that
    distinction. A *refusal* served nothing, so attaching the field's provenance
    to it would make a refusal over a `P1` field distinguishable from a refusal
    over a field carrying none: a side channel opened in the exact function
    whose job is to close them.
    """
    if fld.instruction is not None:
        return Serving(Outcome.INSTRUCTION, fld.instruction, fld.rung, why,
                       via_edge=edge.kind if edge else None,
                       provenance=fld.provenance)
    return Serving(Outcome.REFUSED, None, fld.rung, why + "; no derived instruction authored",
                   via_edge=edge.kind if edge else None)
