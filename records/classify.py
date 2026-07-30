"""Assign a rung to a field, and refuse to guess when the clause needs a human.

`docs/SENSITIVITY.md`'s *Classifying a new field* is five steps, and step 3 is a
**general clause** — *"does it carry a category the law follows?"* — whose four
familiar examples are illustrative rather than bounding (§18 item 11, closed
2026-07-30). That file's own *does not decide* list names the consequence:

> *"A lookup table is mechanically verifiable; a general clause is a judgment,
> and rule 19 says a guard that cannot be shown to fail has not been shown to
> work. The likely shape is that the clause stays human-evaluated at
> schema-definition time and the **enumeration of decided cases** is what the
> build checks."*

This module is that shape, built. It does **not** evaluate the clause. It
carries the decided cases, applies them mechanically, and returns `UNDECIDED`
for anything outside them — which is a build failure, not a default. A
classifier that guessed would be the thing rule 13 forbids wearing the costume
of automation.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .rungs import Rung, compose

# --- the decided cases -----------------------------------------------------

#: The four familiar categories of step 3. Examples of the clause, not its whole.
COMMON = frozenset({"health", "money", "discipline", "likeness"})

#: `SENSITIVITY.md` *Protected status*, decided 2026-07-30 closing §18 item 11.
#: These reach `L4` **through the clause**, not through a §6 class — which is
#: why they are here and not in the class-to-rung mapping.
PROTECTED_STATUS = frozenset({
    "confidential_address",   # Safe at Home and equivalents
    "housing_status",         # McKinney-Vento
    "foster_placement",
    "immigration_status",
})

#: The inversion. `chosen_name` is a fact to *use*; elevating it makes a
#: deadnaming program **more** likely by pushing the printing path back to the
#: legal name. Its protected counterpart is the SIS legal record.
NOT_ELEVATED = frozenset({"chosen_name", "pronouns"})
LEGAL_RECORD = frozenset({"sis_legal_name", "sis_legal_gender_marker"})


class Decision(Enum):
    DECIDED = "decided"
    UNDECIDED = "undecided"  # a human must classify this; NOT a default rung


@dataclass(frozen=True)
class Descriptor:
    """What the schema knows about a field at definition time."""

    name: str
    publishable: bool = False
    identifies_a_person: bool = False
    category: Optional[str] = None
    reveals_a_refusal: bool = False       # step 4, rule 3
    is_enforcement_content: bool = False  # step 4, rule 2
    is_key_material: bool = False         # step 4, rule 1
    #: Rungs of the fields this one is derived from. Non-empty means the class
    #: table's `DERIVED_ANON` row applies and step 2 alone is not enough.
    derived_from: tuple = ()
    passed_reidentification_check: bool = False


@dataclass(frozen=True)
class Classification:
    decision: Decision
    rung: Optional[Rung]
    reason: str
    via: str = ""  # which decided case applied

    @property
    def needs_a_human(self) -> bool:
        return self.decision is Decision.UNDECIDED


def classify(d: Descriptor) -> Classification:
    """Apply `SENSITIVITY.md`'s five steps, deciding only what has been decided.

    Step 4 runs **last and overrides**, exactly as that document says: a field
    can be `PII_MINOR` by class, `L3` by step 2, and still land at `L5` because
    rendering it would identify who declined.
    """
    # Step 4 first in code, because it overrides — checking it last would mean
    # every earlier return had to be revisited, and one of them would be missed.
    if d.is_key_material:
        return Classification(Decision.DECIDED, Rung.L5,
                              "key material and authentication secrets", "L5 rule 1")
    if d.is_enforcement_content:
        return Classification(Decision.DECIDED, Rung.L5,
                              "the content of an enforced external restriction", "L5 rule 2")
    if d.reveals_a_refusal:
        return Classification(Decision.DECIDED, Rung.L5,
                              "rendering it would reveal a refusal", "L5 rule 3")

    # Step 1.
    if d.publishable:
        return Classification(Decision.DECIDED, Rung.L1, "can be published", "step 1")

    # Step 2 — and the gate the written procedure omits.
    #
    # The class table says `DERIVED_ANON` is `L2` **"only after the
    # re-identification check"** and **"inherits max of inputs until it
    # passes"**. The five numbered steps carry no such check, so a derived
    # field passes step 2 and lands at `L2` with nothing having looked at it.
    # That is a fail-open in exactly the place re-identification risk lives:
    # a count over a section of three is not anonymous. Filed as §18 item 14.
    if not d.identifies_a_person:
        if d.derived_from and not d.passed_reidentification_check:
            inherited = compose(*d.derived_from)
            return Classification(
                Decision.DECIDED, inherited,
                "derived, and the re-identification check has not passed; inherits "
                f"max of inputs ({inherited})", "step 2: DERIVED_ANON unchecked")
        return Classification(Decision.DECIDED, Rung.L2,
                              "does not name or resolve to a person", "step 2")

    # The inversion, before the general clause, because `chosen_name` would
    # otherwise be a plausible candidate for elevation and elevating it is the
    # error §18 item 11 was closed to prevent.
    if d.name in NOT_ELEVATED:
        return Classification(Decision.DECIDED, Rung.L3,
                              "a fact to use, not to protect; its counterpart is the "
                              "legal record", "protected status: inversion")
    if d.name in LEGAL_RECORD:
        return Classification(Decision.DECIDED, Rung.L4,
                              "the protected half of the chosen-name pair",
                              "protected status: legal record")

    # Step 3 — the general clause. Decided cases only.
    if d.category in COMMON:
        return Classification(Decision.DECIDED, Rung.L4,
                              f"{d.category} is one of step 3's familiar categories",
                              "step 3: common")
    if d.category in PROTECTED_STATUS:
        return Classification(Decision.DECIDED, Rung.L4,
                              f"{d.category} reaches L4 through the clause, not a class",
                              "step 3: protected status")
    if d.category is None:
        return Classification(Decision.DECIDED, Rung.L3,
                              "identifies a person and carries no category", "step 3: none")

    # A category nobody has decided. This is the whole point of the module.
    return Classification(
        Decision.UNDECIDED, None,
        f"category {d.category!r} is not in the decided set; step 3's clause is a "
        "judgment and this classifier does not make judgments",
        "step 3: undecided",
    )


def unclassified(descriptors) -> tuple:
    """Fields a build must refuse to ship.

    `SENSITIVITY.md`: *"An unclassified field is a **build failure**, not a
    default."* Returns the descriptors needing a human, so a build step can
    fail with the list rather than with a count.
    """
    return tuple(d for d in descriptors if classify(d).needs_a_human)
