"""Classification decides only what has been decided, and says so otherwise.

The interesting assertions here are the ones about *not* classifying. A
classifier that returns a rung for every input is indistinguishable, from its
output alone, from one that is guessing — and guessing is the failure rule 13
forbids, wearing the costume of automation.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.classify import (  # noqa: E402
    COMMON, LEGAL_RECORD, NOT_ELEVATED, PROTECTED_STATUS,
    Decision, Descriptor, classify, unclassified,
)
from records.rungs import Rung  # noqa: E402


def d(name, **kw) -> Descriptor:
    base = dict(identifies_a_person=True)
    base.update(kw)
    return Descriptor(name, **base)


# --- the decided cases -----------------------------------------------------


def test_the_five_steps_in_order():
    assert classify(Descriptor("venue", publishable=True)).rung is Rung.L1
    assert classify(Descriptor("bus_capacity")).rung is Rung.L2
    assert classify(d("chair")).rung is Rung.L3
    assert classify(d("allergy", category="health")).rung is Rung.L4


def test_step_4_overrides_everything_below_it():
    """`SENSITIVITY.md`: *"Step 4 runs last and overrides. A field can be
    `PII_MINOR` by class, `L3` by step 2, and still land at `L5`."*

    Checked against a field that would otherwise be `L1` — the strongest form,
    because a publishable field reaching `L5` proves the override is not merely
    ordering `L3` before `L4`."""
    assert classify(Descriptor("vault_key", publishable=True, is_key_material=True)).rung is Rung.L5
    assert classify(Descriptor("order_text", publishable=True,
                               is_enforcement_content=True)).rung is Rung.L5
    assert classify(Descriptor("waiver_taken", publishable=True,
                               reveals_a_refusal=True)).rung is Rung.L5


def test_item_11s_four_categories_reach_l4_through_the_clause():
    """B1's decision, made applicable. These are `L4` **through step 3**, not
    through a §6 class — which is the whole content of the resolution."""
    for cat in sorted(PROTECTED_STATUS):
        c = classify(d(f"field_{cat}", category=cat))
        assert c.rung is Rung.L4, f"{cat} did not reach L4"
        assert "clause" in c.reason, f"{cat} reached L4 by the wrong route: {c.reason}"


def test_the_chosen_name_inversion_holds_in_code():
    """The asymmetry that looks like an oversight and is load-bearing.

    Elevating `chosen_name` makes a deadnaming program **more** likely, because
    the printing path falls back to the legal name it can still reach. So the
    chosen name stays at its class rung and the *legal record* is the protected
    half."""
    for name in sorted(NOT_ELEVATED):
        c = classify(d(name))
        assert c.rung is Rung.L3, f"{name} was elevated — the inversion is inverted"
    for name in sorted(LEGAL_RECORD):
        assert classify(d(name)).rung is Rung.L4, f"{name} is not protected"

    # And the ordering that makes it hold: a chosen name is not rescued by
    # carrying a category, because the inversion is checked before step 3.
    assert classify(d("chosen_name", category="health")).rung is Rung.L3


# --- the refusal to guess --------------------------------------------------


def test_an_undecided_category_is_not_given_a_rung():
    """The point of the module. `SENSITIVITY.md` says step 3's clause stays
    human-evaluated and the enumeration of decided cases is what the build
    checks — so an undecided category must produce no rung at all."""
    c = classify(d("gang_affiliation_note", category="safeguarding_concern"))
    assert c.decision is Decision.UNDECIDED
    assert c.rung is None, "the classifier guessed a rung for an undecided category"
    assert c.needs_a_human


def test_undecided_is_not_quietly_l3():
    """The tempting default, and the wrong one. `L3` is *served in full to any
    principal holding an edge*, so defaulting an unrecognised category there is
    a disclosure decision made by an `if` nobody wrote."""
    c = classify(d("x", category="something_new"))
    assert c.rung is not Rung.L3


def test_undecided_is_not_quietly_l5_either():
    """The over-correction. Filing everything unknown at `L5` looks safe and
    makes the classifier useless — `L5` is never served to anyone, so it would
    silently break every operational need attached to the new category. Refusing
    to decide is not the same as deciding maximally."""
    c = classify(d("x", category="something_new"))
    assert c.rung is not Rung.L5
    assert c.rung is None


def test_a_build_can_fail_with_the_list_not_a_count():
    """*"An unclassified field is a build failure, not a default."* A build step
    needs the offending fields to report, not a number to compare."""
    fields = [
        d("chair"),
        d("allergy", category="health"),
        d("housing", category="housing_status"),
        d("mystery_one", category="unknown_a"),
        d("mystery_two", category="unknown_b"),
    ]
    bad = unclassified(fields)
    assert {x.name for x in bad} == {"mystery_one", "mystery_two"}
    assert len(bad) == 2


# --- the decided set is itself checkable -----------------------------------


def test_the_decided_sets_do_not_overlap():
    """A category in two sets would classify by whichever branch ran first,
    which is a rung decided by source order rather than by anyone."""
    assert not (COMMON & PROTECTED_STATUS)
    assert not (NOT_ELEVATED & LEGAL_RECORD)


def test_every_protected_status_category_is_named_in_the_canonical_document():
    """The pair's middle (rule 12). This module and `docs/SENSITIVITY.md` are a
    declaration and its implementation; if the table there gains a row and this
    set does not, the build must fail rather than silently under-classify."""
    doc = (Path(__file__).resolve().parent.parent / "docs" / "SENSITIVITY.md").read_text(
        encoding="utf-8").lower()
    aliases = {
        "confidential_address": "confidential address",
        "housing_status": "mckinney-vento",
        "foster_placement": "foster placement",
        "immigration_status": "immigration",
    }
    for cat in sorted(PROTECTED_STATUS):
        needle = aliases.get(cat, cat.replace("_", " "))
        assert needle in doc, (
            f"{cat} is in the code's decided set and not in SENSITIVITY.md — "
            "the pair has lost its middle"
        )


def test_a_derived_field_inherits_until_the_reidentification_check_passes():
    """The gate the written procedure omits — §18 item 14.

    `SENSITIVITY.md`'s class table: `DERIVED_ANON` is `L2` **"only after the
    re-identification check"** and **"inherits max of inputs until it passes."**
    The five numbered steps carry no such check, so a derived field passes step
    2 and lands at `L2` with nothing having looked at it.

    That is a fail-open in the one place re-identification risk actually lives.
    *"One student in this section carries an auto-injector"* is a count, names
    nobody, and identifies a child if the section has three members."""
    from records.rungs import Rung as R
    unchecked = Descriptor("section_allergy_count", identifies_a_person=False,
                           derived_from=(R.L4, R.L3))
    c = classify(unchecked)
    assert c.rung is R.L4, "an unchecked aggregate over an L4 input was published as L2"
    assert "max of inputs" in c.reason

    checked = Descriptor("section_allergy_count", identifies_a_person=False,
                         derived_from=(R.L4, R.L3), passed_reidentification_check=True)
    assert classify(checked).rung is R.L2, "the check passed and the rung did not fall"


def test_a_non_derived_field_is_unaffected_by_the_new_gate():
    """The gate must not make every anonymous field inherit something. A field
    derived from nothing is still `L2` by step 2."""
    assert classify(Descriptor("bus_capacity")).rung is Rung.L2


def test_the_classifier_is_not_broken_shut():
    """Negative control. A classifier that returned UNDECIDED for everything
    would pass every refusal test above."""
    assert classify(d("allergy", category="health")).decision is Decision.DECIDED
    assert classify(Descriptor("venue", publishable=True)).decision is Decision.DECIDED


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
