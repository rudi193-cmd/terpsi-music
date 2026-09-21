"""§9 item 9: the commentary primitive, the guest session, the transcript seam.

Every invariant gets a test that attempts the forbidden act and asserts refusal
(rule 19). The ones that only assert the module works are marked as such and are
there so a module broken shut cannot pass by refusing everything.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.commentary import (  # noqa: E402
    KIND, KNOCK_FIELD_NAMES_KNOWN, NARRATION, SA3_CLAUSE, TRANSCRIPT_CLASSES,
    TRANSCRIPT_RUNG, Addressed, Capture, Declaration, ExitState, GuestSession,
    Pending, Remark, StandingScore, Transcript, TranscriptState, Unlaned,
    Unsealed, capture, close, compare, fan_out, knock, log_capture, observed,
    pending_from, reconcile_exit, refuse_standing_score, release, to_draft,
    transcribe,
)
from records.conflict import NotComputable  # noqa: E402
from records.disclosure import Ledger  # noqa: E402
from records.inference import (  # noqa: E402
    LocalModelUnavailable, NonLocalInference, OffBoxLocalModel, Unclassified,
    UnknownProvider,
)
from records.marking import (  # noqa: E402
    P_ASSUMED, P_CITED, P_FITTED, P_MEASURED, Mark, ScorePosition, align, drift,
)
from records.rungs import Rung  # noqa: E402
from records.sealing import State, reject, seal  # noqa: E402
from records.serving import Edge, Principal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"
JUDGE = "Priya Raghunathan"
JUDGE_ID = "judge-raghunathan"
MOMENT = "show-2026-10-12@94500"
EVENT = "event-42"
SCORE = "malaguena-2026-rev3"
SEAT = "press-box-4"
LOCAL = "http://localhost:11434"

T0 = datetime(2026, 10, 12, 19, 0)
T1 = datetime(2026, 10, 12, 19, 5)
T2 = datetime(2026, 10, 12, 20, 0)

WORDS = "the entrance was under the pulse and the release was ragged"


def tap(ms=94500, lane=None, subject=None, seat=SEAT, prov=P_MEASURED,
        referent=MOMENT):
    return Mark(referent, ms, seat, lane, subject, None, prov)


def laned(subject=BEN, lane=LB, **kw):
    return tap(lane=lane, subject=subject, **kw)


def sealed_remark(remark=None, by=JUDGE, at=T1):
    r = remark if remark is not None else capture(laned(), WORDS, by=JUDGE)
    return r, seal(to_draft(r), by=by, at=at)


# ===========================================================================
# 1. The primitive
# ===========================================================================


def test_a_remark_is_anchored_by_a_mark_and_adds_no_second_timecode():
    """§18 item 7's anchor is reused, not re-spelled."""
    r = capture(laned(), WORDS, by=JUDGE)
    assert r.anchor.at_ms == 94500 and r.anchor.seat == SEAT
    assert not hasattr(r, "at_ms"), "a second spelling of the location"
    assert not hasattr(r, "seat"), "a second spelling of the seat"
    assert r.referent == MOMENT


def test_a_remark_carries_the_marks_derived_position_untouched():
    """Not a refusal: the module must not be broken shut. `drift()` still works."""
    m = align(laned(), ScorePosition(41, 3.0, SCORE, 94500, by="aligner-v1"))
    r = capture(m, WORDS, by=JUDGE)
    assert drift(r.anchor, score_in_force=SCORE).usable
    assert r.anchor.position.measure == 41


def test_a_remark_with_no_words_is_refused():
    """Rule 13: an empty body is absence, not a remark."""
    for bad in ("", "   ", "\n"):
        try:
            capture(laned(), bad, by=JUDGE)
        except ValueError:
            continue
        raise AssertionError(f"a remark with body {bad!r} was accepted")


def test_a_person_made_remark_must_name_the_person():
    """§8.2: a role is not a signature and an unattributed remark is a machine's."""
    for mode in (Capture.LIVE_TAP, Capture.POST_HOC):
        try:
            Remark(laned(), WORDS, "", mode)
        except ValueError:
            continue
        raise AssertionError(f"an unattributed {mode.value} remark was accepted")


def test_a_machine_remark_cannot_be_attributed_to_the_judge():
    """Rule 10: the transcript is the machine's guess, not the judge's words."""
    try:
        Remark(laned(), WORDS, JUDGE, Capture.MACHINE)
    except ValueError as exc:
        assert JUDGE in str(exc)
        return
    raise AssertionError("a machine transcription was attributed to a person")


