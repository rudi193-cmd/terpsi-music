"""D-4 acceptance: who gets a drop (`docs/PLAN-DROP.md` D-4).

Rule 19. D-4's forbidden act is preparing a drop for a restricted or lapsed
guardian. The test requires that such a guardian is absent from the prepared
set, and that the producer cannot be handed one — there is no `to` parameter to
reach past the predicate. Reuses `records/sending.py`'s dated predicate (§16).

Stdlib, `records/`, `drop/`. Runs under pytest or directly:

    python3 -m pytest tests/test_drop_preparing.py -q
    python3 tests/test_drop_preparing.py
"""

from __future__ import annotations

import inspect
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.sending import ContactRestriction, Standing  # noqa: E402
from records.serving import Edge  # noqa: E402

from drop.preparing import Prepared, PreparedDrops, prepare  # noqa: E402

BEN = "student-ben"
AUG = datetime(2025, 8, 1)
MAR = datetime(2026, 3, 1)
OCT = datetime(2026, 10, 1)


def mother() -> Edge:
    return Edge("guardian_of", "g-mother", BEN, AUG, created_at=AUG)


def father() -> Edge:
    return Edge("guardian_of", "g-father", BEN, AUG, created_at=AUG)


def ended_father() -> Edge:
    return Edge("guardian_of", "g-father", BEN, AUG, invalid_at=MAR, created_at=AUG)


def restraint() -> ContactRestriction:
    return ContactRestriction("g-father", BEN, MAR, MAR, authority="court order 44-B")


def seal_for(guardian_id: str) -> str:
    """A stand-in producer: the payload the drop would carry for one guardian."""
    return f"sealed-view-for-{guardian_id}"


def ids(prepared: PreparedDrops):
    return tuple(d.guardian_id for d in prepared)


# --- the happy path ---------------------------------------------------------


def test_every_reachable_guardian_gets_a_drop():
    prepared = prepare(BEN, [mother(), father()], [], MAR, seal_for=seal_for)
    assert prepared.state is Standing.DERIVED
    assert set(ids(prepared)) == {"g-mother", "g-father"}
    assert all(isinstance(d, Prepared) for d in prepared)
    assert prepared.drops[0].payload == seal_for(prepared.drops[0].guardian_id)


# --- forbidden act: a restricted guardian gets no drop ----------------------


def test_a_restricted_guardian_gets_no_drop():
    """D-4's forbidden act. The restricted guardian is derived out by the dated
    predicate and is absent from the prepared set — never prepared, so the
    producer is never handed them."""
    prepared = prepare(BEN, [mother(), father()], [restraint()], OCT, seal_for=seal_for)
    assert ids(prepared) == ("g-mother",), (
        f"a restricted guardian was prepared a drop: {ids(prepared)}")
    assert prepared.suppressed and prepared.suppressed[0][0] == "g-father"


def test_a_lapsed_guardian_gets_no_drop():
    """Guardianship that ended by `invalid_at` (refusal 3) is not a recipient of
    a drop, the same way it is not a recipient of a message."""
    prepared = prepare(BEN, [mother(), ended_father()], [], OCT, seal_for=seal_for)
    assert ids(prepared) == ("g-mother",), (
        f"a lapsed guardian was prepared a drop: {ids(prepared)}")


def test_the_producer_cannot_be_handed_a_recipient():
    """G4, for the prepare path. `prepare()` derives the set and takes no `to`;
    a caller cannot reach past the predicate by naming a guardian."""
    params = set(inspect.signature(prepare).parameters)
    forbidden = {"to", "recipient", "recipients", "guardian", "guardians", "send_to"}
    assert not (params & forbidden), (
        f"prepare() grew a recipient parameter: {sorted(params & forbidden)}")


# --- forbidden act: an unknown source is a refusal, not an empty set --------


def test_an_unknown_source_is_a_refusal_not_an_empty_set():
    """Fail-closed (rule 13). If the restriction source could not be consulted,
    the prepared set is UNKNOWN and iterating it raises — a drop prepared for
    nobody because a backend was down must not read as a student with no
    reachable guardians."""
    def broken():
        raise ConnectionError("the restriction backend is unreachable")

    prepared = prepare(BEN, [mother(), father()], broken, MAR, seal_for=seal_for)
    assert prepared.state is Standing.UNKNOWN
    try:
        list(prepared)
    except RuntimeError as exc:
        assert "not derived" in str(exc)
        return
    raise AssertionError("an UNKNOWN prepared set iterated as empty (rule 13)")


def test_a_student_with_no_reachable_guardians_is_still_derivable():
    """The other direction: a genuinely empty derived set is not an error, or the
    distinction from UNKNOWN collapses."""
    prepared = prepare(BEN, [], [], MAR, seal_for=seal_for)
    assert prepared.state is Standing.DERIVED
    assert list(prepared) == []


# --- negative control -------------------------------------------------------


def test_prepare_is_not_broken_shut():
    prepared = prepare(BEN, [mother()], [], MAR, seal_for=seal_for)
    assert ids(prepared) == ("g-mother",)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
