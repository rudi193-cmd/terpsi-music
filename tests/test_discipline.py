"""The last two checkers, pointed at code that breaks each rule.

Four of `conform.py`'s checks have now been tested for the first time. **Four
were broken.** These two were the worst of the set: one was wrong in both
directions at once, and the other passed a suite that reports success no matter
what.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import conform  # noqa: E402
import discipline  # noqa: E402
from conform import State, check_revocation_is_dated, check_suite_runs_standalone  # noqa: E402
from discipline import (  # noqa: E402
    NOT_SUITES, Cut, Runner, deletions, runners, scan_deletions, scan_runner,
)

DECOYS = ROOT / "tests" / "fixtures" / "decoys"


def decoy(name):
    p = DECOYS / name
    return p if p.is_dir() else DECOYS / f"{name}.py"


# --- revocation: the shipped check was wrong in both directions -----------


def test_every_spelling_of_deletion_is_found():
    got = deletions([decoy("deletes_standing")])
    kinds = [d.cut for d in got]
    assert Cut.DEL in kinds, "`del edges[0]` — the plainest spelling — was missed"
    assert Cut.SQL in kinds, "an executed DELETE FROM was missed"
    assert kinds.count(Cut.REMOVE) == 3
    assert len(got) == 5


def test_a_leading_underscore_does_not_hide_a_removal():
    """`\\bedges` finds no word boundary in `self._edges`, because an underscore
    is a word character. The shipped regex missed it for that reason alone."""
    got = scan_deletions("def f():\n    self._edges.remove(x)\n", "m.py")
    assert got and got[0].cut is Cut.REMOVE


def test_a_subdirectory_is_scanned():
    got = deletions([decoy("deletes_nested")])
    assert len(got) == 1 and "buried.py" in got[0].module


def test_prose_about_deleting_is_not_a_deletion():
    """**The false positive the shipped check actually made.** It flagged the
    one clean file — whose docstring reads *"never call `edges.remove(`"* — while
    missing five real deletions in the file next to it. A rule written in prose
    is not the rule being broken."""
    assert deletions([decoy("deletes_in_prose")]) == ()


def test_a_DELETE_only_counts_when_it_is_handed_to_something():
    """The first version of *this* check walked every string constant and
    flagged its own decoy's docstring — the same mistake, one layer up."""
    assert scan_deletions('X = "DELETE FROM edge"\n', "m.py") == ()
    got = scan_deletions('db.execute("DELETE FROM edge WHERE id = ?")\n', "m.py")
    assert got and got[0].cut is Cut.SQL


def test_dating_a_revocation_is_not_deleting_it():
    assert deletions([decoy("dates_standing")]) == ()


def test_a_comprehension_is_NOT_flagged_documented():
    """**A limitation, and the reason the check is narrower than it looks.**

    `[e for e in edges if e.live_at(at)]` is how `records/sending.py` derives a
    recipient list, and it is character for character how you would drop a
    revoked row. In a codebase of pure predicates the two are the same
    operation, so this cannot separate them and does not try.

    Revocation-by-delete is a property of a **store**, and there is no store.
    Asserted by name so nobody mistakes the silence for coverage."""
    src = "def live(edges, at):\n    return [e for e in edges if e.live_at(at)]\n"
    assert scan_deletions(src, "m.py") == ()


def test_the_core_is_clean_and_the_check_says_why_that_is_narrow():
    got = check_revocation_is_dated()
    assert got.state is State.UNKNOWN, (
        "a PASS here would overstate what can be checked without a store"
    )
    assert "there is no store" in got.evidence


def test_it_fails_when_pointed_at_a_deletion():
    assert check_revocation_is_dated(decoy("deletes_standing")).state is State.FAIL
    assert check_revocation_is_dated(decoy("dates_standing")).state is State.PASS


# --- standalone runners: the shipped check passed all three failures ------


def test_a_suite_that_only_mentions_main_in_a_docstring_is_missing_a_runner():
    got = scan_runner('"""Explains that __main__ is required."""\n', "m.py")
    assert got.runner is Runner.MISSING


def test_an_empty_guard_is_not_a_runner():
    s = runners([decoy("runners") / "test_empty_runner.py"])[0]
    assert s.runner is Runner.EMPTY


