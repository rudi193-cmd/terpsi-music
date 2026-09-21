"""§9 item 11 — the gated assistance seam, attacked from every direction.

Rule 19: a guard that cannot be shown to fail has not been shown to work. Every
test here attempts the forbidden act — a cloud provider, a stopped local model, a
machine draft fed back to seal itself, a student's own draft iterated on, a read
that was never entitled, a rating of a student, a ranking of two — and asserts
the refusal.

The four acceptance tests `docs/PLAN-ASSIST.md` names are the four
`test_acceptance_*` below; the rest are the guard-by-guard forbidden acts each
ablation row in `tests/ablate.py` points at.

One test is a **middle** rather than a check (rule 12):

    test_the_growth_narrative_rung_is_the_ladders_rung_for_its_classes
        pair: docs/SENSITIVITY.md's class-to-L table <-> GROWTH_NARRATIVE. The
        capability declares PII_MINOR/L3; this parses the table.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_assistance.py
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.assistance import (  # noqa: E402
    GROWTH_NARRATIVE, AssistanceDraft, Capability, Grounding, NARRATION,
    NotComputable, StandingScore, Ungrounded, UnattendedLoop, assist, compare,
    from_entitlement, from_sealed, growth_narrative,
)
from records.inference import (  # noqa: E402
    LOCAL, InferenceRefused, LocalModelUnavailable, NonLocalInference,
    OffBoxLocalModel, accept,
)
from records.rungs import Rung, compose  # noqa: E402
from records.sealing import State, authored_by, draft, reject, seal  # noqa: E402
from records.serving import Field, Outcome, Serving  # noqa: E402

HERE = "http://localhost:11434"
T0 = datetime(2026, 7, 31)
ANA, ANA_LANE = "student-ana", "lane-ana"
BEN, BEN_LANE = "student-ben", "lane-ben"
BODY = "Ana's phrasing steadied across the season; her sight-reading is next."
HUMAN = "Alex Okonkwo"


def _raises(exc_type, fn, *a, **kw):
    """Run something that must raise `exc_type` and return it. A different
    exception propagates to the runner, which is the failure we want."""
    try:
        fn(*a, **kw)
    except exc_type as exc:
        return exc
    raise AssertionError(f"{getattr(fn, '__name__', fn)} did not raise {exc_type.__name__}")


def a_grounding(lane=ANA_LANE, subject=ANA) -> Grounding:
    """An entitled one-lane read, grounded the way A-4 requires."""
    fld = Field(lane_id=lane, subject_id=subject, name="attendance",
                rung=Rung.L3, payload="present 40/42")
    return from_entitlement(fld, Serving(Outcome.PAYLOAD, "present 40/42",
                                         Rung.L3, "served"))


def a_local_call(text=BODY):
    return lambda: (text, LOCAL)


def a_draft(text=BODY, subject=ANA) -> AssistanceDraft:
    return growth_narrative(a_local_call(text), groundings=[a_grounding(subject=subject)],
                            endpoint=HERE)


# --- the four acceptance tests (docs/PLAN-ASSIST.md) -----------------------


def test_acceptance_1_local_or_loud():
    """A non-local provider and a stopped local model both refuse; neither
    returns a usable string. Refusal 1 / §6, routed through the gate."""
    # A cloud provider answered — refused, whatever the capability says.
    cloud = _raises(NonLocalInference, growth_narrative, lambda: ("a", "groq"),
                    groundings=[a_grounding()], endpoint=HERE)
    assert cloud.state.value == "non_local_provider"

    # The local model was down — its own state, and never an empty answer a
    # surface could render as "no findings".
    def stopped():
        raise ConnectionRefusedError("[Errno 111] Connection refused")

    down = _raises(LocalModelUnavailable, growth_narrative, stopped,
                   groundings=[a_grounding()], endpoint=HERE)
    assert down.state.value == "local_unavailable"

    # The two are different events, never the same surface (refusal 1's last
    # sentence), and neither hands back an object a caller reads text off.
    assert cloud.state is not down.state
    for exc in (cloud, down):
        assert not hasattr(exc, "text")

    # The local label at another machine is refused too — the label is necessary
    # and not sufficient.
    off = _raises(OffBoxLocalModel, growth_narrative, a_local_call(),
                  groundings=[a_grounding()], endpoint="http://10.0.0.5:11434")
    assert off.state.value == "off_box_local"


def test_acceptance_2_draft_not_answer():
    """Assistance output is a PENDING/DRAFT draft; a seal requires a named human;
    a rejection lands as durably as a seal. Rule 10 / §8.2."""
    d = a_draft()
    assert d.state is State.DRAFT
    assert not d.servable, "a machine answer was servable without a human"
    assert d.record.author_id is None, "a machine draft was attributed to somebody"

    # There is no accessor that returns it as a human's sealed judgment.
    _raises(NotImplementedError, lambda: d.sealed)

    # A seal needs a name; a role and a machine are refused (records.sealing).
    for who in ("", "system", "the director", "bot"):
        _raises(ValueError, seal, d.record, by=who, at=T0)
    sealed = seal(d.record, by=HUMAN, at=T0)
    assert sealed.servable and sealed.sealed_by == HUMAN

    # A rejection is as durable as an approval — reason and dated signer kept.
    r = reject(a_draft().record, by=HUMAN, at=T0, reason="not what the data shows")
    assert r.state is State.REJECTED and r.sealed_by == HUMAN and r.reason
    assert not r.servable


def test_acceptance_3_no_unattended_loop():
    """A chain with no human signature cannot produce a sealed record, and a
    student's own draft is never an unattended-loop input. §8.2 / A-3."""
    d = a_draft()

    # Feeding a machine draft back into assistance to seal itself: refused,
    # because an AssistanceDraft is not a Grounding — the loop is unrepresentable
    # rather than merely checked.
    loop = _raises(UnattendedLoop, assist, a_local_call(), groundings=[d],
                   subject_id=ANA, capability=GROWTH_NARRATIVE, endpoint=HERE)
    assert loop.narration == NARRATION["unattended_loop"]

    # And a machine draft's own record cannot be grounded either, until a named
    # human seals it — at which point the human signature is in the chain.
    _raises(UnattendedLoop, from_sealed, d.record, lane_id=ANA_LANE)
    sealed = seal(d.record, by=HUMAN, at=T0)
    g = from_sealed(sealed, lane_id=ANA_LANE)  # sealed → grounds, human in chain
    assert g.subject_id == ANA

    # A student's own unsealed draft is its own refusal (the second half of A-3).
    own = authored_by(ANA, ANA, "student.account", "my season in my words")
    exc = _raises(UnattendedLoop, from_sealed, own, lane_id=ANA_LANE)
    assert exc.narration == NARRATION["own_draft"]
    # But a student's own *sealed* account carries their signature and grounds.
    own_sealed = seal(own, by=ANA, at=T0)
    assert from_sealed(own_sealed, lane_id=ANA_LANE).subject_id == ANA


