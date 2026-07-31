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

---

## The sealing seam (S-3), and why it is a shape rather than a filter

`docs/PLAN-STORE.md` decision 3: *payloads sealed at rest per lane; predicate
columns clear.* `store/sealing_plan.py` derives **which** columns those are;
this module is where the sealing happens, and it happens **before the INSERT**,
never after.

**There is no code path that puts a clear payload into a sealed column, and the
reason is the shape of the call rather than a check inside it.** A caller names
the *fact* — `values["payload"]` — and never the storage. The seam takes those
bytes, hands them to `records/atrest.py::seal_bytes` with the lane's key, and
writes the four envelope columns itself. The clear column is tombstoned by
migration 004 and is never in the column list this module builds; the envelope
columns are refused by name if a caller tries to spell one. So *"insert a
readable payload"* is not a thing that is filtered out — it is a thing that
cannot be written down. The path around the adapter — a hand-written `INSERT` as
`terpsi_app` — is refused by the DDL instead, by
`lane_entry_payload_sealed_is_ciphertext`, and `tests/test_store_atrest.py`
performs that act and asserts on the constraint's name.

**Nothing here unseals, and nothing here ever will.** The core/seam partition
(§6) puts the key with the caller: `store/reading.py` returns the `Sealed`
envelope and whoever holds the lane key opens it. `tests/test_sealing_plan.py`
scans `store/` for the unsealing verbs and fails on any of them, so this is a
guard rather than a paragraph.

**What this module still does not do.** It does not seal in
`records/sealing.py`'s sense — that is rule 10's human cascade and remains a
human act — and it does not decide who may write. The last is the role's job and
the role is `terpsi_app`: `INSERT` and `SELECT`, nothing else.

Stdlib, `records/atrest.py`, and the driver's SQL composition.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from psycopg import sql as _sql

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.atrest import LaneKey, seal_bytes  # noqa: E402

from .classification import UnclassifiedColumn, carries, tables
from .sealing_plan import envelope_columns, lane_column, sealed_in

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


# --- the sealing seam's refusals -------------------------------------------


class SealingRefused(ValueError):
    """Base for the ways a sealed-column write is not one.

    One base so a caller can catch *the payload did not get sealed* without
    enumerating the reasons, and four subclasses because the reasons are four
    different facts and a caller deciding what to do about them needs to tell a
    missing key from a wrong one (rule 13, at a signature).
    """


class EnvelopeColumnRefused(SealingRefused):
    """A caller naming an envelope column directly.

    `payload_sealed`, `payload_key_id`, `payload_scheme` and `payload_sealed_at`
    are produced by this module from a `Sealed`, and are not an application's to
    write. Permitting one would restore the whole hole by the back door: a caller
    that can set `payload_sealed` can set it to anything, and the DDL's shape
    constraint is the last thing standing rather than the second.
    """


class LaneKeyRequired(SealingRefused):
    """A write carrying a sealed-class value with no lane key to seal it under.

    Refused rather than written in the clear, which is
    `records/atrest.py::PrimitiveUnavailable`'s argument one layer up: a
    fallback that stores the payload readable would make sealed and unsealed
    look identical at every call site, and the first place anyone notices is a
    breach.
    """


class LaneKeyMismatch(SealingRefused):
    """A lane key offered for one lane and a row belonging to another.

    W-1, at the seam: one lane, one key. Sealing Ben's row under Cara's key puts
    two students' records under one key, so destroying Cara's makes Ben's
    unreadable and Ben's erasure leaves Cara able to read his.
    """


