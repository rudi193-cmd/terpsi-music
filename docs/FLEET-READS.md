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
  **Withdrawn.** Rows can be verified remotely, and the pass has since
  completed: **41 of 41 exists-rows verified at source as of 2026-08-01** (see
  *The pass, completed* below and §14's enforced note). The *"four"* this bullet
  first reported was the 2026-07-30 start, not the finish.
- ~~**`Nestor` may be unreachable even locally-authorised.** §17 flags it: it is
  the sole occupant of `Die-Namic-Systems`, and *"`add_repo` refuses cross-tier
  and a session can hold one owner's repos or another's, not both."*~~
  **False, 2026-07-30 — and false in the same family as this section's main
  premise.** `Nestor` is at `rudi193-cmd/nestor` and cloned with no cross-tier
  obstacle. §17's placement reads *"is going to be the only repo under
  `Die-Namic-Systems`"* — future tense, a decision not yet executed. This bullet
  turned an unexecuted plan into a present-tense access barrier, which would
  have deterred exactly the read that disproved it.
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
facts and `status_source` ∈ `auto · curator` recording who decided. (Confirmed
by reading the schema directly on 2026-08-01 — see below.)

---

## The pass, completed — 2026-08-01

§18 item 0's pass is done. **41 of 41 §14 exists-rows are verified at source**,
the figure derived and enforced by `tests/test_component_map.py` (the header note
reads `41 of 41`). The one row naming no fleet source — scale-direction — is
built here (`presentation/scales.py`), not a fleet claim.

- **How.** Read through the GitHub API (`get_file_contents`/`search_code` at a
  pinned sha), repositories brought into scope with `add_repo` where needed
  (`SAFE`, `willow-config`, `willow-compose`, and the standalone app repos), and
  the one cross-owner repo (`almanac-template`) over the public web. No local
  `~/github/` checkout and no GitHub organisation were required — the struck
  section at the top of this file was wrong about that, and this pass is the
  proof.
- **Corrections the pass forced, carried in §14 in-cell.** SAFE `HARD_STOPS`
  carries no under-13 stop (the COPPA governance is `UTETY` ground rule 4 only);
  `willow-compose` is not itself a family-data app (it *excludes* family data);
  `private-ledger` is a shipped app, not a template, and its injected `ingest`
  promotes aggregates *outward*, not a data-source bridge; `oakenscrolls-office`
  calibrates one user's own forecasts, not judges; `ask-jeles` persists more than
  the row claimed. Each is a `VERIFIED` row that diverged from the prose and now
  says so.
- **Two fleet facts worth carrying.** `willow-config` commits its `mcp_apps/`
  manifests (only the grant subdirs are gitignored) — this app's refusal 2 is
  stricter; and its tracked `env` sets a cloud inference fallback chain
  (`WILLOW_INFERENCE_PROVIDER=auto`), the fail-open posture this app's refusal 1
  inverts.

---

## Provenance of this file

Assembled by extracting every backticked repository name from
`docs/ARCHITECTURE.md`, `docs/CAPABILITY-MAP.md` and `CLAUDE.md`, then sorting
by what §18 blocks on. ~~**No repository in this list has been opened.**~~
~~**Three have, on 2026-07-30** — `Willow`, `safe-app-store` and
`safe-app-common-package`; see *Reads performed*. The remaining 33 have not.~~
**The pass completed 2026-08-01: every §14 exists-row was opened at source** —
the 2026-07-30 reads plus the 2026-08-01 waves across willow-gate, nestor,
willow-mcp, UTETY, kartikeya, jeles, jeles-remote, the `safe-app-store` apps,
`SAFE`, `willow-config`, `willow-compose`, and `almanac-template` over the public
web (see *The pass, completed*). The tiering is a judgement about reading order,
not a claim about contents, and the counts were derived from the tree.

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
| `Nestor` | `111c187` | `nestor/curator.py`, seal states | **CONFIRMED.** `Curator.servable` at `curator.py:82`, `unverifiable()` at `:118`, cascade `sealed`/`draft`/`pending` all present. **But it is at `rudi193-cmd/nestor`, not `Die-Namic-Systems`** |
| `willow-gate` | `3092de5` | `src/willow_gate/friction_floor.py` | **CONFIRMED**, and it is a sibling of this repository's `voice.py` — see below |
| `willow-data-vault` | `b634de0` | `README.md`, `schema/` | **CONFIRMED.** Three-layer architecture, `vault.key` + Fernet. Nine files: schemas and bootstrap only, *"never data"* |
| `quiet-corner` | `1230e96` | `qc-data.js`, `docs/backend-architecture.md` | **§7.3 CONFIRMED exactly.** Eight `*_visible` fields; the source itself states *"API does not enforce them in Tier 1/2"* |
| `corpus-lens` | `0c2a124` | `README.md`, `tests/test_wall.py` | **§4.2 CONFIRMED verbatim**, both halves including the test |
| `UTETY` | `b953e84` | `README.md`, `docs/build-plan.md` | **CONFIRMED**, and the rule is sharper than §18 item 9 records |
| `kartikeya` | `de77d67` | `src/kartikeya/sandbox.py`, `execute.py` | **CONFIRMED.** bwrap isolation, fails closed. **And it contains item 0's fix** |
| `quick-stupids` | `a92389c` | whole tree | **REFUTES this repository's own claim.** No `band/persona.py`, no Python, no tombstone |
| `almanac-template` | — | — | **UNREACHABLE.** `add_repo` refuses cross-tier; `almanac-data` is a different org |
| `jeles-remote` | `cdb2a1d` | `README.md`, `sources.py` | **§4.3 CONFIRMED**, all four criteria; the source count is 65 exactly |
| `Jeles` | `0ae85b5` | `README.md` | **CONFIRMED.** *"The corpus sits in front of live search, it doesn't replace it"* |
| `willow-config` | `4645535` | tree | **CONFIRMED** — all three named files present. And a third `kart-sandbox.json` |

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
`invalid_at` that precedes its `valid_at`. `migrations/001_lanes.sql`
carries ten named ones, and enforces append-only with a trigger rather than a
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

---

## `willow-grove/DESIGN_CONSTRAINTS.md` — read in full, `9b8ed75`

Seven constraints, written for a *fresh build* of Willow Grove. This repository
is a fresh build of a different app in the same fleet, and five of the seven
transfer without translation. Its own framing is the reason to take it
seriously: **"a constraint without a test is a preference"** — rule 19, arrived
at independently — and every constraint carries a *how to check you complied*.

It also carries an explicit confidence caveat: constraints 2–5 rest on an
automated survey *"that has not been independently re-verified."* Treated
accordingly below.

| | Constraint | Maps to | What this repository does not have |
|---|---|---|---|
| 1 | **Never render absence as assurance** | rule 13 | **the test, and the type** |
| 2 | Do not create schema you do not own | §16 | — (owns its schema) |
| 3 | Decide the human-queue question out loud | rule 13, applied to *scope* | the labelling half |
| 4 | Ship a manifest that something actually validates | §18 item 4 | already filed |
| 5 | Do not become the third fork | §18 item 2 | — (spike retires) |
| 6 | Keep the bus contract single-valued | §15 | — (no bus yet) |
| 7 | Do not add a fifth Grove name | fleet-noun rule | — |

**Constraint 1 is the one to take.** It is rule 13 with two things rule 13 does
not have:

- **A type, not a discipline.** *"A reader function returns `Result[list] |
  Unreachable`, not `list`. The renderer must be unable to display 'clear'
  without having actually received an answer."* Rule 13 says absence surfaces as
  `unknown`; this says make the alternative unrepresentable.
- **A runnable acceptance test.** *"Point the app at an unreachable DSN in CI
  and assert no surface reports health."* Rule 13 currently has no test in this
  repository at all — it is a declaration, which by §7.2's own distinction makes
  it a ledger.

Its evidence is worth reading before this repository builds any surface: the
same fail-soft appears **18 times** in one file, and the pane whose stated
purpose is that automation pauses until a human acts renders a dead database as
`✓ queue clear` — *a green check on the failure.*

**Constraint 3 adds a half rule 13 is missing.** Absence of *reachability* is
covered here; absence of *scope* is not. A pane that shows a real answer from
one of two sources, unlabelled, is not unreachable and is still misleading. The
check is behavioural and good: *"ask someone who has not read this file — does
this pane show everything the fleet has escalated? If they cannot answer from
the UI, it fails."*

**Constraint 2 supplies the sharpest concrete instance of §16 in the fleet.**
`willow.routing_decisions` is created by both `willow-2.0/core/grove_reader.py`
and `safe-app-willow-grove/schema.sql`, different shapes, both `IF NOT EXISTS`
— so **boot order silently decides the schema and the loser no-ops.** No error
at create, none at boot; the failure arrives later, in a query, on someone
else's machine. §16 argues this abstractly; this is the worked example.

### Two things to carry that this repository has not written down

- **No surface may widen its own permissions.** From
  `willow-mcp/manifest_admin.py:4-9`, quoted in *What to carry over*: manifest
  writes are CLI-only and forbidden from being an MCP tool, because *"an agent
  could otherwise grant itself whatever it was just denied."* That is W-4 —
  *a ward may request, never authorize* — pointed at the software rather than at
  the student, and `CLAUDE.md` has no rule for it. **Proposed, not added:
  writing a new refusal is the maintainer's call.**
- **Fail-closed is a per-call-site decision, not an inherited posture.**
  `willow-mcp/gate.py:13` denies on a missing manifest; Grove's reads fail soft.
  The constraint's point is that reads and grants *may* legitimately differ —
  what is not acceptable is inheriting one by copy-paste. Rule 13 currently
  reads as uniform.

### And one line that indicts this session's own output

> *"When a constraint stops being relevant, delete it and say why in the commit
> message — **a stale constraint is worse than none, because it trains people to
> skip the list.**"*

`BUILD-PLAN.md` is accumulating struck text under the tombstone discipline while
opening with a rule that it must stay one page. Those two disciplines are in
tension, the tension is real, and this sentence is the argument for resolving it
toward deletion-with-a-reason rather than toward accumulation.


## Tier 2, first three — and one pair this repository created without noticing

**`Nestor`'s placement is decided and unexecuted, and §14 does not distinguish
those.** The row reads *"`Nestor` → `Die-Namic-Systems`, sole occupant —
**Decided**"*. §17's prose is future tense, so "Decided" is accurate about the
*decision*; the repository is still `rudi193-cmd/nestor`. A reader taking the
row as a statement about the tree would be wrong, which is item 0's whole
complaint applied to a row that is *technically* right. Its three functional
claims all verify.

**`willow-gate/friction_floor.py` is `voice.py`'s `mirroring` rule, built
first.** This repository shipped a friction detector as a `FLAG`-not-`REFUSE`
rule and argued the position from scratch. `friction_floor.py` states the same
four properties in its docstring:

| `friction_floor.py` | `voice.py` |
|---|---|
| *"a SIGNAL, not a verdict"* | `FLAG` rather than `REFUSE` for `mirroring` |
| *"will false-positive… and false-negative"* | `KNOWN_MISSES`, `NEAR_BOUNDARY` |
| *"lexicons are deliberately small and are NOT claimed to be complete"* | the honesty list, with a test that it stays honest |
| *"it fails loud, not open"* | `refuses()` treats a raise as a refusal |

**That is a pair, and rule 12 says name the middle or do not create it.** The
two are not identical — `friction_floor` watches the agent↔user relationship for
sycophancy, `voice.py`'s rule watches whether the assistant is mirroring a
stressed staff member — but they are the same mechanism against the same class
of harm, and this repository built its own without knowing.

And `friction_floor` carries an argument this repository's version does not, on
a point `voice.py` explicitly defers:

> *"It is DETERMINISTIC and MODEL-FREE on purpose. It never calls an LLM,
> because **a mirror cannot audit itself** — the model that is smoothing you is
> the last thing you'd trust to notice it is smoothing you."*

`voice.py` records that its rule tier is *"the fastest and weakest"* and that
*"the tier above is a classifier."* This says the tier above must not be the
same model that produced the text. That is a constraint on refusal 1's local
model, not just on where it runs, and it is not written down here.

**`willow-data-vault` is a blueprint, and the tiering assumed otherwise.**
Nine files — schema and `bootstrap/provision.sh`, explicitly *"never data."*
§14's row verifies. But Tier 2 above lists it as *"Zone A sealing"*, and there is
no sealing implementation in it to read. That is consistent with §9 foundation 3
already saying at-rest sealing across the Zone A boundary is **not** built; the
reading order was wrong, not the component map.


## The two read for what they get right about being wrong

**`quiet-corner` — §7.3's claim is exact, and the source admits it in prose.**
Eight fields, counted: `roster` · `attendance` · `standards` ·
`knowledge_graph` · `iep` · `behavior` · `parent_contact` · `archive`. And
`docs/backend-architecture.md:453`:

> *"Frontend gates all rendering and request construction on these flags. **API
> does not enforce them in Tier 1/2.**"*

So this is not an undiscovered defect — it is a **documented** one, which makes
it a cleaner example than §7.3 claims. The declaration and the enforcement
disagree, the gap is written down, and nothing fails. §16's point exactly: an
acknowledged missing middle is still a missing middle.

Two things worth taking, neither in §7.3:

- **The defaults encode the ladder.** Three of eight default to `false` —
  `iep_visible`, `behavior_visible`, `parent_contact_visible`. Those are the
  `L4`-shaped ones (health, discipline) plus guardian contact. The vocabulary
  *does* map onto the ladder as §7.3 says, and the **defaults** are where that
  mapping is actually expressed.
- **`parent_contact` defaults closed while `roster` defaults open**, so the app
  treats guardian contact as more sensitive than student roster. This
  repository puts `PII_GUARDIAN` and `PII_MINOR` both at `L3`. Worth a look when
  `L3` is next opened.

**`corpus-lens` — §4.2's load-bearing claim is verbatim, and so is the test.**
`README.md:19-20`:

> *"A custody schedule was once reconstructed from keystroke timing alone —
> content redaction does not scrub the shape of a week."*

And §4.2's harder claim — that the README documents what the wall does *not*
hide, with a test asserting it — is `tests/test_wall.py:147`:

```
def test_weekly_cadence_IS_reconstructable_documented_not_hidden(self):
```

**That is the shape this repository should copy directly.** A test whose subject
is a *limitation* rather than a guarantee, named so it cannot be mistaken for a
failing assertion and quietly "fixed." `voice.py`'s `KNOWN_MISSES` is the same
idea and `corpus-lens` got there first; the naming convention is better and is
free to adopt.

## `kartikeya.resolve_sandbox_config` — item 0's own problem, already solved

The single most transplantable thing found in this pass. Its docstring is §18
item 0's sentence, arrived at independently, about sandbox policy rather than
about a component map:

> *"The fallback used to be silent: a fleet worker started without
> `$KART_SANDBOX_CONFIG` ran on the vendored default indefinitely, producing a
> reduced mount set that is **indistinguishable — from the task result alone —
> from the fleet policy.** Callers that know a fleet policy is expected can now
> detect the drift instead of inferring it from which paths happen to be
> missing."*

Item 0 says *"an unverified table and a verified one look identical."* This says
a defaulted config and a fleet config look identical. **Same defect, same fix:**
`resolve_sandbox_config(root) -> tuple[dict, str]`, documented as *"resolve the
bwrap mount policy AND report which candidate supplied it."*

**Return the value with its provenance, and give the not-found case a name**
(`_NO_CONFIG_SOURCE`) rather than letting it wear the default's clothes. That is
rule 13 as a return type — the shape `willow-grove`'s constraint 1 asks for
(`Result[list] | Unreachable`), already built and in use.

It settles how §14 should carry verification state: not a column of prose, but
**claim plus source**, with an explicit sentinel for "nothing supplied this."
Take this together with `almanac-template`'s `status_source ∈ auto · curator`
and the §14 requirement is fully specified by existing fleet work.

Also confirmed: bwrap isolation is real and **fails closed** — `execute.py:111`
returns `failed` with *"bwrap not found — install bubblewrap"* rather than
running unsandboxed.

**The two `kart-sandbox.json` copies are a pair with a middle, not a drift.**
`kartikeya`'s (2519 bytes) is the product-neutral default and its own
`description` names the override path; `willow-2.0`'s (5452 bytes) is the
fleet-specific override, adding `GROVE_`, `SAFE_` and `DISCORD_` prefixes and
different binds. Reported as designed rather than as drift, because the default
file declares the mechanism. Worth noting anyway that the override only ever
**widens** a sandbox, and nothing observed constrains how far.

## `UTETY` — item 9's line is already drawn, and with evidence

§18 item 9 reads *"practice logging against UTETY's no-leaderboard rule… the
line has to be drawn by someone."* It has been drawn, and it is not the blanket
ban the item implies. `README.md` ground rule 2:

> *"**Feedback is about the work, never the learner** — no 'you're smart', no
> leaderboards."*

`docs/build-plan.md` carries the citation and the sharper form: Kluger & DeNisi,
*~⅓ of feedback interventions make performance worse, and self-directed feedback
is the harmful mode.* So the line is **work-focused versus learner-focused**,
not metric versus no-metric. The build plan's operative wording is *"no
leaderboards shown to struggling students"*, and its research brief weighs where
points and badges do help.

That is the same line this repository draws in refusals 4 and 6 — no standing
cross-context score, never a priority between two students — reached from
education research rather than from authority doctrine. **Item 9 is closer to a
citation than to a decision**, and the choice it asks for may already be made.

## `quick-stupids` — the pair this repository declared, and could not see was broken

`personas.PROVENANCE` named `quick-stupids:band/persona.py` as the
non-authoritative half of its pair, and PR #4 stated the playground copy *"now
carries a tombstone pointing here."* Both were checked at `a92389c`. **Both were
false.**

- **There is no `band/persona.py`.** The repository holds fourteen files: an
  `app/` browser-shell skeleton in JavaScript, `README.md`, `CLAUDE.md`,
  `.gitignore`. No `band/`, no `persona.py`, **no Python at all**.
- **There is no tombstone.** The only supersession language in that README is
  line 41 *retracting* an earlier supersession claim — and it is about `app/`, a
  different component *"briefly confused"* for this one.

**The guard could not have caught it.** `test_the_pair_declares_its_middle`
asserted that the two strings had the right prefixes. A path that does not exist
satisfies that perfectly. The middle was checking its own *shape* and reporting
it as verified — which is `tests/test_claimed_artifacts.py`'s entire subject,
committed one repository over, where that test cannot reach.

Worth stating plainly: **PR #5's thesis was that a report claiming an artifact
must ship it. PR #4, merged the same day, claimed an artifact in another
repository that was not there.** The discipline was present and its scope
stopped at the repository boundary — the same shape as scout-13's original
finding, one level out.

**Fixed as far as it can be from here.** `PROVENANCE.far_side` now records
`state` / `checked` / `at` / `note` — value plus provenance plus date, the shape
`kartikeya.resolve_sandbox_config` uses for the same reason. A cross-repo claim
genuinely cannot be verified from this repository's CI, so the new guard does
not assert the far side exists. It asserts **somebody looked and said when**,
and it fails on an undated, stateless or unpinned declaration. Recording
`absent` passes, because recording absence is the correct outcome of having
looked (rule 13).

## `almanac-template` — cross-tier for `add_repo`, but reachable over the public web (corrected 2026-08-01)

`add_repo` refused: *"cross-tier adds are not supported in v1: requested
`almanac-data/almanac-template` but session already has repos from owner(s)
[rudi193-cmd]."*

This is the constraint the struck section at the top of this file warned about —
attached to the wrong repository. `Nestor` was named as the cross-tier risk and
is on the same account; the `almanac-data` org is the actual boundary. So the
warning was not wrong about the *mechanism*, only about where it applies, and
the cost of getting that wrong was deterring twelve reads that worked.

**Consequence for §14's verification column — corrected 2026-08-01.**
~~`almanac-template`'s `catalog-entry.schema.json` is named as the model to adopt
wholesale and cannot be read from this session.~~ `add_repo` refuses the
cross-owner attach, but the repository is **public**, so the constraint is on
that one tool, not on reading: it was read over the public web
(`raw.githubusercontent`, pinned `49f1d62`). **Row 996 is `VERIFIED`** —
`catalog-entry.schema.json` carries both `observed` (machine facts from the last
probe: `checked`/`reachable`/`http_status`) and `status` (a derived lifecycle
label auditable against it), and `.github/workflows/link-check.yml` runs a daily
`cron: "0 12 * * *"` over `scripts/check_links.py` that files a dead-link issue
through `scripts/alert_on_dead_links.py`. The `kartikeya.resolve_sandbox_config`
fallback was a real substitute but was not needed. "Genuinely unreachable" was
the wrong conclusion — cross-tier for `add_repo` is not the same as unreadable.

---

## ~~Names that do not resolve — the dead-link tally, checked~~ — WRONG, see the correction below

> **Struck 2026-07-30.** Every conclusion in this section about the eight app
> names is false — they are all present as `apps/<name>` inside
> `safe-app-store`. The query looked for standalone repositories; the fleet
> keeps apps inside the store. Left in place because the *manner* of the error
> is the useful part, and the correction is below.

~~`list_repos` over the account returned the full set (`has_more: false`), so
absence here is measured rather than inferred. Ten names this document uses
were checked; **eight do not exist under `rudi193-cmd`**:~~

| Name as written | Resolution |
|---|---|
| `law-gazelle` | **absent** |
| `private-ledger` | **absent** |
| `field-acoustics` | **absent** — and §9 foundation 6 calls it *"the first real capability"* |
| `story-timeline` | **absent** — cited in `safe-design`'s README as carrying sixty hardcoded colours |
| `ask-jeles` | **absent** — §18 item 9 leans on its record-the-shape pattern |
| `civics-check` | **absent** |
| `the-squirrel` | **absent** |
| `nest-seed` | **absent** — Tier 2 lists it as *"digitisation, `nest_promote`/`nest_digest`"* |
| `safe-app-common` | **renamed** → `safe-app-common-package`, read at `2b3d088` |
| `almanac-template`, `almanac-data` | **exist**, under the `almanac-data` org — cross-tier for `add_repo`, but `almanac-template` was read over the public web (row 996 `VERIFIED`; see the corrected section above) |

**This is §15's dead-link tally landing on this document.** It records fifteen
store manifests naming a repository that does not exist and warns *"bare names
are used throughout below; expect misses."* The warning was right and the count
here is eight of ten.

Three of those eight are load-bearing somewhere else and should not be left as
bare names:

- **`field-acoustics`** is §9's first vertical module — the first thing this
  repository would build after foundation. If the name is wrong, foundation 6 is
  pointing at nothing.
- **`ask-jeles`** carries the pattern §18 item 9 proposes to resolve practice
  logging with. Item 9 already has a better source in `UTETY`, read at
  `b953e84`, so the loss is survivable — but the citation is dangling.
- **`nest-seed`** is the only Tier 2 entry that cannot be read at all.

Whether these are renames, private repositories under another account, or names
that never existed is **not established here**. What is established is that they
are not on this account, and a bare name that resolves to nothing is exactly the
`P2` decay §15 describes. Each needs a resolution or a tombstone; neither is
this file's to write.

---

## `kart-sandbox.json` is in three repositories, and two of them are a bare pair

Corrected from the entry earlier in this file, which saw two copies and reported
the override mechanism as their middle. With `willow-config` read, there are
three:

| Location | Bytes | SHA (first 12) | Declared? |
|---|---|---|---|
| `kartikeya/src/kartikeya/data/` | 2519 | `a7d71f2d3df1` | **yes** — the vendored product-neutral default, whose own `description` names the override path |
| `willow-config/kart-sandbox.json` | 5452 | `a98d66cc8de1` | plausibly `$WILLOW_HOME` — the documented override location |
| `willow-2.0/willow/fylgja/config/` | 5452 | `a98d66cc8de1` | **no** |

**The second and third are byte-identical**, and nothing observed reconciles
them. `kartikeya.resolve_sandbox_config` resolves `$KART_SANDBOX_CONFIG` →
`$WILLOW_HOME/kart-sandbox.json` → the vendored default. That mechanism explains
*one* override. It says nothing about why a third copy of the same bytes sits
under `willow-2.0/willow/fylgja/config/`.

**Identical today is the dangerous state, not the safe one.** §16's tally is
four pairs and four drifts; a pair that is currently in sync presents exactly
like a pair with a middle, right up until someone edits one side. This is a
sandbox mount policy — the file that decides what a sandboxed task can reach —
so the drift direction that matters is the one that silently widens it.

The earlier entry in this file called the two-copy case *"a pair with a middle,
not a drift."* That was right about `kartikeya` ↔ override and wrong as a
description of the whole picture, because a third copy had not been looked for.
Corrected here rather than edited above, so the shape of the error stays visible:
**finding a declared mechanism is not the same as finding all the copies.**

## `willow-config` — all three claimed files present

`willow.md`, `config/settings.global.json` and `kart-sandbox.json` all exist at
`4645535`. Tier 2's description of this repository is accurate.

## `Jeles` and `jeles-remote`

`Jeles` at `0ae85b5` — §14's *"verified answers in front of inference"* is the
repository's own framing: *"the corpus sits in front of live search, it doesn't
replace it. A confident nugget match answers instantly — no search, no LLM
call."* That is refusal 1's posture reached from a different direction: the
cheapest way to avoid a non-local inference call is to answer without inferring.

`jeles-remote` at `cdb2a1d` — §4.3's four criteria for a permitted hosted
component all hold. Stateless (*"no volumes, no database,
`min_machines_running = 0`"*), refuses to start without its key, opaque payloads,
and the *"~65 institutional search APIs"* count is **65** `search_` functions
exactly. Worth noting the near-miss: `sources.py` says *"up to 16 sources run in
parallel"*, which reads like a source count and is a concurrency limit. A tally
taken by grepping the first plausible number would have reported 16.

---

## The last seven — six claims hold, one is wrong in the unsafe direction

| Repository | Commit | Claim | Result |
|---|---|---|---|
| `willow-seed` | `a9274e8` | cloud fallback chain, must be disabled | **holds, and is harder than §14 says** |
| `openclaw-sap-gate` | `82d80d9` | SAP/1.0, *"fail-open default fingerprint"* | **WRONG — it is fail-closed, with a test** |
| `yggdrasil-training-data` | `c183222` | fail-closed on unknown, trusted-source bypass | **holds, both halves** |
| `awesome-sovereign-software` | `1039334` | five-point test, required exit line | **holds** |
| `oakenscrolls-office` | `7cd5067` | working calibration ledger | **holds** — Brier and log-score in `calibration.py` |
| `DispatchesFromReality` | `4655d6d` | dated consent, prose only | **holds** — zero Python files |
| `willow-compose` | `821d3db` | 29,432 pieces, family data excluded | **holds**, count exact |

### `openclaw-sap-gate` — §14 describes it as less safe than it is

§14 reads *"**Exists**, with a **fail-open** default fingerprint and
revocation-by-deletion."* The source says the opposite, twice, and tests it:

```
# Fail-closed preserved: if NEITHER is set, _EXPECTED_FP is "" and _verify_pgp
# denies ("SAP_PGP_FINGERPRINT not configured").
```

`gate.py:102` — *"unset ⇒ fail-closed deny"*. `gate.py:10` — *"Any failure →
deny + log."* And `tests/test_gate.py:92` is
`test_no_fingerprint_pinned_fails_closed`.

Note the word **"preserved"** in that comment: it reads like a property that was
once lost and restored. So §14's claim may have been true of an earlier revision
— which is §15's `P2` decay exactly, a citation whose source moved on while the
label stayed. **Corrected in §14.** Revocation-by-deletion is confirmed and
correctly flagged: it is what refusal 3 forbids, which is why this repository
takes the four-step chain and not that.

### `willow-seed` — the claim holds and understates the work

`README.md:148` and `docs/QUICKSTART.md:181` carry the chain verbatim —
`Ollama → Groq → Cerebras → SambaNova`, keys from `credentials.json`. §14's
*"must be disabled, not unused"* is right. Three things make it harder than that
sentence implies:

- **`willow-seed` contains no code implementing it.** README, QUICKSTART, a
  requirements comment, and a template docstring. Disabling it there is
  impossible because there is nothing there to disable.
- **The implementation is in `willow-2.0`, spread across at least six files** —
  `sap/core/inference.py` has `chat_groq` / `chat_openrouter` / `chat_codex` /
  `chat_ollama` as peer functions, and Cerebras/SambaNova appear in five more.
  **No single switch was found** by grep for `disable`, `local_only`, `offline`
  or `WILLOW_INFERENCE_PROVIDER` in either repository. Absence of a grep hit is
  not proof of absence; it is what was looked for and not found.
- **The only dispatch chain located tries cloud first and never tries local.**
  `archive/legacy/sap/sap_mcp_v1.py:1527` is
  `chat_groq(...) or chat_openrouter(...)`. It is archived, so it may not run —
  but no live call site for `chat_ollama` was found at all.

And the framing is the dangerous part. `QUICKSTART.md:194` presents it as
reassurance: *"**Local-first:** Your data lives on your machine. The fleet
fallback uses free-tier cloud APIs only when local inference is unavailable…
nothing is stored."* That sentence is what refusal 1 exists to refuse, written
as a safety property. A reader adopting `willow-seed` inherits the chain while
reading the words "local-first".

### `yggdrasil-training-data` — a second instance of the class

§14 says *"fail-closed on unknown — but carries a trusted-source bypass not to
reproduce."* Both halves hold. `route()` returns `"unknown"` for anything
outside two allowlists and unknown records are **not written**. Then:

```python
if hint == "slm":
    dest = "slm"
else:
    dest = route(record)
```

Three of the four `SOURCE_FILES` are tagged `"slm"`, so **every record in them
is exported without `route()` ever running.** The per-record classifier is
correct, fails closed, and is skipped wholesale by a per-file trust declaration
upstream of it.

**That is the same shape as `catalog_lint.py:71-73`**, which skips the manifest
check for catalog entries without a local `path`. Two independent instances,
found by reading, of *a middle that exists, is correct, and cannot fire for a
whole class of inputs*. §16 names three failure modes — absent, mis-aimed,
cannot fire — and this is a fourth worth stating separately: **bypassed by a
declaration upstream.** The guard is never wrong; it is never asked.

### The other four, briefly

- **`awesome-sovereign-software`** — *"sovereignty **is** the ability to
  leave"*, five criteria every entry must pass **all** of, and an exit line
  required per entry. §11.1's criterion is real and this repository still has no
  exit line, which §18 item 5 already says.
- **`oakenscrolls-office`** — `calibration.py` implements Brier and log score
  over `(confidence, outcome)` pairs, with confidence bounded to `[0.5, 0.99]`.
  A working calibration ledger, as claimed. §14 is right that adjudicator
  calibration is nonetheless a prohibited scope here (`SA-3`): the mechanism
  being good is not the objection.
- **`DispatchesFromReality`** — **zero Python files.** §14's *"prose only… no
  code anywhere in the fleet"* is exact, and dated/staged consent must still be
  invented here.
- **`willow-compose`** — `29,432` appears in `README.md`, `engine/build_holdings.py`
  and the data dump; the count is exact rather than rounded. Its stated exclusion
  is explicit: *"Family specifics, medical, legal, schedules, names — surfaced
  during the assembly, kept out of every durable artifact on purpose."* §14's
  note that this app is a family-data app *by definition* stands: the corpus's
  exclusion is precisely this repository's subject matter.

---

## Correction — the eight "absent" names are all present, and the store re-read

**The dead-names section above is wrong and is struck.** All eight names exist,
as `apps/<name>` inside `safe-app-store` at `b1825f7`:

```
apps/law-gazelle   apps/private-ledger  apps/field-acoustics  apps/story-timeline
apps/ask-jeles     apps/civics-check    apps/the-squirrel     apps/nest-seed
```

Twenty-seven apps, and `catalog.json` gives each of the eight a correct
`path`. Nothing was missing.

**What went wrong is worth more than the correction.** `list_repos` was queried
for *standalone repositories* with those names, found none, and the result was
written up as *"absence here is measured rather than inferred."* The query was
right and the namespace was wrong: the fleet's convention is that apps live
inside the store, which `§17` says plainly and this file's own Tier 3 list
implies by sitting beside `apps/marching-arts`.

**A rigour claim attached to a wrong-namespace query is worse than no claim at
all**, because "measured" invites the reader to stop checking. That is this
repository's own subject — a middle that reports on its own shape rather than
its referent — committed by the pass built to catch it, for the second time in
one session.

### What is actually true, measured this time

**Fifteen manifests name a repository that does not exist — §15's tally is
exact.** Not the apps: the `repository` *field inside each app's
`safe-app-manifest.json`*. Derived by resolving all 22 against the account's
full repository set:

| | |
|---|---|
| apps in the store | 27 |
| manifests declaring a `repository` | 22 |
| resolve | 7 |
| **do not resolve** | **15** |

`safe-app-UTETY-Reddit-Bots · safe-app-ask-jeles · safe-app-dating-wellbeing ·
safe-app-field-notes · safe-app-game · safe-app-llmphysics-bot ·
safe-app-nasa-archive · safe-app-private-ledger · safe-app-public-ledger ·
safe-app-semantic-translator · safe-app-source-trail · safe-app-the-binder ·
safe-app-the-squirrel · safe-app-utety-chat · safe-app-vision-board`

**And nothing checks them.** `tools/catalog_lint.py` is 132 lines. `repository`
appears three times, once as a check:

```python
elif status != "archived" and not entry.get("repository"):
    errors.append(f"{app_id}: no path, not archived, no external repository")
```

That reads `entry` — the **catalog** row — and asserts the field is *non-empty*.
It never resolves it, and it never looks at the **manifest's** `repository`
field at all. So the fifteen dead links are checked by nothing, not even for
presence.

**This is the same defect as the pair guard corrected earlier today**, and now
the class has three instances: `test_the_pair_declares_its_middle` asserted
string prefixes; `catalog_lint` asserts a field is non-empty; both validate a
declaration's **shape** and never its **referent**. Distinct from the
bypassed-upstream mode — here the guard runs, passes, and was never asked the
question that matters.

**The earlier characterisation of `catalog_lint` was also second-hand and is
now first-hand.** It was taken from `willow-grove/DESIGN_CONSTRAINTS.md` and
reported as verified without opening the file. Read at source, the manifest
check is indeed gated on a local `path` (`if path and (REPO / path).is_dir():`),
so the constraint's claim holds — but the sharper fact, that the *manifest's*
own repository field is never read by anything, was not in the secondary source
and would not have been found by trusting it.

### Two tallies confirmed while there

- **§6's "three of twenty-seven store apps have a `test_no_egress.py`"** —
  exact. `oakenscrolls-office`, `private-ledger`, `marching-arts`.
- **`grove`'s catalog entry names `safe-app-grove`**, which does not exist —
  confirming `DESIGN_CONSTRAINTS.md`'s note independently. Only three catalog
  entries declare an external repository at all: `grove`, `ratatosk`,
  `willow-grove`.

### What this does to `field-acoustics`

`apps/field-acoustics` exists, with a catalog path and no manifest `repository`
field. **§9's foundation 6 points at something real.** The claim that it did
not, made earlier today and carried into `docs/BUILD-PLAN.md`, was false and is
removed there.

---

## Tallies re-derived, 2026-07-30 — five were wrong

Every count claimed in this file was re-run, this time **naming the items**
rather than reporting a number. Two held, five did not, and one of the five
reverses a hazard reported to the maintainer.

| Tally | Claimed | Re-derived | |
|---|---|---|---|
| repositories read | 28 | **27** | session scope counted `terpsi-music` |
| `willow-2.0` bitemporal tables | 17 | **17** | holds; all named |
| `willow-tech-manual` L-ladder | absent | **absent** | holds; also checked `classif`, `band` |
| `jeles-remote` sources | 65 | **61 reachable** | 65 defined, 4 orphaned, 1 opt-in |
| chain implementation spread | "≥6 files" | **24 files** | understated by 4× |
| inference off-switch | "none found" | **exists** | `WILLOW_INFERENCE_PROVIDER=local` |
| live dispatch order | "cloud first, no local" | **local first** | I read archived code as live |

### The one that matters: there *is* an off-switch, and `CLAUDE.md` named it

`willow-2.0/core/inference_router.py` — a file never opened, because the grep
was for `chat_ollama` call sites and this router uses different function names:

```
Priority (WILLOW_INFERENCE_PROVIDER):
  local  → Ollama only
  cloud  → Gemini → Groq (70b) → OpenRouter-compatible fleet keys
  auto   → Ollama, then cloud chain
```

`_chain("local")` returns `[("ollama", _try_ollama)]` and nothing else. **That is
a complete off-switch**, and refusal 1 in this repository's own `CLAUDE.md`
names the variable verbatim — *"no cloud fallback chain, no
`WILLOW_INFERENCE_PROVIDER=auto`."* The answer was in the file governing the
work while the report said it could not be found.

**What is genuinely true, and is the real hazard:** line 213 reads
`os.environ.get("WILLOW_INFERENCE_PROVIDER", "auto")`. **The default is `auto`**
— Ollama first, then Gemini → Groq → OpenRouter → fleet. So the chain is not
undisableable; it is **fail-open when unconfigured**, which is a different and
more tractable problem. Refusal 1 is already calibrated to exactly this: it
forbids the default rather than the mechanism.

And the earlier claim that the only dispatch tries cloud first was **reading
archived code as live**. `archive/legacy/sap/sap_mcp_v1.py:1527` is
`chat_groq(...) or chat_openrouter(...)`, cloud-only — but it is archived. The
live router tries local first.

**One thing found that is directly useful.** `respond()` returns
`(response_text, provider_used)` — the provider that actually served is returned
to the caller. So **refusal 1 can be enforced by assertion rather than by
configuration**: a caller can require `provider_used == "ollama"` and fail
otherwise, instead of trusting an environment variable to have been set. That is
the claim-plus-source shape again, and it converts refusal 1 from a deployment
note into something testable.

Also corrected: the providers appear in **24** Python files in `willow-2.0`, not
"at least six" — and the two documented chains disagree. `willow-seed`'s README
says Groq → Cerebras → SambaNova; the router says Gemini → Groq → OpenRouter →
fleet. Neither is wrong about its own subject; there is no single chain.

### Read again 2026-07-31, to build against rather than to cite

The account above is sound and it is not sufficient to build from. Four things
it does not say, found by reading `core/inference_router.py` line by line while
writing `records/inference.py` against it:

| | at source | why it changes the guard |
|---|---|---|
| **`core/llm_edge.py`** | its `respond()` calls the router and **discards `provider_used`**, returning a bare string; on exception it falls through to `_groq(...)` and then `_ollama(...)` in two `except: pass` blocks | the enforceable return shape is a property of *one* function, not of the fleet's edge. A caller of the sibling has no label to assert on, so **an absent label is a refusal here**, not a benefit of the doubt |
| **a fourth mode** | `_chain("hns")` returns `hns + local + cloud`, and is absent from the file's own docstring; `_try_hns` posts to `node["2.0_stub"]["ollama_url"]` — **another machine's Ollama** | `provider_used == "ollama"` is necessary and not sufficient. `OLLAMA_URL` moves the plain path off-box too, so the guard checks the **address** as well as the label |
| **`mode=`** | `chat(system, user, *, mode=None)` takes the chain by argument, bypassing `WILLOW_INFERENCE_PROVIDER` entirely | an off-switch a caller can pass an argument around is a default. Enforcement cannot live in the variable |
| **`_load_key`** | falls back to `sap.core.inference.load_credential` when the environment is empty | *"no credential prefixes"* in install acceptance (§11.1) has to mean the credential store as well as the environment |

**One disagreement is inside a single file**, which is the cheapest kind to
miss: the module docstring lists three modes and a three-step cloud chain; the
code implements four modes and a four-step chain.

**And a count re-derived with its pattern**, because the `24` above has none and
is therefore not reproducible. Files under `willow-2.0` matching
`GROQ_API_KEY|OPENROUTER_API_KEY|GEMINI_API_KEY|api.groq.com|openrouter.ai|generativelanguage.googleapis.com`:
**21** of 848 `.py` files, **17** excluding `archive/` and `tests/`. Files
mentioning `inference_router`: **4**. Files mentioning `llm_edge`: **9**. The
`24` is not contradicted — it is unreproducible, which under rule 17 is the same
problem arriving one step earlier.

**Not read, and it matters:** `willow/routing/shadow.py` carries a five-rung
complexity ladder — `r1_trivial … r5_frontier` — whose `_RUNG_ENGINE` maps the
top two rungs to `"cloud"`. It is a *third* ladder using the word rung (§15's
hazard, with `L1–L5` and `P1–P5`), and its default preference for hard questions
is the one refusal 1 forbids. Nothing here uses it; if anything ever does, that
mapping is the thing to look at first.

### `jeles-remote` — definitions counted, sources claimed

65 `def search_*` functions exist. **61 are registered in `SOURCES`** and
therefore dispatchable; four are defined and unreachable —
`search_fbi_vault`, `search_ig_nobel`, `search_isfdb`, `search_omdb` — and one
registered source is `opt_in`, so a default search reaches 60.

§4.3's *"~65"* survives on the tilde. The earlier report here said "65 exactly",
which counted the easy thing and named it the claimed thing — in the same
paragraph that congratulated itself for not misreading the concurrency limit as
a source count.

### The two that held

`willow-2.0`'s seventeen: `agents · binder_edges · binder_files · cmb_atoms ·
compact_contexts · dispatch_tasks · edges · feedback · forks · hook_registry ·
jeles_atoms · jeles_sessions · journal · opus_atoms · policy_rules ·
ratifications · tasks`. Each receives **both** columns. Note the migration
alters seventeen; `jeles_sources` was later created carrying them, so the
schema total is eighteen and "17 tables" describes the migration.

`willow-tech-manual`: 68 files, zero hits for `sensitiv`, `band`, or any
`L1`–`L5` token. The two `classif` hits are an npm package name and one
unrelated sentence about queue accuracy. The negative holds.

### The pattern under all five errors

Every wrong tally came from **counting what was easy to count in the place I
happened to be looking**, then reporting the number as though it answered the
question asked. Definitions for sources. Session scope for repositories read.
One file's grep for a system-wide claim. Archived code for live code. A
wrong-namespace query for existence.

The fix that would have caught all five is the one this repository already
requires and I did not apply to myself: **name the items, not the count.** Every
tally above that survived re-derivation is one where the items were listed the
first time.