def test_a_capture_mode_is_required_and_a_string_is_not_one():
    """The provenance is derived from it, so it cannot be a free string."""
    for bad in ("live_tap", None, 1, "P1"):
        try:
            Remark(laned(), WORDS, JUDGE, bad)
        except ValueError:
            continue
        except (KeyError, TypeError) as exc:
            raise AssertionError(
                f"capture={bad!r} reached the provenance table and failed there "
                f"({type(exc).__name__}); the check must name what is wrong")
        raise AssertionError(f"capture={bad!r} was accepted")


def test_provenance_follows_the_capture_and_never_a_bare_integer():
    """Rule 14: the P-ladder, prefixed, from marking.py's own constants."""
    assert capture(laned(), WORDS, by=JUDGE).provenance == P_MEASURED
    assert capture(laned(), WORDS, by=JUDGE,
                   mode=Capture.POST_HOC).provenance == P_CITED
    assert Remark(laned(), WORDS, "", Capture.MACHINE).provenance == P_FITTED


def test_a_remark_cannot_outrank_the_tap_it_hangs_on():
    """`align()`'s refusal, applied to the other derived half."""
    weak = laned(prov=P_ASSUMED)
    try:
        capture(weak, WORDS, by=JUDGE)          # P1 words on a P5 observation
    except ValueError as exc:
        assert P_ASSUMED in str(exc)
        return
    raise AssertionError("a P1 remark hung on a P5 observation was accepted")


def test_an_unlaned_remark_addresses_the_work_and_names_nobody():
    """§8.1's `addresses`, with the roster removed. Not a refusal."""
    r = capture(tap(), "the ballad wanted more air", by=JUDGE)
    assert r.addresses is Addressed.WORK
    assert r.lane_id is None and r.subject_id is None


# ===========================================================================
# 2. W-1 / W-3 — the fan-out, and the roster column that cannot be written
# ===========================================================================


def test_a_shared_moment_is_two_lane_entries_with_one_referent():
    """Rule 8, W-3. The flagship shape, asserted as a count and as identity."""
    rs = fan_out((laned(BEN, LB), laned(ANA, LA)), WORDS, by=JUDGE)
    assert len(rs) == 2
    assert {r.lane_id for r in rs} == {LB, LA}
    assert {r.referent for r in rs} == {MOMENT}, "one referent, shared"


def test_no_type_in_this_module_can_hold_a_list_of_students():
    """W-1's roster column is unwritable, not refused.

    Asserted over the dataclass fields rather than by trying one call, because
    the claim is about the shape: a later field holding a sequence of subjects
    would pass any single-call test written today.
    """
    import dataclasses

    import records.commentary as mod

    for name in dir(mod):
        obj = getattr(mod, name)
        if not dataclasses.is_dataclass(obj):
            continue
        for f in dataclasses.fields(obj):
            assert f.name not in ("subjects", "students", "roster",
                                  "participants", "members", "addressees"), \
                f"{name}.{f.name} is a roster column (W-1)"


def test_a_fan_out_over_two_moments_is_refused():
    """Two moments are two remarks; one row covering both is the roster column."""
    try:
        fan_out((laned(BEN, LB), laned(ANA, LA, referent="show@other")),
                WORDS, by=JUDGE)
    except ValueError as exc:
        assert "referent" in str(exc)
        return
    raise AssertionError("a fan-out spanning two referents was accepted")


def test_a_fan_out_over_no_marks_is_refused():
    """And it says *that* is what is wrong, not that the referents disagree.

    The message is asserted because the referent check below would also refuse
    an empty fan-out, for a reason that is true of two moments and nonsense
    about none — a guard caught by the wrong guard is one nobody has tested.
    """
    try:
        fan_out((), WORDS, by=JUDGE)
    except ValueError as exc:
        assert "shared moment" in str(exc), str(exc)
        return
    raise AssertionError("a fan-out over nothing was accepted")


def test_a_fan_out_naming_one_lane_twice_is_refused():
    """One lane entry written twice is not a shared moment."""
    try:
        fan_out((laned(BEN, LB), laned(BEN, LB, ms=94600)), WORDS, by=JUDGE)
    except ValueError as exc:
        assert "same lane" in str(exc)
        return
    raise AssertionError("a fan-out naming one lane twice was accepted")


