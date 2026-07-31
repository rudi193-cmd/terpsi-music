"""A read and its disclosure entry commit together, or neither commits.

`docs/PLAN-STORE.md` decision 6, and the sixth forbidden act on its acceptance
list: **"A read commits without its disclosure entry; a disclosure entry without
its read."** Both halves are attempted here.

**The same-transaction claim is checked against the database rather than
asserted.** `pg_current_xact_id()` is taken inside the transaction the read runs
in, and the committed row's `xmin` is the transaction that wrote it. Comparing
them is the difference between a mechanism and a note about one (rule 18) — an
implementation that read, committed, and then wrote the entry in a second
transaction passes every test that only counts rows.

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

from records.disclosure import GENESIS, Entry, entry_for  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Field, Outcome, Principal, Serving, serve  # noqa: E402
from store.narration import (NarratedState, NarrationWithoutRead, Passage,  # noqa: E402
                             narrate, project, serve_field, unproject)

AT = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)

BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")
ENTRY = uuid.UUID("33333333-1111-1111-1111-111111111111")
NO_SUCH_LANE = uuid.UUID("99999999-9999-9999-9999-999999999999")


def seed(owner):
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (ANN, "1979-02-02")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                    (LBEN, BEN, "everything, as CSV, on request"))
        # The entry is read by `entry_id`, never by its payload — which is the
        # point being made one file over: above the derive floor the store
        # serves an instruction and never opens anything. Since migration 004
        # the clear column is constrained to NULL, so there is nothing to put a
        # value in and nothing here needs one.
        cur.execute(
            "INSERT INTO lane_entry (entry_id, lane_id, kind, author_id, "
            " created_at, valid_at) VALUES (%s,%s,'allergy',%s,now(),now())",
            (ENTRY, LBEN, ANN))
    owner.commit()


def served(rows):
    """A predicate that discloses. Stands in for `records/serving.serve`, whose
    own inputs are not what this file is about."""
    return Serving(Outcome.PAYLOAD, str(rows[0][0]) if rows else None, Rung.L4,
                   "L4 with edge and declared purpose", via_edge="guardian_of")


def refused(rows):
    return Serving(Outcome.REFUSED, None, Rung.L4, "no live entitlement edge")


def count(conn):
    return conn.execute("SELECT count(*) FROM disclosure_log").fetchone()[0]


def a_read(conn, decide=served, **over):
    kw = dict(query="SELECT payload FROM lane_entry WHERE entry_id = %s",
              params=(ENTRY,), decide=decide, principal_id=str(ANN),
              subject_id=str(BEN), lane_id=str(LBEN), field_name="allergy",
              at=AT, recipient="guardian_of", authority="grant-x")
    kw.update(over)
    return serve_field(conn, **kw)


# --- the ordinary path, and the atomicity proof -----------------------------


def test_a_narrated_read_serves_and_logs_in_one_transaction():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            before = count(app)
            got = a_read(app)
            assert got.state is NarratedState.SERVED, got.reason
            assert got.value is not None
            assert count(app) == before + 1

            # The proof, from the database: the transaction that wrote the row
            # is the transaction the read ran in.
            xmin = app.execute(
                "SELECT xmin::text FROM disclosure_log ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
            assert int(xmin) == got.xid, (
                f"the entry was written by transaction {xmin} and the read ran "
                f"in {got.xid} — they are not the same transaction")
        finally:
            app.close()
            owner.close()


def test_every_outcome_is_narrated_including_a_refusal():
    """Rule 10: an audit trail that logs only agreement is not one. A refusal
    that went unrecorded is precisely the row an audit needs to answer *"was
    this restriction working"*."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = a_read(app, decide=refused)
            assert got.state is NarratedState.SERVED
            assert got.serving.outcome is Outcome.REFUSED
            what = app.execute(
                "SELECT what FROM disclosure_log ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
            assert what.endswith("refused"), what
        finally:
            app.close()
            owner.close()


def test_the_lanes_chain_links_entry_to_entry():
    """Per lane, because `records/disclosure.Ledger` is per lane: a position must
    mean *the nth thing about your child* and nothing else."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            a_read(app)
            a_read(app)
            rows = app.execute(
                "SELECT prev_hash, hash FROM disclosure_log ORDER BY seq"
            ).fetchall()
            assert len(rows) == 2
            assert bytes(rows[0][0]).hex() == GENESIS
            assert bytes(rows[1][0]) == bytes(rows[0][1]), (
                "the second entry does not follow the first")
        finally:
            app.close()
            owner.close()


# --- half one: a read that cannot be narrated does not commit ---------------


def test_a_read_whose_narration_cannot_be_written_does_not_commit():
    """The disclosure entry names a lane that does not exist, so the `INSERT`
    hits a foreign key. The whole transaction rolls back: no entry, and — the
    part that matters — **no served value reaches the caller**, because the
    value is returned only on the far side of the commit."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            before = count(app)
            got = a_read(app, lane_id=str(NO_SUCH_LANE))
            assert got.state is NarratedState.UNAVAILABLE
            assert "did not commit" in got.reason
            try:
                got.value
            except Exception as exc:  # noqa: BLE001
                assert "nothing was served" in str(exc)
            else:
                raise AssertionError(
                    "a value was served out of a transaction that rolled back")
            assert count(app) == before, "an entry landed from a rolled-back read"
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_a_predicate_that_raises_between_the_read_and_the_narration_commits_neither():
    """The abort between the two halves, made deliberately."""
    def explodes(rows):
        raise RuntimeError("the read predicate blew up")

    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            before = count(app)
            got = a_read(app, decide=explodes)
            assert got.state is NarratedState.UNAVAILABLE
            assert "blew up" in got.reason
            assert count(app) == before
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_a_store_that_went_down_mid_read_narrates_nothing():
    """Nothing was decided, so there is nothing to narrate — and the caller gets
    an unavailable answer rather than a served one."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = a_read(app, query="SELECT nonexistent FROM lane_entry",
                         params=())
            assert got.state is NarratedState.UNAVAILABLE
            app.rollback()
            assert count(app) == 0
        finally:
            app.rollback()
            app.close()
            owner.close()


# --- half two: a narration without its read ---------------------------------


def test_a_narration_without_a_live_passage_is_refused():
    """A passage minted by a read that has since committed is no longer in the
    current transaction, and `Passage.check` asks the database rather than
    trusting the field. This is *a disclosure entry without its read*, and there
    is no spelling of it that lands."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = a_read(app)          # mints a passage, commits
            assert got.state is NarratedState.SERVED
            stale = Passage(got.xid, str(LBEN), "allergy")
            entry = entry_for(served([(1,)]), principal_id=str(ANN),
                              subject_id=str(BEN), field_name="allergy", at=AT,
                              prev=GENESIS, authority="grant-x")
            before = count(app)
            try:
                narrate(app, entry, passage=stale, lane_id=str(LBEN),
                        recipient="guardian_of")
            except NarrationWithoutRead as exc:
                assert "belongs in the transaction of the read" in str(exc)
            else:
                raise AssertionError("an entry was written with no read to narrate")
            app.rollback()
            assert count(app) == before
        finally:
            app.close()
            owner.close()


def test_a_passage_invented_out_of_thin_air_is_refused():
    """The blunt version: a caller that constructs a `Passage` rather than
    obtaining one. The transaction id is the database's, so a made-up one does
    not match whatever the connection is actually in."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            entry = entry_for(served([(1,)]), principal_id=str(ANN),
                              subject_id=str(BEN), field_name="allergy", at=AT,
                              prev=GENESIS)
            try:
                narrate(app, entry, passage=Passage(1, str(LBEN), "allergy"),
                        lane_id=str(LBEN), recipient="guardian_of")
            except NarrationWithoutRead:
                app.rollback()
                assert count(app) == 0
                return
            raise AssertionError("a fabricated passage wrote a disclosure entry")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_the_disclosure_log_still_refuses_to_be_rewritten():
    """001's append-only trigger, re-attacked through the store rather than
    through `psql`, because that is the path an application takes. Two guards
    now cover it and each is asserted by name: the privilege for the app role,
    the trigger for the owner."""
    from cluster import refused_by

    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            a_read(app)
            refused_by(lambda: app.execute(
                "UPDATE disclosure_log SET what = 'nothing happened'"), "42501")
            app.rollback()
            refused_by(lambda: owner.execute(
                "UPDATE disclosure_log SET what = 'nothing happened'"),
                "append-only")
            owner.rollback()
            refused_by(lambda: owner.execute("DELETE FROM disclosure_log"),
                       "append-only")
        finally:
            owner.rollback()
            app.close()
            owner.close()


# --- the projection: §16's middle, both directions --------------------------


def test_the_projection_round_trips():
    """The table and `records/disclosure.Entry` are two spellings of one record,
    which is §16's pair. `project`/`unproject` is the named middle, and a middle
    that does not round-trip is a lossy conversion with a reassuring name."""
    for outcome, rung in ((Outcome.PAYLOAD, Rung.L4), (Outcome.REFUSED, Rung.L3),
                          (Outcome.INSTRUCTION, Rung.L4), (Outcome.UNKNOWN, None)):
        entry = entry_for(Serving(outcome, None, rung, "why"),
                          principal_id=str(ANN), subject_id=str(BEN),
                          field_name="allergy", at=AT, prev=GENESIS,
                          authority="grant-x")
        row = project(entry, lane_id=str(LBEN), recipient="guardian_of")
        back = unproject(row, subject_id=str(BEN))
        assert back == entry, f"{outcome} did not round-trip: {back} != {entry}"


def test_the_digest_in_the_table_is_the_one_records_disclosure_computed():
    """One chain algorithm, two storage shapes. If the store computed its own
    hash there would be two, and the second would be right until the day it was
    not."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            got = a_read(app)
            stored = app.execute(
                "SELECT hash FROM disclosure_log ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
            assert bytes(stored).hex() == got.entry.digest
            recomputed = entry_for(got.serving, principal_id=str(ANN),
                                   subject_id=str(BEN), field_name="allergy",
                                   at=AT, prev=GENESIS, authority="grant-x")
            assert recomputed.digest == got.entry.digest
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
        raise SystemExit(report("test_store_narration", 0, len(tests), unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_narration", failures, len(tests)))
