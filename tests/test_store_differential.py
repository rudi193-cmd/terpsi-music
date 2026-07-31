"""The named middle for the read predicate's two implementations (rule 12, §16).

`docs/PLAN-STORE.md` decision 4: *"The read predicate is compiled at the store as
row-level security, with a differential middle. The lane seal, the edge check and
the rung ceiling exist as RLS policies per lane, AND as the Python predicates
already in `records/serving.py`. Two implementations of one rule is §16's pair,
so the middle ships in the same commit: a differential suite that drives the same
forbidden acts through both and fails on any disagreement."*

**This file is that suite, and it is the reconciler named in
`tools/conform.py`'s `NAMED_MIDDLES`.** One case set — `CASES`, and the count is
derived from it wherever it is reported rather than written into prose (rule 17)
— each case driven twice:

* through **`records/serving.py::serve`** with rows read out of the cluster — the
  real `Edge`, `Envelope` and `Field` types, not doubles;
* through **the live database under `migrations/003_row_security.sql`**, as
  `terpsi_app`, with the acting principal in the GUC and **no Python predicate
  anywhere in the path** — one `SELECT count(*)` and whatever the policies say.

A disagreement in either direction fails. So does a case whose two layers agree
on the wrong answer, which is why every case also declares what it expects: two
implementations that are broken the same way agree perfectly, and a middle that
only checked agreement would report green on a store that serves nothing and a
predicate that refuses everything.

---

**The question both layers are asked, stated exactly, because it is the whole
design of this file.**

    May this principal be served an `L3` field in this lane, at this instant,
    with no grant source consulted?

`L3` and not `L1`, and the choice is not arbitrary. Below `rungs.DERIVE_AT` the
predicate serves a payload with **no entitlement edge at all** — a rehearsal time
is not sealed by standing — so at `L1`/`L2` `serve()` is deliberately more
permissive than these policies and the store is the binding layer. At `L3` and
above the two answer the same question: the lane seal, then a live edge to this
subject. `grants=None` keeps `serving._ceiling` out of it, because the ceiling
compares a *field's* rung against a *grant's* and a row does not know which rung
is being asked for — that half is Python-only and
`migrations/003_row_security.sql`'s header says so.

The mapping from each layer's answer to a boolean, in full:

* SQL: `count(*) = 1` for the case's `lane_entry` row, read as the app role.
* Python: `serve(...).outcome is Outcome.PAYLOAD`.

Two mappings this file makes and names, because a mapping is where two
implementations drift quietly:

* **An ended envelope.** `records/crossing.Envelope` carries no `invalid_at`
  field — the type predates the table. A row that was dated closed is adapted as
  an envelope whose expiry is `least(expires_at, invalid_at)`, which is exactly
  what `envelope_permits` spells as `expires_at > now() AND (invalid_at IS NULL
  OR invalid_at > now())`.
* **An unnamed principal.** The GUC unset has no counterpart in `serve()`, whose
  `Principal` always carries an id. It is adapted as a principal id that appears
  in no edge — *an identity nothing knows*, against SQL's *no identity at all*.
  The two are different questions and the case asserts they coincide; if they
  ever stop coinciding, that is a finding and not a fixture problem.

**Scope edges are absent from the Python side and that is not a gap.** An edge
pointing at an ensemble carries no lane and no subject, so `records.serving.Edge`
has nowhere to put it; `holds_live_edge` matches on `target_lane_id` and never
sees it either. *"Nguyen is staff of the drumline"* is true and entitles nothing
about any one student's lane, in both layers, and the case set includes him for
exactly that reason.

Needs a database. No skip — see `tests/cluster.py`. Without a cluster this exits
2 with a loud `UNKNOWN`, and `tools/conform.py`'s `row-security-differential`
row reports `UNKNOWN` rather than `PASS`.

    python3 tests/test_store_differential.py
"""

from __future__ import annotations

import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import ClusterUnknown, Database, available, installed, report  # noqa: E402

from records.crossing import Envelope  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import (Edge, Field, Outcome, Principal,  # noqa: E402
                             _acting_ward, serve)
from store.session import name_principal  # noqa: E402

# --- the people, the lanes, the standing ------------------------------------
#
# Domain-plausible on purpose: a guardian who is also an enrolled adult is the
# ordinary case that makes W-3 bite, because reading her own child's lane means
# crossing out of her own. Every lane below is one row and every edge is one row;
# the world is wide rather than deep so that each case varies exactly one thing.

