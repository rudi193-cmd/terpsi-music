"""Acceptance for the voice gate, by mutation.

Rule 19: a guard that cannot be shown to fail has not been shown to work.
Acceptance is mutation, not a green suite. So every invariant here has a test
that attempts the forbidden act and asserts refusal, and the `mutation_*`
tests break each mechanism deliberately and assert the checks notice.

Rule 17: no count in this file is quoted from prose. Every number is derived
from the module under test.

Stdlib only. No network. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_voice.py
"""

from __future__ import annotations

import contextlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import personas  # noqa: E402
import voice  # noqa: E402


@contextlib.contextmanager
def swapped(obj, name, value):
    """Break something on purpose, then put it back."""
    original = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, original)


def _caught(line, rule):
    return any(f.startswith(rule) for f in voice.check(line))


# --- the ledger half -------------------------------------------------------

def test_every_violation_is_caught_by_the_rule_that_names_it():
    missed = [(line, rule) for line, rule in voice.VIOLATIONS if not _caught(line, rule)]
    assert not missed, f"uncaught: {missed}"


def test_there_is_a_violation_fixture_for_every_rule():
    """A rule with no fixture is a rule nobody has ever seen fire."""
    ruled = {name for name, _a, _p, _w in voice.RULES}
    fixtured = {rule for _line, rule in voice.VIOLATIONS}
    assert ruled == fixtured, f"rules without fixtures: {sorted(ruled - fixtured)}"


def test_everything_it_should_say_passes_its_own_lint():
    flagged = [(line, voice.check(line)) for line in voice.SOUNDS_LIKE if voice.check(line)]
    assert not flagged, flagged


def test_every_rule_declares_an_action_and_the_refusal_it_protects():
    for name, action, _pattern, why in voice.RULES:
        assert action in (voice.REFUSE, voice.FLAG), f"{name} has no action"
        assert len(why) > 40, f"{name} names no refusal behind it"


def test_a_statistic_without_its_aggregation_is_caught():
    assert _caught("Your average is 76.", "naked_statistic")
    assert voice.ok("Your average is 76, across four sheets this season.")


def test_a_served_value_without_its_rung_is_caught():
    assert any(f.startswith("no_rung")
               for f in voice.check("Saturday is clear.", serves_value=True))
    assert voice.ok("Saturday is clear. P5, assumed — nobody checked the venue "
                    "calendar.", serves_value=True)


def test_the_rung_is_prefixed_never_a_bare_integer():
    """Rule 14: no scale compares as a bare integer."""
    assert not voice.ok("Provenance 5.", serves_value=True)
    assert voice.ok("Provenance P5.", serves_value=True)


# --- the gate half ---------------------------------------------------------

def test_the_gate_blocks_what_the_ledger_flags():
    g = voice.guard()
    assert g({"text": "Call time is 5:15."}) == []
    assert g({"text": "You're having a great season!"})


def test_the_gate_fails_closed_on_a_payload_it_cannot_read():
    """Rule 13: absence surfaces as unknown, and unknown is not a pass."""
    g = voice.guard(field="text")
    for payload in ({"other": "hello"}, "not a dict", None, {}):
        refused, findings = voice.refuses(g, payload)
        assert refused, f"{payload!r} was waved through"
        assert "unknown" in findings[0]


def test_a_guard_that_raises_is_a_refusal():
    """A check that could not run is not a check that passed."""
    def broken(_payload):
        raise RuntimeError("regex engine on fire")

    refused, findings = voice.refuses(broken, {"text": "anything"})
    assert refused
    assert "unknown" in findings[0] and "RuntimeError" in findings[0]


def test_every_refusal_carries_the_policy_version():
    _refused, findings = voice.refuses(voice.guard(), {"text": "You'll score 78."})
    assert findings and all(voice.POLICY_VERSION in f for f in findings)


def test_a_flag_tier_finding_is_recorded_and_does_not_block():
    findings = voice.check("You're absolutely right, that judge was unfair.")
    assert findings, "mirroring was not recorded at all"
    assert voice.blocking(findings) == [], "a FLAG rule blocked a dispatch"


