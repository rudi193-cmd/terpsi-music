# Open-Source Survey — what can be borrowed, and from where

**Status:** `draft`, unsealed. Produced by 24 parallel scouts on 2026-07-30. **No human has verified a single row.** Under §8.2 and §16 that makes this document a draft: usable for search and routing, never quotable as what the fleet has confirmed.

**Scope:** external open source only. This is the counterpart to §14, which maps this design onto the fleet's *own* components. Where §14 asks "do we already have this," this asks "has somebody outside already built it."

**This document does not govern.** `docs/ARCHITECTURE.md` governs. Where the two disagree, the doc wins and this file is the defect. Nothing here is a decision; §12 is where decisions live and §18 is where the open list lives.

**Evidence:** every claim traces to a scout report under `docs/survey/`, named in part 12 below and non-authoritative by the same rule as this file.

---

## 0. How to read this

§18 item 0 records the defect this survey is built to avoid: **an unverified table and a verified one look identical.** So there is no "Exists" column here. Every claim carries a `P`-rung (§15) describing *this survey's* evidence for it, not the quality of the project:

| | Rung | Here it means |
|---|---|---|
| **P1** | Measured | A scout ran, counted, implemented, or reproduced the thing this session |
| **P2** | Cited | The repository or a named source file was fetched and read this session |
| **P3** | Fitted | A conclusion derived from `P1`/`P2` facts by an argument stated in the scout report |
| **P4** | Estimated | Inferred from an analogous project or from search text, not from the artifact |
| **P5** | Assumed | Named only; the host was unreachable. **Do not build on it.** |

Rungs propagate by `min` (§15) — a `P3` conclusion resting on a `P5` licence claim is `P5`. `seal_state` is `draft` for every row and there is deliberately no `verifier` column, because there is no verifier.

### Two limits on the whole sweep

Stated here rather than in a footnote, because they bound every section below.

- **Search was exhausted.** The session's WebSearch budget (200 calls) ran out partway through. The first several scouts had search; the rest ran on GitHub repository and code search plus direct fetches. **Discovery is thinner in the later slices, not more complete** — each scout's report records where its own coverage stops.
- **Most non-GitHub hosts were refused by the egress proxy.** Among them: `sqlite.org`, `loc.gov`, `w3.org`, `rfc-editor.org`, `studentprivacy.ed.gov`, `cdc.gov`, `osha.gov`, `ecfr.gov`, `huggingface.co`, `hl7.org`, and most vendor documentation. Anything resting on those is `P5` and marked so. This is why several licence and model-weight claims below are open questions rather than facts.

A third limit worth naming: this survey was assembled by one reader from 24 reports. Its own summarisation is unchecked, which is the §16 pair it creates — see part 13.

---

## 1. Findings that change the design

These are not tools. They are twelve places where the sweep found the document to be wrong, incomplete, or contradicting itself. They are the reason to read this file at all; everything from part 3 onward is procurement.

### 1.1 Escrow and cryptographic erasure contradict each other — `P3`

§5 asks for both: a key recoverable without any single person (2-of-3 Shamir across director, district administrator, sealed offline share), and per-subject erasure that honours a guardian's request. If a quorum reaches a root key from which subject DEKs derive, **every erasure is quorum-reversible while the guardian was told the record was destroyed.** Nothing found resolves it. This is a §12 decision, not a research item, and it should be added to §18's blocking list.

*Scout 01.*

### 1.2 `invalid_at` cannot say "entered in error" — `P2`, found twice independently

§7.1 ends a relationship by dating it. That expresses *was true, then ended*. It cannot express *was never true* — and the difference is a guardian record entered by mistake in a custody dispute, which rule 16's durability then makes permanent. Two unrelated traditions draw the line explicitly: `pg_bitemporal` separates `correction` from `inactivate` as distinct verbs, and Wikibase separates a `deprecated` rank carrying a **mandatory reason** from a normal-rank statement with an end time. Recommendation: a mandatory `invalidation_kind` alongside `invalid_at`, decided before migration 001.

*Scouts 05 and 24, independently.*

### 1.3 The guardian send cadence contradicts the contact-restriction rule — `P3`

§4.2 says send to both guardians on the same cadence so timing does not leak a custody arrangement. §4.1 says a guardian under a contact restriction must not be messaged. Those cannot both hold: **skipping the restricted mailbox makes the envelope count the custody order**, which is the precise disclosure the cadence rule exists to prevent. A read-cap/write-cap split — deliver an envelope the restricted mailbox cannot open — preserves both, at the cost of a design decision with safety consequences. Belongs with the §7.1 work and needs a human to choose it.

*Scout 02.*

### 1.4 At this scale, the strongest privacy design is also the simplest — `P1`

