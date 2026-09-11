# Part III, read at source

**State: the read is done. Three of the seven clauses were being quoted from a
gloss, and one of those three was being quoted from a gloss inside a docstring
that said "at source." 2026-09-11.**

`docs/ARCHITECTURE.md` §18 blocker 3 names one gate before
`docs/schema/001_lanes.proposed.sql` becomes `migrations/001_lanes.sql`:

> **It rests on a paraphrase.** W-1…W-7 exist in `Willow`'s
> `PROTECTED_AGENTS.md` Part III and were not read at source […] **Open Part
> III before this becomes `migrations/001_lanes.sql`.**

This file is that read, and the record §18 item 0 asks every such pass to leave
behind — *"because an unverified table and a verified one look identical."*

---

## Provenance of this read

| | |
|---|---|
| **Read** | `governance/PROTECTED_AGENTS.md`, *Powers Over Agents*, Draft 0.6, unratified |
| **In** | `willow-memory/willows-grove`, working tree at `8c9c8e8` |
| **File last changed** | `7f2b3cf`, 2026-08-29 |
| **Blob** | `2886a41` |
| **How** | Cloned locally and opened. Not summarised, not fetched through an API, not recalled |
| **Tier** | `P1` for the clause text below. **Not** `P1` for "this is the charter `Willow` holds" — see the caveat |

**The caveat, because it is the whole point of the exercise.** The copy read is
the one in `willows-grove`. Whether `Willow` proper holds the same bytes is not
established here, and **this file does not claim it does.** What is established
is narrower and still worth having: the seven clauses this repository encodes
now trace to a document that can be opened, at a commit that resolves, rather
than to a summary of a summary.

**The citation this repository already carried does not resolve.**
`records/crossing.py`, `records/exit.py` and `records/conflict.py` each cite
Part III at `c8c96b4`. That object name resolves in **none** of the twelve
repositories reachable from this session. So the earlier read was real — its
findings are confirmed below, and one of them was excellent — but its citation
cannot be re-fetched, which is exactly the failure §15 warns about in the
sentence `docs/LANE-MODEL.md` quotes back at itself. The three modules are
re-anchored in this commit on a commit that exists.

**And three files were still asserting the obstacle this document removes.**
`docs/ARCHITECTURE.md` §14's own component map has said **VERIFIED 2026-07-30**
for `PROTECTED_AGENTS.md` Part III since the day it was written, and
`docs/FLEET-READS.md` agrees. Meanwhile §18 blocker 3, `LANE-MODEL.md`'s
provenance note, and the header comment of the DDL itself all said the document
had not been read. **One document, saying both, for six weeks.** That is rule
17's defect with the unusual property of being self-contained — no external
figure drifted; the file disagreed with itself. Corrected in place at all three
sites, struck rather than deleted, per §16 rule 20.

---

## The seven clauses

Read left to right: what the source says, what this repository encodes, verdict.

| Clause | At source | Here | Verdict |
|---|---|---|---|
| **W-1** | A lane from *"the steward's first act for them"* — separate storage, permissions, audit trail; no shared "family" or "fleet" partition | `lane.subject_id` NOT NULL UNIQUE; `lane_entry.lane_id` NOT NULL; `referent` carries no participant column | **Faithful.** The temporal half — *from the first act* — survives translation into §7.4 and into the DDL comment |
| **W-2** | *"'The children' is not a scope; a name is."* Wildcard and group scopes **invalid at issuance** | `access_grant.lane_id` a single NOT NULL column; no join table; no pattern column | **Faithful.** "Invalid at issuance" is encoded as *unwritable*, which is stronger than validated |
| **W-3** | Default deny; **a crossing requires a guardian-signed envelope naming both lanes, purpose, and expiry**; a shared event is two lane entries with one referent | Sentences 1 and 3 in the DDL; sentence 2 in `records/crossing.py`, which found the omission | **Repaired, and the repair is the model for the two below.** Still no thirteenth table; the type exists and the DDL does not |
| **W-4** | *A ward may request, never authorize* — and *"asserted permission is checked at its source (I-2); every ask gets an answer (I-6)"* | §7.4 renders the first six words. `records/serving.py` and `records/standing.py` enforce it for the `self` edge; `records/dispositions.py` carries I-6 | **Faithful in effect, thin in the rendering.** Both cross-references are honoured by code that cites them independently. See the gap below on `access_grant.signer_id` |
| **W-5** | *Agency grows by signature* — **"envelopes name the ward as co-signer for enumerated matters, widened only by new guardian-signed envelopes"** — plus propose-never-enact, plus a clean record is evidence not a grant | §7.4 quotes the propose/enact half and §7.4's *self*-edge argument quotes the track-record half. **The co-signature mechanism is quoted nowhere and encoded nowhere** | **Constructive half dropped** |
| **W-6** | The threshold written into the office at entry; keys to subject *or named successor*; full history intact; standing *"ends or reduces to what the new owner grants back"*; a lane opened without a written exit is invalidly opened | `lane.exit_terms` NOT NULL with a non-blank CHECK; `records/exit.py` quotes the clause **complete and verbatim** | **Faithful, and the only clause quoted in full anywhere in the tree.** Two residuals below |
| **W-7** | Conflicts halt and escalate, never compute a priority — **"Resolutions accumulate as precedent the guardian may ratify into standing envelopes; none takes force without signature"** | §7.4's table and `records/conflict.py`'s docstring both stop at the first sentence. `conflict.py` presents its quotation as *"the clause at source"* | **Constructive half dropped, under a label claiming otherwise** |

