"""W-7, which was quoted in four documents and enforced by nobody.

**Found by inventory, 2026-07-31.** `records/conflict.py` had three ablation
mutations and no suite of its own — they all pointed at `tests/test_practice.py`,
because W-7 arrived while item 9 was being closed and its tests were written
where the work happened.

That is not a correctness gap: the guards were red. It is a *findability* gap,
and this repository has a name for the shape. Somebody grepping for what covers
W-7 finds a practice-logging suite, and the clause that says **the system
presents and a human decides** looks like a detail of streak counting. A clause
with no file of its own is one refactor from being moved somewhere worse.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.conflict import (  # noqa: E402
    Escalation, NotComputable, Stake, halt, refuse_to_rank,
)

BEN, ANA = "student-ben", "student-ana"
NOW = datetime(2026, 3, 20)


def test_an_escalation_cannot_carry_a_recommendation():
    """The refusal is structural: there is no field for an order and reaching
    for a recommendation gets the clause, not an AttributeError somebody papers
    over with getattr(..., None)."""
    e = halt(Stake.BETWEEN_WARDS, decision="last chair, trumpet",
             affects=[BEN, ANA], to_whom="dir-dana", at=NOW,
             considerations=["Ben has the earlier audition date",
                             "Ana covered the part in October"])
    assert "recommendation" not in {f.name for f in dataclasses.fields(Escalation)}
    try:
        e.recommendation
    except NotComputable as exc:
        assert "W-7" in str(exc)
        return
    raise AssertionError("an escalation produced a recommendation")


def test_considerations_are_unordered_so_they_cannot_be_handed_over_ranked():
    e = halt(Stake.BETWEEN_WARDS, decision="d", affects=[BEN, ANA],
             to_whom="dir-dana", at=NOW, considerations=["a", "b", "c"])
    assert isinstance(e.considerations, frozenset)


def test_the_staff_convenience_half_is_representable():
    """CLAUDE.md refusal 6 carries both halves and the second is the one that
    gets dropped: a rehearsal time or a route that is easier to run and worse
    for one student."""
    e = halt(Stake.WARD_VS_CONVENIENCE,
             decision="moving Tuesday sectionals to 6am to free the gym",
             affects=[BEN], to_whom="dir-dana", at=NOW)
    assert e.stake is Stake.WARD_VS_CONVENIENCE and e.affects == (BEN,)


def test_an_escalation_goes_to_a_named_person_never_a_role():
    for bad in ("staff", "the director", "an adult", "system", "  "):
        try:
            halt(Stake.WARD_VS_CONVENIENCE, decision="d", affects=[BEN],
                 to_whom=bad, at=NOW)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} received an escalation")


def test_a_collision_between_wards_names_two():
    try:
        halt(Stake.BETWEEN_WARDS, decision="d", affects=[BEN], to_whom="dir-dana",
             at=NOW)
    except ValueError:
        return
    raise AssertionError("one name was accepted as a collision between wards")


def test_an_escalation_must_say_what_was_being_decided():
    for bad in ("", "   "):
        try:
            halt(Stake.WARD_VS_CONVENIENCE, decision=bad, affects=[BEN],
                 to_whom="dir-dana", at=NOW)
        except ValueError:
            continue
        raise AssertionError("an escalation with no decision was accepted")


def test_refuse_to_rank_has_one_spelling():
    """Repeating an inline raise at each call site is how one of them ends up
    returning a sorted list during a busy afternoon."""
    try:
        refuse_to_rank("anything", [BEN, ANA])
    except NotComputable:
        return
    raise AssertionError("refuse_to_rank returned")


def test_the_module_is_not_broken_shut():
    e = halt(Stake.WARD_VS_CONVENIENCE, decision="6am sectionals", affects=[BEN],
             to_whom="dir-dana", at=NOW)
    assert e.affects == (BEN,) and e.stake is Stake.WARD_VS_CONVENIENCE


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