def test_a_mark_naming_a_student_with_no_lane_never_reaches_a_remark():
    """W-1 is marking.py's and stays enforced through this constructor."""
    try:
        capture(Mark(MOMENT, 1, SEAT, None, BEN), WORDS, by=JUDGE)
    except ValueError:
        return
    raise AssertionError("a subject with no lane reached a remark")


# ===========================================================================
# 3. Refusal 4 / SA-3 — the score that cannot exist
# ===========================================================================


def test_reaching_for_a_rating_raises_with_the_clause_attached():
    """Refusal 4. The `Escalation.recommendation` shape: a clause, not a None."""
    r = capture(laned(), WORDS, by=JUDGE)
    for attr in ("rating", "score", "calibration"):
        try:
            getattr(r, attr)
        except StandingScore as exc:
            assert exc.clause == SA3_CLAUSE
            assert "invalid even signed by root" in str(exc)
            continue
        raise AssertionError(f"Remark.{attr} returned instead of refusing")


def test_the_refusal_is_not_an_attribute_error_a_caller_can_paper_over():
    """`getattr(r, 'score', None)` must not quietly yield a default."""
    r = capture(laned(), WORDS, by=JUDGE)
    try:
        getattr(r, "score", None)
    except StandingScore:
        return
    raise AssertionError("getattr(..., None) swallowed the SA-3 refusal")


def test_no_field_anywhere_holds_a_score_that_travels():
    """`SA-3` is unrepresentable, not merely refused."""
    import dataclasses

    import records.commentary as mod

    banned = {"score", "rating", "ranking", "placement", "calibration",
              "reliability", "events", "season", "history", "average"}
    for name in dir(mod):
        obj = getattr(mod, name)
        if not dataclasses.is_dataclass(obj):
            continue
        for f in dataclasses.fields(obj):
            assert f.name not in banned, f"{name}.{f.name} is a standing score"


def test_a_remark_binds_to_exactly_one_event():
    """One anchor, one referent. There is nowhere for a second event to go."""
    import dataclasses

    r = capture(laned(), WORDS, by=JUDGE)
    names = {f.name for f in dataclasses.fields(Remark)}
    assert names == {"anchor", "body", "by", "capture"}, names
    assert isinstance(r.anchor, Mark)


def test_refuse_standing_score_always_raises():
    try:
        refuse_standing_score("a season reliability curve", JUDGE)
    except StandingScore as exc:
        assert exc.narration == NARRATION["standing_score"]
        return
    raise AssertionError("refuse_standing_score returned")


def test_comparing_two_remarks_raises_the_house_refusal():
    """Refusal 6, through `conflict.refuse_to_rank` rather than a second spelling."""
    a = capture(laned(BEN, LB), WORDS, by=JUDGE)
    b = capture(laned(ANA, LA), WORDS, by=JUDGE)
    try:
        compare(a, b)
    except NotComputable as exc:
        assert "human decides" in str(exc)
        return
    raise AssertionError("two remarks were ordered")


def test_the_sa3_clause_here_is_the_documents_clause():
    """Rule 12's middle for the clause pair: §13 and this module quote one thing."""
    doc = (ROOT / "docs" / "ARCHITECTURE.md").read_text()
    assert SA3_CLAUSE in doc, (
        "SA3_CLAUSE has drifted from docs/ARCHITECTURE.md §13; the module is "
        "the defect, and a refusal citing a clause the document does not say "
        "cannot be re-checked against it")


def test_the_narrations_name_no_fleet_noun_and_no_scope_code():
    """A student, guardian or judge never reads an internal identifier."""
    fleet = re.compile(
        r"\b(willow|grove|jeles|kart|soil|loam|frank|nest|safe|sap|nestor)\b",
        re.I)
    for key, text in NARRATION.items():
        assert not fleet.search(text), f"{key} names a fleet component"
        assert "SA-3" not in text, f"{key} shows a scope code to a person"
        assert "W-" not in text and "I-7" not in text, f"{key} shows a clause code"


# ===========================================================================
# 4. The seal cascade
# ===========================================================================


def test_a_judges_remark_enters_the_cascade_as_a_draft_authored_by_them():
    r = capture(laned(), WORDS, by=JUDGE)
    rec = to_draft(r)
    assert rec.state is State.DRAFT and rec.author_id == JUDGE
    assert rec.kind == KIND and not rec.servable


def test_a_machine_transcription_enters_authored_by_nobody():
    """Rule 10: attributed to the machine, never to the judge."""
    rec = to_draft(Remark(laned(), WORDS, "", Capture.MACHINE))
    assert rec.state is State.DRAFT
    assert rec.author_id is None, "a transcript acquired an author"


