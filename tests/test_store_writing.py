"""The draft-write path: what lands, and what is refused with the registry cited.

Two of `docs/PLAN-STORE.md`'s forbidden acts are attempted here — **an `INSERT`
into a column the classification registry does not carry**, and an application
write arriving already sealed — plus the control that proves the adapter is not
simply broken shut.

**The registry is `tools/registry.py`'s and this file checks that too.** The
adapter reads the seed out of `migrations/001_lanes.sql`; the cluster has its own
copy in `field_classification`. Two copies of one mapping is exactly the pair
`tools/registry.py` exists to close, so the pair is closed here as well: the
adapter's view and the cluster's are asserted equal, and a row added to one and
not the other goes red.

Needs a database. No skip — see `tests/cluster.py`.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import ClusterUnknown, Database, available, installed, report  # noqa: E402

from store.classification import (UnclassifiedColumn, carries,  # noqa: E402
                                  classification_of, registry_columns)
from store.writing import (OPENS_AS, SEALED, SealStateRefused,  # noqa: E402
                           UnknownTable, insert_draft)

AT = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)

BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")


def seed(owner):
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (ANN, "1979-02-02")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                    (LBEN, BEN, "everything, as CSV, on request"))
    owner.commit()


def an_entry(**over):
    body = dict(entry_id=uuid.uuid4(), lane_id=LBEN, kind="attendance",
                payload="{}", author_id=ANN, created_at=AT, valid_at=AT)
    body.update(over)
    return body


# --- the ordinary path ------------------------------------------------------


def test_an_application_write_lands_as_a_draft():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = insert_draft(app, "lane_entry", an_entry(),
                               returning="entry_id")
            app.commit()
            state = app.execute(
                "SELECT seal_state FROM lane_entry WHERE entry_id = %s", (got,)
            ).fetchone()[0]
            assert state == "draft"
        finally:
            app.close()
            owner.close()


def test_the_write_does_not_commit_itself():
    """The caller owns the transaction, because a write that committed itself
    could not share one with the disclosure entry that narrates it."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            insert_draft(app, "lane_entry", an_entry())
            app.rollback()
            n = app.execute("SELECT count(*) FROM lane_entry").fetchone()[0]
            assert n == 0, "insert_draft committed on the caller's behalf"
        finally:
            app.close()
            owner.close()


# --- forbidden act: a column the registry does not carry --------------------


def test_an_insert_into_an_unclassified_column_is_refused_with_the_registry_cited():
    """The registry is the guard **named** in the refusal, not just the fact of
    one: a caller who reads the message must be able to go and add the row."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            body = an_entry()
            body["nickname"] = "Benny"
            try:
                insert_draft(app, "lane_entry", body)
            except UnclassifiedColumn as exc:
                assert "lane_entry.nickname" in str(exc)
                assert "tools/registry.py" in str(exc)
                assert "not a default" in str(exc)
            else:
                raise AssertionError("an unclassified column was inserted into")
            app.rollback()
            assert app.execute(
                "SELECT count(*) FROM lane_entry").fetchone()[0] == 0
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_a_write_to_a_table_the_registry_does_not_carry_is_refused():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            try:
                insert_draft(app, "schema_migrations", {"filename": "x"})
            except UnknownTable as exc:
                assert "schema_migrations" in str(exc)
                assert isinstance(exc, UnclassifiedColumn), (
                    "UnknownTable must be catchable as UnclassifiedColumn")
            else:
                raise AssertionError("a write to an unregistered table was built")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_a_returning_column_is_checked_too():
    """The obvious hole: a checked column list and an unchecked `RETURNING`."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            try:
                insert_draft(app, "lane_entry", an_entry(), returning="nickname")
            except UnclassifiedColumn:
                return
            raise AssertionError("an unclassified column was returned")
        finally:
            app.rollback()
            app.close()
            owner.close()


# --- forbidden act: an application write that arrives sealed ----------------


def test_an_application_write_cannot_arrive_sealed():
    """§8.2 and rule 10. A row inserted as `sealed` skipped the only step that
    makes it a record, and afterwards is indistinguishable from one somebody
    stood behind."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            try:
                insert_draft(app, "lane_entry",
                             an_entry(seal_state=SEALED, sealed_by=ANN))
            except SealStateRefused as exc:
                assert "records/sealing.py" in str(exc)
                assert "named human" in str(exc)
            else:
                raise AssertionError("an application write arrived sealed")
            app.rollback()
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_an_application_write_cannot_name_a_sealer():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            try:
                insert_draft(app, "lane_entry", an_entry(sealed_by=ANN))
            except SealStateRefused as exc:
                assert "sealed_by is set by the seal" in str(exc)
            else:
                raise AssertionError("an application write named a sealer")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_a_state_outside_the_cascade_is_refused_by_name():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            try:
                insert_draft(app, "lane_entry", an_entry(seal_state="approved"))
            except SealStateRefused as exc:
                assert "'approved'" in str(exc)
                assert "a third state is a place for a row to hide in" in str(exc)
            else:
                raise AssertionError("a state outside the cascade was accepted")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_pending_is_still_reachable():
    """A guard that refuses everything is not a guard. `pending` is in the
    cascade and must stay writable, or the refusals above are satisfied by an
    adapter that accepts nothing."""
    assert "pending" in OPENS_AS and SEALED not in OPENS_AS
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = insert_draft(app, "lane_entry", an_entry(seal_state="pending"),
                               returning="entry_id")
            app.commit()
            assert app.execute(
                "SELECT seal_state FROM lane_entry WHERE entry_id = %s", (got,)
            ).fetchone()[0] == "pending"
        finally:
            app.close()
            owner.close()


# --- the registry the adapter reads is the one in the cluster ---------------


def test_the_registry_the_adapter_reads_is_the_one_in_the_cluster():
    """Two copies of one mapping — the migration's seed as text, and
    `field_classification` as rows. `tools/registry.py` is the middle for the
    seed against the procedure and the document; this is the fourth leg, and
    without it the store could enforce a registry the cluster does not have."""
    with Database() as db:
        owner, app = installed(db)
        try:
            in_cluster = {(t, c): (k, r) for t, c, k, r in owner.execute(
                "SELECT table_name, column_name, data_class, rung "
                "FROM field_classification").fetchall()}
            from_text = {key: classification_of(*key) for key in registry_columns()}
            assert from_text == in_cluster, (
                "the adapter's registry and the cluster's disagree: "
                f"{set(from_text) ^ set(in_cluster)}")
            # Derived, never quoted (rule 17).
            assert len(from_text) == len(registry_columns())
        finally:
            app.close()
            owner.close()


def test_every_column_the_ddl_declares_is_one_the_adapter_will_accept():
    """The reverse direction: a column that exists and is unclassified would be
    refused by the adapter, which is correct — and would also mean CI's *every
    column is classified* step should already have failed. Asserting both keeps
    the two checks from silently covering for each other."""
    with Database() as db:
        owner, app = installed(db)
        try:
            declared = owner.execute(
                "SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' ORDER BY 1, 2").fetchall()
            missing = [(t, c) for t, c in declared if not carries(t, c)]
            assert not missing, f"the adapter would refuse live columns: {missing}"
        finally:
            app.close()
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
        raise SystemExit(report("test_store_writing", 0, len(tests), unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_writing", failures, len(tests)))
