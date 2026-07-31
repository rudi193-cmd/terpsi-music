"""The stdlib-only gate, shown to hold and shown to fail (TM-DEPS-01).

`tools/imports.py` is the enforcement half of the posture 57 docstrings assert
and nothing enforced: every import resolves to the standard library, a
dependency `requirements.txt` declares, or a local module — or it is a finding.
The tree is clean today, so a checker written only against it would pass on the
day it ships and every day after whether or not it works (`tools/purity.py`'s
lesson, the fourth checker in a row to need it). So the fail case is real:
`tests/fixtures/decoys/imports_undeclared.py` imports `requests` and `flask`,
and the gate must catch both.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/test_imports.py -q
    python3 tests/test_imports.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import imports as I  # noqa: E402

DECOY = ROOT / "tests" / "fixtures" / "decoys" / "imports_undeclared.py"


def _allowed():
    return I._STDLIB | I.declared_roots() | I.local_roots()


# --- the real tree ---------------------------------------------------------


def test_the_real_tree_imports_only_what_is_declared():
    """The whole point: over the app and its suite, every import is stdlib, one
    of the two declared dependencies, or a local module. Nothing was scanned is
    not a pass."""
    r = I.check(list(I._default_paths()))
    assert r.verdict is I.Verdict.CLEAN, [str(f) for f in r.findings]
    assert r.scanned > 0


def test_the_two_declared_dependencies_are_the_only_third_party_roots():
    """Derived from `requirements.txt`, not hard-coded, so the gate and the
    declaration cannot drift. If a third dependency is accepted, this figure
    moves and the test is what makes the change visible."""
    assert I.declared_roots() == frozenset({"cryptography", "psycopg"})


def test_every_declared_distribution_maps_to_a_known_import_root():
    """The one limitation, guarded. A distribution whose import name differs
    from its package name (`PyYAML` -> `yaml`) and has no `_DIST_TO_IMPORT`
    entry would be admitted under the wrong name; `unmapped()` is asserted empty
    so that gap fails here rather than silently letting the wrong root pass."""
    assert I.unmapped() == (), (
        f"declared distributions with no import-root mapping: {I.unmapped()}")


# --- the fail case ---------------------------------------------------------


def test_an_undeclared_import_is_a_finding():
    """Rule 19. The decoy imports `requests` and `flask`; both are findings,
    each named by its root, and the verdict is not clean."""
    reaches = I.scan_source(DECOY.read_text(encoding="utf-8"), "decoy.py", _allowed())
    findings = {r.root for r in reaches if r.is_finding}
    assert "requests" in findings and "flask" in findings, findings


def test_the_gate_scan_excludes_the_decoys_so_they_do_not_fail_the_build():
    """The decoy lives under `tests/`, which the gate does scan — so it must be
    excluded by name, or the gate would fail the build on the file that exists
    to prove the gate works. `_files` skips `tests/fixtures/decoys/`."""
    scanned = I._files([ROOT / "tests"])
    assert DECOY not in scanned
    assert all("fixtures/decoys" not in str(p) for p in scanned)


def test_a_dynamic_import_of_an_undeclared_name_is_a_finding():
    """`import_module("numpy")` hides `numpy` from the static graph; the check
    reads the literal and judges it the same as an `import`."""
    src = "from importlib import import_module\nx = import_module('numpy')\n"
    reaches = I.scan_source(src, "d.py", _allowed())
    assert any(r.is_finding and r.root == "numpy" for r in reaches), reaches


def test_a_dynamic_import_with_a_non_literal_name_is_unresolved_not_clean():
    """Rule 13 at the seam: a name the graph cannot read is unknown, never
    waved through."""
    src = "from importlib import import_module\ndef f(n): return import_module(n)\n"
    reaches = I.scan_source(src, "d.py", _allowed())
    assert any(r.kind is I.Kind.UNRESOLVED and r.is_finding for r in reaches)


def test_an_unparseable_file_is_a_finding_not_a_pass():
    reaches = I.scan_source("def broken(:\n", "d.py", _allowed())
    assert len(reaches) == 1 and reaches[0].is_finding
    assert "unparseable" in reaches[0].detail


def test_a_relative_import_is_local_by_construction():
    """`from . import x` and `from .mod import y` are this package's own and
    carry no root to judge — never findings."""
    src = "from . import serving\nfrom .rungs import Rung\n"
    reaches = I.scan_source(src, "records/x.py", _allowed())
    assert not any(r.is_finding for r in reaches), [str(r) for r in reaches]


def test_a_scan_of_nothing_is_vacuous_not_clean():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = I.check([Path(d)])
    assert r.verdict is I.Verdict.VACUOUS and not r.ok


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
