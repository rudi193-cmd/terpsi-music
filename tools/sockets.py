"""Every listener the source can open, against every listener the manifest admits.

**Built before the manifest, deliberately.** When this was written §18 item 4
had not decided what surfaces exist, so there was nothing to declare yet — and
that was the argument for writing it then rather than later. The manifest landed
2026-07-31 against a checker that already refused; `tools/manifest.py` is now its
caller, and it supplies the target list rather than this file naming paths by
hand. §4.3 records the failure it prevents, at source and verified:

> `safe-app-willow-grove` declares `"surfaces": ["tui"]`, permissions limited to
> `lan_listen`/`lan_send`, and a `CLAUDE.md` rule reading **"No web ports for the
> dashboard. Portless means portless."** `bridge/app.py` opens **two**
> all-interface listeners, and `grove/mcp_local.py:317` opens a UDP socket to
> `8.8.8.8:80` to discover the local IP — outside the bridge, so the
> *"scoped to the dashboard"* defence does not cover it. **The app carries no
> purity test at all.**

Nobody lied. The declaration shipped first and nothing was ever pointed at it,
which is §16's *absent middle* in its most ordinary form. **A checker that exists
before the first manifest means the manifest cannot be born wrong** — whatever
item 4 decides gets written against something that already refuses.

**Three things this gets right that a grep does not.**

*It parses and never imports.* A checker that imported a module to inspect it
would execute the code under inspection, and for a network module that means
opening the socket you were trying to detect. `ast.parse` only.

*A port is not enough — the host must match, and wider is a finding.* Declaring
`8560` and binding `0.0.0.0:8560` is exactly the willow-grove case: the manifest
reads true to a checker comparing ports and false to anyone on the LAN segment.
`0.0.0.0`, `::` and `""` are all-interfaces; loopback is not; declaring the
second and binding the first is `HOST_WIDER_THAN_DECLARED`.

*A bind it cannot resolve is not a pass.* When the host or port comes from a
variable, the answer is `UNRESOLVED` and it counts as a finding — rule 13, at the
one place where guessing means an open port nobody wrote down.

**And the vacuous case is reported as vacuous.** With no manifest and no
listeners this scan has nothing to check, and a check with nothing to check must
not read as a check that passed. `reconcile()` says so, `conform.py` renders it
`UNKNOWN`, and the moment a listener appears with no manifest to declare it the
result is `FAIL` rather than a shrug. `tools/manifest.py` carries the same
posture one level up: a manifest that cannot be read, or a scan that covered no
files, is `UNKNOWN` and never `PASS`.

**One thing this file does not distinguish, recorded rather than left to be
found:** `sqlite3.connect(":memory:")` is read as an outbound connection,
because the call name is all the parse sees. That is why `tools/manifest.py`
excuses `docs/` rather than scanning it, and `tests/test_manifest.py` pins the
misreading so that fixing it here fails there and prompts the exclusion to
shrink.

    python3 tools/sockets.py [path ...]

Stdlib only. No network — which this file is in a poor position to claim, so
`tests/test_sockets.py` asserts it by scanning this module with itself.
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"

#: Hosts that accept from anywhere. `""` is the sharp one: `bind(("", 8560))` is
#: all-interfaces and reads as a blank rather than as a wildcard.
ALL_INTERFACES = frozenset({"0.0.0.0", "::", "", "*"})
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})

#: Constructors that bind by taking an address tuple as their first argument.
_SERVER_CTORS = frozenset({
    "TCPServer", "UDPServer", "ThreadingTCPServer", "ForkingTCPServer",
    "HTTPServer", "ThreadingHTTPServer",
})

#: Callables that bind via host=/port= keywords (or positionally, after the app).
_RUNNERS = frozenset({"run_app", "run", "serve", "start_server", "create_server"})

_UNRESOLVED = "?"


class Kind(Enum):
    LISTEN = "listen"      # something will accept connections here
    OUTBOUND = "outbound"  # something will reach out from here


@dataclass(frozen=True)
class Endpoint:
    kind: Kind
    module: str
    line: int
    how: str
    host: str = _UNRESOLVED
    port: str = _UNRESOLVED

    @property
    def resolved(self) -> bool:
        return self.host != _UNRESOLVED and self.port != _UNRESOLVED

    @property
    def all_interfaces(self) -> bool:
        return self.host in ALL_INTERFACES

    def __str__(self) -> str:
        return f"{self.module}:{self.line} {self.how} {self.host}:{self.port}"


def _const(node) -> Optional[str]:
    """A literal's value as a string, or None when it is not a literal."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
        return str(node.value)
    return None


