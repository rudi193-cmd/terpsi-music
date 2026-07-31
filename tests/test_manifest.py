"""The manifest, and the reconciliation that lands in the same commit as it.

Rule 12, and §18 item 4's closing note: *"rule 12's socket-reconciliation test
lands in the same commit as the manifest, in this repository's own CI rather
than the store's."* This file is that test. §4.3's failure was an ordering — a
declaration shipped first and nothing was ever pointed at it — so the checker
came first (`tools/sockets.py`, and its own suite), and the manifest arrives
against something that already refuses.

Every check below is pointed at the forbidden act: a listener nothing declares,
a declaration nothing binds, a surface on disk nobody declared, a permission
that reaches a third party, a typo'd key, and a scan that covered nothing.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import manifest as M  # noqa: E402
import sockets  # noqa: E402

DECOYS = ROOT / "tests" / "fixtures" / "decoys"

GOOD = {
    "app": "terpsi-music",
    "manifest_version": 1,
    "surfaces": ["print", "text", "tui", "web"],
    "listeners": [],
    "outbound": [],
    "permissions": ["local_storage"],
    "inference": {"provider": "local", "cloud_fallback": False},
}


def _manifest(data):
    path = Path(tempfile.mkdtemp()) / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _codes(r):
    return {f.code for f in r.findings}


# --- today's tree ---------------------------------------------------------


def test_the_repository_reconciles_with_its_own_manifest():
    r = M.reconcile()
    assert r.ok, [f"{f.code}: {f.detail}" for f in r.findings]
    assert r.scanned > 0
    assert r.surfaces_declared == r.surfaces_present == ("print", "text", "tui", "web")


def test_the_manifest_declares_no_listener_because_nothing_binds_one():
    """The claim, stated as a claim: this is falsifiable and it holds today."""
    declared = sockets.declared_from(M.MANIFEST)
    assert declared == (), declared
    found = sockets.scan(list(M.sources()))
    assert [str(e) for e in found] == [], "something in the scanned tree opens a socket"


# --- the moment a listener appears ---------------------------------------


def test_a_listener_in_a_scanned_path_fails_the_build():
    """Nobody has to remember to switch the check on when a surface starts
    listening — this is the case §4.3 records as having shipped undetected."""
    r = M.reconcile(paths=list(M.sources()) + [DECOYS / "all_interfaces.py"])
    assert not r.ok
    assert "UNDECLARED" in _codes(r)


def test_declaring_the_port_is_not_enough_the_host_must_match():
    """`0.0.0.0:8560` against a manifest declaring loopback: true to a checker
    comparing ports, false to anyone on the segment."""
    m = _manifest(dict(GOOD, listeners=[
        {"host": "127.0.0.1", "port": "8560", "surface": "web"}]))
    r = M.reconcile(manifest=m, paths=[DECOYS / "all_interfaces.py"])
    assert "HOST_WIDER_THAN_DECLARED" in _codes(r)


def test_a_declaration_nothing_binds_is_a_finding_too():
    m = _manifest(dict(GOOD, listeners=[
        {"host": "127.0.0.1", "port": "9999", "surface": "gone"}]))
    r = M.reconcile(manifest=m, paths=[ROOT / "presentation" / "ir.py"])
    assert "DECLARED_ABSENT" in _codes(r)


def test_an_outbound_connection_is_a_finding_whatever_the_manifest_says():
    m = _manifest(GOOD)
    r = M.reconcile(manifest=m, paths=[DECOYS / "outbound_probe.py"])
    assert "OUTBOUND" in _codes(r)


# --- the surfaces, both directions ---------------------------------------


def test_a_door_on_disk_that_nobody_declared_fails():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "kiosk").mkdir()
        (Path(d) / "web").mkdir()
        r = M.reconcile(manifest=_manifest(dict(GOOD, surfaces=["web"])),
                        paths=[ROOT / "presentation" / "ir.py"],
                        surfaces_at=Path(d))
        assert "SURFACE_UNDECLARED" in _codes(r)
        assert any("kiosk" in f.detail for f in r.findings)


def test_a_declared_door_with_no_directory_fails():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "web").mkdir()
        r = M.reconcile(manifest=_manifest(dict(GOOD, surfaces=["web", "kiosk"])),
                        paths=[ROOT / "presentation" / "ir.py"],
                        surfaces_at=Path(d))
        assert "SURFACE_ABSENT" in _codes(r)


# --- permissions, by allowlist -------------------------------------------


def test_a_cloud_permission_is_refused_by_name():
    """Refusal 1. The declaration half only — see the finding's own wording."""
    for perm in ("cloud_inference", "remote_model", "hosted_transcription"):
        r = M.reconcile(manifest=_manifest(dict(GOOD, permissions=[perm])),
                        paths=[ROOT / "presentation" / "ir.py"])
        assert "CLOUD_PERMISSION" in _codes(r), perm


def test_a_permission_nobody_recognises_is_a_finding_not_a_shrug():
    """An allowlist, because the failure direction of a denylist is that
    anything nobody thought of is permitted."""
    r = M.reconcile(manifest=_manifest(dict(GOOD, permissions=["telemetry"])),
                    paths=[ROOT / "presentation" / "ir.py"])
    assert "UNKNOWN_PERMISSION" in _codes(r)


