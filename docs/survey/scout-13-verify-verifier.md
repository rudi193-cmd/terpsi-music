# Scout 13 — Proving a guard fires; detecting declaration/enforcement divergence

**Slice:** mutation testing (esp. SQL constraints and triggers), property/metamorphic/differential
testing, deterministic simulation and fault injection, lightweight formal methods for an
authorization predicate, declaration-vs-enforcement drift detection, coverage stronger than lines,
conformance suites as shipped artifacts.

**Scope note / honesty.** WebSearch budget was exhausted early (200/200) so most verification is
WebFetch against real repo pages plus GitHub's code-search API. Star/commit figures below are as
reported by those pages on 2026-07-30 and are *cited*, not derived from a tree — CLAUDE.md §17
applies to them as much as to anything else. A closing section lists every claim I could **not**
verify. One finding (§SQL, mutant A–D) I derived by running code, and the script is in this
directory.

---

## 1 · Ranked table

Verdict key: **ADOPT** = install this quarter · **STEAL** = take the shape, write ~50–200 lines
locally · **READ** = worth an hour, do not adopt.

| # | Project | What it is | License | Activity (as of 2026-07-30) | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) + `RuleBasedStateMachine` | Property-based testing; `@rule`/`@precondition`/`@invariant`/`Bundle` state machines with shrinking | MPL-2.0 (LICENSE.txt present) | 8.8k★, 17,730 commits, very active | §7.1 guardianship dates, W-1/W-3 lane model, §7.4 ward clauses | **ADOPT** |
| 2 | **SQLite-native schema-object manifest + ablation mutants** (derived here, no dependency) | `sqlite_master` inventory test + `DROP TRIGGER` / neuter-`WHEN` / drop-`CHECK` mutation operators | n/a (~60 lines) | n/a | §10 "mutate it and watch the suite go red"; the renamed-trigger defect exactly | **ADOPT** |
| 3 | [CrossHair](https://github.com/pschanely/CrossHair) | SMT-backed symbolic execution of *Python* contracts; finds counterexamples to a predicate | MIT-ish (LICENSE present) | 1.3k★, 2,333 commits, active; Hypothesis ships it as a backend (`hypothesis-crosshair`) | §7 resolver predicate, §7.4 W-2/W-7, refusal indistinguishability | **ADOPT** |
| 4 | [cog](https://github.com/nedbat/cog) | Embeds Python in static files; `--check` fails if regenerated output would differ | MIT | 407★, 323 commits, Batchelder-maintained | §10 / CLAUDE.md §17 — "counts in prose that nothing checks" | **ADOPT** |
| 5 | [cosmic-ray](https://github.com/sixty-north/cosmic-ray) | Python mutation testing; sessions, resumable, distributed workers, build-tool integration | MIT | 646★, pushed 2026-04-02 | §10 acceptance-is-mutation; §16 rule 2 (mutation-test the middle) | **ADOPT** |
| 6 | [SchemaAnalyst](https://github.com/schemaanalyst/schemaanalyst) | Search-based test-data generation **and mutation analysis of relational schema integrity constraints**; SQLite supported | GPL-3.0 | Java, 24★/8 forks, 1,632 commits — research-grade, low activity | The only real prior art for mutating CHECK/NOT NULL/UNIQUE/PK/FK | **STEAL** (operator catalogue), read the papers |
| 7 | [SQLancer](https://github.com/sqlancer/sqlancer) | Metamorphic DBMS oracles: **TLP**, NoREC, PQS, DQP, CERT, CODDTest; SQLite target built in | MIT | Java 11+, 1.7k★, 2,699 commits, active | Metamorphic oracle for the row-level authorization predicate (see §3) | **STEAL** (TLP shape) |
| 8 | [Hermit](https://github.com/facebookexperimental/hermit) | Determinizes arbitrary Linux x86-64 programs (ptrace); `--chaos --sched-seed=N` explores adversarial schedules | BSD-3-Clause | Rust, 1.4k★, "maintenance mode", 3–6× overhead | Deterministic-simulation tradition, for a team that writes Python | **STEAL / READ** |
| 9 | [cedar-spec](https://github.com/cedar-policy/cedar-spec) | Lean formalisation of an authorization language + **differential randomized testing** harness Lean-model ↔ Rust production impl | Apache-2.0 | 191★, 737 commits, active (AWS) | §16 "these two implementations must agree"; the canonical/vendored pairs | **READ** (best-in-class reference), STEAL the DRT harness shape |
| 10 | [cruft](https://github.com/cruft/cruft) | `cruft check` exits 1 when a project has drifted from the template it was generated from; `cruft diff --exit-code` | MIT | Python, 1.6k★, active | §17 "a template without a conformance check is just the first copy" | **ADOPT** |
| 11 | [cncf/k8s-conformance](https://github.com/cncf/k8s-conformance) | Vendors PR four artifacts (`PRODUCT.yaml`, `README`, `e2e.log`, `junit_01.xml`) per suite version; the merged PR *is* the dated public record | repo Apache-2.0 | 935★, 1,957 commits, suites v1.24→v1.36 | §17 requirement 2 — "promotion writes a record" | **STEAL** (exact shape) |
| 12 | [rustls `bogo/`](https://github.com/rustls/rustls/tree/main/bogo) | rustls runs **BoringSSL's** TLS conformance suite against itself via a shim + `config.json.in` with an explicit known-failure list | Apache/MIT/ISC | Active | Conformance suite you don't own, plus a *declared* accepted-failure set | **STEAL** (the known-failure list is the good part) |
| 13 | [Schemathesis](https://github.com/schemathesis/schemathesis) | Generates inputs from a declared OpenAPI/GraphQL schema and finds schema-violation / validation-bypass divergence; built on Hypothesis | MIT | 3.5k★, 4,603 commits, active | Declaration ↔ enforcement, if any surface is HTTP (§4.2 parent PWA) | **ADOPT if there is an API**, else READ |
| 14 | [APSW](https://github.com/rogerbinns/apsw) — `src/faultinject.c`, `tools/genfaultinject.py` | Python SQLite wrapper exposing SQLite's **VFS**; ships a *generated* fault injector that makes each C call site fail in turn | OSI-approved | 847★, 5,647 commits, active | §5/§11 escrow + restore, "a stopped Ollama must fail loudly" family | **STEAL** (VFS error injection), READ the generator |
| 15 | [Atlas](https://github.com/ariga/atlas) | `atlas schema diff` (declared HCL/SQL ↔ live DB) and `atlas migrate lint` with 50+ analyzers; SQLite supported | repo Apache-2.0 (⚠ distributed CLI has a paid tier) | Go, 8.6k★, active | Migration-001 safety, destructive-change gate | **READ / trial** |
| 16 | [OpenFGA](https://github.com/openfga/openfga) | Declared authorization model **plus a shipped test format** (`.fga.yaml`, `fga model test`) asserting check/list_objects outcomes | Apache-2.0 | Go, 5.5k★, active (Auth0/Docker/Canonical) | §7 — the pattern of shipping the model's tests *with* the model | **STEAL** (the test-file format) |
| 17 | [Alloy 6](https://github.com/AlloyTools/org.alloytools.alloy) | Lightweight formal methods; relational model *finder* with bundled SAT solvers (Sat4j/minisat/glucose) | open source (see repo) | Java 17+, 859★, CI builds every commit | Model the ward/guardianship/lane relation before writing migration 001 | **READ**, one-week spike |
| 18 | [Chaos Toolkit](https://github.com/chaostoolkit/chaostoolkit) | Python CLI where the experiment JSON declares a `steady-state-hypothesis` block of probes+tolerances, verified around the fault | Apache-2.0 | 2.0k★, active | The declared-hypothesis discipline, not the chaos | **STEAL** (the file format) |
| 19 | [sqlglot](https://github.com/tobymao/sqlglot) | SQL parser/optimizer/canonicaliser with a semantic AST `diff` (Insert/Remove/Move/Update/Keep) | MIT | Python, 9.5k★, 7,982 commits | #120's "re-aim the differential at behaviour not spelling" — **but see the caveat in §2** | **ADOPT for CHECK, DO NOT USE for triggers** |
| 20 | [cocotb-coverage](https://github.com/mciepluc/cocotb-coverage) | Hardware-verification **functional coverage** (`CoverPoint`, `CoverCross`, `coverage_section`) and constrained randomisation, in pure Python; XML/YAML export | BSD-2-Clause | 127★, v2.0 released 2025-10-03 | Coverage *closure* against a declared goal set, instead of line % | **STEAL** (the closure discipline) |
| 21 | [Arlo](https://github.com/votingworks/arlo) | Risk-limiting-audit engine: ballot manifest, sample size from a declared risk limit, escalation to full recount | AGPL-3.0 | Python/JS, 153★, 2,165 commits | How much verification is enough, and the manifest-reconciliation shape | **READ** (see §5) |
| 22 | [sqllogictest-rs](https://github.com/risinglightdb/sqllogictest-rs) | `.slt` files from SQLite's own conformance suite; `statement ok` / `statement error` / `query` with expected results | Apache-2.0 / MIT | 228★, 180 commits; used by DataFusion, RisingWave, Databend | A *file format* for "attempt the forbidden act and assert refusal", runnable by any engine | **STEAL** (the format) |
| 23 | [mutatest](https://github.com/EvanKepner/mutatest) | Python mutation testing whose selling point is running trials **without source-code modification** | MIT | 101★, last push 2023-02 — **stale** | Directly the "harness left a mutation in the tree" defect | **READ** (design, not the tool) |
| 24 | [mutmut](https://github.com/boxed/mutmut) | Python mutation testing; v3 uses an in-memory trampoline, mutants only hit disk on explicit `mutmut apply` | BSD-3-Clause | 1.4k★, 675 commits, active | Faster than cosmic-ray, but see the `apply` hazard in §2 | **ADOPT or cosmic-ray, pick one** |
| 25 | [mutant-swarm](https://github.com/HiveRunner/mutant-swarm) | Mutation testing **and SQL coverage** for Hive SQL — the only other maintained-ish SQL mutation tool I found | (see repo) | Java, 24★, last updated 2024-08 | Evidence of how thin this field is | **READ** |
| 26 | [Sybil](https://github.com/simplistix/sybil) | Extracts and executes examples from Markdown/reST as part of a pytest run | (see repo) | Python, 90★, 476 commits | Alternative to cog for prose assertions | **READ** |

---

## 2 · MUTATING SQL CONSTRAINTS AND TRIGGERS — the honest answer

**There is no maintained tool that mutates SQLite triggers. Build it yourself; it is about sixty
lines.** That is the honest answer and it is better news than it sounds, because the sixty lines are
mostly `sqlite_master` queries.

What actually exists, in descending order of usefulness:

- **SchemaAnalyst** (GPL-3.0, Java, 24★, 1,632 commits) is the real prior art and it does support
  SQLite. Its mutation operators seed schema faults of both omission and commission — removing
  columns from primary keys, removing `NOT NULL`, removing `UNIQUE`, modifying foreign keys — and
  it runs an `AllOperatorsWithRemovers` pipeline by default. It does **not** touch triggers. It is
  a research artifact: Java 1.7-era build, Gradle, `CLASSPATH` juggling, 24 stars. **Do not adopt
  it. Steal its operator catalogue**, which is the single most valuable thing in this whole report
  for §7.1 and the bitemporal invariants, and read the paper that matters most:
  *"Automatic Detection and Removal of Ineffective Mutants for the Mutation Analysis of Relational
  Database Schemas"* (Wright, Kapfhammer, McMinn). That paper is about exactly this project's
  defect — mutants that degrade the score because they could never have changed behaviour — and it
  is the published fix for "three mutations that renamed a trigger."
- **mutant-swarm** (HiveRunner) does mutation testing *and* SQL coverage for Hive SQL. Wrong
  dialect, 24 stars, last touched 2024. Cited only as evidence of scarcity.
- **SQLMutation** (Tuya et al.) mutates `SELECT` queries, was a web service, and is dead.
- **Nothing** mutates `CREATE TRIGGER` bodies in any dialect that I could find.

### The tooling trap I walked into, so you don't

I expected **sqlglot** to be the answer — parse the DDL, mutate the AST, and use `sqlglot.diff` to
prove the mutation is semantic rather than cosmetic. I installed sqlglot 30.14.0 and tried it. It
does not work, and the way it fails is a perfect instance of §16's "mis-aimed middle":

```
=== parse CREATE TRIGGER (sqlite dialect) ===
'CREATE TRIGGER guardian_consent_required ... ' contains unsupported syntax.
Falling back to parsing as a 'Command'.
OK  type: Block   this: None   kind: None
  Command(this=CREATE, expression=' TRIGGER guardian_consent_required BEFORE INSERT ...')

=== does sqlglot.diff notice a TRIGGER RENAME? ===
  rename:      1 non-Keep edits -> ['Update']
  gutted WHEN: 1 non-Keep edits -> ['Update']
```

sqlglot does not parse trigger bodies at all — it wraps the whole statement in an opaque `Command`
node holding raw text. So `sqlglot.diff` reports the *same single `Update`* for a cosmetic rename
and for a `WHEN` clause replaced by `0`. A differential built on it would compare spelling while
claiming to compare behaviour: #120, reproduced in 2026, in the tool I would have recommended on
the strength of its README. **CLAUDE.md §16 rule 3 is why I ran it.**

sqlglot **is** good for `CHECK` constraints — those parse into real `exp.Check` /
`exp.CheckColumnConstraint` nodes and round-trip cleanly:

```
=== CHECK constraint in CREATE TABLE ===
OK, check nodes found: 2
   - CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
   - CHECK (sensitivity IN ('L1', 'L2', 'L3', 'L4', 'L5'))
```

So: **sqlglot for `CHECK` and column-constraint mutation, hand-rolled SQLite for triggers.**

### What to build instead — verified working, four mutants

Script: `./trigger_mutation_demo.py` in this directory (stdlib only, `sqlite3` 3.45.1). It builds a
guardian-consent trigger plus a bitemporal `CHECK`, then applies four mutants and reports whether
the adversarial test goes red and whether a schema-object manifest test goes red.

> **Provenance of this table.** When this report was written the script it names was not in the
> tree, so the one result here derived by *running code* rather than by citation was the one result
> that could not be re-run — §18 item 0 ("an unverified table and a verified one look identical")
> occurring inside the report about verifying verifiers. The script has since been restored and the
> table below is its actual output. `tests/test_claimed_artifacts.py` is the middle that would have
> caught the original absence, and it fails when a report claims an artifact the tree does not have.

Actual output:

| Mutant | Adversarial test refuses forbidden act? | Schema-object manifest matches? |
|---|---|---|
| baseline | ✅ refused | ✅ matches |
| **A · rename the trigger** | ✅ **still refused — mutant SURVIVES silently** | ❌ **manifest CATCHES it** |
| **B · `DROP TRIGGER`** (ablation) | ❌ RED — guard shown to fail | ❌ |
| **C · neuter `WHEN` → `WHEN 0`** | ❌ RED | ✅ **manifest does NOT catch it** |
| **D · drop the bitemporal `CHECK`** | backdated `invalid_at` accepted | ❌ **manifest CATCHES it** |

**One correction from re-running it.** Row D's manifest cell was `(n/a)`; it is not. A *named*
`CHECK` survives in `sqlite_master.sql` as the stored text of the statement that created the table,
so dropping it is caught by both middles — unlike the trigger's `WHEN` clause in row C, which the
manifest cannot see. The distinction is worth carrying: **naming a constraint is what makes its
removal visible to an inventory.** An anonymous `CHECK` would behave like row C.

Three things fall straight out of that table and all three are load-bearing:

1. **A rename is invisible to behaviour and to name-blind tests alike.** In mutant A the trigger was
   renamed and *the forbidden act was still refused*, because SQLite fires triggers by definition,
   not by name. So a rename is not a mutation of the guard at all — it is a mutation of *nothing*,
   an "ineffective mutant," and #211's three renamed triggers were never going to go red. The
   harness was not broken in a subtle way; it was applying a no-op and counting it.
2. **The correct primary operator is ablation, not edit.** `DROP TRIGGER <name>` cannot be a no-op.
   Same for `CHECK`: emit the `CREATE TABLE` without the clause. Textual edits invite renames;
   ablation cannot.
3. **Manifest and behaviour are two different middles and neither subsumes the other.** The
   `sqlite_master` name manifest catches the rename that behaviour misses (A); behaviour catches
   the neutered `WHEN` that the manifest misses (C). Ship both. The manifest is §16 rule 5's
   `test_allowlist_entries_exist` applied to the schema, and it is ~6 lines:

   ```python
   DECLARED_TRIGGERS = {"media_release_needs_guardian", ...}   # the declaration
   def test_trigger_inventory_matches_declaration(conn):
       live = {r[0] for r in conn.execute(
           "SELECT name FROM sqlite_master WHERE type='trigger'")}
       assert live == DECLARED_TRIGGERS      # a rename cannot quietly widen the door
   ```

**Proposed operator set for `terpsi-music`**, from SchemaAnalyst's catalogue plus the trigger
operators SchemaAnalyst lacks:

| Operator | Target | Why it matters here |
|---|---|---|
| `DROP TRIGGER` | each trigger | the ablation baseline; every trigger must have one test that goes red |
| `WHEN <expr>` → `WHEN 0` | trigger | "never fires" — the shape of the guardian trigger that stopped firing on a partition suffix (§17) |
| `WHEN <expr>` → `WHEN 1` | trigger | fires always — catches tests that only assert refusal and never assert acceptance |
| `RAISE(ABORT,…)` → `SELECT NULL` | trigger body | the trigger runs and permits — the nastiest one |
| `BEFORE` → `AFTER` | trigger timing | an `AFTER` guard cannot prevent the write |
| drop `CHECK` clause | table | `invalid_at >= valid_at`, `L1–L5` domain, `T0–T4` |
| weaken `CHECK`: `>=`→`>`, `AND`→`OR`, negate | table | boundary and connective faults; catches CLAUDE.md §14 bare-integer comparisons |
| drop `NOT NULL` | column | absence surfacing as a result (§6 / CLAUDE.md §13) |
| drop `UNIQUE` / remove col from PK | table | SchemaAnalyst's core operators |
| `FOREIGN KEY` → no-op, or `ON DELETE CASCADE` added | table | **cascade is a delete-shaped revocation — CLAUDE.md §3 forbids it; a mutant that adds a cascade and survives is a finding** |
| `PRAGMA foreign_keys=OFF` | connection setup | SQLite enforces FKs *only if the pragma is on, per connection*. This is a one-line mutant that should turn the suite red and, in most codebases, does not. |

That last row deserves its own sentence. In SQLite, foreign keys are off by default and enabled
per-connection. A declaration/enforcement gap sits in the schema file for free: the `REFERENCES`
clause is the declaration, `PRAGMA foreign_keys=ON` is the enforcement, and nothing connects them.
Add a mutant that flips the pragma off and a manifest test that asserts
`PRAGMA foreign_keys` returns 1 on every connection the app opens.

### Two hazards in the Python mutation tools themselves

- **mutmut v3** applies mutants via an in-memory trampoline, *not* by editing your files — good.
  But `mutmut apply <mutant>` does write to disk, and the docs carry the warning verbatim: *"You
  should **REALLY** have the file you mutate under source code control and committed before you
  apply a mutant!"* That is the exact edge #211 fell off. **Gate it:** run mutation only inside a
  throwaway `git worktree`, and make the harness's last act
  `git diff --exit-code && git status --porcelain` with a hard failure on any output. A mutation
  harness that can leave residue must prove it left none, or every number after it is fiction.
- **cosmic-ray** (MIT, 646★, pushed 2026-04-02) is the more auditable of the two: explicit
  sessions in a database, resumable, distributed workers, reports. Slower detection rate than
  mutmut per the comparison literature. Pick one; do not run both, because two mutation scores is
  a pair and would need a middle.
- **mutatest** advertises exactly the property you want — "safely run mutation trials without
  source code modifications" — and has been unmaintained since Feb 2023. Read its design, don't
  install it.

---

## 3 · Paragraph per top find, with the concrete transplant and its cost

**1 · Hypothesis `RuleBasedStateMachine` — the single highest-value adoption, and it is the one
that fits §18 item 3.** The blocking item is that there is no schema for the lane model, and the
hard part is not the columns, it is that `valid_at`/`invalid_at` guardianship plus sealed sibling
lanes plus "revoke by dating, never deleting" is a *state machine* whose invariants must hold after
every operation sequence, including sequences no one thought of — a court order arriving mid-season,
a birthdate corrected two seasons late, a guardian edge invalidated between two reads. That is what
`RuleBasedStateMachine` is for: declare `@rule`s (`enrol`, `assign_guardian`, `invalidate_guardian`,
`correct_dob`, `share_event`, `export`), declare `@invariant`s (*no lane entry is ever deleted*, *a
shared event is always exactly two lane entries with one referent*, *the send list and the guardian
edge derive from one predicate*, *no student's entry is less durable than an entry about them*),
and let it generate and **shrink** operation sequences until an invariant breaks. Shrinking is the
part that matters: it hands you the three-step reproduction, which becomes the regression test that
§17 says is the most valuable artifact in `marching-arts`. Verified: `hypothesis/src/hypothesis/stateful.py`
defines `RuleBasedStateMachine`, `Bundle`, `invariant`, `precondition`, `initialize`. **Cost:** `pip
install hypothesis`; half a day to write the first machine; MPL-2.0, no runtime dependency in
production code. **Do this before writing migration 001**, because the machine is a cheaper place to
discover that W-3 needs a referent table than the migration is.

**2 · The SQLite schema-object manifest — twenty lines that would have caught three of the six
defects.** Covered at length in §2. Transplant: one test module, `tests/test_schema_manifest.py`,
holding four declared sets — trigger names, `CHECK` clause texts (normalised through
`sqlglot.parse_one(...).sql()` so whitespace doesn't churn), table+column names carrying `PII_MINOR`
/ `HEALTH` / `FINANCIAL`, and the set of connection pragmas — each compared against
`sqlite_master` and `PRAGMA` output. **Cost:** an afternoon, zero dependencies for the trigger and
pragma halves. Its value is that it is the *only* member of this report's cast that catches a
rename, and a rename is the fleet's documented failure mode twice over (#211's triggers, and the
guardian trigger that stopped firing when the chain name gained a partition suffix, §17). Pair it
with §16 rule 5: the manifest must itself be checked for rot, meaning every declared name must
exist, not merely every live name be declared. One-sided set comparison fails open.

**3 · CrossHair — the lightweight formal method with an actual learning-curve story, and it is
Python.** The §18 list wants an authorization predicate that provably cannot return nothing to
everyone (the "refusal indistinguishability" caveat, §7, which "passes even if the predicate returns
nothing to anyone"). Alloy or TLA+ would model that, at the cost of maintaining a second artifact in
a second language — a canonical/vendored pair, in §16 terms, with no middle. CrossHair avoids the
pair entirely: you write the predicate **once, in Python**, annotate it with pre/post-conditions,
and CrossHair explores paths with an SMT solver looking for a counterexample. `crosshair watch` runs
in the background while you edit. It is verified real and healthy (1.3k★, 2,333 commits) and — the
detail that raises my confidence most — Hypothesis has adopted it as a pluggable backend: the
Hypothesis source says of `hypothesis-crosshair` that it "implements a `PrimitiveProvider` which
uses an SMT solver to generate inputs that uncover new branches." So you can run your existing
property tests *under* CrossHair with one settings change, rather than adopting a new workflow.
**Transplant:** state the resolver's postcondition as `__post__` — for each of a set of principals
including a null principal, the returned row set is a subset of what the grant permits **and** for
at least one principal it is non-empty (this is precisely the "fixture that could not fail" guard,
stated as a contract instead of a test). **Cost:** `pip install crosshair-tool`; a day to learn;
expect timeouts on anything touching a real DB, so factor the predicate out as a pure function over
plain data first — which you want anyway.

**4 · cog — the whole answer to "counts asserted in prose that nothing checks," at a cost of one
CI line.** Verified verbatim from `nedbat/cog/docs/running.rst`: `--check` "Check that the files
would not change if run again", plus `--check-fail-msg MSG` ("If --check fails, include MSG in the
output to help devs understand how to run cog in your project") and `--diff` ("With --check, show a
diff of what failed the check"). That `--check-fail-msg` is a small thing that tells you this tool
has been used in anger. **Transplant:** every number in `ARCHITECTURE.md` and `CLAUDE.md` that is a
count of something in the tree — §14's component rows, §18's "four that block", the 197 tests,
`FLEET_SEAMS.md`'s four breaks, "seventeen sections", the count of ward clauses — goes inside a cog
block that derives it. `cog --check docs/*.md CLAUDE.md` in CI. **Cost:** MIT, one dependency, an
hour for the first three numbers. The subtle win: §16's consolidation metric ("a consolidation drawn
correctly makes `FLEET_SEAMS.md` shorter") becomes a *computed* number rather than a claim, and
§18's decay requirement ("this section decays and should show it") becomes enforceable — cog can
emit the count of open items and the date each was last touched. Note the direction of the pair
here: cog makes the *document* the generated side and the *tree* canonical, which is the right way
round and the opposite of what prose usually does.

**5 · cosmic-ray / mutmut — mutation as the acceptance gate, run in a worktree, with a killed-run
tripwire.** §10's rule is already written; what is missing is the operational discipline that stops
the harness from lying. Three requirements, all cheap. (a) Run inside `git worktree add`, and make
the harness's exit path assert `git status --porcelain` is empty — this is the middle for the pair
*(harness, tree)*, and #211 shows the pair exists. (b) **Record the mutation score with its
denominator and the harness's own exit status in the same artifact.** A killed harness that reports
"87%" over 40 of 900 mutants is indistinguishable from a healthy one reporting 87% unless the
denominator and the completion flag travel together. This is §16's `servable` column applied to a
number: `score` next to `run_complete`, because they are not the same question. (c) Distinguish
**mutation coverage** from **test strength** — killed/total versus killed/(mutants actually reached
by a test). The first conflates "no test goes near this" with "tests go near it and don't check it";
the second isolates the fixture-that-cannot-fail. cosmic-ray's reports plus `coverage.py` dynamic
contexts (`dynamic_context = test_function`) give you both. **Cost:** MIT, a day of plumbing, then
minutes-to-hours per run. Scope it to the guard modules — the resolver predicate, the consent
triggers, the chain anchors, the egress gate, the guardianship dates — not the whole tree.

**6 · SQLancer's TLP oracle, transplanted to the authorization predicate.** This is the
non-obvious one and I think it is the best idea in the report. Ternary Logic Partitioning takes a
query with predicate `p` and splits it into three: `WHERE p`, `WHERE NOT p`, `WHERE p IS NULL`. The
metamorphic law is that the union of the three must equal the unpartitioned result. SQLancer uses it
to find logic bugs in DBMSs including SQLite. **Point it at the resolver instead.** For a row-level
authorization predicate `visible(principal, row)`, the law becomes: for every principal, the rows
returned under `visible`, plus the rows returned under `NOT visible`, plus the rows where `visible`
evaluates to `NULL` (which in a consent-backend-errored world is not empty — CLAUDE.md §13) must
reconstitute the full table exactly once. That single assertion catches three separate documented
defects at once: a predicate that returns nothing to anyone (the union is short by everything), a
predicate that returns everything to everyone (the `NOT` partition is empty when it shouldn't be),
and a three-valued-logic hole where an errored consent lookup silently drops rows from *both*
partitions — which is "absence rendered as a negative answer" (§6, §10) showing up as a
conservation-law violation rather than as a judgement call. It also fixes the specific bug §17
records: *"denies that silently stopped binding when the parentheses came off the joined clause"* —
a mis-parenthesised `AND`/`OR` breaks the partition sum. **Cost:** you do not install SQLancer
(Java, DBMS-oriented). You write about thirty lines of Python asserting the conservation law, driven
by Hypothesis over generated principals and rows. Cheapest high-value item on this list after the
manifest.

**7 · cncf/k8s-conformance — the exact shape for §17's "promotion writes a record."** PR #113 found
that `promote_check.py` "returns an exit code and writes nothing," and that Nestor and Jeles both
cleared all eight gates while neither left a record. Kubernetes solved this socially, not
technically: to claim conformance you open a pull request against a public repo adding four files —
`PRODUCT.yaml` (who you are), a `README`, `e2e.log` (the raw run), and `junit_01.xml` (machine-
readable results) — into a directory named for the suite version (`v1.24` … `v1.36`). The merged PR
is the dated, signed, public, immutable record; the reviewer is a working group; the suite version
is in the path so a result can never float free of what it was tested against. **Transplant:** a
`conformance/` directory in the template repo, one subdirectory per suite version, each instance
committing `INSTANCE.yaml` + `pytest` JUnit XML + the raw log, merged by a human. Four properties
worth copying deliberately: the suite version is in the path; the raw log ships alongside the
parsed results (so a doctored XML is checkable); the record is a commit, not a row in a database the
app can write; and the submission is a *human* act, which matches §5's "promotion to canonical is a
human act." **Cost:** a directory convention and a CI job. No dependency. This is the cheapest
close of any §18 item on this list.

**8 · cruft — drift detection between an instance and the template that made it.** §17 names the
disease precisely: four canonical/vendored pairs already drifting, every one of which began as
"keep in sync" in a README. cruft is the middle for that pair as a shipped tool: `cruft check`
returns exit code 1 when a project is not on the latest template version, `cruft diff --exit-code`
shows what the instance has changed relative to the template, and the README ships a GitHub Actions
workflow that runs on a schedule and opens a PR. **Cost:** MIT, Python, 1.6k★; requires that the
template be a Cookiecutter template and that each instance keep a `.cruft.json` — a real constraint,
and the reason to decide this now rather than after the second app exists. **Honest limit, which
matters given §16 rule 3:** `cruft check` compares *template version hashes*, not behaviour. It
tells you an instance is behind; it does not tell you whether the divergence is cosmetic or whether
a guard was removed. So cruft is the *presence* middle and the conformance suite (find 7) is the
*behaviour* middle, and you need both — which is exactly the pattern §2 found for triggers, arriving
from a completely different direction. State which property each compares, in the commit that
creates it.

**9 · cedar-spec — read this, then decide you don't need it, and keep one idea.** AWS maintains a
Lean formalisation of the Cedar authorization language with correctness proofs, alongside a
differential-randomized-testing harness that generates random schemas, entities, policies and
requests and asserts the Lean definitional implementation and the production Rust implementation
reach identical authorization decisions. Apache-2.0, 191★, 737 commits, live. For a small team this
is not adoptable — it is two languages, a theorem prover and a fuzzing harness. **But it is the
best available reference for what a fully-built middle over "declaration ↔ enforcement" looks like
when the stakes are authorization**, and one property is directly transplantable: the DRT harness
generates *the inputs together* — a schema, entities, policies, and a request are generated as a
consistent bundle, so the comparison never degenerates into comparing error messages. Contrast
#120's differential, which reported 14,650 disagreements that were entirely SQL text. If
`terpsi-music` ends up with the resolver predicate in Python and any second expression of it —
in SQL as a view, in a trigger, in a TypeScript port, in a manifest — generate the *scenario* and
compare *decisions*, never the two expressions.

**10 · Hermit — deterministic simulation testing for a team that will never write Rust.** The DST
tradition (FoundationDB → TigerBeetle → Antithesis) is the right instinct for a system whose worst
failures are ordering-dependent: a guardian edge invalidated between the authorization check and the
export, a court order landing mid-transaction, two lane writes racing. **The honest finding is that
this tradition has essentially nothing for Python** — I checked the community's own curated list
(`ivanyu/awesome-deterministic-simulation-testing`) and it names madsim, MadRaft and turmoil for
Rust, Unthread for C/C++, Antithesis as a commercial platform, and **no Python tools at all.** So
the transplant is a discipline plus one general-purpose tool. Discipline: seed every RNG, inject the
clock as a dependency instead of calling `datetime.now()`, keep the app single-threaded, and make
every test able to run the whole system end to end in-process against `:memory:`. Tool: Hermit
(BSD-3-Clause, Meta, 1.4k★, maintenance mode) determinizes arbitrary Linux x86-64 programs — thread
scheduling, time, timers, RNG, CPUID, file metadata — and its `--chaos --sched-seed=N` mode
"explores alternative deterministic schedules," so a schedule-sensitive failure reproduces exactly
from its seed. That is "run the whole system against an adversarial scheduler," available to a
Python test suite for the price of a wrapper command and 3–6× wall-clock. **Cost:** needs
user/PID/mount namespaces, ptrace, seccomp; Linux compatibility is "substantial but incomplete";
maintenance mode, so treat it as a research spike, not a dependency. Complement with APSW's VFS
(find 14) for the I/O-failure half, since Hermit determinizes scheduling but does not inject
errors.

---

## 4 · Coverage measures that catch "a fixture that cannot fail"

Ranked by cost-to-value for this codebase:

1. **Mutation score, split into mutation coverage and test strength.** killed/total versus
   killed/covered. The second number is the one that isolates the fixture that cannot fail: a
   mutant that is *executed* by a test and still survives means the test ran the code and checked
   nothing. Line coverage cannot express this and neither can branch coverage. Get it from
   cosmic-ray/mutmut intersected with `coverage.py` dynamic contexts.
2. **The positive/negative control pair, borrowed wholesale from assay validation (§5).** Every
   guard gets two tests: the forbidden act must be refused, *and the permitted act must be
   accepted.* The `terpsi-music` charter already mandates the first (`PROTECTED_AGENTS.md` I-12,
   "a test that attempts the forbidden act and asserts refusal"). It does not mandate the second,
   and without it a `WHEN 1` mutant — trigger fires always, refusing everyone — survives, which is
   §7's refusal indistinguishability as a coverage gap. My demo includes it: *"negative control
   (legit guardian consent must be ACCEPTED): accepted OK."*
3. **MC/DC (modified condition/decision coverage), applied by hand to the authorization
   predicate.** From DO-178C avionics practice: for a decision with N conditions, demonstrate that
   each condition *independently* changes the outcome, which needs roughly N+1 well-chosen cases,
   not 2^N. There is no MC/DC tool for Python that I could verify. But the resolver predicate is
   *one* decision with a handful of conditions, and writing its MC/DC table by hand is an
   afternoon that produces the definitive answer to "does every clause of this predicate actually
   do anything." It also catches the dead clause — a condition that can never independently affect
   the outcome is either redundant or masked by a bug, and in avionics practice unreachable code is
   a finding requiring resolution, not a shrug.
4. **Functional coverage / coverage closure, from hardware verification (cocotb-coverage,
   BSD-2-Clause, v2.0 Oct 2025).** Line coverage asks "did the code run"; functional coverage asks
   "did I exercise every combination I *declared* I cared about," and reports the unhit bins.
   `CoverPoint`/`CoverCross` in pure Python, exportable to XML/YAML. Declare the cross of
   {persona} × {L1..L5} × {consent state} × {valid/invalid/unknown guardianship} and let closure
   be the gate. The cultural import matters more than the library: **in hardware verification, a
   declared cover point that is never hit is treated as a defect in the testbench, not as a gap to
   be excused.** That is the discipline §10 is reaching for.
5. **Checked coverage** — the academic measure that is exactly on point (a line counts as covered
   only if it is in the dynamic backward slice of an *assertion*, so code that runs but whose
   result nothing checks is not covered). Schuler & Zeller, *Assessing Oracle Quality with Checked
   Coverage*. **I could not verify a maintained Python implementation.** Listed as an idea, not a
   tool; mutation test strength is the practical proxy.

---

## 5 · Weirdest things I found

**1 · The positive control, and the fact that a clinical lab would void the whole run.** In an
accredited diagnostic assay, every batch carries a known-positive and a known-negative control
alongside the patient samples. If the positive control does not come up positive, the run is void —
not the sample, *the run* — and no patient result from that batch is reported, however plausible it
looks. Interpretation is governed by pre-declared multi-rule criteria (Westgard rules) on a control
chart, decided before the data arrives, so nobody gets to argue after the fact about whether a
drift was real. Map that onto §10 and the whole "verification apparatus was itself verified"
problem changes shape: the fix is not *more tests*, it is **a control specimen in every suite
run**. Add one deliberately-broken guard to the suite — a fixture that ablates a known trigger and
asserts the ablation is detected — and make the *entire run* void if that control passes. A green
suite then means two things instead of one: the code behaved, and the apparatus was awake. #211's
killed mutation harness "turned every subsequent number into fiction" precisely because no control
existed to void the run. The wider scheme (ISO/IEC 17043 proficiency testing: an accreditation body
periodically sends every lab an unknown-to-them sample and grades the answers) is the natural
extension to §17's conformance suite: the template doesn't just publish the suite, it periodically
sends each instance a blind case and records the response. *Domain knowledge; not fetch-verified.*

**2 · Ballot manifests and risk-limiting audits (Arlo, AGPL-3.0, VotingWorks, Python, 153★,
2,165 commits).** An RLA works by drawing a random sample of paper ballots and comparing them
against the electronic tally, escalating the sample — up to a full hand recount — until either the
outcome is statistically confirmed at a declared *risk limit* or it is overturned. Two ideas here
that nothing else in this report has. First, **the risk limit is declared before the audit, not
after**, and it determines the sample size; you commit to how wrong you're willing to be, in
public, in advance. That is the honest way to answer "how many mutants is enough" — pick a risk
limit for the guard modules and derive the count, instead of running what fits in CI and reporting
whatever score results. Second, **the ballot manifest**: before sampling, the jurisdiction declares
how many ballots exist and where they are, and the audit reconciles the physical batches against
that manifest. A batch that does not match the manifest is a finding *in itself*, independent of
how the votes fell. That is §2's schema manifest, invented independently by election officials, and
it carries the same lesson: the inventory and the contents are two different audits and the
inventory is the cheaper one. Arlo also has the escalation ladder, which §10 lacks: a stated
procedure for what happens when the audit *fails*, agreed before anyone is embarrassed.

**3 · Hermit's chaos mode — a deterministic hypervisor as a testing tool, from Meta, in maintenance
mode.** You can take an existing, unmodified, nondeterministic program and make its thread
scheduling, clock, timers, randomness, CPUID and file metadata deterministic from the outside, then
*deliberately search the schedule space* with `--chaos --sched-seed=N`. It is the FoundationDB
insight — determinism first, then adversarial scheduling — delivered as a `ptrace` sandbox instead
of a rewrite of your application in a simulation-aware framework. BSD-3-Clause, 1.4k★, 3–6×
overhead, "not a security boundary," Linux syscall coverage "substantial but incomplete." The
weird part is the trade: DST normally costs you your whole architecture, and this offers it for a
wrapper command and a 5× slowdown, at the price of depending on a maintenance-mode ptrace
hypervisor. Worth a spike precisely because the DST ecosystem has *nothing* for Python — the
community's own curated list names no Python tools at all.

**4 · APSW auto-generates its own fault injector.** Verified in the tree: `tools/genfaultinject.py`
generates `src/faultinject.h`, which is then `#include`d at call sites throughout `src/*.c`
(`pyutil.c`, `traceback.c`, …), with a control hook `APSW_FaultInjectControl(faultfunction,
filename, funcname, linenum, args)`. So the fault-injection harness is *derived from the source*
rather than hand-maintained alongside it, which means a new call site cannot silently escape the
injector — a rename or an addition cannot quietly shrink the tested set. That is §16's
`test_allowlist_entries_exist` lesson solved by generation rather than by checking: don't verify
that the declaration matches the tree, **derive the declaration from the tree.** For
`terpsi-music`, the transplantable version is generating the adversarial-test *skeleton* from the
schema — enumerate every trigger and `CHECK` in `sqlite_master`, emit one xfail-strict ablation test
per object, and fail the build on any object with no corresponding test. A new trigger added without
an adversarial test then breaks CI on the day it is written, which is the only day anyone remembers
why it exists. (Separately, APSW exposes SQLite's VFS to Python, so the same repo gives you the
route to inject `EIO`, short reads and failed `fsync` into the escrow/restore paths of §5 and §11.)

**5 · rustls runs BoringSSL's test suite against itself, and keeps a written list of the tests it
fails.** rustls ships a `bogo/` directory with a shim binary that adapts rustls to BoGo — Google's
TLS conformance suite, written for a different library, by people with no stake in rustls passing —
plus `config.json.in` carrying an `ErrorMap` and an explicit known-failure list. Two inversions of
normal practice. First, **the suite is chosen for its independence from you**: a conformance suite
you wrote cannot tell you that your mental model is wrong, only that your code matches it. Second,
**the accepted failures are a versioned, reviewable file** rather than a folk memory or a skipped
test. That is a tombstone (§16) for each deviation: named, dated, in the tree, reviewable in a
diff. The transplant for §17: when an instance cannot pass a clause of the conformance suite, the
answer is not to weaken the suite or skip the test but to add a line to a `known-failures` file
that names the clause, the reason and the date — and then to *count that file*, in prose, with cog,
so the number of accepted deviations is a published figure that someone has to look at. §16's
consolidation metric applied to conformance: a correct instance makes that file shorter.

---

## 6 · Claims I could not verify (read as `unknown`, not as absent)

CLAUDE.md §13 and §17 apply to this report as much as to the code.

- **`sqlite.org` is unreachable through this proxy** (HTTP 403 for the whole domain, including
  `/testing.html`), and `web.archive.org` is blocked by the tool. SQLite's own documented practice
  — 100% MC/DC branch coverage, exhaustive OOM/I/O-error/crash fault injection, and its own
  mutation-testing programme — is the most on-point single document for this entire slice and I
  **could not read it**. It is widely cited and I believe it says all of that; treat it as
  `P2 Cited`, not `verified`. Read it first thing on a box that can reach the domain.
- **`pitest.org` 403.** PIT's "test strength" metric (killed/covered, distinct from mutation
  coverage) is reported from memory. The *idea* is what matters and it is computable locally from
  cosmic-ray plus `coverage.py` contexts, but do not quote PIT's definition without checking.
- **Wikipedia 403** — so bebugging / fault seeding (Harlan Mills, ~1972: seed N known faults, and
  from the fraction testers find, estimate the residual defect count; the ancestor of mutation
  testing, and the basis for capture-recapture defect estimation from two independent reviewers'
  overlap) is unverified. Worth chasing: this fleet has an observed 6-vs-0 split between defects in
  verification apparatus and defects in code under verification, and capture-recapture is the
  standard way to turn that kind of observation into an estimate of *how many remain*.
- **DO-178C / DO-330** tool qualification — the avionics rule that a verification tool which could
  fail to detect an error must itself be qualified, at a level derived from the harm it could let
  through — is the doctrinal citation for "the verification apparatus was itself verified," and I
  did not fetch a source. Also unverified: the DO-178C independence requirement (verification of
  the highest criticality level must be performed by someone other than the developer), which is
  the organisational version of the same idea and is free to adopt in a small team as "the person
  who wrote the guard does not write its adversarial test."
- **ISO/IEC 17043 proficiency testing and Westgard rules** (§5 entry 1) are domain knowledge, not
  fetched.
- **Alloy's license** — the repo page confirmed a license file exists and that it is open source
  but did not name it. Commonly reported as MIT; verify before shipping anything derived.
- **Atlas's licensing is a live hazard.** The `ariga/atlas` repo is Apache-2.0, but the distributed
  CLI mixes free and paid ("Atlas Pro") functionality and the "50+ analyzers" figure comes from
  marketing copy on the repo page. Check which `migrate lint` analyzers are in the Apache-2.0 build
  before depending on one.
- **`sqlglot` parses SQLite `CREATE TRIGGER` as an opaque `Command`** — this one I *did* verify, by
  running it (sqlglot 30.14.0, output quoted in §2). Flagging it here too because it is the finding
  most likely to be contradicted by a README.
- Stars/commits throughout are as reported on repo pages on 2026-07-30, and are a proxy for
  activity, not a measurement of it. Two entries are explicitly stale: **mutatest** (last push
  2023-02) and **mutant-swarm** (last updated 2024-08). **Hermit** self-describes as maintenance
  mode. **SchemaAnalyst** is a research artifact.

## 7 · Artifacts in this directory

- `trigger_mutation_demo.py` — runnable, stdlib-only. Four SQLite mutants (trigger rename, `DROP
  TRIGGER`, neutered `WHEN`, dropped `CHECK`) against an adversarial test and a `sqlite_master`
  manifest test, plus the negative control. Output table in §2. Lift the `trigger_inventory` and
  `check_constraint_inventory` helpers directly.
- `sqlglot_probe.py` — NOT RETAINED. The probe that established sqlglot cannot see inside a
  trigger and that its AST diff reports a rename and an evisceration identically. The finding it
  produced is recorded in §2 and is unreproduced: it rests on `sqlglot` 30.14.0, which this
  repository does not depend on and should not acquire for one probe. Treat it as `P2 Cited` on a
  source that no longer exists, and re-derive before anything is built on it.
