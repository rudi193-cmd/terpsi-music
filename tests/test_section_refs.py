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
CRAFT_SOURCES = ROOT / "docs" / "CRAFT-SOURCES.md"
CLAUDE = ROOT / "CLAUDE.md"
SURVEY = ROOT / "docs" / "OPEN-SOURCE-SURVEY.md"
SURVEY_DIR = ROOT / "docs" / "survey"
DOCS_DIR = ROOT / "docs"

#: Docs whose references are checked by a test of their own above. Everything
#: else in `docs/` is swept by `test_other_docs_references_resolve`, so a new
#: document cannot arrive as a pointer nobody verifies -- which is the failure
#: this file exists to prevent, applied to itself.
SEPARATELY_CHECKED = {ARCHITECTURE, CAPABILITY_MAP, SURVEY}

# "`scout-07-audio-score.md`" in the survey's index table.
_SCOUT_FILE = re.compile(r"`(scout-\d{2}-[a-z0-9-]+\.md)`")

#: Where a bare §N in a swept document points when the line does not name a
#: target itself. ARCHITECTURE.md is the fallback and is right for almost
#: everything; the exceptions are listed here because routing them wrong is
#: silent — CRAFT-SOURCES.md is *about* §24 of the capability map, a section
#: ARCHITECTURE.md does not have, so the fallback would fail it on every line.
#:
#: This table and the sweep below are one mechanism. Three branches each
#: shipped a different partial version of it: an enumerated POINTERS tuple
#: (docs/SENSITIVITY.md's branch), a glob sweep with a hardcoded architecture
#: default (docs/PLAN-GUARDIANSHIP.md's), and a single named check for
#: docs/EXTERNAL-ARM.md (docs/survey/trigger_mutation_demo.py's). The sweep is
#: the general form and the enumerations are subsumed by it; the routing that
#: only the enumeration had is preserved here. §16 -- the pair got its middle
#: rather than a fourth copy.
DEFAULT_TARGETS = {
    CRAFT_SOURCES: CAPABILITY_MAP,
}

#: Swept docs that declare numbered sections of their own. A bare §N in one of
#: these is ambiguous: it default-routes outward, but the document has an §N
#: too, so a self-reference resolves against the wrong file and *passes*.
#: Neither entry self-references today (checked below), and the registry exists
#: so a third cannot arrive without someone deciding it is safe.
SELF_NUMBERED = {
    ROOT / "docs" / "EXTERNAL-ARM.md",
    ROOT / "docs" / "PLAN-GUARDIANSHIP.md",
    ROOT / "docs" / "SKINS.md",
}

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


def bare_references(path: Path) -> list[tuple[int, str]]:
    """(line number, section id) for every §N that does *not* name its document.

    `references()` reports where a reference routed; this reports whether the
    text said so. A qualified "§6 of the architecture" and a bare "§6" route to
    the same place and are not the same claim — only the second one is relying
    on a default.
    """
    out = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in _REF.finditer(line):
            if _STATUTE.search(line[: m.start()]):
                continue
            if _QUALIFIER.match(line, m.end()):
                continue
            out.append((lineno, m.group(1)))
    return out


def indexed_scout_files(path: Path) -> set[str]:
    """Scout report filenames the survey's index claims exist."""
    return set(_SCOUT_FILE.findall(path.read_text(encoding="utf-8")))


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


def test_survey_references_resolve():
    """OPEN-SOURCE-SURVEY.md points at both canonical documents and is checked on
    the same terms as CLAUDE.md — otherwise it is a third pointer nobody verifies.
    Note it reserves §N for the canonical docs: its own parts are cited as
    "part 4" / "finding 1.2", so that one sigil keeps one meaning (§16)."""
    bad = unresolved(SURVEY, default=ARCHITECTURE)
    assert not bad, "\n".join(bad)


def other_docs() -> list[Path]:
    return sorted(p for p in DOCS_DIR.glob("*.md") if p not in SEPARATELY_CHECKED)


def target_for(path: Path) -> Path:
    """The document a bare §N in `path` refers to."""
    return DEFAULT_TARGETS.get(path, ARCHITECTURE)


def test_other_docs_references_resolve():
    """Any other document in `docs/` is held to the same terms.

    Without this, adding a file with §-references creates exactly the pair
    ARCHITECTURE.md §16 warns about: a pointer and a canonical document with
    nothing reconciling them. The sweep is the middle."""
    bad = []
    for path in other_docs():
        bad.extend(unresolved(path, default=target_for(path)))
    assert not bad, "\n".join(bad)


def test_the_docs_sweep_is_not_vacuous():
    """A glob that matched nothing would pass the test above for the wrong
    reason -- the same trap `test_architecture_has_numbered_sections` guards."""
    found = other_docs()
    assert found, "no other docs found -- glob broken, or the sweep is decorative"
    cited = sum(len(references(p, default=target_for(p))) for p in found)
    assert cited, f"{len(found)} docs swept and not one reference among them"


def test_the_routing_table_names_only_docs_that_exist():
    """DEFAULT_TARGETS is an allowlist keyed on paths, and §16's objection to
    allowlists is that they fail open when the tree moves past them. A rename
    would leave the entry matching nothing and the document silently back on
    the architecture fallback — passing, and pointing at the wrong file."""
    missing = [p.name for p in DEFAULT_TARGETS if not p.exists()]
    assert not missing, f"routing entries for absent docs: {missing}"
    assert set(DEFAULT_TARGETS) <= set(other_docs()), (
        "a routed document is not in the sweep, so its routing does nothing"
    )


