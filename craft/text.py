"""Parsing and phonetic heuristics.

**On accuracy, up front.** English syllable counting and stress assignment are
dictionary problems, and this package has no dictionary — stdlib only, no
download. What is here is a heuristic with a small exception table, and it is
wrong on some words. Two things keep that honest:

1. **The load-bearing checks are comparative.** Comparing verse 1 line 3
   against verse 2 line 3 runs the same counter over both, so a systematic
   error cancels. A miscount has to differ *between* the lines being compared
   to produce a false finding, which is far rarer than being wrong in general.
   Absolute counts are reported as advisory.

2. **Unknown is a result.** A word the stress heuristic cannot place returns
   `None`, and checks that depend on it decline to report rather than guessing
   — §6 of the architecture, and CLAUDE.md rule 13. A rubric that failed to
   load returns "unavailable," not "no findings."
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Unstressed in ordinary speech unless a line deliberately leans on them.
# Closed class, so this list is a fact about English rather than a judgement.
FUNCTION_WORDS = frozenset("""
a an the and or but nor for yet so if then than that this these those
of to in on at by with from into onto over under up down out off as
is am are was were be been being do does did have has had will would
shall should can could may might must
i me my we us our you your he him his she her it its they them their
there here who whom whose what which when where why how
not no nor too very just only own same s t
""".split())

# Where the vowel-group heuristic is known to be wrong. Kept deliberately
# short: every entry is a place the rule failed, not a general dictionary.
SYLLABLE_EXCEPTIONS = {
    "somebody": 3, "somebody's": 3, "everybody": 4, "everyone": 3,
    "everyone's": 3, "everything": 3, "nothing": 2, "nobody": 3,
    "nobody's": 3, "anything": 3, "something": 2, "whatever": 3,
    "eleven": 3, "seven": 2, "heaven": 2, "even": 2, "every": 2,
    "fire": 2, "hour": 1, "our": 1, "quiet": 2, "being": 2,
    "hazards": 2, "engine": 2, "couldn't": 2, "wouldn't": 2,
    "shouldn't": 2, "didn't": 2, "doesn't": 2, "isn't": 2, "wasn't": 2, "fingers": 2, "father": 2, "father's": 2,
    "minutes": 2, "plastic": 2, "signal": 2, "little": 2, "people": 2,
}

# Words that name a state, feeling, or evaluation rather than something a
# sense could register. Crude on purpose — see `concreteness` in checks.py,
# which reports density and never a verdict.
ABSTRACT_WORDS = frozenset("""
love hate fear hope dream dreams soul soul's heart hearts mind memory
forever always never eternity destiny fate truth beauty beautiful
freedom free real magic wonder wonderful amazing perfect
happiness happy sad sadness lonely loneliness pain joy sorrow
feeling feelings emotion passion desire longing
life death time moment moments way ways thing things stuff
something nothing everything anything someone anyone everyone
better worse best worst good bad nice great
""".split())

_WORD = re.compile(r"[A-Za-z][A-Za-z']*")
_VOWELS = re.compile(r"[aeiouy]+")
# "VERSE 1", "CHORUS", "PRE", "CHORUS (out)", "BRIDGE"
_HEADER = re.compile(r"^([A-Z][A-Z0-9]*(?:\s+[A-Z0-9()][A-Za-z0-9()]*)*)\s*$")

# A lyric sheet has a closed vocabulary of section names. Without this, an
# ALL-CAPS prose heading in the same file — PROVENANCE, RIGHTS, ARRANGEMENT —
# parses as a verse and gets scanned for rhyme, which is how the first run of
# this package solemnly reported that a copyright notice had an inconsistent
# scheme. Unrecognised headers are reported, never silently dropped.
SECTION_KINDS = frozenset("""
VERSE CHORUS PRE PRECHORUS BRIDGE TAG HOOK REFRAIN INTRO OUTRO
POST POSTCHORUS INTERLUDE VAMP CODA BREAKDOWN DROP TURNAROUND
""".split())


# --- structures -------------------------------------------------------------


@dataclass(frozen=True)
class Line:
    text: str
    number: int          # 1-based, within the file
    stanza: int          # 0-based, within its section
    index: int           # 0-based, within its stanza

    def words(self) -> list[str]:
        return _WORD.findall(self.text)


@dataclass
class Section:
    kind: str            # VERSE | CHORUS | PRE | BRIDGE | TAG | ...
    label: str           # the header as written, e.g. "CHORUS (out)"
    order: int           # 0-based position in the file
    nth: int = 0         # 0-based among sections sharing this label
    lines: list[Line] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Unique and readable. Two sections both headed CHORUS would otherwise
        generate identical finding ids, and a declared intent would silently
        apply to whichever the reader did not mean."""
        base = self.label.replace(" ", "-")
        return base if self.nth == 0 else f"{base}#{self.nth + 1}"

    def stanzas(self) -> list[list[Line]]:
        out: list[list[Line]] = []
        for line in self.lines:
            while len(out) <= line.stanza:
                out.append([])
            out[line.stanza].append(line)
        return [s for s in out if s]

    def body(self) -> str:
        """Normalised text, for deciding whether two sections are the same."""
        return "\n".join(" ".join(l.text.split()).lower() for l in self.lines)


