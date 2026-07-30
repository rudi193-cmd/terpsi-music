# Scout 23 — Identity resolution, SIS interop, chosen name, family graph, small-cell suppression

**Date:** 2026-07-30 · **Slice:** reconciling one human across many sources; the narrow gated seam to an SIS; not re-identifying minors through aggregates.

**Method note.** WebSearch budget was exhausted, so this was done through GitHub repo/code search plus direct WebFetch of `github.com` and `raw.githubusercontent.com`. `mcp__github__get_file_contents` is scoped to `rudi193-cmd/terpsi-music` only in this session and returned *"Access denied"* for every external repo, so all external file reads went through WebFetch of raw URLs. Every row below is tagged:

- **`[repo]`** — I fetched the repository's own source, schema, docs, config or test files and am reporting what I read.
- **`[repo-list]`** — I read it in a curated list *inside* a repository I fetched, but did not open the project itself.
- **`[inference]`** — I could not fetch it; the claim is reasoning or recollection, not verification. Treat as a lead.

Project rules this slice is answerable to, by CLAUDE.md number: **#3** (never revoke by deleting), **#5** (no group grants over students), **#8** (one lane per student; a shared event is two lane entries with one referent), **#9** (gate the export, narrate the read), **#10** (machine answer is a `draft` until a named human seals it; record rejections as durably as approvals), **#13** (absence surfaces as `unknown`, never as a result), **#14** (scales never compare as bare integers), **#16** (a student's entries are as durable as entries about them), **#19** (a guard that cannot be shown to fail has not been shown to work). Plus `ARCHITECTURE.md` §8's *unsealed suggestion, never a silent merge* and `CAPABILITY-MAP.md` §17's *participation demographics against school demographics*.

---

## Ranked table

