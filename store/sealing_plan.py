"""Which columns seal at rest, **derived** — never a list somebody maintains.

`docs/PLAN-STORE.md` decision 3 is one sentence and this module is its
mechanism: *"Payloads sealed at rest per lane; predicate columns clear. The `L3`+
rule already says the payload is `NULL` in the SELECT list and only a derived
instruction is served — so the store never needs to read payload contents to
answer a query."*

A hand-written list of sealed columns is the shape rule 17 exists to refuse: it
is right on the day it is written and silently wrong after the next migration.
So the set is computed from two things already in the tree — the classification
registry (`tools/registry.py` over every migration's seed) and the
DDL itself — and `migrations/004_sealed_payloads.sql` is checked against it by
`tests/test_sealing_plan.py`. A column added to a sealable table without a
decision goes red rather than quietly landing in the clear.

## The rule, as exclusions

A classified column seals **iff no exclusion applies to it.** Each exclusion is
a fact read off the tree, and each is reported by name, so a reader can disagree
with a specific one rather than with a verdict:

* **`RUNG_BELOW_L3`** — `L1`/`L2`. `docs/SENSITIVITY.md`'s derive floor is `L3`
  and below it the payload is the normal serving mode; sealing what is served in
  the clear anyway buys nothing and costs a key lookup per read.
* **`KEY`** — a primary key, a `UNIQUE`, or a `REFERENCES`. The store joins on
  it. Ciphertext has no referential integrity, and Fernet is randomised, so two
  seals of one id do not even compare equal — a sealed foreign key is not a
  weaker join, it is no join.
* **`TEMPORAL`** — a `timestamptz` or `date`. §7's whole model is interval
  predicates (`valid_at`/`invalid_at`, `expires_at`); a sealed date cannot be
  compared and every liveness check becomes a full unseal.
* **`EVALUATED_BY_DDL`** — the column name appears inside a `CHECK` expression on
  its own table. A `CHECK` reads the *value* — `length(btrim(x)) > 0`,
  `x IN (...)`, `x <> y` — and ciphertext satisfies or fails those meaninglessly.
  `lane.exit_terms` is the instructive one: it is `PII_MINOR`/`L3` content, and
  `lane_exit_terms_present` is W-6 enforced at the row. Sealing it would trade a
  ward clause for an encryption property.

  **The sealing's own constraints are not evidence against it**, and leaving them
  in was a real circularity caught by running this: migration 004 tombstones
  `lane_entry.payload` with `CHECK (payload IS NULL)`, so the first version of
  this derivation read that constraint, concluded `payload` was evaluated by the
  DDL, and reported that the column it had just sealed should be clear. A
  derivation that reads its own output is worse than a hand-written list, because
  it looks derived. So a `CHECK` is skipped when it is the seal's own enforcement
  — one naming an envelope column, or a bare `(x IS NULL)` tombstone — and
  `tests/test_sealing_plan.py` pins the fixed point directly: the set derived from
  the migrations *before* the sealing one equals the set derived from all of them.


* **`NOT_A_CONTAINER`** — the declared type is not `jsonb`. This is the exclusion
  that carries a judgement rather than a mechanism, and it is stated as one: in
  this schema `jsonb` is the only type whose contents the DDL declines to
  describe, which is exactly why the seed classifies `lane_entry.payload`
  `HEALTH`/`L4` — *"composition is by max and that column can hold anything."*
  Everything else at `L3`+ is a value the schema names: a uuid it joins on, a
  timestamp it compares, a text a `CHECK` reads, or a discriminator whose
  vocabulary **is** the query surface. `lane_entry.kind` is the case worth
  disagreeing with explicitly: the seed already concedes it discloses
  (*"'medical_note' discloses without its payload"*), and it stays clear because
  sealing it makes *"which entries are in this lane"* unanswerable without
  unsealing every row — which is decision 3's argument switched off.
* **`NO_SINGLE_LANE`** — the table does not name exactly one `NOT NULL` lane.
  There is no key to seal under: `records/atrest.py` mints one key per lane
  (W-1), so a table naming zero lanes has no key and a table naming two —
  `crossing_envelope` — would put one row under one sibling's key, making the
  other sibling's erasure incomplete or the first's over-broad.
* **`CHAIN_MATERIAL`** — the table carries a `hash`/`prev_hash` pair.
  `records/atrest.py::composes()` asserts that destroying a lane's key leaves the
  chain verifying; sealing chain material under that same key would break the
  exact property the erasure is supposed to preserve.

**Every exclusion that applies is reported, not just the first.** A precedence
order would let a column with three reasons look like a column with one, and the
reason a reader most wants is not reliably the one a precedence picks.

Stdlib only. No database — this reads migration text, the same choice
`store/classification.py` argues for: the migration is in the tree, is
checksummed by `store/migrate.py`, and a row deleted from a live cluster cannot
widen what seals.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import registry as _registry  # noqa: E402 — the source of truth, called not copied

MIGRATIONS = ROOT / "migrations"


def _sql() -> str:
    """Every migration as one text — `tools/registry.py::schema_text`'s job.

    Not `001` alone: 004 adds the envelope columns and seeds their
    classification, and a derivation that read only the first file would
    conclude they are unclassified and refuse writes to columns it created.
    """
    return _registry.schema_text(MIGRATIONS)

#: The rung at or above which a container column seals. `records/rungs.py`'s
#: derive floor, imported rather than respelled — the floor moving must move
#: this with it.
from records.rungs import DERIVE_AT, Rung, at_least  # noqa: E402

#: The one type in this schema whose contents the DDL declines to describe.
CONTAINER_TYPE = "jsonb"

#: The Sealed envelope's fields, as the column suffixes migration 004 adds.
#: `records/atrest.Sealed` carries five; `lane_id` is deliberately **not** one of
#: these — the row already names its lane, and a second copy would be a pair with
#: no middle (rule 12). Reading rebuilds the envelope with the row's own lane id,
#: so a row moved between lanes fails to open as `MISBOUND` instead of opening.
ENVELOPE_SUFFIXES = ("sealed", "key_id", "scheme", "sealed_at")

#: What makes a table's rows chain material.
_CHAIN_COLUMNS = frozenset({"hash", "prev_hash"})

_CHECK = re.compile(r"\bCHECK\s*\(", re.I)
_LANE_REF = re.compile(r"\bREFERENCES\s+lane\s*\(\s*lane_id\s*\)", re.I)


class Clear(Enum):
    """Why a classified column is **not** sealed. Never a bare boolean."""

    RUNG_BELOW_L3 = "rung_below_l3"
    KEY = "key"
    TEMPORAL = "temporal"
    EVALUATED_BY_DDL = "evaluated_by_ddl"
    NOT_A_CONTAINER = "not_a_container"
    NO_SINGLE_LANE = "no_single_lane"
    CHAIN_MATERIAL = "chain_material"


#: One sentence per exclusion, so a migration comment and a test failure quote
#: the same reason. The long form of each is in this module's docstring.
WHY: Dict[Clear, str] = {
    Clear.RUNG_BELOW_L3: "below the L3 derive floor; served in the clear anyway",
    Clear.KEY: "a key the store joins on; randomised ciphertext is not a join",
    Clear.TEMPORAL: "an interval predicate; a sealed date cannot be compared",
    Clear.EVALUATED_BY_DDL: "named inside a CHECK on its own table, which reads the value",
    Clear.NOT_A_CONTAINER: "a value the schema names, not a container it declines to describe",
    Clear.NO_SINGLE_LANE: "its table names zero or two lanes; there is no one key to seal under (W-1)",
    Clear.CHAIN_MATERIAL: "chain material; composes() requires the chain to verify after the key is destroyed",
}


@dataclass(frozen=True)
class Disposition:
    """One column's at-rest decision, with every exclusion that produced it."""

    table: str
    column: str
    data_class: str
    rung: str
    sql_type: str
    exclusions: Tuple[Clear, ...]

    @property
    def sealed(self) -> bool:
        """Sealed iff nothing excluded it. An empty tuple is the whole rule."""
        return not self.exclusions

    @property
    def reason(self) -> str:
        if self.sealed:
            return (f"{self.rung} {self.sql_type} in a table naming one lane and "
                    "no chain: sealed at rest, per lane, before INSERT")
        return "; ".join(WHY[e] for e in self.exclusions)

    def __str__(self) -> str:
        state = "SEALED" if self.sealed else "clear"
        return f"{self.table}.{self.column} [{self.data_class}/{self.rung}] {state} — {self.reason}"