Computed rather than surveyed: 200 households at roughly six transactional interactions per year is about **23 messages per week system-wide.** Broadcasting the entire weekly batch to every client — trivial private retrieval, the relay learning nothing about recipients — costs about **18.8 MiB per household per year** at a 16 KiB envelope. Constant-rate delivery is about **0.81 MiB per household per year**. Every mixnet and PIR scheme surveyed exists to make this affordable at millions of users. **Do not build a mixnet, a PIR scheme, or a padding state machine.** Related correction: Padmé is the wrong padding function here — implemented and measured at 305 distinct output sizes over 512 B–4 MiB; one fixed size is strictly better.

*Scout 02.*

### 1.5 A renamed SQL trigger is an ineffective mutant — `P1`

§10 records three mutations that renamed a trigger rather than disabling it, so it kept firing. The reason is mechanical: **SQLite fires triggers by definition, not by name**, so a rename is a no-op being scored as a killed mutant. Reproduced this session across four variants, with a second result: a `sqlite_master` name manifest catches the rename but **misses a neutered `WHEN` clause**, while `DROP TRIGGER` cannot be a no-op. So the primary mutation operator for schema guarantees must be **ablation, not edit**, and both middles ship because neither covers the other. Roughly 60 lines, no dependencies.

*Scout 13, with runnable probes in its report.*

### 1.6 The obvious translation engine fails the families §14 of the capability map is for — `P1`

Counted from the package index: Argos/LibreTranslate ships **100 packages across 50 language codes, and 98 of 100 pairs have English on one side.** Present: Spanish, Vietnamese, Arabic, Chinese, Russian, Tagalog, Urdu. Absent: Haitian Creole, Somali, Nepali, Burmese, Amharic, Tigrinya, Pashto, Dari, Hmong, Karen, Marshallese, Khmer, Punjabi, Tamil. Adopted naively it serves the families with the most existing support and **returns nothing, silently, to the ones named as the real access barrier** — rule 13 violated by default on the most equity-sensitive surface in the system. Any translation feature needs a coverage manifest that renders `unavailable` rather than empty.

*Scout 20.*

### 1.7 Nobody models per-audience visibility of a chosen name — `P3`

A student may be out to the director and not to a guardian; a printed concert program has a different audience than a roster. §20 of the capability map requires this handled deliberately. No system found models it. The base exists — HL7 Gender Harmony gives `Name to Use` and `Pronouns` as `0..n` with validity periods, structurally separated from source-attributed recorded sex, and Gramps' private-flag-plus-export-proxy is the nearest prior art for the printing half — but the per-audience layer is new work, and it is the case where a bug is a serious harm.

*Scouts 23 and 12.*

### 1.8 Refusal 6 is correct and needs an instrument — `P2`

"The system presents, a human decides" is right, and as built it hands a director a blank page at the moment they most need help. Two complementary answers. For scheduling, the property that makes the refusal *testable* is **permutation-invariance under student relabelling**: no objective coefficient, weight, or tie-break indexed by student identity, verified by permuting two students and asserting the feasible set permutes correspondingly. For genuinely scarce slots, `panelot`/`stratification-app` supplies declared quotas plus a lottery plus a **publishable per-person selection probability**. And the happy result: the flagship rotating pull-out scheduler is compliant *in its natural formulation* — a Latin-rectangle completion in which every student's row is identical by construction.

*Scouts 10 and 24.*

### 1.9 The SIS seam cannot carry the fields that matter — `P2`

Ed-Fi's own OneRoster bridge hardcodes `pronouns` and `agentSourceIds` to `NULL`. So chosen name, pronouns, and the guardian graph are **locally owned by necessity** — which is also the safe outcome, because no sync can then clobber them and the SIS cannot leak them. The realistic seam shrinks to a one-way CSV pull for enrolment, grades, and attendance, which is far smaller than the integration project §13 implies.

*Scout 23.*

### 1.10 Rubrics need versions, and a seal must cite one — `P2`

`Divinum Officium` renders the same liturgical date under six co-existing historical rubric editions, all retained, with golden-file regression tests. Adjudication rubrics change every few seasons. **A 2023 caption score read against today's rubric is a falsification**, so rubric edition belongs in the seal, and §8.1's "rubrics are projections over commentary" needs a version axis it does not currently have.

*Scout 24.*

### 1.11 Nothing statically checks a module's declared write paths — `P3`

§6 names the gap; the sweep confirms no tool in any ecosystem closes it. Recommended shape, built to §16's rules: **declare the paths once, enforce twice** — an extended AST walk plus Landlock rules derived from *the same declaration* — name the reconciler in the same commit, and prove it by mutation. One caveat for the doc: Landlock's network rules are **port-based, not address-based, and TCP only** — a layer, not a boundary. A second, from a different direction: an AGPL *subprocess* is equally invisible to the import checker, so the licence question and the egress question share one blind spot.

