# At-rest sealing across the Zone A boundary

**Status:** canonical for its own subject, in the way `docs/LANE-MODEL.md` and
`docs/SENSITIVITY.md` are for theirs. `docs/ARCHITECTURE.md` §5 governs the
design; where §5 underspecifies, the decision is recorded here and carried to
§18. Where this file and §5 disagree, §5 wins and this file is the defect.
`records/atrest.py` is the code; `tests/test_atrest.py` is what holds it.

§9 lists five foundation items and marks the third half-built: *"chain
integrity and per-subject erasure are built; at-rest sealing across the Zone A
boundary is not."* This is the second half, written to be propagated — §9 says
what this app lands in foundation 1–5 is what every later app inherits.

---

## What is built, and what it is worth calling

Rule 18, first, because the answer is the part most worth getting precise.

**This section said "a mechanism and a ledger, not a gate" until 2026-07-31, and
it was accurate: nothing routed through it, because there was no store.** S-3
changed that and the sentence has to change with it rather than be left as a
flattering understatement in the other direction.

**It is enforcement on the store's write path, and a mechanism everywhere else.**
`store/writing.py` routes every payload for a sealed-class column through
`seal_bytes()` before the `INSERT`, and there is no code path that spells a clear
one: the clear column is tombstoned by `migrations/004_sealed_payloads.sql` and
constrained to `NULL`, the envelope columns are refused by name if a caller tries
to write one, and a hand-written `INSERT` going round the adapter entirely is
refused by `lane_entry_payload_sealed_is_ciphertext`. Which columns those are is
**derived** (`store/sealing_plan.py`), not listed, and the migration is
reconciled against the derivation in both directions.

**What is still not decided here** is the same list as before, unchanged: where
the master lives, who holds escrow shares, and whether a *deployment*'s store is
sealed. What S-3 settled is that when one is, this is how.

What *is* enforcement on the reading path: `reconcile()` runs before any
ciphertext is touched, and `unseal()` routes through it rather than beside it.
`tests/test_atrest.py` asserts that routing against the source, so removing the
call is a failing test rather than a silent downgrade.

**And the store does not unseal.** Reads return the `Sealed` envelope; the caller
holding the lane key opens it. That is §6's core/seam partition, and it is a
guard rather than a paragraph — `tests/test_sealing_plan.py` scans `store/` for
the opening verbs and fails on any of them. The reason it costs nothing is §5's
own `L3`+ rule: above the derive floor `records/serving.py` serves an
*instruction* and never the payload, so a store that cannot open a payload still
answers every question the resolver asks.
`tests/test_store_atrest.py::test_serve_at_L4_completes_without_a_single_unseal`
instruments the three opening verbs and requires zero calls.

## The hierarchy as built

    Master key            — never touches a record; wraps lane keys and nothing else
      └─ Lane keys        — one lane, one key; random, wrapped, destroyable
           └─ Sealed payloads — each naming its lane, its key id and its scheme

Three tiers where §5 draws four, and each departure is a decision rather than
an omission.

| | §5 as written | as built | why |
|---|---|---|---|
| middle tier | group key per **access circle** | one key per **lane** | a circle key spans students; erasing one then means erasing seven |
| lane key | DEK per record, wrapped per circle | one key per lane, wrapped under the master | per-record keys are a wrapping table the size of the store and buy nothing the lane boundary does not |
| derivation | not stated | **random, never derived** | a derived key is recomputable from the master forever, so destroying it destroys nothing |
| wrapping | X25519 + HPKE | symmetric, under the master | the asymmetric property is unused inside Zone A, and the accepted dependency carries no HPKE |
| record cipher | AES-256-GCM | Fernet | what the one accepted dependency carries; authenticated; context bound inside the plaintext rather than through AAD |
| master custody | TPM/HSM on the hub | **not decided here** | the core takes key material as an argument and persists nothing |

### The decision that matters most

