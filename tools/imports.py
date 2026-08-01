"""Every import resolves to the standard library, a *declared* dependency, or a
local module — or it is a finding. This is TM-DEPS-01's enforcement half.

`requirements.txt` declares the dependencies this repository accepts, each with
its reason, and every acceptance was a maintainer's deliberate act (§18 items
15 and 18). Nothing else may enter by an `import`. Until now that posture was
asserted in 57 docstrings and enforced by nobody: `tools/purity.py` catches a
network client only because it is on the *egress* list, and `tools/drivers.py`
catches the database driver only where it is admitted — a fresh `import numpy`,
or `import flask`, passed every gate. This is the gate for that: the set of
third-party roots the tree may import is exactly the set `requirements.txt`
names, derived from the file rather than hard-coded, so the check and the
declaration cannot drift.

**`tools/drivers.py` is the pattern** and this file follows it: parse, never
import; a finding is the `import` itself, not a call, because a module that
imports an undeclared package has taken the dependency whether or not this run
reaches the line that uses it; the vacuous case (nothing scanned) is reported
as vacuous, never as a pass. The two dotted-name helpers are imported from
`providers.py` rather than re-spelled (§16).

**The relationship to `drivers.py`, named rather than left to be noticed.**
`drivers.py` answers *where* the one declared driver may be imported (only
`store/`); this answers *whether* an import is declared at all. A driver import
inside `store/` passes here (it is declared) and passes there (it is admitted);
a driver import outside `store/` fails there; an undeclared package anywhere
fails here. The two gates compose and neither subsumes the other.

**One limitation, stated.** The map from a distribution name to its import
root is not the identity in general — `PyYAML` imports as `yaml`. This repo's
two dependencies are each their own import root, so `_DIST_TO_IMPORT` carries
only them; a future dependency whose import name differs from its package name
needs a line there, and `test_imports.py` asserts every declared package
resolves to a known import root so that gap fails loudly rather than silently
admitting the wrong name.

    python3 tools/imports.py [path ...]

Stdlib only. No network, no writes.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from providers import _dotted, _tail  # noqa: E402 — imported, never re-spelled

#: Distribution name (as `requirements.txt` spells it, extras and version
#: stripped) → the top-level name an `import` actually uses. Identity for both
#: current dependencies; a package whose import name differs needs a line here,
#: and the absence of one is a loud test failure rather than a silent pass.
_DIST_TO_IMPORT: Dict[str, str] = {
    "cryptography": "cryptography",
    "psycopg": "psycopg",
}

#: Dynamic spellings, as everywhere else a name can hide from the import graph.
_DYNAMIC = frozenset({"__import__", "import_module"})

#: Decoys exist to be caught, so the real scan does not walk them; and a file
#: under a dot-directory is VCS or tooling state, never the app.
_SKIP_PREFIXES = ("tests/fixtures/decoys/",)


class Kind(Enum):
    IMPORT = "import"
    DYNAMIC = "dynamic"
    UNRESOLVED = "unresolved"   # a dynamic import whose name is not a literal


class Verdict(Enum):
    CLEAN = "clean"        # every import resolved; nothing undeclared
    VACUOUS = "vacuous"    # nothing scanned — not a pass
    FINDINGS = "findings"


@dataclass(frozen=True)
class Reach:
    kind: Kind
    module: str
    line: int
    root: str
    detail: str
    resolved: bool          # stdlib, declared, or local

    @property
    def is_finding(self) -> bool:
        return not self.resolved

    def __str__(self) -> str:
        return f"{self.module}:{self.line} {self.detail}"


@dataclass(frozen=True)
class Scan:
    verdict: Verdict
    reaches: Tuple[Reach, ...]
    scanned: int

    @property
    def findings(self) -> Tuple[Reach, ...]:
        return tuple(r for r in self.reaches if r.is_finding)

    @property
    def ok(self) -> bool:
        return self.verdict is Verdict.CLEAN


def declared_roots(requirements: Optional[Path] = None) -> FrozenSet[str]:
    """The import roots `requirements.txt` admits, derived from the file.

    Each requirement line is stripped of its version specifier and extras to a
    distribution name, then mapped to the name an `import` uses. A distribution
    with no entry in `_DIST_TO_IMPORT` is returned under its own name *and*
    flagged by `unmapped()`, so the reconciliation is never silently wrong.
    """
    path = requirements if requirements is not None else REQUIREMENTS
    if not path.exists():
        return frozenset()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        dist = line.split("==")[0].split(">=")[0].split("~=")[0].split("[")[0].strip().lower()
        if dist:
            out.add(_DIST_TO_IMPORT.get(dist, dist))
    return frozenset(out)


def unmapped(requirements: Optional[Path] = None) -> Tuple[str, ...]:
    """Declared distributions with no `_DIST_TO_IMPORT` entry — the case where
    the import root is a guess. Empty today; a loud test failure if it grows."""
    path = requirements if requirements is not None else REQUIREMENTS
    if not path.exists():
        return ()
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        dist = line.split("==")[0].split(">=")[0].split("~=")[0].split("[")[0].strip().lower()
        if dist and dist not in _DIST_TO_IMPORT:
            out.append(dist)
    return tuple(out)


def local_roots(where: Optional[Path] = None) -> FrozenSet[str]:
    """Import roots that are this repository's own modules, derived from the
    tree. A module is reachable both as `package.module` and, because `tools/`,
    `store/` and `tests/` are put on `sys.path`, as a bare `module`, so both the
    top-level directory names and every file's own stem are local roots."""
    base = where if where is not None else ROOT
    roots = set()
    for py in base.rglob("*.py"):
        rel = py.relative_to(base)
        if any(part.startswith(".") for part in rel.parts):
            continue
        roots.add(rel.parts[0][:-3] if len(rel.parts) == 1 else rel.parts[0])
        roots.add(py.stem)
    return frozenset(roots)