def test_a_non_local_inference_provider_is_refused():
    for provider in ("auto", "openai", ""):
        r = M.reconcile(
            manifest=_manifest(dict(GOOD, inference={"provider": provider,
                                                     "cloud_fallback": False})),
            paths=[ROOT / "presentation" / "ir.py"])
        assert "NON_LOCAL_INFERENCE" in _codes(r), provider


def test_a_fallback_that_is_not_declared_false_is_refused():
    for value in (True, "no", None):
        r = M.reconcile(
            manifest=_manifest(dict(GOOD, inference={"provider": "local",
                                                     "cloud_fallback": value})),
            paths=[ROOT / "presentation" / "ir.py"])
        assert "CLOUD_FALLBACK" in _codes(r), value


# --- the shape of the declaration itself ---------------------------------


def test_a_typod_key_is_a_finding_and_not_a_quiet_none():
    """`"listners": [...]` declares nothing, and `sockets.declared_from` would
    read the manifest as *declares no listeners* — true today and silently
    false the moment a surface listens."""
    data = dict(GOOD)
    data["listners"] = data.pop("listeners")
    r = M.reconcile(manifest=_manifest(data), paths=[ROOT / "presentation" / "ir.py"])
    assert _codes(r) >= {"UNKNOWN_KEY", "MISSING_KEY"}


def test_a_missing_manifest_is_unknown_and_never_a_pass():
    r = M.reconcile(manifest=Path("/nonexistent/manifest.json"))
    assert r.vacuous and not r.ok
    assert _codes(r) == {"MANIFEST_ABSENT"}


def test_a_manifest_that_cannot_be_parsed_declares_nothing():
    p = Path(tempfile.mkdtemp()) / "manifest.json"
    p.write_text("{oops", encoding="utf-8")
    r = M.reconcile(manifest=p)
    assert r.vacuous and _codes(r) == {"MANIFEST_UNREADABLE"}


def test_a_scan_of_nothing_is_not_a_scan_that_passed():
    """The vacuous case, `conform.py`'s convention: a check with nothing to
    check has not checked anything."""
    r = M.reconcile(manifest=_manifest(GOOD), paths=[])
    assert r.vacuous and not r.ok
    assert "NOTHING_SCANNED" in _codes(r)


# --- coverage: the lint may not skip by construction ---------------------


def test_every_python_file_is_either_scanned_or_excused_with_a_reason():
    """`safe-app-store`'s lint errors on a missing manifest only when the entry
    carries a local path — a middle that cannot fire for a whole class of
    entries. The defence is that the scanned set is derived from the tree and
    the complement is enumerable."""
    everything = set(M._all_python())
    assert set(M.sources()) | set(M.excused()) == everything
    assert not set(M.sources()) & set(M.excused())
    for p in M.excused():
        assert M._excused(p.relative_to(M.ROOT)), p


def test_the_new_packages_are_scanned_without_anyone_adding_them_to_a_list():
    scanned = {p.relative_to(M.ROOT).as_posix() for p in M.sources()}
    assert "presentation/ir.py" in scanned
    assert "surfaces/web/render.py" in scanned
    assert "tools/manifest.py" in scanned


def test_a_package_nobody_has_heard_of_is_not_excused():
    for invented in ("kiosk/app.py", "surfaces/kiosk/server.py", "bridge/__main__.py"):
        assert M._excused(Path(invented)) is None, invented


def test_the_two_excused_paths_are_exactly_these_two_and_each_says_why():
    assert set(M.EXCUSED) == {"tests/fixtures/decoys", "docs"}
    for path, why in M.EXCUSED.items():
        assert len(why) > 40, path


def test_the_sqlite_false_positive_that_the_docs_exclusion_rests_on():
    """**Pinned, not hidden.** `tools/sockets.py` reads
    `sqlite3.connect(":memory:")` as an outbound network connection. That is
    why `docs/` is excused rather than scanned, and if the checker is ever
    taught the difference this test fails and says to revisit the exclusion."""
    demo = ROOT / "docs" / "survey" / "trigger_mutation_demo.py"
    found = sockets.scan([demo])
    assert any(e.kind is sockets.Kind.OUTBOUND for e in found), (
        "sockets.py no longer reads sqlite3.connect() as outbound — the `docs` "
        "exclusion in tools/manifest.py was justified by this and can now shrink"
    )
    assert "sqlite" in M.EXCUSED["docs"]


# --- the obligation is in CI, not only in this file ----------------------


def test_the_workflow_runs_the_reconciliation_and_the_render_check():
    """*"In this repository's own CI"* is the obligation. A guard that runs only
    when somebody remembers is the ledger §7.2 distinguishes from a gate."""
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "tools/manifest.py" in workflow
    assert "presentation/render.py --check" in workflow


def test_the_module_is_not_broken_shut():
    assert M.reconcile(manifest=_manifest(GOOD),
                       paths=[ROOT / "presentation" / "ir.py"]).findings == ()


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
