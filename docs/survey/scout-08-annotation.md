# Scout 08 — Annotation models: time-anchored, addressed, attributed, and *disagreeing*

**Slice:** data models and formats for time-anchored, addressed, attributed annotation — and for structured
disagreement between annotators. Feeds `docs/ARCHITECTURE.md` §8.1 (Commentary is the primitive) and §8.2
(a transcript is a `draft` until a named human seals it).

**Method note / honesty about verification.** The session's WebSearch budget was already exhausted (200/200,
shared across scouts) early in this run, and the agent proxy blocks `w3.org`, `tei-c.org`, `cidoc-crm.org`,
`sparontologies.github.io`, `arxiv.org`, `docs.argilla.io` and most other spec hosts. **GitHub raw + the GitHub
API were reachable**, so nearly every claim below is verified by reading actual spec source or actual code, not
a README. Where a claim rests on a search snippet or could not be checked at all, it says so in the row.
Nothing here is asserted from memory alone.

---

## 1. Ranked table

Verdict key: **adopt** = take into the schema/vocabulary now · **steal-the-idea** = copy the mechanism, not the code ·
**read-only-interest** = worth knowing, do not depend on.

| # | Project / spec | What it is | License | Activity (verified) | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **MEI — `<annot>` + `MEI.performance`** ([music-encoding/music-encoding](https://github.com/music-encoding/music-encoding)) | Music-notation schema. `<annot>` already carries anchor+span+addresses+attribution; `MEI.performance` bridges score position ↔ recording time | ECL-2.0 (Educational Community License, Apache-shaped) | 236★, pushed **2026-07-24** | The whole of §8.1's `Commentary` block, minus the audio body | **adopt** (as column names + a Schematron-style constraint set) |
| 2 | **EMA / Music Addressability API** ([music-addressability/ema](https://github.com/music-addressability/ema), spec at [umd-mith/ema/docs/api.md](https://github.com/umd-mith/ema/blob/master/docs/api.md)) | A URL-path grammar for "virtually circling" a passage: measures / staves / beats, with a BNF | Spec header says **CC-BY 2015**; impl repos are `NOASSERTION` | Spec v1.0.0 Draft; org repos last pushed 2021–2023 (**dormant**) | `anchor` + `span` + `addresses` as one parseable string | **adopt** (the grammar; not the code) |
| 3 | **W3C Web Annotation Data Model** ([w3c/web-annotation](https://github.com/w3c/web-annotation)) | W3C Rec: `body`/`target`/`motivation`, 8 Selector types, 2 State types, `refinedBy`, `creator` vs `generator` | W3C royalty-free / permissive doc licence | Rec since 2017, stable (not "active" — finished) | `addresses`, and **the `draft`/`sealed` distinction in disguise** | **adopt** (vocabulary) |
| 4 | **CiTO 2.8.2** ([SPAROntologies/cito](https://github.com/SPAROntologies/cito)) | Citation Typing Ontology. A *graded* disagreement family, every relation with a named inverse | **CC-BY 4.0** | `owl:versionIRI .../2026-06-22`, repo updated 2026-06-29 — **live** | The upgrade to `contradicts_or_tensions_with` | **adopt** (take the names verbatim) |
| 5 | **DICOM SR flags** (verified via [ImagingDataCommons/highdicom](https://github.com/ImagingDataCommons/highdicom) `src/highdicom/sr/sop.py`) | `CompletionFlag` PARTIAL\|COMPLETE **and** `VerificationFlag` UNVERIFIED\|VERIFIED, orthogonal; VERIFIED *cannot be set* without a named verifier + organization | highdicom MIT; DICOM standard freely published | highdicom active | §8.2 `draft`/`sealed`/`pending` — and rule #18 (enforcement, not ledger) | **steal-the-idea** |
| 6 | **TEI critical apparatus** (`textcrit` module, [TEIC/TEI](https://github.com/TEIC/TEI)) | `<app>`/`<lem>`/`<rdg>`/`<rdgGrp>`/`<witDetail>`, `@wit`, `@type=substantive\|orthographic`, `@cause`, `@varSeq`, `@resp` | **dual CC-BY + BSD-2** | 344★, pushed **2026-07-28** | Three judges on one passage, as a first-class *apparatus entry* | **steal-the-idea** (strongly) |
| 7 | **Argilla response model** ([argilla-io/argilla](https://github.com/argilla-io/argilla)) | `ResponseStatus = draft \| submitted \| discarded` (+ virtual `pending`); machine `suggestions` separate from human `responses`; `distribution.min_submitted` | **Apache-2.0** | 5,063★, pushed 2026-07-29 — very active | §8.2's four states, already an enum in production | **steal-the-idea** |
| 8 | **PROV-O** (W3C Rec; verified via many `prov.ttl` copies incl. [RDFLib/pyLODE](https://github.com/RDFLib/pyLODE)) | `wasDerivedFrom`, `wasAttributedTo`, `wasRevisionOf`, `hadPrimarySource`, **`wasInvalidatedBy` / `invalidatedAtTime` / `qualifiedInvalidation`→`prov:Invalidation`** | W3C permissive | Rec 2013, stable | `derived_from`; **and refusal #3 — `invalid_at`, with a named invalidating act** | **adopt** (vocabulary only) |
| 9 | **Nanopublications** ([Nanopublication/nanopub-java](https://github.com/Nanopublication/nanopub-java)) | Assertion / provenance / pubinfo as three named graphs, keypair-signed; retraction is a *new signed nanopub* via `npx:retracts` | Apache-2.0 | Active (RDF4J-based) | Rejection recorded as durably as approval; `NESTOR_SEAL_KEY` analogue | **steal-the-idea** |
| 10 | **DKPro Statistics Agreement** ([dkpro/dkpro-statistics](https://github.com/dkpro/dkpro-statistics)) | `UnitizingAnnotationStudy(raters, begin, end)` + `addUnit(offset, length, rater, category)` + `KrippendorffAlphaUnitizingAgreement` | **Apache-2.0** | 13★, pushed 2026-07-11 | **Measures `reject_match`**: disagreement about *where the span is*, not what the label is | **adopt** (as a one-off analysis tool) |
| 11 | **BORIS** ([olivierfriard/BORIS](https://github.com/olivierfriard/BORIS)) | Ethology event-logger. SQLite-backed event store; point vs state events, subjects, modifiers; IRR plugins (weighted/unweighted Cohen's κ, ±modifiers, time-binned); **Needleman-Wunsch** observer-sequence similarity; CLI | **GPL-3** | 242★, pushed 2026-07-22; IRR plugins dated **2026-01-30**; 2,834 citations | Two judges coded the same recording — how do you compare them? | **steal-the-idea** |
| 12 | **INCEpTION curation** ([inception-project/inception](https://github.com/inception-project/inception)) | N annotators produce independent documents; a curator merges into a distinguished `CURATION_USER`; `SourceDocumentState.CURATION_IN_PROGRESS / CURATION_FINISHED`; pluggable `MergeStrategyFactory`, incl. `ThresholdBasedMergeStrategyFactoryImpl` | **Apache-2.0** | 708★, pushed 2026-07-28 | Refusals #10 + #11: adjudication is a *human act producing a distinct record* | **steal-the-idea** |
| 13 | **JAMS** ([marl/jams](https://github.com/marl/jams)) | JSON music-annotation format: `file_metadata` / `annotations[]` / `sandbox`; **multiple annotations per file per namespace**; `annotation_metadata` = `curator{name,email}`, `annotator`, `annotation_tools`, `annotation_rules`, `validation`, `data_source` | **ISC** | 204★; format stable, low churn | Per-judge annotation sets over one `Recording`, with rubric provenance | **steal-the-idea** |
| 14 | **OpenTimelineIO** ([AcademySoftwareFoundation/OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)) | `Marker(marked_range: TimeRange, color, comment, metadata)`; `marked_range` is **relative to the owning Item**; every object carries `OTIO_SCHEMA` name+version with `register_upgrade_function` migrations | **Apache-2.0** | 1,938★, pushed 2026-07-29 | Anchors that survive re-editing; a format that outlives the app (§16) | **steal-the-idea** |
| 15 | **CRMinf 1.2.1** (CIDOC CRM Argumentation Model) | `I1 Argumentation`, `I2 Belief`, `I5 Inference Making`, **`I7 Belief Adoption`**, `I6 Belief Value`, `J5 holds to be` | CIDOC CRM terms (permissive) | v1.2.1 current | Provenance-vs-seal-state distinction (§15); belief held *because of trust in a source* | **read-only-interest** — *verified via search snippet only; cidoc-crm.org unreachable this session* |
| 16 | **Raven selection tables** (format; tooling verified via [maRce10/Rraven](https://github.com/maRce10/Rraven)) | Tab-delimited: `Selection, View, Channel, Begin Time (s), End Time (s), Low Freq, High Freq` + arbitrary annotation columns | Rraven **GPL ≥2**, CRAN v1.0.16 | Rraven on CRAN; format 20+ years in field use | The "readable without the app" ideal, in its dumbest and most durable form | **steal-the-idea** |
| 17 | **MELD** ([oerc-music/meld](https://github.com/oerc-music/meld)) | Framework: MEI + W3C Web Annotation as JSON-LD, addressing "musically meaningful score sections"; MELD 2.0 stores annotations in **Solid Pods** | BSD (© 2016 D. M. Weigl, Oxford e-RC) | 22★, updated 2026-03-06; meta-repo, impl split across 3+ repos | Exactly this problem, solved with an RDF+LDP stack | **read-only-interest** (stack cost fails the SQLite test) |
| 18 | **crowd-kit** ([Toloka/crowd-kit](https://github.com/Toloka/crowd-kit)) / **CrowdTruth** ([CrowdTruth/CrowdTruth-core](https://github.com/CrowdTruth/CrowdTruth-core)) | Truth inference from disagreeing annotators (Dawid-Skene, MACE, GLAD); CrowdTruth treats disagreement as signal, not noise | Apache-2.0 both | 252★ / 63★, both updated mid-2026 | **⚠ SA-3 HAZARD — see §3 below** | **read-only-interest, with a refusal attached** |
| 19 | **CollateX** ([interedition/collatex](https://github.com/interedition/collatex)) | Collates N witnesses into a variant graph / alignment table (Gothenburg model: tokenize→normalize→align→analyze→visualize) | **GPL-3** | 99★, updated 2026-07-22 | Aligning three judges' remark streams over one passage | **read-only-interest** (GPL-3 + JVM) |
| 20 | **pympi** ([dopefishh/pympi](https://github.com/dopefishh/pympi)) | Reads/writes **ELAN `.eaf`** and **Praat TextGrid**; zero dependencies; tier merge/filter, annotation shifting | (v1.71; license not verified) | Mature, low churn | Import path from any linguist's existing tooling; tier model = one lane per addressee | **steal-the-idea** (the tier model) |
| 21 | **Advene** ([oaubert/advene](https://github.com/oaubert/advene)) | Time-aligned video annotation with user-defined *schemas*; annotation "packages" exchangeable **independently of the video** | **GPL-2** (Zenodo DOI) | Long-running research tool | Sidecar-not-canonical (refusal #11) in a 20-year-old shape | **read-only-interest** |
| 22 | **LegalRuleML** (OASIS; schema/RDFS mirrored on GitHub) | `DefeasibleStrength`, `Override` — which of two conflicting norms prevails, and under what condition | OASIS standard | Stable standard | "This judge's remark supersedes that one" as an explicit, queryable edge | **read-only-interest** (heavyweight XML/RDF) |
| 23 | **SADFace** ([Open-Argumentation/SADFace](https://github.com/Open-Argumentation/SADFace)) | Simple Argument Description Format — argument graphs in plain JSON (the cheap alternative to AIF) | **GPL-3** | 4★, updated 2026-06-29 — thin | Attack/support edges without an RDF stack | **read-only-interest** (GPL-3, tiny community) |
| 24 | **segeval** ([cfournie/segmentation.evaluation](https://github.com/cfournie/segmentation.evaluation)) | Boundary-edit-distance segmentation comparison (B, S, boundary similarity) | **BSD** | Dormant | Second opinion on "did two judges mark the same boundary?" | **read-only-interest** |
| 25 | **ASReview** ([asreview/asreview](https://github.com/asreview/asreview)) | Active-learning systematic-review screening | Apache-2.0 | 960★, pushed 2026-07-29 | Screening loop; **not** a reconciliation model (single-reviewer oriented) | **read-only-interest** |

**Could not verify at all this session** (search budget gone, hosts blocked) — listed so nobody mistakes them for
findings: PanelCheck (sensory-panel performance software — no canonical OSS repo located), ISU figure-skating /
FIG gymnastics judging code or open score datasets, SCA Coffee Value Assessment forms, Wikidata statement ranks
(`deprecated` + reason-for-deprecation), IIIF AV, and "The Music Annotation Pattern" (arXiv 2304.00988 — appeared
in a search result, no repo found).

---

## 2. Top finds, with concrete transplant and cost

### 2.1 MEI `<annot>` + `MEI.performance` — the primitive is already a published schema

This is the find that should change §8.1. Read from
`source/modules/MEI.shared.xml` and `source/modules/MEI.performance.xml` on `develop`, MEI's `<annot>` element
composes exactly the terpsi `Commentary` block:

- **`span`, anchored to score position** — `att.startEndId` (`@startid`/`@endid`, pointing at note IDs) *and*
  `att.timestamp.log` (`@tstamp`, a beat within a measure) *and* `att.timestamp2.log` (`@tstamp2`, typed
  `data.MEASUREBEAT`: *"a count of measures plus a beat location in the ending measure"*). So a span is
  `measure+beat → measure+beat`, natively. That is §8.1's "measure 112, at the tempo change", as a datatype.
- **`addresses`** — `att.staffIdent` (`@staff`), `att.layerIdent` (`@layer`), `att.partIdent` (`@part`/`@partstaff`).
  Ensemble / Section / Part / Individual, already four levels.
- **`author`** — `@resp`, documented as *"records the editor(s) responsible for identifying or creating the annotation."*
- **`dimension`** — `@type` and `@func` (`att.annot.log` says values "can be taken from any convenient typology").
- **The referent set** — `att.plist`, "the active participants in a user-defined collection", with a Schematron rule
  asserting every `@plist` token resolves to a real `@xml:id`.
- **An audience gate** — `att.audience` = closed list `private` ("internal use only") | `public`. A music schema
  already distinguishes the narrated read from the gated export (rule #9).

And `MEI.performance` is the score-time ↔ wall-clock bridge terpsi thought it had to invent:
`<performance>` → `<recording>` → `<avFile>` / `<clip>` (with `@begin`/`@end`/`@betype`), plus `<when>` carrying
`@absolute` + `@abstype`, or `@since` + `@interval` + `@inttype` for relative timing. Then **`att.alignment/@when`
lets *any* score element point at a `<when>`** — with a Schematron constraint `check_whenTarget` verifying the
target is really a `<when>`.

**Transplant.** Do not adopt MEI as a storage format. Adopt its *field decomposition and its constraints* as SQLite
columns on `commentary`: `anchor_start_measure`, `anchor_start_beat`, `anchor_end_measure`, `anchor_end_beat`,
`addresses_staff`, `addresses_layer`, `addresses_part`, `author_person_id`, `dimension_type`, `audience`, plus a
nullable `recording_when_ms` that is the *derived* wall-clock alignment rather than the anchor. The `<when>`
indirection is the important structural lesson: **the anchor is score position; the recording timestamp is a
separate resolvable object, and one score position may map to several `<when>`s across several recordings** — three
performances of the same chart, one anchor. A schema that puts `t_seconds` on the commentary row cannot express that.

**Cost.** Low and mostly one-time: a day mapping the attribute classes onto columns, plus the `CHECK` constraints
that make them mechanism rather than documentation (rule #18) — `@tstamp2` ordering, `@plist` referential integrity,
`audience IN ('private','public')`. The real cost is deciding the measure-numbering authority, which is a domain
decision MEI does not make for you (repeats, pickup bars, rehearsal marks vs measures). ECL-2.0 is permissive.

### 2.2 EMA / Music Addressability API — the anchor as one parseable, greppable string

Read from `umd-mith/ema/docs/api.md` (v1.0.0 Draft, editor Raffaele Viglianti, header says CC-BY 2015). EMA defines
an addressing grammar with a real BNF:

```
GET /{identifier}/{measureRanges}/{stavesToMeasures}/{beatsToMeasures}/{completeness}
```

`measureRanges` = `1,3-5` or `10-end` or `all`; staves are mapped *per measure range* with commas and combined with
`+` (`1,2-3,1+3` = staff 1 in m.1, staves 2–3 in m.3, staves 1 and 3 in m.4); beats are prefixed `@` and mapped to
staves with `+` (`@1-2+@1-2,@1`). Keywords `start` / `end` / `all` make it writable without knowing the score length.
`completeness` (e.g. `raw`) says how much surrounding context the selection must carry to remain valid.

**Transplant.** Store the EMA expression as a `TEXT` column `anchor_ema` beside the decomposed columns from §2.1 —
one canonical, human-readable, diffable string per anchor, plus indexed integers for querying. `1-2/1,2-3/@1-2+@1-2`
is legible in `sqlite3` output with no application present, which is precisely the §16 requirement. It also solves
the awkward case the decomposed columns handle badly: *"the low brass at 112 and again at 118"* — one discontinuous
anchor, one commentary row, no join table.

**Cost.** An EMA parser/serializer is a small, well-specified job (the BNF is ~10 lines); do not take the Python
implementations — `ema-for-mei`, `ema-for-musicxml`, `ema-js-parser`, `ema-webapi` are all `NOASSERTION`-licensed and
last pushed 2021–2023. **Write your own parser against the spec.** Budget: two days including a mutation test that
asserts a malformed expression is *refused*, not silently coerced (rule #19).

**The precedent nobody mentioned.** `umd-mith/ema/nanopub/` contains code that converted the *Du Chemin: Lost Voices*
project's relational database of musical analyses into **nanopublications whose subjects are EMA expressions** — i.e.
attributed, signed, retractable analytical claims about specific passages of music. That is the terpsi Commentary
primitive, prototyped around 2015. It is worth reading before writing §8.1's final form.

### 2.3 CiTO — the graded disagreement ladder, CC-BY, and still moving

`cito.ttl` on `master` reports `owl:versionInfo "2.8.2"` and `owl:versionIRI <http://purl.org/spar/cito/2026-06-22>`,
licensed **CC-BY 4.0**. The architecture doc wants `contradicts_or_tensions_with` verbatim. CiTO offers something
strictly better: a *ladder* of disagreement, each rung defined, **each with a named inverse**:

| Predicate | Definition (quoted from `cito.ttl`) | Inverse |
|---|---|---|
| `qualifies` | "qualifies or places conditions or restrictions upon statements, ideas or conclusions" | `isQualifiedBy` |
| `disagreesWith` | "disagrees with statements, ideas or conclusions presented in" | `isDisagreedWithBy` |
| `disputes` | "disputes statements, ideas or conclusions presented in" | `isDisputedBy` |
| `critiques` | "critiques statements, ideas or conclusions presented in" | `isCritiquedBy` |
| `refutes` | "refutes statements, ideas or conclusions presented in" | `isRefutedBy` |
| `corrects` | "corrects statements, ideas or conclusions presented in" | `isCorrectedBy` |
| `updates` | "updates statements, ideas, hypotheses or understanding presented in" | `isUpdatedBy` |
| `repliesTo` | "replies to statements, ideas or criticisms presented in" | `hasReplyFrom` |
| `retracts` | (retraction) | `isRetractedBy` |

Plus the agreement side (`agreesWith`, `confirms`, `supports`, `extends`, `obtainsSupportFrom`) — which matters,
because §16's "an audit trail that logs only agreement is not one" has a mirror: *a relation vocabulary that can only
record conflict is not one either.* Three judges who **agree** about brass balance at m.112 is the finding that makes
the season-long query in §8.1 meaningful, and it needs an edge too.

**Transplant.** One table, `commentary_relation(from_id, predicate, to_id, asserted_by, asserted_at, note)`, with
`predicate` constrained by `CHECK (predicate IN (...))` against a small closed list borrowed from CiTO with the
prefix dropped: `qualifies`, `disagrees_with`, `disputes`, `critiques`, `refutes`, `corrects`, `updates`,
`replies_to`, `agrees_with`, `confirms`, `supports`, `derived_from`. Store one directed edge; **do not materialise the
inverse** — CiTO's contribution is that every inverse has a *name*, so your query layer can present
"remarks disputed by" without a second row that can drift out of sync (rule #12: name the middle, or don't make the pair).
Keep `derived_from` from `story-timeline`; drop `contradicts_or_tensions_with` in favour of the ladder, because
"tensions with" collapses `qualifies` and `refutes` into one bucket and those are different objects.

Two hard constraints, both of which are refusals in disguise: an edge must carry `asserted_by` (a *person* says two
remarks conflict — the system may not infer it, per refusal #6, and this is the queryable-not-computed line §8.1
cares about); and `CHECK (from_id != to_id)`.

**Cost.** Near zero. It is a `CHECK` list and a CC-BY attribution line. This is the cheapest high-value item on the list.

### 2.4 DICOM SR — two orthogonal flags, and a standard that *refuses* an unsigned seal

Verified in `highdicom/src/highdicom/sr/sop.py`. A DICOM Structured Report carries **three** independent state
axes, not one:

- `CompletionFlag` = `PARTIAL` | `COMPLETE` — is the document finished?
- `VerificationFlag` = `UNVERIFIED` | `VERIFIED` — has a human attested it?
- `is_final` — is the instance now immutable?

And the constraint that makes it mechanism rather than a ledger: `VerificationFlag = 'VERIFIED'` **requires** a
`VerifyingObserverSequence` with `VerifyingObserverName` (validated by `check_person_name`), `VerifyingOrganization`,
and a verification datetime. The API signature is `is_verified: bool` with the docstring noting the observer name and
organization are *"required if `is_verified`"*. You cannot mark something verified without saying who verified it.

Separately: `ValueTypeValues.TCOORD` = *"Listing of temporal coordinates"* — DICOM SR has had a temporal-coordinate
content-item type for annotating waveforms since the 1990s.

**Transplant.** §8.2's table has one axis where it needs two. A transcript can be *complete* (the aligner finished,
every word has a timestamp) and still *unverified*; it can be *partial* and *verified* (the judge confirmed the three
sentences that came through and marked the rest unusable). Collapsing those loses the case the grace period is for.
Concretely:

```sql
CREATE TABLE commentary_transcript (
  ...
  completion   TEXT NOT NULL CHECK (completion IN ('partial','complete')),
  seal_state   TEXT NOT NULL CHECK (seal_state IN ('pending','draft','sealed','rejected')),
  sealed_by    INTEGER REFERENCES person(id),
  sealed_org   TEXT,
  sealed_at    TEXT,
  CHECK (seal_state <> 'sealed' OR (sealed_by IS NOT NULL
                                AND sealed_org IS NOT NULL AND trim(sealed_org) <> ''
                                AND sealed_at IS NOT NULL))
);
```

That last `CHECK` is the whole transplant, and it is what §5's *"a sealed grant without a signer is refused by
`CHECK`"* already does for grants. Do the same for seals. **A guard that cannot be shown to fail has not been shown
to work** (rule #19): the acceptance test is an `UPDATE ... SET seal_state='sealed'` with `sealed_by` NULL that must
raise, plus the `Curator`-style `servable` companion from §16 — a row saying `sealed` whose signature does not verify
comes back `servable=False`.

**Cost.** Two columns and one `CHECK`. Hours.

### 2.5 TEI critical apparatus — 30 years of "three witnesses disagree about this passage"

From `P5/Source/Specs/{app,lem,rdg,rdgGrp,witDetail,att.textCritical,att.witnessed}.xml`, dual-licensed CC-BY + BSD-2,
repo pushed 2026-07-28. The structure:

- **`<app>`** — "one entry in a critical apparatus, with an optional lemma and usually one or more readings" — i.e.
  **the contested passage is itself a first-class object**, distinct from any of the competing accounts of it.
- **`<lem>`** — the lemma / base text: the reading the editor stands behind, *without deleting the others*.
- **`<rdg>`** — one reading, with `att.witnessed/@wit`: "a space-delimited list of one or more pointers indicating
  the witnesses" attesting it. Three judges saying the same thing is one `<rdg>` with three `@wit` pointers, not three rows.
- **`<rdgGrp>`** — "groups two or more readings perceived to have a genetic relationship or other affinity."
- **`att.textCritical`** — `@type` with a semi-closed list including **`substantive`** ("the reading offers a
  substantive variant") vs **`orthographic`** ("differs only orthographically, not in substance"); `@cause` (a typology
  of *why* the variant exists: `haplography`, `dittography`, `paleographicConfusion`, `falseEmendation`, …); `@varSeq`
  (variant sequence) and `@hand`/`@resp`.

**Transplant.** Two ideas, both cheap and both load-bearing.

First, **`substantive` vs `orthographic` is the single most useful column terpsi could add to disagreement.** Two
judges who wrote "low brass late" and "trombones behind" have an *orthographic* variant — same finding, different
words — and a system that surfaces that as a disagreement to a director is crying wolf. Two judges where one says
"late" and one says "early" have a *substantive* variant, and that is the one worth a human's attention. The column
belongs on `commentary_relation` as `variance` (`substantive` | `orthographic` | `unknown`), defaulting to
**`unknown`** rather than to `substantive`, per rule #13.

Second, **the apparatus entry as an object.** Terpsi should have a `passage_apparatus` row — an addressable, dated
record that *"these N commentaries all concern this anchor, and here is the disposition"* — rather than only pairwise
edges. It gives the dated disposition rule #15 demands a place to live, gives `<lem>` a home (the director's or head
judge's accepted account, added without destroying the others), and gives §7.4 I-7 its guarantee: retiring an
apparatus entry sets `invalid_at`; the `<rdg>` rows never move.

**Cost.** One table, one column, and a naming decision. Do **not** take CollateX (GPL-3, JVM) for automated collation
— and do not automate the collation at all in v1: aligning three judges' remarks is precisely refusal #6 territory if
the output ranks them.

### 2.6 Argilla — §8.2's states, already an enum, already in production

`argilla-server/src/argilla_server/enums.py`:

```python
class ResponseStatus(StrEnum):
    draft = "draft"
    submitted = "submitted"
    discarded = "discarded"
```

with a fourth *virtual* status in the filter layer: `ResponseStatusFilter` = `pending | draft | submitted | discarded`,
where `pending` means **no response exists yet** — which is exactly §8.2's `pending` ("alignment or transcription
produced nothing usable — said plainly, not guessed at"), i.e. absence surfaced as a state rather than as a result
(rule #13).

Three further details worth taking:

1. **`suggestions` (machine) are a different field from `responses` (human).** A model's guess never occupies the
   same slot as a person's answer. That is refusal #10 as a schema decision, and it is why Argilla can show a
   suggestion without it ever becoming the record.
2. **Responses are per-user**, so N judges on one record is native, and `test_get_dataset_users_progress.py` tracks
   each user's own state independently.
3. **`settings.distribution.min_submitted`** — a declared, per-dataset rule for how many independent submissions a
   record needs before it counts as done. That is the timebound-declared-at-issuance shape of rule #15, applied to
   adjudication coverage.

**Cost.** Zero code; it is a vocabulary and three structural decisions. Argilla itself is a 5,000-star Python/FastAPI/
Elasticsearch server — do **not** adopt the software. Note the useful naming friction: Argilla's `discarded` and
Nestor's `reject_match` are the same act, and terpsi should pick one word and tombstone the other (rule #20).

### 2.7 DKPro's unitizing alpha — the only tool found that actually measures `reject_match`

`dkpro-statistics-agreement/src/main/java/org/dkpro/statistics/agreement/unitizing/` contains
`UnitizingAnnotationStudy(int raters, int begin, int end)`, `addUnit(long offset, long length, int rater, Object category)`,
and `KrippendorffAlphaUnitizingAgreement`, with tests reproducing Krippendorff (1995: p.57) and (2004: p.254).
Apache-2.0, pushed 2026-07-11.

The distinction matters more here than anywhere else in this report. Ordinary inter-rater agreement (Cohen's κ,
coding-style α) assumes the *units are given* and asks whether raters labelled them the same. **Unitizing** α assumes
the units are *not* given and asks whether raters carved the continuum in the same places. `reject_match` — *"this
correct remark is attached to the wrong passage"* — is a unitizing disagreement, not a coding one. It is the error
§8.2 names as the common one, and it is the one every off-the-shelf agreement library silently cannot see.

**Transplant.** Not as a runtime dependency (it is Java; the host is not). Use it **once, offline, as a validation
instrument** on a pilot event: take two judges' anchored commentary over one performance, feed spans as units over the
measure continuum, and get a number for how often independent judges anchor the same remark to the same place. That
number sizes the anchoring UI problem — tap-to-mark vs forced alignment — before the UI is built, which is exactly the
§18 "read §14 as a claim, not as ground truth" discipline applied to a design assumption.

**Cost.** One afternoon and a JVM in the sandbox (§5.1), producing a number rather than a component. If you want it in
process later, `segeval` (BSD, Python, boundary-edit-distance) is the dormant-but-usable substitute.

### 2.8 BORIS — the closest working analogue, and it is already SQLite-shaped

GPL-3, 242★, pushed 2026-07-22, IRR plugins version-dated 2026-01-30, 2,834 citations. An ethologist watching a video
and pressing keys as a monkey does things is *the same act* as a judge talking into a recorder while a band plays, and
BORIS has been solving it for fourteen years. `boris/irr.py` signature — `cohen_kappa(cursor, obsid1, obsid2, interval,
selected_subjects, include_modifiers)` where `cursor` is a `sqlite3.cursor` over aggregated events — tells you the
architecture: **events aggregate into SQLite, and analysis is SQL over that.**

What is worth taking:

- **Point events vs state events.** A state event has start and stop; a point event is instantaneous
  (`irr_cohen_kappa_with_modifiers.py` notes it "supports instantaneous events: start == stap"). Terpsi's `span`
  needs the same distinction: *"measure 112"* (a mark) and *"measures 96–120"* (a passage) are different anchors, and
  forcing a zero-length span on the first loses the judge's intent.
- **Ethogram + modifiers.** A closed, project-defined list of behaviour codes, each with optional modifiers. That is
  §8.1's `dimension` (rubric criterion / caption) with sub-caption modifiers, and BORIS's insistence that the ethogram
  is *project configuration, not code* is why "a symphonic festival is a configuration rather than a second
  application" is achievable.
- **The exclusion matrix** — a declared set of mutually incompatible codes, enforced at coding time. Terpsi's
  equivalent: a rubric criterion cannot be both `intonation` and `blend`; declare it and let the insert refuse.
- **Needleman-Wunsch** (`menuSimilarities.addAction(self.actionNeedleman_Wunsch)`) for comparing two observers'
  *event sequences*. When two judges mark the same events in the same order but a bar apart, sequence alignment finds
  the correspondence where a timestamp join finds nothing.
- **`boris_cli.py`** — headless analysis. §5.1's sandbox wants exactly this shape.

**Cost.** Read it, don't link it: GPL-3 plus PySide6 is a poor fit for a system that must not grow a GUI dependency.
Budget a day reading `boris/irr.py`, `boris/analysis_plugins/`, and the project-file schema. The payoff is that BORIS's
plugin architecture for IRR — each measure a separate, versioned, named plugin with its own docstring stating what it
assumes — is a good model for how terpsi should ship *any* statistic over judges: as a named, dated, individually
citable thing, not a number in a dashboard.

### 2.9 INCEpTION's curation model — adjudication as a distinguished document, not an edit

`SourceDocumentState.CURATION_IN_PROGRESS` / `CURATION_FINISHED`, a reserved pseudo-user `CURATION_USER`
(`WebAnnoConst.CURATION_USER`), `CurationSessionServiceImpl.setCurationTarget(...)`, `MergeDialog`, and a pluggable
`MergeStrategyFactory` whose default binding is `ThresholdBasedMergeStrategyFactoryImpl`. Apache-2.0, pushed 2026-07-28.

The architecture: each annotator's work is a separate, untouched document. Curation produces a **new** document owned
by a distinguished non-human user, built by an explicit merge whose strategy is declared and swappable. The annotators'
documents are never edited by the curator. That is refusal #11 (canonical store read-only to the app; agents write
sidecars; promotion is a human act) and refusal #10 (a machine answer is a `draft` until a named human seals it),
implemented in a 700-star Java codebase.

**Transplant.** The `ThresholdBasedMergeStrategy` is the piece to name explicitly in §8.1: **a threshold-based merge is
the only kind terpsi may have, and it must never resolve.** Where ≥N judges agree, the merged record is created as a
`draft` with its constituents cited; where they do not, the system *presents the divergence and halts* — refusal #6,
"the system presents, a human decides." Write it down as a declared strategy with a name and a threshold rather than as
scattered `if` statements, because a named strategy can be tested for refusal and an implicit one cannot (rule #19).

**Cost.** Design only. Do not adopt INCEpTION (Java/Spring/UIMA/Wicket).

---

## 3. ⚠ One finding that is a refusal, not a candidate

**Every inter-rater-reliability tool in this space computes a durable per-annotator quality score, and that is
prohibited scope `SA-3`.**

`Toloka/crowd-kit` (Dawid-Skene, MACE, GLAD) and `CrowdTruth/CrowdTruth-core` exist to estimate *annotator competence*
and reweight annotations by it. CrowdTruth's own topics list `inter-annotator-agreement` and its model is an explicit
worker/unit/annotation quality triangle. BORIS's κ, DKPro's α, and Argilla's `agreement_metrics.py` /
`annotator_metrics.py` all produce per-annotator numbers as a matter of course.

CLAUDE.md refusal #4: *"No durable rating of a judge, clinician, student, or staff member carried between events or
contexts. Prohibited scope `SA-3`; invalid even signed by root."* A per-judge κ persisted across a season **is** a
standing cross-context score of a judge. §15's `oakenscrolls-office` note ("grades claims against outcomes") sits
uncomfortably close to the same line and deserves an explicit boundary in §13.

The distinction that keeps the useful part: **agreement about a passage is a property of the passage; agreement about
a judge is a property of the judge.** The first is what §8.1 wants — "diff the same passage across judges who
disagreed." The second is `SA-3`. So:

- Agreement statistics may be computed **per event, per passage**, scoped to one adjudication, and stored on the
  apparatus entry.
- They may **not** be aggregated to a `judge_id` and carried forward, and there must be a test that attempts exactly
  that aggregation and asserts refusal (rule #19).
- Take the *algorithms* from crowd-kit if a one-off calibration study is ever wanted; do not take the *data model*,
  which is built around persistent worker skill.

This is the sort of thing that arrives as a helpful library and leaves as a policy violation, so it belongs in §13
before anyone imports it.

---

## 4. Weirdest things I found

**1. Ethologists solved judge-vs-judge agreement fourteen years ago, over SQLite, and threw in gene-sequence alignment.**
BORIS (`olivierfriard/BORIS`, GPL-3, 2,834 citations) is for watching animals. Its `boris/irr.py` takes a
`sqlite3.cursor` and two observation IDs and returns Cohen's κ over time bins; its Analysis menu offers
**Needleman-Wunsch** — the 1970 protein-sequence alignment algorithm — to compare two observers' event streams.
A marching-band judge and a primatologist have the same problem (a continuous performance, a coding scheme, a second
observer who saw it slightly differently), and only one of them has open-source tooling for it.

**2. A 1990s radiology standard already refuses to record a seal without a signer.**
DICOM Structured Reporting separates `CompletionFlag` (PARTIAL|COMPLETE) from `VerificationFlag`
(UNVERIFIED|VERIFIED) — is it *finished* is a different question from has a human *attested* it — and setting VERIFIED
is invalid without `VerifyingObserverName` + `VerifyingOrganization` + datetime. It also has a `TCOORD` value type,
"Listing of temporal coordinates", for annotating waveforms. Terpsi's §8.2 table has one axis where DICOM has two, and
§5's *"a sealed grant without a signer is refused by `CHECK`"* is a rediscovery of a constraint that has been shipping
in hospital PACS systems since before the students in this database were born.

**3. Textual scholars have a closed vocabulary for "is this a real disagreement or just different wording."**
TEI's `att.textCritical/@type` distinguishes `substantive` ("offers a substantive variant") from `orthographic`
("differs only orthographically, not in substance"), and `@cause` gives a typology of *why* variants arise —
`haplography`, `dittography`, `paleographicConfusion`, `falseEmendation`. Editors of medieval manuscripts formalised
the difference between "these two witnesses disagree" and "these two witnesses said the same thing differently,"
because conflating them ruins an apparatus. Conflating them will also make terpsi cry wolf at a band director who
gets told two judges disagree when they wrote synonyms.

**4. The bird people won the "readable without the app" argument by never having an app format.**
A Cornell Raven **selection table** is a tab-delimited text file: `Selection · View · Channel · Begin Time (s) ·
End Time (s) · Low Freq (Hz) · High Freq (Hz)`, plus whatever annotation columns you invent. That is it. Twenty years
of bioacoustics annotation, openable in any spreadsheet, parseable in one line, and there is a CRAN package
(`Rraven`, GPL≥2, v1.0.16) whose entire purpose is moving between it and R. Set against MELD — the same problem
solved with MEI + JSON-LD Web Annotations + SPARQL + Solid Pods, four repositories deep — it is a bracing argument
about what "the data outlives the tool" actually costs.

**5. This exact primitive was built in 2015, for 16th-century French chansons, and it used nanopublications.**
`umd-mith/ema/nanopub/` converted the *Du Chemin: Lost Voices* project's relational database of musical analyses into
nanopublications — cryptographically signed, three-named-graph claims (assertion / provenance / publication info) —
whose subjects are EMA expressions addressing specific measures, staves and beats. Attributed, retractable
(`npx:retracts`, with the reader convention `FILTER NOT EXISTS { ?creator npx:retracts ?np_uri }`), never-deleted
claims about a passage of music. Swap Renaissance musicologists for marching-band adjudicators and it is §8.1 plus
§8.2 plus `reject_match`, funded by an NEH grant eleven years ago, and now mostly dormant on GitHub.

---

## 5. What to do next (shortest path to a first commit)

1. **Write §8.1's schema against MEI's `<annot>` decomposition** (§2.1) and store an EMA expression alongside (§2.2).
   Both are permissively licensed and neither adds a dependency.
2. **Replace `contradicts_or_tensions_with` with the CiTO ladder** plus `variance ∈ (substantive, orthographic, unknown)`
   from TEI (§2.3, §2.5). One table, one `CHECK`, one CC-BY attribution.
3. **Split §8.2's state column into `completion` × `seal_state`** and add the `CHECK` that refuses a sealed row
   without a named sealer and organization (§2.4). Ship the mutation test that proves it refuses.
4. **Add a `passage_apparatus` object** so a disagreement and its dated disposition have somewhere to live that is
   not a pairwise edge (§2.5, rule #15).
5. **Write the SA-3 boundary into §13 before importing any agreement library** (§3), and pair it with a test that
   attempts per-judge aggregation and asserts refusal.
6. **Run DKPro's unitizing α once on pilot data** (§2.7) to size the anchoring problem with a number rather than an
   assumption — this is a §18 item 0 move applied to a design premise.