def test_a_sealed_remark_becomes_servable_and_a_rejected_one_does_not():
    """Rule 10: rejections are recorded as durably as approvals."""
    r, s = sealed_remark()
    assert s.servable and s.sealed_by == JUDGE
    rejected = reject(to_draft(r), by=JUDGE, at=T1, reason="wrong passage")
    assert rejected.state is State.REJECTED and not rejected.servable
    assert rejected.reason == "wrong passage"


def test_there_is_no_auto_seal_helper_in_this_module():
    """A convenience wrapper supplying a name would be the auto-seal path."""
    import records.commentary as mod

    for name in dir(mod):
        assert name not in ("seal", "autoseal", "seal_transcript", "confirm"), \
            f"records.commentary.{name} is a second door onto the seal"


# ===========================================================================
# 5. Release — the gate commentary leaves through
# ===========================================================================


def judge_edge(subject=BEN, at=T0):
    return Edge("judge_at", JUDGE_ID, subject, at - timedelta(hours=1),
                created_at=at - timedelta(hours=1))


def test_release_refuses_a_draft_and_names_the_state():
    """§8.2: only SEALED is servable."""
    r = capture(laned(), WORDS, by=JUDGE)
    try:
        release(r, to_draft(r), Principal(JUDGE_ID), [judge_edge()], T1,
                rung=Rung.L3)
    except Unsealed as exc:
        assert "draft" in str(exc)
        return
    raise AssertionError("an unsealed remark was released")


def test_release_refuses_a_rejected_record():
    r = capture(laned(), WORDS, by=JUDGE)
    rejected = reject(to_draft(r), by=JUDGE, at=T1, reason="wrong passage")
    try:
        release(r, rejected, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    except Unsealed:
        return
    raise AssertionError("a rejected remark was released")


def test_release_refuses_a_seal_over_different_words():
    """A seal names what was sealed; other text cannot ride under this anchor."""
    r = capture(laned(), WORDS, by=JUDGE)
    _, other = sealed_remark(capture(laned(), "a different sentence entirely",
                                     by=JUDGE))
    try:
        release(r, other, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    except Unsealed as exc:
        assert "not this remark" in str(exc)
        return
    raise AssertionError("a seal over other words was released under this anchor")


def test_release_has_no_default_rung():
    """Rule 13: which rung commentary lands at is undecided, and stays so."""
    r, s = sealed_remark()
    try:
        release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=None)
    except ValueError as exc:
        assert "not decided" in str(exc)
    else:
        raise AssertionError("release() picked a rung nobody decided")

    import inspect

    sig = inspect.signature(release)
    assert sig.parameters["rung"].default is inspect.Parameter.empty, \
        "rung acquired a default"


def test_release_refuses_a_remark_that_names_no_student():
    r = capture(tap(), "the ballad wanted more air", by=JUDGE)
    _, s = sealed_remark(r)
    try:
        release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    except Unlaned:
        return
    raise AssertionError("an unlaned remark was released down a lane path")


def test_release_routes_through_the_voice_gate():
    """Rule 18: enforcement, and the proof is that the gate can refuse here.

    A remark whose prose orders two students is refused *by the voice gate*,
    after the serving decision said it could leave — which is the only way to
    show the second half is wired rather than declared.
    """
    ordering = "Ben should get the chair and I'd give it to him over Ana"
    r = capture(laned(), ordering, by=JUDGE)
    _, s = sealed_remark(r)
    d = release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    assert not d.released, "an ordering of two students left the system"
    assert d.blocked_by_voice, "the serving decision refused it, not the gate"
    assert d.text is None
    assert any("ordering_two_students" in f for f in d.voice_findings), \
        d.voice_findings


def test_release_records_the_decision_when_a_log_is_supplied():
    """§7.2's narrate the read, through the existing chain."""
    from records.disclosure import Log

    r, s = sealed_remark()
    d = release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3,
                log=Log(), authority="judge_at :: event-42")
    assert d.log is not None and len(d.log.entries) == 1
    assert d.log.entries[0].field_name == KIND
    assert d.log.verify()[0]


def test_release_refuses_a_principal_with_no_edge():
    """The read predicate still governs; this adds to it and replaces nothing."""
    r, s = sealed_remark()
    d = release(r, s, Principal("stranger"), [], T1, rung=Rung.L3)
    assert not d.released


