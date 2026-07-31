"""Records — the read predicate and the sensitivity ladder's machine form.

Plain domain noun, no fleet nouns (`CLAUDE.md`, *Working here*). Nothing in
this package reaches the network, loads a model, or opens a store: it decides,
and the caller supplies the rows.
"""

from .witness import (Anchor, Evidence, Independence, Receipt, Standing as WitnessStanding,
                      anchor_for, anchor_for_ledger, derives, ledger_derivation,
                      missing, schedule, standing)
from .publication import (Cadence, NotPublishable, Payload, Proof, Publication,
                          Status, Submission, payload_for, payloads_for,
                          permitted, proof_artifact, reconcile, register,
                          submission_artifact, unpublished)
from .atrest import (Agreement, Composition, Erasability, Erasure, EscrowDisposition,
                     EscrowState, KeyState, KeyUnavailable, Keyring, LaneKey,
                     MasterKey, Opening, PrimitiveUnavailable, Readable, Sealed,
                     WrappedLaneKey, composes, destroy, escrow_state, escrow_survey,
                     new_master, open_lane_key, record_escrow, rehearse,
                     reseal, rewrap, rotate_lane_key, seal_bytes, unseal,
                     unseal_with, unwrap)
from .crossing import Envelope, permits
from .dispatch import Dispatch, dispatch
from .exit import Lane, Threshold, open_lane, transfer
from .classify import (Classification, Decision, Descriptor, aggregate, classify,
                       unclassified)
from .attendance import (AbsenceRequest, AttendanceEntry, Excusal, NoRoster,
                         NotSendable, OwnAttendance, Presence, Referent, Signal,
                         SignalKind, correct, excusal, headcount, notify,
                         request_absence, roster, send_attendance, signal,
                         take_roll)
from .fees import (WAIVER, Assessment, Balance, CardData, Charge, FeeGroup,
                   Membership, NotDisclosable, Payment, Source, Tender, Total,
                   allocate, assess, balance, looks_like_a_card_number,
                   plan_priority, rank_by_need, reverse, roster_by_balance,
                   total, waiver_rung)
from .disclosure import Entry, Ledger, Log, verify_against
from .inference import (Answer, InferenceRefused, LocalModelUnavailable,
                        NonLocalInference, OffBoxLocalModel, Refusal, Unclassified,
                        UnknownProvider, accept, covered, through)
from .receipts import (AsymmetricUnavailable, Ed25519Signer, GuardianReceipt,
                       HmacTagger, Issuance, NoSigner, Uncheckable, authentic,
                       contradictions, gaps, generate_signer, held_by, issue,
                       receipt_text, schemes)
from .dispositions import Disposition, Request, answer, ask, extend, state_at
from .conflict import (Escalation, NotComputable, Stake, halt, one_lane,
                       refuse_to_rank)
from .consent import Governance, Model, governs
from .export import Artifact, bundle
from .marking import Mark, ScorePosition, align, drift, realign
from .practice import Milestone, OwnPractice, Session, milestones, own
from .standing import (SELF, SELF_CAP, LogAccess, MaySupersede, OwnLog, Supersession,
                       Widening, is_self_edge, may_supersede, own_log,
                       past_threshold, self_edge, widens)
from .orders import (Ended, Ending, Guardianship, GuardianshipState, NoGuardian,
                     Order, OrderKind, end_guardianship, guardianship_of,
                     past_exercise, supersede)
from .rungs import DERIVE_AT, NEVER_SERVED, Rung, at_least, compose, outranks, parse
from .sealing import Record, State, authored_by, draft, redraft, reject, seal
from .sending import ContactRestriction, Payload, SendList, Standing, deliver, recipients, who_could_see
from .serving import Edge, Field, Grant, Outcome, Principal, Serving, serve

__all__ = [
    "Rung", "DERIVE_AT", "NEVER_SERVED", "at_least", "outranks", "compose", "parse",
    "Edge", "Field", "Grant", "Principal", "Serving", "Outcome", "serve",
    "ContactRestriction", "Payload", "SendList", "Standing", "deliver", "recipients",
    "who_could_see",
    "Descriptor", "Classification", "Decision", "classify", "unclassified",
    "aggregate",
    "Presence", "Referent", "AttendanceEntry", "AbsenceRequest", "Excusal",
    "OwnAttendance", "Signal", "SignalKind", "NotSendable", "NoRoster",
    "take_roll", "correct", "request_absence", "excusal", "headcount",
    "signal", "notify", "roster", "send_attendance",
    "Charge", "Payment", "FeeGroup", "Membership", "Tender", "Source",
    "Assessment", "Balance", "Total", "CardData", "NotDisclosable", "WAIVER",
    "assess", "balance", "total", "reverse", "allocate", "rank_by_need",
    "plan_priority", "roster_by_balance", "waiver_rung",
    "looks_like_a_card_number",
    "Log", "Ledger", "Entry", "verify_against",
    "Answer", "Refusal", "InferenceRefused", "Unclassified", "UnknownProvider",
    "NonLocalInference", "OffBoxLocalModel", "LocalModelUnavailable",
    "accept", "through", "covered",
    "GuardianReceipt", "issue", "authentic", "held_by", "gaps", "contradictions",
    "Issuance", "HmacTagger", "AsymmetricUnavailable", "NoSigner", "Uncheckable",
    "receipt_text", "schemes",
    "Record", "State", "draft", "seal", "reject", "redraft",
    "Record", "State", "authored_by", "draft", "seal", "reject", "redraft",
    "Request", "Disposition", "ask", "answer", "state_at", "extend",
    "Escalation", "NotComputable", "Stake", "halt", "refuse_to_rank", "one_lane",
    "Governance", "Model", "governs",
    "Artifact", "bundle",
    "Mark", "ScorePosition", "align", "drift", "realign",
    "Session", "OwnPractice", "Milestone", "own", "milestones",
    "SELF", "SELF_CAP", "Widening", "OwnLog", "LogAccess", "self_edge",
    "is_self_edge", "past_threshold", "widens", "own_log",
    "Supersession", "MaySupersede", "may_supersede",
    "Order", "OrderKind", "NoGuardian", "Ending", "Ended", "Guardianship",
    "GuardianshipState", "end_guardianship", "supersede", "guardianship_of",
    "past_exercise",
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
    "anchor_for_ledger", "ledger_derivation", "derives",
    "Cadence", "Payload", "Submission", "Proof", "Publication", "Status",
    "NotPublishable", "permitted", "payload_for", "payloads_for", "reconcile",
    "unpublished", "submission_artifact", "proof_artifact", "register",
]
