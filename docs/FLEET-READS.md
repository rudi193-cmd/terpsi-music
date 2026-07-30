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
| `Nestor` | `111c187` | `nestor/curator.py`, seal states | **CONFIRMED.** `Curator.servable` at `curator.py:82`, `unverifiable()` at `:118`, cascade `sealed`/`draft`/`pending` all present. **But it is at `rudi193-cmd/nestor`, not `Die-Namic-Systems`** |
| `willow-gate` | `3092de5` | `src/willow_gate/friction_floor.py` | **CONFIRMED**, and it is a sibling of this repository's `voice.py` — see below |
| `willow-data-vault` | `b634de0` | `README.md`, `schema/` | **CONFIRMED.** Three-layer architecture, `vault.key` + Fernet. Nine files: schemas and bootstrap only, *"never data"* |
| `quiet-corner` | `1230e96` | `qc-data.js`, `docs/backend-architecture.md` | **§7.3 CONFIRMED exactly.** Eight `*_visible` fields; the source itself states *"API does not enforce them in Tier 1/2"* |
| `corpus-lens` | `0c2a124` | `README.md`, `tests/test_wall.py` | **§4.2 CONFIRMED verbatim**, both halves including the test |
| `UTETY` | `b953e84` | `README.md`, `docs/build-plan.md` | **CONFIRMED**, and the rule is sharper than §18 item 9 records |
| `kartikeya` | `de77d67` | `src/kartikeya/sandbox.py`, `execute.py` | **CONFIRMED.** bwrap isolation, fails closed. **And it contains item 0's fix** |
| `quick-stupids` | `a92389c` | whole tree | **REFUTES this repository's own claim.** No `band/persona.py`, no Python, no tombstone |
| `almanac-template` | — | — | **UNREACHABLE.** `add_repo` refuses cross-tier; `almanac-data` is a different org |

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

## `almanac-template` — genuinely unreachable, and this is the real cross-tier case

`add_repo` refused: *"cross-tier adds are not supported in v1: requested
`almanac-data/almanac-template` but session already has repos from owner(s)
[rudi193-cmd]."*

This is the constraint the struck section at the top of this file warned about —
attached to the wrong repository. `Nestor` was named as the cross-tier risk and
is on the same account; the `almanac-data` org is the actual boundary. So the
warning was not wrong about the *mechanism*, only about where it applies, and
the cost of getting that wrong was deterring twelve reads that worked.

**Consequence for §14's verification column.** `almanac-template`'s
`catalog-entry.schema.json` is named as the model to adopt wholesale and cannot
be read from this session. But `kartikeya.resolve_sandbox_config` supplies the
same shape from a reachable repository — claim plus source, with a named
sentinel for nothing-supplied-this — so the column is not blocked on it.
