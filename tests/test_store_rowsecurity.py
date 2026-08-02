"""The compiled half, attacked: the seal as the cluster enforces it.

`docs/PLAN-STORE.md`'s acceptance list, second item: **"A query crosses a lane
without an envelope — through RLS, with the Python predicate disabled, and the
reverse."** This file is the first of those two directions, and it is the one
where the predicate is not merely disabled but *absent from the path*: every
attack below is a string of SQL handed to `terpsi_app` over TCP, with nothing
from `records/` between the query and the answer.

**The reverse direction is `tests/test_serving.py` and `tests/test_crossing.py`
and is deliberately not repeated here.** `test_a_sealed_lane_does_not_open_for_a_sibling`,
`test_a_ward_reading_another_wards_lane_is_denied_below_the_derive_floor`,
`test_a_forged_self_edge_does_not_make_somebody_a_ward` and
`test_without_an_envelope_a_crossing_is_refused` drive the crossing through the
predicate with no store anywhere near it — which is *"the predicate with RLS
hypothetically absent"* exactly, since those suites have never had a database.
Restating them against a cluster would be a third implementation of the same
assertions with nothing reconciling it; the reconciler for the two that do exist
is `tests/test_store_differential.py`.

---

**Asserting a refusal when the guard cannot name itself.** 001's and 002's
refusals raise, and every attack on them asserts on the constraint or trigger
named in the error, because a `BEFORE ROW` trigger fires ahead of every CHECK
and an attack that only asserts *"this was refused"* can be satisfied by a guard
other than the one under test. A `SELECT` refused by row security does not
raise. It returns nothing, and *nothing* is also what an empty table returns, a
missing `GRANT`, a typo in a `WHERE` clause and a seed that never ran.

So each refusal here is asserted three ways together, and no one of them alone:

1. the app role reads **zero** rows;
2. a connection **outside** the policy reads the row, so it exists;
3. the policy is present in `pg_policies` **under the name this file expects**,
   with row security enabled and forced on the table.

And each is ablated in `.github/workflows/tests.yml`, where dropping the policy
is required to make the attack **land** — a mutation that kills no gate is a
failed mutation, not a passing one.

Needs a database. No skip — see `tests/cluster.py`.

    python3 tests/test_store_rowsecurity.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import (APP_PASSWORD, ClusterUnknown, Database,  # noqa: E402
                     available, installed, report)

from store.connecting import APP_ROLE, OWNER_ROLE  # noqa: E402
from store.session import GUC, NoPrincipal, acting, name_principal, principal_of  # noqa: E402

MIGRATION = ROOT / "migrations" / "003_row_security.sql"

#: The tables the migration seals, and the policy that seals each. Written here
#: rather than read out of the cluster, because a list derived from
#: `pg_policies` would agree with `pg_policies` by construction and assert
#: nothing. The reverse direction — no table sealed that this list omits — is
#: `test_every_public_table_is_either_sealed_or_named_as_unsealed`.
SEALED = {
    "person": "person_lane_seal",
    "lane": "lane_lane_seal",
    "lane_entry": "lane_entry_lane_seal",
    "edge": "edge_lane_seal",
    "access_grant": "access_grant_lane_seal",
    "crossing_envelope": "crossing_envelope_lane_seal",
    "self_widening": "self_widening_lane_seal",
    "declination": "declination_lane_seal",
    "disclosure_log": "disclosure_log_lane_seal",
    "consent_chain": "consent_chain_lane_seal",
    "reconciled_session": "reconciled_session_principal_seal",
}

#: Carrying no lane-scoped row, and left unsealed with the reason in the
#: migration's closing comment. A table that quietly joined this set would be a
#: table nobody decided about.
UNSEALED = {"referent", "scope_object", "field_classification"}

REACH_ROLE = "terpsi_reach"

BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
CARA = uuid.UUID("11111111-2222-2222-2222-222222222222")
ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")
LCARA = uuid.UUID("22222222-2222-2222-2222-222222222222")
GANN = uuid.UUID("dddddddd-1111-1111-1111-111111111111")
SELF_CARA = uuid.UUID("dddddddd-2222-2222-2222-222222222222")
ENTRY = uuid.UUID("33333333-1111-1111-1111-111111111111")


def seed(owner):
    """Ben's lane with one entry, Ann's guardianship, and Cara sealed into hers."""
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (CARA, "2012-09-14"),
                          (ANN, "1979-02-02")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        for lane, who in ((LBEN, BEN), (LCARA, CARA)):
            cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                        (lane, who, "everything, as CSV, on request"))
        cur.execute(
            "INSERT INTO edge VALUES (%s,'guardian_of',%s,%s,NULL,'enrolment "
            "form',now(),now() - interval '1 year',NULL)", (GANN, ANN, LBEN))
        cur.execute(
            "INSERT INTO edge VALUES (%s,'self',%s,%s,NULL,'enrolment',"
            "now(),now() - interval '1 year',NULL)", (SELF_CARA, CARA, LCARA))
        cur.execute(
            "INSERT INTO lane_entry (entry_id, lane_id, kind, author_id, "
            " created_at, valid_at) VALUES (%s,%s,'allergy',%s,now(),now())",
            (ENTRY, LBEN, ANN))
    owner.commit()


def rows_seen(conn, sql, params=()):
    n = conn.execute(sql, params).fetchone()[0]
    conn.rollback()
    return n


# --- the acceptance act: a crossing refused with no predicate in the path -----


def test_a_query_crossing_a_lane_is_refused_by_the_policy_with_no_predicate_anywhere():
    """`PLAN-STORE.md`'s acceptance list, second item, first direction.

    Cara is a ward — she holds a live, genuine `self` edge into her own lane —
    and she asks the database, in raw SQL as `terpsi_app`, for a row in Ben's.
    `records/serving.py` is not imported on this path and could be deleted
    without changing the answer.

    The three-way attribution the module docstring describes is performed here
    in full, so a reader can see what a refusal costs to assert when the guard
    cannot speak its own name.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            # (1) the app role, acting as Cara, reads nothing.
            crossing = rows_seen_as(app, CARA,
                                    "SELECT count(*) FROM lane_entry WHERE lane_id = %s",
                                    (LBEN,))
            assert crossing == 0, (
                f"a ward read {crossing} row(s) of another ward's lane with no "
                "envelope (W-3: between wards, default deny)")

            # (2) the row is there. A zero over an empty table proves nothing.
            assert rows_seen(owner,
                             "SELECT count(*) FROM lane_entry WHERE lane_id = %s",
                             (LBEN,)) == 1

            # (3) the policy that did it exists, by name, on a table with row
            #     security enabled AND forced.
            policy, enabled, forced = owner.execute(
                "SELECT p.policyname, c.relrowsecurity, c.relforcerowsecurity "
                "  FROM pg_policies p "
                "  JOIN pg_class c ON c.relname = p.tablename "
                " WHERE p.tablename = 'lane_entry' AND p.policyname = %s",
                (SEALED["lane_entry"],)).fetchone()
            assert policy == SEALED["lane_entry"]
            assert enabled and forced, (
                f"{policy} exists on a table with rowsecurity={enabled} "
                f"force={forced}; a policy on a table that does not enforce it "
                "is a ledger")

            # And the control: the same statement, same connection, same
            # transaction shape, for the guardian who does hold standing.
            assert rows_seen_as(app, ANN,
                                "SELECT count(*) FROM lane_entry WHERE lane_id = %s",
                                (LBEN,)) == 1, (
                "the policy refuses the entitled reader too, so the refusal "
                "above is a broken store rather than a seal")
        finally:
            app.close()
            owner.close()


