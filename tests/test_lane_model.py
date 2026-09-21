"""The ward clauses survive as schema, not as comments.

`migrations/001_lanes.sql` encodes W-1 (a lane from the first write), W-2 (a
grant names one ward), W-3 in both halves (a shared event is two lane entries
with one referent, **and** a crossing takes a guardian-signed envelope naming
both lanes, purpose and expiry), W-4 (a ward may request, never authorize), W-5
(agency grows by signature, per enumerated matter) and W-6 (no lane without a
written exit). Each is expressed as a structural property of the DDL — a NOT
NULL, an absent column, a CHECK that omits a value — precisely so that it
cannot be softened by a later edit that looks reasonable in isolation.

The path moved from `docs/schema/001_lanes.proposed.sql` when the DDL was
promoted; a tombstone stands at the old path and is checked below, because a
successor named in prose that nobody verifies is the pointer §16 warns about.

§8 and §18 both say the same thing about why this is worth guarding: retrofitting
either clause is a data migration across every table referencing a student. The
cheapest moment to catch a roster column is before it holds data.

ARCHITECTURE.md §10: a guard that cannot be shown to fail has not been shown to
work. Every check is a function over SQL text, so it can be pointed at a decoy.

Stdlib only. No network. Does not require a database — this reads the DDL as
text and asserts its shape. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_lane_model.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# One parser. `strip_comments`, `tables`, `columns` and `classified` were
# written here and now live in `tools/registry.py`, which reconciles the seed
# against `records/classify.py` and needs the same reader. A second copy would
# have been the pair that module exists to close (§16, rule 12), and the two
# would have drifted in the direction where a phantom column reads as classified.
from registry import (  # noqa: E402
    classified, columns, strip_comments, tables,
)

SCHEMA = ROOT / "migrations" / "001_lanes.sql"
TOMBSTONE = ROOT / "docs" / "schema" / "001_lanes.proposed.sql"
SENSITIVITY = ROOT / "docs" / "SENSITIVITY.md"

# State takes the bitemporal pair; history must not (§7.1's exclusion list).
# An envelope and a widening are state: both end by a date, never by a DELETE
# (refusal 3), because a revoked permission that was deleted cannot answer
# "who could cross into Ben's lane on October 12, and why."
STATE_TABLES = (
    "person", "lane", "referent", "lane_entry", "scope_object", "edge",
    "access_grant", "crossing_envelope", "self_widening", "declination",
)
HISTORY_TABLES = ("disclosure_log", "consent_chain", "reconciled_session")

# Tables that authorize. Each names ONE ward, by foreign key, with no join
# table and no pattern column — W-2/refusal 5 made inexpressible rather than
# rejected. The suffix check below refuses a join table hung off any of them.
GRANT_SHAPED = ("access_grant", "crossing_envelope", "self_widening")

# A column name on a grant-shaped table that could hold a set or a pattern
# instead of a name. `ids` catches `lane_ids`; `glob` and `pattern` catch the
# shapes a scope language arrives as.
SET_SHAPED = ("scope", "pattern", "wildcard", "filter", "glob", "ids", "group")

# Tables whose row shape a CHECK cannot reach, and the guard each must carry.
# Every one of these is a rule about whose signature counts.
SIGNATURE_TRIGGERS = ("edge", "crossing_envelope", "self_widening")

# A column on `referent` whose name matches any of these has put participants
# back on the shared object, which is the partition W-1 and W-3 forbid.
ROSTER_SHAPED = (
    "roster", "member", "participant", "attendee", "student", "person",
    "subject", "lane", "enrolled", "assigned",
)

# Minor status is a birthdate evaluated at the read (§7), never a stored flag.
FLAG_SHAPED = ("is_minor", "is_adult", "minor_flag", "adult_flag")

# "CREATE TRIGGER x BEFORE UPDATE OR DELETE ON disclosure_log"
_TRIGGER = re.compile(
    r"CREATE TRIGGER\s+\w+\s+BEFORE\s+(.*?)\s+ON\s+(\w+)", re.IGNORECASE | re.DOTALL
)


def before_triggers(sql: str) -> dict[str, str]:
    """{table: the events its BEFORE trigger fires on}.

    Two families share this reader and they do different work. On the three
    history tables a `BEFORE UPDATE OR DELETE` trigger is what makes
    "append-only" an enforcement rather than a comment. On `edge`,
    `crossing_envelope` and `self_widening` a `BEFORE INSERT OR UPDATE` trigger
    is the only thing that can reach a second row to ask whether a signature is
    a guardian's — which a CHECK, seeing one row of one table, cannot.
    """
    return {m.group(2): m.group(1).upper() for m in _TRIGGER.finditer(strip_comments(sql))}


def constraints(body: str) -> str:
    """Every CHECK / CONSTRAINT clause, joined — for substring assertions.

    Paren-balanced rather than line-based: `field_classification`'s class list
    spans three lines, and a line-based reader would silently return only the
    first, making an empty vocabulary look like a matching one."""
    out, depth, collecting = [], 0, False
    for line in body.splitlines():
        s = line.strip()
        if not collecting and s.lower().startswith(("constraint", "check")):
            collecting, depth = True, 0
        if collecting:
            out.append(s)
            depth += s.count("(") - s.count(")")
            if depth <= 0:
                collecting = False
    return "\n".join(out)


def documented_classes() -> set[str]:
    """The §6 classes SENSITIVITY.md maps to a rung. The SQL's allowed set must
    equal this — two documents disagreeing about the class vocabulary is the
    canonical/vendored pair §16 exists to prevent."""
    text = SENSITIVITY.read_text(encoding="utf-8")
    return set(re.findall(r"^\|\s*`([A-Z][A-Z_]+)`\s*\|\s*`L[1-5]`\s*\|", text, re.M))


def problems(sql: str) -> list[str]:
    """Human-readable failures, empty when every clause is still encoded."""
    bad = []
    t = tables(sql)

    def col(table, name):
        return columns(t[table]).get(name) if table in t else None

    # --- W-1: no ward fact outside a lane ---------------------------------
    if "lane_entry" not in t:
        bad.append("W-1: no lane_entry table")
    elif "NOT NULL" not in (col("lane_entry", "lane_id") or ""):
        bad.append("W-1: lane_entry.lane_id is missing or nullable — a fact "
                   "about a ward can exist outside a lane")

    # --- W-2: a grant names exactly one ward ------------------------------
    if "access_grant" not in t:
        bad.append("W-2: no access_grant table")
    else:
        g = columns(t["access_grant"])
        if "NOT NULL" not in g.get("lane_id", ""):
            bad.append("W-2: access_grant.lane_id is missing or nullable")
        # The pattern-column and array-column scans are the GRANT_SHAPED loop
        # below, which runs over all three authorizing tables rather than this
        # one. §16: the pair got a middle rather than a second copy.
    for name in t:
        if name != "access_grant" and "grant" in name and "lane" in name:
            bad.append(f"W-2: {name} looks like a grant-to-lane join table — a "
                       "grant must name one lane and be unable to name a set")

    # --- W-2 / refusal 5, generalised over every table that authorizes ----
    #
    # The three grant-shaped tables each name one ward. A set arrives three
    # ways and none of them is a wildcard string: a join table hung off the
    # grant, a pattern column, or an array column. The last is the one a name
    # check misses entirely — `to_lane_ids uuid[]` reads as singular enough.
    for name in t:
        if name in GRANT_SHAPED:
            continue
        for g in GRANT_SHAPED:
            if name.startswith(g + "_"):
                bad.append(f"W-2: {name} hangs off {g} — a grant must name one "
                           "ward and be unable to name a set")
    for g in GRANT_SHAPED:
        if g not in t:
            continue
        for name, definition in columns(t[g]).items():
            if any(w in name.lower() for w in SET_SHAPED):
                bad.append(f"W-2: {g}.{name} could express a group scope")
            if "[]" in definition:
                bad.append(f"W-2: {g}.{name} is an array — a column holding a set "
                           "is a group grant whatever it is called")

    # --- W-3, second half: the crossing the clause permits -----------------
    #
    # "a crossing requires a guardian-signed envelope naming both lanes,
    # purpose, and expiry" (PROTECTED_AGENTS.md Part III, read at source). The
    # first twelve tables encoded the prohibition and not the permission, so a
    # legitimate sibling crossing was unrepresentable. Each of the clause's
    # four requirements is one assertion here.
    if "crossing_envelope" not in t:
        bad.append("W-3: no crossing_envelope table — the clause's permission "
                   "is unrepresentable, so a real crossing can only be served "
                   "by not recording that it happened")
    else:
        env = columns(t["crossing_envelope"])
        ec = constraints(t["crossing_envelope"])
        for side in ("from_lane_id", "to_lane_id"):
            d = env.get(side, "")
            if "NOT NULL" not in d:
                bad.append(f"W-3: crossing_envelope.{side} is missing or nullable "
                           "— an envelope naming one lane is a wildcard over the other")
            if "REFERENCES lane" not in d:
                bad.append(f"W-3: crossing_envelope.{side} is not a reference to a "
                           "lane — a crossing scoped to anything but a named lane "
                           "is a group grant")
        if "from_lane_id <> to_lane_id" not in ec.replace("!=", "<>"):
            bad.append("W-3: crossing_envelope does not CHECK that the two lanes "
                       "differ — one lane named twice is not a crossing")
        if "NOT NULL" not in env.get("purpose", ""):
            bad.append("W-3: crossing_envelope.purpose is missing or nullable")
        if "purpose" not in ec:
            bad.append("W-3: crossing_envelope.purpose has no non-blank CHECK — "
                       "NOT NULL alone is satisfied by an empty string")
        if "NOT NULL" not in env.get("expires_at", ""):
            bad.append("W-3: crossing_envelope.expires_at is missing or nullable — "
                       "an envelope without an expiry is a standing grant (W-5)")
        if "expires_at > signed_at" not in ec:
            bad.append("W-3: crossing_envelope does not CHECK that the expiry is "
                       "after the signature")
        if "REFERENCES person" not in env.get("signed_by", ""):
            bad.append("W-3: crossing_envelope.signed_by is missing or is not a "
                       "person — a role cannot sign")
        for forbidden in ("symmetric", "both_ways", "reciprocal", "bidirectional"):
            if any(forbidden in c for c in env):
                bad.append(f"W-3: crossing_envelope.{forbidden} makes one signature "
                           "open two seals; direction is the ordered pair")
        # The envelope crosses a seal and confers no rung. L5 is unreachable
        # through it because there is nothing to put a rung in — the same move
        # W-2 makes with group scopes, one axis over.
        for name in env:
            if "rung" in name.lower():
                bad.append(f"W-3: crossing_envelope.{name} gives an envelope a rung; "
                           "a crossing does not widen the ladder, and a column here "
                           "is somewhere to write L5")

    # --- W-5 / W-4: the widening, and who may sign it ---------------------
    if "self_widening" not in t:
        bad.append("W-5: no self_widening table — the self edge's L3 cap has "
                   "nothing that lifts it, so §18 item 12's L4 case is "
                   "unrepresentable")
    else:
        w = columns(t["self_widening"])
        wc = constraints(t["self_widening"])
        if "REFERENCES person" not in w.get("subject_id", ""):
            bad.append("W-5: self_widening.subject_id is missing or is not a person")
        if "NOT NULL" not in w.get("category", ""):
            bad.append("W-5: self_widening.category is missing or nullable — a "
                       "widening over no particular matter is a standing grant")
        if "btrim(category)" not in wc:
            bad.append("W-5: self_widening.category has no non-blank CHECK")
        if "'*'" not in wc:
            bad.append("W-2: self_widening.category has no wildcard CHECK — "
                       "'everything' is not a matter, a name is")
        if "NOT NULL" not in w.get("purpose", ""):
            bad.append("W-5: self_widening.purpose is missing or nullable")
        if "expires_at > signed_at" not in wc:
            bad.append("W-5: self_widening does not CHECK that the expiry is after "
                       "the signature — W-5 forbids the standing grant")
        if "REFERENCES person" not in w.get("signed_by", ""):
            bad.append("W-5: self_widening.signed_by is missing or is not a person")
        if "signed_by <> subject_id" not in wc.replace("!=", "<>"):
            bad.append("W-4: self_widening does not CHECK that the signer is not "
                       "the subject — a ward signing its own widening is the "
                       "clause defeated in one field")
        if "max_rung" not in wc:
            bad.append("ladder: self_widening.max_rung has no CHECK")
        elif "'L5'" in wc:
            bad.append("ladder: self_widening.max_rung admits L5, which is never "
                       "served to any principal including the subject")

    # --- a signature claim needs a trigger; a CHECK cannot reach a row ----
    for name in SIGNATURE_TRIGGERS:
        if name not in t:
            continue
        events = before_triggers(sql).get(name, "")
        if "INSERT" not in events or "UPDATE" not in events:
            bad.append(
                f"signature: {name} has no BEFORE INSERT OR UPDATE trigger — "
                "whose signature counts is a fact about a second row, which a "
                "CHECK cannot see (§7.2: say which)"
            )

    # --- W-3: the referent carries no participants ------------------------
    if "referent" not in t:
        bad.append("W-3: no referent table")
    else:
        for name in columns(t["referent"]):
            if any(w in name.lower() for w in ROSTER_SHAPED):
                bad.append(f"W-3: referent.{name} puts participants back on the "
                           "shared object — a shared event is two lane entries "
                           "with one referent")

    # --- W-6: a lane opened without a written exit is invalidly opened ----
    if "lane" not in t:
        bad.append("W-6: no lane table")
    else:
        if "NOT NULL" not in (col("lane", "exit_terms") or ""):
            bad.append("W-6: lane.exit_terms is missing or nullable")
        if "exit_terms" not in constraints(t["lane"]):
            bad.append("W-6: lane.exit_terms has no non-blank CHECK — NOT NULL "
                       "alone is satisfied by an empty string")

    # --- the ladder: L5 is unreachable through a grant --------------------
    if "access_grant" in t:
        c = constraints(t["access_grant"])
        if "max_rung" not in c:
            bad.append("ladder: access_grant.max_rung has no CHECK")
        else:
            if "'L5'" in c.split("access_grant_l4")[0]:
                bad.append("ladder: access_grant.max_rung admits L5, which is "
                           "never served to anyone under any grant")
            if "'L4'" in c and "purpose" not in c:
                bad.append("ladder: L4 is grantable without a declared purpose")

    # --- §7.1: state takes the pair, history must not ---------------------
    for name in STATE_TABLES:
        if name not in t:
            bad.append(f"§7.1: state table {name} is missing")
            continue
        cols = columns(t[name])
        for required in ("created_at", "valid_at", "invalid_at"):
            if required not in cols:
                bad.append(f"§7.1: {name} has no {required}")
    for name in HISTORY_TABLES:
        if name not in t:
            bad.append(f"§7.1: history table {name} is missing")
            continue
        cols = columns(t[name])
        for forbidden in ("valid_at", "invalid_at"):
            if forbidden in cols:
                bad.append(f"§7.1: {name} carries {forbidden} — it is append-only "
                           "history, and a historical fact is not mutable state")

    # --- §7: minor status is a birthdate, not a flag ----------------------
    for tname, body in t.items():
        for cname in columns(body):
            if any(f in cname.lower() for f in FLAG_SHAPED):
                bad.append(f"§7: {tname}.{cname} is a minority flag — a flag stays "
                           "true until somebody runs the job that clears it")

    # --- append-only means a trigger, not a comment -----------------------
    #
    # Omitting valid_at/invalid_at does not stop an UPDATE. Confirmed the hard
    # way: against a live instance, UPDATE then DELETE on disclosure_log both
    # succeeded, silently rewriting the FERPA §99.32 disclosure record.
    triggers = before_triggers(sql)
    for name in HISTORY_TABLES:
        if name not in t:
            continue
        events = triggers.get(name, "")
        if "UPDATE" not in events or "DELETE" not in events:
            bad.append(
                f"append-only: {name} has no BEFORE UPDATE OR DELETE trigger — "
                "the label is a claim and this is the enforcement (§7.2)"
            )

    # --- every column is classified ---------------------------------------
    #
    # SENSITIVITY.md: an unclassified field is a build failure, not a default.
    # This is that build failure.
    seed = classified(sql)
    for tname, body in sorted(t.items()):
        for cname in columns(body):
            if (tname, cname) not in seed:
                bad.append(f"unclassified: {tname}.{cname} has no field_classification row")
    declared = {(tn, cn) for tn, body in t.items() for cn in columns(body)}
    for key in sorted(seed):
        if key not in declared:
            bad.append(f"stale classification: {key[0]}.{key[1]} is classified but not declared")

    return bad


# --- the checks ------------------------------------------------------------


def _sql() -> str:
    return SCHEMA.read_text(encoding="utf-8")


def test_the_parser_finds_the_tables():
    """A regex matching nothing would make every check below pass vacuously."""
    t = tables(_sql())
    assert len(t) == len(STATE_TABLES) + len(HISTORY_TABLES) + 1, sorted(t)
    assert "lane_entry" in t and "access_grant" in t
    assert "crossing_envelope" in t and "self_widening" in t
    assert len(columns(t["lane_entry"])) >= 10, columns(t["lane_entry"])
    # Every table carrying a BEFORE trigger, and no others. Asserted as a set
    # rather than as a length: the count stayed right when the two families
    # were added and would have hidden a trigger on the wrong table.
    assert set(before_triggers(_sql())) == set(HISTORY_TABLES) | set(SIGNATURE_TRIGGERS)
    # Derived from the tree, not written down (rule 17). A literal here decays
    # the moment a column is added, and decays silently in the safe direction.
    declared = sum(len(columns(body)) for body in t.values())
    assert len(classified(_sql())) == declared, (len(classified(_sql())), declared)


def test_the_edge_target_has_referential_integrity():
    """The first draft carried a polymorphic (target_kind, target_id) pair with
    no foreign key. A live instance accepted a target_id pointing at nothing and
    a target_kind of 'Sandwich'. Both columns must now be real references, with
    exactly one populated."""
    e = columns(tables(_sql())["edge"])
    assert "target_kind" not in e, "free-text target kind is back"
    assert "REFERENCES lane" in e.get("target_lane_id", "")
    assert "REFERENCES scope_object" in e.get("target_scope_id", "")
    assert "num_nonnulls" in constraints(tables(_sql())["edge"])


def test_a_multiline_check_yields_no_phantom_columns():
    """Regression. `edge`'s kind CHECK spans three lines; a line-based column
    reader turned its value list into columns named `'guardian_of',` and `))`,
    which then failed the classification-coverage check for a schema that was
    in fact fully classified."""
    cols = columns(
        """
    edge_id uuid PRIMARY KEY,
    kind    text NOT NULL,
    CONSTRAINT edge_kind CHECK (kind IN (
        'guardian_of', 'staff_of', 'director_of'
    )),
    CONSTRAINT edge_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