@dataclass
class Lyric:
    sections: list[Section]

    def of_kind(self, kind: str) -> list[Section]:
        return [s for s in self.sections if s.kind == kind]

    def kinds(self) -> list[str]:
        seen = []
        for s in self.sections:
            if s.kind not in seen:
                seen.append(s.kind)
        return seen


# --- parsing ----------------------------------------------------------------


def parse(text: str) -> tuple[Lyric, list[str]]:
    """Read a lyric sheet: ALL-CAPS headers, indented lines, blank-line stanzas.

    Only headers whose first word is in `SECTION_KINDS` open a section. Every
    other ALL-CAPS heading is prose and is returned in the second element so
    the caller can say what it skipped — a parser that quietly drops half a
    file looks identical to one that found nothing there.
    """
    sections: list[Section] = []
    current: Section | None = None
    stanza = 0
    skipped: list[str] = []

    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()

        if not stripped:
            if current and current.lines:
                stanza += 1
            continue

        if _HEADER.match(stripped) and len(stripped) <= 40:
            kind = stripped.split()[0].upper()
            if kind in SECTION_KINDS:
                current = Section(kind=kind, label=stripped, order=len(sections))
                sections.append(current)
                stanza = 0
            else:
                current = None
                skipped.append(stripped)
            continue

        if current is None:
            continue  # front matter, or the body of a prose heading
        # Only indented text is verse; a flush-left paragraph is prose.
        if raw[:1] not in (" ", "\t"):
            current = None
            continue

        current.lines.append(
            Line(text=stripped, number=lineno, stanza=stanza, index=len(current.lines))
        )

    live = [s for s in sections if s.lines]
    seen: dict[str, int] = {}
    for n, s in enumerate(live):
        s.order = n
        s.nth = seen.get(s.label, 0)
        seen[s.label] = s.nth + 1
    return Lyric(sections=live), skipped


# --- phonetics --------------------------------------------------------------


def syllables(word: str) -> int:
    """Vowel-group count with the usual corrections. Advisory, not exact."""
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return 0
    if w in SYLLABLE_EXCEPTIONS:
        return SYLLABLE_EXCEPTIONS[w]

    n = len(_VOWELS.findall(w))
    if n == 0:
        return 1  # "hmm", "shh" — one beat in the mouth

    if w.endswith("e") and n > 1 and not re.search(r"[^aeiouy]le$", w):
        n -= 1                                   # silent final e
    if re.search(r"[^aeiouxszh]es$", w) and n > 1:
        n -= 1                                   # "takes", not "kisses"
    if re.search(r"[^aeioudt]ed$", w) and n > 1:
        n -= 1                                   # "walked", not "wanted"
    return max(1, n)


def line_syllables(line: Line) -> int:
    return sum(syllables(w) for w in line.words())


def stress(word: str) -> bool | None:
    """True stressed, False unstressed, None unknown.

    Monosyllables split cleanly on the closed class of function words. For
    polysyllables the position of stress needs a dictionary, so this returns
    None and every caller declines to report rather than guessing.
    """
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return None
    if syllables(w) > 1:
        return None
    return w not in FUNCTION_WORDS


def stress_pattern(line: Line) -> list[bool | None]:
    return [stress(w) for w in line.words()]


_SILENT = [("ght", "t"), ("gh", ""), ("wr", "r"), ("kn", "n"), ("mb$", "m")]

# One sound, two or three letters. Collapsed to a single placeholder before
# any consonant is counted, because "watch" spells /tʃ/ with three letters and
# a letter-counting cluster check calls that unsingable.
_DIGRAPHS = [("tch", "\x01"), ("ch", "\x01"), ("sh", "\x02"), ("th", "\x03"),
             ("ng", "\x04"), ("ck", "k"), ("ph", "f"), ("wh", "w"), ("qu", "kw")]

