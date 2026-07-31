"""The Ledger core: no card data, no visible waiver, no ranking, no invented zero.

The forbidden acts attempted here, each asserted to be refused: constructing a
payment that carries a card number (twice — by field and by smuggle), rendering
a waiver status to anyone including the director, publishing a per-section total
over a cohort of three, ordering two students by need, searching a roster by
balance, and reading a balance as `$0` because a source was down.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records import fees  # noqa: E402
from records.classify import classify  # noqa: E402
from records.conflict import Escalation, NotComputable, Stake  # noqa: E402
from records.fees import (  # noqa: E402
    WAIVER, Balance, CardData, Charge, FeeGroup, Membership, NotDisclosable,
    Payment, Source, Tender, allocate, assess, balance, looks_like_a_card_number,
    plan_priority, rank_by_need, reverse, roster_by_balance, total, waiver_rung,
)
from records.rungs import NEVER_SERVED, Rung  # noqa: E402
from records.serving import Edge, Field, Outcome, Principal, serve  # noqa: E402

BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"
SEASON = "2026-fall"
NOW = datetime(2026, 9, 1)
LATER = datetime(2026, 10, 1)

#: The standard band and the aid band. Nothing in either says which is which.
FULL = FeeGroup("band-a", "marching-season", 34000, SEASON)
REDUCED = FeeGroup("band-b", "marching-season", 0, SEASON)
BANDS = (FULL, REDUCED)


def member(subject, lane, group) -> Membership:
    return Membership(lane, subject, group.group_id, NOW, created_at=NOW)


def charge(subject=BEN, lane=LB, cents=34000) -> Charge:
    return Charge(lane, subject, "marching-season", cents, SEASON, NOW, created_at=NOW)


def payment(cents=10000, **kw) -> Payment:
    kw.setdefault("token_ref", "tok_9f4a2b")
    return Payment(LB, BEN, cents, Tender.CARD_TOKEN, NOW, "treasurer-ruiz",
                   SEASON, created_at=NOW, **kw)


# --- PCI: there is nowhere to put a card number ---------------------------


def test_a_payment_has_no_field_for_a_card_number():
    """**The forbidden construction.** The ordinary way to store a PAN is a
    field; there is not one, so the attempt fails at construction rather than
    being validated away."""
    names = {f.name for f in dataclasses.fields(Payment)}
    for banned in ("pan", "card_number", "cardnumber", "number", "cvv", "cvc",
                   "expiry", "exp_month", "exp_year", "track", "magstripe"):
        assert banned not in names, f"Payment grew {banned!r} — SAQ-A is gone"
    for banned in ("pan", "card_number", "cvv"):
        try:
            payment(**{banned: "4111111111111111"})
        except TypeError:
            continue
        raise AssertionError(f"Payment accepted a {banned!r} argument")


def test_a_pan_smuggled_into_the_field_that_does_exist_is_refused():
    """The interesting attack: no field for a PAN, so it goes in the token."""
    for field, value in (("token_ref", "4111111111111111"),
                         ("token_ref", "tok_4111 1111 1111 1111"),
                         ("reference", "4111-1111-1111-1111"),
                         ("memo", "paid by card 4111111111111111")):
        try:
            payment(**{field: value})
        except CardData as exc:
            assert field in str(exc)
            continue
        raise AssertionError(f"a card number was accepted in {field!r}")


def test_a_charge_refuses_card_data_too():
    """Every string field of every money record, not just the payment's token —
    closing one field leaves the memo line open, and the memo line is where it
    would actually go."""
    try:
        Charge(LB, BEN, "season fee 4111 1111 1111 1111", 34000, SEASON, NOW,
               created_at=NOW)
    except CardData:
        return
    raise AssertionError("a card number was accepted on a charge")


def test_the_pan_check_does_not_fire_on_ordinary_identifiers():
    """A guard that fails a UUID is a guard somebody removes on a Friday."""
    for ordinary in ("550e8400-e29b-41d4-a716-446655440000", "lane-ben",
                     "2026-fall", "check 10428", "tok_3MtwBwLkdIwHu7ix28a3tqPa",
                     "invoice 2026-0043"):
        assert not looks_like_a_card_number(ordinary), ordinary
    # And it does fire on the thing it is for.
    assert looks_like_a_card_number("4111 1111 1111 1111")


def test_a_card_payment_without_a_token_is_refused():
    try:
        Payment(LB, BEN, 100, Tender.CARD_TOKEN, NOW, "treasurer-ruiz", SEASON,
                created_at=NOW)
    except ValueError as exc:
        assert "token" in str(exc)
        return
    raise AssertionError("a card payment with no token was accepted")


def test_money_is_integer_minor_units():
    for bad in (340.00, 340.5, "34000", True):
        try:
            charge(cents=bad)  # type: ignore[arg-type]
        except TypeError:
            continue
        raise AssertionError(f"{bad!r} was accepted as money")


# --- the waiver: L5 by rule 3, and invisible by construction --------------


def test_a_waiver_status_classifies_at_L5_by_rule_3():
    """`SENSITIVITY.md` names *"a fee waiver taken"* as its own example of the
    rule. The rung is derived by the classifier, not asserted here."""
    c = classify(WAIVER)
    assert c.rung is NEVER_SERVED and c.via == "L5 rule 3"
    assert waiver_rung() is NEVER_SERVED


def test_a_waiver_status_is_served_to_nobody_including_the_director():
    """The forbidden read. `L5` is refused under any grant, to any principal —
    including a live edge, including the subject."""
    fld = Field(LB, BEN, "fee_waiver", waiver_rung(), category="money",
                payload="reduced band")
    director = Principal("director-shaw", frozenset({"money"}))
    edges = [Edge("director_of", "director-shaw", BEN, datetime(2020, 1, 1),
                  created_at=datetime(2020, 1, 1)),
             Edge("self", BEN, BEN, datetime(2020, 1, 1),
                  created_at=datetime(2020, 1, 1))]
    for who in (director, Principal(BEN, frozenset({"money"}))):
        got = serve(fld, who, edges, LATER, lane_id=LB)
        assert got.outcome is Outcome.REFUSED and got.value is None


def test_a_charge_has_no_waiver_column_and_no_second_amount():
    """*"There must be no place where the pre-waiver amount and the post-waiver
    amount both appear, because the difference is the disclosure."*"""
    names = {f.name for f in dataclasses.fields(Charge)}
    for banned in ("waiver", "waived", "discount", "discounted", "aid",
                   "scholarship", "standard_cents", "original_cents",
                   "full_cents", "list_cents", "reduced"):
        assert banned not in names, f"Charge grew {banned!r} — the difference is visible"


