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
from conform import (  # noqa: E402
    Check, State, check_no_egress, check_security_audit, main, render, run, write,
)

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


# --- the security audit, as a gate rather than a document ------------------

#: A minimal audit document. `PIN` is filled in per test, because the check
#: asks git whether the pinned commit is in this history — a pin naming a tree
#: nobody has is not evidence about this one.
_AUDIT = """\
# Security audit — probe

- **date** `{when}`
- **commit** `{pin}`

| check | what | verdict | severity | evidence |
|---|---|---|---|---|
| `R1` | sql | **NOT-APPLICABLE** | — | applies when a driver arrives |

| id | check | severity | status | one line |
|---|---|---|---|---|
{rows}
"""


def _audit(d, *, when="2026-07-31", pin=None, rows=""):
    if pin is None:
        import subprocess
        pin = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, cwd=conform.ROOT).stdout.strip()
    path = Path(d) / "SECURITY-AUDIT.md"
    path.write_text(_AUDIT.format(when=when, pin=pin, rows=rows), encoding="utf-8")
    return path


def test_a_missing_audit_is_absent_and_absent_is_not_a_pass():
    """Rule 13, and the state §10 cares about most: an install gate that does
    not exist is a different fact from one that ran and found nothing."""
    with tempfile.TemporaryDirectory() as d:
        got = check_security_audit(Path(d) / "nothing-here.md")
    assert got.state is State.ABSENT and not got.conforms


def test_an_open_high_finding_fails_the_build():
    """The reason this row is a gate. §10 treats the rubric as install
    acceptance, and an acceptance check that reports a high finding without
    stopping anything is a ledger."""
    with tempfile.TemporaryDirectory() as d:
        got = check_security_audit(_audit(
            d, rows="| `TM-PROBE-01` | R9 | `S1` | open | it is bad |"))
    assert got.state is State.FAIL and "TM-PROBE-01" in got.evidence


def test_a_closed_high_finding_does_not_fail_the_build():
    """The other direction. A check that fails on every finding ever recorded
    is one somebody deletes the findings from."""
    with tempfile.TemporaryDirectory() as d:
        got = check_security_audit(_audit(
            d, rows="| `TM-PROBE-02` | R9 | `S1` | closed 2026-07-31 | it was bad |"))
    assert got.state is State.PASS, got.evidence


def test_an_open_low_finding_does_not_fail_the_build():
    with tempfile.TemporaryDirectory() as d:
        got = check_security_audit(_audit(
            d, rows="| `TM-PROBE-03` | R14 | `S3` | open | unenforced |"))
    assert got.state is State.PASS and "1 open" in got.evidence


def test_a_stale_audit_is_unknown_rather_than_a_pass():
    """An audit is a statement about a tree at a date. Past the limit it stops
    being evidence about this one, and `UNKNOWN` is what that state is called."""
    with tempfile.TemporaryDirectory() as d:
        got = check_security_audit(_audit(d, when="2020-01-01"))
    assert got.state is State.UNKNOWN and str(conform.STALE_AFTER_DAYS) in got.evidence


def test_an_audit_with_no_date_or_no_pin_is_unknown():
    with tempfile.TemporaryDirectory() as d:
        undated = Path(d) / "undated.md"
        undated.write_text("# audit\n\n- **commit** `d2817f2`\n", encoding="utf-8")
        assert check_security_audit(undated).state is State.UNKNOWN

        unpinned = Path(d) / "unpinned.md"
        unpinned.write_text("# audit\n\n- **date** `2026-07-31`\n", encoding="utf-8")
        assert check_security_audit(unpinned).state is State.UNKNOWN


def test_a_pin_this_history_does_not_contain_is_unknown():
    """The one thing the pin actually decides. *How far behind* is a judgement
    about diffs and is not decidable here — which is why staleness is a date.

    Two branches since 2026-07-31, because git has two ways of not saying yes
    and they are different facts: a sha it has never seen (this fixture's
    zeros) is *undecidable*, while a real commit outside HEAD's ancestry is a
    definite *no*. CI's shallow checkout hit the first and the check reported
    the second — a negative nobody established — which is how one red run
    bought this split."""
    with tempfile.TemporaryDirectory() as d:
        got = check_security_audit(_audit(d, pin="0" * 40))
    assert got.state is State.UNKNOWN and "cannot decide" in got.evidence

    import subprocess as sp
    r = sp.run(["git", "rev-list", "--max-parents=0", "HEAD"],
               capture_output=True, text=True, cwd=conform.ROOT)
    root = r.stdout.split()[0] if r.returncode == 0 and r.stdout.strip() else None
    orphan = sp.run(["git", "commit-tree", root + "^{tree}", "-m", "orphan"],
                    capture_output=True, text=True, cwd=conform.ROOT) if root else None
    if orphan and orphan.returncode == 0:
        with tempfile.TemporaryDirectory() as d:
            got = check_security_audit(_audit(d, pin=orphan.stdout.strip()))
        assert got.state is State.UNKNOWN and "not an ancestor" in got.evidence


def test_the_real_audit_document_is_read_and_passes():
    """Separate from the probes above: they prove the branches, this proves the
    thing being branched on is the document in the tree."""
    got = check_security_audit()
    assert got.state is State.PASS, got.evidence
    assert "SECURITY-AUDIT.md" in got.evidence


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


def test_write_reports_the_tree_it_found_not_the_one_it_made():
    """**The observer effect, and it shipped for one run.**

    `render()` asks git whether the working tree is dirty. An empty record file
    already created in `docs/conformance/` is itself an untracked change, so
    rendering *inside* the `open("x")` block makes every record report dirty —
    including one written from a clean checkout, which is the case the warning
    exists to distinguish. `test_the_record_says_when_the_tree_was_dirty` calls
    `render()` directly and could not see it.

    So the probe is a **clean git repository of its own**, which is the only
    place the two orderings give different answers — this repository is dirty
    whenever `tests/ablate.py` is mutating it, and a probe against this tree
    would agree with the defect and pass.
    """
    import subprocess

    def git(where, *args):
        return subprocess.run(["git", "-c", "user.email=probe@example.invalid",
                               "-c", "user.name=probe", *args],
                              capture_output=True, text=True, cwd=where)

    with tempfile.TemporaryDirectory() as d:
        probe = Path(d)
        git(probe, "init", "-q")
        (probe / "seed.txt").write_text("clean\n", encoding="utf-8")
        git(probe, "add", "-A")
        git(probe, "commit", "-q", "-m", "seed")
        assert not git(probe, "status", "--porcelain").stdout.strip(), (
            "the probe repository did not start clean; the test proves nothing"
        )

        real_root, real_records = conform.ROOT, conform.RECORDS
        try:
            conform.ROOT = probe
            conform.RECORDS = probe / "docs" / "conformance"
            text = write([Check("a", "b", State.PASS, "e")], AT).read_text(
                encoding="utf-8")
        finally:
            conform.ROOT, conform.RECORDS = real_root, real_records

    assert "working tree dirty" not in text, (
        "a record written from a clean checkout reported the tree dirty — the "
        "act of creating the file is what git saw"
    )


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
    shells out to the whole mutation table, and paying that to learn that a
    filter filters is the kind of slow suite people stop running. (The count
    that stood here was a figure the table had moved past — rule 17, in the
    file that tests the conformance record.)
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
