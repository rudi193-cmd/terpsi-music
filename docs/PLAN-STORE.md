# Plan — the store

**Status:** plan. Governs nothing; `docs/ARCHITECTURE.md` governs, and §18
item 18 is the entry that points here. `docs/PLAN-GUARDIANSHIP.md` is the
precedent for this document's shape: acceptance gates first, mechanism only
where a gate needs one named.

**Written 2026-07-31.** Everything in `records/` is predicates over rows the
caller supplies. The store is where five threads meet in one artifact: rule
11's read-only canonical, the `L3`+ NULL rule, at-rest sealing, the compiled
read predicate, and the disclosure log. Retrofitting any of them is the
expensive direction, so this plan exists before the first write does.

---

## The decisions this plan records

1. **PostgreSQL, settled by the tree rather than by preference.**
   `migrations/001_lanes.sql` is already executed there in CI — fourteen
   tables, triggers, interval CHECKs, twenty-seven forbidden acts refused by
   the guard named in each error. A second engine means a ported schema, and
   a ported schema is the pair-without-a-middle this fleet has lost four of.
   Sovereignty is not the counterargument it usually is: `docs/EXIT.md`'s
   artifact is CSV and plain text, never the database file.

2. **The write model is rule 11 with the seal cascade as its middle.** Writes
   land as **drafts** — the sidecar, writable by the app's role. A named
   human's seal (`records/sealing.py`) **is** the promotion. Sealed rows are
   insert-only history: readable by the app role, rewritable by nobody,
   `invalid_at` the only ending (refusal 3). Two database roles, one existing
   cascade, no new promotion machinery to invent — and no third state for a
   row to hide in.

3. **Payloads sealed at rest per lane; predicate columns clear.** The `L3`+
   rule already says the payload is `NULL` in the SELECT list and only a
   derived instruction is served — so the store never needs to read payload
   contents to answer a query. Payload columns are sealed with
   `records/atrest.py`'s per-lane keys at the seam, before INSERT; rung,
   class, dates and edges stay clear for the predicates. The sensitivity rule
   and the encryption design are the same decision made twice, and the store
   makes them one.

4. **The read predicate is compiled at the store as row-level security, with
   a differential middle.** §7's resolver shape: the lane seal, the edge
   check and the rung ceiling exist as RLS policies per lane, AND as the
   Python predicates already in `records/serving.py`. Two implementations of
   one rule is §16's pair, so the middle ships in the same commit: a
   differential suite that drives the same forbidden acts through both and
   fails on any disagreement. Neither layer is the backup of the other —
   the store is not the only path to a row, and the predicate is not the
   only path to a read.

5. **Error channels from the first read.** Every store read distinguishes
   *errored* from *empty* at the type level — the callable-or-sequence shape
   `records/sending.py` already carries. This closes the majority of
   `tests/test_rule13_acceptance.py`'s `CANNOT_DISTINGUISH` list in one
   move, and each closure flips a finding test, which is the fix landing.

6. **The disclosure log is written in the same transaction as the read it
   narrates.** A read that commits without its narration, or a narration
   without its read, must be impossible at the store — not reconciled after.

7. **The store lives in `store/`, outside `records/`.** `records/` stays
   pure (predicates over rows; `tools/purity.py` continues to hold it to
   zero writes, zero egress). `store/` is the declared write path: the
   manifest gains a write-paths declaration and `tools/sockets.py` /
   `tools/conform.py` gain its reconciliation **in the same commit** (rule
   12; the declaration-without-enforcement pair is the one §16 is written
   about).

8. **Sequencing: the store needs no listener.** The TUI is a local terminal
   against a local connection; the staff/director surface goes live on the
   store alone with the manifest still declaring zero listeners. The guest
   browser and the parent PWA remain a separate decision (§9 item 7) with
   their own trust-surface review. The perimeter grows in two visible steps.

## Gates before the first write

| | gate | who |
|---|---|---|
| G-A | `docs/ESCROW.md` exists: custodians, threshold, rehearsal calendar, recorded and **rehearsed** — R16 flips to a build-failing `S1` at the first at-rest write without it | **maintainer picks; options below** |
| G-B | The `reconciled_session` rung rule is recorded (the three `jsonb` columns at `L4`; the composition-is-max rule written where the seed can cite it) | **maintainer confirms** |
| G-C | Manifest write-paths declaration + its reconciliation, same commit | build |
| G-D | The two-role split exists before the first table is populated — a store born single-role never sheds the habit | build |

## Escrow options (G-A) — pick one, or name a fourth

| | shape | survives | costs |
|---|---|---|---|
| E-1 | **3-of-5 split**: director, district administrator, guardian-council seat, counsel, sealed deposit | any two losses; no single office can act alone; the guardian seat is the adverse interest | five real people, an annual rehearsal that actually convenes them |
| E-2 | **2-of-3 minimal**: director, district, sealed deposit | one loss; simplest to rehearse | director + district can act together without any adverse-interest party present |
| E-3 | **2-of-3 with the guardian seat**: director, guardian-council seat, sealed deposit | one loss; adverse interest always required | the guardian seat must be re-appointed as families graduate — a standing process, not a one-time pick |

The recommendation, if asked: **E-1**, for the same reason item 15 went to the
composite — the failure modes differ, and a dispute uses whichever survived.
Whatever is picked, the rehearsal date is declared at issuance with no
default, and an unrehearsed plan reads `UNKNOWN`, never `RECORDED`
(`records/atrest.py` already enforces the states).

## Acceptance is mutation (rule 19) — the forbidden acts, before the code

Written now so the build is graded against a list it did not write for
itself. Each must be attempted and refused, and each refusal ablated:

- The app role rewrites a sealed row; deletes anything; reads a payload
  column in the clear.
- A query crosses a lane without an envelope — through RLS, with the Python
  predicate disabled, and the reverse.
- A sealed payload read from disk without the lane key yields ciphertext,
  and the lane's erasure leaves the chain verifying (`atrest.composes()`
  against the real store).
- An errored connection presents as an empty result anywhere.
- An INSERT into a column the classification registry does not carry.
- A read commits without its disclosure entry; a disclosure entry without
  its read.
- A write path appears that the manifest does not declare — the build fails
  without anyone remembering to check.

## Decomposition, for dispatch after G-A and G-B

- **S-1 — the spine**: `store/` package, roles, migration runner, the
  error-channel adapter, same-transaction narration. Everything else waits
  on it; this one is not parallel.
- **S-2 — RLS and the differential middle** (after S-1).
- **S-3 — the sealing seam**: atrest wiring, escrow disposition surfaced in
  conformance, R16's transition exercised deliberately in a test before it
  happens by accident (after S-1, parallel with S-2).
- **S-4 — the TUI vertical over the store** (after S-2 and S-3): the first
  surface with real data behind it, zero listeners, the knock wired in
  enforcement mode at last — `conform.py`'s `knock-enforcing` row stops
  being a ledger.

## What this plan deliberately does not do

- **Does not open a port.** §9 item 7 is its own decision and its own review.
- **Does not decide custody of the box or the master key.** Deployment acts,
  recorded where deployment is recorded.
- **Does not restate a mechanism.** Every row points at the module or
  document that owns it; where it names one, the gate needed the name.
