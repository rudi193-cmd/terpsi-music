"""§18 item 12: the subject's standing in their own lane.

§7's entitlement edges are `guardian_of`, `staff_of`, `director_of`, `judge_at`,
`clinician_for`. **None of them is the subject**, so `records/serving.py`
implemented §7 faithfully and a student reading their own chair assignment was
served *"one member of this section"* about their own name.

**The item was framed as a yes/no and that framing is why it stayed open.**
Three-fifths of it was already decided by the ladder. `L5` is checked *before*
the edge check and is never served to anyone including the subject; `L1` and
`L2` sit below the derive floor and are served without any edge at all. The live
question was only `L3` and `L4`, and it was never *whether* the subject has
standing — every other principal's standing is rung-shaped, and there was no
reason the subject's would not be.

**Decided 2026-07-30.** A `self` edge, capped at `L3` until W-6's threshold.

* **`L1`–`L3`: served in full.** Refusing a student their own chair placement is
  not protection; the student sits in the chair. And it is worse than useless,
  because §7's indistinguishability guarantee makes that derived form identical
  to the one a suppressed record would produce — the student cannot tell *"the
  system will not say"* from *"there is something here."*
* **`L4`: the derived instruction**, exactly as for any entitled principal
  without a declared purpose. A guardian may sign a per-category `Widening`
  (W-5's *"agency grows by signature"*). A fourteen-year-old does not read their
  own psychological evaluation off a phone with nobody in the room.
* **`L5`: unchanged.** Never served, to anyone, including the subject.
* **After the threshold**: the cap lifts and `self` behaves exactly like any
  other edge — `L4` on a declared purpose. That is W-6 arriving as the mechanism
  §7 already has (*"minor status is a birthdate, not a flag"*), rather than as a
  special event somebody must remember to run.

**Why an edge and not a `principal.id == subject_id` special-case**, which was
the item's second option and the cheaper one:

1. **It is dated.** The threshold is a date compared on every read. A predicate
   special-case has nowhere to put the threshold, and nowhere to put its end.
2. **It is auditable.** *"Who could see Ben's medical form on October 12, and
   why"* must answer *"Ben, via self."* A special-case logs `via_edge=None`,
   which in the disclosure log is indistinguishable from an unentitled read —
   §7.2's *narrate the read* silently broken by the fix.
3. **It can be ended** by `invalid_at` (refusal 3). A safety plan in which the
   subject is the risk is rare and real, and has nowhere to live otherwise.
4. **It is already a row.** `migrations/001_lanes.sql`'s `edge` table takes it
   by widening one CHECK — and, since promotion, a trigger that refuses a
   `self` row whose holder is not the lane's subject.

**Why not the item's third option — deliberate no-standing.** It makes I-7
unverifiable by the party it protects. *"A student's entries are as durable as
entries about them"* is a claim a student cannot check without reading their
lane, and rule 19 says a guarantee that cannot be shown to hold is not a
guarantee. It also makes W-6 the worst moment in the design: years of records,
first sight, all at once, with nobody left to ask.

**W-4 and W-5 both survive**, and one consequence of that is load-bearing here.
W-4 is *"a ward may request, never authorize"* — so for a pre-threshold `self`
edge, **`principal.purposes` is never consulted at all.** A minor declaring a
purpose over their own `L4` record is a ward authorizing itself, and reading the
declaration would be W-4 defeated by a keyword argument. Only a guardian's
signature widens. W-5 forbids agency growing by *drift*; a cap set identically
for every student at enrolment is not drift, and nothing here lifts a cap
because a student's attendance is good.

Stdlib only. No network, no store.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Sequence, Tuple

from .crossing import _NOT_A_PERSON
from .disclosure import Entry, Log
from .rungs import Rung
from .serving import Edge, _WILDCARDS

#: The edge kind. A string rather than an enum because §7's other four kinds are
#: strings and a mixed vocabulary is worse than a plain one.
SELF = "self"

#: The rung a `self` edge reaches before the threshold. Above it, a guardian's
#: signature is required per category.
SELF_CAP = Rung.L3


def self_edge(subject_id: str, *, valid_at: datetime, created_at: datetime,
              invalid_at: Optional[datetime] = None) -> Edge:
    """The subject's own standing in their own lane.

    Constructed rather than hand-rolled so `principal_id == subject_id` holds by
    construction. `is_self_edge` re-checks it anyway, because an `Edge` arriving
    from a row nobody validated is the case that matters.
    """
    return Edge(SELF, subject_id, subject_id, valid_at, invalid_at,
                created_at=created_at)


def is_self_edge(e: Edge) -> bool:
    """Whether this is a *genuine* self edge.

    **A forged one is the obvious attack and it is cheap.** `Edge("self",
    "staff-nguyen", "student-ben", ...)` would otherwise entitle a staff member
    through the subject's own door — the kind names the relationship and nothing
    was checking that the relationship held. So the holder must be the subject,
    and a row claiming `self` for anyone else is not a weaker edge, it is not an
    edge.
    """
    return e.kind == SELF and e.principal_id == e.subject_id


def past_threshold(at: datetime, threshold: Optional[datetime]) -> bool:
    """Whether W-6's threshold has been reached at `at`.

    A date compared on every read, never a flag and never a job (§7: *"minor
    status is a birthdate, not a flag — a flag stays true until somebody
    remembers to run the job that clears it"*). An unknown threshold is **not**
    a reached one: `None` reads as not yet, which is the fail-closed direction.
    """
    return threshold is not None and at >= threshold


# --- the guardian-signed widening (W-5) ------------------------------------


@dataclass(frozen=True)
class Widening:
    """A guardian's signature lifting the `self` cap for one category.

    Shaped after `crossing.Envelope`, and for the same reason: the four things
    with no defaults are the four a hurried implementation omits.

    * **one named category** — a widening over "everything" is a standing grant
      and W-2's *"'the children' is not a scope; a name is"* applied to the
      other axis
    * **an expiry** — W-5 forbids the standing grant
    * **a guardian's signature** — a role cannot sign, and neither can staff
    * **not the subject's own** — W-4. A ward signing its own widening is the
      whole clause defeated in one field, so it is rejected at construction
      rather than checked at use.
    """

    subject_id: str
    category: str
    purpose: str
    signed_by: str
    signed_at: datetime
    expires_at: datetime

    def __post_init__(self):
        cat = (self.category or "").strip().lower()
        if cat in _WILDCARDS:
            raise ValueError(
                f"{self.category!r} is not a category; a widening names one (W-2)"
            )
        if not (self.purpose or "").strip():
            raise ValueError("a widening without a purpose is a standing grant")
        name = (self.signed_by or "").strip()
        if not name or name.lower() in _NOT_A_PERSON:
            raise ValueError(
                f"{self.signed_by!r} is not a guardian's signature; a role cannot sign"
            )
        if name == self.subject_id:
            raise ValueError(
                "a ward may request, never authorize (W-4): the subject cannot "
                "sign their own widening"
            )
        if self.expires_at <= self.signed_at:
            raise ValueError(
                "a widening without a future expiry is a standing grant (W-5)"
            )

    def live_at(self, when: datetime) -> bool:
        return self.signed_at <= when < self.expires_at


@dataclass(frozen=True)
class ProposedWidening:
    """A widening a steward proposes, citing the record — and enacts by nobody.

    W-5 at source: *"The steward may propose a widening, citing the record; it
    may never enact one. A clean track record is evidence for a proposal, never
    a grant in itself."* `Widening` above is the **enacted** form; until this
    type there was nowhere to put a proposal except the enacted table, so
    proposing was enacting. This is the proposal, and its whole point is that it
    **grants nothing and widens nothing.**

    `migrations/005_proposed_widening.sql` is its durable, sealed ledger. The
    enforcement of *never enact* is `ratify()` below, the named middle (rule 12):
    the only path from here to a `Widening` runs through a live guardian's
    signature. `widens()` skips this type on sight, so even a **guardian's own
    proposal** is inert until they sign it — which is the clause, precisely.

    Same four things with no defaults as `Widening`, minus the signature, plus
    the evidence: a proposal is a *request* (W-4: *"a ward may request"*), so
    the proposer may be the ward itself, and there is deliberately no
    `proposed_by != subject_id` rule — that restriction belongs on the guardian
    signature that enacts it, not on the asking.
    """

    subject_id: str
    category: str
    purpose: str
    proposed_by: str
    evidence: str
    proposed_at: datetime
    expires_at: datetime

    def __post_init__(self):
        if (self.category or "").strip().lower() in _WILDCARDS:
            raise ValueError(
                f"{self.category!r} is not a category; a proposal names one (W-2)"
            )
        if not (self.purpose or "").strip():
            raise ValueError("a widening without a purpose is a standing grant")
        if not (self.evidence or "").strip():
            raise ValueError(
                "a proposal cites the record; evidence is required (W-5: "
                "'citing the record') and a proposal with nothing behind it is "
                "drift wearing a form"
            )
        if not (self.proposed_by or "").strip():
            raise ValueError("a proposal is made by someone; proposed_by is required")
        if self.expires_at <= self.proposed_at:
            raise ValueError(
                "a proposal without a future expiry is a standing one (W-5)"
            )

    @property
    def signed_by(self) -> str:
        """The proposer, exposed under the name `widens()` reads — deliberately.

        A `ProposedWidening` is otherwise shaped exactly like a `Widening`, so
        `widens()` refusing it is a decision about its *type* (unratified), not
        an accident of a missing attribute it would have skipped anyway. A
        guardian who proposes is still only proposing.
        """
        return self.proposed_by

    def live_at(self, when: datetime) -> bool:
        """Live as a *pending proposal*, which is not live as an authority."""
        return self.proposed_at <= when < self.expires_at


def propose(subject_id: str, category: str, purpose: str, *,
            proposed_by: str, evidence: str, at: datetime,
            expires_at: datetime) -> ProposedWidening:
    """A steward proposes a widening. **This enacts nothing** (W-5).

    Returns a `ProposedWidening`, never a `Widening`: the type is the boundary.
    A caller that wants the widening to take effect must have a guardian
    `ratify()` it.
    """
    return ProposedWidening(subject_id, category, purpose, proposed_by, evidence,
                            at, expires_at)


def ratify(proposal: ProposedWidening, *, signed_by: str, at: datetime,
           expires_at: datetime) -> Widening:
    """Enact a proposal: a live guardian's signature turns it into a `Widening`.

    The named middle (rule 12) between `migrations/005`'s `proposed_widening`
    ledger and `migrations/001`'s `self_widening`. It **reuses** `Widening`'s
    construction rather than re-checking (§16): W-4 (`signed_by != subject_id`),
    the wildcard category and the future expiry are one implementation, so a
    ward ratifying its own proposal is refused there, in the one place the rule
    lives. `at` is the signing instant; the enacted widening carries the
    proposal's subject, category and purpose unchanged.
    """
    return Widening(
        subject_id=proposal.subject_id,
        category=proposal.category,
        purpose=proposal.purpose,
        signed_by=signed_by,
        signed_at=at,
        expires_at=expires_at,
    )


class WideningsUnknown(RuntimeError):
    """The widening source could not be consulted.

    Raised rather than returned, because `widens()` answers `Optional[Widening]`
    and `None` already means *nothing widens this category* — a third meaning in
    the same value is how the seam came to be indistinguishable in the first
    place. A caller that wants the softer answer catches this; `serving.serve`
    does, and turns it into `Outcome.UNKNOWN`.
    """


def widens(widenings: Sequence[Widening] | Callable[[], Sequence[Widening]], *,
           subject_id: str, category: Optional[str], at: datetime,
           signer_edges: Sequence[Edge] = ()) -> Optional[Widening]:
    """The live widening covering this category, or `None`.

    **The signer's standing is checked at the instant of use**, not of signing —
    same as `crossing.permits`, and for the same reason: a guardian whose
    standing has ended cannot keep a widening open by having signed it while
    they still had it. That is refusal 3 applied to the signature.

    A field with no category cannot be widened. `L4` means *identifies an
    individual **and** carries a category the law follows*; if the category is
    missing the field is misclassified, and inventing a match here would widen
    on the strength of a defect.

    **`widenings` takes a sequence or a callable**, the shape
    `records/sending.py::recipients` has always carried. A callable that raises
    is `WideningsUnknown`, never `None`: a guardian who signed nothing and a
    store that could not be asked led to the same `None` and the same held cap,
    which is the row `tests/test_rule13_acceptance.py` carried for this seam
    until the store gave the error somewhere to come from.
    """
    if callable(widenings):
        try:
            widenings = tuple(widenings())
        except Exception as exc:  # noqa: BLE001 — any failure is unknown, not empty
            raise WideningsUnknown(
                f"the widening source failed: {exc!r}; an unwidened category and "
                "a source that could not be read are different facts (rule 13)"
            ) from exc
    if not category:
        return None
    for w in widenings:
        # Only an enacted Widening widens. A ProposedWidening is shaped exactly
        # like one and would otherwise flow through -- including a guardian's own
        # proposal -- so it is refused by type here: W-5's "may propose... may
        # never enact" is this one line. ratify() is the only bridge.
        if not isinstance(w, Widening):
            continue
        if w.subject_id != subject_id or w.category != category:
            continue
        if not w.live_at(at):
            continue
        standing = any(
            e.kind == "guardian_of" and e.principal_id == w.signed_by
            and e.subject_id == subject_id and e.live_at(at)
            for e in signer_edges
        )
        if standing:
            return w
    return None


# --- the subject's own disclosure log ---------------------------------------


class LogAccess(Enum):
    GRANTED = "granted"
    REFUSED = "refused"
    UNKNOWN = "unknown"   # not a result (rule 13)


@dataclass(frozen=True)
class OwnLog:
    """The subject's view of who read them. Iterating it without standing raises.

    Shaped after `sending.SendList`: an empty log and a refused one are
    different facts and must not both arrive as `()`. The state is checked on
    iteration rather than trusted at the call site, because the call site is
    where it gets forgotten.
    """

    state: LogAccess
    entries: Tuple[Entry, ...]
    total: int
    reason: str

    def __iter__(self):
        if self.state is not LogAccess.GRANTED:
            raise PermissionError(
                f"this log view is {self.state.value}, not a list of entries: {self.reason}"
            )
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    @property
    def complete(self) -> bool:
        """Whether this view is the whole log. Never inferred from emptiness."""
        return self.state is LogAccess.GRANTED and len(self.entries) == self.total


def own_log(log: Log, viewer_id: str, subject_id: str, at: datetime,
            edges: Sequence[Edge]) -> OwnLog:
    """What the subject may see of the log of reads about them.

    **Not rung-capped, and that is the decision.** A student who cannot read
    their own `L4` medical field can still see that the athletic director read
    it on October 12. The entry names the reader, the field, the rung, the
    outcome and the authority — and `Entry` has never carried the disclosed
    value, so nothing about the field's contents travels through this view. What
    the subject learns is *that they were read*, which is the one thing a record
    about a person should never be able to hide from them.

    This is I-7 and §7.2 pointed at the person the record is about. Yesterday's
    `records/receipts.py` gives a guardian the same property from outside; this
    gives the subject it from inside, and the two fail differently.

    **Fails closed on an unscoped log** (§5). A `Log` carrying entries about more
    than one subject is not a lane's log, and serving it filtered would be the
    global-chain defect `Ledger` exists to prevent, re-created at the read.

    **Guardian standing over this view is deliberately not decided here.** It is
    the obvious next question and it is not item 12: a guardian reading the log
    learns which *staff member* is looking at a record, which is nearer §13's
    prohibited standing scores than it looks. Guardians already hold receipts.
    """
    subjects = {e.subject_id for e in log.entries}
    if len(subjects) > 1:
        return OwnLog(LogAccess.UNKNOWN, (), len(log.entries),
                      f"this log carries entries about {len(subjects)} subjects; a "
                      "lane's log carries one, and filtering an unscoped log at the "
                      "read re-creates the defect Ledger exists to prevent")
    if subjects and subject_id not in subjects:
        return OwnLog(LogAccess.UNKNOWN, (), len(log.entries),
                      "this log is not about the named subject")

    holds = any(is_self_edge(e) and e.subject_id == subject_id
                and e.principal_id == viewer_id and e.live_at(at)
                for e in edges)
    if not holds:
        return OwnLog(LogAccess.REFUSED, (), len(log.entries),
                      "own_log serves the subject's own view; the viewer holds no "
                      "live self edge to this subject")

    return OwnLog(LogAccess.GRANTED, log.entries, len(log.entries),
                  f"{len(log.entries)} read(s) recorded about this subject, at every rung")


# --- I-7's supersession asymmetry -------------------------------------------


class Supersession(Enum):
    PERMITTED = "permitted"
    REFUSED = "refused"
    UNKNOWN = "unknown"   # not a permission (rule 13)


@dataclass(frozen=True)
class MaySupersede:
    """A decision about ending or amending one entry, with its reason."""

    state: Supersession
    reason: str

    @property
    def permitted(self) -> bool:
        """True only for `PERMITTED`. An `UNKNOWN` is not a yes."""
        return self.state is Supersession.PERMITTED


def may_supersede(*, author_id: Optional[str], subject_id: Optional[str],
                  principal_id: str, edges: Sequence[Edge] = (),
                  at: Optional[datetime] = None) -> MaySupersede:
    """Whether `principal_id` may supersede an entry authored by `author_id`.

    **The clause, at source** (`Willow` `PROTECTED_AGENTS.md`, I-7 —
    *the record binds the holder most*):

    > *"No office's Force extends to deleting or amending entries about its own
    > exercise. Entries authored by the governed about the office are as durable
    > as entries authored by the office about the governed."*

    `docs/LANE-MODEL.md` states the schema-side consequence and says it cannot
    be a column CHECK: *"supersession of a `lane_entry` whose `author_id` is the
    lane's own subject requires an authority that no office-derived grant
    confers. That is a predicate over the acting principal and the row."* This
    is that predicate.

    **The asymmetry is the whole content**, and it is why the clause is not
    "entries are immutable":

    * an entry the **office** authored may be superseded by the office — its
      own draft, its own note, its own correction
    * an entry the **governed** authored may be superseded by nobody but its
      author, and **no edge helps** — not `director_of`, not `guardian_of`, not
      an office-derived grant of any rung. The check runs before any edge is
      consulted, because an edge that could confer this would be the clause
      defeated by whoever holds the most of them.

    A missing author or subject is `UNKNOWN` and refuses (rule 13): an entry
    whose authorship nobody recorded is not thereby the office's to amend.
    `edges` and `at` are accepted and deliberately unused in the refusing
    branch — see the docstring of the branch itself.
    """
    if not (author_id or "").strip() or not (subject_id or "").strip():
        return MaySupersede(
            Supersession.UNKNOWN,
            "this entry records no author, or no lane subject; an entry whose "
            "authorship is unknown is not the office's to amend (I-7)")

    if principal_id == author_id:
        return MaySupersede(
            Supersession.PERMITTED,
            "the author supersedes their own entry")

    if author_id == subject_id:
        # The governed authored it. No edge is consulted on purpose: I-7's
        # authority is one "that no office-derived grant confers", so reading
        # `edges` here to look for a stronger one would be the clause defeated
        # by exactly the principal it binds hardest.
        return MaySupersede(
            Supersession.REFUSED,
            "I-7: this entry was authored by the lane's own subject about the "
            "office, and no office-derived grant confers authority to supersede "
            "it — entries authored by the governed are as durable as entries "
            "authored about them")

    if at is None:
        return MaySupersede(
            Supersession.UNKNOWN,
            "supersession is a dated act and no instant was supplied")

    standing = any(e.subject_id == subject_id and e.principal_id == principal_id
                   and e.live_at(at) and not (e.kind == SELF and not is_self_edge(e))
                   for e in edges)
    if not standing:
        return MaySupersede(
            Supersession.REFUSED,
            "no live edge to this lane's subject at this instant")
    return MaySupersede(
        Supersession.PERMITTED,
        "an office-authored entry, superseded by a principal with live standing")