*Scouts 06 and 07.*

### 1.12 Session reconciliation is the contribution — `P3`

Nothing found reconciles a declared purpose against observed behaviour at session close; the nearest tool records a reason and never checks it. So §7.2 is not a procurement item. Two things make it cheaper than building from nothing: **DHIS2's `protected` access level** ("break the glass" — reason on entry, temporary ownership, audit attached to the record) is the closest shipped shape, and **MonPoly** checks log files against metric first-order temporal logic policies, which makes the exit diff mutation-testable by injecting a violating trace.

*Scouts 04 and 11.*

---

## 2. Where §18's items landed

§18 is the open list. This is what the sweep did to it, and two items moved.

| §18 item | State after the sweep | Rung |
|---|---|---|
| **0** · Read §14 as a claim | Reinforced, with a worked instance: a tool was nearly recommended off its README, then found to report a cosmetic rename and a gutted `WHEN` clause identically — §16's mis-aimed middle, inside the checker | `P1` |
| **1** · `L1–L5` undefined | **Unmoved.** Still needs writing. But the *shape* has strong prior art: coded ordinals carrying `flag_values` + `flag_meanings`, one meaning per value, with the quality code in a separate variable | `P2` |
| **2** · Disposition of the playground copy | Unmoved — a decision, not research | — |
| **3** · No schema for the lane model | **Substantially answered.** EHR-per-subject is W-1; `EventRef` + `role_type` is W-3 with a worked shared-event example; `PotentialMatch`-not-persisted removes the unmerge problem. Largest remaining hole: per-subject *physical* partitioning prior art | `P2` |
| **4** · Which surfaces exist | **Answered as a shape:** `ColorMode`/`SizeMode`/`isVisualModeDisabled` — print is a colour mode, kiosk is a size mode, audio-only is a flag. Recommendation: four backends (TUI, server-rendered HTML, print, text), one middle, layout `surfaces/{tui,web,print,text}/` | `P2` |
| **5** · Exit line unwritten | **Answered as machinery.** A BagIt profile is a JSON contract for the exit package, so enrolment can dry-run the export and refuse to open the lane if it fails — W-6 as executable code. Four specific claims that make the target sentence dishonest today are itemised in the scout report | `P2` |
| **6** · No conformance suite | **Shape found.** Four artifacts — product manifest, README, **raw log**, parsed results — in a directory named for the suite version, merged by a human | `P2` |
| **7** · Score anchoring unchosen | **Dissolved.** Make `anchor` a sum type with `kind ∈ TAP\|ALIGNED\|MANUAL\|UNKNOWN`, `wall_clock` always required, `measure` optional. Tap-to-mark first and unconditionally; alignment is a refinement a tap constrains; legacy OMR is third and separable | `P3` |
| **8** · Second cross-face dependency | Untouched — internal | — |
| **9** · Practice logging vs no-leaderboard | **Answered twice.** A Bayesian recall model that tolerates irregular review makes sparse practice *information* rather than failure; and acoustic fingerprinting verifies a passage was practised **without storing or transmitting audio at all** | `P2` |
| **10** · Whose consent governs which surface | Unmoved as a mapping, but the vocabulary exists: a standard that puts purpose in **both** the grant and the audit record | `P2` |

And one item to add, from finding 1.1: **escrow versus erasure is undecided and blocking.**

---

## 3. Adopt now

Verified this session, cheap, and load-bearing. Licences as read; re-read before committing.

| Project | Licence | What it buys | Lands at | Rung |
|---|---|---|---|---|
| `whisper.cpp` | MIT | Local transcription as a CLI over local model files — **no server, no socket**, runs under full network isolation | §5.1, §8.2 | `P2` |
| `sherpa-onnx` | Apache-2.0 | Offline ASR *and* diarization in one native binary; no Python, no GPU, no internet | §8.2 | `P2` |
| BagIt + BagIt Profiles + `bagit_profile` | CC0 | The exit package as a validatable contract | §11.1, W-6 | `P2` |
| Frictionless Data Package | Unlicense | `datapackage.json` generated from the live schema, shipped *inside* the export | §11.1 | `P2` |
| `import-linter` | BSD-2 | Forbidden-import contracts over **indirect** chains, which single-element assertions miss | §6 | `P2` |
| Hypothesis `RuleBasedStateMachine` | MPL-2.0 | Lane-model rules and invariants with shrinking — **run before migration 001** | §18 item 3 | `P2` |
| `cog --check` | MIT | One CI line closing rule 17 for every count asserted in prose | §10, §18 | `P2` |
| `CPMpy` (`tools/explain`) | Apache-2.0 | Minimal-conflict enumeration, so infeasibility returns *which constraints collide* rather than a least-bad schedule | §7.4 W-7 | `P2` |
| `age` recipient-stanza format | BSD-3 | A solved header format for per-record keys wrapped per circle | §5 | `P2` |
| `catppuccin/whiskers --check` | MIT | Renders a template and exits non-zero if it differs from committed output — the token pair's middle | §15 | `P2` |
| Atkinson Hyperlegible Next | SIL OFL | One licence-clean family for TUI, web, and print; the 2025 release adds a monospace cut | §15 | `P4` |
| `hledger` balance assertions | GPL-3.0+ | Three-way reconciliation as a **parse error** — the journal will not load if the figures disagree | §7 of the capability map | `P2` |
| `grocy` | MIT | The only mature battery-lifecycle tracker found; §5 of the capability map calls batteries the top day-of failure | §5 of the capability map | `P2` |
| `OpenMarch/schema` | Apache-2.0 | An open drill format whose `coordinates` array is one row per person per set — rule 8 satisfied upstream. Young and unproven | §9 of the capability map | `P2` |
| `pdfcpu` | Apache-2.0 | Visible per-student stamping | §4 of the capability map | `P4` |

