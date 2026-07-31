# The lane model — schema for W-1 and W-3

**Status:** adopted 2026-07-31. Canonical for the reasoning behind
`migrations/001_lanes.sql`, which is the DDL. `docs/ARCHITECTURE.md`
governs everything else; `docs/SENSITIVITY.md` governs the rungs. This document
carries no numbered sections — a `§N` here always refers to the architecture.

**Why it exists.** §18 blocker 3: W-1 and W-3 are schema decisions rather than
modelling preferences, §8 is an entity sketch with no fields or keys, and
retrofitting either clause later is a data migration across every table that
references a student. Migration 001 could not be written from what was on the
page.

**Fourteen tables, 116 columns, all classified** — counted from
`migrations/001_lanes.sql` and confirmed against a live PostgreSQL 16 instance,
not carried forward from the previous revision of this sentence, which said
twelve and 93. The DDL moved out of `docs/schema/` on 2026-07-31; a tombstone
stands at the old path.

> **The provenance note at the bottom is now a record rather than a warning.**
> Part III was opened at source (`c8c96b4`) before this was promoted, which was
> the condition that note set. Reading it added two tables.

---

## The two clauses, and what each costs

**W-1 — a lane, not an account.** Separate storage, permissions and audit trail
*from the steward's first act*, with no shared "family" partition. The
operative words are *first act*: this is §5's per-subject partitioning, but
created at the first write rather than assembled when someone requests erasure.

**W-3 — lanes are mutually sealed.** Default deny between wards, *"a crossing
requires a guardian-signed envelope naming both lanes, purpose, and expiry,"*
and *"a shared event is two lane entries with one referent."* Two students at
one rehearsal is two records.

Three sentences, and this document encoded two of them for a day. The middle
one is a **permission**, and the two halves fail in opposite directions: default
deny unenforced means an illegitimate crossing is not stopped; no envelope table
means a legitimate crossing is not *representable*, so the only way to serve a
real sibling case is to not record that it happened. `crossing_envelope` is the
thirteenth table and closes the second half. **A ward clause that forbids
without providing the sanctioned path is not the clause.**

The cost is concentrated and worth stating plainly: **a rehearsal attended by
150 students writes 150 rows.** Every instinct trained on normalized schemas
says to store one `Rehearsal` with a roster column and join. That instinct is
the thing W-3 forbids, and the reason is not storage efficiency but
partitioning — a roster column is a shared partition wearing a foreign key, and
every query over it returns other wards' rows by default.

`referent` is what remains once the roster is removed: the shared object with
no participants on it. Its emptiness is the schema rule. Anything later added
to `referent` that names or counts participants reintroduces exactly the
partition W-1 forbids, which is why the test asserts the absence rather than
trusting the comment.

---

## Decisions this document makes

**One lane per person, not one lane per ward.** W-1 requires lanes for wards.
This extends them to everyone — staff, guardians, judges, clinicians.

Three reasons. A guardian's contact details are `PII_GUARDIAN` at `L3` and want
the same dated-revocation discipline a student's do. A single storage pattern
means there is no second write path that could accidentally hold ward data.
And the alternative requires every write to first answer *is this person a
ward?*, which is precisely the branch where W-1 gets violated by accident — a
sixteen-year-old drum tech is staff and ward at once, and the branch has to get
that right on every path forever.

The cost is that W-6's exit terms must be written for a judge who attends one
event. That seems like the correct amount of friction for opening a lane.

**Grants are separate from edges, and only grants authorize.** §7 models
relationships as edges, some of which point at groups: `staff_of : Chris →
Drumline`. W-2 says group scopes are invalid at issuance. Both are satisfiable
at once only if the edge is a *fact* and the grant is the *authorization*: the
drumline edge is recorded because it is true, and it authorizes nothing until
one grant per lane is issued against it, each naming a single lane.

A staff member covering forty students therefore holds forty rows. That is the
intended cost of W-2, and the schema is built so the cheap version cannot be
written — `access_grant.lane_id` is a single `NOT NULL` column, there is no
grant-to-lane join table, and there is no scope-pattern column to put a
wildcard in. **Group grants are inexpressible rather than rejected**, which is
the same move §6 makes with egress: no destination to deny because there is no
client to call one.

