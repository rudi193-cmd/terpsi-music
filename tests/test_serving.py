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
    #: Asserted as a *property* rather than as a position. This read
    #: `fields(Edge)[-1].name == "created_at"` until the ending's own clock was
    #: added beside it, and a positional assertion breaks on a field that is
    #: appended rather than on the thing it was checking — which is that
    #: `created_at` is required and keyword-only.
    spec = {f.name: f for f in dataclasses.fields(Edge)}
    assert spec["created_at"].kw_only
    assert spec["created_at"].default is dataclasses.MISSING, (
        "created_at grew a default; §7.1's second axis became optional"
    )
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


# --- W-3's default deny: the half the seal was missing ----------------------
#
# `docs/LANE-MODEL.md` listed this as stated-and-unenforced: *"the schema
# partitions; it does not enforce that a query stays in its lane."*


def ana_field(rung=Rung.L2, **kw) -> Field:
    base = dict(lane_id="lane-ana", subject_id="student-ana", name="call_time",
                rung=rung, payload="5:45pm at the band room",
                instruction="report at the posted time")
    base.update(kw)
    return Field(**base)


def ben_self() -> Edge:
    return Edge("self", BEN, BEN, SEASON, created_at=SEASON)


def test_a_ward_reading_another_wards_lane_is_denied_below_the_derive_floor():
    """**The forbidden act that used to succeed.** Two things had to line up and
    both are ordinary: a read that passes no `lane_id` never reached the seal at
    all, and an `L2` field needs no entitlement edge — so Ben was served Ana's
    call time with nothing consulted. W-3's opening words are *"Between wards,
    default deny."*"""
    s = serve(ana_field(), Principal(BEN), [ben_self()], SEASON)
    assert s.outcome is Outcome.REFUSED, (
        "a ward read another ward's lane entry; the seal is not rung-shaped"
    )
    assert "default deny" in s.reason


def test_the_ward_seal_is_not_rung_shaped():
    """It refuses at every rung, because the partition is not a sensitivity
    question. An `L1` fact that genuinely may be published does not need a lane
    entry to be read from."""
    for rung in (Rung.L1, Rung.L2, Rung.L3):
        s = serve(ana_field(rung=rung), Principal(BEN), [ben_self()], SEASON)
        assert s.outcome is Outcome.REFUSED, f"{rung} crossed the seal"


def test_naming_the_target_lane_as_the_origin_is_not_a_crossing():
    """A ward who names the lane they are reading *into* as their origin has
    named one lane twice, and `Envelope` refuses that at construction — so no
    envelope can ever match and the refusal is structural."""
    s = serve(ana_field(), Principal(BEN), [ben_self()], SEASON, lane_id="lane-ana")
    assert s.outcome is Outcome.REFUSED


def test_a_signed_envelope_is_still_the_sanctioned_path_for_a_ward():
    """The companion assertion. A clause that forbids without providing the
    sanctioned path is not the clause — so the legitimate sibling case has to
    work, from the ward's own lane, on a guardian's signature."""
    from records.crossing import Envelope

    ana_guardian = Edge("guardian_of", "g-mother", "student-ana", SEASON,
                        created_at=SEASON)
    env = Envelope(LANE, "lane-ana", "shared bus roster for the Dayton trip",
                   "g-mother", SEASON, LATER)
    s = serve(ana_field(), Principal(BEN), [ben_self(), ana_guardian], SEASON,
              lane_id=LANE, envelopes=[env])
    assert s.outcome is Outcome.PAYLOAD, s.reason
    assert "crossing permitted by envelope" in s.reason


def test_a_forged_self_edge_does_not_make_somebody_a_ward():
    """`is_self_edge`, not `kind == "self"`. The seal restricts rather than
    widens here, and letting a forged row decide either direction is one
    defect."""
    forged = Edge("self", "staff-nguyen", "student-ana", SEASON, created_at=SEASON)
    staff = Edge("staff_of", "staff-nguyen", "student-ana", SEASON, created_at=SEASON)
    s = serve(ana_field(rung=Rung.L3), Principal("staff-nguyen"), [forged, staff],
              SEASON)
    assert s.outcome is Outcome.PAYLOAD, (
        "a forged self edge made a staff member into a ward and sealed them out"
    )


def test_an_ended_self_edge_no_longer_seals_anybody_in():
    """Refusal 3, on the seal. A graduate whose `self` edge ended is not a ward,
    and the seal that follows from being one ends with it."""
    ended = Edge("self", BEN, BEN, SEASON, SEASON + timedelta(days=10),
                 created_at=SEASON)
    staff = Edge("staff_of", BEN, "student-ana", SEASON, created_at=SEASON)
    s = serve(ana_field(rung=Rung.L3), Principal(BEN), [ended, staff], LATER)
    assert s.outcome is Outcome.PAYLOAD