def test_routing_is_load_bearing():
    """The override table earns its place only if the fallback would be wrong.
    If this ever passes trivially, delete the table rather than keep a middle
    that cannot fail."""
    for path, target in DEFAULT_TARGETS.items():
        assert not unresolved(path, default=target), f"{path.name} fails its own route"
        assert unresolved(path, default=ARCHITECTURE), (
            f"{path.name} resolves against ARCHITECTURE.md too — its entry in "
            "DEFAULT_TARGETS is decorative"
        )


def test_survey_index_matches_the_tree_in_both_directions():
    """ARCHITECTURE.md §16: an allowlist that no longer matches the tree fails
    open. The survey's index is that allowlist, so it is checked both ways — a
    named file that is gone leaves a dangling citation, and a present file that
    is unnamed is evidence nothing points at."""
    named = indexed_scout_files(SURVEY)
    present = {p.name for p in SURVEY_DIR.glob("scout-*.md")}

    assert named, "survey index named no scout files — regex broken?"
    assert not (named - present), f"indexed but missing: {sorted(named - present)}"
    assert not (present - named), f"present but unindexed: {sorted(present - named)}"


def test_the_index_check_can_actually_fail():
    """The both-directions check passes vacuously if the regex matches nothing,
    so confirm it catches a name with no file behind it."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        decoy = Path(td) / "DECOY.md"
        decoy.write_text("See `scout-99-does-not-exist.md`.\n", encoding="utf-8")
        named = indexed_scout_files(decoy)
    present = {p.name for p in SURVEY_DIR.glob("scout-*.md")}
    assert named == {"scout-99-does-not-exist.md"}
    assert named - present, "checker did not notice a file that is not there"


# Two tests stood here and were retired into the sweep above, status first:
#
#   test_pointer_document_references_resolve  — RETIRED, superseded by
#       test_other_docs_references_resolve. It checked five named documents;
#       the sweep checks every document in `docs/`, which is a superset. Its
#       one non-redundant part was the per-document routing, now DEFAULT_TARGETS
#       and covered by test_routing_is_load_bearing. Nothing it asserted is
#       unasserted; the stub is this comment because a reader arriving from the
#       branch that added it needs to be told where it went (§16).
#
#   test_external_arm_references_resolve — RETIRED, same successor, no
#       non-redundant part at all: EXTERNAL-ARM.md is in `docs/` and the sweep
#       reaches it. Keeping it would have made the third copy of one check.
#
# The property that made the retired pair safe is generalized below rather than
# dropped with them.


def test_self_numbered_docs_are_registered():
    """A swept document that declares its own numbered sections makes every
    bare §N in it ambiguous: the reference default-routes outward, and the
    document has an §N of its own, so a self-reference resolves against the
    wrong file and *passes*. That is the failure this file exists to catch,
    committed by this file.

    The retired pointer-doc guard asserted no swept document had this shape.
    That precondition is now false — EXTERNAL-ARM.md and PLAN-GUARDIANSHIP.md
    both arrived with numbered sections — so the assertion becomes a registry:
    a document with the shape is allowed, and a *new* one cannot appear without
    someone deciding it is safe."""
    unregistered = sorted(
        p.name for p in other_docs() if headings(p) and p not in SELF_NUMBERED
    )
    assert not unregistered, (
        f"{unregistered} declare numbered sections and are not in SELF_NUMBERED. "
        "A bare §N in them is ambiguous. Either address by clause id instead, "
        "qualify the references, or register the file after checking it does "
        "not cite its own sections bare."
    )


def test_registered_docs_do_not_cite_their_own_sections_bare():
    """The check the registry is worth having. Registration says the ambiguity
    was considered, not that it is harmless — so the collision itself is
    asserted against, per document, on every run."""
    bad = []
    for path in sorted(SELF_NUMBERED):
        if not path.exists():
            continue
        own = headings(path)
        for lineno, section in bare_references(path):
            if section in own:
                bad.append(
                    f"{path.name}:{lineno} cites a bare §{section}, which is also "
                    f"one of its own headings — it routes to "
                    f"{target_for(path).name}, and nothing in the text says that "
                    "is what was meant. Qualify it ('§N of the architecture')."
                )
    assert not bad, "\n".join(bad)


def test_the_self_reference_guard_can_fail():
    """§10 and rule 19: the guard above passes today, which is exactly when a
    guard needs to be shown capable of failing. Feed it the shape it is looking
    for and confirm it is seen — and confirm the qualified form is not, since a
    guard that flags both would just be noise someone switches off."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "PROBE.md"
        probe.write_text(
            "## 6. Sequencing\n\nAs §6 describes.\nAs §6 of the architecture describes.\n",
            encoding="utf-8",
        )
        own = headings(probe)
        collisions = [(n, s) for n, s in bare_references(probe) if s in own]

    assert own == {"6"}, f"heading parser missed the probe's section: {own}"
    assert collisions == [(3, "6")], (
        f"expected the bare §6 caught and the qualified one passed, got {collisions}"
    )


def test_the_self_numbered_registry_is_not_stale():
    """SELF_NUMBERED is an allowlist, and §16's objection applies to it as much
    as to any other: an entry for a document that no longer has the shape is a
    permission nobody revoked."""
    stale = sorted(
        p.name for p in SELF_NUMBERED if not p.exists() or not headings(p)
    )
    assert not stale, (
        f"{stale} are registered as self-numbered and are not (or are gone). "
        "Drop the entry — a stale allowlist is the failure mode, not the fix."
    )


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