def test_a_runner_that_cannot_fail_the_process_is_worse_than_none():
    """**The one that matters.** It catches every failure, prints `FAIL`, and
    exits 0 — so the conformance record carries a row saying the suite runs
    standalone while the suite reports success no matter what."""
    s = runners([decoy("runners") / "test_swallowing_runner.py"])[0]
    assert s.runner is Runner.SWALLOWS
    assert "worse than" in s.detail


def test_the_shape_this_repository_uses_passes():
    s = runners([decoy("runners") / "test_good_runner.py"])[0]
    assert s.ok


def test_sys_exit_counts_as_well_as_raise_SystemExit():
    src = ('def test_x():\n    assert True\n\n'
           'if __name__ == "__main__":\n    import sys\n    sys.exit(0)\n')
    assert scan_runner(src, "m.py").runner is Runner.OK


def test_the_left_side_must_be_dunder_name():
    """`if SHIM == "__main__": raise SystemExit(0)` compares the right *string*
    against the wrong *name*. It is not a runner, and only the left-hand check
    says so — the two halves of the guard need separate decoys or one of them
    is never exercised."""
    src = ('def test_x():\n    assert True\n\n'
           'if SHIM == "__main__":\n    raise SystemExit(0)\n')
    assert scan_runner(src, "m.py").runner is Runner.MISSING


def test_the_right_side_must_be_dunder_main():
    """The mirror. `if __name__ == "__not_main__":` never runs, so a block
    behind it is not a runner."""
    src = ('def test_x():\n    assert True\n\n'
           'if __name__ == "__not_main__":\n    raise SystemExit(0)\n')
    assert scan_runner(src, "m.py").runner is Runner.MISSING


def test_the_guard_is_matched_structurally_not_by_substring():
    """`if __name__ == "__main__":` is an AST shape. The shipped check asked
    whether the *string* appeared anywhere in the file."""
    src = 'NOTE = "run me with __main__"\nraise SystemExit(0)\n'
    assert scan_runner(src, "m.py").runner is Runner.MISSING


# --- the decoys are excluded from the real scan, and only there -----------


def test_the_real_scan_skips_fixtures():
    """Decoys are deliberately broken. Counting them as suites would make this
    check fail forever, which is how a check gets deleted rather than fixed."""
    got = runners([ROOT / "tests"])
    assert all("fixtures" not in s.module for s in got)
    assert all(s.ok for s in got), [s.module for s in got if not s.ok]
    assert NOT_SUITES == ("fixtures",)


def test_pointing_it_at_the_fixtures_finds_every_one():
    """The other half, so the exclusion cannot quietly become a blind spot."""
    got = runners([decoy("runners")], skip=())
    assert {s.runner for s in got} == {Runner.OK, Runner.EMPTY, Runner.MISSING,
                                       Runner.SWALLOWS}


def test_the_real_check_passes_and_counts_what_it_looked_at():
    got = check_suite_runs_standalone()
    assert got.state is State.PASS and "test file(s)" in got.evidence


def test_it_fails_when_pointed_at_a_broken_runner():
    assert check_suite_runs_standalone(decoy("runners")).state is State.FAIL


def test_a_scan_of_nothing_is_unknown_and_not_a_pass():
    empty = DECOYS / "does-not-exist"
    assert check_suite_runs_standalone(empty).state is State.UNKNOWN
    assert check_revocation_is_dated(empty).state is State.UNKNOWN


# --- the checker does not do what it checks for ---------------------------


def test_discipline_parses_and_never_imports_what_it_inspects():
    src = (ROOT / "tools" / "discipline.py").read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    for banned in ("import_module(", "__import__(", "exec(", "eval(", "runpy"):
        assert banned not in body


def test_the_checker_is_clean_under_its_own_scan():
    """It names `del`, `remove`, `clear` and `DELETE FROM` throughout. If it
    performed one, it would have to report itself."""
    assert deletions([ROOT / "tools" / "discipline.py"]) == ()


def test_an_unparseable_file_cannot_be_shown_to_be_clean():
    got = scan_deletions("def broken(:\n", "broken.py")
    assert got and "unparseable" in got[0].detail
    assert scan_runner("def broken(:\n", "broken.py").runner is Runner.MISSING


def test_the_module_is_not_broken_shut():
    assert check_suite_runs_standalone().state is State.PASS
    assert check_revocation_is_dated(decoy("dates_standing")).state is State.PASS


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