# Long and short E are different vowels and must not share a class: "keys"
# and "yet" both spell an e, and calling them a near-rhyme was enough to
# report every verse of a correctly-schemed song as inconsistent.
_VOWEL_CLASS = {
    "a": "A", "ai": "AY", "ay": "AY", "au": "AW", "aw": "AW",
    "e": "E", "ee": "EE", "ea": "EE", "ey": "EE", "ie": "EE",
    "i": "I", "igh": "IE", "uy": "IE",
    "o": "O", "oa": "OH", "ow": "OH", "oe": "OH",
    "oo": "OO", "ou": "OU", "u": "U", "ew": "OO",
    "oi": "OI", "oy": "OI",
}


def _collapse(word: str) -> str:
    """Spelling reduced toward sound: silent letters out, digraphs to one."""
    w = re.sub(r"[^a-z]", "", word.lower())
    for a, b in _SILENT:
        w = re.sub(a, b, w) if a.endswith("$") else w.replace(a, b)
    for a, b in _DIGRAPHS:
        w = w.replace(a, b)
    return re.sub(r"([bcdfgjklmnpqrstvwxz])\1", r"\1", w)


def rhyme_key(word: str) -> tuple[str, str] | None:
    """(vowel class, coda) from the last vowel of a word. None if unreadable.

    Deliberately coarse. "keys"/"trees" must match and "tight"/"white" must
    match, which rules out comparing raw spellings.
    """
    raw = re.sub(r"[^a-z]", "", word.lower())
    w = _collapse(raw)
    if not w:
        return None
    if w.endswith("e") and len(w) > 2 and not re.search(r"[^aeiouy]le$", w):
        w = w[:-1]

    groups = list(_VOWELS.finditer(w))
    if not groups:
        return None
    last = groups[-1]
    vowel = last.group()
    coda = w[last.end():]
    # Final y: "my" and "cry" are long-i, "happy" and "city" are long-e.
    if vowel == "y" and last.end() == len(w):
        cls = "IE" if len(groups) == 1 else "EE"
    else:
        cls = _VOWEL_CLASS.get(vowel, vowel[:1].upper())
    return (cls, coda)


def rhymes(a: str, b: str) -> str:
    """"perfect" | "slant" | "none" | "unknown".

    Slant is deliberately narrow: a shared coda under a different vowel
    (park/work), or a shared vowel whose codas end on the same consonant
    (hand/sand). A shared vowel alone is assonance, not rhyme — the loose
    version called "waits" and "park" a rhyme and reported every verse in a
    correctly-schemed song as inconsistent.
    """
    ka, kb = rhyme_key(a), rhyme_key(b)
    if ka is None or kb is None:
        return "unknown"
    if a.lower() == b.lower() or ka == kb:
        return "perfect"
    # A shared coda of two or more consonants is a near-rhyme (park/work). A
    # single shared final consonant is not — "hat" and "tight" both end in /t/
    # and so does a third of the language.
    if len(ka[1]) >= 2 and ka[1] == kb[1]:
        return "slant"
    if ka[0] == kb[0] and ka[1] and kb[1] and ka[1] != kb[1]:
        return "slant"                       # same vowel, different coda
    return "none"


def last_word(line: Line) -> str | None:
    ws = line.words()
    return ws[-1] if ws else None


def consonant_runs(word: str) -> list[str]:
    """Clusters that are actually hard to sing.

    Two corrections over counting letters. Silent letters are removed first,
    because "ght" is spelled as three consonants and pronounced as one — the
    naive version flagged *brought*, *right* and *tight* as unsingable. And a
    word-initial cluster of three is ordinary in English (*street*, *structure*)
    while a coda cluster of three is not (*hazards*, *length*), so only codas
    are flagged at three; anywhere else needs four.
    """
    # An apostrophe marks an elided vowel, so the consonants either side of it
    # are in different syllables. "couldn't" is not a /ldnt/ cluster.
    if "'" in word:
        return []
    w = _collapse(word)
    if w.endswith("e") and len(w) > 2:
        w = w[:-1]

    out = []
    for m in re.finditer(r"[^aeiouy]{3,}", w):
        at_end = m.end() == len(w)
        if len(m.group()) >= 4 or (at_end and m.start() > 0):
            out.append(_spell(m.group()))
    return out


_UNCOLLAPSE = {"\x01": "ch", "\x02": "sh", "\x03": "th", "\x04": "ng"}


def _spell(cluster: str) -> str:
    """Placeholders back to letters, so a report says "nths" and not "ns"."""
    return "".join(_UNCOLLAPSE.get(c, c) for c in cluster)
