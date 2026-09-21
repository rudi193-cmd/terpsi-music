# PLAN-DROP — item 7's in-repo half: the drop producer

Item 7 in `docs/ARCHITECTURE.md §9` is *"Parent PWA + the drop."* §4.2 fixes the
target as option **(b)** — a stateless, ciphertext-only mailbox drop — and §4.3
holds it to the `jeles-remote` bar. `docs/survey/scout-03-relay-localfirst.md`
is the prior-art reading; its closing *"what I would actually build"* is the
blueprint this plan slices.

**Scope of this phase, decided 2026-07-31:** the **drop producer core**, in-repo,
with **no inbound listener** and **no hosted relay**. The hosted relay itself
*"remains unbuilt"* (§4.3) — it is a separate deployment, not this repository's
commit. What lands here is the producer side: a guardian-scoped view sealed into
an opaque, size-bucketed payload; the hold / hand-over / delete drop mechanism as
a **local** store with an owner-bound credential; the cadence/padding control;
and the who-gets-a-drop gate, reused from `records/sending.py`. Everything a
listener, a network, or an identity system would add is tombstoned below.

---

## What already exists, and is reused rather than rebuilt (§16)

| Need | Reused from | Note |
|---|---|---|
| At-rest sealing | `records/atrest.py` | `Keyring`, `LaneKey`/`WrappedLaneKey`, `Sealed`, `available()` (fails loud, rule 13). Per-lane keys under a master; the family-circle seal is a lane seal. |
| Who may be told | `records/sending.py` | `recipients()`, `who_could_see()`, `ContactRestriction`, `SendList`. `deliver()` takes **no `to`** (G4) — the un-passable-parameter discipline the drop's owner-bound credential extends. |
| The §7.1 dated predicate | the edges behind `sending.recipients` | Guardianship ends by `invalid_at`; a contact restriction gates reachability. Both already gate the send list. |
| Rendering | `presentation/ir.py`, `presentation/markup.py` | `View` → escaped HTML (`document`), R6-audited. The guardian's rendered view is the plaintext the drop seals. |
| Guardian-scoped read shape | `console/session.py` (director) | The read-through-RLS-and-predicate shape; the guardian variant is scoped to one student and produces a sealed payload rather than a terminal render. |

---

## Slices

Each slice names the forbidden act its acceptance test attempts (rule 19).

### D-1 — the sealed guardian view

A guardian-scoped assembly: the entries a single guardian is entitled to about a
single student, through the serve predicate, into a `presentation.View`, then
sealed with `records/atrest.py` into an opaque `Sealed` payload. One student per
payload — never a roster row (W-1/W-3). Classifies and seals per **family
circle** (a lane seal). If sealing material is unavailable, the producer returns
`unknown` and lands nothing (rule 13), never a plaintext payload.

**Forbidden act:** a payload that names or resolves to a second student. The test
attempts to assemble a two-student view and requires the refusal.

### D-2 — the drop, as a local store

The `briar-mailbox` shape (scout-03 §1), reimplemented not vendored: an
owner-bound credential where the credential **is** the mailbox binding, so
*"which mailbox?"* is never a parameter a caller supplies. Accept ciphertext,
hold it, hand it over, delete it. A **local** store (no listener, no socket) —
the hold/hand-over/delete mechanism only. Refuses to operate without its key
material (fail-closed, the `jeles-remote` bar, §4.3), and holds **no domain
schema** — the payload is opaque bytes, not a queryable record.

**Forbidden act:** a handle bound to mailbox A requests mailbox B's contents. The
refusal is **structural** — B's contents are unrepresentable from A's handle, not
rejected after a check (scout-03 acceptance test 1).

### D-3 — the cadence and padding control

§4.2's primary control, from `corpus-lens` and SecureDrop's constant-size set
(scout-03 §2, `scout-02-metadata.md`): pad every handed-over payload to a size
**bucket**, and flush on a **fixed cadence** uncorrelated with the event that
produced the drop. Two hand-overs over stores of different sizes produce
identical response sizes. And — the honest half — a test that asserts the leak
that **survives**: weekly cadence is not hidden, stated and measured rather than
implied, `corpus-lens`-style.

**Forbidden act:** a drop whose size or timing tracks its contents. One test
requires byte-identical sizes across unequal stores; a second **asserts the
surviving leak** so the limit is measured, not glossed.

### D-4 — who gets a drop

Reuse `records/sending.recipients` / `who_could_see`: the §7.1 dated-guardianship
predicate and `ContactRestriction` decide who a drop is prepared for. A guardian
under a contact restriction gets no drop, by the same source-shaped property that
makes `deliver()` take no `to` — there is nowhere to put a restricted recipient.

**Forbidden act:** preparing a drop for a restricted or lapsed guardian. The test
requires that the restricted guardian is not in the prepared set, and that the
producer cannot be handed one.

---

## Acceptance (the three that must be able to fail — scout-03, rule 19)

1. **Non-enumerability is structural.** A handle for mailbox A cannot express a
   request for mailbox B; the second-mailbox read is unrepresentable, ablated.
2. **Fail-closed without keys.** The producer/drop started without its key
   material **refuses to operate** and says so (rule 13), never degrades to a
   plaintext or empty payload; ablated.
3. **Constant size, measured residual.** Unequal stores hand over equal-size
   payloads; and the surviving cadence leak is asserted by its own test, so it is
   a disclosed limit rather than an unlooked-for one.

Each lands as an ablation row in `tests/ablate.py` and a forbidden-act test in
the slice's suite; the R16 escrow fuse is unaffected — the drop **seals**, it
does not add a new record-write path (see below).

## R16 note — the drop does not move the escrow fuse

D-1 seals a *derived view* for hand-over; it is not a `store.writing`
record-write, so `tools/audit.py::durable_callers()` stays empty and R16 stays
`FINDING`/`S2`. If a slice writes a sealed payload to a durable local store that
outlives the process (D-2's hold), that is the boundary to check against
`AT_REST_BOUNDARY`: a held sealed payload **is** a byte that outlives the
process. The build must either keep the drop store ephemeral (held in the hub's
already-sealed Zone A) or bring a dated escrow rehearsal — and if it cannot, it
records the transition honestly rather than quietly widening the boundary. **This
is the one R16-relevant decision in the phase and the audit will turn on it.**

---

## Deferred deliberately — tombstones (§16 rule 20)

| Deferred | Why | Successor |
|---|---|---|
| The hosted relay | §4.3: *"remains unbuilt"*; a separate deployment, held to the `jeles-remote` bar | A future ops phase; this plan builds only the producer it feeds |
| Non-enumerable **blinded-challenge** fetch | SecureDrop's own README: PoC, protocol not finalized | Adopt the *pattern* (constant-size set) in D-3; the cryptographic theorem is later |
| Passkey enrollment / device binding | Identity infra; §4.1's device-held credential | A future enrollment phase; D-2's owner-bound credential is a local stand-in, not a passkey |
| The PWA client shell | Client-side artifact (service worker, local decrypt) | Renders a handed-over payload through the existing `surfaces/web`; deferred with the enrollment it depends on |
| SMS gateway | §4.1 notification, item 8's *"Open but small"*; `records/sending.py` already gates who | The signal path, not the record path — never a record on SMS (refusal 7) |
| Edge replica / cryptree / database-per-lane | Zone C; scout-03 §4/§5 | A future replication phase; the lane seal already seals siblings here |

Nothing above is excused — each is a named middle owed a later commit, not a gap.
