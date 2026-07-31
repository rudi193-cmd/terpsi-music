"""§9 item 11 — local agent assistance, behind the gate.

The domain surface is capability-map **§19 of the capability map, Insight and
Assistance**, whose first line is the whole constraint: *"All of this runs behind
the egress gate on local models, since nearly every input is `PII_MINOR` or
`MEDIA_MINOR`."* This module is the **gated assistance seam** plus one
representative capability that exercises it end to end — a per-student
longitudinal growth narrative — not the full §19 breadth (`docs/PLAN-ASSIST.md`).

Nothing here is rebuilt that already exists (§16). The four pieces this seam is
made of are called, never re-derived:

* `records/inference.py` owns refusal 1. Every model call goes through
  :func:`~records.inference.through`, and a non-local answer, a bare-string
  return, or a stopped local model each surfaces as its own refusal — never a
  served answer. This module builds no request: the caller closes over its own
  model and prompt, exactly as `records/commentary.py::transcribe` does.
* `records/sealing.py` owns the cascade. Assistance output lands as
  `sealing.draft` — a `DRAFT` attributed to nobody — and a seal or a rejection is
  a later act by a **named human**, recorded as durably as the other (rule 10).
* `records/serving.py` / `records/aggregate.py` own the entitlement gate.
  Assistance is grounded only in data the principal was served — one lane through
  `serve`, cross-lane through the aggregate door — never a new door of its own.
* `records/commentary.py` and `records/conflict.py` own the two refusals a
  standing rating (`SA-3`) and a priority between two students (W-7) get. This
  module calls `refuse_standing_score` and `refuse_to_rank`; it does not spell
  either again (rule 12).

**The two hard clauses, and how each is made structural rather than checked.**

*Refusal 1 / §6 (A-1).* There is no path to a model that does not pass through
`inference.through`. This module names no provider, holds no client, and takes no
`fallback`/`allow`/`retry` parameter anywhere — the shape `inference.Answer`
established, where the forbidden state has no field to live in.

*Rule 10 / §8.2 (A-2, A-3).* Assistance output is an :class:`AssistanceDraft`,
which is a `DRAFT` and nothing else: `servable` is `False`, `sealed` raises, and
there is no accessor that yields it as a human's judgment. And a draft is **not**
a :class:`Grounding` — the only thing :func:`assist` will build over — so a chain
with no human signature cannot close: to ground assistance in a prior assistance
output, that output must first be sealed by a named human, at which point the
signature the clause requires is in the chain. *"No artifact is sealed by a chain
containing no human signature"* (§8.2) is therefore not a rule that runs and
could be skipped; it is a shape with nowhere to put the forbidden thing.

**R16 (the escrow fuse).** Drafts land through `records/sealing.py`, the
`records/` draft path — **not** `store/writing.py`'s record-write path — so
`tools/audit.py::durable_callers()` stays empty and R16 stays `FINDING`/`S2`
(`docs/PLAN-ASSIST.md`, the R16 note). This module puts no byte at rest.

Stdlib only. No network, no model, no store: handed what a call returned, it
decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from .commentary import StandingScore, refuse_standing_score
from .conflict import NotComputable, one_lane, refuse_to_rank
from .inference import CLASSES as _SIX_CLASSES
from .inference import Answer, InferenceRefused, through
from .rungs import Rung, compose
from .sealing import Record, State
from .sealing import draft as _land_draft
from .serving import Field, Outcome, Serving

# --- what a person may be shown when this seam refuses ----------------------

#: No fleet noun, no provider identifier, no host: those are operator facts and
#: belong in the exception text and the log (`CLAUDE.md`, *Working here*). The
#: local-or-loud refusals a person reads are `records/inference.py::NARRATION`'s,
#: because those are the ones raised by the gate this seam routes through; the
#: ones here are the seam's own — the draft that is not yet a judgment, the loop
#: that has no human in it, and the read that was never entitled.
NARRATION = {
    "unattended_loop": (
        "Not yet: a machine's draft cannot be built on by the machine again "
        "without a person standing behind it first. A named person seals a "
        "draft; only then can it inform the next one."),
    "own_draft": (
        "Not used: a student's own unfinished draft is not material for the "
        "assistant to work over. Their words are theirs until they seal them."),
    "ungrounded": (
        "Unavailable: the assistant works only from what this reader is already "
        "entitled to see. Nothing here was, so there is nothing to draft from."),
    "not_a_judgment": (
        "This is a draft, not a decision. Nobody has confirmed it, and it is "
        "shown as a suggestion for a person to accept or reject."),
}


# --- the refusals this seam adds --------------------------------------------


class UnattendedLoop(Exception):
    """A machine (or a student's) draft was offered where the chain needs a human.

    §8.2: *"No artifact is sealed by a chain containing no human signature."* An
    exception rather than a returned state, for `inference`'s reason: a caller in
    this position has no sensible fallback, and a returned refusal is a thing a
    busy afternoon turns into ``if not ok: pass``.
    """

    def __init__(self, detail: str, *, narration: str):
        super().__init__(detail)
        self.detail = detail
        self.narration = narration


class Ungrounded(Exception):
    """Assistance was grounded in something the principal was not served (A-4).

    Not the same fact as *nothing was found*: an entitlement decision that
    `REFUSED` or came back `UNKNOWN` says the reader was not served this, and a
    draft built over it would launder an unentitled read into a narrative
    (rule 13, §7). Distinct from :class:`UnattendedLoop`, which is about the seal
    chain rather than the entitlement.
    """

    def __init__(self, detail: str, *, narration: str = ""):
        super().__init__(detail)
        self.detail = detail
        self.narration = narration or NARRATION["ungrounded"]


# --- the capability, declared rather than tagged per call -------------------


@dataclass(frozen=True)
class Capability:
    """What a capability touches, declared once and derived from the domain.

    The classes and rung are **not** accepted from the call site. `transcribe`'s
    lesson (`records/commentary.py`): a caller supplying its own `classes=` could
    tag a growth narrative `PUBLIC` and slip a minor's record past the rung/class
    agreement check. So a capability declares what it touches, and :func:`assist`
    reads it off the capability — there is no `classes=` parameter to override.

    The class names are validated against `records/inference.py::CLASSES`, the
    one copy of §6's eight names, rather than a second list here (rule 12).
    """

    name: str
    classes: Tuple[str, ...]
    rung: Rung
    kind: str

    def __post_init__(self):
        if not (self.name or "").strip():
            raise ValueError("a capability names what it is")
        if not self.classes:
            raise ValueError(
                "a capability declares the §6 classes it touches; an untagged "
                "capability is unknown, and unknown does not serve (rule 13)")
        unknown = [c for c in self.classes if c not in _SIX_CLASSES]
        if unknown:
            raise ValueError(
                f"{unknown} are not §6 classes; a class this build does not "
                "recognise cannot be shown to be outside refusal 1")
        if not isinstance(self.rung, Rung):
            raise ValueError(
                f"rung must be a Rung, not {type(self.rung).__name__} — rule 14, "
                "and a bare integer would compare against the wrong ladder")
        if not (self.kind or "").strip():
            raise ValueError("a capability names the lane_entry kind it lands as")


#: The representative capability (`docs/PLAN-ASSIST.md`): *"longitudinal growth
#: narratives for conferences, drafted from real data"* — one student, one lane
#: (W-1). A narrative about an identifiable minor drawn from their own record is
#: `PII_MINOR`, which `docs/SENSITIVITY.md`'s class-to-`L` table puts at `L3`; the
#: rung is :func:`compose` of the declared classes rather than the literal
#: `Rung.L3`, so a change to that table reaches here. The pair's named middle
#: (rule 12) is `tests/test_assistance.py::
#: test_the_growth_narrative_rung_is_the_ladders_rung_for_its_classes`, which
#: parses the table and fails when the two drift.
GROWTH_NARRATIVE = Capability(
    name="longitudinal growth narrative",
    classes=("PII_MINOR",),
    rung=compose(Rung.L3),
    kind="assistance.growth_narrative",
)


# --- what assistance is allowed to be grounded in ---------------------------

#: The serving outcomes that were actually served to the principal. `REFUSED` and
#: `UNKNOWN` are not among them: the first is not entitled, the second is not
#: known, and neither is material a draft may be built over (rule 13).
_ENTITLED = (Outcome.PAYLOAD, Outcome.INSTRUCTION)


@dataclass(frozen=True)
class Grounding:
    """Vetted material assistance may be built over. The type is the enforcement.

    A `Grounding` can only be obtained from :func:`from_entitlement` (an entitled
    read) or :func:`from_sealed` (a human-sealed record). Both refuse the shapes
    A-3 and A-4 forbid, so this type cannot exist for an unsealed draft, a
    student's own draft, or an unentitled read. :func:`assist` takes `Grounding`
    values and nothing else — which is what makes the unattended loop
    unrepresentable rather than merely refused: an :class:`AssistanceDraft` is not
    one of these, so it cannot be fed back in without being sealed first.
    """

    lane_id: str
    subject_id: str
    rung: Optional[Rung]
    basis: str  # how it was grounded, in plain words — for a legible chain


def from_entitlement(field: Field, decision: Serving) -> Grounding:
    """Ground assistance in a read the principal was entitled to (A-4).

    The entitlement is `records/serving.py`'s, not a new one: `decision` is what
    `serve()` returned, and only an outcome that actually served the reader
    grounds anything. A `REFUSED` or `UNKNOWN` decision is refused here, so a
    draft cannot be built over data the reader was not shown. Cross-lane material
    grounds the same way through the aggregate door (`records/aggregate.py`),
    whose cells are already suppressed; this per-student capability stays in one
    lane (W-1), so it grounds from a one-lane `serve()` decision.
    """
    if decision.outcome not in _ENTITLED:
        raise Ungrounded(
            f"the read came back {decision.outcome.value}, not served; assistance "
            "is grounded only in what the principal was entitled to see, and an "
            "unentitled or unknown read is not that (A-4, rule 13)")
    return Grounding(field.lane_id, field.subject_id, decision.rung,
                     f"entitled read ({decision.outcome.value})")


def from_sealed(record: Record, *, lane_id: str) -> Grounding:
    """Ground assistance in a human-sealed record (A-3).

    A sealed record carries the human signature §8.2 requires, so it is material
    the next draft may be built on. An **unsealed** record is not, and the two
    ways it can be unsealed are the two halves of A-3:

    * a machine's own draft, attributed to nobody — the unattended loop; and
    * a student's own draft (``author_id == subject_id``), still unsealed —
      *"iterating a fourteen-year-old's draft is the harm this refuses."*

    A student's own **sealed** account is fine: the student is the human who
    stood behind it, so the chain has a signature. `lane_id` is required because
    a record lands in a student's lane (W-1) and this seam's one-lane check needs
    it; a sealed `Record` does not carry it and the caller supplies it.
    """
    if record.servable:
        return Grounding(lane_id, record.subject_id, None, "human-sealed record")
    if record.author_id is not None and record.author_id == record.subject_id:
        raise UnattendedLoop(
            "this is a student's own unsealed draft; iterating on it is the harm "
            "§8.2 refuses — a person's words are theirs until they seal them",
            narration=NARRATION["own_draft"])
    raise UnattendedLoop(
        f"this record is {record.state.value}, not sealed; a machine draft cannot "
        "ground the next machine call without a named human sealing it first "
        "(§8.2: no chain with no human signature seals anything)",
        narration=NARRATION["unattended_loop"])


# --- the machine draft ------------------------------------------------------


@dataclass(frozen=True)
class AssistanceDraft:
    """A machine answer, shown to have come from the local model, sealed by nobody.

    Holds the :class:`~records.inference.Answer` (which is *where the answer came
    from*, vetted by refusal 1) and the `sealing.Record` it landed as (which is
    `DRAFT`, attributed to nobody). It is a draft and it says so in every
    accessor: `servable` is `False`, `sealed` raises, and there is no property
    that returns it as a human's judgment. A seal is `records.sealing.seal`, which
    requires a named human and has no default — this type offers no wrapper for
    it, because a convenience sealer would be the auto-seal path §8.2 says does
    not exist.
    """

    answer: Answer
    record: Record
    capability: Capability
    grounded_in: Tuple[Grounding, ...]

    def __post_init__(self):
        if self.record.state is not State.DRAFT:
            raise ValueError(
                f"assistance lands as a draft, not {self.record.state.value}; the "
                "seal is a later act by a named human (rule 10, §8.2)")
        if self.record.author_id is not None:
            raise ValueError(
                f"this draft is attributed to {self.record.author_id!r}; a machine "
                "answer is attributed to nobody until a named human seals it by "
                "name (rule 10)")

    @property
    def state(self) -> State:
        return self.record.state

    @property
    def servable(self) -> bool:
        """Never. A draft informs; only its sealed successor is served (§8.2)."""
        return False

    @property
    def draft_body(self) -> str:
        """The draft text, for a surface that shows it **as an unsealed draft**.

        Named `draft_body` rather than `body`, so a call site cannot reach for it
        expecting a finished answer. What it renders carries the not-a-judgment
        narration alongside it; the words are the machine's guess until sealed.
        """
        return self.record.body

    @property
    def not_a_judgment(self) -> str:
        return NARRATION["not_a_judgment"]

    @property
    def sealed(self):
        """There is no seal here, and asking is the error (rule 10).

        A property rather than an absent attribute, for `inference.Answer`'s
        reason: a caller reaching for one gets the clause, not an
        `AttributeError` they will paper over with `getattr(..., False)`.
        """
        raise NotImplementedError(
            "a machine answer is a draft until a named human seals it "
            "(CLAUDE.md rule 10, §8.2); this says where the answer came from, not "
            "that anyone approved it — use records.sealing.seal()")

    # --- what it is not (A-4, SA-3) ---------------------------------------

    @property
    def score(self):
        """There is none, and asking is the error (refusal 4, `SA-3`).

        A longitudinal narrative is the shape most likely to be reduced to a
        travelling number about a student — a growth *score*. There is no field
        for one and the accessor refuses, so the narrative stays prose a human
        reads and never a rating carried between contexts.
        """
        refuse_standing_score("AssistanceDraft.score", self.record.subject_id or "this student")

    @property
    def rating(self):
        """There is none, and asking is the error (refusal 4, `SA-3`)."""
        refuse_standing_score("AssistanceDraft.rating", self.record.subject_id or "this student")

    @property
    def trajectory(self):
        """There is none, and asking is the error (refusal 4, `SA-3`).

        A *trajectory* is a longitudinal rating wearing a verb; §13 put exactly
        this kind of carried-forward calibration inside the prohibited scope.
        """
        refuse_standing_score("AssistanceDraft.trajectory", self.record.subject_id or "this student")


# --- the gated call ---------------------------------------------------------


def assist(call: Callable[[], object], *, groundings: Sequence[Grounding],
           subject_id: str, capability: Capability, endpoint: str) -> AssistanceDraft:
    """Run a caller's assistance call through the gate and land it as a draft.

    The order is the argument. The material is checked to be grounded before a
    model is reached; the model is reached only through `inference.through`; and
    what comes back lands as a `DRAFT` attributed to nobody.

    `call` takes no arguments and returns the `(response_text, provider_used)`
    pair the upstream router returns; the caller closes over its own prompt,
    model and client, because this module builds no request. Everything about
    *whether that answer may exist* is `records/inference.through`'s, called here
    and not re-derived: a non-local provider, a bare-string return, the local
    label at another machine, and a stopped local model all arrive at the caller
    as `InferenceRefused` subclasses carrying refusal 1's clause, never as a
    served answer and never as an empty one a surface could render as *"no
    findings"* (rule 13).

    **The groundings must be :class:`Grounding` values.** An
    :class:`AssistanceDraft` or a raw `Record` is refused as an unattended loop —
    the belt to :func:`from_sealed`'s braces, and together they make the loop
    unrepresentable: the only way to obtain a `Grounding` is through a factory
    that refuses an unsealed draft.

    There is no `fallback`, no `allow`, no `retry`, and no `**kwargs` — every
    parameter is named here on purpose, the shape `inference.through` holds.
    """
    if not groundings:
        raise Ungrounded(
            "assistance grounded in nothing is refused; a draft over no material "
            "is a machine writing about a student from thin air (rule 13)")
    for g in groundings:
        if not isinstance(g, Grounding):
            raise UnattendedLoop(
                f"assistance is grounded only in vetted material — an entitled "
                f"read or a human-sealed record — never a {type(g).__name__} fed "
                "back to seal itself (§8.2, A-3)",
                narration=NARRATION["unattended_loop"])
    if not (subject_id or "").strip():
        raise Ungrounded(
            "a draft lands in a student's lane and names whose it is; an "
            "unnamed subject is unknown, not a default (rule 13, W-1)")

    answer: Answer = through(call, classes=list(capability.classes),
                             endpoint=endpoint, rung=capability.rung)
    record = _land_draft(subject_id, capability.kind, answer.text)
    return AssistanceDraft(answer, record, capability, tuple(groundings))


# --- the representative capability ------------------------------------------


def growth_narrative(call: Callable[[], object], *,
                     groundings: Sequence[Grounding],
                     endpoint: str) -> AssistanceDraft:
    """Draft a per-student longitudinal growth narrative (capability-map §19).

    *"Longitudinal growth narratives for conferences, drafted from real data"* —
    one student, one lane (W-1), drafted by a local model through :func:`assist`
    (A-1), landed as a `DRAFT` (A-2), refused as an unattended loop if grounded in
    an unsealed draft (A-3), and carrying no score (A-4). It is the capability
    that touches the most clauses at once.

    **One lane, structurally.** The narrative is about one student, so its
    groundings share one lane. That is `records/conflict.py::one_lane`, the
    promoted shared middle — a narrative spanning two lanes is a cross-lane read
    W-3 seals and, drafted into one row, the roster column W-1 forbids. It is not
    re-spelled here; a narrative over two students refuses through the same guard
    a balance and a practice statistic refuse through.
    """
    lane = one_lane(groundings, "a longitudinal growth narrative over two students")
    subject = _sole_subject(groundings)
    return assist(call, groundings=groundings, subject_id=subject,
                  capability=GROWTH_NARRATIVE, endpoint=endpoint)


def _sole_subject(groundings: Sequence[Grounding]) -> str:
    """The one student these groundings are about, or a refusal.

    `one_lane` has already established a single lane; this reads the subject off
    it. A lane belongs to one student (W-1), so two subjects under one lane is a
    contradiction rather than a comparison — refused, not resolved.
    """
    subjects = {g.subject_id for g in groundings if g.subject_id}
    if len(subjects) != 1:
        raise Ungrounded(
            f"a growth narrative is about one student; got {sorted(subjects)}. "
            "One lane is one student (W-1), and a narrative over two is the "
            "roster row W-1 forbids")
    return next(iter(subjects))


# --- no priority between two students (W-7) ---------------------------------


def compare(a: AssistanceDraft, b: AssistanceDraft) -> None:
    """Order two students' growth narratives. Always raises (refusal 6, W-7).

    The refusal has a name at the point somebody reaches for it, for
    `conflict.refuse_to_rank`'s reason: an inline `raise` repeated at each call
    site is how one ends up returning a sorted list on a busy afternoon. A
    narrative *presents* what a student did; ranking one student against another
    is the priority the system never computes — a human decides.
    """
    subjects = [s for s in (a.record.subject_id, b.record.subject_id) if s]
    refuse_to_rank("comparing two students' growth narratives", subjects)


__all__ = [
    "AssistanceDraft", "Capability", "GROWTH_NARRATIVE", "Grounding",
    "NARRATION", "StandingScore", "NotComputable", "Ungrounded", "UnattendedLoop",
    "assist", "compare", "from_entitlement", "from_sealed", "growth_narrative",
]
