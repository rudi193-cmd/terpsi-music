"""W-6, attempted: opening a lane without an exit, and exporting a partial past.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Rung  # noqa: E402
from records.exit import Lane, Threshold, open_lane, transfer  # noqa: E402

T0 = datetime(2026, 3, 1)
T9 = datetime(2030, 6, 1)
BEN = "student-ben"


def a_lane(**kw) -> Lane:
    base = dict(at=T0, threshold=Threshold.GRADUATION,
                exit_terms="At graduation, keys and full history issue to Ben; "
                           "guardian standing ends on the same date.")
    base.update(kw)
    return open_lane("lane-ben", BEN, **base)


def history():
    return [
        Field("lane-ben", BEN, "chair", Rung.L3, payload="trumpet 2"),
        Field("lane-ben", BEN, "allergy", Rung.L4, category="health", payload="tree nut"),
        Field("lane-ben", BEN, "attendance", Rung.L3, payload="present"),
    ]


def test_a_lane_cannot_be_opened_without_a_written_exit():
    """W-6's own sentence, enforced at construction. By graduation it is far
    too late to discover nobody wrote down what leaving means."""
    for terms in ("", "   ", "\n"):
        try:
            a_lane(exit_terms=terms)
        except ValueError as exc:
            assert "invalidly opened" in str(exc)
            continue
        raise AssertionError(f"a lane opened with exit_terms={terms!r}")


def test_the_exit_arguments_are_required_and_keyword_only():
    import inspect
    p = inspect.signature(open_lane).parameters
    for name in ("threshold", "exit_terms"):
        assert p[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert p[name].default is inspect.Parameter.empty, f"{name} grew a default"


def test_the_transfer_carries_the_whole_history_not_a_safe_subset():
    """*"An agent retired is retired **with** its record."* Nothing is filtered
    by rung on the way out — the subject is receiving their own past, and a
    tidied export is what W-6 exists to forbid."""
    t = transfer(a_lane(), entries=history(),
                 edges=[Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)], at=T9)
    assert len(t.entries) == 3, "the export dropped part of the history"
    assert t.highest_rung is Rung.L4, "the L4 field was filtered out of the subject's own record"
    assert t.complete


def test_a_transfer_with_no_history_is_refused():
    """An empty export that reports success is the fail-open here: the
    graduate is told they have their record and has nothing."""
    try:
        transfer(a_lane(), entries=[], edges=[], at=T9)
    except ValueError:
        return
    raise AssertionError("an empty transfer succeeded")


def test_standing_ends_and_is_not_deleted():
    """Refusal 3. The transfer reports which edges must be terminated by date;
    it does not rewrite them, because a silent rewrite leaves no dated record
    of the handover."""
    edges = [
        Edge("guardian_of", "g-mother", BEN, T0, created_at=T0),
        Edge("staff_of", "staff-nguyen", BEN, T0, created_at=T0),
    ]
    t = transfer(a_lane(), entries=history(), edges=edges, at=T9)
    assert set(t.ended_edges) == {("guardian_of", "g-mother"), ("staff_of", "staff-nguyen")}
    assert all(e.invalid_at is None for e in edges), "transfer() mutated the edges"


def test_the_subjects_own_standing_does_not_end_at_their_own_threshold():
    """The recipient keeps whatever standing they held. Ending the subject's
    own edge at the moment they inherit the lane would hand over the keys and
    revoke the lock in the same act."""
    edges = [
        Edge("guardian_of", "g-mother", BEN, T0, created_at=T0),
        Edge("staff_of", BEN, BEN, T0, created_at=T0),  # if a self edge ever exists
    ]
    t = transfer(a_lane(), entries=history(), edges=edges, at=T9)
    assert ("staff_of", BEN) not in t.ended_edges


def test_an_already_ended_edge_is_not_listed_again():
    ended = Edge("guardian_of", "g-father", BEN, T0, invalid_at=T0, created_at=T0)
    t = transfer(a_lane(), entries=history(), edges=[ended], at=T9)
    assert t.ended_edges == ()


def test_a_named_successor_may_receive_instead_of_the_subject():
    """W-6: *"to its subject **or named successor**."*"""
    t = transfer(a_lane(), entries=history(), edges=[], at=T9, to="estate-of-ben")
    assert t.to_whom == "estate-of-ben"


def test_the_exit_terms_travel_with_the_transfer():
    """The graduate receives the terms they were opened under, not the terms
    in force on the day they left — otherwise the exit is whatever the program
    most recently decided it was."""
    t = transfer(a_lane(), entries=history(), edges=[], at=T9)
    assert "keys and full history issue to Ben" in t.exit_terms


def test_the_module_is_not_broken_shut():
    assert a_lane().exit_terms
    assert transfer(a_lane(), entries=history(), edges=[], at=T9).complete


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
