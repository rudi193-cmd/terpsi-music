"""The tripwire on the second dependency, against decoys that really import it.

`tools/drivers.py` exists because the store's driver was accepted narrowly: the
store may talk to PostgreSQL and nothing else may. A checker written against a
tree that already obeys the rule passes on the day it ships and every day after
— `tools/purity.py`'s recorded finding, three checkers in a row — so acceptance
here is entirely against `tests/fixtures/decoys/driver_*.py`: source that really
imports it outside the store, source that only names it, and source that reaches
it through `importlib` where no import statement declares it.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/test_drivers.py -q
    python3 tests/test_drivers.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import drivers  # noqa: E402
import providers  # noqa: E402

DECOYS = ROOT / "tests" / "fixtures" / "decoys"


def test_a_driver_import_outside_the_store_is_a_finding():
    r = drivers.check([DECOYS / "driver_outside_store.py"])
    assert r.verdict is drivers.Verdict.FINDINGS and not r.ok
    assert any("imports psycopg" in f.detail for f in r.findings)


def test_a_dynamic_import_of_the_driver_is_a_finding():
    """No import statement declares it, so the import graph shows nothing."""
    r = drivers.check([DECOYS / "driver_dynamic.py"])
    assert r.verdict is drivers.Verdict.FINDINGS
    assert any("import_module" in f.detail for f in r.findings)


def test_the_driver_named_only_in_prose_is_not_a_finding():
    """The decoy against the wrong implementation. A grep fails this file; the
    finding is an import, not a word."""
    text = (DECOYS / "driver_in_prose.py").read_text(encoding="utf-8")
    assert text.count("psycopg") >= 4, "the prose decoy stopped naming the driver"
    r = drivers.check([DECOYS / "driver_in_prose.py"])
    assert r.verdict is drivers.Verdict.VACUOUS, [str(x) for x in r.reaches]
    assert not r.findings


def test_the_store_is_admitted_and_it_really_does_import_the_driver():
    """Both halves. If `store/` stopped importing the driver the scan would be
    vacuous, and a vacuous scan must not read as a clean one."""
    r = drivers.check([ROOT / "store"])
    assert r.verdict is drivers.Verdict.CLEAN and r.ok
    assert r.reaches, "nothing in store/ imports the driver; the scan is vacuous"
    assert all(x.allowed for x in r.reaches)


def test_the_real_tree_carries_the_driver_only_in_the_store():
    """The shipped claim, over the shipped tree. Red the day an import lands
    anywhere else — which is the whole reason this file exists rather than a
    line in a review checklist."""
    targets = [ROOT / p for p in ("records", "tools", "store", "craft",
                                  "presentation", "surfaces", "venue",
                                  "voice.py", "personas.py")]
    r = drivers.check([t for t in targets if t.exists()])
    assert not r.findings, [str(f) for f in r.findings]
    assert r.verdict is drivers.Verdict.CLEAN, (
        "the tree imports no driver anywhere, so this checker is vacuous")


def test_an_unparseable_file_is_a_finding_wherever_it_sits():
    """Rule 13. A file nobody can read cannot be shown not to import the driver,
    and being inside `store/` does not make it readable."""
    for where in ("store/broken.py", "records/broken.py"):
        found = drivers.scan_source("def broken(:\n", where)
        assert found and found[0].is_finding, where


def test_the_allowlist_is_a_prefix_and_not_a_substring():
    """`storefront/` is not `store/`. A substring match would admit it, and the
    module that got admitted by accident is the one nobody reviews."""
    assert drivers.admitted("store/connecting.py")
    assert drivers.admitted("store")
    assert not drivers.admitted("storefront/connecting.py")
    assert not drivers.admitted("tools/store_helper.py")


def test_the_dotted_helpers_are_imported_from_providers_and_not_respelled():
    """§16 in miniature: two spellings of *resolve an `ast.Attribute` chain* is
    a pair. This module has one, and it is `tools/providers.py`'s."""
    assert drivers._dotted is providers._dotted
    assert drivers._tail is providers._tail


def test_the_requirements_file_pins_the_driver_with_its_reason():
    """The pin and the tripwire are a pair (rule 12), and the pin without a
    reason is the dependency nobody can argue with later."""
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pins = [ln.strip() for ln in text.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]
    driver = [p for p in pins if p.startswith("psycopg")]
    assert len(driver) == 1, f"expected one driver pin, found {driver}"
    assert "==" in driver[0], f"{driver[0]} is not pinned exactly"
    # The reason and its date, in the comment block above the pin.
    reason = text.split(driver[0])[0]
    assert "store" in reason and "2026-07-31" in reason, (
        "the pin carries no reason and no date")
    # Derived, never quoted (rule 17): this file is the tree's dependency list.
    assert len(pins) == 2, f"requirements.txt carries {len(pins)} pins: {pins}"


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