**`L5` is unreachable through a grant, by CHECK.** `access_grant.max_rung`
permits `L1`–`L4`; `self_widening.max_rung` permits `L4` and nothing else. The
ladder's top rung is not policy-excluded, it is absent from both constraints, so
a grant or a widening purporting to serve `L5` fails at write time.

`crossing_envelope` takes the stronger form of the same rule: it has **no rung
column at all**. An envelope crosses a seal and widens nothing — the rung, the
entitlement edge and the declared purpose all still apply below it — so there is
nowhere to write `L5` rather than a constraint refusing it. Inexpressible rather
than rejected, which is the move W-2 makes with group scopes and §6 makes with
egress.

**A widening names one matter, and the schema will not take a set.**
`self_widening.category` carries a non-blank `CHECK` and a wildcard `CHECK`
against `*`, `all`, `any`, `every`. That is W-2's *"'the children' is not a
scope; a name is"* applied to the other axis: refusal 5 is unexpressible in both
directions at once, because the subject is one person by foreign key and the
matter is one string that cannot be a star.

**Declinations are a table, not a column.** A `declined boolean` on
`lane_entry` travels in `SELECT *`, and §7's indistinguishability guarantee
dies the first time someone writes one. Separating the table means rendering a
refusal requires a deliberate join that no view performs and the test can look
for.

---

## The bitemporal split

§7.1 settles the mechanism: adopt willow-2.0's `valid_at` / `invalid_at` rather
than inventing `effective_from` / `effective_until`, keep `created_at`
immutable beside them, and terminate by setting a date rather than by `DELETE`.

Its exclusion list is the half that shapes this schema. State takes the pair;
history must not, because a historical fact is not mutable state.

| Takes `valid_at` / `invalid_at` | Deliberately without |
|---|---|
| `person`, `lane`, `referent`, `lane_entry` | `disclosure_log` |
| `edge`, `access_grant`, `declination` | `consent_chain` |
| `scope_object`, `crossing_envelope`, `self_widening` | `reconciled_session` |

Ten and three; `field_classification` is a registry and takes neither. The
envelope and the widening are **state** and that is a decision, not an
oversight: both end by a date and never by a `DELETE` (refusal 3). A revoked
envelope that was deleted cannot answer *"who could cross into Ben's lane on 12
October, and why."* Both carry `expires_at` beside the pair — the timebound the
clause requires *declared at issuance* (I-6) — and the two are different facts:
`expires_at` is what the signer wrote down, `invalid_at` is the revocation that
arrived afterwards.

**Both axes are needed, and the case that proves it is ordinary.** A court order
dated in March, delivered to the program in October. *When the restriction took
effect* and *when this system learned of it* are different dates, and a
disclosure made in June was either compliant or not depending on which one you
ask. `created_at` is never updated; the migration's habit of backfilling
`valid_at` from it must not be repeated on these tables.

---

## Worked example: the court order

The case §7.1 is written against, traced through the schema.

1. An order restricting Ann's contact with Ben, dated 14 March, arrives 2 October.
2. `UPDATE edge SET invalid_at = '2026-03-14' WHERE …` — the `guardian_of`
   edge is dated closed at the order's date. `created_at` still reads 2 October.
   Nothing is deleted.
3. Every read re-derives entitlement from live edges, so Ann's grants stop
   resolving. **The same predicate derives the outbound send list**, which is
   the half §7.1 insists on: a restricted guardian still on the SMS list
   receives a live location disclosure about a minor, pushed to a device, with
   no way to recall it.
4. "Who could see Ben's medical form on 12 October, and why" is answerable, by
   query, against dated rows.
5. The order's *contents* are `L5` — enforced, never rendered, including to the
   director. The system stores the effect. Nobody in a band program needs the
   findings.
6. The order is modified in January. `invalid_at` moves; no record was
   discarded that reinstatement has to reconstruct.

**`records/orders.py` is this walkthrough as code**, and building it added two
things the trace above did not have. The first is that the ending needs its
**own** knowledge clock: `created_at` says when the *edge* was learned and
nothing said when its *termination* was, so the March-delivered-in-October case
could be recorded and not asked about — `Edge.ended_known_at` and
`live_as_known_at()` are that second axis on the second event. The second is
step 7, which was missing: **an order may not leave the lane in silence.** An
ending that removes the last live `guardian_of` edge is refused unless the order
carries a named, dated declaration of the state it leaves behind, or names the
guardianship that supersedes it. *No guardian, and nobody said why* is `UNKNOWN`,
and `UNKNOWN` is not a state a court order is allowed to produce.

