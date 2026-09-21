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

from dataclasses import dataclass, field as _field
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
