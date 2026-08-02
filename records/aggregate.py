"""§9 item 10: aggregate exports for corporate and booster reporting.

Rule 9 is the subject — *gate the export, narrate the read* — and §7.2 is where
it comes from: *"the realistic harms in a music program are not someone glancing
at a schedule; they are the roster on a thumb drive, the spreadsheet mailed to a
vendor."* An aggregate handed to a booster board is that spreadsheet. So the
aggregate is not a report this module renders on request; it is an **export-class
artifact whose issuance is announced**, and the announcement is structural
rather than remembered — see *The announcement is load-bearing* below.

**The whole content of an aggregate's safety is the re-identification check.**
`docs/SENSITIVITY.md` has said so since it was written: `DERIVED_ANON` is `L2`
*"only after the re-identification check"* and *"inherits `max` of inputs until
it passes."* §18 item 14 closed the gap in the written procedure and
`records/classify.py` step 2a is the gate. **This module does not re-implement
that rule** (rule 12). It decides one thing — whether the check passed — and
hands the answer to `classify()`. `_descriptor_for` is the named middle of that
pair, and it is the only place the two meet.

**The worked harm is §18 item 14's own** and it is the acceptance case:

> *"One student in this section carries an auto-injector"* names nobody and
> identifies a child if the section has three members.

---

### Three suppression cases, and the second is the one that gets skipped

1. **Small cell.** A cell below `k` is suppressed, zero included. A zero cell
   cannot arise from `release()` — cells come from the readings, so a section
   nobody is in produces no cell and is *absent* rather than published as `0`,
   which would be inventing a number. The rule still covers zero, because a
   published `0` over a named cell is a statement about *every* member of that
   cell, and the day a caller counts a population rather than an attribute the
   branch has to already be there.
2. **Complementary.** *"Hiding one cell while publishing its row and its total
   is not suppression"* — the reader subtracts. `docs/survey/scout-23` is
   explicit that this is mandatory rather than optional, and that naive
   implementations ship without it. The check here is a feasible-interval one:
   a suppressed cell is recovered when its interval collapses to a point, which
   happens whenever it is the only suppressed cell against a known total, and
   also whenever the residual pins every suppressed cell at once. Cells are
   suppressed to a fixpoint; a table that cannot reach one is `UNRELEASABLE`
   rather than published.
3. **Incomplete input.** A lane that could not be read, or an input below the
   verified tier (I-10: *"exports are… drawn from verified-tier records only"*).
   This is the subtlest of the three because the naive handling — drop the row
   and count what is left — produces a **smaller number that looks complete**.
   Rule 13: absence surfaces as `unknown`, never as a result. So an unreadable
   input marks its cell and **stops every count in the table**, and an input
   whose cell is not even known makes the whole release `UNKNOWN`.

*Why an incomplete table releases nothing rather than releasing its good cells.*
The softer option is to withhold only the total. It is not a control: the
population size of a section is public, so a reader who can count the section
recovers the withheld part by subtraction. Withholding a number everybody can
count is the shape of a gate that is really a ledger (rule 18).

### The threshold is a policy input, and this module ships no number

`k` has **no default**, because every available default would be a number this
repository cannot source. `docs/survey/scout-23` records that
`studentprivacy.ed.gov` returned HTTP 403 and that the authoritative US guidance
on minimum n-size is therefore **unread** — *"per CLAUDE.md #17 I am quoting no
numbers from it."* That constraint is inherited here rather than quietly
resolved. `CellFloor` carries the value **with its publisher, version and
jurisdiction**, which is §12 of the capability map's finding taken at its word:
a threshold is a tuple, not a number.

### The announcement is load-bearing, and the artifact cannot exist without it

`_render` takes the announced ledger and writes its chain head into the
manifest. An aggregate that was never announced therefore has nothing to put
there — the artifact is not merely *supposed* to be logged, it is unbuildable
un-logged, the same argument that makes `export.bundle` build its manifest last
and over the other files. Every contributing lane is announced in **its own
chain** (W-1), including the lanes whose contribution was suppressed and the
lanes that could not be read: an audit trail that records only the disclosures
cannot answer *was the suppression working*.

### Multi-lane legitimacy

`records/practice.py`'s `_one_lane` is untouched and still refuses: a practice
statistic that spans lanes is a leaderboard, and nothing here weakens it. An
aggregate is the **sanctioned** multi-lane read and it gets its own door,
`_many_lanes`, which cannot be called without a `Gate`. The `Gate`'s conditions
are: a declared purpose, a declared audience whose ceiling this can reach, a
threshold with its provenance, a ledger to announce into, at least two lanes,
no input at `L5`, and a cell dimension that is not a person.

### What this deliberately does not do

**One dimension per release, and no cross-tab engine.** `scout-23`: *"with a few
hundred students and any two demographic dimensions, almost every cell falls
below any defensible threshold, so a general engine will spend its life
returning `suppressed` — and the one time it returns a number, that number is
the disclosure."* A request naming more than one dimension is refused.

**Differencing across releases is not closed here, and is not pretended to be.**
The rule the fleet already knows is that suppression must be computed *once over
the union of everything that will ever be published*; doing that properly is
Gaussian elimination over linked tables, which `scout-23` says to steal the idea
from rather than to implement. What exists here is `differencing_risk()`, which
reports when two releases were drawn over the same population. **That is a
ledger, not an enforcement** (rule 18) — nothing routes through it, and it is
named that way in its own docstring so the distinction cannot be lost.

Stdlib only. No network, no store, and nothing here touches a filesystem: the
caller writes the artifacts, exactly as in `records/export.py`.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from .classify import Decision, Descriptor, classify
from .disclosure import Ledger
from .export import Artifact
from .marking import P_CITED, outranks as stronger_provenance
from .rungs import NEVER_SERVED, Rung, outranks
from .serving import Outcome, Serving
from .witness import anchor_for_ledger


class NotGated(Exception):
    """An aggregate was asked for without one of the gate's conditions.

    An exception rather than a returned state, for `NotComputable`'s reason: a
    caller in this position has no sensible fallback, and a returned refusal is
    a thing a busy afternoon turns into `if not ok: pass`.
    """


# --- what an audience is ---------------------------------------------------


class Audience(Enum):
    """Who the artifact is for. Declared at issuance, never inferred."""

    INSIDE = "inside_the_program"
    BOOSTER = "booster_organisation"
    SPONSOR = "corporate_sponsor"
    DISTRICT = "district_office"
    PUBLIC = "public"


#: The rung each audience may be served at. Every audience for an aggregate
#: tops out at `L2`, which is the ladder saying what this module is for: an
#: aggregate that reached `L3` is a disclosure with a table around it.
CEILING: Dict[Audience, Rung] = {
    Audience.INSIDE: Rung.L2,
    Audience.BOOSTER: Rung.L2,
    Audience.SPONSOR: Rung.L2,
    Audience.DISTRICT: Rung.L2,
    Audience.PUBLIC: Rung.L1,
}

#: Dimensions that are a person wearing a table's clothes. A cell per student is
#: refusal 5's shape — *"'the drumline' is not a scope; a name is"* — inverted:
#: here the name is the thing that must not become a cell.
NOT_A_DIMENSION = frozenset({
    "student", "students", "subject", "subjects", "lane", "lanes", "name",
    "names", "individual", "individuals", "person", "people", "member",
    "members", "child", "children", "ward", "wards",
})


# --- the threshold ---------------------------------------------------------


@dataclass(frozen=True)
class CellFloor:
    """`k`, and where `k` came from. A number alone is not a policy input.

    §12 of the capability map's finding, applied: *"a threshold is a tuple, not
    a number — regulators disagree on the exchange rate, so value, publisher,
    version and jurisdiction travel together."* A programme that cannot say who
    set its `k` cannot defend it to the office that asks.

    **There is no default.** Not for ergonomics and not for lack of candidates:
    the authoritative guidance is unread (`scout-23`, HTTP 403), so any number
    written here would be prose this repository cannot source, which is exactly
    what rule 17 is about.
    """

    k: int
    publisher: str
    version: str
    jurisdiction: str

    def __post_init__(self):
        if self.k < 2:
            raise ValueError(
                f"k={self.k} suppresses nothing: a floor of 1 admits every cell "
                "with a member in it, and 0 is the threshold switched off. A "
                "threshold that cannot suppress is not a threshold"
            )
        for name in ("publisher", "version", "jurisdiction"):
            if not (getattr(self, name) or "").strip():
                raise ValueError(
                    f"a threshold with no {name} is a number somebody typed; "
                    "value, publisher, version and jurisdiction travel together"
                )

    @property
    def cited(self) -> str:
        return f"k={self.k} ({self.publisher} {self.version}, {self.jurisdiction})"


# --- what the caller supplies ----------------------------------------------


class Read(Enum):
    """Whether a lane's contribution was actually read.

    Two states because rule 13 needs two: a lane that answered *nothing* and a
    lane that could not be reached must not produce the same row.
    """

    READ = "read"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class Reading:
    """One lane's contribution to one cell.

    `cell` is which cell this lane falls in — a section, an ensemble, a grade.
    `rung` is the rung of the *input* field, which is schema-level and therefore
    known even when the value is not; it is what the output inherits until the
    re-identification check passes.
    """

    lane_id: str
    subject_id: str
    cell: Optional[str]
    rung: Rung
    provenance: str = P_CITED
    state: Read = Read.READ
    why: str = ""

    def __post_init__(self):
        if not (self.lane_id or "").strip():
            raise ValueError("a reading with no lane is not lane-scoped (W-1)")
        if not (self.subject_id or "").strip():
            raise ValueError("a reading names whose record it is drawn from")
        # Raises for anything that is not a P-ladder rung (rule 14).
        stronger_provenance(P_CITED, self.provenance)
        if self.state is Read.READ and not (self.cell or "").strip():
            raise ValueError(
                "a reading that was read names the cell it falls in; an unnamed "
                "cell is an unreadable one and has its own state"
            )
        if self.state is Read.UNREADABLE and not (self.why or "").strip():
            raise ValueError(
                "an unreadable reading says why it could not be read; an absence "
                "with no reason is indistinguishable from a result (rule 13)"
            )

    @property
    def verified_tier(self) -> bool:
        """I-10: exports are drawn from verified-tier records only.

        `P1 measured` and `P2 attested`. A `P3` model output or a `P5`
        assumption is not export material, and — this is the half that matters —
        it does not get quietly dropped either, because dropping it is how the
        count gets smaller while still looking complete.
        """
        return not stronger_provenance(P_CITED, self.provenance)


@dataclass(frozen=True)
class AggregateRequest:
    """What is being asked for, for whom, and under what threshold.

    §7.2: *"purpose is not a field on a call; it is a property of a session…
    declared on entry, reconciled on exit."* The purpose declared here is what
    the announcement carries, so the reconciliation has something to compare
    against.

    `requested_by` is required and is not checked against a role list here:
    `records/conflict.py` owns the person-versus-role test and this module does
    not carry a fifth copy of it (rule 12).
    """

    purpose: str
    audience: Audience
    dimension: str
    population: str
    floor: CellFloor
    requested_by: str
    at: datetime

    def __post_init__(self):
        if not (self.purpose or "").strip():
            raise ValueError(
                "an aggregate with no declared purpose cannot be reconciled "
                "against one; §7.2's knock is the purpose mechanism"
            )
        if not (self.requested_by or "").strip():
            raise ValueError("an aggregate is asked for by somebody, and it is named")
        if not (self.population or "").strip():
            raise ValueError(
                "an aggregate names the population it is drawn over; without it "
                "two releases over the same students cannot be told apart"
            )
        dim = (self.dimension or "").strip().lower()
        if not dim:
            raise ValueError("an aggregate names what its cells range over")
        if dim in NOT_A_DIMENSION:
            raise ValueError(
                f"{self.dimension!r} is not a dimension; a cell per student is a "
                "disclosure with a table around it"
            )
        if "," in dim or "×" in dim or " x " in dim:
            raise ValueError(
                f"{self.dimension!r} names more than one dimension. A cross-tab "
                "over a few hundred students suppresses almost every cell, and "
                "the one cell it publishes is the disclosure"
            )


# --- the gate --------------------------------------------------------------


@dataclass(frozen=True)
class Gate:
    """Proof that every legitimacy condition was met, as a value.

    A token rather than a boolean, so that the multi-lane read cannot be reached
    without one. The conditions are re-checked here as well as in
    `_legitimate`, because a `Gate` a caller constructed by hand would otherwise
    be the side door §7.4 I-10 says the seam is not.
    """

    request: AggregateRequest
    lanes: Tuple[str, ...]
    ceiling: Rung

    def __post_init__(self):
        if self.request.audience is Audience.PUBLIC:
            raise NotGated(
                "a public release is not this module's to make: suppression has "
                "to be computed once over everything that will ever be "
                "published, and nothing here can see that union"
            )
        if CEILING[self.request.audience] is not self.ceiling:
            raise NotGated(
                f"the ceiling {self.ceiling} is not the one declared for "
                f"{self.request.audience.value}"
            )
        if len(self.lanes) < 2:
            raise NotGated(
                f"{len(self.lanes)} lane(s): an aggregate over one lane is that "
                "student's record with a table drawn round it"
            )


def _legitimate(request: AggregateRequest, readings: Sequence[Reading],
                into: Optional[Ledger]) -> Gate:
    """The gate, with each condition its own refusal.

    Enforcement, not a ledger: `release()` has no path to a table that does not
    come through here, and `_many_lanes` will not read without the token this
    returns.
    """
    if into is None:
        raise NotGated(
            "an aggregate is announced or it is not issued: the harm is data "
            "leaving, and an export nobody recorded is the one that cannot be "
            "answered for afterwards (rule 9, §7.2)"
        )
    if not readings:
        raise NotGated(
            "an aggregate over no readings is unknown, not a table of zeros; a "
            "count derived from nothing is the vacuous pass §7 already names"
        )
    enforcement = [r for r in readings if r.rung is NEVER_SERVED]
    if enforcement:
        raise NotGated(
            f"{len(enforcement)} reading(s) at {NEVER_SERVED}: a count over the "
            "content of an enforced restriction is a rendering of it, and that "
            "rung is never rendered to anyone under any grant"
        )
    lanes = tuple(sorted({r.lane_id for r in readings}))
    return Gate(request, lanes, CEILING[request.audience])


def _many_lanes(readings: Sequence[Reading], gate: Gate) -> Tuple[str, ...]:
    """The sanctioned multi-lane read, and the only one in this package.

    `records/practice.py`'s `_one_lane` is untouched: a practice statistic still
    refuses to span lanes, because a ranking is a cross-lane read and W-3 seals
    them. An aggregate is a cross-lane read too, which is why it does not get to
    reuse that door — it gets its own, and the token is the difference.
    """
    if not isinstance(gate, Gate):
        raise NotGated(
            "a cross-lane read needs the gate's token; W-3 seals sibling lanes "
            "and an aggregate is the exception that has to say its conditions"
        )
    return tuple(sorted({r.lane_id for r in readings}))


# --- cells -----------------------------------------------------------------


class CellState(Enum):
    """What happened to one cell.

    The two suppressed states are distinct **inside** the result and identical
    **in the artifact** — see `_manifest`. Which case applied to a cell is a
    bound on that cell's value, so attributing it per cell would hand back part
    of what the suppression withheld.
    """

    RELEASED = "released"
    SUPPRESSED_SMALL = "suppressed_small_cell"
    SUPPRESSED_COMPLEMENT = "suppressed_complement"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class CellResult:
    """One cell, its disposition, and the rung the classifier derived for it.

    **No field here holds a lane id or a subject id, and that is structural
    rather than a convention.** This is the value every artifact is rendered
    from — `_render` hands the cell tuple to `_table`, `_readme` and `_manifest`
    and gives them nothing else about the people behind it — so an identifier
    that reaches a `CellResult` is one format string away from a published file.

    **Retired 2026-08-02: `contributors`.** Superseded by `_announce`'s own loop
    over `readings`, which had always been the real mechanism.

    It was a sixth field carrying the lane ids behind the cell, and its docstring
    said *"it is what the announcement is written from."* It was not.
    `_announce` walks `readings` directly and takes `lane_id` and `subject_id`
    off each `Reading`, because it writes one entry per reading into that lane's
    own chain (W-1) — a per-cell set of lane ids carries no subject and cannot
    record one lane twice for two cells, so this field could not have been the
    source and never was. It was no better a source for `Release.lanes`: that
    comes from `_many_lanes`, which is gated and derives its own set.

    **Nothing is newly authoritative, because the field never was.** It was
    populated positionally at both construction sites in `_cells` and read by no
    line in the tree — a declaration with nothing behind it, `docs/CROSSINGS.md`
    crossing one's pattern, in the module whose whole subject is that
    identifiers do not leak.

    **No stub is left.** A default of `()` would keep the hazard while providing
    nothing: the field exists, so a later edit fills it. Crossing one's
    prescription is to remove the ability rather than forbid the act, and with
    the field gone there is nowhere on this value for an identifier to sit.
    `tests/test_aggregate.py` holds both halves — the artifact text is still
    scanned for lane and student ids, and the cell values are now scanned too,
    because `why` is rendered only for an incomplete cell and a lane id sitting
    in the `why` of a released table would pass a scan of the text alone.
    """

    key: str
    state: CellState
    count: Optional[int]
    rung: Optional[Rung]
    why: str

    @property
    def suppressed(self) -> bool:
        return self.state in (CellState.SUPPRESSED_SMALL,
                              CellState.SUPPRESSED_COMPLEMENT)


class Aggregate(Enum):
    """What the release as a whole is."""

    RELEASED = "released"
    INCOMPLETE = "incomplete"      # an input failed; no count is published
    UNKNOWN = "unknown"            # not even the cells are known
    UNRELEASABLE = "unreleasable"  # suppression could not reach a fixpoint


# --- the re-identification check, and the bridge to the classifier ----------


def _descriptor_for(key: str, inputs: Sequence[Rung], passed: bool) -> Descriptor:
    """The named middle between this module's decision and the ladder's rule.

    The pair is *"suppression decides whether a cell is safe"* and *"the ladder
    decides what rung that makes it"*, and rule 12 says name the reconciler in
    the same commit as the pair. This is it, and it is deliberately thin: it
    reports `passed_reidentification_check` and the rungs of the inputs, and it
    makes **no** claim about what rung comes out. `records/classify.py` step 2a
    owns that, and re-deriving `max`-of-inputs here would be the second spelling
    §16 keeps recording.
    """
    if not inputs:
        raise NotGated(
            f"cell {key!r} has no inputs; a derived field with nothing behind it "
            "reaches L2 through step 2 with nothing having looked at it, which "
            "is the fail-open §18 item 14 was closed to stop"
        )
    return Descriptor(
        name=f"aggregate:{key}",
        identifies_a_person=False,
        derived_from=tuple(inputs),
        passed_reidentification_check=passed,
    )


def _rung_for(key: str, inputs: Sequence[Rung], passed: bool) -> Tuple[Rung, str]:
    """Run the real classifier over one cell and refuse to guess for it."""
    got = classify(_descriptor_for(key, inputs, passed))
    if got.decision is not Decision.DECIDED or got.rung is None:
        raise NotGated(
            f"cell {key!r} classified {got.decision.value}: {got.reason}. An "
            "unclassified field is a build failure, not a default"
        )
    return got.rung, got.reason


# --- suppression -----------------------------------------------------------


def _determined(residual: int, bounds: Sequence[int]) -> bool:
    """Whether any suppressed cell's feasible interval collapses to one value.

    `residual` is what the published cells leave over against the total;
    `bounds` is the upper bound each suppressed cell is known to obey — `k-1`
    for a cell suppressed as a small cell, and the residual itself for a cell
    suppressed as a complement, since the latter says nothing about its own
    size.

    For a cell `i`: it lies in `[max(0, residual - Σ_{j≠i} bounds_j),
    min(bounds_i, residual)]`. When the low end reaches the high end the reader
    has the number, and a suppression that hands back the number is not one.

    The two cases that matter fall out rather than being special-cased: one
    suppressed cell against a known total is always determined, and a residual
    of zero determines every suppressed cell at once.
    """
    if not bounds:
        return False
    total_bound = sum(bounds)
    for i, own in enumerate(bounds):
        high = min(own, residual)
        low = max(0, residual - (total_bound - own))
        if low >= high:
            return True
    return False


def _suppress(counts: Dict[str, int], floor: CellFloor
              ) -> Tuple[Dict[str, CellState], bool]:
    """Primary then complementary suppression, to a fixpoint.

    Returns the per-cell state and whether the fixpoint was reached. The total
    is treated as **known** unconditionally, because it is: the size of a
    section is countable by anyone standing in front of it, and a suppression
    scheme that assumes otherwise is protecting against a reader who does not
    exist.
    """
    state = {key: (CellState.SUPPRESSED_SMALL if n < floor.k else CellState.RELEASED)
             for key, n in counts.items()}
    total = sum(counts.values())

    while True:
        held = [k for k, s in state.items()
                if s in (CellState.SUPPRESSED_SMALL, CellState.SUPPRESSED_COMPLEMENT)]
        if not held:
            return state, True
        residual = total - sum(counts[k] for k, s in state.items()
                               if s is CellState.RELEASED)
        bounds = [floor.k - 1 if state[k] is CellState.SUPPRESSED_SMALL else residual
                  for k in held]
        if not _determined(residual, bounds):
            return state, True
        candidates = sorted((counts[k], k) for k, s in state.items()
                            if s is CellState.RELEASED)
        if not candidates:
            return state, False
        state[candidates[0][1]] = CellState.SUPPRESSED_COMPLEMENT


# --- the release -----------------------------------------------------------


@dataclass(frozen=True)
class Release:
    """An aggregate, its disposition, its artifacts and its announcement."""

    request: AggregateRequest
    state: Aggregate
    cells: Tuple[CellResult, ...]
    artifacts: Tuple[Artifact, ...]
    announced: Ledger
    lanes: Tuple[str, ...]

    @property
    def released(self) -> Tuple[CellResult, ...]:
        return tuple(c for c in self.cells if c.state is CellState.RELEASED)

    @property
    def suppressed(self) -> Tuple[CellResult, ...]:
        return tuple(c for c in self.cells if c.suppressed)

    @property
    def incomplete(self) -> Tuple[CellResult, ...]:
        return tuple(c for c in self.cells if c.state is CellState.INCOMPLETE)


def _cells(readings: Sequence[Reading], gate: Gate) -> Tuple[
        Tuple[CellResult, ...], Aggregate]:
    """Tally, suppress, classify. Every branch that loses a reading is a state."""
    lost = [r for r in readings if r.state is Read.UNREADABLE or not r.verified_tier]

    # A reading whose *cell* is unknown could belong to any of them, so there is
    # no cell to mark and no total to stand on. The whole aggregate is unknown,
    # which is the only honest answer and is not a table of smaller numbers.
    blind = [r for r in lost if not (r.cell or "").strip()]

    by_cell: Dict[str, List[Reading]] = {}
    for r in readings:
        key = (r.cell or "").strip()
        if key:
            by_cell.setdefault(key, []).append(r)

    if blind or not by_cell:
        why = (f"{len(blind)} reading(s) could not be read and do not say which "
               "cell they fall in; every cell is affected and none can be named"
               if blind else "no reading names a cell")
        rungs = tuple(r.rung for r in readings)
        rung, _ = _rung_for("*", rungs, False)
        return ((CellResult("*", CellState.INCOMPLETE, None, rung, why),),
                Aggregate.UNKNOWN)

    spoiled = {(r.cell or "").strip(): r for r in lost}
    counts = {key: sum(1 for r in rows if r.state is Read.READ and r.verified_tier)
              for key, rows in by_cell.items()}
    state, settled = _suppress(counts, gate.request.floor)

    # One unreadable input stops every count in the table. The count that would
    # otherwise be published is not wrong by a little; it is a complete-looking
    # number over an incomplete population, and the reader has no way to tell.
    if spoiled:
        for key in state:
            state[key] = CellState.INCOMPLETE

    out: List[CellResult] = []
    for key in sorted(by_cell):
        rows = by_cell[key]
        cell_state = state[key]
        passed = cell_state is CellState.RELEASED and settled
        rung, reason = _rung_for(key, tuple(r.rung for r in rows), passed)
        why = reason if cell_state is not CellState.INCOMPLETE else (
            spoiled[key].why if key in spoiled
            else "another cell in this table has an input that could not be read")
        out.append(CellResult(
            key, cell_state,
            counts[key] if cell_state is CellState.RELEASED else None,
            rung, why))

    if not settled:
        return tuple(out), Aggregate.UNRELEASABLE
    if spoiled:
        return tuple(out), Aggregate.INCOMPLETE
    return tuple(out), Aggregate.RELEASED


def _within_ceiling(cells: Sequence[CellResult], ceiling: Rung) -> None:
    """No cell carries a number above what its audience may be served at.

    **A tripwire, and named as one.** With the classifier behaving, a cell that
    carries a count has passed the re-identification check and is `L2`, which is
    at or below every audience this gate admits — so nothing in the rest of this
    module can make this fire, exactly like `records/orders.py`'s
    *"an ending never shortens the graph"*. It is ablated the way that one is:
    by the forbidden act rather than by the branch, moving an audience's ceiling
    down and requiring the release to stop.

    It is not redundant with the suppression pass. A table whose inputs are
    already `L2` produces suppressed cells that are *also* `L2`, so the ladder
    alone would let them through — suppression is what protects them, and this
    checks the other direction.
    """
    over = [c for c in cells if c.count is not None and outranks(c.rung, ceiling)]
    if over:
        raise NotGated(
            f"{len(over)} cell(s) carry a count at a rung above {ceiling}, which "
            f"is what this audience may be served at: "
            + ", ".join(f"{c.key} ({c.rung})" for c in over)
        )


# --- the announcement ------------------------------------------------------


def _outcome(state: CellState) -> Outcome:
    """What one lane's contribution did, in the disclosure log's vocabulary."""
    if state is CellState.RELEASED:
        return Outcome.PAYLOAD
    if state is CellState.INCOMPLETE:
        return Outcome.UNKNOWN
    return Outcome.REFUSED


def _announce(into: Ledger, request: AggregateRequest, readings: Sequence[Reading],
              cells: Sequence[CellResult]) -> Ledger:
    """Record the issuance in every contributing lane's own chain.

    **Every lane, not every released lane.** A trail that carries only the
    disclosures cannot answer *was the suppression working*, and rule 10 is
    explicit that an audit trail which records only agreement is not one. A lane
    whose contribution was suppressed is recorded `REFUSED`; a lane that could
    not be read is recorded `UNKNOWN`; and both go in the lane's own chain,
    because W-1 wants a trail per lane rather than one trail with a column
    naming which student a row is about.
    """
    by_cell = {c.key: c for c in cells}
    fallback = cells[0] if cells else None
    authority = (f"{request.audience.value} · purpose: {request.purpose} · "
                 f"{request.floor.cited}")
    ledger = into
    for r in sorted(readings, key=lambda r: (r.lane_id, r.subject_id, r.cell or "")):
        cell = by_cell.get((r.cell or "").strip(), fallback)
        if cell is None:
            continue
        outcome = _outcome(cell.state) if r.state is Read.READ else Outcome.UNKNOWN
        serving = Serving(outcome,
                          None,
                          cell.rung,
                          f"aggregate over {request.dimension}: {cell.why}")
        ledger = ledger.record(
            serving, lane_id=r.lane_id, principal_id=request.requested_by,
            subject_id=r.subject_id, field_name=f"aggregate:{request.dimension}",
            at=request.at, authority=authority)
    return ledger


# --- rendering -------------------------------------------------------------


def _table(cells: Sequence[CellResult]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(("cell", "state", "count", "rung"))
    for c in cells:
        # One word for both suppression cases. Which case applied is a bound on
        # the cell's value, and handing that back would undo part of the
        # suppression it is reporting.
        shown = "suppressed" if c.suppressed else c.state.value
        w.writerow((c.key, shown,
                    "" if c.count is None else str(c.count),
                    str(c.rung) if c.rung else ""))
    return buf.getvalue()


def _readme(request: AggregateRequest, cells: Sequence[CellResult],
            state: Aggregate) -> str:
    released = [c for c in cells if c.state is CellState.RELEASED]
    held = [c for c in cells if c.suppressed]
    partial = [c for c in cells if c.state is CellState.INCOMPLETE]
    lines = [
        "AGGREGATE REPORT",
        "================",
        "",
        f"Purpose:     {request.purpose}",
        f"For:         {request.audience.value.replace('_', ' ')}",
        f"Population:  {request.population}",
        f"Counts by:   {request.dimension}",
        f"Issued:      {request.at.date().isoformat()}, at the request of "
        f"{request.requested_by}",
        "",
        "WHAT THIS IS",
        "------------",
        "Counts only. No student is named here, and no row in this folder is",
        "about one person.",
        "",
        "SMALL COUNTS ARE WITHHELD, AND SO ARE SOME LARGE ONES",
        "-----------------------------------------------------",
        f"A count below {request.floor.k} is not shown. A count of one over a",
        "small group names a child even though no name appears, so the number",
        "is withheld rather than rounded or blurred.",
        "",
        "Further counts are withheld where publishing them would let the",
        "withheld ones be worked out by subtraction. That is why a large count",
        "is sometimes missing too: on its own it would give away a small one.",
        "",
        f"The threshold is not ours to pick: {request.floor.cited}.",
        "",
    ]
    if state is Aggregate.UNKNOWN:
        lines += [
            "THIS REPORT HAS NO COUNTS",
            "-------------------------",
            "Part of the underlying record could not be read, and it is not known",
            "which counts it would have affected. A smaller number would look",
            "complete and would not be, so no number is given. This is not an",
            "empty result: it is an unavailable one.",
            "",
        ]
    elif state is Aggregate.INCOMPLETE:
        lines += [
            "THIS REPORT HAS NO COUNTS",
            "-------------------------",
            f"{len(partial)} of {len(cells)} group(s) draw on a record that could",
            "not be read. Publishing the rest would give you numbers that look",
            "complete and are not, so every count in this report is withheld.",
            "The affected groups are named in cells.csv.",
            "",
        ]
    elif state is Aggregate.UNRELEASABLE:
        lines += [
            "THIS REPORT HAS NO COUNTS",
            "-------------------------",
            "There is no way to publish any count in this table without the",
            "withheld ones being recoverable by subtraction. Nothing is shown.",
            "",
        ]
    lines += [
        "WHAT IS IN THIS FOLDER",
        "----------------------",
        "  cells.csv     one row per group, with its count or the word",
        "                suppressed. Open it in any spreadsheet.",
        "  MANIFEST.txt  a list of these files with a checksum and a count of",
        "                what was withheld, so nothing goes missing quietly.",
        "  README.txt    this file.",
        "",
        f"There are {len(cells)} group(s): {len(released)} shown, "
        f"{len(held)} withheld, {len(partial)} unavailable.",
        "",
        "WHO KNOWS THIS WAS MADE",
        "-----------------------",
        "Every record this drew on carries a dated entry saying so, in that",
        "student's own file. That is true of the records whose counts were",
        "withheld as well.",
        "",
    ]
    return "\n".join(lines)


def _manifest(request: AggregateRequest, cells: Sequence[CellResult],
              state: Aggregate, announced: Ledger,
              artifacts: Sequence[Artifact]) -> str:
    """The manifest, in `records/export.py`'s format.

    Two writers, one format, and the middle is that `export.verify()` is the
    only reader of either — `tests/test_aggregate.py` runs an aggregate bundle
    through it. A second verifier would be the pair rule 12 forbids.

    **The counts here are of cells, never of students.** A total is a number
    about people, and a manifest that reports one hands back exactly what the
    suppression withheld.

    The chain head is written in because it cannot be faked: an aggregate that
    was never announced has no head to write, so the artifact is unbuildable
    rather than merely unrecorded (rule 9). It is the **whole-programme** fold
    from `records/witness.py` rather than the per-lane heads, because
    `Ledger.anchors()` says publishing those individually leaks which lanes
    exist — and its entry **count** is left out for the same reason the totals
    are: a count of entries over a fresh chain is a count of students.
    """
    small = sum(1 for c in cells if c.state is CellState.SUPPRESSED_SMALL)
    comp = sum(1 for c in cells if c.state is CellState.SUPPRESSED_COMPLEMENT)
    partial = [c for c in cells if c.state is CellState.INCOMPLETE]
    head = anchor_for_ledger(announced, request.at).head
    lines = [
        "MANIFEST",
        "========",
        f"purpose:     {request.purpose}",
        f"audience:    {request.audience.value}",
        f"population:  {request.population}",
        f"issued:      {request.at.isoformat()} by {request.requested_by}",
        f"state:       {state.value}",
        f"threshold:   {request.floor.cited}",
        "",
        f"cells:       {len(cells)}",
        f"released:    {sum(1 for c in cells if c.state is CellState.RELEASED)}",
        f"suppressed:  {small + comp}",
        f"incomplete:  {len(partial)}",
        f"complementary suppression: {'applied' if comp else 'not needed'}",
        "",
        "announced in the contributing records; disclosure chain now at",
        f"  {head}",
        "",
        "FILES (sha256, bytes, name)",
    ]
    for a in artifacts:
        lines.append(f"  {a.digest}  {len(a.text.encode('utf-8')):>8}  {a.name}")
    held = [c for c in cells if c.suppressed]
    if held:
        lines += ["", "WITHHELD GROUPS (named, no number)"]
        for c in held:
            lines.append(f"  {c.key}")
        lines += [
            "",
            "Which of the two reasons applies to which group is deliberately not",
            "stated: the reason is itself a bound on the withheld number.",
        ]
    if partial:
        lines += ["", "UNAVAILABLE GROUPS (an input could not be read)"]
        for c in partial:
            lines.append(f"  {c.key}  — {c.why}")
    lines += [
        "",
        "A file missing from this list, or a checksum that does not match, means",
        "the bundle was altered after it was made.",
        "",
    ]
    return "\n".join(lines)


def _render(request: AggregateRequest, cells: Sequence[CellResult],
            state: Aggregate, announced: Ledger) -> Tuple[Artifact, ...]:
    """Artifacts, built over the announcement. The caller writes them."""
    body = (
        Artifact("README.txt", "text/plain", _readme(request, cells, state)),
        Artifact("cells.csv", "text/csv", _table(cells)),
    )
    return body + (Artifact("MANIFEST.txt", "text/plain",
                            _manifest(request, cells, state, announced, body)),)


def release(request: AggregateRequest, readings: Sequence[Reading], *,
            into: Optional[Ledger] = None) -> Release:
    """Issue one aggregate: gate, tally, suppress, classify, announce, render.

    The order is the argument. The gate refuses before anything is counted; the
    classifier decides the rung rather than this module; the announcement
    happens before the artifact exists and is what the artifact is built over.
    """
    gate = _legitimate(request, readings, into)
    lanes = _many_lanes(readings, gate)
    cells, state = _cells(readings, gate)
    _within_ceiling(cells, gate.ceiling)
    announced = _announce(into, request, readings, cells)
    return Release(request, state, cells,
                   _render(request, cells, state, announced), announced, lanes)


# --- the differencing ledger -----------------------------------------------


@dataclass(frozen=True)
class Overlap:
    """Two releases drawn over one population. A risk, not a verdict."""

    population: str
    purposes: Tuple[str, ...]
    dimensions: Tuple[str, ...]


def differencing_risk(releases: Sequence[Release]) -> Tuple[Overlap, ...]:
    """Where two releases were drawn over the same population.

    **This is a ledger, not an enforcement, and the distinction is the point
    (rule 18).** Nothing routes through it; `release()` neither calls it nor
    consults it. Publishing participation by section, by ensemble and by grade
    over one set of students is three views of one table and the reader
    subtracts — closing that needs suppression computed once over the union of
    everything that will ever be published, which is Gaussian elimination over
    linked tables and is not built here. What this does is make the overlap
    *visible* so a human decides, which is the honest shape for a mechanism the
    tree does not have.
    """
    seen: Dict[str, List[Release]] = {}
    for r in releases:
        seen.setdefault(r.request.population.strip().lower(), []).append(r)
    out = []
    for _, group in sorted(seen.items()):
        if len(group) > 1:
            out.append(Overlap(
                group[0].request.population,
                tuple(sorted(g.request.purpose for g in group)),
                tuple(sorted(g.request.dimension for g in group))))
    return tuple(out)