"""
    )
    assert set(cols) == {"edge_id", "kind"}, cols


def test_comments_are_stripped_before_matching():
    """The DDL's own comments say the words 'roster column' and 'student'. If
    comments reached the column scan, W-3 would fail against a correct file —
    and someone would 'fix' it by deleting the explanation."""
    assert "roster" in _sql(), "the comment this guards against is gone"
    assert "roster" not in strip_comments(_sql()).lower()


def test_the_clauses_are_still_encoded():
    bad = problems(_sql())
    assert not bad, "\n".join(bad)


def test_class_vocabulary_agrees_with_the_ladder():
    """field_classification's CHECK and SENSITIVITY.md's mapping table must name
    the same eight classes. Either drifting makes one of them wrong."""
    t = tables(_sql())
    assert "field_classification" in t
    in_sql = set(re.findall(r"'([A-Z][A-Z_]+)'", constraints(t["field_classification"])))
    in_sql -= {f"L{n}" for n in range(1, 6)}
    documented = documented_classes()
    assert documented, "parsed no classes out of SENSITIVITY.md"
    assert in_sql == documented, (
        f"only in the schema: {sorted(in_sql - documented)}; "
        f"only in SENSITIVITY.md: {sorted(documented - in_sql)}"
    )


def test_every_rung_in_the_schema_is_a_real_rung():
    rungs = set(re.findall(r"'(L\d)'", strip_comments(_sql())))
    assert rungs and rungs <= {"L1", "L2", "L3", "L4", "L5"}, rungs


def test_the_check_can_actually_fail():
    """A schema that softens all four clauses in ways each looking reasonable
    alone: a nullable lane on entries, a scope pattern on grants, a roster on
    the referent, and an exit nobody has to write."""
    decoy = """