def _or_unresolved(value: Optional[str]) -> str:
    """`None` becomes unresolved; `""` does **not**.

    Written explicitly because `_const(x) or _UNRESOLVED` is the obvious spelling
    and it is wrong here in the one case that matters most: `bind(("", 8560))` is
    **all-interfaces spelled as a blank**, and an empty string is falsy, so the
    `or` idiom silently reclassified the widest possible bind as *could not
    resolve*. The decoy caught it on its first run, which is what the decoy is
    for.
    """
    return _UNRESOLVED if value is None else value


def _from_tuple(node) -> Tuple[str, str]:
    """`("0.0.0.0", 8560)` → `("0.0.0.0", "8560")`, unresolved where it is not literal."""
    if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) >= 2:
        return (_or_unresolved(_const(node.elts[0])),
                _or_unresolved(_const(node.elts[1])))
    return (_UNRESOLVED, _UNRESOLVED)


def _from_kwargs(call: ast.Call) -> Tuple[str, str]:
    host = port = _UNRESOLVED
    for kw in call.keywords:
        if kw.arg in ("host", "address", "bind", "interface"):
            host = _or_unresolved(_const(kw.value))
        elif kw.arg == "port":
            port = _or_unresolved(_const(kw.value))
    return host, port


def _name_of(func) -> str:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def scan_source(src: str, module: str) -> Tuple[Endpoint, ...]:
    """Endpoints reachable from this source. Parses; never imports, never runs."""
    out: List[Endpoint] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        # A file that will not parse cannot be shown to be clean. Rule 13.
        return (Endpoint(Kind.LISTEN, module, exc.lineno or 0,
                         "unparseable — cannot be shown to open nothing"),)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _name_of(node.func)

        if name in ("bind", "listen") and node.args:
            host, port = _from_tuple(node.args[0])
            if name == "listen" and host == _UNRESOLVED:
                continue  # `sock.listen(5)` is a backlog; the bind above carries the address
            out.append(Endpoint(Kind.LISTEN, module, node.lineno, f".{name}()", host, port))

        elif name in _SERVER_CTORS and node.args:
            host, port = _from_tuple(node.args[0])
            out.append(Endpoint(Kind.LISTEN, module, node.lineno, f"{name}()", host, port))

        elif name in _RUNNERS and node.keywords:
            host, port = _from_kwargs(node)
            if port != _UNRESOLVED or host != _UNRESOLVED:
                out.append(Endpoint(Kind.LISTEN, module, node.lineno,
                                    f"{name}(host=, port=)", host, port))

        elif name in ("connect", "connect_ex", "sendto", "create_connection") and node.args:
            idx = 1 if name == "sendto" and len(node.args) > 1 else 0
            host, port = _from_tuple(node.args[idx])
            out.append(Endpoint(Kind.OUTBOUND, module, node.lineno, f".{name}()", host, port))

    return tuple(out)


def scan(paths: Sequence[Path]) -> Tuple[Endpoint, ...]:
    out: List[Endpoint] = []
    for base in paths:
        files = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for py in files:
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            out.extend(scan_source(py.read_text(encoding="utf-8"), str(rel)))
    return tuple(out)


# --- the manifest side -----------------------------------------------------


@dataclass(frozen=True)
class Declared:
    host: str
    port: str
    surface: str = ""

    def covers(self, e: Endpoint) -> bool:
        return self.port == e.port and self.host == e.host


