# Scout 12 — Consent as machinery, media of minors, dignity-first design

Scope: `docs/ARCHITECTURE.md` §7.2, §7.3, §8/§8.2, §10; `docs/CAPABILITY-MAP.md` §6, §12, §16, §18, §20; `CLAUDE.md` refusals 1–7 and shapes 8–20.

---

## 0 · Method, and an honest statement of what I could and could not verify

Read this first, because it changes how much weight each entry below can carry.

- **WebSearch was unavailable.** The session's search budget (200/200) was already spent when this task started. Discovery therefore ran through the GitHub repository/code search API plus direct fetches of `github.com` and `raw.githubusercontent.com`.
- **The egress proxy denies most non-code hosts.** Confirmed 403 at the CONNECT layer for `w3c.github.io`, `consentfultech.io`, and (from the proxy's own recent-failure log) a long tail of standards-body and institutional domains. So **specs, zines, design guides and district-review artifacts that live on their own websites could not be opened.** Where I name one, it is marked `UNVERIFIED LEAD` and you should treat it as a search string for a future session, not as a finding.
- **Everything in the ranked tables was verified against its actual repository this session** — license read from the LICENSE blob where one exists, activity from the API's `updated_at`/`pushed_at` or the commits page, archived flag from the API. Where a field could not be established I say so rather than guessing.
- Consequence for the four targets: **Targets 1, 2 and 4 came out well** (they are code-shaped, and code lives on GitHub). **Target 3's design-guidance half is under-served** — the code half (schema design for names/gender) came out unexpectedly strongly, but the trauma-informed/safeguarding/anti-surveillance *literature* is on blocked hosts. Budget a follow-up session with search enabled for Target 3 specifically.

### The single most important finding is a negative one

**There is no open-source implementation of dated, staged, independently-revocable consent for human subjects.** I went looking for one three ways:

- GitHub's `consent-management` topic, `stars:>30`: **14 repositories, and every functional one is a cookie banner** — Consent-O-Matic, Klaro, Orejime, consent-banner-js, WordPress `wp-consent-level-api`, three CMS plugins. Not one models a data subject.
- Keyword search across name/description/readme for consent-record/receipt/withdraw/revoke vocabulary: 17 results, no relevant implementations (the result set is SEO spam and unrelated crypto/agent repos).
- `consent2share` (SAMHSA's 42 CFR Part 2 consent-segmentation platform, which was the strongest historical candidate for staged consent): **0 results on GitHub.** It is not discoverable there any more.

So §7.3's claim — *"no dated or revocable consent exists anywhere in the fleet"* — extends outward. It does not exist in open source either, as a library you could adopt. What exists is (a) **specifications** with the right field set, (b) **one production application** that implements a partial version of it for exactly this population, and (c) **one protocol RFC** that gets owner ≠ subject more right than anything else I found and then leaves revocation as a literal `TODO`. Those three are the top of the report.

This is good news for §17: the middle terpsi-music has to build is genuinely unbuilt, so building it well is the fleet's contribution rather than a vendored copy (§16).

---

## Target 1 — Consent as a record, not a checkbox

### Ranked

| Project | What | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|
| **primeroIMS/primero** | UNICEF child-protection case management (CPIMS+/GBVIMS+). Consent is a *validation on the disclosure object*, defaulting to deny | AGPL-3.0 | Live: `updated_at` 2026-07-29, 33 open issues, not archived; JS + Ruby/Rails, 74★ | §7.2 gate-the-export; §7.4 W-1/W-3/W-4; CLAUDE.md #9, #10, #13 | **steal-the-idea (hard), read the code line by line** |
| **decentralized-identity/aries-rfcs #0103 "Indirect Identity Control"** | Delegation vs guardianship vs controllership as one modelled family; proxy trust framework + proxy credential + proxy challenge | Apache-2.0 (repo) | Repo live (`updated_at` 2026-07-21, 343★); **RFC itself status PROPOSED since 2019-06-04 and never advanced** | §7.3 owner ≠ subject; §7.1 dated termination; §7.4 W-2/W-5/W-7; I-6 | **steal-the-idea — this is the missing doctrine's data model** |
| **w3c/dpv** (Data Privacy Vocabulary, incl. the ISO/IEC 27560 consent-records guide) | Ontology + taxonomies for purposes, legal bases, rights, and a dedicated *Implementing ISO/IEC 27560:2023 Consent Records and Receipts* guide | W3C Document License | Active, 79★, not archived; sector extensions incl. **Education** | §10 compliance map; the `Consent` entity's field set; §15 provenance | **adopt the vocabulary, not a dependency** |
| **ethyca/fides** | Privacy-engineering platform: data map, `fideslang` taxonomy, DSR request fulfilment with an approval workflow | Apache-2.0 | Active, Python, 473★ | §10 data inventory; Target 4 overlap | **read-only interest** (server + admin UI + Postgres; heavy for a school hub) |
| **w3c/odrl** | Policy expression language — permission/prohibition/duty over assets with constraints | W3C CG | Active, 41★, 62 open issues | Grant expression for guest judges; `MediaAsset` release terms | **read-only interest** |
| **authzed/spicedb** / **openfga/openfga** | Zanzibar-style relationship-based authorization; "guardian-of" is a relation, not a role | (not read this session) | Both very active, 6.9k★ / 5.5k★, Go | §7's resolver; W-2 one-ward grants | **read-only interest** — see caveat below |
| **privacybydesign/irmago** (Yivi/IRMA) | Attribute-based credentials with selective disclosure; a real deployed European stack | (not read this session) | Active, Go, 83★, 83 open issues | Guest/judge attestation without identity dump | **read-only interest** |
| **MuckRock/muckrock** | FOIA request tracker: every request has a filed date, a statutory clock, a dated disposition, and a public wait | **No LICENSE file in the repo** — unlicensed, do not vendor | Active, Python, 122★, 297 open issues | **I-6 "silence is not a disposition"** | **steal-the-idea only** |
| Klaro / Orejime / Consent-O-Matic / `wp-consent-level-api` | Cookie consent | MIT-ish | Active | nothing | **reject** — named so the next scout does not re-walk this ground |

#### Top find 1 — Primero: consent as a fail-closed validation on the disclosure, with the override in the same row

This is the most directly transplantable thing in the whole report, and it is in production in humanitarian child protection, i.e. the closest real-world analogue to a program holding minors' records under a threat model that includes people with legitimate credentials.

Verified structure. `Transition` (`app/models/transition.rb`) is the base class for every act of moving a case between people or organisations — `Assign`, `Referral`, `Transfer`, `TransferRequest`. It carries:

```ruby
validate :consent_given_or_overridden

def consent_given_or_overridden
  return if consent_given? || consent_overridden
  errors.add(:consent, 'transition.errors.consent')
end

def consent_given?
  false          # base class denies
end
```

Four properties, each of which terpsi-music has a rule for:

1. **The base method returns `false`.** A new disclosure type that forgets to answer the consent question is refused, not permitted. That is CLAUDE.md #13 and §10's fail-closed idiom expressed in eight lines. Compare `openclaw-sap-gate`'s empty-fingerprint default (§7.2): same position in the design, opposite default.
2. **Consent is answered per disclosure kind, from the subject's own record.** `Assign#consent_given? → true` (moving a case between colleagues inside the org is not a disclosure). `Referral#consent_given?` / `Transfer#consent_given?` → `record.consent_for_services` for the GBV module, `record.disclosure_other_orgs` otherwise. So the same consent field means different things at different boundaries, resolved at the boundary.
3. **`consent_overridden` is a persisted column on the disclosure row.** The override is not a bypass, it is a recorded fact stored next to who transitioned it, to whom, when, and under which `authorized_role_unique_id`. This is CLAUDE.md #10 — *record rejections as durably as approvals* — generalised to *record overrides as durably as consents*. `TransferRequest` sets `consent_overridden: consent_individual_transfer`, so even the override's basis is a field.
4. **Three independently-revocable consent flags exist on the child record** (`app/models/child.rb`, verified in the `Child` attribute list): `consent_for_services`, `consent_for_tracing`, `disclosure_other_orgs`. Each gates a different downstream capability. `consent_for_tracing` is the striking one: `MatchingService#find_match_records(match_criteria, match_class, require_consent = true)` means **consent determines whether a record is even eligible to appear in family-tracing search results.** A record without tracing consent is not "found and hidden" — it is not a candidate.

That last point is the one to take into §8. `Nestor`'s `EntityResolver` reconciling *Robert Smith* / *Bobby Smith* / *R. Smith* is structurally the same operation as family tracing, and Primero's answer is that **the consent predicate belongs inside the matcher, not around it.** A resolver that matches first and filters after has already computed the link.

Two more Primero mechanisms worth naming:

- **`hidden_name`** (boolean on `Child`) plus `RecordDataService#embed_hidden_name`, which replaces the name with asterisks (`expect(data['name']).to match(/\*+/)`), alongside `case_id_code`, `client_code`, `name_nickname`, `name_other`. Pseudonymity is a per-record property of the subject, applied at serialisation, and `PermittedFieldService` only admits `hidden_name` itself to users who `can?(:update, model_class)`. So *whether this person is name-masked* is itself a gated field.
- **`Transition` status vocabulary**: `in_progress` / `accepted` / `rejected` / `done` / `revoked`, with `rejected_reason` and `responded_at`. A disclosure request is a durable object with a dated disposition and a recorded refusal — I-6 and CLAUDE.md #10 in a state machine that already exists.

**Transplant.** Do not vendor Primero (AGPL-3.0, Rails + a large React admin, and its CPIMS+/GBVIMS+ configuration bundles are gated behind an email request per its own LICENSE — that alone makes it a partial artifact). Take the shape:

- a `Disclosure` record (terpsi's `Export`, per §7.2's read-vs-export split) whose validity *requires* a consent predicate that defaults to refusing;
- `consent_overridden` + `override_basis` + `overridden_by` as columns on that record, never as a log line elsewhere;
- consent as several independently-settable predicates named after the act they permit (`consent_media_release`, `consent_directory_info`, `consent_adjudication_recording`, `consent_share_district`), not one `consented: bool`;
- the consent predicate compiled *into* the resolver/matcher and the export query, matching §7's "one SQL predicate" discipline.

**Cost.** Small — this is a schema decision plus a validation, and it is one of the cheap ones *if made now*. Retrofitting it is the §7.4 W-3 migration problem. Real cost is the adversarial tests: per CLAUDE.md #19 and §10's mutation gate, each consent predicate needs a test that flips it to `true` and asserts the export still refuses when the *other* predicate is unset, and a mutation that neuters `consent_given?`'s `false` default and watches the suite go red.

**Gap you must fill.** Primero's consent fields are **booleans, not dated records.** No `valid_at`/`invalid_at`, no timebound declared at issuance, no staging. So Primero solves *enforcement* and leaves *time* open; §7.1 is still terpsi's to write. Say that plainly in §14 rather than logging Primero as "exists."

#### Top find 2 — Aries RFC 0103: the owner ≠ subject data model, with revocation left as a TODO

§7.3 says the fleet's hardest open problem is owner ≠ subject and that `corpus-lens` declared it out of scope. RFC 0103 (Daniel Hardman, 2019) is the most careful published attempt at it I could find, and its structure answers several §7.4 clauses directly. Verified from the RFC source and its sample trust framework.

The model: a **proxy trust framework** (published, versioned, semver, addressable by URI) + a **proxy credential** binding `holder` to `proxied` + a **proxy challenge** that evaluates the credential *in context* at use time.

What to take, clause by clause:

- **`credentialSubject.proxied.permissions` — the permission model belongs to the ward, not to the guardian.** The guardian's credential carries `holder.role`; the *permissions* live on the proxied identity and the challenge compares role against them. This is a better shape than a grant-per-guardian table, and it makes **W-2 true by construction**: there is exactly one `proxied`, so "the drumline" is not expressible. A wildcard scope is not rejected by a validator; it has nowhere to live.
- **`holder.rationaleURI` — required for guardianship, optional for the others.** The sample framework enumerates `dependent-appointment` (strongest), `kinship` (with an ordered sub-vocabulary `biological-parent` → `step-parent` → `sibling` → `grandparent` → `aunt-or-uncle` → `first-cousin` → `indirect-relative` → `tribe-adult`, and *kinships weaker than `first-cousin` are invalid as a rationale on their own*), `adjudicated` (a legal authority — or, memorably, a council of five grandmothers), and `self`. **This is §7.1's answer.** A guardianship whose rationale is `adjudicated` is a different object from one whose rationale is `kinship`, and the court order arriving mid-season changes the rationale and the dates rather than deleting a row.
- **`auditURI` and `appealURI` are mandatory disclosure fields on the credential.** Every grant names, at issuance, where its exercise is recorded and who hears an appeal. Compare I-6 (every ask gets a dated disposition, and the office cannot lengthen its own timebound) and W-7 (halt and escalate — `appealURI` *is* the escalation target, declared up front instead of improvised during the conflict).
- **`holder.constraints.*`** — time, place, circumstance. The sample defines `boundaries` (localised, with the rule that **if one locale's description is more permissive than another's, the most restrictive reading governs** — a good rule for a multilingual parent-facing surface, cf. capability map §18 language access), `point_of_origin` + `radius_km`, `jurisdictions`, and — the one to steal outright — **`biometric_consent_freshness`**. A constraint whose subject is *how recently consent was confirmed*. That is a timebound expressed as a precondition of use rather than as an expiry date on a row, and it is exactly what a consent-to-record-a-performance needs.
- **The permission vocabulary in the sample is uncomfortably instructive.** `routine-medical-care`, `school` ("Enroll or unenroll dependent in school programs"), `light-travel` ("outside the camp, returning before dark"), `extended-travel`, `necessaries`, `contracts`, `delegate`, `successor`, `authorize`, and `gender-identity` ("Specify the gender by which the dependent shall be known"). A guardian permission to *set another person's gender* is in a published sample trust framework. Read alongside capability map §6 (attire policy and gender presentation "needs an explicit, humane design rather than an accidental one") and line 472 (chosen name and pronouns distinct from the SIS legal record), this is the concrete warning: **if you do not decide who may set a student's name and gender, your schema will decide it, and the default will be the guardian.** Cross-reference Target 3.
- **The RFC's own honesty about the threat model** is worth quoting into §7: *"Since guardianship does not always derive from dependent consent... the dependent in a guardianship relationship is particularly vulnerable to abuse from within."* And: guardianship is *"the most likely of the three forms of indirect control to require an audit trail."* That is the abuser-with-legitimate-credentials threat model stated by a protocol spec, and it is the argument for §7.2's inversion (announcement loudest for the least trusted) being applied to *guardians*, not only to guests.

**Do not adopt the technology.** It presumes W3C Verifiable Credentials, DIDs, ZKP link secrets, and Evernym's SGL rule language (`{"grant": …, "when": …}`) hosted at `evernym.github.io` — Evernym no longer exists as an independent company and I could not verify SGL has a live repository (GitHub search for it returned nothing). The RFC has been `PROPOSED` since June 2019 with a status note pointing at a Sovrin task force Google Doc. **And the revocation section is, verbatim, `[TODO: discuss offline mode, freshness, and revocation]`.** So the best published model of guardianship in open source has an empty hole exactly where §7.1 lives.

**Transplant.** Restate RFC 0103's ingredient list as a local, versioned contract in terpsi's own terms — precisely the treatment §7.2 recommends for SAP/1.0. Concretely: a `Guardianship` edge gains `rationale` (enum, with `adjudicated` distinguished from `kinship`), `basis_document`, `valid_at`, `invalid_at`, `audit_target`, `appeal_target`, and `constraints`. Fill the RFC's TODO with §7.1's dated termination and you have closed the fleet's named hardest problem, in a form you can point at a prior art document for.

**Cost.** Days of design, not weeks of code — the edge already exists (§9 foundation 1, built). The expensive part is the vocabulary work: `rationale` and `permission` enums have to be enumerated and versioned, because an unversioned enum in a consent record is §16's rot problem with a court order attached.

#### Top find 3 — DPV + ISO/IEC 27560 for the `Consent` entity's field set

`w3c/dpv` is active, W3C Document Licensed, and — verified from the repository index — ships an established guide at `w3id.org/dpv/guides/consent-27560`, *Implementing ISO/IEC 27560:2023 Consent Records and Receipts*, plus a sector extension for **Education**. I could not open the guide itself (`w3c.github.io` and `w3id.org` both 403 through the proxy), so **I am not quoting its field names.** What I can assert: the alignment exists, it is maintained under W3C, and it is the right citation to put in §10's compliance map so that the `Consent` entity's shape has a named publisher rather than being invented locally (cf. capability map §12's argument that an uncited threshold is a `P5` assumption in a policy counsel will read).

**Transplant.** Cheap and high-value: adopt DPV's *vocabulary* as the naming source for `Consent.purpose`, `legal_basis`, and `Right` — an ontology reference, not a runtime dependency, so no cloud and no egress. **Action for the next session with search enabled: open the 27560 guide and extract the actual field list before the `Consent` schema is frozen.** Do not freeze it first.

#### Read-only, with a caveat I will not paper over

SpiceDB and OpenFGA are the obvious ReBAC engines for "guardian-of" as an edge, and both are extremely active. **I did not verify this session whether either expresses `valid_at`/`invalid_at` natively** (SpiceDB's caveats mechanism is the candidate). Since §7.1's whole point is dated validity, treat "use SpiceDB for guardianship" as an unproven claim until someone checks. Also note both are servers — adding one to a school hub is a network dependency and a §7.2 "which of five gates do we depend on" problem, not a library import.

`MuckRock/muckrock` has **no LICENSE file**. It is a fine thing to read for the I-6 pattern (a request object with a filed date, a statutory clock, a dated disposition, and the wait itself made visible) and it must not be copied.

---

## Target 2 — Media of minors

`MediaAsset` carries consent state as a first-class field. The tooling to *act* on that field is the healthiest ecosystem in this report, and it is almost entirely local-first, because it was built by and for people who could not send the file to a cloud.

### Ranked

| Project | What | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|
| **everestpipkin/image-scrubber** | Browser-only protest-photo anonymiser: strips EXIF, *shows you what it is removing*, paint + blur redaction, works offline as an installed PWA | MIT | `pushed_at` 2022-02-25, 1009★, **not archived — dormant but complete**; single-page JS | `MediaAsset` redaction at the human step; §5.1 sandbox; the drop (§3) | **adopt (vendor the file)** |
| **ORB-HD/deface** | CenterFace/ONNX face detection → box or blur, images *and* video, CLI, fully offline | MIT | `pushed_at` 2024-10-13, 1522★, 37 open issues, not archived; Python | Bulk pass over event media before any egress | **adopt** |
| **exiftool/exiftool** | The metadata reader/writer. Nothing else is close | GPL | Very active, 4911★, Perl | Metadata scrub + verification that the scrub happened | **adopt (as a verifier, see below)** |
| **contentauth/c2pa-rs** | C2PA provenance manifests: signed assertions bound to the asset, incl. CAWG identity assertions | MIT **and** Apache-2.0 | Active, 373★, 208 open issues, Rust | **Consent state travelling *with* the asset**; §15 provenance ladder; I-10 treaty crossings | **steal-the-idea, strong** |
| **facebookresearch/videoseal** | Invisible video/image watermarking. PixelSeal 256-bit, ChunkySeal 1024-bit, VideoSeal v1.0 256-bit; local PyTorch, TorchScript standalone | MIT | Active, 716★, Python | Per-recipient traceable distribution of performance video | **steal-the-idea / pilot** |
| **adobe/trustmark** | Arbitrary-resolution image watermarking, from the Content Authenticity project | MIT | Active, 130★ | Same, for stills; pairs with C2PA | **read-only interest** |
| **microsoft/presidio** | PII detection + anonymisation, incl. an image redactor over OCR | MIT | Active, Python | Redacting *documents* — medical forms, rosters, scanned releases | **adopt for the form path** |
| **hukkelas/deep_privacy2** | Full-body realistic anonymisation (GAN), not just faces | Apache-2.0 | Active, 381★, Python | Research interest — see the warning below | **read-only interest** |
| **Horizontal-org/Tella-Android** | Human-rights documentation app: encrypts and hides sensitive media on-device, then uploads to *your* server | MIT | Active, Kotlin, 102★ | The parent/staff capture app's threat model; §4.2 confidential transport | **steal-the-idea** |
| **OpenArchive/Save-app-ios** (+ `save-dweb-backend`, Veilid/Iroh) | Media archiving for at-risk documenters, with attribution/credit choices at capture | GPL | Active, Swift/Rust, 20★ / 25★ | Consent-and-attribution captured *at capture time* | **read-only interest** |
| **bellingcat/auto-archiver** | Pluggable archiving pipeline with enrichers/formatters | (not read) | Active, 1101★, Python | Pipeline *shape* for a media ingest with mandatory stages | **read-only interest** |
| **guardianproject/ObscuraCam** | The original face-blur camera (Guardian Project + WITNESS) | GPL-3.0 | **Effectively abandoned** — newest commit 2024-10-07 is a Weblate translation merge; last substantive commits 2022-03; 345★, not archived | historical | **read-only interest — do not build on** |
| **mat2** (Metadata Anonymisation Toolkit 2) | The best metadata scrubber after exiftool; GNOME "Metadata Cleaner" wraps it | — | **Could not verify.** Not on GitHub; upstream is `0xacab.org`, which this session's proxy blocks | metadata scrub | **UNVERIFIED — check next session** |

#### Top find — image-scrubber, and the reason it is better than its competitors for *this* use

Verified from the repo README: it removes EXIF, **"The program will display the data it is removing"**, offers paint *and* blur, caps at 2500×2500, and states **"All processing happens directly in the browser — no information is stored or sent anywhere"**, with instructions to load the page and then switch on airplane mode before opening any image.

Three things make this the right adopt:

1. **It narrates the redaction.** It shows the operator the metadata it is about to destroy. That is §7.2's "narrate the read" applied to a destructive operation, and it is the difference between a scrubber and a scrubber you can put in front of a booster-club volunteer.
2. **It is structurally incapable of egress**, and it is a single MIT-licensed page you can vendor into the hub and serve from Zone A. No model download, no Python, no GPU. Contrast every cloud "redaction API": disqualifying under CLAUDE.md refusal 1 anyway, since `MEDIA_MINOR` may not leave.
3. **Its own README states the design fact that should become a rule here:** *"The blur function has built-in pixel shuffling/noise and is fairly secure but sensitive information should be covered with the paint tool."* **Blur is a weaker guarantee than occlusion.** For a photo of a minor whose family declined the release, the operation must be opaque paint or the asset must not exist in the published derivative at all. Write that into §8 next to the `MediaAsset` constraint, because "we blurred the faces" is the sentence that will be offered as compliance.

This is also the argument against `deep_privacy2` for anything parent-facing. Synthesising a plausible replacement face over a real child is a *generative* act on `MEDIA_MINOR`; it is fascinating research and it is not a consent mechanism. Keep it read-only.

**Cost.** image-scrubber: hours (vendor one page, add it to the media pipeline as the human redaction step, add a test that the saved output has no EXIF using exiftool as an independent checker). Note §16 — vendoring it creates a pair, so name the reconciler in the same commit: a pinned upstream commit hash plus a test that fails if the vendored copy drifts. And per §10's finding that six defects were in the verification apparatus: the EXIF test must use a *different* tool (exiftool) than the scrubber, or you get the fleet's fixture-that-hashes-with-the-function-it-reads-back failure.

#### The genuinely new idea — C2PA as the carrier for consent state

This is the transplant I would most want in §8, and I have not seen it proposed.

`MediaAsset.consent_state` as a database column protects the asset while it is inside the system. The problem §8 actually names is *after publication* — and a column does not travel. C2PA manifests are signed assertions cryptographically bound to the asset, they support custom assertions, and `c2pa-rs` is dual MIT/Apache-2.0, Rust, active, with CAWG identity assertion support.

So: **when the system emits a derivative of a `MEDIA_MINOR` asset, it writes a C2PA manifest asserting (a) the consent state that authorised this emission, (b) the redaction operations applied, (c) which release covered it and its timebound, (d) the sealing human (§8.2's `sealed`, not `draft`), signed by the program's key.** A photo that escapes then carries its own provenance, and a downstream holder can tell an authorised derivative from a copy. This maps cleanly onto §15's `P1–P5` provenance ladder and onto I-10 (*"exports are treaty-scoped, drawn from verified-tier records only, and the seam is not a side door"*) — a C2PA manifest is precisely a treaty document attached to the crossing.

**Cost.** Real but bounded: a Rust dependency in Zone A, a signing key in the §5 hierarchy (which raises escrow — the one thing §5 says nothing covers), and a decision about whether manifests are emitted for internal derivatives or only at egress. Start at egress only. **Caveat verified honestly:** I confirmed `c2pa-rs` implements "several common C2PA assertions and hard bindings" and supports CAWG identity assertions; I did **not** confirm this session that custom assertion authoring and assertion *redaction* are exposed in the SDK's current API. Check before committing.

#### Per-recipient traceable distribution

`facebookresearch/videoseal` (MIT, active, 716★) gives 256-bit and 1024-bit payloads embedded locally in video. 256 bits is far more than enough to encode a recipient ID plus an issuance date. The use case is real and specific: a competition recording distributed to five adjudicators and three staff, where a leak needs to be attributable. Combined with the C2PA manifest above you get *both* an overt provenance record and a covert recipient mark.

Be honest about two things. The repo does not document per-recipient keying as a use case — you are building that on top. And a watermark is a deterrent and a forensic aid, not a control; per §7.2's read/export split, the control is still that the export was gated and announced. **Do not describe watermarking as enforcement.** It is a ledger written into the pixels (CLAUDE.md #18).

---

## Target 3 — Dignity and anti-surveillance design for tools used *on* young people

This is where the proxy hurt most. The code half came out much better than expected; the guidance half I could not verify at all.

### Ranked

| Project | What | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|
| **HL7/fhir-gender-harmony** (Gender Harmony cross-paradigm IG, Edition 1) | Splits the single "sex/gender" field into **Gender Identity (GI)**, **Sex Parameter for Clinical Use (SPCU)**, **Recorded Sex or Gender (RSG)**, **Name to Use (NtU)**, **Pronouns** — each with cardinality and a **Validity Period** | No LICENSE file in repo (HL7 IP policy applies) | Repo `updated_at` 2025-08-04, 2★ — small because it is a spec source, not an app; the standard itself is published and balloted | Capability map line 472 (chosen name/pronouns vs SIS legal record), §6 attire/gender presentation, §8 `Person` facets, CLAUDE.md #13 | **adopt the model wholesale** |
| **primeroIMS/primero** `hidden_name` + `case_id_code` + `PermittedFieldService` | Per-subject pseudonymity applied at serialisation, with the masking flag itself permission-gated | AGPL-3.0 | Active | Capability map §18 "structurally invisible to peers"; §7.3's session_scope done right | **steal-the-idea** |
| **HL7/cda-sex-gender-representation** | The CDA companion templates | — | Exists, `updated_at` 2025-08-25, 0★ | same | **read-only interest** |
| **openreferral/specification** (HSDS) | Human Services Data Specification — how to model services, eligibility and access without modelling the person | — | Active, 129★, branch `3.2` | Capability map §18 anonymous need identification; fee waivers, meals, transport | **read-only interest** |
| **kobotoolbox/kpi** | Offline-first form collection built for humanitarian "do no harm" contexts | AGPL-3.0 | Active, Python, 178★, 551 open issues | Consent forms and medical forms captured offline at band camp | **read-only interest** |
| **ushahidi/platform** | Crowdsourced reports with per-post visibility and protected fields | (not read) | Active, PHP, 726★ | Capability map §12 anonymous concern reporting for hazing/harassment | **read-only interest** |
| Design guidance: Consentful Tech Project (FRIES), Designing for Children's Rights (D4CR), UNICEF RITEC, 5Rights / Age Appropriate Design Code, IEEE 2089, eSafety Safety-by-Design, "Trauma-Informed Computing" (CHI 2022), Our Data Bodies *Digital Defense Playbook*, EFF *Spying on Students* | Design literature | — | §7.2 announcement design; guardian visibility vs surveillance; streaks | **UNVERIFIED LEADS — all on proxy-blocked hosts; do not cite until opened** |

#### Top find — Gender Harmony solves the chosen-name/legal-name schema problem, and it does it by making the legal record *one issued document among several*

Verified by reading `input/pagecontent/model.md` and `background.md` in `HL7/fhir-gender-harmony`. The model decomposes into five person-level attributes: **Gender Identity (GI)**, **Sex Parameter for Clinical Use (SPCU)**, **Recorded Sex or Gender (RSG)**, **Name to Use (NtU)**, **Pronouns**.

The four properties that make it the right answer for a school records system:

1. **Gender Identity has cardinality `0..n`, each instance with its own `Validity Period`** ("The time frame during which this Gender Identity applies"), and the guide states validity periods **may overlap**. So identity is a dated, multi-valued, append-only history — not a column you overwrite. A student's record in September and the same record in March are both true, both dated, and neither destroys the other. That is CLAUDE.md #3's *never revoke by deleting* applied to identity, and it is the same `valid_at`/`invalid_at` shape §7.1 needs for guardianship. **One temporal-validity mechanism, two uses** — which is exactly what §16 wants: a named middle rather than a second implementation.
2. **RSG carries an `Issuer`.** The IG's own changelog records the field being renamed *from* "Jurisdiction" *to* "Issuer" (Jira OTHER-2586). The consequence is the important part: the legal/administrative sex-or-gender value is modelled as **an assertion made by a named issuer on a document**, plural, not as a fact about the person. Read against §8's `Person` facets: the SIS's value is not `Person.gender`, it is `RecordedSexOrGender(issuer: SIS, valid_from: …)`, sitting beside `NameToUse` and beside whatever the passport says. **This is what stops the printed concert program from deadnaming a student** — NtU is a first-class attribute with its own cardinality, not a nickname field hanging off the legal name, and the program renders NtU because that is what NtU is *for*.
3. **Pronoun binding strength was deliberately loosened from extensible to `example`** so jurisdictions can extend the value set. A closed pronoun enum is a defect; the standard says so.
4. **It has an explicit answer for absence.** *"If the Person... is unable to express a personal sense of being a man, woman, boy, girl or any point on the gender spectrum, gender identity may be recorded as Unknown. Unknown can be used in cases where parents do not want to specify a value but one must be recorded."* That is CLAUDE.md #13 — *absence surfaces as `unknown`, never as a result* — written into a health standard for the exact owner ≠ subject case: **the guardian declining to answer produces `Unknown`, not a defaulted value and not a blank that reads as female.** And per §7's refusal-indistinguishability caveat, `Unknown` is also what a student who has not been asked yet looks like. The guardian's refusal and the un-asked question are the same value. That is the refusal-indistinguishable-from-absence property in Target 1, achieved for free by choosing the right vocabulary.

The IG's `background.md` also supplies the *why* in a form a district technology review will accept, with sourced numbers: the 2015 U.S. Transgender Survey (n=27,715) found 33% had at least one negative health-care experience related to being transgender and 23% avoided needed care for fear of mistreatment; it documents records being weaponised ("many jobs require that health records be released to employers") and clinicians refusing to remove diagnoses patients asked to have removed. Capability map §6 asks for "an explicit, humane design rather than an accidental one" for attire policy and gender presentation. This is the citation that makes the explicit design defensible instead of a preference.

**Transplant.** In §8's domain model, replace any single gender field with: `GenderIdentity[]` (validity period, may overlap, `Unknown` permitted and meaningful), `NameToUse` (what appears on the program, the roster, the locker tag, the caption in a judge's commentary), and `RecordedSexOrGender[]` (each with `issuer` + validity — SIS, state, competition circuit, all separately). Explicitly **do not** implement SPCU: it is a clinical-decision-support construct and terpsi-music is not a clinical system; the analogue here is a rooming or attire *constraint*, which per capability map §8 ("rooming lists with constraint rules: grade, gender, requested roommates") is a policy input and per **W-7 must halt to a human rather than compute an assignment.**

**Cost.** Moderate and front-loaded: three tables instead of one column, a rendering rule (every student-facing and public surface reads NtU; only a district/state submission reads the relevant RSG, selected by issuer), and an import rule for the SIS (I-10: the SIS value enters as an RSG assertion at the lowest confidence tier with the SIS named as issuer — **it does not become the person's gender**). Retrofitting this after the first printed program is a migration *and* a harm. This is a §9-foundation decision, not a §9-then item.

#### Guardian visibility without guardian surveillance

The capability map already contains the mechanism (§1's note on `ask-jeles`: capture off by default every launch, never persisted across launches, records only the *shape* of an activity — query class, hit count, citation count, answer length — never content). Three things I can add from verified sources:

- **RFC 0103's warning gives you the design principle**: the dependent is *"particularly vulnerable to abuse from within"*, and guardianship is the form of indirect control most likely to require an audit trail. So the §7.2 inversion should be extended: **announcement is loudest for the least trusted *and* for the closest.** A guardian reading their own ward's lane is the session most worth narrating to the ward, because it is the access that a contact restriction is meant to constrain and that looks perfectly legitimate in a permissions table. This is the shelter/DV threat model you asked me to chase, and the RFC states it in protocol language rather than advocacy language.
- **Primero's `hidden_name` is the concrete pattern for §7.3's failed `session_scope`.** `quiet-corner` put an eight-key visibility vocabulary in the frontend and enforced nothing. Primero puts the masking decision on the *record*, applies it in the serialisation service (`embed_hidden_name`), and gates the mask flag itself through `PermittedFieldService`. Same vocabulary idea, correct location. §7.3 says the vocabulary is worth taking and the enforcement location is the failure; Primero is the worked example of the right location.
- **On streaks and standings**: I found no verified open-source project taking a position on this, and the honest report is that the guidance literature I would cite (Center for Humane Technology, deceptive.design, the trauma-informed computing work) is on hosts this session cannot reach. The one thing I will assert from verified material is structural, and it comes from §7.4 W-7 rather than from a design source: **a streak is a computed comparison over time, and a standing is a computed priority between students.** W-7 forbids the second outright. A leaderboard is not a UI choice with a privacy downside; it is a prohibited computation. That argument needs no external citation.

---

## Target 4 — FERPA / COPPA / student-privacy specific open source

### Ranked

| Project | What | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|
| **the-markup/blacklight-collector** | The engine behind The Markup's Blacklight: loads a page and reports third-party trackers, session recorders, canvas fingerprinting, key/mouse logging, Facebook/Google pixels | GPL | Active, `updated_at` 2026-07-16, 235★, TypeScript | §10 COPPA row: *"no third-party trackers, ever"*; state law no-sale/no-ads posture | **adopt — as a CI gate** |
| **ethyca/fides** (`fideslang`) | Privacy taxonomy + data map as declared artifacts | Apache-2.0 | Active, Python, 473★ | §10 data inventory; the artifact counsel sees before parents see the app | **steal-the-idea (the taxonomy), reject the platform** |
| **w3c/dpv** Education extension | Sector vocabulary for education data processing | W3C Doc License | Active | §10 state-law row; privacy notice generation | **adopt as vocabulary** |
| **microsoft/presidio** | PII detection/anonymisation for text, structured data and images-via-OCR | MIT | Active | Redacting medical forms and rosters for a district review packet | **adopt** |
| **agilemobiledev/webXray** / **thezedwards/webXray** (Libert's third-party-request analyser) | Detects third-party HTTP requests and attributes them to receiving companies; the tool behind the academic literature on school/health-site leakage | (not read) | Forks only; originals 35★ / 4★, `updated_at` 2026-01 / 2025-11 — **fragmented, no clear canonical upstream** | same as Blacklight | **read-only interest** — prefer Blacklight |
| **andersju/webbkoll** | Website privacy checker (Swedish, "Dataskydd.net") | — | **ARCHIVED** (`archived: true`, 262★, Elixir) | — | **dead — do not adopt** |
| SDPC National Data Privacy Agreement (NDPA), CoSN Trusted Learning Environment, 1EdTech TrustEd Apps, Common Sense Privacy Evaluation Framework, LINDDUN / PLOT4ai threat libraries, CMU privacy "nutrition label" generator | District-review artifacts and privacy threat-modelling card decks | Mixed | — | §10; install acceptance (§11.1) | **UNVERIFIED LEADS — all on blocked hosts** |

#### Top find — Blacklight as an install-acceptance gate, not a report

§10 says *"COPPA — no third-party trackers, ever."* CLAUDE.md #18 says say enforcement or ledger. A privacy notice claiming no trackers is a ledger. `the-markup/blacklight-collector` turns it into enforcement: it is a Node/TypeScript library that drives a headless browser over a URL and returns a structured inventory of third-party requests, cookies, session-recording scripts, canvas fingerprinting, key and mouse logging, and named ad-tech pixels.

**Transplant.** Add to the install-acceptance gate alongside the §10 R16/R17 recommendation: **R18 — the parent-facing PWA and every guardian-visible surface returns zero third-party requests under Blacklight, and the check runs in CI.** Then, per CLAUDE.md #19 and the §10 mutation discipline, prove the gate can fail: add a fixture page with a single deliberate third-party pixel and assert the check goes red. That is the adversarial test I-12 requires, and it is cheap.

This also aims directly at §7.3's `quiet-corner` finding — a roadmap asserting *"the app makes zero third-party requests at runtime"* while shipping a dormant REST client against `http://127.0.0.1:8432`. A structural check would have caught the claim drifting from the code. Note the limitation honestly: **Blacklight observes runtime requests, so it catches the live path and not the dormant one.** The dormant network path needs the AST-style import check (§6 inner ring) as well. Two gates, two failure modes — and per §7.2, say which one you depend on for which claim.

**Cost.** Low — GPL, so run it as a CI tool rather than linking it into the app, which sidesteps the licence question entirely. Half a day plus the mutation fixture.

#### On privacy-notice generators and data-inventory-as-code

I did not find a credible open-source privacy-notice generator. `fides`'s value here is not its server but **`fideslang`**: the idea that the data inventory is a *declared, versioned, machine-checkable artifact in the repository* rather than a spreadsheet counsel receives by email. That is the same move §10 already makes with `willow-2.0/TRUST.md` — whose structure it correctly identifies as the valuable part: *"not a policy, a map of every path data can take, each with the switch that opens it."*

The one thing to add, and it is a §16 point: **that map is a declaration, and a declaration plus an enforcement is a pair that needs a named middle in the same commit.** The middle is a test that walks the declared paths and asserts each named switch exists and defaults closed — otherwise TRUST.md becomes the fleet's documented-gate-that-nothing-routes-through, which is precisely `quiet-corner`'s `session_scope` (§7.3) with better prose. Retargeting TRUST.md at guardians without building that check would reproduce the exact defect this app exists to avoid.

---

## Weirdest things I found

**1 — A published guardianship trust framework in which `adjudicated` guardianship may be conferred by "a council consisting of 5 grandmothers."**
Verbatim from the Sovrin ID4All Vulnerable Populations sample framework in `aries-rfcs`. It sits in an ordered kinship vocabulary (`biological-parent` … `tribe-adult`) with a hard rule that kinships weaker than `first-cousin` are invalid as a rationale on their own. The reason it matters is not the grandmothers: it is that **the framework treats "on what basis is this person the guardian" as a required, enumerated, URI-referenceable field with a strength ordering** — which is §7.1's dated-order problem approached from the issuance side rather than the termination side. And the same framework contains a guardian permission literally named `gender-identity`: *"Specify the gender by which the dependent shall be known."* Someone wrote down the power to name another person's gender as a checkbox in a refugee-camp credential. Capability map §6's request for "an explicit, humane design rather than an accidental one" now has a worked example of the accidental one.

**2 — The consent flag that changes search results.**
Primero's `MatchingService#find_match_records(match_criteria, match_class, require_consent = true)`: without `consent_for_tracing`, a separated child's record is not a candidate for family-reunification matching at all. I expected consent to gate disclosure. Finding it inside the *matcher* — so that the link is never computed rather than computed-and-hidden — reframes §8's `EntityResolver`. A resolver that matches then filters has already learned the thing consent was meant to withhold, and in a family-tracing context that is the whole harm. The most sensitive query in terpsi-music is "is this Robert Smith the same person as this R. Smith," and Primero says the consent predicate belongs *inside* that question.

**3 — The best model of owner ≠ subject in open source has an empty TODO exactly where terpsi-music's gap is.**
RFC 0103, `PROPOSED` since 2019-06-04, gets `proxied.permissions`, `rationaleURI`, `appealURI`, `auditURI` and `constraints.biometric_consent_freshness` right — and then ends with `[TODO: discuss offline mode, freshness, and revocation]`. §7.3 says *"this app is where that gap either gets closed or gets shipped unsolved."* The gap is not merely open in the fleet; it is open in the published prior art, with a TODO marker on it, and it has been open for seven years. Also worth recording as a §20 tombstone case: the RFC's own status note points at a Google Doc, its rule language (SGL) was hosted by a company that no longer exists independently, and it moved org from `hyperledger` to `decentralized-identity` — the same absorbed-and-unfindable pattern §7.2 records for SAP/1.0.

**4 — A clinical standard that specifies what to record when a parent refuses to answer.**
Gender Harmony: *"Unknown can be used in cases where parents do not want to specify a value but one must be recorded."* A refusal by the guardian and a question never asked produce the identical stored value. That is the refusal-indistinguishable-from-absence property — the thing Target 1 describes as needing cryptographic or statistical machinery — obtained by vocabulary design in an HL7 implementation guide. The cheapest solution to the hardest-sounding requirement in this brief came from a health-IT balloting process, and it arrived with `Validity Period` and multi-valued `Issuer`-bearing records attached, which also happen to be the shape §7.1 needs for guardianship. One temporal mechanism, two problems.

**5 — A protest-photo tool that tells you blur is not good enough.**
`image-scrubber`'s README: *"The blur function has built-in pixel shuffling/noise and is fairly secure but sensitive information should be covered with the paint tool."* Written for people photographing police, it is the correct rule for a photo of a minor whose family declined the release, and it contradicts what almost every school-facing product does. Worth pairing with the tool's other habit — **displaying the metadata before destroying it** — which is §7.2's "narrate" applied to a destructive act, in a 1000-star single-page MIT app that has not needed a commit since 2022 because it is finished.

Runner-up, recorded because someone will otherwise look for it: **the abandoned tier is real.** `guardianproject/ObscuraCam` (GPL-3.0, 345★, the original Guardian Project + WITNESS face-blur camera) has had nothing but a translation merge since March 2022 and is *not* marked archived, so it reads as alive. `andersju/webbkoll` is genuinely archived. `mat2` is not on GitHub and its host is unreachable from here. And `consent2share` — SAMHSA's 42 CFR Part 2 consent-segmentation platform, the one piece of prior art that actually implemented staged consent over sensitive health data — returns **zero results** on GitHub. The strongest historical candidate for the thing this project needs has left no artifact behind, which is §20's argument for tombstones stated by absence.

---

## Recommended actions, in dependency order

1. **Before the `Consent` schema is frozen**, open `w3id.org/dpv/guides/consent-27560` (needs a session with search/fetch to non-code hosts) and take its field list. Do not invent the field list first and reconcile later — that is the §16 pair with no middle.
2. **Adopt Primero's shape now**, because it is a §9-foundation schema decision: consent as several named predicates on the subject; a `Disclosure`/`Export` record whose validation calls a predicate that **defaults to refusing**; `consent_overridden` + basis + actor as columns on that same row. Add the mutation tests that neuter the default and watch the suite go red.
3. **Adopt the Gender Harmony decomposition now**, for the same reason: `GenderIdentity[]` with overlapping validity periods and a meaningful `Unknown`, `NameToUse` as the render target for every student-facing surface, `RecordedSexOrGender[]` with `issuer`. Skip SPCU.
4. **Restate RFC 0103 as a local versioned contract** (§7.2's own recommendation for SAP/1.0), fill its revocation TODO with §7.1's `valid_at`/`invalid_at`, and carry `rationale` (`adjudicated` ≠ `kinship`), `appeal_target`, `audit_target`, `constraints`.
5. **Wire Blacklight into install acceptance as R18**, with a deliberately-tracked fixture page proving the check can fail.
6. **Vendor image-scrubber; add deface for bulk; use exiftool as the independent verifier** — different tool for checking than for doing, per §10's verification-apparatus finding. Name the reconciler for the vendored copy in the same commit.
7. **Prototype C2PA manifests at egress only**, carrying consent state, redaction operations, covering release + timebound, and the sealing human. Verify custom-assertion support in `c2pa-rs` before committing. Call watermarking a ledger, never a gate.
8. **Book a follow-up scout with web search enabled for Target 3's guidance half.** The design literature (Consentful Tech/FRIES, D4CR, UNICEF RITEC, 5Rights/AADC, IEEE 2089, eSafety Safety-by-Design, trauma-informed computing, EFF *Spying on Students*) and the district-review artifacts (SDPC NDPA, CoSN TLE, LINDDUN/PLOT4ai) are all unread. Nothing in this report depends on them, and §6/§18 of the capability map does.
