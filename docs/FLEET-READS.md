# Fleet reads — the 36 repositories this design rests on

**Status:** work list. Governs nothing. `docs/ARCHITECTURE.md` §14 is the
component map; this is the reading order for verifying it, and the record of
why that verification has not happened.

This document carries no numbered sections: a `§N` here always means
`docs/ARCHITECTURE.md`.

---

## ~~Why it cannot be done yet~~ — WRONG, corrected 2026-07-30

> **This section's central claim was false, and it was load-bearing.** The
> repositories are on GitHub under the `rudi193-cmd` account — the same owner as
> this one — and `Willow`, `safe-app-store` and `safe-app-common-package` are
> **public**. Three were added and cloned from a remote session on 2026-07-30,
> and the reads below were performed. `add_repo`'s cross-owner restriction never
> applied, because there was no cross-owner boundary to cross.
>
> **The cost of the error was not the delay.** This document told `BUILD-PLAN.md`
> that item 0 was structurally impossible remotely, `BUILD-PLAN.md` split its
> whole plan around that constraint, and §18 item 1a was filed as an unreachable
> read for the same reason. One unchecked sentence about infrastructure
> re-planned the project. It is left standing, struck, because deleting it would
> hide how far a false premise travelled (§16, rule 20).
>
> **What was actually true:** §17's note about `~/github/` describes a local
> working layout, not the absence of remotes. This document inferred the second
> from the first and nobody checked. The check was one tool call.

~~§18 item 0 asks for one pass that opens the source behind every **Exists** row
in §14 and either confirms it or downgrades it. That pass requires these 36
repositories and **there is no GitHub organisation to read them from.**
§17 records that everything is a flat peer under `~/github/`, which is
reachable from a local session and invisible to a remote one.~~

Consequences, as originally stated — the first is withdrawn, the others stand:

- ~~**§14's table stays `P2 Cited` for every remote session.** Not as a caveat —
  as a structural fact. Anything written remotely rests on the summary.~~
  **Withdrawn.** Rows can be verified remotely and four now have been. See
  *Reads performed* below.
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

~~**The single highest-value file in the tier** is `apps/marching-arts`'s
resolver, for one question: whether #112's *"payload is `NULL` in the SELECT
list at L3 and above"* is absolute or scoped to principals without an
entitlement edge. `docs/SENSITIVITY.md` assumes scoped. If it is absolute, `L3`
and `L4` are wrong. That is §18 item 1a, and it is one file.~~

**Read 2026-07-30 — and the question was malformed.** It is scoped, so the
assumption held. But the scoping is by *subject identity*, not by entitlement
edge, and band 3 is ACCOMMODATION rather than *Attributed* — the two ladders do
not share a rung. See *Reads performed*. Item 1a was closed as a decision before
this read; the read corroborates the disposition and refutes the framing.

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
by what §18 blocks on. ~~**No repository in this list has been opened.**~~
**Three have, on 2026-07-30** — `Willow`, `safe-app-store` and
`safe-app-common-package`; see *Reads performed*. The remaining 33 have not. The
tiering is a judgement about reading order, not a claim about contents, and the
counts were derived from the tree on 2026-07-30.

---

## Reads performed

First entries in what item 0 asked for. Each row is `P1 measured` — the file was
opened in a clone at the named commit, not summarised.

