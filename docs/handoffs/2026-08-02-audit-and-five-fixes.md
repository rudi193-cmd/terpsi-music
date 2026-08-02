# Handoff — 2026-08-02: an audit of the branch, and the defects it found

**Status:** continuity record. Governs nothing; `docs/ARCHITECTURE.md` governs,
and `docs/CROSSINGS.md` is the findings record this indexes.

**State at handoff.** Branch `claude/coat-hat-check-p6obau`, HEAD `e266806`,
clean and synced with origin. All 487 guards in `tests/ablate.py` ablate red and
20 of 21 in `tests/ablate_store.py` do, the twenty-first being the declared
survivor its own table pairs. This document is a pointer to the tree, not a
second copy of it (§16); where it and the code disagree, the code wins and this
file is the defect.

A `§N` here means `docs/ARCHITECTURE.md`.

---

## What this session did

It did not build a capability. It **audited the branch for one defect shape** —
*a refusal that is real and does not cover the act it is attached to* — and
fixed what it found — the table below is the whole list, one of them high.
Findings and the patterns under them are in `docs/CROSSINGS.md`, three addenda
dated 2026-08-02; this section is the index, not the record.

| # | Where | What | Commit |
|---|---|---|---|
| 1 | `records/retention.py` | A record-scoped refusal driving a lane-scoped erasure. A `Disposition` for one aged-out attendance record destroyed the key opening the same student's **live** medical note. Reproduced against `lane_entry` with the migrations applied | `8bcfa6c` |
| 2 | `tests/test_rule13_acceptance.py` | The seam inventory was the only authority on its own completeness. Its middle walked `SEAMS` and asserted a test per row; nothing walked the tree and asserted a row per seam | `e266806` |
| — | `craft/` | The seam the inventory was blind to, carrying the exact defect under rule 13 that the sweep exists to prevent: `findings (0)` under an *unavailable* banner, and a `run_diff` that cleared every finding by comparing against a draft it could not read | `d89d6a1` |
| 3 | `store/roles.py` | `RoleState.app_privileges` filled from a module constant under a docstring reading *"Reported, not assumed"* — and false at construction, since `apply_grants` runs after `ensure_roles` | `019877a` |
| 4 | `records/aggregate.py` | `CellResult.contributors` documented as *"what the announcement is written from"*; the announcement is written by `_announce` walking `readings` | `daf4eac` |
| 5 | `.gitignore` | `tests/ablate_store.py`'s lock and sidecar were untracked rather than ignored, so a mid-run `git add -A` would commit a 30 KB recovery record for a live mutation | `661b2fa` |

Findings 1, 3 and 4 were fixed by **removing the ability rather than forbidding
the act** — crossing one's prescription. `purge()` cannot express a
whole-student erasure any more; `RoleState` cannot report a privilege it never
read; `CellResult` has no field for an identifier to sit on.

Tree at this HEAD, every figure counted from the tree today: 29
`records/*.py`; 69 `tests/test_*.py`; 1,478 `test_*` functions, derived;
487 + 21 mutations, derived; `SEAMS` 43 rows and the sweep 84 tests, derived.

---

## What is open — pick up here

The four items from the 2026-08-01 handoff are **unchanged and still open**;
nothing in this session touched them. Read that file for their detail.

