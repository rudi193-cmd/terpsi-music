# Handoff — 2026-08-01: §14 verification complete, the retention purge built

**Status at handoff.** Branch `claude/coat-hat-check-p6obau`, HEAD `2d00f1a`,
**clean and synced with origin, green on CI** (both the `guards` and `schema`
jobs). Nothing uncommitted, nothing in flight. This document is a pointer to the
tree, not a second copy of it (§16); where it and the code disagree, the code
wins and this file is the defect.

A `§N` here means `docs/ARCHITECTURE.md`.

---

## What this session landed

Every item below is committed and pushed; figures are derived from the tree at
this HEAD (rule 17).

- **§14 fleet-component verification is complete — `41 of 41`** exists-rows
  verified at source, enforced by `tests/test_component_map.py`'s header-figure
  guard (it *derives* the count from the rows; a wrong marker fails). Started the
  session at 12. The pass ran through the GitHub API + `add_repo`, with one
  cross-owner repo (`almanac-template`) read over the public web. Five rows
  diverged from the prose and carry the correction **in-cell** (SAFE
  `HARD_STOPS` has no under-13 stop; `willow-compose` is not itself a family-data
  app; `private-ledger` is a shipped app not a template; `oakenscrolls-office`
  calibrates one user's forecasts not judges; `ask-jeles` persists more than
  claimed). Record: `docs/FLEET-READS.md` → *The pass, completed — 2026-08-01*.
- **Security audit re-pinned to `106ec13`** (`docs/SECURITY-AUDIT.md`), every
  figure re-derived from the tree. No rubric verdict moved; **R16 stays
  `FINDING`/`S2`** (it turns on an escrow rehearsal that is an install-acceptance
  act, §11.1, not a commit — see below).
- **§9 item 9 (Adjudication) was already built; its marker was stale.**
  `records/commentary.py` has carried the whole vertical since 2026-07-31 (the
  `Remark` primitive, `fan_out`, the SA-3 refusal, the guest session with its
  §7.2 exit reconciliation, and the transcription seam), held by 74 tests. Only
  the §9 line lacked its "built" annotation; that is now fixed. **A dispatched
  worktree builder reinvented a worse subset from a stale base and was discarded
  — see the worktree gotcha below.**
- **§9 item 8's season-boundary retention purge is built** —
  `records/retention.py` (new). A purge here is **crypto-erasure plus a durable
  dated tombstone, never a delete** (refusal 3): it owns the *when* (a predicate
  over `season` + the three dates: which records a boundary has carried past a
  caller-supplied horizon) and delegates the *how* to `records/atrest.py`'s
  per-subject `destroy()`, which leaves an `Erasure` row that outlives what it
  erased. Refusals, each with a test that attempts the act and a mutation in
  `tests/ablate.py` (all shown to fail): no early/live-record purge (`NotDue`);
  the record of a purge is not itself purgeable (`Indelible`, rule 16); a
  seasonless record or unknown kind fails closed (rule 13); `purge()` drives
  only dated dispositions (rule 15); a naive datetime is refused cleanly, not a
  raw `TypeError`. **No retention *period* is shipped** — durations come from the
  caller, as item 10 refused a default `k`. Held by `tests/test_retention.py`
  (**15 tests**). Audited clean (SHIP, no findings) — the audit was run **inline**
  because the async agents kept dying to the container churn (below).

Design note carried in the code: `records/retention.py` is **not** re-exported
from `records/__init__.py` on purpose — its names (`Disposition`, `Assessment`,
`Standing`, `assess`) already mean other things in the package, so it is
addressed module-qualified (`records.retention.X`).

---

## Build state — §9, at this HEAD

Read §9 for the full text; the one-line status:

