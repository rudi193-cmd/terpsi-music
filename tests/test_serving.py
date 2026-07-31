"""The read predicate, and every forbidden act attempted against it.

`ARCHITECTURE.md` §10 and `PROTECTED_AGENTS.md` I-12: every invariant needs a
test that attempts the forbidden act and asserts refusal. This file is the first
in the repository where the forbidden act involves a student rather than a
document.

The mutation section at the end is the part that matters. A suite that only
asserts the predicate behaves cannot distinguish a working predicate from one
that refuses everything, or from one whose rules have been quietly widened — so
each guard is broken on purpose and the suite is required to notice.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_serving.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import (  # noqa: E402
    Edge, Field, Outcome, Principal, Rung, at_least, compose, outranks, parse, serve,
)

SEASON = datetime(2026, 3, 1)
LATER = SEASON + timedelta(days=90)
BEFORE = SEASON - timedelta(days=1)

BEN = "student-ben"
LANE = "lane-ben"


def guardian(at=SEASON, until=None) -> Edge:
    return Edge("guardian_of", "guardian-alvarez", BEN, at, until, created_at=at)


def judge() -> Edge:
    return Edge("judge_at", "judge-okonkwo", "event-saturday", SEASON, created_at=SEASON)


def roster_field(**kw) -> Field:
    base = dict(lane_id=LANE, subject_id=BEN, name="chair",
                rung=Rung.L3, payload="Ben Alvarez · trumpet 2",
                instruction="one member of this section")
    base.update(kw)
    return Field(**base)


def health_field(**kw) -> Field:
    base = dict(lane_id=LANE, subject_id=BEN, name="allergy",
                rung=Rung.L4, category="health",
                payload="epinephrine, tree-nut allergy",
                instruction="one student on this vehicle carries an auto-injector "
                            "in the blue medical bag; the trip binder names them")
    base.update(kw)
    return Field(**base)


# --- the ladder is not an integer -----------------------------------------


def test_rungs_cannot_be_compared_as_bare_integers():
    """Rule 14, enforced by the type rather than remembered by the author.

    `marching-arts` used `IntEnum`, so `band >= 3` was idiomatic there. Here
    the comparison must raise, which is what makes the rule structural."""
    try:
        Rung.L3 < Rung.L4  # noqa: B015
    except TypeError:
        pass
    else:
        raise AssertionError("Rung supports `<` — rule 14 is a convention again")
    assert str(Rung.L3) == "L3", "a rung must render with its prefix, never as a number"


def test_ordering_exists_but_only_through_named_calls():
    assert outranks(Rung.L4, Rung.L3)
    assert not outranks(Rung.L3, Rung.L4)
    assert at_least(Rung.L4, Rung.L3)
    assert at_least(Rung.L3, Rung.L3)


def test_composition_is_max_and_empty_is_an_error():
    """`SENSITIVITY.md`: composition is max everywhere, and a projection does
    not lower a rung. Composing nothing raises rather than returning `L1`,
    because an empty record defaulting to open is the fail-open direction."""
    assert compose(Rung.L1, Rung.L4, Rung.L2) is Rung.L4
    try:
        compose()
    except ValueError:
        pass
    else:
        raise AssertionError("compose() of nothing returned a rung")


def test_an_unresolvable_rung_is_not_defaulted_to_open():
    for bad in ("L9", "", "3", "open"):
        try:
            parse(bad)
        except ValueError:
            continue
        raise AssertionError(f"parse({bad!r}) resolved instead of refusing")
    assert parse("l3") is Rung.L3  # case-insensitive, still strict


# --- the forbidden acts ----------------------------------------------------


def test_a_judge_is_not_served_a_students_name():
    """§7.2's worked example. The judge holds an edge to the *event*, not to
    the student, so there is no entitlement edge to this subject."""
    s = serve(roster_field(), Principal("judge-okonkwo"), [judge()], SEASON)
    assert s.outcome is Outcome.INSTRUCTION
    assert s.value == "one member of this section"
    assert "Ben" not in (s.value or ""), "the judge was served a name"
    assert not s.disclosed


def test_a_guardian_is_served_their_own_childs_name():
    """The other half, and the reason §18 item 1a had to be decided scoped: an
    absolute reading would make this refuse, which cannot be the shipped
    behaviour of a roster application."""
    s = serve(roster_field(), Principal("guardian-alvarez"), [guardian()], SEASON)
    assert s.outcome is Outcome.PAYLOAD
    assert s.value == "Ben Alvarez · trumpet 2"
    assert s.via_edge == "guardian_of"


def test_an_expired_edge_is_not_an_edge():
    """§7.1: guardianship ends by setting `invalid_at`. A court order arriving
    mid-season is the case that proves it, and the read must honour the date
    without anyone remembering to revoke."""
    ended = guardian(until=SEASON + timedelta(days=10))
    s = serve(roster_field(), Principal("guardian-alvarez"), [ended], LATER)
    assert s.outcome is Outcome.INSTRUCTION, "an ended edge still served a payload"
    assert "no live entitlement edge" in s.reason


def test_an_edge_is_not_live_before_it_begins():
    s = serve(roster_field(), Principal("guardian-alvarez"), [guardian()], BEFORE)
    assert s.outcome is Outcome.INSTRUCTION


def test_l4_needs_a_declared_purpose_even_with_an_edge():
    """The chaperone case. An entitled principal without a declared medical
    purpose gets the instruction; the diagnosis was never on the screen."""
    staff = Principal("staff-nguyen")
    edges = [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)]
    s = serve(health_field(), staff, edges, SEASON)
    assert s.outcome is Outcome.INSTRUCTION
    assert "epinephrine, tree-nut allergy" not in (s.value or "")
    assert "auto-injector" in s.value, "the chaperone cannot act on this"

    declared = Principal("staff-nguyen", frozenset({"health"}))
    s2 = serve(health_field(), declared, edges, SEASON)
    assert s2.outcome is Outcome.PAYLOAD
    assert s2.via_purpose == "health"


def test_the_same_staff_member_ten_minutes_earlier_gets_nothing_extra():
    """§7.2: purpose is declared on entry, not inferred from the request. The
    same person on the same device under an attendance purpose does not get
    the medical payload."""
    attendance = Principal("staff-nguyen", frozenset({"attendance"}))
    edges = [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)]
    s = serve(health_field(), attendance, edges, SEASON)
    assert s.outcome is Outcome.INSTRUCTION


def test_l5_is_refused_to_everyone_including_the_entitled():
    """Enforcement-only means every principal, under any grant.

    **Asserts the reason, not only the outcome, and the difference is not
    cosmetic.** Ablating the `L5` check leaves this field still refused — by
    the missing-instruction rule further down — so an outcome-only assertion
    passes against a predicate that has stopped enforcing `L5` at all. That is
    `EXTERNAL-ARM.md`'s *"a gate green because a different constraint was
    catching it"*, found here by ablation rather than by reading.

    The predicate returns `reason` precisely so a caller can check *which* rule
    fired. This test is the first caller to use it for that.
    """
    order = roster_field(rung=Rung.L5, payload="contact restriction, court order 44-B",
                         instruction="a restriction applies to this student")
    for p, e in (
        (Principal("guardian-alvarez", frozenset({"health"})), [guardian()]),
        (Principal("director-shaw", frozenset({"health"})),
         [Edge("director_of", "director-shaw", BEN, SEASON, created_at=SEASON)]),
    ):
        s = serve(order, p, e, SEASON)
        assert s.outcome is Outcome.REFUSED, f"{p.id} was served an L5 field"
        assert s.value is None, "an L5 field yielded a value"
        assert "L5" in s.reason, (
            f"refused for the wrong reason ({s.reason!r}) — the L5 rule may not be firing"
        )


def test_a_sealed_lane_does_not_open_for_a_sibling():
    """W-3. The guardian holds a live edge to this student and still may not
    read them through another student's lane, because a crossing needs an
    envelope and there is no table for one."""
    s = serve(roster_field(), Principal("guardian-alvarez"), [guardian()],
              SEASON, lane_id="lane-sibling")
    assert s.outcome is Outcome.REFUSED
    assert "W-3" in s.reason


def test_an_unclassified_field_reads_as_unknown_not_as_open():
    """Rule 13. Absence surfaces as `unknown`, never as a result — and
    specifically never as `L1`."""
    s = serve(roster_field(rung=None), Principal("guardian-alvarez"), [guardian()], SEASON)
    assert s.outcome is Outcome.UNKNOWN
    assert s.value is None
    assert s.rung is None


def test_a_missing_instruction_refuses_rather_than_falling_back_to_the_payload():
    """The fail-open shape this predicate exists to prevent: no derived form
    authored must not mean 'serve the fact instead'."""
    s = serve(health_field(instruction=None), Principal("staff-nguyen"),
              [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)], SEASON)
    assert s.outcome is Outcome.REFUSED
    assert s.value is None


def test_a_refusal_and_an_absence_are_indistinguishable():
    """§7's indistinguishability guarantee. A student who declined and a
    student with nothing to declare must produce the same rows."""
    declined = health_field(payload="media release refused", instruction=None)
    absent = Field(lane_id=LANE, subject_id=BEN, name="allergy", rung=Rung.L4,
                   category="health", payload=None, instruction=None)
    p, e = Principal("staff-nguyen"), [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)]
    a, b = serve(declined, p, e, SEASON), serve(absent, p, e, SEASON)
    assert (a.outcome, a.value) == (b.outcome, b.value) == (Outcome.REFUSED, None)


def test_the_decision_carries_its_reason():
    """§7.2, narrate the read. A caller must be able to assert on *why*, and a
    log must have something to record beyond a boolean."""
    s = serve(health_field(), Principal("staff-nguyen", frozenset({"health"})),
              [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)], SEASON)
    assert s.reason and s.rung is Rung.L4 and s.via_edge == "staff_of"
    assert s.disclosed is True
    assert serve(roster_field(), Principal("nobody"), [], SEASON).disclosed is False


# --- mutation acceptance (rule 19) -----------------------------------------
#
# A suite that only asserts good behaviour cannot tell a working predicate from
# one broken shut, nor notice a rule quietly widened. Each mutation below
# breaks one guard and asserts this file would catch it.


def _serves_payload(fld, principal, edges, at=SEASON, lane=None) -> bool:
    return serve(fld, principal, edges, at, lane).outcome is Outcome.PAYLOAD


def test_the_predicate_is_not_broken_shut():
    """The negative control. A predicate that refuses everyone also refuses
    every forbidden act, and would pass every assertion above."""
    assert _serves_payload(roster_field(), Principal("guardian-alvarez"), [guardian()]), (
        "the permitted act is refused — every refusal test above is vacuous"
    )


def test_dropping_the_purpose_check_would_be_caught():
    """Mutant: L4 served on an edge alone. Confirm the suite's L4 test is the
    thing standing between that mutant and a green run."""
    staff = Principal("staff-nguyen")  # no declared purpose
    edges = [Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)]
    assert not _serves_payload(health_field(), staff, edges), (
        "L4 served without a declared purpose — the knock is not enforced"
    )


def test_dropping_the_date_check_would_be_caught():
    ended = guardian(until=SEASON + timedelta(days=10))
    assert not _serves_payload(roster_field(), Principal("guardian-alvarez"), [ended], LATER), (
        "an expired edge served a payload — §7.1 is not enforced at the read"
    )


def test_dropping_the_lane_seal_would_be_caught():
    assert not _serves_payload(roster_field(), Principal("guardian-alvarez"),
                               [guardian()], SEASON, "lane-sibling"), (
        "a cross-lane read succeeded — W-3 is not enforced"
    )


def test_promoting_l5_to_servable_would_be_caught():
    """Both halves: not served, and refused *by the L5 rule*. Without the
    second assertion this mutant survives — see the note on the L5 test."""
    order = roster_field(rung=Rung.L5, payload="court order 44-B",
                         instruction="a restriction applies")
    p = Principal("guardian-alvarez", frozenset({"health"}))
    assert not _serves_payload(order, p, [guardian()]), "L5 was served"
    assert "L5" in serve(order, p, [guardian()], SEASON).reason, (
        "L5 refused by some other rule — the never-served check is not firing"
    )


def test_defaulting_an_unclassified_field_to_open_would_be_caught():
    assert not _serves_payload(roster_field(rung=None),
                               Principal("guardian-alvarez"), [guardian()]), (
        "an unclassified field was served — rule 13 is not enforced"
    )


def test_the_subject_of_an_edge_is_checked_not_just_its_existence():
    """A principal holding a live edge to a *different* student must not read
    this one. W-2's 'a name is the scope' at the read rather than at issuance."""
    other = Edge("guardian_of", "guardian-alvarez", "student-other", SEASON, created_at=SEASON)
    assert not _serves_payload(roster_field(), Principal("guardian-alvarez"), [other]), (
        "an edge to another student served this student's payload"
    )