**Steal the shape, not the dependency** — verified, but adopt as ~a few hundred lines rather than a package: `nomenklatura`'s judgement edges (`NO_JUDGEMENT` until a human decides, a tested unmerge, and `NEGATIVE` as a **durable blocking edge** so two siblings stay unmergeable forever); OpenStreetMap's `Redaction` (erasure as an authored, reasoned, dated record that owns by foreign key the rows it hides, and is revocable); Koha's offline circulation queue with its rejection taxonomy and its pool-and-globally-sort rule for multi-device queues; CAP 1.2's alert envelope; Fineract's per-permission maker-checker; `vxsuite`'s theme types.

---

## 4. Prior art per section

Condensed. Each row's evidence is in the named scout report.

| Section | What exists outside | Verdict | Rung |
|---|---|---|---|
| §3 the drop | `briar-mailbox` — owner-bound credential, accept ciphertext, hold, hand over, delete | Steal the shape; AGPL + JVM argues against the code | `P2` |
| §3 relay non-enumerability | A constant-size padded set of blinded challenges covering the whole store, so the server never learns which mailbox a fetcher owns | Best idea found for §4.2; PoC, not production | `P2` |
| §3 edge replicas | `cht-core` — per-user partial replication in a health context, using **database-per-user rather than a filter** | Privacy rule and performance rule agree | `P2` |
| §5 at-rest sealing | `age` / AWS Encryption SDK header formats. **`gocryptfs` is not a fit** — one content key with per-file IDs as nonces, no per-file DEK to wrap | Adopt a format | `P2` |
| §5 escrow | Clevis `sss` pin — shipping k-of-n threshold unlock nesting other pins under a Shamir threshold. Covers the disk, not `vault.key` or the DEKs | Partial | `P2` |
| §5 count anchor | A standardised checkpoint of origin, **tree size**, root hash. BagIt's `payload-oxum` is the same invention independently | Adopt; already standard | `P2` |
| §5 partitioned erasure | Merkle formats with *elision* — remove a subtree, keep its digest, enclosing signatures still verify | Licence unresolved; SD-JWT is the boring fallback | `P4` |
| §6 write-path declaration | Nothing. Landlock supplies runtime enforcement only | Build; see finding 1.11 | `P3` |
| §6 capability drift | Transitive capability classes with a committed baseline, CI failing on capability **gain** rather than absolute state | Better shape than a static allowlist | `P2` |
| §7 guest grants | `REMS` — outsiders apply for time-boxed access to sensitive person-records, a handler dispositions it, an end-dated entitlement results | I-6 already built | `P2` |
| §7 expiry primitives | Attenuable tokens with expiry as a check rather than a field, and terminal "sealed" tokens — nearest existing primitive to W-2 | Two concepts, not the library | `P2` |
| §7 revocation-as-date | PREMIS rights: symmetric start/end dates, mandatory restriction codes, and **a blank end date meaning *unknown*, not *forever*** | Adopt the vocabulary | `P4` |
| §7.2 export gate | An NHS-data export gate with two independent reviewers, **structurally impossible self-review**, and rejections as workflow states | Closest shipped analogue to the knock | `P2` |
| §7.2 read vs export | Verify-caps — prove a record exists and is unaltered **without disclosing it**. A third permission class §7.2 has not named, and what an inspection request actually needs | Name it | `P4` |
| §8 identity | Match candidates computed on read and **never persisted**, so there is nothing to unmerge; `name_nickname` weighted highest — the Robert/Bobby fix is a stored field, not a better metric | Adopt both | `P2` |
| §8.1 anchoring | A published music-encoding standard: measure-plus-beat typed anchors, four addressing levels, attribution, and a performance layer where **one score anchor maps to several recordings** | Largest single reuse found | `P2` |
| §8.1 disagreement | A graded citation ladder with named inverses — `qualifies → disagreesWith → disputes → critiques → refutes`, plus `corrects`/`retracts` | Strictly better than one collapsed relation | `P2` |
| §8.1 contested passages | Critical-apparatus markup making the contested passage a first-class object, with `@type=substantive\|orthographic` — the column that stops crying wolf when two judges write synonyms | Adopt | `P2` |
| §8.2 seal state | Completion and verification as **orthogonal** flags, where verified is invalid without a named verifier, organisation, and timestamp | §8.2's table has one axis where it needs two | `P2` |
| §8.2 pipeline | Judge audio is single-speaker by construction, so diarization does not belong on the critical path; the cheapest diarizer is a second input channel | Also makes the material lane-separable | `P3` |
| §11.1 tombstones | `reserved` field declarations, breaking-change linters, and a `*_missing` lint with a non-zero exit — three forms of "removal must be accounted for or CI fails" | Adopt | `P2` |
| §15 one mapping table | Six ordinal scales in one module with paired named conversions, raising rather than coercing, and **refusing to map "cannot be judged"** | Adopt the shape, add the composition rules | `P2` |
| §15 scale direction | A standards body that had epistemic and access status fused, unfused them, and **still loses information because its rungs are bare letters** | The strongest argument for the prefix rule is a reversal | `P4` |
| §15 rung typing | Units-of-measure libraries make cross-scale comparison fail **at import time** rather than in review | Structural, not remembered | `P4` |
| §15 citation decay | Two states the current vocabulary lacks: **`deviated`** (resolves, no longer supports *our* claim) and **`usurped`** (domain resold; rendering suppressed) | Add both | `P4` |
| §1 of the capability map | Note-level score↔performance alignment, offline and online; pitch engines that are permissively licensed for **code and weights**; on-CPU pitch fast enough to run on the student's device and delete the upload path | Adopt | `P2` |
| §3 of the capability map | Rotating pull-out reduces to Latin-rectangle completion; minimal-conflict enumeration replaces auto-resolution | See finding 1.8 | `P2` |
| §4 of the capability map | Hierarchical storage locations with part-level counts, plus `instock_unknown` — rule 13, arrived at independently; usage logged as a **side effect of performing** rather than typed in | Adopt both | `P2` |
| Uniforms and inventory, §6 of the capability map | Army property doctrine: the **component hand receipt** is the piece-level garment record, and the **sub-hand receipt** is how a section leader holds twelve harnesses without becoming a group grant under rule 5 | Doctrine, not code | `P4` |
| §7 of the capability map | A production transit-concession system applying discounts by **group membership at the processor**, storing nothing about the user — invisible aid with no waiver field and no discount line | Closest thing to a direct answer found | `P2` |
| §12 of the capability map | A threshold is a **tuple, not a number** — regulators disagree on the noise exchange rate, so value, publisher, version, and jurisdiction travel together; and a black globe thermometer moves the heat threshold from `P3` to `P1` for tens of dollars | Adopt the record shape | `P2` |
| §14 of the capability map | An alert envelope with per-language blocks, distinct effective/onset/expires fields, `msgType` including `Cancel` **by reference rather than deletion**, and three scales that never collapse | Steal the schema | `P2` |
| §17 of the capability map | Suppression computed **once over the union of everything published**, or readers difference the reports; and vector chart formats blocked from release **because they embed the suppressed data** | Adopt both rules | `P2` |
| §20 of the capability map | Erasure as an **additive** record whose suppression list deliberately **does not propagate**, because a replicating delete is a weapon | Constrains what §3 sync may carry | `P4` |

