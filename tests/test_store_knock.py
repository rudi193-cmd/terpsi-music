"""The knock in enforcement mode, over a real store — S-4's vertical, end to end.

`docs/PLAN-STORE.md` S-4, and §7.2: a session declares a purpose on entry and is
reconciled against what it did on exit. `tests/test_console.py` drives the guards
that turn on Python alone; this drives the ones that need a cluster, so the whole
path is exercised where it actually runs:

    knock → acting principal → read through RLS *and* the predicate → IR →
    rendered text → narration in the same transaction → exit reconciliation →
    the reconciled_session row.

**What "enforcement" means here** (rule 18). A session that reads without a
declared purpose is refused before the store is touched; an entitled director's
read is served *and narrated*; an unentitled director's read returns nothing —
refused by the lane seal in the cluster and by the predicate in Python — and on
exit the session reconciles declared against observed and lands a row, or (a
close that could not read the store) reports its own `UNKNOWN`. Something routes
through the knock, so `tools/conform.py`'s `knock-enforcing` row is a gate.

**Read-first (R16).** Every write here is narration or reconciliation —
`disclosure_log`, `reconciled_session`, both append-only history with no sealed
column. Nothing calls `store/writing.py`'s record-write path, so the escrow fuse
stays `S2` (see `tools/audit.py`, and `tests/test_audit.py`).

Needs a database. No skip — `tests/cluster.py`. Exits `2` with a loud UNKNOWN
where there is no cluster, and is held back from the guards job for that reason,
run by the schema job which has one.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import (ClusterUnknown, Database, available, installed,  # noqa: E402
                     refused_by, report)

from records.commentary import ExitState  # noqa: E402
from records.serving import Outcome  # noqa: E402

from console.render import exit_line, rendered  # noqa: E402
from console.session import (ReadWithoutDeclaration, SessionClosed,  # noqa: E402
                             open_session)

OPEN = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
READ = OPEN + timedelta(minutes=5)
CLOSE = OPEN + timedelta(minutes=30)

BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")   # Ben's guardian
CAM = uuid.UUID("11111111-5555-5555-5555-555555555555")   # a stranger to Ben
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")
ENTRY = uuid.UUID("33333333-1111-1111-1111-111111111111")
GANN = uuid.UUID("dddddddd-1111-1111-1111-111111111111")


def seed(owner):
    """Ben's lane, one entry, Ann's guardianship, and a stranger (Cam)."""
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (ANN, "1979-02-02"),
                          (CAM, "1980-03-03")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                    (LBEN, BEN, "everything, as CSV, on request"))
        cur.execute(
            "INSERT INTO edge VALUES (%s,'guardian_of',%s,%s,NULL,'enrolment "
            "form',now(),now() - interval '1 year',NULL)", (GANN, ANN, LBEN))
        # No payload: migration 004 tombstoned the clear column to NULL, and the
        # read serves `kind` — an L3 column present in the clear — not the payload.
        cur.execute(
            "INSERT INTO lane_entry (entry_id, lane_id, kind, author_id, "
            " created_at, valid_at) VALUES (%s,%s,'allergy',%s,now(),now())",
            (ENTRY, LBEN, ANN))
    owner.commit()


def _count(owner, table: str) -> int:
    return owner.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


# --- the vertical, entitled ------------------------------------------------


def test_an_entitled_director_reads_narrates_and_reconciles():
    """The whole path for a guardian who declared the lane she read.

    Served (RLS let the row through and the predicate served it), narrated (a
    disclosure entry landed in the read's own transaction), rendered (with the
    rung prefix), and reconciled (declared == observed → RECONCILED, and the
    reconciled_session row is there)."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        session = open_session(principal_id=str(ANN), purpose="review event 42",
                               event_id="event-42", lanes=(str(LBEN),), at=OPEN,
                               conn=app)
        before = _count(owner, "disclosure_log")
        served = session.read(table="lane_entry", column="kind", lane_id=str(LBEN),
                              subject_id=str(BEN), at=READ, recipient="guardian_of")

        assert served.outcome is Outcome.PAYLOAD, served.narrated.reason
        assert served.narrated.value == "allergy"
        # narrated in the same transaction: a disclosure entry landed.
        assert _count(owner, "disclosure_log") == before + 1

        text = rendered(session.compose(title="Lane view", at=READ), colour=False)
        assert "allergy" in text and "[L3 " in text and str(ANN) in text

        result = session.close(CLOSE)
        assert result.state is ExitState.RECONCILED, result.reason
        assert result.reconciled
        assert _count(owner, "reconciled_session") == 1
        row = owner.execute(
            "SELECT principal_id, declared->>'purpose', diff->>'state', "
            "observed->>'entries' FROM reconciled_session").fetchone()
        assert str(row[0]) == str(ANN)
        assert row[1] == "review event 42"
        assert row[2] == "reconciled"
        assert int(row[3]) >= 1, "the observed half saw no entry it should have"


# --- the vertical, unentitled: both layers refuse -------------------------


