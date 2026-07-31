"""§7.1's court order, from arrival to every predicate that has to notice it.

The case the section is written against, run end to end: *an order restricting
Ann's standing over Ben, dated 14 March, delivered 2 October.* The assertion
that matters is not that any one predicate refuses — each of those already had
a test — but that **they all stop at the same instant, from one act**, and that
the record of what Ann did while she held standing is still there afterwards.

Every guard here has a mutation in `tests/ablate.py`. Stdlib only.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import (  # noqa: E402
    Edge, Field, Outcome, Principal, Rung, Widening, serve,
)
from records.crossing import Envelope, permits  # noqa: E402
from records.disclosure import Ledger  # noqa: E402
from records.orders import (  # noqa: E402
    Ended, GuardianshipState, NoGuardian, Order, OrderKind, end_guardianship,
    guardianship_of, past_exercise, supersede,
)
from records.receipts import held_by, issue  # noqa: E402
from records.sending import ContactRestriction, recipients, who_could_see  # noqa: E402
from records.standing import self_edge, widens  # noqa: E402

BEN, LB, SIB_LANE = "student-ben", "lane-ben", "lane-sibling"
ANN, DAD, AUNT = "g-ann", "g-dad", "g-aunt"

SEASON = datetime(2025, 8, 1)
FEBRUARY = datetime(2026, 2, 1)
MARCH = datetime(2026, 3, 14)      # the order's date — when it became true
JUNE = datetime(2026, 6, 1)        # a disclosure made in the gap
OCTOBER = datetime(2026, 10, 2)    # the day it reached the program
NOVEMBER = datetime(2026, 11, 1)

COURT = "Family Court, Montgomery County — order 26-DR-118"
KEY = b"an issuing key, held by the institution"


def ann(**kw) -> Edge:
    return Edge("guardian_of", ANN, BEN, SEASON, created_at=SEASON, **kw)


def dad(**kw) -> Edge:
    return Edge("guardian_of", DAD, BEN, SEASON, created_at=SEASON, **kw)


def me() -> Edge:
    return self_edge(BEN, valid_at=SEASON, created_at=SEASON)


def order(**kw) -> Order:
    base = dict(order_id="ord-118", authority=COURT, subject_id=BEN,
                principal_id=ANN, effective_at=MARCH, received_at=OCTOBER)
    base.update(kw)
    return Order(**base)


def health() -> Field:
    return Field(LB, BEN, "allergy", Rung.L4, category="health",
                 payload="tree-nut anaphylaxis; carries epinephrine",
                 instruction="one student on this vehicle carries an auto-injector")


def signed_by_ann() -> Widening:
    return Widening(BEN, "health", "the student asked to read their own file",
                    ANN, SEASON, SEASON + timedelta(days=800))


def envelope_signed_by_ann() -> Envelope:
    return Envelope(SIB_LANE, LB, "shared bus roster for the Dayton trip",
                    ANN, SEASON, SEASON + timedelta(days=800))


def a_ledger() -> Ledger:
    served = serve(health(), Principal("staff-nguyen", frozenset({"health"})),
                   [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)],
                   FEBRUARY)
    return Ledger().record(served, lane_id=LB, principal_id="staff-nguyen",
                           subject_id=BEN, field_name="allergy", at=FEBRUARY)


# --- the walkthrough --------------------------------------------------------


def test_the_order_lands_and_four_predicates_stop_together():
    """**The whole point of the module, in one test.** Ann loses messaging,
    receipts, envelope-signing and widening-signing at the same instant, from a
    single act. Nothing is separately switched off, which is the failure mode
    §7.1 names: *"a restricted guardian still on the SMS list receives a live
    location disclosure about a minor, pushed to a device, with no way to
    recall it."*"""
    before = (ann(), dad(), me())
    ending = end_guardianship(before, order())
    assert ending.applied, ending.reason
    after = tuple(ending)

    # 1 · messaging (G12). The send list is derived and Ann is not on it.
    who = recipients(BEN, after, (), NOVEMBER)
    assert tuple(who) == (DAD,), f"an ended guardian was still a recipient: {tuple(who)}"

    # 2 · receipts. Standing, not reachability — and the standing is gone.
    receipts = issue(a_ledger(), LB, BEN, after, NOVEMBER, KEY)
    assert {r.to_guardian for r in receipts} == {DAD}

    # 3 · a crossing signed by Ann no longer opens Ben's seal.
    assert permits([envelope_signed_by_ann()], from_lane=SIB_LANE, to_lane=LB,
                   at=NOVEMBER, subject_id=BEN, signer_edges=after) is None

    # 4 · a widening signed by Ann no longer lifts the self cap.
    assert widens([signed_by_ann()], subject_id=BEN, category="health",
                  at=NOVEMBER, signer_edges=after) is None
    lifted = serve(health(), Principal(BEN), after, NOVEMBER,
                   widenings=[signed_by_ann()])
    assert lifted.outcome is Outcome.INSTRUCTION, (
        "a widening outlived the standing of the guardian who signed it"
    )


