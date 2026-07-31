"""The one mapping table for the three ordinal scales.

Rule 14: *"scales never compare as bare integers, and no scale is encoded by
colour alone. `L1–L5` sensitivity, `T0–T4` trust, `P1–P5` provenance — one
mapping table, prefixes always."* This module is that table, for **rendering**.
It is not the sensitivity→trust crossing, which is a different mapping with a
different subject and lives in `docs/SENSITIVITY.md` (*Crossing to the trust
ladder*); a rung's badge and the trust a rung demands are not the same fact, and
merging them would be §15's own collision in the file written to prevent it.

**It restates neither ladder it can reach.** The `L` rows are built from
`records.rungs.Rung` and the `P` rows from `records.marking`'s `P_*` constants —
one source each, no second copy — and `drift()` is the named middle (rule 12):
it re-derives both orders through the domain's **own** ordering predicates, so a
reordered ladder is a finding here rather than an inverted badge on a surface.

**`T0–T4` has no owner in this repository and the table says so rather than
guessing.** §15 gives only the endpoints — `T0` Exiled, `T4` Elder — and
`docs/SENSITIVITY.md` records that the Rookie/Steady/Veteran assignment for the
middle rungs *"is the obvious reading and has not been checked."* Rendering an
unverified name as though it were verified is `P2` decay with a badge on it, so
`T1`–`T3` carry no word and render as `name unknown`. Rule 13: absence surfaces
as unknown, never as a result — including when the absent thing is a label.

**Emphasis encodes caution, not magnitude, and that is why two ladders run
visually opposite.** §2.5 of `scout-21` names the hazard: if `L5` (most
restricted) and `T4` (most privileged) both render as the heaviest thing on the
page, a reader learns the wrong reflex. So `weight` rises toward *the rung that
should make a reader slow down* — `L5`, `T0`, `P5` — and the trust ladder's
weight therefore runs opposite to its ordinal by construction rather than by
anyone remembering.

Colour is not here. A `Level` names a **token**; `presentation/tokens.yaml` says
what a token looks like. Repainting is a token change and cannot move a badge's
identity, because identity is the prefix.

Stdlib only.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.marking import (  # noqa: E402
    P_ASSUMED, P_CITED, P_ESTIMATED, P_FITTED, P_MEASURED,
)
from records.marking import outranks as _stronger_provenance  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.rungs import outranks as _more_restricted  # noqa: E402


class Scale(Enum):
    """Three scales, and they are not interchangeable at any point."""

    SENSITIVITY = "sensitivity"   # L1–L5 · how much may ever be rendered
    TRUST = "trust"               # T0–T4 · how privileged the principal is
    PROVENANCE = "provenance"     # P1–P5 · how the value came to be known


#: What a rung renders as when nothing in reach names it. Never a blank, never
#: an invented word.
UNNAMED = "name unknown"

#: Scales whose ladder has no owner inside this repository, so `drift()` cannot
#: reconcile them and does not pretend to. Declared rather than assumed clean.
UNRECONCILED: Tuple[Scale, ...] = (Scale.TRUST,)


@dataclass(frozen=True)
class Level:
    """One rung of one scale, as a surface renders it.

    Frozen and unordered on purpose: `dataclass` without `order=True` leaves
    `<` raising `TypeError`, so two levels cannot be compared with an operator
    any more than two `Rung`s can. There is no integer on this class at all
    except `weight`, which is a rendering emphasis and is never a rung.
    """

    scale: Scale
    prefix: str                 # "L3", "T0", "P5" — the identity, always rendered
    word: Optional[str]         # "Attributed"; None where nothing here names it
    token: str                  # resolved in presentation/tokens.yaml
    weight: int                 # 0–4 visual emphasis: caution, not magnitude

    @property
    def text(self) -> str:
        """The badge, as a string. **The prefix is not optional.**

        This is the single line the forced-monochrome parity check rests on: if
        the badge's text carries the prefix, then greyscale, `TERM=dumb`, a
        black-and-white printed program and a screen reader all lose nothing but
        decoration.
        """
        return f"{self.prefix} {self.word or UNNAMED}"


def _titled(value: str) -> str:
    """`"enforcement_only"` → `"Enforcement-only"`. The word is *derived* from
    the domain's own enum value rather than re-typed here, so there is no
    second spelling of a rung name to drift."""
    return value.replace("_", "-").capitalize()


_PROVENANCE_WORDS = {
    P_MEASURED: "Measured",
    P_CITED: "Cited",
    P_FITTED: "Fitted",
    P_ESTIMATED: "Estimated",
    P_ASSUMED: "Assumed",
}

#: `records.rungs.Rung` in declaration order, which is ascending restriction.
#: `drift()` verifies that through `rungs.outranks` rather than trusting it.
_L_ORDER: Tuple[Rung, ...] = tuple(Rung)

#: The `P`-ladder in descending strength, from `records.marking`.
_P_ORDER: Tuple[str, ...] = (P_MEASURED, P_CITED, P_FITTED, P_ESTIMATED, P_ASSUMED)

#: The trust ladder. Only the endpoints are named anywhere this repository can
#: reach (§15); the middle three are `None` and render as `UNNAMED`.
_T_ORDER: Tuple[Tuple[str, Optional[str]], ...] = (
    ("T0", "Exiled"), ("T1", None), ("T2", None), ("T3", None), ("T4", "Elder"),
)


def _build() -> Tuple[Level, ...]:
    rows = []
    for i, rung in enumerate(_L_ORDER):
        # More restricted, more caution: weight rises with the rung.
        rows.append(Level(Scale.SENSITIVITY, rung.name, _titled(rung.value),
                          f"caution_{i}", i))
    for i, (prefix, word) in enumerate(_T_ORDER):
        # **Deliberately opposite.** Less trusted, more caution: `T0` is the
        # heaviest badge on the page and `T4` the lightest, so a reader never
        # learns "bright means important" across two ladders that disagree.
        rows.append(Level(Scale.TRUST, prefix, word,
                          f"caution_{len(_T_ORDER) - 1 - i}", len(_T_ORDER) - 1 - i))
    for i, key in enumerate(_P_ORDER):
        # Weaker provenance, more caution: `P5 Assumed` is the loud one, which
        # is §15's rule that low provenance is announced rather than withheld.
        rows.append(Level(Scale.PROVENANCE, key, _PROVENANCE_WORDS[key],
                          f"caution_{i}", i))
    return tuple(rows)


#: **The table.** Keyed by prefix, which is unique across all three scales —
#: that uniqueness is what lets a badge be looked up without being told which
#: ladder it came from, and it is asserted in `tests/test_presentation.py`.
TABLE: Dict[str, Level] = {lv.prefix: lv for lv in _build()}

LEVELS: Tuple[Level, ...] = tuple(TABLE.values())


def level(key) -> Level:
    """The row for `"L3"`, refusing anything that is not a prefixed rung.

    An integer is refused **by type**, not parsed: `level(3)` is the bare-integer
    idiom rule 14 exists to stop, and answering it — even correctly — would make
    the rule a convention again. `level("3")` is refused for the same reason.
    """
    if isinstance(key, (bool, int, float)):
        raise TypeError(
            f"{key!r} is a bare number; scales are addressed by prefix "
            "(L1–L5 sensitivity, T0–T4 trust, P1–P5 provenance) — rule 14"
        )
    if isinstance(key, Rung):        # the domain's own type, always welcome
        key = key.name
    if not isinstance(key, str):
        raise TypeError(f"{key!r} is not a rung prefix")
    try:
        return TABLE[key.strip()]
    except KeyError:
        raise ValueError(
            f"not a rung on any of the three scales: {key!r}. Rungs are "
            "addressed as L1–L5, T0–T4 or P1–P5, never as bare integers"
        ) from None


def of_scale(scale: Scale) -> Tuple[Level, ...]:
    return tuple(lv for lv in LEVELS if lv.scale is scale)


def drift() -> Tuple[str, ...]:
    """The named middle (rule 12). Findings where this table and the domain's
    own ladders disagree.

    Both halves are re-derived through the **domain's** ordering predicates —
    `rungs.outranks` and `marking.outranks` — rather than through an index in
    this file. A table that agreed with itself and disagreed with the ladder it
    renders is the pair §16 is about, and it would surface as an inverted badge
    on a printed program rather than as an error.
    """
    findings = []

    l_here = tuple(lv.prefix for lv in of_scale(Scale.SENSITIVITY))
    l_domain = tuple(r.name for r in Rung)
    if set(l_here) != set(l_domain):
        findings.append(
            f"sensitivity rows {l_here} do not cover records.rungs.Rung {l_domain}")
    for a, b in zip(l_here, l_here[1:]):
        if not _more_restricted(Rung[b], Rung[a]):
            findings.append(
                f"{b} is not more restricted than {a} in records.rungs, but this "
                "table renders it with more caution")

    p_here = tuple(lv.prefix for lv in of_scale(Scale.PROVENANCE))
    if set(p_here) != set(_P_ORDER):
        findings.append(
            f"provenance rows {p_here} do not cover records.marking {_P_ORDER}")
    for a, b in zip(p_here, p_here[1:]):
        if not _stronger_provenance(a, b):
            findings.append(
                f"{a} is not stronger than {b} in records.marking, but this table "
                "renders it with less caution")

    for lv in LEVELS:
        if lv.token != f"caution_{lv.weight}":
            findings.append(f"{lv.prefix} names {lv.token} at weight {lv.weight}")

    return tuple(findings)


def heaviest(scale: Scale) -> Level:
    """The rung a reader should slow down at. `L5`, `T0`, `P5` — and the fact
    that the trust ladder's heaviest is its *lowest* rung is the deliberate
    inversion §2.5 of `scout-21` asks for."""
    return max(of_scale(scale), key=lambda lv: lv.weight)


if __name__ == "__main__":  # pragma: no cover - a look at the table
    for lv in LEVELS:
        print(f"  {lv.scale.value:<12} {lv.text:<24} {lv.token}  weight {lv.weight}")
    for f in drift():
        print(f"  DRIFT {f}")