def rows_seen_as(app, principal, sql, params=()):
    """One count, under one named principal, in one transaction. Raw SQL only."""
    app.rollback()
    name_principal(app, principal)
    n = app.execute(sql, params).fetchone()[0]
    app.rollback()
    return n


# --- rule 13: an anonymous session is not an entitled one --------------------


def test_a_session_that_names_no_principal_reads_no_row_of_any_sealed_table():
    """Every sealed table, not the one the crossing test happens to use.

    An unset GUC is the state a connection is in by default — a pool hands one
    out, an operator opens `psql` — so the fail-closed direction has to hold
    everywhere rather than where it was remembered.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            app.rollback()
            assert principal_of(app) is None
            loud = []
            for table in sorted(SEALED):
                n = app.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                if n:
                    loud.append(f"{table}: {n} row(s)")
            app.rollback()
            assert not loud, (
                "an unnamed session reached rows in " + ", ".join(loud)
                + " — an anonymous session is not an entitled one (rule 13)")
            # The control: the same tables under a principal with standing are
            # not all empty, or the assertion above is satisfied by an empty
            # database.
            reached = rows_seen_as(app, ANN, "SELECT count(*) FROM lane_entry")
            assert reached == 1, (
                "no sealed table holds a reachable row, so the sweep above "
                "asserted nothing")
        finally:
            app.close()
            owner.close()


def test_a_blank_or_malformed_principal_reads_nothing_rather_than_everything():
    """The GUC is text and the policies cast it. Three ways to hand it something
    that is not a person, all of which must fail closed at the cluster — and be
    refused loudly one layer up, which is the assertion after them."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            for bad in ("", "   ", "*", "all", "not-a-uuid", "'; DROP TABLE lane; --"):
                app.rollback()
                app.execute("SELECT set_config(%s, %s, true)", (GUC, bad))
                n = app.execute("SELECT count(*) FROM lane_entry").fetchone()[0]
                assert n == 0, f"{bad!r} in the GUC reached {n} row(s)"
                assert principal_of(app) is None
            app.rollback()
            # The table is still there, which is the injection half of the sweep.
            assert rows_seen(owner, "SELECT count(*) FROM lane") == 2
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_the_seam_refuses_an_unnamed_principal_loudly_instead_of_sending_a_blank():
    """`store/session.py` is where a missing principal is a message rather than
    an empty result. The policies already fail closed; this is the difference
    between a caller who learns what went wrong and one who reads a lane they
    are entitled to as empty."""
    with Database() as db:
        owner, app = installed(db)
        try:
            for bad in (None, "", "   ", "the drumline", "*"):
                try:
                    name_principal(app, bad)
                except NoPrincipal as exc:
                    assert str(exc), "a refusal with no reason in it"
                else:
                    raise AssertionError(f"{bad!r} was accepted as a principal")
            # Not broken shut.
            assert name_principal(app, ANN) == str(ANN)
            app.rollback()
        finally:
            app.close()
            owner.close()


