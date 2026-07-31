"""Two rules a reader would otherwise take on trust: nothing is deleted, every suite runs alone.

Both lived in `tools/conform.py` as short functions that had never been pointed
at anything, and **both were broken in the same two ways as the three before
them** — a non-recursive glob and a substring match standing in for a parse.

`check_revocation_is_dated` was the worse of the two, because it was wrong in
*both* directions at once. Against a directory holding five real deletions and
one clean file, it flagged **the clean file** — whose docstring read *"Never call
`edges.remove(`"* — and missed every one of:

    del edges[0]                                   # the plainest spelling
    self._edges.remove(eid)                        # `\\bedges` finds no boundary in `_edges`
    [e for e in edges if e.id != eid]              # dropping the row, by another name
    store.execute("DELETE FROM edge WHERE ...")    # the one that actually reaches a disk
    sub/hidden.py                                  # never looked at; the glob was `*.py`

`check_suite_runs_standalone` asked whether the string `__main__` appeared
anywhere in the file. It therefore passed a suite whose **docstring** mentions
`__main__` and which has no runner, a suite whose runner is `pass`, and — worst —
a suite whose runner catches every failure, prints `FAIL`, and **exits 0**. All
three contain failing tests. All three exit 0 standalone. A runner that swallows
failures is worse than no runner at all, because the conformance record then
carries a row saying the suite runs alone.

**One limitation is named here rather than discovered**, and it is the important
one. `[e for e in edges if e.live_at(at)]` is how `records/sending.py` derives a
recipient list, and it is *character for character* how you would drop a
revoked edge. In a codebase of pure predicates the two are the same operation,
so this scan cannot separate them and does not try. **Revocation-by-delete is a
property of a store, and there is no store** — so what this check can prove today
is narrow, and it says `UNKNOWN` rather than dressing that up.

Stdlib only. Parses; never imports.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent

#: Receivers whose removal ends someone's standing. Declared rather than
#: inferred, so the list is auditable and a new one is a visible diff. Matched
#: on the trailing word, so `_edges`, `self.edges` and `live_edges` all count —
#: the shipped regex used `\bedges` and a leading underscore is a word
#: character, so `self._edges.remove()` slipped through.
STANDING_NAMES = frozenset({
    "edge", "edges", "grant", "grants", "guardian", "guardians", "standing",
    "consent", "consents", "enrollment", "enrollments", "assignment",
    "assignments", "restriction", "restrictions", "lane", "lanes",
})

#: Methods that remove in place.
REMOVERS = frozenset({"remove", "pop", "clear", "discard", "popitem",
                      "difference_update", "symmetric_difference_update"})

_SQL_DELETE = re.compile(
    r"\bDELETE\s+FROM\b|\bDROP\s+(TABLE|ROW)\b|\bTRUNCATE\s+(TABLE\s+)?\w", re.I)


def _sql_deletes(node) -> bool:
    """Whether this argument is SQL that removes rows.

    **f-strings are the normal spelling and the first version missed them.**
    `execute(f"DELETE FROM edge WHERE id={eid}")` is an `ast.JoinedStr`, not an
    `ast.Constant`, so a scan over constants alone sees nothing — and
    parameterised SQL built by interpolation is what this looks like the moment
    a store exists. The named limit (`sql = "..."` then `execute(sql)`) is a
    different and rarer shape; this one was neither named nor caught.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return bool(_SQL_DELETE.search(node.value))
    if isinstance(node, ast.JoinedStr):
        literal = "".join(v.value for v in node.values
                          if isinstance(v, ast.Constant) and isinstance(v.value, str))
        return bool(_SQL_DELETE.search(literal))
    return False


class Cut(Enum):
    DEL = "del"                # a `del` statement anywhere in the core
    REMOVE = "remove"          # in-place removal from a standing collection
    SQL = "sql"                # DELETE FROM in a string literal


@dataclass(frozen=True)
class Deletion:
    cut: Cut
    module: str
    line: int
    detail: str

    def __str__(self) -> str:
        return f"{self.module}:{self.line} {self.detail}"


