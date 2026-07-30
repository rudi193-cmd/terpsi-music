"""Every §N reference must resolve to a real heading.

CLAUDE.md is deliberately a pointer rather than a summary (see its header), and
section references are the only thing keeping it honest against the documents it
points at. A pointer nobody checks is a middle that cannot fail, which
ARCHITECTURE.md §16 argues is worse than no middle at all — so this is that check.

Stdlib only. No network. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_section_refs.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"
CAPABILITY_MAP = ROOT / "docs" / "CAPABILITY-MAP.md"
SENSITIVITY = ROOT / "docs" / "SENSITIVITY.md"
LANE_MODEL = ROOT / "docs" / "LANE-MODEL.md"
CLAUDE = ROOT / "CLAUDE.md"

# Documents that point outward for every §N and declare no numbered sections of
# their own, so a bare reference in them is unambiguously ARCHITECTURE.md's.
POINTERS = (SENSITIVITY, LANE_MODEL)

# "## 7. Authorization" / "### 7.4 The Ward Case, adopted" -> 7 / 7.4
_HEADING = re.compile(r"^#{2,6}\s+(\d+(?:\.\d+)*)[.\s]")

# "§7.4", "§15", and the leading number of "§7.4 W-2" (the clause id is not part
# of the section number).
_REF = re.compile(r"§(\d+(?:\.\d+)*)")

# A reference may name its document explicitly, in which case it wins over the
# citing file's default target.
_QUALIFIER = re.compile(
    r"\s*(?:of|in)\s+(?:the\s+)?(capability\s+map|architecture)", re.IGNORECASE
)

# "FERPA §99.32" cites a statute, not a heading here. An external citation is
# named by the all-caps token immediately preceding it; a bare §N is ours.
_STATUTE = re.compile(r"\b[A-Z]{3,}\s*$")


def headings(path: Path) -> set[str]:
    """Numbered section ids declared in a markdown file."""
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _HEADING.match(line)
        if m:
            found.add(m.group(1))
    return found


def references(path: Path, default: Path) -> list[tuple[int, str, Path]]:
    """(line number, section id, target document) for every §N in a file."""
    out = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in _REF.finditer(line):
            if _STATUTE.search(line[: m.start()]):
                continue  # FERPA §99.32 and friends — not our headings
            target = default
            q = _QUALIFIER.match(line, m.end())
            if q:
                named = q.group(1).lower()
                target = CAPABILITY_MAP if named.startswith("capability") else ARCHITECTURE
            out.append((lineno, m.group(1), target))
    return out


def unresolved(path: Path, default: Path) -> list[str]:
    """Human-readable failures, empty when every reference resolves."""
    known = {ARCHITECTURE: headings(ARCHITECTURE), CAPABILITY_MAP: headings(CAPABILITY_MAP)}
    bad = []
    for lineno, section, target in references(path, default):
        if section not in known[target]:
            bad.append(
                f"{path.name}:{lineno} cites §{section} — no such heading in {target.name}"
            )
    return bad


# --- the checks ------------------------------------------------------------


def test_architecture_has_numbered_sections():
    """Guards the parser itself: a regex that matched nothing would pass every
    other test in this file for the wrong reason."""
    found = headings(ARCHITECTURE)
    assert len(found) >= 15, f"only found {len(found)} numbered headings — parser broken?"
    assert "1" in found and "16" in found


def test_claude_md_references_resolve():
    """CLAUDE.md's pointers are its only tie to the canonical document."""
    bad = unresolved(CLAUDE, default=ARCHITECTURE)
    assert not bad, "\n".join(bad)


def test_architecture_self_references_resolve():
    bad = unresolved(ARCHITECTURE, default=ARCHITECTURE)
    assert not bad, "\n".join(bad)


def test_capability_map_references_resolve():
    bad = unresolved(CAPABILITY_MAP, default=CAPABILITY_MAP)
    assert not bad, "\n".join(bad)


def test_pointer_document_references_resolve():
    """SENSITIVITY.md and LANE-MODEL.md are canonical for their own subject and
    point outward for everything else, so every §N in them is ARCHITECTURE.md's."""
    bad = []
    for path in POINTERS:
        bad += unresolved(path, default=ARCHITECTURE)
    assert not bad, "\n".join(bad)


def test_pointer_documents_declare_no_numbered_sections():
    """The property that makes the test above safe.

    Default-routing sends a bare §N in these files to ARCHITECTURE.md. If one
    ever grew a "## 3. ..." of its own, a self-reference to §3 would silently
    resolve against ARCHITECTURE.md §3 (Topology) — passing, and pointing at
    the wrong document. They address by rung and by clause id precisely so the
    collision cannot arise, and this asserts it stays that way."""
    bad = []
    for path in POINTERS:
        found = headings(path)
        if found:
            bad.append(
                f"{path.name} declares numbered sections {sorted(found)} — a bare "
                "§N in it is now ambiguous. Address by rung or clause, or teach "
                "references() to route to it."
            )
    assert not bad, "\n".join(bad)


def test_the_check_can_actually_fail(tmp_path=None):
    """ARCHITECTURE.md §10 and PROTECTED_AGENTS.md I-12: a guard that cannot be
    shown to fail has not been shown to work. Point the checker at a file citing
    a section that does not exist and confirm it complains."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        decoy = Path(td) / "DECOY.md"
        decoy.write_text("A rule that points nowhere (§9999).\n", encoding="utf-8")
        bad = unresolved(decoy, default=ARCHITECTURE)
    assert len(bad) == 1, f"checker did not catch a dangling reference: {bad}"
    assert "9999" in bad[0]


def test_qualified_references_route_to_the_named_document():
    """'§18 of the capability map' must not be checked against ARCHITECTURE.md,
    which has no §18. Without this the qualifier handling could silently
    degrade to default-routing and nothing would notice."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "PROBE.md"
        probe.write_text("See §18 of the capability map.\n", encoding="utf-8")
        _, section, target = references(probe, default=ARCHITECTURE)[0]
    assert section == "18"
    assert target == CAPABILITY_MAP


def test_statute_citations_are_skipped_but_bare_refs_are_not():
    """The statute exclusion is itself a way for this checker to go quiet. A rule
    that swallowed every §N would make the whole file pass vacuously, so both
    halves are asserted: the statute is ignored, the bare reference is not."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "PROBE.md"
        probe.write_text(
            "FERPA §99.32 requires a disclosure record.\nBut §99.32 alone is ours.\n",
            encoding="utf-8",
        )
        refs = references(probe, default=ARCHITECTURE)
        bad = unresolved(probe, default=ARCHITECTURE)
    assert len(refs) == 1, f"expected the statute skipped and the bare ref kept, got {refs}"
    assert refs[0][0] == 2, "wrong reference survived the statute filter"
    assert len(bad) == 1 and "9999" not in bad[0]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}\n{exc}\n")
    raise SystemExit(1 if failures else 0)