def test_the_principal_does_not_outlive_its_transaction():
    """`SET LOCAL`, and the reason it is the only shape offered.

    A connection that carried a principal between transactions is the pooled-
    connection defect: request *n+1* reads under request *n*'s identity. The
    reset here is the database's — a commit ends it — and not a `finally` this
    module has to be trusted to run.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            with acting(app, ANN):
                assert principal_of(app) == str(ANN)
                assert app.execute(
                    "SELECT count(*) FROM lane_entry").fetchone()[0] == 1
            app.commit()
            assert principal_of(app) is None, (
                "the principal survived the transaction that established it")
            assert app.execute(
                "SELECT count(*) FROM lane_entry").fetchone()[0] == 0
            app.rollback()
        finally:
            app.close()
            owner.close()


def test_the_compiled_envelope_is_directional():
    """W-3's direction, asserted where it *can* be attributed.

    **Why it is here and not in the differential.** That suite compares *reach*,
    and reversing an envelope only changes a reach for a principal who is a ward
    of one lane AND holds an entitlement edge into the other — because a crossing
    does not widen the entitlement edge (`tests/test_crossing.py::
    test_a_crossing_does_not_widen_anything_else`). A ward never holds an edge
    into a sibling's lane, so in this domain the two failure paths coincide and a
    reach comparison cannot tell a symmetric envelope from a missing one. Making
    it `(from, to) IN ((a,b),(b,a))` survives the whole differential, which was
    measured rather than assumed.

    So direction is asserted against the compiled function itself, one level
    below reach, where a symmetric spelling has nowhere to hide. The Python side
    is `tests/test_crossing.py::test_an_envelope_is_directional`, and the two
    together are what the differential cannot cover.

    One signature opening two seals is the cheap violation W-3 exists to make
    unwritable, and it is the one a hurried port writes.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            with owner.cursor() as cur:
                cur.execute(
                    "INSERT INTO crossing_envelope VALUES (%s,%s,%s,'shared ride "
                    "home after the away game',%s,%s,now(),now() + interval "
                    "'30 day',now(),now(),NULL)",
                    (uuid.UUID("cccc9999-0000-0000-0000-000000000000"),
                     LCARA, LBEN, ANN, GANN))
            owner.commit()
            forward = owner.execute("SELECT envelope_permits(%s, %s)",
                                    (LCARA, LBEN)).fetchone()[0]
            back = owner.execute("SELECT envelope_permits(%s, %s)",
                                 (LBEN, LCARA)).fetchone()[0]
            owner.rollback()
            assert forward is True, (
                "the envelope does not permit the crossing it names, so the "
                "reverse assertion below is satisfied by a broken function")
            assert back is False, (
                "an envelope permitting Cara's lane to read Ben's also permits "
                "Ben's to read Cara's — one signature opening two seals (W-3)")
        finally:
            owner.rollback()
            app.close()
            owner.close()


