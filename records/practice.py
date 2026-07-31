"""§18 item 9: practice logging against the no-leaderboard rule.

§13 files this as a content question:

> *"UTETY's ground rule 2 is **feedback is about the work, never the learner** —
> no praise of the person, no leaderboards — with a policy test linting content
> against self-directed praise. The capability map proposes practice streaks,
> cumulative-hour milestones, and chair-challenge standings. Some of that is
> about the work and survives; some of it is a leaderboard with a different
> name."*

**Two things in that framing are wrong, and both make the item easier.**

**First, the standings half is not a UTETY question.** It is already forbidden
here, by CLAUDE.md refusal 6 and W-7: *never compute a priority between two
students.* Chair-challenge standings are exactly that, and a fleet ground rule
in a sibling app is the weaker of the two authorities. The item asked whether to
adopt someone else's policy while our own charter already refused it.

**Second, the content layer already covers its half.** `voice.py` refuses
`evaluative_praise`, `peer_comparison` and `ordering_two_students` in prose,
with a policy version stamped on every refusal. UTETY's lint has an equivalent
here and had one before this item was written.

**What neither covers is the gap this module is for: a leaderboard is not
prose.** It is a sorted list, and no text rule can see one. A `SELECT … ORDER BY
minutes DESC` produces no sentence for `voice.py` to refuse and no praise to
lint. The enforcement has to be structural, and it turns out the lane model
already supplies it:

> **A ranking requires reading N lanes, and W-3 seals them.** Every own-work
> statistic — streak, total, milestone — is a function of *one* lane's entries.
> Every comparison needs two. So the leaderboard is not forbidden by a policy
> that has to be remembered; it is unreachable through a predicate that already
> refuses cross-lane reads. §13 never noticed because it filed the question
> under content.

So the rule this module enforces is one line: **a practice statistic reads one
lane.** `conflict.one_lane()` is the middle, and it raises rather than
filtering, because a function that quietly dropped the other lanes' rows would
return a number that looks like an own-work statistic and is not. It lived here
as `_one_lane` until `records/attendance.py` and `records/fees.py` needed the
same rule; `_one_lane` is now this module's phrasing over the shared one.

**Milestones are addressed, never announced.** *"Ben reached fifty hours"* read
by a section is a comparison by implication — it tells everyone else where they
stand, which is §7's indistinguishability guarantee failing through a
celebration. So `milestone()` returns something bound to one lane and there is
no broadcast form.

**And the shape, not the content** (`ask-jeles`'s pattern): a session records
that work happened, for how long, on what material. It does not record how it
sounded. A practice log that grades the practising is the evaluative layer
UTETY's ground rule exists to keep out, arriving as telemetry.

Stdlib only. No network, no store.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Sequence, Tuple

from .conflict import one_lane, refuse_to_rank


@dataclass(frozen=True)
class Session:
    """One practice session. Shape, never content.

    `material` names what was worked on — a passage, an exercise, a drill set.
    There is deliberately no field for how it went: no rating, no self-assessed
    quality, no tags like *"rough"* or *"clean"*. Those turn a log into an
    assessment record about a learner, which is both UTETY's ground rule and a
    reclassification from `L2` to something the ladder treats far more
    carefully.
    """

    lane_id: str
    subject_id: str
    on: date
    minutes: int
    material: str = ""

    def __post_init__(self):
        if self.minutes <= 0:
            raise ValueError("a session with no duration is not a session")


def _one_lane(sessions: Sequence[Session]) -> str:
    """This module's words for `conflict.one_lane`, which used to live here.

    It moved on 2026-07-31, in the commit where `records/attendance.py` and
    `records/fees.py` became the second and third callers. The rule is the same
    one — *a statistic reads one lane* — and a copy per module is the pair rule
    12 forbids. What stays here is the phrasing, because a refusal should name
    the statistic that was attempted rather than the helper that stopped it.
    """
    return one_lane(sessions, "a practice statistic spanning lanes")


@dataclass(frozen=True)
class OwnPractice:
    """One student's own work. Every field is a function of their lane alone."""

    lane_id: str
    sessions: int
    minutes: int
    streak_days: int
    longest_streak_days: int

    @property
    def hours(self) -> float:
        return self.minutes / 60


def own(sessions: Sequence[Session], *, as_of: Optional[date] = None) -> OwnPractice:
    """Aggregate one student's practice. One lane in, one summary out."""
    lane = _one_lane(sessions)
    days = sorted({s.on for s in sessions})
    longest = current = 0
    prev: Optional[date] = None
    for d in days:
        current = current + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        longest = max(longest, current)
        prev = d

    # A streak is only live if it reaches the day being asked about. Counting a
    # streak that ended in March as current in October is the flag-versus-date
    # failure §7 already names, in a cheerful costume.
    live = 0
    if days and as_of is not None:
        if (as_of - days[-1]).days <= 1:
            live = current
    elif days:
        live = current

    return OwnPractice(lane, len(sessions), sum(s.minutes for s in sessions),
                       live, longest)


@dataclass(frozen=True)
class Milestone:
    """A fixed threshold reached, bound to the lane it belongs to.

    **Bound, not broadcast.** There is no cohort field and no recipient list
    beyond the lane, because *"Ben reached fifty hours"* read by a section tells
    everyone else where they stand — §7's indistinguishability guarantee failing
    through a celebration.
    """

    lane_id: str
    threshold_hours: int
    reached_on: date


#: Fixed and absolute. A threshold derived from a cohort — "the top decile", "an
#: hour above average" — is a ranking with a friendlier name, and it is the one
#: substitution that would slip through everything else here.
THRESHOLDS = (5, 10, 25, 50, 100, 250)


def milestones(sessions: Sequence[Session]) -> Tuple[Milestone, ...]:
    """Thresholds this student's own work has crossed, with the date each fell."""
    lane = _one_lane(sessions)
    out, running = [], 0
    hit = set()
    for s in sorted(sessions, key=lambda s: s.on):
        running += s.minutes
        for t in THRESHOLDS:
            if t not in hit and running >= t * 60:
                hit.add(t)
                out.append(Milestone(lane, t, s.on))
    return tuple(out)


def standings(sessions: Sequence[Session]) -> None:
    """There are none. Present so the refusal is findable by name.

    Someone will look for this function — the capability map proposes it, and a
    missing name reads as *not built yet* rather than *refused*. An
    `ImportError` invites a local reimplementation; this raises with the clause
    attached.
    """
    refuse_to_rank("practice standings", [s.subject_id for s in sessions])
