"""The trust root is never *committed*, checked over the tree git actually tracks.

`CLAUDE.md` refusal 2 and `docs/SECURITY-AUDIT.md` `TM-ROOT-01`: `mcp_apps/`,
`_net_leases/` and any grant material stay out of the tree and off any remote.
Two things already enforce the *staged* set — `.gitignore` stops `git add -A`,
and `.githooks/pre-commit` refuses a force-add — but the audit names one
residual out loud: **the hook is a gate only where `core.hooksPath` points at
it** (one install act per clone), so a clone that never ran `scripts/install-
hooks.sh` is back to `.gitignore` alone, and nothing catches a trust-root path
that reached a commit through an uninstalled clone.

This is that catch, and it is deliberately at a different point than the hook:
the hook reads what is *about to be committed*; this reads what **is** committed
(`git ls-files`), so it holds on every checkout regardless of whether the hook
was installed. `tests/test_trustroot.py` runs it over the real tree (the live
gate — a committed trust root turns that test red in CI, which runs the suite)
and attempts the forbidden act against a throwaway repo (rule 19). The two
checks compose: the hook stops the commit on an installed clone, this fails the
build if one ever slips past it.

    python3 tools/trustroot.py [dir]

Stdlib only (`git ls-files` by subprocess). No writes, no network.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent

#: A path component that is a trust-root directory, matched by *component* rather
#: than by a glob so all four shapes the hook enumerates are one rule: a bare
#: `mcp_apps` gitlink (`["mcp_apps"]`), `mcp_apps/x` (under), `vendor/mcp_apps`
#: (nested-exact), and `vendor/mcp_apps/x` (nested-under) all carry the component.
_TRUST_ROOT_DIRS = frozenset({"mcp_apps", "_net_leases"})

#: Grant material is named by suffix, wherever it sits.
_GRANT_SUFFIXES = (".grant", ".lease")


class Verdict(Enum):
    CLEAN = "clean"        # git answered and tracks no trust-root path
    FINDINGS = "findings"  # a trust-root path is tracked — refusal 2 breached
    UNKNOWN = "unknown"    # git could not answer; not a pass (rule 13)


@dataclass(frozen=True)
class Scan:
    verdict: Verdict
    paths: Tuple[str, ...]
    detail: str

    @property
    def ok(self) -> bool:
        return self.verdict is Verdict.CLEAN


def is_trust_root(path: str) -> bool:
    """Whether a repo-relative path is trust-root material.

    A path is trust root if any of its components is a trust-root directory —
    which catches the bare-gitlink shape a `mcp_apps/*` glob misses, the gap
    `TM-ROOT-01` recorded after the PR #16 review — or if it ends in a grant
    suffix.
    """
    p = path.replace("\\", "/").strip("/")
    if not p:
        return False
    if any(part in _TRUST_ROOT_DIRS for part in p.split("/")):
        return True
    return p.endswith(_GRANT_SUFFIXES)


def tracked_paths(where: Optional[Path] = None) -> Optional[Tuple[str, ...]]:
    """Every path git tracks, or `None` if git cannot answer (not a repo, no git).

    `None` is distinct from an empty tuple on purpose: a directory git knows
    nothing about has not been checked, and reporting it as "tracks no trust
    root" is the absence-as-result shape rule 13 refuses.
    """
    base = where if where is not None else ROOT
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=base,
                           capture_output=True, text=True)
    except (OSError, ValueError):
        return None
    if r.returncode != 0:
        return None
    return tuple(p for p in r.stdout.split("\0") if p)


def scan(where: Optional[Path] = None) -> Scan:
    """The tracked tree, judged. `UNKNOWN` when git could not be asked."""
    tracked = tracked_paths(where)
    if tracked is None:
        return Scan(Verdict.UNKNOWN, (),
                    "git could not list tracked files here (not a repository, or "
                    "git is unavailable); a tree that cannot be read is unknown, "
                    "not clean (rule 13)")
    hits = tuple(p for p in tracked if is_trust_root(p))
    if hits:
        return Scan(Verdict.FINDINGS, hits,
                    f"{len(hits)} trust-root path(s) are committed, which refusal 2 "
                    "forbids: " + ", ".join(hits[:5]))
    return Scan(Verdict.CLEAN, (),
                f"{len(tracked)} tracked path(s); none is trust-root material")


def main(argv: Sequence[str]) -> int:
    where = Path(argv[0]) if argv else ROOT
    r = scan(where)
    if r.verdict is Verdict.UNKNOWN:
        print(f"UNKNOWN: {r.detail}")
        return 2
    if r.verdict is Verdict.FINDINGS:
        for p in r.paths:
            print(f"FINDING {p}  (trust-root material, never committed — refusal 2)")
        print(r.detail)
        return 1
    print(f"clean: {r.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
