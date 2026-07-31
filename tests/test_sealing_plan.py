"""The sealing decision, the migration that implements it, and the seam's refusals.

Everything here runs with **no database**, which is why it is in the guards job
rather than the schema job: the derivation is over migration text, the seam's
refusals happen before a statement is built, and the no-unseal rule is a
property of the source. The acts that need a live cluster — a clear `INSERT` as
the app role, the erasure walkthrough, rotation over real rows — are
`tests/test_store_atrest.py`, and neither file stands in for the other.

Three pairs get their middle named here (rule 12), and each is a pair that has
already drifted somewhere in this fleet:

* **the derivation ↔ migration 004.** A derived set nobody compares to the DDL
  is a report; the DDL is what actually seals.
* **`lane_entry`'s columns ↔ `refuse_sealed_mutation()`'s list.** 002 claims a
  column added without a thought fails safe. It does not — confirmed against a
  live PostgreSQL 16 — and 004 is the migration that would have shipped the
  hole. This is what stops the next one.
* **the migration's scheme string ↔ `records/atrest.py`'s `OPENABLE`.** A CHECK
  cannot import a constant, so the constant is written twice and reconciled here.

Stdlib only. Runs under pytest or directly:

    python3 tests/test_sealing_plan.py
"""

from __future__ import annotations

import ast
import contextlib
import io
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import registry as R  # noqa: E402
from records import atrest  # noqa: E402
from store import sealing_plan as SP  # noqa: E402
from store import writing as W  # noqa: E402

MIGRATIONS = ROOT / "migrations"
SEALING_MIGRATION = MIGRATIONS / "004_sealed_payloads.sql"

AT = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
LANE = "22222222-1111-1111-1111-111111111111"
OTHER_LANE = "22222222-2222-2222-2222-222222222222"


def a_lane_key(lane_id=LANE):
    """Minted here, in memory, and never written anywhere (refusal 2).

    `tests/test_key_custody.py` scans the tree for what this returns; this
    function is the reason there is nothing for it to find.
    """
    master = atrest.new_master()
    _, key = atrest.open_lane_key(atrest.Keyring(), lane_id=lane_id,
                                  master=master, at=AT)
    return key


def an_entry(**over):
    body = dict(entry_id="e", lane_id=LANE, kind="attendance",
                payload=b'{"note":"broken arm"}', author_id="a",
                created_at=AT, valid_at=AT)
    body.update(over)
    return body


# --- the derivation ---------------------------------------------------------


def test_the_derivation_seals_something():
    """A derivation that seals nothing is vacuous, and a vacuous scan is not a
    passing one (rule 13). Every assertion below about *which* columns seal is
    satisfied by an empty set unless this holds first."""
    assert SP.sealed_columns(), (
        "the sealing plan seals no column; every check below would pass "
        "vacuously and the store would hold every payload in the clear")
    # The runner exits 2 on an empty plan, the same way `tools/drivers.py` exits
    # 2 on a scan that found nothing: a vacuous run is not a passing one.
    with contextlib.redirect_stdout(io.StringIO()):
        assert SP.main() == 0


def test_the_sealed_set_is_the_L3_plus_containers_in_a_single_lane_table():
    """The rule, restated as a property rather than as a list.

    Anything sealed must clear every exclusion; anything at `L3`+ that is not
    sealed must name at least one. Neither direction is a count, so a column
    added tomorrow is graded by the rule rather than against a number.
    """
    for d in SP.plan():
        if d.sealed:
            assert d.rung in ("L3", "L4", "L5"), d
            assert d.sql_type == SP.CONTAINER_TYPE, d
            assert not d.exclusions, d
        elif d.rung in ("L3", "L4", "L5"):
            assert d.exclusions, f"{d} is L3+ and clear for no stated reason"
            for e in d.exclusions:
                assert e in SP.WHY, e


def test_every_exclusion_is_one_some_real_column_actually_uses():
    """A vocabulary with unreachable members is a vocabulary nobody checked.

    `records/serving.py`'s outcomes get this treatment and so does this: an
    exclusion that no column in the schema triggers is either dead or wrong,
    and both are worth going red over.
    """
    used = {e for d in SP.plan() for e in d.exclusions}
    unused = set(SP.Clear) - used
    assert not unused, f"exclusions no column reaches: {[e.value for e in unused]}"