def test_all_four_were_open_the_day_before_the_order_took_effect():
    """The companion assertion §7 insists on: *"any test asserting a restricted
    guardian sees nothing must sit beside one asserting an entitled guardian
    sees exactly what they should."* A predicate that refused everybody would
    pass the test above and fail this one."""
    live = (ann(), dad(), me())
    day_before = MARCH - timedelta(days=1)
    assert ANN in tuple(recipients(BEN, live, (), day_before))
    assert {r.to_guardian for r in issue(a_ledger(), LB, BEN, live, day_before, KEY)} \
        == {ANN, DAD}
    assert permits([envelope_signed_by_ann()], from_lane=SIB_LANE, to_lane=LB,
                   at=day_before, subject_id=BEN, signer_edges=live) is not None
    assert serve(health(), Principal(BEN), live, day_before,
                 widenings=[signed_by_ann()]).outcome is Outcome.PAYLOAD


def test_the_record_of_the_ended_guardians_exercise_survives():
    """I-7: *no office's Force extends to deleting entries about its own
    exercise.* The ending is Ann's office ending; it must not take Ann's record
    with it."""
    before = (ann(), dad(), me())
    after = tuple(end_guardianship(before, order()))

    assert len(after) == len(before), "the ending changed the size of the graph"
    assert {e.principal_id for e in after} == {e.principal_id for e in before}

    kept = past_exercise(after, ANN, BEN)
    assert len(kept) == 1, "the ex-guardian's edge is gone; refusal 3 broken"
    edge = kept[0]
    assert edge.invalid_at == MARCH
    assert edge.created_at == SEASON, "created_at was rewritten (§7.1)"
    assert edge.live_at(FEBRUARY), "history stopped being answerable (G2)"
    assert not edge.live_at(NOVEMBER)

    # And the receipts Ann already holds are still hers, and still verify.
    issued = issue(a_ledger(), LB, BEN, before, FEBRUARY, KEY)
    assert held_by(issued, ANN, LB), "an ending reached back and took the receipts"


def test_the_ending_names_the_authority_that_produced_it():
    """A date with no authority is a date nobody can answer for. *"Who could see
    Ben's medical form on October 12, and why"* has to answer for the ending as
    well as for the standing."""
    edge = past_exercise(tuple(end_guardianship((ann(), dad()), order())), ANN, BEN)[0]
    assert edge.ended_by and "26-DR-118" in edge.ended_by
    assert "ord-118" in edge.ended_by