| Repository | Commit | Read | Result |
|---|---|---|---|
| `Willow` | `c8c96b4` | `PROTECTED_AGENTS.md` Part III | **Confirms §7.4.** All seven ward clauses present and rendered faithfully in `ARCHITECTURE.md`. Draft 0.6, unratified, candidate Article XIV — which §14 already said |
| `safe-app-store` | `b1825f7` | `apps/marching-arts`, `libs/subject-consent` | **Both exist.** 27 apps in the store |
| `safe-app-store` | `b1825f7` | `marching_arts/bands.py`, `policy.py` | **Divergence — see below.** The band scale is not the L-ladder |
| `safe-app-common-package` | `2b3d088` | `src/safe_app_common/no_egress.py` | **Exists**, with `tests/test_no_egress_checker.py` beside it. §9 foundation 4 confirmed |
| `willow-tech-manual` | `5cff7cd` | whole tree, 68 files | **Negative claim CONFIRMED.** Zero occurrences of `sensitiv` and zero `L1`–`L5` tokens in any file. §18 was right that it does not carry the ladder, so `SENSITIVITY.md` was correctly written from scratch |
| `willow-2.0` | `4147013` | `migrations/20260522_bitemporal_all_tables.sql` | **"17 tables" CONFIRMED exactly** — counted from the migration. And this repository is *stricter* than what it adopted; see below |
| `safe-design` | `457cb7e` | `src/safe_design/backends/`, `tests/` | **Three backends** — `css`, `textual`, `curses_backend`. Parity is **enforced, not claimed** |
| `safe-app-willow-grove` | `a2e11b3` | `safe-app-manifest.json`, `bridge/`, `grove/`, `CLAUDE.md` | **§4.3's claim CONFIRMED and understated.** Two listeners, not one; the outbound probe is outside the bridge; no purity test |
| `willow-mcp` | `3815449` | `manifest_admin.py`, `identity_binding.py` | **CONFIRMED.** `confirm-binding` carries *"Do not wire this into an `@mcp.tool()`"*; all four `email_basis` values present with drift surfaced, not silently applied |
| `willow-grove` | `9b8ed75` | `DESIGN_CONSTRAINTS.md`, `CODE_REVIEW.md` | **CONFIRMED**, and it contains something this repository needs — see below |

### The divergence, and why it is the most important thing here

`marching_arts/bands.py` declares **seven bands, `L0`–`L6`**:

```
SELF 0 · ROSTER 1 · CRAFT 2 · ACCOMMODATION 3 · HEALTH 4 · SAFEGUARDING 5 · FAMILY 6
```

`SENSITIVITY.md` is built on **five rungs, `L1`–`L5`**, with different names and
different meanings. Both facts §6 cites are true *of the spike's scale*:
`DERIVE_AT = Band.ACCOMMODATION` is band 3, and `NEVER_SERVED = {SAFEGUARDING}`
is band 5. **They were transplanted by number onto a different ladder** — the
spike's `L3` is ACCOMMODATION; this repository's `L3` is *Attributed*, "anything
identifying a student."

That is §15's own hazard — *"scales never compare as bare integers"* — committed
in the sourcing of the ladder §15 governs. The spike compounds it by using
`IntEnum`, so its bands compare as bare integers by construction; declining to
inherit that was correct and was done for the wrong reason, since nobody had
read it.

**The rule at source is scoped**, which confirms the disposition of item 1a
independently:

```sql
CASE WHEN facts.band >= 3 AND facts.subject_id != :viewer
THEN NULL ELSE facts.payload END
```

But scoped **by subject identity, not by entitlement edge**. Under the spike only
the data subject ever receives their own payload; a guardian reading their
child's accommodation gets the instruction. `SENSITIVITY.md`'s `L4` is looser —
an entitled principal with a declared purpose receives the payload. **That
difference is a live design question and is not resolved by this read.**

Two further findings, recorded where they were found rather than acted on here:

- **The spike ranks `FAMILY` (6) above `HEALTH` (4)**, defined as "family and
  financial circumstance" — where housing status and foster placement live. It
  reached §18 item 11's conclusion independently and went further; this
  repository still places `FINANCIAL` level with `HEALTH`.
- **`SAFEGUARDING` is "routed, never received"**, on the reasoning that *"in
  every leadership-implicating case on the public record, surfacing was
  external, so an intake would digitise a broken path rather than repair it."*
  That is a stronger argument for `L5`'s posture than this repository currently
  makes for its own.


### Three smaller results from the second batch

