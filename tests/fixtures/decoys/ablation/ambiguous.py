"""The same guard text in two places, which is how a mutation hits the wrong one.

`ablate()` used `str.replace(pattern, repl, 1)` and asked only whether the file
had changed. A pattern occurring twice therefore mutated the first site, left
the second one whole, and reported on a guard it had not removed.

`records/sending.py` was in exactly this state: `and r.live_at(at)` sits in both
`recipients()` and `who_could_see()`, and only the first was ever ablated. The
second survived the moment it was pointed at.
"""

ORDER = {"a": 0, "b": 1, "c": 2}


def rank(value):
    if value not in ORDER:
        raise ValueError(f"not a value: {value!r}")
    return ORDER.get(value, -1)


def rank_again(value):
    if value not in ORDER:
        raise ValueError(f"not a value: {value!r}")
    return ORDER.get(value, -1)