# --- the SECURITY DEFINER search_path pin ------------------------------------


#: A principal with no edge into any lane — the attacker for the shadow test.
#: Not a `person` row and does not need to be: the GUC is a bare uuid the
#: policies cast and compare, and "someone the store has never entitled" is
#: exactly who a forged edge is for.
OUTSIDER = uuid.UUID("99999999-9999-9999-9999-999999999999")


def test_a_pg_temp_shadow_does_not_unseal_a_lane():
    """The reach helpers are SECURITY DEFINER, so they run the definer's rights
    against the *caller's* `search_path` unless they pin their own. They read
    `edge`, `lane` and `crossing_envelope` unqualified, and `pg_temp` is searched
    first by default — so a caller who can create a temporary table (the app role
    holds the default `TEMPORARY` privilege) can plant `pg_temp.edge` with a row
    granting themselves an edge into a lane, and RLS turns that shadow into a
    read.

    The attacker is `OUTSIDER`: no edge into any lane, so the seal that should
    stop them is `holds_live_edge` — clause (a), the entitlement check — and a
    forged edge is the whole of the attack. (A ward is the wrong attacker here:
    `ward_lane` finds their *real* self edge and W-3(b) stops them before
    `holds_live_edge` is reached, so a ward would pass even with the entitlement
    helper de-qualified, and the test would prove nothing.)

    **The migration schema-qualifies every table reference in the five reach
    functions (`public.edge`, …) and pins each to `search_path = pg_catalog,
    pg_temp`, and that qualification is what this asserts.** Two attacks, and the
    second is the one that shows why the reference and not the grant map is what
    should hold:

    * **(A) the pg_temp shadow** — available to anyone who can name a principal,
      needs no grant. `OUTSIDER` plants `pg_temp.edge` claiming a live edge into
      Ben's lane and fronts it in `search_path`. De-qualified, `holds_live_edge`
      resolves `edge` to the temp table; qualified, `public.edge` reads the real
      one and finds nothing.

    * **(B) a definer-readable shadow, i.e. the grant map one migration wider.**
      Without qualification, (A) fails *closed but by accident*: the definer role reads
      only the three real tables, so a `pg_temp` shadow it cannot read raises
      rather than leaking. The safety is a property of the grant map, not of the
      seal — a later `GRANT USAGE` on a schema the app can write into removes it
      silently, with no guard going red. Part B simulates exactly that (a
      `helper` schema the app writes and the reach role reads) and asserts the
      qualification holds anyway. It is the case that *did* leak before the fix,
      confirmed against a live cluster.

    Attributed three ways like every refusal in this file: (1) the read returns
    zero rows, (2) an entitled principal (Ann, Ben's guardian) still reads the
    same lane, so a zero is the seal and not an empty table, and (3) the shadow
    really was in front of the real table. Ablated in `tests/ablate_store.py` by
    de-qualifying `public.edge` in `holds_live_edge`, which is required to make
    the read land.
    """
    forged_temp = (
        "INSERT INTO edge VALUES (gen_random_uuid(), 'staff_of', %s, %s, NULL, "
        "'forged', now() - interval '1 day', now() - interval '1 day', NULL)")
    shadow_cols = (
        "(edge_id uuid, kind text, holder_id uuid, target_lane_id uuid, "
        "target_scope_id uuid, source text, created_at timestamptz, "
        "valid_at timestamptz, invalid_at timestamptz)")
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            # Attribution (2): the lane is real and readable by someone entitled,
            # so a zero below is the seal working rather than an empty table.
            entitled = rows_seen_as(app, ANN,
                                    "SELECT count(*) FROM lane_entry WHERE lane_id = %s",
                                    (LBEN,))
            assert entitled == 1, (
                f"Ben's guardian reads {entitled} of his lane; the fixture is "
                "wrong and the refusals below would prove nothing")

            # (A) pg_temp shadow. One transaction: the LOCAL search_path and the
            # LOCAL principal GUC both die with the rollback that follows.
            app.rollback()
            with app.cursor() as cur:
                cur.execute("CREATE TEMP TABLE edge " + shadow_cols)
                cur.execute(forged_temp, (OUTSIDER, LBEN))
                cur.execute("SELECT set_config('search_path', 'pg_temp, public', true)")
                cur.execute("SELECT set_config(%s, %s, true)", (GUC, str(OUTSIDER)))
                # Attribution (3): the shadow really is in front of the real table.
                assert cur.execute(
                    "SELECT to_regclass('edge') = to_regclass('pg_temp.edge')"
                ).fetchone()[0] is True, (
                    "the attack did not front a shadow, so an empty read below "
                    "proves nothing — fix the attack, not the code")
                # The read is schema-qualified so only `edge` is shadowed, not the
                # table under attack. Unpinned, `holds_live_edge` resolves `edge`
                # to the temp table and — the definer cannot read it — raises
                # `permission denied`: the pin missing, the seal on the grant map.
                # Named so the ablation reads as this guard, not a bare DB error.
                try:
                    seen = cur.execute(
                        "SELECT kind FROM public.lane_entry WHERE lane_id = %s",
                        (LBEN,)).fetchall()
                except Exception as exc:  # noqa: BLE001
                    first = str(exc).splitlines()[0]
                    if "edge" in first:
                        raise AssertionError(
                            "the reach helper resolved `edge` to the caller's "
                            f"pg_temp shadow ({first}); SET search_path is not "
                            "pinned on the definer functions") from None
                    raise
            app.rollback()
            assert seen == [], (
                f"a pg_temp.edge shadow unsealed Ben's lane: read {seen} "
                "(the reach helper resolved edge to the caller's temp table)")

            # (B) the grant map one migration wider: a schema the app writes and
            # the reach role reads. This is the shape that leaked before the pin.
            with owner.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS helper")
                cur.execute("GRANT USAGE, CREATE ON SCHEMA helper TO " + APP_ROLE)
                cur.execute("GRANT USAGE ON SCHEMA helper TO " + REACH_ROLE)
                cur.execute(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE " + APP_ROLE +
                    " IN SCHEMA helper GRANT SELECT ON TABLES TO " + REACH_ROLE)
            owner.commit()
            app.rollback()
            with app.cursor() as cur:
                cur.execute("CREATE TABLE helper.edge " + shadow_cols)
                cur.execute(
                    "INSERT INTO helper.edge VALUES (gen_random_uuid(), "
                    "'staff_of', %s, %s, NULL, 'forged', now() - interval "
                    "'1 day', now() - interval '1 day', NULL)", (OUTSIDER, LBEN))
                cur.execute("SELECT set_config('search_path', 'helper, public', true)")
                cur.execute("SELECT set_config(%s, %s, true)", (GUC, str(OUTSIDER)))
                readable = cur.execute(
                    "SELECT has_table_privilege(%s, 'helper.edge', 'SELECT')",
                    (REACH_ROLE,)).fetchone()[0]
                leaked = cur.execute(
                    "SELECT kind FROM public.lane_entry WHERE lane_id = %s",
                    (LBEN,)).fetchall()
            app.rollback()
            assert readable is True, (
                "the definer role cannot read the shadow, so part B is testing "
                "the grant-map accident rather than the pin — the point of B is "
                "a shadow the definer CAN read")
            assert leaked == [], (
                f"a definer-readable shadow unsealed Ben's lane: read {leaked}. "
                "The pin is not holding; the seal rests on the grant map again")
        finally:
            app.rollback()
            owner.rollback()
            app.close()
            owner.close()


