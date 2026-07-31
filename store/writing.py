"""The draft-write path: what the application role may put in the store.

`docs/PLAN-STORE.md` decision 2 — *"the write model is rule 11 with the seal
cascade as its middle"*. Writes land as **drafts**. A named human's seal is the
promotion, and the seal is `records/sealing.py`'s and nobody else's: this module
can produce a `draft`, can produce a `pending`, and **cannot produce a
`sealed`**. There is no parameter for it and adding one would move the act of
standing behind a record from a person to a function call.

**Two refusals live here, and both are at the adapter rather than in the DDL**,
because both are about what the application may attempt rather than about what a
row may contain:

* **An unclassified column.** Every column named in the `INSERT` is checked
  against `store/classification.py`, which asks `tools/registry.py`. A column
  the registry does not carry is refused with the registry cited. The DDL cannot
  do this — a `CHECK` sees values, not the set of columns somebody wrote — and
  the CI step that asserts every column is classified runs at schema time, which
  is one deploy too early to stop a hand-written `INSERT` naming a column that
  was added and never seeded.
* **A seal state the cascade does not open with.** `sealed` is refused by name,
  and so is anything outside `records/sealing.py`'s vocabulary. The DDL's
  `lane_entry_seal_state` CHECK admits `sealed`, correctly — the *table* must
  hold sealed rows, or there would be nothing for the seal to produce. What must
  not happen is the application minting one, and that is a rule about the writer.

**Identifiers are composed with the driver's own quoting**, never with an
f-string. The table and column names reaching the SQL have all been checked
against the registry first, so injection is already closed by the allowlist; the
quoting is there because the next person to add a code path here will not know
that, and a defence that depends on remembering the previous defence is one
defence.

**What this module does not do.** It does not seal (S-3), does not encrypt the
payload at rest (S-3 — writes land in the clear today, and that is a gap with a
name rather than an oversight), and does not decide who may write. The last is
the role's job and the role is `terpsi_app`: `INSERT` and `SELECT`, nothing else.

Stdlib plus the driver's SQL composition.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from psycopg import sql as _sql

from .classification import UnclassifiedColumn, carries, tables

#: The states a write may open in, straight from `records/sealing.py`'s cascade.
#: `SEALED` is absent, and its absence is the rule: there is no way to spell it
#: here, the way `L5` has no way to be spelled in `access_grant.max_rung`.
OPENS_AS = ("draft", "pending")

#: The state a seal produces. Named so the refusal can name it, imported by the
#: test so the two cannot drift.
SEALED = "sealed"


class SealStateRefused(ValueError):
    """An application write that tried to arrive already sealed.

    §8.2 and rule 10: *a machine answer is a `draft` until a named human seals
    it.* A row inserted as `sealed` has skipped the only step that makes it a
    record, and it would be indistinguishable afterwards from one a person
    actually stood behind.
    """


class UnknownTable(UnclassifiedColumn):
    """A write to a table the registry does not carry.

    A subclass, because it is the same refusal at a coarser grain and a caller
    catching `UnclassifiedColumn` should catch this too — a table nothing
    classifies has no classified columns by definition.
    """


def check_columns(table: str, columns) -> Tuple[str, ...]:
    """Every column, against the registry. Raises on the first one missing.

    Returned rather than merely checked so the caller can log what was verified;
    a check whose result is discarded reads the same as one that was skipped.
    """
    if table not in tables():
        raise UnknownTable(
            f"{table!r} is not a table the classification registry carries "
            f"({', '.join(tables())}). tools/registry.py parses the seed in "
            "migrations/001_lanes.sql, and a table with no classified columns "
            "is a place to keep facts nobody has rung")
    names = tuple(columns)
    for column in names:
        if not carries(table, column):
            raise UnclassifiedColumn(
                f"{table}.{column} is not in the classification registry "
                "(tools/registry.py, over migrations/001_lanes.sql's seed). "
                "docs/SENSITIVITY.md: an unclassified field is a build failure, "
                "not a default — refusing the write rather than inventing a rung")
    return names


def check_seal_state(values: Dict[str, Any]) -> str:
    """The state this write opens in. `sealed` is refused by name."""
    state = values.get("seal_state", "draft")
    if state == SEALED:
        raise SealStateRefused(
            "an application write cannot arrive sealed. records/sealing.py's "
            "seal() requires a named human and a date; a row inserted as "
            f"{SEALED!r} would be indistinguishable afterwards from one somebody "
            "stood behind (§8.2, rule 10)")
    if state not in OPENS_AS:
        raise SealStateRefused(
            f"{state!r} is not a state the cascade opens with. "
            f"records/sealing.py has {', '.join(OPENS_AS)} before a seal, and a "
            "third state is a place for a row to hide in")
    return state


def insert_draft(conn, table: str, values: Dict[str, Any], *,
                 returning: Optional[str] = None):
    """Insert one row as a draft. Returns the `returning` column when asked.

    Does **not** commit: the caller owns the transaction, because a write that
    committed itself could not share one with the disclosure entry that narrates
    it (`store/narration.py`), and this is the module that would otherwise make
    that impossible.
    """
    body = dict(values)
    if table == "lane_entry":
        body["seal_state"] = check_seal_state(body)
        if body.get("sealed_by") is not None:
            raise SealStateRefused(
                "an application write cannot name a sealer. sealed_by is set by "
                "the seal, and the seal is a human act (records/sealing.py)")
    names = check_columns(table, body)

    statement = _sql.SQL("INSERT INTO {table} ({columns}) VALUES ({places})").format(
        table=_sql.Identifier(table),
        columns=_sql.SQL(", ").join(_sql.Identifier(n) for n in names),
        places=_sql.SQL(", ").join(_sql.Placeholder() for _ in names),
    )
    if returning:
        check_columns(table, (returning,))
        statement = statement + _sql.SQL(" RETURNING {}").format(
            _sql.Identifier(returning))

    with conn.cursor() as cur:
        cur.execute(statement, tuple(body[n] for n in names))
        return cur.fetchone()[0] if returning else None
