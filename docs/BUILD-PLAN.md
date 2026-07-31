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

### The item upstream of the rest

**Item 15 — who witnesses the anchor.** This repository exists because
institutions do not follow their own rules and nobody can prove it. Every other
mechanism assumes a record that is **believable later**, and a record its author
controls is weak evidence. The mechanism is built; the counterparty is not
chosen, and until it is, the rest is a very careful diary.

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

### The live hazard, built 2026-07-31

Refusal 1 forbids a cloud inference fallback. The assertion shape this section
argued for is now `records/inference.py`, with `tools/providers.py` watching for
a call site that skips it; `docs/CROSSINGS.md` is not where this belongs and
`§6` is where the rule lives, so this row is now a pointer.

**Four things this section's account of the upstream file got wrong or left
out**, found by opening it rather than by re-reading the note about it:

- **`core/llm_edge.py` is the more dangerous import**, and no plan here
  mentioned it. Its `respond()` calls the router, **discards `provider_used`**,
  returns a bare string, and on any exception falls through to Groq and then to
  Ollama inside two `except: pass` blocks. The assertion shape does not exist
  for a caller of that function — which is why an absent provider label is a
  refusal here and not a benefit of the doubt.
- **There is a fourth mode.** `_chain("hns")` returns `hns + local + cloud` and
  is absent from the file's own docstring; `_try_hns` posts the request to
  *another node's* Ollama. So "local" and "`ollama`" are not the same claim, and
  `OLLAMA_URL` can address another machine in the plain path too. The guard
  checks the address as well as the label.
- **The environment variable is not the only way in.** `chat()` takes
  `mode=`, which bypasses `WILLOW_INFERENCE_PROVIDER` entirely. An off-switch
  somebody can pass an argument around is a default, not a switch.
- **Removing keys from the environment is not severance.** `_load_key` falls
  back to `sap.core.inference.load_credential`, so the install-acceptance line
  *"no credential prefixes"* has to mean the credential store as well as the
  environment.

**One count corrected, and the correction is about method.** The *"providers
appear in 24 Python files"* figure — carried here until today and still in
`docs/FLEET-READS.md` — is not reproducible, because no pattern was recorded
with it. Re-derived 2026-07-31 with the pattern written down —
files under `willow-2.0` matching
`GROQ_API_KEY|OPENROUTER_API_KEY|GEMINI_API_KEY|api.groq.com|openrouter.ai|generativelanguage.googleapis.com`
— it is **21** of 848 `.py` files, or **17** excluding `archive/` and `tests/`.
Four files mention `inference_router`; nine mention `llm_edge`. A number without
its pattern is rule 17's own defect wearing a derivation's clothes.

### Where the tree actually stands

```
migrations/   ABSENT — the DDL is still in docs/schema/
surface dir   none
craft/        text-only: no student data, no network, no model
voice.py      ROUTED — records/dispatch.py runs it after the seal, before dispatch
records/      the read predicate — the first code here that decides about a person
inference     GUARD ONLY — refusal 1 asserted; no call site exists to route yet
```

**`records/` is the vertical slice, built 2026-07-30**, and it earned its keep
twice on the first day. Ablating each guard showed one mutant surviving — the
`L5` never-served check could be removed and the suite stayed green, because a
different rule caught the same field further down (`EXTERNAL-ARM.md`'s *"a gate
green because a different constraint was catching it"*). And implementing §7's
edge vocabulary faithfully revealed that **a student cannot read their own
record**, now §18 item 12.

Neither was findable by reading. Both took an afternoon.

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
| ~~C1~~ | ~~The vertical slice~~ | **Built 2026-07-30** — `records/serving.py`, the first code here that touches the domain. Found §18 item 12 |
| ~~C1b~~ | ~~The send predicate~~ | **Built 2026-07-30** — `records/sending.py`, G1–G11 of `PLAN-GUARDIANSHIP.md`. Found §18 item 13 and a missing `created_at` on `Edge` |
| ~~C1c~~ | ~~The classifier~~ | **Built 2026-07-30** — `records/classify.py`, `SENSITIVITY.md`'s five steps. Found §18 item 14 within minutes |
| C1 | Extend `craft/` | nothing — text-only, no student data, no network, no model |
| C2 | Sweep `docs/survey/*.md` for `§N` | needs the routing decision in `scout-25` part 5 first |
| C3 | A rule-13 acceptance test | nothing. `willow-grove`'s constraint 1 supplies the shape — point a reader at an unreachable source in CI and assert no surface reports health. Rule 13 has **no test here** |
| ~~C4~~ | ~~The crossing-envelope table~~ | **Built 2026-07-30** — `records/crossing.py`, wired into `serve()`. W-3's permission is representable at last |
| ~~C5~~ | ~~The disclosure log, seal cascade, dispositions, W-6 exit~~ | **Built 2026-07-30** |
| ~~C6~~ | ~~Route `voice.guard()`~~ | **Built 2026-07-30** — `records/dispatch.py`. `voice.py` is a gate rather than a ledger, and routing it found `no_rung` checking the wrong scale |
| ~~C7~~ | ~~Anchoring — where the anchor lives~~ | **Built 2026-07-30** — `records/witness.py`. §5 specified the anchor and never its custody. **§18 item 15** is the decision: who witnesses it |

Short, and the shortness is the finding. **This repository is decision-blocked,
not effort-blocked** — and the instinct to build C in parallel should be
resisted for anything downstream of layout. `docs/PLAN-GUARDIANSHIP.md` is the
worked example: eleven acceptance gates, fully specified, unbuildable until B3
says what a surface is.

## Order

1. **B3** — surfaces. Everything about layout waits on it.
2. **The crossing-envelope table**, then item 4 clears the DDL into `migrations/`.
3. **The exit line**, before anything installs.
4. ~~**Decide the refusal-1 inheritance question** before any inference path is
   written.~~ **Decided and built 2026-07-31** — nothing is inherited.
   `records/inference.py` asserts on `provider_used`; the environment variable
   stays an off-switch and is never the enforcement. The ordering held: the
   guard exists and there is still no inference path, so one cannot be born
   unguarded.
5. Then §9's list in its existing order — noting foundations 1 and 2 are **to build**.

## What this plan deliberately does not do

- **Does not re-order §9.** Its ordering principle — expensive-to-retrofit first
  — is sound. What was wrong is its *status labels*, and those are corrected in
  place.
- **Does not schedule.** No dates: the blocking item is someone else's
  keystrokes and estimating it here would be fiction.
- **Does not restate a mechanism.** Every row points at the document that owns
  it. If a mechanism appears described here, that is a defect (§16).