**Lane keys are random and wrapped, not derived.** `HKDF(master,
info=lane_id)` is cheaper — nothing to persist, no wrapping table — and it
cannot pass §5's own erasure test: *"one member's history is deletable without
touching anyone else's."* A derived key comes back the moment anyone holds the
master, so an erasure that destroys it destroys a cache. A random lane key
wrapped under the master goes when its wrapping goes, which is the only reason
rotation and erasure can both be true at once.

### One lane, one key

W-1 asks for separate storage, permissions and audit trail per ward. A key tier
organised by circle confines that to storage: seal every Ensemble 7 student under
one key and rule 8's roster column has moved down a layer, where it is harder
to see and harder to migrate out of. So a lane id that names a set — `all`,
`*`, `the drumline` — is refused at minting, and a key id already bound to one
lane cannot be registered against another.

## Rotation, and the thing everyone gets wrong

**Re-wrapping under a new master must not require resealing a single record,
and does not.** A sealed payload names the *lane key*; it never names the
master. So the cost of rotating a master is the number of lanes, not the number
of records — `tests/test_atrest.py` compares the sealed objects before and
after rather than trusting this sentence.

Three separate acts, kept separate because §5 treats them as different
decisions:

* **`rewrap()`** — master rotation. Every lane key re-wrapped, no payload
  moved, no key id changed.
* **`rotate_lane_key()`** — §5's **forward-only** revocation. A new lane key is
  minted and the old wrapping is kept, so last season's records still open.
  Correct for the graduated senior's parent who legitimately saw them.
* **`reseal()`** — full re-encryption of history. §5 reserves it for a custody
  order or a terminated staff member, so it is a call somebody has to reach
  for, and it refuses to cross lanes.

**Rotating the master does not inherit the old escrow disposition.** The shares
held for the old master do not reconstruct the new one, so the new master reads
`ABSENT` the moment the rotation returns. That is the intended reading and it
is asserted, because a rotation that quietly carried the disposition forward
would be the most dangerous kind of quiet.

## Erasure, and the chain that survives it

§5's hardest paragraph is the one where consent transitions are links in a
chain the whole corps depends on. `records/disclosure.py` answered it by
partitioning per lane. The other half is here: **destroying a lane's key makes
that lane's payloads unreadable and leaves the chain and its anchors verifying
exactly as before.**

It holds structurally — the chain hashes a *decision* and deliberately never a
payload, so key material is not chain material — and *structurally* is exactly
the kind of reasoning that quietly ceases to hold after a refactor nobody
connected to it. `composes()` is the named middle for that pair (rule 12, same commit).
It reports one of five states rather than a boolean:

| state | meaning |
|---|---|
| `COMPOSES` | payloads unreadable, chain verifies, anchor matches, erasure dated |
| `CHAIN_BROKEN` | the erasure took the chain with it — §5 requires both halves |
| `ERASURE_INCOMPLETE` | a payload still opens, or a wrapping remains |
| `UNRECORDED` | the wrappings are gone with no dated act naming them |
| `NOT_ERASED` | keys still held; nothing was erased |

**Refusal 3 is honoured, not bent.** *Never revoke by deleting* is about
standing — guardianship ends by `invalid_at` so a dated record survives. Key
material here is genuinely destroyed, and the `Erasure` row survives it: who,
when, why, and which key ids. A keyring whose wrappings vanished with no
`Erasure` beside them is `UNRECORDED`, which is a finding — a key that
disappeared is otherwise indistinguishable from one that was lost, and that
distinction is what a guardian is owed.

## Why a payload did not open: never one boolean

§5 forces three of these apart and the module keeps them apart. Collapsing them
into *could not read it* answers a guardian's question with the one phrasing
that is never true, which is rule 13.

| state | the fact it reports |
|---|---|
| `UNREADABLE` | the ciphertext does not authenticate: altered, or the wrong key |
| `KEY_DESTROYED` | a named person destroyed the key on a date, for a reason |
| `KEY_UNKNOWN` | nothing here has ever heard of this key id |
| `MISBOUND` | it authenticates and was sealed for a different lane, key or scheme |
| `MASTER_MISMATCH` | the key is held under a master that was not offered |
| `SCHEME_UNKNOWN` | a payload from a later build, which is not the same as damage |

