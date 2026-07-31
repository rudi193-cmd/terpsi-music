"""The store: the one place in this tree that writes, and the only one.

`docs/PLAN-STORE.md` is the specification and this package is **S-1, the
spine** — the roles, the migration runner, the error-channel adapter, the
same-transaction narration and the draft-write path — **plus S-2's session
identity** (`session.py`). Everything in `records/` decides over rows a caller
supplies; nothing there persists. This is the artifact where five finished
mechanisms meet, and the plan exists because retrofitting any of them is the
expensive direction.

**Why this package is outside `records/`, stated once here.** `records/` is
predicates: zero writes, zero egress, held there by `tools/purity.py` and
reported by `tools/conform.py`. `store/` is the declared exception, and the
declaration *is* gate G-C — `manifest.json`'s `write_paths` and `outbound`
entries, reconciled against this tree by `tools/manifest.py` in the same commit
that this package lands. A write path that nothing declares fails the build
without anybody remembering to check, which is the only version of that check
that survives a tired afternoon (§16, rule 12).

**What S-1 does not do**, so that the gaps read as scope rather than as
oversight:

* **~~No row-level security.~~ Landed with S-2, 2026-07-31**, as
  `migrations/003_row_security.sql` and `session.py`. The seal is compiled at
  the cluster and the rest of `serve()` is not — the migration's header says
  which halves, and `tests/test_store_differential.py` is the middle that keeps
  the two implementations honest. **This package still re-implements no
  predicate**: `session.py` names who is acting and the policies do the rest,
  so there is exactly one read predicate in Python and it is not here.
* **No sealing.** `records/atrest.py`'s per-lane keys, the escrow disposition
  and R16's fuse are S-3. Writes here land as **drafts** in the clear, which is
  correct for the cascade and incomplete for the plan.
* **No surface.** S-4 is the first vertical over real data.
* **No ending.** The app role holds `INSERT` and `SELECT` and nothing else, so
  setting `invalid_at` — refusal 3's only ending — is not reachable through
  this package yet. It belongs with the act that performs it and is named here
  rather than left to be discovered.

**Read order, if you are new to it.** `roles.py` (who may do what), then
`migrate.py` (how the schema gets there), then `session.py` (who is acting, and
for how long), then `reading.py` (why an errored read is not an empty one), then
`narration.py` (why a read and its disclosure entry commit together or not at
all), then `writing.py` (why an unclassified column cannot be inserted into).
"""

from __future__ import annotations

from .classification import UnclassifiedColumn, carries, registry_columns
from .connecting import APP_ROLE, OWNER_ROLE, app_dsn, connect, owner_dsn
from .migrate import (Applied, MigrationModified, MigrationOutOfOrder, Plan,
                      PlanState, apply_all, discover)
from .narration import (NarrationWithoutRead, Narrated, Passage, narrate,
                        project, serve_field, unproject)
from .reading import ReadState, Reading, StoreUnavailable, read
from .roles import ensure_roles
from .session import GUC, NoPrincipal, acting, name_principal, principal_of
from .writing import SealStateRefused, insert_draft

__all__ = [
    "APP_ROLE", "GUC", "OWNER_ROLE", "Applied", "MigrationModified",
    "MigrationOutOfOrder", "NarrationWithoutRead", "Narrated", "NoPrincipal",
    "Passage", "Plan", "PlanState", "ReadState", "Reading", "SealStateRefused",
    "StoreUnavailable", "UnclassifiedColumn", "acting", "app_dsn", "apply_all",
    "carries", "connect", "discover", "ensure_roles", "insert_draft",
    "name_principal", "narrate", "owner_dsn", "principal_of", "project",
    "read", "registry_columns", "serve_field", "unproject",
]
