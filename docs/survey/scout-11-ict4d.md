# Scout 11 — ICT4D / humanitarian / global-health open source

Slice: the humanitarian, global-development and public-health OSS world, hunted against
`docs/ARCHITECTURE.md` §4 / §4.1 (per-persona transports, the 80/15/5 traffic split, "SMS carries
signals never records", the local SIM gateway, enrollment without a help desk),
`docs/CAPABILITY-MAP.md` §12 (Health and Safety) and §14 (Communication), and `CLAUDE.md`
refusals #1, #3, #5, #7 and shapes #8, #9, #13, #15.

**Verdict up front: this vein is as rich as predicted, but not evenly.** The transplantable
material is concentrated in three places — (a) *local* SMS gateway software that is genuinely
alive, (b) one fully-worked message *lifecycle* model that already contains the states this
project will otherwise invent badly, and (c) two authorization mechanisms — DHIS2's
break-the-glass and its relationship model — that are §7.2 and §7.1 built, shipped, and running
in production in dozens of countries. The child-protection case-management world (Primero) is the
closest *domain* sibling this project has anywhere, and is AGPL, which makes it a
read-and-steal rather than a dependency.

---

## Method and honesty notes — read before trusting any row below

- **WebSearch budget was exhausted** (200/200 for the session) after four queries in this scout.
  Everything after that was verified by direct `WebFetch` of `github.com` HTML pages,
  `raw.githubusercontent.com` files, and commit-list pages. The GitHub REST API
  (`api.github.com`) and `curl` to `github.com` are both blocked in this session, so
  license/activity facts come from reading the repo page, the `LICENSE` blob, or the
  `/commits/<branch>` page — which is why some rows say "commit dates not obtained" rather
  than guessing.
- **Hosts blocked by egress policy (403 at the proxy), so their content is NOT summarized here
  from the page itself:** `docs.communityhealthtoolkit.org`, `docs.dhis2.org`, `primero.org`,
  `gbvims.com`, `cleaninsights.org`, `community.rapidpro.io`, `rm.coe.int`, `datepersonale.md`,
  `icvanetwork.org`, `the-engine-room.github.io`, `ctdatacollaborative.org`. Where a document is
  listed in the PRACTICE section on the strength of a search-result title/URL only, it is marked
  **[existence verified, contents not fetched]**. Per `CLAUDE.md` #17 I have not paraphrased any
  document I could not open.
- Everything marked "ACTIVE" has a commit or release date I read with my own eyes; dates are
  given. Everything marked DEAD likewise.
- Three projects in this space that a naive search would surface are **dead or renamed**, and
  that is a finding in itself — see the tombstones section.

---

## Ranked table

Ranked by value to *this* project, not by fame.

| # | Project | What it is | License | Activity (verified) | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **CHT Gateway** (`medic/cht-gateway`) | Android app: phone becomes the SMS gateway for your own server; polls *your* endpoint for outbound, POSTs inbound | AGPL-3.0 | 472 commits; releases published; part of a live platform | §4.1 local gateway; "no third party holds the roster" | **adopt** |
| 2 | **CHT SMS state machine + deny list** (`medic/cht-docs`) | 11 documented SMS states incl. `denied`, `cleared`, `muted`; `outgoing_deny_list`, `multipart_sms_limit` | AGPL-3.0 docs | Docs current | §4.1 STOP/opt-in state, tiering, "who is messaged" gate | **adopt the model** |
| 3 | **SMS Gateway for Android** (`capcom6/android-sms-gateway`) | Same shape, modern: Kotlin/Ktor, explicit **Local Server mode** (no cloud at all) or your own private server | **Apache-2.0** | **v1.68.1 released Jul 29; v1.65.0→v1.68.1 in 2 months**; 5.2k stars | §4.1 local gateway, sovereign transport | **adopt** |
| 4 | **DHIS2 "break the glass"** (`dhis2-docs`, tracker) | Program access level `protected`: finding a record outside your capture scope offers break-the-glass; you **give a reason** and receive **temporary ownership** | BSD-3-Clause | Docs repo 2,607 commits, active | **§7.2 the knock** — declared purpose on entry, reconciled | **steal the idea (exactly)** |
| 5 | **DHIS2 relationship model** | Relationships are first-class data with typed constraints per side; **unidirectional needs write-source + read-destination, bidirectional needs write-both** | BSD-3-Clause | active | **§7.1** guardianship as independently-revocable typed edges | **steal the idea** |
| 6 | **Primero / CPIMS+ / GBVIMS+** (`primeroIMS/primero`) | Inter-agency child-protection & GBV case management; UNICEF+IRC+Save+UNHCR; 60+ countries | **AGPL-3.0** (verified LICENSE) | **commits through Jul 9** — ACTIVE | §12, §7.4 Ward Case, sealed records, referrals with consent | **read-only-interest + steal heavily** |
| 7 | **CHT `moving-contacts` lesson** | Moving a contact moves it, all descendants, **and all reports authored by them**; offline users who lose a contact **keep it on device**, and updates "silently fail to sync" | AGPL-3.0 docs | current | §7.1 revocation, §4.2 envelope, #13 `unknown` | **steal — and write the failing test** |
| 8 | **RapidPro Android Channel** (`rapidpro/android-channel`) | Android SMS relay for RapidPro; **documents that "SMS usage on Android is rate-limited per project"** and ships "packs" to spread load | AGPL-3.0 (Nyaruka/UNICEF 2014-2023) | in-tree, part of live platform | §4.1 throughput reality — the only hard in-repo evidence I found | **steal the idea** |
| 9 | **NEMO** (was **ELMO**, `thecartercenter/elmo`) | Carter Center election-observation data platform: web + ODK Collect + **SMS** entry paths, plus **SMS broadcasting** | Apache-2.0 | **commits through Jul 16** — ACTIVE | §4.1 SMS-as-intake, §14 broadcast | **steal the idea** |
| 10 | **gammu / gammu-smsd** | The canonical Unix daemon driving a *local GSM modem* on the box itself | GPL-2.0 | 14,662 commits, maintained (M. Cihar) | §4.1 "cellular modem on the hub" | **adopt (as the modem path)** |
| 11 | **playSMS** | Web front end / router over gammu, Kannel, SMS Server Tools, Jasmin | GPLv3 | **v1.4.8, build stamp 2508131200 (Aug 2025)**; 4,183 commits | §4.1 send queue + staggering | **read-only-interest** |
| 12 | **OpenCRVS** (`opencrvs/opencrvs-core`) | Civil registration: births, deaths, legal informants; correction and annulment workflows | **MPL-2.0** + a Civil Registration & Healthcare Disclaimer | 24,682 commits; 993 open issues | #3 never revoke by deleting; dated legal relationships | **read-only-interest** |
| 13 | **ODK Central** (`getodk/central`) | Self-host form server: Postgres + Enketo + pyxform, Docker Compose, no vendor hosted tier | **Apache-2.0** | 885 commits, releases | §12 medical/consent forms, offline intake | **steal the idea (XLSForm)** |
| 14 | **Enketo** (`enketo/enketo`) | Offline-capable web forms from XForms; the engine under ODK **and** Kobo | open (JS monorepo) | **ODK stepped back May 2024; Kobo assumed maintainership Mar 2025** | §4.2 transactional 5% forms; §11.1 exit plan | **read-only-interest** |
| 15 | **OpenSRP FHIR Core** (`opensrp/fhircore`) | Android FHIR, offline, encrypted at rest, household/CHW registers | Apache-2.0 | 1,902 commits | §7.4 W-1 one lane per student; household modelling | **read-only-interest** |
| 16 | **DHIS2 Android Capture** | Offline-first capture app for tracker/event/datasets, program rules | BSD-3-Clause | 11,368 commits | edge devices §4, offline attendance | **read-only-interest** |
| 17 | **Tangerine** (`Tangerine-Community/Tangerine`) | RTI's offline tablet assessment/data collection for schools; CouchDB + PouchDB | GPLv3 | 8,062 commits; 609 open issues | §3 Scheduling/Attendance in low connectivity; §2 assessment | **read-only-interest** |
| 18 | **Kolibri** (`learningequality/kolibri`) | Offline-first learning platform, peer sync between local devices | **MIT** | 37,990 commits | §3 attendance/roster on a modest box; the drop | **read-only-interest** |
| 19 | **Tella** (`Horizontal-org/Tella-Android`) | Offline documentation app: SQLCipher gallery, **camouflage**, **panic delete**, uploads to *your* server | **MIT** | 650+ commits, active; FOSS variant exists with trackers stripped | kiosk/edge device for judges & clinicians (§4) | **steal the idea** |
| 20 | **Uwazi** (`huridocs/uwazi`) | Human-rights document/evidence database | **MIT** | 21,191 commits; 417 open issues | §8.1 commentary as primitive; evidence handling | **read-only-interest** |
| 21 | **Apollo** (`nditech/apollo`) | NDI/TimbaObjects citizen election-observation platform; Flask + Postgres + Redis + worker, Docker Compose | open (LICENSE present, type not read) | 4,653 commits | §4.1 mass structured intake from many low-trust observers | **weird / read-only** |
| 22 | **sdcMicro** (`sdcTools/sdcMicro`) | R package for statistical disclosure control on microdata, with Shiny GUI | GPL-2.0 | 1,503 commits | **§6 egress gate** — measurable minimization of an export | **steal the idea** |
| 23 | **openIMIS** (`openimis/openimis-be_py`) | Health-insurance/benefit management for low-income populations; modular Django | AGPL | 1,012 commits | §7 Finance, fee waivers, enrolment validity | **read-only-interest** |
| 24 | **Reticulum** (`markqvist/Reticulum`) | Cryptographic networking stack over LoRa/packet radio/serial; coordination-less addressing, initiator anonymity | Reticulum License (protocol public domain) | 6.5k stars, 2,999 commits | §4.2 relay alternative; bus-trip comms with no carrier | **weird / read-only** |
| 25 | **CommCare HQ** (`dimagi/commcare-hq`) | The heavyweight of the sector: case management + SMS, 195k commits | **BSD-3-Clause** | very active | §7.4 case ownership/sharing | **read-only-interest** (needs `commcare-cloud`; paid hosted tier exists) |
| 26 | **KoboToolbox** (`kobotoolbox/kpi`) | Form server used across the whole sector | **AGPL-3.0** | 20,390 commits | §12 forms | **read-only-interest** — heavy (two Postgres DBs, many containers) |
| 27 | **MOSIP** (`mosip/mosip-docs`) | National-ID platform; foundational identity | MPL-2.0 | 6,784 commits on 1.2.0 | enrollment; guardian/introducer *unverified* | **read-only-interest** |
| 28 | **Open Referral / HSDS** | Standard for machine-readable human-services directories | CC BY-SA | 129 stars, active | §12 referral pathways, mental-health resources | **steal the schema** |
| 29 | **DPG Standard** (`DPGAlliance/DPG-Standard`) | 9-indicator conformance questionnaire for digital public goods | CC BY-SA 4.0, v1.1.6 (2024-09-04) | maintained | **§17 template conformance check**; §16 declaration-vs-enforcement | **steal the idea** |
| 30 | **Sahana Eden** (`sahana/eden`) | Disaster-management RAD kit (beneficiary registry, shelter) | LICENSE present, type not read | 14,986 commits; **28 stars, 6 open issues — commit dates NOT obtained; treat status as unknown** | disaster/weather cascade §12 | **read-only-interest, verify first** |

### Dead or renamed — state this before anyone builds on them

| Project | Reality | Why it matters here |
|---|---|---|
| **SMSSync** (`ushahidi/SMSSync`) | **DEAD** — last commit **2017-02-21**. LGPL-3.0, Java, still the top hit for "Android SMS gateway humanitarian" | This is the one a casual search hands you. Do not build the parent channel on it. |
| **FrontlineSMS** (`frontlinesms/frontlinesms2`) | **DEAD** — last real activity **2014-05-21**, one stray commit 2016-11-22. Grails | FrontlineSMS *was* the canonical local-SIM gateway of this sector. Its successor went hosted, then went away. This is §11.1's exit-plan argument as history, not theory. |
| **Freedom Fone** (`freedomfone/FreedomFone`) | **DEAD** — last commit **2016-11-07**; install docs target Ubuntu 12.04/14.04 | Still worth reading: IVR + `gammu-smsd` in one box, deliberately internet-free. |
| **RapidFTR** (`rapidftr/RapidFTR`) | **Retired, with a clean tombstone**: "UNICEF no longer supports RapidFTR, but please check out www.primero.org to see what RapidFTR has grown into." | The best real-world example of `CLAUDE.md` #20 I found in any sector. See PRACTICE. |
| **Verboice** (`instedd/verboice`) | **Semi-dormant** — last commit **2025-02-21** and it was a CI runner bump; last substantive work 2024-03. GPL-3.0, Ruby, IVR | Alive enough to read, not alive enough to depend on. |
| **ELMO → NEMO** | **Renamed.** `thecartercenter/elmo` now describes itself as NEMO | Exactly the "renamed, so your search misses it" case. |

---

## Top finds, with concrete transplant and cost

### 1. `medic/cht-gateway` + the CHT SMS state machine — the local gateway *and* the model of what a message is

The Community Health Toolkit is Medic's platform for community health workers: offline-first
CouchDB apps that reach households through smartphones **and basic phones over SMS**, AGPL-3.0.
Its gateway is an Android app in the band room, exactly as §4.1 imagines: "an SMS gateway for
Android — send and receive SMS from your webapp via an Android phone." Critically it is not
bound to Medic's own server — it configures either a CHT-Core instance URL **or a custom
endpoint**, and ships a demo Node.js server, so the hub can be the only thing it ever talks to.
Real engineering already in it: multipart with a CDMA compatibility mode for networks with poor
multipart support, **idempotent handling keyed on message ID**, and retry with exponential
backoff capped at 20 attempts. It must be the Android default SMS app on 4.4+, which is an
operational fact worth writing into the install acceptance gate — the band-room handset becomes
a single-purpose device, not someone's phone.

The higher-value transplant is not the app, it is the **state vocabulary**, which CHT documents
as: `scheduled` → `pending` → `forwarded-to-gateway` → `received-by-gateway` →
`forwarded-by-gateway` → `sent` → `delivered`, plus four terminal states —
`failed` (will not retry without human intervention), `denied` (recipient matched a configured
denial rule: alphanumeric restriction, length rule, or explicit blocklist), `cleared` (a later
event cancelled the message — *"for example, a patient visited before a reminder was sent"*), and
`muted` (deliberately halted by user action, and unmutable by user action). Read that against
§4.1's three dragged-in problems. `denied` **is** the §7.1 dated-guardianship predicate gating
who gets messaged, expressed as a per-message terminal state with a reason rather than as a
filter that silently drops. `muted` **is** STOP handling, and crucially it is reversible and
attributed. `cleared` is the "rehearsal un-moved" case that a naive queue sends anyway. And
`failed`-does-not-auto-retry is the right default when the payload is about a minor.

CHT's loop protection is embarrassingly simple and worth copying verbatim: an
`outgoing_deny_list` in app settings (`"outgoing_deny_list": "800, SAFARICOM"`), because the
observed failure is the webapp autoreplying to a shortcode forever. Also present:
`multipart_sms_limit`.

**Transplant:** take the 11-state enum and the deny list as the schema of the Announcement/Send
domain from the first write. Take the gateway app as the transport, or as the reference for
capcom6 (below). **Cost:** the enum is a day's work and saves a rewrite; the gateway is AGPL-3.0,
which for a separately-deployed Android relay talking to the hub over HTTP is a *distribution*
question, not a hub-licensing question — but it is a question, and #12's named middle applies:
if the send pipeline declares these states, something must enforce that no send bypasses them.

### 2. `capcom6/android-sms-gateway` — the one that is actually being shipped this month, and Apache-2.0

This is the find I would not have expected to beat the humanitarian incumbents. A Kotlin/Ktor
Android app, 5.2k stars, that "turns your smartphone into an SMS gateway for sending and
receiving messages via API" — and it explicitly offers a **Local Server mode that operates with
no cloud connectivity at all**, plus the option to "deploy your own private server." Release
cadence is the tell: v1.65.0 on May 29, v1.66.0 Jun 22, v1.67.0 Jul 8, v1.68.0 Jul 14,
**v1.68.1 Jul 29** — i.e. yesterday relative to this session. **Apache-2.0**, which sidesteps
the AGPL conversation entirely.

Two cautions I verified rather than assumed. Its dependency list includes **Firebase**, which is
a cloud coupling to check before adopting — the local mode is documented, the Firebase role in
that mode is not, and this is precisely the "cloud fallback chain" refusal #1 exists for. And
**no rate limiting or messages-per-minute control is documented anywhere in the repo**, so the
§4.1 staggering requirement is on us regardless of which gateway wins.

**Transplant:** run it in Local Server mode on the band-room handset, hub posts to it over the
LAN, hub owns the queue and the pacing. **Cost:** an evening to stand up; a real afternoon to
prove the Firebase path is inert in local mode, and that proof belongs in install acceptance
(§10) as a mutation test — block the Firebase host and assert sends still succeed. If it cannot
be shown to work with Google unreachable, it fails refusal #1's spirit even though it is not
inference.

### 3. DHIS2's `protected` access level — §7.2's knock, already shipped

This is the strongest single mechanism I found anywhere in the sector, and it is verbatim from
the DHIS2 tracker user guide:

> "If the program is configured with access level **protected**, and the user searches and finds
> tracked entity instances that is owned by organisation unit that the user does not have data
> capture authority for, the user is presented with the option of breaking the glass."

and the user must "give a reason for breaking the glass, then gain **temporary ownership** of the
tracked entity instance." DHIS2 also exposes an "Audit history" view on the record itself.

Map it straight onto §4's clinician/judge persona and §7.2's knock: a declared purpose on entry
(the reason string), a time-boxed grant that expires without anyone remembering to revoke it
(temporary ownership), and a reconciliation the record itself carries (audit history on the
entity, not only in a server log). The design difference worth noting: DHIS2 attaches the audit
trail **to the record that was opened**, which is `CLAUDE.md` #16's "a student's entries are as
durable as entries about them" in a stronger form than a central log — the trace cannot be
dropped by deleting a log table without deleting the student's own record.

**Transplant:** the reason-string-plus-temporary-ownership pattern, and the decision to make the
access level a **property of the program (context)** rather than of the user's role. §13's
prohibition on standing cross-context scores becomes enforceable if the grant is a property of
the event, as DHIS2 makes it a property of the program. **Cost:** small, if built early; this is
schema, not UI. Note DHIS2's access levels are configured per program and the *names* of the
other levels (I saw the field documented as "Choose the access level of the program", and
`protected` behaviour quoted above) — **I did not verify the full enum of level names from
source**, so do not quote a four-level ladder in prose until someone reads it. `docs.dhis2.org`
is blocked from this session; the markdown lives at
`dhis2/dhis2-docs:src/user/using-the-tracker-capture-app.md`.

Second DHIS2 transplant, from `src/user/relationship-model.md`: relationships between tracked
entities are **first-class data objects** with a `RelationshipType` that constrains each side
(entity kind — tracked entity / enrollment / event — plus tracked-entity-type, program, program
stage), so "a mother-child relationship could mandate both entities are 'Person' type." And the
authorization rule is the part to steal outright: **a unidirectional relationship requires write
access on the source and read on the destination; a bidirectional one requires write on both.**
That is §7.1's guardianship edge with its permission semantics derived from its direction, and
§7.4 W-2's "a name, not a group" enforced by type constraint at creation rather than by review.

### 4. Primero / CPIMS+ / GBVIMS+ — the closest domain sibling that exists, and it is AGPL

Primero is inter-agency child-protection case management — UNICEF, IRC, Save the Children, UNHCR,
Plan International — deployed in 60+ countries with 10,000+ users, and it is the direct successor
to RapidFTR. **AGPL-3.0** (I read the LICENSE: UNICEF copyright 2014, AGPL v3 or later), Rails +
React + PostgreSQL 15, deployed in production via **Ansible** with Docker for development, and
**actively developed — commits through July 9**. Its modules are CPIMS+ (child protection),
GBVIMS+ (gender-based violence, where need-to-know is absolute), and MRM+ (grave violations
against children).

Two things to note honestly. First, **the domain configuration is gated**: the repo README says
that for "access to the CPIMS+ and GBVIMS+ configurations (JSON bundles), please contact
childprotectioninnovation@gmail.com". So the code is AGPL and the *form-and-workflow definitions
that encode a decade of child-protection practice* are behind a request. That is itself a
design signal worth arguing about here — they separated engine from policy, and versioned the
engine publicly while gating the policy. §16's canonical/vendored pair, solved by not shipping
the pair. Second, **its in-repo `doc/` directory is developer material only** (api.md, dao/,
postgres_upgrade, ssl, ui_ux, webhooks) — the consent/referral/transfer semantics live in the
gated configurations and on `primero.org`, which is **blocked from this session**. So I can
vouch for the project's existence, license, stack, and liveness, and I explicitly cannot yet
vouch for the specific consent-and-sealing mechanics from source.

**Transplant:** read it, do not depend on it. AGPL-3.0 on a Rails monolith is not a component
you embed in this app; the value is the data model for a case that multiple agencies touch under
different consent states. **Cost:** a genuine reading week, plus one email if the configurations
matter. **The highest-value single ask in this whole report is that email** — the CPIMS+ form
bundle is the nearest thing to a pre-existing answer to §7.4's Ward Case.

### 5. The `moving-contacts` lesson — revocation does not retract what already replicated

Buried in CHT's operational docs is the most useful *negative* finding in this scout. Moving a
contact to a new parent in the hierarchy "will move the specified contact, all the contacts under
that contact, **and all reports created by any of those contacts**." And then:

> "Offline users who have contacts removed from their visible hierarchy will not automatically see
> those contacts disappear. **The contact remains on the user's device.**"

with updates to those contacts able to "**silently fail to sync**," requiring the user to clear
cache and resync. The tool is deliberately two-phase — download the proposed change locally,
review, then a separate upload command commits it.

Read that against §7.1. A court order arrives mid-season; a guardianship edge gets `invalid_at`;
the resolver correctly stops authorizing. **The records already on that guardian's device do not
move,** and — worse — the failure is *silent*, which is precisely `CLAUDE.md` #13's absence
surfacing as a result rather than as `unknown`. This is a real, documented, production-scale
version of the failure this app is most exposed to, and it comes with the mitigation shape:
the tool refuses to be one-shot, and the docs tell operators to explicitly instruct users to
resync.

**Transplant:** three things. (a) A revocation must produce a *dated, visible* retraction
obligation, not just an authorization change — and it must be reconcilable, because on SMS and on
a replicated PWA it can never be fully satisfied. (b) `CLAUDE.md` #19 says a guard that cannot be
shown to fail has not been shown to work: write the test that revokes an edge and asserts the
system *reports the residue it cannot retract* rather than reporting success. (c) Copy the
two-phase review-then-commit shape for any hierarchy/lane move. **Cost:** the test is cheap; the
honesty is the expensive part, and it belongs in the same register as `corpus-lens` documenting
what its wall does not hide (§4.2).

### 6. Throughput: what the sector actually documents, which is less than you'd hope

§4.1's claim — a person-to-person SIM sending 300 messages in 90 seconds looks like spam and gets
blocked — is correct in spirit, and I want to be precise about what I could and could not verify
from source, because #17 applies.

**What I verified:** `rapidpro/android-channel`'s own README states that "SMS usage on Android is
rate-limited per project," and that this is *why* the architecture includes companion "packs" —
additional paired devices/projects — "to support sending additional messages by distributing the
load across multiple projects." That is a production platform run by UNICEF and Nyaruka
conceding that a single Android relay has a ceiling and solving it by **horizontal fan-out across
handsets**, not by asking the carrier for more. That is directly actionable: the emergency
all-call design should assume N handsets, or accept minutes of latency, and the tier design
should make an all-call rare, as §4.1 already argues.

**What I could not verify from source, and should not be quoted until someone does:** any
specific messages-per-minute figure for `gammu-smsd` or for an Android relay. Neither
`medic/cht-gateway` nor `capcom6/android-sms-gateway` documents any throughput number or
rate-limit control at all — I looked. `community.rapidpro.io` (which has an FAQ likely to cover
it) and `docs.communityhealthtoolkit.org` are both blocked from this session. **Treat every
throughput number currently in `ARCHITECTURE.md` §4.1 as a `P5` assumption** in the sense of
§15 until it has a named source, and note that the honest ones will be *carrier- and
country-specific*, which is the real reason nobody in this sector publishes a number.

**What the sector does instead of publishing numbers:** it builds the pacing into the router.
playSMS (GPLv3, v1.4.8 Aug 2025, 4,183 commits) exists precisely as a queue-and-route layer over
gammu / Kannel / SMS Server Tools / Jasmin, and Jasmin (Apache-2.0, Python/Twisted) is an
SMPP-and-HTTP router with store-and-forward over AMQP — note Jasmin documents **no GSM modem
support**, it is an SMPP ESME, so it is the wrong layer for the sovereign-modem story and the
right layer only if an A2P route is ever added for the emergency class.

### 7. NEMO (was ELMO), and Apollo — mass structured intake from many low-trust reporters

`thecartercenter/elmo` — now **NEMO** — is Apache-2.0, Ruby + JS, 11,414 commits, and **actively
developed with commits through July 16**. It is election-observation infrastructure: thousands of
observers, all of them outside your organization, submitting structured checklists, with
"multiple data entry paths, including web, ODK Collect, **and SMS**" plus **SMS broadcasting**
back out to them. Recent commit messages I saw include "PII removal" and "export caching",
which is a reassuring signal about what its maintainers think about.

Why this matters here more than its subject matter suggests: the judge/clinician persona in §4 is
structurally an election observer. Low trust, event-bound, own device, submits structured
assessments under time pressure, must not be able to browse anything, and the org needs the
submissions aggregated but must not let the aggregate leak individual-level data. NEMO is the
only actively-maintained OSS I found that treats **SMS as a first-class *inbound* structured-form
channel** rather than only as notification — worth reading for the §4.1 acknowledgment class
("Got it", "She's sick tonight") which this project will otherwise hand-roll.

`nditech/apollo` (NDI + TimbaObjects) is the sibling: Flask + Postgres + Redis + a task worker
behind nginx, all Docker Compose, 4,653 commits. Easy self-host on a modest box. I did not read
its license file's type.

### 8. sdcMicro — the egress gate's missing measuring instrument

`sdcTools/sdcMicro`, GPL-2.0, R with C/C++, 1,503 commits, with a Shiny GUI so a non-programmer
can drive it. It anonymizes microdata and — this is the point — **measures disclosure risk** on
the result. §6's egress gate and §4's "corporate / circuit / district never connects, they
receive signed, minimized, aggregated exports" both currently rely on a human deciding that an
export is minimized enough. sdcMicro is the sector's answer to "how would you know," and it
turns "minimized" from an assertion into a number attached to the export.

**Transplant:** not the R dependency — the *artifact*. Every export through the gate should carry
a disclosure-risk statement computed by something, and a k-anonymity-style check on a 200-student
roster's quasi-identifiers (section, grade, instrument, town) will fail loudly and usefully,
because at N=200 a marching band roster re-identifies from three columns. **Cost:** low if the
check is a small in-house function on the export's quasi-identifier set; the value is that it
converts §6 from a ledger into enforcement in exactly `CLAUDE.md` #18's sense.

---

## PRACTICE rather than code — the guidance worth stealing

This sector's most transferable output is not software. Ranked by usefulness here.

**1. RapidFTR's tombstone — the reference implementation of `CLAUDE.md` #20.** The repo
description reads, in full, the retirement notice: *"RapidFTR streamlines and speeds up the Family
Tracing and Reunification process using small handheld devices to collect information. UNICEF no
longer supports RapidFTR, but please check out www.primero.org to see what RapidFTR has grown
into."* Status first, successor named, reason implicit in "no longer supports," contents mapped
forward, and the stub still exists so old links and old citations resolve. It is three sentences
and it does everything §16's "how a document should die" asks. Copy the form.

**2. Enketo's maintainership handoff — the vendor-vanishing drill, executed in public.** ODK
announced in **May 2024** that it was stepping back from Enketo; the **Kobo team assumed
maintainership in March 2025**. Enketo is the web-forms engine underneath ODK, KoboToolbox *and*
OpenClinica — i.e. a genuine single point of failure for a large part of this sector — and the
transition was announced, dated, and to a named party. §11.1 makes the exit plan a shipping
requirement; this is what a good one looks like from the *dependency's* side, and it is the
question to ask of every component in §14's Exists column: if the maintainer steps back, who is
the named successor, and is that written down anywhere?

**3. GBVIMS Information Sharing Protocols.** In the GBV information-management world, an
inter-agency deployment does not go live without a signed **Information Sharing Protocol** — a
document that enumerates what data may be shared, with whom, at what level of aggregation, for
what purpose, and what is never shared at all. That is §4's "corporate / circuit / district"
row and §6's egress policy as a *countersigned artifact between organizations* rather than as
config. **[existence verified via search results only — `gbvims.com` is blocked from this
session; the ISP template itself was not fetched, so do not quote its contents.]** For this
project the analogue is the district and the circuit: a dated, signed, human-readable statement
of what leaves, which the export gate then enforces, with the gate and the document named to each
other per #12.

**4. ICRC, *Handbook on Data Protection in Humanitarian Action*, 2nd ed.** The sector's standard
reference; data minimization is at **§11.6**. Its distinctive contribution — and the reason it is
worth a read here specifically — is its treatment of **consent as a weak legal basis** when the
subject cannot meaningfully refuse, and its use of alternatives (vital interest, important
grounds of public interest) instead. That argument transfers directly: a guardian handed an
enrollment form at a mandatory parent meeting is not in a strong consenting position either, and
§12's medical forms are collected under something closer to vital interest than to free consent.
**[existence and §11.6 location verified from search results; the PDF itself is blocked from this
session at three separate hosts — not fetched, not paraphrased further.]**

**5. IASC, *Operational Guidance on Data Responsibility in Humanitarian Action*, Feb 2021.**
The operational companion to the above, covering information-sharing protocols, retention and
disposal, and **data incident management** as named processes with templates.
**[existence verified; PDF host `icvanetwork.org` blocked — not fetched.]** Flagging it because
"incident handling" is currently absent from `ARCHITECTURE.md`'s compliance map as far as §10
goes, and this sector has the template.

**6. The DPG Standard's 9 indicators — a conformance check this project can actually run.**
`DPGAlliance/DPG-Standard`, CC BY-SA 4.0, v1.1.6 (2024-09-04). The nine: (1) SDG relevance,
(2) approved open licenses, (3) **clear ownership, documented**, (4) **platform independence** —
no mandatory closed dependencies, or a functional open alternative exists, (5) documentation
sufficient for an unfamiliar deployer, (6) **non-PII data extraction in non-proprietary
formats**, (7) privacy and applicable-law compliance by design, (8) alignment with standards and
best practices, (9) **"anticipate, prevent, and do no harm by design."** Indicators 4 and 6 are
§11.1's exit plan restated as a checklist someone else already wrote and maintains; indicator 9
is refusals #1–#7's family resemblance. §17 wants "a template without a conformance check is just
the first copy" — this is a ready-made, externally-maintained skeleton for that check, and using
someone else's rubric is exactly the §17 argument for not writing your own.

**7. The Responsible Data Handbook (The Engine Room).** `the-engine-room/responsible-data-handbook`
exists on GitHub (92 commits, low activity, effectively in maintenance), with the live content at
`responsibledata.io/resources/handbook` — **both the gh-pages host and the site are blocked from
this session, so contents unverified.** Noted for a follow-up with working egress; this is the
sector's plain-language practitioner text on minimization, retention and harm, and the sector's
term of art — "responsible data" — is the search keyword this project is missing.

**8. Medic's own governance detail, found incidentally.** CHT's privacy policy states it "is
reviewed and updated periodically by our **Responsible Data Working Group**" and names a **Data
Protection Officer** contact. A named standing body that owns the policy, and a named human who
answers about it, is the organizational half of §16's middle — a policy with no owner rots
silently. Cheap to copy; the band program's version is one named person in the handbook.

**9. MomConnect (South Africa) — the largest SMS-to-guardians program on record, and its opt-out
design.** Built on Praekelt's **Vumi**, USSD registration at any public clinic, 1.16M mothers
registered Aug 2014–Apr 2017, and — the detail worth stealing — "users can re-register with a new
mobile number should they need to and **they can opt-out from MomConnect should they miscarry or
lose their baby**." A messaging program that designed, up front, for the case where continuing to
send is a harm. Translate: a student who quits, is withdrawn, dies, or is removed from a home
must stop generating messages *by design*, not by someone remembering, and the opt-out must be
reachable from the phone that receives the messages. **[MomConnect facts from peer-reviewed
sources indexed in PMC via search results; `Vumi`'s repo was not fetched and its maintenance
status is unverified — do not assume Vumi is alive.]**

**10. sdcMicro's premise, as practice rather than code:** in this sector, publishing an aggregate
about vulnerable people is treated as a statistical-disclosure problem with a measurable risk,
not as a redaction problem with a human sign-off. That reframing is the practice; the R package is
just where they put it.

---

## Weirdest things I found

**1. Freedom Fone — IVR in a box, wired to `gammu-smsd`, dead since 2016.** A Zimbabwean project
(Kubatana) that built voice menus and voice-mail-drop "radio" for audiences with no literacy
assumption and no internet, with SMS handled by gammu on the same machine. Last commit
**2016-11-07**; install docs target Ubuntu 12.04 and 14.04. Useless as a dependency, genuinely
interesting as a design document: it is the only thing I found that treats **voice as the primary
channel and text as the fallback**, which is the correct polarity for the guardian who cannot
read the language of the announcement — §14's "translation for multilingual families, the most
commonly missing feature in this category." A recorded voice message in the family's language,
delivered by an outbound call from the hub's own modem, leaks less to a carrier than a text does
(no retained message body at the SMSC, no lock-screen render, no iCloud sync) and reaches an
audience SMS does not. `instedd/verboice` (GPL-3.0, Ruby, semi-dormant, last real work 2024) is
the same idea with more recent code. Nobody in this project's fleet is thinking about voice.

**2. Election observation as the clinician/judge threat model.** NEMO (Carter Center) and Apollo
(NDI) both exist to take structured assessments from hundreds or thousands of people the
organization does not control, over SMS and web, at a moment of high stakes and no second chance,
and then aggregate without leaking the individual submissions. Swap "observer at a polling
station" for "judge at a circuit event" and the architecture is the same architecture. NEMO is
Apache-2.0 and had commits **this month**. I would never have searched for election tooling to
solve adjudication commentary intake, and it is the best fit I found for it.

**3. Reticulum — addressing with no authority, over LoRa.** `markqvist/Reticulum`, 6.5k stars,
Python 3, protocol dedicated to the public domain: end-to-end encrypted, multi-hop,
**coordination-less globally unique addressing** built from 512-bit keysets (Ed25519 signing +
X25519 encryption), with **initiator anonymity**, running over LoRa, packet radio, serial, or
WiFi, entirely in userspace. It exists to build networks that have no operator to subpoena and no
kill switch. Two uses here: it is the only serious answer to §4.2's relay that involves no hosted
component and no carrier at all, and — more practically — a competition bus or a marching field
with no coverage is exactly its design case, where §12's lightning-hold and bus-incident
protocols currently assume a working cell network. Also note what its identity model does that
Grove's u2u does not: confidentiality is not an open question in it.

**4. Tella's camouflage and panic delete, as a model for the guest kiosk.** MIT-licensed,
actively developed, and built for human-rights defenders: an encrypted SQLCipher gallery
invisible to the phone's normal file browser, **an app that changes its own name and icon to hide
in the app list**, one-action deletion of everything it holds, metadata capture to prove
provenance, and uploads only to a server you run. There is even a FOSS build variant with
Crashlytics, the Google map provider, and every other tracker stripped out — a shipped example of
`CLAUDE.md` #12's named middle, where the pair is "app with trackers / app without" and the middle
is a maintained separate build. §4 wants "a kiosk device the org owns and wipes" for judges and
clinicians; Tella is a wipe-on-demand encrypted capture app that already exists, and the FOSS
variant's *existence as a policy artifact* is worth more here than the app.

**5. openIMIS — health-insurance claims software for the very poor, which is the fee-waiver
problem.** AGPL, Django + GraphQL, modular, Docker, 1,012 commits. It manages insurees, policies,
enrolment and claims for populations who cannot pay, in institutions with no IT staff — which is
`CAPABILITY-MAP.md` §7 (Finance) and §18 (Equity and Access) with the names changed. A fee waiver
is a benefit determination with an eligibility period, a dated disposition, and an appeal; that is
a solved shape in health-financing software and an unsolved one in every school activity system I
know of. Directly relevant to `CLAUDE.md` #15, "every ask gets a dated disposition."

---

## Gaps and follow-ups for whoever has working egress

1. **Email `childprotectioninnovation@gmail.com`** for the CPIMS+ / GBVIMS+ configuration bundles.
   Highest-value single action in this report.
2. Read `dhis2/dhis2-docs:src/user/using-the-tracker-capture-app.md` and the programs
   configuration doc for the **full access-level enum** and what exactly is written to the audit
   trail on a break-the-glass. Do not restate a four-level ladder in prose until then.
3. Verify **Firebase is inert** in capcom6 Local Server mode, as a mutation test.
4. Fetch the **ICRC handbook §11.6**, the **IASC Feb-2021 operational guidance** (incident
   management + retention), and the **GBVIMS ISP template**. All three were blocked here.
5. Verify whether **Vumi** (Praekelt) is alive at all before citing MomConnect's stack.
6. `sahana/eden` commit dates — I got repo size and issue counts but not dates, and 28 stars with
   6 open issues on a 15k-commit repo is ambiguous rather than healthy.
7. Not investigated for lack of budget, and plausibly rich: agricultural-extension IVR/SMS
   advisory at scale (Precision Development, Gram Vaani, Viamo's 3-2-1 service — practice on
   staggering millions of low-value messages), refugee registration (UNHCR PRIMES is not open
   source; MOSIP's guardian/introducer enrollment for undocumented people and infants is
   unverified and would matter for §7.1), and IOM's CTDC, which I believe published a
   trafficking-victim microdata set under formal disclosure control — **unverified, host blocked,
   flagged as a lead only**.