def test_a_refuse_tier_finding_does_block():
    assert len(voice.blocking(voice.check("You're having a great season!"))) == 1


# --- honesty about the gap -------------------------------------------------

def test_the_known_misses_are_still_genuinely_missed():
    """A stale honesty list is worse than none.

    If a rule grows to cover one of these, this fails until the entry is
    removed — which is how the list stays a claim rather than a decoration.
    """
    now_caught = [(line, why) for line, why in voice.KNOWN_MISSES if voice.check(line)]
    assert not now_caught, f"now caught, remove from KNOWN_MISSES: {now_caught}"


def test_the_near_boundary_set_is_hard_rather_than_easy():
    """An easy benign set makes a damaging filter measure as excellent."""
    assert len(voice.NEAR_BOUNDARY) >= 10


def test_exactly_one_documented_false_positive():
    """Quoting a judge who wrote 'better than last week'. Exempting quoted
    spans would fix it and open a laundering path, so the conservative choice
    is taken: a false positive costs one edit before a seal, a false negative
    reaches a student."""
    flagged = [line for line in voice.NEAR_BOUNDARY if voice.check(line)]
    assert len(flagged) == 1, flagged
    assert "better than last week" in flagged[0]


def test_coverage_reports_every_figure_with_its_denominator():
    report = voice.coverage()
    for key in ("violations_caught", "violations_missed",
                "near_boundary_false_positives"):
        assert "/" in report[key], f"{key} has no denominator"
    assert report["aggregation"]
    assert "unknown" in report["honest_summary"]


def test_coverage_counts_match_the_module_rather_than_prose():
    """Rule 17: do not quote a count you did not derive from the tree."""
    report = voice.coverage()
    assert report["violations_caught"].endswith(f"/{len(voice.VIOLATIONS)}")
    assert report["violations_missed"].endswith(f"/{len(voice.KNOWN_MISSES)}")


# --- the card --------------------------------------------------------------

def test_every_canon_lock_is_on_the_card():
    """Whitespace-normalised, because a lock must not depend on where a line
    wraps. The first version of this check compared raw text and failed on
    "never the one / who sends" -- a fragile test reporting a defect that was
    not there, which is its own kind of wrong answer."""
    card = " ".join(personas.get_persona("Terpsi").split())
    missing = [lock for lock in personas.CANON_LOCKS
               if " ".join(lock.split()) not in card]
    assert not missing, f"canon locks not on the card: {missing}"


def test_the_card_carries_no_fleet_nouns():
    """Modules take plain domain nouns; a card is a string that can leak."""
    card = personas.get_persona("Terpsi").lower()
    for noun in ("willow", "grove", "jeles", "kart", "soil", "loam", "frank",
                 "nest", "safe", "sap", "nestor", "binder", "gerald"):
        assert not re.search(rf"\b{noun}\b", card), f"card names {noun!r}"


def test_the_card_states_the_aggregation_beside_the_figure():
    """The figure it quotes is the one this project watched travel without it."""
    card = personas.get_persona("Terpsi")
    assert "0.988" in card and "within-sheet Spearman across" in card
    assert "0.986" in card


def test_the_refusal_line_names_a_person_and_records_nothing():
    card = personas.get_persona("Terpsi")
    assert "Karen Alvarez" in card
    assert "not writing any of this down" in card


def test_an_unknown_persona_falls_back_rather_than_returning_none():
    assert personas.get_persona("nobody") == personas.get_persona("Terpsi")


def test_the_pair_declares_its_middle():
    """Rule 12: a vendored pair without a named reconciler is the defect."""
    p = personas.PROVENANCE
    assert p["authoritative"].startswith("terpsi-music:")
    assert p["non_authoritative"].startswith("quick-stupids")
    assert p["relationship"] == "rebuilt, not copied"