# --- FORCE, and the owner bypass ---------------------------------------------


def test_the_declared_owner_owns_the_tables_and_is_not_exempt_from_their_policies():
    """FORCE ROW LEVEL SECURITY, attempted rather than read off the catalogue.

    **Both halves, because either alone is worthless.** `relforcerowsecurity` on
    a table owned by a superuser is a true fact and evidence of nothing —
    superusers bypass row security whatever the flag says — so the migration
    moves ownership to `terpsi_migrator`, and this asserts the ownership *and*
    performs the bypass as that role.

    `SET ROLE` rather than a second login: what is under test is the *table
    owner's* exemption, which is a property of ownership and not of
    authentication, and after `SET ROLE` to a NOSUPERUSER role the session is no
    longer bypassing anything.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            wrong_owner = [
                (t, o) for t, o in owner.execute(
                    "SELECT tablename, tableowner FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY 1").fetchall()
                if o != OWNER_ROLE]
            assert not wrong_owner, (
                f"{OWNER_ROLE} does not own {wrong_owner}; FORCE ROW LEVEL "
                "SECURITY names the owner, and an owner who is a superuser "
                "bypasses row security whatever the flag says")

            unforced = [t for t, force in owner.execute(
                "SELECT relname, relforcerowsecurity FROM pg_class "
                "WHERE relname = ANY(%s)", (sorted(SEALED),)).fetchall()
                if not force]
            assert not unforced, f"row security is not FORCEd on {unforced}"

            owner.rollback()
            owner.execute(f"SET ROLE {OWNER_ROLE}")
            n = owner.execute("SELECT count(*) FROM lane_entry").fetchone()[0]
            assert n == 0, (
                f"the table owner read {n} row(s) of a sealed table without "
                "naming a principal; FORCE ROW LEVEL SECURITY is not in effect")
            owner.execute("RESET ROLE")
            owner.rollback()
            # The control: the row the owner could not see is there.
            assert rows_seen(owner, "SELECT count(*) FROM lane_entry") == 1
        finally:
            owner.rollback()
            app.close()
            owner.close()


def test_the_app_role_cannot_read_the_policies_own_bookkeeping_role_out_from_under_them():
    """The escape hatch, bounded. `terpsi_reach` holds a `USING (true)` policy on
    the three reference tables, which is what stops the seal's own lookups from
    recursing. It must not be reachable by the application: it cannot log in,
    and the app role is not a member of it."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            canlogin, = owner.execute(
                "SELECT rolcanlogin FROM pg_roles WHERE rolname = %s",
                (REACH_ROLE,)).fetchone()
            assert not canlogin, (
                f"{REACH_ROLE} can log in; the definer of five SECURITY DEFINER "
                "functions is not an identity anybody should hold")
            member = owner.execute(
                "SELECT pg_has_role(%s, %s, 'USAGE')", (APP_ROLE, REACH_ROLE)
            ).fetchone()[0]
            assert not member, (
                f"{APP_ROLE} is a member of {REACH_ROLE} and can SET ROLE to a "
                "window over every lane")
            app.rollback()
            try:
                app.execute(f"SET ROLE {REACH_ROLE}")
            except Exception:
                app.rollback()
            else:
                raise AssertionError(f"the app role set role to {REACH_ROLE}")
        finally:
            app.rollback()
            app.close()
            owner.close()