def test_an_edge_carries_the_second_clock_and_it_is_required():
    """§7.1: *"keep `created_at` immutable alongside the pair, and never update
    it."* It was absent from `Edge` until `records/sending.py` needed it — the
    second slice finding a defect in the first, which no amount of reading §7.1
    had surfaced.

    Required and keyword-only, so a five-argument positional call fails loudly
    instead of absorbing a date into `invalid_at` and meaning something else."""
    import dataclasses
    try:
        Edge("guardian_of", "g", BEN, SEASON, SEASON)  # 5 positional
    except TypeError as exc:
        assert "created_at" in str(exc)
    else:
        raise AssertionError("created_at is not required — §7.1's second axis is optional")

    e = Edge("guardian_of", "g", BEN, SEASON, created_at=SEASON)
    assert dataclasses.fields(Edge)[-1].name == "created_at"
    try:
        e.created_at = LATER  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("created_at was rewritable")


def test_the_read_path_honours_the_knowledge_horizon_like_the_send_path():
    """The read half of G5, and the reason the two predicates must agree.

    An edge the system had not yet learned of cannot have entitled a read that
    already happened. Asked *"what could this principal see in June"*, the
    answer depends on whether you mean *with June's knowledge* or *with what we
    know now* — and an audit of a disclosure that already went out needs the
    first."""
    learned_late = Edge("guardian_of", "guardian-alvarez", BEN, SEASON,
                        created_at=LATER)  # true since March, recorded in June
    with_todays_knowledge = serve(roster_field(), Principal("guardian-alvarez"),
                                  [learned_late], SEASON, known_as_of=LATER)
    assert with_todays_knowledge.outcome is Outcome.PAYLOAD

    as_known_then = serve(roster_field(), Principal("guardian-alvarez"),
                          [learned_late], SEASON, known_as_of=SEASON)
    assert as_known_then.outcome is Outcome.INSTRUCTION, (
        "a read was entitled by an edge the system had not yet learned of"
    )


