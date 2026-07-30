# Build plan

**Status:** plan. Governs nothing; `docs/ARCHITECTURE.md` governs. No numbered
sections — a `§N` here is always the architecture's.

**One page on purpose.** If this file grows past two screens it has stopped
being a plan and become another thing to read. Everything here points at a
decision or a task; it never restates a mechanism.

**Pruned 2026-07-30.** Earlier revisions accumulated struck blocks under the
tombstone discipline until the file argued against its own first rule.
`willow-grove/DESIGN_CONSTRAINTS.md` settles the tension: *"when a constraint
stops being relevant, delete it and say why in the commit message — a stale
constraint is worse than none, because it trains people to skip the list."* The
removed material is in `docs/FLEET-READS.md` and in §18's own tombstones, which
is where it belongs.

---

## Are the ducks in a row

**No. The decisions largely are; the build is not, and one item blocks
outright.**

### Blocking the first commit

| | | |
|---|---|---|
| **B3** | item 4 — which surfaces exist | **Deferred, in hand elsewhere.** Nothing about the first commit's layout is decidable until it lands. This is the only item that blocks rather than merely waits |
| **item 3** | the lane DDL leaves `docs/schema/` | One gate cleared, one opened — see below |
| **item 5** | the exit line | §11.1 requires it **before the first install**. It does not exist |

**Item 3 moved sideways rather than forward.** Reading Part III at source
cleared the *"rests on a paraphrase"* gate — and opened a new one. W-3 requires
*"a guardian-signed envelope naming both lanes, purpose, and expiry"*, and no
such table exists among the twelve. The prohibition is encoded; the permission
is not, so a legitimate sibling crossing is **unrepresentable**, not merely
ungated. A thirteenth table is needed before promotion, and item 4 still gates
it either way.

### One thing that got worse on 2026-07-30, not better

- **The foundation is emptier than §9 claimed.** Items 1 and 2 were marked
  *built* on the spike's authority. The spike retires and nothing is inherited,
  so both are **to build**.
- ~~**`field-acoustics` does not exist.**~~ **Withdrawn 2026-07-30 — it does.**
  `apps/field-acoustics` is in `safe-app-store` with a correct catalog path, as
  are the other seven names reported absent alongside it. The earlier claim
  searched for standalone repositories; the fleet keeps apps inside the store.
  §9 foundation 6 points at something real. See `docs/FLEET-READS.md`.

### One live hazard with no answer yet

Refusal 1 forbids a cloud inference fallback. **Corrected 2026-07-30 after
re-deriving the tallies** — the first account of this was wrong in the
maintainer's favour and the real shape is more tractable.

`willow-2.0/core/inference_router.py` reads
`os.environ.get("WILLOW_INFERENCE_PROVIDER", "auto")`, and `_chain("local")`
returns Ollama and nothing else. **So an off-switch exists** — refusal 1 already
names the variable verbatim — **and the default is `auto`**, which means the
chain is fail-open when unconfigured rather than undisableable. The providers
appear in 24 Python files, and the two documented chains disagree with each
other, so "we will not use `willow-seed`" remains insufficient.

**The tractable part:** `respond()` returns `(response_text, provider_used)`.
Refusal 1 can therefore be enforced **by assertion** — require
`provider_used == "ollama"` and fail otherwise — rather than by trusting an
environment variable to have been set. That converts it from a deployment note
into something testable, and is the shape to build.

### Where the tree actually stands

```
migrations/   ABSENT — the DDL is still in docs/schema/
surface dir   none
craft/        text-only: no student data, no network, no model
voice.py      enforcement-ready, routed through nothing
```

Nothing here touches student data yet. That is correct for this stage, and it
means *ready for the build* should be read as **ready to start it**.

---

## What is settled

Four §18 items closed 2026-07-30 — 1, 1a, 2 and 11 — each struck in place with
its resolution. `docs/SENSITIVITY.md` is canonical for the ladder, *Protected
status*, and the scoped `L3`+ NULL reading. §14 carries a per-row
`VERIFIED`/`UNVERIFIED` state enforced by `tests/test_component_map.py`, and 27
fleet repositories have been read.

**The lesson worth carrying out of that pass**, because it will recur: item 1a
was filed as the highest-value *read* in the item-0 sweep and was not a read at
all. It was sourced to a spike, and **a claim sourced to a spike is a decision
nobody has taken yet, wearing the costume of a fact.** Some of §14's thirty
remaining `UNVERIFIED` rows are the same shape; opening the files will not fix
those.

## Buildable today

| | task | depends on |
|---|---|---|
| C1 | Extend `craft/` | nothing — text-only, no student data, no network, no model |
| C2 | Sweep `docs/survey/*.md` for `§N` | needs the routing decision in `scout-25` part 5 first |
| C3 | A rule-13 acceptance test | nothing. `willow-grove`'s constraint 1 supplies the shape — point a reader at an unreachable source in CI and assert no surface reports health. Rule 13 has **no test here** |
| C4 | The crossing-envelope table | nothing blocks *designing* it; adoption still waits on item 4 |

Short, and the shortness is the finding. **This repository is decision-blocked,
not effort-blocked** — and the instinct to build C in parallel should be
resisted for anything downstream of layout. `docs/PLAN-GUARDIANSHIP.md` is the
worked example: eleven acceptance gates, fully specified, unbuildable until B3
says what a surface is.

## Order

1. **B3** — surfaces. Everything about layout waits on it.
2. **The crossing-envelope table**, then item 4 clears the DDL into `migrations/`.
3. **The exit line**, before anything installs.
4. **Decide the refusal-1 inheritance question** before any inference path is written.
5. Then §9's list in its existing order — noting foundations 1 and 2 are **to build**.

## What this plan deliberately does not do

- **Does not re-order §9.** Its ordering principle — expensive-to-retrofit first
  — is sound. What was wrong is its *status labels*, and those are corrected in
  place.
- **Does not schedule.** No dates: the blocking item is someone else's
  keystrokes and estimating it here would be fiction.
- **Does not restate a mechanism.** Every row points at the document that owns
  it. If a mechanism appears described here, that is a defect (§16).