CREATE TABLE lane (
    lane_id     uuid PRIMARY KEY,
    exit_terms  text,
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz
);
CREATE TABLE lane_entry (
    entry_id  uuid PRIMARY KEY,
    lane_id   uuid REFERENCES lane(lane_id)
);
CREATE TABLE referent (
    referent_id  uuid PRIMARY KEY,
    student_ids  uuid[] NOT NULL
);
CREATE TABLE access_grant (
    grant_id    uuid PRIMARY KEY,
    lane_id     uuid,
    scope_glob  text,
    max_rung    text NOT NULL,
    CONSTRAINT access_grant_max_rung CHECK (max_rung IN ('L1','L5'))
);
CREATE TABLE disclosure_log (
    seq        bigserial PRIMARY KEY,
    valid_at   timestamptz NOT NULL,
    invalid_at timestamptz
);
CREATE TABLE person (
    person_id uuid PRIMARY KEY,
    is_minor  boolean NOT NULL
);
"""
    joined = "\n".join(problems(decoy))
    for expected in (
        "W-1: lane_entry.lane_id",
        "W-2: access_grant.lane_id",
        "W-2: access_grant.scope_glob",
        "W-3: referent.student_ids",
        "W-6: lane.exit_terms is missing or nullable",
        "ladder: access_grant.max_rung admits L5",
        "carries valid_at",
        "person.is_minor is a minority flag",
        "append-only: disclosure_log has no BEFORE UPDATE OR DELETE trigger",
        "unclassified: person.is_minor",
    ):
        assert expected in joined, f"missed {expected!r} in:\n{joined}"


def test_an_update_only_trigger_is_not_enough():
    """A trigger firing on UPDATE but not DELETE leaves the log deletable, and
    reads as protection at a glance."""
    decoy = """