BEN = uuid.UUID("11111111-0000-0000-0000-0000000000b1")   # a ward
CARA = uuid.UUID("11111111-0000-0000-0000-0000000000ca")  # another ward
DEE = uuid.UUID("11111111-0000-0000-0000-0000000000de")
EVE = uuid.UUID("11111111-0000-0000-0000-0000000000e0")
FAY = uuid.UUID("11111111-0000-0000-0000-0000000000fa")
GIL = uuid.UUID("11111111-0000-0000-0000-000000000091")
ANN = uuid.UUID("11111111-0000-0000-0000-0000000000a0")   # guardian, and enrolled
ROB = uuid.UUID("11111111-0000-0000-0000-0000000000b0")   # director, no lane
NGUYEN = uuid.UUID("11111111-0000-0000-0000-0000000000e9")  # staff, no lane
#: A clinician who holds a live edge into one lane **and** carries the forged
#: `self` row into another. Both at once, deliberately: a forged self edge held
#: by somebody with no other standing is refused by the entitlement check
#: whatever the ward test does, so it cannot tell the two guards apart. Pam can.
PAM = uuid.UUID("11111111-0000-0000-0000-0000000000da")
OLD = uuid.UUID("11111111-0000-0000-0000-0000000000d1")   # standing ended
NOBODY = uuid.UUID("00000000-0000-0000-0000-000000000000")  # in no edge, anywhere

LANE = {
    BEN: uuid.UUID("22222222-0000-0000-0000-0000000000b1"),
    CARA: uuid.UUID("22222222-0000-0000-0000-0000000000ca"),
    DEE: uuid.UUID("22222222-0000-0000-0000-0000000000de"),
    EVE: uuid.UUID("22222222-0000-0000-0000-0000000000e0"),
    FAY: uuid.UUID("22222222-0000-0000-0000-0000000000fa"),
    GIL: uuid.UUID("22222222-0000-0000-0000-000000000091"),
    ANN: uuid.UUID("22222222-0000-0000-0000-0000000000a0"),
}
BORN = {BEN: "2010-05-01", CARA: "2012-09-14", DEE: "2011-03-03",
        EVE: "2011-07-07", FAY: "2010-11-11", GIL: "2012-01-20",
        ANN: "1979-02-02", ROB: "1971-06-06", NGUYEN: "1988-11-30",
        PAM: "1983-08-08", OLD: "1975-04-04"}
ENSEMBLE = uuid.UUID("aaaa1111-0000-0000-0000-000000000001")


def _id(tag: str) -> uuid.UUID:
    """A stable uuid from a short tag, so a failure names a row a human can find."""
    return uuid.uuid5(uuid.NAMESPACE_URL, "terpsi-differential/" + tag)


# --- one case -----------------------------------------------------------------


@dataclass(frozen=True)
class Case:
    """One forbidden — or permitted — act, and the guard that decides it.

    `reaches` is what BOTH layers must answer. `guard` names what does the
    deciding, so a case that starts passing for a new reason is visible: the
    house lesson is that a refusal which could be a different guard's is not
    evidence, and at this layer a refusal is a row count rather than an error
    string, so the attribution has to live in the case.
    """

    name: str
    principal: Optional[uuid.UUID]   # None models the unset GUC
    subject: uuid.UUID               # whose lane is being read
    reaches: bool
    guard: str