def test_the_module_is_not_broken_shut_a_plain_remark_can_be_released():
    """The control. A module that refused everything would pass every test above."""
    r, s = sealed_remark(capture(laned(), "the release at bar 40 was clean",
                                 by=JUDGE))
    d = release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    assert d.released, d.reason
    assert d.text


def test_a_remarks_provenance_travels_with_it_or_it_does_not_leave():
    """§15, found by routing this module through the gate.

    A judge's words cannot leave as bare prose: the gate refuses a served value
    carrying no `P`-rung, so a `P1` thing a person said and a `P3` machine guess
    cannot arrive looking alike.
    """
    r, s = sealed_remark(capture(laned(), "the release at bar 40 was clean",
                                 by=JUDGE))
    d = release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    assert d.released and P_MEASURED in d.text, d.text
    assert d.text.startswith("the release at bar 40 was clean")

    # And the qualifier is on the sentence, never on the sealed body.
    assert s.body == "the release at bar 40 was clean"
    assert s.servable, "the render edited the body and broke the seal"


def test_a_bare_render_would_be_refused_by_the_gate():
    """The guard behind the previous test, shown failing (rule 19).

    Ablating `_render` down to the body alone is the mutation; this asserts the
    gate is what catches it, rather than trusting that it would.
    """
    import voice

    refused, findings = voice.refuses(
        voice.guard(field="text", serves_value=True),
        {"text": "the release at bar 40 was clean"},
    )
    assert refused, "a value with no provenance passed the gate"
    assert any("no_provenance" in f for f in findings), findings


def test_the_judge_register_defect_is_now_reachable_through_a_call_site():
    """`docs/RECONCILE-JUDGE.md`'s demonstrated defect, pinned as behaviour.

    *"Today the gate would refuse a judge's legitimate sentence, and nobody has
    noticed because no surface routes one through it yet."* One now does. This
    test asserts the **current** behaviour so the open decision (*needs a
    human — 1*: give the ruleset a register axis, or route judge commentary
    outside the gate) is visible in the suite rather than only in a document.

    It is not an endorsement. Routing around the gate here would have built the
    hole rule 18 names — *"a gate with a hole shaped like a persona is a ledger
    for that persona"* — so the refusal stands until a human chooses.
    """
    craft = "The trumpets were ahead of the pulse in bar 40."
    r = capture(laned(), craft, by=JUDGE)
    _, s = sealed_remark(r)
    d = release(r, s, Principal(JUDGE_ID), [judge_edge()], T1, rung=Rung.L3)
    assert not d.released, (
        "the judge register defect has been fixed — good, and this test is now "
        "the stale one: update it and docs/RECONCILE-JUDGE.md's 'needs a "
        "human — 1' together")
    assert any("peer_comparison" in f for f in d.voice_findings), d.voice_findings


# ===========================================================================
# 6. The knock — §7.2's least-trusted session
# ===========================================================================


def a_knock(lanes=(LB,), at=T0):
    return knock(JUDGE_ID, purpose="score ensemble 7", event_id=EVENT,
                 lanes=lanes, at=at)


def test_a_session_with_no_declared_purpose_is_refused():
    try:
        knock(JUDGE_ID, purpose="  ", event_id=EVENT, lanes=(LB,), at=T0)
    except ValueError as exc:
        assert "purpose" in str(exc)
        return
    raise AssertionError("a session knocked with nothing declared")


def test_a_session_with_no_event_is_refused():
    """§4: the grant is to an event, not to a roster."""
    try:
        knock(JUDGE_ID, purpose="score ensemble 7", event_id="", lanes=(LB,), at=T0)
    except ValueError:
        return
    raise AssertionError("a guest session was opened against no event")


def test_a_wildcard_lane_in_a_declaration_is_refused():
    """Refusal 5 / W-2: a group is not a scope, and a name is."""
    for bad in ("*", "all", "any", "every", "", "   "):
        try:
            knock(JUDGE_ID, purpose="p", event_id=EVENT, lanes=(bad,), at=T0)
        except ValueError:
            continue
        raise AssertionError(f"a declaration over {bad!r} was accepted")


def test_a_lane_declared_twice_is_refused():
    """A declaration that double-counts a lane makes the exit diff unreadable."""
    try:
        knock(JUDGE_ID, purpose="p", event_id=EVENT, lanes=(LB, LB), at=T0)
    except ValueError as exc:
        assert "twice" in str(exc)
        return
    raise AssertionError("a declaration naming one lane twice was accepted")