CREATE TABLE disclosure_log (
    seq bigserial PRIMARY KEY
);
CREATE TRIGGER disclosure_log_append_only
    BEFORE UPDATE ON disclosure_log
    FOR EACH ROW EXECUTE FUNCTION refuse_mutation();
"""
    assert any("BEFORE UPDATE OR DELETE" in p for p in problems(decoy)), problems(decoy)


def test_a_stale_classification_is_caught():
    """A column classified but no longer declared means the registry is
    describing a schema that has moved. Silent, and the same defect class as
    §15's decayed citation."""
    decoy = """
CREATE TABLE person (
    person_id uuid PRIMARY KEY
);
INSERT INTO field_classification (table_name, column_name, data_class, rung) VALUES
    ('person','person_id','PII_MINOR','L3'),
    ('person','favourite_colour','INTERNAL','L2');
"""
    assert any("stale classification: person.favourite_colour" in p
               for p in problems(decoy)), problems(decoy)


def test_a_blank_exit_is_caught_even_when_not_null():
    """W-6's NOT NULL is satisfied by ''. The non-blank CHECK is the actual
    guard, and this asserts its absence is noticed."""
    decoy = """
CREATE TABLE lane (
    lane_id    uuid PRIMARY KEY,
    exit_terms text NOT NULL,
    created_at timestamptz NOT NULL,
    valid_at   timestamptz NOT NULL,
    invalid_at timestamptz
);
"""
    assert any("non-blank CHECK" in p for p in problems(decoy)), problems(decoy)