def test_the_derivation_does_not_read_its_own_output():
    """**The fixed point, and it did not hold on the first attempt.**

    Migration 004 tombstones `lane_entry.payload` with `CHECK (payload IS
    NULL)`. The first version of `EVALUATED_BY_DDL` read that constraint,
    concluded the column was evaluated by the DDL, and reported that the column
    it had just sealed should be clear — a derivation quoting its own effect,
    which is worse than a hand-written list because it looks derived.

    So the set derived from the migrations *before* the sealing one must equal
    the set derived from all of them.
    """
    earlier = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(MIGRATIONS.glob("*.sql"), key=lambda p: p.name)
        if p != SEALING_MIGRATION)
    before = tuple((d.table, d.column) for d in SP.plan_over(earlier) if d.sealed)
    assert before == SP.sealed_columns(), (
        f"the sealing migration changed the derivation's answer: "
        f"{before} before, {SP.sealed_columns()} after")


def test_the_envelope_columns_do_not_themselves_seal():
    """No recursion: a sealed column's storage is not a payload to seal again."""
    for table, column in SP.all_envelope_columns():
        assert not SP.is_sealed(table, column), f"{table}.{column} seals itself"


def test_a_two_lane_table_has_no_key_to_seal_under():
    """W-1 at the key layer, and the reason `crossing_envelope` is excluded.

    Asked of the function rather than of the exclusion list, so the refusal is
    shown rather than inferred from a tuple.
    """
    assert SP.lane_column("lane_entry") == "lane_id"
    for table in ("crossing_envelope", "person", "reconciled_session"):
        try:
            SP.lane_column(table)
        except ValueError as exc:
            assert "one lane, one key" in str(exc), exc
        else:
            raise AssertionError(f"{table} was handed a single lane key")


# --- the derivation, against the migration that implements it ---------------


def test_the_migration_creates_exactly_the_columns_the_derivation_asks_for():
    """**The pair's middle.** Either direction failing is the pair drifting."""
    text = SEALING_MIGRATION.read_text(encoding="utf-8")
    added = {(m.group(1), m.group(2)) for m in re.finditer(
        r"ALTER TABLE (\w+) ADD COLUMN (\w+)", text)}
    assert added == set(SP.all_envelope_columns()), (
        f"migration 004 adds {sorted(added)}; the derivation asks for "
        f"{sorted(SP.all_envelope_columns())}")


def test_every_sealed_column_is_tombstoned_by_the_migration():
    """The clear column must be constrained to NULL, or the seal is optional."""
    text = SEALING_MIGRATION.read_text(encoding="utf-8")
    for table, column in SP.sealed_columns():
        assert re.search(rf"CHECK \(\s*{column} IS NULL\s*\)", text), (
            f"{table}.{column} seals and migration 004 leaves it writable in "
            "the clear; a sealed column with a live clear twin is not sealed")


def test_the_new_columns_are_classified_and_the_seal_does_not_lower_a_rung():
    """Sealing is a storage property, never a declassification.

    A `payload_sealed` classified below the payload it seals would be
    encryption used as an argument for wider access, which is the trade §5
    declines to make.
    """
    seed = R.classified(R.schema_text(MIGRATIONS))
    for table, column in SP.sealed_columns():
        clear_class, clear_rung = seed[(table, column)]
        sealed_col = SP.envelope_columns(column)[0]
        assert (table, sealed_col) in seed, f"{table}.{sealed_col} is unclassified"
        assert seed[(table, sealed_col)] == (clear_class, clear_rung), (
            f"{table}.{sealed_col} is {seed[(table, sealed_col)]} and the column "
            f"it seals is {(clear_class, clear_rung)}; sealing is not a "
            "declassification")
    for table, column in SP.all_envelope_columns():
        assert (table, column) in seed, f"{table}.{column} is unclassified"


def test_the_migration_and_atrest_agree_on_the_scheme():
    """A `CHECK` cannot import a constant, so the constant is written twice.

    Named rather than left as a coincidence: this is the pair, and this is its
    middle. A build that learns a second scheme changes both, or goes red.
    """
    text = SEALING_MIGRATION.read_text(encoding="utf-8")
    in_sql = set(re.findall(r"payload_scheme = '([a-z0-9.-]+)'", text))
    assert in_sql, "migration 004 constrains no scheme"
    assert in_sql <= set(atrest.OPENABLE), (
        f"migration 004 admits {in_sql} and this build opens "
        f"{sorted(atrest.OPENABLE)}; a payload it accepts and cannot open is "
        "not a payload")


def test_the_ciphertext_shape_check_admits_a_real_seal_and_refuses_plaintext():
    """The constraint is a claim about bytes; the bytes are produced here.

    Reading the prefix out of the migration rather than restating it, so the
    test cannot agree with a constraint it is not looking at.
    """
    text = SEALING_MIGRATION.read_text(encoding="utf-8")
    m = re.search(r"substring\(payload_sealed from 1 for (\d+)\) = "
                  r"'\\x([0-9a-fA-F]+)'::bytea", text)
    assert m, "migration 004 states no ciphertext prefix"
    n, prefix = int(m.group(1)), bytes.fromhex(m.group(2))
    assert len(prefix) == n

    got = atrest.seal_bytes(b'{"note":"broken arm"}', lane_key=a_lane_key(), at=AT)
    assert got.ciphertext[:n] == prefix, (
        "a real Fernet token does not carry the prefix migration 004 requires; "
        "the constraint would refuse every legitimate seal")
    minimum = int(re.search(r"octet_length\(payload_sealed\) >= (\d+)", text).group(1))
    assert len(got.ciphertext) >= minimum
    assert not b'{"note":"broken arm"}'[:n] == prefix
    assert len(b'{"note":"broken arm"}') < minimum