def test_the_far_side_of_the_pair_carries_a_dated_check():
    """The half the assertion above could not reach, and did not know it could not.

    Until 2026-07-30 this file asserted only that the two strings had the right
    prefixes. `quick-stupids:band/persona.py` satisfied that and does not exist
    — the repository holds no Python at all — so the pair's middle was checking
    its own shape and calling it verified. That is the defect
    `tests/test_claimed_artifacts.py` exists to catch, one repository over,
    where that test cannot see.

    A cross-repo claim genuinely cannot be verified from this repository's CI.
    So the guard is not "the far side exists" — it is **"somebody looked, and
    said when."** An undated or stateless declaration fails; a declaration
    recording `absent` passes, because recording absence is the correct outcome
    of having looked (rule 13).
    """
    far = personas.PROVENANCE.get("far_side")
    assert far, "the pair names a far side with no record of anyone checking it"
    assert far.get("state") in {"present", "absent", "unknown"}, (
        f"far_side.state must be present/absent/unknown, got {far.get('state')!r}"
    )
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", far.get("checked", "")), (
        "far_side.checked must be an ISO date — an undated check decays silently (§15)"
    )
    assert "@" in far.get("at", ""), (
        "far_side.at must pin repo@commit; 'I looked once' is not a citation"
    )


def test_the_far_side_check_can_fail():
    """Rule 19. A declaration that forgot its check must be seen to fail."""
    import copy

    for broken in ({}, {"state": "present"}, {"state": "nope", "checked": "2026-07-30", "at": "x@y"}):
        p = copy.deepcopy(personas.PROVENANCE)
        p["far_side"] = broken
        failed = False
        try:
            far = p["far_side"]
            assert far
            assert far.get("state") in {"present", "absent", "unknown"}
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", far.get("checked", ""))
            assert "@" in far.get("at", "")
        except AssertionError:
            failed = True
        assert failed, f"a far_side of {broken!r} passed the check"


def test_there_is_a_register_for_every_audience_the_card_serves():
    assert set(personas.REGISTER) == {personas.STUDENT, personas.STAFF,
                                      personas.GUARDIAN, personas.DIRECTOR}


# --- mutation acceptance ---------------------------------------------------

def test_mutation_a_blinded_ruleset_is_noticed():
    """Empty the compiled rules: every violation should sail through."""
    with swapped(voice, "_COMPILED", []):
        still_caught = [line for line, rule in voice.VIOLATIONS if _caught(line, rule)]
    assert not still_caught, "rules fired with the table emptied — wrong object patched"
    assert all(_caught(line, rule) for line, rule in voice.VIOLATIONS), "not restored"


def test_mutation_dropping_one_rule_is_noticed_by_that_rules_fixture():
    """Each rule is load-bearing for at least its own fixture."""
    for name, action, pattern, why in voice.RULES:
        line = next(l for l, r in voice.VIOLATIONS if r == name)
        without = [r for r in voice._COMPILED if r[0] != name]
        with swapped(voice, "_COMPILED", without):
            assert not _caught(line, name), f"{name} still fired with {name} removed"


def test_mutation_dropping_the_aggregation_check_is_noticed():
    with swapped(voice, "_STATISTIC", re.compile(r"(?!x)x")):
        assert not _caught("Your average is 76.", "naked_statistic")


def test_mutation_a_gate_that_fails_open_on_unknown_is_noticed():
    def lenient(payload):
        if not isinstance(payload, dict) or "text" not in payload:
            return []          # the defect: unreadable reads as clear
        return voice.blocking(voice.check(str(payload["text"])))

    refused, _ = voice.refuses(lenient, {"other": "hello"})
    assert not refused, "the mutation did not take"
    refused, _ = voice.refuses(voice.guard(), {"other": "hello"})
    assert refused, "the real gate does not fail closed"


def test_mutation_promoting_the_flag_rule_to_refuse_is_visible():
    """The FLAG/REFUSE split is a decision, so it must be observable."""
    promoted = [(n, voice.REFUSE, p, w) for n, _a, p, w in voice._COMPILED]
    with swapped(voice, "_COMPILED", promoted):
        findings = voice.check("You're absolutely right, that judge was unfair.")
        assert voice.blocking(findings), "promotion had no effect"


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
