"""A module with one real guard, so a mutation has something to remove.

**The first version of this decoy did not work, and the reason is the point.**
It was `VALUES = ("a", "b", "c")` with `return VALUES.index(value)`, so removing
the guard did not change the outcome: `tuple.index` raises `ValueError` for a
missing member, which is the same exception the guard raised, and the suite
still passed. The mutation read `SURVIVES` — correctly, because nothing about
the observable behaviour had moved.

A guard whose removal is masked by the next line is not a guard. The lookup
returns a default instead, so the un-guarded path produces a *value*.
"""

ORDER = {"a": 0, "b": 1, "c": 2}


def rank(value):
    if value not in ORDER:
        raise ValueError(f"not a value: {value!r}")
    return ORDER.get(value, -1)