def test_the_subjects_standing_is_an_edge_and_is_not_ambient():
    """§18 item 12, **closed 2026-07-30**. `records/standing.py` is canonical
    and `tests/test_standing.py` carries the guards; what remains here is the
    half that belongs to the predicate.

    The subject now holds standing in their own lane, and it is a `self` **edge**
    rather than a `principal.id == subject_id` special-case — so a subject
    arriving without one is refused exactly like anyone else, and the read that
    succeeds names the edge for the log to narrate.

    ---

    **What this test used to be, and why it is worth recording.** It asserted the
    old behaviour — the subject served *"one member of this section"* about their
    own name — with a tripwire meant to fire when a `self` edge appeared:

        assert not any(k in ("self", "subject_of")
                       for k in ("guardian_of", "staff_of"))

    That compares two hardcoded tuples. It is a tautology, it passed after the
    `self` edge shipped, and **it could never have failed** — §16's *cannot fire*
    mode, in the test written to detect the change. `willow-mcp` #211's fixture
    with no row the principal could not already see is the same defect, and this
    repository quoted that finding before committing it.
    """
    own = roster_field()

    without = serve(own, Principal(BEN), [], SEASON)
    assert without.outcome is Outcome.INSTRUCTION, (
        "the subject was served their own payload with no edge at all; standing "
        "became ambient rather than dated"
    )
    assert "no live entitlement edge" in without.reason

    with_edge = serve(own, Principal(BEN),
                      [Edge("self", BEN, BEN, SEASON, created_at=SEASON)], SEASON)
    assert with_edge.outcome is Outcome.PAYLOAD
    assert with_edge.via_edge == "self", (
        "the read did not name the edge that entitled it; §7.2 has nothing to narrate"
    )


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
