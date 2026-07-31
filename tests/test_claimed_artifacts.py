"""A report that claims to ship an artifact must ship it.

`test_section_refs.py` checks the survey index against the tree in both
directions, because an allowlist that no longer matches the tree fails open
(ARCHITECTURE.md §16). That check covers the *reports*. It does not cover the
things a report says it produced — and scout-13 shipped a section titled
"Artifacts in this directory" naming two scripts that were not in the directory,
with its single strongest finding derived from one of them.

That is §18 item 0's defect ("an unverified table and a verified one look
identical") occurring inside the report about verifying verifiers, which makes
it the best available argument that the class needs a middle rather than care.

Scope, deliberately narrow: only files a report claims are *its own, here*.
The survey cites hundreds of filenames belonging to other repositories —
`knowledge.py`, `catalog.json`, `kart-sandbox.json` — and those are prior art,
correctly absent. The distinguishing signal is the artifacts section, not the
backticks.

Stdlib only. No network. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_claimed_artifacts.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SURVEY_DIR = ROOT / "docs" / "survey"

# "## 7 · Artifacts in this directory", "### Artifacts in this repo", etc.
_ARTIFACT_HEADING = re.compile(
    r"^(#{2,6})\s+.*artifacts?\s+in\s+this\s+(?:directory|repo(?:sitory)?)",
    re.IGNORECASE,
)
_ANY_HEADING = re.compile(r"^(#{1,6})\s")

# A bare filename in backticks: no directory separator, so it is being claimed
# as sitting beside the report rather than inside some other project.
_BARE_FILE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:py|sh|sql|json|ya?ml))`")

# Artifacts that were produced and deliberately not retained still have to be
# accounted for -- silently dropping one is the same defect as claiming one that
# never existed. A report may mark a line NOT RETAINED, which excuses the file
# and keeps the claim visible.
_NOT_RETAINED = re.compile(r"\bnot retained\b", re.IGNORECASE)


def artifact_claims(path: Path) -> tuple[set[str], set[str]]:
    """(claimed and expected present, claimed but marked not retained)."""
    present, excused = set(), set()
    lines = path.read_text(encoding="utf-8").splitlines()
    depth = None
    for line in lines:
        heading = _ANY_HEADING.match(line)
        if depth is not None and heading and len(heading.group(1)) <= depth:
            depth = None  # section ended
        start = _ARTIFACT_HEADING.match(line)
        if start:
            depth = len(start.group(1))
            continue
        if depth is None:
            continue
        for name in _BARE_FILE.findall(line):
            (excused if _NOT_RETAINED.search(line) else present).add(name)
    return present, excused


def all_claims() -> tuple[dict[str, str], set[str]]:
    """(filename -> claiming report, filenames excused as not retained)."""
    claimed, excused = {}, set()
    for report in sorted(SURVEY_DIR.glob("*.md")):
        here, gone = artifact_claims(report)
        for name in here:
            claimed[name] = report.name
        excused |= gone
    return claimed, excused


def shipped() -> set[str]:
    """Non-markdown files actually sitting in the survey directory."""
    return {p.name for p in SURVEY_DIR.iterdir() if p.is_file() and p.suffix != ".md"}


# --- the checks ------------------------------------------------------------


def test_claimed_artifacts_are_present():
    """The direction that has already failed once."""
    claimed, _ = all_claims()
    missing = {n: r for n, r in claimed.items() if n not in shipped()}
    assert not missing, "claimed but not in the tree: " + ", ".join(
        f"{n} (claimed by {r})" for n, r in sorted(missing.items())
    )


def test_shipped_artifacts_are_claimed():
    """The other direction. A script nobody points at is evidence of nothing,
    and will be deleted by the next person tidying up, taking a derivation with
    it. Same reasoning as the survey index being checked both ways."""
    claimed, excused = all_claims()
    orphans = shipped() - set(claimed) - excused
    assert not orphans, f"present but claimed by no report: {sorted(orphans)}"


def test_the_parser_finds_the_section_that_exists():
    """Guards the parser: a regex matching nothing would make both checks above
    pass vacuously, which is the failure this whole file is about."""
    claimed, excused = all_claims()
    assert claimed or excused, (
        "no artifact claims found in any report — parser broken? "
        "scout-13 has an 'Artifacts in this directory' section"
    )


def test_the_check_can_actually_fail():
    """ARCHITECTURE.md §10 and PROTECTED_AGENTS.md I-12: attempt the forbidden
    act and assert refusal. Point the parser at a report claiming a file that is
    not there and confirm it is seen."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        decoy = Path(td) / "scout-99-decoy.md"
        decoy.write_text(
            "# Decoy\n\n## 7 · Artifacts in this directory\n\n"
            "- `does_not_exist.py` — runnable, stdlib-only.\n",
            encoding="utf-8",
        )
        claimed, _ = artifact_claims(decoy)

    assert claimed == {"does_not_exist.py"}, f"parser missed the claim: {claimed}"
    assert "does_not_exist.py" not in shipped()


def test_the_section_boundary_holds():
    """The artifacts section must end at the next heading of the same level or
    higher. Without that the parser would swallow the rest of the document and
    demand every prior-art filename in the report — which would make the check
    so noisy it would be switched off, and a check that gets switched off is the
    same as no check."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "scout-98-probe.md"
        probe.write_text(
            "## 7 · Artifacts in this directory\n\n"
            "- `mine.py` — produced here.\n\n"
            "## 8 · Prior art\n\n"
            "- `someone_elses.py` — lives in another repository.\n",
            encoding="utf-8",
        )
        claimed, _ = artifact_claims(probe)

    assert claimed == {"mine.py"}, f"section boundary leaked: {claimed}"


def test_not_retained_excuses_a_file_without_hiding_the_claim():
    """A produced-then-discarded artifact stays on the record. Confirm the
    escape hatch works and that it does not simply make the claim vanish."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "scout-97-probe.md"
        probe.write_text(
            "## 7 · Artifacts in this directory\n\n"
            "- `kept.py` — runnable.\n"
            "- `thrown_away.py` — NOT RETAINED; the finding it produced is in §3.\n",
            encoding="utf-8",
        )
        claimed, excused = artifact_claims(probe)

    assert claimed == {"kept.py"}
    assert excused == {"thrown_away.py"}, "the discarded artifact left no trace"


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
