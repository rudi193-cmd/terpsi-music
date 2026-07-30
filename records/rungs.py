"""The `L1`–`L5` ladder as a type that cannot be compared as an integer.

`docs/SENSITIVITY.md` is canonical for what the rungs *mean*. This module is
canonical for nothing except their machine representation, and exists because
rule 14 — *"scales never compare as bare integers"* — has until now been a
convention. `apps/marching-arts` used `IntEnum`, so its bands compared as bare
integers by construction and `band >= 3` was not merely possible but idiomatic.

Here `Rung` carries non-ordinal values, so `Rung.L3 < Rung.L4` raises
`TypeError`. Ordering exists, but only through :func:`outranks` and
:func:`at_least`, which say the scale's name at the call site. The rule is
enforced by the type rather than remembered by the author.

Stdlib only.
"""

from __future__ import annotations

from enum import Enum


class Rung(Enum):
    """A sensitivity rung. Values are names, deliberately not numbers."""

    L1 = "open"
    L2 = "internal"
    L3 = "attributed"
    L4 = "restricted"
    L5 = "enforcement_only"

    def __str__(self) -> str:  # "L3", never "3"
        return self.name


#: Ascending restriction. The only place the order is written down.
_ASCENDING = (Rung.L1, Rung.L2, Rung.L3, Rung.L4, Rung.L5)

#: Rungs at or above which a payload is not the normal serving mode. §6's
#: cited rule, under the scoped reading decided in §18 item 1a.
DERIVE_AT = Rung.L3

#: Never rendered on any surface, to any principal, under any grant.
NEVER_SERVED = Rung.L5


def outranks(a: Rung, b: Rung) -> bool:
    """True when `a` is strictly more restricted than `b`."""
    return _ASCENDING.index(a) > _ASCENDING.index(b)


def at_least(a: Rung, floor: Rung) -> bool:
    """True when `a` is `floor` or more restricted."""
    return _ASCENDING.index(a) >= _ASCENDING.index(floor)


def compose(*rungs: Rung) -> Rung:
    """The rung of a record made of several fields.

    `SENSITIVITY.md`: *"Composition is `max`, everywhere."* A record is the
    `max` of its fields; a projection does not lower a rung. Composing nothing
    is an error rather than `L1`, because an empty record defaulting to *open*
    is the fail-open direction.
    """
    if not rungs:
        raise ValueError("compose() of no rungs — an empty record is not L1")
    return max(rungs, key=_ASCENDING.index)


def parse(value: str) -> Rung:
    """Coerce a stored `"L3"` to a `Rung`, refusing anything else.

    Fails loudly. A rung that cannot be resolved is **not** defaulted to `L1`:
    a silent downgrade to the least restricted value is the wrong failure
    direction for this column, and is the one thing `marching-arts`'s `parse`
    got right that is worth keeping.
    """
    try:
        return Rung[str(value).strip().upper()]
    except KeyError:
        raise ValueError(f"not a rung: {value!r}") from None
