"""The tripwire, pointed at code that really does reach a model.

`records/inference.py` cannot see a module that never touches it, so this is
the half that watches for one being written. There is no inference path in this
repository yet — which is exactly the condition under which a checker ships
broken and nobody finds out, so every check here runs against
`tests/fixtures/decoys/inference_*.py`.

**The decoys are parsed and never imported.** Two of them import
`core.inference_router`, which does not exist here; one posts to Groq. A
checker that imported them to inspect them would make the call it was written
to find.

**Two of them are decoys against the wrong implementation.**
`inference_in_prose.py` names every provider and endpoint in prose, so a grep
fails it and this must not. `inference_launders.py` imports the guard and calls
it — so a checker asking "does this module import the guard?" clears a file
whose two dangerous calls never go near it.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_providers.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import providers  # noqa: E402
from conform import State, check_local_inference  # noqa: E402
from providers import (  # noqa: E402
    GUARD_ENTRIES, Kind, Verdict, check, counted, scan, scan_source,
)

DECOYS = ROOT / "tests" / "fixtures" / "decoys"
REAL = [ROOT / "records", ROOT / "tools", ROOT / "craft", ROOT / "voice.py",
        ROOT / "personas.py"]


def decoy(name: str) -> Path:
    return DECOYS / f"{name}.py"


def _findings(name: str):
    return check([decoy(name)], skip=()).findings


# --- an unguarded path is found -------------------------------------------


def test_the_plainest_unguarded_path_is_found():
    got = _findings("inference_direct")
    assert len(got) == 2, [str(f) for f in got]
    assert all(f.kind is Kind.ROUTER_CALL for f in got)
    assert all("respond" in f.detail for f in got)


def test_a_provider_reached_without_the_router_is_found():
    """The hole a router-shaped checker leaves: `urllib` and a bearer token, a
    `curl` in a subprocess, and a request straight to the local runner — which
    is on the right machine and still returns no provider label to assert on."""
    got = _findings("inference_endpoint")
    details = " ".join(f.detail for f in got)
    assert len(got) == 3, [str(f) for f in got]
    assert "api.groq.com" in details
    assert "generativelanguage.googleapis.com" in details
    assert ":11434" in details or "/api/generate" in details


def test_importing_the_guard_is_not_the_same_as_going_through_it():
    """`inference_launders.py` imports `records.inference`, calls it on the
    concert blurb, and calls the router directly beside it — including a
    `except: pass` retry against the cloud chain, which is refusal 1's last
    sentence spelled out."""
    got = _findings("inference_launders")
    lines = sorted(f.line for f in got)
    assert len(got) == 2, [str(f) for f in got]
    assert all("respond" in f.detail or "chat" in f.detail for f in got)
    guarded = [r for r in scan([decoy("inference_launders")], skip=())
               if r.kind is Kind.ROUTER_CALL and r.guarded]
    assert guarded, "the legitimate guarded call was flagged too"
    assert min(lines) > min(r.line for r in guarded), (
        "the alibi call should be the earliest; the findings come after it")


# --- and a guarded one is not ---------------------------------------------


def test_the_guarded_control_passes():
    """A checker that flagged this would be a rule against importing a router,
    not a rule about refusal 1 — and the first person who needed a model would
    delete it."""
    r = check([decoy("inference_guarded")], skip=())
    assert r.verdict is Verdict.CLEAN, [str(f) for f in r.findings]
    assert any(x.kind is Kind.ROUTER_CALL and x.guarded for x in r.reaches)


def test_it_parses_rather_than_grepping():
    """`inference_in_prose.py` names the router, `api.groq.com` and the local
    endpoint in a docstring and in two constants. A grep fails it."""
    assert _findings("inference_in_prose") == ()
    assert check([decoy("inference_in_prose")], skip=()).verdict is Verdict.VACUOUS


def test_the_decoys_are_parsed_and_never_imported():
    """Two of them import a module that does not exist here and one posts to
    Groq. Importing them to inspect them would make the call."""
    scan([DECOYS], skip=())
    assert "inference_direct" not in sys.modules
    assert "core.inference_router" not in sys.modules


def test_all_the_decoys_together():
    got = check([DECOYS], skip=()).findings
    modules = {f.module.split("/")[-1] for f in got}
    assert {"inference_direct.py", "inference_endpoint.py",
            "inference_launders.py"} <= modules
    assert "inference_guarded.py" not in modules
    assert "inference_in_prose.py" not in modules


# --- what it cannot see, said by name -------------------------------------


def test_a_non_literal_endpoint_is_invisible_and_that_is_recorded():
    """`urlopen(cfg.url)` carries no string this checker can read, and this
    does no type inference. Asserted so the gap reads as a known limit rather
    than as coverage — `purity._on_a_path`'s posture."""
    src = ("import urllib.request\n"
           "def ask(cfg, body):\n"
           "    return urllib.request.urlopen(cfg.url, body)\n")
    assert scan_source(src, "hidden.py") == ()


