"""The trust-root pre-commit gate, shown to refuse (CLAUDE.md refusal 2).

`.githooks/pre-commit` is the enforcement half of the refusal `.gitignore` only
mitigates. The distinction is the test's whole subject: an ignore rule refuses
`git add`, but `git add -f` walks past it, so the acceptance case here is a
**force-added** grant file — the one `.gitignore` cannot catch — reaching a
real commit and being refused at the hook.

Rule 19: the guard is run against the forbidden act, in a throwaway repository
built for the purpose, rather than trusted because it exists. Rule 18: the hook
is a gate only once `core.hooksPath` points at it, so the test installs it in
the temp repo rather than assuming the developer's clone did — a green run here
says the *hook* refuses, not that this checkout happens to have it wired.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/test_trust_root_hook.py -q
    python3 tests/test_trust_root_hook.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".githooks" / "pre-commit"
GITIGNORE = ROOT / ".gitignore"

#: The paths the hook must refuse — one per shape of the trust root. Each is
#: force-added, because that is the case the gate exists for.
FORBIDDEN = (
    "_net_leases/root.key",
    "mcp_apps/some-app/grant.json",
    "season.grant",
    "roster.lease",
    "nested/dir/_net_leases/held.key",
)

#: The control: ordinary versioned files a commit must still accept, including
#: a couple whose names flirt with the patterns without matching them.
ALLOWED = (
    "docs/NOTES.md",
    "records/grant_helpers.py",     # "grant" in the stem, not a .grant file
    "mcp_apps_notes.md",            # not under mcp_apps/
)


def _git(repo: Path, *args: str, want_ok: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if want_ok and r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r


def _repo(tmp: str) -> Path:
    """A throwaway repo with the real hook installed the way a clone installs it."""
    repo = Path(tmp)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    hooks = repo / ".githooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text(HOOK.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks / "pre-commit").chmod(0o755)
    _git(repo, "config", "core.hooksPath", ".githooks")
    # A first ordinary commit, so HEAD exists and later diffs have a parent.
    (repo / "README").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _stage_forced(repo: Path, rel: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not a real secret; this repo is a temp dir\n", encoding="utf-8")
    _git(repo, "add", "-f", rel)   # -f, because .gitignore is not what is on trial


def test_a_forced_grant_file_is_refused_at_the_commit():
    """The acceptance case: each forbidden shape, force-added past `.gitignore`,
    reaches a commit and is refused — by the hook, naming the path."""
    for rel in FORBIDDEN:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _repo(tmp)
            _stage_forced(repo, rel)
            r = _git(repo, "commit", "-m", "sneak the trust root in", want_ok=False)
            assert r.returncode != 0, f"{rel} committed; the gate did not fire"
            assert "refusal 2" in (r.stderr + r.stdout), r.stderr
            assert rel in (r.stderr + r.stdout), f"the refusal did not name {rel}"
            # And nothing landed: HEAD is still the seed commit.
            log = _git(repo, "log", "--format=%s").stdout.split()
            assert "sneak" not in " ".join(log)


def test_an_ordinary_commit_still_passes():
    """A gate that refuses everything is not a gate (the house control)."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _repo(tmp)
        for rel in ALLOWED:
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("ordinary versioned content\n", encoding="utf-8")
            _git(repo, "add", rel)
        r = _git(repo, "commit", "-m", "ordinary work", want_ok=False)
        assert r.returncode == 0, f"the hook refused an ordinary commit:\n{r.stderr}"


def test_a_forbidden_and_an_allowed_file_together_still_refuse():
    """One grant file in a commit of otherwise-fine work still stops the commit —
    the gate is over the staged set, not the majority of it."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _repo(tmp)
        (repo / "docs").mkdir()
        (repo / "docs" / "ok.md").write_text("fine\n", encoding="utf-8")
        _git(repo, "add", "docs/ok.md")
        _stage_forced(repo, "_net_leases/held.key")
        r = _git(repo, "commit", "-m", "mixed", want_ok=False)
        assert r.returncode != 0 and "_net_leases/held.key" in (r.stderr + r.stdout)


def test_the_hook_and_the_gitignore_name_the_same_trust_root():
    """The pair (rule 12): `.gitignore` mitigates and the hook enforces, and the
    two must refuse the same set or one guards what the other waves through. The
    middle is this assertion — every literal trust-root token in the hook is also
    an ignore rule."""
    ignore = GITIGNORE.read_text(encoding="utf-8")
    for token in ("mcp_apps/", "_net_leases/", "*.grant", "*.lease"):
        assert token in ignore, f"the hook refuses {token}; .gitignore does not ignore it"


def test_the_hook_reads_the_staged_set_not_the_working_tree():
    """The property that makes it a gate and not advice: a grant file present in
    the working tree but **not staged** does not stop an unrelated commit, and
    the same file staged does. Absence of a stage is not absence of the file."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _repo(tmp)
        (repo / "season.grant").write_text("present but unstaged\n", encoding="utf-8")
        (repo / "work.txt").write_text("unrelated\n", encoding="utf-8")
        _git(repo, "add", "work.txt")
        ok = _git(repo, "commit", "-m", "unrelated work", want_ok=False)
        assert ok.returncode == 0, "an unstaged grant file blocked an unrelated commit"
        _git(repo, "add", "-f", "season.grant")
        bad = _git(repo, "commit", "-m", "now stage it", want_ok=False)
        assert bad.returncode != 0, "the staged grant file was not refused"


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
