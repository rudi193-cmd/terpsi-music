"""What the core reaches for: the network it imports, and the disk it writes.

`tools/sockets.py` answers *what listens*. This answers the two §6 questions
either side of it — **can the inner ring reach out**, and **where does it
write** — and it exists because both checks lived inside `conform.py` as ten
lines apiece that had only ever been run against a clean tree.

**Both were broken, and the decoys found it in one run.** `check_no_egress`
returned `PASS` for a directory containing all four of these:

| what | why it was missed |
|---|---|
| `__import__("socket")` | not an `ast.Import` node |
| `importlib.import_module("urllib.request")` | same |
| `subprocess.run(["curl", …])` | `subprocess` was not in the egress set, and it is a network call |
| `sub/leaky.py` importing `socket` | the scan globbed `*.py`, **not** `**/*.py` — a subpackage was invisible |

`check_write_paths` was worse in a quieter way: it took **no path argument at
all**, so it could not be pointed at anything, and it matched substrings — so a
docstring saying *"never calls `open(`"* failed the file, and `Path.open()`,
`os.rename` and `tempfile` passed it.

**The pattern across all three checkers is the same.** A guard written against
the tree it guards passes on the day it ships and every day after, whether or
not it works. §14 already records the fleet-wide version — *"the AST checker
sees imports, not filesystem writes"* — and both halves of that sentence turned
out to be true here.

**Two rules carried over from `sockets.py`, because they are the same rules.**

*It parses and never imports.* Executing a module to inspect it is how you find
out about its network call by making it.

*Unresolvable is not a pass.* `open(path, mode)` with a non-literal mode is
`UNKNOWN_MODE` and counts as a write, the same way a bind whose host comes from
the environment counts as undeclared. The alternative is a checker that is
quietest exactly where the code is least legible.

Stdlib only. No network, no writes — asserted by scanning this file with itself.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent

#: Modules whose presence in the inner ring means it can reach out.
EGRESS_MODULES = frozenset({
    "socket", "ssl", "http", "urllib", "urllib3", "requests", "httpx", "aiohttp",
    "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "nntplib",
    "websockets", "websocket", "xmlrpc", "asyncio", "paramiko", "boto3",
    "grpc", "pika", "redis", "psycopg2", "pymongo",
})

#: Callables that start a process. A shell is a network client when the thing it
#: runs is `curl`, and no import of `socket` appears anywhere in the file.
_SPAWN_MODULES = frozenset({"subprocess", "os", "pty", "multiprocessing"})
_SPAWN_CALLS = frozenset({
    "run", "call", "check_call", "check_output", "Popen", "system",
    "popen", "spawnl", "spawnv", "execv", "execvp",
})

#: Dynamic import spellings. These carry a string where an `import` carries a
#: name, so nothing in the import graph shows them.
_DYNAMIC = frozenset({"__import__", "import_module"})

#: Verbs that mean the filesystem and nothing else, whoever owns them.
_UNAMBIGUOUS_WRITES = frozenset({
    "write_text", "write_bytes", "makedirs", "removedirs", "rmtree",
    "copytree", "copyfile", "mkstemp", "mkdtemp", "symlink_to",
    "NamedTemporaryFile", "TemporaryDirectory",
})

#: Verbs that mean the filesystem **only when a filesystem module owns them.**
#: `dataclasses.replace()` is not `os.replace()`, and the first version of this
#: check flagged every frozen-dataclass update in `records/` as a disk write —
#: a false positive is how a check earns the reputation that gets it disabled.
_OWNED_WRITES = frozenset({
    "mkdir", "remove", "unlink", "rename", "replace", "rmdir",
    "copy", "copy2", "move", "touch", "link",
})

_FS_OWNERS = frozenset({"os", "shutil", "tempfile", "pathlib", "path"})

_WRITE_MODES = ("w", "a", "x", "+")


class Reach(Enum):
    EGRESS = "egress"
    SPAWN = "spawn"
    WRITE = "write"
    READ = "read"
    UNKNOWN_MODE = "unknown_mode"   # a write until shown otherwise


@dataclass(frozen=True)
class Touch:
    reach: Reach
    module: str
    line: int
    detail: str

    @property
    def is_write(self) -> bool:
        """A read is a dependency; a write is a write. Kept apart on purpose —
        a check that cries wolf on every `open()` gets switched off."""
        return self.reach in (Reach.WRITE, Reach.UNKNOWN_MODE)

    def __str__(self) -> str:
        return f"{self.module}:{self.line} {self.detail}"


def _root_of(dotted: str) -> str:
    return dotted.split(".")[0]


def _attr_owner(func) -> str:
    """`subprocess.run` → `subprocess`; `shutil.rmtree` → `shutil`."""
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id
    return ""


def _name_of(func) -> str:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _on_a_path(func) -> bool:
    """`Path("x").unlink()` — the receiver is literally a `Path(...)` call.

    **The blind spot this leaves is named rather than hidden**: `p.unlink()`
    where `p` is a variable holding a `Path` is invisible to a checker that does
    not do type inference, and this one does not. `tests/test_purity.py` asserts
    the gap so it reads as a known limit rather than as coverage.
    """
    return (isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Call)
            and _name_of(func.value.func) == "Path")


def _mode_of(call: ast.Call) -> Optional[str]:
    """The mode `open()` was called with, or `None` when it is not a literal."""
    if len(call.args) >= 2:
        a = call.args[1]
        return a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else None
    for kw in call.keywords:
        if kw.arg == "mode":
            return (kw.value.value
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)
                    else None)
    return "r"  # open(path) reads


def scan_source(src: str, module: str) -> Tuple[Touch, ...]:
    """Everything this source reaches for. Parses; never imports, never runs."""
    out: List[Touch] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return (Touch(Reach.UNKNOWN_MODE, module, exc.lineno or 0,
                      "unparseable — cannot be shown to reach nothing"),)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if _root_of(a.name) in EGRESS_MODULES:
                    out.append(Touch(Reach.EGRESS, module, node.lineno,
                                     f"imports {a.name}"))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if _root_of(node.module) in EGRESS_MODULES:
                out.append(Touch(Reach.EGRESS, module, node.lineno,
                                 f"imports from {node.module}"))
        elif isinstance(node, ast.Call):
            name = _name_of(node.func)
            owner = _attr_owner(node.func)

            if name in _DYNAMIC:
                target = (node.args[0].value
                          if node.args and isinstance(node.args[0], ast.Constant)
                          and isinstance(node.args[0].value, str) else None)
                if target is None:
                    out.append(Touch(Reach.EGRESS, module, node.lineno,
                                     f"{name}() with a non-literal name — the import "
                                     "graph cannot show what this loads"))
                elif _root_of(target) in EGRESS_MODULES:
                    out.append(Touch(Reach.EGRESS, module, node.lineno,
                                     f"{name}({target!r}) — no import statement declares it"))

            elif owner in _SPAWN_MODULES and name in _SPAWN_CALLS:
                out.append(Touch(Reach.SPAWN, module, node.lineno,
                                 f"{owner}.{name}() starts a process; a shell is a "
                                 "network client when what it runs is"))

            elif name == "open":
                mode = _mode_of(node)
                if mode is None:
                    out.append(Touch(Reach.UNKNOWN_MODE, module, node.lineno,
                                     "open() with a non-literal mode — counted as a "
                                     "write, because unresolvable is not a pass"))
                elif any(m in mode for m in _WRITE_MODES):
                    out.append(Touch(Reach.WRITE, module, node.lineno,
                                     f"open(..., {mode!r})"))
                else:
                    out.append(Touch(Reach.READ, module, node.lineno,
                                     f"open(..., {mode!r})"))

            elif name in _UNAMBIGUOUS_WRITES:
                out.append(Touch(Reach.WRITE, module, node.lineno,
                                 f"{owner + '.' if owner else ''}{name}()"))

            elif name in _OWNED_WRITES and (owner in _FS_OWNERS or _on_a_path(node.func)):
                out.append(Touch(Reach.WRITE, module, node.lineno,
                                 f"{owner + '.' if owner else 'Path(…).'}{name}()"))

    return tuple(out)


def scan(paths: Sequence[Path]) -> Tuple[Touch, ...]:
    """Recursive. The original globbed `*.py` and a subpackage was invisible."""
    out: List[Touch] = []
    for base in paths:
        files = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for py in files:
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            out.extend(scan_source(py.read_text(encoding="utf-8"), str(rel)))
    return tuple(out)


def egress(paths: Sequence[Path]) -> Tuple[Touch, ...]:
    return tuple(t for t in scan(paths) if t.reach in (Reach.EGRESS, Reach.SPAWN))


def writes(paths: Sequence[Path]) -> Tuple[Touch, ...]:
    return tuple(t for t in scan(paths) if t.is_write)


def reads(paths: Sequence[Path]) -> Tuple[Touch, ...]:
    return tuple(t for t in scan(paths) if t.reach is Reach.READ)


def counted(paths: Sequence[Path]) -> int:
    """How many files were actually looked at.

    Reported alongside every verdict, because *"no findings"* over zero files
    and over nineteen are the same sentence and different facts — the shape
    `sockets.py` calls `VACUOUS`.
    """
    n = 0
    for base in paths:
        n += 1 if base.is_file() else len(list(base.rglob("*.py")))
    return n
