"""W-7: where interests meet, the system halts. It does not compute a priority.

The clause at source (`willows-grove` `governance/PROTECTED_AGENTS.md` Part III,
blob `2886a41`; see `docs/PART-III-READ.md` for the read and its provenance):

> *"Where two wards' interests collide, or a ward's interest collides with the
> guardian's convenience, the steward **halts and escalates** — never computes a
> priority. **Resolutions accumulate as precedent the guardian may ratify into
> standing envelopes; none takes force without signature.**"*

**The second sentence was missing here until 2026-09-11, and this docstring
called the first one "at source" while it was.** It is the constructive half —
the sanctioned path through the prohibition — and W-3 lost the same half the
same way (`records/crossing.py`), which is why `tests/test_clause_quotes.py`
now holds both. What is implemented below is still only the halt: **there is no
`Precedent` type and no ratification path**, so the escalation learns nothing
from its own history. Named in `docs/PART-III-READ.md` rather than left to be
rediscovered, and the human register is explicit about what is missing —
*"watching your answers, learn to bring it to you better."*

CLAUDE.md's refusal 6 carries both halves, and the second is the one that gets
dropped: *"a rehearsal time, a route, or a section split that is easier to run
and worse for one student."* A tie-break between two students is the obvious
case. Staff convenience against one student is the frequent one.

**W-7 had no implementation anywhere in this repository** until this file — it
was quoted in four documents and enforced by nobody, which is rule 18's
distinction with nothing on the enforcement side. This is the type that makes
the refusal structural: the functions that would rank return an `Escalation`,
and an `Escalation` **cannot carry an order**. There is no field to put one in
and no accessor that yields one, so a caller cannot reach past the halt to a
ranking, the way `serve()` gives no path to a payload it did not decide to hand
over.

**What it does carry is what a human needs to decide**: who is affected, what
was being decided, what considerations were assembled, and who it went to. The
system presents. A named person decides, and §8.2's seal is how that decision
becomes real.

**Assembling considerations is not ranking them**, and the line matters because
a refusal that also refuses to be useful gets routed around. `considerations`
is an unordered `frozenset` of plain strings — the deciding human sees
everything relevant and no arrow pointing at an answer.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field, replace as _replace
from datetime import datetime
from enum import Enum
from typing import FrozenSet, Optional, Sequence, Tuple


class Stake(Enum):
    """What kind of collision this is. Both halves of refusal 6."""

    BETWEEN_WARDS = "between_wards"          # two students' interests meet
    WARD_VS_CONVENIENCE = "ward_vs_convenience"  # a student's against ease of running


class NotComputable(Exception):
    """Raised where a caller asked for the priority itself.

    Distinct from returning an `Escalation`: an escalation is the *answer* to a
    legitimate question about a conflict. This is what a request for the ranking
    gets, and it is an exception because a caller in that position has no
    sensible fallback and must be made to stop.
    """


@dataclass(frozen=True)
class Escalation:
    """A halt, with what a human needs in order to decide it.

    Deliberately incapable of expressing a priority. `affects` is sorted for
    stable display and carries no meaning in its order; `considerations` is a
    `frozenset` so it cannot be handed over pre-ranked.
    """

    stake: Stake
    decision: str            # what was being decided, in plain domain words
    affects: Tuple[str, ...]  # subject ids, sorted for display only
    to_whom: str             # a named person, never a role (§4.1, §8.2)
    raised_at: datetime
    considerations: FrozenSet[str] = _field(default_factory=frozenset)

    def __post_init__(self):
        if not (self.decision or "").strip():
            raise ValueError("an escalation must name what was being decided")
        if not self.affects:
            raise ValueError("an escalation must name who is affected")
        who = (self.to_whom or "").strip()
        if not who or who.lower() in _NOT_A_PERSON:
            raise ValueError(
                f"{self.to_whom!r} is not a person; W-7 escalates to a named human "
                "and a role is how an escalation reaches nobody"
            )
        if self.stake is Stake.BETWEEN_WARDS and len(set(self.affects)) < 2:
            raise ValueError(
                "a collision between wards names two; one name is not a collision"
            )

    @property
    def recommendation(self):
        """There is none, and asking is the error.

        A property rather than an absent attribute so the refusal is *legible*:
        a caller reaching for a recommendation gets the clause, not an
        `AttributeError` they will paper over with `getattr(..., None)`.
        """
        raise NotComputable(
            "W-7: the system presents and a human decides. There is no "
            "recommendation here and adding one would be the violation."
        )


_NOT_A_PERSON = frozenset({
    "system", "machine", "agent", "automation", "staff", "the staff",
    "director", "the director", "role:director", "the office", "office",
    "guardian", "the guardian", "someone", "an adult",
})


def halt(stake: Stake, *, decision: str, affects: Sequence[str], to_whom: str,
         at: datetime, considerations: Sequence[str] = ()) -> Escalation:
    """Raise a conflict to a named human instead of resolving it."""
    return Escalation(stake, decision, tuple(sorted(set(affects))), to_whom, at,
                      frozenset(c for c in considerations if (c or "").strip()))


def one_lane(rows: Sequence, what: str) -> str:
    """The single lane these rows belong to, or a refusal.

    **The structural half of W-7, and it was `records/practice.py`'s private
    `_one_lane` until a second module needed it.** That module's finding
    generalizes: every own-work statistic is a function of *one* lane's rows and
    every comparison needs two, so a ranking is unreachable through a function
    that refuses a mixed row set. It holds for practice minutes, for attendance
    counts, and for a balance — *"who owes the most"* is a ranking of students by
    money, and it is one `GROUP BY` away from an ordinary total.

    Promoted here rather than copied, in the commit that needed the second
    caller (rule 12). `refuse_to_rank` already lives in this module, this rule is
    enforced *by* it, and a second spelling of "read one lane" is the pair §16
    records four failures of.

    **Raises rather than filtering.** Silently dropping the other lanes' rows
    returns a number that looks like an own-lane statistic and is not — the same
    reason `receipts.gaps()` refuses a mixed sequence instead of picking one.

    `what` is required and is the caller's own words, because the refusal a
    reader sees should name the statistic that was attempted rather than the
    helper that stopped it.
    """
    lanes = {r.lane_id for r in rows}
    if len(lanes) > 1:
        refuse_to_rank(what, [getattr(r, "subject_id", "") for r in rows])
    if not lanes:
        raise ValueError(f"no rows; {what} needs a lane to be about")
    return next(iter(lanes))


def refuse_to_rank(what: str, affects: Sequence[str]) -> None:
    """Call this where a ranking was requested. It always raises.

    Present so the refusal has one spelling. Repeating an inline `raise` at each
    call site is how one of them ends up returning a sorted list during a busy
    afternoon.
    """
    raise NotComputable(
        f"W-7: {what} would order {len(set(affects))} students. The system "
        "presents and a human decides; use halt() to escalate."
    )


# --- W-7's constructive half: precedent, and its ratification ---------------
#
# The clause carries two halves and this repository dropped the second twice
# (`docs/PART-III-READ.md`): *"Resolutions accumulate as precedent the guardian
# may ratify into standing envelopes; none takes force without signature."* The
# halt above is the prohibition. Everything below is the sanctioned path through
# it — and building only the halt is exactly what item 2 of that read names:
# *"the escalation path halts forever and learns nothing."*


@dataclass(frozen=True)
class Precedent:
    """A resolved escalation, kept so a guardian may ratify it — never a rule
    the machine applies.

    What it is: a durable record of how a **named human** decided **one**
    conflict — the escalation it resolves, the resolution in plain words, who
    decided, and when — plus, once a guardian has signed it, that signature.
    `resolve()` records it; `ratify()` makes it *standing*.

    What it is **not**, and this is refusal 6 held one indirection later: an
    order for any *other* conflict. Like the `Escalation` it came from,
    `.recommendation` raises — a precedent does not rank a new collision or
    resolve it unattended, and a ratified one is the most tempting place to reach
    for *"so do that again."* The machine still halts on the next conflict.

    The only way a precedent touches a later conflict is `as_consideration()`,
    and it is deliberately the weakest touch there is: a standing precedent
    becomes a plain string in the next escalation's `considerations` — the
    unordered `frozenset` — alongside everything else relevant, with no arrow at
    an answer. *"They bring it to you — and, watching your answers, learn to
    bring it to you better"* is the system surfacing what a human decided before,
    never deciding for them. Assembling considerations is not ranking them, here
    as in `halt()`.

    **Unratified, it takes no force** — *"none takes force without signature."*
    `standing` is `False` until `signed_by` is set, and `as_consideration()`
    refuses a merely recorded precedent. That recorded/standing boundary is the
    same shape as W-5's `ProposedWidening`/`Widening` (`records/standing.py`),
    and `ratify()` below is its named middle (rule 12): the one path to a
    standing precedent runs through a guardian's signature.
    """

    escalation: Escalation
    resolution: str          # what the named human decided, in plain domain words
    decided_by: str          # the named human who decided, never a role (§8.2)
    decided_at: datetime
    signed_by: Optional[str] = None   # the ratifying guardian; None = recorded, not standing
    signed_at: Optional[datetime] = None

    def __post_init__(self):
        if not (self.resolution or "").strip():
            raise ValueError(
                "a precedent records how a conflict was decided; an empty "
                "resolution is a halt that was never actually resolved, and rule "
                "10 wants a rejection recorded as durably as an approval"
            )
        decider = (self.decided_by or "").strip()
        if not decider or decider.lower() in _NOT_A_PERSON:
            raise ValueError(
                f"{self.decided_by!r} is not a person; a W-7 resolution is a "
                "named human's decision and a role decided nothing (§8.2)"
            )
        if decider in self.escalation.affects:
            raise ValueError(
                "a ward may request, never authorize (W-4): an affected student "
                "cannot be recorded as the one who decided their own conflict"
            )
        if self.signed_by is not None:
            _check_ratifier(self.signed_by, self.escalation.affects)
            if self.signed_at is None:
                raise ValueError(
                    "a ratified precedent carries the instant it was signed; a "
                    "signature without a date is not a dated act (§7.1)"
                )

    @property
    def standing(self) -> bool:
        """Whether a guardian has ratified this into a standing envelope.

        *"None takes force without signature"* — an unratified precedent is
        history, and history binds nobody. This one bit decides whether
        `as_consideration()` will surface it at all.
        """
        return self.signed_by is not None

    @property
    def recommendation(self):
        """A precedent orders no future case, and asking is the error.

        The same refusal as `Escalation.recommendation`, and it has to live here
        too: a *ratified* precedent is precisely where a hurried caller reaches
        for *"then do that again,"* and honouring it would be the machine
        computing a priority from stored history — refusal 6, one hop later. A
        property rather than an absent attribute so the refusal is legible, not
        an `AttributeError` papered over with `getattr(..., None)`.
        """
        raise NotComputable(
            "W-7: a precedent records how one conflict was decided; it is not a "
            "ruling on this one. The system presents and a human decides."
        )


def _check_ratifier(signed_by: str, affects: Tuple[str, ...]) -> None:
    """A ratifying signature is a guardian's, and never an affected ward's.

    Shaped after `Widening`'s two signature checks (`records/standing.py`) and
    kept in one place so `ratify()` and `Precedent.__post_init__` cannot drift:
    a role cannot ratify (*"the guardian may ratify"*), and a student named in
    the conflict cannot ratify the precedent of their own conflict (W-4, *"a
    ward may request, never authorize"*).
    """
    name = (signed_by or "").strip()
    if not name or name.lower() in _NOT_A_PERSON:
        raise ValueError(
            f"{signed_by!r} is not a guardian's signature; a role cannot ratify "
            "a precedent (W-7: 'the guardian may ratify')"
        )
    if name in affects:
        raise ValueError(
            "a ward may request, never authorize (W-4): an affected student "
            "cannot ratify the precedent of their own conflict"
        )


def resolve(escalation: Escalation, *, resolution: str, decided_by: str,
            at: datetime) -> Precedent:
    """Record how a named human decided an escalation. This ratifies nothing.

    Returns a `Precedent` with no signature — recorded, not standing. It is
    §8.2's seal of the decision (a named human, a durable record), and by rule
    10 a rejection is recorded as durably as an approval: *"heard both, chose the
    earlier audition date"* and *"declined to split the section"* are both
    resolutions worth keeping. Making the resolution *stand* — so it may be cited
    in a future escalation — is a separate, signed act: `ratify()`.
    """
    return Precedent(escalation, resolution, decided_by, at)


def ratify(precedent: Precedent, *, signed_by: str, at: datetime) -> Precedent:
    """A guardian signs a recorded precedent into a standing one.

    The named middle (rule 12) between a recorded resolution and a standing
    envelope: the only path to `standing is True` runs through a guardian's
    signature, and `Precedent.__post_init__` (via `_check_ratifier`) is where
    that signature is checked — a role, or a ward named in the conflict, is
    refused there, in the one place the rule lives. It **reuses** the precedent's
    escalation, resolution, decider and time unchanged; a guardian ratifies what
    was decided, they do not restate it.

    *"None takes force without signature"* is this function existing at all:
    before it a resolution could only sit recorded, with no representation of a
    guardian having adopted it. Even after it, a standing precedent confers no
    authority to rank — it is a consideration for the next human, never a ruling.
    """
    return _replace(precedent, signed_by=signed_by, signed_at=at)


def as_consideration(precedent: Precedent) -> str:
    """A standing precedent, phrased for a future escalation's `considerations`.

    The *only* way a precedent reaches a later conflict, and deliberately the
    weakest one: a plain string that joins the unordered `frozenset` the deciding
    human reads. Surfacing *"a like collision in October was resolved by the
    earlier audition date"* helps a human decide; it does not decide, and it
    carries no arrow. That is *"learn to bring it to you better"* stopping short
    of refusal 6.

    **Refuses an unratified precedent** — *"none takes force without signature."*
    A merely recorded resolution has no standing to be cited as one, and letting
    it in here would be a precedent taking force without the signature the clause
    requires. `NotComputable` rather than a soft skip, because a caller citing
    unratified history as authority has made the W-7 error and must be stopped.
    """
    if not precedent.standing:
        raise NotComputable(
            "W-7: an unratified precedent takes no force and cannot be cited as "
            "one; a guardian must ratify() it before it stands as a consideration"
        )
    return (f"precedent ({precedent.decided_by}, {precedent.decided_at:%Y-%m-%d}): "
            f"{precedent.resolution}")
