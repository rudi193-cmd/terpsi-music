# PLAN-ASSIST — §9 item 11: local agent assistance, behind the gate

`docs/ARCHITECTURE.md §9` item 11 is *"Local agent assistance behind the gate."*
The domain surface is capability-map **§19 Insight and Assistance**, whose first
line is the whole constraint: *"All of this runs behind the egress gate on local
models, since nearly every input is `PII_MINOR` or `MEDIA_MINOR`."* This phase
builds the **gated assistance seam** plus one representative capability that
exercises it end to end — not the full §19 breadth.

**The two hard clauses this phase exists to enforce:**
- **Refusal 1 / §6:** anything touching `PII_MINOR`/`PII_GUARDIAN`/`HEALTH`/
  `FINANCIAL`/`MEDIA_MINOR` is answered by a **local** model; a non-local answer
  or a stopped local model is refused **loudly**, never a served answer.
- **Rule 10 / §8.2:** a machine answer is a **`draft` until a named human seals
  it**; rejections are recorded as durably as approvals; a machine draft is never
  shown as a human's judgment, and never the input to an unattended loop.

---

## What already exists, and is reused rather than rebuilt (§16)

| Need | Reused from | Note |
|---|---|---|
| Local-only inference gate | `records/inference.py` | `through(call, *, classes, endpoint, rung)` / `accept(pair, …)` → `Answer`. A non-local provider is `NonLocalInference`; a stopped local model is `LocalModelUnavailable`; an untagged call is `Unclassified`. The forbidden state is unrepresentable (`Answer.__post_init__`). **This module builds no request** — the caller closes over its own model/prompt; assistance does the same. |
| Draft → human seal | `records/sealing.py` | `draft()`, `authored_by()`, `seal(rec, *, by, at)`, `reject(rec, *, by, at, reason)`, `State`, `Record`. Rule 10, with rejection as durable as approval, and I-7 (a record of the exercise is undeletable). |
| Machine remark as unsealed draft | `records/commentary.py` | `capture(anchor, body, by=…)` lands a `Remark` as an unsealed draft attributed to the machine; `refuse_standing_score` (SA-3); `compare` refuses ranking two remarks. |
| Which inputs force local | `records/classify.py` | An input's classes/rung decide whether refusal 1 binds — derived, not asserted. |
| Entitlement gate | `records/serving.py` (one lane) / `records/aggregate.py` (cross-lane, already suppressed) | Assistance serves only entitled data; cross-lane summaries go through the aggregate door, not a new one. |

---

## Slices

Each slice names the forbidden act its acceptance test attempts (rule 19).

### A-1 — the gated assistance call

Every assistance model call routes through `records/inference.through` with the
input's `classes` (from `classify`) and a **local** endpoint. There is no path
that reaches a model without that vetting, and no `fallback`/`allow` parameter.
A non-local provider, a bare-string return that dropped its provider label, or a
stopped local model each surfaces as its own refusal — never a served answer, and
never an empty answer a surface could render as *"no findings"* (rule 13).

**Forbidden act:** an assistance call that reaches a cloud provider (or whose
local model is down) returns a usable answer. The test drives a non-local pair
and a raising local call and requires the refusal, not a string.

### A-2 — the machine draft

Assistance output lands as a **`draft`** through `records/sealing.py` /
`records/commentary.py`, attributed to the machine, sealable or rejectable only
by a **named human**. A rejection is recorded as durably as a seal (an audit
trail that logs only agreement is not one). The draft is never returned in a
shape a surface would render as a human's sealed judgment.

**Forbidden act:** a machine answer served as a sealed record with no human in
the chain. The test requires the result is a `draft` in state `PENDING`, and that
sealing needs a named human.

### A-3 — no unattended loop

A machine draft cannot be the sealing input to another machine call without a
human signature in the chain (§8.2: *"No artifact is sealed by a chain containing
no human signature."*). And **a student's own draft is never the input to an
unattended loop** — iterating a fourteen-year-old's draft is the harm this
refuses.

**Forbidden act:** feeding a machine (or a student) draft back into assistance to
seal itself. The test attempts the loop and requires it cannot close without a
human seal between iterations.

### A-4 — behind the entitlement gate, and no scores

Assistance operates only on data the principal is entitled to: one lane through
`serve`, cross-lane only through the `aggregate` gate (which already suppresses
small cells). No standing cross-context score of any student or staff member
(SA-3, refusal 4); no priority computed between two students (W-7, refusal 6) —
assistance **presents**, a human decides.

**Forbidden act:** an assistance output that ranks two students, or carries a
durable score between contexts. The test requires the refusal (reuse
`commentary.refuse_standing_score` / `compare` and the W-7 refusal).

---

## Acceptance (the ones that must be able to fail — rule 19)

1. **Local-or-loud.** A non-local provider and a stopped local model both refuse;
   neither returns a usable string. Ablated.
2. **Draft, not answer.** Assistance output is a `PENDING` draft; a seal requires
   a named human; a rejection lands as durably as a seal. Ablated.
3. **No unattended loop.** A chain with no human signature cannot produce a
   sealed record; a student's draft is never an unattended-loop input. Ablated.
4. **No score, no priority.** Ranking two students or carrying a standing score is
   refused. Ablated.

## R16 note — assistance does not move the escrow fuse

Assistance drafts land through `records/sealing.py` / `records/commentary.py`
(the `records/` draft path), **not** `store/writing.py`'s record-write path, so
`tools/audit.py::durable_callers()` stays empty and R16 stays `FINDING`/`S2`.
If a slice writes a draft durably through the store, that is the boundary to
check — keep the assistance output in the `records/` draft machinery (as
commentary already does) rather than adding a store record-write. The build must
confirm R16 is still `FINDING`/`S2` with `durable_callers: ()` on the finished
tree.

## The representative capability (make it concrete, not the whole §19)

Build **one** capability end to end so the four slices are exercised on real
shapes: a **per-student longitudinal growth narrative** — capability-map §19,
*"longitudinal growth narratives for conferences, drafted from real data"* —
one student (one lane, W-1), drafted by a local model through A-1, landed as a
`draft` through A-2, refused as an unattended loop through A-3, and carrying no
score through A-4. It is the capability that touches the most clauses at once.

## Deferred deliberately — tombstones (§16 rule 20)

| Deferred | Why | Successor |
|---|---|---|
| The model deployment / client | The app ships no model; `inference.through` takes a `call` closure the deployment provides | An install/ops concern, not this repo's commit |
| The rest of §19 (rehearsal & commentary summarization, program notes, newsletter) | One representative capability proves the seam; breadth is repetition | Later capability commits, each behind the same gate |
| Scaffold-withdrawal proposal flow (W-5 *surfaces the case, a human signs*) | Its own decision surface | A later commit; A-4's no-score rule is the piece of it that lands now |
| Draft-to-draft diff (§19) | A craft surface, not the gate | Later |

Nothing above is excused — each is a named middle owed a later commit, not a gap.