---

## 5. Refusals, confirmed and extended

The sweep tested the refusal list against the world. It held, and it caught things.

**Refusals that fired unprompted.** A video-based ergonomic scoring tool for students was written up by its own scout as a **refusal case** rather than a candidate — it collides with refusal 1, prohibited scope `SA-3`, and rule 6, and the existing rules answered it without anyone litigating. A drone-choreography library's automatic point-matching calls a vendor's servers over HTTP, **undisclosed in its README** — refusal 1 waiting to happen, in an otherwise excellent pattern. A diarization library ships a cloud "precision" path that sends audio to a vendor: a `willow-seed`-class fallback one import from `MEDIA_MINOR`, which per §6 must be disabled and *tested as disabled*, not merely unused.

**Two extensions worth writing into the refusal list.**

- **Agreement about a *passage* is a property of the passage; agreement about a *judge* is `SA-3`.** Every inter-rater-reliability library in this space computes durable per-annotator competence scores, and they arrive free inside any package imported for the useful part. This needs a test that attempts per-judge aggregation and asserts refusal, written *before* anyone reaches for a library. `P2`
- **A forensic prohibition worth adopting verbatim:** never phrase a conclusion in the direction of the proposition. It maps onto `SA-3` and belongs beside it. `P4`

**And one refusal to add on the strength of finding 1.6:** a translation or accessibility feature that silently returns nothing for an unsupported input is rule 13 violated where it matters most. Absence renders as `unavailable`, per language, per surface.