1. §9 item 8's remainder — the inventory and forms models, and the calendar.
2. §9 item 1 — the store-side resolver / authenticate-at-the-read (#127).
3. R16 — the escrow rehearsal. Not code; an install-acceptance act (§11.1).
4. The scale-direction / trust-column caveat in `docs/SENSITIVITY.md`.

This session added one:

5. **§18 item 19 — seal per `(lane, season)`.** The key-model fix that would
   make finding 1's refusal unnecessary. `atrest.destroy` filters on `lane_id`
   alone, so it does not narrow with rotation and every generation of a lane's
   key goes at once; giving a season its own key makes a whole-student erasure
   the explicit act it should always have been. It touches the wrapping identity
   in `records/atrest.py`, `store/sealing_plan.py`, `migrations/004`'s envelope
   columns, and escrow's key count.

   **It is also a schema gap, which the item records and is worth repeating
   here: there is no `season` column anywhere in `migrations/`.** The word
   appears in two SQL comments and nowhere else. The axis the whole retention
   predicate turns on is carried by the record types in `records/` and by
   nothing durable. Any work on item 19 starts there.

---

## Gotchas — read before you build

The 2026-08-01 handoff's gotchas still hold. These are new or newly confirmed.

- **`isolation: "worktree"` branches from `d2817f2`, and it is not
  intermittent.** The previous handoff recorded it once; this session hit it
  **three times out of three**, on every worktree agent dispatched. Every agent
  recovered only because its brief opened with an explicit base check. If you
  dispatch a worktree builder, make its first instruction
  `git rev-parse HEAD`, require a known-good commit, and
  `git fetch origin <branch> && git reset --hard origin/<branch>` otherwise.
  Verify a second time that the files the task needs actually exist.

- **PostgreSQL does not stay up in this container.** It went down twice
  mid-session with no obvious trigger. `service postgresql status`; if `down`,
  `service postgresql start` and wait a few seconds. The store suites behave
  correctly when it is gone — exit 2, `UNKNOWN`, *"No store test ran. That is
  not a pass (rule 13)"* — so a red store run is a cluster question first.

- **`cryptography` can be installed and still unusable.** The container shipped
  the pinned 41.0.7 via the system package manager with `_cffi_backend`
  missing, so every sealing path raised `PrimitiveUnavailable` — correctly and
  loudly, but it looks like a code failure. `pip install cffi` fixed it.
  `pip install -r requirements.txt` does not, because pip declines to reinstall
  the Debian-owned `cryptography`.

- **`tests/test_conform.py` shells out to the full `tests/ablate.py`.** Running
  the whole `tests/` directory therefore triggers a ~20-minute registry run. Run
  suites individually, or exclude that file, unless you mean it. If you start
  one by accident, `SIGTERM` the `ablate.py` process — its handler restores the
  mutated file — and check for `.ablate-inflight.json` / `.ablate-lock` before
  committing.

- **Store suites cannot be parallelized against one cluster.** They run
  cluster-wide role DDL; concurrent runs fail with `tuple concurrently updated`.
  Serially, they pass.

- **A mutation row whose suite needs a cluster belongs in
  `tests/ablate_store.py`, never `tests/ablate.py`.** The latter derives its
  control list from its own mutations, so a cluster-dependent row there turns
  the no-database `guards` CI job red.

- **`tests/test_retention.py` bans the substring `"del "` in
  `records/retention.py`,** to prove the module never deletes. The word
  *model* followed by a space contains it. Writing "key model change" in that
  module's prose fails the suite for a reason that has nothing to do with the
  test's subject.

- **Rule 17 is a merge-time obligation, not only a writing-time one.** Three
  mutation counts written correctly on parallel branches — 473, 478, 483 — were
  each stale the moment those branches merged. A figure derived from the tree
  you are standing on is still a claim about a tree that is about to change
  under you. Re-derive counts after every merge, and grep the docs for the old
  ones.

---

## How to confirm the state yourself

```
git status --porcelain                   # empty = clean
git rev-parse HEAD                        # == origin/claude/coat-hat-check-p6obau
grep material= records/atrest.py          # both must read material=<withheld>
service postgresql status                 # online, or start it
export TERPSI_TEST_DSN="host=localhost user=postgres password=postgres dbname=postgres"
python3 tests/test_retention.py           # 20 ok
python3 tests/test_rule13_acceptance.py   # 84 ok
python3 tests/ablate.py                   # ~20 min; all 487 red
```

---

*Canonical docs: `docs/ARCHITECTURE.md` (§18 open list, §14 component map),
`docs/CAPABILITY-MAP.md`, `docs/SENSITIVITY.md`, `docs/LANE-MODEL.md`. The
findings record for this session: `docs/CROSSINGS.md`, three addenda dated
2026-08-02. The previous handoff, whose open list is still current:
`docs/handoffs/2026-08-01-verification-and-retention.md`.*
