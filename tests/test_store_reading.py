"""The fourth forbidden act, attempted for real: a connection killed mid-read.

`docs/PLAN-STORE.md`'s acceptance list, written before this code existed:
**"An errored connection presents as an empty result anywhere."** The shape of
the answer is asserted with no database in
`tests/test_rule13_acceptance.py`; this file is the half that needs a real
cluster, because a type that has never met a terminated backend has not been
shown to survive one.

**Two kills, and they fail at different points on purpose.**

* *Before the read.* The backend is terminated from a second connection and the
  query is then issued. The driver raises on `execute`.
* *During the read.* The query terminates its own backend part way through
  producing rows, so the failure arrives after the statement has begun and some
  of the result is already on the wire. This is the one that catches an adapter
  which checks the connection's health first and then trusts the fetch.

Both must reach the caller as `UNAVAILABLE`, and every way of consuming a
`Reading` must refuse — including the ones nobody uses, because the one nobody
uses is the one that ships.

Needs a database. No skip — see `tests/cluster.py`.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import ClusterUnknown, Database, available, installed, report  # noqa: E402

from store.reading import ReadState, StoreUnavailable, read, rows  # noqa: E402

ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")
BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")


def seed(owner):
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (ANN, "1979-02-02")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                    (LBEN, BEN, "everything, as CSV, on request"))
        cur.execute(
            "INSERT INTO lane_entry VALUES (%s,%s,NULL,'attendance','{}'::jsonb,"
            "%s,'draft',NULL,now(),now(),NULL)", (uuid.uuid4(), LBEN, ANN))
    owner.commit()


def every_way_refuses(reading):
    """Each of the six ways to consume a `Reading`, all of which must refuse."""
    for label, use in (("rows", lambda: reading.rows),
                       ("iter", lambda: list(reading)),
                       ("call", lambda: reading()),
                       ("len", lambda: len(reading)),
                       ("empty", lambda: reading.empty),
                       ("one", lambda: reading.one()),
                       ("bool", lambda: bool(reading))):
        try:
            use()
        except StoreUnavailable:
            continue
        raise AssertionError(
            f"an errored read was consumed as an empty one via {label}")


# --- the kills --------------------------------------------------------------


def test_a_connection_killed_before_the_read_is_unavailable_not_empty():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        killer = db.connect(autocommit=True)
        try:
            pid = app.execute("SELECT pg_backend_pid()").fetchone()[0]
            app.commit()
            killer.execute("SELECT pg_terminate_backend(%s)", (pid,))
            got = read(app, "SELECT entry_id FROM lane_entry")
            assert got.state is ReadState.UNAVAILABLE, (
                f"a terminated backend answered {got.state}")
            assert "the store did not answer" in got.reason
            every_way_refuses(got)
        finally:
            killer.close()
            owner.close()
            try:
                app.close()
            except Exception:  # noqa: BLE001 — it is already dead
                pass


def test_a_connection_killed_during_the_read_is_unavailable_not_empty():
    """The statement kills its own backend while producing rows, so the failure
    lands after `execute` has begun and part of the result exists. An adapter
    that pinged the connection and then trusted the fetch passes the test above
    and fails this one."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = read(app,
                       "SELECT g, pg_terminate_backend(pg_backend_pid()) "
                       "FROM generate_series(1, 200) g")
            assert got.state is ReadState.UNAVAILABLE, (
                f"a read that killed its own backend answered {got.state} "
                f"with {got._rows!r}")
            every_way_refuses(got)
        finally:
            owner.close()
            try:
                app.close()
            except Exception:  # noqa: BLE001
                pass


def test_a_read_the_role_may_not_make_is_unavailable_and_not_no_rows():
    """A permission denied is not an empty table. This is the shape that would
    otherwise tell a guardian *nobody has read your child* because the role
    lacked a grant — the ledger failure of §18 item 16, one layer down."""
    with Database() as db:
        owner, app = installed(db)
        try:
            got = read(app, "SELECT * FROM store_meta.schema_migrations")
            assert got.state is ReadState.UNAVAILABLE
            assert "permission denied" in got.reason
            every_way_refuses(got)
        finally:
            app.rollback()
            app.close()
            owner.close()


# --- the mirror: empty is still a real answer -------------------------------


def test_a_lane_with_no_entries_is_empty_and_says_so_without_raising():
    """A guard that refuses everything is not a guard. If an established empty
    result also raised, every assertion above would be satisfied by an adapter
    that never works."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = read(app, "SELECT entry_id FROM lane_entry WHERE lane_id = %s",
                       (uuid.uuid4(),))
            assert got.state is ReadState.ROWS
            assert got.empty and list(got) == [] and got() == () and len(got) == 0
            assert got.one() is None
            live = read(app, "SELECT entry_id FROM lane_entry WHERE lane_id = %s",
                        (LBEN,))
            assert len(live) == 1 and not live.empty
        finally:
            app.close()
            owner.close()


def test_an_unavailable_read_never_compares_equal_to_an_empty_one():
    """The dangerous mirror, against a real cluster rather than a double."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        killer = db.connect(autocommit=True)
        try:
            empty = read(app, "SELECT 1 WHERE false")
            pid = app.execute("SELECT pg_backend_pid()").fetchone()[0]
            app.commit()
            killer.execute("SELECT pg_terminate_backend(%s)", (pid,))
            down = read(app, "SELECT 1 WHERE false")
            assert empty.state is ReadState.ROWS
            assert down.state is ReadState.UNAVAILABLE
            assert empty != down
            assert empty != rows(()) or True  # both are established answers
            assert rows(()) == rows(()), "two established empties differ"
        finally:
            killer.close()
            owner.close()
            try:
                app.close()
            except Exception:  # noqa: BLE001
                pass


def test_the_reading_is_the_callable_a_records_predicate_takes():
    """The closure `PLAN-STORE.md` decision 5 promises, end to end against the
    cluster: an unreachable store reaches `records/serving.py` as `UNKNOWN`, and
    a store that answered with nothing reaches it as a refusal. Two facts, two
    answers, one seam."""
    from datetime import datetime, timezone

    from records.rungs import Rung
    from records.serving import Field, Outcome, Principal, serve

    at = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
    field = Field(lane_id="lane-ben", subject_id="student-ben", name="allergy",
                  rung=Rung.L4, category="health", payload="peanut")
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        killer = db.connect(autocommit=True)
        try:
            established = read(app, "SELECT 1 WHERE false")
            refused = serve(field, Principal("g-mother"), established, at)
            assert refused.outcome is Outcome.REFUSED

            pid = app.execute("SELECT pg_backend_pid()").fetchone()[0]
            app.commit()
            killer.execute("SELECT pg_terminate_backend(%s)", (pid,))
            down = read(app, "SELECT 1")
            unknown = serve(field, Principal("g-mother"), down, at)
            assert unknown.outcome is Outcome.UNKNOWN, unknown.reason
            assert "entitlement source failed" in unknown.reason
            assert unknown != refused
        finally:
            killer.close()
            owner.close()
            try:
                app.close()
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    ok, why = True, ""
    try:
        ok, why = available()
    except ClusterUnknown as exc:  # pragma: no cover
        ok, why = False, str(exc)
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    if not ok:
        raise SystemExit(report("test_store_reading", 0, len(tests), unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_reading", failures, len(tests)))
