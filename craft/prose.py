"""The same tool, wearing a second skin: craft checks over this repo's prose.

`checks.py` reads a lyric and reports where the craft is off. This reads a
document and does the same thing, against the craft `CLAUDE.md` states in
English. Six rules there are checkable and were left as prose:

    rule 13  absence surfaces as `unknown`, never as a result   -> ABSENCE
    rule 14  scales never compare as bare integers              -> RUNG
    rule 17  do not quote a count you did not derive            -> COUNT
    rule 18  say "enforcement" or "ledger"                      -> GATE
    rule 20  when retiring anything, leave a tombstone          -> TOMBSTONE
    (house)  a document declares its status and what governs it -> STATUS

**This is a new input to an existing tool, not a second tool.** `Finding`,
`Report` and `load_intents` are imported from `checks.py` rather than
reimplemented, so the declaration mechanic, the report shape and the intent
file format have one implementation and two callers. `docs/SKINS.md` §6 is the
reason: the cheapest middle is the one you do not need.

What it deliberately does not check, because something already does, and a
second copy would be the pair this repo keeps recording:

    §-references resolve                 tests/test_section_refs.py
    a claimed artifact is in the tree    tests/test_claimed_artifacts.py

Same contract as the lyric side, and the same limits. It reports where
something is; it returns no total, no verdict and nothing resembling a
judgement of quality. It cannot tell a defect from a decision, so a finding
you disagree with is declared rather than suppressed, and the declaration is
what gets kept. A document it cannot read comes back `unavailable`, never
clean — which is rule 13 applied to the checker itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from craft.checks import Finding, Report, load_intents  # noqa: F401  (re-exported)

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Row:
    number: int
    text: str
    heading: str
    in_fence: bool


@dataclass
class Doc:
    rows: list[Row]

    def prose(self) -> list[Row]:
        """Fenced blocks are code and diagrams, not prose. Skipped."""
        return [r for r in self.rows if not r.in_fence and r.text.strip()]

    def headings(self) -> list[str]:
        seen = []
        for r in self.rows:
            if r.heading not in seen:
                seen.append(r.heading)
        return seen


def _slug(text: str, limit: int = 30) -> str:
    text = re.sub(r"[`*_~\[\]()]", "", text)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").upper()
    return text[:limit].rstrip("-") or "TOP"


def parse(text: str) -> Doc:
    rows, heading, fenced = [], "TOP", False
    for n, raw in enumerate(text.splitlines(), start=1):
        if _FENCE.match(raw):
            fenced = not fenced
            rows.append(Row(n, raw, heading, True))
            continue
        if not fenced:
            head = _HEADING.match(raw)
            if head:
                heading = _slug(head.group(2))
        rows.append(Row(n, raw, heading, fenced))
    return Doc(rows)


def _quoted(text: str) -> list[tuple[int, int]]:
    """Spans inside quotes or backticks.

    A document that *teaches* a rule quotes the thing the rule forbids —
    ARCHITECTURE.md §10 says a rubric that failed to load must not return
    "no findings" — and a checker that fires on the sentence explaining the
    rule is one that gets switched off, which is the same as no checker.
    """
    spans = []
    for pattern in (r"`[^`]+`", r'"[^"]{0,200}"', r"'[^']{0,200}'", r"“[^”]{0,200}”"):
        spans += [(m.start(), m.end()) for m in re.finditer(pattern, text)]
    return spans


def _inside(spans: list[tuple[int, int]], at: int) -> bool:
    return any(start <= at < end for start, end in spans)


def _sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE.split(text.strip()) if s]


# --- 1. COUNT (rule 17) -----------------------------------------------------

#: Nouns naming something countable **in a tree**. Rule 17 is about figures the
#: code moved past, so an abstract count ("three tiers", "six populations") is
#: out of scope by design and an artifact count is in it.
#:
#: This is an allowlist and it can rot: a noun nobody thought of is a count
#: nobody checks, and the failure is silent (§16). `run_all` reports the list's
#: size in its notes so the scope is visible at the point of use rather than
#: only here.
COUNTABLE = (
    "test", "tests", "table", "tables", "row", "rows", "column", "columns",
    "file", "files", "repo", "repos", "repository", "repositories",
    "check", "checks", "migration", "migrations", "scout", "scouts",
    "commit", "commits", "app", "apps", "gate", "gates",
    "finding", "findings", "defect", "defects", "entry", "entries",
    "function", "functions", "module", "modules", "line", "lines",
    "document", "documents", "doc", "docs", "section", "sections",
    "rule", "rules", "clause", "clauses", "field", "fields", "pair", "pairs",
)

_NUMBER_WORD = (
    "two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    "fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|"
    "fifty|sixty|seventy|eighty|ninety|hundred"
)
_COUNT_CLAIM = re.compile(
    r"\b(\d{1,6}|" + _NUMBER_WORD + r")\s+(?:\w+\s+){0,2}?(" + "|".join(COUNTABLE) + r")\b",
    re.I,
)

#: What a derivation looks like in this house. Any of these in the same
#: sentence and the figure is accounted for.
_DERIVED = re.compile(
    r"\b(derived|derive[sd]?|counted|counting|as counted|from the tree|in this tree|"
    r"per rule 17|rule 17|grep|wc -l|glob|today|measured here|reproduced here|"
    r"the tree said|by reading)\b",
    re.I,
)


def check_count(doc: Doc) -> tuple[list[Finding], list[str]]:
    """A figure about the tree, with nothing nearby saying it came from there.

    The checker cannot tell a derived count from a copied one — that is the
    whole of rule 17's difficulty, and it is why this flags rather than
    corrects. A writer who did derive it declares that, and the declaration
    becomes the record of how.
    """
    out, notes = [], []
    total = 0
    for row in doc.prose():
        spans = _quoted(row.text)
        for sentence in _sentences(row.text):
            at = row.text.find(sentence)
            for m in _COUNT_CLAIM.finditer(sentence):
                if _inside(spans, at + m.start()):
                    continue
                total += 1
                if _DERIVED.search(sentence):
                    continue
                out.append(Finding(
                    check="COUNT",
                    id=f"COUNT:{row.heading}:{_slug(m.group(0), 24)}",
                    where=row.heading,
                    line=row.number,
                    message=(
                        f'"{m.group(0)}" is a figure about the tree with no '
                        f"derivation in the same sentence. Either say how it was "
                        f"counted, or declare it and record where it came from."
                    ),
                ))
    notes.append(
        f"COUNT: {total} figures about tree artifacts seen, over a noun list of "
        f"{len(COUNTABLE)}. A noun not on that list is a count nobody checks."
    )
    return out, notes


# --- 2. GATE (rule 18) ------------------------------------------------------

_GATE_CLAIM = re.compile(
    r"\b(is gated|are gated|gates the|gated at|gated by|enforced|enforces|"
    r"prevents|blocks|stops)\b", re.I)
_GATE_RESOLVED = re.compile(
    r"\b(enforcement|ledger|routes through|routed through|nothing routes|"
    r"un-wired|unwired|wired into|bind_tools|which of the two)\b", re.I)

#: A denial that something prevents anything is not a claim that it does.
#: Without this the checker fires on *"flags for a human and never blocks"* —
#: a sentence being careful in exactly the way rule 18 asks for — which is the
#: shape of false positive that gets a check switched off.
_NEGATED = re.compile(
    r"\b(never|not|cannot|can'?t|no|nothing|does\s?n'?o?t|won'?t|unable to|"
    r"rather than)\s+(\w+\s+){0,2}$", re.I)


def check_gate(doc: Doc) -> list[Finding]:
    """A claim that something is gated, without saying which of the two it is.

    §7.2 asks this of the architecture in its own words: *every claim in this
    document that something is "gated" must name which of the two it is.* A
    ledger is a legitimate thing to have; a ledger described as a gate is not.
    """
    out = []
    for row in doc.prose():
        spans = _quoted(row.text)
        for sentence in _sentences(row.text):
            at = row.text.find(sentence)
            m = _GATE_CLAIM.search(sentence)
            if not m or _inside(spans, at + m.start()):
                continue
            if _GATE_RESOLVED.search(sentence) or _NEGATED.search(sentence[:m.start()]):
                continue
            out.append(Finding(
                check="GATE",
                id=f"GATE:{row.heading}:{_slug(m.group(0), 20)}",
                where=row.heading,
                line=row.number,
                message=(
                    f'"{m.group(0)}" claims something is prevented. Say whether '
                    f"anything routes through it before the act, or whether it "
                    f"records after — enforcement or ledger."
                ),
            ))
    return out


# --- 3. ABSENCE (rule 13) ---------------------------------------------------

_ABSENCE = re.compile(
    r"\b(no findings|nothing found|all clear|no issues|nothing to report|"
    r"came back clean|no restrictions|no problems|nothing of note)\b", re.I)
_ABSENCE_RESOLVED = re.compile(r"\b(unknown|unavailable|not checked|nobody looked)\b", re.I)


def check_absence(doc: Doc) -> list[Finding]:
    """Absence rendered as a result.

    Related to `voice.false_all_clear` and deliberately not the same rule:
    that one reads a sentence about to be dispatched to a person, this one
    reads a document. The pair's middle is
    `tests/test_prose.py::test_the_two_absence_rules_do_not_disagree`, which
    asserts neither passes a phrase the other refuses.
    """
    out = []
    for row in doc.prose():
        spans = _quoted(row.text)
        for m in _ABSENCE.finditer(row.text):
            if _inside(spans, m.start()):
                continue
            sentence = next((s for s in _sentences(row.text) if m.group(0) in s), row.text)
            if _ABSENCE_RESOLVED.search(sentence):
                continue
            out.append(Finding(
                check="ABSENCE",
                id=f"ABSENCE:{row.heading}:{_slug(m.group(0), 20)}",
                where=row.heading,
                line=row.number,
                message=(
                    f'"{m.group(0)}" reports an absence as a result. A lookup '
                    f"that did not run and one that ran and found nothing are "
                    f"different facts; only one of them is this sentence."
                ),
            ))
    return out


# --- 4. RUNG (rule 14) ------------------------------------------------------

_BARE_RUNG = re.compile(r"\b(level|tier|rung)\s+(\d)\b", re.I)


def check_rung(doc: Doc) -> list[Finding]:
    """A scale position written as a bare integer.

    §15's hazard: two five-position scales already run in opposite directions,
    both are called "level", and `if level >= 3` reads correctly in review
    against either. The prefix is what stops a position travelling between
    scales — `L1`-`L5` sensitivity, `T0`-`T4` trust, `P1`-`P5` provenance.
    """
    out = []
    for row in doc.prose():
        spans = _quoted(row.text)
        for m in _BARE_RUNG.finditer(row.text):
            if _inside(spans, m.start()):
                continue
            out.append(Finding(
                check="RUNG",
                id=f"RUNG:{row.heading}:{_slug(m.group(0), 16)}",
                where=row.heading,
                line=row.number,
                message=(
                    f'"{m.group(0)}" is a position on a scale with no prefix on '
                    f"it. Three scales here use small integers and two of them "
                    f"ascend in opposite directions."
                ),
            ))
    return out


# --- 5. TOMBSTONE (rule 20) -------------------------------------------------

_RETIRED = re.compile(
    r"\b(retired|superseded|deprecated|withdrawn|no longer canonical|"
    r"replaced by)\b", re.I)

#: The five parts of §16's tombstone, and what each looks like in text.
TOMBSTONE_PARTS = {
    "status first": r"\b(status|state:|retired|this file is retired|do not cite)\b",
    "successor named": (
        r"\b(successor|replaced by|canonical text|now lives|see instead|"
        r"superseded by|resolved by|resolved in)\b|`[\w./-]+\.(?:md|sql|py)`"),
    "reason": r"\b(because|why it was|superseded when|the reason|widened|on the grounds)\b",
    "contents mapped forward": r"\b(maps?|mapped|mapping|clause|informative only|non-authoritative)\b",
    "why the stub exists": r"\b(kept only|so .{0,30}do not dangle|nothing new should|dangle|still exists)\b",
}

#: A struck item on an open list is a smaller object than a retired document,
#: and §16's five parts are written for the second. `ARCHITECTURE.md` §18
#: states the why-the-stub rationale once for the whole list rather than per
#: item, so demanding it on every line would be the checker misreading the
#: form. Three parts are the subset that must be per-item, because each is a
#: fact about *that* item that nothing else records.
ITEM_PARTS = ("status first", "successor named", "reason")


def check_tombstone(doc: Doc) -> list[Finding]:
    """A thing marked retired, missing parts of the tombstone.

    Scoped to headings and to struck-through items, which is where a
    retirement is *declared*. Body prose discussing retirement in general is
    not a retirement, and firing on it would make the check noise.
    """
    out = []
    rows = doc.prose()
    for i, row in enumerate(rows):
        text = row.text
        declared = bool(_HEADING.match(text) and _RETIRED.search(text))
        struck = "~~" in text and _HEADING.match(text) is None and text.strip().startswith("**~~")
        if not (declared or struck):
            continue
        wanted = ITEM_PARTS if struck else tuple(TOMBSTONE_PARTS)
        window = " ".join(r.text for r in rows[i:i + 12])
        missing = [name for name in wanted
                   if not re.search(TOMBSTONE_PARTS[name], window, re.I)]
        if missing:
            out.append(Finding(
                check="TOMBSTONE",
                id=f"TOMBSTONE:{row.heading}:{_slug(text, 24)}",
                where=row.heading,
                line=row.number,
                message=(
                    f"Retirement declared here, and the tombstone is missing: "
                    f"{', '.join(missing)}. A thing removed without one is "
                    f"indistinguishable from a thing that was never there."
                ),
            ))
    return out


# --- 6. STATUS (house convention) -------------------------------------------

_STATUS = re.compile(r"\*\*Status:?\*\*|^Status:", re.I | re.M)
_AUTHORITY = re.compile(
    r"\b(governs|not a decision record|not canonical|canonical for|"
    r"nothing here governs)\b", re.I)


def check_status(doc: Doc) -> tuple[list[Finding], list[str]]:
    """A document that does not say what it is or what governs it.

    Every document in `docs/` opens by declaring its own weight — *strawman
    for argument*, *findings record, governs nothing*, *draft, unsealed*. That
    is what stops a survey being read as a decision, and it is the cheapest
    protection in the repo.
    """
    out, notes = [], []
    head = "\n".join(r.text for r in doc.rows[:14])
    whole = "\n".join(r.text for r in doc.rows)
    first = doc.rows[0].heading if doc.rows else "TOP"

    # A document that states its authority up front has done the job the
    # Status line exists to do. `CLAUDE.md` opens with *"This file is not
    # canonical. docs/ARCHITECTURE.md governs"* and carries no Status label;
    # demanding the label there would be checking the spelling rather than the
    # property (§16 rule 3 — say which one you compare).
    if not _STATUS.search(head) and not _AUTHORITY.search(head):
        out.append(Finding(
            check="STATUS",
            id=f"STATUS:{first}:no-status",
            where=first,
            line=1,
            message=(
                "No **Status:** line in the opening. A reader cannot tell a "
                "decision record from a strawman from a findings file, and the "
                "three carry different weight."
            ),
        ))
    elif not _AUTHORITY.search(whole):
        out.append(Finding(
            check="STATUS",
            id=f"STATUS:{first}:no-authority",
            where=first,
            line=1,
            message=(
                "A status is declared and nothing says what governs. Say which "
                "document wins where this one disagrees, or say it governs "
                "nothing."
            ),
        ))
    else:
        notes.append("STATUS: status declared, and authority stated.")
    return out, notes


# --- driver -----------------------------------------------------------------

#: name -> the callable. `RULES` is derived from this rather than written
#: beside it, so the vocabulary cannot outlive what produces it — which is the
#: defect `checks.CHECKS` and `checks.DIFF_CHECKS` currently carry, declared
#: and consumed by nothing.
_REGISTRY = {
    "COUNT": check_count,
    "GATE": check_gate,
    "ABSENCE": check_absence,
    "RUNG": check_rung,
    "TOMBSTONE": check_tombstone,
    "STATUS": check_status,
}
RULES = tuple(_REGISTRY)


def _disambiguate(found: list[Finding]) -> list[Finding]:
    """Two identical matches under one heading would collide, and a colliding
    id makes a declaration apply to a line the writer never read."""
    seen: dict[str, int] = {}
    out = []
    for f in found:
        seen[f.id] = seen.get(f.id, 0) + 1
        out.append(f if seen[f.id] == 1 else replace(f, id=f"{f.id}#{seen[f.id]}"))
    return out


def run_all(text: str, intents: dict[str, str] | None = None) -> Report:
    """Every rule. Findings a writer has declared move to `declared`."""
    intents = intents or {}
    report = Report()

    if not text.strip():
        report.unavailable.append(
            "Empty document. Returning unavailable rather than no findings "
            "(rule 13).")
        return report

    doc = parse(text)
    if not doc.prose():
        report.unavailable.append(
            "Nothing outside code fences to read as prose. Returning "
            "unavailable rather than no findings (rule 13).")
        return report

    found: list[Finding] = []
    for name, fn in _REGISTRY.items():
        result = fn(doc)
        if isinstance(result, tuple):
            fs, notes = result
            found += fs
            report.notes += notes
        else:
            found += result

    if len(doc.headings()) <= 1:
        report.unavailable.append(
            "No markdown headings found, so every finding is filed under TOP "
            "and ids are weak against edits. Structural checks are partial.")

    for f in _disambiguate(found):
        if f.id in intents:
            report.declared.append((f, intents[f.id]))
        else:
            report.findings.append(f)
    return report


def run_diff(before: str, after: str) -> tuple[list[Finding], list[str]]:
    """Draft to draft, in both directions.

    §24 again: a revision that fixes two things and breaks one has done that,
    and a report of only the wins is flattering rather than teaching.
    """
    old = {(f.check, f.id): f for f in run_all(before).findings}
    new = {(f.check, f.id): f for f in run_all(after).findings}

    resolved = [f for k, f in old.items() if k not in new]
    introduced = [f for k, f in new.items() if k not in old]
    persisting = [f for k, f in new.items() if k in old]

    notes = [
        f"Findings: {len(resolved)} resolved, {len(introduced)} introduced, "
        f"{len(persisting)} unchanged."
    ]
    notes += [f"  resolved   [{f.id}]" for f in resolved]
    notes += [f"  unchanged  [{f.id}]" for f in persisting]
    return introduced, notes
