"""What in this tree reaches a model, and whether it came through the guard.

`records/inference.py` makes an unguarded *answer* unrepresentable. It cannot
make an unguarded *call site* impossible, because a module that talks to a
provider directly never touches the type. This is the half that closes that:
point it at the tree and it names every call that reaches a model without
passing through `records.inference`.

**Written before there is anything to find, on purpose.** §4.3's worked failure
is a declaration that shipped first with nothing pointed at it; the inverse is
this checker shipping with nothing to point at. So its acceptance is entirely
against `tests/fixtures/decoys/inference_*.py` — source that really does call a
router, really does post to a provider endpoint, and really does launder one
call past a guard it also uses — because a checker written against a tree with
no inference in it passes on the day it ships and every day after, whether or
not it works (`tools/purity.py`'s finding, three checkers in a row).

**Two rules carried from `purity.py` and `sockets.py`, because they are the
same rules.**

*It parses and never imports.* Importing a module to find out whether it calls a
cloud model is a way of finding out by making the call.

*The finding is a call, not a name.* A provider named in a docstring is prose; a
provider imported and never used is a dependency; the thing refusal 1 is about
is a request being made. `inference_in_prose.py` and `inference_guarded.py` are
both decoys **against the wrong implementation** — a grep fails them and this
must not.

**Guarded means lexically inside a guard call**, not "the module imports the
guard somewhere". `inference_launders.py` imports `records.inference`, calls it
once on something harmless, and calls the router directly beside it; a checker
that asked whether the import existed would clear it. So a reaching call counts
as guarded only when it sits **inside the argument subtree** of a call to
`records.inference.accept` or `.through` — which is where the pair a guard vets
must come from anyway.

Stdlib only. No network, no writes.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent

#: The guard. Exempt from its own check, and the only thing that makes a
#: reaching call acceptable.
GUARD_MODULE = "records/inference.py"

#: How the guard is spelled at an import. A module reaching a model must import
#: one of these; anything else is not the guard however it is named locally.
GUARD_PATHS = frozenset({
    "records.inference", ".inference", "inference", "records",
})

#: The functions that vet a pair. `records/inference.py` exports exactly these
#: two ways in, and `tests/test_providers.py` asserts this set still matches it.
GUARD_ENTRIES = frozenset({"accept", "through"})

#: Modules that answer with a model. The first four are the fleet's own edge —
#: `inference_router` is the live one; `llm_edge` is the sibling that discards
#: the provider label, which makes it the more dangerous import of the two.
ROUTER_MODULES = frozenset({
    "inference_router", "llm_edge", "model_adapter", "professor_client",
})

#: Third-party client libraries. A module that imports one of these is building
#: its own path to a provider and will not be seen by anything watching the
#: fleet's router.
CLIENT_MODULES = frozenset({
    "openai", "anthropic", "groq", "cohere", "mistralai", "litellm",
    "google.generativeai", "vertexai", "boto3", "ollama", "llama_cpp",
    "transformers", "sentence_transformers", "torch",
})

#: Hosts and paths that are an inference request whatever library carries them.
#: `11434` and `/api/chat` are here for a reason that is easy to miss: a call
#: straight to the *local* runner is unguarded too. It returns no provider
#: label at all, so nothing downstream can assert on one.
PROVIDER_ENDPOINTS = (
    "api.groq.com", "openrouter.ai", "generativelanguage.googleapis.com",
    "api.openai.com", "api.anthropic.com", "api.cohere.ai", "api.mistral.ai",
    "api.together.xyz", "api.cerebras.ai", "api.sambanova.ai",
    ":11434", "/api/chat", "/api/generate", "/chat/completions",
    ":generateContent",
)

#: Call names that carry a payload somewhere. Only a finding when a provider
#: endpoint appears among the arguments — `urlopen(cfg.url)` is invisible to
#: this checker and `tests/test_providers.py` asserts the gap by name, the way
#: `purity._on_a_path` does, so it reads as a known limit rather than coverage.
_SENDERS = frozenset({
    "urlopen", "Request", "request", "post", "get", "send", "run", "call",
    "check_output", "Popen",
})


class Kind(Enum):
    ROUTER_CALL = "router_call"        # the fleet's edge, called
    CLIENT_CALL = "client_call"        # a provider SDK, called
    ENDPOINT_CALL = "endpoint_call"    # a request naming a provider address
    ROUTER_IMPORT = "router_import"    # recorded, not a finding on its own


class Verdict(Enum):
    CLEAN = "clean"          # calls were found and every one came through the guard
    VACUOUS = "vacuous"      # nothing reaches a model here — not a pass
    FINDINGS = "findings"


@dataclass(frozen=True)
class Reach:
    kind: Kind
    module: str
    line: int
    detail: str
    guarded: bool

    @property
    def is_finding(self) -> bool:
        """An import is how you find the call; the call is the finding."""
        return self.kind is not Kind.ROUTER_IMPORT and not self.guarded

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
        """`CLEAN` only. A scan that found nothing has not checked anything."""
        return self.verdict is Verdict.CLEAN


def _dotted(node) -> str:
    """`records.inference.through` → `"records.inference.through"`."""
    parts: List[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _tail(dotted: str) -> str:
    return dotted.rsplit(".", 1)[-1]


def _matches(dotted: str, names: frozenset) -> bool:
    """A dotted import path against a set of module names.

    Matched at the head and the tail, because `core.inference_router`,
    `inference_router` and `google.generativeai` are all how the same thing
    gets written, and matching the whole string only would see none of them.
    """
    if dotted in names or _tail(dotted) in names:
        return True
    return dotted.split(".")[0] in names


def _kind_of(dotted: str) -> Optional[Kind]:
    """Which sort of model-reaching module this import is, if it is one."""
    if _matches(dotted, ROUTER_MODULES):
        return Kind.ROUTER_CALL
    if _matches(dotted, CLIENT_MODULES):
        return Kind.CLIENT_CALL
    return None


def _strings_in(call: ast.Call) -> List[str]:
    out = []
    for node in ast.walk(call):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
        elif isinstance(node, ast.JoinedStr):
            out.extend(p.value for p in node.values
                       if isinstance(p, ast.Constant) and isinstance(p.value, str))
    return out


def _endpoint_in(call: ast.Call) -> Optional[str]:
    for s in _strings_in(call):
        for marker in PROVIDER_ENDPOINTS:
            if marker in s:
                return marker
    return None


def _guard_aliases(tree: ast.AST) -> Tuple[Set[str], Set[str]]:
    """`(names imported from the guard, module aliases for it)`."""
    entries: Set[str] = set()
    modules: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = ("." * (node.level or 0)) + (node.module or "")
            if mod in GUARD_PATHS or (node.module or "") in GUARD_PATHS:
                for a in node.names:
                    if a.name in GUARD_ENTRIES:
                        entries.add(a.asname or a.name)
                    elif a.name == "inference":
                        modules.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name in GUARD_PATHS or _tail(a.name) == "inference":
                    modules.add(a.asname or a.name.split(".")[0])
    return entries, modules


def _guarded_nodes(tree: ast.AST, entries: Set[str], modules: Set[str]) -> Set[int]:
    """Every node lexically inside a call to the guard.

    Subtree membership rather than "the module imports it": a call laundered
    beside a guarded one is the shape this has to catch, and it is the shape a
    tired afternoon produces.
    """
    inside: Set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted(node.func)
        if not dotted:
            continue
        prefix = dotted.rsplit(".", 1)[0] if "." in dotted else ""
        is_guard = (dotted in entries
                    or (_tail(dotted) in GUARD_ENTRIES
                        and (prefix in modules or prefix.split(".")[0] in modules)))
        if is_guard:
            for child in ast.walk(node):
                inside.add(id(child))
    return inside


def scan_source(src: str, module: str) -> Tuple[Reach, ...]:
    """Every reach for a model in one file. Parses; never imports, never runs."""
    out: List[Reach] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return (Reach(Kind.ROUTER_CALL, module, exc.lineno or 0,
                      "unparseable — cannot be shown to reach no model", False),)

    entries, modules = _guard_aliases(tree)
    inside = _guarded_nodes(tree, entries, modules)

    #: Local names bound to a router or client module, and which of the two it
    #: was, so `w.chat(...)` and a bare `respond(...)` are both seen and both
    #: are attributed to the module they came from rather than to the verb.
    router_names: Dict[str, Tuple[str, Kind]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                kind = _kind_of(a.name)
                if kind is not None:
                    router_names[a.asname or a.name.split(".")[0]] = (a.name, kind)
                    out.append(Reach(Kind.ROUTER_IMPORT, module, node.lineno,
                                     f"imports {a.name}", True))
        elif isinstance(node, ast.ImportFrom) and node.module:
            kind = _kind_of(node.module)
            if kind is not None:
                for a in node.names:
                    router_names[a.asname or a.name] = (f"{node.module}.{a.name}", kind)
                out.append(Reach(Kind.ROUTER_IMPORT, module, node.lineno,
                                 f"imports from {node.module}", True))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted(node.func)
        head = dotted.split(".")[0] if dotted else ""
        guarded = id(node) in inside

        if head and head in router_names:
            origin, kind = router_names[head]
            out.append(Reach(kind, module, node.lineno,
                             f"{dotted}() reaches {origin}", guarded))
            continue

        marker = _endpoint_in(node) if _tail(dotted) in _SENDERS else None
        if marker:
            out.append(Reach(Kind.ENDPOINT_CALL, module, node.lineno,
                             f"{dotted}() carries {marker!r}", guarded))

    return tuple(out)


def scan(paths: Sequence[Path], skip: Sequence[str] = (GUARD_MODULE,)) -> Tuple[Reach, ...]:
    """Recursive, like `purity.scan` — a subpackage was invisible to the first
    version of that one and this is the same glob."""
    out: List[Reach] = []
    for base in paths:
        files = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for py in files:
            rel = py.relative_to(ROOT) if str(py).startswith(str(ROOT)) else py
            if str(rel).replace("\\", "/") in set(skip):
                continue
            out.extend(scan_source(py.read_text(encoding="utf-8"), str(rel)))
    return tuple(out)


def counted(paths: Sequence[Path]) -> int:
    n = 0
    for base in paths:
        n += 1 if base.is_file() else len(list(base.rglob("*.py")))
    return n


def check(paths: Sequence[Path], skip: Sequence[str] = (GUARD_MODULE,)) -> Scan:
    """The verdict, with `VACUOUS` kept apart from `CLEAN`.

    *"No unguarded calls"* over a tree with no inference in it and over a tree
    with twelve guarded call sites are the same sentence and different facts.
    Today this repository is the first of those, and the record has to say so.
    """
    reaches = scan(paths, skip=skip)
    calls = [r for r in reaches if r.kind is not Kind.ROUTER_IMPORT]
    if not calls:
        return Scan(Verdict.VACUOUS, reaches, counted(paths))
    verdict = (Verdict.FINDINGS if any(r.is_finding for r in reaches)
               else Verdict.CLEAN)
    return Scan(verdict, reaches, counted(paths))


def main(argv: Sequence[str]) -> int:
    targets = [Path(a) for a in argv] or [
        ROOT / "records", ROOT / "tools", ROOT / "craft",
        ROOT / "voice.py", ROOT / "personas.py"]
    r = check(targets)
    for reach in r.reaches:
        if reach.kind is Kind.ROUTER_IMPORT:
            print(f"  import    {reach}")
    for f in r.findings:
        print(f"  UNGUARDED {f}")
    if r.verdict is Verdict.VACUOUS:
        print(f"\n  VACUOUS — {r.scanned} module(s) scanned and none reaches a "
              "model. Nothing was checked, which is not the same as nothing "
              "being wrong.")
        return 0
    print(f"\n  {r.verdict.value}: {len(r.reaches)} reach(es), "
          f"{len(r.findings)} unguarded, {r.scanned} module(s)")
    return 1 if r.findings else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