---

## What running it found

The DDL was executed against PostgreSQL 16 and each constraint attacked. The
first draft passed eight mutation tests and failed four things no amount of
reading would have caught:

| Defect | Fix |
|---|---|
| `UPDATE` and `DELETE` both succeeded on `disclosure_log` — the FERPA §99.32 record was silently rewritable | `BEFORE UPDATE OR DELETE` trigger on all three history tables |
| `edge.target_id` had no foreign key; a UUID referring to nothing was accepted | `scope_object` table; two nullable FKs with `num_nonnulls(...) = 1` |
| `edge.target_kind` had no CHECK — `'Sandwich'` was accepted | Column removed; which FK is set *is* the kind |
| `field_classification` held 0 rows against 87 columns | Every column seeded — 93 on the day, 116 since the two tables below — coverage asserted in the suite and in CI |

**Three of the four were declarations without enforcement**, written into a
migration whose own document names that defect — "append-only" in a comment
above three tables that were not, and a set of allowed target kinds in a
comment above a column that accepted anything. §7.2's rule is the one that
catches this: *say which*. A label is a ledger.

The fourth is worse in kind, because the empty registry made the ladder
decorative. `docs/SENSITIVITY.md` says an unclassified field is a build
failure; there was no build failure, because there was nothing to check
against.

### And what running it found at promotion, 2026-07-31

The two new tables were attacked the same way — 27 forbidden acts against
PostgreSQL 16, six legitimate ones asserted still to land. Two findings, both
about the *guard that fired* rather than about a hole:

| Defect | Fix |
|---|---|
| **A `BEFORE ROW` trigger fires ahead of every `CHECK`, `NOT NULL` and foreign key on the same row.** An envelope pointed at an ensemble instead of a lane was refused — by the signature trigger, which never let it reach the foreign key. The guard under test had not fired, and the attack passed | Attacks assert on the **constraint named in the error**, never on the fact of a refusal. Three cases now approach through a column the trigger does not read, so the intended guard is the one that speaks |
| **Refusing only a forged `self` edge left the mirror row insertable.** `('guardian_of', Ben, Ben's lane)` is a ward holding guardianship over itself, and every "is the signer a guardian of this lane" check then answers *yes* for the ward — W-4 defeated one table down, including on the envelope, which carries no signer `CHECK` of its own | The rule is an **equivalence**: exactly one edge kind may name its own subject as holder, and it is `self`. Both directions refused by one trigger, both attacked |

The first is `EXTERNAL-ARM.md`'s *"a gate green because a different constraint
was catching it"*, arriving through execution order rather than through
overlapping rules. It is the reason a refusal count is a weak claim: **eight
refusals with the guards unnamed is consistent with one guard refusing eight
things.**

---

## What the DDL still cannot enforce

Invariants stated in the schema's comments and **not** expressible as
constraints. Naming them here is the §16 discipline: a declaration without an
enforcement is a pair, and the middle is the code that closes it.

**The four §18 item 3 names are now closed, and each entry below says where.**
The `self` edge's holder closed twice, once per layer — `is_self_edge()` at
the predicate (2026-07-30) and the `edge_self_holder_is_subject` trigger at
the store (2026-07-31), which is the right shape rather than a duplicate: the
store is not the only path to a row, and the predicate is not the only path
to a read. The other three closed together on 2026-07-31, because they turned
out to be the same kind of thing — **predicates over the acting principal**,
which is why none could be a column CHECK and why all three landed in
`records/` beside the read predicate rather than in ledgers of their own.

**The hash chain, last on this list, is still open** and is not one of the four.
It is not a predicate over a principal; it is a mechanism whose columns exist
and whose code does not.

**I-7 — the record binds the holder most.** *Entries authored by the governed
about the office are as durable as entries authored by the office about the
governed.* Expressed as policy: supersession of a `lane_entry` whose
`author_id` is the lane's own subject requires an authority that no
office-derived grant confers.

