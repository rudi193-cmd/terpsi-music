"""The craft checker does what §24 says, and refuses what §24 forbids.

Two classes of test here. The first is ordinary: the phonetics and the checks
behave on known inputs, including the specific false positives the first
working version produced — a copyright notice scanned as a verse, "brought"
flagged as an unsingable cluster, "waits" and "park" called a rhyme. Those are
regressions now, because each one was found by running the thing rather than
by reading it.

The second class guards the constraints. §24's binding rule is *diagnose,
never score*, and a scoring feature would be a natural, well-meant addition
that nothing else would catch. §6 of the architecture requires the core be
unable to reach the network. Both are asserted structurally rather than
trusted.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_craft.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from craft.checks import (  # noqa: E402
    Report,
    check_meter,
    check_rhyme,
    check_sing,
    check_structure,
    load_intents,
    run_all,
    run_diff,
)
from craft.text import (  # noqa: E402
    consonant_runs,
    line_syllables,
    parse,
    rhymes,
    stress,
    syllables,
)

SONG = ROOT / "lyrics" / "get-ready.txt"

TWO_VERSES = """
VERSE 1
    Frost on the lot at six
    Cold in the valves and keys

VERSE 2
    Somebody's father waits
    Down where the buses park and turn and wait
"""


# --- phonetics --------------------------------------------------------------


def test_syllables_on_known_words():
    for word, n in [("frost", 1), ("the", 1), ("valves", 1), ("nobody", 3),
                    ("eleven", 3), ("somebody's", 3), ("hazards", 2),
                    ("plastic", 2), ("couldn't", 2), ("go", 1)]:
        assert syllables(word) == n, f"{word}: got {syllables(word)}, want {n}"


def test_the_opening_line_scans_as_six():
    lyric, _ = parse(TWO_VERSES)
    assert line_syllables(lyric.sections[0].lines[0]) == 6


def test_stress_is_unknown_rather_than_guessed():
    """CLAUDE.md rule 13. A polysyllable needs a dictionary this package does
    not ship, so it returns None and callers decline."""
    assert stress("the") is False
    assert stress("frost") is True
    assert stress("somebody") is None


def test_rhyme_pairs_that_matter():
    assert rhymes("keys", "trees") == "perfect"
    assert rhymes("park", "dark") == "perfect"
    assert rhymes("tight", "white") == "perfect"
    assert rhymes("park", "work") == "slant"
    # Regression: "ei" was absent from the vowel table, so "eight" fell through
    # to short-E and the checker reported that the song's own hook did not
    # rhyme with its own third line.
    assert rhymes("eight", "wait") == "perfect"


def test_rhyme_pairs_the_loose_version_got_wrong():
    """Regressions. Both of these were reported as rhymes by the first working
    version, which was enough to call every verse in a correctly-schemed song
    inconsistent."""
    assert rhymes("waits", "park") == "none", "shared vowel class is assonance"
    assert rhymes("hat", "tight") == "none", "one shared final consonant is not a rhyme"
    assert rhymes("keys", "yet") == "none", "long e and short e are different vowels"


def test_clusters_are_phonetic_not_orthographic():
    """Regression. "ght" is three letters and one sound; the letter-counting
    version flagged brought, right and tight as unsingable."""
    assert consonant_runs("brought") == []
    assert consonant_runs("watch") == [], "tch is one sound"
    assert consonant_runs("street") == [], "an initial cluster of three is ordinary"
    assert consonant_runs("couldn't") == [], "an apostrophe marks an elided vowel"
    assert consonant_runs("hands") == ["nds"]
    assert consonant_runs("months") == ["nths"], "and it must be spelled back out"


# --- parsing ----------------------------------------------------------------


def test_prose_headings_are_not_verses():
    """Regression, and the worst one. The first run scanned a copyright notice
    for rhyme scheme and reported that it had an inconsistent one."""
    text = """
RIGHTS
    None subsist, so far as can be determined
    US copyright requires a human author

VERSE 1
    Frost on the lot at six
