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
    # G-C, 2026-07-31. Present in the fixture because it is a required key: a
    # manifest without it declares nothing about writes, and declaring nothing
    # is not the same as declaring none (`sockets.declared_from`'s lesson,
    # applied to the second declaration this manifest carries).
    "write_paths": [{"path": "presentation/render.py", "kind": "filesystem",
                     "why": "the fixture's one declared writer"}],
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
    """The claim, stated as a claim: this is falsifiable and it holds today.

    **The outbound half stopped being empty on 2026-07-31** and the test says so
    rather than being widened to `>= 0`. `store/connecting.py` opens exactly one
    connection, to the local store; every other module in the scanned tree still
    binds nothing and reaches nothing, and both facts are asserted here.
    """
    declared = sockets.declared_from(M.MANIFEST)
    assert declared == (), declared
    found = sockets.scan(list(M.sources()))
    listeners = [e for e in found if e.kind is sockets.Kind.LISTEN]
    outbound = [e for e in found if e.kind is sockets.Kind.OUTBOUND]
    assert [str(e) for e in listeners] == [], "something in the scanned tree listens"
    # By module, not by call site: `reachable()` goes through `connect()` too,
    # and the claim is about which files can reach out, not how many lines do.
    assert {e.module for e in outbound} == {"store/connecting.py"}, (
        f"outbound is not confined to the store: {[str(e) for e in outbound]}")
    assert outbound, "nothing reaches out at all, so this assertion is vacuous"


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


def test_an_outbound_connection_no_module_declares_is_a_finding():
    """§6's inner ring forbids outbound. `GOOD` declares none, so the probe is a
    finding — the behaviour this check had before the store existed, preserved
    rather than loosened when `outbound` gained a meaning."""
    m = _manifest(GOOD)
    r = M.reconcile(manifest=m, paths=[DECOYS / "outbound_probe.py"])
    assert "OUTBOUND" in _codes(r)


def test_an_outbound_connection_is_admitted_only_where_the_manifest_names_it():
    """The store's connection, declared **by module** because a DSN is resolved
    at run time and there is no host:port in the source to compare against.

    Both directions, for `_check_surfaces`'s reason: a declaration covering a
    module that opens nothing is a stale declaration, and the next module added
    under that path would inherit a permission nobody re-examined.
    """
    admitted = _manifest(dict(GOOD, outbound=[
        {"module": "tests/fixtures/decoys/outbound_probe.py", "kind": "probe",
         "why": "the decoy, admitted on purpose for this test"}]))
    r = M.reconcile(manifest=admitted, paths=[DECOYS / "outbound_probe.py"])
    assert "OUTBOUND" not in _codes(r), [f.detail for f in r.findings]

    stale = _manifest(dict(GOOD, outbound=[
        {"module": "store/connecting.py", "kind": "database", "why": "x"}]))
    r = M.reconcile(manifest=stale, paths=[ROOT / "presentation" / "ir.py"])
    assert "OUTBOUND_DECLARED_ABSENT" in _codes(r)


def test_the_stores_connection_is_the_one_outbound_the_real_manifest_admits():
    """The shipped claim. Red the day a second module opens a connection, and
    red the day `store/connecting.py` stops opening one — a declaration with
    nothing behind it is §4.3's failure, which is why both halves are here."""
    declared = sockets.declared_outbound_from(M.MANIFEST)
    assert declared is not None and len(declared) == 1
    assert declared[0].module == "store/connecting.py"
    assert declared[0].kind == "database" and len(declared[0].why) > 40
    assert M.reconcile().ok


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


# --- G-C: the write-path declaration and its reconciliation --------------
#
# `docs/PLAN-STORE.md` gate G-C, landing in the same commit as `store/`. The
# acceptance list's last item is the failure direction: *"a write path appears
# that the manifest does not declare — the build fails without anyone
# remembering to check."*


def test_a_write_path_nothing_declares_fails_the_build():
    """**The decoy, caught by name.** `store_write_undeclared.py` hands an
    `INSERT` to a cursor and sits under none of the declared paths."""
    m = _manifest(GOOD)
    r = M.reconcile(manifest=m,
                    paths=[ROOT / "presentation" / "render.py",
                           DECOYS / "store_write_undeclared.py"])
    assert "WRITE_UNDECLARED" in _codes(r)
    assert any("store_write_undeclared.py" in f.detail
               for f in r.findings if f.code == "WRITE_UNDECLARED")
    assert not r.ok


def test_a_module_that_only_talks_about_writing_is_not_a_finding():
    """The counterpart decoy, against the wrong implementation. A grep for
    `INSERT INTO` fails `store_write_in_prose.py`; this must not — a rule
    written in prose is not the rule being broken, and a check that cries wolf
    is a check somebody switches off."""
    m = _manifest(GOOD)
    r = M.reconcile(manifest=m,
                    paths=[ROOT / "presentation" / "render.py",
                           DECOYS / "store_write_in_prose.py"])
    assert "WRITE_UNDECLARED" not in _codes(r), [f.detail for f in r.findings]