| # | Project | What it is | License | Activity (as seen) | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **nomenklatura** (OpenSanctions) `[repo]` | Non-destructive entity resolution: judgement edges + canonical clusters + real unmerge | MIT | active; `resolver.py`, `docs/reference/resolver.md`, tests present | §8 unsealed suggestion; #3; #10; #16 | **adopt** (the resolver, not the sanctions stack) |
| 2 | **ACRO** (AI-SDC / UWE Bristol) `[repo]` | Drop-in analysis commands that auto-apply SDC rules and emit an output-checking record for a human checker | MIT | active; v0.4.12, 2026 demo notebooks | §17 demographics gap analysis; #9; #10; #13 | **adopt** (the rule set + the checker workflow) |
| 3 | **Primero / CPIMS+** (UNICEF) `[repo]` | Child-protection case system; `PotentialMatch` is a **virtual** model — candidates are computed, never persisted | see repo LICENSE (not read) `[inference]` | active (updated 2026-07) | §8; #5; #10; minors specifically | **steal-the-idea** (strongly) |
| 4 | **HL7 Gender Harmony** logical model `[repo]` | Five separated elements incl. **Name to Use** and **Pronouns**, each `0..n` **with validity periods**, and **Recorded Sex or Gender** as a distinct source-attributed thing | HL7 (spec, not code) | IG repo, last touched 2025 | chosen name vs SIS legal record; §20 | **adopt the model** |
| 5 | **GaussSuppression** (Statistics Norway) `[repo]` | Secondary/complementary suppression by Gaussian elimination; `SuppressLinkedTables(linkedGauss="consistent")` | **MIT** | v1.3.0, active 2026 | §17 small cells; #9 | **steal-the-idea** (algorithm is the point) |
| 6 | **CiviCRM** relationship model `[repo]` | `civicrm_relationship`: typed, directional, `start_date`/`end_date`, `is_active`, **`is_permission_a_b` / `is_permission_b_a`** per-edge data-access grant | AGPL-3 `[inference]` | very active | family graph as independently revocable edges; #3; #5 | **steal-the-idea** |
| 7 | **JeMPI** (Jembi) `[repo]` | Master patient index with review-notification queue and **"Unlink and create new Golden Record"** | see repo `[inference]` | 23★, updated 2026-06 | §8; unmerging; review queue | **steal-the-idea** |
| 8 | **Gramps** export proxies `[repo]` | `LivingProxyDb` + `PrivateProxyDb` — chained read-only proxy DBs that progressively restrict an export, with preview; per-record `private` flag | GPL-2 `[inference]` | very active | #9 gate the export; #11 canonical store read-only; printed program | **steal-the-idea** (high value) |
| 9 | **Splink** (UK Ministry of Justice) `[repo]` | Fellegi-Sunter probabilistic linkage; `waterfall_chart` + `comparison_viewer_dashboard` for per-pair explanation | MIT `[inference]` | 2301★, active daily | threshold selection; explaining a match to a human | **steal-the-idea** (see caveat) |
| 10 | **Ed-Fi Data Standard** `[repo]` | `StudentContactAssociation` with `ContactPriority`, `ContactRestrictions`, `LegalGuardian`, `LivesWith`, `EmergencyContactStatus`, `PrimaryContactStatus`; `PreferredFirstName`/`PreferredLastSurname`; repeating typed `otherNames` | Apache-2 `[inference]` | active; DS 5.x/6/7 | SIS interop; family graph vocabulary | **read-only-interest** (vocabulary donor) |
| 11 | **Ed-Fi `edfi-oneroster`** `[repo]` | Serves OneRoster 1.2 from an Ed-Fi ODS. Hardcodes `pronouns`, `agentSourceIds`, `userMasterIdentifier` as NULL | Apache-2 `[inference]` | 5★, updated 2026-07 | the honest ceiling of rostering interop | **read-only-interest** (evidence, not code) |
| 12 | **Gibbon** (GibbonEdu/core) `[repo]` | School platform: `gibbonPerson.preferredName` **and** `officialName` as separate columns; `gibbonFamilyAdult` with `contactPriority`, `contactEmail`, **`childDataAccess`** | **GPL-3** | active | chosen name; family edges with per-adult data access | **steal-the-idea** |
| 13 | **Canvas LMS** `[repo]` | `name` / `short_name` ("Display Name") / `sortable_name` / `pronouns`; two governance switches: `can_add_pronouns` (institution) and `can_change_pronouns` (self-service) | AGPL-3 `[inference]` | very active | chosen name governance — *who may edit it* | **steal-the-idea** |
| 14 | **IPIF / prosopogrAPhI + papilotte** `[repo]` | Factoid model (Bradley/Short 2005): a **Factoid** aggregates a Source + a Person + a Statement, so every assertion is source-attributed | see repos `[inference]` | prosopogrAPhI stale (2023); papilotte stale (2023) | §8; #10; provenance `P1–P5` | **steal-the-idea** (the weirdest good one) |
| 15 | **sdcMicro** (Statistics Austria) `[repo]` | Microdata SDC: k-anonymity, l-diversity, individual + global risk estimation, local suppression | **GPL-2**, v5.8.2 | active (2026-07) | `DERIVED_ANON` re-identification check | **read-only-interest** (methods reference) |
| 16 | **sdcTable / cellKey / ptable / easySdcTable** `[repo]` | Hierarchical tabular SDC; cell-key perturbation | GPL `[inference]` | sdcTable stale (2024); cellKey active | hierarchical tables (program → ensemble → section) | **read-only-interest** |
| 17 | **dedupe** (dedupeio) `[repo-list]` | Active-learning dedup; asks a human to label pairs, then blocks + clusters | MIT `[inference]` | 4488★, active | active-learning review queue | **read-only-interest** |
| 18 | **recordlinkage-annotator** `[repo-list]` | Browser UI purely for manual labelling of record pairs | `[inference]` | 48★, 2025 | review-queue UI prior art | **read-only-interest** |
| 19 | **libpostal** `[repo-list]` | Statistical international address parsing/normalisation | MIT `[inference]` | 4857★, active | address normalisation before comparison | **read-only-interest** (C lib; heavy) |
| 20 | **hlink** (IPUMS, U. Minnesota) `[repo]` | Config-driven probabilistic linkage of **historical US census** records at scale | not stated in README | active | the "same human across decades of messy sources" archetype | **read-only-interest** (absurd overkill) |
| 21 | **RELAIS** (Istat, Italian NSO) `[repo-list]` | National statistical office record-linkage toolkit, R/Java | **EUPL-1.1** | `[inference]` | NSO practice | **read-only-interest** |
| 22 | **fastLink / reclin2 / RecordLinkage (R)** `[repo-list]` | R Fellegi-Sunter implementations; fastLink is the political-science standard | CRAN | `[inference]` | small-n linkage in R | **read-only-interest** |
| 23 | **Zingg** `[repo]` | Spark MDM/identity resolution | AGPL `[inference]` | 1233★ | — | **read-only-interest** (absurd overkill) |
| 24 | **conciliator** `[repo-list]` | OpenRefine reconciliation services for **VIAF**, ORCID, Open Library + a framework to build more | `[inference]` | 127★, 2026-07 | library name-authority reconciliation as a *service* protocol | **steal-the-idea** (the protocol shape) |
| 25 | **anonlink / clkhash** (CSIRO Data61) `[repo]` | Privacy-preserving record linkage via Bloom-filter cryptographic linkage keys | `[inference]` | 75★/47★, active | linking to the SIS *without* sending names | **read-only-interest** (see §Gaps) |
| 26 | **RiC-O** (Int'l Council on Archives) `[repo]` | OWL ontology for archival description, v1.1 (May 2025) | not stated on repo page | active | person/identity/name separation `[inference]` | **read-only-interest** — claim unverified |

---

## Top finds, with the concrete transplant and its cost

### 1. nomenklatura's Resolver — this is the thing to build against

`[repo]` — verified from `docs/reference/resolver.md`, `nomenklatura/resolver/resolver.py`, `nomenklatura/tui/dedupe.py`, `tests/test_resolver.py`.

The docs state the design in one sentence: *"Deduplication in `nomenklatura` is non-destructive: instead of rewriting entity records, every decision — 'these two are the same', 'these are different', 'not sure yet' — is stored as an edge between two entity IDs."* Judgements are `POSITIVE`, `NEGATIVE`, `UNSURE`, and `NO_JUDGEMENT`. Candidate pairs generated by the blocking/xref pass **are stored as `NO_JUDGEMENT` edges until a human decides them** — that is `ARCHITECTURE.md` §8's *unsealed suggestion* already implemented, with a name for the state. Positive judgements are transitive and a cluster gets one **canonical ID**; `Resolver.UNDECIDED = (Judgement.NO_JUDGEMENT, Judgement.UNSURE)`.

Four properties matter more than the matching itself:

1. **`explode(node_id)` — "Dissolve all edges linked to the cluster to which the node belongs."** A real unmerge, and `tests/test_resolver.py` exercises it (`resolver.explode("a1")` then asserts `get_canonical("a17") == "a17"`). There is also `remove(node)` ("Remove all edges linking to the given node") and `prune()` (drop suggestions, collapse aged canonical-to-canonical merges). Requirement #19 is satisfiable here because the reversal path is already a tested code path, not a migration script.
2. **`NEGATIVE` is durable and load-bearing.** "These two are not the same" is stored as a blocking edge and consulted by `get_judgement()` before re-comparison. For two siblings both named Smith in the same program, a director's one-time "these are different children" becomes a permanent fact that no later re-run can undo. This is the single most valuable property for this domain and it is exactly CLAUDE.md #10's *record rejections as durably as approvals*.
3. **Every decision records `getpass.getuser()` and an ISO timestamp** alongside the judgement and an optional confidence score. That is the sealer's provenance §8 asks for, already in the row.
4. **Source data stays untouched**, which is CLAUDE.md #11 (canonical store read-only to the app; agents write sidecars) with no adaptation needed — the resolver *is* a sidecar.

**Transplant.** Take the resolver's *shape*, not the package. A `person_judgement` table: `(left_person_id, right_person_id, judgement ∈ {positive, negative, unsure, no_judgement}, decided_by, decided_at, confidence)`, plus a derived canonical-cluster view. Candidate generation (any blocking function you like) writes `no_judgement` rows. `Person` resolution reads the cluster view. `explode(person_id)` is your unmerge. This is perhaps 300 lines and one migration.

**Cost and cautions.** (a) Nomenklatura's storage is SQLAlchemy over SQLite/Postgres — fine, but it's a whole dependency to drag in for one table; prefer reimplementing the resolver shape. (b) Its canonical ID is `get_canonical()` = "maximum identifier from the connected cluster" via synthetic `Identifier.make()` IDs; you almost certainly want the canonical `Person` to be a real, human-nominated lane rather than a max() over synthetic IDs, because CLAUDE.md #8 makes the lane the unit of storage and audit. Picking the canonical lane is a human act. (c) `prune()` deletes suggestion edges — under CLAUDE.md #16 you may want tombstoning instead of deletion even for rejected suggestions, since a suggestion that was raised and declined is itself a record of the system's exercise of authority. (d) Nomenklatura is built for company/sanctions entities on the Follow-the-Money schema; ignore all of that.

### 2. ACRO — the aggregate-export gate, with numbers

`[repo]` — verified from `README.md`, `pyproject.toml` (**MIT**, Python ≥3.10), `acro/default.yaml`, `acro/acro.py`, `docs/source/user_guide/configuration.rst`, and the 2026 demo notebook/Stata log.

ACRO wraps ordinary analysis calls (crosstabs, regressions, survival) so that producing a table *simultaneously* runs the disclosure tests and records the result for a human output-checker. The README's framing is the useful one: *"SDC done with researchers rather than to them"*, and ACRO "assists rather than replaces human reviewers." SACRO-Viewer is the checker's UI, showing "identified issues, potential mitigation options, and tracking decisions made." That is CLAUDE.md #10 applied to statistics: the table is a `draft` carrying its own flags, and a named human seals it.

**The verified default rule set** (`acro/default.yaml`, echoed in the runtime log as `INFO:acro:config`):

| Key | Default | What it means for a music program |
|---|---|---|
| `safe_threshold` | **10** | No cell with fewer than 10 students. A section of eight *never* produces a cell. |
| `safe_dof_threshold` | 10 | Degrees-of-freedom floor for analytical stats (regressions). |
| `safe_nk_n` / `safe_nk_k` | **2 / 0.90** | Dominance: if the largest 2 contributors account for ≥90% of a total, it's disclosive. |
| `safe_pratio_p` | 0.10 | p-ratio rule for magnitude tables (fees, hours). |
| `safe_round_base` | 5 | Rounding base when rounding is the mitigation. |
| `zeros_are_disclosive` | **True** | A zero cell is a disclosure, not an absence. |
| `survival_safe_threshold` | 10 | Applies to survival/retention curves. |
| `check_missing_values` | False | Off by default. |
| `blocked_extensions` | **`[".svg", ".gph"]`** | Vector/graph formats are blocked outright. |

Two of those are worth stopping on. **`zeros_are_disclosive: True`** is the single most important line in this report for `CAPABILITY-MAP.md` §17. The demographics gap analysis is *designed to surface zeros* — "no students from this group are in the program" is the finding. ACRO's default says that finding is itself a disclosure. In a program of a few hundred, "zero students of group X in the drumline" plus a school roster is frequently a named child, or a named absence. This is also where CLAUDE.md #13 bites: a suppressed zero must render as `unknown`/`suppressed`, and specifically **not** as `0`, because `0` reads as a result. **`blocked_extensions: [".svg", ".gph"]`** is the non-obvious gate: an SVG chart of a suppressed table embeds the underlying data points as path coordinates, and a Stata `.gph` embeds the dataset. Any "export the equity dashboard as a graphic" feature is an egress hole unless it rasterises. That is CLAUDE.md #9 in one config line, and it is the kind of thing you only learn from people who check outputs for a living.

**Transplant.** Do not adopt ACRO as a dependency (it's pandas/statsmodels-shaped and expects a research workflow). Adopt (i) the rule *names and defaults* as your aggregate policy, declared in one place; (ii) the pattern that the aggregate-producing function returns `(table, disclosure_findings)` and the table cannot be exported while findings are unresolved; (iii) the blocked-extension list; (iv) a checker record per export, naming the human. **Cost:** you must write the rules yourself (threshold, dominance, zeros) — a day or two, and each rule needs a mutation test per #19: build a table with a cell of 9 and assert refusal.

### 3. Primero — the match candidate that is never a row

`[repo]` — verified from `app/models/potential_match.rb`, `app/services/matching_service.rb`, `spec/requests/api/v2/potential_matches_controller_spec.rb`, `app/views/api/v2/potential_matches/_potential_match.json.jbuilder`.

Primero is UNICEF's child-protection information system (CPIMS+/GBVIMS+) — minors' records, in the highest-stakes setting there is. Its family-tracing feature matches unaccompanied children against caregivers' tracing requests. The design decision to steal is stark:

**`class PotentialMatch < ValueObject`** — the file's own comment says *"This virtual model encapsulates a potential link between a trace on a TracingRequest and a case (Child). It contains logic for comparing the two records and pass judgement on how likely it is that they represent the same person."* It is **not persisted**. There is no potential-matches table. A candidate is *computed on read* from a Solr fuzzy query and rendered; if nobody acts on it, nothing was ever written. There is consequently nothing to un-merge, because merging was never a database operation — a human worker acts on a suggestion by editing the actual records.

Three more specifics:

- **`MATCH_FIELDS` boosts nickname-equivalence highest:** `{ fields: %w[name name_other name_nickname], boost: 15.0 }`, then `sex` and `age` at 10.0, relation-name variants at 10.0, DOB and relation fields at 5.0, nationality/language/religion at 3.0, ethnicity at 1.0. The *Robert / Bobby / R. Smith* problem is solved by carrying `name_other` and `name_nickname` **as stored fields on the person** and matching across all three — not by cleverer string distance. That is the cheapest and best idea in this whole report.
- **Thresholds:** `NORMALIZED_THRESHOLD = 0.1` (below this, don't even show it) and `LIKELIHOOD_THRESHOLD = 0.7`. Scores are normalised by dividing by the max score in the result set. The likelihood band is `LIKELY` if there is only one result, or if `(score - average_score) > 0.7`, else `POSSIBLE`.
- **The candidate view is itself a permission surface:** the JSON builder gates fields individually — `if current_user.can?(:view_photo, PotentialMatch)`, and likewise `:view_audio`. Seeing that a candidate *exists* is a different permission from seeing the child's photo inside it.

**Transplant.** (i) Make the suggestion a computed view, not a table — then CLAUDE.md #3 and the "wrong merge combines two children's records" fear both evaporate for the *suggestion* layer, and only the human's decision needs durability (which nomenklatura's judgement table gives you). (ii) Store `name_other` and `name_nickname` on `Person` from day one and match across them. (iii) Permission-gate the *fields inside* a match candidate, not just access to the queue.

**Cost and a caution.** Primero's `likelihood` is **relative to the candidate set** (`score - mean(scores) > 0.7`), so the same pair can be `LIKELY` in a thin result set and `POSSIBLE` in a rich one — non-monotonic and not reproducible across runs. Do not copy that. And note the collision with CLAUDE.md #14: `score: 0.4136639493462357` is exposed raw in the API and rendered in a column literally labelled `potential_match.score`. Under #14 a confidence must not be shown as a bare number pretending to be a scale — and `ARCHITECTURE.md` §15 explicitly says *"Confidence is not a rung."* Render bands (`likely` / `possible`) with an explicit prefix and keep the float internal. Primero's own field label conflates the two (`{ label: i18n.t("potential_match.score"), name: "likelihood" }` — the score label bound to the likelihood field). That's the bug #14 exists to prevent, visible in production code.

### 4. HL7 Gender Harmony — the chosen-name model, already specified

`[repo]` — verified from `input/pagecontent/model.md` in `HL7/fhir-gender-harmony`.

See the dedicated section below; the headline is that the model gives you **Name to Use** and **Pronouns** as `0..n` elements *each carrying a validity period*, and separates them from **Recorded Sex or Gender**, which is explicitly the "what some document/system says" bucket carrying `issuer jurisdiction` and `source field` metadata.

### 5. GaussSuppression — suppressing one cell is not enough

`[repo]` — verified from `DESCRIPTION` (**MIT + file LICENSE**, v1.3.0, Statistics Norway, Langsrud/Lupp), `R/AdditionalSuppression.R`, `R/SuppressLinkedTables.R`, `vignettes/Small_count_frequency_table_suppression.Rmd`, `NEWS.md`.

Primary suppression (`SuppressSmallCounts(maxN = ...)`, `SuppressDominantCells()`) hides the small cell. **Secondary/complementary suppression is the actual problem**, and it is what this package exists for: if you suppress "trumpets, group X = 3" but publish the row total and the column total, arithmetic recovers the 3. Gaussian elimination over the table's linear structure finds the additional cells that must also be suppressed.

The transplantable ideas, in descending order of value to this project:

1. **`SuppressLinkedTables(..., linkedGauss = "consistent")`** — a cell suppressed in one table must be suppressed in every linked table it appears in. The `man/` example is explicit: *"'A' 'annet'/'arbeid' suppressed in b[[1]], since suppressed in b[[3]]."* For `CAPABILITY-MAP.md` §17 this is the whole ballgame: a district view publishing *participation by school*, *participation by ensemble*, and *participation by grade* over the same students lets a reader difference the three views to recover the suppressed cells. Suppression must be computed **once over the union of everything you will ever publish**, not per-report. This is a schema/architecture decision, not a reporting one — and it is exactly the kind of thing CLAUDE.md #12 wants a named middle for: the "aggregate publication set" is the pair, and the consistent-suppression pass is its reconciler.
2. **`protectZeros`** is a first-class parameter — the library treats "is a zero disclosive?" as a decision you must make explicitly, matching ACRO's `zeros_are_disclosive: True`. Two independent statistical offices' tooling agrees this must be a conscious choice; CLAUDE.md #13 decides it for you.
3. **Singleton handling** — `NEWS.md` references a singleton method with an `elimination` variant (`?SSBtools::NumSingleton`). A table where a suppressed cell has exactly one contributor is a special disclosure case, because the contributor knows their own value and can subtract it. In a program where every guardian can see their own child's row, **every guardian is a singleton attacker**. This is the re-identification threat model for `DERIVED_ANON` and it is not the generic one.
4. **`maxN` can be named/variable-specific** (v1.3.0) — different thresholds per dimension. A threshold of 10 on ensemble-level cells and something stricter on section-level cells is expressible.

**Cost.** It's R, and the project is not an R project. This is **steal-the-idea, not adopt**: implement primary suppression + a consistency pass over your declared publication set, in whatever language the hub runs. Do not implement Gaussian-elimination secondary suppression yourself unless you must — for a few hundred students the cheaper and safer answer is to *not publish the cross-tabs at all* and publish only pre-agreed, pre-suppressed aggregates (see the small-cell section).

### 6. CiviCRM — the family graph as revocable directional edges

`[repo]` — verified from `schema/Contact/Relationship.entityType.php`, `CRM/Contact/BAO/Relationship.php`, `CRM/Contact/BAO/Query.php`, `CRM/Contact/Form/Search/Criteria.php`, and the v3/v4 API tests.

`civicrm_relationship` carries, per edge: `relationship_type_id`, `contact_id_a`, `contact_id_b`, `start_date`, `end_date`, `is_active`, `description`, and — the reason to care — **`is_permission_a_b`** and **`is_permission_b_a`**, two independent directional permission flags whose values are named things like `'View only'` (per `tests/phpunit/api/v4/Entity/RelationshipTest.php`). `CRM/Contact/BAO/Query.php` enforces them in SQL (`civicrm_relationship.is_permission_a_b IN (...)`), and `QueryTest.php` asserts the generated SQL contains that clause — so it is **enforcement, not a ledger** (CLAUDE.md #18). The search UI exposes `start_date`/`end_date` as an "Active Period" so you can ask "who could see this child's record in March."

This is `CAPABILITY-MAP.md` §20's family-situations list modelled correctly and CLAUDE.md #5 satisfied structurally: there is no household account, only named-person-to-named-person edges. Split households are two edges from one child. A court order restricting contact is `is_permission_a_b = 0` plus `end_date` — **and note that ending an edge sets `end_date`/`is_active`, it does not delete the row**, which is CLAUDE.md #3 (`invalid_at`) with a different field name. Foster placement changes mid-year are a new edge and an `end_date` on the old one, with both still on the record.

**Transplant.** `GuardianEdge(child_person_id, adult_person_id, relation_type, valid_from, invalid_at, notification_ok, data_access ∈ {none, view, view_update}, reason, decided_by)`. One row per adult per child. A sibling pair with the same two parents is four edges, not one household — which is also what CLAUDE.md #8's sealed sibling lanes require. **Cost:** near zero to design, real to *enforce* — every read path must join the edge and check the period and the grant, and per #19 each needs a test that attempts access through an expired or revoked edge and asserts refusal. CiviCRM's own AGPL-3 `[inference]` licence and PHP make it a design donor only.

**One gap in CiviCRM's model for this domain:** there is no notion of *which notification* an edge permits. `CAPABILITY-MAP.md` §20 asks "which guardian receives which notification" — a per-edge boolean is too coarse when one guardian may receive schedule changes but not fee balances. Gibbon is slightly ahead here with separate `contactEmail` and `childDataAccess` flags per family-adult; you likely want a small set of named notification classes per edge. That is a genuine "what does not exist elsewhere" finding.

### 7. Gramps — the export is a stack of proxy databases

`[repo]` — verified from `gramps/gui/plug/export/_exportoptions.py`.

Genealogy software has fought the "living people in a published family tree" battle for thirty years, and Gramps' answer is architecturally better than a redaction pass. Exports run through **chained proxy databases** — `LivingProxyDb` and `PrivateProxyDb` — each a read-only restricting view, stackable with person and note filters, with a **preview** of the resulting dataset before the export commits. Records carry a `private` flag, and *"Do not include records marked private"* drops them.

The living-people options are, verbatim: **"Include all selected people"**, **"Replace given names of living people"**, **"Replace complete name of living people"**, **"Do not include living people"**.

Two transplants. First, **the export path should be a composition of restricting proxies over the canonical store, not a filter over query results** — which is CLAUDE.md #11 (canonical store read-only; agents see sidecars) and #9 (exports are a distinct permission class) implemented as a type, so it is hard to bypass by accident. The preview is the "announced" half of #9: the director sees exactly what will leave before it leaves. Second, **`private` as a flag on an individual record — including on a `Name` record** — means a legal name can exist in the database and be structurally excluded from any export or printed report. That is the concert-programme problem (see below).

**Cost.** GPL-2 `[inference]` and Python/GTK; take the pattern. The real cost is that a proxy-DB layer only works if *every* export goes through it, and proving that is an egress-purity test, not a code review.

### 8. Splink — good for explaining a match, thin on the human part

`[repo]` — verified from `splink/internals/linker_components/visualisations.py`, `docs/topic_guides/evaluation/{edge_metrics,edge_overview,labelling}.md`, `docs/charts/index.md`, `mkdocs.yml`, and the DuckDB/Postgres full-example tests.

Splink is the UK Ministry of Justice's probabilistic linkage library — a genuine national-government record-linkage tool, 2301★, committed to daily. Two features are directly relevant even though the library itself is overkill:

- **`waterfall_chart`** decomposes a single pair's match weight into per-comparison contributions — *why* this pair scored what it scored, field by field. That is the review-queue UI this project needs: a director deciding whether Bobby is Robert should see "surname exact: strong evidence for; date of birth differs: strong evidence against", not `0.87`. It also directly serves `ARCHITECTURE.md` §15 — the chart shows evidence, not a rung.
- **`comparison_viewer_dashboard`** produces an interactive dashboard with "example predictions from across the spectrum of match scores" — i.e. how you *calibrate* a threshold by looking at what lives at each score band.

**Two honest caveats.** `docs/topic_guides/evaluation/labelling.md` is, verbatim, *"This page is under construction - check back soon!"* — the leading government record-linkage library has **no published clerical-review guidance**. And `edge_metrics.md` gives no threshold-selection advice; it argues only that *"A model cannot be meaningfully summarised by just one of these performance measures"* and points at F-score, P₄ and Matthews correlation coefficient, noting F-score is asymmetric because it "considers the prediction of matching records, but ignores how well the model correctly predicts non-matching records." **There is no open-source consensus method for picking a match threshold.** That is a real finding, not a gap in my search: the practice is "look at pairs at each score band and decide," which is why the viewer dashboards exist. For this project the implication is freeing — you are not failing to find a principled threshold, there isn't one, so set it high, route everything else to a human, and spend your effort on the review UI and the unmerge path instead of on tuning.

**Scale verdict.** Splink is built for millions of rows across DuckDB/Spark/Athena/Postgres. For a few hundred students it is **absurd overkill**; the transplantable parts are the waterfall decomposition and the calibration-by-band habit.

### 9. Ed-Fi and OneRoster — what the SIS seam can honestly be

`[repo]` — verified from `Ed-Fi-Data-Standard/Models/StudentIdentificationAndDemographics.mmd`, `Descriptors/OtherNameTypeDescriptor.xml`, `Samples/Sample XML/Student.xml`, `certification-testing/bruno/SIS/v5/{Student,Contact}/**`, `Ed-Fi-Extensions` TPDM SQL, and `edfi-oneroster/standard/{4.0.0,5.2.0}/artifacts/{mssql,pgsql}/core/users.sql`.

**What exists in the standards.** Ed-Fi's `StudentContactAssociation` (renamed from `StudentParentAssociation` in DS 5.x) carries `Relation`, `PrimaryContactStatus`, `LivesWith`, `EmergencyContactStatus`, `ContactPriority`, `ContactRestrictions`, `LegalGuardian`. `Student`/`Contact`/`Staff` all carry `PreferredFirstName` and `PreferredLastSurname` (DS 5.x+; the TPDM extension SQL documents them as *"The first name the individual prefers, if different from their legal first name"*), plus `PersonalTitlePrefix`, plus a repeating `otherNames[]` collection typed by an `OtherNameTypeDescriptor` (values include `Nickname`, `Other Name`). `Contact` additionally has `Sex` and `GenderIdentity`. `Person` has a `SourceSystem` descriptor — *"the originating record source system for the person"* — which is the provenance hook you want.

**What that gives you.** A vocabulary donor, and validation that the *repeating typed name* shape (one canonical name + N typed alternates) is standard practice in education data, matching Gramps' `primary_name` + `alternate_names[NameType]` and Primero's `name` + `name_other` + `name_nickname`. Three unrelated domains converged on it. Use it.

**Two weaknesses worth naming.** (a) `ContactRestrictions` is typed **`string`** in the model file — a free-text field where the safety-critical fact lives. `CAPABILITY-MAP.md` §20 calls court-ordered contact restriction *"a safety issue where a bug is a serious harm"*; a free-text string is unenforceable by construction, and this is precisely CLAUDE.md #18's distinction — Ed-Fi's `ContactRestrictions` is a **ledger**, not a gate. Your version must be structured and predicate-checkable. (b) The Ed-Fi model has no pronouns field at all.

**The honest ceiling of rostering interop, in one file.** `edfi-oneroster` is the Ed-Fi Alliance's own OneRoster 1.2 bridge. Its `users` view hardcodes as NULL: **`pronouns`**, **`agentSourceIds`** (the parent/guardian relationship links), `userMasterIdentifier`, `preferredMiddleName`, `sms`, `phone`, `userProfiles`, `password`. The DS 4.0.0 variant additionally comments `-- DS4 doesn't have PreferredFirstName column`, so preferred names are NULL there too.

Read that carefully: **OneRoster 1.2 has a `pronouns` field and a guardian-link field in its user resource, and the reference implementation from the standards body on the other side cannot fill either one.** So:

- **Chosen name and pronouns cannot be imported from the SIS in practice.** They must be first-class, locally-owned data in terpsi-music. This settles the schema question by removing the alternative — and it is a *good* outcome, because §20 wants them handled deliberately and distinctly from the SIS legal record anyway. It also means the SIS can never overwrite them on the next sync, which is the failure mode that outs children.
- **The guardian graph cannot be imported either.** `agentSourceIds` NULL means the family graph is yours to build and own, which is what CLAUDE.md #5 and #3 require anyway (a group grant or an undated deletion arriving from a vendor sync would violate both).
- **What the seam can realistically be:** a one-way, gated, *pull* import of the narrow set that genuinely lives in the SIS — enrolment, grades and attendance for the §13 eligibility check, and legal name as a `Recorded Sex or Gender`-style source-attributed record. **OneRoster CSV** (a zip of flat files) is the realistic transport, not the REST API: no OAuth dance, no vendor onboarding, no live coupling, and it fits `ARCHITECTURE.md` §9's "deferred deliberately: any live integration with an external platform." Ed-Fi ODS/API, SIF and the OneRoster REST API are all vendor-integration projects; `CAPABILITY-MAP.md` §13 needs grades and attendance, which a nightly CSV drop satisfies completely.
- **Gradebook sync one-way is not just a policy choice, it is the only thing the ecosystem supports well.** Writing grades back would require Ed-Fi ODS/API write credentials or LTI Assignment & Grade Services `[inference]`, both of which convert this into a networked, credentialed system.

**Cost.** Parsing OneRoster CSV: small. The real cost is the gate around it — an import is an egress event in reverse and needs its own permission class, classification of every incoming field onto the L-ladder, and a rule that the importer may never write to chosen-name or guardian-edge tables. That last one should be enforced by the schema (separate write paths), not by reviewer discipline.

### 10. IPIF / the factoid model — the weird one that reframes the problem

`[repo]` — verified from `IPIF/prosopogrAPhI/README.md` and `gvasold/papilotte/src/papilotte/openapi/ipif.yml`.

Historians reconciling people across medieval charters hit this problem a thousand years before schools did, and their answer inverts it. In the **factoid model** (Bradley/Short 2005), a **Factoid** is a first-class record that *aggregates a Source, a Person, and a Statement* — the openapi spec's `depth=reduced` parameter returns "only `@id` for the source, the person, and the statement aggregated by the factoid." You never store "this person was a trumpeter." You store "*this source* asserts that *this person* was a trumpeter." Identity across sources is itself just another assertion, made by a named scholar, citable and retractable.

**Why this matters here.** `ARCHITECTURE.md` §8 wants "a confident match returns the canonical record with the sealer's provenance." The factoid model says: make the *assertion* the row, and the canonical record a projection over assertions. Then "the SIS says Robert Smith", "the booster spreadsheet says Bobby Smith", and "Director Nakamura sealed these as one child on 2026-03-04" are three rows of the same kind, none of which destroyed the others. Retracting the seal is deleting one assertion, not un-baking a merge. This composes perfectly with `ARCHITECTURE.md` §8.1's already-chosen `story-timeline` provenance record and its `contradicts_or_tensions_with` relation — two sources disagreeing about a student's name is that relation exactly, and it makes the disagreement queryable rather than resolved-by-last-write. It also gives §15's `P1–P5` provenance ladder a natural place to live: on the factoid, not on the person.

**Verdict: steal-the-idea.** Both implementations are stale (prosopogrAPhI last touched 2023, papilotte 2023), the API is a draft, and the digital-humanities tooling around it is not something to depend on. The *shape* is free and it is the right shape.

---

## Small-cell suppression for aggregates about minors

`CAPABILITY-MAP.md` §17 asks for **"participation demographics against school demographics — the gap analysis that reveals who is not in the program"**, plus free/reduced-lunch participation rates in fee-based activities. `ARCHITECTURE.md` classifies a `DERIVED_ANON` class expected to survive a re-identification check. This is the most dangerous feature in the capability map and the one most likely to be built casually.

**The core arithmetic problem.** An aggregate over a section of eight students is not anonymous, and the reason is not cell size alone — it is that the attacker has the denominator. School demographics are public (state report cards). Program rosters are semi-public (concert programmes, competition results, social media). Every guardian knows their own child's row. So the adversary holds: the population, a partial roster, and one exact record. Under those conditions:

1. **A zero is a disclosure.** Both ACRO (`zeros_are_disclosive: True`) `[repo]` and GaussSuppression (`protectZeros` as an explicit parameter) `[repo]` treat this as a decision that must be made consciously. "Zero students receiving free/reduced lunch are in wind ensemble" identifies a group by exclusion, and combined with a public roster may identify individuals. CLAUDE.md #13 forces the rendering: suppressed must surface as `unknown`/`suppressed`, **never as `0`** — because a rendered `0` is read as a finding, and here it is both a finding and a leak.
2. **Complementary suppression is mandatory, not optional.** Hiding one cell while publishing its row and column totals is not suppression. `[repo]` GaussSuppression exists entirely for this.
3. **Differencing across reports is the likely real-world breach.** `SuppressLinkedTables(linkedGauss = "consistent")` `[repo]` — a cell suppressed in one table must be suppressed in *every* linked table. A district dashboard that publishes participation by school, by ensemble, and by grade over the same students is three views of one table; the reader subtracts. **Suppression must be computed once over the union of the declared publication set.** Under CLAUDE.md #12 this is a pair needing a named middle: the publication set and the suppression pass, created in the same commit.
4. **Every guardian is a singleton attacker.** GaussSuppression's singleton handling `[repo]` addresses the case where a suppressed cell has one contributor who knows their own value and subtracts it. In this domain that is not an edge case — it is the default reader. A guardian viewing an equity dashboard already holds one exact row of it.
5. **Vector graphics leak the table.** `blocked_extensions: [".svg", ".gph"]` `[repo]`. An SVG chart of a suppressed table carries the data as path coordinates. `CAPABILITY-MAP.md` §17 wants "advocacy dashboards built for board presentations" — the export button on that dashboard must rasterise or be gated.

**Concrete recommendation, given hundreds of records not millions.**

- **Do not build a general cross-tab engine.** With a few hundred students and any two demographic dimensions, almost every cell falls below any defensible threshold, so a general engine will spend its life returning `suppressed` — and the one time it returns a number, that number is the disclosure. Publish a small, fixed, pre-agreed set of aggregates, each individually reasoned about, each with its suppression computed over the whole set.
- **Adopt `safe_threshold: 10` as the floor and treat it as a floor, not a target.** ACRO's verified default is 10 `[repo]`; a section of eight can therefore never yield a cell, which is the correct outcome. Do not let a config knob lower it per-report — one threshold, one place, declared.
- **Prefer comparing to the school population without publishing the program cell.** "Program participation differs from school population on dimension X by more than Y" can be a `true/false/unknown` finding routed to a human, with no cell published at all. That answers §17's actual question — *who is not in the program* — without a table. It also fits the §18 "anonymous need identification, so a student never has to ask publicly" posture.
- **`DERIVED_ANON` must be a *verified* class, not a declared one.** CLAUDE.md #18: a class name is a ledger; a re-identification test is enforcement. Per #19, the test is a mutation: construct a table that passes the threshold rule, then attempt re-identification using (public school demographics + a partial roster + one known student's row) and assert the attempt fails. If that test does not exist, `DERIVED_ANON` is an aspiration. `sdcMicro` `[repo]` (GPL-2, v5.8.2, Statistics Austria) is the reference for the *measures* — individual and global re-identification risk, k-anonymity, l-diversity — even though the package itself is R and not adoptable here.
- **Scale note per the brief:** sdcTable, cellKey, tau-ARGUS and the full Gaussian-elimination machinery are built for national census tables. For this project they are **overkill** — but the four ideas above (zeros, complementary, cross-report consistency, singleton contributors) are not overkill, they are the minimum, and they are exactly what a naive implementation omits.

---

## Chosen name vs legal name as a schema problem

This has real harm attached: a system that prints a legal name on a concert programme, or that lets a nightly SIS sync silently overwrite a chosen name, outs a child to an audience or to a family. `CAPABILITY-MAP.md` §20 lists it under "family situations requiring care" and specifically names *"what appears on a printed concert program."*

**The best specified model available: HL7 Gender Harmony** `[repo]` (verified from `input/pagecontent/model.md`). Five independent elements; three matter here.

| Element | Cardinality | Validity period | Purpose (per the spec) |
|---|---|---|---|
| **Name to Use (NtU)** | `0..n` | **yes** | "the preferred name for patient communication and care"; periods let name changes be tracked over time |
| **Pronouns** | `0..n` | **yes** | patient-preferred pronouns; multiple simultaneously supported, context-dependent |
| **Recorded Sex or Gender (RSG)** | `0..n` | yes | sex/gender "from existing documents or systems **without implying it represents current identity**"; attributes include source value, type, record description, acquisition date, **issuer jurisdiction**, and source field metadata |
| Gender Identity | `0..n` | yes (may overlap) | self-reported only |
| Sex Parameter for Clinical Use | `0..n` | yes | clinical reference ranges — **not applicable here** |

The spec is explicit that these do not collapse: *"administrative gender, administrative sex, and sex assigned at birth are exchanged today, and when exchanged in this way the data should not be considered a representation of Gender Identity (GI) or Sex Parameter for Clinical Use (SPCU)."* And per the model page, "NtU and Pronouns operate independently from RSG, ensuring that legal documentation doesn't dictate preferred communication practices."

**The four design decisions this yields, translated to terpsi-music:**

1. **Name to Use and Pronouns are `0..n` with validity periods, locally owned, never derived from the SIS.** Cardinality `0..n` + dates is not over-engineering: it means a name change is an *added* record with a period, so CLAUDE.md #3 holds (you never delete the prior name, you bound it) and CLAUDE.md #16 holds (the student's own entries about themselves are as durable as the institution's). It also means "what was this student called in the spring concert programme" is answerable two years later without having kept the legal name in the render path.
2. **The legal name is an `RSG`-shaped record, not a field on Person.** Model it as `SourceAttributedName { value, source_system, source_field, acquired_at, issuer, valid_period }` — Ed-Fi already supplies the `Person.SourceSystem` descriptor for exactly this `[repo]`. This has a direct architectural payoff: because the legal name is a *source-attributed record* rather than the canonical name, it is naturally classified, naturally excludable from exports, and naturally not the default render. It is also the correct shape under the factoid model above.
3. **The render path must default to Name to Use, and the exceptions must be enumerated in code.** Legal name is needed for: the SIS eligibility match, travel documentation (§20 lists undocumented families and the ID requirements of travel), and possibly medical/insurance forms. Everything else — roster, attendance, chair assignment, practice queue, adjudication commentary addressing, **and the printed concert programme** — uses Name to Use. Make the legal-name accessor a distinct, audited call, not a property read. **Gramps supplies the pattern** `[repo]`: a `private` flag on the individual `Name` record plus a `PrivateProxyDb` in the export chain, so the legal name can exist in the store and be structurally absent from any generated document. Its living-people option *"Replace complete name of living people"* is the same machinery pointed at the same fear.
4. **Decide, explicitly and in writing, who may edit a student's chosen name.** This is the hardest question and it is a governance question, not a schema one — but **Canvas LMS shows the schema shape for it** `[repo]`: two separate switches, `can_add_pronouns` (does this institution enable the feature at all) and `can_change_pronouns` (may the *user* change their own), from `app/views/accounts/settings.html.erb`, with pronouns drawn from an admin-curated list (`PronounsInput`, `available_pronouns_list`) rather than free text. Canvas also carries a three-name model — `name`, `short_name` (labelled **"Display Name"** in `app/views/users/_name.html.erb`), `sortable_name` — and its SIS CSV importer can set `short_name` (`spec/lib/sis/csv/user_importer_spec.rb` asserts `user.short_name == "The Dos"`). That last detail is a **warning**, not a model: if the SIS import path can write the display name, the SIS can overwrite a chosen name on any sync. In terpsi-music the importer must be structurally barred from that table.

This is where the §7.1/§13 consent question lands with real stakes. `ARCHITECTURE.md` §13 asks "whose consent is it?" — for chosen name the answer cannot be "the guardian's, by default," because the case that makes this feature matter is the student whose guardian does not know or does not agree, and CLAUDE.md's refusal #7 (never put a record on SMS) exists for adjacent reasons. `CAPABILITY-MAP.md` §20 also lists *estranged or no-contact parents* and *court orders restricting contact* in the same block. A guardian-visible surface that renders chosen name is a disclosure channel to the family. **Concretely: chosen name needs a visibility scope per audience** — at minimum `{staff, peers/roster, printed programme, guardian-facing surfaces, SIS export}` — each independently settable, defaulting to the narrowest, and each a distinct permission per CLAUDE.md #9. That is more than any system I found implements. Gibbon splits `preferredName` from `officialName` as plain columns `[repo]` and Canvas has one global `short_name`; neither models per-audience visibility. **This is genuine new work, and it is the highest-harm gap in this slice.**

**Also verified, and worth stating plainly: the standards will not help you here.** OneRoster 1.2 has a `pronouns` field; the Ed-Fi Alliance's own OneRoster bridge hardcodes it to NULL, and Ed-Fi has no pronouns column at all `[repo]`. There is no interop path for chosen name and pronouns. That is a feature, not a bug — it means the data is yours, local, and cannot be clobbered by a vendor sync.

---

## Gaps — what I could not verify

**Blocked by the egress proxy / no WebSearch:**

- **`studentprivacy.ed.gov` returned HTTP 403.** I could not read **NCES SLDS Technical Brief 3, "Statistical Methods for Protecting Personally Identifiable Information in Aggregate Reporting"**, which is the authoritative US education guidance on minimum n-size, complementary suppression, blurring and top/bottom coding. Per CLAUDE.md #17 I am quoting **no numbers** from it. The `safe_threshold: 10` figure above is ACRO's verified default `[repo]`, **not** an ED/NCES requirement, and I did not verify the commonly-cited ESSA state-plan n-size range. **Someone must read that document before this feature is designed.** Likewise unread: the ED Privacy Technical Assistance Center (PTAC) checklists.
- **Trans-inclusive database-design writing** (e.g. the well-known *A List Apart* / practitioner essays on gender and name fields, and the "Designing forms for gender diversity" genre) — WebSearch unavailable and these are not GitHub-hosted. The chosen-name section above is built from *implementations* (HL7, Canvas, Gibbon, Gramps) and from the project's own §20, not from that literature. This is a real gap in the "published guidance" half of that target.
- **The OneRoster 1.2 specification itself** (1EdTech) and the **SIF** specification — not fetched. My OneRoster field list is inferred from the field names in Ed-Fi's `users.sql` view `[repo]`, which is strong evidence of the target schema but is not the spec. The claim "OneRoster 1.2 has a `pronouns` field" rests on that alias.
- **CEDS** (Common Education Data Standards) — not reached at all. Likely the best US vocabulary for guardian-relationship and restricted-contact enumerations; worth a look.

**Not verified for licence (do not rely on these):** Primero (README says "carefully read our LICENSE"; I did not read it, and it is reportedly not a standard OSI licence — **check before any code reuse**), CiviCRM (believed AGPL-3), Canvas LMS (believed AGPL-3), Gramps (believed GPL-2), Splink (believed MIT), Ed-Fi repos (believed Apache-2), JeMPI, hlink (README does not state one), dedupe, libpostal, sdcTable, cellKey, RELAIS (`[repo-list]` says EUPL-1.1 but I did not confirm at source). Verified at source: **nomenklatura MIT**, **ACRO MIT**, **GaussSuppression MIT**, **sdcMicro GPL-2**, **Gibbon GPL-3**.

**Searched and found nothing usable:**

- **Voter-roll deduplication** — repeated GitHub searches returned zero results. ERIC (the US Electronic Registration Information Center), which is the real practice here, is not open source `[inference]`. No transplantable code found.
- **Vital-records / death-index matching** — zero results. CDC's National Death Index and NCHS linkage methodology are not open-source implementations `[inference]`. Not reached.
- **Humanitarian beneficiary registration/dedup beyond Primero** — searches for beneficiary/biometric dedup returned nothing. UNHCR PRIMES, WFP Building Blocks, Red Rose are not open source `[inference]`. Primero is the one genuinely open, genuinely on-point system I found in this space, and it is the better find anyway because its subjects are minors.
- **Sanctions screening beyond nomenklatura** — I did not examine OpenSanctions' `yente`, `followthemoney` or `rigour` (the name-normalisation library), which likely contain useful transliteration/name-variant handling. Lead, not finding.
- **Hospital MPI beyond JeMPI** — `OpenEMPI`, `SanteMPI`, `OpenCR` all returned zero results in repo search; only JeMPI and the archived MohawkMEDIC `client-registry` (C#, 2017-era) surfaced. I did not verify whether OpenCR is superseded by JeMPI.
- **Confidential-address programs (Safe at Home)** — no open-source data model found for substitute-address programs. `CAPABILITY-MAP.md` §20 lists this and I have nothing to offer beyond "the guardian edge must be able to carry an address-suppressed flag." Unmet.

**Verified-as-absent (findings, not gaps):**

- **Splink's clerical-review guidance does not exist** — `docs/topic_guides/evaluation/labelling.md` reads verbatim *"This page is under construction - check back soon!"* `[repo]`, and `edge_metrics.md` gives no threshold-selection advice `[repo]`. There is no open-source consensus method for choosing a match threshold.
- **RiC-O's person/identity/name separation is unconfirmed.** I fetched the RiC-O repo page `[repo]` and it did **not** mention `rico:Identity`, `rico:hasOrHadIdentity`, `rico:Name` or `rico:Appellation`; code search over the repo returned zero hits. My belief that RiC-O separates an Agent from its date-bounded Identities is **`[inference]` and unverified** — I did not fetch the OWL file (`ontology/current-version/`). It remains a promising lead for the chosen-name model (archival practice needs "this person was known as X during period Y" for the same reasons this project does), and the same applies to **EAC-CPF** and **SNAC**, neither of which I reached.
- **Ed-Fi's `ContactRestrictions` is typed `string`** `[repo]` — the safety-critical court-order field is free text in the standard. This is a ledger, not a gate (CLAUDE.md #18).
- **No system found models per-audience visibility of a chosen name.** See the chosen-name section; this is new work.

---

## Weirdest things I found

1. **UNICEF's child-protection system solved the unmerge problem by never merging.** `PotentialMatch < ValueObject` in Primero `[repo]` is a *virtual* model — the candidate link between an unaccompanied child and a caregiver's tracing request is computed on read from a Solr query and never persisted. There is no potential-matches table, so there is no merge to reverse. The highest-stakes child-record matching system I could find made the suggestion layer stateless on purpose. It also boosts `name_nickname` equivalence to 15.0, the highest weight in the model — the *Robert/Bobby* problem is solved by storing the nickname, not by a better string metric.

2. **`blocked_extensions: [".svg", ".gph"]`.** ACRO `[repo]` blocks vector graphics from leaving a secure research environment, because an SVG of a suppressed table carries the suppressed values as path coordinates and a Stata `.gph` embeds the dataset. The entire "export the equity dashboard for the board presentation" feature in `CAPABILITY-MAP.md` §17 is an egress hole in one file format, and I would never have thought to look for it. Two words of YAML written by people who check outputs for a living.

3. **Medieval historians reframed the problem as source-attribution and got a better answer.** The factoid model (Bradley/Short 2005), via IPIF and the `papilotte` server `[repo]`: a **Factoid** aggregates a Source + a Person + a Statement, so nothing is ever asserted about a person except as a claim made by a named source. Identity across sources is itself just another retractable assertion. It composes exactly with `ARCHITECTURE.md` §8.1's `contradicts_or_tensions_with` relation and gives §15's `P1–P5` provenance ladder a home. Dormant since 2023, and the right shape.

4. **Genealogy software has a four-option enum for how much of a living person's name may leave the building.** Gramps `[repo]`: *"Include all selected people"* / *"Replace given names of living people"* / *"Replace complete name of living people"* / *"Do not include living people"*, implemented as chainable read-only proxy databases (`LivingProxyDb`, `PrivateProxyDb`) with a preview before export. Thirty years of family historians accidentally publishing living relatives' details produced a better export architecture than most privacy-first systems have — and "replace the given name on the printed output" is literally the concert-programme control this project needs.

5. **The standards body's own bridge admits the standard cannot carry the data.** `edfi-oneroster/standard/4.0.0/artifacts/pgsql/core/users.sql` `[repo]` contains `null::text as "preferredFirstName", -- DS4 doesn't have preferredfirstname column` and `null::text as "pronouns"`, alongside `agentSourceIds` (the guardian links) also NULL. The Ed-Fi Alliance shipping a OneRoster adapter that hardcodes pronouns and the entire family graph to NULL is the most concise possible argument that chosen name, pronouns and guardianship must be locally owned in terpsi-music — written, unintentionally, by the interop vendors themselves.

*Runner-up:* CiviCRM enforces a **per-relationship-direction** data-access grant in SQL (`is_permission_a_b` / `is_permission_b_a`, asserted in `QueryTest.php`) `[repo]` — a nonprofit CRM has the independently-revocable-guardian-edge model that `CAPABILITY-MAP.md` §20 needs, and it has had it for years.
