"""The store: the one place in this tree that writes, and the only one.

`docs/PLAN-STORE.md` is the specification and this package is **S-1, the
spine** — the roles, the migration runner, the error-channel adapter, the
same-transaction narration and the draft-write path. Everything in `records/`
decides over rows a caller supplies; nothing there persists. This is the
artifact where five finished mechanisms meet, and the plan exists because
retrofitting any of them is the expensive direction.

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

* **No row-level security.** The compiled read predicate is S-2, with the
  differential middle against `records/serving.py`. This adapter *serves rows
  to* those predicates and does not re-implement them; there is exactly one
  read predicate and it is not here.
* **No sealing.** `records/atrest.py`'s per-lane keys, the escrow disposition
  and R16's fuse are S-3. Writes here land as **drafts** in the clear, which is
  correct for the cascade and incomplete for the plan.
* **No surface.** S-4 is the first vertical over real data.
* **No ending.** The app role holds `INSERT` and `SELECT` and nothing else, so
  setting `invalid_at` — refusal 3's only ending — is not reachable through
  this package yet. It belongs with the act that performs it and is named here
  rather than left to be discovered.

**Read order, if you are new to it.** `roles.py` (who may do what), then
`migrate.py` (how the schema gets there), then `reading.py` (why an errored
read is not an empty one), then `narration.py` (why a read and its disclosure
entry commit together or not at all), then `writing.py` (why an unclassified
column cannot be inserted into).
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
from .writing import SealStateRefused, insert_draft

__all__ = [
    "APP_ROLE", "OWNER_ROLE", "Applied", "MigrationModified",
    "MigrationOutOfOrder", "NarrationWithoutRead", "Narrated", "Passage",
    "Plan", "PlanState", "ReadState", "Reading", "SealStateRefused",
    "StoreUnavailable", "UnclassifiedColumn", "app_dsn", "apply_all",
    "carries", "connect", "discover", "ensure_roles", "insert_draft",
    "narrate", "owner_dsn", "project", "read", "registry_columns",
    "serve_field", "unproject",
]
