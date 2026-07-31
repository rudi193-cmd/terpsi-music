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
from typing import Optional, Sequence, Tuple

from .crossing import _NOT_A_PERSON
from .disclosure import Entry, Log
from .rungs import Rung
from .serving import Edge

#: The edge kind. A string rather than an enum because §7's other four kinds are
#: strings and a mixed vocabulary is worse than a plain one.
SELF = "self"

#: The rung a `self` edge reaches before the threshold. Above it, a guardian's
#: signature is required per category.
SELF_CAP = Rung.L3

_WILDCARDS = frozenset({"*", "all", "any", "every", ""})


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


def widens(widenings: Sequence[Widening], *, subject_id: str,
           category: Optional[str], at: datetime,
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
    """
    if not category:
        return None
    for w in widenings:
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