def test_acceptance_4_no_score_no_priority():
    """Ranking two students or carrying a standing score is refused. Refusal 4
    (SA-3) and refusal 6 (W-7)."""
    a, b = a_draft(subject=ANA), a_draft(text="Ben's tone improved.", subject=BEN)

    # No standing cross-context score of a student.
    for reach in (lambda: a.score, lambda: a.rating, lambda: a.trajectory):
        _raises(StandingScore, reach)

    # No priority computed between two students.
    _raises(NotComputable, compare, a, b)

    # And a narrative over two students' lanes is the same refusal at the door.
    two = [a_grounding(lane=ANA_LANE, subject=ANA),
           a_grounding(lane=BEN_LANE, subject=BEN)]
    _raises(NotComputable, growth_narrative, a_local_call(), groundings=two,
            endpoint=HERE)


# --- the guard-by-guard forbidden acts (each ablation points here) ---------


def test_a_cloud_provider_is_refused_through_the_capability():
    """Ablation: records/inference.py `if provider != LOCAL:`. If the capability
    did not route through the gate, mutating that guard could not turn this red —
    which is what this proves."""
    for provider in ("groq", "gemini", "openrouter", "some-new-thing"):
        assert isinstance(
            _raises(InferenceRefused, growth_narrative, lambda p=provider: ("a", p),
                    groundings=[a_grounding()], endpoint=HERE),
            NonLocalInference), provider