def test_a_declaration_has_no_group_field_and_no_trust_level():
    """W-2, and §7.2's *'Elder' is not a text field anyone can type*."""
    import dataclasses

    names = {f.name for f in dataclasses.fields(Declaration)}
    for banned in ("section", "ensemble", "part", "group", "roster",
                   "trust_level", "trust", "rung_ceiling"):
        assert banned not in names, f"Declaration.{banned}"


def test_the_module_does_not_claim_to_be_the_thirteen_fields():
    """Rule 17: the field names are not in this tree, so nothing counts to 13."""
    assert KNOCK_FIELD_NAMES_KNOWN is False
    src = (ROOT / "records" / "commentary.py").read_text()
    assert "KNOCK_FIELDS = (" not in src
    import dataclasses

    assert len(dataclasses.fields(Declaration)) != 13 or True  # not asserted


def test_a_capture_outside_the_session_window_is_refused():
    """§4: the grant is time-boxed, and a capture outside it is the failure."""
    s = close(a_knock(), T2)
    r = capture(laned(), WORDS, by=JUDGE)
    try:
        log_capture(Ledger(), s, r, at=T2 + timedelta(hours=3))
    except ValueError as exc:
        assert "outside" in str(exc)
        return
    raise AssertionError("a capture after the session window was logged")


def test_every_capture_reaches_the_subjects_own_lane_chain():
    """§5: adjudication commentary inherits per-subject partitioning."""
    s = a_knock(lanes=(LB, LA))
    led = Ledger()
    for r in fan_out((laned(BEN, LB), laned(ANA, LA)), WORDS, by=JUDGE):
        led = log_capture(led, s, r, at=T1)
    assert {ln for ln, _ in led.lanes} == {LB, LA}
    assert all(len(log.entries) == 1 for _, log in led.lanes), \
        "one chain carried both students"
    assert led.verify()[0]


def test_an_unlaned_capture_writes_no_row_about_any_student():
    """A guest who only spoke about the ensemble touched no student's record."""
    s = a_knock()
    led = log_capture(Ledger(), s, capture(tap(), "more air in the ballad",
                                           by=JUDGE), at=T1)
    assert led.lanes == (), "an ensemble remark wrote into a student's chain"


def test_the_observed_half_is_a_filter_over_the_chain_not_a_second_record():
    """J6: a separate summary could show the guest a different history."""
    s = a_knock(lanes=(LB,))
    led = log_capture(Ledger(), s, capture(laned(), WORDS, by=JUDGE), at=T1)
    seen = observed(led, s)
    assert seen.lanes == (LB,) and seen.entries == 1

    import dataclasses

    names = {f.name for f in dataclasses.fields(GuestSession)}
    assert "observed" not in names and "diff" not in names, \
        "the observed half is stored, so it can disagree with the chain"


def test_another_principals_entries_are_not_this_guests_doing():
    s = a_knock(lanes=(LB,))
    other = knock("staff-nguyen", purpose="attendance", event_id=EVENT,
                  lanes=(LA,), at=T0)
    led = log_capture(Ledger(), other,
                      capture(laned(ANA, LA), WORDS, by="Nguyen Thi Mai"), at=T1)
    assert observed(led, s).touched_nothing


def test_an_open_session_reconciles_to_unknown_and_never_to_reconciled():
    """Rule 13: a session still in progress is not a pass."""
    s = a_knock()
    rec = reconcile_exit(s, Ledger())
    assert rec.state is ExitState.UNKNOWN
    assert not rec.reconciled
    assert "still open" in rec.narration


def test_touching_a_lane_that_was_never_declared_diverges():
    """§7.2's worked failure, and it stands whether or not the grant permitted it."""
    s = a_knock(lanes=(LB,))
    led = Ledger()
    for r in fan_out((laned(BEN, LB), laned(ANA, LA)), WORDS, by=JUDGE):
        led = log_capture(led, s, r, at=T1)
    rec = reconcile_exit(close(s, T2), led)
    assert rec.state is ExitState.DIVERGED and not rec.reconciled
    assert rec.undeclared == (LA,)


def test_a_declared_lane_never_touched_is_recorded_and_is_not_a_failure():
    s = close(a_knock(lanes=(LB, LA)), T2)
    led = log_capture(Ledger(), s, capture(laned(), WORDS, by=JUDGE), at=T1)
    rec = reconcile_exit(s, led)
    assert rec.reconciled and rec.unvisited == (LA,)


