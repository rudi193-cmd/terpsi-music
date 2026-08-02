"""§18 item 6: the conformance record, and the checks behind it shown to fail.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import conform  # noqa: E402
from conform import Check, State, check_no_egress, main, render, run, write  # noqa: E402

AT = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)

#: `check_ablation` shells out to the whole mutation harness (~14s). These tests
#: are about `conform.py`, not about the guards — `tests/ablate.py` covers those
#: directly and `tools/conform.py` runs it for real. Skipping it here keeps the
#: ordinary suite fast without anything going unchecked.
FAST = ("ablation",)


# --- UNKNOWN is not a pass ------------------------------------------------


def test_unknown_does_not_conform():
    """Rule 13, at the level of the record. Most of §17's guarantees are
    undecidable here today, and a record that let those read as passing would
    be the formality §17 warns about."""
    for s in (State.UNKNOWN, State.ABSENT, State.FAIL):
        assert not Check("x", "y", s, "e").conforms
    assert Check("x", "y", State.PASS, "e").conforms


def test_todays_record_is_mostly_not_pass_and_that_is_correct():
    """**Asserted deliberately.** If this ever reads all-pass, either the work
    is genuinely done or the checks have been softened, and the two look
    identical from outside. This test makes the second visible."""
    checks = run(skip=FAST)
    assert any(c.state is State.UNKNOWN for c in checks), (
        "no UNKNOWN checks remain — either §17's guarantees are all decided "
        "here now, or the undecidable ones were quietly dropped. Say which."
    )


# --- the checks can fail (rule 19) ----------------------------------------


def test_the_egress_check_complains_when_pointed_at_a_decoy():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "clean.py").write_text("import hashlib\n")
        assert check_no_egress(p).state is State.PASS

        (p / "leaky.py").write_text("import socket\n")
        got = check_no_egress(p)
        assert got.state is State.FAIL and "socket" in got.evidence


def test_the_egress_check_sees_a_from_import_too():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "sneaky.py").write_text("from urllib.request import urlopen\n")
        assert check_no_egress(p).state is State.FAIL


def test_the_egress_check_is_not_fooled_by_a_name_in_a_string():
    """The naive version greps. This one parses, so a docstring saying *no
    socket* does not fail the file it appears in."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "honest.py").write_text('"""No socket, no http, no network."""\nx = 1\n')
        assert check_no_egress(p).state is State.PASS


def test_the_real_core_passes_it():
    got = check_no_egress()
    assert got.state is State.PASS, f"records/ reaches the network: {got.evidence}"


def test_the_declared_sockets_check_can_be_shown_to_fail():
    """Rule 19. The PASS and UNKNOWN paths run on today's listener-free tree;
    the FAIL branch never did, because the check took no argument to point at a
    decoy — the one sibling of `check_no_egress` that could not be. A module
    binding an all-interface listener with no manifest to declare it must FAIL,
    and a listener-free module must read UNKNOWN, never PASS."""
    decoys = conform.ROOT / "tests" / "fixtures" / "decoys"
    no_manifest = Path("/nonexistent/manifest.json")
    bad = conform.check_declared_sockets(where=[decoys / "all_interfaces.py"],
                                         manifest=no_manifest)
    assert bad.state is State.FAIL, bad
    vacuous = conform.check_declared_sockets(where=[decoys / "clean.py"],
                                             manifest=no_manifest)
    assert vacuous.state is State.UNKNOWN, vacuous


def test_the_component_map_check_can_be_shown_to_fail():
    """Rule 19. The wrapper turns the subprocess exit into PASS or FAIL, and on
    the real tree the exit is always zero — so only the PASS side had run. Point
    it at a script that exits nonzero and the FAIL side must fire."""
    with tempfile.TemporaryDirectory() as d:
        one = Path(d) / "exits_one.py"
        one.write_text("import sys; sys.exit(1)\n")
        assert conform.check_component_map(script=one).state is State.FAIL
        zero = Path(d) / "exits_zero.py"
        zero.write_text("print('§14: decoy ok')\n")
        assert conform.check_component_map(script=zero).state is State.PASS


# --- the record -----------------------------------------------------------


def test_a_record_is_never_overwritten():
    """*'Does it conform'* is answerable from any one record; *'when did it
    stop'* only from the series. An overwritable record answers the first
    question and destroys the second."""
    with tempfile.TemporaryDirectory() as d:
        conform.RECORDS = Path(d) / "conformance"
        checks = [Check("a", "b", State.PASS, "e")]
        first = write(checks, AT)
        assert first.exists()
        try:
            write(checks, AT)
        except FileExistsError:
            return
        finally:
            conform.RECORDS = conform.ROOT / "docs" / "conformance"
        raise AssertionError("a second run overwrote the first record")


def test_the_record_carries_the_date_the_commit_and_the_states():
    text = render([Check("a", "guarantee one", State.PASS, "looked at x"),
                   Check("b", "guarantee two", State.UNKNOWN, "cannot decide")], AT)
    assert "2026-07-30" in text
    assert "**PASS**" in text and "**UNKNOWN**" in text
    assert "1 pass · 0 fail · 1 unknown" in text
    assert "`UNKNOWN` is not a pass" in text


def test_the_record_says_when_the_tree_was_dirty():
    """A record pinned to a commit that does not describe what was checked is
    worse than an unpinned one, because it looks precise."""
    import subprocess
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, cwd=conform.ROOT).stdout.strip()
    text = render([Check("a", "b", State.PASS, "e")], AT)
    assert ("working tree dirty" in text) == bool(dirty), (
        "the record's dirty-tree warning disagrees with git"
    )


def test_the_outcome_digest_changes_when_a_state_changes():
    a = render([Check("a", "b", State.PASS, "e")], AT)
    b = render([Check("a", "b", State.FAIL, "e")], AT)
    assert a != b
    da = [l for l in a.splitlines() if "outcome digest" in l][0]
    db = [l for l in b.splitlines() if "outcome digest" in l][0]
    assert da != db, "the digest did not move when an outcome did"


def test_the_digest_ignores_evidence_wording():
    """Rewording an evidence string is not a change of outcome, and a digest
    that moved on it would make the series unreadable."""
    a = render([Check("a", "b", State.PASS, "looked at x")], AT)
    b = render([Check("a", "b", State.PASS, "examined x")], AT)
    da = [l for l in a.splitlines() if "outcome digest" in l][0]
    db = [l for l in b.splitlines() if "outcome digest" in l][0]
    assert da == db


# --- the exit code --------------------------------------------------------


def test_a_fail_is_a_build_failure_and_an_unknown_is_not():
    """UNKNOWN must not fail the build: most of §17's guarantees are
    undecidable here, and a gate that always fails is a gate that gets switched
    off."""
    real = conform.CHECKS
    try:
        conform.CHECKS = (lambda: Check("u", "w", State.UNKNOWN, "e"),)
        assert main([]) == 0
        conform.CHECKS = (lambda: Check("f", "w", State.FAIL, "e"),)
        assert main([]) == 1
    finally:
        conform.CHECKS = real


def test_the_suite_runs_today_without_failing():
    assert not [c for c in run(skip=FAST) if c.state is State.FAIL], (
        "a conformance check is failing; that is a build failure, not a note"
    )


def test_skipping_omits_a_check_and_never_invents_a_passing_one():
    """A conformance record with a hole in it is honest; one with an invented
    row is not.

    Uses a stand-in registry rather than the real one: the real `check_ablation`
    shells out to 78 mutations, and paying 40s to learn that a filter filters is
    the kind of slow suite people stop running.
    """
    real = conform.CHECKS
    try:
        def check_ablation():
            return Check("ablation", "w", State.PASS, "e")

        def check_no_egress():
            return Check("no-egress", "w", State.PASS, "e")

        conform.CHECKS = (check_ablation, check_no_egress)
        full = {c.id for c in run()}
        fast = {c.id for c in run(skip=FAST)}
        assert full == {"ablation", "no-egress"}
        assert fast == {"no-egress"}, "skip() dropped the wrong check or invented a row"
    finally:
        conform.CHECKS = real


def test_the_real_ablation_check_is_wired_and_passes():
    """Separate, and the slow one. The stand-in above proves the filter; this
    proves the thing being filtered is real."""
    got = conform.check_ablation()
    assert got.state is State.PASS, got.evidence
    assert "ablate red" in got.evidence


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