def test_a_declared_write_path_that_writes_nothing_is_a_finding():
    """A stale declaration reads as a real one, and the next module added under
    it inherits a permission nobody re-examined. Same rule as the surfaces."""
    m = _manifest(dict(GOOD, write_paths=[
        {"path": "presentation/render.py", "kind": "filesystem", "why": "real"},
        {"path": "kiosk/", "kind": "filesystem", "why": "nothing is here"}]))
    r = M.reconcile(manifest=m, paths=[ROOT / "presentation" / "render.py"])
    assert "WRITE_PATH_ABSENT" in _codes(r)


def test_a_write_path_declared_without_a_reason_is_a_finding():
    """A declaration nobody can review is the kind that outlives its reason."""
    m = _manifest(dict(GOOD, write_paths=[
        {"path": "presentation/render.py", "kind": "filesystem", "why": "  "}]))
    r = M.reconcile(manifest=m, paths=[ROOT / "presentation" / "render.py"])
    assert "WRITE_PATH_UNEXPLAINED" in _codes(r)


def test_a_manifest_with_no_write_paths_key_declares_nothing_and_fails():
    """`REQUIRED_KEYS` carries it, so an absent key is `MISSING_KEY` rather than
    an empty list — *declaring nothing is not the same as declaring none*."""
    without = {k: v for k, v in GOOD.items() if k != "write_paths"}
    r = M.reconcile(manifest=_manifest(without),
                    paths=[ROOT / "presentation" / "ir.py"])
    assert "MISSING_KEY" in _codes(r)
    assert any("write_paths" in f.detail for f in r.findings)


def test_the_declaration_covers_by_prefix_and_a_sibling_is_not_covered():
    """`storefront/` is not `store/`. A substring match would admit it."""
    assert M._covers("store/", "store/writing.py")
    assert M._covers("store", "store/writing.py")
    assert M._covers("tools/conform.py", "tools/conform.py")
    assert not M._covers("store/", "storefront/writing.py")
    assert not M._covers("tools/conform.py", "tools/conformity.py")


def test_the_real_manifest_declares_every_writer_in_the_real_tree():
    """The shipped claim, over the shipped tree, with the count derived rather
    than quoted (rule 17)."""
    from purity import scan_source

    r = M.reconcile()
    assert r.ok, [f"{f.code}: {f.detail}" for f in r.findings]
    writers = {p.relative_to(M.ROOT).as_posix() for p in M.sources()
               if any(t.is_write for t in
                      scan_source(p.read_text(encoding="utf-8"), p.name))}
    assert writers, "nothing in the tree writes, so this reconciliation is vacuous"
    declared = [d["path"] for d in json.loads(
        M.MANIFEST.read_text(encoding="utf-8"))["write_paths"]]
    for module in sorted(writers):
        assert any(M._covers(d, module) for d in declared), module


def test_records_is_not_a_write_path_and_declares_none():
    """§6's inner ring. The store is the declared exception and `records/` is
    the thing it is an exception to — if `records/` ever wrote, this is where
    that becomes visible rather than in a review."""
    from purity import scan_source

    for p in sorted((ROOT / "records").rglob("*.py")):
        found = [t for t in scan_source(p.read_text(encoding="utf-8"), p.name)
                 if t.is_write]
        assert not found, f"{p.name} writes: {[str(t) for t in found]}"
    declared = [d["path"] for d in json.loads(
        M.MANIFEST.read_text(encoding="utf-8"))["write_paths"]]
    assert not any(d.startswith("records") for d in declared)


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
    assert "tools/drivers.py" in workflow, (
        "the driver tripwire is not run in CI, so the second dependency's "
        "acceptance is enforced by a review checklist")


def test_every_store_test_the_guards_job_holds_back_is_run_by_the_schema_job():
    """**The middle for a routing decision** (rule 12).

    The guards job skips `tests/test_store_*.py` because they exit 2 with
    `UNKNOWN` where there is no cluster, and a job that is red every run is a
    job everybody learns to ignore. That skip is only safe while something else
    runs them, and *"something else runs them"* is the kind of claim that goes
    stale silently — a store module that stopped being run anywhere would look
    exactly like one that passes.

    So: the set held back is derived from the tree, and every member must be
    named in the workflow. A glob in the workflow would have covered a module
    that stopped existing; a hand-written list that nothing checks would miss
    one that started. This is the check that makes either safe.
    """
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    held_back = sorted(p.name for p in (ROOT / "tests").glob("test_store_*.py"))
    assert held_back, "no store tests exist, so this assertion is vacuous"
    assert "tests/test_store_*)" in workflow, (
        "the guards job no longer holds the store tests back, so they run "
        "without a cluster and paint that job red")
    for name in held_back:
        assert f"tests/{name}" in workflow, (
            f"{name} is held back from the guards job and no job runs it")


def test_the_module_is_not_broken_shut():
    """`render.py` is the fixture's one declared writer, so both halves of the
    write-path check have something real to agree about — a control that scanned
    a module writing nothing would be satisfied by a stale declaration."""
    assert M.reconcile(manifest=_manifest(GOOD),
                       paths=[ROOT / "presentation" / "render.py"]).findings == ()


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