The last three are here because they are distinct operational facts rather than
flavours of failure. `MISBOUND` exists because Fernet has no associated-data
parameter: the context §5 would bind through AES-GCM's AAD is bound by sealing
the header **inside** the authenticated plaintext, so editing an envelope's
lane produces a payload that refuses rather than one that opens into the wrong
lane.

## Escrow: surfaced, not solved

§5 calls single-file key loss *"the failure mode that ends the program"* and
proposes shares across the director, a board administrator and a sealed offline
share, rehearsed annually. **None of that is decided, and a module that decided
it would be taking a maintainer's decision.**

So what is built is the *shape* of a disposition and no policy: it does not say
how many shares, what threshold, who may hold one, or how often the drill runs.
What it refuses to do is stay quiet.

| state | when |
|---|---|
| `ABSENT` | no disposition is recorded for this master — §5's program-ending failure, as a state |
| `UNKNOWN` | a disposition exists and has never been rehearsed. §5: *an untested key recovery is not escrow* |
| `RECORDED` | rehearsed, inside the window it declared |
| `STALE` | rehearsed, and the drill it declared next is overdue |

The next rehearsal date is **declared at issuance with no default**, which is
the clause `records/dispositions.py` states as P-2 — a default would let issuers stop
declaring. The survey is derived from the wrappings rather than from a list
somebody maintains, so a master that is depended on and appears in no escrow
record is the row that surfaces.

`tools/conform.py` carries this as `key-escrow`. ~~It reads `ABSENT` today~~ **it
reads `UNKNOWN` since 2026-07-31**, and the change was earned by a decision
landing rather than by the check softening: gate G-A picked `E-1` — 3-of-5 across
five custodian roles, `docs/ESCROW.md` — and migration 004 means a sealed store
can exist here. `ABSENT` would now be claiming nothing had been decided about
something that had.

`UNKNOWN` is the middle rung and both walls matter. Not `ABSENT`, because a
policy is recorded and *nothing decided* is a different fact from *decided and
never drilled*. Not `PASS`, because §5 is flat: *an untested key recovery is not
escrow*, and `docs/ESCROW.md` records zero rehearsals on purpose — the first one
is an install-acceptance act (§11.1) and happens in a room, not in CI. The row
goes green the day that document gains a dated rehearsal, and
`tests/test_conform.py` drives that transition against a synthetic document
rather than waiting for it.

## What this does not decide

Carried to `docs/ARCHITECTURE.md` §18 rather than left here to be found:

1. **Whether the canonical store is sealed at rest at all.** §5 poses it
   directly — *"decide deliberately whether student records need more than
   filesystem permissions plus a `0700` box"* — and this module makes either
   answer expressible without preferring one.
2. **Who holds escrow shares, at what threshold, on what drill calendar.**
3. **Where the master lives.** §5 says TPM/HSM-sealed on the hub; nothing here
   reads or writes it, and the install-acceptance step that would check it does
   not exist.
4. **§5's crossing-to-B/C column is not built.** Sealing *per family circle for
   a crossing* is a different operation from sealing at rest, wants the
   asymmetric property this tier does not use, and belongs beside
   `records/crossing.py` when there is something to cross to.
5. **Per-record keys.** §5's DEK-per-record is not built and is not obviously
   wanted; the lane is the boundary every other clause in this design uses.

## Two things worth knowing about the code

**Nothing here touches the filesystem or the network**, which is §6's core/seam
partition rather than a style preference: `seal_bytes()` returns an artifact
and the caller persists it, exactly as `records/export.py` returns
`(name, media type, text)` and the caller writes. `tools/purity.py` is pointed
at the module and `tests/test_atrest.py` runs it there directly.

**The dependency import is lazy and refuses rather than degrading.** A box
without a usable primitive still imports `records`, and then raises
`PrimitiveUnavailable` rather than storing a record in the clear — the argument
`records/receipts.py` makes for `AsymmetricUnavailable`, where a silent
downgrade would make two very different states look identical at every call
site.

---

*Every count and every state name above is derived from `records/atrest.py` and
`tests/test_atrest.py` as they stand, not from an earlier draft of either.*
