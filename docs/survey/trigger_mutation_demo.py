#!/usr/bin/env python3
"""Four SQLite mutants against two middles: an adversarial test and a manifest.

Restores the artifact scout-13 §7 claims and §2 derives its central table from.
The table was previously unreproducible — the script was named in the report and
was not in the tree, which is §18 item 0's defect ("an unverified table and a
verified one look identical") landing inside the report about verifying
verifiers. This file makes the table re-runnable; the numbers in §2 are now
either confirmed by running it or corrected against it.

The claim under test: **ablation, not textual edit, is the correct primary
mutation operator for a schema guarantee**, because SQLite fires triggers by
definition and not by name, so renaming one is a mutation of nothing. A harness
that scores a rename as a killed mutant is inflating its denominator with an
ineffective mutant.

And the second, less obvious half: the adversarial test and the schema-object
manifest are two different middles, and **neither subsumes the other**. Ship
both.

Stdlib only, no network, no fixtures. Runs under pytest or directly:

    python3 docs/survey/trigger_mutation_demo.py
    python3 -m pytest docs/survey/trigger_mutation_demo.py -q
"""

from __future__ import annotations

import sqlite3

# --- the schema under test -------------------------------------------------
#
# Two guarantees, deliberately of different kinds:
#   * a TRIGGER enforcing CLAUDE.md #4-adjacent consent doctrine (§7's "consent
#     is never requested by its beneficiary"), which is procedural, and
#   * a CHECK enforcing the bitemporal ordering §7.1 relies on, which is
#     declarative.
# The mutation operators that reach one do not reach the other.

SCHEMA = """
CREATE TABLE person (
    person_id   INTEGER PRIMARY KEY,
    is_minor    INTEGER NOT NULL CHECK (is_minor IN (0, 1))
);

CREATE TABLE consent (
    consent_id  INTEGER PRIMARY KEY,
    subject_id  INTEGER NOT NULL REFERENCES person(person_id),
    requested_by INTEGER NOT NULL REFERENCES person(person_id),
    valid_at    TEXT NOT NULL,
    invalid_at  TEXT,
    CONSTRAINT consent_interval_ordered
        CHECK (invalid_at IS NULL OR invalid_at > valid_at)
);

CREATE TRIGGER consent_not_self_requested
BEFORE INSERT ON consent
WHEN NEW.subject_id = NEW.requested_by
BEGIN
    SELECT RAISE(ABORT, 'a ward may request, never authorize');
END;
"""

FIXTURE = """
INSERT INTO person (person_id, is_minor) VALUES (1, 1), (2, 0);
"""


def build(mutant: str | None = None) -> sqlite3.Connection:
    """A fresh in-memory database, optionally with one mechanism mutated."""
    schema = SCHEMA
    if mutant == "rename":
        # A textual edit that changes the guard's NAME and nothing else.
        schema = schema.replace(
            "CREATE TRIGGER consent_not_self_requested",
            "CREATE TRIGGER consent_self_request_guard",
        )
    elif mutant == "drop_trigger":
        schema = schema[: schema.index("CREATE TRIGGER")]
    elif mutant == "neuter_when":
        schema = schema.replace(
            "WHEN NEW.subject_id = NEW.requested_by", "WHEN 0"
        )
    elif mutant == "drop_check":
        schema = schema.replace(
            """,
    CONSTRAINT consent_interval_ordered
        CHECK (invalid_at IS NULL OR invalid_at > valid_at)""",
            "",
        )
    elif mutant is not None:
        raise ValueError(f"unknown mutant {mutant!r}")

    conn = sqlite3.connect(":memory:")
    conn.executescript(schema)
    conn.executescript(FIXTURE)
    return conn


# --- middle 1: the adversarial test ----------------------------------------


def adversarial_refuses(conn: sqlite3.Connection) -> bool:
    """True when the forbidden act is refused — i.e. the guard behaved.

    PROTECTED_AGENTS.md I-12: a test that attempts the forbidden act and asserts
    refusal. The forbidden act here is a ward requesting consent on their own
    behalf.
    """
    try:
        conn.execute(
            "INSERT INTO consent (subject_id, requested_by, valid_at) "
            "VALUES (1, 1, '2026-01-01')"
        )
    except sqlite3.IntegrityError:
        return True
    return False


def adversarial_accepts_the_permitted_act(conn: sqlite3.Connection) -> bool:
    """The negative control, and the half I-12 does not currently require.

    A guard that refuses EVERYONE also refuses the forbidden act, so a suite
    that only asserts refusal cannot tell a working guard from a broken-shut
    one. This asserts the permitted act still goes through.
    """
    try:
        conn.execute(
            "INSERT INTO consent (subject_id, requested_by, valid_at) "
            "VALUES (1, 2, '2026-01-01')"
        )
    except sqlite3.IntegrityError:
        return False
    return True


def backdated_interval_refused(conn: sqlite3.Connection) -> bool:
    """The declarative guarantee: an interval that ends before it began."""
    try:
        conn.execute(
            "INSERT INTO consent (subject_id, requested_by, valid_at, invalid_at) "
            "VALUES (1, 2, '2026-06-01', '2026-01-01')"
        )
    except sqlite3.IntegrityError:
        return True
    return False


# --- middle 2: the schema-object manifest ----------------------------------