| # | Capability | State |
|---|---|---|
| 1 | Person/relationship graph, time-boxed edges | enforcement half built; the store-side resolver / authenticate-at-the-read (#127) is still to write |
| 2 | Data classification on every field | built, enforced twice, reconciled by `tools/registry.py` (3 fields `UNKNOWN` — a recorded finding, not a pass) |
| 3 | Envelope + key hierarchy | chain integrity + per-subject erasure built; at-rest sealing across Zone A is R16 (below) |
| 4 | Egress purity in the core | built, AST-proven |
| 5 | Append-only audit log | built (hash-chained disclosure log + count-anchor) |
| 6 | First vertical module | `venue/` built |
| 7 | Parent PWA + the drop | in-repo drop-producer built; hosted relay / PWA client / SMS gateway tombstoned |
| 8 | Money/inventory/forms/calendar | attendance + fees + **the retention purge** built; **inventory, forms, calendar still open** |
| 9 | Adjudication | **built** (`records/commentary.py`) — marker corrected this session |
| 10 | Aggregate exports | built (`records/aggregate.py`) |
| 11 | Local agent assistance | built (`records/assistance.py`) |

Tree size at HEAD: 29 `records/*.py`, 69 `tests/test_*.py`, 472 ablation
mutations (all derived).

---

## What is open — pick up here

1. **§9 item 8 remainder — the inventory and forms models, and the calendar.**
   Both are `records/` predicates over caller-supplied rows, like everything
   else there; forms (medical/consent) touch `HEALTH`/`PII_GUARDIAN` and are the
   higher-value half. No plan doc exists for either yet.
2. **§9 item 1 completion — the store-side resolver / authenticate-at-the-read
   predicate** (§7's resolver shape, #127). The store now exists, so this is
   buildable; it is foundational plumbing rather than a user-facing capability.
3. **R16 — the escrow rehearsal.** Not code: an install-acceptance act (§11.1).
   R16 becomes an open `S1` (build-failing) at the first non-test caller of the
   store's **record-write** path unless `docs/ESCROW.md` carries a dated
   rehearsal by then. The retention purge does **not** trip this — it drives
   `atrest.destroy`, not `store/writing.py`.
4. **The scale-direction / trust-column caveat** in `docs/SENSITIVITY.md` — the
   Rookie/Steady/Veteran → `T1`/`T2`/`T3` numbering was never checked against
   `willow-gate`; the one §14-adjacent reading the verification pass did not
   settle.

Read `§18` (the open list) and `§14`'s component map before starting.

---

## Gotchas — read before you build

- **The container reverted to snapshot `7a71d79` three times this session.**
  Each revert silently restored an old tree **plus** a `records/atrest.py`
  mutation that leaks key material in `MasterKey.__repr__`
  (`material=<withheld>` → `material={self.material!r}`) — stale ablation debris.
  **Never commit it.** Recovery: `git fetch origin claude/coat-hat-check-p6obau
  && git reset --hard origin/claude/coat-hat-check-p6obau`, then
  `rm -f .ablate-lock .ablate-inflight.json`. Your work is safe on origin — push
  after every commit and the revert costs nothing.
- **`isolation: "worktree"` branched a builder from `d2817f2`** (an ancient
  commit, before the store and dependencies existed), not from HEAD. The agent
  then rebuilt existing modules from scratch and its output was unmergeable.
  **Verify a builder's base commit before trusting its output, or build inline.**
- **A running ablation legitimately mutates files.** `tests/ablate.py` mutates a
  source line, runs a test, and restores — so a stop mid-run shows "uncommitted
  changes" that are *not* debris. Check `ps` for a live `ablate.py` and the
  `.ablate-lock`/`.ablate-inflight.json` timestamps before deciding a change is
  debris vs. an in-flight mutation. Do not `git restore` under a live ablation.
- **The §14 `VERIFIED-COUNT` marker and its ablate mutation are coupled.** When
  the count changes, the `tests/ablate.py` row that watches it
  (`"VERIFIED-COUNT: N of M"`) must move with it, or the `test_ablate` meta-test
  goes red. This drift broke CI once this session.

## How to confirm the state yourself

```
git status --porcelain            # empty = clean
git rev-parse HEAD                 # == origin/claude/coat-hat-check-p6obau
grep material= records/atrest.py   # both must read material=<withheld>
python3 tests/test_retention.py    # 15 ok
python3 -m pytest tests/test_component_map.py -q   # §14 count guard
```

---

*Canonical docs: `docs/ARCHITECTURE.md` (§18 open list, §14 component map),
`docs/CAPABILITY-MAP.md`, `docs/SENSITIVITY.md`, `docs/LANE-MODEL.md`. Plan docs
for built verticals: `docs/PLAN-STORE.md`, `docs/PLAN-DROP.md`,
`docs/PLAN-ASSIST.md`. The verification ledger: `docs/FLEET-READS.md`.*