CASES: Tuple[Case, ...] = (
    # --- the three that must land. A guard that refuses everything is not a
    # --- guard, and a differential over a store that serves nothing agrees
    # --- perfectly with a predicate that refuses everything.
    Case("a director with a live edge reads the lane", ROB, BEN, True,
         "the entitlement edge (serving._entitling_edge / holds_live_edge)"),
    Case("the subject reads their own lane through the self edge", BEN, BEN, True,
         "the self edge (standing.is_self_edge / ward_lane)"),
    Case("a ward crosses under a live guardian-signed envelope", ANN, BEN, True,
         "the crossing envelope (crossing.permits / envelope_permits)"),

    # --- the seal, W-3 clause (b), with the entitlement edge held constant.
    # --- Ann holds a live guardian_of edge into every one of these lanes, so
    # --- the ONLY variable across the four is the envelope.
    Case("a ward crosses with no envelope at all", ANN, DEE, False,
         "W-3(b) between wards, default deny (serve's seal / reaches_lane)"),
    # **Not a direction case, and the name says so.** The envelope that exists
    # between Ben's lane and Cara's names neither of Ann's ends, so what refuses
    # her is the absence of an envelope *from her lane* — an envelope elsewhere
    # in the cluster opening a seal it does not name is its own forbidden act
    # and this is it. Direction itself is not attributable through a reach
    # comparison in this domain: it would need a principal who is a ward of one
    # lane AND holds an entitlement edge into another AND is covered by a
    # reversed envelope, and a ward never holds the second. It is asserted at
    # the function level instead —
    # `tests/test_store_rowsecurity.py::test_the_compiled_envelope_is_directional`
    # for the SQL and `tests/test_crossing.py::test_an_envelope_is_directional`
    # for the Python — and the report says which.
    Case("a ward crosses while an envelope between two other lanes exists",
         ANN, CARA, False,
         "an envelope opens only the seal it names (crossing.permits)"),
    Case("a ward crosses on an envelope dated closed", ANN, EVE, False,
         "invalid_at truncates the expiry (refusal 3)"),
    Case("a ward crosses on an envelope that expired", ANN, FAY, False,
         "the expiry W-5 requires (Envelope.live_at / expires_at > now())"),
    Case("a ward crosses on an envelope whose signer's standing has ended",
         ANN, GIL, False,
         "standing at the instant of USE, not of signature (crossing.permits)"),

    # --- the rest of the refusals.
    Case("a ward with no standing at all in another lane", CARA, BEN, False,
         "W-3(b) between wards, default deny"),
    Case("staff whose only edge points at an ensemble", NGUYEN, BEN, False,
         "a scope edge entitles no lane (W-2, refusal 5)"),
    Case("a guardian whose standing ended", OLD, BEN, False,
         "the edge is dated, and an expired edge is not an edge (refusal 3)"),
    Case("a forged self edge entitles nothing in the lane it names",
         PAM, GIL, False,
         "standing.is_self_edge / holds_live_edge's lane.subject_id = holder_id"),
    # The mirror, and the one that catches a ward test which stopped checking
    # whether the self edge is genuine: a forged row must not *seal its holder
    # in* either. Pam holds a live clinician edge into Ben's lane and reaches
    # it; if the forged row made her a ward of Gil's, this read would become a
    # crossing and the store would refuse what the predicate serves.
    Case("a forged self edge does not seal its holder into a lane",
         PAM, BEN, True,
         "serving._acting_ward / ward_lane's lane.subject_id = holder_id"),
    Case("no principal named at all", None, BEN, False,
         "an anonymous session is not an entitled one (rule 13)"),
)


# --- the world ----------------------------------------------------------------