def test_the_guests_narration_names_no_lane_identifier():
    """J6: the guest reads their own trail; a lane id is another student's key."""
    s = a_knock(lanes=(LB,))
    led = Ledger()
    for r in fan_out((laned(BEN, LB), laned(ANA, LA)), WORDS, by=JUDGE):
        led = log_capture(led, s, r, at=T1)
    rec = reconcile_exit(close(s, T2), led)
    for lane in (LB, LA, BEN, ANA):
        assert lane not in rec.narration, rec.narration
    assert "not part of what you declared" in rec.narration


def test_a_session_cannot_close_before_it_opened():
    try:
        close(a_knock(), T0 - timedelta(hours=1))
    except ValueError:
        return
    raise AssertionError("a session closed before it opened")


def test_the_session_shape_is_the_ddls():
    """Rule 12's middle: this type and `reconciled_session` are one shape.

    The columns are read out of the migration rather than restated, so a change
    to either side fails here instead of drifting quietly.
    """
    ddl = (ROOT / "migrations" / "001_lanes.sql").read_text()
    block = ddl.split("CREATE TABLE reconciled_session (", 1)[1].split(");", 1)[0]
    cols = {ln.strip().split()[0] for ln in block.strip().splitlines()
            if ln.strip() and not ln.strip().startswith("--")}
    assert {"opened_at", "closed_at", "principal_id", "declared", "observed",
            "diff"} <= cols, cols

    import dataclasses

    d = {f.name for f in dataclasses.fields(Declaration)}
    g = {f.name for f in dataclasses.fields(GuestSession)}
    assert "opened_at" in d and "principal_id" in d
    assert "closed_at" in g and "declared" in g
    # observed and diff are computed, never stored — that is the J6 property.
    assert not ({"observed", "diff"} & (d | g))


# ===========================================================================
# 7. The transcription seam
# ===========================================================================


def returning(text, provider):
    return lambda: (text, provider)


def raising(exc):
    def _call():
        raise exc
    return _call


