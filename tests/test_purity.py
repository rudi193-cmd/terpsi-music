"""The egress and write checks, pointed at code that really does both.

Both of these lived in `tools/conform.py` as ten lines apiece that had only ever
been run against a clean tree, and **both were broken.** The decoys found it in
one run. Same argument as `tests/test_sockets.py`: a guard written against the
tree it guards passes on the day it ships and every day after, whether or not it
works.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import conform  # noqa: E402
import purity  # noqa: E402
from conform import State, check_no_egress, check_write_paths  # noqa: E402
from purity import Reach, counted, egress, reads, scan_source, writes  # noqa: E402

DECOYS = ROOT / "tests" / "fixtures" / "decoys"


def decoy(name):
    p = DECOYS / name
    return p if p.is_dir() else DECOYS / f"{name}.py"


# --- the four holes the old egress check had ------------------------------


def test_a_dynamic_import_is_egress():
    """`__import__("socket")` is not an `ast.Import` node, so nothing in the
    import graph shows it. The old check returned PASS."""
    got = egress([decoy("egress_dynamic")])
    detail = " ".join(t.detail for t in got)
    assert "socket" in detail and "urllib.request" in detail
    assert len(got) == 2


def test_a_process_spawn_is_egress():
    """`subprocess` is not a network module and `subprocess.run(["curl", …])` is
    a network call. It was not in the old set."""
    got = egress([decoy("egress_subprocess")])
    assert len(got) == 1 and got[0].reach is Reach.SPAWN


def test_a_subpackage_is_scanned():
    """**The quietest of the four.** The old scan globbed `*.py`, not `**/*.py`,
    so a subdirectory was invisible and reported as clean — and the evidence
    string said how many modules it had looked at, which was the only clue."""
    got = egress([decoy("egress_nested")])
    assert len(got) == 1 and "leaky.py" in got[0].module


def test_the_egress_check_parses_rather_than_grepping():
    """`egress_in_prose.py` names socket, urllib.request and subprocess in a
    docstring. A grep fails it; an AST scan must not."""
    assert egress([decoy("egress_in_prose")]) == ()


def test_all_four_together_still_returned_PASS_from_the_old_check():
    """The regression this file exists for: one directory holding every hole,
    which the check that shipped called clean."""
    got = egress([DECOYS])
    modules = {t.module.split("/")[-1] for t in got}
    assert {"egress_dynamic.py", "egress_subprocess.py", "leaky.py"} <= modules


# --- the write check, which could not be pointed at anything --------------


def test_it_takes_a_path_at_all():
    """The old one did not, so there was no way to run it against a decoy."""
    import inspect
    assert "where" in inspect.signature(check_write_paths).parameters


def test_it_finds_every_shape_of_write():
    got = writes([decoy("writes_files")])
    detail = " ".join(t.detail for t in got)
    for shape in ("open(", "write_text", "write_bytes", "makedirs", "remove", "rmtree"):
        assert shape in detail, f"{shape} was not seen"


def test_a_non_literal_mode_counts_as_a_write():
    """Unresolvable is not a pass — the same rule `sockets.py` applies to a bind
    whose host comes from the environment. The alternative is a checker that is
    quietest exactly where the code is least legible."""
    got = writes([decoy("writes_unknown_mode")])
    assert len(got) == 1 and got[0].reach is Reach.UNKNOWN_MODE


def test_a_read_is_not_a_write():
    """A check that cries wolf on every `open()` is a check somebody switches
    off. Reads are reported and do not fail."""
    assert writes([decoy("reads_only")]) == ()
    assert len(reads([decoy("reads_only")])) == 2
    assert check_write_paths(decoy("reads_only")).state is not State.FAIL


def test_the_write_check_parses_rather_than_grepping():
    """The old one matched substrings, so a docstring saying *never calls
    `open(`* failed the file it appeared in."""
    assert writes([decoy("writes_in_prose")]) == ()
    assert check_write_paths(decoy("writes_in_prose")).state is not State.FAIL


def test_dataclasses_replace_is_not_os_replace():
    """**A false positive found while writing this.** The first version put
    `replace` in the write set unqualified and flagged every frozen-dataclass
    update in `records/` as a disk write. A check that cries wolf is a check
    that gets disabled, so an ambiguous verb needs a filesystem owner."""
    src = "import dataclasses\nx = dataclasses.replace(y, a=1)\nz = d.copy()\n"
    assert scan_source(src, "m.py") == ()
    assert writes([ROOT / "records"]) == (), "records/ reported a write it does not make"


def test_an_unambiguous_verb_needs_no_owner():
    assert scan_source("p.write_text('x')\n", "m.py")[0].reach is Reach.WRITE
    assert scan_source("shutil.rmtree(d)\n", "m.py")[0].reach is Reach.WRITE


def test_a_write_on_a_literal_Path_is_seen():
    got = scan_source("from pathlib import Path\nPath('x').unlink()\n", "m.py")
    assert got and got[0].reach is Reach.WRITE


def test_a_write_through_a_Path_VARIABLE_is_NOT_seen_documented():
    """**A limitation, not a guarantee.** `p.unlink()` where `p` holds a `Path`
    needs type inference this checker does not do. Asserted by name so it reads
    as a known blind spot rather than as coverage, and so closing it later is a
    visible diff rather than a silent widening."""
    assert scan_source("p = Path('x')\np.unlink()\n", "m.py") == ()


# --- both checks report what they looked at -------------------------------


def test_a_scan_of_nothing_is_unknown_and_not_a_pass():
    """*No findings* over zero files and over nineteen are the same sentence and
    different facts — `sockets.py` calls this shape VACUOUS."""
    empty = ROOT / "tests" / "fixtures" / "decoys" / "does-not-exist"
    assert counted([empty]) == 0
    assert check_no_egress(empty).state is State.UNKNOWN
    assert check_write_paths(empty).state is State.UNKNOWN


def test_the_evidence_says_how_many_files_were_looked_at():
    got = check_no_egress()
    assert got.state is State.PASS
    assert "module(s) scanned" in got.evidence and "recursively" in got.evidence


def test_the_write_check_stays_unknown_because_no_write_path_is_declared():
    """No writes found is not the same as writes being declared and matched.

    **This test read `"no manifest" in got.evidence` until 2026-07-31**, when
    §18 item 4 landed one. The manifest declares surfaces, listeners and
    permissions and says nothing about write paths, so this check is `UNKNOWN`
    for a narrower reason than before and the evidence now says which — the old
    wording would have gone on claiming a fact the tree had moved past, which
    is rule 17's defect living in a checker's own evidence string.
    """
    got = check_write_paths()
    assert got.state is State.UNKNOWN
    assert "no write paths" in got.evidence, got.evidence


# --- the checkers do not do the things they check for ---------------------


def test_purity_parses_and_never_imports_what_it_inspects():
    src = (ROOT / "tools" / "purity.py").read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    for banned in ("import_module(", "__import__(", "exec(", "eval(", "runpy"):
        assert banned not in body, f"tools/purity.py executes what it inspects: {banned}"


def test_the_checker_is_clean_under_its_own_scan():
    """It names every egress module and every write verb in the file. If it
    reached for one, it would have to report itself."""
    assert egress([ROOT / "tools" / "purity.py"]) == ()
    assert writes([ROOT / "tools" / "purity.py"]) == ()


def test_the_core_is_clean_today():
    assert egress([ROOT / "records"]) == ()
    assert writes([ROOT / "records"]) == ()


def test_an_unparseable_file_cannot_be_shown_to_be_clean():
    got = scan_source("def broken(:\n", "broken.py")
    assert got and "unparseable" in got[0].detail


def test_the_module_is_not_broken_shut():
    assert check_no_egress().state is State.PASS
    assert check_no_egress(decoy("egress_dynamic")).state is State.FAIL
    assert check_write_paths(decoy("writes_files")).state is State.FAIL


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