def _trailing_name(node) -> str:
    """`self._edges` → `_edges`; `edges` → `edges`; `Foo().bar` → `bar`."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_standing(name: str) -> bool:
    """Whether this receiver holds standing.

    **The comment on `STANDING_NAMES` claimed `live_edges` counted and it did
    not.** `lstrip("_")` removes leading underscores only, so `_edges` matched
    and `live_edges` did not — a declaration with nothing behind it, in the
    checker written to find declarations with nothing behind them. Now the
    trailing `_`-separated segment is matched as well, so `live_edges`,
    `suppressed_edges` and `self._edges` all count.
    """
    n = name.lstrip("_").lower()
    return n in STANDING_NAMES or n.rsplit("_", 1)[-1] in STANDING_NAMES


def scan_deletions(src: str, module: str) -> Tuple[Deletion, ...]:
    out: List[Deletion] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return (Deletion(Cut.DEL, module, exc.lineno or 0,
                         "unparseable — cannot be shown to delete nothing"),)

    for node in ast.walk(tree):
        if isinstance(node, ast.Delete):
            targets = ", ".join(
                _trailing_name(t.value if isinstance(t, ast.Subscript) else t)
                or "?" for t in node.targets)
            out.append(Deletion(Cut.DEL, module, node.lineno,
                                f"del {targets} — the core deletes nothing; "
                                "revocation sets invalid_at (refusal 3)"))

        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in REMOVERS:
                who = _trailing_name(node.func.value)
                if _is_standing(who):
                    out.append(Deletion(
                        Cut.REMOVE, module, node.lineno,
                        f"{who}.{node.func.attr}() removes standing rather than "
                        "dating it"))

        if isinstance(node, ast.Call):
            # A `DELETE` only counts when it is **handed to something**. The
            # first version walked every string constant, so this module's own
            # decoy — a docstring saying *"never DELETE FROM edge"* — was
            # flagged, which is the same false positive the shipped regex made
            # over lines. A rule written in prose is not the rule being broken.
            #
            # Known limit: `sql = "DELETE FROM edge"` followed by `execute(sql)`
            # is invisible. Constant propagation is not worth it here; the store
            # is where this gets enforced properly, and there is no store.
            for arg in list(node.args) + [k.value for k in node.keywords]:
                if _sql_deletes(arg):
                    out.append(Deletion(
                        Cut.SQL, module, node.lineno,
                        "a DELETE statement is executed — a deleted row leaves no "
                        "dated record and no answer to 'who could see this on "
                        "October 12'"))
    return tuple(out)


def deletions(paths: Sequence[Path]) -> Tuple[Deletion, ...]:
    out: List[Deletion] = []
    for base in paths:
        files = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for py in files:
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            out.extend(scan_deletions(py.read_text(encoding="utf-8"), str(rel)))
    return tuple(out)


# --- standalone runners ----------------------------------------------------


class Runner(Enum):
    OK = "ok"
    MISSING = "missing"    # no `if __name__ == "__main__":` block at all
    EMPTY = "empty"        # a block that does nothing
    SWALLOWS = "swallows"  # a block that runs tests and cannot fail the process


@dataclass(frozen=True)
class Suite:
    module: str
    runner: Runner
    detail: str

    @property
    def ok(self) -> bool:
        return self.runner is Runner.OK


def _is_main_guard(node) -> bool:
    """`if __name__ == "__main__":` — matched structurally, not by substring.

    The shipped check asked whether the *string* `__main__` appeared anywhere in
    the file, which a docstring satisfies.
    """
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    left, ops, comps = node.test.left, node.test.ops, node.test.comparators
    return (isinstance(left, ast.Name) and left.id == "__name__"
            and len(ops) == 1 and isinstance(ops[0], ast.Eq)
            and isinstance(comps[0], ast.Constant) and comps[0].value == "__main__")


def _is_exit_call(func) -> bool:
    """`sys.exit`, `os._exit`, bare `exit`/`quit` — and nothing else.

    The first version accepted **any** attribute named `exit`, so `logger.exit()`
    and `self.exit()` counted as ending the process.
    """
    if isinstance(func, ast.Name):
        return func.id in ("exit", "quit")
    if isinstance(func, ast.Attribute):
        owner = func.value.id if isinstance(func.value, ast.Name) else ""
        return owner in ("sys", "os") and func.attr in ("exit", "_exit")
    return False


def _can_be_nonzero(arg) -> bool:
    """Whether this exit status can be a failure.

    Absent, `0` and `None` are successes; everything else — a name, a
    conditional, a string (`SystemExit("msg")` exits 1) — can fail.
    """
    if arg is None:
        return False
    if isinstance(arg, ast.Constant):
        return arg.value not in (0, None, False)
    return True


def _exits_nonzero(block: Sequence[ast.stmt]) -> bool:
    """Whether this block can end the process with a **failing** status.

    **The name promised two conditions and the first version checked one.** It
    asked whether an exit call existed and never what it returned, so the exact
    shape this check was built to catch passed in a different spelling:

        print("FAIL"); sys.exit(0)          -> OK
        print("FAIL"); raise SystemExit(0)  -> OK

    That is *"catches every failure, prints FAIL, and exits 0"* — the case
    `check_suite_runs_standalone` exists for — reported as a working runner.
    Worse, `test_sys_exit_counts_as_well_as_raise_SystemExit` asserted `OK` on
    `sys.exit(0)`: the test meant to fix the *spelling* and the `0` was
    incidental, so a green test locked the hole in.

    **A guard with two conditions needs two decoys, or one condition is
    decorative** — this PR's own sentence, arriving one level up. `raise
    SystemExit(1 if failures else 0)` and `sys.exit(failures)` both still pass,
    which is every real suite in this repository.
    """
    for node in block:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Raise) and sub.exc is not None:
                if isinstance(sub.exc, ast.Call):
                    f = sub.exc.func
                    if isinstance(f, ast.Name) and f.id == "SystemExit":
                        if _can_be_nonzero(sub.exc.args[0] if sub.exc.args else None):
                            return True
                # `raise SystemExit` with no call instantiates with no args and
                # exits 0, so it is not a failing exit.
            elif isinstance(sub, ast.Call) and _is_exit_call(sub.func):
                if _can_be_nonzero(sub.args[0] if sub.args else None):
                    return True
    return False


def scan_runner(src: str, module: str) -> Suite:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return Suite(module, Runner.MISSING, "unparseable")

    for node in tree.body:
        if not _is_main_guard(node):
            continue
        body = [s for s in node.body if not isinstance(s, ast.Pass)]
        if not body:
            return Suite(module, Runner.EMPTY,
                         "a __main__ block that does nothing")
        if not _exits_nonzero(node.body):
            return Suite(module, Runner.SWALLOWS,
                         "a runner that cannot fail the process — it reports "
                         "success to everything downstream, which is worse than "
                         "having no runner")
        return Suite(module, Runner.OK, "runs standalone and exits nonzero on failure")
    return Suite(module, Runner.MISSING, "no `if __name__ == \"__main__\":` block")


