# Scout 04 — Authorization as time-boxed relationship edges; the guest-access shape

Slice: relationship edges with expiry instead of roles; guest grants; the knock (declared
purpose reconciled at session close); narrate-the-read / gate-the-export.

Read first: `docs/ARCHITECTURE.md` §7–§7.4, §12, `CLAUDE.md`.
Every project below was fetched and confirmed to exist unless explicitly marked
**UNVERIFIED** in the verification notes at the end. Nothing is named on memory alone.

---

## 0. The finding that reorders the search

The brief asks for two things that pull in opposite directions:

1. *grants that die on their own with nobody remembering to revoke them* → argues for
   **bearer capability tokens** (macaroons, Biscuit, UCAN, Tenuo). Their whole value is that
   the verifier needs no central authority and no network.
2. *"who could see Ben's medical form on October 12, and why"* → argues for a **dated fact in
   a store the box owns**, which is §7.1's `valid_at`/`invalid_at`.

The token family cannot serve (2), and its own specs say so. UCAN states plainly that it
"do[es] not offer confinement (as that would require all processes to be online), so it is
impossible to guarantee knowledge of all of the sub-delegations," and treats revocation as a
last-resort remedy. Biscuit's revocation story is a *list of block signatures the verifier is
expected to have been told about*. Both are the right design for a distributed system with no
authoritative middle — and terpsi-music is the exact opposite: one on-prem box, zero inbound
ports, one canonical store, one predicate every read funnels through (§7's `Store.predicate`).
**The box has confinement. Spending it to buy offline verification is a bad trade**, and it
would convert §7.1's answerable history into a best-effort revocation list.

So the correct posture, and the thing this report is organised around:

- **Enforcement stays where §7 already put it** — one SQL predicate over bitemporal edges.
  Nothing found beats it for this deployment; several things found are *worse* in a way that
  is invisible until a court asks (see SpiceDB below, which garbage-collects expired edges).
- **Steal shapes, not runtimes**, from the capability world: attenuation-only delegation,
  TTL mandatory at issuance, sealed/terminal grants, signed receipts, `nbf` as well as `exp`.
- **The genuinely missing half — reconciliation of declared purpose against observed
  behaviour — is not in the authz world at all.** It is in runtime verification (MonPoly),
  process mining (PM4Py), and healthcare audit research (explanation-based auditing). That is
  where the transplantable prior art lives, and none of it is authz middleware.

---

## 1. Ranked table

Ranked by value to this slice, not by popularity.

| # | Project | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **HL7 FHIR `Consent` + `Permission` + `AuditEvent`** (hl7.org/fhir) | Spec. `Consent.provision` nests permit/deny with a `period`, `actor`, `purpose`; `AuditEvent.agent.purposeOfUse` carries the *declared* reason an actor participated | HL7 (free, open) | R5 published, R6 balloting | §7 edge table, §7.2 knock, §12.9 | **adopt the vocabulary** |
| 2 | **MonPoly** (upstream bitbucket `jshs/monpoly`; verified fork `remolueoend/monpoly`) | Tool that checks *log files* for compliance with policies in Metric First-Order Temporal Logic; papers include "Monitoring usage-control policies in distributed systems", "Scalable Offline Monitoring" | LGPL-2.1 | OCaml, prototype, ETH Zurich, fork active 2025 | §7.2 reconciliation, §12.9 | **steal the idea → possibly adopt as the reconciler** |
| 3 | **REMS** — Resource Entitlement Management System, CSC Finland (`CSCfi/rems`) | System. Outsiders apply for access to someone else's sensitive records; owner/committee approves; produces an *entitlement* and a signed GA4GH visa; full audit trail of committed actions | MIT | Clojure/CLJS, ~12.8k commits, 64★, active | §7 guest grants, §7.4 I-6 | **steal the idea (read the schema)** |
| 4 | **Biscuit** (`biscuit-auth/biscuit`) | Token. Datalog checks, offline attenuation by appending signed blocks, third-party blocks, **sealed** tokens (terminal, no further attenuation), revocation identifiers = block signatures | Apache-2.0 | 1.1k★, 293 commits, impls in Rust/Py/Go/Java/Haskell/C#; in prod at Apache Pulsar, Clever Cloud | judge/clinician session token | **adopt (narrow), if a token is wanted at all** |
| 5 | **PREMIS rights + Archivematica** (`artefactual/archivematica`) | Spec + system. `termOfGrant` / `termOfRestriction` containers each carry start and end dates; "Allow" → grant, "Disallow"/"Conditional" → restriction; a donor restriction can be set to *expire*, after which records release automatically | AGPL-3.0 (Archivematica); PREMIS = LoC standard | Python, 510★, active | §7.1 dated termination, §15 L-ladder | **adopt the vocabulary** |
| 6 | **Cedar + datetime extension** (`cedar-policy/cedar`, RFC 0080) | Policy language. Native `datetime`/`duration` types with `offset`, `durationSince`, comparisons; symbolic compiler (`cedar-policy-symcc`) verifies properties **and returns concrete counterexamples** | Apache-2.0 | Rust, 1.6k★; datetime accepted 2024-09, shipped 4.3.0 2025-01 | §7 predicate, §10 mutation testing | **steal the idea** |
| 7 | **Explanation-Based Auditing** — Fabbri & LeFevre (arXiv 1109.6880; JAMIA 2013) | Research. Generate an *explanation* for each access to a patient record from data elsewhere in the DB; review only the **unexplained** residue. >94% of accesses explained | paper (see patent flag) | 2011–2013, no OSS impl found | §7.2 narrate-the-read | **steal the idea** |
| 8 | **SpiceDB** (`authzed/spicedb`) | ReBAC engine. Caveats (CEL over request context) + **Relationship Expiration** as a first-class trait on an edge (1.40, experimental) | Apache-2.0 | Go, 6.9k★, very active; self-host, no control plane needed | §7 edges | **steal the idea — do NOT adopt as store of record** |
| 9 | **PM4Py** (`process-intelligence-solutions/pm4py`) | Library. Conformance checking: alignments produce an optimal *diff* between a declared model and an observed trace (skips/inserts), plus fitness & precision | **AGPL-3.0** (commercial available) | Python, 994★, 9.6k commits | §7.2 the diff | **steal the idea** |
| 10 | **UCAN** (`ucan-wg/spec`) | Spec. Delegation chains, attenuation MUST-not-widen, `nbf`/`exp`, chain-as-provenance-log | Community Spec License v1 | v1.0.0, 285★ | guest delegation | **read-only interest + one idea (`nbf`)** |
| 11 | **Netflix Repokid** (`Netflix/repokid`) | Tool. Strips IAM permissions a role has not actually used (via Access Advisor) — reconciles *granted* against *observed* | Apache-2.0 | Python, 1.1k★, 344 commits | §7.2 inverse knock | **steal the idea** |
| 12 | **Tahoe-LAFS capability lattice** (tahoe-lafs.org) | System. write-cap → read-cap is a one-way **diminish**; verify-cap is weaker still: proves integrity **without reading plaintext** | GPL-2+/TGPPL | v1.20.0 (2024-12), Python, active | §7.2 read vs export | **steal the idea** |
| 13 | **Teleport** (`gravitational/teleport`) | System. `--reason` on session start → propagated into a `session_tracker` resource; session recording; moderated sessions (a second human must be present) | AGPL-3.0 (OSS edition) | Go, very active, self-hostable | §7.2 knock, W-7 escalation | **steal the idea** |
| 14 | **W3C DPV + ISO/IEC TS 27560 consent records** (`w3c/dpv`, `w3c-cg/dpv`) | Vocabulary + spec. `hasExpiry` → `hasExpiryTime` *or* `hasExpiryCondition`; `hasProvisionTime`/`hasWithdrawalTime`/`hasWithdrawalMethod`; `ConsentExpired` as an explicit state | W3C CG / open | active, 2.3 releases | §7.3 consent chain, §13 | **adopt the vocabulary** |
| 15 | **Tenuo** (`tenuo-ai/tenuo`) | Rust library. Cryptographic "warrants": scoped, TTL'd, **subtractive delegation**, holder-bound (proof-of-possession), offline verify <50µs, **signed authorization receipts** | Apache-2.0 | Rust+Python, 680 commits, 77★, v0.2, Dec 2025 | guest tokens, §7.2 receipts | **read-only interest (young) + steal "receipt"** |
| 16 | **Topaz** (`aserto-dev/topaz`) | Local authorizer: OPA decision engine + embedded Zanzibar-style directory + decision logs; sidecar, embedded DB, no cloud control plane | Apache-2.0 | Go, 1.4k★, 893 commits | on-prem reference arch | **read-only interest** |
| 17 | **OpenBao** (`openbao/openbao`) | Vault fork under LF open governance. Every secret carries a **lease**; at lease end it is revoked automatically; hierarchical revocation trees | MPL-2.0 | Go, 6.9k★, 20.9k commits | grant TTL mechanics | **read-only interest** |
| 18 | **libmacaroons** (`rescrv/libmacaroons`) | C library. Caveat-based attenuation, third-party caveats + discharge macaroons, offline verification via chained HMAC | BSD-3-Clause | C+Python, 513★, 90 commits, quiet | precursor to Biscuit | **read-only interest** |
| 19 | **OpenFGA** (`openfga/openfga`) | Zanzibar-style engine; SQLite/Postgres/MySQL; Conditions (ABAC) incl. documented **temporal access policies**, contextual tuples | Apache-2.0 | Go, 5.5k★, 2k commits | §7 edges | **read-only interest** |
| 20 | **ArchivesSpace** (`archivesspace/archivesspace`) | System. Machine-actionable restriction fields: Local Access Restriction Type (required) + **Restriction Begin / Restriction End**; rights statements can scope access to a *location* (the reading room) | ECL-2.0 | Ruby, 433★, active | §7.1, export class | **read-only interest** |
| 21 | **GA4GH Passports / Visas / AAI** (`ga4gh-duri.github.io`) | Spec. `ControlledAccessGrants` visa = "this DAC approved this person for this dataset"; systems using visas **MUST** provide mechanisms to limit the life of access; `exp` checked, with early-expiry logic | open spec | active standard | guest grant issuance | **read-only interest** |
| 22 | **Solid Access Requests & Grants** (`inrupt/solid-client-access-grants-js`) | VC-based access grants carrying **`purpose`**, `issuanceDate`, `expirationDate`; the derive endpoint excludes expired *and* **future-dated** grants | MIT (client lib); ESS server is commercial | active | §7.1 future-dated order | **read-only interest** |
| 23 | **Fraunhofer IESE MYDATA / IND²UCE** (mydata-control.de) | Usage-control framework: PEPs that filter/mask at data interfaces, obligations like "usable only 8–17 on working days", "log this use", "delete by date" | licence not confirmed — likely not OSS | commercial product, active | §7.2 obligations | **read-only interest** |
| 24 | **GTRBAC** — Joshi & Bertino | Research. Periodic *and* duration constraints on roles, user-role and role-permission assignments; separates *enabling* from *activation* | paper | 2000s, foundational | §7 formal grounding | **read-only interest** |
| 25 | **Spritely Goblins / ocaps / Capsicum libcasper / Zircon rights** (see §5) | ocap systems: revocable forwarders, `Revoker`/`Revocable`, rights-reduction on handle duplicate | Apache-2.0 / BSD / various | all active except `ocaps` (2018) | attenuation patterns | **read-only interest** |

Hosted-control-plane flags (host is one on-prem box, zero inbound, no cloud):
**tlock** (§5) is disqualified — decryption *requires* reaching a drand beacon. **Tenuo Cloud**
and **AuthZed Cloud** are optional add-ons; their OSS cores are standalone. **Inrupt ESS** (the
server behind Solid Access Grants) is commercial — the client library is not enough to adopt.
Everything else in the table runs offline.

---

## 2. Top finds — transplant and cost

### 2.1 FHIR `Consent` / `Permission` / `AuditEvent.purposeOfUse` — the only standard that puts purpose in *both* halves

This is the highest-value find and it is a vocabulary, not a dependency. `Consent` is defined as
a directive that "permits or denies identified actors or roles to perform actions affecting the
patient within a given context **for specific purposes and periods of time**." Structurally:
a base `decision` (permit|deny), then `provision`s that state exceptions, each provision carrying
`period`, `actor` (reference + role), `action`, `purpose`, and `securityLabel`. R5 splits out a
`Permission` resource for the non-patient-consent case. And on the audit side,
`AuditEvent.agent.purposeOfUse` records **the reason a particular actor was involved** —
asserted from that actor's own perspective, with multiple values allowed.

That is §7.2's knock, in a published standard, in a domain with the same owner≠subject problem
this app has. The grant declares purpose; the audit record declares purpose; a reconciler can
diff them. FHIR does not *do* the reconciliation — but it is the only mainstream vocabulary that
holds both sides in comparable shape.

**Transplant.** Name the grant table's columns after `Consent.provision`: `decision`
(permit|deny), `period_start`/`period_end` → the existing `valid_at`/`invalid_at`, `actor`,
`action`, `purpose`, `security_label` → the `L`-ladder rung (§15). Name the disclosure log's
purpose column `purpose_of_use` and make the knock's entry header write it. Two nested provision
levels give the family-circle semantics for free: base deny, one permit provision per guardian
edge, one deny provision for the restricted guardian with its own `period` — which is exactly
§7.1's court order, expressible without inventing anything.

**Cost.** Low, and it is mostly discipline: FHIR's own nesting semantics (a provision inside a
permit provision is an exception to the exception) is a trap, and §7's resolver already fixed the
predicate as `(allow₁ OR …) AND NOT (deny₁ OR …)`. Take the *field names and the period*, not the
recursion. Do not import FHIR resources, a FHIR server, or HAPI — that would create exactly the
canonical/vendored pair §16 forbids, with no middle. One page in `docs/` mapping our columns to
FHIR element names is the whole transplant, and it buys a regulator-legible schema for free.

