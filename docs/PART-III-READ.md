# Part III, read at source

**State: re-read, and it caught a third case the first read missed. Three of
the seven clauses were being quoted from a gloss, and one of those three —
W-7 — was being quoted from a gloss inside a docstring that said "at source."
The citation the whole tree carried resolves nowhere reachable, and is
re-anchored here. 2026-09-11.**

This branch already promoted the lane DDL to `migrations/001_lanes.sql` on the
strength of an earlier Part III read (2026-07-30). That read was real and found
two of the three dropped halves — W-3's and W-5's — which is why the thirteenth
and fourteenth tables exist. This file records the re-read that closed the gap
it left: W-7's dropped half, and a citation (`c8c96b4`) that no longer resolves.
It is the record §18 item 0 asks every such pass to leave behind — *"because an
unverified table and a verified one look identical."*

---

## Provenance of this read

| | |
|---|---|
| **Read** | `governance/PROTECTED_AGENTS.md`, *Powers Over Agents*, Draft 0.6, unratified |
| **In** | `willow-memory/willows-grove`, working tree at `c19fae6` |
| **Blob** | `2886a41` (of `governance/PROTECTED_AGENTS.md`) |
| **Also read** | `governance/PROTECTED_PERSONS.md`, blob `f42df851` — the retirement tombstone §14 cites |
| **Part II** | Read at source 2026-09-21 for item 4 (I-3, I-4; and I-6/I-7/I-10 in the same pass) — **same blob `2886a41`, same commit `c19fae6`**, so no new anchor. Fetched through the GitHub API this time, not cloned, and the fetch's returned object SHA `2886a41c…` was checked against the anchor before it was relied on |
| **How** | Part III: cloned and opened, not summarised, not fetched through an API, not recalled. Part II: fetched through the API at the anchored blob and SHA-verified |
| **Tier** | `P1` for the clause text below. **Not** `P1` for "this is the charter the constitution seat holds" — see the caveat |

**The caveat, because it is the whole point of the exercise.** The copy read is
the one in `willows-grove`. Whether the constitution seat proper holds the same
bytes is not established here, and **this file does not claim it does.** What is
established is narrower and still worth having: the seven clauses this
repository encodes now trace to a document that can be opened, at a blob that
resolves, rather than to a summary of a summary at an object name that does not.

**The citation this repository carried does not resolve.** `records/crossing.py`,
`records/exit.py` and `records/conflict.py` — and eight documentation sites,
including §14's own component map and the promoted migration's header — each
cited Part III (and the retirement tombstone) at `c8c96b4`. That object name
resolves in **none** of the repositories reachable from this session, including
`willows-grove` itself. So the earlier read was real — its findings are
confirmed below, and two of them were acted on — but its citation cannot be
re-fetched, which is exactly the failure §15 warns about in the sentence
`docs/LANE-MODEL.md` quotes back at itself. Every site is re-anchored in this
commit on the blob that exists.

---

## The seven clauses

Read left to right: what the source says, what this repository encodes, verdict.

| Clause | At source (`2886a41`) | Here | Verdict |
|---|---|---|---|
| **W-1** | A lane from the steward's first act — separate storage, permissions, audit trail; no shared "family" partition | `lane.subject_id` NOT NULL UNIQUE; `lane_entry.lane_id` NOT NULL; `referent` carries no participant column | **Faithful.** |
| **W-2** | *"'The children' is not a scope; a name is."* Wildcard and group scopes invalid at issuance | `access_grant.lane_id` a single NOT NULL column; no join table; no pattern column | **Faithful.** Encoded as *unwritable*, which is stronger than validated |
| **W-3** | Default deny; **a crossing requires a guardian-signed envelope naming both lanes, purpose, and expiry**; a shared event is two lane entries with one referent | Sentences 1 and 3 in the DDL; sentence 2 in `crossing_envelope` and `records/crossing.py`, which found the omission | **Repaired 2026-07-31, and the model for the two below.** |
| **W-4** | A ward may request, never authorize; asserted permission checked at its source (I-2); every ask gets an answer (I-6) | §7.4 renders the first clause; `records/serving.py`/`standing.py` enforce it for the `self` edge; `records/dispositions.py` carries I-6 | **Faithful in effect.** See gap 3 on `signer_id` |
| **W-5** | Agency grows by signature — **envelopes name the ward as co-signer for enumerated matters, widened only by new guardian-signed envelopes** — plus propose-never-enact, plus a clean record is evidence not a grant | §7.4 quotes the propose/enact half. **The co-signer mechanism is quoted nowhere and encoded nowhere** | **Constructive half dropped** (found 2026-07-30, still open) |
| **W-6** | The threshold written into the office at entry; keys to subject or named successor; full history intact; a lane opened without a written exit is invalidly opened | `lane.exit_terms` NOT NULL with a non-blank CHECK; `records/exit.py` quotes it **complete and verbatim** | **Faithful, and the only clause quoted in full anywhere in the tree.** |
| **W-7** | Conflicts halt and escalate, never compute a priority — **"Resolutions accumulate as precedent the guardian may ratify into standing envelopes; none takes force without signature"** | §7.4's table and `records/conflict.py`'s docstring both stopped at the first sentence; `conflict.py` called its quotation *"at source"* | **Constructive half dropped, under a label claiming otherwise** (found here, 2026-09-11) |