def test_the_sealed_row_trigger_names_every_column_of_the_table():
    """**The pair 002 got wrong, with the middle it needed.**

    `refuse_sealed_mutation()` compares a hand-written list. 002's comment says
    *"a column added without a thought for this rule is refused by default,
    which is the direction that fails safe"* — and the opposite is true: a
    column missing from the list is not compared, so an `UPDATE` touching only
    it lands on a sealed row. Confirmed against PostgreSQL 16 before it was
    written down, and 004 is the commit that would have shipped it — four new
    columns holding the sealed payload, every one freely rewritable.

    So the list is reconciled against the table: every column except
    `invalid_at`, which refusal 3 requires to stay settable.
    """
    sql = R.schema_text(MIGRATIONS)
    columns = set(R.columns(R.tables(sql)["lane_entry"]))
    fn = re.search(r"CREATE OR REPLACE FUNCTION refuse_sealed_mutation.*?\$\$;",
                   sql, re.DOTALL)
    assert fn, "no refuse_sealed_mutation() in the migrations"
    compared = set(re.findall(r"NEW\.(\w+)\s+IS DISTINCT FROM", fn.group(0)))
    assert compared == columns - {"invalid_at"}, (
        f"the sealed-row trigger compares {sorted(compared)} and lane_entry has "
        f"{sorted(columns)}. A column it does not compare is editable on a "
        f"sealed row: missing {sorted(columns - {'invalid_at'} - compared)}")


# --- the seam's refusals, with no database ---------------------------------


def test_a_payload_is_sealed_before_the_insert_and_the_clear_column_is_gone():
    """The whole seam in one assertion: what comes out names storage, not a fact."""
    body = W.seal_payloads("lane_entry", an_entry(), lane_key=a_lane_key(), at=AT)
    assert "payload" not in body, (
        "the clear column survived the seam; there is a path that INSERTs a "
        "readable payload")
    for column in SP.envelope_columns("payload"):
        assert column in body, column
    assert body["payload_scheme"] in atrest.OPENABLE
    assert body["payload_sealed"][:5] == b"gAAAA"
    assert b"broken arm" not in body["payload_sealed"]


def test_the_seam_is_reversible_only_by_the_holder_of_the_key():
    """What the store wrote is what `unseal_with` opens — and nothing else."""
    key = a_lane_key()
    body = W.seal_payloads("lane_entry", an_entry(), lane_key=key, at=AT)
    envelope = atrest.Sealed(lane_id=LANE, key_id=body["payload_key_id"],
                             scheme=body["payload_scheme"],
                             ciphertext=body["payload_sealed"],
                             sealed_at=body["payload_sealed_at"])
    opened = atrest.unseal_with(envelope, lane_key=key)
    assert opened.opened, opened
    assert opened.plaintext == b'{"note":"broken arm"}'

    stranger = a_lane_key()
    assert atrest.unseal_with(envelope, lane_key=stranger).state \
        is atrest.Readable.UNREADABLE


def test_naming_an_envelope_column_is_refused_by_name():
    """The back door: a caller that can set `payload_sealed` can set it to
    anything, and the DDL's shape constraint would be the only thing left."""
    for column in SP.envelope_columns("payload"):
        try:
            W.seal_payloads("lane_entry", an_entry(**{column: b"x"}),
                            lane_key=a_lane_key(), at=AT)
        except W.EnvelopeColumnRefused as exc:
            assert column in str(exc), exc
            assert "seal_bytes" in str(exc), exc
        else:
            raise AssertionError(f"{column} was written by a caller")


def test_a_sealed_write_with_no_lane_key_is_refused_rather_than_stored_clear():
    try:
        W.seal_payloads("lane_entry", an_entry(), lane_key=None, at=AT)
    except W.LaneKeyRequired as exc:
        assert "no clear column to fall back to" in str(exc), exc
    else:
        raise AssertionError("a payload was written with no key to seal it")


def test_the_master_key_never_touches_a_record_at_the_seam_either():
    """§5's first line, enforced by type in `records/atrest.py` and not
    circumvented here by a seam that accepts anything key-shaped."""
    try:
        W.seal_payloads("lane_entry", an_entry(), lane_key=atrest.new_master(),
                        at=AT)
    except W.LaneKeyRequired as exc:
        assert "MasterKey" in str(exc) or "root key" in str(exc), exc
    else:
        raise AssertionError("the master key sealed a record")


