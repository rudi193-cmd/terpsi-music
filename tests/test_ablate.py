"""Rule 19, turned on the thing that enforces rule 19.

`tests/ablate.py` decides whether a guard can be shown to fail. Until
2026-07-31 it decided that from the suite's **exit status alone**, so three
different events shared one answer: a test caught the mutation, the module
stopped importing, and the mutated file stopped parsing. All three exit
nonzero. All three were reported `caught`.

Two shipped mutations were in the second and third state:

* `class Rung(Enum)` -> `IntEnum` raised at import — `IntEnum` members must be
  `int` and the rungs carry names — so `tests/test_rungs.py` died on its import
  line with **zero** failing tests, and its 25-pair comparison sweep had never
  once executed under its own mutation.
* `return None  # (` commented out an opening paren and left a string dangling,
  so `records/conflict.py` did not parse and W-7's sharpest mechanism had never
  been shown to fail.

So `verdict()` now requires a **named** failure. This file is what points at
it, against `tests/fixtures/decoys/ablation` — three outcomes, three decoys,
because a check with three outcomes and one decoy has two decorative branches.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("_ablate", ROOT / "tests" / "ablate.py")
ablate_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ablate_mod)

ablate, verdict, MUTATIONS = ablate_mod.ablate, ablate_mod.verdict, ablate_mod.MUTATIONS

DECOYS = "tests/fixtures/decoys/ablation"
GUARD = "    if value not in ORDER:"


def _sidecar():
    """A breadcrumb of this test's own, never the harness's.

    A real ablation may be in flight while this runs — `tools/conform.py`
    shells out to the harness — and two writers to one sidecar is the defect
    the sidecar exists to fix.
    """
    return Path(tempfile.gettempdir()) / "ablate-selftest-inflight.json"


def _ablate(target, pattern, repl, suite):
    return ablate(f"{DECOYS}/{target}", pattern, repl, "self-test",
                  f"{DECOYS}/{suite}", inflight=_sidecar())


# --- verdict(), as a function ---------------------------------------------


def test_a_passing_suite_means_the_mutation_survived():
    assert verdict(True, "ok   test_a\n") == "SURVIVES"
    assert verdict(True, "") == "SURVIVES"


def test_a_named_failure_is_the_only_thing_that_counts_as_caught():
    assert verdict(False, "ok   test_a\nFAIL test_b\nAssertionError: no\n") == "caught"


def test_a_nonzero_exit_with_no_named_failure_is_an_error_not_a_pass():
    """**The whole point of this file.** A traceback is not a guard firing."""
    crash = ('Traceback (most recent call last):\n'
             '  File "tests/test_rungs.py", line 25, in <module>\n'
             "ValueError: invalid literal for int() with base 10: 'open'\n")
    assert verdict(False, crash) == "NO NAMED FAILURE"
    assert verdict(False, "") == "NO NAMED FAILURE"


def test_the_word_FAIL_must_begin_a_line():
    """A test *named* for failure, or a docstring quoting one, is not a report.
    `tests/test_discipline.py` carries `print("FAIL")` inside decoy source."""
    assert verdict(False, 'ok   test_x\n  the string "FAIL here" appears\n') \
        == "NO NAMED FAILURE"
    assert verdict(False, "ok   test_prints_FAIL_on_error\n") == "NO NAMED FAILURE"


# --- and wired, against the decoys ----------------------------------------


def test_the_decoys_are_green_before_anything_is_mutated():
    """A control. Every result below is meaningless if these start red."""
    for suite in ("test_guarded.py", "test_indifferent.py", "test_unimportable.py"):
        r = subprocess.run([sys.executable, "-B", str(ROOT / DECOYS / suite)],
                           capture_output=True, cwd=ROOT)
        assert r.returncode == 0, f"{suite} is red unmutated"


def test_a_guard_a_test_looks_at_is_caught():
    assert _ablate("guarded.py", GUARD, "    if False:", "test_guarded.py") == "caught"


def test_a_guard_nothing_looks_at_survives():
    """The negative control: the same mutation, a suite that never asks."""
    assert _ablate("guarded.py", GUARD, "    if False:",
                   "test_indifferent.py") == "SURVIVES"


def test_a_mutation_that_stops_the_module_importing_is_not_caught():
    """`IntEnum` members must be `int`; these carry names. The suite exits
    nonzero having run no test at all, and before this check that was `caught`."""
    assert _ablate("unimportable.py", "class Band(enum.Enum):",
                   "class Band(enum.IntEnum):",
                   "test_unimportable.py") == "NO NAMED FAILURE"


def test_a_mutation_that_does_not_apply_is_still_an_error():
    assert _ablate("guarded.py", "if value not in NOTHING:", "if False:",
                   "test_guarded.py") == "NOT APPLIED"


def test_a_pattern_that_occurs_twice_is_an_error_not_a_first_hit():
    """**The third failure mode, found by ablating the harness with itself.**

    `str.replace(pattern, repl, 1)` takes the first occurrence, and "the file
    changed" was the only check. So a pattern appearing twice mutated one site
    and reported on the other. Two rows were in this state: the harness's own
    new mutations matched their entries in `MUTATIONS` rather than the code they
    named, and `records/sending.py`'s `and r.live_at(at)` had left the
    `who_could_see()` half unablated since the row was written.
    """
    assert _ablate("ambiguous.py", GUARD, "    if False:",
                   "test_guarded.py") == "AMBIGUOUS x2"


def test_every_pattern_in_the_real_table_names_exactly_one_site():
    """The check above, applied to the shipped table rather than to a decoy.
    A row that becomes ambiguous through an ordinary refactor is silent
    otherwise — the mutation still applies, to somewhere else."""
    for target, pattern, _repl, label, _suite in MUTATIONS:
        seen = (ROOT / target).read_text(encoding="utf-8").count(pattern)
        assert seen == 1, f"{label}: {seen} occurrences in {target}"


def test_the_decoy_tree_is_restored_afterwards():
    """Every call above mutates a file on disk. If the `finally` stopped
    restoring, this suite would leave the decoys broken for the next reader."""
    for name in ("guarded.py", "unimportable.py"):
        before = (ROOT / DECOYS / name).read_text(encoding="utf-8")
        _ablate(name, GUARD if name == "guarded.py" else "class Band(enum.Enum):",
                "    if False:" if name == "guarded.py" else "class Band(enum.IntEnum):",
                "test_guarded.py" if name == "guarded.py" else "test_unimportable.py")
        assert (ROOT / DECOYS / name).read_text(encoding="utf-8") == before
    assert not _sidecar().exists(), "the breadcrumb outlived the run"


# --- the runners this depends on ------------------------------------------


def test_every_runner_reports_a_crash_as_a_named_failure():
    """`verdict()` requires a `FAIL ` line, and the runners are what print one.

    They caught only `AssertionError` until 2026-07-31, so a test that reached
    an un-guarded path and raised `IndexError` aborted the file — no `FAIL`
    line, and every later test in it silently did not run. Eight of the
    shipped mutations were in exactly that state.
    """
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        src = path.read_text(encoding="utf-8")
        runner = src.split('if __name__ == "__main__":')[-1]
        assert "except Exception as exc:" in runner, f"{path.name} narrows its runner"
        assert "except AssertionError as exc:" not in runner, path.name
        assert 'print(f"FAIL {name}' in runner, f"{path.name} prints no named failure"


def test_the_real_table_names_a_suite_that_exists_for_every_mutation():
    """A mutation pointing at a missing suite would exit nonzero with no `FAIL`
    line, which now reads `NO NAMED FAILURE` rather than `caught`. Cheaper to
    say so here than to discover it as a verdict."""
    for target, _pat, _repl, label, suite in MUTATIONS:
        assert (ROOT / target).exists(), f"{label}: {target} is missing"
        assert (ROOT / suite).exists(), f"{label}: {suite} is missing"


def test_the_module_is_not_broken_shut():
    assert verdict(False, "FAIL test_x\n") == "caught"
    assert verdict(True, "") == "SURVIVES"


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