# --- the declaration and the cluster agree -----------------------------------


def test_every_policy_this_file_names_is_in_the_cluster_and_in_the_migration():
    """Both directions. A policy renamed in the migration and not here would
    leave the assertions above testing a policy that no longer exists; a policy
    named here and never created would make them vacuous."""
    text = MIGRATION.read_text(encoding="utf-8")
    with Database() as db:
        owner, app = installed(db)
        try:
            live = {(t, p) for t, p in owner.execute(
                "SELECT tablename, policyname FROM pg_policies "
                "WHERE schemaname = 'public'").fetchall()}
            for table, policy in SEALED.items():
                assert (table, policy) in live, (
                    f"{policy} is not a policy on {table} in this cluster")
                assert f"CREATE POLICY {policy} ON {table}" in text, (
                    f"{policy} is in the cluster and not in {MIGRATION.name}")
            # Every seal has a permissive INSERT policy beside it, and the name
            # says what it is: this migration compiles the READ predicate and
            # the write path is held by privilege, not by row security.
            for table in SEALED:
                assert (table, f"{table}_insert_unsealed") in live, (
                    f"{table} has no INSERT policy, so the app role's INSERT "
                    "grant is silently dead")
        finally:
            app.close()
            owner.close()


def test_every_public_table_is_either_sealed_or_named_as_unsealed():
    """The reverse of `SEALED`: a table added later without a decision fails
    here rather than arriving unprotected and unnoticed."""
    with Database() as db:
        owner, app = installed(db)
        try:
            live = dict(owner.execute(
                "SELECT c.relname, c.relrowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relkind = 'r'").fetchall())
            assert set(live) == set(SEALED) | UNSEALED, (
                "the public schema's tables are not the ones this file accounts "
                f"for: {set(live) ^ (set(SEALED) | UNSEALED)}")
            for table, enabled in sorted(live.items()):
                want = table in SEALED
                assert enabled == want, (
                    f"{table} has row security {'on' if enabled else 'off'} and "
                    f"this file expects it {'on' if want else 'off'}")
        finally:
            app.close()
            owner.close()