> **Enforced at `records/standing.py`'s `may_supersede()`**, called from
> `records/sealing.py`'s `reject()` and `redraft()` — the two verbs the clause
> names, *deleting or amending*, and the only two spellings this tree offers.
> `Record.author_id` is `lane_entry.author_id`; the refusing branch reads **no
> edges at all**, because an authority "that no office-derived grant confers"
> cannot be one a predicate looks for among grants. Ablated as *"I-7's
> supersession asymmetry"*, *"I-7: the office cannot reject the ward's entry"*
> and *"I-7: the office cannot rewrite the ward's entry"*.
>
> **The forbidden act it stops was reachable before it existed.** Rejection is
> terminal in that module — `seal()` refuses a rejected record — so a director
> calling `reject()` on a student's account of an incident made it permanently
> unservable without deleting a row.

**~~W-3's default deny.~~ The schema no longer only partitions — closed
2026-07-31 by `migrations/003_row_security.sql` (S-2), and closed *precisely*
rather than entirely.** The sentence this entry carried was *"the schema
partitions; it does not enforce that a query stays in its lane"*, and that is
now false for the seal and still true for four other things.

> **Compiled into the store**: the lane seal's two clauses — a live edge into
> the lane, and *between wards, default deny* with a live guardian-signed
> envelope as the only crossing — as row-level security policies on eleven
> tables, evaluated against a per-transaction acting principal
> (`store/session.py`, `SET LOCAL` on a custom GUC). An unset principal reads no
> row anywhere, `FORCE ROW LEVEL SECURITY` is on and ownership moved to
> `terpsi_migrator` so the flag binds a role that is not a superuser, and the
> crossing is attacked as raw SQL with nothing from `records/` on the path.
>
> **Still a predicate and not a partition**: the grant ceiling, the derive
> floor and the payload/instruction split, `L5`'s never-served rule, `L4`'s
> declared purpose with the self cap and W-5's widening, and §7.1's second
> clock. Each turns on something that is not a column of the row being read.
> The migration's header lists them; rule 18 is why the list is in the file
> rather than in a summary.
>
> **The predicate stays, and now there are two of it.** That is §16's pair and
> it ships with its middle in the same commit:
> `tests/test_store_differential.py` drives one case set through
> `records/serving.py` with real rows and through the cluster under RLS, and
> fails on any disagreement in either direction. `tests/ablate_store.py` breaks
> both sides in turn and requires the middle to notice.
>
> **One thing the middle cannot attribute, recorded rather than rounded up**:
> reversing the compiled envelope's direction survives the differential,
> because a reach comparison can only see it for a principal who is a ward of
> one lane *and* holds an entitlement edge into another — and a crossing does
> not widen the entitlement edge, so no such principal exists in this domain.
> It is caught one level below reach, by
> `tests/test_store_rowsecurity.py::test_the_compiled_envelope_is_directional`
> for the SQL and `tests/test_crossing.py::test_an_envelope_is_directional` for
> the Python.

> **~~And the crossing itself has no table.~~ Closed 2026-07-31 — it is
> `crossing_envelope`, the thirteenth table.** Found by reading W-3 at source
> on 2026-07-30 and built at promotion: two `NOT NULL` lane references that
> must differ, a non-blank purpose, an expiry `CHECK`ed to follow the
> signature, a signer who is a person, and a `BEFORE INSERT OR UPDATE` trigger
> requiring that person to hold a live `guardian_of` edge over the lane whose
> seal is being opened.
>
> **Enforced at `records/serving.py`'s `serve()`**, on the branch that also
> carries the named-lane crossing, using `_acting_ward()`. The seal now has
> both halves of the clause rather than one: a read that *names* another lane,
> and a reader who *is* another ward. The second was open in two ordinary
> places at once — a read passing no `lane_id` never reached the seal, and a
> field below the derive floor needs no entitlement edge — so a ward was served
> another ward's `L2` lane entry with nothing consulted. The check sits above
> the derive floor because **the seal is not rung-shaped**: it is about the
> partition, not the sensitivity. Ablated as *"W-3 default deny between wards"*,
> *"an unnamed origin lane is not a wildcard"*, *"a forged self edge does not
> make a ward"* and *"an ended self edge is not a ward's seal"*.
>
> **And the sanctioned path still works**, which is the half this document
> warns about one entry down: a ward reading a sibling's lane from their own,
> on a guardian-signed envelope naming both lanes, is served.

