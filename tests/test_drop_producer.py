"""D-1 acceptance: the sealed guardian view (`docs/PLAN-DROP.md` D-1).

Rule 19: every invariant has a test that attempts the forbidden act and asserts
the refusal. D-1's forbidden act is a payload that names or resolves to a second
student; the second is fail-closed — a producer without its key material must
land nothing rather than a plaintext payload.

Stdlib, `records/`, `presentation/`, `drop/`. Runs under pytest or directly:

    python3 -m pytest tests/test_drop_producer.py -q
    python3 tests/test_drop_producer.py
"""

from __future__ import annotations

import inspect
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.atrest import Keyring, new_master, open_lane_key, unseal_with  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Outcome, Serving  # noqa: E402

from presentation.ir import Row, cell, view  # noqa: E402
from presentation.markup import document  # noqa: E402

from drop.producer import (STYLESHEET, Made, Production, TwoStudents,  # noqa: E402
                           produce)

AT = datetime(2026, 7, 31, 9, 0)


def _row(subject: str, lane: str, value: str) -> Row:
    c = cell(Serving(Outcome.PAYLOAD, value, Rung.L2, "entitled for this guardian"),
             label="placement")
    return Row(heading=f"lane {lane}", cells=(c,), referent=subject, lane_id=lane)


def one_student_view(subject: str = "student-ben"):
    return view("Ben — guardian view", [_row(subject, "lane-ben", "First chair, trumpet")],
                read_by="g-mother", at=AT)


def two_student_view():
    return view("two students in one view",
                [_row("student-ben", "lane-ben", "First chair"),
                 _row("student-maria", "lane-maria", "Second chair")],
                read_by="g-x", at=AT)


def a_lane_key(lane: str = "lane-ben"):
    keyring, lane_key = open_lane_key(Keyring(), lane_id=lane, master=new_master(), at=AT)
    return lane_key


# --- the happy path: one student, sealed and recoverable --------------------


def test_a_single_student_view_seals_and_round_trips():
    lane_key = a_lane_key()
    v = one_student_view()
    prod = produce(v, lane_key_source=lambda: lane_key, at=AT)
    assert prod.state is Made.SEALED and prod.landed
    assert prod.sealed is not None and prod.sealed.lane_id == "lane-ben"
    # The sealed plaintext is the rendered guardian view, and it opens.
    opening = unseal_with(prod.sealed, lane_key=lane_key)
    assert opening.opened, opening.reason
    assert opening.plaintext == document(v, stylesheet=STYLESHEET, mode="screen").encode("utf-8")


# --- forbidden act 1: a second student in one payload -----------------------


def test_a_two_student_view_is_refused_before_sealing():
    """D-1's forbidden act. A view naming two students would put two students
    under one lane key; it is refused before any ciphertext exists."""
    lane_key = a_lane_key()
    try:
        produce(two_student_view(), lane_key_source=lambda: lane_key, at=AT)
    except TwoStudents:
        return
    raise AssertionError(
        "a two-student view was sealed — one lane, one student (W-1/W-3) is not enforced")


def test_the_refusal_is_structural_not_a_flag_on_the_row():
    """There is no roster column to carry a second student: the IR refuses a
    participant list on a Row, so the second student can only arrive as a second
    Row with a distinct referent, which is exactly what _one_student catches."""
    from presentation.ir import Row as IRRow
    assert "referent" in inspect.signature(IRRow).parameters
    for forbidden in ("participants", "roster", "students", "subjects"):
        assert forbidden not in inspect.signature(IRRow).parameters, (
            f"Row grew a {forbidden!r} field — a roster column defeats W-3")


# --- forbidden act 2: fail-closed without key material ----------------------


def test_no_sealing_primitive_lands_nothing_not_a_plaintext():
    """Acceptance test 2. Started without the primitive usable, the producer
    refuses and lands nothing — never a plaintext or empty payload (rule 13)."""
    lane_key = a_lane_key()
    prod = produce(one_student_view(), lane_key_source=lambda: lane_key, at=AT,
                   available=lambda: False)
    assert prod.state is Made.UNAVAILABLE
    assert prod.sealed is None, "an unavailable production carried a payload"
    assert "primitive" in prod.reason.lower()


def test_a_key_source_that_raises_is_unavailable_not_sealed():
    """The other fail-closed axis: the lane key material could not be obtained.
    A source that raises surfaces as UNAVAILABLE, never as a seal that happened
    anyway (rule 13)."""
    def no_key():
        raise RuntimeError("the master is on a box that is not answering")

    prod = produce(one_student_view(), lane_key_source=no_key, at=AT)
    assert prod.state is Made.UNAVAILABLE
    assert prod.sealed is None


def test_the_primitive_is_checked_before_the_view_is_touched():
    """Order matters: a box that cannot seal lands nothing before it even reads
    a view, so an unavailable box does not raise TwoStudents on a bad view — it
    is unavailable first. Fail-closed is the outer guard."""
    prod = produce(two_student_view(), lane_key_source=a_lane_key, at=AT,
                   available=lambda: False)
    assert prod.state is Made.UNAVAILABLE


# --- the Production invariant (absence is its own state) ---------------------


def test_a_production_cannot_be_sealed_with_no_payload():
    try:
        Production(Made.SEALED, None, "nothing")
    except ValueError:
        pass
    else:
        raise AssertionError("a SEALED production with no payload was constructible")


def test_an_unavailable_production_cannot_carry_a_payload():
    lane_key = a_lane_key()
    good = produce(one_student_view(), lane_key_source=lambda: lane_key, at=AT)
    try:
        Production(Made.UNAVAILABLE, good.sealed, "leaked")
    except ValueError:
        return
    raise AssertionError("an UNAVAILABLE production carried a payload — the "
                         "plaintext fallback fail-closed forbids")


# --- negative control -------------------------------------------------------


def test_the_producer_is_not_broken_shut():
    """Every refusal above is vacuous if nothing ever seals."""
    lane_key = a_lane_key()
    assert produce(one_student_view(), lane_key_source=lambda: lane_key,
                   at=AT).state is Made.SEALED


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