def _seed(owner) -> Dict[uuid.UUID, uuid.UUID]:
    """Every person, lane, edge, envelope and entry the case set needs.

    Returns `{subject_id: entry_id}` — one `lane_entry` per lane, which is the
    row both layers are asked about. Its `kind` column is the field: the
    classification registry seeded in `migrations/001_lanes.sql` puts
    `lane_entry.kind` at `PII_MINOR`/`L3`, so the `L3` this suite drives is the
    rung the cluster itself records for the column being read, not one chosen to
    make the comparison work.
    """
    entries: Dict[uuid.UUID, uuid.UUID] = {}
    with owner.cursor() as cur:
        for who, born in BORN.items():
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        for who, lane in LANE.items():
            cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                        (lane, who, "everything, as CSV, on request"))
        cur.execute("INSERT INTO scope_object VALUES (%s,'Ensemble','Drumline',"
                    "now(),now(),NULL)", (ENSEMBLE,))

        def edge(tag, kind, holder, lane, valid, invalid=None):
            cur.execute(
                "INSERT INTO edge VALUES (%s,%s,%s,%s,NULL,'enrolment form',"
                "now(), now() + %s::interval, "
                "CASE WHEN %s::text IS NULL THEN NULL ELSE now() + %s::interval END)",
                (_id(tag), kind, holder, lane, valid, invalid, invalid))

        # The subjects' own standing.
        edge("self-ben", "self", BEN, LANE[BEN], "-1 year")
        edge("self-cara", "self", CARA, LANE[CARA], "-1 year")
        # Ann is enrolled in the community ensemble and holds her own lane. That
        # is what makes her a ward for W-3's purposes and why reading her own
        # child's file is a crossing.
        edge("self-ann", "self", ANN, LANE[ANN], "-1 year")

        # Ann's guardianship, live, over six lanes. Held constant across the
        # seal cases so the envelope is the only thing that varies.
        for who in (BEN, CARA, DEE, EVE, FAY, GIL):
            edge(f"g-ann-{who}", "guardian_of", ANN, LANE[who], "-1 year")

        edge("d-rob-ben", "director_of", ROB, LANE[BEN], "-1 year")
        # Ended by a date, never by a delete (refusal 3).
        edge("g-old-ben", "guardian_of", OLD, LANE[BEN], "-2 year", "-1 year")
        edge("g-old-gil", "guardian_of", OLD, LANE[GIL], "-2 year", "-1 year")

        cur.execute(
            "INSERT INTO edge VALUES (%s,'staff_of',%s,NULL,%s,'staff roster',"
            "now(),now(),NULL)", (_id("s-nguyen"), NGUYEN, ENSEMBLE))
        edge("c-pam-ben", "clinician_for", PAM, LANE[BEN], "-1 year")

        # The five envelopes are written out rather than looped: each differs
        # from the live one in exactly one field, and a loop would hide which.
        cur.execute(
            "INSERT INTO crossing_envelope VALUES (%s,%s,%s,'reading my child''s "
            "file from my own lane',%s,%s,now(),now() + interval '30 day',now(),"
            "now(),NULL)",
            (_id("env-live"), LANE[ANN], LANE[BEN], ANN, _id(f"g-ann-{BEN}")))
        # Direction: this permits BEN's lane to read CARA's, and Ann asks the
        # other way round.
        cur.execute(
            "INSERT INTO crossing_envelope VALUES (%s,%s,%s,'sibling carpool',"
            "%s,%s,now(),now() + interval '30 day',now(),now(),NULL)",
            (_id("env-direction"), LANE[BEN], LANE[CARA], ANN, _id(f"g-ann-{CARA}")))
        # Dated closed (refusal 3).
        cur.execute(
            "INSERT INTO crossing_envelope VALUES (%s,%s,%s,'handover to the new "
            "counsellor',%s,%s,now() - interval '2 day',now() + interval '30 day',"
            "now(),now() - interval '2 day',now() - interval '1 day')",
            (_id("env-ended"), LANE[ANN], LANE[EVE], ANN, _id(f"g-ann-{EVE}")))
        # Expired on its own terms.
        cur.execute(
            "INSERT INTO crossing_envelope VALUES (%s,%s,%s,'one weekend trip',"
            "%s,%s,now() - interval '2 day',now() - interval '1 day',now(),"
            "now() - interval '2 day',NULL)",
            (_id("env-expired"), LANE[ANN], LANE[FAY], ANN, _id(f"g-ann-{FAY}")))
        # Signed while the signer still had standing; the standing has since
        # ended. 001's trigger checks the signature date, this suite checks the
        # reading date, and they are deliberately different questions.
        cur.execute(
            "INSERT INTO crossing_envelope VALUES (%s,%s,%s,'handover',%s,%s,"
            "now() - interval '18 month',now() + interval '30 day',now(),"
            "now() - interval '18 month',NULL)",
            (_id("env-signer-ended"), LANE[ANN], LANE[GIL], OLD, _id("g-old-gil")))

        # The forged self edge. 001's `edge_self_holder_is_subject` refuses it at
        # write time, so it is inserted with that trigger disabled — the
        # workflow's own `ALTER TABLE … DISABLE TRIGGER` move, for the same
        # reason: a guard nobody can get past leaves the read-side filter
        # untested, and the read-side filter is what this suite is about.
        cur.execute("ALTER TABLE edge DISABLE TRIGGER edge_self_holder_is_subject")
        edge("forged-self", "self", PAM, LANE[GIL], "-1 year")
        cur.execute("ALTER TABLE edge ENABLE TRIGGER edge_self_holder_is_subject")

        for who, lane in LANE.items():
            entries[who] = _id(f"entry-{who}")
            cur.execute(
                "INSERT INTO lane_entry (entry_id, lane_id, kind, author_id, "
                " created_at, valid_at) VALUES (%s,%s,'allergy',%s,now(),now())",
                (entries[who], lane, ANN))
    owner.commit()
    return entries