def test_an_unentitled_director_sees_nothing():
    """Cam holds no edge to Ben and reaches his lane through neither layer.

    The cluster returns no row (the lane seal), and Cam cannot even narrate the
    attempt — a `disclosure_log` entry on a lane he does not reach is refused by
    the same seal on the way in (`INSERT … RETURNING` cannot read back a row he
    is sealed out of). So the read is **unavailable**, not served, and renders
    `unknown` — never Ben's value and never a blank (rule 13).

    **A finding, recorded rather than smoothed over:** a principal entitled to a
    lane but refused by the *predicate* (e.g. `L4` with no purpose) is narrated
    `REFUSED`; a principal sealed out of the lane entirely cannot narrate at all
    and reads `unavailable`. Both show the director nothing, but they are
    different states, and whether the store should let an out-of-lane refusal
    leave a footprint is a store-layer question S-4 surfaces and does not
    decide."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        session = open_session(principal_id=str(CAM), purpose="curiosity",
                               event_id="event-42", lanes=(str(LBEN),), at=OPEN,
                               conn=app)
        served = session.read(table="lane_entry", column="kind", lane_id=str(LBEN),
                              subject_id=str(BEN), at=READ, recipient="none")
        assert served.outcome is None, "an out-of-lane read must not be served"
        text = rendered(session.compose(title="Lane view", at=READ), colour=False)
        assert "allergy" not in text
        assert "unknown" in text


# --- reconciliation diverges when a lane was not declared -----------------


def test_a_read_of_an_undeclared_lane_diverges_on_exit():
    """§7.2's worked failure: what was touched was not what was declared. Ann
    declares no lane, reads Ben's, and the exit records DIVERGED — whether or not
    the grant permitted it."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        session = open_session(principal_id=str(ANN), purpose="a quick look",
                               event_id="event-42", lanes=(), at=OPEN, conn=app)
        served = session.read(table="lane_entry", column="kind", lane_id=str(LBEN),
                              subject_id=str(BEN), at=READ, recipient="guardian_of")
        assert served.outcome is Outcome.PAYLOAD
        result = session.close(CLOSE)
        assert result.state is ExitState.DIVERGED, result.reason
        assert not result.reconciled
        assert str(LBEN) in result.undeclared
        # the narration the guest reads names no lane id (another student's key)
        assert str(LBEN) not in exit_line(result)
        row = owner.execute(
            "SELECT diff->>'state' FROM reconciled_session").fetchone()
        assert row[0] == "diverged"


# --- the knock refuses a read with no declaration -------------------------


def test_a_session_cannot_open_without_a_declared_purpose_over_the_store():
    """The door, with a real connection in hand: still refused, and the store is
    never touched — the refusal is the knock's, before any read."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            open_session(principal_id=str(ANN), purpose="   ", event_id="event-42",
                         lanes=(str(LBEN),), at=OPEN, conn=app)
        except ReadWithoutDeclaration:
            assert _count(owner, "disclosure_log") == 0
            return
        raise AssertionError("a session opened over the store with no purpose")


def test_a_closed_session_refuses_a_further_read_over_the_store():
    """After the exit is reconciled and the row landed, a read is a new session's."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        session = open_session(principal_id=str(ANN), purpose="review",
                               event_id="event-42", lanes=(str(LBEN),), at=OPEN,
                               conn=app)
        session.read(table="lane_entry", column="kind", lane_id=str(LBEN),
                     subject_id=str(BEN), at=READ, recipient="guardian_of")
        session.close(CLOSE)
        try:
            session.read(table="lane_entry", column="kind", lane_id=str(LBEN),
                         subject_id=str(BEN), at=CLOSE, recipient="guardian_of")
        except SessionClosed:
            return
        raise AssertionError("a closed session read the store")


# --- the reconciled_session row is history, not state ---------------------


def test_the_reconciled_session_row_cannot_be_rewritten_or_removed():
    """§7.1: reconciled sessions are history. The app role cannot UPDATE at all
    (privilege), and the append-only trigger refuses even the owner (rule 18: the
    privilege and the trigger are two guards, and each is named where it speaks)."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        session = open_session(principal_id=str(ANN), purpose="review",
                               event_id="event-42", lanes=(str(LBEN),), at=OPEN,
                               conn=app)
        session.read(table="lane_entry", column="kind", lane_id=str(LBEN),
                     subject_id=str(BEN), at=READ, recipient="guardian_of")
        session.close(CLOSE)
        # the app role: refused before any trigger, by privilege (SQLSTATE 42501)
        refused_by(lambda: app.execute(
            "UPDATE reconciled_session SET diff = '{}'::jsonb"), "42501")
        app.rollback()
        # the owner: past the privilege, refused by the append-only trigger
        refused_by(lambda: owner.execute(
            "UPDATE reconciled_session SET diff = '{}'::jsonb"), "append-only")
        owner.rollback()
        refused_by(lambda: owner.execute("DELETE FROM reconciled_session"),
                   "append-only")
        owner.rollback()


# The __main__ runner stays LAST — the harness caught that trap already.
if __name__ == "__main__":
    ok, why = available()
    if not ok:
        print(report("test_store_knock", 0, 0, unknown=why))
        raise SystemExit(2)
    failures = ran = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            ran += 1
            try:
                fn()
                print(f"ok   {name}")
            except ClusterUnknown as exc:
                print(report("test_store_knock", 0, 0, unknown=str(exc)))
                raise SystemExit(2)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    raise SystemExit(report("test_store_knock", failures, ran))