> **And the crossing itself has no table — found by reading W-3 at source,
> 2026-07-30.** The full clause is *"Between wards, default deny; **a crossing
> requires a guardian-signed envelope naming both lanes, purpose, and
> expiry.** A shared event is two lane entries with one referent."* This
> document encoded the third sentence and the first; the middle one is absent
> from all twelve tables — `envelope` and `crossing` appear zero times in the
> DDL.
>
> The other half of the paragraph stands and is the entry above: default deny
> is still a predicate, not a partition. **The two halves failed differently
> and only one of them is fixed by a table** — an illegitimate crossing is
> still stopped by `records/serving.py` and by nothing in the DDL.
>
> W-5's *"agency grows by signature"* had the identical shape and was found by
> looking for it: `self_widening` is the fourteenth table, and it is the only
> thing that lifts the `self` edge's `L3` cap.

**~~The `self` edge's holder.~~ Closed 2026-07-31 by
`edge_self_holder_is_subject`.** Added to `edge_kind` 2026-07-30 (§18 item 12).
Its defining property is that `holder_id` **is** the lane's `subject_id`, and a
CHECK cannot reach through `target_lane_id` to `lane.subject_id` to say so — so
this was the one edge kind whose meaning the table stated and could not hold. A
row reading `('self', <staff person>, <Ben's lane>)` was accepted by the DDL and
would, unchecked, entitle a staff member through the subject's own door.
`records/standing.py`'s `is_self_edge()` was the middle, called by the read
predicate before any edge matches, and ablated in `tests/ablate.py` as *"a
forged self edge."* The comment above `edge` said a `BEFORE INSERT OR UPDATE`
trigger was the DDL-side answer *when this migration stops being proposed*, and
this is that. The predicate stays: the store is not the only path to a row.

> **Writing the trigger found the row it was not written to refuse.** Refusing
> a forged `self` edge and stopping there leaves `('guardian_of', Ben, Ben's
> lane)` insertable — a ward holding guardianship over itself. Every guard that
> asks *"is the signer a guardian of this lane"* then answers yes for the ward,
> so the clause falls one table down: the ward signs its own crossing envelope, which
> has no signer `CHECK` of its own because the clause puts the requirement on
> the guardian rather than on a column. The rule is an **equivalence** —
> exactly one edge kind may name its own subject as holder — and both
> directions are refused and both attacked.
>
> The consequence for `self_widening_ward_cannot_sign_its_own`: with the edge
> trigger standing, that CHECK cannot be reached through an ordinary path. It is
> kept as defence in depth and demonstrated in CI **with the signature trigger
> disabled**, because a constraint nobody has seen fire has not been shown to
> work (rule 19).

**The rung ceiling.** `access_grant.max_rung` records the ceiling and the
registry is now populated for every column the DDL declares — 116, counted from
`migrations/001_lanes.sql` and confirmed against `information_schema` on a live
instance — so the lookup has something to
resolve against. What is missing is the code that performs it at serving time.
Until that exists the registry is **a ledger and not a gate**, and §7.2's rule
applies — say which.

> **Enforced at `records/serving.py`'s `serve()`**, beside the entitlement-edge
> check, via `_ceiling()` and the `Grant` type. `Grant` refuses at construction
> everything `access_grant` refuses by CHECK — `L5`, a wildcard lane, an `L4`
> grant with no purpose, an expiry that is not in the future — so the two
> spellings of the rule cannot disagree. **The edge is a fact; the grant
> authorizes**, and until this existed `serve()` decided on the edge alone.
> Ablated as *"the grant ceiling is consulted"*, *"the ceiling refuses above
> itself"*, *"no live grant is not an unlimited one"*, *"a grant's own dates"*,
> *"L5 is unreachable through a grant"*, *"W-2: a grant names one lane"* and
> *"L4 without a purpose is not a grant"*.
>
> **What remains, stated exactly rather than left to be discovered.** `grants`
> is `Optional`: `None` means *no grant source was consulted* and the decision
> rests on the edge alone, `()` means *consulted and this principal holds
> nothing*, which denies at `L3` and above. That distinction is rule 13 in a
> signature and it is also the residual — **a caller that passes `None` is not
> gated by the ceiling**. There is no surface to make it mandatory for (§18
> item 4), and the two failure directions are opposite, so a single sentinel
> would have merged a fail-open with a fail-closed. `records/dispatch.py`
> forwards it as given and never normalises it; that forwarding is itself
> ablated.
>
> The other half of the original entry is untouched: **the 93-column registry
> is still a ledger.** Nothing in `records/` resolves a column name to its rung
> — `Field.rung` is supplied by the caller. That is the largest remaining piece
> of the ladder and it is a different piece from this one.

