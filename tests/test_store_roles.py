"""Gate G-D attacked: what the application role is refused, by the guard that names it.

Rule 19 — *a guard that cannot be shown to fail has not been shown to work* —
against a real PostgreSQL 16, following `.github/workflows/tests.yml`'s schema
job. Six forbidden acts from `docs/PLAN-STORE.md`'s acceptance list are
attempted here as the app role and one as the owner, and **each assertion names
the guard that must speak**:

* a privilege refusal is `SQLSTATE 42501` and names the table;
* a trigger refusal names its own message.

The two must not be allowed to stand in for one another, and that is not a
theoretical worry: a privilege check runs *before* any `BEFORE ROW` trigger, so
an attack on the sealed-row trigger performed as the app role would be caught by
the missing `UPDATE` grant and would prove nothing about the trigger. The
sealed-row attacks are therefore made **as the owner**, which holds every
privilege — the only way to reach the trigger at all, and the mirror of the
workflow's `ALTER TABLE … DISABLE TRIGGER` step for `self_widening`.

Needs a database. If there is none the result is a loud `UNKNOWN` and a nonzero
exit — never a skip.

    python3 -m pytest tests/test_store_roles.py -q
    python3 tests/test_store_roles.py
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import (ClusterUnknown, Custody, Database,  # noqa: E402
                     installed, refused_by)

from records.atrest import seal_bytes  # noqa: E402

from store.roles import APP_HOLDS, APP_LACKS, META_SCHEMA, held_by_app  # noqa: E402

AT = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)

BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")
ENTRY = uuid.UUID("33333333-1111-1111-1111-111111111111")
SEALED = uuid.UUID("33333333-2222-2222-2222-222222222222")


#: The column the rewrite attacks below aim at, since S-3.
#:
#: It was `payload` and could not stay: migration 004 tombstoned that column and
#: constrained it to `NULL`, so an `UPDATE` naming it is refused by
#: `lane_entry_payload_is_tombstoned` — a *different* guard from the privilege
#: and the trigger these tests are about, which is the exact substitution this
#: file's docstring says must not be allowed. `payload_sealed` is the column
#: that now holds what `payload` held, so the attacks moved with the data.
REWRITABLE = "payload_sealed"


def an_envelope(lane=LBEN):
    """A real sealed payload, from a key minted for this test database only.

    Key material never leaves this function's frame and is never written
    anywhere (refusal 2; `tests/test_key_custody.py` is the tripwire). The
    ciphertext has to be real because `lane_entry_payload_sealed_is_ciphertext`
    reads its shape.
    """
    custody = Custody(str(lane), at=AT)
    return seal_bytes(b'{"body":"a note"}', lane_key=custody.key(lane), at=AT)


def seed(owner):
    """Two people, a lane, one draft entry and one sealed one."""
    got = an_envelope()
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (ANN, "1979-02-02")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                    (LBEN, BEN, "everything, as CSV, on request"))
        for entry, kind, state, sealer in ((ENTRY, "attendance", "draft", None),
                                           (SEALED, "commentary", "sealed", ANN)):
            cur.execute(
                "INSERT INTO lane_entry (entry_id, lane_id, kind, payload_sealed, "
                " payload_key_id, payload_scheme, payload_sealed_at, author_id, "
                " seal_state, sealed_by, created_at, valid_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now())",
                (entry, LBEN, kind, got.ciphertext, got.key_id, got.scheme,
                 got.sealed_at, ANN, state, sealer))
    owner.commit()


# --- the split exists at all -----------------------------------------------


def test_two_roles_exist_and_the_app_holds_exactly_two_privileges():
    """G-D's whole claim, asked of the cluster rather than of our own SQL."""
    with Database() as db:
        owner, app = installed(db)
        try:
            held = held_by_app(owner, "lane_entry")
            assert set(held) == set(APP_HOLDS), (
                f"the app role holds {held}, not {APP_HOLDS}")
            for lacked in APP_LACKS:
                assert lacked not in held, (
                    f"the app role holds {lacked} on lane_entry; "
                    "store/roles.py revokes it")
        finally:
            app.close()
            owner.close()


def test_creating_the_roles_twice_changes_nothing_and_raises_nothing():
    """The runner calls `ensure_roles` on every run. Idempotent means idempotent:
    a role step that had to be behind a flag would be a role step somebody
    eventually runs at the wrong time."""
    from store.roles import ensure_roles

    with Database() as db:
        owner, app = installed(db)
        try:
            again = ensure_roles(owner)
            assert again.created == (), (
                f"a second run created {again.created}; it must find both roles")
            assert set(held_by_app(owner, "lane_entry")) == set(APP_HOLDS)
        finally:
            app.close()
            owner.close()


# --- the forbidden acts, as the app role -----------------------------------


