"""The migration runner: filename order, a checksum per file, and three refusals.

`migrations/001_lanes.sql` has been executed and attacked in CI since it landed,
by a `psql -f` in a workflow. That is enough to prove the DDL and not enough to
run a cluster: nothing recorded *which* migrations an instance had, so nothing
could notice a file that changed after it was applied, or one that arrived with
a number below the last one applied. Both are silent, and both produce two
instances whose schemas differ while their trees agree.

**What is recorded.** One row per applied file in `store_meta.schema_migrations`
— ordinal, filename, checksum of the exact bytes applied, and when. The
checksum is over the file as read, not over a normalised form: a whitespace-only
edit to an applied migration is still an edit to a file this instance ran, and
deciding which edits are harmless is a judgement no runner should be making at
three in the morning.

**Three refusals, each attempted in `tests/test_store_migrate.py`.**

* **A modified migration.** The file's checksum no longer matches the row.
  `MigrationModified`, naming the file and both digests. Never re-applied and
  never quietly re-recorded.
* **An out-of-order migration.** A pending file whose name sorts below the
  highest applied name. `MigrationOutOfOrder`, naming both. This is the one that
  looks harmless: the file applies cleanly, and the instance that ran them in
  the other order has a different schema with the same ledger.
* **A migrations directory that cannot be read.** `PlanState.UNREADABLE` with
  the reason attached — **not an empty plan** (rule 13). *"There are no
  migrations to apply"* and *"the migrations could not be listed"* are the same
  sentence and different facts, and the first is how an instance comes up with
  no schema and no complaint.

**Each migration and its ledger row commit together.** The `INSERT` into
`schema_migrations` happens inside the migration's own transaction, so a
migration that fails half way records nothing and a ledger row can never name a
migration that did not land. That is the same rule `store/narration.py` applies
to a read and its disclosure entry, one layer down.

Stdlib only. The caller supplies the connection.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

from .roles import META_SCHEMA

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"

LEDGER = f"{META_SCHEMA}.schema_migrations"

LEDGER_DDL = f"""
CREATE SCHEMA IF NOT EXISTS {META_SCHEMA};
CREATE TABLE IF NOT EXISTS {LEDGER} (
    ordinal    integer     NOT NULL,
    filename   text        PRIMARY KEY,
    checksum   text        NOT NULL,
    applied_at timestamptz NOT NULL
);
"""


class PlanState(Enum):
    READY = "ready"            # the directory was read; `pending` is the answer
    UNREADABLE = "unreadable"  # it could not be read. Not an empty plan.


@dataclass(frozen=True)
class Migration:
    filename: str
    checksum: str
    sql: str


@dataclass(frozen=True)
class Applied:
    ordinal: int
    filename: str
    checksum: str
    applied_at: datetime


@dataclass(frozen=True)
class Plan:
    """What would be applied, or why that question could not be answered."""

    state: PlanState
    pending: Tuple[Migration, ...] = ()
    applied: Tuple[Applied, ...] = ()
    reason: str = ""

    @property
    def readable(self) -> bool:
        return self.state is PlanState.READY

    def __iter__(self):
        """Iterating an unreadable plan raises rather than yielding nothing.

        `records/sending.py`'s `SendList.__iter__`, applied one layer down and
        for the same failure: `for m in discover(...)` over a directory that
        could not be listed is indistinguishable, from the loop alone, from an
        instance that is up to date.
        """
        if self.state is not PlanState.READY:
            raise RuntimeError(
                f"the migration plan is {self.state.value}, not ready: "
                f"{self.reason}. An unreadable migrations directory is not an "
                "empty one")
        return iter(self.pending)


class MigrationModified(RuntimeError):
    """An applied migration's bytes have changed since it was applied."""


class MigrationOutOfOrder(RuntimeError):
    """A pending migration sorts below one that has already been applied."""


