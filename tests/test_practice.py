"""§18 item 9 and W-7: own work counts, students are never ordered.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.conflict import NotComputable  # noqa: E402
from records.practice import (  # noqa: E402
    THRESHOLDS, Milestone, Session, milestones, own, standings,
)

BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"
NOW = datetime(2026, 3, 20)


def days(lane, subject, first, n, minutes=60, gap=1):
    from datetime import timedelta
    return [Session(lane, subject, first + timedelta(days=i * gap), minutes)
            for i in range(n)]


# --- own work: a function of one lane -------------------------------------


def test_a_streak_counts_one_students_own_days():
    p = own(days(LB, BEN, date(2026, 3, 1), 5), as_of=date(2026, 3, 5))
    assert p.sessions == 5 and p.streak_days == 5 and p.longest_streak_days == 5


def test_a_broken_streak_is_not_current():
    """The flag-versus-date failure §7 already names, in a cheerful costume: a
    streak that ended in March must not read as live in October."""
    s = days(LB, BEN, date(2026, 3, 1), 5)
    p = own(s, as_of=date(2026, 6, 1))
    assert p.streak_days == 0 and p.longest_streak_days == 5


def test_hours_and_milestones_are_absolute_thresholds():
    s = days(LB, BEN, date(2026, 3, 1), 12, minutes=60)
    ms = milestones(s)
    assert [m.threshold_hours for m in ms] == [5, 10]
    assert all(m.lane_id == LB for m in ms)


def test_thresholds_are_fixed_and_not_derived_from_a_cohort():
    """The one substitution that would slip through everything else here: a
    threshold like *the top decile* or *an hour above average* is a ranking with
    a friendlier name."""
    assert THRESHOLDS == (5, 10, 25, 50, 100, 250)
    assert all(isinstance(t, int) for t in THRESHOLDS)


# --- the structural half: a ranking needs two lanes ------------------------


def test_a_statistic_spanning_two_lanes_refuses_rather_than_filtering():
    """**The finding item 9 turns on.** A leaderboard is not prose and no text
    rule can see one. But every own-work statistic reads one lane and every
    comparison needs two, so W-3's seal already forbids the ranking — the
    enforcement was structural and nobody had noticed."""
    mixed = days(LB, BEN, date(2026, 3, 1), 3) + days(LA, ANA, date(2026, 3, 1), 3)
    for fn in (own, milestones):
        try:
            fn(mixed)
        except NotComputable:
            continue
        raise AssertionError(f"{fn.__name__} computed across lanes")


def test_it_raises_rather_than_silently_dropping_the_other_lane():
    """A filtered version would return a number that looks like an own-work
    statistic and is not."""
    mixed = days(LB, BEN, date(2026, 3, 1), 3) + days(LA, ANA, date(2026, 3, 1), 9)
    try:
        own(mixed)
    except NotComputable as exc:
        assert "lanes" in str(exc)
        return
    raise AssertionError("a cross-lane aggregate returned a number")


def test_standings_exists_so_the_refusal_is_findable_by_name():
    """A missing name reads as *not built yet* and invites a local
    reimplementation; this raises with the clause attached."""
    try:
        standings(days(LB, BEN, date(2026, 3, 1), 2))
    except NotComputable as exc:
        assert "W-7" in str(exc)
        return
    raise AssertionError("standings() returned something")


# --- the log records shape, not content -----------------------------------


def test_a_session_has_nowhere_to_record_how_it_went():
    """A rating field would turn a log into an assessment record about a
    learner — UTETY's ground rule, and a reclassification the ladder treats far
    more carefully."""
    import dataclasses
    fields = {f.name for f in dataclasses.fields(Session)}
    assert fields == {"lane_id", "subject_id", "on", "minutes", "material"}
    for banned in ("rating", "quality", "score", "assessment", "tags", "how"):
        assert banned not in fields


def test_a_milestone_is_bound_to_a_lane_and_has_no_broadcast_form():
    """*"Ben reached fifty hours"* read by a section tells everyone else where
    they stand — §7's indistinguishability guarantee failing through a
    celebration."""
    import dataclasses
    fields = {f.name for f in dataclasses.fields(Milestone)}
    assert fields == {"lane_id", "threshold_hours", "reached_on"}
    for banned in ("cohort", "rank", "percentile", "recipients", "announce"):
        assert banned not in fields


def test_a_zero_length_session_is_not_a_session():
    for bad in (0, -30):
        try:
            Session(LB, BEN, date(2026, 3, 1), bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} minutes was accepted")


def test_the_module_is_not_broken_shut():
    p = own(days(LB, BEN, date(2026, 3, 1), 3), as_of=date(2026, 3, 3))
    assert p.minutes == 180 and p.streak_days == 3
    assert [m.threshold_hours for m in
            milestones(days(LB, BEN, date(2026, 3, 1), 6))] == [5]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}\n{exc}\n")
    raise SystemExit(1 if failures else 0)
