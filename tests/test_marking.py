"""§18 item 7: the tap is authoritative, the score position is derived.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.marking import (  # noqa: E402
    P_ASSUMED, P_CITED, P_FITTED, P_MEASURED, Agreement, Mark, ScorePosition,
    align, drift, outranks, realign, shared,
)

BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"
SCORE = "malaguena-2026-rev3"
MOMENT = "show-2026-10-12@94500"


def tap(ms=94500, lane=None, subject=None, seat="press-box-4"):
    return Mark(MOMENT, ms, seat, lane, subject)


def pos(ms=94500, measure=41, beat=3.0, against=SCORE):
    return ScorePosition(measure, beat, against, ms, by="aligner-v1")


# --- the asymmetry that is the whole design -------------------------------


def test_a_mark_is_always_anchored_by_its_tap():
    m = tap()
    assert m.anchored and m.at_ms == 94500
    assert m.provenance == P_MEASURED


def test_a_score_position_cannot_claim_to_be_measured():
    """An alignment is a model's output. Letting it claim `P1` would make a bad
    alignment indistinguishable from an observation."""
    for claim in (P_MEASURED,):
        try:
            ScorePosition(41, 3.0, SCORE, 94500, provenance=claim)
        except ValueError:
            continue
        raise AssertionError(f"an alignment claimed {claim}")


def test_an_alignment_cannot_outrank_the_tap_it_was_derived_from():
    weak = Mark(MOMENT, 94500, "seat", provenance=P_ASSUMED)
    strong = ScorePosition(41, 3.0, SCORE, 94500, provenance=P_CITED)
    try:
        align(weak, strong)
    except ValueError:
        return
    raise AssertionError("a derived position outranked its own observation")


def test_aligning_adds_a_position_and_leaves_the_timecode_alone():
    m = tap()
    aligned = align(m, pos())
    assert aligned.at_ms == m.at_ms and aligned.position is not None
    assert m.position is None, "align() mutated the original"


def test_there_is_no_way_to_build_a_mark_anchored_only_by_score_position():
    """The design this module exists to refuse. `at_ms` has no default."""
    fields = {f.name: f for f in dataclasses.fields(Mark)}
    assert fields["at_ms"].default is dataclasses.MISSING
    assert fields["position"].default is None


# --- the named middle (rule 12) -------------------------------------------


def test_an_agreeing_alignment_reconciles():
    r = drift(align(tap(), pos(ms=94600)), score_in_force=SCORE)
    assert r.state is Agreement.AGREES and r.usable and r.drift_ms == 100


def test_a_diverged_alignment_says_so_rather_than_picking_a_half():
    r = drift(align(tap(), pos(ms=98000)), score_in_force=SCORE)
    assert r.state is Agreement.DIVERGED and not r.usable
    assert r.drift_ms == 3500 and "tap is what was observed" in r.reason


def test_an_unaligned_mark_is_usable_because_the_tap_is_the_anchor():
    r = drift(tap())
    assert r.state is Agreement.UNALIGNED and r.usable and r.drift_ms is None


# --- staleness, the common failure ----------------------------------------


def test_a_position_taken_against_an_edited_score_is_stale_even_when_it_agrees():
    """**Checked before drift, and that ordering is the point.** A position
    derived against a superseded score can agree perfectly and still point at a
    bar that no longer exists; reporting AGREES there is the more dangerous
    answer."""
    m = align(tap(), pos(ms=94500, against="malaguena-2026-rev2"))
    r = drift(m, score_in_force=SCORE)
    assert r.state is Agreement.STALE and not r.usable
    assert r.drift_ms == 0, "the halves agreed exactly and it is still stale"


def test_a_position_must_name_the_score_it_was_derived_against():
    for bad in ("", "   "):
        try:
            ScorePosition(41, 3.0, bad, 94500)
        except ValueError:
            continue
        raise AssertionError("a position with no score identity was accepted")


def test_realign_is_a_separate_verb_from_align():
    """Overwriting a position discards a previous claim. Giving it its own name
    means a call site cannot do it by accident."""
    stale = align(tap(), pos(against="rev2"))
    fixed = realign(stale, pos(against=SCORE))
    assert drift(fixed, score_in_force=SCORE).state is Agreement.AGREES
    assert stale.position.against == "rev2", "realign() mutated the original"


# --- W-3 and W-1 ----------------------------------------------------------


def test_a_shared_moment_is_two_lane_entries_with_one_referent():
    marks = (tap(lane=LB, subject=BEN), tap(lane=LA, subject=ANA),
             tap(lane=LB, subject=BEN))
    got = shared(MOMENT, marks)
    assert len(got) == 3 and {m.lane_id for m in got} == {LB, LA}


def test_there_is_no_function_producing_one_row_with_a_participant_list():
    """That row is the roster column W-1 forbids."""
    import records.marking as mod
    fields = {f.name for f in dataclasses.fields(Mark)}
    for banned in ("participants", "students", "roster", "subject_ids", "lane_ids"):
        assert banned not in fields
    assert not hasattr(mod, "merge") and not hasattr(mod, "flatten")


def test_a_mark_naming_a_student_is_lane_scoped():
    for lane, subject in ((LB, None), (None, BEN)):
        try:
            Mark(MOMENT, 1, "seat", lane, subject)
        except ValueError:
            continue
        raise AssertionError(f"lane={lane!r} subject={subject!r} was accepted")


def test_a_mark_about_the_ensemble_needs_no_lane():
    m = Mark(MOMENT, 1, "press-box-4")
    assert m.lane_id is None and m.subject_id is None


def test_a_mark_has_nowhere_to_rank_or_rate_a_student():
    fields = {f.name for f in dataclasses.fields(Mark)}
    for banned in ("score", "rating", "rank", "placement", "better_than", "quality"):
        assert banned not in fields


# --- rule 14 --------------------------------------------------------------


def test_provenance_never_compares_as_a_bare_integer():
    assert outranks(P_MEASURED, P_FITTED) and not outranks(P_FITTED, P_MEASURED)
    for bad in ("L3", "3", "P9", ""):
        try:
            outranks(bad, P_FITTED)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} compared as a P-rung")


def test_a_mark_records_the_seat_because_the_acoustic_model_needs_it():
    """§13: a judge's remark is anchored to a moment and a seat; the acoustic
    model predicts what arrived at that seat."""
    for bad in ("", "   "):
        try:
            Mark(MOMENT, 1, bad)
        except ValueError:
            continue
        raise AssertionError("a mark with no seat was accepted")


def test_the_module_is_not_broken_shut():
    m = align(tap(lane=LB, subject=BEN), pos())
    assert drift(m, score_in_force=SCORE).usable
    assert m.position.measure == 41


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