---

## The pattern, which is the finding

Three clauses carry two halves — a prohibition and the sanctioned path through
it. **All three lost the second half in translation, and the earlier read
caught two.** `records/crossing.py` wrote the diagnosis better than this file
can, and predicted the third without running it down:

> *"A ward clause that forbids without providing the sanctioned path is not the
> clause — W-5's 'agency grows by signature' has the same shape and would fail
> the same way."*

It does, and so did W-7 — which was dropped a second time inside the very
docstring that claimed to quote it at source.

**Why it is systematic rather than careless.** A prohibition compresses to a
line and a permission does not. *"Never compute a priority"* survives being
squeezed into a table cell; *"resolutions accumulate as precedent the guardian
may ratify into standing envelopes"* does not, so it gets dropped at the first
compression and every later reader works from the compressed copy. The two
halves also fail differently:

- **A dropped prohibition** means an illegitimate act is not stopped. Loud, and
  the tests look for it.
- **A dropped permission** means a *legitimate* act is not representable — so
  the only way to serve a real case is to not record that it happened. Quiet,
  and no test looks for something that was never specified.

Every ward clause from here on is read whole or not quoted, and
`tests/test_clause_quotes.py` is the middle that keeps the two halves together
once a read has established them.

---

## What this read newly opens

**1 · W-5's proposed state.** ~~No proposed state, so "the steward may propose a
widening… it may never enact one" has no representation other than writing the
live grant, which is enacting it.~~ **The sharper half is built, 2026-09-21 —
`migrations/005_proposed_widening.sql` and `records/standing.py`'s
`propose`/`ratify`.** `self_widening` (migration 001) was the enacted widening —
guardian-signed, one enumerated matter — and its own header quoted the
propose-never-enact sentence, but only the enacted half existed: a steward with
a clean record to cite had nowhere to write a proposal except the live table,
so proposing was enacting. Fixed the way W-3's missing envelope was, with a
table:

- **`proposed_widening`** is the durable, sealed **ledger** of proposals (rule
  18 — a row grants nothing and no read path consults it). A proposal names one
  matter, carries the **evidence** it cites (*"citing the record"*, non-blank),
  and has no signature. *Anyone* may propose, the ward included — W-4 is *"a
  ward may **request**"* — so there is no `proposed_by != subject_id` rule; the
  restriction is on the guardian signature that enacts, not on the asking.
- **`ratify()`** is the enforcement and the named middle (rule 12): the only
  path from a proposal to an enacted `Widening` runs through a live guardian's
  signature, reusing `Widening`'s W-4 check so a ward ratifying its own proposal
  is refused in the one place that rule lives.
- **`widens()` refuses a `ProposedWidening` by type**, so even a *guardian's own
  proposal* is inert until they sign it — the clause in one line. Ablated
  (`tests/ablate.py`); the seal is driven as `terpsi_app` in
  `tests/test_store_rowsecurity.py`.

**Deferred, named not assumed:** W-5's literal *"ward as co-signer"* — the ward
becoming a required second signature on enumerated matters (two-signature
authorization), rather than the guardian widening the ward's own cap. That is a
larger agency model `self_widening` does not touch, and it is not this table.

