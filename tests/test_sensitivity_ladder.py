"""The L-ladder is complete, internally consistent, and un-confusable.

`docs/SENSITIVITY.md` is the only place the five rungs are defined, and §18
item 1 blocks migration 001 on it. A definition that quietly loses a rung, or a
§6 data class that quietly stops being mapped, would leave a field with nothing
to classify against — and the symptom is a `KeyError` in a migration months
later, not a failing document.

ARCHITECTURE.md §10 and PROTECTED_AGENTS.md I-12: a guard that cannot be shown
to fail has not been shown to work. Every check here is a function returning
problems, so it can be pointed at a decoy and shown to complain.

Stdlib only. No network. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_sensitivity_ladder.py
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SENSITIVITY = ROOT / "docs" / "SENSITIVITY.md"

RUNGS = ("L1", "L2", "L3", "L4", "L5")

# The eight classes ARCHITECTURE.md §6 defines. Every one needs a rung, or a
# field carrying it has nothing to resolve against.
CLASSES = (
    "PUBLIC",
    "INTERNAL",
    "DERIVED_ANON",
    "PII_MINOR",
    "PII_GUARDIAN",
    "HEALTH",
    "FINANCIAL",
    "MEDIA_MINOR",
)

# Rung names owned by the other ladders in play. CLAUDE.md rule 14 and §15: the
# scales must not be confusable, and a shared name is the cheapest way to
# confuse them. `sealed`/`draft`/`pending` are Nestor's seal cascade (§8.2).
RESERVED_NAMES = {
    # T0–T4 trust (§15)
    "exiled", "rookie", "steady", "veteran", "elder",
    # P1–P5 provenance (§15)
    "measured", "cited", "fitted", "estimated", "assumed",
    # seal state (§8.2, §16)
    "draft", "sealed", "pending",
}

# "### `L4` — Restricted"
_RUNG_HEADING = re.compile(r"^#{3}\s+`(L[1-5])`\s+—\s+(\S.*?)\s*$")

# "| `HEALTH` | `L4` | Allergies, ... |"
_CLASS_ROW = re.compile(r"^\|\s*`([A-Z][A-Z_]+)`\s*\|\s*`(L[1-5])`\s*\|")

# "| `L4` | `T2` | **yes** | **yes** ... |" and the `L5` row, whose trust cell
# is an em dash because nothing unlocks it.
_CROSSING_ROW = re.compile(r"^\|\s*`(L[1-5])`\s*\|\s*(`T[0-4]`|—)\s*\|")


def _lines(text: str) -> list[str]:
    return text.splitlines()


def defined_rungs(text: str) -> dict[str, str]:
    """{rung id: rung name} for every rung with a definition heading."""
    out = {}
    for line in _lines(text):
        m = _RUNG_HEADING.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def class_rungs(text: str) -> dict[str, str]:
    """{class: rung} from the class-to-L mapping table."""
    out = {}
    for line in _lines(text):
        m = _CLASS_ROW.match(line)
        if m and m.group(1) in CLASSES:
            out[m.group(1)] = m.group(2)
    return out


def crossing_rungs(text: str) -> set[str]:
    """Rungs given a row in the sensitivity-to-trust table."""
    return {m.group(1) for m in (_CROSSING_ROW.match(l) for l in _lines(text)) if m}


def problems(text: str) -> list[str]:
    """Human-readable failures, empty when the ladder is whole."""
    bad = []
    defined = defined_rungs(text)
    mapped = class_rungs(text)
    crossed = crossing_rungs(text)

    for rung in RUNGS:
        if rung not in defined:
            bad.append(f"{rung} has no definition heading")
        if rung not in crossed:
            bad.append(f"{rung} has no row in the sensitivity-to-trust table")

    for cls in CLASSES:
        if cls not in mapped:
            bad.append(f"§6 class {cls} is not mapped to a rung")

    for cls, rung in sorted(mapped.items()):
        if rung not in defined:
            bad.append(f"{cls} maps to {rung}, which has no definition")

    for rung, name in sorted(defined.items()):
        if name.lower() in RESERVED_NAMES:
            bad.append(
                f"{rung} is named {name!r}, which belongs to another ladder "
                "(§15 trust/provenance, or §8.2 seal state)"
            )

    return bad


# --- the checks ------------------------------------------------------------


def _text() -> str:
    return SENSITIVITY.read_text(encoding="utf-8")


def test_the_parsers_find_something():
    """Guards the regexes: patterns that matched nothing would make every other
    assertion here pass for the wrong reason."""
    text = _text()
    assert len(defined_rungs(text)) == 5, defined_rungs(text)
    assert len(class_rungs(text)) == 8, class_rungs(text)
    assert len(crossing_rungs(text)) == 5, crossing_rungs(text)


def test_the_ladder_is_whole():
    bad = problems(_text())
    assert not bad, "\n".join(bad)


def test_no_class_maps_to_l5():
    """SENSITIVITY.md's stated finding, asserted so that adding a ninth class at
    L5 forces the three per-record rules to be revisited rather than bypassed."""
    at_l5 = [c for c, r in class_rungs(_text()).items() if r == "L5"]
    assert not at_l5, (
        f"{at_l5} map to L5 by class, but L5 is documented as unreachable by "
        "class and assigned per record. Update the rules or the table."
    )


def test_rungs_ascend_with_restriction():
    """PUBLIC must sit below PII_MINOR, which must sit below HEALTH. A mapping
    that inverted would satisfy every completeness check above."""
    mapped = class_rungs(_text())
    assert mapped["PUBLIC"] < mapped["INTERNAL"] < mapped["PII_MINOR"] < mapped["HEALTH"]
    assert mapped["PII_GUARDIAN"] == mapped["PII_MINOR"]
    assert mapped["MEDIA_MINOR"] == mapped["FINANCIAL"] == mapped["HEALTH"]


def test_the_check_can_actually_fail():
    """Point every check at a ladder missing a rung, missing a class, and using
    a name another scale owns, and confirm all three complain."""
    decoy = "\n".join(
        [
            "### `L1` — Open",
            "### `L2` — Internal",
            "### `L3` — Attributed",
            "### `L4` — Sealed",  # name owned by the seal cascade
            # L5 absent entirely
            "| `PUBLIC` | `L1` | x |",
            "| `HEALTH` | `L4` | x |",
            # the other six classes absent
            "| `L1` | `T0` | no | no |",
        ]
    )
    bad = problems(decoy)
    joined = "\n".join(bad)
    assert "L5 has no definition heading" in joined, joined
    assert "PII_MINOR is not mapped" in joined, joined
    assert "belongs to another ladder" in joined, joined


def test_the_check_passes_a_correct_decoy():
    """The mirror of the test above. A check that complained about everything
    would pass the failure test and still be useless."""
    decoy = "\n".join(
        [f"### `{r}` — Name{i}" for i, r in enumerate(RUNGS)]
        + [f"| `{c}` | `L1` | x |" for c in CLASSES]
        + [f"| `{r}` | `T0` | no | no |" for r in RUNGS]
    )
    assert not problems(decoy), problems(decoy)


def test_sensitivity_file_is_reachable():
    """A path typo would make every read raise rather than assert, which reads
    as an error rather than a failure and is easier to skim past."""
    assert SENSITIVITY.is_file(), f"missing {SENSITIVITY}"


# --- protected status (§18 item 11, closed 2026-07-30) ---------------------
#
# The decision was that step 3's clause governs and its four familiar examples
# do not bound it. A decision recorded only in prose is a ledger (rule 18), and
# the specific way this one erodes is predictable: someone reads the four
# examples as the list, or "tidies" the chosen-name entry to match the other
# four because the asymmetry looks like an oversight. Both are asserted against.

_PROTECTED_ROW = re.compile(r"^\|\s*([A-Z][^|]*?)\s*\|\s*`(L[1-5])`\s*\|")

#: Substrings identifying the four decided categories. Matched loosely on
#: purpose -- this checks the decision survived, not the wording.
PROTECTED = ("confidential address", "mckinney-vento", "foster placement", "immigration")


def protected_rungs(text: str) -> dict[str, str]:
    """{category line: rung} from the Protected status table."""
    return {
        m.group(1).lower(): m.group(2)
        for m in (_PROTECTED_ROW.match(l) for l in _lines(text))
        if m
    }


def test_the_four_protected_categories_are_decided_and_at_l4():
    """Item 11's four survivors. `L5` here would be the tempting error -- it
    reads as stronger and would make every one of them unservable, so a liaison
    could not act on the fee waiver the status exists to trigger."""
    rows = protected_rungs(SENSITIVITY.read_text(encoding="utf-8"))
    for needle in PROTECTED:
        hits = [rung for cat, rung in rows.items() if needle in cat]
        assert hits, f"no Protected status row for {needle!r} — decision lost"
        assert all(r == "L4" for r in hits), f"{needle!r} is at {hits}, expected L4"


def test_the_chosen_name_inversion_is_not_tidied_away():
    """The asymmetry is load-bearing and looks like an oversight, which is
    exactly what gets 'fixed'. Elevating the chosen name would push the
    program-printing path back to the legal name -- strengthening the guarantee
    in appearance and inverting it in fact."""
    text = SENSITIVITY.read_text(encoding="utf-8")
    rows = protected_rungs(text)
    tidied = [cat for cat in rows if "chosen name" in cat]
    assert not tidied, (
        f"chosen name appears in the Protected status table as {tidied} — it is "
        "not elevated; the SIS legal record is the protected half"
    )
    assert "legal record" in text.lower() or "legal name" in text.lower(), (
        "the protected counterpart of the chosen name is not named at all"
    )


def test_the_protected_status_check_can_actually_fail():
    """Rule 19. Point the parser at a table that dropped a category and at one
    that filed a category at L5, and confirm both are seen."""
    dropped = "| Confidential address program | `L4` | x |"
    assert not [c for c in protected_rungs(dropped) if "mckinney" in c], (
        "parser invented a row that is not there"
    )
    wrong = "| McKinney-Vento housing status | `L5` | x |"
    rows = protected_rungs(wrong)
    assert rows and all(r == "L5" for r in rows.values()), (
        f"parser did not read the rung it was given: {rows}"
    )


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
