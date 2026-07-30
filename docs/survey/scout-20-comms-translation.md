# Scout 20 — Communication, Translation, Calendar, Alerting

Slice: getting a short, urgent, minimal message to hundreds of households reliably, in their
language, with acknowledgment, without a vendor holding the roster.

Grounded in: `docs/CAPABILITY-MAP.md` §14 (Communication), §3 (Calendar), `docs/ARCHITECTURE.md`
§4.1 (the traffic split; SMS carries signals, never records), `CLAUDE.md` refusals #7 (never put a
record on SMS), #1 (no non-local inference on student data), #10 (machine answer is a `draft`
until a named human seals it), #13 (absence surfaces as `unknown`), #14 (prefixed ordinal scales),
#18 (enforcement vs ledger).

---

## 0 · Verification method, and its hole — read this before trusting the table

**What I verified, and how.** Every repository below was resolved against the live GitHub API or by
reading its actual files over `raw.githubusercontent.com` during this session (2026-07-30). Licenses
were read from the repo's own `LICENSE`/`COPYING` file or the API `license.spdx_id`, not from
memory. Every controlled vocabulary, state ladder, schema field, and package count quoted below was
extracted from a real file with a script, not recalled — the extraction commands and the fetched
artifacts (`cap12.xsd`, `gtfs-rt.proto`, `gtfs-ref.md`, `idx.json`, `gibbon_mp.php`) are in this
scratchpad directory and can be re-run.

**What I could not verify, and it matters.** This session's WebSearch budget was exhausted before
I ran a single query, and the egress policy allows **only GitHub hosts** — `huggingface.co`,
`docs.oasis-open.org`, `rfc-editor.org`, `gtfs.org`, `ed.gov`, `studentprivacy.ed.gov`, `ecfr.gov`,
`hl7.org`, `arrl.org`, `aclanthology.org`, `jamanetwork.com`, `uscenterforsafesport.org`, `cdt.org`
and `arxiv.org` were all refused at CONNECT. Consequences, stated plainly rather than papered over:

- **Model licenses and sizes for NLLB-200, MADLAD-400, M2M-100, SeamlessM4T and the OPUS-MT
  checkpoints are recalled, not read.** They are marked `P2 Cited (from memory)` below and every
  one of them needs a verification pass before anything is built on it. This is exactly the §18
  item-0 defect applied to my own output, so it is labelled rather than hidden.
- **The professional and regulatory literature on where MT is unsafe is unverified in-session**:
  ISO 18587 (post-editing of MT output), the 2015 OCR/DOJ Dear Colleague letter on EL parents'
  language access under Title VI, the JAMA Internal Medicine work on machine-translated discharge
  instructions, NCIHC/ATA position statements, US Center for SafeSport MAAPP, FERPA §99.32's
  record-of-disclosures requirement. §8 below states each claim and tags it. **Do not cite §8's
  external authorities out of this document without re-reading the primary sources.**
- Anything below tagged **`[unverified]`** was not opened in this session. Everything untagged was.

---

## 1 · Ranked table

Activity = last push observed on the default branch, this session. "Vendor required?" means: does
the design structurally force a third party to hold roster or message content.