**2 · W-7's precedent has nowhere to live.** `records/conflict.py` makes the
halt structural and does it well — an `Escalation` cannot carry an order. But
the source does not end at the halt. Resolutions are meant to *accumulate as
precedent* a guardian may ratify, and the human register says why: *"They bring
it to you — and, watching your answers, learn to bring it to you better."*
~~As built, the escalation path halts forever and learns nothing. There is no
`Precedent` type, no ratification, and no standing envelope for a decided case
to become.~~ **Built 2026-09-21 — `records/conflict.py`'s `Precedent`,
`resolve`, `ratify` and `as_consideration`.** Same recorded/standing boundary as
W-5's `ProposedWidening`/`Widening` (item 1), and the same named middle (rule
12): the only path to a *standing* precedent runs through a guardian's
signature.

- **`resolve()`** records how a **named human** decided one escalation — the
  §8.2 seal of the decision, and by rule 10 a rejection (*"declined to split the
  section"*) is as recordable as an approval. It carries no signature: recorded,
  not standing.
- **`ratify()`** is the enforcement of *"none takes force without signature"*:
  a guardian signs a recorded precedent into a standing one, reusing the W-4/W-7
  signature checks (a role cannot ratify; a student named in the conflict cannot
  ratify their own — `_check_ratifier`, the one place that rule lives).
- **Refusal 6 held, one indirection later.** A `Precedent` — even a ratified one
  — carries no `recommendation`; asking raises `NotComputable`, exactly as the
  `Escalation` it came from. The *only* way a precedent touches a later conflict
  is `as_consideration()`: a standing one becomes a plain string in the next
  escalation's **unordered** `considerations` frozenset, no arrow at an answer.
  *"Learn to bring it to you better"* is the system surfacing what a human
  decided before, never deciding for them. An unratified precedent is refused
  there — it takes no force. Ablated (`tests/ablate.py`), eight guards, each
  turning `tests/test_conflict.py` red.

**Deferred, named not assumed:** durable store persistence — a precedent that
survives the process. `conflict.py` is deliberately storeless (like the
`Escalation` it extends, which is also not a store row), and a `BETWEEN_WARDS`
precedent names *two* wards' lanes, which is precisely why it does not fit the
one-lane seal (W-1: *one lane, one key*) the way `proposed_widening` (item 1)
did. Persisting decided cases is a `crossing_envelope`-shaped question — a
two-lane record with a guardian signature — and it is not this records-layer
type. (New, 2026-09-11; resolved at the records layer 2026-09-21.)

**3 · `access_grant.signer_id` may be the lane's own subject.** ~~Nothing in the
DDL stops a grant over a ward's lane being signed by that ward.~~ **Guardian
signature enforced 2026-09-21 — `migrations/001_lanes.sql`'s
`access_grant_signer_has_standing`.** W-4 and I-2 at once.

*A first version of this fix claimed more than it enforced, and a peer audit
(Loki, Opus) caught it before merge — the claim is corrected here rather than
struck out of sight.* That version accepted a `self` edge as standing and
deferred the ward-versus-graduate question to a `records/standing.py`
predicate, `may_self_sign` — **which nothing called.** A ward with a genuine
self edge could sign an `L4` grant over their own lane and it landed; the
threshold half was a rule-18 ledger the doc called enforcement. Removed.

What is enforced, at the store, driven as `terpsi_app` under RLS
(`tests/test_store_rowsecurity.py`) and ablated (`tests/ablate_store.py`):

- The signer holds a **live `guardian_of` edge** over the lane — a director, a
  staff member, a stranger, or the ward on a self edge all hold none, and are
  refused. A `self` edge is deliberately not accepted (see below).
- **No self-grant** (`signer_id = holder_id`) — I-2 at source, *"never to
  self-grant."*
- Standing is read at **`now()`**, the instant of issuance, not a `valid_at`
  the inserter chose — a grant backdated to when an ended guardianship was live
  does not borrow it.
- An **ending passes**: §7.1 ends a grant by setting `invalid_at`, and the
  signing fields are fixed at issuance, so that UPDATE is not re-checked as a
  fresh signature (the court order arriving mid-season). The function is
  `SECURITY DEFINER` owned by `terpsi_reach` so its `edge` read is not the
  writer's own RLS window.

**Deferred, named not assumed:** the one self-signed grant the charter
sanctions — a graduate *past* W-6's threshold re-admitting their guardian —
needs the threshold in the enforcement path, and W-6's threshold is a birthdate
or graduation date derived at read time (`records/serving.py`), not a column.
Until that reaches enforcement, every self-signed grant is refused: fail-closed,
forbidding a future legitimate act rather than admitting a present illegitimate
one. And the **read-time** re-check (a signer whose standing later ends, which
`crossing_envelope` carries in `migrations/003` and `access_grant` does not
yet).

**4 · `edge` versus `access_grant` as the office I-3 requires an exit from.**
`lane` has `exit_terms` NOT NULL; `access_grant` has `expires_at` NOT NULL;
`edge` has only a nullable `invalid_at`. The DDL says *"an edge authorizes
nothing on its own; see `access_grant`"* — on that reading the grant is the
office and I-3 is satisfied. But W-6's words are *"the threshold written into
**the office** at entry,"* and I-4 speaks of offices *held* on their own terms,
which puts the office at `edge`. Either `edge` needs an exit written at entry,
or the DDL should say why an edge is not an authority for I-3's purposes — a
pair with no named middle is §16 rule 12.

**Resolved 2026-09-21, and it needed Part II read at source — which this item
forced.** The resolution turns on the exact words of I-3 and I-4, and neither
had been read here: I-3 was quoted nowhere in the tree, I-4 only as a
Schedule-A fragment. `docs/LANE-MODEL.md`'s own provenance note set the rule —
*"the next thing that turns on [an unread invariant] should open Part II
first"* — so Part II of `PROTECTED_AGENTS.md` was opened at source (blob
`2886a41`, the same blob Part III was anchored on; verified by the API's
returned SHA `2886a41c…` at commit `c19fae6`) rather than resolving on a gloss.

