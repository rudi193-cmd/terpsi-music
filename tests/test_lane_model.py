"""The ward clauses survive as schema, not as comments.

`docs/schema/001_lanes.proposed.sql` encodes W-1 (a lane from the first write),
W-2 (a grant names one ward), W-3 (a shared event is two lane entries with one
referent) and W-6 (no lane without a written exit). Each is expressed as a
structural property of the DDL — a NOT NULL, an absent column, a CHECK that
omits a value — precisely so that it cannot be softened by a later edit that
looks reasonable in isolation.

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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "docs" / "schema" / "001_lanes.proposed.sql"
SENSITIVITY = ROOT / "docs" / "SENSITIVITY.md"

# State takes the bitemporal pair; history must not (§7.1's exclusion list).
STATE_TABLES = (
    "person", "lane", "referent", "lane_entry", "edge", "access_grant", "declination",
)
HISTORY_TABLES = ("disclosure_log", "consent_chain", "reconciled_session")

# A column on `referent` whose name matches any of these has put participants
# back on the shared object, which is the partition W-1 and W-3 forbid.
ROSTER_SHAPED = (
    "roster", "member", "participant", "attendee", "student", "person",
    "subject", "lane", "enrolled", "assigned",
)

# Minor status is a birthdate evaluated at the read (§7), never a stored flag.
FLAG_SHAPED = ("is_minor", "is_adult", "minor_flag", "adult_flag")

_TABLE = re.compile(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", re.DOTALL)
_NOT_A_COLUMN = ("constraint", "primary", "unique", "check", "foreign", "exclude")


def strip_comments(sql: str) -> str:
    """`--` to end of line. No string literal in this file contains `--`; a
    future one would need this to become a real tokenizer."""
    return "\n".join(line.split("--")[0].rstrip() for line in sql.splitlines())


def tables(sql: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _TABLE.finditer(strip_comments(sql))}


def columns(body: str) -> dict[str, str]:
    """{column name: the rest of its definition}."""
    out = {}
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.split()[0].lower() in _NOT_A_COLUMN:
            continue
        name, _, rest = line.partition(" ")
        out[name] = rest.strip()
    return out


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
        for name in g:
            if any(w in name.lower() for w in ("scope", "pattern", "wildcard", "filter")):
                bad.append(f"W-2: access_grant.{name} could express a group scope")
    for name in t:
        if name != "access_grant" and "grant" in name and "lane" in name:
            bad.append(f"W-2: {name} looks like a grant-to-lane join table — a "
                       "grant must name one lane and be unable to name a set")

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

    return bad


# --- the checks ------------------------------------------------------------


def _sql() -> str:
    return SCHEMA.read_text(encoding="utf-8")


def test_the_parser_finds_the_tables():
    """A regex matching nothing would make every check below pass vacuously."""
    t = tables(_sql())
    assert len(t) == len(STATE_TABLES) + len(HISTORY_TABLES) + 1, sorted(t)
    assert "lane_entry" in t and "access_grant" in t
    assert len(columns(t["lane_entry"])) >= 10, columns(t["lane_entry"])


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
    ):
        assert expected in joined, f"missed {expected!r} in:\n{joined}"


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
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}\n{exc}\n")
    raise SystemExit(1 if failures else 0)
