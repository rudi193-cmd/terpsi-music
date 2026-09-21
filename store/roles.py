"""Gate G-D: two roles, before the first table is populated.

*"A store born single-role never sheds the habit."* The split is not a hardening
step to be applied later — later means a migration across every grant in a live
cluster, performed by whoever is on call, against an application that has spent
a season assuming it may `UPDATE`.

**The division.**

* `terpsi_migrator` **owns** the tables. It runs DDL and nothing else runs DDL.
* `terpsi_app` holds `SELECT` and `INSERT`. It holds **no** `UPDATE`, **no**
  `DELETE`, **no** `TRUNCATE`, **no** `REFERENCES`, and **no** `CREATE` on the
  schema — so it cannot rewrite history, cannot end a record by removing it
  (refusal 3), and cannot create a table of its own to keep the things the
  classification registry would have refused.

`migrations/001_lanes.sql`'s own comment asks for exactly this and names it as
somebody else's job: *"Revoking UPDATE and DELETE from the application role
belongs in the install (§11) and is the other half."* This is the other half.
The trigger in that file is proof against an ORM cascade and a migration written
in a hurry; the privilege is proof against the application.

**Idempotent, because the runner calls it on every run.** `CREATE ROLE` has no
`IF NOT EXISTS`, so each role is created inside a `DO` block that checks
`pg_roles` first. Re-running changes nothing and raises nothing, which is what
lets the runner call it unconditionally rather than behind a flag somebody has
to remember to set.

**The revokes are written even where the grants were never issued.** A `REVOKE`
of a privilege nobody granted is a no-op, and writing it anyway is the
difference between *"we did not grant UPDATE"* and *"UPDATE is revoked"* — the
first is a claim about history and the second is a claim about the cluster. Only
the second survives somebody running `GRANT ALL` on a Friday.

**What this does not do.** It sets no password unless one is supplied: a default
password in a source tree is a credential in a source tree. `ensure_roles` with
`app_password=None` leaves authentication to the cluster's `pg_hba.conf`, which
is a deployment act recorded where deployment is recorded.

Stdlib only — the SQL is text and the caller supplies the connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .connecting import APP_ROLE, OWNER_ROLE

#: The bookkeeping schema. `store_meta` rather than `public` on purpose: the
#: runner's ledger is not domain data, and `.github/workflows/tests.yml` asserts
#: that every column in `public` carries a `field_classification` row. Putting
#: the runner's own table there would either break that check or require
#: classifying a checksum as if it were a fact about a student. The separation
#: is the honest answer and `tests/test_store_migrate.py` asserts that no domain
#: table ever appears in this schema.
META_SCHEMA = "store_meta"


@dataclass(frozen=True)
class RoleState:
    """What the cluster looks like after `ensure_roles`. Reported, not assumed.

    `created` earns that second sentence: it is `after - before`, both halves
    read from `pg_roles` around the DDL, so it reports what this call changed
    rather than what this call intended.

    **Retired 2026-08-02: `app_privileges`.** Superseded by `held_by_app` below,
    which is now the only answer this module gives to *what may the app role
    do*.

    It was a fourth field filled with the module constant `APP_HOLDS`, and it
    was not merely assumed — it was false at the point it was built.
    `store/migrate.py`'s `run()` orders `ensure_roles` → `apply_all` →
    `apply_grants`, so at the moment the field was constructed there was no
    table to hold a privilege on and no grant had been issued: the app role held
    nothing and the field said `("SELECT", "INSERT")`. The sentence *reported,
    not assumed* sat one line above it.

    **Its contents map forward to `held_by_app(conn, table)`, and the mapping is
    not an equivalence.** The retired field answered *what we mean to grant*,
    blind to cluster and to table; `held_by_app` answers *what this cluster has
    granted on this table*. A caller that genuinely wants the intention wants
    `APP_HOLDS` and should name it — `tests/test_store_roles.py` reads both and
    compares them, which is exactly the comparison a field that answered with
    one while claiming to be the other made impossible.

    **No stub is left, and that is the point rather than an oversight.** Nothing
    in the tree read the field, so there is nothing to forward, and a deprecated
    attribute would only be a second spelling for `held_by_app` to drift from
    (rule 12). Removing the field removes the *ability* to report a privilege
    nobody read — `docs/CROSSINGS.md` crossing one's prescription, make the
    violation inexpressible rather than forbid it — and that survives a careless
    edit in a way a comment above the field does not.

    **What this does not carry.** No privilege list, no grant, and no claim
    about any table. There is no honest privilege answer at the moment this
    value is built, and rule 13 says an absence surfaces as `unknown` rather
    than as a result; the honest shape is to decline the question here and make
    the caller ask the cluster.
    """

    owner: str
    app: str
    created: Tuple[str, ...]      # roles that did not exist before this call


def _create_role(role: str, *, login: bool) -> str:
    """`CREATE ROLE` guarded by `pg_roles`, because there is no `IF NOT EXISTS`."""
    return f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                CREATE ROLE {role}{' LOGIN' if login else ''} NOSUPERUSER
                    NOCREATEDB NOCREATEROLE NOINHERIT;
            END IF;
        END
        $$;
    """


