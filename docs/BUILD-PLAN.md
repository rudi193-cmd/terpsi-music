# Build plan

**Status:** plan. Governs nothing; `docs/ARCHITECTURE.md` governs. No numbered
sections — a `§N` here is always the architecture's.

**One page on purpose.** There are 14,332 lines under `docs/` at time of
writing, this file included — derived, not quoted (#17). If this file
grows past two screens it has stopped being a plan and become another thing to
read. Everything here is a pointer to a decision or a task, never a restatement.

---

## The fact that orders everything else

> **This section was built on a false premise and is struck, 2026-07-30.** It
> read `FLEET-READS.md`'s claim that the repositories were unreachable
> remotely, concluded that no remote session could ever verify §14, and split
> the entire plan around that. The repositories are on GitHub under the same
> account as this one, several public. Three were cloned from a remote session
> and four §14 rows are now verified. **The check was one tool call, and this
> plan re-organised a project rather than make it.**
>
> Kept struck rather than rewritten, because the shape of the error is the
> useful part: an infrastructure claim nobody tested became the organising
> principle of the work. That is the same failure as a claim sourced to a
> spike, one level up.

**What actually orders the work.** §9's foundation labels are still wrong —
items 1 and 2 rest on a spike that retires — but that is a correction anyone
can make from here, not a constraint. The real ordering principle is what is
*decided* versus what is *observed*, and the session that closed items 1a, 2
and 11 established that several things filed as reads were decisions nobody had
taken. Track A is now a working queue rather than a locked door.

---

## Track A — reads (no longer blocked)

Three reads. **All three are now performable from here**, and two are done.

| | task | closes | output |
|---|---|---|---|
| A1 | Open the 36 repos; confirm or downgrade every *Exists* row | item 0 | **In progress 2026-07-30** — 12 repos read, 10 §14 rows verified plus one verified *negative*, 24 unread. Tier 1 complete. Rows carry `VERIFIED <date> at <commit>` |
| ~~A2~~ | ~~Open `Willow`'s `PROTECTED_AGENTS.md` Part III~~ | item 3 | **Done 2026-07-30** at `c8c96b4`. §7.4 renders all seven clauses faithfully. Found: the DDL encodes W-3's prohibition and drops its permission — no crossing-envelope table |
| ~~A3~~ | ~~Read the `L3`+ NULL rule in `apps/marching-arts`~~ | item 1a | **Closed 2026-07-30 — scoped, decided not inherited.** It was never a read |

**A3 was not a Track A item and that is the lesson worth keeping.** It was
filed as the highest-value read in the item-0 pass because #112 was taken for
an implementation to consult. `marching-arts` was a spike, so opening the file
would have established what a prototype happened to do — a different question
from what the rule should be. **A claim sourced to a spike is a decision nobody
has taken yet, wearing the costume of a fact.** Worth carrying into A1: some of
the other 34 `Exists` rows are the same shape, and reading them will not fix
them.

## Track B — needs a human, not a keyboard

Three decisions. Each is a paragraph of judgment, not a project.

| | decision | notes |
|---|---|---|
| ~~B1~~ | ~~Item 11 — the rung for protected categories~~ | **Closed 2026-07-30.** Step 3's clause governs; the four examples are illustrative. `SENSITIVITY.md` *Protected status* is canonical |
| ~~B2~~ | ~~Item 2 — disposition of `apps/marching-arts`~~ | **Closed 2026-07-30.** Spike; it retires. Findings carry forward, code does not. First commit is an empty tree |
| B3 | Item 4 — which surfaces exist | **Deferred 2026-07-30** — worked in a separate session, not unanswered. Still gates layout and any dispatcher |

**B1's hold is lifted.** Fields in those categories may now be classified, at
`L4`. Neither this plan's earlier suggestion nor item 11's own conclusion
survived the discussion: `L5` is unservable and would strand the liaison the
status exists to help, and new classes were never needed because the route into
the ladder was the defect, not the vocabulary. **Chosen name left the list** —
its harm is non-use, and the protected half is the SIS legal record.

One residual, carried into `SENSITIVITY.md` rather than here: **what checks a
general clause.** A lookup table is verifiable; a clause is a judgment (#19).

## Track C — buildable now

Short, and the shortness is the finding rather than an oversight.

| | task | depends on |
|---|---|---|
| C1 | Extend `craft/` | nothing — text-only, no student data, no network, no model |
| C2 | Sweep `docs/survey/*.md` for `§N` | nothing — needs the routing decision in `scout-25` part 5 first |
| C3 | A rule-13 acceptance test | nothing. `willow-grove`'s constraint 1 supplies the shape: point a reader at an unreachable source in CI and assert no surface reports health. Rule 13 has **no test in this repository** |

That is the honest list. **This repository is decision-blocked, not
effort-blocked.**

---

## What that means for sequencing

The instinct is to build C in parallel while A and B resolve. Resist it. Three
of the four things worth building next — the guardianship predicate, the
dispatcher `voice.guard()` needs, the promotion of the lane DDL to
`migrations/` — are each gated on a Track A read or a Track B decision, and
building them first means building against a guess.

`docs/PLAN-GUARDIANSHIP.md` is the worked example: eleven acceptance gates,
fully specified, and unbuildable until B3 says what a surface is and A2 says
what W-3 actually requires.

**A1 remains; B3 is deferred rather than open.** B1, B2, 1a and A2 all closed on
2026-07-30 — three by deciding, one by reading.

**Nothing on the critical path is blocked.** A1 is a queue of 33 unread
repositories, and it can be worked from here. Two findings on B3 landed while it
was discussed and are recorded at §18 item 4: its enumeration omits the guest
surface clinicians and judges need, and `surfaces` is a manifest field whose
fleet precedent shipped a declaration nothing enforced.

**One open design question came out of A2's read** and is recorded in
`SENSITIVITY.md` rather than here: the spike serves an `L4` payload only to the
data subject, where `L4` allows an entitled principal with a declared purpose.
Stricter-at-source versus deliberate-improvement, unresolved.

---

## Order

1. ~~**A3**, **B1**, **B2**~~ — all closed 2026-07-30.
2. ~~**A2**~~ — done 2026-07-30. The lane model's paraphrase is now checked against the clause, and one gap found.
3. **B3** — deferred, in hand elsewhere. It gates layout and any dispatcher, so nothing downstream of layout starts before it lands.
4. **A1** — 24 repositories unread. Expect some rows to need deciding rather than reading, per A3; expect scale mismatches, per the band/rung divergence; and expect this repository to be *stricter* than its sources as often as looser, per `willow-2.0`'s missing interval CHECK.
5. Then, and only then, §9's list in its existing order — noting foundation 1 and 2 are now **to build**, not built.

## What this plan deliberately does not do

- **Does not re-order §9.** §9's ordering principle — expensive-to-retrofit
  first — is sound and is not the problem. What is unverified is its *status
  labels*, which is item 0, which is A1.
- **Does not schedule.** No dates, because the remaining critical items are
  someone else's keystrokes and estimating them here would be fiction.
- **Does not restate a mechanism.** Every row points at the document that owns
  it. If a mechanism appears to be described here, that is a defect (§16).