@dataclass(frozen=True)
class World:
    owner: object
    app: object
    entries: Dict[uuid.UUID, uuid.UUID]


@contextmanager
def a_world():
    """A throwaway database with the whole case set seeded into it."""
    with Database() as db:
        owner, app = installed(db)
        try:
            yield World(owner, app, _seed(owner))
        finally:
            app.close()
            owner.close()


# --- layer one: the live database under RLS, with no Python predicate ---------


def through_rls(world: World, case: Case) -> Tuple[bool, datetime]:
    """Does the app role reach this case's row? **Raw SQL, as `terpsi_app`.**

    Nothing in `records/` is on this path. The acting principal goes into the
    GUC and one `SELECT count(*)` comes back; whatever filters it is a policy in
    `migrations/003_row_security.sql`.

    Returns the reach and the instant the policies evaluated at — `now()` is
    transaction-start, so reading it here and handing it to `serve()` is what
    makes the two layers ask about the same moment rather than about two moments
    a few milliseconds apart.
    """
    app = world.app
    app.rollback()                      # a fresh transaction, so `now()` is fresh
    if case.principal is not None:
        name_principal(app, case.principal)
    at = app.execute("SELECT now()").fetchone()[0]
    n = app.execute("SELECT count(*) FROM lane_entry WHERE entry_id = %s",
                    (world.entries[case.subject],)).fetchone()[0]
    app.rollback()
    return n == 1, at


# --- layer two: records/serving.py, over the same rows ------------------------


def _edges(owner) -> Tuple[Edge, ...]:
    """Every lane-targeted edge in the cluster, as `records.serving.Edge`.

    The inner join drops scope edges: they carry no subject, `Edge` has nowhere
    to put one, and `holds_live_edge` never matches one either. Read as the
    owner, which bypasses row security — the Python layer must be handed the
    rows a predicate would be handed, not the rows the policies already filtered,
    or the differential would be comparing RLS against itself.
    """
    rows = owner.execute(
        "SELECT e.kind, e.holder_id, l.subject_id, e.valid_at, e.invalid_at, "
        "       e.created_at "
        "  FROM edge e JOIN lane l ON l.lane_id = e.target_lane_id").fetchall()
    return tuple(Edge(kind, str(holder), str(subject), valid_at, invalid_at,
                      created_at=created_at)
                 for kind, holder, subject, valid_at, invalid_at, created_at in rows)


def _envelopes(owner) -> Tuple[Envelope, ...]:
    """Every crossing envelope, as `records.crossing.Envelope`.

    **`invalid_at` truncates the expiry** — see the module docstring. The type
    carries no ending of its own, and mapping a dated-closed envelope onto a
    shortened expiry is the only faithful reading: `Envelope.live_at` is
    `signed_at <= when < expires_at`, and an envelope revoked on the 5th is not
    live on the 6th however far its nominal expiry runs.
    """
    rows = owner.execute(
        "SELECT from_lane_id, to_lane_id, purpose, signed_by, signed_at, "
        "       expires_at, invalid_at FROM crossing_envelope").fetchall()
    out = []
    for frm, to, purpose, signer, signed_at, expires_at, invalid_at in rows:
        ends = expires_at if invalid_at is None else min(expires_at, invalid_at)
        out.append(Envelope(str(frm), str(to), purpose, str(signer),
                            signed_at, ends))
    return tuple(out)


#: The two ways a caller can name the read's *origin* lane, which is `serve()`'s
#: `lane_id` argument and the one input the store has no column for.
#:
#: * `SESSION` — the origin the store itself determines: a principal who is a
#:   ward reads *from* their own lane, everybody else's read names the lane it is
#:   about. This is the spelling `migrations/003_row_security.sql` compiles, and
#:   it is the one the agreement assertion uses.
#: * `NAMED` — the origin a caller supplies when it names the lane it is reading
#:   and nothing else, which is the natural spelling of `WHERE lane_id = %s` and
#:   is what a surface writes when nobody told it about W-3.
#:
#: **Two spellings and not one, because the seal has two clauses and the first
#: hides the second.** Under `SESSION` a ward's origin already differs from the
#: lane being read, so `serve()` enters the seal through clause (a) — *the read
#: names a different lane* — and clause (b), *the reader is another ward*, never
#: has to fire. Ablating clause (b) therefore survived this suite when it was
#: first written, which is rule 19's whole point arriving as a real miss rather
#: than as a worry: a middle that cannot be shown to fail on a guard is not
#: covering that guard. `NAMED` is what makes clause (b) load-bearing.
SESSION, NAMED = "session", "named"


