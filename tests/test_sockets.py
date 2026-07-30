"""The socket checker, pointed at code that really does open sockets.

Rule 19, and the whole reason this ships before the manifest: a checker that has
only ever been run against a tree with no listeners is indistinguishable from one
that cannot see a listener at all.

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

import sockets  # noqa: E402
from sockets import (  # noqa: E402
    ALL_INTERFACES, Declared, Kind, Verdict, check, declared_from, reconcile,
    scan, scan_source,
)

DECOYS = Path(__file__).resolve().parent / "fixtures" / "decoys"


def decoy(name):
    return DECOYS / f"{name}.py"


def endpoints(name):
    return scan([decoy(name)])


def listeners(name):
    return [e for e in endpoints(name) if e.kind is Kind.LISTEN]


def manifest(entries):
    d = tempfile.mkdtemp()
    p = Path(d) / "manifest.json"
    p.write_text(json.dumps({"listeners": entries}), encoding="utf-8")
    return p


# --- the checker sees what it is supposed to see --------------------------


def test_it_finds_an_all_interface_bind():
    """§4.3's worked failure: a 'portless' app with 0.0.0.0:8560."""
    got = listeners("all_interfaces")
    assert any(e.host == "0.0.0.0" and e.port == "8560" for e in got)
    assert all(e.all_interfaces for e in got)


def test_it_finds_a_server_constructor_not_just_a_bind_call():
    """`HTTPServer(("", 8561), …)` never calls `.bind`, and `""` is
    all-interfaces spelled as a blank.

    **This failed on the checker's first run and the bug is worth recording.**
    The literal extractor read `_const(x) or _UNRESOLVED` — the obvious spelling
    — and an empty string is falsy, so the widest possible bind was silently
    reclassified as *could not resolve*. A checker written without a decoy would
    have shipped reporting the willow-grove case as unknown rather than as
    all-interfaces, and looked like it worked.
    """
    got = listeners("all_interfaces")
    blank = [e for e in got if e.port == "8561"]
    assert blank and blank[0].host == "" and blank[0].all_interfaces
    assert "" in ALL_INTERFACES


def test_it_finds_the_outbound_probe():
    """`grove/mcp_local.py:317`'s shape — a UDP connect to 8.8.8.8 for local-IP
    discovery, outside the component the declaration was scoped to."""
    out = [e for e in endpoints("outbound_probe") if e.kind is Kind.OUTBOUND]
    assert out and out[0].host == "8.8.8.8" and out[0].port == "80"


def test_a_backlog_argument_is_not_mistaken_for_an_address():
    """`sock.listen(5)` is a backlog. Counting it as a bind would report a
    listener at `5:?` and bury the real one."""
    for e in listeners("all_interfaces"):
        assert e.port in ("8560", "8561"), f"a backlog was read as an address: {e}"


def test_it_parses_rather_than_greps():
    """`clean.py` says 'bind 0.0.0.0', 'socket' and 'listen' in prose. A
    text-matching checker fails it; this one must not."""
    assert endpoints("clean") == ()


def test_an_unparseable_file_cannot_be_shown_to_be_clean():
    got = scan_source("def broken(:\n", "broken.py")
    assert got and "unparseable" in got[0].how


# --- the sharp comparisons ------------------------------------------------


def test_declaring_the_port_is_not_enough_the_host_must_match():
    """**The willow-grove case exactly.** A manifest declaring 8560 reads true to
    a checker comparing ports and false to anyone on the LAN segment."""
    m = manifest([{"host": "127.0.0.1", "port": "8560", "surface": "console"}])
    r = check([decoy("all_interfaces")], m)
    codes = {f.code for f in r.findings}
    assert "HOST_WIDER_THAN_DECLARED" in codes
    assert not r.ok


def test_a_loopback_bind_matching_its_declaration_is_clean():
    m = manifest([{"host": "127.0.0.1", "port": "8560", "surface": "console"}])
    r = check([decoy("loopback_only")], m)
    assert r.ok and r.verdict is Verdict.CLEAN and not r.findings