def test_the_app_role_cannot_update_a_sealed_row():
    """Acceptance list, item 1. The privilege speaks, and the assertion says so:
    `42501` and the table's name. The *trigger's* half of this rule is attacked
    below as the owner, because a privilege refusal happens first and would
    otherwise be mistaken for it."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            refused_by(lambda: app.execute(
                f"UPDATE lane_entry SET {REWRITABLE} = NULL "
                "WHERE entry_id = %s", (SEALED,)), "42501")
            app.rollback()
            text = refused_by(lambda: app.execute(
                f"UPDATE lane_entry SET {REWRITABLE} = NULL "
                "WHERE entry_id = %s", (SEALED,)), "lane_entry")
            assert "permission denied" in text
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_the_app_role_cannot_delete_anything():
    """Acceptance list, item 1, second clause — and refusal 3: standing ends by a
    date. `tools/discipline.py` said of its own known limit that *"the store is
    where this gets enforced properly, and there is no store."* There is now, and
    the enforcement is a privilege rather than a code review."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            for table in ("lane_entry", "edge", "lane", "person",
                          "access_grant", "crossing_envelope", "declination"):
                refused_by(lambda t=table: app.execute(f"DELETE FROM {t}"), "42501")
                app.rollback()
        finally:
            app.close()
            owner.close()


def test_the_app_role_cannot_own_a_table():
    """A role that can create a table can keep, in a table of its own,
    everything the classification registry would have refused in the schema it
    was given. `42501` again, and the schema is named in the message."""
    with Database() as db:
        owner, app = installed(db)
        try:
            text = refused_by(
                lambda: app.execute("CREATE TABLE sidecar (x text)"), "42501")
            assert "schema public" in text, text
            app.rollback()
            refused_by(lambda: app.execute(
                "CREATE TABLE public.sidecar2 AS SELECT 1"), "42501")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_the_app_role_cannot_truncate_or_drop():
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            refused_by(lambda: app.execute("TRUNCATE lane_entry"), "42501")
            app.rollback()
            refused_by(lambda: app.execute("DROP TABLE lane_entry"), "42501")
            app.rollback()
            refused_by(lambda: app.execute(
                "ALTER TABLE lane_entry ADD COLUMN sneak text"), "42501")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_the_app_role_cannot_reach_the_runners_own_ledger():
    """`store_meta` is the migration runner's, and the application has no
    business in it. Revoked explicitly rather than left to default privileges,
    which grant `USAGE` on a schema to `PUBLIC` in older clusters."""
    with Database() as db:
        owner, app = installed(db)
        try:
            refused_by(lambda: app.execute(
                f"SELECT * FROM {META_SCHEMA}.schema_migrations"), "42501")
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_the_app_role_can_still_insert_a_draft_and_select():
    """A guard that refuses everything is not a guard.

    The workflow's own control step, applied to the role split: if the app role
    could do nothing at all, every refusal above would be satisfied by an
    install that simply does not work.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            new = uuid.uuid4()
            got = an_envelope()
            app.execute(
                "INSERT INTO lane_entry (entry_id, lane_id, kind, payload_sealed,"
                " payload_key_id, payload_scheme, payload_sealed_at, author_id,"
                " created_at, valid_at) "
                "VALUES (%s,%s,'attendance',%s,%s,%s,%s,%s,now(),now())",
                (new, LBEN, got.ciphertext, got.key_id, got.scheme,
                 got.sealed_at, ANN))
            app.commit()
            got = app.execute("SELECT seal_state FROM lane_entry WHERE entry_id = %s",
                              (new,)).fetchone()
            assert got == ("draft",)
            n = app.execute("SELECT count(*) FROM lane_entry").fetchone()[0]
            assert n == 3, f"the app role reads {n} rows, expected 3"
        finally:
            app.close()
            owner.close()


# --- the sealed-row trigger, reached as the owner ---------------------------


def test_a_sealed_row_cannot_be_rewritten_even_by_the_owner():
    """*"Rewritable by nobody"* — migration 002, and the reason it exists.

    Made as the **owner**, which holds `UPDATE`, so the trigger is the only
    thing that can speak. As the app role this attempt is refused by the missing
    privilege and the trigger never runs, which would be a green test over a
    guard that had not fired.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            refused_by(lambda: owner.execute(
                f"UPDATE lane_entry SET {REWRITABLE} = NULL "
                "WHERE entry_id = %s", (SEALED,)), "insert-only history")
            owner.rollback()
            refused_by(lambda: owner.execute(
                "UPDATE lane_entry SET seal_state = 'draft' WHERE entry_id = %s",
                (SEALED,)), "insert-only history")
            owner.rollback()
            refused_by(lambda: owner.execute(
                "DELETE FROM lane_entry WHERE entry_id = %s", (SEALED,)),
                "not deletable")
        finally:
            owner.rollback()
            app.close()
            owner.close()


def test_a_sealed_row_may_still_be_ended_by_a_date():
    """Refusal 3's only spelling has to stay reachable, or the deletion becomes
    the only way to end a record — which is the outcome the refusal exists to
    prevent. The draft beside it stays fully amendable: it is the sidecar."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            owner.execute("UPDATE lane_entry SET invalid_at = now() "
                          "WHERE entry_id = %s", (SEALED,))
            owner.execute("UPDATE lane_entry SET kind = 'rehearsal' "
                          "WHERE entry_id = %s", (ENTRY,))
            owner.commit()
            ended = owner.execute(
                "SELECT invalid_at IS NOT NULL FROM lane_entry WHERE entry_id = %s",
                (SEALED,)).fetchone()[0]
            assert ended, "a sealed row could not be ended by a date"
        finally:
            owner.close()
            app.close()


if __name__ == "__main__":
    ok, why = (True, "")
    try:
        from cluster import available
        ok, why = available()
    except ClusterUnknown as exc:  # pragma: no cover
        ok, why = False, str(exc)
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    from cluster import report
    if not ok:
        raise SystemExit(report("test_store_roles", 0, len(tests), unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_roles", failures, len(tests)))
