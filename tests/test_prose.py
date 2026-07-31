"""Acceptance for the document skin of `craft/`.

Rule 19: a guard that cannot be shown to fail has not been shown to work. So
every rule in `craft/prose.py` gets a fixture that violates it, a fixture that
does not, and a mutation that neutralises the rule and asserts the violation
fixture stops being caught — which is what proves the fixture depends on the
rule rather than on something incidental.

Two things here are middles rather than checks (§16 rule 1, name the pair and
its middle in the same commit):

    test_the_existing_sweeps_cover_this_module
        pair: craft/checks.py <-> craft/prose.py. Both are swept by
        test_craft.py's purity and no-scoring checks *because those glob
        craft/*.py*. A glob is a middle that rots silently if the second file
        ever moves, so this asserts the coverage rather than assuming it.

    test_the_two_absence_rules_do_not_disagree
        pair: voice.false_all_clear <-> prose ABSENCE. Same rule 13, two
        corpora, two implementations. This pins where they agree and where
        they deliberately differ, so widening one without the other fails.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_prose.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import voice                                    # noqa: E402
from craft import prose                         # noqa: E402
from craft.checks import Report                 # noqa: E402
from craft.prose import RULES, run_all, run_diff  # noqa: E402

DOCS = ROOT / "docs"


def _fires(text: str, check: str) -> bool:
    return any(f.check == check for f in run_all(text).findings)


def _head(body: str) -> str:
    """A minimal well-formed document, so only the rule under test fires."""
    return f"# Probe\n\n**Status:** fixture. Governs nothing.\n\n## Section\n\n{body}\n"


# --- one violation and one clean form per rule ------------------------------

#: rule -> (a document that violates it, a document that does not)
FIXTURES = {
    "COUNT": (
        _head("The schema has twelve tables and all of them matter."),
        _head("The schema has twelve tables, counted from the tree today."),
    ),
    "GATE": (
        _head("The manifest ACL blocks any app that has not been granted."),
        _head("The manifest ACL blocks any app not granted — enforcement, "
              "since every call routes through it before dispatch."),
    ),
    "ABSENCE": (
        _head("The sweep came back clean and nothing found contradicts it."),
        _head("The sweep did not run, so the answer is unknown rather than clear."),
    ),
    "RUNG": (
        _head("Anything at level 3 or above is withheld from a guest."),
        _head("Anything at L3 or above is withheld from a guest."),
    ),
    "TOMBSTONE": (
        "# Probe\n\n**Status:** fixture. Governs nothing.\n\n"
        "## The old model, superseded\n\nWe do it differently now.\n",
        "# Probe\n\n**Status:** fixture. Governs nothing.\n\n"
        "## The old model, superseded\n\n"
        "Status: retired, do not cite it as doctrine. The successor is "
        "`docs/LANE-MODEL.md`, because the subject widened. Every clause maps "
        "forward and the map is informative only. Kept only so existing "
        "references do not dangle; nothing new should link here.\n",
    ),
    "STATUS": (
        "# Probe\n\n## Section\n\nA document with no declared weight.\n",
        _head("A document that declared its weight."),
    ),
}

#: rule -> the module-level pattern the rule is built on. Neutralising it must
#: silence the violation fixture. STATUS is absent on purpose: it fires on the
#: *absence* of a declaration, so blanking its pattern makes it fire more
#: rather than less, and its mutation is done on the fixture instead.
PATTERN_OF = {
    "COUNT": "_COUNT_CLAIM",
    "GATE": "_GATE_CLAIM",
    "ABSENCE": "_ABSENCE",
    "RUNG": "_BARE_RUNG",
    "TOMBSTONE": "_RETIRED",
}

_NEVER = re.compile(r"(?!x)x")


def test_there_is_a_fixture_for_every_rule():
    """A rule with no fixture is a rule nobody has shown to work."""
    assert set(FIXTURES) == set(RULES), (
        f"fixtures and rules disagree: {set(FIXTURES) ^ set(RULES)}")


def test_every_rule_catches_its_violation():
    for rule, (bad, _) in FIXTURES.items():
        assert _fires(bad, rule), f"{rule} did not catch its own violation"


def test_every_rule_is_silent_on_the_corrected_form():
    """The other half. A rule that fires on everything teaches nothing, and
    a checker people switch off is the same as no checker."""
    for rule, (_, good) in FIXTURES.items():
        assert not _fires(good, rule), (
            f"{rule} fired on the corrected form: "
            f"{[str(f) for f in run_all(good).findings if f.check == rule]}")


def test_neutralising_a_rule_stops_it_catching_anything():
    """Mutation (rule 19). Blank the pattern the rule rests on and the
    violation must stop being caught — which is what proves the fixture is
    held up by the rule and not by something incidental."""
    for rule, attr in PATTERN_OF.items():
        bad = FIXTURES[rule][0]
        assert _fires(bad, rule), f"{rule} fixture broken before mutation"
        original = getattr(prose, attr)
        try:
            setattr(prose, attr, _NEVER)
            assert not _fires(bad, rule), (
                f"{rule} still fired with {attr} neutralised — the fixture is "
                f"not testing the rule it names")
        finally:
            setattr(prose, attr, original)


def test_the_status_rule_can_fail():
    """STATUS's mutation, done on the fixture because the rule fires on an
    absence. Strip the declaration and it must be seen."""
    good = FIXTURES["STATUS"][1]
    assert not _fires(good, "STATUS")
    stripped = "\n".join(
        line for line in good.splitlines() if "Status:" not in line)
    assert _fires(stripped, "STATUS"), "a document with no declared weight passed"


# --- the two middles --------------------------------------------------------


def test_the_existing_sweeps_cover_this_module():
    """`test_craft.py` proves import purity and no-scoring by globbing
    `craft/*.py`. That covers this file today and would silently stop if it
    moved. Assert the coverage rather than inheriting it."""
    swept = {p.name for p in (ROOT / "craft").glob("*.py")}
    assert "prose.py" in swept, "the purity and no-scoring sweeps no longer see this module"

    source = (ROOT / "tests" / "test_craft.py").read_text(encoding="utf-8")
    assert 'ROOT / "craft"' in source and '.glob("*.py")' in source, (
        "test_craft.py no longer sweeps craft/*.py — this module's purity and "
        "no-scoring coverage has moved and nothing here would have noticed")


#: Phrases both rule 13 implementations claim. Neither may pass one.
SHARED_ABSENCE = ("no findings", "all clear", "no issues")

#: The declared divergence. `voice` reads a sentence about to reach a person;
#: `prose` reads a document. Each catches phrasings the other does not, and
#: pinning them here means widening one without the other fails this test
#: rather than drifting quietly (§16 rule 5 — check the middle for rot).
VOICE_ONLY = ("everything looks fine", "nothing to worry about", "all good")
PROSE_ONLY = ("nothing found", "nothing to report", "came back clean",
              "no restrictions", "no problems", "nothing of note")


def test_the_two_absence_rules_do_not_disagree():
    for phrase in SHARED_ABSENCE:
        assert voice.check(f"The check ran. {phrase.capitalize()}."), (
            f"voice missed a shared phrase: {phrase}")
        assert _fires(_head(f"The check ran. {phrase.capitalize()}."), "ABSENCE"), (
            f"prose missed a shared phrase: {phrase}")


def test_the_declared_divergence_is_still_the_actual_one():
    """The rot half. If one side grows to cover the other's list, this fails
    until the lists are updated — the same shape as UTETY's allowlist test."""
    for phrase in VOICE_ONLY:
        assert not _fires(_head(f"The check ran. {phrase.capitalize()}."), "ABSENCE"), (
            f"prose now catches {phrase!r}; move it out of VOICE_ONLY")
    for phrase in PROSE_ONLY:
        assert not voice.check(f"The check ran. {phrase.capitalize()}."), (
            f"voice now catches {phrase!r}; move it out of PROSE_ONLY")