**A compliance question the sweep raised about existing fleet code.** A Bayesian-knowledge-tracing posterior is a durable per-student numeric rating, which is arguably `SA-3` — and §14 lists a component holding one as "adjacent, worth reading before rebuilding." Reading it may produce a finding rather than a reuse. Preferred fix is to make cross-student comparison **unrepresentable** rather than gated. Relatedly, the sweep recommends *against* deep knowledge tracing on privacy grounds rather than accuracy grounds: it produces uninterpretable embeddings about minors, which is the worst possible artifact to hold when a guardian exercises an inspection right. **Interpretability is a privacy feature here.** `P3`

---

## 6. Convergences

Where two scouts with different briefs found the same thing, the finding is stronger than either report.

| Convergence | Scouts | Meaning |
|---|---|---|
| `invalid_at` cannot express "entered in error" | 05, 24 | Bitemporal databases and knowledge bases draw the same line. See finding 1.2 |
| Local inference needs no server at all | 06, 07 | Two independent routes close §14's network-isolated-inference row |
| Nothing detects colour-only encoding of an ordinal | 09, 21 | The gate must be written: forced-monochrome render, assert the prefix, mutate to confirm it fails |
| A published standard already carries the commentary primitive | 07, 08, 16 | Three briefs converged on the same music-encoding standard from alignment, annotation, and cataloguing |
| `immudb` is source-available, not open source | 05, 18 | Fails the §11.1 exit test as a dependency |
| A sovereign SMS gateway exists and is active | 11, 20 | The same Apache-2.0 project, found from humanitarian and comms directions |
| Erasure must be an additive, authored record | 05, 24 | OpenStreetMap redactions and Fossil shunning agree, in unrelated systems |

---

## 7. Tombstones

Projects that are dead, archived, renamed, or relicensed — several of which are top search results, which is the trap. Rule 20 applies to citing them.

| Project | State | Rung |
|---|---|---|
`apache/incubator-kie-optaplanner` | Archived | `P2` |
| `TimefoldAI/timefold-solver-python` | Archived | `P2` |
| `minio/minio` | **Archived read-only 2026-04-25**; maintainers moved to a commercial product. Any install leaning on it for on-prem WORM has regressed on *survives the vendor* with no code change | `P2` |
| `willow-rs` (the unrelated open-source Willow Protocol) | Archived on GitHub 2025-10-23, moved to a host the proxy blocked — destination **unverified** | `P4` |
| SMSSync | Last commit 2017-02-21 — and a top search hit | `P2` |
| FrontlineSMS | 2014, one stray 2016 commit — also a top search hit | `P2` |
| Freedom Fone | Died 2016 | `P4` |
| ELMO | Renamed to NEMO | `P4` |
| ObscuraCam | Translation-only commits since 2022, **not archived**, so it reads alive | `P2` |
| `pyre-check` | Archived; its analysis tool moved | `P2` |
| `deptrac-src`, `hairgap` | Archived | `P2` |
| `webbkoll` | Archived | `P2` |

Best real-world example of rule 20 found anywhere in the sweep: **RapidFTR's retirement notice.** Worth reading before writing the next tombstone.

---

## 8. Licence traps

Each of these looks adoptable and is not, or is not what its README implies.

- **`RapidPro` is BSL-1.1 — not open source until 2028-07-29.** The most-recommended tool in its space. `P2`
- **`PowerSync`** has the best partial-sync semantics found and is FSL-licensed — fails §11.1's exit test as a dependency. `P2`
- **`immudb`** is BSL-1.1. `P2`
- **`Loxya`/Robert2** is CC BY-NC-SA 4.0 — not open source, and the non-commercial clause is ambiguous for a fee-charging program. `P2`
- **`Muscat`**, the most domain-relevant cataloguing application in existence, **ships no LICENSE file and no licence statement.** `P2`
- **`zetavg/Inventory`**, the best-fitting RFID codebase found, is "All rights reserved" with hand-written exceptions. `P2`
- **Model weights diverge from code licences**, repeatedly: a widely-used beat-tracking library is permissive in code and **non-commercial in its models** — and the models are the part that works. Quality-estimation models for translation are non-commercial with one exception. `P2`
- **`Essentia`'s model licences are unknown** — both licensing pages were refused and the docs are silent. Treat as **blocking**, not as permissive. `P5`
- **`Gordian Envelope`** resolves to no declared licence on GitHub despite an IETF draft. `P2`
- **`XCP-explain`, `RobinX`, `MuckRock`** — no LICENSE file. `P2`
- **AGPL where it bites:** four audio and OMR tools are AGPL-3.0, which is hazardous next to a parent-facing PWA — and an AGPL **subprocess** is invisible to the import checker. `P2`
- **Bypasses inside otherwise-good mechanisms:** a maker-checker implementation ships a checker-superuser bypass; an export-boundary pattern carries a trusted-source bypass. Adopt the mechanism, forbid the bypass, write the adversarial test. `P2`
- **A named-local mode with a cloud dependency in the tree:** the recommended SMS gateway lists a push-notification service as a dependency. Prove it inert in local mode as an acceptance mutation test rather than trusting the mode's name. `P2`