# --- reading the DDL --------------------------------------------------------


#: A `CHECK` that exists **because** a column was sealed, and is therefore not
#: evidence that it should not have been. Two shapes, both structural:
#: an expression naming an envelope column, and a bare `(x IS NULL)` tombstone.
_TOMBSTONE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s+IS\s+NULL\s*$", re.I)


def _is_sealing_constraint(expression: str) -> bool:
    if _TOMBSTONE.match(expression):
        return True
    return any(name.endswith(tuple(f"_{s}" for s in ENVELOPE_SUFFIXES))
               for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression))


def _checked_columns(body: str) -> frozenset:
    """Every column name appearing inside a `CHECK (...)` on this table.

    Paren-balanced rather than line-based, for `tools/registry.py::columns`'s
    reason: a multi-line CHECK read a line at a time yields fragments, and here
    a fragment would silently drop a column out of the exclusion.

    The seal's own constraints are skipped — see the module docstring's
    `EVALUATED_BY_DDL` entry for the circularity that forced this.
    """
    names = set()
    for m in _CHECK.finditer(body):
        depth, i = 1, m.end()
        while i < len(body) and depth:
            if body[i] == "(":
                depth += 1
            elif body[i] == ")":
                depth -= 1
            i += 1
        expression = body[m.end():i - 1]
        if _is_sealing_constraint(expression):
            continue
        names.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression))
    return frozenset(names)