def test_a_guardian_of_both_siblings_is_not_a_ward_and_is_not_sealed_out():
    """The seal is *between wards*. A guardian holding edges to two children is
    not in a lane themselves and reads each lane on its own edge."""
    both = Edge("guardian_of", "g-mother", "student-ana", SEASON, created_at=SEASON)
    s = serve(ana_field(rung=Rung.L3), Principal("g-mother"), [both, guardian()],
              SEASON)
    assert s.outcome is Outcome.PAYLOAD


# --- the rung ceiling -------------------------------------------------------


def a_grant(**kw):
    from records import Grant
    base = dict(holder_id="staff-nguyen", lane_id=LANE, max_rung=Rung.L3,
                signed_by="dana-reyes", valid_at=SEASON,
                expires_at=SEASON + timedelta(days=200), created_at=SEASON)
    base.update(kw)
    return Grant(**base)


def staff() -> Edge:
    return Edge("staff_of", "staff-nguyen", BEN, SEASON, created_at=SEASON)


def test_a_grant_ceiling_below_the_field_refuses_the_payload():
    """`access_grant.max_rung` recorded the ceiling and nothing performed the
    comparison at serving time, which is exactly what made the column a ledger
    (§7.2's *say which*). The edge is a fact; the grant authorizes."""
    who = Principal("staff-nguyen", frozenset({"health"}))
    capped = serve(health_field(), who, [staff()], SEASON,
                   grants=[a_grant(max_rung=Rung.L3)])
    assert capped.outcome is Outcome.INSTRUCTION
    assert "grant ceiling" in capped.reason

    lifted = serve(health_field(), who, [staff()], SEASON,
                   grants=[a_grant(max_rung=Rung.L4, purpose="health")])
    assert lifted.outcome is Outcome.PAYLOAD


def test_an_empty_grant_table_is_not_an_unlimited_one():
    """The forbidden act: a principal with a live edge and no grant at all is
    served an `L3` payload. `()` means *consulted, and nothing found*."""
    s = serve(roster_field(), Principal("staff-nguyen"), [staff()], SEASON, grants=[])
    assert s.outcome is Outcome.INSTRUCTION
    assert "no live grant" in s.reason


def test_no_grant_table_and_an_empty_one_are_different_instructions():
    """Rule 13 in a signature. `None` says *no grant source was consulted*, `()`
    says *consulted and empty*; a single sentinel would have merged a fail-open
    with a fail-closed."""
    unconsulted = serve(roster_field(), Principal("staff-nguyen"), [staff()],
                        SEASON, grants=None)
    consulted = serve(roster_field(), Principal("staff-nguyen"), [staff()],
                      SEASON, grants=())
    assert unconsulted.outcome is Outcome.PAYLOAD
    assert consulted.outcome is Outcome.INSTRUCTION


def test_a_grant_over_another_lane_does_not_reach_this_one():
    s = serve(roster_field(), Principal("staff-nguyen"), [staff()], SEASON,
              grants=[a_grant(lane_id="lane-ana")])
    assert s.outcome is Outcome.INSTRUCTION


def test_an_expired_or_ended_grant_is_not_a_grant():
    for kw in ({"expires_at": SEASON + timedelta(days=1)},
               {"invalid_at": SEASON + timedelta(days=1)}):
        s = serve(roster_field(), Principal("staff-nguyen"), [staff()], LATER,
                  grants=[a_grant(**kw)])
        assert s.outcome is Outcome.INSTRUCTION, f"a grant survived {kw}"


def test_the_ceiling_composes_by_max_across_several_grants():
    who = Principal("staff-nguyen", frozenset({"health"}))
    s = serve(health_field(), who, [staff()], SEASON,
              grants=[a_grant(max_rung=Rung.L2),
                      a_grant(max_rung=Rung.L4, purpose="health")])
    assert s.outcome is Outcome.PAYLOAD


def test_l5_is_unreachable_through_a_grant_by_construction():
    """`access_grant_max_rung` omits `L5`, so a grant purporting to serve it
    fails at write time. The type fails at construction, for the same reason."""
    try:
        a_grant(max_rung=Rung.L5)
    except ValueError:
        return
    raise AssertionError("a grant was issued at L5")


def test_a_grant_cannot_name_a_group_or_a_wildcard_lane():
    """W-2 and refusal 5. A grant table with a single `NOT NULL` lane column
    cannot express a group; neither can this."""
    for bad in ("", "   ", "*", "all", "ANY", "every"):
        try:
            a_grant(lane_id=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as a lane in a grant")


def test_an_l4_grant_without_a_declared_purpose_is_not_a_grant():
    try:
        a_grant(max_rung=Rung.L4)
    except ValueError:
        pass
    else:
        raise AssertionError("an L4 grant issued with no purpose")


def test_a_grant_without_a_future_expiry_is_a_standing_grant():
    try:
        a_grant(expires_at=SEASON)
    except ValueError:
        return
    raise AssertionError("a grant with no future expiry was accepted (W-5)")


def test_an_unsigned_or_unheld_grant_is_refused():
    for kw in ({"signed_by": "  "}, {"holder_id": ""}):
        try:
            a_grant(**kw)
        except ValueError:
            continue
        raise AssertionError(f"a grant was built with {kw}")


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