#: Every statement, in order. Exposed as data rather than buried in a function
#: body so `tests/test_store_roles.py` can assert on the set — a privilege list
#: nobody can enumerate is a privilege list nobody reviews.
def statements(app_password: Optional[str] = None) -> Tuple[str, ...]:
    """The idempotent role DDL, in application order.

    `app_password` is interpolated rather than parameterised because `ALTER
    ROLE` takes no parameters in PostgreSQL. It is quoted with a doubled
    apostrophe and rejected outright if it carries one, which is the narrow safe
    case; the alternative is a password nobody can type.
    """
    out = [
        _create_role(OWNER_ROLE, login=True),
        _create_role(APP_ROLE, login=True),
        f"CREATE SCHEMA IF NOT EXISTS {META_SCHEMA} AUTHORIZATION {OWNER_ROLE};",
        # The owner owns the schema it writes into. Without this the tables are
        # owned by whoever bootstrapped the cluster, and "the migrator owns the
        # DDL" is a sentence rather than a fact.
        f"GRANT ALL ON SCHEMA public TO {OWNER_ROLE};",
        f"GRANT USAGE ON SCHEMA public TO {APP_ROLE};",
        # The app may not create a table. A role that can create a table can
        # keep, in a table of its own, everything the classification registry
        # would have refused in the schema it was given.
        f"REVOKE CREATE ON SCHEMA public FROM {APP_ROLE};",
        f"REVOKE CREATE ON SCHEMA public FROM PUBLIC;",
        f"REVOKE ALL ON SCHEMA {META_SCHEMA} FROM {APP_ROLE}, PUBLIC;",
    ]
    if app_password is not None:
        if "'" in app_password:
            raise ValueError(
                "the app role's password carries an apostrophe; this function "
                "quotes it into DDL and will not guess at an escaping")
        out.append(f"ALTER ROLE {APP_ROLE} PASSWORD '{app_password}';")
    return tuple(out)


#: Applied after the migrations, because a `GRANT ON ALL TABLES` reaches the
#: tables that exist when it runs. The `ALTER DEFAULT PRIVILEGES` lines are what
#: cover the ones that do not exist yet — without them a table added by
#: migration 003 is invisible to the app role until somebody re-runs a grant,
#: and "the store went read-only after a deploy" is the symptom.
def grants() -> Tuple[str, ...]:
    """What the app role may do, and — written explicitly — what it may not."""
    return (
        f"GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO {APP_ROLE};",
        # bigserial on the three append-only logs needs the sequence.
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE};",
        # Written although nothing granted them. See the module docstring: a
        # revoke that was never needed is the difference between a claim about
        # history and a claim about the cluster.
        f"REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER "
        f"ON ALL TABLES IN SCHEMA public FROM {APP_ROLE};",
        f"ALTER DEFAULT PRIVILEGES FOR ROLE {OWNER_ROLE} IN SCHEMA public "
        f"GRANT SELECT, INSERT ON TABLES TO {APP_ROLE};",
        f"ALTER DEFAULT PRIVILEGES FOR ROLE {OWNER_ROLE} IN SCHEMA public "
        f"GRANT USAGE, SELECT ON SEQUENCES TO {APP_ROLE};",
    )


#: The privileges the app role is asserted to hold, and the ones it is asserted
#: to lack. `tests/test_store_roles.py` reads this rather than a literal list of
#: its own, so the assertion and the grant cannot drift (rule 12).
APP_HOLDS: Tuple[str, ...] = ("SELECT", "INSERT")
APP_LACKS: Tuple[str, ...] = ("UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


def ensure_roles(conn, *, app_password: Optional[str] = None) -> RoleState:
    """Create both roles and the meta schema, idempotently. Returns what exists.

    The connection must be one that may create roles — the bootstrap identity,
    used once at install and by the runner. It is deliberately **not**
    `owner_dsn()`'s role: the migrator owns tables, not roles.

    **It reports no privilege, deliberately.** This runs before `apply_all` and
    before `apply_grants` (see `store/migrate.py`'s `run()`), so there is not
    yet a table to hold a privilege on; anything said here about what the app
    role may do would be a statement about a later step. `held_by_app` is the
    question's home, and it asks the cluster.
    """
    before = _existing(conn)
    with conn.cursor() as cur:
        for sql in statements(app_password):
            cur.execute(sql)
    conn.commit()
    after = _existing(conn)
    return RoleState(OWNER_ROLE, APP_ROLE, tuple(sorted(after - before)))


def apply_grants(conn) -> Tuple[str, ...]:
    """Grant the app role its two privileges and revoke the five it must lack."""
    with conn.cursor() as cur:
        for sql in grants():
            cur.execute(sql)
    conn.commit()
    return grants()


def _existing(conn) -> frozenset:
    with conn.cursor() as cur:
        cur.execute("SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)",
                    ([OWNER_ROLE, APP_ROLE],))
        return frozenset(r[0] for r in cur.fetchall())


def held_by_app(conn, table: str) -> Tuple[str, ...]:
    """Which privileges the app role actually holds on a table, from the cluster.

    Asked of `information_schema` rather than inferred from the grants above,
    because the question a test needs answered is *what is true in this
    cluster*, and re-reading our own SQL back would answer *what we intended*.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT privilege_type FROM information_schema.table_privileges "
            "WHERE grantee = %s AND table_name = %s ORDER BY 1",
            (APP_ROLE, table))
        return tuple(r[0] for r in cur.fetchall())