def _lane_columns(body: str, table: str) -> Tuple[str, ...]:
    """The `NOT NULL` columns of this table that name one lane.

    `lane` itself counts through its own primary key: a `lane` row *is* the
    lane, so there is a key for it even though it references nothing.
    """
    if table == "lane":
        return ("lane_id",)
    return tuple(name for name, rest in _registry.columns(body).items()
                 if _LANE_REF.search(rest) and re.search(r"\bNOT\s+NULL\b", rest, re.I))


def _sql_type(rest: str) -> str:
    return (rest.split() or [""])[0].lower()


def _is_key(name: str, rest: str, body: str) -> bool:
    if re.search(r"\b(PRIMARY\s+KEY|UNIQUE|REFERENCES)\b", rest, re.I):
        return True
    # A table-level PRIMARY KEY (`field_classification`) names its columns in a
    # constraint line rather than beside the column.
    m = re.search(r"\bPRIMARY\s+KEY\s*\(([^)]*)\)", body, re.I)
    return bool(m and name in [c.strip() for c in m.group(1).split(",")])


@lru_cache(maxsize=8)
def plan_over(sql: str) -> Tuple[Disposition, ...]:
    """The disposition of every classified column in **this** schema text.

    Taking the text rather than reading the directory is what makes the fixed
    point checkable: `tests/test_sealing_plan.py` runs this over the migrations
    *before* the sealing one and requires the same sealed set, so a derivation
    perturbed by its own output goes red instead of looking derived.
    """
    seed = _registry.classified(sql)
    bodies = _registry.tables(sql)

    out = []
    for (table, column), (data_class, rung) in sorted(seed.items()):
        body = bodies.get(table, "")
        cols = _registry.columns(body)
        rest = cols.get(column, "")
        sql_type = _sql_type(rest)

        exclusions = []
        if not at_least(Rung[rung], DERIVE_AT):
            exclusions.append(Clear.RUNG_BELOW_L3)
        if _is_key(column, rest, body):
            exclusions.append(Clear.KEY)
        if sql_type.startswith(("timestamp", "date", "time")):
            exclusions.append(Clear.TEMPORAL)
        if column in _checked_columns(body):
            exclusions.append(Clear.EVALUATED_BY_DDL)
        if sql_type != CONTAINER_TYPE:
            exclusions.append(Clear.NOT_A_CONTAINER)
        if len(_lane_columns(body, table)) != 1:
            exclusions.append(Clear.NO_SINGLE_LANE)
        if _CHAIN_COLUMNS & set(cols):
            exclusions.append(Clear.CHAIN_MATERIAL)

        out.append(Disposition(table, column, data_class, rung, sql_type,
                               tuple(exclusions)))
    return tuple(out)


# --- what the rest of the store asks ---------------------------------------


def plan() -> Tuple[Disposition, ...]:
    """Every classified column with its at-rest disposition, table then column."""
    return plan_over(_sql())


def sealed_columns() -> Tuple[Tuple[str, str], ...]:
    """`((table, column), …)` — the columns that seal. Derived, never declared."""
    return tuple((d.table, d.column) for d in plan() if d.sealed)


def sealed_in(table: str) -> Tuple[str, ...]:
    return tuple(c for t, c in sealed_columns() if t == table)


def is_sealed(table: str, column: str) -> bool:
    return (table, column) in sealed_columns()


def lane_column(table: str) -> str:
    """The one lane column of a sealable table — the row's key, by name.

    Raises for a table with no single lane, because a caller asking which key to
    seal a two-lane row under has asked a question W-1 has no answer to.
    """
    sql = _sql()
    found = _lane_columns(_registry.tables(sql).get(table, ""), table)
    if len(found) != 1:
        raise ValueError(
            f"{table} names {len(found)} lane(s) and a sealed row is sealed "
            "under exactly one lane key (W-1: one lane, one key)")
    return found[0]


def envelope_columns(column: str) -> Tuple[str, ...]:
    """The columns migration 004 adds for one sealed column, in order."""
    return tuple(f"{column}_{s}" for s in ENVELOPE_SUFFIXES)


def all_envelope_columns() -> Tuple[Tuple[str, str], ...]:
    return tuple((t, e) for t, c in sealed_columns() for e in envelope_columns(c))


def main(argv=None) -> int:
    """`python3 store/sealing_plan.py` — the decision, column by column."""
    rows = plan()
    for d in rows:
        print(("  " if d.sealed else "     ") + str(d))
    n = len(sealed_columns())
    print(f"\n{n} of {len(rows)} classified column(s) seal at rest")
    # A derivation that seals nothing is vacuous, and a vacuous scan is not a
    # passing one (rule 13) — the same exit tools/drivers.py uses.
    return 0 if n else 2


if __name__ == "__main__":
    raise SystemExit(main())