def test_a_transcript_lands_as_an_unsealed_draft_attributed_to_the_machine():
    t = transcribe(returning(WORDS, "ollama"), laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    assert t.state is TranscriptState.DRAFT
    assert t.record.state is State.DRAFT
    assert t.record.author_id is None, "attributed to a person"
    assert not t.servable
    assert t.by_machine == "asr-local-v3"


def test_asking_a_transcript_who_said_it_raises_rather_than_answering():
    """The judge is the speaker; the transcript is a model's answer about them."""
    t = transcribe(returning(WORDS, "ollama"), laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    try:
        t.said_by
    except NotImplementedError as exc:
        assert "draft until they seal it" in str(exc)
        return
    raise AssertionError("a transcript named the person who spoke")


def test_a_transcripts_remark_is_never_attributed_to_a_person():
    t = transcribe(returning(WORDS, "ollama"), laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    r = t.as_remark()
    assert r.capture is Capture.MACHINE and r.by == ""
    assert r.provenance == P_FITTED


def test_a_transcript_cannot_be_built_over_an_authored_record():
    """A person's own words are not a machine's guess at them."""
    from records.sealing import authored_by

    try:
        Transcript(authored_by(BEN, JUDGE, KIND, WORDS), laned(),
                   "asr-local-v3")
    except ValueError as exc:
        assert JUDGE in str(exc)
        return
    raise AssertionError("an authored record was wrapped as a transcript")


def test_a_transcript_cannot_be_built_over_a_sealed_record():
    _, s = sealed_remark()
    try:
        Transcript(s, laned(), "asr-local-v3")
    except ValueError as exc:
        assert "draft" in str(exc)
        return
    raise AssertionError("a sealed record was wrapped as an unsealed transcript")


def test_a_transcript_must_name_what_produced_it():
    from records.sealing import draft as make_draft

    for bad in ("", "  "):
        try:
            Transcript(make_draft(BEN, KIND, WORDS), laned(), bad)
        except ValueError:
            continue
        raise AssertionError("an unattributed machine answer was accepted")


def test_a_third_party_answer_is_refused_and_the_documented_chain_is_covered():
    """Refusal 1, through the guard rather than beside it."""
    for provider in ("gemini", "groq", "openrouter", "fleet", "hns",
                     "a-provider-nobody-has-heard-of"):
        try:
            transcribe(returning(WORDS, provider), laned(), endpoint=LOCAL,
                       by_machine="asr-local-v3")
        except NonLocalInference:
            continue
        raise AssertionError(f"{provider!r} transcribed a student's performance")


def test_the_local_label_at_another_machine_is_refused():
    """`OLLAMA_URL` can address another box; a familiar label is not evidence."""
    try:
        transcribe(returning(WORDS, "ollama"), laned(),
                   endpoint="http://hub-2.school.internal:11434",
                   by_machine="asr-local-v3")
    except OffBoxLocalModel:
        return
    raise AssertionError("an off-box model transcribed a performance")


def test_a_stopped_local_model_fails_loudly_and_never_degrades():
    try:
        transcribe(raising(RuntimeError("connection refused")), laned(),
                   endpoint=LOCAL, by_machine="asr-local-v3")
    except LocalModelUnavailable:
        return
    raise AssertionError("a stopped local model produced a transcript")


def test_an_empty_answer_is_absence_and_not_an_empty_remark():
    """Rule 13: an empty transcript would render as a remark nobody made."""
    try:
        transcribe(returning("   ", "ollama"), laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    except LocalModelUnavailable:
        return
    raise AssertionError("an empty answer became a transcript")


def test_a_bare_string_return_is_refused_rather_than_assumed_local():
    """`llm_edge.respond()` drops the provider label; here that is a refusal."""
    try:
        transcribe(lambda: WORDS, laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    except UnknownProvider:
        return
    raise AssertionError("a bare string was accepted as a local answer")


def test_the_seam_declares_the_classes_and_the_caller_cannot_override_them():
    """A caller tagging a judge's dictation PUBLIC would pass the guard."""
    import inspect

    assert set(TRANSCRIPT_CLASSES) == {"MEDIA_MINOR", "PII_MINOR"}
    assert TRANSCRIPT_RUNG is Rung.L4
    params = inspect.signature(transcribe).parameters
    for banned in ("classes", "rung", "provider", "fallback", "allow", "kwargs"):
        assert banned not in params, f"transcribe() accepts {banned}"
    assert not any(p.kind is inspect.Parameter.VAR_KEYWORD
                   for p in params.values()), "transcribe() takes **kwargs"


def test_the_classes_this_seam_declares_are_ones_the_guard_recognises():
    """An unknown class is `Unclassified`, so a typo here would refuse at runtime."""
    from records.inference import CLASSES

    assert set(TRANSCRIPT_CLASSES) <= CLASSES


def test_an_unclassified_tagging_would_be_refused_by_the_guard():
    """The guard behind this seam, exercised directly so the seam's reliance is shown."""
    from records.inference import through as raw_through

    try:
        raw_through(returning(WORDS, "ollama"), classes=(), endpoint=LOCAL)
    except Unclassified:
        return
    raise AssertionError("an untagged inference call was accepted")


def test_a_refusal_becomes_pending_only_when_a_caller_asks_for_it():
    """§8.2's third state, and it never happens behind the caller's back."""
    try:
        transcribe(raising(RuntimeError("down")), laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    except LocalModelUnavailable as exc:
        p = pending_from(exc, laned())
        assert p.state is TranscriptState.PENDING and not p.servable
        assert "LocalModelUnavailable" in p.reason
        assert "did not respond" in p.narration
        try:
            p.body
        except NotImplementedError:
            return
        raise AssertionError("a pending transcript rendered a body")
    raise AssertionError("the refusal did not arrive")


def test_a_transcript_cannot_outrank_the_tap_it_was_anchored_to():
    from records.sealing import draft as make_draft

    try:
        Transcript(make_draft(BEN, KIND, WORDS), laned(prov=P_ASSUMED),
                   "asr-local-v3", P_FITTED)
    except ValueError:
        return
    raise AssertionError("a P3 transcript outranked a P5 observation")


def test_a_sealed_transcript_is_the_judges_and_a_role_cannot_seal_it():
    """§8.2: a role is not a signature, and sealing.py refuses it, not this module."""
    t = transcribe(returning(WORDS, "ollama"), laned(), endpoint=LOCAL,
                   by_machine="asr-local-v3")
    for role in ("the director", "system", "staff", "", "   "):
        try:
            seal(t.record, by=role, at=T1)
        except ValueError:
            continue
        raise AssertionError(f"{role!r} sealed a transcript")
    done = seal(t.record, by=JUDGE, at=T1)
    assert done.servable and done.sealed_by == JUDGE


def test_the_seam_reaches_no_model_of_its_own():
    """`tools/providers.py`'s rule, asserted here too: the call is the caller's."""
    src = (ROOT / "records" / "commentary.py").read_text()
    for router in ("inference_router", "llm_edge", "model_adapter", "requests",
                   "httpx", "urllib", "socket"):
        assert f"import {router}" not in src, f"commentary.py imports {router}"


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
