"""Where the database driver is reachable from, and where it must not be.

`requirements.txt` carries two dependencies. The second is the store's driver,
accepted with the store plan's dispatch, and the acceptance was narrow: **the
store may talk to PostgreSQL and nothing else may.** A module elsewhere in the
tree that imports `psycopg` has opened a second path to the canonical store —
one that no adapter narrates, no role restricts and no write-path declaration
covers. That is rule 11's *read-only to the app* defeated by an import.

**`tools/providers.py` is the pattern**, and this file follows it rather than
inventing a second one: parse, never import; scan a path set derived from the
tree; report the vacuous case as vacuous. Its two dotted-name helpers are
imported from there rather than copied, because two spellings of *"resolve an
`ast.Attribute` chain"* is the pair §16 is about, in miniature.

**Where it deliberately differs, and why the difference is not an oversight.**
In `providers.py` the finding is a *call*, because a provider imported and never
used is a dependency rather than a request. Here the finding is the **import**.
A module that imports the driver can connect on any line written afterwards, and
the whole value of the store's seam is that the set of modules able to open a
connection is small enough to read. So the rule is stricter than `providers.py`'s
on purpose, and stating that here is cheaper than having somebody discover the
asymmetry and "fix" it.

Prose is not an import (`ALLOWED` names the store, and this module's own
docstring says `psycopg` four times without importing it), so the decoys are
`tests/fixtures/decoys/driver_*.py`: one that really imports it outside the
store, one that names it only in a string, and one that reaches it through
`importlib`. A checker written against a clean tree passes on the day it ships
and every day after — `tools/purity.py`'s finding, three checkers in a row.

    python3 tools/drivers.py [path ...]

Stdlib only. No network, no writes.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from providers import _dotted, _tail  # noqa: E402  — imported, never re-spelled

#: Every name that is the driver. `psycopg2` is here although this repository
#: pins v3: the point is that the inner ring reaches no database by any
#: spelling, and a module importing the older client is not less of a second
#: path for being out of date.
DRIVER_MODULES = frozenset({
    "psycopg", "psycopg2", "psycopg_binary", "psycopg_pool", "asyncpg",
    "pg8000", "sqlalchemy", "sqlite3", "MySQLdb", "pymysql", "pymongo",
})

#: The one place the driver is admitted. A prefix, matched on the path, because
#: the store is a package and its modules are not enumerated here — a list of
#: files would go stale the first time one was added.
ALLOWED: Tuple[str, ...] = ("store/",)

#: Dynamic spellings. These carry a string where an `import` carries a name, so
#: nothing in the import graph shows them — `tools/purity.py`'s `_DYNAMIC`, for
#: the same reason and against the same evasion.
_DYNAMIC = frozenset({"__import__", "import_module"})


class Kind(Enum):
    IMPORT = "import"            # `import psycopg` / `from psycopg import ...`
    DYNAMIC = "dynamic"          # `import_module("psycopg")`
    UNRESOLVED = "unresolved"    # a dynamic import whose name is not a literal


class Verdict(Enum):
    CLEAN = "clean"        # the driver was found, and only where it is admitted
    VACUOUS = "vacuous"    # nothing imports it anywhere — not a pass
    FINDINGS = "findings"


@dataclass(frozen=True)
class Reach:
    kind: Kind
    module: str
    line: int
    detail: str
    allowed: bool

    @property
    def is_finding(self) -> bool:
        return not self.allowed

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
        """`CLEAN` only. A scan that found no driver anywhere has not checked
        anything — the shape `sockets.py` calls `VACUOUS`, and the state this
        repository was in before the store existed."""
        return self.verdict is Verdict.CLEAN


def admitted(module: str) -> bool:
    """Whether this path is one of the places the driver is allowed."""
    text = str(module).replace("\\", "/")
    return any(text == p.rstrip("/") or text.startswith(p) for p in ALLOWED)


def _is_driver(dotted: str) -> bool:
    if not dotted:
        return False
    return (dotted in DRIVER_MODULES
            or _tail(dotted) in DRIVER_MODULES
            or dotted.split(".")[0] in DRIVER_MODULES)


def scan_source(src: str, module: str) -> Tuple[Reach, ...]:
    """Every reach for the driver in one file. Parses; never imports, never runs."""
    out: List[Reach] = []
    ok = admitted(module)
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        # Unparseable is not a pass, and it is not admitted either: a file
        # nobody can read cannot be shown not to import the driver, wherever
        # it sits. `tools/purity.py` learned this the expensive way.
        return (Reach(Kind.UNRESOLVED, module, exc.lineno or 0,
                      "unparseable — cannot be shown not to import the driver",
                      False),)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if _is_driver(a.name):
                    out.append(Reach(Kind.IMPORT, module, node.lineno,
                                     f"imports {a.name}", ok))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if _is_driver(node.module):
                out.append(Reach(Kind.IMPORT, module, node.lineno,
                                 f"imports from {node.module}", ok))
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            if _tail(name) not in _DYNAMIC:
                continue
            target = (node.args[0].value
                      if node.args and isinstance(node.args[0], ast.Constant)
                      and isinstance(node.args[0].value, str) else None)
            if target is None:
                out.append(Reach(
                    Kind.UNRESOLVED, module, node.lineno,
                    f"{_tail(name)}() with a non-literal name — the import graph "
                    "cannot show whether this loads the driver", ok))
            elif _is_driver(target):
                out.append(Reach(Kind.DYNAMIC, module, node.lineno,
                                 f"{_tail(name)}({target!r}) — no import statement "
                                 "declares it", ok))
    return tuple(out)


def scan(paths: Sequence[Path]) -> Tuple[Reach, ...]:
    out: List[Reach] = []
    for base in paths:
        files = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for py in files:
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            out.extend(scan_source(py.read_text(encoding="utf-8"), str(rel)))
    return tuple(out)


def counted(paths: Sequence[Path]) -> int:
    n = 0
    for base in paths:
        n += 1 if base.is_file() else len(list(base.rglob("*.py")))
    return n


def check(paths: Sequence[Path]) -> Scan:
    reaches = scan(paths)
    if not reaches:
        return Scan(Verdict.VACUOUS, reaches, counted(paths))
    verdict = (Verdict.FINDINGS if any(r.is_finding for r in reaches)
               else Verdict.CLEAN)
    return Scan(verdict, reaches, counted(paths))


def main(argv: Sequence[str]) -> int:
    targets = [Path(a) for a in argv] or [
        ROOT / "records", ROOT / "tools", ROOT / "store", ROOT / "craft",
        ROOT / "presentation", ROOT / "surfaces", ROOT / "venue",
        ROOT / "voice.py", ROOT / "personas.py"]
    targets = [t for t in targets if t.exists()]
    r = check(targets)
    for reach in r.reaches:
        print(f"  {'admitted ' if reach.allowed else 'UNDECLARED'} {reach}")
    if r.verdict is Verdict.VACUOUS:
        print(f"\n  VACUOUS — {r.scanned} module(s) scanned and none imports the "
              "driver. Nothing was checked, which is not the same as nothing "
              "being wrong.")
        return 2
    if r.findings:
        print(f"\n  FAIL — {len(r.findings)} module(s) outside "
              f"{', '.join(ALLOWED)} reach the driver, over {r.scanned} scanned")
        return 1
    print(f"\n  PASS — {len(r.reaches)} driver import(s), every one inside "
          f"{', '.join(ALLOWED)}; {r.scanned} module(s) scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