_STDLIB = frozenset(sys.stdlib_module_names) | {"__future__"}


def _root_of(dotted: str) -> str:
    return dotted.split(".")[0] if dotted else ""


def scan_source(src: str, module: str, allowed: FrozenSet[str]) -> Tuple[Reach, ...]:
    """Every import in one file, each judged against `allowed`. Parses; never
    imports, never runs."""
    out: List[Reach] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return (Reach(Kind.UNRESOLVED, module, exc.lineno or 0, "",
                      "unparseable — cannot be shown to import only what is declared",
                      False),)

    def judge(kind: Kind, root: str, line: int, detail: str) -> None:
        out.append(Reach(kind, module, line, root, detail, root in allowed))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = _root_of(a.name)
                judge(Kind.IMPORT, root, node.lineno, f"imports {a.name}")
        elif isinstance(node, ast.ImportFrom):
            # A relative import (`from . import x`) has level > 0 and is always
            # local by construction; node.module is None or a submodule name.
            if node.level and not node.module:
                continue
            root = "" if node.level else _root_of(node.module or "")
            if node.level:
                continue
            judge(Kind.IMPORT, root, node.lineno, f"imports from {node.module}")
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            if _tail(name) not in _DYNAMIC:
                continue
            target = (node.args[0].value
                      if node.args and isinstance(node.args[0], ast.Constant)
                      and isinstance(node.args[0].value, str) else None)
            if target is None:
                out.append(Reach(Kind.UNRESOLVED, module, node.lineno, "",
                                 f"{_tail(name)}() with a non-literal name — the "
                                 "import graph cannot show what it loads", False))
            else:
                root = _root_of(target)
                judge(Kind.DYNAMIC, root, node.lineno,
                      f"{_tail(name)}({target!r})")
    return tuple(out)


def _files(paths: Sequence[Path]) -> List[Path]:
    out = []
    for base in paths:
        for py in ([base] if base.is_file() else sorted(base.rglob("*.py"))):
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            text = str(rel).replace("\\", "/")
            if any(text.startswith(p) for p in _SKIP_PREFIXES):
                continue
            if any(part.startswith(".") for part in rel.parts):
                continue
            out.append(py)
    return out


def check(paths: Sequence[Path], requirements: Optional[Path] = None,
          where: Optional[Path] = None) -> Scan:
    allowed = _STDLIB | declared_roots(requirements) | local_roots(where)
    files = _files(paths)
    reaches: List[Reach] = []
    for py in files:
        rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
        reaches.extend(scan_source(py.read_text(encoding="utf-8"), str(rel), allowed))
    if not files:
        return Scan(Verdict.VACUOUS, tuple(reaches), 0)
    verdict = (Verdict.FINDINGS if any(r.is_finding for r in reaches)
               else Verdict.CLEAN)
    return Scan(verdict, tuple(reaches), len(files))


def _default_paths() -> Tuple[Path, ...]:
    # Every application package, so a new third-party import cannot slip past the
    # gate by living in a directory the scan forgot: `console/`, `drop/` and
    # `venue/` landed after the first version of this list and were outside it —
    # the enforcement/audit scope mismatch PR #16's security pass named.
    return (ROOT / "records", ROOT / "store", ROOT / "console", ROOT / "drop",
            ROOT / "venue", ROOT / "tools", ROOT / "presentation", ROOT / "surfaces",
            ROOT / "craft", ROOT / "tests", ROOT / "docs" / "survey",
            ROOT / "voice.py", ROOT / "personas.py")


def main(argv: Sequence[str]) -> int:
    paths = [Path(a) for a in argv] or list(_default_paths())
    paths = [p for p in paths if p.exists()]
    r = check(paths)
    if r.verdict is Verdict.VACUOUS:
        print("UNKNOWN: no Python scanned — a scan of nothing is not a pass")
        return 2
    for f in r.findings:
        print(f"FINDING {f}  (root {f.root!r} is not stdlib, declared, or local)")
    if r.verdict is Verdict.FINDINGS:
        print(f"{len(r.findings)} undeclared import(s) across {r.scanned} file(s)")
        return 1
    print(f"clean: {r.scanned} file(s), every import stdlib / declared / local")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
