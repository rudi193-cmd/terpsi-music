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
| **How** | Cloned and opened, not summarised, not fetched through an API, not recalled |
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

**1 · W-5's co-signer has nowhere to live.** `access_grant` carries one
`signer_id`. The source requires envelopes that *"name the ward as co-signer
for enumerated matters."* There is no co-signer column, no enumerated-matters
column, and — the sharper half — **no proposed state**, so *"the steward may
propose a widening […] it may never enact one"* has no representation other than
writing the live grant, which is enacting it. The same shape as W-3's
missing-envelope table, and it wants the same fix. (Carried from the 2026-07-30
read, still unbuilt.)

**2 · W-7's precedent has nowhere to live.** `records/conflict.py` makes the
halt structural and does it well — an `Escalation` cannot carry an order. But
the source does not end at the halt. Resolutions are meant to *accumulate as
precedent* a guardian may ratify, and the human register says why: *"They bring
it to you — and, watching your answers, learn to bring it to you better."* As
built, the escalation path halts forever and learns nothing. There is no
`Precedent` type, no ratification, and no standing envelope for a decided case
to become. (New, 2026-09-11.)

**3 · `access_grant.signer_id` may be the lane's own subject.** ~~Nothing in the
DDL stops a grant over a ward's lane being signed by that ward.~~ **Resolved
2026-09-21 — `migrations/001_lanes.sql`'s `access_grant_signer_has_standing`
trigger and `records/standing.py::may_self_sign`.** That was W-4 and I-2 at
once. It was *"the same shape as the `self` edge's holder"* — and the read that
wrote this line got the shape half right and the split wrong. The self edge's
DB-checkable half was **identity** (holder = subject), a fact the store holds;
`signer_id`'s distinguishing half is the **threshold**, and the store holds no
threshold — W-6's is a birthdate or a graduation date derived at read time
(`records/serving.py`), never a column. So a single trigger cannot decide it: a
flat `signer_id <> subject_id` forbids the graduate re-admitting their guardian
(the act W-6 requires), and a flat *"signer must be a guardian"* forbids it too
(`edge_self_holder_is_subject` refuses a subject holding `guardian_of` over
their own lane). The resolution splits on what the store can see: the **trigger**
requires the signer to hold a live `guardian_of` or `self` edge over the lane
(the threshold-independent half — it closes the hole where any person could
sign), and **`may_self_sign`** carries the rest (a *self*-signed grant is legal
only past the threshold), the named middle for the pair (§16, rule 12). Both
guards are ablated: `tests/test_store_rowsecurity.py` and `tests/ablate_store.py`
for the trigger, `tests/test_standing.py` and `tests/ablate.py` for the
predicate. Not closed: the *read-time* re-check (a signer whose standing later
ends), which `crossing_envelope` carries in `migrations/003` and `access_grant`
does not yet — a separate follow-up, named here rather than assumed done.

**4 · `edge` versus `access_grant` as the office I-3 requires an exit from.**
`lane` has `exit_terms` NOT NULL; `access_grant` has `expires_at` NOT NULL;
`edge` has only a nullable `invalid_at`. The DDL says *"an edge authorizes
nothing on its own; see `access_grant`"* — on that reading the grant is the
office and I-3 is satisfied. But W-6's words are *"the threshold written into
**the office** at entry,"* and I-4 speaks of offices *held* on their own terms,
which puts the office at `edge`. Either `edge` needs an exit written at entry,
or the DDL should say why an edge is not an authority for I-3's purposes — a
pair with no named middle is §16 rule 12.

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