### 2.2 MonPoly — the reconciler already exists, and it is not an authz tool

MonPoly is an ETH Zurich prototype (OCaml, LGPL-2.1) that "checks the compliance of log files
with respect to policies that are specified by formulas in Metric First-Order Temporal Logic."
Its own citation list includes *Monitoring usage-control policies in distributed systems* and
*Scalable Offline Monitoring of Temporal Properties*. MFOTL is first-order (quantify over
students, guests, events), metric (intervals: "within 36h", "before the event", "not after
`invalid_at`"), and temporal — so a formula can say things §7 currently states in prose:

- *every export event is preceded within the same session by a knock declaring `export`*
- *no disclosure event names a student for whom a deny provision was valid at that instant*
- *every request has a disposition within its declared timebound* (§7.4 I-6, including the
  "the office cannot lengthen its own timebound" clause, which is a second formula)
- *no read of `HEALTH` occurs in a session whose declared purpose was `score_ensemble`*

**Transplant.** The knock already writes an append-only history (§7.1 excludes reconciled
sessions from bitemporal supersession — correct). Emit that history as a MonPoly-shaped log:
one timestamped line per event, predicates with named arguments. Then the reconciler is a
*formula file in the repo*, versioned, reviewable, and — crucially for §10 — **mutation-testable**:
inject a synthetic violating trace and assert MonPoly reports it. That is a guard that can be
shown to fail. Start with three formulas, not thirty.

**Cost.** Real but bounded. (a) OCaml build in the box's toolchain, or run it offline in the
sandbox (§5.1) over exported log slices — offline monitoring is a documented mode, which suits
a nightly reconciliation better than an inline gate anyway. (b) LGPL-2.1: fine as a separate
executable invoked over files; do not link it. (c) It is a *prototype* — treat it as the ledger
side (§7.2's "say which"), never as the thing that prevents. (d) If the OCaml dependency is
unacceptable, the transplant degrades gracefully to hand-written SQL assertions over the same
log — the durable value is **the log format and the formulas**, and MFOTL is worth reading even
if MonPoly never ships. Flag: I verified the fork's README (LGPL-2.1, OCaml, upstream on
Bitbucket); the upstream Bitbucket page itself did not render for me.

### 2.3 REMS — the closest *domain* analogue found anywhere, and it is MIT-licensed

REMS (CSC Finland, MIT, Clojure) exists because outsiders need time-boxed access to someone
else's sensitive records about people. An applicant logs in with a federated ID, applies for a
named resource, accepts terms; the application circulates to the resource owner or a designated
representative for approval; approval produces an **entitlement**; and the system "produces the
necessary reports on the applications and the granted data access rights," with an audit trail
of all committed actions. It optionally emits the entitlement as a signed GA4GH
`ControlledAccessGrants` visa (JWT, `iss` from config, JWKS at `/api/jwk`) — i.e. the grant is
*also* an offline-verifiable capability, while the store keeps the answerable history. That is
precisely the two-layer split §0 above argues for, already built by someone else.

Read it for three things: (1) the **application→approval→entitlement→revocation** state machine,
which is §7.4 I-6's "every ask gets a dated disposition" with reminders and reporting attached;
(2) the separation of *resource*, *workflow*, *catalogue item*, and *licence* — the same shape
this app needs for judge-at-event vs clinician-at-session; (3) how it reports entitlements to
downstream systems without those systems holding a copy.

**Transplant.** Steal the state machine and the vocabulary (`application`, `entitlement`,
`handler`, `licence`), not the code — Clojure/CLJS is a whole second stack. The fee-waiver,
absence-request and records-inspection surfaces (§7.4 I-6, capability map §18) are the same
object as a REMS application, and building them as one mechanism with a declared timebound is
strictly cheaper than three.

**Cost.** Zero if used as a design reference. Adopting the service itself would import Clojure,
a Postgres schema, and federated-login assumptions this box does not want. Do **not** copy its
GA4GH visa emission literally — a JWT entitlement handed to a judge is a bearer token whose
revocation is unanswerable, which is the §0 trap.

### 2.4 SpiceDB relationship expiration — the right primitive, with a disqualifying implementation detail

SpiceDB (Apache-2.0, Go, self-hostable with no control plane) is the ReBAC engine whose data
model is closest to §7's edges, and as of 1.40 it has **Relationship Expiration** as an
experimental first-class trait: a write can carry an expiration time, "after which a relationship
will be treated as removed and eventually automatically cleaned up." Before that, users expressed
time-bounds through **caveats** — CEL expressions evaluated against request context, which is a
clean way to say "this edge holds only while `now < expires_at`". Authzed's own write-up notes
that without first-class expiry, time-bounding "clutter[s] the permissions graph".

**The disqualifier is in the sentence above:** expired relationships are *garbage collected*.
There is an open issue about GC of caveat-expired relationships. A system that deletes the edge
when it expires cannot answer "who could see Ben's medical form on October 12, and why" — it is
§7.1's `DELETE` failure with better ergonomics. This is the most useful negative result in this
report: the leading open-source ReBAC engine's answer to expiry is *removal*, and this project's
hard rule is that revocation is never removal.

**Transplant.** Take the primitive, invert the disposal. Put `expires_at` on the edge as a
**third** dated column alongside `valid_at`/`invalid_at`, and never collect. Then the three
sources of an edge ending are one mechanism with three sources: arithmetic (majority),
issuance-time TTL (`judge_at` +36h), and order (`invalid_at` set by a court). Adopt the caveat
idea as a `condition` column holding a small, enumerable expression — and note Cedar (below)
is the better language for that column than CEL, because it can be symbolically verified.

**Cost.** If SpiceDB itself were adopted: a second datastore of authorization truth beside the
canonical store, i.e. a §16 pair with no middle, plus GC that destroys the history. Recommend
against. Reading its schema language and its expiration blog posts costs an afternoon.

### 2.5 Explanation-Based Auditing — makes "narrate the read" survivable

Fabbri & LeFevre's insight: in an EHR, *most* accesses are legitimate and their reason is already
recoverable from data elsewhere in the database (this clinician is on that patient's care team,
this appointment exists, this order was placed). So generate an explanation per access, and hand
the compliance officer only the **unexplained** residue — reported at >94% explained in their
study, with an associated JAMIA paper on explaining accesses via diagnosis information.

§7.2 commits to narrating reads. In a 200-household program with a season of rehearsals, honest
narration produces a log nobody reads, and an unread log is a ledger that is not even a ledger.
This is the technique that turns it into something a director can actually act on.

**Transplant.** For each read event, attempt to derive an explanation from dated facts the store
already holds: *guardian edge valid at that instant*, *staff_of edge for the ensemble the student
is in*, *judge_at edge for the event this sheet belongs to*, *the student asked for it (W-4)*.
Explained reads roll up to a count in the guardian's own disclosure view (FERPA §99.32 wants the
record anyway). Unexplained reads are the narration. This composes exactly with the knock: a
session's declared purpose is one more explanation source, and *an access explained only by the
grant and not by any relationship in the data* is the §7.2 reconciliation failure — the judge who
declared "score ensemble 7" and touched forty medical records.

