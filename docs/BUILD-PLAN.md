# Build plan

**Status:** plan. Governs nothing; `docs/ARCHITECTURE.md` governs. No numbered
sections — a `§N` here is always the architecture's.

**One page on purpose.** If this file grows past two screens it has stopped
being a plan and become another thing to read. Everything here points at a
decision or a task; it never restates a mechanism.

**Pruned 2026-07-30.** Earlier revisions accumulated struck blocks under the
tombstone discipline until the file argued against its own first rule.
`willow-grove/DESIGN_CONSTRAINTS.md` settles the tension: *"when a constraint
stops being relevant, delete it and say why in the commit message — a stale
constraint is worse than none, because it trains people to skip the list."* The
removed material is in `docs/FLEET-READS.md` and in §18's own tombstones, which
is where it belongs.

**Finalized 2026-07-31.** The two decisions that blocked — §18 items 4 and 15 —
are taken by the maintainer and recorded in place there; this file only points.
This revision also corrects two places where this file had drifted behind §18
and the tree — it listed the exit line as unwritten after `docs/EXIT.md` landed,
and the crossing-envelope table as absent after `records/crossing.py` shipped.
Both were this file's defect (the doc wins; rule 12's pair, drifting), fixed by
deletion per the pruning rule above.

---

## Are the ducks in a row

**Yes, as of 2026-07-31. Decision-blocked no longer — what remains is effort,
and it is ordered below.**

- **Item 15 is decided: the composite.** Anchors witnessed three ways —
  OpenTimestamps weekly, a legible annual deposit, guardian receipts
  continuously — because they fail differently and a dispute two years out
  uses whichever survived. The shapes exist (`records/witness.py`,
  `records/receipts.py`); **the wiring landed 2026-07-31**
  (`records/publication.py`, `docs/WITNESS-DEPOSIT.md`) and what remains of
  order item 3 is a dependency decision, not a task — see below.
- **Item 4 is decided: `scout-21` §3, adopted.** Four rendering backends over
  one presentation-IR middle, three trust paths, and the `presentation/` +
  `surfaces/` layout that section names. Layout is unblocked, and with it item
  3's promotion gate.

## Where the tree actually stands (2026-07-31, derived by looking)

```
migrations/    001_lanes.sql — fourteen tables, run against PostgreSQL 16;
               five-part tombstone at docs/schema/
presentation/  the middle — IR, tokens, one mapping table, rendered/ diffed
surfaces/      four doors on ls — tui, web, print, text; skeletons
manifest.json  four surfaces, zero listeners, zero outbound; reconciled in CI
craft/         text-only: no student data, no network, no model
records/       the domain core; suite green
inference      GUARD ONLY — refusal 1 asserted in records/inference.py;
               no call site exists to route yet, which is the point
tools/         conform, sockets, purity, providers, discipline — checkers
               exist BEFORE the things they check, so those cannot be
               born wrong
```

## Order

1. ~~**The surfaces skeleton.**~~ — **Built 2026-07-31, audited and merged** —
   `presentation/` (IR, tokens, the one mapping table, committed rendered
   artifacts diffed in CI) and `surfaces/{tui,web,print,text}` — four doors on
   `ls`, thin renderers, no framework. `manifest.json` landed in the same
   commit as the reconciliation that checks it, per item 4's obligations.
   Honest limits, recorded there and held here: these are skeletons — no
   server, no session, and scout-21's three trust paths are docstrings, a
   ledger not an enforcement; and the IR does not re-check W-1 (a `Serving`
   carries no lane id), so the cross-lane refusal lives in `serve()` alone —
   a named gap.
2. ~~**Promote the lane DDL.**~~ — **Built 2026-07-31, audited and merged** —
   `migrations/001_lanes.sql`: fourteen tables, `crossing_envelope` (W-3's
   permission) and `self_widening` (W-5's) encoded structurally, executed
   against PostgreSQL 16 with 27 forbidden acts refused each by the guard
   named in its error. Item 4 was found not to gate it. The
   stated-and-unenforced list drops to three — `edge_self_holder_is_subject`
   is now a trigger, and writing it found the mirror row (a ward holding
   `guardian_of` over itself) that would have signed its own envelope.
3. ~~**Wire the witness composite.**~~ **Built 2026-07-31** —
   `records/publication.py` and `docs/WITNESS-DEPOSIT.md`. The weekly payload,
   its register and the states around a proof that never came back; the annual
   deposit as a procedure with a dated disposition when it is missed. **One
   thing is left and it is a decision, not effort: Ed25519 issuance.** The seam
   takes either backend, the absence is `ABSENT` in the conformance record
   rather than inferred, and adding an asymmetric primitive means adding this
   repository's first dependency — a maintainer's call. Until it is made, no
   deployment claim rests on a third party attributing a receipt.
4. ~~**Refusal-1 by assertion**~~ — **Built 2026-07-31, audited and merged** —
   `records/inference.py` asserts on what actually answered, with five refusal
   states and no field a caller could use to allowlist a provider;
   `tools/providers.py` watches by AST for a call site that skips the guard,
   wired into `conform.py` and honestly `UNKNOWN` while nothing here infers.
   The ordering held: the guard exists first, so an inference path cannot be
   born unguarded. Opening the upstream found `llm_edge.py` discarding
   `provider_used` and a fourth chain mode posting to another node's local
   runner — which is why the guard checks the address as well as the label.
5. ~~**The rule-13 acceptance test** (was C3)~~ — **Built 2026-07-31,
   audited and merged** — `tests/test_rule13_acceptance.py`. Every seam broken
   rather than skipped, and the breakage found three places where a source
   that could not be reached read as one that answered *nothing*:
   `voice.check()` with no rules loaded, `sockets.declared_from` on a manifest
   with no `listeners` key, and `purity.egress` dropping the unparseable file
   that `purity.writes` reports. All three fixed and ablated. Seven more seams
   fail **closed** and cannot say *why* — listed in that file's
   `CANNOT_DISTINGUISH`, each with a test that goes red when it is fixed. The
   sharpest, `Ledger.log_for` answering for a lane it has never heard of,
   needs a decision rather than a test and belongs in §18.
6. **Then §9's list in its existing order** — noting foundations 1 and 2 are
   **to build**, not built; the spike retired and nothing was inherited.

Anytime, no dependencies: extend `craft/` (text-only). Still gated: the
`docs/survey/*.md` §N sweep waits on the routing decision in `scout-25` part 5.

## What is settled

Six §18 items closed across 2026-07-30/31 — 1, 1a, 2, 4, 11 and 15 — each
struck in place with its resolution, and items 5–10, 12 and 13 resolved or
built per their own entries. `docs/SENSITIVITY.md` is canonical for the ladder;
§14 carries a per-row `VERIFIED`/`UNVERIFIED` state enforced by
`tests/test_component_map.py`.

**The lesson worth carrying forward**, because it will recur: a claim sourced
to a spike is a decision nobody has taken yet, wearing the costume of a fact.
Some of §14's `UNVERIFIED` rows are the same shape; opening the files will not
fix those.

## What this plan deliberately does not do

- **Does not re-order §9.** Its ordering principle — expensive-to-retrofit
  first — is sound.
- **Does not schedule.** No dates. The remaining items are effort, but
  estimating effort here would still be fiction.
- **Does not restate a mechanism.** Every row points at the document that owns
  it. If a mechanism appears described here, that is a defect (§16).
