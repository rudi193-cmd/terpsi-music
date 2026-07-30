# Build plan

**Status:** plan. Governs nothing; `docs/ARCHITECTURE.md` governs. No numbered
sections — a `§N` here is always the architecture's.

**One page on purpose.** There are 13,867 lines under `docs/` at time of
writing, this file included — derived, not quoted (#17). If this file
grows past two screens it has stopped being a plan and become another thing to
read. Everything here is a pointer to a decision or a task, never a restatement.

---

## The fact that orders everything else

§9 marks foundation items 1–5 **built**. That rests on §14's *Exists* column,
which §18 item 0 says was assembled from READMEs and pull-request descriptions
rather than from source. `docs/FLEET-READS.md` adds the part that turns a
caveat into a constraint: the 36 repositories sit under `~/github/` as flat
peers, **reachable from a local session and invisible to a remote one.**

So: **no remote session can verify §14, now or later.** Not a scheduling
problem — a structural one.

The plan therefore splits by *where the work can happen*, not by module. That
is the only split that survives contact with this constraint.

---

## Track A — needs the local machine

Three reads. Nothing here is construction, and everything downstream is
planned on unverified ground until they land.

| | task | closes | output |
|---|---|---|---|
| A1 | Open the 36 repos; confirm or downgrade every *Exists* row | item 0 | §14 with a verified/unverified column — the thing that distinguishes the two today |
| A2 | Open `Willow`'s `PROTECTED_AGENTS.md` Part III | item 3 | W-1…W-7 at source, so the DDL stops encoding CLAUDE.md's one-line gloss |
| A3 | Read the `L3`+ NULL rule in `apps/marching-arts` | item 1a | which paths it covers — if absolute rather than scoped, `L3` and `L4` are both wrong |

**A1 is the expensive one and A3 is the sharpest.** A3 is one file and can
invalidate two rungs of a ladder already declared canonical.

## Track B — needs a human, not a keyboard

Three decisions. Each is a paragraph of judgment, not a project.

| | decision | notes |
|---|---|---|
| ~~B1~~ | ~~Item 11 — the rung for protected categories~~ | **Closed 2026-07-30.** Step 3's clause governs; the four examples are illustrative. `SENSITIVITY.md` *Protected status* is canonical |
| B2 | Item 2 — disposition of `apps/marching-arts` | gates the schema's location |
| B3 | Item 4 — which surfaces exist | gates layout, and gates any dispatcher |

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

**A1–A3 and B2–B3 are five items, B1 having closed. None takes a week.** They are the whole
critical path, and the reason this plan is one page rather than a programme.

---

## Order

1. **A3** — cheapest, and can invalidate `SENSITIVITY.md`. Do it before anything rests further on the ladder.
2. ~~**B1**~~ — closed 2026-07-30. Classification is unblocked.
3. **A2** — turns the lane model from a paraphrase into a clause.
4. **A1** — the long read; start it early because it runs alongside everything.
5. **B2, B3** — before any surface or migration lands.
6. Then, and only then, §9's list in its existing order.

## What this plan deliberately does not do

- **Does not re-order §9.** §9's ordering principle — expensive-to-retrofit
  first — is sound and is not the problem. What is unverified is its *status
  labels*, which is item 0, which is A1.
- **Does not schedule.** No dates, because all five remaining critical items are
  someone else's keystrokes and estimating them here would be fiction.
- **Does not restate a mechanism.** Every row points at the document that owns
  it. If a mechanism appears to be described here, that is a defect (§16).
