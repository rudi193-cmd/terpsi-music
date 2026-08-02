"""The L-ladder is complete, internally consistent, and un-confusable.

`docs/SENSITIVITY.md` is the only place the five rungs are defined, and §18
item 1 blocks migration 001 on it. A definition that quietly loses a rung, or a
§6 data class that quietly stops being mapped, would leave a field with nothing
to classify against — and the symptom is a `KeyError` in a migration months
later, not a failing document.

**The §6 class list is read from `docs/ARCHITECTURE.md`, not mirrored here.**
It used to be a hand-typed tuple, which made this suite check `SENSITIVITY.md`
against a *copy* of the thing it claims to guard rather than against §6 itself:
a ninth class added to §6 and never mapped sailed straight past a green suite,
because the copy did not know the class existed. A guard checked against its own
hand-copy of the source has not been shown to fail — docs/CROSSINGS.md crossing
six, arriving in the file whose whole subject is that failure mode.

ARCHITECTURE.md §10 and PROTECTED_AGENTS.md I-12: a guard that cannot be shown
to fail has not been shown to work. Every check here is a function returning
problems, so it can be pointed at a decoy and shown to complain.

Stdlib only. No network. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_sensitivity_ladder.py
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SENSITIVITY = ROOT / "docs" / "SENSITIVITY.md"
ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"

RUNGS = ("L1", "L2", "L3", "L4", "L5")

# The §6 data classes are read from ARCHITECTURE.md at check time — see
# `arch_classes`. They are deliberately *not* duplicated here: a hardcoded
# mirror is the defect this file shipped with.

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

# "- `HEALTH` — allergies, ..." — a §6 class bullet, matched only inside the
# classification subsection (see `arch_classes`).
_CLASS_BULLET = re.compile(r"^- `([A-Z][A-Z_]+)` — ")

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
    """{class: rung} for every class-to-L row in the mapping table.

    Not filtered against a known-class list: the rows are read as they stand,
    so a table mapping a class §6 does not define surfaces as the reverse of the
    drift `problems` names, rather than being silently dropped.
    """
    out = {}
    for line in _lines(text):
        m = _CLASS_ROW.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def arch_classes(text: str) -> tuple[str, ...]:
    """The §6 data classes, read from ARCHITECTURE.md rather than mirrored.

    Scoped to the one `### …Classification…` subsection so an unrelated all-caps
    bullet elsewhere in the document cannot be mistaken for a class. If that
    heading is ever reworded the scope finds nothing and `problems` fails loudly
    on the empty list (rule 13) — a wrong anchor is a visible failure, never a
    silent pass, which is the exact failure mode this whole file is about.
    """
    out: list[str] = []
    in_section = False
    for line in _lines(text):
        if line.startswith("## ") or line.startswith("### "):
            in_section = line.startswith("### ") and "classif" in line.lower()
            continue
        if in_section:
            m = _CLASS_BULLET.match(line)
            if m:
                out.append(m.group(1))
    return tuple(out)


def crossing_rungs(text: str) -> set[str]:
    """Rungs given a row in the sensitivity-to-trust table."""
    return {m.group(1) for m in (_CROSSING_ROW.match(l) for l in _lines(text)) if m}


def problems(text: str, classes: Sequence[str]) -> list[str]:
    """Human-readable failures, empty when the ladder is whole.

    `classes` is §6's list, passed in rather than hardcoded so the real call
    reads it from ARCHITECTURE.md and a decoy §6 can be pointed at this (rule
    19). The correspondence is checked in **both** directions: a §6 class
    SENSITIVITY.md never maps is the drift the module docstring names, and a
    SENSITIVITY.md row for a class §6 does not define is that same drift run
    backwards — a rung mapped against nothing.
    """
    bad = []
    defined = defined_rungs(text)
    mapped = class_rungs(text)
    crossed = crossing_rungs(text)

    if not classes:
        bad.append(
            "no §6 data classes were parsed from ARCHITECTURE.md; a ladder "
            "certified against an empty class list has checked nothing (rule 13)"
        )

    for rung in RUNGS:
        if rung not in defined:
            bad.append(f"{rung} has no definition heading")
        if rung not in crossed:
            bad.append(f"{rung} has no row in the sensitivity-to-trust table")

    for cls in classes:
        if cls not in mapped:
            bad.append(f"§6 class {cls} is not mapped to a rung")

    for cls in mapped:
        if cls not in classes:
            bad.append(f"{cls} is mapped to a rung but §6 does not define it")

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


def _arch_text() -> str:
    return ARCHITECTURE.read_text(encoding="utf-8")


def test_the_parsers_find_something():
    """Guards the regexes: patterns that matched nothing would make every other
    assertion here pass for the wrong reason."""
    text = _text()
    assert len(defined_rungs(text)) == 5, defined_rungs(text)
    assert len(class_rungs(text)) == 8, class_rungs(text)
    assert len(crossing_rungs(text)) == 5, crossing_rungs(text)
    assert len(arch_classes(_arch_text())) == 8, arch_classes(_arch_text())


def test_the_ladder_is_whole():
    bad = problems(_text(), arch_classes(_arch_text()))
    assert not bad, "\n".join(bad)


def test_the_class_list_is_read_from_the_architecture_not_mirrored():
    """The defect this file shipped with. `CLASSES` was a hand-typed copy of §6,
    so the completeness check compared SENSITIVITY.md against the copy and never
    against §6 itself. Derived from both trees, the two must agree today — and
    the checks below prove they will disagree the moment either drifts."""
    arch = set(arch_classes(_arch_text()))
    mapped = set(class_rungs(_text()))
    assert len(arch) == 8, arch
    assert arch == mapped, (
        f"§6 defines {sorted(arch)}; SENSITIVITY.md maps {sorted(mapped)} — "
        "the two have drifted"
    )


def test_a_ninth_section6_class_with_no_rung_is_caught():
    """The exact drift the docstring names, now reproducible. A class added to
    §6 that SENSITIVITY.md never maps must fail the ladder — before it becomes a
    KeyError in a migration. Under the old hand-typed tuple this passed green."""
    classes = arch_classes(_arch_text()) + ("BEHAVIORAL_MINOR",)
    bad = problems(_text(), classes)
    assert any("BEHAVIORAL_MINOR" in b and "not mapped" in b for b in bad), bad


def test_a_rung_mapped_for_a_class_section6_dropped_is_caught():
    """The drift run backwards: SENSITIVITY.md keeps a row for a class §6 no
    longer defines. A rung mapped against nothing is as wrong as a class with no
    rung, and the old one-directional check could not see it."""
    classes = tuple(c for c in arch_classes(_arch_text()) if c != "HEALTH")
    bad = problems(_text(), classes)
    assert any(b.startswith("HEALTH") and "§6 does not define" in b for b in bad), bad


def test_the_class_parser_can_be_pointed_at_a_decoy_and_fails_closed():
    """Rule 19 for the new parser itself. It reads the classes under a decoy
    classification heading and ignores a bullet in the next section; an empty
    parse — a reworded or missing heading — is refused by `problems`, not
    passed."""
    decoy = "\n".join([
        "### How the model meets the L-ladder classification",
        "- `PUBLIC` — x",
        "- `HEALTH` — y",
        "## 7. Next section",
        "- `NOT_A_CLASS` — outside the subsection, must be ignored",
    ])
    assert arch_classes(decoy) == ("PUBLIC", "HEALTH"), arch_classes(decoy)
    assert not arch_classes("## 6. Egress\nno classification heading here\n")
    empty_complaint = problems(_text(), ())
    assert any("empty class list" in b for b in empty_complaint), empty_complaint


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
    bad = problems(decoy, arch_classes(_arch_text()))
    joined = "\n".join(bad)
    assert "L5 has no definition heading" in joined, joined
    assert "PII_MINOR is not mapped" in joined, joined
    assert "belongs to another ladder" in joined, joined


def test_the_check_passes_a_correct_decoy():
    """The mirror of the test above. A check that complained about everything
    would pass the failure test and still be useless."""
    classes = arch_classes(_arch_text())
    decoy = "\n".join(
        [f"### `{r}` — Name{i}" for i, r in enumerate(RUNGS)]
        + [f"| `{c}` | `L1` | x |" for c in classes]
        + [f"| `{r}` | `T0` | no | no |" for r in RUNGS]
    )
    assert not problems(decoy, classes), problems(decoy, classes)


def test_sensitivity_file_is_reachable():
    """A path typo would make every read raise rather than assert, which reads
    as an error rather than a failure and is easier to skim past."""
    assert SENSITIVITY.is_file(), f"missing {SENSITIVITY}"


def test_architecture_file_is_reachable():
    """The §6 class list is now read from here; a path typo must fail loudly
    rather than silently emptying the class list."""
    assert ARCHITECTURE.is_file(), f"missing {ARCHITECTURE}"


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
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