def test_the_charge_is_born_correct_and_the_two_students_rows_are_identical_in_shape():
    """Cal-ITP's mechanic: the aided student and the full-fee student produce the
    same row with a different number, and no field says which is which."""
    ms = [member(BEN, LB, REDUCED), member(ANA, LA, FULL)]
    ben = assess(BEN, LB, "marching-season", BANDS, ms, LATER, season=SEASON).charge
    ana = assess(ANA, LA, "marching-season", BANDS, ms, LATER, season=SEASON).charge
    assert ben.cents == 0 and ana.cents == 34000
    shape = lambda c: {f.name: (getattr(c, f.name) is None) for f in dataclasses.fields(c)}
    assert shape(ben) == shape(ana), "the two rows differ in shape, not only in amount"


def test_no_live_membership_is_unknown_and_not_the_standard_fee():
    """The fallback that would make the *absence* of a membership row mean
    something — which is a waiver boolean with a join in front of it.

    **The schedule here has exactly one band, and that is the load-bearing part
    of the fixture.** Written against the two-band schedule this file uses
    elsewhere, the assertion passed under a mutation that restored the fallback:
    the fallback produced *two* candidate bands, the ambiguity branch caught it,
    and the test agreed with `UNKNOWN` for a reason that had nothing to do with
    the rule it was checking. Found by ablation on 2026-07-31, which is the
    whole argument for rule 19 — the test could not fail.
    """
    for schedule in ((FULL,), BANDS):
        got = assess(BEN, LB, "marching-season", schedule, (), LATER, season=SEASON)
        assert got.state is Source.UNKNOWN, f"a fee was resolved from {len(schedule)} band(s)"
        assert "no live fee band" in got.reason, got.reason
        try:
            got.charge
        except RuntimeError as exc:
            assert "not zero" in str(exc)
            continue
        raise AssertionError("an unresolved fee produced a charge")


def test_an_errored_membership_source_is_unknown_never_a_price():
    """Rule 13 where it invoices a family: a network timeout must not bill the
    full season fee to a household on assistance."""
    def broken():
        raise ConnectionError("fee group store unreachable")

    got = assess(BEN, LB, "marching-season", BANDS, broken, LATER, season=SEASON)
    assert got.state is Source.UNKNOWN and "unreachable" in got.reason


def test_two_live_bands_are_escalated_rather_than_minimised():
    ms = [member(BEN, LB, REDUCED), member(BEN, LB, FULL)]
    got = assess(BEN, LB, "marching-season", BANDS, ms, LATER, season=SEASON)
    assert got.state is Source.UNKNOWN and "W-7" in got.reason


# --- the balance: unknown is never zero ----------------------------------


def test_a_balance_is_charges_less_payments_in_one_lane():
    b = balance([charge()], [payment(10000)], LATER)
    assert b.state is Source.DERIVED and b.cents == 24000 and b.owed


def test_an_errored_source_is_unknown_and_the_amount_raises():
    """**The classic harm.** A zero invented by a failure is a bill on one side
    and a shame on the other."""
    def broken():
        raise TimeoutError("ledger unreachable")

    for charges, payments, side in ((broken, [], "charge"), ([charge()], broken, "payment")):
        b = balance(charges, payments, LATER, lane_id=LB)
        assert b.state is Source.UNKNOWN
        assert side in b.reason
        try:
            b.cents
        except RuntimeError as exc:
            assert "not zero" in str(exc)
            continue
        raise AssertionError("an unknown balance produced a number")