def test_a_crossing_envelope_that_names_one_lane_is_caught():
    """W-3 requires *both* lanes. Every way of naming one, attempted.

    A nullable second lane, a second lane that is not a lane, and a table that
    CHECKs nothing about the pair so one lane can be named twice. The last is
    the one that looks correct: two NOT NULL columns, both real foreign keys,
    and `('ben', 'ben')` sails through.
    """
    decoy = """
CREATE TABLE crossing_envelope (
    envelope_id  uuid PRIMARY KEY,
    from_lane_id uuid NOT NULL REFERENCES lane(lane_id),
    to_lane_id   uuid REFERENCES lane(lane_id),
    purpose      text NOT NULL,
    signed_by    uuid NOT NULL REFERENCES person(person_id),
    signed_at    timestamptz NOT NULL,
    expires_at   timestamptz NOT NULL,
    created_at   timestamptz NOT NULL,
    valid_at     timestamptz NOT NULL,
    invalid_at   timestamptz
);
"""
    joined = "\n".join(problems(decoy))
    for expected in (
        "W-3: crossing_envelope.to_lane_id is missing or nullable",
        "does not CHECK that the two lanes differ",
        "crossing_envelope.purpose has no non-blank CHECK",
        "does not CHECK that the expiry is after the signature",
        "signature: crossing_envelope has no BEFORE INSERT OR UPDATE trigger",
    ):
        assert expected in joined, f"missed {expected!r} in:\n{joined}"


