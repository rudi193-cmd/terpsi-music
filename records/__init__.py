"""Records — the read predicate and the sensitivity ladder's machine form.

Plain domain noun, no fleet nouns (`CLAUDE.md`, *Working here*). Nothing in
this package reaches the network, loads a model, or opens a store: it decides,
and the caller supplies the rows.
"""

from .witness import (Anchor, Evidence, Independence, Receipt, Standing as WitnessStanding,
                      anchor_for, missing, schedule, standing)
from .crossing import Envelope, permits
from .dispatch import Dispatch, dispatch
from .exit import Lane, Threshold, open_lane, transfer
from .classify import Classification, Decision, Descriptor, classify, unclassified
from .disclosure import Entry, Log, verify_against
from .dispositions import Disposition, Request, answer, ask, extend, state_at
from .rungs import DERIVE_AT, NEVER_SERVED, Rung, at_least, compose, outranks, parse
from .sealing import Record, State, draft, redraft, reject, seal
from .sending import ContactRestriction, Payload, SendList, Standing, deliver, recipients, who_could_see
from .serving import Edge, Field, Outcome, Principal, Serving, serve

__all__ = [
    "Rung", "DERIVE_AT", "NEVER_SERVED", "at_least", "outranks", "compose", "parse",
    "Edge", "Field", "Principal", "Serving", "Outcome", "serve",
    "ContactRestriction", "Payload", "SendList", "Standing", "deliver", "recipients",
    "who_could_see",
    "Descriptor", "Classification", "Decision", "classify", "unclassified",
    "Log", "Entry", "verify_against",
    "Record", "State", "draft", "seal", "reject", "redraft",
    "Request", "Disposition", "ask", "answer", "state_at", "extend",
    "Lane", "Threshold", "open_lane", "transfer",
    "Envelope", "permits", "Dispatch", "dispatch",
    "Anchor", "Receipt", "Evidence", "Independence", "WitnessStanding",
    "anchor_for", "schedule", "missing", "standing",
]
