"""The eight text-only checks.

Each returns findings — a place and a description of what is there. None
returns a score, a grade, a total, or a verdict about quality. §24 of the
capability map calls that out as the binding constraint and
`tests/test_craft.py` asserts it structurally, because it is the rule most
likely to be eroded by a well-meaning feature request.

Every finding carries a stable id so a writer can declare it intentional.
A declared finding is not suppressed — it moves to a separate list, because
the declaration is the artifact worth keeping.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from craft.text import (
    ABSTRACT_WORDS,
    FUNCTION_WORDS,
    Line,
    Lyric,
    Section,
    consonant_runs,
    last_word,
    line_syllables,
    parse,
    rhymes,
    stress_pattern,
    syllables,
)

CHECKS = ("METER", "STRUCTURE", "PARITY", "RHYME", "CONCRETE", "SING")
DIFF_CHECKS = ("DIFF", "DELTA")


@dataclass(frozen=True)
class Finding:
    check: str
    id: str
    where: str
    message: str
    line: int | None = None

    def __str__(self) -> str:
        at = f" (line {self.line})" if self.line else ""
        return f"[{self.id}] {self.where}{at}\n    {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    declared: list[tuple[Finding, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    unavailable: list[str] = field(default_factory=list)


def _fid(check: str, section: Section, stanza: int | None = None,
         index: int | None = None) -> str:
    parts = [check, section.id]
    if stanza is not None:
        parts.append(f"S{stanza}")
    if index is not None:
        parts.append(f"L{index}")
    return ":".join(parts)


def _content_words(line: Line) -> list[str]:
    return [w for w in line.words() if w.lower().strip("'") not in FUNCTION_WORDS]


# --- 1. METER ---------------------------------------------------------------


def check_meter(lyric: Lyric) -> list[Finding]:
    """Corresponding lines across sections of one kind should scan alike.

    This is the text-only half of prosody. Checking stress against a beat
    needs a melody (the seam checks, §18 item 7). What text alone can say is
    whether verse 3 line 2 scans like verse 1 line 2 — and if it does not, it
    will fight whatever melody is written over it.

    Comparative by construction, so a systematic error in the syllable counter
    cancels between the lines being compared.
    """
    out = []
    for kind in lyric.kinds():
        group = lyric.of_kind(kind)
        if len(group) < 2:
            continue
        by_position: dict[tuple[int, int], list[tuple[Section, Line, int]]] = {}
        for sec in group:
            for line in sec.lines:
                key = (line.stanza, line.index)
                by_position.setdefault(key, []).append((sec, line, line_syllables(line)))

        for (stanza, index), rows in sorted(by_position.items()):
            if len(rows) < 2:
                continue
            counts = [n for _, _, n in rows]
            common = Counter(counts).most_common(1)[0][0]
            for sec, line, n in rows:
                if n != common:
                    out.append(Finding(
                        check="METER",
                        id=_fid("METER", sec, stanza, index),
                        where=f"{sec.label}, line {index + 1}",
                        line=line.number,
                        message=(
                            f"{n} syllables where the other {kind} sections have "
                            f"{common}. Either regularise it or the melody has to "
                            f"absorb the difference."
                        ),
                    ))
    return out


# --- 2. STRUCTURE -----------------------------------------------------------


def check_structure(lyric: Lyric) -> tuple[list[Finding], list[str]]:
    """Section order, time-to-hook, and whether the last chorus does any work."""
    out, notes = [], []
    if not lyric.sections:
        return out, notes

    notes.append("Order: " + " → ".join(s.label for s in lyric.sections))

    hooks = [s for s in lyric.sections if s.kind == "CHORUS"]
    if hooks:
        before = sum(len(s.lines) for s in lyric.sections[:hooks[0].order])
        notes.append(f"Time to hook: {before} lines before the first CHORUS.")

        if len(hooks) > 1:
            first, last = hooks[0], hooks[-1]
            if first.body() == last.body():
                out.append(Finding(
                    check="STRUCTURE",
                    id=_fid("STRUCTURE", last),
                    where=last.label,
                    line=last.lines[0].number if last.lines else None,
                    message=(
                        "The final chorus is identical to the first. A bridge "
                        "leaves something unresolved so the last chorus can "
                        "resolve it; an exact repeat declines the offer."
                    ),
                ))
    else:
        notes.append("No section named CHORUS — hook checks skipped.")

    for kind in lyric.kinds():
        lengths = {len(s.lines) for s in lyric.of_kind(kind)}
        if len(lengths) > 1:
            notes.append(
                f"{kind} sections differ in length: {sorted(lengths)} lines."
            )
    return out, notes


# --- 3. PARITY --------------------------------------------------------------


def check_parity(lyric: Lyric) -> tuple[list[Finding], list[str]]:
    """Even line groups resolve; odd ones propel. Neither is a defect."""
    out, notes = [], []
    shapes = []
    for sec in lyric.sections:
        for n, stanza in enumerate(sec.stanzas()):
            count = len(stanza)
            shapes.append(f"{sec.label}{'' if n == 0 else f'/{n}'}={count}")

            same_kind = lyric.of_kind(sec.kind)
            if len(same_kind) > 1:
                others = [
                    len(st) for other in same_kind if other is not sec
                    for i, st in enumerate(other.stanzas()) if i == n
                ]
                if others and all(o % 2 != count % 2 for o in others):
                    out.append(Finding(
                        check="PARITY",
                        id=_fid("PARITY", sec, n),
                        where=f"{sec.label}, stanza {n + 1}",
                        line=stanza[0].number,
                        message=(
                            f"{count} lines where the other {sec.kind} sections "
                            f"have {others[0]}. Odd groups push forward and even "
                            f"ones settle, so this section resolves differently "
                            f"from its siblings."
                        ),
                    ))
    if shapes:
        notes.append("Line groups: " + ", ".join(shapes))

    last = lyric.sections[-1] if lyric.sections else None
    if last and last.stanzas() and len(last.stanzas()[-1]) % 2 == 1:
        notes.append(
            f"The song closes on an odd group ({len(last.stanzas()[-1])} lines) "
            "— unresolved by construction. Usually deliberate at the end."
        )
    return out, notes


# --- 4. RHYME ---------------------------------------------------------------


def _scheme(stanza: list[Line]) -> tuple[str, list[str]]:
    """(scheme string, per-line rhyme type against its scheme partner)."""
    letters, kinds = [], []
    endings: list[tuple[str, str]] = []   # (letter, word)
    nxt = ord("A")
    for line in stanza:
        w = last_word(line)
        if w is None:
            letters.append("-")
            kinds.append("unknown")
            continue
        placed = None
        for letter, prev in endings:
            r = rhymes(prev, w)
            if r == "perfect":
                placed, kind = letter, "perfect"
                break
            if r == "slant" and placed is None:
                placed, kind = letter, "slant"
        if placed is None:
            placed = chr(nxt)
            nxt += 1
            kind = "-"
        letters.append(placed)
        kinds.append(kind)
        endings.append((placed, w))
    return "".join(letters), kinds


def check_rhyme(lyric: Lyric) -> tuple[list[Finding], list[str]]:
    """Scheme and rhyme type, and whether sibling sections agree on them."""
    out, notes = [], []
    # Keyed by (kind, stanza index): a bridge's first and second halves are
    # stanzas of one section and have no obligation to match each other. What
    # must agree is verse 1's first stanza with verse 2's first stanza.
    by_kind: dict[tuple[str, int], list[tuple[Section, int, str]]] = {}

    for sec in lyric.sections:
        for n, stanza in enumerate(sec.stanzas()):
            if len(stanza) < 2:
                continue
            scheme, kinds = _scheme(stanza)
            by_kind.setdefault((sec.kind, n), []).append((sec, n, scheme))
            slants = [i for i, k in enumerate(kinds) if k == "slant"]
            notes.append(
                f"{sec.label} stanza {n + 1}: {scheme}"
                + (f" (slant at line {', '.join(str(i + 1) for i in slants)})" if slants else "")
            )

    for (kind, _n), rows in by_kind.items():
        if len(rows) < 2:
            continue
        schemes = Counter(s for _, _, s in rows)
        common = schemes.most_common(1)[0][0]
        for sec, n, scheme in rows:
            if scheme != common:
                out.append(Finding(
                    check="RHYME",
                    id=_fid("RHYME", sec, n),
                    where=f"{sec.label}, stanza {n + 1}",
                    line=sec.stanzas()[n][0].number,
                    message=(
                        f"Scheme {scheme} where the other {kind} sections use "
                        f"{common}. A scheme that appears in one verse and not "
                        f"its siblings reads as a lapse rather than a choice."
                    ),
                ))
    return out, notes


# --- 5. CONCRETE ------------------------------------------------------------


def check_concrete(lyric: Lyric) -> tuple[list[Finding], list[str]]:
    """Abstraction density. The crudest of the eight, and it says so."""
    out, notes = [], []
    for sec in lyric.sections:
        total = abstract = 0
        for line in sec.lines:
            content = _content_words(line)
            if not content:
                continue
            total += len(content)
            hits = [w for w in content if w.lower().strip("'") in ABSTRACT_WORDS]
            abstract += len(hits)
            if hits and len(hits) == len(content):
                out.append(Finding(
                    check="CONCRETE",
                    id=_fid("CONCRETE", sec, line.stanza, line.index),
                    where=f"{sec.label}, line {line.index + 1}",
                    line=line.number,
                    message=(
                        f"Every content word here names a state rather than a "
                        f"thing ({', '.join(hits)}). A line that states the "
                        f"feeling asks the listener to take it on trust."
                    ),
                ))
        if total:
            notes.append(
                f"{sec.label}: {abstract}/{total} content words abstract."
            )
    return out, notes


# --- 6. SING ----------------------------------------------------------------


_PLOSIVES = ("p", "t", "k", "b", "d", "g")


def check_sing(lyric: Lyric) -> list[Finding]:
    """What the mouth has to do. Partial without pitch, and useful anyway."""
    out = []
    for sec in lyric.sections:
        for line in sec.lines:
            words = line.words()
            for w in words:
                runs = consonant_runs(w)
                if runs:
                    out.append(Finding(
                        check="SING",
                        id=_fid("SING", sec, line.stanza, line.index) + f":{w.lower()}",
                        where=f"{sec.label}, line {line.index + 1}",
                        line=line.number,
                        message=(
                            f'"{w}" carries the cluster "{runs[0]}". Clusters do '
                            f"not survive speed; check it against the tempo."
                        ),
                    ))

    # The last note of the song is the one most likely to be held, so it is the
    # only place a closing stop is worth raising. Applied per section it fires
    # on most of English and teaches nobody anything.
    if lyric.sections and lyric.sections[-1].lines:
        sec = lyric.sections[-1]
        line = sec.lines[-1]
        words = line.words()
        tail = words[-1].lower().rstrip("'s") if words else ""
        if tail.endswith(_PLOSIVES):
            out.append(Finding(
                check="SING",
                id=_fid("SING", sec, line.stanza, line.index) + ":tail",
                where=f"{sec.label}, last line of the song",
                line=line.number,
                message=(
                    f'The song ends on "{words[-1]}", closing on a stop. A held '
                    f"final note wants an open vowel; this one cuts. Fine if the "
                    f"ending is meant to be abrupt."
                ),
            ))
    return out


# --- 7 & 8. DIFF and DELTA --------------------------------------------------


def _key(f: Finding) -> tuple[str, str]:
    return (f.check, f.id)


def run_diff(before: str, after: str) -> tuple[list[Finding], list[str]]:
    """Draft to draft: what moved, and what it did to the findings.

    §24: revision is where the craft lives and the first draft never is. This
    reports the delta in both directions — resolved *and* introduced — because
    a revision that fixes two things and breaks one has done that, and a tool
    reporting only the wins is flattering rather than teaching.
    """
    old, _ = parse(before)
    new, _ = parse(after)
    old_report, new_report = run_all(before), run_all(after)
    old_ids = {_key(f): f for f in old_report.findings}
    new_ids = {_key(f): f for f in new_report.findings}

    notes: list[str] = []
    old_lines = {" ".join(l.text.split()).lower()
                 for s in old.sections for l in s.lines}
    new_lines = {" ".join(l.text.split()).lower()
                 for s in new.sections for l in s.lines}
    added, removed = new_lines - old_lines, old_lines - new_lines
    kept = len(new_lines & old_lines)
    notes.append(
        f"Lines: {len(added)} new, {len(removed)} gone, {kept} unchanged."
    )
    for text in sorted(removed):
        notes.append(f"  - {text}")
    for text in sorted(added):
        notes.append(f"  + {text}")

    resolved = [f for k, f in old_ids.items() if k not in new_ids]
    introduced = [f for k, f in new_ids.items() if k not in old_ids]
    persisting = [f for k, f in new_ids.items() if k in old_ids]

    notes.append(
        f"Findings: {len(resolved)} resolved, {len(introduced)} introduced, "
        f"{len(persisting)} unchanged."
    )
    for f in resolved:
        notes.append(f"  resolved   [{f.id}]")
    for f in persisting:
        notes.append(f"  unchanged  [{f.id}]")

    return introduced, notes


# --- driver -----------------------------------------------------------------


def load_intents(text: str) -> dict[str, str]:
    """`<finding-id>  <reason>` per line. Blank lines and whole-line `#`
    comments are ignored.

    Comments must own their line. An inline `#` is *not* a comment, because
    finding ids contain one — `SING:CHORUS#2:S0:L2:hands` distinguishes the
    second chorus from the first, and stripping at the first `#` truncated it
    to `SING:CHORUS`, so every declared intent on a repeated section silently
    failed to apply and the finding stayed open with no indication why.
    """
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fid, _, reason = line.partition(" ")
        out[fid.strip()] = reason.strip() or "(no reason given)"
    return out


def run_all(text: str, intents: dict[str, str] | None = None) -> Report:
    """Every check. Findings a writer has declared move to `declared`."""
    intents = intents or {}
    lyric, skipped = parse(text)
    report = Report()

    if skipped:
        report.notes.append(
            "Read as prose, not verse: " + ", ".join(skipped)
            + ". Only headers naming a song section are scanned."
        )

    if not lyric.sections:
        report.unavailable.append(
            "No song sections found. Expected headers like VERSE / CHORUS / "
            "BRIDGE with indented lines under them; returning unavailable "
            "rather than no findings (§6)."
        )
        return report

    found = list(check_meter(lyric)) + list(check_sing(lyric))
    for fn in (check_structure, check_parity, check_rhyme, check_concrete):
        fs, notes = fn(lyric)
        found += fs
        report.notes += notes

    unknown = sum(
        1 for s in lyric.sections for l in s.lines
        for st in stress_pattern(l) if st is None
    )
    words = sum(len(l.words()) for s in lyric.sections for l in s.lines)
    if unknown:
        report.unavailable.append(
            f"Stress unknown for {unknown} of {words} words (polysyllables need "
            f"a dictionary this package does not ship). Stress-dependent checks "
            f"declined rather than guessed."
        )

    for f in found:
        if f.id in intents:
            report.declared.append((f, intents[f.id]))
        else:
            report.findings.append(f)
    return report