def test_a_bind_it_cannot_resolve_is_not_a_pass():
    """Rule 13 at the one place where guessing means an open port nobody wrote
    down. `bind((HOST, PORT))` from the environment is not declared-or-not; it
    is unknown, and unknown is a finding."""
    m = manifest([{"host": "0.0.0.0", "port": "8560", "surface": "web"}])
    r = check([decoy("unresolved_bind")], m)
    assert {f.code for f in r.findings} >= {"UNRESOLVED"}
    assert not r.ok


def test_a_stale_declaration_is_a_finding_too():
    """A manifest row nothing binds reads as a real listener to anyone auditing
    the manifest, and hides that the surface was removed."""
    m = manifest([{"host": "127.0.0.1", "port": "8560", "surface": "console"},
                  {"host": "127.0.0.1", "port": "9999", "surface": "gone"}])
    r = check([decoy("loopback_only")], m)
    assert [f.code for f in r.findings] == ["DECLARED_ABSENT"]
    assert "9999" in r.findings[0].detail


def test_an_undeclared_listener_is_named_and_not_summarised():
    m = manifest([])
    r = check([decoy("loopback_only")], m)
    assert [f.code for f in r.findings] == ["UNDECLARED"]
    assert "8560" in r.findings[0].detail and "loopback_only" in r.findings[0].detail


def test_outbound_is_a_finding_even_when_the_manifest_is_complete():
    """§6's inner ring forbids outbound. There is no manifest field that makes
    an 8.8.8.8 probe acceptable in the core."""
    m = manifest([])
    r = check([decoy("outbound_probe")], m)
    assert {f.code for f in r.findings} == {"OUTBOUND"}


# --- the vacuous case, reported as vacuous --------------------------------


def test_no_manifest_and_no_listeners_is_vacuous_and_not_clean():
    """**The property this whole file exists to protect.** Today's tree has no
    manifest and no listeners, so the scan has nothing to check — and a check
    with nothing to check must not read as a check that passed."""
    r = check([decoy("clean")], Path("/nonexistent/manifest.json"))
    assert r.verdict is Verdict.VACUOUS
    assert not r.ok, "a vacuous scan reported as clean"


def test_no_manifest_but_a_listener_fails_rather_than_shrugging():
    """The moment item 4 lands a surface, this stops being vacuous on its own —
    nobody has to remember to turn the check on."""
    r = check([decoy("all_interfaces")], Path("/nonexistent/manifest.json"))
    assert {f.code for f in r.findings} == {"NO_MANIFEST"}
    assert not r.ok


def test_an_empty_manifest_and_no_manifest_are_different_facts():
    """*Nobody has declared anything* is the state before item 4. *The manifest
    declares no listeners* is a claim that can be wrong. Collapsing them would
    let the second inherit the first's excuse."""
    assert declared_from(Path("/nonexistent/manifest.json")) is None
    assert declared_from(manifest([])) == ()
    assert reconcile([], None).verdict is Verdict.VACUOUS
    assert reconcile([], ()).verdict is Verdict.CLEAN


# --- the checker does not do the thing it checks for ----------------------


def test_it_parses_and_never_imports_the_code_it_inspects():
    """A checker that imported a module to inspect it would execute the code
    under inspection — and for a network module, that means opening the socket
    you were trying to detect."""
    src = (ROOT / "tools" / "sockets.py").read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    for banned in ("import_module", "__import__", "exec(", "eval(", "runpy"):
        assert banned not in body, f"tools/sockets.py executes what it inspects: {banned}"
    for name in ("all_interfaces", "outbound_probe", "unresolved_bind"):
        assert f"fixtures.decoys.{name}" not in sys.modules
        assert name not in sys.modules


def test_the_checker_is_clean_under_its_own_scan():
    """It names every socket API in the file. If it opened one, it would have
    to report itself."""
    r = check([ROOT / "tools" / "sockets.py"], manifest([]))
    assert r.findings == (), f"the checker opens something: {r.findings}"


def test_the_repository_is_clean_today():
    r = check([ROOT / "records", ROOT / "tools", ROOT / "voice.py"], manifest([]))
    assert r.ok, f"something in the tree opens a socket: {[str(f) for f in r.findings]}"


def test_the_module_is_not_broken_shut():
    m = manifest([{"host": "127.0.0.1", "port": "8560", "surface": "console"}])
    assert check([decoy("loopback_only")], m).ok
    assert not check([decoy("all_interfaces")], m).ok


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