def test_the_roles_this_migration_creates_are_the_ones_store_roles_names():
    """The middle for a pair of spellings (rule 12).

    `store/roles.py` creates two roles in Python; this migration creates the
    same two in SQL, because the CI schema job applies migrations with `psql`
    and never runs the Python. Two spellings of one name is a pair, and a
    rename on one side would leave the other creating a role nothing uses while
    the policies referenced a role nothing creates.
    """
    text = MIGRATION.read_text(encoding="utf-8")
    for role in (OWNER_ROLE, APP_ROLE):
        assert f"rolname = '{role}'" in text, (
            f"{role} is store/roles.py's name and {MIGRATION.name} does not "
            "create it; the psql path would apply this migration against a "
            "cluster with no such role")
        assert f"CREATE ROLE {role} " in text


def test_the_guc_this_migration_reads_is_the_one_store_session_sets():
    """The other pair of literals: a GUC name in Python and the same string in
    SQL. Renaming one leaves a store where every read is refused and nothing
    says why."""
    text = MIGRATION.read_text(encoding="utf-8")
    assert f"current_setting('{GUC}'" in text, (
        f"store/session.py sets {GUC!r} and the migration reads something else")


def test_the_migration_widens_no_privilege_of_the_app_role():
    """S-2's hard constraint, asserted against the file rather than remembered.

    The only thing this migration may grant `terpsi_app` is `EXECUTE` on the
    five functions its own policies call. A `GRANT UPDATE`, a `GRANT DELETE` or
    a table-level grant here would hand back what `store/roles.py` revoked, and
    row security would be sealing a role that no longer needs to cross a lane to
    do damage.
    """
    text = MIGRATION.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("GRANT") or APP_ROLE not in stripped:
            continue
        assert stripped.startswith("GRANT EXECUTE ON FUNCTION") or \
            stripped.startswith("GRANT USAGE ON SCHEMA"), (
                f"this migration grants the app role more than EXECUTE: {stripped}")
    with Database() as db:
        owner, app = installed(db)
        try:
            # And from the cluster, which is the claim that matters. The
            # enumeration of what the app holds and lacks is
            # tests/test_store_roles.py's; this only asserts the two forbidden
            # ones did not come back.
            back = owner.execute(
                "SELECT DISTINCT privilege_type FROM information_schema.table_privileges "
                "WHERE grantee = %s AND privilege_type IN ('UPDATE','DELETE','TRUNCATE')",
                (APP_ROLE,)).fetchall()
            assert not back, f"the app role holds {back} after migration 003"
        finally:
            app.close()
            owner.close()