---

## 9. Deserts

Where nothing exists. These are the build-versus-adopt answers, and collectively they are the argument that this application is worth writing.

**Confirmed absent by search this session** — `P2` unless noted:

- Dated, staged, revocable **human-subject** consent as a library. The relevant topic tag is *entirely cookie banners*.
- Session reconciliation of declared purpose against behaviour (§7.2).
- Static checking of declared filesystem write paths (§6).
- A retention schedule expressed as data.
- Mutation of SQLite triggers. Constraint mutation has prior art; trigger mutation does not.
- Automated detection of colour-only encoding of an ordinal scale.
- Booster or PTA treasurer software.
- Band or orchestra **part**-management.
- A maintained public-domain term calculator; cue-sheet or rights-clearance tooling.
- Piece-level costume and wardrobe tracking; theatre production inventory; PPE inspection intervals; school device checkout; band instrument inventory.
- Any open reader for proprietary drill formats — and nobody has attempted one.
- Cleaning-tracking for drill; a drill-revision staleness engine **in any domain**; a parade planner; an acoustics-to-adjudicator coordinate bridge.
- A maintained large-ensemble score follower. The only one is 4★ and dead since 2016; everything published is piano.
- Rudiment or scale check-off trees; instrument-specific tuning-tendency tooling.
- **Bereavement or memorial records software, in any domain** — §20 of the capability map's hardest human case has no prior art anywhere. `P4`
- A consensus method for match-threshold selection; the leading tool's clerical-review guidance is verbatim "under construction."

**One dead end, recorded so nobody repeats it:** dance notation is useless for drill. Every digital implementation notates one body's limbs, not many bodies' floor positions. `P2`

---

## 10. Honest-limits practice worth copying

§4.2 admires a component that documents what its wall does *not* hide, with a test asserting it. The sweep looked for the best examples anywhere:

- A database whose published limits page is paired with a test file asserting those exact limits. **The best instance found**, and the pattern to copy for every guarantee in §6 and §7. `P4`
- A README section titled "When does it fail," structured as parameter, measured effect, residual. The template for §4.2's statement. `P2`
- A leakage-measurement tool that turns "we padded it" into bits-of-leakage **in CI**. `P2`
- A community that **ships the attacker as maintained infrastructure** rather than as a one-off test — which is how the mutation arm for a privacy guarantee gets built and stays built. `P2`
- Threat model as validated text with CI invariants — the named middle between a written model and a suite. `P2`
- Statistical-recomputation tools that recompute reported figures **from their stated basis in prose** and prove some arithmetically impossible. The missing middle for rule 17. `P2`
- A production system documenting that revoking access **does not retract already-replicated data** — "the contact remains on the user's device," updates "silently fail to sync." §5's forward-only-revocation caveat, observed at national scale, failing *silently*. Belongs in the same register. `P2`
- An accessibility rubric of 50 heuristics phrased as **testable questions** — the only artifact found treating visual accessibility the way this project treats invariants. `P4`

---

## 11. What this sweep could not verify

Listed so that absence reads as `unknown` rather than as a result (rule 13). Each is a real follow-up, not a footnote.

- **Legal authorities, all blocked.** The IRS position on individual fundraising accounts in 501(c)(3) boosters; the USDA overt-identification and community-eligibility material behind the invisible-waiver requirement; current payment self-assessment wording; NCES guidance on minimum cell size — **so the threshold of 10 quoted in part 4 is a tool's default, not a regulatory requirement.** No numeric heat or noise threshold is stated anywhere in this survey for the same reason.
- **Model weight licences** behind the blocked model host, including the ones flagged in part 8.
- **The moved Willow Protocol repository** — existence at its new host unconfirmed.
- `field-acoustics` itself was never read; every claim about how §13's coordinate bridge would fit it derives from prose.
- Whether the leading relationship-authorization engines garbage-collect expired edges: one scout reported it as read, another marked the same assumption unverified. **One source read settles it; until then, do not build §7.1 on either.**
- Two scouts' null results are probably search artifacts rather than absences — multi-word repository queries silently return zero on the API used.
- Standards documents quoted from search text rather than source, itemised per scout report.