---

## The pattern, which is the finding

Three clauses carry two halves — a prohibition and the sanctioned path through
it. **All three lost the second half in translation, and only one was caught.**

`records/crossing.py` found it for W-3 on 2026-07-30 and wrote the diagnosis
better than this file can:

> *"A ward clause that forbids without providing the sanctioned path is not the
> clause — W-5's 'agency grows by signature' has the same shape and would fail
> the same way."*

It does, and so does W-7. The prediction was correct and nobody ran it down,
which is its own small lesson about findings recorded as asides.

**Why it is systematic rather than careless.** A prohibition compresses to a
line and a permission does not. *"Never compute a priority"* survives being
squeezed into a table cell; *"resolutions accumulate as precedent the guardian
may ratify into standing envelopes"* does not, so it gets dropped at the first
compression and every later reader works from the compressed copy. The two
halves also fail differently, and the difference is what makes the loss
expensive rather than untidy:

- **A dropped prohibition** means an illegitimate act is not stopped. Loud, and
  the tests look for it.
- **A dropped permission** means a *legitimate* act is not representable — so
  the only way to serve a real case is to not record that it happened. Quiet,
  and no test looks for something that was never specified.

Every ward clause from here on is read whole or not quoted.

---

## What this read newly opens

**1 · W-5's co-signature has nowhere to live.** `access_grant` carries one
`signer_id`. The source requires envelopes that *"name the ward as co-signer
for enumerated matters."* There is no co-signer column, no enumerated-matters
column, and — the sharper half — **no proposed state.** `lane_entry` has the
draft→sealed cascade precisely so a machine's answer can wait for a human;
`access_grant` has no equivalent, so *"the steward may propose a widening […]
it may never enact one"* has no representation other than writing the live
grant, which is enacting it. **The same shape as W-3's missing envelope table,
and it wants the same fix.**

**2 · W-7's precedent has nowhere to live.** `records/conflict.py` makes the
halt structural and does it well — an `Escalation` cannot carry an order. But
the source does not end at the halt. Resolutions are meant to *accumulate as
precedent* a guardian may ratify, and the human register says why: *"They bring
it to you — and, watching your answers, learn to bring it to you better."* As
built, the escalation path halts forever and learns nothing. There is no
`Precedent` type, no ratification, and no standing envelope for a decided case
to become.

**3 · `access_grant.signer_id` may be the lane's own subject.** Nothing in the
DDL stops a grant over Ben's lane being signed by Ben. That is W-4 and I-2 at
once — *"never derived from the governed agent's own lane without their
standing"*, *"no credential is minted from data about the governed."* It is the
same unreachable-CHECK shape as the `self` edge's holder, and the same answer
applies: a predicate in `records/`, a trigger when the migration stops being
proposed.

**And it must not be written as a flat rule.** W-6 says the guardian's standing
*"ends or reduces to what the new owner grants back"* — so **after** the
threshold, a grant signed by the subject over their own lane is not merely
legal, it is the mechanism by which a graduate re-admits their parent. A naive
`signer_id <> subject_id` would forbid the exact act W-6 requires. The rule is
conditional on the threshold, and W-6 is why it is already known to be.

**4 · `edge` is the one office-bearing table with no exit written at entry.**
I-3: *"The exit is written at the entry […] an envelope without an expiry or
exit condition is invalid at issuance."* `lane` has `exit_terms` NOT NULL;
`access_grant` has `expires_at` NOT NULL; `edge` has neither — only a nullable
`invalid_at`, which records a termination later rather than declaring an exit
at entry, and I-3 distinguishes those in its next sentence: *"Exits execute;
they are not renegotiated at the door."*

**This one is genuinely arguable and the argument is what is missing.** The DDL
says *"an edge authorizes nothing on its own; see `access_grant`"* — on that
reading the edge is a fact and the grant is the office, and I-3 is satisfied by
`expires_at`. But W-6's own words are *"the threshold written into **the
office** at entry"*, and I-4 speaks of offices *held* and *exercised* on their
own terms — which puts the office at `edge` and the exercise at `access_grant`.
Either `edge` needs an exit written at entry, or the DDL should say why an edge
is not an authority for I-3's purposes. **It currently says neither, and a pair
with no named middle is §16 rule 12.**

---

## What this read does *not* do

- **It does not promote the DDL.** Blocker 3's other two gates — the four
  stated-and-unenforced invariants, and the dependency on blockers 2 and 4 —
  are untouched by it. One gate of three.
- **It does not vendor the charter.** A copy in this tree would be §16 rule
  12's pair, and the reconciler it would need is one this session cannot build,
  because the authoritative `Willow` copy is not reachable from here. Clauses
  are excerpted where a finding rests on them, as `ARCHITECTURE.md` already
  does, and `tests/test_clause_quotes.py` is the middle that keeps the excerpts
  and the modules from drifting apart.
- **It does not re-verify §14's other rows.** Item 0's pass stays open. This is
  one row of it, closed properly, which is the rate the rest should expect.
- **It settles no ratification question.** Draft 0.6 is unratified and Schedule
  A is proposed. Reading a clause at source says what it says, not that it
  binds.