# --- the contract the skin inherits ----------------------------------------


def test_the_vocabulary_cannot_outlive_what_produces_it():
    """`checks.CHECKS` and `checks.DIFF_CHECKS` are declared and consumed by
    nothing, which is §16 in miniature. `RULES` is derived from the registry
    so the same drift is not expressible here."""
    assert RULES == tuple(prose._REGISTRY), "RULES is no longer derived from the registry"
    for name in RULES:
        assert _fires(FIXTURES[name][0], name), f"{name} is declared and produces nothing"


def test_a_declared_finding_moves_but_is_not_hidden():
    """§24's mechanic, inherited whole: the declaration is the artifact."""
    bad = FIXTURES["COUNT"][0]
    plain = run_all(bad)
    assert plain.findings
    target = plain.findings[0]

    declared = run_all(bad, {target.id: "derived by grep, and here is how"})
    assert target.id not in {f.id for f in declared.findings}, "still open"
    assert target.id in {f.id for f, _ in declared.declared}, "suppressed rather than moved"
    assert declared.declared[0][1] == "derived by grep, and here is how"


def test_ids_are_unique_even_when_two_matches_collide():
    text = _head("It has twelve tables.\n\nIt still has twelve tables.")
    ids = [f.id for f in run_all(text).findings]
    assert len(ids) == len(set(ids)), f"colliding ids: {ids}"


