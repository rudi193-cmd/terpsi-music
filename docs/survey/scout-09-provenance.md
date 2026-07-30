# Scout 09 — Provenance, verification, citation decay

Slice: expressing "how much should I trust this value" as a scale that **travels with data and never gates it**.
Read first: `docs/ARCHITECTURE.md` §15 (direction hazard, P1–P5, confidence-is-not-a-rung, verification-as-third-axis, rendering), `CLAUDE.md` 13 / 14 / 17.

**Verification honesty note.** Web search budget ran out partway; the rest was done by fetching raw spec/source files. Every row below is marked with how it was verified. Three items are marked **UNVERIFIED-IN-DETAIL** because the host 403'd or the path 404'd — they are leads, not facts, and I have not dressed them up as facts. (§15's own rule: a `P2` that could not be re-fetched must say so.)

---

## Ranked table

| # | Project / standard | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **`MISP/misp-taxonomies` → `estimative-language`, `admiralty-scale`** | Machine-readable JSON of ICD 203 (likelihood × analytic confidence) and the Admiralty two-axis code | CC0 / public domain (repo-level statement) | Active, community-maintained, `admiralty-scale` at version 5 | P1–P5 vocabulary shape; two-axis separation; **and a live example of the forbidden collapse** | **adopt** the file format + **steal** the counter-example |
| 2 | **`oasis-open/cti-python-stix2` → `stix2/confidence/scales.py`** | One module holding six named ordinal scales and their conversions to a single normalized space | BSD-3-Clause | Active (OASIS TC) | §15 "a single mapping lives in one place, and every gate calls it"; item 13 (unknown refuses to become a number) | **adopt the shape** — this is §15's mapping table already written |
| 3 | **CF Conventions §3.5 Flags + `ioos/compliance-checker`** | netCDF convention: a coded ordinal must carry its own meanings table; enforcement tool that fails when it doesn't | CF spec: community/open. checker: Apache-2.0 | Both active (CF 1.11 supported) | item 14 (never bare integers, one mapping table); item 19 (guard shown to fail) | **adopt** the invariant + the test |
| 4 | **Robust Links (Memento) — `mementoweb/robustlinks`, `renevoorburg/robustify.js`** | Link-decoration spec: store original URL + archived URL + version date on every citation | Repo points at Memento/SiteStory licence (permissive; not restated in-repo) | Spec stable; JS libs low-churn but live | §15 "`P2` requires storing enough to survive its source disappearing" | **adopt** the three-field citation shape |
| 5 | **Wikipedia CS1 `url-status` + InternetArchiveBot** | Citation status enum `live · dead · unfit · usurped · deviated`, plus a bot that repairs and tags at encyclopedia scale | Content CC BY-SA; IABot code open | Continuously active | almanac-template's seven decay states; fingerprint drift; the daily sweep | **steal the idea** (two missing states) |
| 6 | **SDMX `CL_OBS_STATUS` / `CL_CONF_STATUS`** | Statistical exchange standard that **split** observation status from confidentiality status into two code lists | Open standard (SDMX/Eurostat) | Live; Eurostat split effective 2025-01-27 | §15 "Provenance is epistemic, not authorization" | **steal the idea** — external precedent for the split |
| 7 | **IPCC AR6 / Mastrandrea 2010 uncertainty guidance** | Three calibrated scales (evidence & agreement → confidence → likelihood) with an explicit rule for falling back when you cannot judge | Open guidance note | AR6 in force | item 13 (absence surfaces as a different shape, not a fabricated number) | **steal the idea** |
| 8 | **GRADE (certainty of evidence)** | Rung derived by declared upgrade/downgrade reasons; kept strictly separate from strength of recommendation | Handbook open; GRADEpro tool free-access, not FOSS | Active (WHO/NICE/Cochrane) | derivation audit for P-rungs; epistemic-vs-action split | **steal the idea** |
| 9 | **`lycheeverse/lychee`** | Fast async link checker; caching, Wayback replacement suggestions, CI exit codes, JSON output, usable as a Rust library | Apache-2.0 / MIT | Very active | the liveness sweep half of §15's decay job | **adopt** if the fleet's `check_links.py` is not kept |
| 10 | **Nanopublications — `fair-workflows/nanopub`** | Claim split into separate named graphs: assertion / provenance / publication-info; signed; **retracted, never deleted** | Apache-2.0 | Active (copyright notices through 2025) | §15's four-field descriptor; item 3 (`invalid_at`, not delete) | **steal the idea** |
| 11 | **Darwin Core `identificationQualifier`, `identificationVerificationStatus`** | Biodiversity term set where uncertainty rides *inside* the identification string (`cf.`, `aff.`, `?`) | CC0 (TDWG) | Active ratified standard | item 14 — a qualifier that cannot be dropped in transit | **steal the idea** |
| 12 | **Getty CDWA Creator Qualifier / Linked Art `AttributeAssignment`** | Museum attribution ladder ("attributed to", "school of", "after") modelled as an assertion made *by someone, at some time* | CDWA free to use; Linked Art CC-BY | CDWA stable; Linked Art active | §15's `verifier` field; seal-state as a third axis | **steal the idea** |
| 13 | **ENFSI Guideline for Evaluative Reporting** | Forensic verbal scale bound to numeric likelihood-ratio bands, with two hard prohibitions | Open PDF guideline | In force across EU labs | rendering rules; "never compare bare integers" from the other direction | **steal the idea** (two prohibitions) |
| 14 | **OSM `check_date` / `survey:date` / `fixme`** | Freshness-of-verification carried as a dated key; absent key ≠ low score | ODbL data; wiki CC-BY-SA | Active | `no-baseline` vs `drift`; never-checked vs checked-and-stale | **steal the idea** + cautionary tale |
| 15 | **C2PA / `contentauth/c2pa-rs`** | Signed provenance manifests that travel alongside an asset without modifying it | MIT / Apache-2.0 | Very active (spec 2.4) | §5 sidecar-not-canonical; provenance as attached label | **read-only interest** (too heavy for one box) |
| 16 | **W3C Credible Web CG credibility signals** | Reviewed vocabulary of trust signals, deliberately not a score | W3C CG (no explicit repo licence found) | **Dormant** (records thin after 2022) | rendering signals without aggregating them | **read-only interest** |
| 17 | **SLSA levels / tracks** | Build-provenance ladder, renamed to track-prefixed levels (`Build L1–L3`) | Apache-2.0 (repo) | Active | prefixing rungs so a bare integer cannot travel | **UNVERIFIED-IN-DETAIL** — lead only |

---

## Top finds, with the concrete transplant and its cost

### 1. MISP's two taxonomies — adopt the format, and adopt the *bug* as your regression test

**Verified** by fetching `admiralty-scale/machinetag.json` and `estimative-language/machinetag.json` from `MISP/misp-taxonomies`.

`estimative-language` is ICD 203 rendered as JSON, and it is structurally exactly what §15 asks for: **two predicates that never mix.** `likelihood-probability` carries seven rungs each bound to an explicit numeric band (`almost no chance` = 01–05% … `almost certain` = 95–99%), and `confidence-in-analytic-judgment` carries three (low / moderate / high) defined by *why* — assumptions required, source corroboration, argument strength. That is §15's "`provenance` and `confidence` side by side, one ordinal and one continuous, neither pretending to be the other," already published, already machine-readable, and citing its authority (ICD 203, JP 2-0) inline.

`admiralty-scale` is the two-axis source-reliability × information-credibility code, and MISP has extended the classic A–F with a seventh rung the original lacks: **`G: Deliberately deceptive`**. That rung matters here more than it looks. A guardian-supplied medical form, a transferred district record, a self-reported prior placement — the fleet currently has no way to say "this source is not merely unreliable, it is adversarial," and `E: Unreliable` does not carry it.

**And now the reason this is find #1 rather than find #4.** Both MISP scales assign a `numerical_value` to every rung, and both encode the unknown rung as the numeric midpoint:

- `F: Reliability cannot be judged` → **50**, identical to `C: Fairly reliable` → 50
- `6: Truth cannot be judged` → **50**, identical to `3: Possibly true` → 50

That is `CLAUDE.md` item 13 violated in a widely-deployed public taxonomy: absence has been surfaced *as a result*, and the result it was surfaced as is "middling." A downstream `if numerical_value >= 50` cannot distinguish "we checked and it's fair" from "we have never used this source." It is the same shape as §15's warning about `P2` decay — a rung held by inertia — except here the inertia is arithmetic.

Contrast **find #2**: `cti-python-stix2` implements the *same* Admiralty credibility scale and **raises `ValueError` for "6 - Truth cannot be judged" because it has no mapping.** Two open-source implementations of one scale; one collapses unknown into a number, one refuses to. This project's item 13 is on the side of the one that refuses — and now that position has a citation and a named counter-example rather than being an assertion.

**Transplant.** Take the `machinetag.json` shape — `namespace`, `predicates`, `values`, `version`, `uuid` — as the on-disk form of the one mapping table §15 requires: one file per scale (`sensitivity`, `trust`, `provenance`), each predicate's rungs listed with their prefixed identifier (`L1`, `T0`, `P3`) as the primary key and the human label as text. Drop `numerical_value` entirely, or make it nullable and leave it null for every unjudgeable rung.

**Cost, SQLite single box:** very low. Three small JSON files in the tree, loaded at startup into one `scales` table (`scale`, `rung_id`, `ordinal`, `label`, `glyph`, `composes_by`), plus a loader that refuses a file where any rung lacks a prefix. Half a day. No dependency — the taxonomies are CC0 data, not code, so nothing is vendored that needs a §16 middle beyond the loader itself.

**Acceptance test (item 19), free of charge:** load a fixture whose unknown rung carries a numeric value and assert the loader rejects it. The forbidden act is available off the shelf, in a real file, from a real project. That is a mutation test you did not have to invent.

### 2. `stix2/confidence/scales.py` — §15's "one mapping table in one place," already written

**Verified** by fetching the file from `oasis-open/cti-python-stix2` (BSD-3-Clause).

The module holds six scales — None/Low/Med/High, 0–10, Admiralty Credibility, Words of Estimative Probability, the DNI probability scale, and a normalized 0–100 space — and exposes exactly two functions per scale, paired: `<scale>_to_value(scale_value)` and `value_to_<scale>(confidence_value)`. Every cross-scale conversion goes through the normalized space, so there are `2n` functions rather than `n²`, and there is precisely one place where any given rung's meaning is written down.

Three properties transfer directly and are worth more than the code:

1. **Conversion is a named function call, never an integer comparison.** You cannot accidentally compare a WEP rung to an Admiralty rung, because neither is a number until you have named which scale you are leaving. This is `if level >= 3` made unwriteable rather than merely discouraged.
2. **It raises rather than coerces.** `"STIX Confidence value cannot be determined for %s"` and `"Range of values out of bounds: %s"` — no silent coercion, no `None` return. An out-of-range rung is a defect, not a degraded answer.
3. **The unjudgeable rung has no mapping and says so**, as above.

**Transplant.** Write `scales.py` (or `scales/mod.rs`) with `sensitivity_to_ordinal`, `trust_to_ordinal`, `provenance_to_ordinal` and their inverses, and — critically — the *composition* functions, which STIX does not need but §15 does: `compose_sensitivity(*rungs) -> max`, `compose_trust(claimed, registered_ceiling) -> min`, `compose_provenance(*rungs) -> min`. Put the three composition rules in the same module as the three ladders, because §15's argument that the scales can never be merged rests on them differing, and that argument is only checkable if both halves live together.

Do **not** add a normalized cross-scale space. STIX needs one because it interoperates with five external vocabularies; this app has three internal ladders that must never be compared at all. Borrow the "conversion is a named call" discipline and skip the pivot.

**Cost:** low, and it is work §18 requires regardless. ~200 lines plus tests. The real cost is discipline: every existing comparison site has to route through it, or you have built a ledger and called it enforcement (item 18).

### 3. CF Conventions §3.5 Flags + `ioos/compliance-checker` — the ordinal lives in a separate variable that the data points at

**Verified** by fetching `cf-convention/cf-conventions/ch03.adoc` and `ioos/compliance-checker/compliance_checker/cf/cf_1_6.py`.

This is a thirty-year-old scientific file-format convention that independently arrived at item 14, and it goes one structural step further than §15 currently does.

The convention: a variable holding coded status values must carry `flag_values` (the list of possible codes, in the variable's own datatype) **and** `flag_meanings` (a blank-separated list of descriptive phrases, *"one for each flag value"*). The mapping table is not in a document, not in a wiki, not in a constant somewhere in the app — **it is inside the file, next to the codes, and it is not optional.** For non-exclusive conditions there is `flag_masks` with the same one-meaning-per-mask requirement. Quality and status variables take `standard_name = "status_flag"`.

The step further: the quality code is **its own variable**, and the data variable references it through `ancillary_variables`. The trust label is not a column on the record and not a magic value in the data — it is a parallel object bound to the data by an explicit pointer. That is §15's *"provenance is a label that travels with a value, never a condition on serving it"* expressed as a data layout, and it makes the "never gates" property structural: a reader that ignores `ancillary_variables` still gets the value, in full, unimpeded. Withholding is not even expressible.

And the enforcement exists, with quotable failure messages. `compliance-checker` asserts:

- `"Variable {variable.name} must have attribute flag_meanings defined when flag_values attribute is present"`
- `"{name}'s flag_meanings and flag_values should have the same number of elements."`
- `"{name} flag_meanings and flag_masks should have the same number of elements."`

plus uniqueness of flag values, datatype agreement, and a prohibition on a zero mask. It runs at three strictness levels (lenient / normal / strict) and returns a failure code, so it fails CI. One honest gap: it does **not** require `standard_name = status_flag` — the checks fire on any variable carrying flag attributes, regardless of naming. So the convention's naming discipline is convention-only; the counting discipline is enforced. Worth knowing which half is which before citing it as precedent.

**Transplant.** Two things, and the second is the valuable one.

First, the invariant: any table that stores a rung must store, or foreign-key to, the rung set it belongs to — a `provenance` column with no reference to the `P` ladder is rejected at schema-check time, exactly as `flag_values` without `flag_meanings` is rejected. In SQLite: `provenance_rung TEXT NOT NULL REFERENCES scales(rung_id)` where `scales.rung_id` is the *prefixed* string (`'P3'`, not `3`), so the foreign key itself makes a bare integer unstorable. The database refuses the direction hazard.

Second, the layout: consider putting the four-field descriptor from §15 (`provenance`, `confidence`, `seal_state`, `verifier`) in a **sidecar table keyed to the value's row**, not as four columns on it. This aligns with §5 (the canonical store is read-only to the app; agents write sidecars) and with §7.4 W-1 (one lane per student) — a provenance annotation about a student's record is an entry, and item 16 says entries about a student are as durable as the record. Four columns on the canonical row cannot be written by an agent without writing the canonical row. A sidecar can.

**Cost:** low-to-moderate. The FK is trivial. The sidecar join is a design decision, not a library, and it is cheaper to make now than after the first table ships. Borrow zero code — netCDF is entirely the wrong storage layer here. Borrow the shape and the three assertion messages.

### 4. Robust Links + Wikipedia `url-status` — citation decay, solved twice, independently, with two states the fleet is missing

**Verified**: `mementoweb/robustlinks` repo contents (attributes and their semantics); Wikipedia `url-status` values via search results, with per-value definitions.

Robust Links is the Memento project's answer to §15's exact sentence — *"`P2` requires storing enough to survive its source disappearing: not a URL, but a resolved content hash, a pinned commit, or the quoted claim itself."* Their answer is three fields carried on every citation:

- `data-originalurl` — the URI of the resource as the author intended it
- `data-versionurl` — a specific archived memento
- `data-versiondate` — the datetime of linking, i.e. **when the author's claim about this source was true**

The last one is doing the subtle work. A version date alone lets you find *a* memento near the moment of citation even when the specific archive copy is also gone, and it is the field that makes "never checked" distinguishable from "checked, then rotted" without any status column at all: no `data-versiondate`, no observation. That is the same distinction almanac-template encodes as `no-baseline`, reached from the opposite direction.

Robust Links also gave the field its vocabulary: **link rot** (the source is gone) versus **content drift** (the source resolves and has changed). §15 calls the second one `fingerprint_result: drift`. Same concept, and the older name is the one external readers will recognize.

Wikipedia arrived at a five-value enum for the same problem — `url-status` ∈ `live · dead · unfit · usurped · deviated` — and **two of those five are not in almanac-template's seven**, and both matter for a school:

- **`deviated`** — *"the original URL is 'live' but no longer supports the article text."* This is drift, but promoted from an observation to a curated status, and note what it is relative to: not "the bytes changed" but "the bytes no longer support **the claim we made from it**." A district calendar that reflows its HTML has drifted in fingerprint but not in claim. A circuit rubric that silently changed a class-size threshold has drifted in claim while possibly matching a coarse fingerprint. `drift` catches the first cheaply and the second only by luck; `deviated` names the thing you actually care about, and — correctly, per §15's `status_source: auto · curator` — only a human can set it.
- **`usurped`** — *"the domain in the URL no longer serves its original intent, particularly when the domain has been (mis)appropriated"* by advertising, malware, phishing or resellers, **and links to a usurped URL are suppressed in rendering.** This is the one I would push hardest to add. `dark` says the source is gone. It does not say the source came back as something hostile. An expired booster-club domain or a retired state-standards subdomain resold to an ad network is an ordinary event, and this app renders links to guardians and to judges. A seven-state ladder that lacks `usurped` will happily render that link with its old label. Note also that this is the **one** decay state that legitimately affects rendering — and it is a safety suppression, not a provenance gate, so it does not violate "provenance never gates." Worth stating explicitly when you add it, or someone will later cite it as precedent for withholding weakly-sourced values.

**Transplant.** Extend almanac-template's `catalog-entry.schema.json` `status` enum with `usurped` and `deviated`, keeping `status_source` (`auto` may set `usurped` from a heuristic and `dark` from a probe; only `curator` may set `deviated`). Add the Robust Links triple to whatever `P2` citation record you build: `original_url`, `archived_url`, `version_date`, alongside the fingerprint baseline §15 already specifies. Store the **quoted claim** too — §15 already asks for it and Robust Links does not have it, because a memento of a rubric page is not the same artifact as the sentence you relied on.

**Cost:** low. You are adopting an existing fleet schema (§15 says adopt it wholesale) plus two enum values and three columns. `lychee` (#9, Apache-2.0/MIT) can be the prober if `check_links.py` is not carried over: it has `--cache`, CI exit code 2, JSON and JUnit output, `file://` support, and `--suggest`, which proposes web-archive replacements for broken links — that last one is a ready-made recovery-candidate generator feeding almanac-template's `recovery.authenticity` ladder. It has **no** content-hash or drift detection, so lychee covers reachability only; the fingerprint half stays yours. Two dependencies where the fleet already has one is a §16 pair — if you take lychee *and* keep `check_links.py`, name the reconciler in the same commit or take only one.

### 5. SDMX splitting observation status from confidentiality status — the external precedent for "provenance is epistemic, not authorization"

**Verified** via search: `CL_OBS_STATUS` code list contents and versions, and the Eurostat change effective 2025-01-27 dispatching flags into two separate code lists, `OBS_STATUS` and `CONF_STATUS`.

SDMX is the statistical-exchange standard behind Eurostat, the FAO and most national statistics offices. Its observation-status code list is a P-ladder by another name: `A` normal, `E` estimated, `P` provisional, `I` imputed by a receiving agency, `F` forecast, `B` break, `S` strike, `M` **missing**. Two details are worth the trip:

**They split the flag.** Observation status (how do we know this number?) and confidentiality status (who may see it?) used to travel as one flag field and were separated into two code lists. That is §15's central claim — that an epistemic ladder and an access ladder are different objects — validated by an international standards body that had them fused, discovered it did not work, and paid the migration cost to unfuse them. When someone proposes folding `P` into the `L` ladder because "both are five levels and both are about how careful we're being," this is the answer, and it is stronger than an assertion because it is a reversal.

**`M` is a rung.** Missing is a status code, not a value, and not a zero. Item 13 in a production statistical pipeline.

**And a contradiction worth recording.** SDMX rungs are **bare single letters**, unprefixed — and the standard needed *multiple* published documents on "possible ways of implementing" the code list, plus a version 2.2 clarification distinguishing `E` (estimated by the source) from `I` (imputed by the receiving agency), because implementers were conflating them. Version 2.2 exists to disambiguate two rungs that a bare letter could not keep apart. This is §15's prefix rule earning its keep: SDMX has the mapping table and still lost information at the boundary, because the token that travels (`E`) does not carry which ladder it came from. **Do not soften the prefix requirement.** The organization with the most experience running an ordinal status ladder across institutional boundaries is the one that shows what the unprefixed version costs.

**Cost:** zero. This is ammunition for §18 and §15, not a dependency. Do not adopt SDMX; the standard is vastly oversized for one box and its transport is XML/JSON messaging for statistical cubes.

### 6. IPCC calibrated language — the fallback rule is item 13 done right, by people writing for hostile readers

**Verified** via search: the AR5/AR6 guidance note (Mastrandrea et al. 2010) and its three-scale structure.

The IPCC runs **three** calibrated scales, not one: *evidence and agreement* (qualitative, two-dimensional — type/amount/quality/consistency of evidence crossed with degree of agreement), *confidence* (a qualitative measure of the validity of a finding, built from the first), and *likelihood* (quantitative, probabilistic). They compose in one direction only, and here is the part to steal:

**The evidence-and-agreement scale exists specifically for the case where authors lack sufficient information to judge confidence or probability.** When you cannot reach the higher-information scale, you do not guess a rung on it, and you do not withhold the finding. You publish on the coarser scale, in its own vocabulary, and the shape of the statement tells the reader which scale you were able to reach.

That is `CLAUDE.md` item 13 with the mechanism supplied. §15 says absence surfaces as `unknown`; IPCC says absence surfaces as *a statement on a different, honestly coarser scale* — which is strictly more useful, because "unavailable" and "we have limited evidence and the sources disagree" are both honest and only one of them is informative. And it is done by a body whose every sentence is read adversarially, which is the relevant test for adjudication commentary and for a records-inspection response.

**Transplant.** Where a `P`-rung genuinely cannot be determined, do not emit `P5 ASSUMED` — `P5` is a *positive* claim that something was asserted without evidentiary basis, and using it for "we don't know the provenance" is exactly the MISP `numerical_value: 50` error in ordinal clothing. Add a distinct non-rung, `P?` or `provenance_unknown`, that renders as `PROVENANCE NOT ESTABLISHED` and is unordered — it participates in no `min`, and `compose_provenance` returns it whenever any input carries it (absorbing, not comparable). This is a genuine addition to §15, which currently has five rungs and no place to put "we cannot say which rung."

**Cost:** low, if done before the ladder ships; annoying after, because `min` over a set containing an unordered element has to be written deliberately rather than as `min()`. One function, one test asserting `compose_provenance('P1', 'P?') == 'P?'`.

### 7. The attribution-ladder tradition — museums, herbaria, and forensic labs all put the qualifier where it cannot be dropped

Three independent fields, one shared instinct, and it bears on rendering (§15) more than on storage.

**Getty CDWA Creator Qualifier** (definition verified via search; the specific term list is **UNVERIFIED-IN-DETAIL** — the Getty host 403'd, so I am not quoting the ladder verbatim). The verified part is the one that matters: the qualifier is *"used when the attribution is uncertain, is in dispute, when there is more than one actor, when there is a former attribution, or when the attribution otherwise requires clarification"* — and in linked-data mappings it becomes an **`AttributeAssignment`**, i.e. an event with an actor and a date. Not a property of the object: *an assertion someone made.* That is §15's `verifier` field and `seal_state` as a third axis, arrived at by cataloguers who learned the hard way that "Rembrandt" and "attributed to Rembrandt" get collapsed by the next person to touch the record unless the qualifier is structurally welded on. The museum world's other lesson, from the same source: uncertainty often has to survive as free text because the controlled ladder cannot carry every nuance — which argues for `provenance_note` alongside the rung, not instead of it.

**Darwin Core `identificationQualifier`** (definition verified verbatim from the TDWG terms doc): *"A brief phrase or a standard term to express the degree of uncertainty of an Identification."* Biologists put it **inside the name string** — `Quercus cf. alba`, `Ctenomys aff. opimus`, `Amanita sp.` — for one reason: a qualifier stored in a separate field gets dropped by the next export, and a specimen whose tentative identification has been laundered into a confident one is worse than an unidentified specimen. CC0, ratified, active. The companion term `identificationVerificationStatus` is the seal-state axis in the same standard.

The cost of getting this wrong is the fleet's documented failure mode in miniature: §15 already warns that a `P2` label survives its source's death. The attribution traditions warn about the reverse trip — the *label* dying while the value survives, arriving downstream as bare fact.

**ENFSI Guideline for Evaluative Reporting** (verified via search) contributes two prohibitions, and prohibitions are what §15's rendering section is short on:

1. **A verbal qualifier never travels without its numeric band.** The ENFSI scale binds each verbal level to an explicit likelihood-ratio range (weak = 1–10, moderate = 10–100, and so on up to extremely strong above 1,000,000), and the guidance is explicit that verbal qualifiers *do not replace* the numbers — they exist to communicate probative value, not to substitute for it. Directly relevant to §15's rendering rule: the glyph or word carries the same information as the colour, and neither carries it *instead of* the rung identifier.
2. **Never state the conclusion in the direction of the proposition.** ENFSI prohibits source attribution — *"this fibre came from the suspect's coat"* — because a likelihood ratio about evidence given a hypothesis is not a statement about the hypothesis given the evidence. Inverting it is the transposed conditional, and the guideline treats it as a reportable error rather than a stylistic preference.

That second one deserves a place in `CLAUDE.md`'s refusal list in domain form. A `P1 Measured` acoustic prediction and a judge's caption score are, per §15, both claims in the same eventual row. The transposed-conditional error there reads as: *"the model measured what arrived at the judge's seat, therefore the judge's score was wrong."* That is a statement about a named adult's professional judgement, inferred from a provenance rung, and it is the same forbidden move as `SA-3` (item 4, no standing cross-context scores) — reached not by storing a rating but by rendering an inference as a finding. §15 says the join *"is what makes judge calibration a measurement rather than a rhetorical position."* ENFSI's experience is that the join is exactly where the rhetoric sneaks back in, and that the defence is a written prohibition on the direction of the sentence, not care.

**Cost:** zero dependency; two prose rules and one rendering constraint. The Darwin Core lesson — qualifier inside the token — is worth one concrete adoption: make the rendered form of any served value *contain* its rung (`P3 · FITTED`), so a copy-paste into an email carries it. This is also the `TERM=dumb` / printed-program path §15 requires, and it means the accessible path and the anti-laundering path are the same implementation.

### 8. Nanopublications — assertion, provenance and publication-info as three separate graphs

**Verified**: `fair-workflows/nanopub` is Apache-2.0, actively maintained (copyright notices through 2025, live CI), signs publications with RSA keys generated at setup, and supports **retraction** as a first-class operation rather than deletion. The four-named-graph structure (head / assertion / provenance / publication-info) is **partially verified** — the library README confirms assertion graphs, provenance helpers (`add_prov_generated_time`, `attribute_publication_to_profile`), signing, and retraction, but I could not fetch the guidelines document for the normative graph definitions (`nanopub.net` 403'd, the guidelines repo path 404'd). Treat the structural claim as a strong lead.

Why it is on the list anyway: the split it makes is the one §15 makes, and the pairing is instructive. The *assertion* is the claim. The *provenance* graph says where the claim came from. The *publication-info* graph says who published this nanopublication and when — which is a statement about the **record**, not about the claim. Provenance versus seal-state, as separate graphs rather than separate columns, so that a claim can be re-published by someone else without rewriting its provenance, and so that the act of standing behind something is itself a dated, attributed, signed object.

That last property is item 16 (`a student's entries are as durable as entries about them`) and item 3 (`never revoke by deleting`) in the same mechanism: retraction is a new nanopublication *about* the old one. Nothing is removed; the seal is withdrawn by a further signed statement. For a system where a court order can arrive mid-season and where "a machine answer is a `draft` until a named human seals it," the interesting question is what happens when the human who sealed it withdraws — and nanopub's answer is that unsealing is an event with a name and a date, not a column flipping back.

**Cost:** do not adopt the library — RDF, named graphs and a distributed publishing network are wildly wrong for a single-box SQLite school app, and adding an RDF store to hold provenance would be a §16 pair with no plausible middle. Adopt the shape: a `seal_events` table (`target_row`, `action` ∈ `seal | unseal | reject`, `actor`, `at`, `reason`) rather than a `seal_state` column, with current state derived. `seal_state` then becomes a view, and §15's note that *"a stored status and an enforceable one are not the same question"* gets an answer: the stored one is the projection, the events are the record. Moderate cost — this is a data-model decision, cheap now and expensive later, and it also satisfies item 10's requirement that rejections be recorded as durably as approvals, which a single mutable column cannot do.

### 9. C2PA and the manifest-as-sidecar idea — worth reading, wrong size to adopt

**Verified**: `contentauth/c2pa-rs` is dual MIT / Apache-2.0, very active, spec at 2.4. Validation status constants exist (`CLAIM_MISSING`, `ASSERTION_MISSING`, `ASSERTION_DATAHASH_MISMATCH`, `MANIFEST_INACCESSIBLE`, `GENERAL_ERROR`, …) and log items carry a `LogKind` of `Success` or `Failure`.

Two things transfer conceptually. First, a C2PA manifest is provenance that travels *with* an asset without altering it, and validation collects a list of status items rather than returning one boolean — a failed assertion is a named code with a location, not a thrown-away false. That is the right shape for a provenance evaluator: return the findings, let the caller render them, and never reduce to a pass/fail that the UI then has to invent an explanation for.

Second, an honest gap I could not fully resolve and will not paper over. The specification text describes validators determining whether data is *well-formed, valid, trusted, or unknown* — a four-way outcome with `unknown` first-class. The Rust SDK's log kind that I could read is binary (`Success` / `Failure`), with `MANIFEST_INACCESSIBLE` sitting on the failure side as a code. So "we could not check" and "we checked and it failed" appear to be distinguished by *which code* rather than by *which kind*, and the `unknown` tier appears to live in trust-list evaluation rather than in the validation log. I read one file, not the SDK. If someone wants to cite C2PA as precedent for item 13, that gap is where to look first — and either answer is useful: precedent if the tiers are distinct, a second MISP-style counter-example if they collapse.

**Cost of actual adoption: too high, and don't.** Certificates, a trust list, and a signing infrastructure for a program that needs three ordinal ladders and a SQLite file. It is also `MEDIA_MINOR`-adjacent — signed provenance on student photos and performance video is a genuinely interesting future question and a genuinely bad first commit. Read-only interest, revisit if media handling ever gets its own phase.

---

## Weirdest things I found

1. **MISP encodes "reliability cannot be judged" as the number 50 — the same number as "fairly reliable."** A widely-deployed threat-intelligence taxonomy, funded and maintained, ships `CLAUDE.md` item 13's exact violation as data. And its sibling implementation of the same scale (`cti-python-stix2`) *raises an exception* on the same rung for the same reason the project would. One scale, two open-source implementations, opposite positions on whether absence may become a result. I did not expect the argument to be settled by a diff between two files.

2. **Wikipedia has a citation state for "the source came back as something hostile."** `url-status=usurped` — the domain got resold to advertising, malware or a phishing operation, and rendering **suppresses** the link. Fifteen years of maintaining more citations than anyone else produced a state neither this document nor almanac-template has: not `dark`, not `drift`, but *resurrected as an adversary*. For an app that renders district and booster-club links to guardians, this is the state most likely to be needed and least likely to be predicted.

3. **ENFSI forbids forensic scientists from writing sentences in a particular grammatical direction.** Not from reaching a conclusion — from *phrasing* it as a statement about the proposition rather than about the evidence. "This fibre came from the suspect's coat" is a reportable error even when the likelihood ratio is enormous. A whole profession decided the failure mode was a sentence shape, and wrote the prohibition at the level of the sentence. §15's judge-calibration join needs exactly this rule and does not have it.

4. **A 1990s scientific file format solved "scales never compare as bare integers" by refusing to let the integers travel alone.** CF Conventions require `flag_values` and `flag_meanings` in the same file, one meaning per value, and put the quality code in a *separate variable* that the data variable points at via `ancillary_variables` — so provenance physically cannot gate the value, because ignoring the pointer still yields the data. And `ioos/compliance-checker` fails the file when the meanings are missing or the counts disagree. The invariant, the layout, and the mutation test, from oceanography.

5. **Botanists smuggle uncertainty inside the name so nobody can strip it.** `Quercus cf. alba` — the qualifier lives in the identification string, not a neighbouring column, because a hedge in its own field gets dropped by the next CSV export and the specimen arrives downstream looking confidently identified. Darwin Core standardizes this as `identificationQualifier`. The same instinct that makes `field-acoustics` write the word `ASSUMED` into the headline, discovered independently by people whose downstream consumers were other people's spreadsheets.

6. **The IPCC keeps a scale whose entire purpose is to be used when you cannot use the better scale.** Evidence-and-agreement exists for findings where confidence and probability cannot be judged — so the shape of the sentence tells you which rung of *epistemic access* the authors reached. Absence is not `unknown` and not withheld; it is a statement in a visibly coarser vocabulary. This is the most sophisticated version of item 13 I found, and it is in a climate report.

---

## What I did not find

No open-source project that renders an ordinal trust level with a **verified** guaranteed-text path in the way §15 requires (glyph or label carrying the same information as colour, with a `TERM=dumb` route). WCAG SC 1.4.1 is the normative rule and everyone cites it; I could not verify a concrete implementation that *tests* for colour-only encoding of an ordinal scale before running out of search budget. `safe-design`'s token/parity approach as described in §15 may genuinely have no open-source equal, which would make it the fleet asset worth keeping rather than replacing. Worth one more scouting pass with fresh budget — search terms that were queued and unspent: "axe-core color-only rule ordinal", "GOV.UK Design System tag component text required", "textual rich accessible status glyph", "CVSS qualitative severity rating scale not risk".

Also unverified: SLSA's track-prefixed levels (`Build L1–L3`) and whether the spec states levels are incomparable across tracks. `slsa.dev` 403'd and three repo paths 404'd. If it says what I think it says, it is the mainstream precedent for prefixing rungs — a levels ladder that was renamed from bare `SLSA 1–4` precisely because bare integers were being compared across incomparable dimensions. Cheap to check with a working fetch.