def trigger_inventory(conn: sqlite3.Connection) -> set[str]:
    """Declared trigger names, read from the database rather than the source."""
    return {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
    }


def check_constraint_inventory(conn: sqlite3.Connection) -> set[str]:
    """Named CHECK constraints, recovered from the stored table DDL.

    SQLite has no catalog view for constraints, so this reads `sqlite_master.sql`
    — which is the stored text of the statement that created the table.
    """
    found = set()
    for (sql,) in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ):
        for part in sql.split("CONSTRAINT ")[1:]:
            found.add(part.split()[0].strip("(,"))
    return found


DECLARED_TRIGGERS = {"consent_not_self_requested"}
DECLARED_CHECKS = {"consent_interval_ordered"}


def manifest_matches(conn: sqlite3.Connection) -> bool:
    """True when the live schema still declares exactly what it should.

    Compared in BOTH directions on purpose. `live <= declared` passes when a
    declared object has vanished, which is the same fail-open shape as a stale
    allowlist (ARCHITECTURE.md §16).
    """
    return (
        trigger_inventory(conn) == DECLARED_TRIGGERS
        and check_constraint_inventory(conn) == DECLARED_CHECKS
    )


# --- the run ---------------------------------------------------------------

MUTANTS = [
    ("A", None, "unmutated (control)"),
    ("B", "rename", "rename the trigger"),
    ("C", "drop_trigger", "DROP TRIGGER"),
    ("D", "neuter_when", "WHEN -> WHEN 0"),
    ("E", "drop_check", "drop the bitemporal CHECK"),
]


def run() -> list[dict]:
    rows = []
    for tag, mutant, label in MUTANTS:
        conn = build(mutant)
        row = {
            "tag": tag,
            "label": label,
            "adversarial_refuses": adversarial_refuses(build(mutant)),
            "permitted_accepted": adversarial_accepts_the_permitted_act(build(mutant)),
            "interval_refused": backdated_interval_refused(build(mutant)),
            "manifest_matches": manifest_matches(conn),
        }
        rows.append(row)
        conn.close()
    return rows


def _fmt(b: bool) -> str:
    return "yes" if b else "NO "


def main() -> int:
    rows = run()
    print("  mutant                       adversarial  permitted  interval  manifest")
    print("                                  refuses?   accepted?  refused?   matches?")
    for r in rows:
        print(
            f"  {r['tag']}  {r['label']:<26} "
            f"{_fmt(r['adversarial_refuses']):^10} "
            f"{_fmt(r['permitted_accepted']):^10} "
            f"{_fmt(r['interval_refused']):^9} "
            f"{_fmt(r['manifest_matches']):^9}"
        )
    print()
    print("  A mutant is CAUGHT when a middle that should hold stops holding.")
    return 0


# --- the assertions, so this file is a test and not only a demo ------------


def test_control_is_healthy():
    """If the unmutated schema does not refuse the forbidden act AND accept the
    permitted one, every other result in this file is meaningless."""
    conn = build()
    assert adversarial_refuses(build()), "guard does not refuse the forbidden act"
    assert adversarial_accepts_the_permitted_act(build()), "guard refuses everyone"
    assert backdated_interval_refused(build()), "CHECK does not refuse a bad interval"
    assert manifest_matches(conn), "manifest disagrees with the unmutated schema"


def test_a_rename_is_a_mutation_of_nothing():
    """The central claim. SQLite fires triggers by definition, not by name, so a
    renamed trigger still refuses — the adversarial test cannot see the edit."""
    assert adversarial_refuses(build("rename")), (
        "renaming the trigger stopped it firing — the premise of this file is wrong"
    )


def test_the_manifest_catches_the_rename_the_behaviour_test_misses():
    """Middle 2 exists because middle 1 has this blind spot."""
    assert not manifest_matches(build("rename"))


def test_ablation_is_caught_by_behaviour():
    assert not adversarial_refuses(build("drop_trigger"))


def test_neutered_when_is_caught_by_behaviour_and_missed_by_the_manifest():
    """The complement of the rename case, and the reason neither middle
    subsumes the other: the trigger is still named and still present, and it no
    longer does anything."""
    assert not adversarial_refuses(build("neuter_when")), "WHEN 0 still refused?"
    assert manifest_matches(build("neuter_when")), (
        "manifest noticed a neutered WHEN — it should not, it compares names"
    )


def test_dropping_the_check_is_caught_by_behaviour_and_by_the_manifest():
    """A named CHECK is visible in the stored DDL, so unlike the trigger's WHEN
    clause its removal is caught twice."""
    assert not backdated_interval_refused(build("drop_check"))
    assert not manifest_matches(build("drop_check"))


def test_the_manifest_compares_both_directions():
    """A one-sided `live <= declared` passes when a declared object is gone.
    Confirm the check is not that."""
    assert not manifest_matches(build("drop_trigger")), (
        "manifest passed with a declared trigger missing — it is one-sided"
    )


if __name__ == "__main__":
    # Same convention as tests/test_section_refs.py: runnable without pytest,
    # because a check that only runs under a dependency this repo does not
    # declare is a check that does not run.
    main()
    failures = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"ok   {_name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {_name}\n{exc}\n")
    raise SystemExit(1 if failures else 0)