**A verified negative is worth as much as a verified positive.** §18 asserted
`willow-tech-manual` does *not* carry the `L1`–`L5` definitions, and that
assertion is why `SENSITIVITY.md` exists at all. Had it been wrong, this
repository would have written a second ladder beside an existing one — §16's
canonical/vendored pair, created by the document that forbids it. It was right.
This is the row shape item 0 most needs: *checked, and the claim held.*

**`willow-2.0` is where this repository took `valid_at`/`invalid_at`, and this
repository hardened it.** The source migration adds the pair to 17 tables and
carries **no CHECK constraint on interval ordering** — nothing stops an
`invalid_at` that precedes its `valid_at`. `docs/schema/001_lanes.proposed.sql`
carries eight named ones, and enforces append-only with a trigger rather than a
comment. So the direction of divergence here is the opposite of the
`marching-arts` case: the paraphrase was *stronger* than its source.

Worth transplanting the other way: the source migration names its **exclusions**
— `frank_ledger`, `hook_executions`, `routing_decisions` — as *"append-only
audit/log; historical fact, not mutable state."* That is the same partition
`disclosure_log` sits on here, arrived at independently, and it is a better
statement of the rule than this repository currently writes down.

**`safe-design` is the fleet's worked example of a pair with its middle.**
Three backends, and `test_css_and_textual_agree_on_every_token` asserts them
equal token by token — *"a token cannot mean one color in the terminal and
another on the web."* That is rule 12 discharged in ten lines, in the same fleet
where `safe-app-willow-grove` declares `"surfaces": ["tui"]` and opens a port.
When §18 item 4 lands, this is the backend layer it lands on, and all three
surfaces named in that item's correction have a backend already.

(`curses_backend` is not in the parity test. It consumes palette indices
directly rather than converting them, so the drift the test guards cannot arise
the same way — noted so its absence reads as a fact rather than a gap.)


### Third batch — one claim understated, and one document that should be adopted

**§4.3 understated `safe-app-willow-grove`, in this repository's favour.** Every
element checked out at `a2e11b3`: `"surfaces": ["tui"]`, `privacy_tier
local_only`, `local_processing 1.0`, permissions capped at `lan_listen` /
`lan_send`, and `CLAUDE.md` rule 1 *"No web ports for the dashboard. Portless
means portless."* Against `bridge/app.py:214` binding `0.0.0.0`. Three details
§4.3 does not have:

- **Two all-interface listeners, not one** — `bridge/app.py:137` and `:214`.
- **The outbound probe is not confined to the seam.** §4.3 defends the app by
  noting the rule is scoped to *the dashboard*. But `8.8.8.8:80` is opened in
  `grove/mcp_local.py:317` as well as `bridge/app.py:60` — `grove/` is the app's
  own namespace, not the declared bridge. The scoping defence is weaker than
  §4.3 allows.
- **The app has no purity test at all.** No `test_no_egress.py`, consistent with
  §6's tally of three across twenty-seven store apps.

**`willow-grove/DESIGN_CONSTRAINTS.md` is titled *"Design constraints for the
fresh build"* — and this repository is the fresh build.** Seven constraints.
Number 4 is *"Ship a manifest that something actually validates"*, which is
independently the correction filed against §18 item 4 on the same day, reached
here from the B3 discussion and there from a code review.

It also supplies the mechanism behind the failure, which neither §4.3 nor item 4
had: **the store's manifest lint skips by construction.**
`safe-app-store/tools/catalog_lint.py:71-73` only errors on a missing manifest
when the catalog entry carries a local `path`, and `willow-grove`'s entry has
none. So the declaration surface and the enforcement surface are in different
repositories — the constraint notes the enforcing ACL lives in `willow-mcp`
`gate.py`, not in the store — and an external-repo app falls between them.

That is a **middle that exists and cannot fire for a whole class of entries**,
which is §16's third failure mode with a named line number. It is the strongest
available argument for item 4's requirement that whatever surfaces this
repository declares, *this repository's own CI* validates them.

`DESIGN_CONSTRAINTS.md` carries a *"What to carry over"* section that has not
been read yet. It is the highest-value unread file found so far.