def test_an_empty_result_from_an_unnamed_lane_is_not_a_balance_of_zero():
    b = balance([], [], LATER)
    assert b.state is Source.UNKNOWN
    b2 = balance([], [], LATER, lane_id=LB)
    assert b2.state is Source.DERIVED and b2.cents == 0


def test_a_balance_spanning_two_lanes_refuses():
    try:
        balance([charge(BEN, LB), charge(ANA, LA)], [], LATER)
    except NotComputable as exc:
        assert "lanes" in str(exc)
        return
    raise AssertionError("a balance was summed across two students")


def test_a_reversal_dates_the_payment_closed_and_never_deletes_it():
    p = payment(10000)
    closed = reverse(p, by="treasurer-ruiz", at=LATER, why="check returned unpaid")
    assert closed.invalid_at == LATER and closed.reversed_by == "treasurer-ruiz"
    assert closed.cents == 10000, "the original amount was rewritten"
    assert balance([charge()], [closed], LATER).cents == 34000


def test_a_reversal_without_a_reason_or_a_name_is_refused():
    for kw in ({"why": ""}, {"by": ""}):
        args = {"by": "treasurer-ruiz", "at": LATER, "why": "returned"}
        args.update(kw)
        try:
            reverse(payment(), **args)
        except ValueError:
            continue
        raise AssertionError(f"a reversal was accepted with {kw}")


# --- the aggregate: where the waiver actually leaks -----------------------


def test_a_section_of_three_cannot_publish_its_total():
    """**The worked harm.** Three students, one on a waiver, one per-section
    total — nobody named and the child identified."""
    section = [charge("s1", "l1", 34000), charge("s2", "l2", 34000),
               charge("s3", "l3", 0)]
    got = total(section, floor=5, at=LATER)
    assert got.cohort == 3 and got.rung is Rung.L4 and not got.servable
    try:
        got.cents
    except NotDisclosable as exc:
        assert "cohort of 3" in str(exc)
        return
    raise AssertionError("a section of three published its total")


def test_a_program_wide_total_clears_the_gate():
    many = [charge(f"s{i}", f"l{i}", 34000) for i in range(60)]
    got = total(many, floor=5, at=LATER)
    assert got.rung is Rung.L2 and got.servable and got.cents == 60 * 34000


def test_the_total_has_no_default_suppression_floor():
    """`classify.aggregate` has none and this must not add one — a default is
    how issuers stop declaring (I-6's argument, applied to `k`)."""
    p = inspect.signature(total).parameters
    assert p["floor"].default is inspect.Parameter.empty


# --- refusal 6 in money's clothes ----------------------------------------


def test_an_allocation_question_returns_an_escalation_and_never_an_order():
    got = allocate("one scholarship, four applicants", among=[BEN, ANA, "s3", "s4"],
                   to_whom="director-shaw", at=LATER,
                   considerations=["two are new families", "one applied twice"])
    assert isinstance(got, Escalation) and got.stake is Stake.BETWEEN_WARDS
    assert set(got.affects) == {BEN, ANA, "s3", "s4"}
    try:
        got.recommendation
    except NotComputable:
        return
    raise AssertionError("an allocation produced a recommendation")


def test_ranking_by_need_and_by_plan_priority_both_refuse():
    for fn in (rank_by_need, plan_priority):
        try:
            fn([BEN, ANA])
        except NotComputable as exc:
            assert "W-7" in str(exc)
            continue
        raise AssertionError(f"{fn.__name__} ordered two students")


def test_a_roster_filtered_by_balance_is_refused():
    """The openSIS widget, built as the failing test `scout-18` asked for."""
    try:
        roster_by_balance(minimum=1, maximum=100000)
    except NotDisclosable as exc:
        assert "monetary predicate" in str(exc)
        return
    raise AssertionError("a roster was filtered by money")


def test_the_module_offers_no_function_that_orders_students():
    """Static, over the module: nothing here sorts by an amount. A `sorted(...,
    key=…cents)` is a leaderboard of who is behind."""
    src = Path(fees.__file__).read_text(encoding="utf-8")
    for pattern in (r"sorted\(", r"\.sort\(", r"ORDER\s+BY"):
        assert not re.search(pattern, src, re.I), f"{pattern} appears in the ledger"


def test_the_module_deletes_nothing():
    src = Path(fees.__file__).read_text(encoding="utf-8")
    bad = re.findall(r"\b(DELETE\s+FROM|\.remove\(|\.pop\(|del\s+\w+\[)", src, re.I)
    assert not bad, f"a delete path appeared in the ledger: {bad}"


def test_the_module_is_not_broken_shut():
    """A companion who can genuinely see something, so the guarantees above are
    not passing vacuously (§7's own caveat about the indistinguishability test)."""
    ms = [member(BEN, LB, FULL)]
    got = assess(BEN, LB, "marching-season", BANDS, ms, LATER, season=SEASON)
    assert got.state is Source.DERIVED and got.charge.cents == 34000
    b = balance([got.charge], [payment(34000)], LATER)
    assert b.cents == 0 and not b.owed
    assert total([charge(f"s{i}", f"l{i}") for i in range(10)],
                 floor=5, at=LATER).servable


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
