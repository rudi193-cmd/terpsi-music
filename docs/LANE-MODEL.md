# The lane model — schema for W-1 and W-3

**Status:** proposed. Canonical for the reasoning behind
`docs/schema/001_lanes.proposed.sql`, which is the DDL. `docs/ARCHITECTURE.md`
governs everything else; `docs/SENSITIVITY.md` governs the rungs. This document
carries no numbered sections — a `§N` here always refers to the architecture.

**Why it exists.** §18 blocker 3: W-1 and W-3 are schema decisions rather than
modelling preferences, §8 is an entity sketch with no fields or keys, and
retrofitting either clause later is a data migration across every table that
references a student. Migration 001 could not be written from what was on the
page.

> **Read the provenance note at the bottom before building on this.** It rests
> on a one-line paraphrase of a charter this session could not open, and that
> is a materially weaker footing than the sensitivity ladder stands on.

---

## The two clauses, and what each costs

**W-1 — a lane, not an account.** Separate storage, permissions and audit trail
*from the steward's first act*, with no shared "family" partition. The
operative words are *first act*: this is §5's per-subject partitioning, but
created at the first write rather than assembled when someone requests erasure.

**W-3 — lanes are mutually sealed.** Default deny between wards, and *"a shared
event is two lane entries with one referent."* Two students at one rehearsal is
two records.

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
permits `L1`–`L4`. The ladder's top rung is not policy-excluded, it is absent
from the constraint, so a grant purporting to serve `L5` fails at write time.

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
| | `reconciled_session` |

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
| `field_classification` held 0 rows against 87 columns | All 93 columns seeded, coverage asserted in the suite and in CI |

**Three of the four were declarations without enforcement**, written into a
migration whose own document names that defect — "append-only" in a comment
above three tables that were not, and a set of allowed target kinds in a
comment above a column that accepted anything. §7.2's rule is the one that
catches this: *say which*. A label is a ledger.

The fourth is worse in kind, because the empty registry made the ladder
decorative. `docs/SENSITIVITY.md` says an unclassified field is a build
failure; there was no build failure, because there was nothing to check
against.

---

## What the DDL still cannot enforce

Invariants stated in the schema's comments and **not** expressible as
constraints. Naming them here is the §16 discipline: a declaration without an
enforcement is a pair, and the middle is the code that closes it.

**The four §18 item 3 names are now closed, and each entry below says where.**
The `self` edge's holder closed on 2026-07-30 with `is_self_edge()`; the other
three closed together, because they turned out to be the same kind of thing —
**predicates over the acting principal**, which is why none could be a column
CHECK and why all three landed in `records/` beside the read predicate rather
than in ledgers of their own.

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

**W-3's default deny.** The schema partitions; it does not enforce that a query
stays in its lane. Enforcement is one predicate, compiled once, funnelled
through the single read method — §7's resolver shape, with #127's
authenticate-at-the-read so a fourth read added later inherits the gate.

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
> The distinction matters because the two halves fail differently. Default deny
> unenforced means an *illegitimate* crossing is not stopped, which is recorded
> above. No envelope table means a **legitimate** crossing is not
> *representable* — there is nowhere to put the guardian's signature, the
> purpose, or the expiry, so the only way to serve a real sibling case is to
> not record that it happened.
>
> This is exactly the risk §18 item 3 named: the schema was built from a
> paraphrase, and the paraphrase kept the prohibition and dropped the
> permission. **A ward clause that forbids without providing the sanctioned
> path is not the clause** — W-5's *"agency grows by signature"* has the same
> shape and would fail the same way. Fixing it is a thirteenth table and it is
> not written here, because the DDL stays in `docs/schema/` until item 3's
> other gates clear.
>
> **The thirteenth table exists as a type**: `records/crossing.py`'s `Envelope`
> and `permits()`, which the read predicate calls. One defect in it was found
> while enforcing the default deny and is worth recording, because it is the
> shape this whole document keeps finding: **`permits()` took `subject_id` with
> a `None` default, and a `None` skipped the signer's standing check
> entirely.** So an envelope signed by a guardian whose standing had since
> ended still opened the seal for any caller who did not name the ward. The
> read path always named it, which is exactly why nothing noticed. The
> parameter is now required, in the missing-parameter form `deliver()` uses for
> recipients: you cannot ask whether a crossing is permitted without saying
> whose lane is being opened.

**The `self` edge's holder.** Added to `edge_kind` 2026-07-30 (§18 item 12).
Its defining property is that `holder_id` **is** the lane's `subject_id`, and a
CHECK cannot reach through `target_lane_id` to `lane.subject_id` to say so — so
this is the one edge kind whose meaning the table states and cannot hold. A row
reading `('self', <staff person>, <Ben's lane>)` is accepted by the DDL and
would, unchecked, entitle a staff member through the subject's own door.
`records/standing.py`'s `is_self_edge()` is the middle, called by the read
predicate before any edge matches, and ablated in `tests/ablate.py` as *"a
forged self edge."* A `BEFORE INSERT OR UPDATE` trigger is the DDL-side answer
when this migration stops being proposed. **A fourth entry on this list, and the
first one added by widening the schema rather than by reading it.**

**The rung ceiling.** `access_grant.max_rung` records the ceiling and the
registry is now populated for all 93 columns, so the lookup has something to
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

**Weaker than `docs/SENSITIVITY.md`, and the difference matters.**

The ladder had nothing to verify against — §18 recorded that no definition
existed anywhere in the fleet, so writing one from scratch was the whole task.
This document is different: W-1 through W-7 and I-6/I-7/I-10 **exist**, in
`Willow`'s `PROTECTED_AGENTS.md` Part III, and this session could not open
them. Every clause here is quoted from CLAUDE.md's one-line summary of a
paraphrase in §7.4, which was itself assembled from a reading of a charter
document. That is `P2 Cited` at two removes, and §15's warning about citations
that cannot be re-fetched applies directly.

Concretely, the risk is not that W-1 says something other than "a lane, not an
account." It is that Part III states seven clauses in a *machine register*
whose exact wording is the specification — §7.4 notes the fragment carries two
registers and that *"a clause that cannot survive translation between the two
registers is not yet a clause."* A schema encoding the human-register gloss of
a machine-register clause is exactly the translation failure that sentence
warns about.

**So: open `PROTECTED_AGENTS.md` Part III before this becomes
`migrations/001_lanes.sql`.** Not before reviewing it, not before arguing with
it — before promoting it. The DDL is cheap to revise now and a data migration
across every table referencing a student once it has run.