class PayloadMissing(SealingRefused):
    """A row whose sealed column has no value at all.

    `lane_entry.payload` was `NOT NULL` before migration 004 and the sealed form
    is nullable, for the reason stated in that migration: a `NOT NULL` there
    would make every direct `psql` seed in CI mint a Fernet token. The
    requirement did not go away, it moved here — and this is where it is said
    (§7.2: say which).
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


def seal_payloads(table: str, values: Dict[str, Any], *,
                  lane_key: Optional[LaneKey], at: Optional[datetime],
                  ) -> Dict[str, Any]:
    """Replace every sealed-class value with its envelope. **Before the INSERT.**

    Returns a new body in which no sealed-class column appears and the envelope
    columns do. The caller named a fact; what comes back names storage, and the
    conversion is the only route between the two.

    `at` is the seal time and is **derived, not defaulted**: the row's own
    `created_at` is what a seal happening at write time means, and inventing
    `now()` here would put a second clock in the row. A table with a sealed
    column and no write time to seal at is refused rather than guessed
    (`records/dispositions.py`'s P-2 rule, applied to a timestamp).
    """
    sealed_here = sealed_in(table)
    if not sealed_here:
        return dict(values)

    for column in sealed_here:
        for spelled in envelope_columns(column):
            if spelled in values:
                raise EnvelopeColumnRefused(
                    f"{table}.{spelled} is part of the Sealed envelope and is "
                    f"written by store/writing.py from records/atrest.py's "
                    f"seal_bytes(), never by a caller. Pass {column!r} — the "
                    "fact — and the seam decides where the bytes land")

    body = {k: v for k, v in values.items() if k not in sealed_here}
    lane_at = values.get(lane_column(table))
    when = at if at is not None else values.get("created_at")

    for column in sealed_here:
        payload = values.get(column)
        if payload is None:
            raise PayloadMissing(
                f"{table}.{column} carries the row's payload and this write has "
                f"none. It was NOT NULL before migration 004 and the sealed form "
                "is nullable so CI's psql seeds need no key material; the "
                "requirement moved here rather than going away")
        if not isinstance(payload, (bytes, bytearray)):
            raise SealingRefused(
                f"{table}.{column} must be bytes to seal. Encoding is the "
                "caller's decision and guessing it here would put a charset "
                "inside the ciphertext (records/atrest.py::seal_bytes)")
        if lane_key is None:
            raise LaneKeyRequired(
                f"{table}.{column} is sealed at rest per lane "
                f"(store/sealing_plan.py) and this write offered no lane key. "
                "There is no clear column to fall back to: migration 004 "
                f"tombstoned {table}.{column} and constrained it to NULL")
        if not isinstance(lane_key, LaneKey):
            raise LaneKeyRequired(
                "the seam seals with a LaneKey. records/atrest.py refuses a "
                "MasterKey by type: the root key never touches a record (§5)")
        if lane_at is not None and str(lane_at) != lane_key.lane_id:
            raise LaneKeyMismatch(
                f"this row belongs to lane {lane_at} and the key offered is for "
                f"{lane_key.lane_id}. One lane, one key (W-1): sealing across "
                "lanes makes one student's erasure another student's data loss")
        if when is None:
            raise SealingRefused(
                f"{table}.{column} seals at a declared instant and this write "
                "carries neither an `at` nor a created_at to derive one from")

        envelope = seal_bytes(bytes(payload), lane_key=lane_key, at=when)
        got = (envelope.ciphertext, envelope.key_id, envelope.scheme,
               envelope.sealed_at)
        body.update(dict(zip(envelope_columns(column), got)))
    return body


def insert_draft(conn, table: str, values: Dict[str, Any], *,
                 lane_key: Optional[LaneKey] = None,
                 at: Optional[datetime] = None,
                 returning: Optional[str] = None):
    """Insert one row as a draft. Returns the `returning` column when asked.

    Does **not** commit: the caller owns the transaction, because a write that
    committed itself could not share one with the disclosure entry that narrates
    it (`store/narration.py`), and this is the module that would otherwise make
    that impossible.

    `lane_key` is the lane's data key, held by the caller and never by this
    module — `records/atrest.py` persists nothing and neither does this. It is
    required exactly when the table has a sealed-class column, which
    `store/sealing_plan.py` decides; for every other table it is unused and
    passing one is harmless.
    """
    body = dict(values)
    if table == "lane_entry":
        body["seal_state"] = check_seal_state(body)
        if body.get("sealed_by") is not None:
            raise SealStateRefused(
                "an application write cannot name a sealer. sealed_by is set by "
                "the seal, and the seal is a human act (records/sealing.py)")
    # Sealing happens before the column check, so the columns checked against the
    # registry are the columns the statement will actually name.
    body = seal_payloads(table, body, lane_key=lane_key, at=at)
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