def through_predicate(world: World, case: Case, at: datetime,
                      origin_as: str = SESSION) -> bool:
    """Does `records/serving.py::serve` hand over the payload? **No SQL predicate.**

    The rows come out of the cluster and everything after that is the module
    `docs/PLAN-STORE.md` calls the other implementation. The `SESSION`/`NAMED`
    choice is the origin lane, above; the ward derivation uses
    `serving._acting_ward` rather than a second rule of this file's own, because
    the ward test is a guard and a test that re-implements the guard it is
    checking has checked its own copy.
    """
    edges = _edges(world.owner)
    envelopes = _envelopes(world.owner)
    subject_lane = {str(s): str(l) for s, l in LANE.items()}

    who = str(case.principal) if case.principal is not None else str(NOBODY)
    target_lane = subject_lane[str(case.subject)]

    if origin_as == NAMED:
        origin = target_lane
    else:
        ward = _acting_ward(who, edges, at)
        origin = subject_lane[ward] if ward is not None else target_lane

    fld = Field(lane_id=target_lane, subject_id=str(case.subject),
                name="lane_entry.kind", rung=Rung.L3, category=None,
                payload="allergy", instruction=None)
    got = serve(fld, Principal(who), edges, at, lane_id=origin,
                envelopes=envelopes, grants=None)
    return got.outcome is Outcome.PAYLOAD


# --- the middle ---------------------------------------------------------------


def test_the_two_implementations_agree_on_every_case():
    """**The reconciler.** Any disagreement, in either direction, is a failure.

    The report names the case, both answers and the guard, because *"the layers
    disagree"* is not a finding anybody can act on and *"the store reached a lane
    the predicate sealed, on the envelope-direction case"* is.
    """
    with a_world() as world:
        disagreed = []
        for case in CASES:
            in_store, at = through_rls(world, case)
            in_python = through_predicate(world, case, at)
            if in_store != in_python:
                disagreed.append(
                    f"{case.name!r}: RLS says "
                    f"{'reached' if in_store else 'refused'} and "
                    f"records/serving.py says "
                    f"{'served' if in_python else 'refused'} "
                    f"— guard: {case.guard}")
        assert not disagreed, (
            f"{len(disagreed)} of {len(CASES)} cases disagree between the "
            "compiled predicate and the Python one:\n  "
            + "\n  ".join(disagreed))


def test_both_layers_land_where_the_case_says_they_should():
    """Agreement is not correctness. Two implementations broken the same way
    agree on everything, and a differential that only compared them would report
    green on a store that serves nothing and a predicate that refuses
    everything. Each case declares its answer and both layers are held to it."""
    with a_world() as world:
        wrong = []
        for case in CASES:
            in_store, at = through_rls(world, case)
            in_python = through_predicate(world, case, at)
            for label, got in (("RLS", in_store), ("serve()", in_python)):
                if got != case.reaches:
                    wrong.append(
                        f"{case.name!r}: {label} answered "
                        f"{'reached' if got else 'refused'}, the case declares "
                        f"{'reached' if case.reaches else 'refused'} "
                        f"— guard: {case.guard}")
        assert not wrong, "\n  ".join([""] + wrong)


def test_a_read_that_names_only_its_own_target_is_never_served_past_the_store():
    """**W-3 clause (b), made load-bearing in this middle.**

    A caller that names the lane it is reading — `WHERE lane_id = %s`, and
    nothing about where it is reading *from* — is the ordinary spelling, and for
    a principal who is a ward of another lane it is exactly the case
    *"between wards, default deny"* exists for. `serve()` must never hand such a
    caller more than the store would have reached, in any case.

    The inequality is one-directional on purpose and the asymmetry is the
    finding, not a fudge: naming your target rather than your origin is a
    *stricter* read, so `serve()` refusing where the store reaches (the
    envelope-crossing cases) is correct and expected. The failure this catches is
    the other way round — a predicate that serves a ward a lane the store seals.

    Ablating the ward disjunct in `records/serving.py`'s seal survives every
    other assertion in this file and dies here.
    """
    with a_world() as world:
        past = []
        for case in CASES:
            in_store, at = through_rls(world, case)
            named = through_predicate(world, case, at, origin_as=NAMED)
            if named and not in_store:
                past.append(
                    f"{case.name!r}: serve() served a read naming only its own "
                    f"target, and the store seals that lane — guard: {case.guard}")
        assert not past, "\n  ".join([""] + past)