def declared_from(manifest: Optional[Path] = None) -> Optional[Tuple[Declared, ...]]:
    """What the manifest admits, or `None` when there is no manifest.

    `None` and `()` are different facts and are kept apart: *nobody has declared
    anything* is the state before item 4, and *the manifest declares no
    listeners* is a claim that can be wrong.

    **A manifest with no `listeners` key has declared nothing**, and that is the
    first fact rather than the second. It was read as the second — the spelling
    was `data.get("listeners", [])` — so a manifest whose key was misspelled,
    nested one level down, or simply not written yet reconciled `CLEAN` against
    a tree with no listeners, where an absent manifest reconciles `VACUOUS`. A
    typo bought a passing check that an absent file could not. `"listeners": []`
    still reads as `()`, because that is somebody's claim and can be wrong.
    """
    p = manifest if manifest is not None else MANIFEST
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if "listeners" not in data:
        return None
    return tuple(Declared(str(d.get("host", _UNRESOLVED)),
                          str(d.get("port", _UNRESOLVED)),
                          str(d.get("surface", "")))
                 for d in data.get("listeners", []))


class Verdict(Enum):
    CLEAN = "clean"
    VACUOUS = "vacuous"     # nothing declared and nothing found — not a pass
    FINDINGS = "findings"


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str


@dataclass(frozen=True)
class Reconciliation:
    verdict: Verdict
    findings: Tuple[Finding, ...]
    listeners: Tuple[Endpoint, ...]
    outbound: Tuple[Endpoint, ...]

    @property
    def ok(self) -> bool:
        """`CLEAN` only. A vacuous scan is not a passing one."""
        return self.verdict is Verdict.CLEAN


def reconcile(found: Sequence[Endpoint],
              declared: Optional[Sequence[Declared]]) -> Reconciliation:
    """Compare what the source opens against what the manifest admits."""
    listeners = tuple(e for e in found if e.kind is Kind.LISTEN)
    outbound = tuple(e for e in found if e.kind is Kind.OUTBOUND)
    findings: List[Finding] = []

    if declared is None:
        if not listeners and not outbound:
            return Reconciliation(
                Verdict.VACUOUS, (), (), ())
        for e in listeners:
            findings.append(Finding(
                "NO_MANIFEST",
                f"{e} — a listener exists and no manifest declares it"))
    else:
        for e in listeners:
            if not e.resolved:
                findings.append(Finding(
                    "UNRESOLVED",
                    f"{e} — host or port is not a literal, so this bind cannot be "
                    "shown to be declared"))
                continue
            if any(d.covers(e) for d in declared):
                continue
            wider = [d for d in declared
                     if d.port == e.port and d.host in LOOPBACK and e.all_interfaces]
            if wider:
                findings.append(Finding(
                    "HOST_WIDER_THAN_DECLARED",
                    f"{e} — the manifest declares {wider[0].host}:{wider[0].port}; "
                    "this binds every interface"))
            else:
                findings.append(Finding("UNDECLARED", f"{e} — not in the manifest"))

        for d in declared:
            if not any(d.covers(e) for e in listeners):
                findings.append(Finding(
                    "DECLARED_ABSENT",
                    f"{d.host}:{d.port} ({d.surface or 'no surface named'}) is declared "
                    "and nothing binds it — a stale declaration reads as a real one"))

    for e in outbound:
        findings.append(Finding(
            "OUTBOUND",
            f"{e} — §6's inner ring forbids outbound; this is the 8.8.8.8 probe's shape"))

    verdict = Verdict.FINDINGS if findings else Verdict.CLEAN
    return Reconciliation(verdict, tuple(findings), listeners, outbound)


def check(paths: Sequence[Path], manifest: Optional[Path] = None) -> Reconciliation:
    return reconcile(scan(paths), declared_from(manifest))


def main(argv: Sequence[str]) -> int:
    targets = [Path(a) for a in argv] or [ROOT / "records", ROOT / "tools",
                                          ROOT / "voice.py", ROOT / "personas.py"]
    r = check(targets)
    for e in r.listeners:
        print(f"  listen    {e}")
    for e in r.outbound:
        print(f"  outbound  {e}")
    for f in r.findings:
        print(f"  {f.code:<24} {f.detail}")
    if r.verdict is Verdict.VACUOUS:
        print("\n  VACUOUS — no manifest and no endpoints. Nothing was checked, "
              "which is not the same as nothing being wrong.")
        return 0
    print(f"\n  {r.verdict.value}: {len(r.listeners)} listener(s), "
          f"{len(r.outbound)} outbound, {len(r.findings)} finding(s)")
    return 1 if r.findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