| # | Project / artifact | What it gives this slice | License (read) | Activity | Vendor req'd? | Maps to | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **OASIS CAP 1.2** (schema read from `kelvinn/capparselib` `src/schema/cap12.xsd`) | Public-warning message envelope: `urgency`/`severity`/`certainty`/`responseType` vocabularies, `effective`/`onset`/`expires` as three distinct times, repeatable per-language `<info>`, `status=Draft|Exercise|Test`, `msgType=Alert|Update|Cancel|Ack|Error`, `references` for supersession | OASIS spec (open); the parser repo carries no SPDX id | parser updated 2025-09-23 | No | §14 urgency tiering, emergency broadcast, translation, #3, #10, #14 | **steal-the-idea (whole envelope)** |
| 2 | **GTFS + GTFS-Realtime** `google/transit` | `TranslatedString` (message = set of BCP-47 variants), `tts_header_text` as a distinct rendering, `communication_period` vs `impact_period` with a containment invariant, `Cause`/`Effect`/`SeverityLevel` enums, `translations.txt` + `feed_lang=mul`, `arrival_time` vs `departure_time` + `timepoint` exact-vs-estimated | Apache-2.0 | 2026-07-09 | No | Call time vs downbeat vs dismissal; weather cascades; multilingual | **steal-the-idea (heavily)** |
| 3 | **XLIFF state ladder** via `translate/translate` (Translate Toolkit) | 10-rung ordinal ladder ending `translated → signed-off → final`, mapped onto a monotone `StateEnum` with ranges | GPL-3.0 | 2026-07-29 | No | #10, #14; the MT-is-a-draft enforcement point | **adopt (the ladder)** |
| 4 | **Weblate** `WeblateOrg/weblate` | Human-in-the-loop translation surface: `STATE_EMPTY→FUZZY→NEEDS_REWRITING→NEEDS_CHECKING→TRANSLATED→APPROVED→READONLY`, MT engines return ranked candidates with a `quality` score and `max_score`, built-in translation memory with per-entry `origin` and an opt-in `contribute_shared_tm` flag | GPL-3.0 | 2026-07-30 | No | Translation review workflow, TM, #10 | **adopt** |
| 5 | **Argos Translate** + **LibreTranslate** + **CTranslate2** | The local MT engine. Fully offline, CPU-viable | MIT/CC0 dual; AGPL-3.0; MIT | 2026-06-27 / 2026-07-25 / 2026-07-03 | No | Local MT (#1) | **adopt, with a named coverage gap (§3)** |
| 6 | **COMET** `Unbabel/COMET` | Quality estimation. `wmt20-comet-qe-da` is **reference-free and Apache-2.0**; all CometKiwi checkpoints are **CC-BY-NC-SA** | code Apache-2.0; models split (read from `LICENSE.models.md`) | 2026-04-21 | No | The MT gate; #13, #18 | **adopt `wmt20-comet-qe-da` specifically** |
| 7 | **GOV.UK Notify** `alphagov/notifications-api` + **GC Notify** `cds-snc/notification-api` | Government-scale templated notification: template versioning, per-recipient delivery status, provider abstraction so the SMS carrier is swappable; the Canadian fork is structurally bilingual | MIT / MIT | 2026-07-29 / 2026-07-29 | No (provider-abstracted) | Segmented announcements, delivery status | **steal-the-idea** |
| 8 | **Gibbon** `GibbonEdu/core` — Messenger module | The only school-domain OSS acknowledgment implementation I found: per-recipient receipt row, per-recipient nonce confirm URL, `[confirmLink]` body token, reminder resend to unconfirmed, SMS as a separate channel with credit check, one log row per send | GPL-3.0 | current | No | §14 acknowledgment tracking, handbook ack | **steal-the-idea** |
| 9 | **capcom6/android-sms-gateway** | §4.1's "dedicated Android handset in the band room" — already built, with a local-only mode that needs no cloud server | Apache-2.0 | 2026-07-30 | **No** (local mode) | §4.1 sovereign gateway | **adopt** |
| 10 | **Prometheus Alertmanager** | The cascade algebra: `inhibit_rules`, `group_wait`, `group_interval`, `repeat_interval`, `mute_time_intervals` | Apache-2.0 | 2026-07-26 | No | One change → forty downstream changes → *not* forty texts | **steal-the-idea** |
| 11 | **sabre/vobject** `ITip/Broker.php` | RFC 5546 §2.1.4 significant-change list, in code: `DTSTART, DTEND, DURATION, DUE, RRULE, RDATE, EXDATE, STATUS`; plus REQUEST/CANCEL/REPLY handling that sets `STATUS:CANCELLED` and bumps `SEQUENCE` | BSD-3-Clause | current | No | Change propagation; tiering predicate; #3 | **adopt (the predicate)** |
| 12 | **Radicale** | Self-hosted CalDAV/CardDAV, single Python process | GPL-3.0 | 2026-07-19 | No | iCal publish/subscribe | **adopt** (with §5's caveat) |
| 13 | **ntfy** | Self-hosted push, 5 named priority rungs (`min/low/default/high/max|urgent`), UnifiedPush — no FCM/APNs dependency | Apache-2.0 | 2026-07-29 | **No** | Urgency tiering for staff/student push | **adopt** |
| 14 | **DocuSeal** `docusealco/docuseal` | Handbook + consent distribution with signature and audit trail, self-hosted | AGPL-3.0 | 2026-07-27 | No | Handbook distribution w/ acknowledgment | **adopt-candidate** (AGPL; separate service holding minors' documents) |
| 15 | **openbroadcaster/obplayer** | CAP-preempting playout with a documented five-step degradation ladder that never goes silent; repo topics include `indigenous-languages`, `polly-voice` | AGPL-3.0 | 2026-06-03 | No | Emergency broadcast; #13 | **steal-the-idea** |
| 16 | **bcgov/naad-connector** | A provincial government's own OSS client onto a national alert feed — the "org runs its own gateway" shape, in production | Apache-2.0 | current | No | Emergency ingest; §4.1 gateway posture | **steal-the-idea** |
| 17 | **Piper TTS** + **Asterisk** | Voice-call channel in family languages, on-prem — the flip-phone / grandparent / low-literacy path SMS misses | `rhasspy/piper` MIT; `OHF-Voice/piper1-gpl` **GPL-3.0**; Asterisk GPL-2.0 | current | No | Access equity; §14 | **steal-the-idea** |
| 18 | **Gammu / gammu-smsd** | Cellular-modem SMSD on the hub — the other half of §4.1's sovereign gateway | GPL-2.0 | 2026-07-30 | No | §4.1 | **adopt-alternative** |
| 19 | **medic/cht-core** (Community Health Toolkit) | Closest domain analogue anywhere: offline-first, SMS-first, multilingual, low-literacy, named individuals, real clinical stakes | AGPL-3.0 | 2026-07-30 | No | Whole slice, as design precedent | **read-only-interest (high value)** |
| 20 | **Sofie** `Sofie-Automation/sofie-core` (NRK) | Broadcast rundown model: Rundown→Segment→Part→Piece with expected vs actual timing | MIT | 2026-07-29 | No | Multi-field event model; plan-vs-actual (§3) | **read-only-interest** |
| 21 | **la5nta/pat** (Winlink) | Store-and-forward structured messaging over links that are down most of the time; standard form templates, `in-reply-to`, `.0` reply files | MIT | 2026-07-21 | No | Degraded-mode messaging; ack protocol | **read-only-interest** |
| 22 | **Jasmin** `jookies/jasmin` | SMPP gateway, if an A2P route is ever justified for the emergency tier only | **NOASSERTION** — no SPDX-identifiable license file; needs a legal read | 2026-04-26 | Carrier, by definition | §4.1 emergency A2P exception | **read-only-interest** |
| 23 | **Zulip** / **Discourse** / **Rocket.Chat** / **Synapse** | Candidate substrates for a supervised student channel | Apache-2.0 / GPL-2.0 / **MIT except `ee/` + `apps/meteor/ee/` which are proprietary** / AGPL-3.0 dual-licensed by Element | all current | No | §14 student-to-student | **read-only-interest — none implements the supervision invariant (§6)** |
| 24 | **RapidPro** `nyaruka/rapidpro` | The obvious candidate — visual flow builder, SMS-first, multilingual, acknowledgment-aware | **Business Source License 1.1** — not open source; forbids use for a "Hosted Messaging Platform"; converts to AGPL-3.0 on **2028-07-29** | 2026-07-30 | No, but licensing is the blocker | §14 | **read-only-interest (license disqualifies)** |
| 25 | **`grafana-cold-storage/oncall`** | Escalation chains and on-call rotation | AGPL-3.0 | **ARCHIVED**, last push 2026-03-24 | No | Escalation ladder | **read-only-interest** — and a live example of a dependency that died; cite it in the §16 tombstone argument |
| 26 | **ChurchCRM** / **Rock RMS** | Congregation notification, segmentation by household | ChurchCRM MIT; **Rock RMS: no `LICENSE` file on `develop`** | current | No | Segmented announcements | **read-only-interest** |
| 27 | **google/cap-library** | Reference CAP validator | — | **ARCHIVED** | No | CAP validation | **read-only-interest** |
| 28 | **Sahana Eden** | Humanitarian/emergency RAD kit with CAP broker | **NOASSERTION**; 28 stars | 2026-07-23 | No | Emergency management | **read-only-interest** |
| 29 | **Apprise** / **Gotify** | Fan-out to many notification backends / simple self-hosted push | BSD-2-Clause / `NOASSERTION` | 2026-07-29 / 2026-07-29 | No | Transport plumbing | **read-only-interest** |
| 30 | **MateCat** / **OmegaT** / **Tolgee** / **ModernMT** | CAT tools and TMS alternatives to Weblate | LGPL-3.0 / OmegaT-license.txt (GPL-family, indirected) / **multi-license monorepo** / Apache-2.0 | current | No | HITL translation | **read-only-interest** |

---

## 2 · CAP 1.2 is the message envelope this project is about to reinvent — badly

**What I read.** `cap12.xsd`, 9,859 bytes, from `kelvinn/capparselib@master:src/schema/cap12.xsd`.
I extracted every `<enumeration>` and attributed each to its owning element by position:

- `status` = **Actual, Exercise, System, Test, Draft**
- `msgType` = **Alert, Update, Cancel, Ack, Error**
- `scope` = **Public, Restricted, Private**
- `category` = Geo, Met, Safety, Security, Rescue, Fire, Health, Env, Transport, Infra, CBRNE, Other
- `responseType` = Shelter, Evacuate, Prepare, Execute, Avoid, Monitor, Assess, AllClear, None
- `urgency` = **Immediate, Expected, Future, Past, Unknown**
- `severity` = **Extreme, Severe, Moderate, Minor, Unknown**
- `certainty` = **Observed, Likely, Possible, Unlikely, Unknown**

And structurally: `<info>` is `maxOccurs="unbounded"` and each `<info>` carries its own
`<language>` (defaulting `en-US`); each `<info>` has **three separate time fields — `effective`,
`onset`, `expires`** — plus `headline`, `description` and `instruction` as distinct fields; the
alert carries `identifier`, `sender`, `sent`, `references`, `incidents`, `restriction`, `addresses`.

**Why this is the top find.** Five things this project needs, that CAP already decided:

1. **Language is a property of the info block, not of the alert.** One alert, N language blocks,
   each independently authored and independently sealable. That is precisely the shape §14's
   translation requirement needs, and it is *not* the shape you get if you bolt a `language` column
   onto a messages table. It also makes the per-language seal state of #10 expressible without a
   schema change.
2. **`effective` / `onset` / `expires` is call-time / downbeat / dismissal, already standardised.**
   The project says conflating those three "causes real chaos." A public-warning standard reached
   the same conclusion about when-the-message-takes-effect vs when-the-hazard-starts vs
   when-it-ends, and gave them three fields rather than one `start`. Adopt the shape and the
   argument comes for free.
3. **`status="Draft"` and `status="Exercise"`/`"Test"` are first-class wire values.** A CAP message
   can be on the wire and not actionable. That is #10 at the transport layer, and `Exercise` is how
   you satisfy #19 — you can *rehearse the emergency broadcast against the real send path* and the
   receivers know it is a drill. An emergency broadcast that has never been fired is a ledger, not
   enforcement (#18); `Exercise` is how you fire it without lying to two hundred households.
4. **`msgType=Cancel` with `references`, never a delete.** Cancellation is a new message that points
   at the identifier it supersedes. That is #3 ("never revoke by deleting") expressed as a wire
   format, and `msgType=Ack` makes acknowledgment a message type rather than a UI affordance.
5. **Three orthogonal ordinal scales — urgency, severity, certainty — never collapsed into one
   "priority" integer.** This is #14's argument, made by a standards body in 2010. Note the
   direction hazard §15 warns about: CAP's `certainty` includes `Unknown` *as a value in the
   enumeration*, which is #13 done right — absence is a legible value, not a gap.

**Transplant.** Define the internal announcement record as a CAP-shaped envelope with domain field
names (§ house rule: no fleet nouns, and here, no emergency-management jargon in front of a
guardian): `AnnouncementSet` → N `AnnouncementInfo` rows, one per language, each with
`takes_effect_at` / `event_starts_at` / `ends_at`, `headline` / `detail` / `instruction`,
plus `urgency`, `severity`, `certainty`, `seal_state`, `sealed_by`, `sealed_at`.
Keep CAP's controlled vocabularies verbatim internally so the mapping table of #14 has exactly one
entry per scale, and render them as prefixed rungs (`U1 Immediate … U5 Unknown`) rather than as
bare integers or colour.

**Cost.** Schema-design time, essentially — one migration and a vocabulary table. There is no
library to adopt: `google/cap-library` is **archived**, `IBM/cap` is **archived**, `kelvinn/capparselib`
is a 30-star parser with no SPDX license, `farrel/RCAP` is Ruby. **Do not take a CAP dependency.**
Take the schema and write 200 lines. This is the rare case where copying a standard's field list is
cheaper than any of its implementations — and where the pair created (the standard, and your
domain-named version of it) needs its named middle per #12: a single conformance test that asserts
your vocabulary tables are exactly CAP's, so drift fails a suite rather than surprising someone.

---

## 3 · Local MT: the engine is fine; the language coverage is the access barrier

This is the finding I'd most want the project to act on, and it is derived, not recalled.

**What I did.** Fetched the Argos/LibreTranslate model index
(`argosopentech/argospm-index@main:index.json`) and enumerated it with a script.

**Result: 100 packages, 50 distinct language codes, and 98 of the 100 pairs have English on one
side.** The available codes are:

`ar az bg bn ca cs da de el en eo es et eu fa fi fr ga gl he hi hu id it ja ko ky lt lv ms nb nl pb pl pt ro ru sk sl sq sv sw th tl tr uk ur vi zh zt`

So the topology is an English hub with two non-English spokes. The README states the design
explicitly and states its cost in the project's own words: Argos "manages automatically pivoting
through intermediate languages … at the cost of some loss of translation quality." For a US school
district this means **almost every non-English→non-English translation is a double pass**, and a
Spanish-speaking guardian reading content originally authored in Vietnamese gets error compounded
twice.

**Now the part that matters for access.** Against the languages a US district actually serves, the
index is present for Spanish, Vietnamese, Arabic, Chinese (simplified `zh` and traditional `zt`),
Russian, Ukrainian, Korean, Tagalog, Persian, Urdu, Bengali, Thai, Swahili, Albanian, Portuguese
(`pt` and Brazilian `pb`), French, German, Polish, Romanian, Turkish, Japanese, Greek, Hebrew.

It is **absent** for: **Haitian Creole, Somali, Nepali, Burmese, Amharic, Tigrinya, Pashto, Dari,
Hmong, Karen, Marshallese, Khmer, Lao, Punjabi, Gujarati, Tamil, Telugu, Kinyarwanda, Kurdish,
Mongolian.**

That absent list is close to a roll-call of the highest-need refugee and immigrant language
communities in US public education. **LibreTranslate, adopted naively, delivers machine translation
to the families who least need it and delivers nothing to the families the capability map calls "a
genuine access barrier."** It would also produce the worst possible artifact: a translation feature
that visibly works for some families and silently returns nothing for others — which is #13's
failure exactly, absence presented as a result.

**What to do about it, in order.**

1. **Make missing coverage a first-class `unknown`, on day one.** A language with no installed model
   must return `translation_unavailable` and route to the human queue, and the UI must say
   "unavailable in Somali" rather than showing an English message with no marking. This is a
   two-hour change if done at the start and a retrofit if not.
2. **Second engine for the tail, chosen on license.** `NLLB-200` (200 languages, covers most of the
   absent list) and `MADLAD-400` (400+ languages) are the candidates. **`[unverified]` — I could not
   reach `huggingface.co` this session.** From memory, NLLB-200 weights are **CC-BY-NC-4.0
   (non-commercial)** and MADLAD-400 is **Apache-2.0**; NLLB distilled-600M is ~2.5 GB in fp32 and
   MADLAD-3B is ~12 GB. Every one of those figures needs reading off the model card before it is
   quoted anywhere, per #17. If the licenses hold, **MADLAD-400 is the license-clean choice** and
   NLLB is the one that requires a deliberate decision about whether a school district's use is
   "non-commercial" — a question for the district's counsel, not for an engineer, and one whose
   answer should be written into the repo rather than assumed.
3. **`LibreTranslate/Locomotive` exists** (referenced from the Argos README, repo confirmed
   reachable) for training Argos-format models from parallel corpora. For a district with a large
   Karen or Marshallese community and no available model, a locally trained model reviewed by a
   community bilingual is a real option — and one whose output should never be trusted above the
   `needs-review` rung.
4. **Runtime.** `CTranslate2` (MIT) is the inference engine under Argos and is CPU-fast and
   quantisable (int8) — this runs on the hub without a GPU. `bergamot-translator` (MPL-2.0) is the
   Firefox-lineage alternative but was last pushed **2024-05-12**, `translateLocally` (MIT)
   **2025-03-30**, and `mozilla/firefox-translations-models` is **archived** (last push 2025-12-15),
   with the active pipeline now at `mozilla/translations` (MPL-2.0, 2026-07-22). If you want the
   Bergamot models, take them from `mozilla/translations`, not from the archived repo, and record
   the archival in the dependency notes — an archived model source is a #20 tombstone waiting to be
   written.

**Refusal #1 compliance is free here.** All of this is local by construction: Argos/CTranslate2 load
a `.argosmodel` from disk and never open a socket. The thing to guard is not the engine but the
*fallback*: a stopped translation service must fail loudly to `unavailable`, never silently fall
back to a cloud translate API. That belongs in the same startup assertion as
`WILLOW_INFERENCE_PROVIDER` — a configured cloud translation endpoint should refuse to start the
process, not be caught at request time (§6's fail-at-startup idiom).

---

## 4 · GTFS is the best multi-field event model in the open, and it is not close

Transit agencies solved "hundreds of people need to know a time changed, in their language, and
some of the times are firm and some are estimates" thirty years before school music programs
described it as an unsolved problem.

**Verified from `google/transit@master` (Apache-2.0):**

From `gtfs-realtime/proto/gtfs-realtime.proto`:

- **`TranslatedString`** — a message is not a string. It is a repeated `Translation`, each with
  `text` plus an optional BCP-47 `language`, with two rules stated in the proto comments: *at least
  one translation must be provided*, and *at most one translation is allowed to have an unspecified
  language tag.* That second rule is the one worth stealing: it makes "the untagged original" a
  singleton, so you can never end up with two candidate defaults.
- **`tts_header_text` and `tts_description_text`** are separate fields from `header_text` and
  `description_text` — same content, different rendering channel, authored separately. This is the
  answer to "the SMS body and the portal body and the robocall script are not the same string." It
  also gives the SMS-minimisation rule of §4.1 a home in the schema: the SMS variant is a
  *different field*, so a reviewer can look at exactly the text that will hit a lock screen.
- **`communication_period` vs `impact_period`**, with this constraint in the proto comment: *every
  time interval in `impact_period` must be fully contained within at least one time interval of
  `communication_period`.* A transit spec encodes "you must tell people before the thing happens,
  and keep telling them at least as long as it lasts" as a **validatable invariant**. Directly
  transplantable, and directly testable per #19 — write the test that constructs an announcement
  whose impact window starts before its communication window and assert the send refuses.
- **`Cause`** = UNKNOWN_CAUSE, OTHER_CAUSE, TECHNICAL_PROBLEM, STRIKE, DEMONSTRATION, ACCIDENT,
  HOLIDAY, **WEATHER**, MAINTENANCE, CONSTRUCTION, POLICE_ACTIVITY, MEDICAL_EMERGENCY, SPECIAL_EVENT.
  **`Effect`** = NO_SERVICE, REDUCED_SERVICE, SIGNIFICANT_DELAYS, DETOUR, ADDITIONAL_SERVICE,
  MODIFIED_SERVICE, OTHER_EFFECT, UNKNOWN_EFFECT, STOP_MOVED, NO_EFFECT, ACCESSIBILITY_ISSUE.
  **`SeverityLevel`** = UNKNOWN_SEVERITY, INFO, WARNING, SEVERE. Note `NO_EFFECT` and
  `ACCESSIBILITY_ISSUE` are values, and `OTHER_CAUSE` is annotated *"Not machine-representable"* —
  an escape hatch that is honest about being one.

From `gtfs/spec/en/reference.md`:

- **`arrival_time` and `departure_time` are separate fields on the same stop**, with the spec noting
  they should be equal only *"if there are not separate times for arrival and departure."* Call time
  and downbeat are arrival and departure at the same event. Dismissal is arrival at the next one.
- **`timepoint`** distinguishes exact times (`timepoint=1`) from *estimated or interpolated*
  (`timepoint=0`). This is the single most useful small idea in the whole scout: **mark which
  published times are firm and which are estimates.** Call time is firm; dismissal is an estimate;
  today the schema treats them identically and families treat them identically and then a parent
  waits forty minutes in a parking lot. One boolean fixes a category of real harm.
- **`translations.txt`** plus `feed_lang`, including `feed_lang=mul` (ISO 639-2) for a genuinely
  multilingual dataset with translations supplied per language. Prior art for "the canonical record
  is multilingual and no single language is privileged."

**Transplant and cost.** Copy the field decomposition, not the format: `EventTime` rows keyed
`(event_id, kind, time, is_estimate)` with `kind ∈ {call, downbeat, dismissal, load_in, load_out}`,
and `Announcement` carrying `cause`/`effect`/`severity` vocabularies. Cost is one migration plus the
containment-invariant test. Do **not** emit real GTFS — you would be publishing named minors'
movements in a format built to be consumed publicly, which is the exact inversion of §6.

---

## 5 · Calendar: publish it, but never treat a subscribed feed as a notification channel

**Verified.** `sabre-io/vobject`'s `ITip/Broker.php` (BSD-3-Clause) implements RFC 5546 iTIP and
carries, as a named public property with the RFC section cited in a comment, its
**significant-change list: `DTSTART`, `DTEND`, `DURATION`, `DUE`, `RRULE`, `RDATE`, `EXDATE`,
`STATUS`.** It also processes `METHOD:REQUEST`/`CANCEL`/`REPLY`, sets `STATUS:CANCELLED` and bumps
`SEQUENCE` on cancel, and generates REPLY on attendee `ACCEPTED/DECLINED/TENTATIVE`.
`ical4j` (read from `Property.java`) confirms `SEQUENCE`, `RECURRENCE-ID`, `STATUS`,
`REQUEST-STATUS` as the standard property names.

**The transplant is the predicate, and it is the answer to the urgency-tiering question.** "Which
schedule edit earns an SMS?" has a standards-backed answer that someone already wrote down: a change
to a *significant* property. Changing the LOCATION note or the DESCRIPTION does not wake two hundred
phones; changing `DTSTART` does. Implement `is_significant_change(old, new)` over the domain's
equivalent set — `call_time`, `downbeat`, `dismissal`, `date`, `status`, `location` — and route only
those to the SMS tier. Everything else updates the feed silently. That single function is most of
the "weather cascade" problem: a cancellation propagating into forty downstream plan changes
produces forty feed updates and **one** significant-change notification, because the downstream
changes are consequences of one significant event.

Pair it with **Alertmanager's** algebra (Apache-2.0, verified in `config/config.go`):
`inhibit_rules` (a firing SEVERE alert suppresses the INFO alerts it implies — i.e. "event
cancelled" suppresses "call time changed" for that event), `group_wait` (hold briefly so a burst of
edits coalesces into one message), `group_interval`, `repeat_interval`, and `mute_time_intervals`
(no non-emergency sends at 03:00). Do not adopt Alertmanager the service; adopt the five parameter
names and their semantics. Cost: a debounce queue and an implication table. This is where the "one
change → forty downstream changes" requirement is actually met, and it is maybe 300 lines.

**The honest caveat, and it is load-bearing.** `Radicale` (GPL-3.0, 2026-07-19) will happily serve
CalDAV and a subscribable `.ics`. But **a subscribed ICS feed is polled on the consumer's schedule,
not the publisher's** — Google Calendar and Apple Calendar refresh external subscriptions on their
own cadence, and RFC 7986's `REFRESH-INTERVAL` / the `X-PUBLISHED-TTL` convention are *hints* a
client may ignore. (I could not confirm either property name in `ical4j`'s `Property.java`, which
suggests the library does not expose them as first-class constants — consistent with them being
weakly supported in practice. `[partially verified]`.) Two consequences to write into the design:

- The calendar is the **record**; SMS is the **signal**. A 5 a.m. lightning cancellation must never
  depend on a family's calendar client having refreshed. §4.1 already says this; the calendar
  feature must not quietly contradict it.
- Publish per-guardian feed URLs (so §7.1's dated-guardianship predicate gates the feed the same way
  it gates the send list) — but note the metadata leak §4.2 already worries about: a feed polled
  from one household's IP on alternating weekends reconstructs the custody arrangement just as
  keystroke timing did. Feed URLs are bearer tokens; they are also a timing side channel. Same
  padding-and-schedule discipline, or accept and *document* the limit the way `corpus-lens` does.

---

## 6 · Student-to-student communication: the substrates are all wrong for the same reason

The project is right that this is a safeguarding design problem, not a chat feature. I looked at
four candidate substrates and verified each license:

- **Zulip** — Apache-2.0. Cleanest license; topic-threaded streams; has message-retention policy.
- **Discourse** — GPL-2.0. Trust levels, flag queues, a mature public moderation model.
- **Rocket.Chat** — **MIT except `ee/` and `apps/meteor/ee/`, which are under a separate proprietary
  license.** The moderation console and much of the compliance tooling live behind that line; verify
  which side of it each feature you need falls on before planning around it.
- **Synapse** — AGPL-3.0, dual-licensed commercially by Element (read from the README); moderation
  is out-of-process via `Draupnir` (which has **no `LICENSE` file on `main` or `v2.x`** — a genuine
  finding: do not adopt an unlicensed moderation bot into a repo holding minors' data).

**None of them implements the invariant, and the invariant is what the feature is.** The
safeguarding rule from youth-serving practice — *no unobserved one-to-one adult↔minor channel; adult
communication with a minor includes a second adult or the guardian; retention is not the
participants' choice* — is a **constraint on the shape of a conversation**, and every one of these
products models a conversation as a set of members with symmetric rights. `[unverified]` — I could
not reach the US Center for SafeSport MAAPP or NSPCC guidance this session to quote the rules
precisely; treat the formulation above as recalled and re-read the primaries before building.

**Design consequence, which follows from CLAUDE.md alone and does not need the external citation.**
Refusal #8 says a shared event is two lane entries with one referent, never one row with a roster
column. A message between two students is the same object: **two lane entries and one referent**,
not one row in a channel. That gives, for free, what no chat product gives:

- Retention is a property of each lane, so one student's guardian exercising an inspection right
  reveals that student's lane, not the other child's (#16: a student's entries are as durable as
  entries about them; and no role's authority extends to deleting the record of its own exercise).
- Supervision is a *grant on the lane*, dated, expiring, revocable per §7.1 — so "who could read
  this thread on October 12, and why" is answerable, which is the only version of supervision that
  survives a complaint.
- A one-to-one adult↔minor lane pair with no third party attached is **structurally unconstructible**
  if the constructor requires a supervising edge — the un-passable-parameter discipline (§6) applied
  to a conversation. That is enforcement. A moderation dashboard is a ledger (#18).

**Verdict: read-only-interest on all four.** Steal Discourse's flag-queue *workflow* and Zulip's
topic model as UI references. Do not adopt a chat server as the student channel; the lane model
already in the architecture is a better fit than anything on the shelf, and the honest sequencing
answer is that this feature should ship *after* the lane schema (§18 item 3), not alongside it.

**Adjacent caution worth one line, tagged.** The commercial school-monitoring category (Gaggle,
Bark, GoGuardian) is the thing an institution will ask for by name, and there is a documented
critique of it — CDT's work on student-activity monitoring and its disproportionate harms to
LGBTQ+ and minority students is the reference I'd reach for. `[unverified]` — `cdt.org` blocked.
Fetch it before this conversation happens with a board, because it will happen.

---

## 7 · Acknowledgment tracking, handbooks, and the FERPA disclosure log

**Gibbon's Messenger is the prior art, and I read the code.** `GibbonEdu/core@master`
`modules/Messenger/src/MessageProcess.php` (506 lines, GPL-3.0). The model:

- A **`gibbonMessengerReceipt` row per recipient**, fetched via
  `MessengerReceiptGateway->selectMessageRecipientList()` — acknowledgment is a table, not a flag on
  the message.
- Each row carries a **per-recipient `key`**, used to build a confirm URL
  (`messenger_emailReceiptConfirm.php?gibbonMessengerID=…&gibbonPersonID=…&key=…`).
- A **`[confirmLink]` token** substituted into the body if present, else the link is prepended —
  so the author controls placement, and a template without the token still gets the link.
- **Reminder resends**: if `sent == 'Y'` and a receipt is still outstanding, the subject is prefixed
  `REMINDER:` and an italic instruction is prepended. Escalation-by-repetition, in a school context.
- **SMS is a separate channel** with a credit-balance precheck (warns under 1000) and a single log
  row per send batch recording status, result count and recipients.
- The function that builds the link is named **`handleFakeReadReceiptLink`**.

**That function name is the most useful thing in this section.** A click on a confirm link is
evidence that a link was clicked. It is not evidence the message was read, and it is certainly not
evidence it was understood — and Gibbon's own source says so in an identifier. This is #18 exactly:
an acknowledgment table is a **ledger** of clicks. Calling it proof of notice is the error. Name the
column `ack_clicked_at`, never `read_at`, and when a policy depends on notice having been given
(fee deadline, records-inspection response, eligibility warning), the dated disposition of #15 must
rest on the org's *send* record plus a human's judgement, not on a guardian's click.

**Two things to not copy from Gibbon.** The per-recipient `key` in an emailed URL is a bearer token
that identifies a named minor's guardian and never expires — fine for "practice moved," wrong for
anything L3+. Make the confirm token single-use, short-TTL, and scoped to the acknowledgment act
only. And the SMS path there carries whatever the author typed; refusal #7 needs the send path to be
*incapable* of carrying a record, which means the SMS variant is a separate, length-capped,
classification-checked field (as GTFS does with `tts_*`), not the same body.

**Handbook distribution with acknowledgment: DocuSeal** (AGPL-3.0, 2026-07-27, self-hosted). Gives
document versioning, per-recipient signing, and an audit trail. Two costs, both real: AGPL, and it
is a **second service that will hold documents about minors** — so it inherits the whole §5/§6
envelope question and the escrow requirement, and it must sit behind the same egress gate. My
verdict is adopt-candidate rather than adopt because the cheaper answer may be: keep the handbook in
the app, and use the acknowledgment table above with a `document_version_id` — you need
"acknowledged version 7 on this date," which is one join, not a signing platform.

**The FERPA disclosure log.** §14 asks for "communication logs sufficient for FERPA disclosure
records." `[unverified]` — I could not reach `ecfr.gov` or `studentprivacy.ed.gov`; from memory the
requirement (34 CFR §99.32) is that the institution maintain, with the education record, a record of
each request for and each disclosure of PII, naming the parties and their legitimate interests,
retained as long as the record itself. **Verify the exact text before implementing.** What I can say
from the tree without any external source: this is a *history* table, so by §7.1's own exclusion
logic it takes no validity-interval pair and must never be superseded or deleted — it belongs with
`frank_ledger` and `routing_decisions`, not with guardianship. And #16 forbids any role from
deleting the record of its own exercise, which means the disclosure log is append-only *for the
director too*. The prior art I would have checked here is FHIR's `AuditEvent` (`agent`, `entity`,
`purposeOfEvent`, `action`, `outcome`) as a field list for "who disclosed what to whom, why" — I
could not read it in-session (`hl7.org` blocked, and the HAPI path I guessed 404'd). Tagged, not
claimed.

---

## 8 · Where unreviewed machine translation must not be used

This section is the one I would put in front of a director, and it is deliberately absolute.

### The line: MT unreviewed may carry a **signal**. It may never carry a **record or an instrument**.

§4.1 already draws exactly this line for SMS, and it is the same line. A signal is a time, a change,
a location of a building, an acknowledgment prompt — "rehearsal moved to 5:15," "bus is thirty
minutes out." A record is anything about a named minor. An **instrument** is anything that changes a
legal relationship or on which someone will rely to act: a consent form, a medical instruction, a
disciplinary notice, a deadline with an appeal right.

**Never unreviewed, with the reason attached:**

| Content | Why unreviewed MT is unsafe here |
|---|---|
| Medical instruction, medication, dosage, allergy, emergency action plan | Negation, dosage, conditionals and modality (*do not give*, *only if*, *may*, *up to*) are the specific classes MT drops or inverts, and they are the entire content of a medical instruction |
| Consent forms and anything a guardian signs | A signature on a translation the organisation cannot attest to is a weak claim to *informed* consent. The document is the instrument; the translation *is* the document for that family |
| Discipline, eligibility, academic-standing notices | Consequential, adversarial, and likely to be re-read by someone else later |
| Anything with a deadline, an appeal right, or a required response | §15's dated-disposition rule means the timebound is part of the message; a mistranslated date or an inverted "must respond by" defeats the disposition |
| Adjudication commentary about a named student | Already a `draft` until sealed (#10); translating a draft produces a draft of a draft, and the register of critical commentary is precisely what MT flattens |
| Guardianship, custody, records-inspection correspondence | The §7.1 population. A court order arriving mid-season is the case that proves it |
| Fee waiver denials, financial hardship correspondence | `FINANCIAL` classification, plus the same appeal-right problem |

**Why "just add a disclaimer" fails.** MT errors are *fluent*. The output is grammatical, confident,
and idiomatic, which means a monolingual sender has no signal at all that it is wrong, and a reader
has no reason to doubt it. A disclaimer transfers risk to the person least able to evaluate the
text. And Argos **pivots through English for 98 of its 100 pairs by design** (§3), so for most
non-English pairs the error is compounded twice before anyone sees it.

### The mechanism, because a policy that isn't enforced is a ledger (#18)

1. **Adopt the XLIFF ladder as the seal state of every outbound string.** Verified from
   `translate/translate@master:translate/storage/xliff.py`, the standard's own progression:
   `new → needs-translation → needs-adaptation → needs-l10n → needs-review-translation →
   needs-review-adaptation → needs-review-l10n → translated → signed-off → final`, mapped onto a
   monotone `StateEnum` with `(lower, upper)` ranges per rung. Render as prefixed rungs per #14
   (`TR0 new … TR9 final`), never as bare integers.
2. **MT output enters at `needs-review-translation`. It cannot be created at `signed-off`.** Not "is
   not," *cannot be* — the writer that produces MT output should not accept a seal state parameter
   at all. That is the §6 un-passable-parameter discipline: `knowledge.py` cannot leak PII because
   PII is not a parameter, and an MT writer cannot forge a seal because the seal is not a parameter.
3. **The send path refuses below `signed-off` for anything classified L3+.** Refuses at the send
   call, fails loudly, and — per #19 — there is a test that constructs an L3 message with an
   unsealed translation, attempts to send it, and asserts refusal. A guard that cannot be shown to
   fail has not been shown to work.
4. **The seal is a named human, dated, against a source version.** `sealed_by`, `sealed_at`,
   `source_version_id`, per language. When the English changes, every sealed translation of it drops
   back to `needs-review-translation` automatically — that is `SEQUENCE`/significant-change (§5)
   applied to translations. **And rejections are recorded as durably as approvals** (#10): a
   reviewer who rejected an MT rendering of a medical instruction created the most important row in
   the table.
5. **Quality estimation triages; it never approves.** `Unbabel/wmt20-comet-qe-da` is reference-free
   and **Apache-2.0** (read from `COMET/LICENSE.models.md`) — use it to *rank the review queue* and
   to flag suspiciously low-scoring segments for priority human attention. Note carefully: **every
   CometKiwi checkpoint (`wmt22-cometkiwi-da`, `wmt23-cometkiwi-da-xl`, `-xxl`) is CC-BY-NC-SA**, as
   are `unite-*` and `XCOMET-*`; only `wmt20-comet-da`, `wmt20-comet-qe-da`, `wmt22-comet-da` and
   `eamt22-cometinho-da` are Apache-2.0. Pick on license, not on leaderboard. And per #13, a QE
   model that failed to load returns `unknown`, which routes to a human — it does not return "fine."
6. **Translation memory is the affordable path to actual coverage.** Weblate's `weblate/memory`
   (verified present) stores entries with `source_language`, `target_language` and `origin`. A music
   program sends the same ~150 sentences every season. Have them professionally translated **once**,
   per language, into the TM; then a TM hit sends immediately with a real human seal behind it, and
   only a TM miss reaches a human. This is how you get same-day multilingual urgent messaging
   without ever putting unreviewed MT in front of a family. **Critically: leave
   `contribute_shared_tm` off.** Weblate's shared TM ships segment content to a shared pool; for a
   TM built from messages about named minors that is an egress event wearing a productivity feature's
   clothes.
7. **The highest-leverage move: a numbered message catalogue, pre-translated, so the urgent path
   never invokes MT at all.** CAP's `eventCode` and the amateur-radio traffic tradition's numbered
   messages (ARRL "ARL" texts — a fixed catalogue of standard message bodies referenced by number,
   `[unverified]`, `arrl.org` blocked) both do this: a small controlled set of message types, each
   with a professionally translated body per language and typed parameter slots
   (`{event}`, `{new_time}`, `{location}`). Rehearsal moved, call time changed, event cancelled,
   lightning hold, bus delayed, pickup location changed, form due. **The emergency tier should be
   100% catalogue and 0% free text**, which simultaneously satisfies refusal #7 (a template with
   typed slots cannot accidentally contain a health note), the SMS throughput constraint (short,
   predictable), the translation problem (pre-sealed, no MT at send time), and #19 (each template is
   testable). Free text exists, requires review, and is never the urgent path.

### The professional line, and children as interpreters

Two rules from community interpreting that this system can enforce structurally rather than
advise about. `[unverified]` — NCIHC/ATA/ISO 18587 all unreachable this session; re-read before
quoting.

- **Interpretation (spoken, live, bidirectional) and translation (written) are different professions
  with different competencies.** A local MT model does neither job; it produces a draft of one of
  them. Nothing in this feature should be presented to a family as "an interpreter."
- **A child must never be the interpreter for their own family** — the rule from healthcare and
  court interpreting, and it maps onto this codebase with unusual precision: a student's lane must
  never be the delivery channel for a guardian-directed record. If the only Somali-capable path to a
  household runs through the fourteen-year-old, the system has recreated the harm. Which means the
  language-coverage gap of §3 is not a nice-to-have feature gap; **it is the mechanism by which a
  program ends up using a child to deliver their own medical or disciplinary news.** That is the
  argument for spending money on human translation of the catalogue, and it is the one I would lead
  with.
- **ISO 18587** is the standard I would reach for to name review depth (full post-editing vs light
  post-editing) rather than inventing vocabulary. `[unverified]`.

---

## 9 · Weirdest things I found

**1 · `bcgov/naad-connector` — a province's emergency alerting is a PHP daemon holding a TCP socket,
badged "Lifecycle: Experimental."** (Apache-2.0.) The Government of British Columbia publishes an
open-source PHP client that connects to Canada's National Alert Aggregation & Dissemination system
**over a raw TCP socket** and relays into a REST API, with a README that notes "Vault secrets are
not going to be used for MVP." I went looking for enterprise mass-notification architecture and
found a government doing precisely what §4.1 recommends — running its own connector rather than
buying a vendor — and being publicly, verifiably ordinary about it. The transplantable content is
the *posture*: the alert ingest is a small, boring, auditable process you own, and it does not need
to be impressive to be correct.

**2 · `openbroadcaster/obplayer`'s failure ladder, and the fact that CAP always wins.** (AGPL-3.0.)
A community-radio playout engine whose documented degradation sequence is: scheduled media → default
playlist → **Fallback Media Mode** → **analog input bypass** → **test signal**, and whose README
states it "always prioritizes valid Common Alerting Protocol (CAP) messages." Broadcasters have a
hard rule — *never go silent* — and they express it as a ladder where every rung is a legible,
deliberate state rather than an error. That is #13 designed by people whose regulator counts dead
air. The repo's topics include `indigenous-languages` and `polly-voice`, i.e. someone has already
faced "the emergency alert must go out in a language the affected community actually speaks, spoken
aloud, automatically."

**3 · GTFS makes "tell them before it happens" a schema constraint.** `impact_period` must be
*fully contained within* `communication_period`. A transit data spec encodes the ethics of
notification as a validation rule that a feed either passes or fails. I have not seen any
communications platform express this, and it is two lines of validation.

**4 · Gibbon's function is called `handleFakeReadReceiptLink`.** A school management platform whose
source code, in an identifier, admits that its read receipts are not read receipts. This is the
single best piece of naming discipline I found all session and it is exactly the enforcement-vs-ledger
distinction of #18, shipped by accident. I would steal the honesty and the naming convention both.

**5 · `la5nta/pat` — Winlink, and CAP's `status="Exercise"`.** Two entries from the
communications-under-adversity tradition. `pat` (MIT, Go) is a ham-radio email client with a
**standard form-template system**, `in-reply-to`, and a `.0` reply-file extension — structured
messaging designed for a link that is down most of the time, which is a better model for "guardian
with an intermittent prepaid phone" than anything in the SaaS category. And CAP ships
`status="Exercise"` and `status="Test"` as **wire values**, meaning the public-warning world decided
thirty years ago that you must be able to fire the real emergency path as a drill without deceiving
anyone. This project's emergency broadcast will otherwise be a code path that has never executed —
and per #19, that is not a guarantee, it is a hope.

---

## 10 · What I would sequence, given §18

Nothing here blocks the four §18 items, and two of these findings *feed* them:

- The CAP-shaped envelope and the `EventTime` decomposition are **schema decisions**, so they belong
  in the same conversation as §18 item 3 (no schema for the lane model). An announcement addressed
  to two siblings is two lane entries with one referent; that falls straight out of #8 if the
  envelope is designed with it, and is a data migration if not.
- The `L1–L5` definitions (§18 item 1) need a worked example each. **The SMS body is the best worked
  example in the whole application** — "call time is 5:15" versus "Ben's insulin authorization
  expires Friday" is the L-ladder's boundary made concrete, and refusal #7 is already the behavioural
  statement of it. Writing §14's message classification would produce most of the L-ladder document
  as a side effect.
- The translation catalogue (§8 item 7) is buyable work, not engineering work, and it has a long lead
  time. If the program serves families in a language Argos does not cover, that procurement should
  start before the code does.