def test_a_draft_is_the_only_state_assistance_lands_in():
    """Ablation: AssistanceDraft's DRAFT-state guard. A sealed record wrapped as
    a fresh draft would look reviewed when nobody reviewed it."""
    ans = accept((BODY, LOCAL), classes=["PII_MINOR"], endpoint=HERE, rung=Rung.L3)
    sealed = seal(draft(ANA, GROWTH_NARRATIVE.kind, BODY), by=HUMAN, at=T0)
    _raises(ValueError, AssistanceDraft, ans, sealed, GROWTH_NARRATIVE, ())
    # A record authored by a person is not a machine draft either.
    authored = authored_by(ANA, ANA, GROWTH_NARRATIVE.kind, BODY)
    _raises(ValueError, AssistanceDraft, ans, authored, GROWTH_NARRATIVE, ())


def test_a_draft_is_not_servable():
    """Ablation: AssistanceDraft.servable. A draft that reads servable is a
    machine answer shown as a sealed record."""
    assert a_draft().servable is False


def test_a_machine_draft_cannot_be_grounded_until_sealed():
    """Ablation: from_sealed's servable guard. An unsealed record grounding
    assistance is the unattended loop."""
    d = draft(ANA, GROWTH_NARRATIVE.kind, BODY)
    exc = _raises(UnattendedLoop, from_sealed, d, lane_id=ANA_LANE)
    assert exc.narration == NARRATION["unattended_loop"]


def test_a_students_own_draft_is_its_own_refusal():
    """Ablation: from_sealed's student-draft branch. Its narration is distinct,
    so neutering the branch (which would fall through to the generic loop
    refusal) is caught by the narration and not only by the type."""
    own = authored_by(BEN, BEN, "student.account", "my words")
    exc = _raises(UnattendedLoop, from_sealed, own, lane_id=BEN_LANE)
    assert exc.narration == NARRATION["own_draft"]
    assert "own" in exc.detail.lower() or "student" in exc.detail.lower()


def test_a_non_grounding_is_refused_as_a_loop():
    """Ablation: assist's isinstance(Grounding) guard. A raw draft or an
    AssistanceDraft passed as material is the loop, refused before a model."""
    d = a_draft()
    _raises(UnattendedLoop, assist, a_local_call(), groundings=[d],
            subject_id=ANA, capability=GROWTH_NARRATIVE, endpoint=HERE)
    raw = draft(ANA, GROWTH_NARRATIVE.kind, BODY)
    _raises(UnattendedLoop, assist, a_local_call(), groundings=[raw],
            subject_id=ANA, capability=GROWTH_NARRATIVE, endpoint=HERE)


def test_assistance_grounds_only_in_entitled_reads():
    """Ablation: from_entitlement's outcome guard. A REFUSED or UNKNOWN read is
    not material a draft may be built over."""
    fld = Field(lane_id=ANA_LANE, subject_id=ANA, name="health", rung=Rung.L4)
    for outcome in (Outcome.REFUSED, Outcome.UNKNOWN):
        _raises(Ungrounded, from_entitlement, fld,
                Serving(outcome, None, Rung.L4, "not served"))
    # An entitled read grounds; the module is not broken shut.
    assert from_entitlement(fld, Serving(Outcome.INSTRUCTION, "see clinician",
                                         Rung.L4, "derived")).subject_id == ANA


def test_no_standing_score_travels_from_a_narrative():
    """Ablation: AssistanceDraft.score. A longitudinal narrative reduced to a
    number is the rating SA-3 forbids."""
    exc = _raises(StandingScore, lambda: a_draft().score)
    assert "SA-3" in str(exc)


def test_two_narratives_cannot_be_ordered():
    """Ablation: compare's refuse_to_rank. The system presents; a human decides
    (W-7)."""
    a, b = a_draft(subject=ANA), a_draft(subject=BEN)
    _raises(NotComputable, compare, a, b)