def test_an_import_alone_is_not_a_finding():
    """An import is how you find the call; the call is the finding. The
    guarded control imports the router and passes."""
    src = "from core.inference_router import respond\n"
    got = scan_source(src, "imports_only.py")
    assert got and all(r.kind is Kind.ROUTER_IMPORT for r in got)
    assert not any(r.is_finding for r in got)


def test_an_unparseable_module_is_not_a_pass():
    got = scan_source("def broken(:\n", "broken.py")
    assert len(got) == 1 and got[0].is_finding


# --- the checker against the real tree ------------------------------------


def test_the_repository_reaches_no_model_yet_and_that_is_not_a_pass():
    """Rule 18, said out loud. Nothing here infers, so this scan has nothing to
    check — `VACUOUS`, not `CLEAN`. The value of the checker today is that the
    first inference path is caught on arrival."""
    r = check(REAL)
    assert r.verdict is Verdict.VACUOUS, [str(f) for f in r.findings]
    assert not r.ok, "a vacuous scan reported as a pass"
    assert r.scanned == counted(REAL) and r.scanned > 0


def test_the_guard_is_the_only_exemption_and_is_named():
    """`records/inference.py` is skipped by path, not by heuristic. A checker
    that exempted anything matching `*inference*` would exempt every file
    somebody names carefully."""
    assert providers.GUARD_MODULE == "records/inference.py"
    assert (ROOT / providers.GUARD_MODULE).exists()


def test_the_guard_entries_are_the_ways_in_that_exist():
    """Pair: `providers.GUARD_ENTRIES` and `records/inference.py`'s exported
    constructors. The middle is this test — a renamed entry point would
    otherwise leave the tripwire recognising nothing as guarded, and a
    tripwire that clears everything is silent in exactly the wrong direction."""
    from records import inference
    for name in GUARD_ENTRIES:
        assert callable(getattr(inference, name, None)), name
    exported = {n for n in dir(inference)
                if not n.startswith("_") and callable(getattr(inference, n))
                and getattr(getattr(inference, n), "__module__", "") == inference.__name__
                and not isinstance(getattr(inference, n), type)}
    assert exported - GUARD_ENTRIES <= {"covered", "is_local_address"}, exported


# --- wired into the build gate --------------------------------------------


def test_the_conformance_check_reports_unknown_while_nothing_infers():
    got = check_local_inference()
    assert got.state is State.UNKNOWN, got.evidence
    assert "caught on arrival" in got.evidence


def test_the_conformance_check_fails_when_pointed_at_a_decoy():
    """Rule 19 for the wiring itself: the check has to be able to fail, and it
    has to be pointable at something that makes it."""
    got = check_local_inference(decoy("inference_direct"))
    assert got.state is State.FAIL and "respond" in got.evidence


def test_the_conformance_check_passes_a_guarded_path():
    got = check_local_inference(decoy("inference_guarded"))
    assert got.state is State.PASS, got.evidence


def test_the_check_is_in_the_conformance_run():
    import conform
    assert conform.check_local_inference in conform.CHECKS


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
