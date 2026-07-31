"""The ladder itself, which every other module imports and nothing tested.

**Found by inventory, 2026-07-31.** `records/rungs.py` had no test file and no
ablation mutation. Rule 14's central claim — `Rung.L3 < Rung.L4` raises — was
asserted once, in `tests/test_serving.py`, as an aside inside another module's
suite; `tests/test_sensitivity_ladder.py` tests `SENSITIVITY.md`, the document,
not the enum. So the one place an ordinal scale is *structurally* prevented from
comparing as a bare integer had no guard that had been shown to fail.

That is the same shape as four of the five `conform.py` checkers this week: a
thing everything depends on, passing by never being pointed at.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.rungs import (  # noqa: E402
    DERIVE_AT, NEVER_SERVED, Rung, at_least, compose, outranks, parse,
)

ALL = (Rung.L1, Rung.L2, Rung.L3, Rung.L4, Rung.L5)


# --- rule 14, made structural ---------------------------------------------


def test_no_two_rungs_compare_with_an_operator():
    """**The claim this module exists for.** `apps/marching-arts` used
    `IntEnum`, so its bands compared as bare integers by construction and
    `band >= 3` was idiomatic. Every ordering operator must raise here, on every
    pair — not just the one pair somebody thought to try."""
    for a in ALL:
        for b in ALL:
            for op, sym in ((lambda x, y: x < y, "<"), (lambda x, y: x > y, ">"),
                            (lambda x, y: x <= y, "<="), (lambda x, y: x >= y, ">=")):
                try:
                    op(a, b)
                except TypeError:
                    continue
                raise AssertionError(f"{a} {sym} {b} did not raise")


def test_a_rung_is_not_an_integer_and_will_not_arithmetic():
    for a in ALL:
        assert not isinstance(a, int), f"{a} is an int; the ladder is comparable"
        for other in (1, 3, 5):
            assert a != other
            try:
                a + other  # noqa: B018
            except TypeError:
                continue
            raise AssertionError(f"{a} + {other} produced a value")


def test_the_values_carry_no_order():
    """A value like `"3"` would re-admit ordering through the back door."""
    assert {r.value for r in ALL} == {"open", "internal", "attributed",
                                      "restricted", "enforcement_only"}
    for r in ALL:
        assert not r.value.isdigit()


def test_a_rung_prints_as_its_name_never_a_number():
    """Every reason string, log entry and export column renders through this.
    `str(Rung.L3)` returning `"Rung.L3"` or `"3"` would put the wrong token in
    a disclosure record."""
    assert [str(r) for r in ALL] == ["L1", "L2", "L3", "L4", "L5"]
    assert f"{Rung.L4}" == "L4"


# --- the only ordering that exists ----------------------------------------


def test_outranks_is_strict_and_total():
    for i, a in enumerate(ALL):
        for j, b in enumerate(ALL):
            assert outranks(a, b) is (i > j), f"outranks({a}, {b})"


def test_at_least_includes_the_floor():
    for i, a in enumerate(ALL):
        for j, b in enumerate(ALL):
            assert at_least(a, b) is (i >= j), f"at_least({a}, {b})"
    assert at_least(Rung.L3, Rung.L3) and not outranks(Rung.L3, Rung.L3)


def test_the_two_named_thresholds_are_where_the_rules_say():
    """`DERIVE_AT` and `NEVER_SERVED` are read by `serve()` on every call. A
    silent move either way changes what leaves the system."""
    assert DERIVE_AT is Rung.L3 and NEVER_SERVED is Rung.L5
    assert at_least(Rung.L3, DERIVE_AT) and not at_least(Rung.L2, DERIVE_AT)


# --- composition is max, and empty is not L1 ------------------------------


def test_composition_is_max_everywhere():
    assert compose(Rung.L1, Rung.L4, Rung.L2) is Rung.L4
    assert compose(Rung.L2) is Rung.L2
    assert compose(*ALL) is Rung.L5


def test_a_projection_cannot_lower_a_rung():
    """*"A record is the max of its fields; a projection does not lower a
    rung."* Dropping the sensitive field from a record does not make the record
    open — the composed value is taken over what it was made of."""
    full = compose(Rung.L4, Rung.L1)
    assert full is Rung.L4
    assert not outranks(Rung.L1, full)


def test_composing_nothing_raises_rather_than_returning_L1():
    """**The fail-open direction, refused.** An empty record defaulting to
    *open* is the one wrong answer here."""
    try:
        compose()
    except ValueError as exc:
        assert "not L1" in str(exc)
        return
    raise AssertionError("compose() of no rungs returned a value")


# --- parsing refuses rather than defaulting -------------------------------


def test_parse_round_trips_every_rung_and_tolerates_case():
    for r in ALL:
        assert parse(str(r)) is r
        assert parse(str(r).lower()) is r
        assert parse(f"  {str(r)}  ") is r


def test_parse_refuses_rather_than_defaulting_to_L1():
    """A silent downgrade to the least restricted value is the wrong failure
    direction for this column."""
    for bad in ("", "L0", "L6", "L", "3", "open", "restricted", "P3", "T2",
                None, 3, "l3x"):
        try:
            got = parse(bad)
        except ValueError:
            continue
        raise AssertionError(f"parse({bad!r}) returned {got}")


def test_parse_refuses_the_other_two_ladders_by_name():
    """§15's hazard: three five-level scales, and `P3` is not `L3`. This
    repository has already transplanted a citation across ladders once."""
    for foreign in ("P1", "P5", "T0", "T4"):
        try:
            parse(foreign)
        except ValueError:
            continue
        raise AssertionError(f"{foreign} parsed as an L-rung")


# --- the ladder cannot be widened by accident -----------------------------


def test_there_are_exactly_five_rungs():
    """`SENSITIVITY.md` defines five and migration 001 resolves against them. A
    sixth added here without the document is a field with nothing to classify
    against."""
    assert len(list(Rung)) == 5
    assert [r.name for r in Rung] == ["L1", "L2", "L3", "L4", "L5"]


def test_every_rung_is_ordered_exactly_once():
    """A rung missing from the internal order raises `ValueError` inside
    `outranks` rather than sorting oddly — but only if something asks. This
    asks."""
    for r in ALL:
        assert at_least(r, Rung.L1)
        assert at_least(Rung.L5, r)


def test_a_rung_survives_a_round_trip_through_storage():
    """Rungs land in logs, exports and receipts. Identity must survive."""
    for r in ALL:
        assert pickle.loads(pickle.dumps(r)) is r
        assert Rung(r.value) is r


def test_the_module_is_not_broken_shut():
    assert outranks(Rung.L5, Rung.L1)
    assert compose(Rung.L2, Rung.L3) is Rung.L3
    assert parse("L4") is Rung.L4


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
