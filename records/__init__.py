"""Records — the read predicate and the sensitivity ladder's machine form.

Plain domain noun, no fleet nouns (`CLAUDE.md`, *Working here*). Nothing in
this package reaches the network, loads a model, or opens a store: it decides,
and the caller supplies the rows.
"""

from .rungs import DERIVE_AT, NEVER_SERVED, Rung, at_least, compose, outranks, parse
from .serving import Edge, Field, Outcome, Principal, Serving, serve

__all__ = [
    "Rung", "DERIVE_AT", "NEVER_SERVED", "at_least", "outranks", "compose", "parse",
    "Edge", "Field", "Principal", "Serving", "Outcome", "serve",
]
