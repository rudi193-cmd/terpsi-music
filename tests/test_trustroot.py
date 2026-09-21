"""The committed-tree trust-root gate, shown to hold and shown to fail (TM-ROOT-01).

`tools/trustroot.py` is the complement to `.githooks/pre-commit`: the hook reads
the staged set on an installed clone; this reads what `git ls-files` actually
tracks, so it holds on every checkout regardless of whether the hook was
installed. The live gate is `test_the_real_tree_tracks_no_trust_root` — a
committed trust root turns it red, and CI runs this suite. The rule-19 half
stages genuine trust-root paths in throwaway repositories and requires the
finding, including the **bare gitlink** shape a `mcp_apps/*` glob missed.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/test_trustroot.py -q
    python3 tests/test_trustroot.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import trustroot as T  # noqa: E402


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True, text=True)


def _repo(d: Path) -> Path:
    """A throwaway git repo with one ordinary tracked file."""
    _git("init", "-q", cwd=d)
    _git("config", "user.email", "t@t", cwd=d)
    _git("config", "user.name", "t", cwd=d)
    (d / "ordinary.py").write_text("x = 1\n", encoding="utf-8")
    _git("add", "ordinary.py", cwd=d)
    _git("commit", "-qm", "ordinary", cwd=d)
    return d


# --- the live gate ---------------------------------------------------------


def test_the_real_tree_tracks_no_trust_root():
    """The point: over the actual repository, git tracks no trust-root path. A
    committed `mcp_apps/`, `_net_leases/`, `*.grant` or `*.lease` fails here, and
    CI runs this suite — the enforcement the hook could not give across an
    uninstalled clone."""
    r = T.scan(ROOT)
    assert r.verdict is T.Verdict.CLEAN, r.detail
    assert r.paths == ()


# --- the fail case (rule 19) -----------------------------------------------


def test_a_tracked_grant_file_is_a_finding():
    with tempfile.TemporaryDirectory() as d:
        repo = _repo(Path(d))
        (repo / "family.grant").write_text("secret", encoding="utf-8")
        _git("add", "-f", "family.grant", cwd=repo)
        _git("commit", "-qm", "leak", cwd=repo)
        r = T.scan(repo)
    assert r.verdict is T.Verdict.FINDINGS, r.detail
    assert "family.grant" in r.paths


def test_a_tracked_mcp_apps_dir_is_a_finding():
    with tempfile.TemporaryDirectory() as d:
        repo = _repo(Path(d))
        (repo / "mcp_apps").mkdir()
        (repo / "mcp_apps" / "app.json").write_text("{}", encoding="utf-8")
        _git("add", "-f", "mcp_apps/app.json", cwd=repo)
        _git("commit", "-qm", "leak", cwd=repo)
        r = T.scan(repo)
    assert r.verdict is T.Verdict.FINDINGS
    assert any(p.startswith("mcp_apps/") for p in r.paths)


def test_a_bare_gitlink_at_the_trust_root_path_is_a_finding():
    """The shape a `mcp_apps/*` glob misses: a submodule gitlink is one index
    entry named `mcp_apps` with nothing after it. Staged as a genuine mode-160000
    entry, exactly as `test_trust_root_hook.py` does, so this proves the same gap
    the hook's own patterns had to close."""
    with tempfile.TemporaryDirectory() as d:
        repo = _repo(Path(d))
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                             capture_output=True, text=True).stdout.strip()
        _git("update-index", "--add", "--cacheinfo", f"160000,{sha},_net_leases",
             cwd=repo)
        _git("commit", "-qm", "gitlink", cwd=repo)
        r = T.scan(repo)
    assert r.verdict is T.Verdict.FINDINGS, r.detail
    assert "_net_leases" in r.paths


def test_a_clean_repo_is_not_a_finding():
    with tempfile.TemporaryDirectory() as d:
        repo = _repo(Path(d))
        r = T.scan(repo)
    assert r.verdict is T.Verdict.CLEAN and r.ok


def test_a_non_git_directory_is_unknown_not_clean():
    """Rule 13: a directory git cannot list is unknown, never a pass. An empty
    finding list from a tree that was never read is the absence-as-result shape
    this check exists to refuse."""
    with tempfile.TemporaryDirectory() as d:
        r = T.scan(Path(d))
    assert r.verdict is T.Verdict.UNKNOWN and not r.ok


def test_the_matcher_catches_all_four_shapes_and_the_suffixes():
    assert T.is_trust_root("mcp_apps")                 # bare gitlink
    assert T.is_trust_root("mcp_apps/app.json")        # under
    assert T.is_trust_root("vendor/_net_leases")       # nested-exact
    assert T.is_trust_root("vendor/_net_leases/x")     # nested-under
    assert T.is_trust_root("a/b/family.grant")         # suffix, nested
    assert T.is_trust_root("x.lease")
    assert not T.is_trust_root("records/sending.py")
    assert not T.is_trust_root("mcp_apps_helper.py")   # not a component
    assert not T.is_trust_root("")


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
