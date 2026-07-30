# Scout 14 — Leaving: exit, export, retention, disposition, tombstones

Scope read first: `docs/ARCHITECTURE.md` §10 (compliance map, records retention row; acceptance-is-mutation),
§11 (operations, season lifecycle, loss of the director), §11.1 (exit is a shipping requirement; five-point
sovereignty test; the Delisted-fails-CI caution; W-6 as the smaller and harder obligation), §7.4 (W-1/W-3/W-6,
I-6, I-7, I-10), §16 "How a document should die" (the five-part tombstone) and its pair/middle rules.
`CLAUDE.md` items 15, 16, 17, 20.

---

## Method and its honest limits

**Read this before trusting any line below.** The session's WebSearch budget was exhausted after the first four
queries. The outbound proxy in this environment permits **only `github.com`, `raw.githubusercontent.com`, and
`api.github.com`** — every other host I probed (`ocfl.io`, `datapackage.org`, `rfc-editor.org`, `loc.gov`,
`sqlite.org`, `protobuf.dev`, `ndsa.org`, `parcore.org`, `verapdf.org`, `gedcom.io`, `ica.org`, `pds.nasa.gov`,
`collectionstrust.org.uk`, `uniformlaws.org`, `kubernetes.io`, `buf.build`, `datacite.org`, `en.wikipedia.org`,
33 hosts total) returned a proxy policy denial. So verification ran through GitHub repo pages and raw files.

Three tiers, marked per row. Per `CLAUDE.md` item 17 I am not going to launder the third tier into the first.

- **[V]** verified this session by fetching the repo page or a raw file (2026-07-30).
- **[S]** verified only by web search result text before the budget ran out; the primary source was not fetched.
- **[K]** cited from prior knowledge, **not verified this session**. Treat as a lead to check, not a fact.

Star counts and commit counts below are as GitHub rendered them on 2026-07-30 and are the kind of figure §10
warns about; they are here as activity signal only, not as claims about the projects.

---

## Ranked table