def test_the_case_set_is_neither_broken_shut_nor_broken_open():
    """A suite of refusals proves a broken store; a suite of permissions proves
    a broken seal. Counts derived from `CASES`, never quoted (rule 17)."""
    reach = [c for c in CASES if c.reaches]
    refuse = [c for c in CASES if not c.reaches]
    assert reach and refuse, (
        f"{len(reach)} reaching and {len(refuse)} refusing case(s): a "
        "differential needs both directions")
    assert len({c.name for c in CASES}) == len(CASES), "two cases share a name"
    assert len({c.guard for c in CASES}) > 1, (
        "every case names the same guard, so nothing distinguishes them")


def test_a_refused_case_is_a_policy_refusing_and_not_an_absent_row():
    """**The attribution.** An RLS refusal is a row count, not an error string,
    so *"this was refused"* and *"there was nothing there"* look identical from
    the app role — which is the house lesson (a refusal that could be a
    different guard's is not evidence) arriving in the one form where the guard
    cannot name itself.

    So every refused case's row is shown to exist, read by a connection outside
    the policy. A zero from the app role is then the policy's and nobody else's.
    """
    with a_world() as world:
        for case in CASES:
            if case.reaches:
                continue
            n = world.owner.execute(
                "SELECT count(*) FROM lane_entry WHERE entry_id = %s",
                (world.entries[case.subject],)).fetchone()[0]
            assert n == 1, (
                f"{case.name!r} is refused, and the row it is refused on does "
                "not exist — this case proves nothing")


def test_the_forged_self_edge_really_is_in_the_table():
    """The one case whose fixture could silently not exist.

    It is inserted with `edge_self_holder_is_subject` disabled, and if that
    insert ever stopped landing — a renamed trigger, a changed column order —
    the case would pass in both layers for the boring reason that there is
    nothing forged to ignore.
    """
    with a_world() as world:
        row = world.owner.execute(
            "SELECT e.holder_id, l.subject_id FROM edge e "
            "JOIN lane l ON l.lane_id = e.target_lane_id "
            "WHERE e.edge_id = %s", (_id("forged-self"),)).fetchone()
        assert row is not None, "the forged self edge was never inserted"
        assert str(row[0]) != str(row[1]), (
            "the forged self edge's holder is the lane's subject, so it is not "
            "forged and the case is vacuous")


def test_the_predicate_layer_actually_calls_the_predicate():
    """A control on this file rather than on the store.

    `through_predicate` could be quietly reduced to a lookup table by a
    refactor and every assertion above would still pass. This drives the same
    rows through `serve()` at `L5` and requires a refusal that only `serve()`
    can produce — the never-served rung, which no policy in
    `migrations/003_row_security.sql` knows about at all.
    """
    with a_world() as world:
        edges = _edges(world.owner)
        fld = Field(lane_id=str(LANE[BEN]), subject_id=str(BEN),
                    name="declination.subject_matter", rung=Rung.L5,
                    payload="a media release, refused")
        got = serve(fld, Principal(str(ROB)), edges,
                    world.owner.execute("SELECT now()").fetchone()[0],
                    lane_id=str(LANE[BEN]), grants=None)
        assert got.outcome is Outcome.REFUSED
        assert "L5 is never served" in got.reason, got.reason
        # And the same principal reaches an L3 row in that lane through both
        # layers, so the refusal above is the rung and not the standing.
        assert through_rls(world, CASES[0])[0] is True


if __name__ == "__main__":
    ok, why = True, ""
    try:
        ok, why = available()
    except ClusterUnknown as exc:  # pragma: no cover
        ok, why = False, str(exc)
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    if not ok:
        raise SystemExit(report("test_store_differential", 0, len(tests),
                                unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    print(f"  {len(CASES)} case(s) driven through both layers")
    raise SystemExit(report("test_store_differential", failures, len(tests)))
