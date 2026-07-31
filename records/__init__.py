"""Records — the read predicate and the sensitivity ladder's machine form.

Plain domain noun, no fleet nouns (`CLAUDE.md`, *Working here*). Nothing in
this package reaches the network, loads a model, or opens a store: it decides,
and the caller supplies the rows.
"""

from .witness import (Anchor, Evidence, Independence, Receipt, Standing as WitnessStanding,
                      anchor_for, missing, schedule, standing)
from .atrest import (Agreement, Composition, Erasability, Erasure, EscrowDisposition,
                     EscrowState, KeyState, KeyUnavailable, Keyring, LaneKey,
                     MasterKey, Opening, PrimitiveUnavailable, Readable, Sealed,
                     WrappedLaneKey, composes, destroy, escrow_state, escrow_survey,
                     new_master, open_lane_key, reconcile, record_escrow, rehearse,
                     reseal, rewrap, rotate_lane_key, seal_bytes, unseal,
                     unseal_with, unwrap)
from .crossing import Envelope, permits
from .dispatch import Dispatch, dispatch
from .exit import Lane, Threshold, open_lane, transfer
from .classify import Classification, Decision, Descriptor, classify, unclassified
from .disclosure import Entry, Ledger, Log, verify_against
from .receipts import (GuardianReceipt, authentic, contradictions, gaps, held_by, issue)
from .dispositions import Disposition, Request, answer, ask, extend, state_at
from .conflict import Escalation, NotComputable, Stake, halt, refuse_to_rank
from .consent import Governance, Model, governs
from .export import Artifact, bundle
from .marking import Mark, ScorePosition, align, drift, realign
from .practice import Milestone, OwnPractice, Session, milestones, own
from .standing import (SELF, SELF_CAP, LogAccess, OwnLog, Widening, is_self_edge,
                       own_log, past_threshold, self_edge, widens)
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
    "Log", "Ledger", "Entry", "verify_against",
    "GuardianReceipt", "issue", "authentic", "held_by", "gaps", "contradictions",
    "Record", "State", "draft", "seal", "reject", "redraft",
    "Request", "Disposition", "ask", "answer", "state_at", "extend",
    "Escalation", "NotComputable", "Stake", "halt", "refuse_to_rank",
    "Governance", "Model", "governs",
    "Artifact", "bundle",
    "Mark", "ScorePosition", "align", "drift", "realign",
    "Session", "OwnPractice", "Milestone", "own", "milestones",
    "SELF", "SELF_CAP", "Widening", "OwnLog", "LogAccess", "self_edge",
    "is_self_edge", "past_threshold", "widens", "own_log",
    "Lane", "Threshold", "open_lane", "transfer",
    "Envelope", "permits", "Dispatch", "dispatch",
    "MasterKey", "LaneKey", "WrappedLaneKey", "Keyring", "KeyState", "Sealed",
    "Opening", "Readable", "Agreement", "Erasure", "Erasability", "Composition",
    "EscrowDisposition", "EscrowState", "KeyUnavailable", "PrimitiveUnavailable",
    "new_master", "open_lane_key", "unwrap", "seal_bytes", "unseal", "unseal_with",
    "reconcile", "rewrap", "rotate_lane_key", "reseal", "destroy", "composes",
    "record_escrow", "rehearse", "escrow_state", "escrow_survey",
    "Anchor", "Receipt", "Evidence", "Independence", "WitnessStanding",
    "anchor_for", "schedule", "missing", "standing",
]
