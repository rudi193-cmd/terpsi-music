"""A ward clause is quoted whole, or it is not quoted "at source".

`docs/PART-III-READ.md` found the same defect three times: a clause carrying a
prohibition *and* the sanctioned path through it loses the second half at the
first compression, and every later reader works from the compressed copy. W-3
lost it and `records/crossing.py` caught it. W-5 lost it and nobody did. W-7
lost it **inside a docstring that called its quotation "at source."**

This is the middle for that pair (§16 rule 12). It cannot check a quotation
against `PROTECTED_AGENTS.md`, which lives in `willows-grove` and is not
vendored here on purpose — a copy would be a pair whose reconciler this
repository cannot build. What it can do is hold the two halves together once a
read has established them, which is the failure that actually happened twice.

Two guards, and they are different in kind:

* **Citations must be re-fetchable.** The tree cited Part III (and the
  retirement tombstone) at `c8c96b4`, which resolves in no repository reachable
  from this session, `willows-grove` included (§15's warning, made concrete). A
  dead object name may appear only on a line that says it is dead.
* **Two-halved clauses keep both halves.** A file quoting W-3 or W-7 at source
  must carry the constructive sentence, not only the prohibition.

Stdlib only. No network. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_clause_quotes.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READ = ROOT / "docs" / "PART-III-READ.md"

#: Object names this repository has anchored a governance read on, each a blob
#: that resolves in `willow-memory/willows-grove` at the working tree recorded
#: in `docs/PART-III-READ.md`. `2886a41` is `governance/PROTECTED_AGENTS.md`
#: (Part III); `f42df851` is `governance/PROTECTED_PERSONS.md` (the retirement
#: tombstone §14 cites). Adding one means a new read, and a new read means a new
#: row in `docs/PART-III-READ.md`.
ANCHORS = frozenset({"2886a41", "f42df851"})

#: Said of a citation that no longer resolves. A dead object name is allowed to
#: appear -- the history is worth keeping -- but only while being called dead.
_DISCLOSED = re.compile(r"resolve[sd]?\s+(?:in\s+)?(?:no|nowhere|none)", re.I)

_SHA = re.compile(r"`([0-9a-f]{7,40})`")

#: The clauses that carry a second, constructive half, and the phrase that IS
#: that half. A file quoting the clause at source and missing this is quoting a
#: gloss and saying otherwise.
CONSTRUCTIVE_HALF = {
    "W-3": "naming both lanes, purpose, and expiry",
    "W-7": "accumulate as precedent",
}

#: W-5's half is quoted nowhere yet, because nothing implements it. The read
#: record is where it is carried until something does; if that line goes, the
#: finding goes with it silently.
W5_HALF = "co-signer"

#: Gaps `docs/PART-III-READ.md` opened. Trimming one out of the record is how a
#: finding becomes folklore, so the record is checked against its own list.
GAPS_OPENED = ("W-5", "W-7", "signer_id", "edge")


def _sources() -> list[Path]:
    """Every file that could carry a Part III citation."""
    out = sorted((ROOT / "records").glob("*.py"))
    out += sorted((ROOT / "docs").glob("*.md"))
    out += sorted((ROOT / "docs" / "schema").glob("*.sql"))
    return out


#: The clause a module owns is the first one it names -- these files open with
#: it in the docstring's first line. Scoping to the subject matters: a module
#: may mention a neighbouring clause in passing (crossing.py points at W-7's
#: territory, conflict.py at W-3's shape) without taking on the duty to quote
#: that neighbour whole.
_CLAUSE = re.compile(r"\bW-\d\b")


def _subject_clause(body: str) -> str | None:
    m = _CLAUSE.search(body)
    return m.group(0) if m else None


def _squash(text: str) -> str:
    """Collapse wrapping so a phrase split across lines still matches."""
    return re.sub(r"\s+", " ", text)


def test_every_part_iii_citation_is_refetchable():
    """A cited object name resolves, or the line says it does not."""
    bad = []
    for path in _sources():
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if "PROTECTED_AGENTS" not in line:
                continue
            for sha in _SHA.findall(line):
                if sha in ANCHORS or _DISCLOSED.search(line):
                    continue
                bad.append(f"{path.relative_to(ROOT)}:{lineno} cites `{sha}`")
    assert not bad, (
        "A governance citation names an object this repository has not anchored, "
        "on a line that does not say it fails to resolve:\n  "
        + "\n  ".join(bad)
        + "\nAnchor it in docs/PART-III-READ.md, or say it is dead where you name it."
    )


def test_two_halved_clauses_are_quoted_whole():
    """Quote W-3 or W-7 `at source` and you quote the permission too."""
    bad = []
    for path in sorted((ROOT / "records").glob("*.py")):
        body = _squash(path.read_text())
        if "PROTECTED_AGENTS" not in body:
            continue
        subject = _subject_clause(body)
        half = CONSTRUCTIVE_HALF.get(subject)
        if half and half not in body:
            bad.append(
                f"{path.relative_to(ROOT)} quotes {subject} at source "
                f"without its constructive half ({half!r})"
            )
    assert not bad, (
        "A ward clause that forbids without providing the sanctioned path is "
        "not the clause -- records/crossing.py, on W-3, before W-7 proved it "
        "twice:\n  " + "\n  ".join(bad)
    )


def test_w5s_unquoted_half_is_carried_by_the_read_record():
    """Nothing implements W-5's co-signature. The finding still has to live somewhere."""
    body = _squash(READ.read_text())
    assert W5_HALF in body, (
        "docs/PART-III-READ.md no longer names W-5's co-signer mechanism. "
        "It is unrepresentable in the schema and unquoted in the code, so this "
        "file was the only place it was written down."
    )


def test_the_read_record_still_names_every_gap_it_opened():
    """A read that removed a gate and lengthened the list must keep the list."""
    body = READ.read_text()
    missing = [g for g in GAPS_OPENED if g not in body]
    assert not missing, (
        "docs/PART-III-READ.md has lost gaps it opened: "
        + ", ".join(missing)
        + ". Close them with a dated resolution (§16 rule 20), never by deletion."
    )


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
