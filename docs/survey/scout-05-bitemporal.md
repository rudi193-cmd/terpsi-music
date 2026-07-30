# Scout 05 — "nothing is ever deleted, everything is dated"

Slice: data stores and modelling techniques for dated-not-deleted state, as-of reads,
correction-by-entry, per-subject partitioning, and "one referent, many subject-scoped
entries" (§7.1, §7.4 W-1/W-3, §8, §5, §11.1, §18 item 3).

---

## 0 · Provenance of this report — read before using it

Per §18 item 0 and CLAUDE.md #17, the epistemic state of each claim below is uneven and
is marked. Two constraints shaped what I could verify:

- **WebSearch budget was exhausted mid-task** (200/200). Searches 1–12 ran; nothing after.
- **Egress policy blocks nearly every non-GitHub host.** Verified by probe:
  `github.com`, `raw.githubusercontent.com`, `api.github.com` reachable; `docs.tigerbeetle.com`,
  `specifications.openehr.org`, `documentation.opencrvs.org`, `mariadb.com`, `www.loc.gov`,
  `en.wikipedia.org`, `illuminatedcomputing.com`, `pgedge.com`, `gramps-project.org`
  all refused at CONNECT.

So claims fall into three tiers, and I have tagged each row:

| Tag | Means |
|---|---|
| `P-src` | I read the repository page or a raw source file myself. Highest confidence. |
| `P-snip` | Search-result snippet quoting the primary spec/doc page; I could **not** open the page. Treat as cited-but-unread — the exact §18-item-0 defect. |
| `P-mem` | My prior knowledge, no fetch succeeded. Verify before building. |

**Star counts and commit counts below are read off the GitHub repo pages, not derived from
clones.** Last-commit *dates* were mostly not exposed in the fetched HTML; where I could not
read one I say `date not captured` rather than guessing. Nothing here should become a figure
in prose without a second pass.

---

## 1 · Ranked table