def test_a_group_crossing_scope_is_caught_by_shape_and_not_by_name():
    """Refusal 5 on the crossing axis: "the drumline" is not a scope.

    Three ways to smuggle a set past a table that looks like it names lanes —
    a scope pattern, an array of lanes, and a join table. None is refused by a
    wildcard string check, because none of them contains a wildcard.
    """
    decoy = """
CREATE TABLE crossing_envelope (
    envelope_id  uuid PRIMARY KEY,
    from_lane_id uuid NOT NULL REFERENCES lane(lane_id),
    to_lane_id   uuid NOT NULL REFERENCES lane(lane_id),
    to_lane_ids  uuid[] NOT NULL,
    lane_pattern text NOT NULL,
    max_rung     text NOT NULL
);
CREATE TABLE crossing_envelope_lanes (
    envelope_id uuid NOT NULL,
    lane_id     uuid NOT NULL
);
"""
    joined = "\n".join(problems(decoy))
    for expected in (
        "W-2: crossing_envelope.to_lane_ids is an array",
        "W-2: crossing_envelope.lane_pattern could express a group scope",
        "W-2: crossing_envelope_lanes hangs off crossing_envelope",
        "W-3: crossing_envelope.max_rung gives an envelope a rung",
    ):
        assert expected in joined, f"missed {expected!r} in:\n{joined}"