def test_a_growth_narrative_reads_one_lane():
    """Ablation: records/conflict.py `if len(lanes) > 1:`. A narrative spanning
    two lanes is a cross-lane read W-3 seals; it refuses through the same middle
    a balance and a practice statistic refuse through (rule 12)."""
    two = [a_grounding(lane=ANA_LANE, subject=ANA),
           a_grounding(lane=BEN_LANE, subject=BEN)]
    _raises(NotComputable, growth_narrative, a_local_call(), groundings=two,
            endpoint=HERE)


# --- rule 13, and the module is not broken shut ----------------------------


def test_assistance_grounded_in_nothing_is_refused():
    """No material is unknown, not an empty draft a surface renders (rule 13)."""
    _raises(Ungrounded, assist, a_local_call(), groundings=[], subject_id=ANA,
            capability=GROWTH_NARRATIVE, endpoint=HERE)


def test_a_draft_with_no_subject_is_refused():
    _raises(Ungrounded, assist, a_local_call(), groundings=[a_grounding()],
            subject_id="  ", capability=GROWTH_NARRATIVE, endpoint=HERE)


def test_the_happy_path_produces_a_draft_from_the_local_model():
    """A refusal that also refuses the legitimate case gets routed around."""
    d = a_draft()
    assert d.state is State.DRAFT
    assert d.answer.provider == LOCAL and d.answer.covered_by_refusal_1
    assert d.draft_body == BODY
    assert d.not_a_judgment == NARRATION["not_a_judgment"]
    # The whole loop closes only with a human seal between iterations.
    sealed = seal(d.record, by=HUMAN, at=T0)
    g = from_sealed(sealed, lane_id=ANA_LANE)
    d2 = growth_narrative(a_local_call("A second draft, grounded in the first, sealed."),
                          groundings=[g], endpoint=HERE)
    assert d2.state is State.DRAFT


def test_a_capability_cannot_mistag_its_classes():
    """The classes are declared, not tagged per call, and validated against §6."""
    _raises(ValueError, Capability, "bad", ("ROSTER_NOTES",), Rung.L3, "k")
    _raises(ValueError, Capability, "bad", (), Rung.L3, "k")
    _raises(ValueError, Capability, "bad", ("PII_MINOR",), 3, "k")


# --- what a person is allowed to read --------------------------------------


def test_no_narration_a_person_reads_names_a_provider_or_a_fleet_noun():
    """CLAUDE.md, *Working here*: fleet nouns and provider identifiers are
    operator facts and never reach a student, guardian or teacher."""
    nouns = ("ollama", "groq", "gemini", "openrouter", "hns", "willow", "grove",
             "jeles", "kart", "soil", "loam", "frank", "nest", "safe", "sap",
             "nestor", "11434", "http", "localhost")
    for key, line in NARRATION.items():
        low = line.lower()
        for noun in nouns:
            assert noun not in low, f"{key} narration says {noun!r}"


def test_the_narrations_pass_the_voice_gate():
    """Pair: this module's person-facing text and voice.py's ruleset. A refusal
    is a sentence a person reads, subject to the same lint as any other."""
    import voice

    for key, line in NARRATION.items():
        assert not voice.blocking(voice.check(line)), (key, voice.check(line))


# --- the middle (rule 12) ---------------------------------------------------


def test_the_growth_narrative_rung_is_the_ladders_rung_for_its_classes():
    """Pair: docs/SENSITIVITY.md's class-to-L table and GROWTH_NARRATIVE. The
    capability declares PII_MINOR/L3 by composing the ladder's rung for its
    classes; this parses the table and fails when the two drift."""
    text = (ROOT / "docs" / "SENSITIVITY.md").read_text(encoding="utf-8")
    table = dict(re.findall(r"^\|\s*`([A-Z][A-Z_]+)`\s*\|\s*`(L[1-5])`\s*\|", text, re.M))
    from records.rungs import parse
    expected = compose(*[parse(table[c]) for c in GROWTH_NARRATIVE.classes])
    assert GROWTH_NARRATIVE.rung is expected, (
        f"declared {GROWTH_NARRATIVE.rung}, ladder says {expected}")
    assert GROWTH_NARRATIVE.classes == ("PII_MINOR",) and table["PII_MINOR"] == "L3"


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
