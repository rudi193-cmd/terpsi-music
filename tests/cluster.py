"""A real PostgreSQL, or a loud unknown. Never a silent skip.

Every store test needs a cluster. The ordinary way to write that is
`@skipif(no database)`, and this repository has spent enough runs on gates that
were green because nothing routed through them to know what a skipped store
suite looks like from outside: identical to one that passed.

**So there is no skip.** `cluster()` returns a DSN or raises `ClusterUnknown`,
and every store test module ends with a `__main__` block that reports
`UNKNOWN — N tests did not run` and **exits nonzero**. A run without a database
is a run whose result nobody has, which is rule 13 applied to the suite itself
rather than to the code under it.

**The house pattern is `.github/workflows/tests.yml`'s schema job** — a
`postgres:16` service, `psql -f migrations/001_lanes.sql`, then every constraint
attacked directly. These tests join it rather than inventing a second way in:
same image, same migration, same discipline of asserting on the guard **named**
in the error rather than on the fact of a refusal.

**Each module gets its own database**, created and dropped around the tests, so
a failure leaves nothing behind for the next module to inherit and two modules
cannot race. The template is `template1` and the creation is done on the
maintenance connection.

`TERPSI_TEST_DSN` points at the cluster; it defaults to the local socket, which
is what a container running its own `postgres` has.
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MAINTENANCE_VAR = "TERPSI_TEST_DSN"
DEFAULT_DSN = "dbname=postgres"


class ClusterUnknown(RuntimeError):
    """No cluster to run against. Reported as UNKNOWN, never as a pass."""


def maintenance_dsn() -> str:
    return os.environ.get(MAINTENANCE_VAR, DEFAULT_DSN)


def _connect():
    """`store.connecting.connect` — **this harness does not import the driver.**

    It could, trivially. Not importing it is what keeps *"exactly one module in
    this tree can open a connection"* true of the tree and not merely of the
    shipped application, so `tools/drivers.py` needs no exception for the tests
    and `manifest.json` declares one outbound module rather than two. An
    exception in a checker is the thing that later covers something else.
    """
    try:
        from store.connecting import connect
    except ImportError as exc:  # pragma: no cover — requirements.txt pins it
        raise ClusterUnknown(
            f"the store's driver is not installed ({exc!r}); "
            "pip install -r requirements.txt") from exc
    return connect


def available() -> Tuple[bool, str]:
    """`(reachable, why)`. The question asked before a module builds a fixture."""
    try:
        from store.connecting import reachable
    except ImportError as exc:  # pragma: no cover
        return False, f"the store's driver is not installed ({exc!r})"
    ok, why = reachable(maintenance_dsn())
    if ok:
        return True, why
    return False, (
        f"no PostgreSQL at {maintenance_dsn()!r}: {why}. Set "
        f"{MAINTENANCE_VAR}, or start the cluster the way "
        ".github/workflows/tests.yml's schema job does")


class Database:
    """A throwaway database, dropped on exit. Use as a context manager."""

    def __init__(self, prefix: str = "terpsi_test"):
        self.name = f"{prefix}_{uuid.uuid4().hex[:12]}"
        self._open = None

    def __enter__(self) -> "Database":
        ok, why = available()
        if not ok:
            raise ClusterUnknown(why)
        self._open = _connect()
        with self._open(maintenance_dsn(), autocommit=True) as conn:
            conn.execute(f'CREATE DATABASE "{self.name}"')
        return self

    def __exit__(self, *exc):
        with self._open(maintenance_dsn(), autocommit=True) as conn:
            conn.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (self.name,))
            self._wait_for_backends(conn)
            conn.execute(f'DROP DATABASE IF EXISTS "{self.name}"')
        return False

    def _wait_for_backends(self, conn, tries: int = 100) -> None:
        """Block until the terminated backends are actually gone.

        **`pg_terminate_backend` sends a signal; it does not wait.** Without
        this the next test's `installed()` can begin while a backend from the
        previous one is still dying, and `ensure_roles` — which touches
        `pg_authid`, a *cluster-global* catalog that a dropped database does not
        take with it — fails with `tuple concurrently updated`.

        Observed once while `tests/test_store_atrest.py` was being written: two
        of fifteen tests failed, both passed in isolation, and four subsequent
        full runs were clean. That is the shape of a flake that teaches everyone
        to press re-run, which is the habit that later hides a real failure.
        Waiting is the fix that removes the race rather than retrying past it.
        """
        for _ in range(tries):
            left = conn.execute(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = %s "
                "AND pid <> pg_backend_pid()", (self.name,)).fetchone()[0]
            if not left:
                return
            time.sleep(0.02)
        # Not raised: the DROP below reports the real problem with the real
        # message, and a harness that failed here would hide the test's own
        # result behind its cleanup.

    @property
    def dsn(self) -> str:
        base = maintenance_dsn()
        # Replace the database, keeping host/user/port from the maintenance DSN.
        parts = [p for p in base.split() if not p.startswith("dbname=")]
        return " ".join(parts + [f"dbname={self.name}"])

    def connect(self, *, user: Optional[str] = None,
                password: Optional[str] = None, autocommit: bool = False):
        dsn = self.dsn
        if user:
            dsn += f" user={user}"
        if password:
            # TCP, because peer authentication over the socket answers for the
            # operating-system user and the whole point of the app connection is
            # that it is a different *database* role.
            dsn += f" password={password} host=127.0.0.1"
        return self._open(dsn, autocommit=autocommit)


APP_PASSWORD = "not-a-secret-this-database-is-dropped-in-a-moment"


def installed(db: "Database", *, migrations: Optional[Path] = None):
    """Roles, schema and grants — the whole install, on a throwaway database.

    Returns `(owner_conn, app_conn)`. The app connection is opened **as the app
    role over TCP**, not as a superuser with `SET ROLE`: a superuser that has
    set role does drop its bypass, but the test would then be asserting about a
    connection nobody in production has. The password is a literal because the
    database it authenticates to is dropped before this function's caller
    returns; nothing here is a credential.
    """
    from store.migrate import run

    owner = db.connect()
    run(owner, migrations, app_password=APP_PASSWORD)
    app = db.connect(user="terpsi_app", password=APP_PASSWORD)
    return owner, app


class Custody:
    """A master, a keyring and one lane key per lane — **minted in memory only.**

    Refusal 2 at the test harness: *never commit the trust root.* Key material
    is minted here, lives for the duration of one throwaway database, and is
    never written to the tree, to a fixture, to an environment variable or to a
    file. `records/atrest.py` persists nothing by design (§6's core/seam
    partition), and this is the shape a caller who honours that looks like: it
    holds the `Keyring` — which carries only wrappings, and is useless without
    the master — plus the master and the unwrapped lane keys in local variables.

    A fixture holding a real key would be worse than a fixture holding a
    password: a key that opens a sealed payload is the payload, and it would be
    in the tree forever. `tests/test_key_custody.py` scans the whole tree for
    both spellings and fails on either, so this is a guard rather than a habit.

    The password in `APP_PASSWORD` above is deliberately *not* the same kind of
    thing and the distinction is worth keeping: it authenticates to a database
    that is dropped before the caller returns, and it decrypts nothing.
    """

    def __init__(self, *lane_ids: str, at: datetime):
        from records.atrest import Keyring, new_master, open_lane_key

        self.master = new_master()
        keyring, keys = Keyring(), {}
        for lane_id in lane_ids:
            keyring, keys[lane_id] = open_lane_key(
                keyring, lane_id=str(lane_id), master=self.master, at=at)
        self.keyring = keyring
        self.keys = keys

    def key(self, lane_id) -> "object":
        return self.keys[str(lane_id)]

    def __repr__(self) -> str:
        # Same rule as `MasterKey.__repr__`: key material is L5 and a dataclass
        # repr in a traceback is a rendering.
        return (f"Custody(lanes={sorted(self.keys)}, "
                f"master={self.master.key_id!r}, material=<withheld>)")


def refused_by(fn, guard: str) -> str:
    """Run `fn`, require it to fail, and require the error to **name** `guard`.

    `.github/workflows/tests.yml`'s `refuse()` in Python. The workflow's comment
    is the reason this exists rather than a bare `assertRaises`: *a BEFORE ROW
    trigger fires ahead of every CHECK, NOT NULL and foreign key on the same
    row, so an attack that only asserts "this was refused" can be satisfied by a
    guard other than the one under test.* A privilege refusal is earlier still —
    it happens before any trigger runs — so a role attack and a trigger attack
    can stand in for each other unless each names what spoke.
    """
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        text = f"{exc}"
        code = getattr(exc, "sqlstate", "") or ""
        if guard not in text and guard != code:
            raise AssertionError(
                f"REFUSED BY THE WRONG GUARD\n   wanted: {guard}\n"
                f"   got:    {type(exc).__name__}: {text.splitlines()[0]}"
                + (f" [SQLSTATE {code}]" if code else "")) from None
        return text
    raise AssertionError(f"NOT REFUSED: expected {guard!r} to speak")


def report(name: str, failures: int, ran: int, unknown: str = "") -> int:
    """The exit code for a store module's `__main__` block.

    `2` for unknown, so a caller can tell *the guards failed* from *nobody
    asked them*. Both are nonzero: a suite that did not run has not passed.
    """
    if unknown:
        print(f"\nUNKNOWN — {name}: {unknown}")
        print("  No store test ran. That is not a pass (rule 13).")
        return 2
    print(f"\n{name}: {ran - failures}/{ran} passed")
    return 1 if failures else 0