"""
    lyric, skipped = parse(text)
    assert [s.label for s in lyric.sections] == ["VERSE 1"]
    assert skipped == ["RIGHTS"]


def test_skipped_headings_are_reported_not_dropped():
    report = run_all(SONG.read_text(encoding="utf-8"))
    assert any("Read as prose" in n for n in report.notes)


def test_stanzas_split_on_blank_lines():
    lyric, _ = parse("BRIDGE\n    one\n    two\n\n    three\n    four\n")
    assert [len(s) for s in lyric.sections[0].stanzas()] == [2, 2]


# --- the checks -------------------------------------------------------------


def test_meter_catches_a_line_that_scans_differently():
    lyric, _ = parse(TWO_VERSES)
    findings = check_meter(lyric)
    assert len(findings) == 1, findings
    assert findings[0].check == "METER"
    assert "VERSE 2" in findings[0].where


def test_meter_is_silent_when_sections_agree():
    lyric, _ = parse(
        "VERSE 1\n    Frost on the lot at six\nVERSE 2\n    Cold in the valves and keys\n"
    )
    assert check_meter(lyric) == []


def test_structure_catches_a_final_chorus_that_repeats():
    text = ("CHORUS\n    Ready on the eight\nBRIDGE\n    Nine months\n"
            "CHORUS\n    Ready on the eight\n")
    lyric, _ = parse(text)
    findings, _ = check_structure(lyric)
    assert any(f.check == "STRUCTURE" for f in findings), findings


def test_structure_is_silent_when_the_last_chorus_varies():
    text = ("CHORUS\n    Hands cold, don't wait\nBRIDGE\n    Nine months\n"
            "CHORUS\n    Hands warm, don't wait\n")
    lyric, _ = parse(text)
    findings, _ = check_structure(lyric)
    assert not [f for f in findings if f.check == "STRUCTURE"]


def test_rhyme_does_not_compare_a_bridge_to_itself():
    """A bridge's two halves are stanzas of one section and owe each other
    nothing. Only stanza n of one VERSE against stanza n of another must agree."""
    text = ("BRIDGE\n    nine months\n    eleven minutes\n"
            "\n    still out there parked\n    through the fence\n")
    lyric, _ = parse(text)
    findings, _ = check_rhyme(lyric)
    assert findings == [], findings


def test_the_song_in_the_repo_has_consistent_verse_schemes():
    """v3 regularised all three verses to ABCB. If a later edit breaks one,
    this is where it shows up."""
    lyric, _ = parse(SONG.read_text(encoding="utf-8"))
    _, notes = check_rhyme(lyric)
    verses = [n for n in notes if n.startswith("VERSE")]
    assert len(verses) == 3, verses
    assert all(n.endswith("ABCB") for n in verses), verses


def test_sing_flags_the_last_note_only_once():
    """Applied per section it fires on most of English. Only the final note of
    the song is likely to be held long enough to matter."""
    text = "VERSE 1\n    ends on a stop\nCHORUS\n    also ends on a cut\n"
    lyric, _ = parse(text)
    tails = [f for f in check_sing(lyric) if f.id.endswith(":tail")]
    assert len(tails) <= 1, tails


# --- the constraints --------------------------------------------------------


def test_finding_ids_are_unique():
    """Regression. Two sections both headed CHORUS produced identical ids, so a
    declared intent silently applied to whichever one the reader did not mean."""
    r = run_all(SONG.read_text(encoding="utf-8"))
    ids = [f.id for f in r.findings] + [f.id for f, _ in r.declared]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, dupes


def test_nothing_here_scores_anything():
    """§24's binding rule: diagnose, never score. A total, a grade, or a
    percentage would be a natural feature request and this is the only thing
    standing in its way."""
    banned = re.compile(
        r"\b(score|scored|scoring|grade|graded|rating|rank|ranked|"
        r"percentile|out of ten|overall quality)\b", re.I
    )
    for path in sorted((ROOT / "craft").glob("*.py")):
        src = path.read_text(encoding="utf-8")
        code = "\n".join(
            line for line in src.splitlines()
            if not line.strip().startswith("#")
        )
        # Docstrings state the prohibition, so strip them before searching.
        tree = ast.parse(src)
        docs = {ast.get_docstring(n) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef))}
        for d in docs:
            if d:
                code = code.replace(d, "")
        hits = banned.findall(code)
        assert not hits, f"{path.name} looks like it scores something: {hits}"

    assert not any(
        f.name in ("score", "grade", "rating", "rank")
        for f in Report.__dataclass_fields__.values()
    )


def test_a_report_has_no_totals_field():
    r = run_all(SONG.read_text(encoding="utf-8"))
    assert set(vars(r)) == {"findings", "declared", "notes", "unavailable"}


def test_the_core_cannot_reach_the_network():
    """§6 of the architecture, inner ring. terpsi-music must ship its own
    check because the fleet's canonical one is not reachable from here."""
    forbidden = {
        "socket", "http", "urllib", "requests", "httpx", "aiohttp", "ftplib",
        "smtplib", "telnetlib", "asyncio", "subprocess", "ssl", "xmlrpc",
    }
    bad = []
    for path in sorted((ROOT / "craft").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                if n.split(".")[0] in forbidden:
                    bad.append(f"{path.name} imports {n}")
    assert not bad, "\n".join(bad)


def test_the_purity_check_can_actually_fail():
    forbidden = {"socket", "urllib"}
    tree = ast.parse("import urllib.request\n")
    hit = [
        a.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for a in node.names if a.name.split(".")[0] in forbidden
    ]
    assert hit == ["urllib.request"]


# --- intent and revision ----------------------------------------------------


def test_a_declared_finding_moves_but_is_not_hidden():
    """§24: the declaration is the artifact worth keeping, so a declared
    finding is reported separately rather than suppressed."""
    text = SONG.read_text(encoding="utf-8")
    plain = run_all(text)
    assert plain.findings, "expected the live song to produce findings"

    target = plain.findings[0]
    declared = run_all(text, {target.id: "the cluster is the point"})
    assert target.id not in {f.id for f in declared.findings}
    assert target.id in {f.id for f, _ in declared.declared}
    assert declared.declared[0][1] == "the cluster is the point"
    assert len(declared.findings) + len(declared.declared) == len(plain.findings)


def test_intent_file_parsing():
    got = load_intents("# a note\n\nRHYME:VERSE-3:S0  deliberate\nSING:X\n")
    assert got == {"RHYME:VERSE-3:S0": "deliberate", "SING:X": "(no reason given)"}


def test_an_id_containing_a_hash_survives_the_comment_stripper():
    """Regression, and a collision between two features added an hour apart.
    Finding ids use `#` to distinguish repeated sections; the intent parser used
    `#` for inline comments. Every declared intent on a second CHORUS was
    silently truncated to SING:CHORUS and never applied."""
    got = load_intents("SING:CHORUS#2:S0:L2:hands  deliberate\n")
    assert got == {"SING:CHORUS#2:S0:L2:hands": "deliberate"}


def test_every_declared_intent_actually_matches_a_finding():
    """The failure above was invisible because a mis-typed or mis-parsed id just
    leaves the finding open. This asserts the repo's own intent file applies in
    full, so a future id change cannot quietly orphan it."""
    text = SONG.read_text(encoding="utf-8")
    intents = load_intents((ROOT / "lyrics" / "get-ready.intent").read_text(encoding="utf-8"))
    r = run_all(text, intents)
    applied = {f.id for f, _ in r.declared}
    orphaned = set(intents) - applied
    assert not orphaned, f"declared but matched nothing: {sorted(orphaned)}"


def test_revision_reports_both_directions():
    """A revision that fixes two things and breaks one has done that. Reporting
    only the wins is flattering rather than teaching."""
    before = "VERSE 1\n    Frost on the lot at six\nVERSE 2\n    Somebody waits here now\n"
    after = "VERSE 1\n    Frost on the lot at six\nVERSE 2\n    Somebody father waits alone tonight\n"
    introduced, notes = run_diff(before, after)
    joined = "\n".join(notes)
    assert "resolved" in joined and "introduced" in joined
    assert any(n.startswith("  + ") for n in notes)
    assert any(n.startswith("  - ") for n in notes)


def test_an_unparseable_file_is_unavailable_not_clean():
    """§6: absence surfaces as unknown, never as a result. A file with no
    sections must not report zero findings as though it passed."""
    r = run_all("just some prose with no headers at all\n")
    assert r.unavailable and not r.findings
    assert "unavailable" in r.unavailable[0]


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
