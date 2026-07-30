# Fleet reads — the 36 repositories this design rests on

**Status:** work list. Governs nothing. `docs/ARCHITECTURE.md` §14 is the
component map; this is the reading order for verifying it, and the record of
why that verification has not happened.

This document carries no numbered sections: a `§N` here always means
`docs/ARCHITECTURE.md`.

---

## Why it cannot be done yet

§18 item 0 asks for one pass that opens the source behind every **Exists** row
in §14 and either confirms it or downgrades it. That pass requires these 36
repositories and **there is no GitHub organisation to read them from.**
§17 records that everything is a flat peer under `~/github/`, which is
reachable from a local session and invisible to a remote one.

Three consequences, all of which should be stated rather than discovered:

- **§14's table stays `P2 Cited` for every remote session.** Not as a caveat —
  as a structural fact. Anything written remotely rests on the summary.
- **`Nestor` may be unreachable even locally-authorised.** §17 flags it: it is
  the sole occupant of `Die-Namic-Systems`, and *"`add_repo` refuses cross-tier
  and a session can hold one owner's repos or another's, not both."*
- **Some of these names are known dead.** §15 records fifteen store manifests
  naming a `repository` that does not exist — `safe-app-private-ledger`,
  `safe-app-the-squirrel`, `safe-app-utety-chat`, `safe-app-ask-jeles` among
  them. Bare names are used throughout below; expect misses.

---

## Tier 1 — required to clear §18's four blockers

Seven. Everything else can wait behind these.

| Repository | Why it is first |
|---|---|
| `safe-app-store` | Holds `apps/marching-arts` and `libs/subject-consent`. **Blocker 2 is a decision about this repo's contents** |
| `Willow` | `PROTECTED_AGENTS.md` Part III — the seven ward clauses W-1…W-7 that `docs/LANE-MODEL.md` encodes from a paraphrase. Also Schedules A and B |
| `willow-2.0` | `valid_at`/`invalid_at` across 17 tables, the mechanism §7.1 adopts. Plus `TRUST.md` and `SECURITY_AUDIT.md` |
| `safe-design` | Tokens and structurally-parity backends. **Blocker 4** picks which backend is load-bearing |
| `willow-mcp` | Three-key egress, the envelope, serve mode, and PR #211's verification-apparatus defects |
| `willow-tech-manual` | §18 claims it does **not** carry the `L1`–`L5` definitions. That claim is why `docs/SENSITIVITY.md` was written from scratch and it should be checked |
| `willow-grove` | §14 ends *"Read before building"* — `FLEET_SEAMS.md` and `DESIGN_CONSTRAINTS.md` |

**The single highest-value file in the tier** is `apps/marching-arts`'s
resolver, for one question: whether #112's *"payload is `NULL` in the SELECT
list at L3 and above"* is absolute or scoped to principals without an
entitlement edge. `docs/SENSITIVITY.md` assumes scoped. If it is absolute, `L3`
and `L4` are wrong. That is §18 item 1a, and it is one file.

## Tier 2 — code this would actually depend on

Eight.

`safe-app-common` (canonical purity checker, `no_egress`) ·
`willow-gate` (the knock, `friction_floor`) ·
`willow-data-vault` (Zone A sealing) ·
`kartikeya` (bubblewrap isolation) ·
`willow-config` (`willow.md`, `settings.global.json`, `kart-sandbox.json`) ·
`Nestor` (resolver, reconciler, seal cascade, `Curator.servable`) ·
`jeles` (verified answers in front of inference) ·
`nest-seed` (digitisation, `nest_promote`/`nest_digest`)

## Tier 3 — read once, for a pattern

Twenty-one.

`law-gazelle` · `UTETY` · `private-ledger` · `almanac-template` ·
`almanac-data` · `oakenscrolls-office` · `field-acoustics` · `quiet-corner` ·
`corpus-lens` · `story-timeline` · `ask-jeles` · `jeles-remote` ·
`civics-check` · `the-squirrel` · `yggdrasil-training-data` ·
`awesome-sovereign-software` · `willow-seed` · `willow-compose` ·
`openclaw-sap-gate` · `DispatchesFromReality` · `safe-app-willow-grove`

**Two in that list are read for what they get wrong**, and should be approached
that way. `quiet-corner` is the nearest sibling this app has and its
`session_scope` is declared per field and enforced nowhere (§7.3).
`safe-app-willow-grove`'s manifest declares `"surfaces": ["tui"]` and the app
opens a port (§5).

## Excluded, deliberately

`willow-memory` and `willow-bot` appear only as passing examples in §14 and
§17 and are mapped to no component. Listed here so their absence reads as a
decision rather than an oversight.

---

## What a completed pass must leave behind

§18 item 0's own requirement: *"the pass itself should leave a record, because
an unverified table and a verified one look identical."*

Minimum per row of §14: which file was opened, at which commit, and whether the
**Exists** claim survived. A row that was checked and confirmed and a row that
was never opened must not render the same, which is the same defect as §15's
silently-decayed `P2` and wants the same fix — a status alongside the claim,
and a record of what was observed rather than only what was concluded.

`almanac-template`'s `catalog-entry.schema.json` is the worked solution and
§15 says to adopt it wholesale: `status` ∈ `live · revised · moved ·
redirected · superseded · dark · frozen`, with `observed` recording machine
facts and `status_source` ∈ `auto · curator` recording who decided.

---

## Provenance of this file

Assembled by extracting every backticked repository name from
`docs/ARCHITECTURE.md`, `docs/CAPABILITY-MAP.md` and `CLAUDE.md`, then sorting
by what §18 blocks on. **No repository in this list has been opened.** The
tiering is a judgement about reading order, not a claim about contents, and the
counts were derived from the tree on 2026-07-30.