**Cost.** Moderate design work, small implementation: the explanation rules are the same joins the
resolver already computes. **Flag: there is a granted US patent (US8745085B2, "System for
explanation-based auditing of medical records data").** I did not read its claims. Treat the
technique as *cite the paper, design independently, and get an opinion before shipping the phrase
"explanation-based auditing" in a product*. The underlying idea — audit by residue — is older and
broader than the patent, but that call is not mine to make.

### 2.6 Biscuit — if a guest token is wanted at all, this is the one

Biscuit (Apache-2.0; Rust, Python, Go, Java, Haskell, C#; in production at Apache Pulsar and
Clever Cloud) is the best-engineered member of the token family for this shape. Four properties
matter here:

- **Expiry is a check, not a field:** `check if time($0), $0 < 2019-02-05T23:00:00Z`. The
  authorizer supplies `time` as an ambient fact. This is the same discipline as §7's "minor
  status is a birthdate, not a flag" — the expiry is *evaluated*, never a state someone clears.
- **Attenuation is append-only and cryptographically chained:** the holder can add blocks that
  only narrow. A judge handed a token for Event 42 can hand a narrower one to their scribe and
  cannot widen it. Blocks cannot be removed without breaking the signature chain.
- **Sealed tokens** are terminal: no further attenuation possible. That is a primitive §7.4 W-2
  wants — a grant naming one ward, which nobody downstream can generalise.
- **Revocation identifiers** are block signatures, surfaced to the authorizer as
  `revocation_id(index, bytes)` facts — so revocation is a *list the verifier consults*, i.e.
  exactly the thing that must become a dated row here rather than a list.

**Transplant.** Narrow use only: the on-site guest session on a borrowed tablet (§7.2's judge).
Issue a sealed Biscuit at check-in carrying `event`, the caption set, the window, and a `time`
check; the tablet holds no standing credential. Then **the token is not the authority** — it is a
convenience over an authority that already exists as a dated row, and every read still funnels
through the resolver predicate, which re-derives from edges. Write the revocation identifier into
the grant row so "was this token live on October 12" is answerable from the store.

**Cost.** Two: (a) a second authorization vocabulary in the tree (Datalog checks *and* SQL
predicate) — a §16 pair, and the named middle must be *the issuer writes both, in one
transaction, or neither*; (b) key material. Biscuit needs a signing keypair, and §6's rule is
that the trust root never enters the tree. If the honest answer is that a session cookie bound
to the box plus a dated grant row does the same job, **skip Biscuit entirely** — its value is
offline verification, and there is nothing offline in this deployment. Recommended posture:
read the spec, adopt the *sealed* and *check-if-time* concepts as design rules, defer the library.

### 2.7 PREMIS rights and Archivematica — a whole profession already spells revocation as a date

PREMIS (Library of Congress) splits rights into `termOfGrant` and `termOfRestriction`, each a
container with start and end dates. Archivematica implements it directly: choose "Allow" and it
creates a `termOfGrant`; choose "Disallow" or "Conditional" and it creates a `termOfRestriction`.
A blank end date explicitly means *unknown or varies* — not *forever*. And the documented payoff
is the one §7.1 is written toward: "a donor policy could be set with a restriction to expire
after a certain date, after which the records could be released to an access system." Restriction
as a dated predicate, driving an automated state change, in production digital-preservation
software since the 2010s. ArchivesSpace independently carries machine-actionable `Restriction
Begin` / `Restriction End` plus a required restriction-*type* code, and its rights statements can
restrict access to a **location** — the reading room.

**Transplant.** Three concrete steals. (1) The **grant/restriction split with symmetric dated
terms** — one table, a `basis` (donor agreement / court order / statute / majority arithmetic),
and a `type` code. This is §7.1's proposal with a standards-body spelling already in the fleet's
preferred shape (`valid_at`/`invalid_at`). (2) **A required restriction-type code**, so "restricted"
is never a free-text note — that is `quiet-corner`'s failure mode (§7.3) in a different costume.
(3) **Blank end date means unknown, not unbounded** — which is §13/CLAUDE.md rule 13, *absence
surfaces as `unknown`, never as a result*, arrived at independently by archivists.

**Cost.** Vocabulary only; no code. AGPL-3.0 applies to Archivematica's code, which is not being
taken. The one thing to resist is PREMIS's full act/basis/documentation graph — it is far larger
than this domain needs.

### 2.8 Cedar's datetime extension — the condition column, with counterexamples

Cedar (Apache-2.0, Rust) gained a native `datetime`/`duration` extension: RFC 0080, accepted
2024-09-11, implemented 2024-11-13, released in `cedar-policy` 4.3.0 on 2025-01-21 as
experimental. It provides real types with `.offset(duration)`, `.durationSince()`, `.toDate()`,
`.toTime()` and full comparison operators — so a validity interval is expressible *in the policy
language*, not smuggled in as integer seconds. It needs no hosted service; it is a crate.

The more interesting half is `cedar-policy-symcc`, the symbolic compiler, which verifies
properties about policies and **returns concrete counterexamples**. §10/CLAUDE.md rule 19 says a
guard that cannot be shown to fail has not been shown to work, and §7's own regression test exists
because of a bug whose signature was silence. A tool that hands you the input on which two policy
versions differ is the mechanised form of that discipline.

**Transplant.** Two options, and I'd take the first. (1) **Steal the type discipline**: whatever
expression language goes in the edge's `condition` column, give it real datetime and duration
types with prefixes and one mapping table (§15's rule generalised from ordinal scales to time),
and never compare bare epoch integers. (2) If a policy language is genuinely wanted, Cedar is the
one to evaluate, because it is the only candidate here with an SMT-based analyser — the
"differential" question *"does this new deny provision withhold any row the old one showed?"* is
answerable mechanically rather than by fixture.

**Cost.** Adopting Cedar means a Rust component and a second policy home beside the SQL predicate
— a §16 pair again. The datetime extension is still flagged experimental. Recommend: read RFC
0080, borrow the operator set, keep enforcement in the predicate.

### 2.9 Tahoe-LAFS, Teleport, Repokid, PM4Py — four short ones worth the read

- **Tahoe-LAFS** gives the cleanest existing statement of *read ≠ export*: a read-cap is
  **diminished** from a write-cap by a one-way derivation, and a **verify-cap** is weaker still —
  it proves integrity *without granting plaintext*. Transplant: make export a distinct permission
  class that cannot be derived from any read grant (§7.2, §9), and steal verify-cap for the case
  this app will hit — *proving to a district or a court that a record exists and is unaltered
  without disclosing it*. Cost: none, it is a design lattice.
- **Teleport** already ships the knock's front half in production software: `--reason` on session
  start, recorded into a `session_tracker` resource, alongside session recording and **moderated
  sessions** (a designated human must be present for the session to proceed). Transplant: the
  reason string is cheap and it is the piece most systems omit; moderated sessions are §7.4 W-7's
  "halt and escalate" as a runtime primitive rather than a policy sentence. Cost: reading docs.
  Note honestly what it does *not* do — Teleport records the reason and never diffs it against
  what happened. Nothing I found does. That gap is the knock's actual novelty.
- **Repokid** (Netflix, Apache-2.0, Python) reconciles the *other* direction: it strips
  permissions a role never exercised, driven by observed-use data. Transplant: run the knock's
  history against the grant table quarterly and surface `staff_of` and `director_of` edges whose
  permissions were never exercised — evidence for narrowing. Careful: W-5 says agency widens only
  by signature; *narrowing* on evidence is permitted, and this is the tool-shape for it.
- **PM4Py** (AGPL-3.0) formalises the diff itself: alignment-based conformance produces an optimal
  mapping between an observed trace and a declared model, listing skips and inserts. That is
  literally §7.2's thirteen-in / thirteen-out diff with a theory behind it. Transplant: the
  *concept* of an alignment as the reconciliation artifact ("here is the cheapest explanation of
  how this session deviated"), which is far more useful in a disclosure report than a boolean.
  Cost: AGPL-3.0 makes linking a licensing decision, not a technical one — read the algorithm,
  don't import the library.

---

## 3. What nobody has built

Worth recording plainly, because it changes the build-vs-adopt call for the knock:

**No project found reconciles a declared session purpose against observed session behaviour at
close.** Teleport captures a reason and never checks it. FHIR records `purposeOfUse` in both grant
and audit and provides no comparator. GA4GH visas and Solid Access Grants carry purpose and expiry
and are never audited against use. REMS records why access was granted, not what was done with it.
The only prior art is in three adjacent fields — runtime verification (MonPoly), process mining
(PM4Py), and health-records audit research (explanation-based auditing) — plus the formal
semantics of purpose itself (Tschantz, Datta & Wing, *Formalizing and Enforcing Purpose
Restrictions in Privacy Policies*, IEEE S&P 2012, which defines purpose *behaviourally*: an action
serves a purpose if it is part of a plan to achieve it, and gives an auditing algorithm on that
basis — the single best conceptual grounding I found for what "did they do what they said" means).

So §7.2 is not a feature to shop for. It is the thing this project would actually be contributing,
and the honest scope is small: a declared-purpose field, an append-only session history, and three
formulas that fail on synthetic violating traces.

---

## 4. Cross-cutting notes against CLAUDE.md's hard rules

- **No group grants / wildcard invalid at issuance (W-2).** Every engine surveyed makes group and
  wildcard grants *easy* — Zanzibar's userset rewrites exist to express "everyone in the drumline."
  Nothing found refuses them at issuance. This is a genuine inversion of the ReBAC grain and must
  be enforced locally, by `CHECK` constraint and a mutation test that attempts a section-level
  grant and asserts refusal. Biscuit's **sealed** token is the nearest existing primitive.
- **No standing cross-context scores (SA-3).** Nothing in the authz corpus addresses this; the
  relevant prior art is unlinkability work (pairwise pseudonymous identifiers, selective
  disclosure). Out of this slice; flagged as unowned.
- **Revocation is never deletion.** Confirmed as a real divergence: SpiceDB *collects* expired
  edges; OpenBao *revokes* leases; UCAN and Biscuit revoke by list. The only surveyed systems that
  spell revocation as a dated fact are the archival ones (PREMIS, ArchivesSpace) and DPV
  (`hasWithdrawalTime`). Take the vocabulary from the archivists, not the engineers.
- **Absence surfaces as `unknown`.** PREMIS's "blank end date means unknown or varies" and DPV's
  distinction between `hasExpiryTime` and `hasExpiryCondition` are both usable precedents for
  writing this down in the schema rather than the prose.
- **Enforcement vs ledger.** Of everything here: enforcement candidates are the SQL predicate,
  Cedar, SpiceDB, Topaz, OpenFGA, Biscuit. Ledgers are MonPoly, PM4Py, Repokid, Teleport's
  recording, and explanation-based auditing. The knock is a **ledger** unless a harness routes
  every export through it first — §7.2 already says this; nothing found changes it.

---

## 5. Weirdest things I found

1. **Hotel key cards are the correct engineering reference for a 36-hour judge grant.** The
   checkout time is *encoded on the card*, and the lock decrypts the authorization code, reads the
   check-in/check-out interval, and compares it against **its own real-time clock** — no network,
   no revocation list, no central authority, and the card dies on schedule with nobody
   remembering. The patent literature (e.g. US5397884, US11200763) describes multi-tier validity
   windows: a short "first validity time" that renews and a longer "second validity time" set from
   the length of stay, so a lost card degrades quickly while a 30-night guest is not
   re-provisioned nightly. That is a direct answer to §13's open question about a 200-household
   deployment re-authorizing eight streams every morning: **two nested validity intervals, one
   short and self-renewing, one long and set at issuance.** The whole industry solved
   "time-boxed guest capability, offline, no revocation" decades ago in brass and firmware.
2. **Archivists automate *release*, not access.** In Archivematica, a donor restriction with an end
   date causes the records to become available when it lapses — the dated predicate runs *toward*
   openness. Every authz system surveyed models time as a shrinking grant; the archival model has
   restrictions that expire into access. For a music program this is the graduation case (W-6) and
   the retention case at once: the interesting date is often when something *stops* being sealed.
3. **A "verify-cap" — proof without disclosure — is a permission class this design has not
   named.** Tahoe-LAFS's third capability tier lets a holder confirm integrity while unable to read
   plaintext. §7.2 splits read from export; there is a third, weaker act — *attest that a record
   exists and is unaltered* — which is exactly what a district audit or a court's first question
   needs, and granting it currently requires granting read.
4. **Library circulation software has shipped `guardian_of` with an expiry date for years.** FOLIO
   models a **proxy/sponsor** relationship — one patron authorized to act on another's behalf —
   with an **Expiration date** field on the relationship itself; Koha carries guarantor/guarantee
   with a per-category "can be guarantee" flag. It is the family-circle edge, in production,
   in software with no security pretensions, where nobody argued about it.
5. **Timelock encryption is the perfect answer to §7.1's future-dated order, and it is
   disqualified.** `drand/tlock` (Apache-2.0/MIT, Go) encrypts data that *cannot* be decrypted
   before a chosen time, which is precisely "a restriction that must take effect at a future date
   has nowhere to live until it does," inverted. But decryption requires fetching a BLS signature
   from a drand beacon over the network — `api.drand.sh`, Cloudflare relays — so it cannot run on a
   box with zero inbound and no cloud dependency. Worth knowing it exists, and worth knowing the
   cheap local substitute is UCAN's `nbf` field: a grant that is *stored, signed, dated, and not
   yet valid*, with the spec's own note that a future `nbf` enables "pre-provisioning."

---

## 6. Verification notes (what I could and could not confirm)

Confirmed by direct fetch of the repository or spec page: Biscuit (Apache-2.0, 1.1k★, expiry check
syntax, sealed tokens, revocation ids), UCAN spec (v1.0.0, Community Spec License, `nbf`/`exp`
rules and the confinement admission), REMS (MIT, Clojure, 64★, ~12.8k commits; GA4GH visa doc
read), SpiceDB (Apache-2.0, Go, 6.9k★, caveats; expiration confirmed via Authzed docs/blog and
issue #1262), OpenFGA (Apache-2.0, Go, 5.5k★, SQLite/Postgres/MySQL), Cedar (Apache-2.0, Rust,
1.6k★, `symcc`) and RFC 0080 (datetime/duration, accepted 2024-09-11, shipped 4.3.0 2025-01-21),
Topaz (Apache-2.0, Go, 1.4k★, local + decision logs), OpenBao (MPL-2.0, Go, 6.9k★, leases),
libmacaroons (BSD-3-Clause, C, 513★), Tenuo (Apache-2.0, Rust, 77★, v0.2, optional cloud),
Tahoe-LAFS capability model (architecture.rst), Archivematica (AGPL-3.0, Python, 510★),
ArchivesSpace (ECL-2.0, Ruby, 433★), PM4Py (AGPL-3.0, Python, 994★), Netflix/repokid (Apache-2.0,
Python, 1.1k★), MonPoly fork `remolueoend/monpoly` (LGPL-2.1, OCaml; upstream = Bitbucket
`jshs/monpoly`), `dckc/awesome-ocap` (the source for the ocap survey), `w3c/dpv`.

Confirmed from vendor/standards documentation rather than a repo fetch: FHIR `Consent`,
`Permission`, `AuditEvent.purposeOfUse` (hl7.org — the R5/R6 `Permission` page itself 403'd me,
the Consent and AuditEvent pages and the Data Access Policies IG did not); PREMIS
`termOfGrant`/`termOfRestriction` (Archivematica user manual + Rockefeller Archive Center
guidelines); ArchivesSpace restriction begin/end fields (institutional practice manuals, JHU and
U. Hawai'i, plus the ArchivesSpace rights-management specification PDF); Teleport `--reason` /
`session_tracker` / moderated sessions (goteleport.com docs); GA4GH Passport/Visa expiry
requirements (ga4gh-duri spec page); Solid Access Grants `purpose`/`expirationDate`/future-VC
exclusion (Inrupt docs); Fuchsia Zircon rights reduction (`zx_handle_duplicate`, fuchsia.dev);
hotel-lock validity intervals (USPTO patents US5397884, US11200763, plus vendor explainers).

**UNVERIFIED / handle with care:**
- **Fraunhofer MYDATA / IND²UCE licensing.** Product pages reference a Fraunhofer GitLab and Maven
  Central artifacts, but I could not confirm an open-source licence. Assume proprietary.
- **`ocaps` (Scala) repository state** — described in awesome-ocap as v0.1.0 (2018-06) with
  `Revoker`/`Revocable` and a `PermeableMembrane` pattern; I did not fetch the repo. Treat the
  *pattern* as the finding, not the library.
- **MonPoly upstream** Bitbucket page did not render; all metadata above comes from the fork.
- **US8745085B2** — a granted patent titled "System for explanation-based auditing of medical
  records data" exists (Google Patents). I did **not** read its claims. See §2.5.
- **ACRL/RBMS–SAA Guidelines on Access to Research Materials** (2020) exist at ala.org and
  www2.archivists.org; both 403'd. I have *not* verified their language about finite restriction
  periods, so nothing in this report rests on it. Worth one fetch later — a normative professional
  statement that restrictions must be time-limited and applied equally would be a useful citation
  for §7.1.
- **Sandstorm's sharing/audit model** — the project is confirmed (self-hosted, capability-based,
  now at sandstorm.org) but every page I tried for its sharing-graph and revocation documentation
  403'd. Kenton Varda's essay on delegation is the thing to fetch; I could not.
- Web search budget for this session was exhausted mid-scout (200/200), so late-stage discovery
  ran through direct fetches only. Unexplored leads I would take next: DCR Graphs / Declare
  (declarative process models as the knock's declared model), IHE BPPC and consent-directive
  audit in health information exchanges, open-source visitor-management systems (I found none I
  could confirm — deliberately not named), and archival reading-room request software (Aeon is
  proprietary; I did not verify an open-source equivalent).