def checksum(sql: str) -> str:
    """SHA-256 over the exact text. No normalisation — see the module docstring."""
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _read_dir(where: Path) -> Tuple[Optional[Tuple[Migration, ...]], str]:
    """`(migrations, "")` or `(None, why)`. Never `((), why)`."""
    try:
        if not where.exists():
            return None, f"{where} does not exist"
        if not where.is_dir():
            return None, f"{where} is not a directory"
        files = sorted(where.glob("*.sql"), key=lambda p: p.name)
        return tuple(Migration(p.name, checksum(t), t)
                     for p, t in ((p, p.read_text(encoding="utf-8")) for p in files)), ""
    except OSError as exc:
        return None, f"{where} could not be read: {exc!r}"


def applied_rows(conn) -> Tuple[Applied, ...]:
    """What this instance has run, in the order it ran it."""
    with conn.cursor() as cur:
        cur.execute(LEDGER_DDL)
        conn.commit()
        cur.execute(f"SELECT ordinal, filename, checksum, applied_at "
                    f"FROM {LEDGER} ORDER BY ordinal")
        return tuple(Applied(*r) for r in cur.fetchall())


def discover(conn, where: Optional[Path] = None) -> Plan:
    """What is pending, having checked what is applied.

    Raises `MigrationModified` and `MigrationOutOfOrder` rather than returning
    them as findings: neither is a state an instance may run in, and a caller
    that had to remember to inspect a field would be the caller that did not.
    """
    base = MIGRATIONS if where is None else Path(where)
    found, why = _read_dir(base)
    if found is None:
        return Plan(PlanState.UNREADABLE, (), (), why)

    done = applied_rows(conn)
    by_name: Dict[str, Applied] = {a.filename: a for a in done}

    for m in found:
        was = by_name.get(m.filename)
        if was is not None and was.checksum != m.checksum:
            raise MigrationModified(
                f"{m.filename} was applied as {was.checksum[:12]}… and now reads "
                f"{m.checksum[:12]}…. An applied migration is history; edit it "
                "and this instance's schema stops being derivable from this tree")

    pending = tuple(m for m in found if m.filename not in by_name)
    if done and pending:
        highest = max(a.filename for a in done)
        behind = [m.filename for m in pending if m.filename < highest]
        if behind:
            raise MigrationOutOfOrder(
                f"{', '.join(behind)} sorts below {highest}, which is already "
                "applied. It would apply cleanly here and land in the other "
                "order on an instance that has not run either — two schemas, "
                "one ledger")
    return Plan(PlanState.READY, pending, done, f"{len(pending)} pending")


def apply_all(conn, where: Optional[Path] = None, *,
              at: Optional[datetime] = None) -> Tuple[Applied, ...]:
    """Apply every pending migration in filename order. Returns what was applied.

    Each file and its ledger row share one transaction. A failure rolls both
    back, so the ledger cannot name a migration that did not land.
    """
    plan = discover(conn, where)
    when = at if at is not None else datetime.now(timezone.utc)
    landed = []
    start = len(plan.applied)
    for i, m in enumerate(plan):  # raises if the plan is unreadable
        with conn.cursor() as cur:
            cur.execute(m.sql)
            cur.execute(
                f"INSERT INTO {LEDGER} (ordinal, filename, checksum, applied_at) "
                "VALUES (%s, %s, %s, %s)",
                (start + i + 1, m.filename, m.checksum, when))
        conn.commit()
        landed.append(Applied(start + i + 1, m.filename, m.checksum, when))
    return tuple(landed)


def run(conn, where: Optional[Path] = None, *,
        app_password: Optional[str] = None) -> Tuple[Applied, ...]:
    """The whole install: roles first, then the schema, then the grants.

    **Roles before the first table is populated** (G-D), and the grants after
    the migrations because `GRANT ON ALL TABLES` reaches the tables that exist
    when it runs.
    """
    from .roles import apply_grants, ensure_roles

    ensure_roles(conn, app_password=app_password)
    landed = apply_all(conn, where)
    apply_grants(conn)
    return landed
