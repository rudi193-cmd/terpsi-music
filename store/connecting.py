"""The one module that opens a connection, and the two roles it opens it as.

**Every `connect()` in this repository is on one line of one file**, and that is
a property worth paying for. `tools/sockets.py` reads a `connect()` call as an
outbound endpoint whatever library carries it, so the manifest's `outbound`
declaration names this module by path; a connection opened anywhere else fails
`tools/manifest.py` in CI, by name, without anybody remembering to look. §6's
inner ring forbids outbound and `records/` is that ring — the store is the
declared exception, and one file is the smallest exception that works.

**Two DSNs, never one** (gate G-D). The migration runner connects as an owner
role that may create tables; the application connects as a role that may
`INSERT` and `SELECT` and may do nothing else. They are separate environment
variables because a single DSN with a comment saying *"use the app role in
production"* is a declaration with no enforcement, and this repository has a
documented history of those. `owner_dsn()` and `app_dsn()` refuse to return the
same string.

**A missing DSN is unknown, never a default.** There is no `localhost`
fallback: a store that quietly connects to whatever is running is how test data
lands in a cluster holding minors' records. `NoDSN` is raised with the variable
named, and the rule-13 sweep asserts that reading a DSN that is not there is not
an empty answer.

Stdlib plus the driver. The driver is admitted here by `tools/drivers.py`'s
`ALLOWED`, which is `store/` and nothing else.
"""

from __future__ import annotations

import os
from typing import Optional

import psycopg

#: The role that owns the tables and runs DDL. Nothing the application does at
#: run time uses it.
OWNER_ROLE = "terpsi_migrator"

#: The role the application connects as. `INSERT` and `SELECT`; no `UPDATE`, no
#: `DELETE`, no `TRUNCATE`, no `CREATE`. `store/roles.py` is where that is
#: granted and revoked, and `tests/test_store_roles.py` attacks it.
APP_ROLE = "terpsi_app"

#: Read at call time rather than at import, so a test can set them.
OWNER_DSN_VAR = "TERPSI_STORE_OWNER_DSN"
APP_DSN_VAR = "TERPSI_STORE_APP_DSN"


class NoDSN(LookupError):
    """No connection string for this role.

    Its own state, not an empty string and not a default (rule 13). A store
    that guesses where it is connecting has answered a question nobody asked it.
    """


class RolesNotSeparated(ValueError):
    """The two DSNs are the same string.

    G-D in one exception: *a store born single-role never sheds the habit.* The
    two-role split is not a deployment convention that can be satisfied by
    intent — if the application connects with the owner's credentials then every
    privilege revoked in `roles.py` is granted back by the connection.
    """


def _from_env(var: str) -> str:
    value = os.environ.get(var)
    if not value or not value.strip():
        raise NoDSN(
            f"{var} is not set. The store has no default connection string: a "
            "store that quietly connects to whatever is running is how test "
            "rows land in a cluster holding education records")
    return value.strip()


def owner_dsn() -> str:
    """The migration runner's connection string. DDL, and nothing else."""
    return _from_env(OWNER_DSN_VAR)


def app_dsn() -> str:
    """The application's connection string.

    Refuses to be the owner's. The check is here rather than in the installer
    because this is the function every application path goes through, and a
    check in the installer answers for the install rather than for the run.
    """
    app = _from_env(APP_DSN_VAR)
    owner = os.environ.get(OWNER_DSN_VAR, "")
    if owner.strip() and app == owner.strip():
        raise RolesNotSeparated(
            f"{APP_DSN_VAR} and {OWNER_DSN_VAR} are the same connection string, "
            f"so the application would connect as {OWNER_ROLE} and hold every "
            "privilege store/roles.py revokes (gate G-D)")
    return app


def connect(dsn: Optional[str] = None, *, autocommit: bool = False,
            **kw) -> "psycopg.Connection":
    """Open one connection. **The only `connect()` in the tree.**

    Everything that needs a connection comes through here, including
    `tests/cluster.py` — which could perfectly well import the driver itself and
    deliberately does not. If the test harness opened its own connections then
    *"exactly one module in this tree can reach the database"* would be false in
    the tree while remaining true in the shipped application, and the checker
    would have to carry an exception for the tests. An exception in a checker is
    the thing that later covers something else.

    `autocommit` defaults to **off**, which is psycopg's default and is
    load-bearing here rather than incidental: `store/narration.py` requires that
    a read and its disclosure entry share a transaction, and under autocommit
    there is no transaction to share. It is a keyword because the two callers
    that want it — creating and dropping a database — are doing the one thing
    that cannot run inside a transaction block.
    """
    return psycopg.connect(dsn if dsn is not None else owner_dsn(),
                           autocommit=autocommit, **kw)


def app_connection(*, autocommit: bool = False) -> "psycopg.Connection":
    """The application's connection, opened as `terpsi_app` from `app_dsn()`.

    **The one factory a surface calls, and the reason it exists is `tools/sockets.py`.**
    That checker reads a bare `connect(...)` as an outbound endpoint by call name,
    and the manifest's `outbound` declaration names exactly this module. A surface
    that spelled `connect()` itself would be a second outbound site the manifest
    does not admit — a finding on the next run — so the surface asks for a
    connection by a name that is not `connect`, and the one `connect()` stays here
    where it is declared. `store/connecting.py` is still the whole outbound list.

    `app_dsn()` refuses to be the owner's (gate G-D), so a session opened through
    here holds `INSERT` and `SELECT` and nothing else — the store's read-first
    surface (S-4) cannot rewrite history or end a record even if it tried.
    """
    return connect(app_dsn(), autocommit=autocommit)


def reachable(dsn: str, *, timeout: int = 5) -> tuple:
    """`(ok, why)` for a store somebody is about to use.

    Here rather than in the caller because it is the same `connect` — a
    reachability probe that opened its own connection would be a second path to
    the database, and the second path is the one nobody watches.
    """
    try:
        with connect(dsn, connect_timeout=timeout) as conn:
            conn.execute("SELECT 1")
        return True, "reachable"
    except Exception as exc:  # noqa: BLE001
        return False, f"{exc!r}"