**The hash chain.** `disclosure_log`, `consent_chain` and `reconciled_session`
each carry `prev_hash` and `hash`. Nothing computes either, and nothing
verifies the chain. The trigger makes the rows immutable in place; it does not
detect a chain that was never linked, and §6's *count-anchor truncation
defence* has no implementation here at all. Columns for a mechanism are not the
mechanism.

---

## What this does not decide

- **Whether `payload jsonb` is right.** It defers the per-kind field work that
  §8's entity list implies and will need revisiting per module. It is not a
  decision to store everything as JSON forever.
- **Identity reconciliation.** §8 assigns it to `Nestor`'s `EntityResolver` —
  sealed canonical mapping, sub-threshold returns an unsealed suggestion rather
  than a silent merge. Nothing here models the suggestion state, because the
  resolver's interface has not been read.
- **Erasure.** §5's per-subject erasure is a distinct act from `invalid_at`,
  with its own authority, and this schema does not express it.
- **Keys.** W-6 transfers a lane *with the keys*. `exit_terms` is prose; the key
  hierarchy that makes a transfer real is §5's and is not modelled.
- **Anything gated on blockers 2 and 4.** Whether this is the first migration of
  a new tree or a transform applied to a moved `marching-arts`, and what
  surfaces read it.

---

## Provenance of this file

**Resolved 2026-07-31, and the resolution is the reason to keep the note.**

~~Weaker than `docs/SENSITIVITY.md`, and the difference matters.~~ The clauses
here are now `P2 Cited` at **one** remove: `Willow`'s `PROTECTED_AGENTS.md`
Part III was opened at source (`c8c96b4`) and W-1…W-7 read as written, before
promotion rather than after. That was the condition the struck paragraphs set.

~~The ladder had nothing to verify against — §18 recorded that no definition
existed anywhere in the fleet, so writing one from scratch was the whole task.
This document is different: W-1 through W-7 and I-6/I-7/I-10 **exist**, in
`Willow`'s `PROTECTED_AGENTS.md` Part III, and this session could not open
them. Every clause here is quoted from CLAUDE.md's one-line summary of a
paraphrase in §7.4, which was itself assembled from a reading of a charter
document. That is `P2 Cited` at two removes, and §15's warning about citations
that cannot be re-fetched applies directly.~~

~~Concretely, the risk is not that W-1 says something other than "a lane, not an
account."~~ It is that Part III states seven clauses in a *machine register*
whose exact wording is the specification — §7.4 notes the fragment carries two
registers and that *"a clause that cannot survive translation between the two
registers is not yet a clause."* A schema encoding the human-register gloss of
a machine-register clause is exactly the translation failure that sentence
warns about.

**And that is precisely what had happened, which is why the warning is kept
rather than deleted.** The gloss this document encoded was *"lanes are mutually
sealed"* and *"a shared event is two lane entries with one referent."* Both are
true. The sentence between them — *"a crossing requires a guardian-signed
envelope naming both lanes, purpose, and expiry"* — was gone, and nothing about
reading the paraphrase could have revealed that, because **a paraphrase that
drops a clause reads as complete.** W-5 had lost the same half in the same way.

The correction cost the two tables named above and a trigger. The lesson generalises past this
file: **a summary preserves prohibitions and loses permissions**, because a
prohibition is the memorable half. Anywhere this repository encodes a clause
from a gloss, the sanctioned path is the part to go and check.

~~**So: open `PROTECTED_AGENTS.md` Part III before this becomes
`migrations/001_lanes.sql`.**~~ Done. **The remaining warning is narrower and
still live:** I-6, I-7 and I-10 are cited here from §7.4's summary and have
*not* been read at source. Nothing in the DDL turns on them today — I-7's
supersession asymmetry is the first entry on the unenforced list and is a
predicate, not a column — but the next thing that does should open Part II
first, for the reason the paragraph above gives.