def test_an_order_names_an_authority_or_it_is_not_an_order():
    for bad in ("", "   ", "system", "automation", "the director"):
        try:
            order(authority=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as the authority for an ending")


# --- the two clocks ---------------------------------------------------------


def test_the_ending_takes_the_orders_date_and_not_the_days_post():
    """§7.1's caveat, and the reason both axes are on the row. The restriction
    took effect on 14 March; the program learned on 2 October. Dating the ending
    from the envelope's arrival would make every disclosure in between look
    compliant."""
    edge = past_exercise(tuple(end_guardianship((ann(), dad()), order())), ANN, BEN)[0]
    assert edge.invalid_at == MARCH
    assert edge.ended_known_at == OCTOBER


def test_a_june_disclosure_evaluates_differently_on_each_axis():
    """G5. *What was true* and *what was known* are different questions about
    the same June instant, and both have to be retrievable from the row."""
    edge = past_exercise(tuple(end_guardianship((ann(), dad()), order())), ANN, BEN)[0]
    assert not edge.live_at(JUNE), "on what was true, Ann's standing had ended"
    assert edge.live_as_known_at(JUNE, horizon=JUNE), (
        "on what was known in June, the order had not arrived"
    )
    assert not edge.live_as_known_at(JUNE, horizon=NOVEMBER), (
        "asked after the order arrived, June answers the other way"
    )


def test_who_could_see_answers_across_the_ending():
    """G10, as a query rather than an investigation.

    Filtered to guardians deliberately: `who_could_see` reports every principal
    with live standing, and Ben's own `self` edge is one of them. That is the
    right answer to *"who could see this"* and it is not the question this test
    is asking."""
    after = tuple(end_guardianship((ann(), dad(), me()), order()))
    guardians = {ANN, DAD}
    before_rows = who_could_see(BEN, (ann(), dad(), me()), (), FEBRUARY)
    assert {p for p, ok, _ in before_rows if ok} & guardians == {ANN, DAD}
    after_rows = who_could_see(BEN, after, (), NOVEMBER)
    assert {p for p, ok, _ in after_rows if ok} & guardians == {DAD}


def test_a_restriction_and_an_ending_are_different_facts():
    """`records/sending.py` keeps standing and reachability apart on purpose. An
    order may restrict contact without ending guardianship, and this module
    ends guardianship without pretending to be a contact restriction — so a
    restricted-but-standing guardian still gets receipts."""
    block = ContactRestriction(ANN, BEN, MARCH, OCTOBER, authority=COURT)
    live = (ann(), dad())
    assert ANN not in tuple(recipients(BEN, live, [block], NOVEMBER))
    assert ANN in {r.to_guardian for r in issue(a_ledger(), LB, BEN, live, NOVEMBER, KEY)}, (
        "a contact restriction quietly revoked the right to audit a child's record"
    )


# --- what an order may not leave behind (I-7's asymmetry) -------------------


def test_an_order_may_not_leave_a_lane_with_nobody_answering_for_it():
    """Task 3's case. Ending the *only* guardianship with no successor and no
    declaration would leave the lane in `UNKNOWN` — not unguarded, but
    unanswered — and an office is not permitted to dissolve the record of its
    own exercise by walking away from the lane."""
    ending = end_guardianship((ann(), me()), order())
    assert ending.state is Ended.REFUSED
    assert ending.standing.state is GuardianshipState.UNKNOWN
    try:
        tuple(ending)
    except RuntimeError:
        return
    raise AssertionError("a refused ending iterated as a finished one")


def test_the_same_order_lands_once_the_lane_carries_a_named_state():
    """The refusal is not *"guardianship may not end"* — W-6 is explicit that a
    guardianship which cannot end was never guardianship. It is *"not into
    silence."* A named reason and a namer is all it takes."""
    said = NoGuardian(BEN, "ward of the county pending placement", "dana-reyes", MARCH)
    ending = end_guardianship((ann(), me()), order(declares=said))
    assert ending.applied, ending.reason
    state = guardianship_of(tuple(ending), BEN, NOVEMBER, (said,))
    assert state.state is GuardianshipState.UNGUARDED
    assert state.declared_by == "dana-reyes"
    assert "placement" in state.reason


def test_a_lane_with_no_guardian_and_no_declaration_is_unknown_not_unguarded():
    """Rule 13 on the relationship graph. `UNKNOWN` iterates as an error, so a
    caller cannot loop over it and conclude the lane is quiet."""
    state = guardianship_of((me(),), BEN, NOVEMBER)
    assert state.state is GuardianshipState.UNKNOWN
    assert state.guardians == ()
    try:
        tuple(state)
    except RuntimeError:
        return
    raise AssertionError("an unknown guardianship iterated as an empty one")


def test_a_declaration_needs_a_reason_and_a_person():
    for bad in (dict(reason=""), dict(declared_by=""), dict(declared_by="the director"),
                dict(declared_by="system")):
        kw = dict(subject_id=BEN, reason="ward of the county", declared_by="dana-reyes",
                  declared_at=MARCH)
        kw.update(bad)
        try:
            NoGuardian(**kw)
        except ValueError:
            continue
        raise AssertionError(f"a lane state was declared with {bad}")


# --- supersession -----------------------------------------------------------


def test_a_superseding_order_lands_the_successor_in_the_same_act():
    """I-7's supersession asymmetry, worked. A two-step *end, then remember to
    add* leaves the lane in `UNKNOWN` between the steps, and that window is one
    crash away from permanent."""
    ending = supersede((ann(), me()),
                       order(kind=OrderKind.SUPERSEDES, successor_id=AUNT))
    assert ending.applied, ending.reason
    after = tuple(ending)

    state = guardianship_of(after, BEN, NOVEMBER)
    assert state.state is GuardianshipState.GUARDED
    assert tuple(state) == (AUNT,)

    # And Ann's exercise is still on the record, dated, with its authority.
    kept = past_exercise(after, ANN, BEN)
    assert len(kept) == 1 and kept[0].invalid_at == MARCH and kept[0].ended_by


def test_a_superseding_order_that_names_nobody_is_refused_at_issuance():
    try:
        order(kind=OrderKind.SUPERSEDES)
    except ValueError:
        pass
    else:
        raise AssertionError("a supersession by nobody was issued")

    for bad in (ANN, BEN):
        try:
            order(kind=OrderKind.SUPERSEDES, successor_id=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as a successor guardian")


def test_supersede_refuses_an_order_that_is_not_a_supersession():
    ending = supersede((ann(), dad()), order())
    assert ending.state is Ended.REFUSED
    assert "supersede()" in ending.reason


def test_the_successor_edge_carries_both_clocks():
    after = tuple(supersede((ann(), me()),
                            order(kind=OrderKind.SUPERSEDES, successor_id=AUNT)))
    new = [e for e in after if e.principal_id == AUNT][0]
    assert new.valid_at == MARCH, "the successor's standing began at the post date"
    assert new.created_at == OCTOBER, "the successor edge lost its knowledge clock"


# --- the shapes an order must not have -------------------------------------


def test_an_order_carries_its_effect_and_never_its_contents():
    """`docs/LANE-MODEL.md` step 5: the order's contents are `L5` — enforced,
    never rendered, including to the director. The way this field arrives is
    somebody helpfully pasting the PDF, so its absence is asserted rather than
    trusted to the comment."""
    import dataclasses
    names = {f.name for f in dataclasses.fields(Order)}
    forbidden = {"contents", "findings", "text", "body", "payload", "document",
                 "scan", "attachment"}
    assert not (names & forbidden), f"an order can hold its own contents: {names & forbidden}"


def test_an_order_is_not_a_group_grant():
    """Refusal 5 and W-2: an order names one ward. There is no `subject_ids`,
    no pattern, and a blank subject is refused."""
    import dataclasses
    names = {f.name for f in dataclasses.fields(Order)}
    assert "subject_ids" not in names and "scope" not in names
    for bad in ("", "   "):
        try:
            order(subject_id=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as the ward an order names")


def test_a_subject_is_not_their_own_guardian():
    try:
        order(principal_id=BEN)
    except ValueError:
        return
    raise AssertionError("an order ended a guardianship the subject held over themselves")


# --- absence is unknown, not a result ---------------------------------------


def test_an_order_against_a_guardianship_this_graph_does_not_hold_is_unknown():
    """A delete-shaped API returns success for this and a caller cannot tell
    *ended* from *never existed*. Here it is a fact to look at."""
    ending = end_guardianship((dad(), me()), order())
    assert ending.state is Ended.UNKNOWN
    try:
        tuple(ending)
    except RuntimeError:
        return
    raise AssertionError("an order that matched nothing reported as applied")


def test_an_order_does_not_move_a_date_that_was_already_set():
    """Reinstatement and re-issue are real; silently moving the earlier date is
    the ledger lying about when the restriction began (SA-4)."""
    already = ann(invalid_at=FEBRUARY)
    ending = end_guardianship((already, dad()), order())
    assert ending.state is Ended.UNKNOWN
    assert past_exercise((already, dad()), ANN, BEN)[0].invalid_at == FEBRUARY


# --- not broken shut --------------------------------------------------------


def test_the_module_is_not_broken_shut():
    ending = end_guardianship((ann(), dad(), me()), order())
    assert ending.applied
    assert ending.standing.state is GuardianshipState.GUARDED
    assert tuple(ending.standing) == (DAD,)
    assert len(ending.ended) == 1
    assert guardianship_of((ann(), dad()), BEN, FEBRUARY).state is GuardianshipState.GUARDED


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