def test_the_reach_helpers_are_not_an_oracle_for_anyone_with_a_connection():
    """A SECURITY DEFINER boolean is a question anybody can ask.

    `reaches_lane(X, Y)` answers *"is X entitled to Y's lane"* — a guardianship,
    read out of a boolean, without touching a row. EXECUTE is revoked from
    PUBLIC so only the roles whose statements the policies run inside may call
    it, and the app role's own call is still bounded by what it may ask about.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            granted = owner.execute(
                "SELECT count(*) FROM information_schema.routine_privileges "
                "WHERE routine_name = 'reaches_lane' AND grantee = 'PUBLIC'"
            ).fetchone()[0]
            assert granted == 0, (
                "reaches_lane is executable by PUBLIC; any role with a "
                "connection can read a guardianship out of a boolean")
            # Not broken shut: the policies still evaluate, which is the whole
            # of the rest of this file.
            assert rows_seen_as(app, ANN, "SELECT count(*) FROM lane_entry") == 1
        finally:
            app.close()
            owner.close()


def test_a_reader_that_cannot_evaluate_the_seal_gets_an_error_not_an_empty_result():
    """Rule 13, arriving from an unexpected direction.

    Revoking `EXECUTE` on the reach helpers from PUBLIC has a consequence
    nobody designed and everybody should want: a role holding `SELECT` on a
    sealed table but not `EXECUTE` on the function its policy calls gets
    `permission denied for function reaches_lane` rather than zero rows. It
    could not evaluate the seal, so it has established nothing — and *"I could
    not tell"* and *"there is nothing here"* are the two answers this whole tree
    exists to keep apart.

    Found by running the workflow's S-1 ablation step against migration 003: an
    ad-hoc role's `DELETE` stopped quietly matching nothing and started saying
    why, which is how the step's own assertion came to count rows rather than
    trust an exit code.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            owner.execute(
                "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE "
                "rolname = 'terpsi_onlooker') THEN CREATE ROLE terpsi_onlooker "
                "NOLOGIN; END IF; END $$;")
            owner.execute("GRANT USAGE ON SCHEMA public TO terpsi_onlooker")
            owner.execute("GRANT SELECT ON lane_entry TO terpsi_onlooker")
            owner.commit()
            owner.execute("SET ROLE terpsi_onlooker")
            try:
                owner.execute("SELECT count(*) FROM lane_entry").fetchone()
            except Exception as exc:  # noqa: BLE001
                assert "reaches_lane" in str(exc), (
                    f"refused, and not by the guard under test: {exc}")
            else:
                raise AssertionError(
                    "a reader with no EXECUTE on the seal's own function read a "
                    "count; an established zero it could not have established")
        finally:
            owner.rollback()
            owner.execute("RESET ROLE")
            owner.rollback()
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
        raise SystemExit(report("test_store_rowsecurity", 0, len(tests),
                                unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_rowsecurity", failures, len(tests)))