def test_an_unreadable_document_is_unavailable_not_clean():
    """Rule 13, turned on the checker itself."""
    for text in ("", "   \n\n  \n", "```\ncode only\n```\n"):
        report = run_all(text)
        assert report.unavailable, f"{text!r} came back with no findings and no reason"
        assert not report.findings


def test_a_report_has_no_totals_field():
    assert set(vars(run_all(_head("x")))) == {
        "findings", "declared", "notes", "unavailable"}
    assert isinstance(run_all(_head("x")), Report)


def test_nothing_in_the_skin_returns_a_number_about_quality():
    """The lyric side asserts this structurally and the skin must inherit it:
    no function here may return an int or float that could be read as a
    judgement of the document."""
    src = (ROOT / "craft" / "prose.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("check_"):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Constant):
                    assert not isinstance(sub.value.value, (int, float)), (
                        f"{node.name} returns a bare number")


# --- quoting, negation, and revision ---------------------------------------


def test_a_quoted_example_does_not_fire():
    """A document teaching a rule quotes what the rule forbids. Firing there
    is how a check gets switched off."""
    text = _head('A rubric that failed to load must not return "no findings".')
    assert not _fires(text, "ABSENCE")


def test_a_denial_is_not_a_claim():
    """`willow_gate.friction_floor` *"flags for a human and never blocks"* —
    a sentence being careful in exactly the way rule 18 asks for."""
    assert not _fires(_head("It flags for a human and never blocks."), "GATE")
    assert _fires(_head("It flags for a human and blocks the dispatch."), "GATE")


def test_revision_reports_both_directions():
    before = _head("It has twelve tables.")
    after = _head("It has twelve tables, counted from the tree today. "
                  "The ACL blocks the call.")
    introduced, notes = run_diff(before, after)
    assert any(f.check == "GATE" for f in introduced), "a new defect went unreported"
    assert any("resolved" in n for n in notes), "the fix went unreported"


def test_the_repository_documents_are_readable():
    """The corpus is in the tree, so read it. Any document coming back
    unavailable means the parser lost it, not that the prose is clean."""
    docs = sorted(DOCS.glob("*.md"))
    assert docs, "no documents found — glob broken, or the sweep is decorative"
    for path in docs:
        report = run_all(path.read_text(encoding="utf-8"))
        assert not report.unavailable, f"{path.name}: {report.unavailable}"


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