def test_a_widening_nobody_signed_is_caught():
    """W-5's signature and W-4's *whose* signature, attempted three ways.

    A nullable signer, a signer the schema never compares to the subject, and
    no trigger to ask whether the signer is a guardian at all. All three read
    as a signed widening at a glance, and the third is the one this schema
    could not express before it grew a trigger.
    """
    decoy = """
CREATE TABLE self_widening (
    widening_id uuid PRIMARY KEY,
    subject_id  uuid NOT NULL REFERENCES person(person_id),
    category    text NOT NULL,
    purpose     text NOT NULL,
    max_rung    text NOT NULL,
    signed_by   uuid,
    signed_at   timestamptz NOT NULL,
    expires_at  timestamptz NOT NULL,
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz,
    CONSTRAINT self_widening_category_present CHECK (length(btrim(category)) > 0),
    CONSTRAINT self_widening_category_is_a_name
        CHECK (lower(btrim(category)) NOT IN ('*', 'all', 'any', 'every')),
    CONSTRAINT self_widening_max_rung CHECK (max_rung IN ('L4')),
    CONSTRAINT self_widening_expiry_is_future CHECK (expires_at > signed_at)
);
"""
    joined = "\n".join(problems(decoy))
    for expected in (
        "W-5: self_widening.signed_by is missing or is not a person",
        "W-4: self_widening does not CHECK that the signer is not the subject",
        "signature: self_widening has no BEFORE INSERT OR UPDATE trigger",
    ):
        assert expected in joined, f"missed {expected!r} in:\n{joined}"


def test_an_l5_widening_is_caught():
    """A widening naming the rung that is never served, to anyone.

    The self edge's cap is `L3` and a widening lifts it to `L4`. `L5` is
    enforcement-only — never rendered, including to the subject — so a CHECK
    that admits it hands the ladder's top rung to a guardian's signature. Also
    caught: a widening over every category, which is W-2 on the other axis.
    """
    decoy = """
CREATE TABLE self_widening (
    widening_id uuid PRIMARY KEY,
    subject_id  uuid NOT NULL REFERENCES person(person_id),
    category    text NOT NULL,
    purpose     text NOT NULL,
    max_rung    text NOT NULL,
    signed_by   uuid NOT NULL REFERENCES person(person_id),
    signed_at   timestamptz NOT NULL,
    expires_at  timestamptz NOT NULL,
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz,
    CONSTRAINT self_widening_max_rung CHECK (max_rung IN ('L4', 'L5')),
    CONSTRAINT self_widening_ward_cannot_sign_its_own CHECK (signed_by <> subject_id),
    CONSTRAINT self_widening_expiry_is_future CHECK (expires_at > signed_at)
);
"""
    joined = "\n".join(problems(decoy))
    for expected in (
        "ladder: self_widening.max_rung admits L5",
        "W-2: self_widening.category has no wildcard CHECK",
        "W-5: self_widening.category has no non-blank CHECK",
    ):
        assert expected in joined, f"missed {expected!r} in:\n{joined}"