| # | Project / standard | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **BagIt** (RFC 8493) + `LibraryOfCongress/bagit-python` **[V]** | Filesystem convention for a self-verifying transfer package: `data/` payload + manifests with checksums + `bag-info.txt` tags. Library creates, validates, reports specific failures. | CC0 **[V]** | 510 commits, 263★, Py3 **[V]** | W-6 per-graduate export; §11.1 program export; "tested like a restore" | **adopt** |
| 2 | **BagIt Profiles** 1.4.0 (2023-01-13) + `bagit-profiles/bagit-profiles-validator` (`bagit_profile`) **[V]** | A JSON *contract* stating which tags, manifests, algorithms and structure a bag must have; a single-file Python validator that pairs with bagit-python. Spec purpose: "allow creators and consumers of Bags to agree on optional components." | CC0 (spec) **[V]** | spec v1.4.0; validator on PyPI **[V]** | W-6 "a lane opened without a written exit is invalidly opened" — the profile *is* the written exit, and it is machine-checkable | **adopt** |
| 3 | **Frictionless Data Package / Table Schema** `frictionlessdata/datapackage` **[V]** | `datapackage.json` beside the CSVs declaring resources, field types, constraints, keys. Spec is a data-definition language, not a runtime. | **Unlicense** (public domain) **[V]** | 1358 commits, 580★, NLnet/NGI0 funded **[V]** | §11.1 "documented schema" — makes the schema travel *inside* the export instead of living in `docs/` | **adopt** |
| 4 | **ArchivesSpace `rights_statement` schema** `archivesspace/archivesspace` **[V]** | Fields verified by raw fetch: `rights_type`, `status`, `determination_date`, **`start_date`, `end_date`**, `license_terms`, **`statute_citation`**, **`jurisdiction`** (ISO 3166), `other_rights_basis`, `external_documents`, **`acts`**, `linked_agents`, `notes`. | ECL-2.0 **[V]** | 15,801 commits, 433★ **[V]** | Sealed lanes (W-3), FERPA restriction expiry, §10 retention rows, §7.1 dated predicates | **steal the idea** (the app itself is JVM+MySQL+Solr — far too heavy) |
| 5 | **protobuf `reserved`** + `bufbuild/buf breaking` + `obi1kenobi/cargo-semver-checks` **[V]** | Three worked forms of "you may not remove an entry without accounting for it." Protobuf: on deleting a field you *"**must** reserve the deleted field number"* and *"should also reserve the field name"*; the guide lists *"deleting a field and not reserving the number"* as a defined hazard. buf: `buf breaking --against '.git#branch=main'`, categories FILE/PACKAGE/WIRE/WIRE_JSON. cargo-semver-checks: rustdoc-JSON diff against a baseline, `function_missing` lint, **exit code 100** on violation, GH Action, deny/warn levels. | Apache-2.0 / Apache-2.0 / Apache-2.0-OR-MIT **[V]** | 11.3k★ / 1.7k★ **[V]** | §11.1 "removing an entry without accounting for it fails CI"; item 20 tombstones; §16 allowlist rot | **adopt the shape** |
| 6 | **age** `FiloSottile/age` **[V]** | Small explicit keys, no config, no PKI, multiple recipients, passphrase mode, one documented format (`age-encryption.org/v1`), independent implementation (`rage`), v1.3.0+ post-quantum recipients. | BSD-3-Clause **[V]** | 23k★ **[V]** | W-6 "keys issue to its subject or named successor"; §5 escrow; item 2 (grants never committed) | **adopt** |
| 7 | **siegfried** `richardlehane/siegfried` **[V]** | Signature-based format identification; single static Go binary; PRONOM + freedesktop MIME-info + LoC FDD (beta) + Wikidata (beta); YAML/CSV/JSON/DROID-CSV out; MD5/SHA1/SHA256/SHA512/CRC. v1.11.6. | Apache-2.0 **[V]** | 269★, released 2026 **[V]** | Export-time format identification + fixity of the media directory; the "original audio" claim in the exit line | **adopt** (pin the signature file; `sf -update` is network egress) |
| 8 | **MADR** `adr/madr` **[V]** | Template front-matter verified by raw fetch: `status: "{proposed \| rejected \| accepted \| deprecated \| … \| superseded by ADR-0123}"`, `date:`, `decision-makers`, and a **Confirmation** section asking *"Is there any automated or manual fitness function?"* | MIT + CC0-1.0 **[V]** | 2.4k★ **[V]** | §16 document death; item 20 tombstone (status first, successor named); item 19 (the fitness-function prompt is §10's mutation rule in a doc template) | **adopt** |
| 9 | **lychee** `lycheeverse/lychee` **[V]** | Rust link checker for md/html/rst/text; CLI, library, GH Action; **exit 2** when a non-excluded link fails. | Apache-2.0 OR MIT **[V]** | 3.8k★, 2129 commits **[V]** | §16 tombstone rule 5 ("kept only so references do not dangle") — the *only* cheap way to prove the stub is still doing its job | **adopt** |
| 10 | **`dwc:disposition`** (Darwin Core) `tdwg/dwc` **[V]** | Verified by raw fetch of `vocabulary/term_versions.csv`: current term version dated **2026-05-26**, *"A current state of a dwc:MaterialEntity with respect to where it can be found"*; the 2007 curatorial version carries examples **`"in collection"`, `"missing"`, `"voucher elsewhere"`**. Darwin Core Archive (Text Guide) = `meta.xml` + CSVs. | CC-BY-4.0 **[V]** | TDWG, 1083 commits **[V]** | Item 20 tombstone for a **transferred** lane; §16's (old reference, new location) pair | **steal the idea** — this is the best single word I found all session |
| 11 | **SIARD 2.2** `DILCISBoard/SIARD` + **DBPTK** `keeps/db-preservation-toolkit` + **DBVTK** `keeps/dbptk-ui` **[V]** | SIARD = ZIP containing `metadata.xml`, XSDs, and per-table XML; explicitly *"independent of proprietary dump formats."* SIARD 2.2 dated 2021-08-31; also 2.1.1/2.1/2.0/1.0. DBPTK converts DBs → SIARD 1/2/DK. DBVTK is a SIARD 2 browser. | SIARD spec: DILCIS/SFA; DBPTK + DBVTK **LGPLv3** **[V]** | SIARD repo quiet (122 commits, 12★); DBPTK 1610 commits; DBVTK 1388 commits **[V]** | §11.1 "data readable without the app" — the *strongest existing prior art* for the whole clause | **steal the idea** (see caveat: DBPTK's listed sources are JDBC — MySQL/Postgres/Oracle/SQLServer/Access/OpenEdge/Sybase — **SQLite is not named**; DBVTK needs Solr) |
| 12 | **factur-x** `akretion/factur-x` **[V]** | Embeds a structured XML file *inside* a PDF/A-3 so the human-readable and machine-readable copies cannot be separated. Standards: Factur-X, ZUGFeRD 2.x, EN 16931, PDF/A-3. | BSD **[V]** | 302★ **[V]** | §11.1 "PDF per student record" — the trick that stops the PDF from becoming a dead end | **adopt the pattern** |
| 13 | **OCFL 1.1** `OCFL/spec` **[V]** | Preservation-centric filesystem/object-store layout: versioned object directories, an inventory, fixity; designed so a repository can be reconstructed from storage. | not stated on the page I fetched — **unverified** | v1.1 current; 431 commits, 67★ **[V]** | The **media directory** layout and per-lane versioning; §5 canonical-store-read-only | **steal the idea** |
| 14 | **RO-Crate** `ResearchObject/ro-crate` **[V]** | `ro-crate-metadata.json` (JSON-LD / schema.org) describing files *and* contextual entities — people, organisations, licences, provenance. | spec Apache-2.0; contexts CC0 **[V]** | 2133 commits, 155★, 2019–2025 **[V]** | A richer alternative to #3 if the export must describe *people and consent state*, not just tables | **steal the idea** |
| 15 | **E-ARK CSIP** `DILCISBoard/E-ARK-CSIP` + **commons-ip** `keeps/commons-ip` **[V]** | European archival information-package spec (METS profile, OAIS-aligned). commons-ip is a Java library + CLI that **validates and creates** E-ARK IP 1/2.0.4/2.1.0/2.2.0, **BagIt**, and Hungarian type-4 SIP. | CSIP CC-BY-4.0; commons-ip LGPLv3 **[V]** | 1090 commits / 587 commits **[V]** | Proof that "validate the transfer package in CI" is normal archival practice, with an existing multi-format validator | **read-only interest** (JVM; BagIt+profile is the cheaper 90%) |
| 16 | **Timelinize** `timelinize/timelinize` **[V]** | Personal data archive. Quote verified: *"All the data you import is indexed in a SQLite database and stored on disk organized by date — no obfuscation or proprietary formats; you can simply browse your files if you wish."* | AGPL-3.0 **[V]** | 3.6k★ **[V]** | The **exit-line prose model** — someone already wrote the sentence §11.1 wants | **steal the sentence** (and its honesty caveat: schema unstable, keep originals) |
| 17 | **sqlite-utils** `simonw/sqlite-utils` **[V]** | CSV/TSV/JSON in and out, schema inspection, `sqlite-utils memory` to query CSVs directly; pip install, no server. | Apache-2.0 **[V]** | 2.1k★, 1176 commits **[V]** | The literal implementation of `terpsi export --all` writing CSV per table | **adopt** |
| 18 | **SQLite as a LoC-recommended storage format for datasets** **[S]** | The Library of Congress Recommended Formats Statement lists SQLite alongside XML/JSON/CSV as a preferred format for datasets. | n/a | LoC RFS updated 2025-2026 **[S]** | §11.1's central format bet, with an external authority behind it — worth citing in the exit line | **cite it** (fetch `sqlite.org/locrsf.html` and the RFS PDF to confirm before quoting) |
| 19 | **conftest** `open-policy-agent/conftest` **[V]** | Rego policies over structured config files; fails CI. | open source, 3.2k★ **[V]** | Retention/disposition schedule as YAML, enforced in CI (see §"the gap" below) | **adopt** |
| 20 | **Archivematica** `artefactual/archivematica` **[V]** | Standards-based OAIS preservation system; AIPs, format policy registry, separate Storage Service. | AGPLv3 **[V]** | active; Artefactual paid support offered **[V]** | The reference implementation of ingest→AIP→DIP | **read-only interest** — dashboard + MCPServer + MCPClient + Storage Service + FPR is not a booster's box |
| 21 | **AtoM** `artefactual/atom` **[V]** | Archival description and public access, commissioned by the ICA. | AGPLv3 **[V]** | 297★, 3895 commits **[V]** | Access/use-conditions modelling; a possible *reading room* for a dissolved program's records | read-only interest (PHP/Symfony + search backend) |
| 22 | **RiC-O 1.1** (May 2025) `ICA-EGAD/RiC-O` **[V]** | ICA's OWL2 ontology for archival records and their layers of context. | ICA **[V]** | 759 commits, 66★ **[V]** | Formal vocabulary if the export ever needs to be described to another archive | read-only interest |
| 23 | **veraPDF** `veraPDF/veraPDF-library` **[V]** | "Industry supported, open source PDF/A validation library." Java 8+. | GPLv3+ / MPLv2+ **[V]** | 338★ **[V]** | Validating the per-student PDF/A actually *is* PDF/A — in CI, not on the box | steal the idea |
| 24 | **PDS4 Information Model** `NASA-PDS/pds4-information-model` **[V]** | The model from which PDS4 XML labels and schemas are generated; labels sit beside the data files. | Apache-2.0 **[V]** | 14★, 43 open issues, CI/CD **[V]** | The "label beside every file, generated from one model" discipline | steal the idea |
| 25 | **GEDCOM 7** `FamilySearch/GEDCOM` **[V]** | The official FamilySearch spec for exchanging genealogical data between mutually hostile applications. | Apache-2.0 **[V]** | 619 commits, 269★, 111 open issues **[V]** | Prior art for a *lifelong personal record* that outlives every app that held it | read-only interest (GEDZIP media packaging **not confirmed** — I could not fetch `gedcom.io`) |
| 26 | **Perkeep** `perkeep/perkeep` **[V]** | Content-addressed personal storage; "Keep your stuff for life." | Apache-2.0 **[V]** | 7.2k★, 389 open issues **[V]** | Personal digital archiving posture | read-only interest |
| 27 | **MinIO** `minio/minio` **[V]** | S3-compatible object store, was the standard on-prem WORM/Object-Lock answer. | AGPLv3 **[V]** | **ARCHIVED 2026-04-25, read-only; maintainers moved to AIStor Free / AIStor Enterprise** **[V]** | §11.1's Delisted section — a *live, dated* sovereignty regression found while scouting | **do not adopt — use as the worked example** |
| 28 | **BorgBackup** `borgbackup/borg` **[V]** | Deduplicating backup, 256-bit authenticated encryption (AES-OCB / chacha20-poly1305). | BSD-3-Clause **[V]** | 13.6k★; **README warns "DO NOT USE BORG2 FOR YOUR PRODUCTION BACKUPS"** **[V]** | §11 3-2-1 backups | read-only interest; append-only mode **not confirmed** on the page I fetched |
| 29 | **Kubernetes deprecation policy** (`kubernetes/website`) **[V]** | A written, versioned deprecation policy with different removal windows per stability track (GA/beta/alpha), enforced by API versioning. | CC-BY-4.0 **[V]** | live doc **[V]** | Item 20's "why the stub still exists" as a *policy with durations*, not a per-case judgement | steal the idea |
| 30 | **GitHub Archive Program** `github/archive-program` **[V]** | 186 film reels of every active public repo as of 2020-02-02 in Svalbard permafrost, plus the **Tech Tree**: *"a collection of technical works which document and explain the layers of technology on which today's open-source software relies."* Inspired by Long Now's Manual for Civilization. | repo public **[V]** | active **[V]** | The idea that an archive ships **its own reading instructions** | see "weirdest" below |

---

## The gap I could not close: retention/disposition schedules as data or code

I looked for an open-source project that expresses a records-retention schedule as machine-readable data —
record series, trigger event, retention period, disposition action, authority citation — and did not find one.
The GitHub repository search I could run (`"retention schedule" disposition yaml`) returned **0 results [V]**.
The two candidates I could check are weak: `nuxeo/nuxeo-retention` **[V]** is a heavy platform addon (4★,
lts-2023 branch) and MinIO's Object Lock path is now archived **[V]**.

**So this is a build, not an adopt — but you do not have to invent the row shape.** ArchivesSpace's
`rights_statement` **[V]** already carries nearly the whole thing: `rights_type` (statutory / licence / other),
`statute_citation`, `jurisdiction`, `start_date`, `end_date`, `determination_date`, plus `acts` (which acts are
permitted, by whom, until when) and `notes`. Add a `trigger` field (graduation, season close, last activity)
and a `disposition` field drawn from `dwc:disposition`'s vocabulary shape and you have a schedule row that
`conftest` **[V]** can lint and that a purge job can read. Cost: a YAML file, a Rego policy, a CI step —
call it a day of work, no runtime dependency, no staff.

This also satisfies item 13 directly: a schedule row whose backend errored returns `unknown`, and `unknown`
must never authorise a purge.

---

## Top finds, with the concrete transplant

### 1. BagIt + a BagIt Profile is the whole of W-6, and it makes "invalidly opened" enforceable

The clause that has no implementation anywhere in §14 is W-6, and the reason is that it is stated as a
*runtime* obligation ("every June, per graduate, unattended") when it is really a *contract* obligation.
BagIt Profiles is exactly that contract. A profile is JSON: it names required `bag-info.txt` tags, required
manifest algorithms, and the permitted payload structure, and its stated purpose **[V]** is to let the creator
and the consumer of a bag "agree on optional components." `bagit_profile` **[V]** is a single-file Python module
that validates a bag against a profile and is built to sit next to `bagit-python` **[V]**, which is CC0 — so
neither introduces a licence question and neither runs a daemon.

**Transplant.** Write `profiles/graduate-lane-v1.json` and commit it. Require tags that make the export a
record rather than a dump: `Lane-Subject-Id`, `Exit-Threshold-Date`, `Key-Recipient` (the subject or the named
successor — W-6's two options and no third), `Seal-State-Manifest`, `Schema-Version`, `Retention-Authority`,
`External-Description`. Then two tests, both mutation-shaped per §10 and item 19: one that builds a graduate's
bag and asserts `bagit_profile` accepts it, and one that **deletes a required tag and asserts the enrolment
path refuses to open the lane**. That second test is the literal encoding of *"a lane opened without a written
exit is invalidly opened"* — enrolment calls the same validator against a *dry-run* export, so a student
cannot be enrolled unless their exit already validates. This is the single highest-leverage thing in this
report and it is the cheapest: two pip installs, one JSON file, two tests. There is no server, no JVM, no
index.

One honest note: it turns W-6 from a June job into a **per-enrolment gate**, which means the export routine
must exist before the first student row. That is what §11.1 says ("write the exit line before the first
install"), stated as code.

### 2. Data Package makes "the schema is documented" a file instead of a promise

§11.1's target line says *"the schema is documented in `docs/`."* That sentence is a pair without a middle
(§16): the docs and the database can drift, and if the program dissolves, `docs/` is in a git repo nobody
kept. Frictionless's `datapackage.json` **[V]** — **Unlicense, public domain [V]**, so it can be embedded and
restated freely — puts the field names, types, constraints and keys **inside the export**, next to the CSVs
they describe. It is the same instinct as SIARD's `metadata.xml` **[V]** and PDS4's labels **[V]**, at a tenth
of the weight.

**Transplant.** `terpsi export --all` writes `data/*.csv` + `datapackage.json`, and CI asserts that the
`datapackage.json` was **generated from the live schema**, not maintained by hand — otherwise you have created
exactly the canonical/vendored pair §16 forbids. The middle here is a generator plus a test that mutates a
column name in the schema and asserts the export test goes red. `sqlite-utils` **[V]** gives you the CSV side
of this in one command and is Apache-2.0, pip-installable, no server. Cost: a few hours; no runtime
dependency on the box.

### 3. ArchivesSpace's rights statement is the sealed-record model, already normalised

Archives have been describing "closed until 2043, under this statute, in this jurisdiction, and here is who
may nevertheless see it" for a century, and ArchivesSpace has that as a JSON schema I read directly **[V]**:
`rights_type`, `status`, `determination_date`, `start_date`, `end_date`, `statute_citation`, `jurisdiction`
(ISO-3166 enum), `other_rights_basis`, `acts`, `linked_agents`, `external_documents`, `notes`.

**Transplant.** Adopt that field list for lane sealing, guardianship termination (§7.1), and FERPA retention
rows, because it gets four things right that a hand-rolled model usually misses: the **basis is cited**
(`statute_citation` — so "why is this sealed" is answerable without asking a human), the **jurisdiction is
named** (§7.4's no-apex clause in a column), the restriction has **both** a start and an end date (so a
restriction that has *expired* is visibly different from one that never existed — item 13), and the
permissions attach to **acts** rather than roles (§7.2's "narrate the read, gate the export" is two acts with
different rules, which this shape expresses natively). Do **not** install ArchivesSpace; it is JVM + MySQL +
Solr. Copy the schema, which is free.

### 4. `reserved`, `buf breaking`, and `cargo-semver-checks` are the CI shape for item 20

§11.1 asks for the Delisted discipline: removing an entry without accounting for it fails CI. Three
communities solved this and I verified all three. Protobuf is the purest: the proto3 guide **[V]** says on
deleting a field you *"**must** reserve the deleted field number"* and *"should also reserve the field name,"*
and lists *"deleting a field and not reserving the number"* among the named hazards. The `reserved` keyword
**is** item 20's tombstone — status first (the identifier is marked dead), the reason implicit in its
presence, and the slot cannot be silently reused. `buf breaking --against '.git#branch=main'` **[V]** makes it
a CI gate with categories (FILE/PACKAGE/WIRE/WIRE_JSON), and `cargo-semver-checks` **[V]** shows the general
mechanism: diff the current surface against a *baseline*, emit a `*_missing` lint, **exit 100**, with per-lint
deny/warn configuration.

**Transplant.** One `lists.yml` holding every entry that may not silently vanish — the egress allowlist, the
component map's Exists column, the pairs-and-middles table, the delisted-dependency log, retired document
paths. A `tombstones.yml` with the five §16 fields per entry. Then a CI check that diffs `lists.yml` against
the merge base and fails unless every removal has a matching tombstone whose successor resolves. Add `lychee`
**[V]** (Apache-2.0-OR-MIT, single binary, **exit 2** on a dead non-excluded link) to prove the retired paths
still resolve — that is §16 tombstone rule 5, "kept only so references do not dangle," turned into a check
rather than an intention. Note the failure mode this must be mutation-tested against, because it is the exact
shape §16 rule 5 warns about: an accounting check that passes because it is reading a list nobody updates.
Cost: two YAML files, one script, one binary in CI.

### 5. `age` is how the keys actually issue to the subject

W-6 says *"keys to the lane issue to its subject or named successor."* Every heavier answer — X.509, GPG,
an account at anything — fails the five-point test on the first two criteria. `age` **[V]** is BSD-3-Clause,
has **small explicit keys**, **no config options**, one documented format (`age-encryption.org/v1`), an
independent implementation (`rage`), multiple recipients per file, a passphrase mode for the case where the
graduate has no key at all, and post-quantum recipients since v1.3.0.

**Transplant.** The graduate's bag is `age`-encrypted to two recipients: the subject's public key, and the
escrow key from §5. Passphrase mode is the fallback for an 18-year-old with no keypair, printed once on paper
at handover — which is also the honest answer for §5's escrow gap. Refuse to build a bag with zero recipients
(that is item 13: a missing recipient is `unknown`, never "no encryption"). Cost: one static binary; the
recipient list is grant material, so per item 2 it never enters the tree.

### Two more worth a paragraph

**`dwc:disposition` [V] is the vocabulary for a transferred lane.** Museum collections management needed a word
for "this specimen is no longer here, and here is where it went," and Darwin Core's 2007 curatorial term
version gives the examples verbatim: `"in collection"`, `"missing"`, `"voucher elsewhere"`. The current
version (term dated 2026-05-26 **[V]**) generalises it to "a current state of a material entity with respect
to where it can be found." That is precisely the stub left behind after a graduate's lane transfers out, and
it distinguishes the three states item 20 needs kept apart: *held here and authoritative*, *transferred, the
authoritative copy is elsewhere and named*, and *we do not know* — which item 13 requires be sayable and which
"deleted" cannot say. Adopt the three-state vocabulary; the `disposition` column on the lane stub costs
nothing and answers "where did this record go" for a district auditor five years later.

**SIARD [V] is the best prior art for the exit clause, and the reason not to adopt it.** SIARD exists to do
exactly what §11.1 demands: a ZIP containing `metadata.xml`, XSDs, and per-table XML, explicitly *"independent
of proprietary dump formats,"* developed by the Swiss Federal Archives and now at 2.2 (2021-08-31) **[V]**.
Read the spec; it is the argument that the exit clause is achievable and normal. But do not build on the
toolchain: DBPTK **[V]** is LGPLv3 Java over JDBC and its listed sources are MySQL/Postgres/Oracle/SQL
Server/Access/OpenEdge/Sybase — **SQLite is not among them**, which is the one database this project has — and
DBVTK **[V]** needs a Solr backend, which is a service a booster cannot run. The transplant is the *file
layout*: schema description and data in one package, validatable, with the description generated from the
same source as the data.

---

## Draft: what the honest exit line should say

§11.1 offers a target line and then says the crucial thing — *"if that sentence cannot be written honestly,
that is the finding."* It cannot be written yet, and four specific claims in it are false or unproven today.
Here is the line I think is honest, followed by what it costs to earn it.

> **Leaving Terpsi.**
> Your program's records are SQLite database files — one per store — plus a media directory of the original
> audio and image files as they were captured. SQLite is a Library of Congress recommended storage format for
> datasets; the media files are in their original formats, identified and checksummed at export.
>
> `terpsi export --all` writes, into a single directory you can copy to any disk:
> `data/` — one CSV per table; `datapackage.json` — the field names, types and keys of every one of those
> tables, generated from the live database, not hand-maintained; `records/` — one PDF per student record, each
> with that student's own CSV embedded inside the PDF file, so the printable copy and the machine-readable copy
> cannot be separated; `media/` — the original audio and images, unmodified, with a checksum manifest and a
> format-identification report; `manifest-sha256.txt` and `bag-info.txt` — so anyone can verify nothing was
> lost or altered in transit, using any BagIt tool.
>
> `terpsi export --lane <student>` does the same for one student: their whole history, encrypted to their own
> key or, if they have none, to a passphrase handed over on paper. Every graduate's export is validated at the
> moment they are **enrolled**, not at graduation — a lane we could not export is a lane we will not open.
>
> **What this software is still needed for:** nothing, to read any of the above. Reading a CSV needs a
> spreadsheet. Reading the SQLite files needs any of a dozen free tools. Reading the PDFs needs a PDF reader.
> Reading the audio needs a media player.
>
> **What is honestly not free of us:** the records at rest are encrypted, so **the export is readable only if
> you hold the key** — see `docs/ESCROW.md` for where yours is and how to prove you can still use it; a key
> you cannot demonstrate today is a key you do not have. Judge commentary transcripts are marked `draft` or
> `sealed` in the export and the distinction is carried through; a draft transcript is not a record and the
> export says so. Text-message notification uses a gateway that may be a paid service; if it lapses, every
> record in this list is unaffected and nothing stops working except the texts.
>
> Last verified by restoring a full export on a machine with no Terpsi installed: **{date}**. If that date is
> more than a season old, this notice is a claim and not a fact.

**The four things that make the §11.1 target line dishonest today, and what each costs:**

1. **"one SQLite file per store"** is not readable if §5's at-rest sealing is doing its job. Any exit line
   that omits the key is false. Fix: name the key and the escrow *in the line*, and make the last-verified
   restore date part of it. Cost: mostly writing; the escrow gap itself is §14's largest open item and is not
   mine to close.
2. **"CSV per table"** is not a student record under W-1/W-3. A lane is scattered across every table, and a
   rehearsal is one entry per student, so `attendance.csv` is not the graduate's attendance. Fix: `--lane`
   assembles per-subject, and the per-student PDF is the human-facing artifact. Cost: real work, and it is
   the work W-6 was always asking for.
3. **"and the original audio"** is unverifiable without format identification. Fix: siegfried at export,
   report in the bag. Cost: one pinned binary. Note the pin matters — `sf -update` is network egress and would
   walk into §6.
4. **"the schema is documented in `docs/`"** is a pair with no middle. Fix: `datapackage.json` generated into
   the export, with a mutation test. Cost: hours.

And one addition §11.1 does not ask for but the Delisted caution implies: a **dated dependency log** in the
repo, one row per external dependency with its licence, its last-checked date, and its status. I found a live
example while scouting: `minio/minio` was **archived read-only on 2026-04-25 [V]**, its maintainers moved to
"AIStor Free" and "AIStor Enterprise," and any install that had leaned on it for on-prem object storage has
regressed on *survives the vendor* without anyone editing a line of code. That is the regression §11.1
describes, it happened three months ago, and nothing in a normal build would have said so out loud.

---

## Weirdest things I found

1. **`dwc:disposition` — museum collections gave me the word `"voucher elsewhere"` [V].** Biodiversity
   informatics needed to say "the specimen is not here; the authoritative one is over there" and standardised
   it as a term, with the current version dated 2026-05-26. Software says "deleted" or "archived" and loses
   the distinction. Three states — held, elsewhere-and-named, unknown — is the whole of item 20's tombstone in
   one controlled-vocabulary field, borrowed from people who catalogue pressed plants.

2. **The GitHub Archive Program ships a Tech Tree [V].** Alongside 186 film reels in Svalbard permafrost is
   *"a collection of technical works which document and explain the layers of technology on which today's
   open-source software relies"* — explicitly modelled on the Long Now Foundation's Manual for Civilization.
   The insight is not the film: it is that **the archive contains its own reading instructions**. Directly
   transplantable and nearly free — the graduate's bag should contain a plain-text `README.txt` written to a
   stranger, not a `docs/` link, because the link is the first thing to die.

3. **Factur-X: European e-invoicing solved "one file, two audiences" and nobody in records management
   noticed [V].** PDF/A-3 permits embedded files, so an invoice is simultaneously a printable page and its own
   machine-readable XML. A BSD-licensed Python library does it in a few lines. Applied here: a graduate's PDF
   record *contains* their CSV. You cannot hand someone the pretty version and lose the data version, because
   they are the same file. I went looking for this in digital-preservation projects and found it in accounts
   payable.

4. **MADR's template asks the §10 question in its own front matter [V].** A markdown ADR template — from the
   architecture-documentation world, nothing to do with archives — includes a **Confirmation** section reading
   *"Is there any automated or manual fitness function?"* right beside `status: superseded by ADR-0123`. That
   is item 19 and item 20 in one file, in a template with 2.4k stars that predates this project's whole
   discussion of middles.

5. **The strongest match for §11.1 in the world is a Swiss government database format from an archiving
   project that started in 2000 [V].** SIARD came out of the Swiss Federal Archives' ARELDA programme **[S]**,
   its purpose statement is almost word-for-word §11.1's "readable without the app," and it is at version 2.2
   with a spec repo that has 12 stars and 122 commits. The clause this project treats as an unusual
   requirement has been a national archive's standing policy for twenty-five years — and the toolchain around
   it still cannot read SQLite **[V]**.

**Honourable mention, unverifiable in this session.** Four leads I could not fetch and therefore will not
dress up as findings, all **[K]**: the WIPP / Human Interference Task Force literature on markers meant to be
legible in 10,000 years (the relevant question for a tombstone: what survives when the *language* of the
warning dies); **RUFADAA**, the US uniform act on fiduciary access to digital assets, which is the legal
machinery for "keys to a named successor" and would tell you what a court expects that handover to look like;
the **CREW/MUSTIE** manual from library de-selection, which is the only appraisal rubric I know of written for
a single unstaffed practitioner deciding what to discard; and **medical practice-closure statutes**, which in
several US states require a *named custodian of records*, *notice to patients*, and a *retention period that
outlives the practice* — the closest legal analogue in existence to "the booster dissolves." All four are
worth a follow-up session with a working search budget; the practice-closure statutes in particular look like
they encode the exact obligation §11.1 is reasoning toward from first principles.
