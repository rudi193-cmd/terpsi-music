"""The bridge from the write path to the classification registry.

**This module is a middle, and it is named as one (rule 12).** The registry is
`tools/registry.py` — which already reconciles three things that could disagree:
the seed in `migrations/001_lanes.sql`, `records/classify.py`'s procedure, and
`docs/SENSITIVITY.md`'s class-to-rung table. A fourth copy of the mapping inside
the store would be the pair that file exists to close, so nothing here decides a
rung, a class, or whether a column is classified. It asks.

**What the write path needs from it**, and nothing more: *does this table carry
this column in the registry?* An `INSERT` into a column the registry does not
know about is refused at the adapter with the registry cited, because
`docs/SENSITIVITY.md`'s rule is that an unclassified field is a build failure
rather than a default — and the store is where a column first stops being a
build artefact and starts being a place a fact about a child is kept.

**Read from the migration text, not from the live `field_classification` table**,
and the choice is deliberate. The table is the seed's *effect*; the migration is
its cause. A row deleted from `field_classification` in a live cluster would
silently widen what the store accepts, whereas the migration is in the tree, is
checksummed by `store/migrate.py`, and is the thing CI already reconciles.

**Every migration, not the first one.** Until 004 the schema was one file and
nothing distinguished *the first migration* from *the schema*; 004 adds columns
and seeds their classification, so a reader stopping at 001 would refuse writes
to columns that exist and are classified. `tools/registry.py::schema_text` is the
one place the files are composed — three concatenations of `migrations/*.sql`
would be three chances to believe in three different schemas.

The cluster's copy is checked against this one by
`tests/test_store_writing.py::test_the_registry_the_adapter_reads_is_the_one_in_the_cluster`,
so the two cannot drift without something going red.

Stdlib only. No database.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import registry as _registry  # noqa: E402 — the source of truth, called not copied

MIGRATIONS = ROOT / "migrations"


class UnclassifiedColumn(ValueError):
    """An `INSERT` naming a column the classification registry does not carry.

    Not a `KeyError`: the caller did not ask for something missing, the caller
    tried to *store* something whose sensitivity nobody has decided. Rung and
    class govern serving and egress respectively, so a column with neither
    cannot be served safely or exported safely, and the write is the last moment
    at which that is cheap to refuse.
    """


@lru_cache(maxsize=1)
def _seed() -> Dict[Tuple[str, str], Tuple[str, str]]:
    """`{(table, column): (data_class, rung)}`, parsed by `tools/registry.py`."""
    return _registry.classified(_registry.schema_text(MIGRATIONS))


def registry_columns() -> Tuple[Tuple[str, str], ...]:
    """Every `(table, column)` the registry carries. Enumerable, so it is reviewable."""
    return tuple(sorted(_seed()))


def carries(table: str, column: str) -> bool:
    """Whether the registry classifies this column."""
    return (table, column) in _seed()


def classification_of(table: str, column: str) -> Tuple[str, str]:
    """`(data_class, rung)`, or `UnclassifiedColumn` — never a default pair."""
    try:
        return _seed()[(table, column)]
    except KeyError:
        raise UnclassifiedColumn(
            f"{table}.{column} is not in the classification registry "
            f"({MIGRATIONS.relative_to(ROOT)}/'s seeds, parsed by "
            "tools/registry.py). "
            "docs/SENSITIVITY.md: an unclassified field is a build failure, not "
            "a default — there is no rung to serve it by and no class to govern "
            "its egress") from None


def tables() -> Tuple[str, ...]:
    """The tables the registry knows. A write to any other is refused."""
    return tuple(sorted({t for t, _ in _seed()}))