def test_the_tombstone_stands_where_the_ddl_used_to_be():
    """Rule 20, applied to this repository's own retirement.

    A pointer whose target moved is §15's decayed citation, and `LANE-MODEL.md`,
    `EXIT.md`, `records/crossing.py` and this file all named the old path. The
    tombstone is what keeps those honest — and it has five parts, because a
    stub saying only "moved" leaves a reader unable to tell whether the
    contents came with it.
    """
    assert TOMBSTONE.exists(), f"no tombstone at {TOMBSTONE}"
    text = TOMBSTONE.read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:6]).upper()
    assert "RETIRED" in head or "STATUS" in head, "status is not first"
    for part in ("migrations/001_lanes.sql", "NON-AUTHORITATIVE"):
        assert part.lower() in text.lower(), f"tombstone omits {part!r}"
    # It must not still be a schema. A stub that silently declares nothing is
    # worse than one that fails: someone runs it and believes 001 is applied.
    assert "CREATE TABLE" not in strip_comments(text), \
        "the tombstone still declares tables"
    assert "RAISE EXCEPTION" in text, \
        "running the tombstone succeeds silently, which reads as a migration"


def test_adjudication_commentary_needs_no_table_of_its_own():
    """§9 item 9 added no DDL, and this is the claim under that decision.

    `records/commentary.py` stores a remark as a `lane_entry`, so the shape has
    to carry four things, and each is asserted here rather than argued in a
    commit message:

    * **a lane**, `NOT NULL`, so a remark about a student is lane-scoped from
      the first write (W-1);
    * **a referent**, so a moment involving several students is several rows
      sharing one — W-3's fan-out, which is what makes the absence of a
      participant column survivable;
    * **a payload**, for the anchor `records/marking.py` owns (`at_ms`, `seat`,
      the derived `ScorePosition`) without giving each a column that a second
      kind of entry would then have to leave null;
    * **the seal cascade**, `seal_state` plus `sealed_by`, which is §8.2's
      draft/sealed/pending and the reason a transcript is not a record.

    A `commentary` table beside this one would be a second store for the same
    fact, which is the pair §16 forbids — and it would need its own copy of
    every clause above.

    **The gap this does not close, recorded rather than papered over:**
    `lane_entry.lane_id` is `NOT NULL`, so a remark addressed to the ensemble
    and naming *nobody* has no home here. That is correct as far as it goes —
    such a remark is not a fact about a person and does not belong in a lane —
    but the DDL offers no other table for it either, and §8.1's `addresses`
    includes `Ensemble`, `Section` and `Part`. `records/commentary.py`
    represents it (`Addressed.WORK`) and refuses to fabricate a lane for it.
    Where it is stored is an open question, and inventing a table to answer it
    was out of scope for this item.
    """
    body = tables(_sql())["lane_entry"]
    cols = columns(body)

    assert "NOT NULL" in cols["lane_id"], "a remark could be stored outside a lane"
    assert "referent" in cols["referent_id"], "no shared referent for a fan-out"
    assert "jsonb" in cols["payload"].lower(), "no payload for the anchor"
    for needed in ("seal_state", "sealed_by", "author_id"):
        assert needed in cols, f"lane_entry has no {needed}; §8.2 needs it"

    # And no parallel structure crept in beside it.
    for name in tables(_sql()):
        assert "commentary" not in name and "remark" not in name, \
            f"table {name!r} duplicates lane_entry for one kind of entry (§16)"

    # W-1 again, at the column level: nothing here holds a set of students.
    for cn in cols:
        assert cn not in ("subject_ids", "lane_ids", "students", "roster",
                          "participants"), f"lane_entry.{cn} is a roster column"


def test_the_check_passes_the_real_schema_only_on_merit():
    """Mirror of the failure tests: a checker that complained about everything
    would pass them and still be useless."""
    assert not problems(_sql())


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
