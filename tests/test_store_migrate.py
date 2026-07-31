"""The migration runner's three refusals, attempted against a real cluster.

`store/migrate.py` records what it applied and refuses two things that would
otherwise be silent — a file edited after it was applied, and a file numbered
below one already applied — and reports a third, an unreadable migrations
directory, as its own state rather than as an empty plan.

All three are attempted here. The third matters most and looks least like a
bug: *"there are no migrations to apply"* and *"the migrations could not be
listed"* are the same sentence, and the first is how an instance comes up with
no schema and no complaint (rule 13).

Needs a database. No skip — see `tests/cluster.py`.

    python3 -m pytest tests/test_store_migrate.py -q
    python3 tests/test_store_migrate.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import ClusterUnknown, Database, available, report  # noqa: E402

from store.migrate import (LEDGER, MigrationModified, MigrationOutOfOrder,  # noqa: E402
                           Plan, PlanState, apply_all, checksum, discover, run)
from store.roles import META_SCHEMA  # noqa: E402

MIGRATIONS = ROOT / "migrations"


def written(where: Path, name: str, body: str) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    p = where / name
    p.write_text(body, encoding="utf-8")
    return p


def a_pair(where: Path):
    written(where, "001_first.sql", "CREATE TABLE alpha (x text);")
    written(where, "003_third.sql", "CREATE TABLE gamma (z text);")
    return where


# --- the ordinary path ------------------------------------------------------


def test_the_real_migrations_apply_in_filename_order_and_are_recorded():
    """The tree's own migrations, run by the runner rather than by `psql -f`.

    The count is derived from the directory, never quoted: rule 17, in the test
    that would otherwise be the easiest place in the repository to write a
    number that drifts.
    """
    on_disk = sorted(p.name for p in MIGRATIONS.glob("*.sql"))
    with Database() as db:
        owner = db.connect()
        try:
            landed = run(owner, MIGRATIONS)
            assert [m.filename for m in landed] == on_disk, (
                f"{[m.filename for m in landed]} applied, {on_disk} on disk")
            assert [m.ordinal for m in landed] == list(range(1, len(on_disk) + 1))
            rows = owner.execute(
                f"SELECT filename, checksum FROM {LEDGER} ORDER BY ordinal"
            ).fetchall()
            assert [r[0] for r in rows] == on_disk
            for name, digest in rows:
                assert digest == checksum(
                    (MIGRATIONS / name).read_text(encoding="utf-8"))
            # And the schema is really there.
            tables = {r[0] for r in owner.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'").fetchall()}
            assert "lane_entry" in tables and "disclosure_log" in tables
        finally:
            owner.close()


def test_a_second_run_applies_nothing_and_is_not_an_error():
    with Database() as db:
        owner = db.connect()
        try:
            first = run(owner, MIGRATIONS)
            again = apply_all(owner, MIGRATIONS)
            assert first and again == (), f"a second run re-applied {again}"
        finally:
            owner.close()


def test_the_runners_ledger_holds_no_domain_table():
    """`store_meta` exists so the runner's bookkeeping is not mistaken for
    domain data — and so CI's *every column is classified* check, which scans
    `public`, does not have to classify a checksum as if it were a fact about a
    student. The separation is only worth anything if it holds."""
    with Database() as db:
        owner = db.connect()
        try:
            run(owner, MIGRATIONS)
            here = {r[0] for r in owner.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s", (META_SCHEMA,)).fetchall()}
            assert here == {"schema_migrations"}, here
        finally:
            owner.close()


# --- refusal 1: a migration that changed after it was applied ---------------


def test_a_modified_migration_is_refused_and_never_re_applied():
    with tempfile.TemporaryDirectory() as d, Database() as db:
        where = a_pair(Path(d))
        owner = db.connect()
        try:
            run(owner, where)
            (where / "001_first.sql").write_text(
                "CREATE TABLE alpha (x text, y text);", encoding="utf-8")
            try:
                discover(owner, where)
            except MigrationModified as exc:
                assert "001_first.sql" in str(exc)
                assert "history" in str(exc)
            else:
                raise AssertionError("an edited migration was accepted")
            # And the edit did not land: the ledger still holds the old digest.
            digest = owner.execute(
                f"SELECT checksum FROM {LEDGER} WHERE filename = '001_first.sql'"
            ).fetchone()[0]
            assert digest != checksum((where / "001_first.sql").read_text())
        finally:
            owner.close()


def test_whitespace_is_a_modification_too():
    """The checksum is over the bytes as read, deliberately. Deciding which
    edits are harmless is a judgement no runner should be making at three in the
    morning, and a reformat that changes a `plpgsql` body is not harmless."""
    with tempfile.TemporaryDirectory() as d, Database() as db:
        where = a_pair(Path(d))
        owner = db.connect()
        try:
            run(owner, where)
            (where / "003_third.sql").write_text(
                "CREATE TABLE gamma (z text);\n", encoding="utf-8")
            try:
                discover(owner, where)
            except MigrationModified:
                return
            raise AssertionError("a whitespace edit to an applied migration passed")
        finally:
            owner.close()


# --- refusal 2: out of order -----------------------------------------------


def test_a_migration_numbered_below_one_already_applied_is_refused():
    """The one that looks harmless: it applies cleanly here, and lands in the
    other order on an instance that has run neither. Two schemas, one ledger."""
    with tempfile.TemporaryDirectory() as d, Database() as db:
        where = a_pair(Path(d))
        owner = db.connect()
        try:
            run(owner, where)
            written(where, "002_second.sql", "CREATE TABLE beta (y text);")
            try:
                discover(owner, where)
            except MigrationOutOfOrder as exc:
                assert "002_second.sql" in str(exc) and "003_third.sql" in str(exc)
            else:
                raise AssertionError("an out-of-order migration was accepted")
            tables = {r[0] for r in owner.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'").fetchall()}
            assert "beta" not in tables, "the out-of-order migration applied anyway"
        finally:
            owner.close()


def test_a_migration_above_the_highest_applied_is_not_refused():
    """The control. A rule that refused every new migration would satisfy the
    test above and stop the repository."""
    with tempfile.TemporaryDirectory() as d, Database() as db:
        where = a_pair(Path(d))
        owner = db.connect()
        try:
            run(owner, where)
            written(where, "004_fourth.sql", "CREATE TABLE delta (w text);")
            landed = apply_all(owner, where)
            assert [m.filename for m in landed] == ["004_fourth.sql"]
            assert landed[0].ordinal == 3
        finally:
            owner.close()


# --- refusal 3: the directory itself ---------------------------------------


def test_an_unreadable_migrations_directory_is_its_own_state_not_an_empty_plan():
    """Rule 13, at the runner. `PlanState.UNREADABLE`, a reason, and iteration
    that raises — because `for m in discover(...)` over a directory that could
    not be listed is indistinguishable, from the loop alone, from an instance
    that is up to date."""
    missing = Path(tempfile.gettempdir()) / "terpsi-no-such-migrations-4b1e"
    assert not missing.exists(), f"{missing} exists; this fixture is not unreachable"
    with Database() as db:
        owner = db.connect()
        try:
            plan = discover(owner, missing)
            assert plan.state is PlanState.UNREADABLE
            assert not plan.readable and plan.pending == ()
            assert str(missing) in plan.reason
            try:
                list(plan)
            except RuntimeError as exc:
                assert "not an empty one" in str(exc)
            else:
                raise AssertionError("an unreadable plan iterated as an empty one")
            try:
                apply_all(owner, missing)
            except RuntimeError:
                pass
            else:
                raise AssertionError("apply_all ran over an unreadable directory")
        finally:
            owner.close()


def test_a_file_where_the_directory_should_be_is_unreadable_not_empty():
    with tempfile.TemporaryDirectory() as d, Database() as db:
        not_a_dir = written(Path(d), "migrations", "this is a file")
        owner = db.connect()
        try:
            plan = discover(owner, not_a_dir)
            assert plan.state is PlanState.UNREADABLE
            assert "not a directory" in plan.reason
        finally:
            owner.close()


def test_an_empty_directory_is_ready_with_nothing_pending_and_that_is_different():
    """The mirror. An empty migrations directory is a real, established answer
    and must not compare equal to one that could not be read."""
    with tempfile.TemporaryDirectory() as d, Database() as db:
        owner = db.connect()
        try:
            empty = discover(owner, Path(d))
            unreadable = Plan(PlanState.UNREADABLE, (), (), "gone")
            assert empty.state is PlanState.READY and empty.readable
            assert list(empty) == []
            assert empty != unreadable and empty.state is not unreadable.state
        finally:
            owner.close()


if __name__ == "__main__":
    ok, why = True, ""
    try:
        ok, why = available()
    except ClusterUnknown as exc:  # pragma: no cover
        ok, why = False, str(exc)
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    if not ok:
        raise SystemExit(report("test_store_migrate", 0, len(tests), unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_migrate", failures, len(tests)))