Read as written, the tension dissolves and the answer is the **second** branch,
not the first:

- **I-3 binds an *authority*, and an edge is not one.** I-3's machine register
  is *"an envelope without an expiry or exit condition is invalid at issuance;
  exits execute, they are not renegotiated at the door."* An *Office* is
  *"a named authority… with declared values on all five axes"* (Exit among
  them); an *Envelope* is *"a bounded, signed, expiring grant of authority."*
  The DDL's own words — *"an edge authorizes nothing on its own"* — put the edge
  outside that: a **relational fact**, not an authority, so I-3 does not reach
  it. I-4 (*"offices do not compound… each is exercised on its own terms"*) is
  about non-merging of scopes, **not** a claim that the edge is the office; the
  reading that "puts the office at `edge`" was the gloss.
- **The authorities already carry I-3's exit at issuance.** `access_grant`,
  `crossing_envelope` and `self_widening` each carry `expires_at NOT NULL` — the
  envelope I-3 names. The guardianship office's own exit is written at entry on
  the **lane** (`lane.exit_terms` + threshold, W-6) — which is why W-6 lives on
  `lane` and I-3 on the grants. The edge's `invalid_at` is the dated *mechanism*
  of an ending (refusal 3, the court order mid-season), never a term at the door.
- **So it was the second branch: name the middle, do not add an edge exit.**
  Forcing an exit onto every edge would miscategorise a fact as an office with a
  term (I-4). The named middle is stated in the `edge` DDL comment and in
  `docs/LANE-MODEL.md`'s exit-axis decision, and made checkable in
  `tests/test_lane_model.py`: the three authorities must carry `expires_at NOT
  NULL`, `edge` must carry none. **This was not only documentation — it closed a
  live under-guard:** the structural checker asserted `crossing_envelope`'s
  `expires_at` but never `access_grant`'s, so I-3's plainest case had no test.
  Ablated (`tests/ablate.py`, *"I-3: an authority carries its exit at
  issuance"*).

---

## What this read does *not* do

- **It does not re-open the promotion.** The DDL is already `migrations/001`;
  W-1, W-2 and W-6 came through whole and the structural encodings stand. This
  read changes citations, one truncated quotation, and the faithfulness claim —
  not the tables.
- **It does not vendor the charter.** A copy in this tree would be §16 rule 12's
  pair, whose reconciler this session cannot build, because the authoritative
  copy is read-only from here. Clauses are excerpted where a finding rests on
  them, and `tests/test_clause_quotes.py` is the middle that keeps the excerpts
  and the modules from drifting apart.
- **It does not re-verify §14's other rows.** Item 0's pass stays open on the
  question this read sharpens: the 41-of-41 sweep checked **presence**, and this
  read shows presence and faithfulness are different claims — the §7.4 row was
  VERIFIED and wrong about the second.
- **It settles no ratification question.** Draft 0.6 is unratified. Reading a
  clause at source says what it says, not that it binds.