---

## 12. Scout index

Twenty-five reports under `docs/survey/`. Machine-produced, `draft`, non-authoritative — cited here so that this survey's `P2` claims have a local source that survives the originals being reclaimed (§15).

**Scout 25 post-dates this survey and is not summarised by it.** Parts 1–11 above were assembled from scouts 01–24; nothing in them accounts for 25. It is indexed here because the index is checked against the tree in both directions and an unindexed file would fail that check — which is the correct outcome, and is why the index says twenty-five while part 13 still says twenty-four.

| # | File | Slice |
|---|---|---|
| 01 | `scout-01-crypto-escrow.md` | Key hierarchy, at-rest sealing, escrow, cryptographic erasure |
| 02 | `scout-02-metadata.md` | Traffic analysis, padding, cadence, measured leakage |
| 03 | `scout-03-relay-localfirst.md` | The drop; local-first sliced replication |
| 04 | `scout-04-authz-guests.md` | Time-boxed relationship grants; the knock |
| 05 | `scout-05-bitemporal.md` | Bitemporal stores; never-delete; the lane model |
| 06 | `scout-06-sandbox-egress.md` | Sandboxing, egress purity, write-path declaration |
| 07 | `scout-07-audio-score.md` | Alignment, diarization, transcription, score anchoring |
| 08 | `scout-08-annotation.md` | Annotation models; structured disagreement |
| 09 | `scout-09-provenance.md` | Provenance ladders, scale direction, citation decay |
| 10 | `scout-10-scheduling.md` | Constraint solving within refusal 6 |
| 11 | `scout-11-ict4d.md` | Humanitarian and public-health field tooling |
| 12 | `scout-12-consent-dignity.md` | Consent machinery, media of minors, dignity design |
| 13 | `scout-13-verify-verifier.md` | Mutation, SQL constraint and trigger mutation, conformance |
| 14 | `scout-14-exit-archives.md` | Exit, retention, disposition, tombstones |
| 15 | `scout-15-practice-mir.md` | Practice, mastery modelling, feedback on playing |
| 16 | `scout-16-library-rights.md` | Cataloguing; rights as first-class data |
| 17 | `scout-17-assets-physical.md` | Asset tracking, uniforms, consumables, field ops |
| 18 | `scout-18-finance-dignity.md` | Ledgers, invisible aid, embezzlement resistance |
| 19 | `scout-19-safety-sensing.md` | Heat and noise sensing; citing a numeric threshold |
| 20 | `scout-20-comms-translation.md` | Notification, acknowledgment, local translation |
| 21 | `scout-21-surfaces-a11y.md` | Surfaces, accessibility, backend parity |
| 22 | `scout-22-drill-spatial.md` | Drill, coordinates, propagation, spatial |
| 23 | `scout-23-identity-interop.md` | Identity resolution, interop, small-cell suppression |
| 24 | `scout-24-wildcard.md` | Deliberately oblique; governance as a checked artifact |
| 25 | `scout-25-protected-categories.md` | Protected-category vocabulary; §18 item 11's rung. **Search summaries only — no source opened** |

`tests/test_section_refs.py` asserts that every file named here exists and that this document's section pointers resolve. A survey index nobody checks is an allowlist that fails open (§16).

---

## 13. The pair this document creates, and its middle

Per rule 12, named in the same commit. This survey is a **summary** of 24 reports that remain beside it — the canonical/vendored shape §16 warns about, with this file as the lossy copy.

> **Twenty-four is right here and twenty-five is right in part 12, and the gap is the point.** `scout-25-protected-categories.md` sits in the directory and is *not* summarised above. Reconciling the two numbers by editing this one would assert a summarisation that was never performed — the drift rule 17 exists to catch, committed to conceal a smaller one. The pair's middle is weaker by exactly one report until someone folds 25 in.

Its middle is partial and should be said so plainly:

- **What is checked:** every scout file named in §12 exists; every `§N` pointer here resolves to a real heading. Both assertions have a test that fails when pointed at a missing file or a dangling reference.
- **What is not checked:** whether this summary faithfully represents the reports. Nothing compares the two, and a wrong rung or a dropped caveat here is invisible.
- **The cheapest real fix** is not a better test: it is that a human reading a row **opens the report behind it before acting**, and seals the row when they do. §14's "Exists" column was assembled the other way, and §18 item 0 exists because of it.

**So the honest instruction for using this file:** treat every row as a lead with a citation, spend the fifteen minutes on the source before it enters a design, and record the verification — because a verified survey and an unverified one look exactly alike.