#: Directory names whose contents are not suites. `fixtures/` holds decoys —
#: files that are *deliberately* broken so a checker can be shown to complain —
#: and counting them as real suites would make this check fail forever, which is
#: how a check gets deleted. Named as a constant so the exclusion is visible
#: rather than buried in a glob, and asserted both ways: the real scan skips
#: them, and pointing the scan *at* them finds every one.
NOT_SUITES = ("fixtures",)


def runners(paths: Sequence[Path], *, skip: Sequence[str] = NOT_SUITES) -> Tuple[Suite, ...]:
    out: List[Suite] = []
    for base in paths:
        if base.is_file():
            files = [base]
        else:
            # **Relative to the base, not absolute.** The first version matched
            # against the whole path, so pointing the scan directly at
            # `tests/fixtures/decoys/runners` skipped every file in it — an
            # exclusion that also blocks deliberate inspection, which would have
            # made this checker the only one in the set that cannot be aimed at
            # its own decoys.
            files = sorted(p for p in base.rglob("test_*.py")
                           if not any(s in p.relative_to(base).parts for s in skip))
        for py in files:
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            out.append(scan_runner(py.read_text(encoding="utf-8"), str(rel)))
    return tuple(out)


def counted(paths: Sequence[Path], pattern: str = "*.py") -> int:
    n = 0
    for base in paths:
        n += 1 if base.is_file() else len(list(base.rglob(pattern)))
    return n