def test_a_key_for_another_lane_is_refused():
    """W-1: sealing Ben's row under Cara's key makes one erasure two data losses."""
    try:
        W.seal_payloads("lane_entry", an_entry(),
                        lane_key=a_lane_key(OTHER_LANE), at=AT)
    except W.LaneKeyMismatch as exc:
        assert "One lane, one key" in str(exc), exc
        assert OTHER_LANE in str(exc) and LANE in str(exc), exc
    else:
        raise AssertionError("a row was sealed under another lane's key")


def test_a_row_with_no_payload_at_all_is_refused_at_the_seam():
    """`NOT NULL` moved here when 004 made the sealed column nullable, and this
    is where that is said (§7.2)."""
    body = an_entry()
    del body["payload"]
    try:
        W.seal_payloads("lane_entry", body, lane_key=a_lane_key(), at=AT)
    except W.PayloadMissing as exc:
        assert "migration 004" in str(exc), exc
    else:
        raise AssertionError("a lane_entry landed with no payload")


def test_a_str_payload_is_refused_rather_than_guessed_at():
    """Encoding is the caller's decision; guessing puts a charset in the
    ciphertext (`records/atrest.py::seal_bytes`, one layer up)."""
    try:
        W.seal_payloads("lane_entry", an_entry(payload='{"note":1}'),
                        lane_key=a_lane_key(), at=AT)
    except W.SealingRefused as exc:
        assert "bytes" in str(exc), exc
    else:
        raise AssertionError("a str payload was encoded by the store")


def test_a_table_with_no_sealed_column_passes_through_untouched():
    """A guard that refuses everything is not a guard. `lane` has no sealed
    column, so a write to it must be unaffected by any of the above — including
    by the absence of a lane key."""
    values = dict(lane_id=LANE, subject_id="p", exit_terms="everything, as CSV")
    assert W.seal_payloads("lane", values, lane_key=None, at=None) == values


def test_all_four_refusals_are_one_family_a_caller_can_catch():
    for cls in (W.EnvelopeColumnRefused, W.LaneKeyRequired, W.LaneKeyMismatch,
                W.PayloadMissing):
        assert issubclass(cls, W.SealingRefused)
        assert issubclass(cls, ValueError)


# --- unsealing is not the store's job --------------------------------------


#: The verbs that open a payload. A `store/` module naming one has taken custody
#: of a key, which is the thing the design says it never does.
UNSEALING = frozenset({"unseal", "unseal_with", "unwrap", "reseal", "destroy",
                       "rewrap", "rotate_lane_key"})


def test_no_module_in_the_store_unseals_anything():
    """**The core/seam partition (§6), as a guard rather than a paragraph.**

    The store holds ciphertext and does not hold the key; that is what turns
    *"an agent cannot carry the records out"* from a policy promise into a
    cryptographic one. A single `unseal()` in `store/` would end it, silently,
    and the module docstring saying otherwise would still read correctly.

    `seal_bytes` is deliberately not in the list — sealing is the seam's job and
    unsealing is not, and a scan that refused both would refuse the design.
    """
    offenders = []
    for py in sorted((ROOT / "store").rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or \
                    getattr(node.func, "attr", None)
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    if a.name in UNSEALING:
                        name = a.name
            if name in UNSEALING:
                offenders.append(f"{py.relative_to(ROOT)}:{node.lineno} {name}")
    assert not offenders, (
        "the store unseals: " + "; ".join(offenders) + ". Reads return the "
        "envelope and the caller holding the lane key opens it (§6)")


def test_the_scan_would_catch_an_unsealing_store():
    """The scan above passes over a store that does not unseal, which is also
    what it would do over a scan that checks nothing (rule 19)."""
    tree = ast.parse("from records.atrest import unseal\n"
                     "def read(x):\n    return unseal(x, keyring=None)\n")
    found = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and (getattr(n.func, "id", None) or getattr(n.func, "attr", None))
             in UNSEALING]
    assert found, "the scan's own matcher finds nothing in an unsealing module"


def test_the_store_does_not_hold_key_material_in_a_signature_default():
    """A default key on the seam would make *seal with the ambient key* the easy
    call, and `records/atrest.py` persists nothing precisely so that no such
    thing exists."""
    import inspect
    sig = inspect.signature(W.insert_draft)
    assert sig.parameters["lane_key"].default is None
    assert sig.parameters["lane_key"].kind is inspect.Parameter.KEYWORD_ONLY


if __name__ == "__main__":
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    print(f"\ntest_sealing_plan: {len(tests) - failures}/{len(tests)} passed")
    raise SystemExit(1 if failures else 0)