| # | Project / standard | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **openEHR change-control model** (`openEHR/specifications-RM`) + **EHRbase** (`ehrbase/ehrbase`) | EHR-per-subject with `VERSIONED_OBJECT`, `CONTRIBUTION` change-sets, `AUDIT_DETAILS`, `ATTESTATION`, and deletion as a *change_type on a new version* | EHRbase **Apache-2.0** `P-src`; spec licence file present, type not read `P-src` | EHRbase: 377★, 1 519 forks-ish/151 forks, 59 open issues, active on `develop`; date not captured `P-src` | W-1 lane, W-3 sealing, §8.2 draft/sealed, §7.1 no-delete, §7.4 I-7 | **steal-the-idea (highest)** |
| 2 | **`xocolatl/periods`** | PostgreSQL extension recreating SQL:2011/2016 application periods, `SYSTEM_TIME`, `FOR PORTION OF`, `WITHOUT OVERLAPS`, system versioning + `as_of`/`from_to`/`between` | **PostgreSQL Licence** `P-src` | 317★, 151 commits, master active `P-src` | §7.1 `valid_at`/`invalid_at` semantics; interval-splitting correctness | **steal-the-idea** (read as executable spec) |
| 3 | **`scalegenius/pg_bitemporal`** | Bitemporal Postgres framework (Asserted Versioning); `effective` + `asserted` `tstzrange` pair with a GiST EXCLUDE constraint | **BSD-3-Clause** `P-src` | 163★, 30 forks, 94 commits; maintenance state not established `P-src` | §7.1 two axes; the missing **verb set** | **steal-the-idea (the API vocabulary)** |
| 4 | **OpenStreetMap `Redaction` + `old_*.visible`** (`openstreetmap/openstreetmap-website`) | Planet-scale accretion store: delete = new version with `visible=false`; lawful erasure = a first-class `Redaction` record with author + title + description that *owns* the rows it hides | GPL-2.0 `P-mem` (licence file not read) | Very active project `P-mem`; the two models read directly `P-src` | §5 erasure-inside-a-chain, §7.1 no-delete, CLAUDE.md #20 tombstones | **steal-the-idea (top for erasure)** |
| 5 | **Gramps `EventRef` + role** (`gramps-project/gramps`) | Genealogy model where one shared `Event` is referenced by N `EventRef`s, each carrying `role_type` — one referent, many subject-scoped entries | **GPL-2.0** `P-src` | 3.0k★, active, not archived; date not captured `P-src` | **W-3 exactly**: 150 entries against one `Rehearsal` | **steal-the-idea (top for lane model)** |
| 6 | **TigerBeetle correcting-transfer discipline** (`tigerbeetle/tigerbeetle`) | Immutable double-entry: transfers never modified; corrections are further transfers; two-phase `pending` → `post`/`void`/timeout-expire | Apache-2.0 `P-mem` | Very active; Jepsen-analysed `P-snip` | correction-by-entry; §8.2 draft→sealed/reject; §7.4 I-6 timebound | **steal-the-idea** |
| 7 | **OpenCRVS record-correction workflow** (`opencrvs/opencrvs-core`) | Civil registration: registrar corrects a *registered* birth record — reason, supporting documents, request-vs-approve split, full audit | **MPL-2.0** `P-src` | 119★, active on `develop`; date not captured `P-src` | the **birthdate-corrected-two-seasons-late** case, as a shipped workflow | **steal-the-idea** |
| 8 | **`dolthub/dolt`** | MySQL-compatible SQL database with real Git semantics: branch, merge, `AS OF`, `dolt_diff_*`, `dolt_history_*`, cell-wise diff | **Apache-2.0** `P-src` | 31 391 commits, single ~103 MB binary, local-only viable `P-src` | §5 canonical-read-only + human promotion; §10 mutation testing | **steal-the-idea (strong)** / read-only-interest as a store |
| 9 | **`message-db/message-db`** | Pure-Postgres event/message store: one `messages` table, `category-id` stream naming, `write_message()` in SQL | **MIT** `P-src` | 1.7k★, 412 commits `P-src` | per-subject partitioning **by stream-name convention**; readable without app | **steal-the-idea** |
| 10 | **`simonw/sqlite-history`** | Triggers that mirror every INSERT/UPDATE/DELETE into `_<table>_history` with `_version`, `_updated`, `_mask` | **Apache-2.0** `P-src` | 130★, **11 commits** — tiny, effectively finished `P-src` | sidecar audit for non-state tables; leaves plain SQLite | **adopt (narrowly) / steal-the-idea** |
| 11 | **`goldmansachs/reladomo`** | Production Java ORM with first-class bitemporal "milestoning"; explicit three-way choice: audit-only / business-time-only / bitemporal chaining | **Apache-2.0** `P-src` | 390★, 367 commits, CI present, not archived `P-src` | §7.1's **state-vs-history exclusion list**, named as a first-class modelling decision | **steal-the-idea** |
| 12 | **ISO 19152 LADM `VersionedObject`** | Land-administration standard: `beginLifespanVersion` / `endLifespanVersion` / `quality` / `source` on an abstract superclass so title chains can be reconstructed as of any historical moment | ISO (paid standard; drafts public) `P-snip` | Edition II 2024–25 `P-snip` | §7.1 naming + the *court-reconstruction rationale* in writing | **steal-the-idea** |
| 13 | **BagIt (RFC 8493) + `LibraryOfCongress/bagit-python`** | Directory + payload + checksum manifests + `bag-info.txt`; `validate()` distinguishes `ChecksumMismatch` / `FileMissing` / `UnexpectedFile`; `payload-oxum` = byte count + file count | **CC0** `P-src` | 263★, 510 commits, maintained `P-src` | **W-6 graduate export**; §5's "emptied is not absent" (oxum ≡ count anchor) | **adopt** |
| 14 | **RO-Crate** (`ResearchObject/ro-crate`) | Self-describing data package: plain directory + `ro-crate-metadata.json` (JSON-LD) | **Apache-2.0** spec, **CC0** contexts `P-src` | 155★, 50 forks, active `P-src` | §11.1 "readable without the app"; W-6 export manifest | **adopt (for the export only)** |
| 15 | **Wikidata/Wikibase statement model** | Statements carry `rank` (preferred/normal/**deprecated** + `P2241` reason-for-deprecation), validity `qualifiers` `P580`/`P582`, and `references` | GPL `P-src` (repo is a Gerrit mirror) | 46 922 commits; **not a modest-box deployment** `P-src` | the **deprecated-vs-ended distinction** this schema will otherwise conflate | **steal-the-idea (model only)** |
| 16 | **MARC 21 Authority `682` + Leader/05 status `d`/`o`/`s`/`x`** | A deleted heading is not removed: status code plus a `682` field explaining the deletion and naming the replacement | Public (LoC) `P-snip` | Standing standard `P-snip` | CLAUDE.md #20 five-part tombstone, already an operating practice | **steal-the-idea** |
| 17 | **Memento — RFC 7089** (`webrecorder/pywb`) | `Accept-Datetime` request header + `Memento-Datetime` response header; TimeGate/TimeMap; documented edge behaviour when the requested time precedes the first version | RFC / pywb open `P-snip` | RFC is stable; pywb active `P-snip` | as-of reads as a **protocol-level** concern, not per-endpoint params | **steal-the-idea** |
| 18 | **`arkhipov/temporal_tables`** | C-trigger system-period versioning for Postgres; `versioning()`, `set_system_time()`, tstzrange system period, history table | **BSD-2-Clause** `P-src` | 1.0k★, 70 commits, CI green on Linux+Windows `P-src` | reference for system-time-only tables (the §7.1 "history" half) | read-only-interest |
| 19 | **`pyeventsourcing/eventsourcing`** | Python event sourcing with pluggable persistence incl. **SQLite**; snapshots; app-level encryption at rest | **BSD-3-Clause** `P-src` | 1.7k★, 5 401 commits, v9.6 `P-src` | sidecar / commentary pipeline, not the canonical store | read-only-interest (see §3 caution) |
| 20 | **`replikativ/datahike`** | Durable Datalog, accretion-only, embedded; konserve backends (file, LMDB, JDBC, S3); history/as-of/since; claims **GDPR excision / complete data purge** | **EPL-1.0** `P-src` | 1 759 commits; cited production use (Swedish Public Employment Service, 2024) `P-src` | the accretion-store-plus-lawful-purge combination | read-only-interest |
| 21 | **`xtdb/xtdb`** | Immutable SQL database with automatic system-time + valid-time, SQL:2011 period functionality over the Postgres wire | **MPL-2.0** `P-src` | 3.0k★, 9 238 commits, v2.1.0 Dec 2025 `P-snip` | the reference for *what good bitemporal SQL feels like* | read-only-interest (see §4) |
| 22 | **`google/trillian`** | Verifiable append-only Merkle log, MySQL/MariaDB storage, "personality" pattern separating admission criteria from the log | Apache-2.0 `P-mem` | Active; Go 1.25+ `P-src` | comparison point for the existing hash-chained disclosure log | read-only-interest |
| 23 | **`terminusdb/terminusdb`** | Git-for-data immutable graph DB, commits/branches/time-travel, local Docker at `:6363` | **Apache-2.0** `P-src` | 3.4k★, 5 759 commits; README announces "new maintainers and an **enterprise version**" `P-src` | version-control-as-database | read-only-interest |
| 24 | **`vlcn-io/cr-sqlite`** | SQLite extension adding CRDTs, per-row/per-column versioning, **causal-length sets for deletes** | **MIT** `P-src` | 3.7k★, 2 163 commits; inserts 2.5× slower `P-src` | the "delete is data" primitive; offline replicas (§11) | read-only-interest |
| 25 | **`simonmichael/hledger` / `beancount/beancount`** | Plain-text double-entry; the file *is* the database | **GPL-3.0** / **GPL-2.0** `P-src` | 4.6k★ / 5.8k★, both active; beancount v3 current, v2 frozen `P-src` | §11.1 exit line taken to its limit | steal-the-idea |
| 26 | **`freelawproject/courtlistener`** | Court docket archive: dockets, entries, filings | **AGPL** `P-src` | 983★, 24 734 commits `P-src` | docket-entry immutability, sealed-entry handling — **could not verify either** | read-only-interest, unverified |
| 27 | **`formancehq/ledger`** | Append-only-ish double-entry ledger service, Postgres | **MIT** `P-src` | 1.3k★, 1 123 commits `P-src` | ledger service shape | read-only-interest |
| 28 | **`codenotary/immudb`** | Immutable append-only tamper-evident DB, Merkle commit log, single binary, PG wire, `immudb_history()` | **BUSL 1.1 — not OSI open source** `P-src` | 9.0k★, v1.9.5 `P-src` | — | **reject** (licence + opaque storage) |
| 29 | **MariaDB system-versioned + application-time tables** | SQL:2011 `FOR SYSTEM_TIME AS OF`, application periods, bitemporal combination, per-column `WITHOUT SYSTEM VERSIONING` | GPL-2.0 `P-mem` | Shipping since 10.3 `P-snip` | the only *mainstream, on-prem, GPL* engine with both axes in core SQL | read-only-interest (wrong engine here) |

---

## 2 · Top finds — transplant and cost

### 2.1 openEHR's change-control package — the lane model already specified, by people who lost the argument once

This is the single highest-value find and it is not a library, it is a standard with a
running open-source implementation. openEHR's architecture puts **one `EHR` object per
subject**, identified by an EHR id, holding versioned information *plus a list of
`CONTRIBUTION` objects acting as audits of change-sets* `P-snip`. Every version carries
`AUDIT_DETAILS` with `system_id`, `committer`, `time_committed`, `change_type`, `description`,
and the subtype **`ATTESTATION`** exists precisely so that "who attested this, and when" is
recorded separately from "who committed it" — described in the spec as being there "as required
by enterprise processes or legislation" `P-snip`. The complete list of `CONTRIBUTION`s "provides
a complete history of the change-sets made to the repository and is the basis for performing
rollback to access previous informational states" `P-snip`.

Read that against §8.2 and it is the same object with different names: openEHR's
`committer`/`ATTESTATION` split *is* `draft` vs `sealed`, and it is thirty years older. Read it
against W-1 and the per-subject EHR *is* the lane. Read it against §7.1 and the change-control
model's whole premise is that a clinical record is append-only and that removing information
is expressed as a new version with a change type, not as an absence.

**Concrete transplant.** Migration 001 (§18 item 3) can be written as three tables plus a
per-lane pattern, borrowing the names outright: a `lane` row per student (the EHR); a
`contribution` table that is the *unit of write* — every write to a lane belongs to exactly one
contribution carrying `committer`, `time_committed`, `change_type`, `description`; and an
`attestation` table that is the seal (§8.2's `sealed`), never merged into the contribution row,
because the whole point is that committer ≠ attester. `change_type` becomes the enum that
replaces DELETE everywhere: `creation`, `amendment`, `modification`, `synthesis`, `deleted`.
`deleted` is a *value in a column on a new row*, which is exactly what §7.1 asks for and
exactly what stops a developer reaching for `DELETE FROM`.

**Cost.** Two real ones. First, the spec is large and archetype-driven, and adopting the
*archetype/template* half (ADL, AQL, RM 1.1.0) would be a catastrophic amount of machinery for
a music program — the transplant is the change-control package only, and the discipline needed
is to take three classes and refuse the other several hundred. Second, EHRbase itself is
**Java 25 + PostgreSQL 15/16+** `P-src`, so it is a reference to read, not a dependency to take:
it fails "single modest box, SQLite, readable without the app" on both counts. Budget: one
afternoon reading `master04-change_control`, then the names land in migration 001 for free.
(Caveat: I could **not** open the spec page — the openEHR host is blocked here — so every
quoted field name above is `P-snip`. Confirm against the actual spec before it enters a
migration.)

### 2.2 `periods` + `pg_bitemporal` — the two operations §7.1 does not yet name

§7.1 settles the *columns* (`valid_at`/`invalid_at`, adopted from willow-2.0) and leaves the
*verbs* unnamed. These two projects supply them, and they disagree in a productive way.

`pg_bitemporal` (BSD-3-Clause, 163★, 94 commits `P-src`) uses `effective tstzrange` and
`asserted tstzrange` with an `EXCLUDE` constraint on `(business_key =, asserted &&, effective &&)`,
and exposes a function set whose *names are the finding*: `ll_bitemporal_insert`,
`ll_bitemporal_update` (record a change in business reality — creates a new assertion),
**`ll_bitemporal_correction`** ("fix past incorrect assertions without adding new historical
records"), **`ll_bitemporal_inactivate`** ("make record(s) not currently effective while keeping
assertion current"), and `ll_bitemporal_delete` (end the assertion interval) `P-src`.

That four-way split is the vocabulary §7.1's court-order case needs. A restriction that *took
effect in March and was learned in October* is an `insert` with a backdated `effective` and a
current `asserted`. A guardianship that *ends today* is an `inactivate`. A guardianship
recorded against the wrong parent is a **`correction`** — and the distinction between
`correction` and `inactivate` is exactly the distinction §7.1 is groping for when it separates
"when the restriction took effect" from "when this system learned of it." Right now this
codebase has one verb for four acts, and the audit log cannot tell them apart afterwards.

`periods` (PostgreSQL Licence, 317★ `P-src`) contributes something different and more
dangerous-to-get-wrong: a working implementation of **`FOR PORTION OF`** via `INSTEAD OF`
triggers on views, which "updates or deletes ... target specific time portions, automatically
inserting new rows for unmodified sections" `P-src`. That is interval splitting, and it is the
operation an application will implement by hand, get subtly wrong, and only discover when a
fee waiver spans two seasons. It also enforces **start inclusive, end exclusive** and
**start strictly less than end** `P-src`, and it notes it "cannot simulate deleting period
portions" `P-src` — an honest boundary worth copying as a documented non-goal rather than
rediscovering. Its `as_of` / `from_to` / `between` function trio is a ready-made read API.

**Concrete transplant.** Do not install either — both are Postgres, this is SQLite. Instead:
(a) adopt the four verb names as the *only* four write functions permitted against any table
carrying the pair, so `DELETE` never appears in application code and the audit log records
which of the four occurred; (b) port `periods`' three invariants as SQLite `CHECK` constraints
and a trigger — `invalid_at IS NULL OR invalid_at > valid_at`, half-open intervals, and
non-overlap per subject-plus-key; (c) lift the `FOR PORTION OF` split algorithm as pseudocode
into the migration's comment block, with a test per branch.

**Cost.** Low and mostly reading — a day for the verb set, two or three for a correct
non-overlap trigger and its mutation tests. The real cost is that SQLite has no range type
and no GiST exclusion constraint, so non-overlap must be enforced by trigger, and a writer
reaching past the module straight to SQL can defeat a trigger the same way §5's guardian-trigger
bug did when the chain name gained a suffix. That is a §16 pair with no middle unless the
constraint is *also* asserted by a periodic verifier over the whole table — which makes this
a **ledger plus enforcement**, and CLAUDE.md #18 requires saying which is which.

### 2.3 OpenStreetMap's `Redaction` — "never delete" and lawful erasure, reconciled in production

This is the answer to the hardest sentence in the slice, and I verified it in source rather
than in prose. `app/models/old_node.rb` carries `validates :visible, :inclusion => [true, false]`
and `belongs_to :redaction, :optional => true` `P-src`. So: a deletion in OSM is a *new
version of the object with `visible=false`* — the row is never removed, which is §7.1's rule
at planet scale. And erasure is a **separate, named, authored object**: `app/models/redaction.rb`
`belongs_to :user`, `has_many :old_nodes`, `:old_ways`, `:old_relations`, with validated-present
`title` and `description`, described in its own docs as "a record associated with a particular
action on the database to hide revisions from the history which are not appropriate to
redistribute any more" `P-src`.

Note what that buys, because it is precisely what §5 and CLAUDE.md #3/#20 are asking for and
what a bare `DELETE` cannot give. The erasure is **itself a dated record with an author and a
stated reason**, it **owns** the rows it suppresses by foreign key, and it is *revocable* —
un-redacting is deleting one Redaction row, not resurrecting data from a backup. Contrast the
usual approach (a `deleted_at` column, or a hard delete plus a log line): neither can answer
"who erased this, under what authority, and what exactly did it cover," which is the only
question that will be asked.

**Concrete transplant.** Add a third concept beside the `valid_at`/`invalid_at` pair, and give
it a domain noun: `Suppression` (or `ErasureOrder`). Columns: `id`, `authority` (the person or
order), `reason`, `basis` (FERPA/COPPA/court/retention-schedule), `created_at`, and a scope. Every
suppressible row gains a nullable `suppression_id`. Reads filter on `suppression_id IS NULL`
by default and fail closed if the join cannot be evaluated (§6, CLAUDE.md #13). Purge at a
season boundary is then two acts, not one: create the Suppression (dated, authored, reasoned),
*then* — and only for the classes where law requires actual destruction — run the physical
delete against the rows that Suppression already covers, leaving the Suppression as the
tombstone. That is CLAUDE.md #20's five-part tombstone with a foreign key instead of a
convention, and it composes with §5's per-subject chain partitioning: the Suppression names
one subject, so the physical delete stays inside one partition.

**Cost.** One table, one nullable FK per suppressible table, and a hard discipline that every
read path joins it — which is the same discipline the lane model already requires, so the
marginal cost is small if it lands in migration 001 and enormous if it lands later. The
non-obvious cost: a Suppression row is itself a record *about* a student, so under §7.4 I-7 it
must be as durable as anything else, meaning no role may delete a Suppression it created. That
needs its own refusal test.

### 2.4 Gramps `EventRef` — genealogy solved W-3 in the 1990s

W-3 says "a shared event is two lane entries with one referent," §18 item 3 says no schema
exists for it, and §8 is a sketch. Genealogy software has shipped this model for decades
because a wedding involves two people and a census involves a household, and the field learned
early that putting a roster on the event is wrong. Gramps' `EventRef` exists, in its own words,
"for keeping information about how the person relates to the referenced event," storing a
`__role` attribute as an `EventRoleType` `P-snip`, and its documented SQL schema gives the
`eventref` table as `object_type_id`, `object_id`, `order`, `last_changed`, `private`,
`ref_object_id` → event, `role_type_id` → eventroletype `P-snip`. The worked example in the
docs is a **census "shared between people of the same house"** `P-snip` — structurally
identical to a rehearsal shared between 150 students.

Two details are worth more than the table itself. **`role_type_id`**: the reference is not a
bare membership link, it carries *how* this subject stood in relation to the referent. A
rehearsal entry for a student is `performer`; for a staff member `supervisor`; for a guardian
`chaperone`; for a judge `adjudicator`. That single column is what lets one `Rehearsal` serve
six personas without a roster column and without six join tables. **`private`**: a per-reference
privacy flag, not a per-event one — the event can be visible while one participant's link to it
is not, which is §7.2's read/export split at row granularity.

**One correction to the obvious read, verified in source.** Gramps' *current* storage is not
the normalised schema. `gramps/plugins/db/dbapi/dbapi.py` creates `person`, `family`, `source`,
`citation`, `event`, `media`, `place`, `repository`, `note`, `tag`, plus a single generic
`reference (obj_handle, obj_class, ref_handle, ref_class)` link table with **no primary key**,
and stores object bodies as `json_data TEXT` or `blob_data BLOB` `P-src`. So the `eventref`
table from the wiki is a derived/legacy SQL projection, and the live store is a document store
with a reference index. **Steal the model, not the storage** — a blob-per-object store fails
§11.1's "readable without the app" the moment the blob is a pickle, and it makes the
`valid_at`/`invalid_at` pair unqueryable.

**Concrete transplant.** `LaneEntry(id, lane_id, referent_type, referent_id, role, valid_at,
invalid_at, created_at, contribution_id, suppression_id)`, with `Rehearsal`, `Travel`,
`Adjudication` as referents holding no participant list whatsoever. Attendance, commentary
addressing, trip rooming and fee incidence all become entries. The referent tables must be
*forbidden* from carrying a participant column, and that prohibition needs a refusal test
(CLAUDE.md #19) — a schema assertion that no table referencing a student appears in a referent
table's columns. This is the cheapest possible moment to do it and, as §7.4 W-3 and §18 item 3
both say, a migration across every student-referencing table afterwards.

**Cost.** Roughly zero now; it *is* migration 001. The genuine cost is query ergonomics: every
"who is at this rehearsal" question becomes an aggregate over lane entries the caller may not
be permitted to see in full, so the count and the list are different permissions — which is
§7.2's gate-the-export/narrate-the-read rule falling out of the schema rather than being bolted
onto it. Note also the storage-layer wrinkle: a single shared `lane_entry` table is one physical
table for all lanes, which satisfies W-3 logically but not W-1's "separate storage." Whether
lanes are separate tables, separate SQLite files, or one table with enforced scoping is the
decision this schema still has to make (see §5 below).

### 2.5 TigerBeetle — correction-by-entry, with the two-phase state machine thrown in

Accounting solved "never mutate a record" before computers, and TigerBeetle is that discipline
compiled. Its documentation is blunt: "Transfers are immutable. They are never modified once
they are successfully created" and "if a detail of a transfer is incorrect and needs to be
modified, this is done using **correcting transfers**" — with the stated rationale that
"adding transfers as opposed to deleting or modifying incorrect ones **adds more information
to the history**" `P-snip`. That last clause is the sentence to put in `docs/` above migration
001, because it reframes append-only from a constraint into a benefit and it will survive
translation to a director.

The second half is the more surprising transplant: **two-phase transfers**. A transfer can be
`pending` — reserving capacity without committing — then either `post`ed (committing at most the
pending amount), explicitly **`void`**ed, or **automatically expired via a `timeout` field**
`P-snip`. Map that onto this codebase and it is three separate unmet requirements at once:
§8.2's `draft` → `sealed` / `reject_match` cascade for commentary; §7.4 I-6's "every ask gets a
dated disposition, silence is not an answer, and the timebound is declared at issuance"; and
the fee/waiver flow where a charge is provisional until a human decides. One state machine,
three uses, and a ledger domain has already proved it holds under adversarial conditions.

**Concrete transplant.** A `Disposition` state machine reused by commentary sealing, fee
waivers, absence requests and records-inspection requests: `pending` with a mandatory
`timeout_at` set *at creation* (I-6's "declared at issuance", and the office cannot extend it —
which means `timeout_at` is immutable after insert and needs a trigger proving so), resolving to
`posted`/`sealed`, `voided`/`rejected`, or `expired`. Expiry is a **predicate on read**
(`now() > timeout_at AND resolved_at IS NULL`), not a nightly job — the same rule §7.1 sets for
majority, and for the same reason: a backdated correction to `timeout_at`'s inputs must not
leave a window query answering "nobody."

**Cost.** Low. The state machine is small; the discipline is that `rejected` must be stored as
durably as `sealed` (§8.2, CLAUDE.md #10) and that an expiry is recorded as an event with a
reason of "no answer," not inferred silently. Do not adopt TigerBeetle itself: it is a
single-purpose financial engine with its own on-disk format, which fails "readable without the
app," and this domain's money is fee schedules and trip accounts, not a payments ledger.

---

## 3 · Cautions on things that look adoptable and are not

- **Event sourcing as the canonical store.** `pyeventsourcing/eventsourcing` (BSD-3, 1.7k★,
  SQLite persistence, app-level encryption at rest, snapshots `P-src`) is genuinely good and
  genuinely wrong here. An event log is *maximally* unreadable without the application: the
  current state of a student's guardianship is a fold over N rows whose meaning lives in Python
  classes, so §11.1's "SQLite plus documented schema, exportable to CSV per record type" fails
  by construction. Bitemporal tables and event sourcing both give you history; only the former
  gives you history you can read with `sqlite3`. Use event sourcing, if at all, for the sidecar
  side (§5's practice logs, agent output, triage state) where replay is the point.
- **XTDB.** MPL-2.0, real SQL:2011 bitemporality, no triggers or history tables `P-src` — the
  most technically apt engine in the list, and it should be rejected. Its own README describes
  it as "cloud native" with an architecture "designed for object storage" `P-src`; it is a JVM
  service; and I found **no documented way to read its data without it** — the storage-config
  page was unreachable from here, so treat "can XTDB run single-node on local disk and can its
  files be read by anything else" as an **unknown**, not a no. Worth one hour if someone
  reconsiders the SQLite decision; not worth reopening the decision for.
- **immudb.** **BUSL 1.1** `P-src`. Not open source, and its Merkle-structured storage is not
  externally readable. Disqualified twice over.
- **Wikibase.** The *model* is a top-five find (see §4); the *software* is MediaWiki plus
  MySQL plus a query service and is not a modest-box deployment `P-src`.
- **`cr-sqlite`.** Attractive for §11's offline replicas, but note its README: current
  "Approach 1" is explicitly **history-free** CRDTs, with the causal-event-log version deferred
  to a planned v2, and inserts are 2.5× slower `P-src`. A history-free store is the opposite of
  this slice's requirement. Its causal-length-set treatment of deletes is the idea to keep.
- **`sqlite-history`.** Adopt narrowly and read the encoding first: it marks a delete by
  setting `_mask = -1` `P-src`. That is a scale encoded as a bare integer with a magic sentinel,
  which is CLAUDE.md #14's exact hazard. If it is used, `-1` gets a named constant and a mapping
  table on day one. It is also an 11-commit project — fine for a mechanism you will read and
  vendor deliberately with a named middle (§16), not fine as an unexamined dependency.

---

## 4 · Weirdest things I found

**1 · MARC 21 Authority field `682`, "Deleted Heading Information."** Libraries have run
CLAUDE.md #20's tombstone rule as production practice since the 1970s. When an established
heading is withdrawn, the record is *not* removed: Leader/05 takes a status code (`d`, `o`, `s`,
or `x`) and a `682` field is added whose entire purpose is "to provide an explanation for the
deletion of an established heading or subdivision record from an authority file," used **only
when** the leader carries one of those codes `P-snip`. Status first, reason stated, successor
named, stub retained, and the retired heading stays searchable so anyone holding the old
identifier lands on the new one. That is the five-part tombstone, standardised, with a
conformance rule (the `682` is invalid unless the status code agrees). Steal the *shape*: a
tombstone whose validity is checked against the status field it claims to explain is a middle
that can fire; a tombstone that is only a comment is a ledger.

**2 · Wikidata's rank/qualifier split — the distinction this schema is about to conflate.**
Wikidata forbids deleting a wrong statement; you set its **rank to `deprecated`** and attach
`P2241` reason-for-deprecation. But — and this is the sharp part — "correct historical
information, such as previous values of a statement, should be annotated with the appropriate
**start time (P580) / end time (P582)** qualifiers rather than being marked as deprecated"
`P-snip`. Two different kinds of not-current, deliberately kept apart: *was true, then ended*
versus *was never true, we were wrong*. The stated benefits of deprecating rather than deleting
include letting "other users know not to re-add the value" `P-snip` — a delete invites the same
mistake back in. §7.1 currently has one mechanism (`invalid_at`) doing both jobs. A guardianship
that ended at majority and a guardianship that was recorded against the wrong parent must not
look identical on read, and today they would. Fix: `invalid_at` plus a mandatory
`invalidation_kind` (`ended` | `superseded` | `erroneous`) and, for `erroneous`, a required
reason — which is also `pg_bitemporal`'s `inactivate`-versus-`correction` split arriving from a
completely different direction. Two independent fields converging on the same distinction is
about as strong a signal as this kind of scouting produces.

**3 · ISO 19152 (LADM) `VersionedObject`, and why land registries wrote the rationale down.**
An ISO land-administration standard puts `beginLifespanVersion`, `endLifespanVersion`, `quality`
and `source` on an *abstract superclass* that concrete cadastral classes inherit, introduced
"in the core LADM to manage and maintain historical data in the database," with the stated
requirement that "inserted and superseded data be given a timestamp" so that "the contents of
the database can be reconstructed as they were at any historical moment" `P-snip`. Land registries
adopted dated-not-deleted because a title dispute is litigated years later and the court asks
what the register said on a specific date — the identical argument §7.1 makes about a court
order arriving mid-season. Two things to steal: the **abstract-superclass placement** (versioning
is inherited, not remembered per table, so a new table cannot forget it — the closest thing a
schema has to an enforcement rather than a convention), and `source` as a *sibling* of the date
pair, since "the responsible organization of a specific instance version" `P-snip` is exactly
what §7.1 needs to distinguish a court order from an SIS import from a director's edit. One
smaller note worth knowing: in Edition II `beginLifespanVersion` went from mandatory to optional
`P-snip` — the same softening that produced §7.1's caveat about rows ending up with only one
axis. If an ISO committee could not hold that line, this codebase should expect not to either,
and should enforce non-null in the schema.

**4 · Memento (RFC 7089): as-of belongs in the protocol, not the query string.** Web archiving
made time travel an **HTTP content-negotiation dimension**. The client sends `Accept-Datetime`;
the response carries `Memento-Datetime` stating the version actually served; a TimeGate picks
the best match and a TimeMap lists what exists; and the spec pins the edge case — if the
requested datetime precedes the first version or follows the most recent, the first or most
recent "must be selected respectively" `P-snip`. pywb implements it including in proxy mode,
where "the `Accept-Datetime` header overrides any other timestamp setting" `P-snip`. The
transplant is architectural: make as-of a **single header on the read path** rather than an
`as_of` parameter each endpoint may or may not implement. Every endpoint becomes time-travelling
at once, the *served* version is always echoed back so a caller can never mistake a nearest-match
for an exact one, and — the part that matters here — the audit question "what did this look like
on October 12" is answered by the same code path that serves today, so it cannot drift out of
agreement with it. Two `WARNING`s: an as-of read must still be gated by *today's* authorization,
never the historical grants, or time travel becomes a privilege-escalation primitive; and every
as-of read is a disclosure and must be narrated (§7.2).

**5 · BagIt's `payload-oxum` is §5's count anchor, invented independently by archivists.**
§5 records that a chain's head anchor must carry "a `count` as well as a hash" so that "a
surviving anchor beside missing rows reads as *tampered*, not *absent*" (#121). BagIt — RFC
8493, used to move archival material between institutions — carries exactly that: a
`payload-oxum` of **total byte count plus file count**, enabling a `--fast` validation that
checks structure without hashing, and `bagit-python`'s validator distinguishes `ChecksumMismatch`
from `FileMissing` from `UnexpectedFile` as separate error classes `P-src`. Two communities with
nothing in common arrived at the same defence: emptied must not read as never-written, and the
counter-check is a count. And `bagit-python` is **CC0** `P-src`, so it can simply be used. This is
the W-6 graduate export, essentially free: a bag per graduating lane, manifest and oxum inside,
`validate()` as the acceptance test, wrapped in an RO-Crate `ro-crate-metadata.json` (Apache-2.0
spec, CC0 contexts `P-src`) so the directory explains itself in JSON-LD to a recipient who has
never heard of this program. §11.1 wants an exit line that can be written honestly before the
first install; this is most of the sentence, already standardised, already validated by tooling
someone else maintains.

*Runner-up, too on-the-nose to be weird:* **OpenCRVS**, a civil-registration system whose
documented core function is correcting a **registered birth record's date of birth** — reason
recorded, supporting documents attached, request-versus-approve split across roles, audit of all
actions, and a re-issued certificate `P-snip`. The scenario §7.1 and this slice both name as the
proving case ("a birthdate corrected two seasons late") is somebody else's shipped feature with a
written specification. Its deployment (TypeScript microservices, Docker Compose / Helm, MPL-2.0,
119★ `P-src`) is wrong for one modest box, so this is a workflow to read, not software to run.

---

## 5 · The decision this scouting cannot make for you

Everything above assumes the lane is a *logical* partition — a `lane_id` column plus enforced
scoping. W-1 says "separate storage." The prior art splits:

- **One row-set, scoped** (message-db's `category-id` stream convention `P-src`; Gramps'
  generic `reference` table `P-src`): cheapest, and the failure mode is precisely §5's
  guardian-trigger bug — a writer reaching past the module straight to SQL escapes the scope.
- **One physical store per subject** (§5's `consent/<subject_hash>` chain partitioning, already
  built): erasure becomes `rm`, unscoped access fails closed by construction, and per-subject
  export for W-6 is the file itself. Costs: cross-lane reads (a rehearsal roster, a season
  ledger) become N-file fan-outs, and "one SQLite file per student" multiplies open handles,
  backup surface and schema-migration work by the roster size.

§5 already chose per-subject partitioning for the consent chain and states the two consequences
that bit (`chain = 'consent'` name-matching, and emptied-versus-absent). Migration 001 should
either extend that choice to lanes and pay the fan-out cost, or state plainly that lanes are
logically scoped and name the enforcement that makes the scope real — and per CLAUDE.md #18, say
which of those is enforcement and which is a ledger. **I found no open-source project that does
per-subject physical partitioning of an education-records-shaped relational store**; the closest
analogues are multi-tenant database-per-tenant patterns, which I could not verify before the
search budget ran out. Treat that as an unknown, not as an absence.

---

## 6 · Sources

Verified by direct fetch (`P-src`):
[xtdb/xtdb](https://github.com/xtdb/xtdb) ·
[goldmansachs/reladomo](https://github.com/goldmansachs/reladomo) ·
[simonw/sqlite-history](https://github.com/simonw/sqlite-history) ·
[scalegenius/pg_bitemporal](https://github.com/scalegenius/pg_bitemporal) ·
[pg_bitemporal reference](https://raw.githubusercontent.com/scalegenius/pg_bitemporal/master/docs/pg_bitemporal_reference.md) ·
[xocolatl/periods](https://github.com/xocolatl/periods) ·
[arkhipov/temporal_tables](https://github.com/arkhipov/temporal_tables) ·
[dolthub/dolt](https://github.com/dolthub/dolt) ·
[message-db/message-db](https://github.com/message-db/message-db) ·
[pyeventsourcing/eventsourcing](https://github.com/pyeventsourcing/eventsourcing) ·
[replikativ/datahike](https://github.com/replikativ/datahike) ·
[terminusdb/terminusdb](https://github.com/terminusdb/terminusdb) ·
[vlcn-io/cr-sqlite](https://github.com/vlcn-io/cr-sqlite) ·
[codenotary/immudb](https://github.com/codenotary/immudb) ·
[google/trillian](https://github.com/google/trillian) ·
[ehrbase/ehrbase](https://github.com/ehrbase/ehrbase) ·
[openEHR/specifications-RM](https://github.com/openEHR/specifications-RM) ·
[opencrvs/opencrvs-core](https://github.com/opencrvs/opencrvs-core) ·
[gramps-project/gramps](https://github.com/gramps-project/gramps) ·
[gramps dbapi.py](https://raw.githubusercontent.com/gramps-project/gramps/master/gramps/plugins/db/dbapi/dbapi.py) ·
[OSM old_node.rb](https://raw.githubusercontent.com/openstreetmap/openstreetmap-website/master/app/models/old_node.rb) ·
[OSM redaction.rb](https://raw.githubusercontent.com/openstreetmap/openstreetmap-website/master/app/models/redaction.rb) ·
[ResearchObject/ro-crate](https://github.com/ResearchObject/ro-crate) ·
[LibraryOfCongress/bagit-python](https://github.com/LibraryOfCongress/bagit-python) ·
[ICA-EGAD/RiC-O](https://github.com/ICA-EGAD/RiC-O) ·
[freelawproject/courtlistener](https://github.com/freelawproject/courtlistener) ·
[simonmichael/hledger](https://github.com/simonmichael/hledger) ·
[beancount/beancount](https://github.com/beancount/beancount) ·
[Gnucash/gnucash](https://github.com/Gnucash/gnucash) ·
[formancehq/ledger](https://github.com/formancehq/ledger) ·
[mediawiki-extensions-Wikibase](https://github.com/wikimedia/mediawiki-extensions-Wikibase) ·
[pjungwir](https://github.com/pjungwir)

Cited but unread — host blocked (`P-snip`):
[openEHR Common IM](https://specifications.openehr.org/releases/RM/Release-1.0.3/common.html) ·
[openEHR EHR IM](https://specifications.openehr.org/releases/RM/latest/ehr.html) ·
[OpenCRVS correct record](https://documentation.opencrvs.org/product-specifications/core-functions/8.-correct-record) ·
[TigerBeetle correcting transfers](https://docs.tigerbeetle.com/coding/recipes/correcting-transfers/) ·
[TigerBeetle Transfer reference](https://docs.tigerbeetle.com/reference/transfer/) ·
[MARC 21 Authority 682](https://www.loc.gov/marc/authority/ad682.html) ·
[Wikidata Help:Ranking](https://www.wikidata.org/wiki/Help:Ranking) ·
[RFC 7089 Memento](https://www.ietf.org/rfc/rfc7089.txt) ·
[pywb Memento API](https://pywb.readthedocs.io/en/latest/manual/memento.html) ·
[ISO 19152 LADM DIS](https://gdmc.nl/oosterom/ISO19152LADM_DIS1.pdf) ·
[LADM Edition II design](https://www.sciencedirect.com/science/article/pii/S0264837723004696) ·
[MariaDB system-versioned tables](https://mariadb.com/kb/en/system-versioned-tables/) ·
[Gramps SQL Database wiki](https://www.gramps-project.org/wiki/index.php/Gramps_SQL_Database) ·
[Gramps EventRef API](https://gramps-project.org/api_5_1_x/_modules/gramps/gen/lib/eventref.html) ·
[Datomic GDPR write-up](https://vvvvalvalval.github.io/posts/2018-05-01-making-a-datomic-system-gdpr-compliant.html) ·
[SQL:2011 temporal survey](https://illuminatedcomputing.com/posts/2019/08/sql2011-survey/) ·
[Postgres 19 temporal](https://www.pgedge.com/blog/looking-forward-to-postgres-19-its-about-time)

---

## 7 · Follow-ups this scout could not close

1. **XTDB single-node local-disk deployment and external readability of its Arrow files** —
   unknown, host blocked. One fetch of `docs.xtdb.com/ops/config/storage` closes it.
2. **CourtListener's docket-entry immutability and sealed-document handling** — the one
   legal-docket lead I could not verify at all.
3. **Per-subject physical partitioning prior art** (database-per-subject at roster scale) —
   search budget ran out before this was covered. This is the open question in §5 above and the
   most consequential gap in this report.
4. **PostgreSQL core temporal status** (`WITHOUT OVERLAPS`, temporal FKs, `FOR PORTION OF`, and
   which release each landed in) — `periods`' README claims native supersession from PG 16+
   `P-src`; the pgEdge and illuminatedcomputing posts that would confirm the release mapping are
   both blocked. Only matters if the SQLite decision is ever revisited.
5. **Whether the openEHR field names quoted in §2.1 are exact** — all `P-snip`. Confirm before
   they enter migration 001, because §7.1's whole point is that adopting existing spellings
   beats inventing new ones, and a *misquoted* existing spelling is worse than either.
