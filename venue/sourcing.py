"""The named middle: a three-state provenance vocabulary against `P1–P5`.

**Rule 12, and the pair is unavoidable.** Anything that hands this package a
reading — a fleet simulator's result, a sound-check sheet, an equipment vendor's
datasheet — labels its own numbers, and the vocabulary in front of us labels them
`measured | fitted | assumed`. This repository's ladder has five rungs (§15).
Two vocabularies for one fact is the pair §16 is about; without a middle, every
call site would translate for itself and they would disagree within a season. So
the translation lands here, in the same commit as the package that needs it, and
`divergence()` is the part that reports what the translation *cannot* carry.

**The finding, and it is not the arity.** §14's component-map row records this as
*"Partial and divergent — four vocabularies, no mapping; the `Cited` and
`Estimated` rungs have nowhere to sit today."* That is right and it is the
smaller half. Reading the source rather than the row turns up a **collision on a
word**:

> `MEASURED` there means *"from a published dataset, with a citation someone can
> check"* — the state is documented that way, its instrument objects require a
> citation before they will accept the data, and the citation is required rather
> than optional precisely so the claim can be looked up.

That is `P2 Cited` here, not `P1 Measured`. §15 reserves `P1` for *"instrumented
here — this ensemble, this event, this instrument"*, which the three-state
vocabulary has no rung for at all. So the two ladders share the strongest word
and disagree about what it means, and a translation that matched on the word
would silently promote every citation in the fleet to the rung this repository
reserves for its own instruments.

Arity is a mismatch a reader notices. A shared word that means two things is one
they do not, which is why this module exists rather than a dict at a call site.

Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.marking import (  # noqa: E402
    P_ASSUMED, P_CITED, P_ESTIMATED, P_FITTED, P_MEASURED,
)

#: The three states as that vocabulary spells them, worst to best in its own
#: ordering. Recorded so the mapping below can be shown to cover all of them.
THREE_STATE: Tuple[str, ...] = ("assumed", "fitted", "measured")

#: The translation. **`measured` lands on `P2`,** for the reason in the module
#: docstring; matching it to `P1` on the strength of the shared word is the
#: defect this table is written to make impossible.
_TO_LADDER: Dict[str, str] = {
    "measured": P_CITED,
    "fitted": P_FITTED,
    "assumed": P_ASSUMED,
}

#: Rungs of this repository's ladder that no three-state source can reach.
#: Declared rather than discovered at a call site, so a caller who needs one
#: knows it has to come from somewhere else.
_UNREACHABLE: Dict[str, str] = {
    P_MEASURED: (
        "nothing in a three-state vocabulary distinguishes a reading instrumented "
        "at this venue, on this day, by this program from one taken out of a "
        "published dataset. P1 is claimed by the program that took the "
        "measurement and by nobody translating for it"
    ),
    P_ESTIMATED: (
        "extrapolation from an analogous case — another stadium, another "
        "ensemble — has no state there at all, so it arrives labelled `fitted` "
        "and lands a rung stronger than it is. P4 has to be set deliberately"
    ),
}


def from_three_state(state: str) -> str:
    """Translate `"measured" | "fitted" | "assumed"` to a rung on this ladder.

    Refuses anything else rather than guessing. A vocabulary this does not know
    is an unknown provenance, and rule 13 says an unknown is reported and never
    resolved to the convenient answer — which here would be the strongest rung
    the word happens to resemble.
    """
    if not isinstance(state, str):
        raise TypeError(f"a provenance state is a word, not {type(state).__name__}")
    key = state.strip().lower()
    if key not in _TO_LADDER:
        raise ValueError(
            f"{state!r} is not one of the three states {THREE_STATE}; a rung "
            "cannot be derived from a vocabulary nothing here knows")
    return _TO_LADDER[key]


def to_three_state(rung: str) -> str:
    """Translate back, and refuse where the translation would lose the claim.

    `P1` and `P4` have no counterpart, so this raises rather than rounding them
    to a neighbour. Rounding `P1` down to `measured` would be survivable;
    rounding `P4 Estimated` up to `fitted` tells a reader a number was derived
    from local data when it was extrapolated from somewhere else, which §15 calls
    *"the difference between a defensible design decision and a guess wearing a
    number."*
    """
    if rung in _UNREACHABLE:
        raise ValueError(
            f"{rung} has no counterpart in a three-state vocabulary: "
            f"{_UNREACHABLE[rung]}")
    for word, mapped in _TO_LADDER.items():
        if mapped == rung:
            return word
    raise ValueError(f"{rung!r} is not a P-ladder rung (rule 14)")


def unreachable() -> Tuple[str, ...]:
    """Rungs of this ladder no three-state source can supply. Two of five."""
    return tuple(sorted(_UNREACHABLE))


def divergence() -> Tuple[str, ...]:
    """Findings between the two vocabularies. Never empty, and that is the point.

    A middle that reported clean would be claiming the two ladders agree. They do
    not, and the useful output of this reconciler is the list of ways — the same
    shape as `presentation/scales.py`'s `drift()`, except that there the finding
    list *should* be empty and here it never can be.
    """
    findings = []

    covered = {s.strip().lower() for s in THREE_STATE}
    if covered != set(_TO_LADDER):
        findings.append(
            f"the three states {THREE_STATE} and the translated keys "
            f"{tuple(sorted(_TO_LADDER))} do not cover each other")

    if _TO_LADDER["measured"] != P_CITED:
        findings.append(
            "`measured` is translated to something other than P2 Cited")
    if _TO_LADDER["measured"] == P_MEASURED:
        findings.append(
            "`measured` has been matched to P1 Measured on the strength of the "
            "shared word; that vocabulary defines it as a published dataset with "
            "a checkable citation, which is P2 here")

    findings.append(
        f"word collision: `measured` there is {P_CITED} Cited here, while "
        f"{P_MEASURED} Measured here means instrumented at this venue by this "
        "program — the two ladders share their strongest word and disagree "
        "about it")
    for rung in sorted(_UNREACHABLE):
        findings.append(f"{rung} is unreachable: {_UNREACHABLE[rung]}")
    findings.append(
        f"{len(_UNREACHABLE)} of {len(_TO_LADDER) + len(_UNREACHABLE)} rungs "
        "cannot arrive through this translation, so a profile built entirely "
        "from a three-state source can never read stronger than P2")

    return tuple(findings)
