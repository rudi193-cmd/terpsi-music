# Terpsi Music — Full Application Architecture

**Status:** strawman for argument, not a decision record.
**Scope:** the complete system, so that any single first module can be built without retrofitting.

> **Revision note.** Parts of this document were written before reading `safe-app-store`'s `apps/marching-arts`, which already implements the authorization, consent, and egress-purity story sketched here — in several places more strictly than proposed. Sections 5, 6, and 7 now describe what exists and confine themselves to what does not. Statements about `marching-arts` are drawn from the merged pull request descriptions (#112–#128), not from reading its source; where this document and that code disagree, the code is right.

---

## 1. The central tension

The system must serve six populations with incompatible network positions:

| Population | Where they are | What they need | Trust |
|---|---|---|---|
| Students | On-site, school-managed or personal devices, minors | Thin slice: schedule, assignments, their own status | Low |
| Staff / techs | On-site, some off-site planning | Broad operational access to one ensemble | Medium |
| Director | Everywhere, all hours | Everything for their program | High |
| Parents / guardians | Anywhere, any device, hundreds of households, wide tech literacy | Their student only: schedule, money, forms, comms | Low, but high volume |
| Clinicians / judges | On-site, transient, outsiders | One ensemble, one date, one rubric | Guest |
| "Corporate" (circuit, district, association) | Remote, institutional | Aggregates, never individuals | External |

The requirement is that the organization's data stays local and private. Students, staff, and director can be served entirely on the local network. **Parents cannot.** They are the population that forces a reachable endpoint, and they are simultaneously the largest, least technical, and most attractive to attack — a directory of minors, their schedules, their locations, and their guardians' payment relationships.

So the question is not "how do we avoid a server," because parents require one. The question is:

> **How little can the server be permitted to know, and how narrow can its interface be, such that its full compromise is survivable?**

Everything below follows from answering that with "nothing" and "very."

---

## 2. Trust model

Three zones, with the boundary drawn deliberately at the hub rather than at the client.

```
┌─────────────────────────────────────────────────┐
│  ZONE A — THE HUB (trusted, on-prem)            │
│  Plaintext lives here and only here.            │
│  System of record. Search, reporting, joins.    │
│  Physical + network control by the org.         │
└───────────────┬─────────────────────────────────┘
                │  everything crossing this line is
                │  sealed (§5) and gated (§6)
┌───────────────┴─────────────────────────────────┐
│  ZONE B — THE DROP (untrusted relay)            │
│  Opaque blobs, addressed to mailbox IDs.        │
│  No queries. No business logic. No plaintext.   │
│  Assume it is hostile.                          │
└───────────────┬─────────────────────────────────┘
                │
┌───────────────┴─────────────────────────────────┐
│  ZONE C — EDGE DEVICES (semi-trusted, scoped)   │
│  Parent phones, judge tablets, student devices. │
│  Hold an encrypted replica of their slice only. │
│  Assume individual devices will be lost/stolen. │
└─────────────────────────────────────────────────┘
```

**Why the boundary is at the hub, not the client.** Full end-to-end encryption to every client sounds stronger and is, in practice, crippling: you cannot sort a roster, run an eligibility report, reconcile fees, or search the music library over data the server can't read. Searchable-encryption schemes that promise otherwise leak more than they admit and will not survive contact with a director asking "who still owes for the trip."

The honest and buildable posture: **the hub is trusted and holds plaintext; nothing else ever does.** The org already trusts the hub — it's their box, in their building, under their lock. Encrypt at the boundary, not at the record-in-place, and you keep a fully functional application while making every path out of the building opaque.

Zone A's plaintext is protected by physical control, full-disk encryption with a TPM-sealed key, and the fact that it has no inbound route from the internet.

---

## 3. Topology

### The hub
A single on-premise node (mini-PC in the band room, or a district-provided VM) running the whole application: API, database, object store, local model runtime, and the egress broker. Sized for hundreds of families and tens of gigabytes of media — this is a small workload; a modest box handles a large program.

**Zero inbound ports.** No port forwards, no DMZ entry, no "just open 443 for the app." The hub makes outbound connections only. Firewall rules for the hub are egress-only and destination-restricted (§6).

### The drop
A minimal relay on commodity infrastructure. Its entire job:

- Authenticate a connection as belonging to a mailbox.
- Accept an opaque, size-capped, rate-limited blob addressed to a mailbox ID.
- Hold it until the other side collects it.
- Delete it.

It has no schema of the domain, no user table beyond opaque mailbox identifiers and their public keys, no search, no admin UI, no ability to enumerate one mailbox from another's session. It should be small enough to read in an afternoon and boring enough to never need a feature.

The hub holds a persistent outbound connection (WebSocket or QUIC) to the drop, collecting requests and depositing responses. Parents' devices connect to the drop the same way. **Neither side ever accepts an inbound connection.**

### Edge devices
An installable PWA holding a local encrypted replica of exactly the slice that device is entitled to. Reads are local and instant; writes queue and flush when connectivity allows.

This is not only a privacy decision. Competition sites, stadium parking lots, and buses have no usable signal, and that is precisely when a director needs the roster and attendance and a parent needs the schedule. **Local-first is an operational requirement that happens to also be the strongest privacy posture.**

---

## 4. Access paths, per persona

Different populations get different transports. Do not build one door.

**Students, staff, on-site director → direct.**
School network to hub, no relay involved. Fastest path, no external dependency, nothing leaves the building. Students are on a captive slice: their schedule, their assignments, their own inventory items, announcements addressed to them. Explicitly no roster browsing, no contact directory, no other students' data — a student-facing directory of minors is a liability with no compensating benefit.

**Off-site staff and director → mesh VPN.**
Small N, technically capable, org-issued or org-enrolled devices. WireGuard via Tailscale, or Headscale if the coordination plane must also be self-hosted. ACLs restrict the tailnet to the app port. This population can absorb a VPN client; parents cannot.

**Parents → the drop.** See §4.1, the hard case.

**Clinicians and judges → ephemeral scoped grants.**
On-site, event-bound. Either a kiosk device the org owns and wipes, or their own device on a guest SSID reaching the hub directly. The grant is a time-boxed relationship edge (`judge_at :: Event_X`, valid for the event window plus a commentary grace period) that expires on its own without anyone remembering to revoke it. Their scores and timecoded commentary are written locally; transmission to a circuit is a deliberate, reviewed export (§6), not a live integration.

**Corporate / circuit / district → never connects.**
No accounts on this system. They receive signed, minimized, aggregated exports pushed through the egress gate with human approval. If they need individual-level data, that is a disclosure decision a human makes and the log records — not a query they run.

### 4.1 The parent problem

Ranked options, with what each actually costs:

| Option | Network posture | Parent UX | Verdict |
|---|---|---|---|
| **(a)** Public web app via outbound tunnel (Cloudflare/Tailscale Funnel) | No inbound holes, but a public, queryable endpoint exists | Best — just a URL | Pragmatic v1; the endpoint is a real attack surface (credential stuffing, DoS, any 0-day in your stack) |
| **(b)** Mailbox relay + PWA replica | No inbound holes, no public query surface, relay sees only ciphertext | Good after install; requires enrollment | **Recommended target** |
| **(c)** Push-only encrypted digests + one-way intake | Minimal surface | Poor for anything interactive — payments, capacity-limited signups, real-time changes | Good fallback channel, bad primary |
| **(d)** VPN for every family | Strongest | Unworkable at 200 households with shared and borrowed devices | Rejected |

**Recommendation: build (b), ship (a) first if you must — but put the envelope and data classification in from day one** so that moving from (a) to (b) is a transport change, not a data migration. That single sequencing decision is the difference between a weekend and a rewrite.

Under (b), compromise of the drop yields: which mailboxes talked, when, and roughly how much. It does not yield names, students, schedules, medical notes, addresses, or balances. If the metadata itself matters — a mailbox suddenly going quiet, or a burst of traffic before a competition — pad blobs to size buckets and flush on a fixed schedule rather than on demand.

**Enrollment without a help desk.** Passkeys, not passwords and not VPN profiles. The director issues an invite (QR at a parent meeting, or a code in an existing communication channel); the parent registers a device-bound passkey. This is phishing-resistant, non-shareable, survives the parent who reuses one password everywhere, and — critically — is a workflow a non-technical guardian completes in under a minute. Multiple guardians per student each get their own credential; households split and custody arrangements change, so guardianship must be modeled as a set of independently revocable edges, never as one shared family login.

**Honest caveat.** A browser-delivered decryptor (the fallback for parents who won't install anything) means the code doing the decryption is served by the thing you don't trust. That is a real weakening. Keep it for low-sensitivity content only — the public performance schedule, a general announcement — and require the installed client for anything protected.

---

## 5. Envelope security

### Key hierarchy

```
Org Root Key            — TPM/HSM-sealed on the hub, never exported
  └─ Group Keys (KEK)   — X25519 keypair per access circle
       └─ Record DEKs   — AES-256-GCM, one per record/blob
            └─ wrapped per entitled circle via HPKE
```

Circles are relationships, not roles: `Family:1234`, `Staff:Ensemble7`, `Directors:Org1`, `Judges:Event42`. A record's DEK is wrapped once per circle entitled to it and stored beside the ciphertext.

### What is sealed, and where

| Data | In Zone A (hub) | Crossing to B/C |
|---|---|---|
| Student records, medical, contacts | Plaintext (queryable) | Sealed per family circle |
| Fees, balances, payments | Plaintext | Sealed per family circle |
| Adjudication scores + commentary | Plaintext | Sealed per event circle |
| Media (recordings, photos of minors) | Encrypted at rest, key in hub | Sealed; never leaves without §6 approval |
| Schedule, public announcements | Plaintext | Sealed, low sensitivity |
| Backups | — | Always sealed, separate escrowed key |

### Rotation, revocation, and the thing everyone gets wrong

Removing a member from a circle rotates the circle key going forward. It does **not** retroactively protect records that member could already read — they may have copies. Decide the policy explicitly and write it down:

- **Forward-only revocation** (rotate, don't re-encrypt history): cheap, honest, correct for most cases — a graduated senior's parent legitimately saw last season's data.
- **Full re-encryption of history**: expensive, and only meaningfully protects against a member who *hadn't* yet synced. Reserve for genuine incidents — a custody order, a terminated staff member.

Devices are revoked independently of people: a lost phone's key is burned without disturbing the guardian's other devices.

### Erasure inside a hash chain — solved, and harder than stated above

The paragraphs above treat erasure as a key-management policy question. It is not, and `marching-arts` (#115) hit the real version: a member's consent transitions are **links in a hash chain the whole corps depends on**, so honouring an erasure request either breaks consent verification for everybody or cannot be done at all. Neither is an answer you can give a guardian.

The resolution is to partition the chain at rest, one per subject (`consent/<subject_hash>`), so one member's history is deletable without touching anyone else's. Every consent operation already names a subject, so the scoped view is the whole view for that call, and an **unscoped read or write fails closed** rather than silently falling back to a global chain.

Two consequences worth carrying into anything else that chains:

- **Partitioning breaks rules that match chain names exactly.** Migration 003's guardian trigger matched `chain = 'consent'`; the moment the name gained a suffix the rule stopped firing and a minor could self-consent with nothing raised. The fix matches both the partitions and the bare name — the bare one still matters, because a writer reaching past the module straight to SQL could otherwise insert under the old name and dodge the rule entirely.
- **Emptied is not absent** (#121). A chain whose rows were deleted must not read as one that never existed, or the strongest attack is also the simplest. The head anchor carries a `count` as well as a hash, and a surviving anchor beside missing rows reads as *tampered*, not *absent* — including on the write path, where a guard written as `if existing and not verify(...)` silently skips on an empty list.

Any new chained artifact in this system — the disclosure log, the egress log of §6, adjudication commentary — inherits all three requirements: per-subject partitioning, fail-closed on unscoped access, and an anchor that distinguishes emptied from never-written.

### Escrow — the failure mode that ends the program

Encrypted student records with lost keys are destroyed student records. The root key must be recoverable without any single person: split it (Shamir, 2-of-3 or 3-of-5) across the director, a district/board administrator, and a sealed offline share. Test the reconstruction annually, on the calendar, as a drill. **An untested restore is not a backup, and an untested key recovery is not escrow.**

---

## 6. Egress gates

The hub's application containers have **no route to the internet**. The only reachable external destination is the local broker. This is enforced at the network namespace, not by asking the code nicely.

### Two enforcement points, and the inner one is stronger

`marching-arts` does not gate egress. It makes egress **inexpressible**: stdlib-only and import-pure, with an AST walk proving no module can reach the network and a check that importing the core pulls in no third-party package (#112). There is no destination to allow or deny because there is no client to call one.

That is the stronger position and it should be preserved wherever it can be. The network-namespace broker below is the *outer* ring — necessary for the parts of the system that genuinely must talk to the world (payment tokenization, the drop, circuit submissions, OS updates), and for any component composed in from elsewhere that has its own opinions about calling home.

The relationship between them:

| Ring | Mechanism | Applies to |
|---|---|---|
| Inner | Import purity, AST-proven, tested | The app core. Cannot express egress at all. |
| Outer | Network-namespace broker, allowlist | Host processes, sync, exports, third-party components |

A component that fails the inner test is not thereby acceptable at the outer ring — it is a component that needs a reason.

### Policy model

Every outbound call at the outer ring is a triple: **destination × data class × purpose.** No triple, no traffic.

### Classification, and how it meets the L-ladder

`marching-arts` already carries a **sensitivity ladder** that is load-bearing in the resolver: at L3 and above the payload is `NULL` in the SELECT list and only a derived instruction is served, and **L5 is never served to anyone under any grant** (#112). That ladder answers *how much of this may ever be rendered*, and it is authoritative.

The classes below answer a different question — *what kind of data is this, and what law follows it* — and exist to drive egress policy and retention, not serving decisions. **They are attributes on a field, mapped to an L-level; they are not a parallel ladder.** Do not introduce a second ranking that can disagree with the first.

- `PUBLIC` — performance dates, venue, ensemble name
- `INTERNAL` — non-identifying operational data
- `PII_MINOR` — anything identifying a student
- `PII_GUARDIAN` — contacts, addresses, relationships
- `HEALTH` — allergies, medications, conditions, emergency instructions
- `FINANCIAL` — balances, payment references
- `MEDIA_MINOR` — photos and recordings containing identifiable students
- `DERIVED_ANON` — aggregates that survive a re-identification check

Tag at schema-definition time. Retrofitting classification across an existing schema is miserable, which is why it belongs in the first module — and why the mapping from these classes onto the existing L-levels should be written down once, in the schema, rather than inferred per feature.

### Enforcement tiers

1. **Allowed** — pre-approved, logged. Payment tokenization, the drop, OS updates from pinned mirrors.
2. **Approval-required** — queued for the director, with a human-readable rendering of exactly what is about to leave and to whom. Circuit score submissions, district reports, anything `PII_*` crossing to a named external party.
3. **Denied by default** — everything else. Including, loudly, any destination that appeared without being added deliberately.

Plus: outbound payload scanning for identifier patterns before release (catches accidents, not adversaries), an append-only hash-chained log, and a **kill switch** the director can hit to freeze all egress while the system continues to work locally. During a season, "works locally with no internet" is not a degraded mode — it is Tuesday.

### The compliance dividend

FERPA §99.32 requires maintaining a record of disclosures of education records. **The egress log is that record**, generated as a byproduct rather than assembled under pressure during an audit. Design the log entries to be human-readable from the start — who, what, to whom, when, under what authority — and one regulatory obligation is satisfied by infrastructure you needed anyway.

### Agents run behind the same gate

Given this repo's MCP wiring: an agent with tool access and a network route is an exfiltration channel wearing a helpful hat, and prompt injection via any ingested content turns it into a live one. So:

- Anything touching `PII_*`, `HEALTH`, or `MEDIA_MINOR` is served by a **local** model inside Zone A. No exceptions, no "just this once for the summary." This explicitly includes commentary transcription (§8.2), which is where the pressure to make an exception will actually come from.
- External model APIs are a destination like any other: allowlisted for `PUBLIC` / `DERIVED_ANON` only, gated, logged.
- Agent tool-calls are constrained by the same authorization tuples as the human they act for — an agent cannot read what its principal cannot read.

---

## 7. Authorization

Roles alone will not express this. The defining requirement is **outsiders holding narrow, time-boxed access into someone else's program**, which is a relationship problem, not a role problem.

This is the section most superseded by what exists. `marching-arts` P1/P2 is the resolver, and it is stricter than what follows.

### What the resolver already guarantees

- **One predicate: `(allow₁ OR allow₂ OR …) AND NOT (deny₁ OR deny₂ OR …)`.** Denies negate the *union* of allows. Dropping the parentheses around the joined denies binds only the first term, the rest silently stop applying, nothing raises, and every row they were meant to withhold becomes visible. That specific failure has a regression test — which is the right response to a bug whose signature is *silence*.
- **Guarantees are mechanisms, not prose.** `source` is `NOT NULL` with a non-blank `CHECK`; a sealed grant without a signer is refused by `CHECK`; `COUNT(*)` runs under the predicate rather than beside it; **roles grant nothing on their own**.
- **Refusal is indistinguishable from absence.** A member who declined and a member who is absent produce the same rows, the same count, and the same subject list — tested as indistinguishability, because if they differed, declining would itself become the signal and every member who exercised the choice would be marked by exercising it. This is the same principle §18 of the capability map asks for around fee waivers, generalized: **the system must not leak the fact of a refusal.** Any new surface — a roster view, an export, an aggregate count — inherits that obligation.
- **Consent is never requested by its beneficiary**, enforced by trigger, with a registered guardian as the single carve-out.
- **Minor status is a birthdate, not a flag** — a flag stays true until somebody remembers to run the job that clears it. Expiry at majority therefore needs no job at all: it is a predicate evaluated inside the grant lookup on every read.
- **Conversion at majority is derived from the data, not from a bookmark** (#122). A "convert anyone who crossed since last open" window would be a second copy of the truth, and a birthdate corrected two seasons late puts majority in the past, so every window query answers *nobody* — silently and permanently.
- **The principal is authenticated at the read, not at the door** (#127). A `Principal` carries an HMAC proof over its identity, roles, and expiry, verified in `Store.predicate` — the one method every read already funnels through, so a fourth read added later inherits the gate. `Principal` stays freely constructible on purpose: a private constructor would move the check back to the door, where a caller who skips the door skips the check.

### What this document still adds

The guest-access shape, which is where the personas outside the program live. Expressed as relationship edges with expiry:

```
guardian_of      : Person:Ann      → Student:Ben
staff_of         : Person:Chris    → Ensemble:Drumline      [season-bounded]
director_of      : Person:Dana     → Program:Marching
judge_at         : Person:Erin     → Event:Regional_Oct12   [expires +36h]
clinician_for    : Person:Frank    → Session:Brass_Sep03    [expires +24h]
```

Properties worth insisting on: every grant carries an expiry (guest grants die on their own); permissions derive from edges rather than being stamped on people; the family circle is a set of individual guardian edges, so one guardian's revocation never touches another's; and every access decision is answerable after the fact — "who could see Ben's medical form on October 12, and why."

Following the existing design, each of these should be a **predicate over dated facts** rather than a row somebody remembers to delete — the same reason majority expiry needs no job.

### 7.1 The gap: guardianship that ends by order rather than by arithmetic

Majority expiry works because the end date is computable from a birthdate the record already holds. **Court-ordered contact restrictions have the same shape and no such arithmetic.** They arrive mid-season, from outside, against one guardian and not the other.

If a terminated guardianship is a `DELETE` while majority is a predicate, the two behave differently in exactly the ways that matter:

- A deleted edge leaves no dated record, so "who could see this on October 12, and why" becomes unanswerable for the one case where a court may actually ask.
- A restriction that must take effect at a future date has nowhere to live until it does.
- Reinstatement — orders get modified — has to reconstruct what deletion discarded.

The recommendation is that guardianship carry `effective_from` / `effective_until` and terminate by **setting a date, never by removing the edge**, so that revocation-by-order and revocation-by-majority are the same mechanism with different sources. Erasure of a guardianship record remains available separately, under §5's per-subject partitioning, as a distinct act with its own authority.

This is the one place in this domain where the failure is a safety failure rather than a bug, and it is worth having the mechanism before the case arrives — because when it arrives it will arrive urgently.

---

## 8. Domain model

Sketch, not schema.

- **Org** → **Program** → **Ensemble** → **Season** → **Event**
- **Person** (+ `Student` / `Guardian` / `Staff` / `Guest` facets — one human, many roles, never duplicated rows)
- **Enrollment**, **Guardianship**, **Eligibility**
- **Inventory:** `Instrument`, `Uniform`, `LibraryItem` (score/part), with `Assignment` and condition history — the "who has the school tuba" question is perennial and currently lives in a spreadsheet
- **Money:** `FeeSchedule`, `Charge`, `Payment`, `FundraisingCredit`, `TripAccount`
- **Ops:** `Rehearsal`, `Attendance`, `Absence`, `Form` / `Consent`, `MedicalNote`, `Travel`
- **Performance:** `Repertoire`, `Chart` / `Drill`, `Recording` — plus the adjudication core below
- **Comms:** `Announcement`, `Thread`, `Acknowledgement`

Two constraints that shape everything: **payment card data never enters the system** — hosted fields, tokens only, staying in PCI SAQ-A territory; and **`MediaAsset` carries consent state as a first-class field**, because a photo of a minor whose family declined the release is a problem you cannot solve after publication.

### 8.1 Commentary is the primitive

The oldest form of adjudication feedback in this domain is a judge talking into a recorder for the length of a performance — the stack of microcassettes every symphonic director went home with. That artifact was *already* timecoded commentary, perfectly synchronized by construction, because the judge was speaking while it happened. What made it useless a week later was not the format. It was that the commentary was **linear, unaddressable, and detached from the thing it described**: one copy, unsearchable, impossible to hand a section only their own remarks, and now sitting in a drawer with no machine left to play it.

So the primitive is not the score sheet. It is:

```
Commentary
  author        → Person (judge | clinician | staff)
  performance   → Recording
  anchor        → Score position (measure/rehearsal mark), NOT wall-clock alone
  span          → start/end
  body          → audio + transcript + speaker
  addresses     → [Ensemble | Section | Part | Individual]
  dimension     → Caption | Rubric criterion | (none — free commentary)
```

**Anchor to score position, not just time.** "At 4:32" means nothing to a musician; "measure 112, at the tempo change" is the addressable unit. Get there by aligning audio to the score where one exists, or by giving the judge a tap-to-mark control and letting them anchor as they speak. This is the hard part and the whole value — unanchored commentary is just a tape with extra steps.

**Rubrics, captions, ratings, and scores are projections over commentary**, not parallel structures beside it. Caption scoring is structured judgment; the festival tape is unstructured judgment; both are assessment attached to a moment in a performance. Modeled this way, a symphonic festival is a *configuration* — a different rubric, ratings instead of caption numbers, more talking and fewer digits — rather than a second application. Marching, indoor, and concert festival all fall out of one model.

What this unlocks, none of which the tape could do: deliver each section only the remarks touching their parts; scrub to a comment and hear the ensemble at that instant; diff the same passage across judges who disagreed; and — the genuinely new one — query every comment about brass balance across a full season to see whether the thing you have been fixing since September is actually moving.

### 8.2 Commentary processing runs locally, without exception

A recording of a judge's voice over a performance by identifiable minors is `MEDIA_MINOR` twice over. **Alignment, diarization, and transcription all run in Zone A on the hub.** Sending this audio to a hosted transcription API would make the entire privacy posture theater — it is the single most sensitive artifact the system produces and the most tempting one to hand to a convenient cloud endpoint. Local speech models are now good enough that this is a real option rather than a compromise.

Pipeline, entirely inside the trust boundary: ingest judge audio and performance audio → align → diarize → transcribe → anchor to score position → index. Transcripts inherit the classification of their source audio; nothing about "it's only text now" declassifies it.

---

## 9. Phasing

The ordering principle: build the things that are expensive to retrofit first, regardless of which module ships first.

**Foundation — hard to add later, so add it now**
1. Person / relationship graph with time-boxed edges (§7) — **built** (P1/P2), less the dated-guardianship gap in §7.1
2. Data classification on every field (§6) — the L-ladder is **built**; the class-to-L mapping is not
3. Envelope + key hierarchy, even while everything is still on one LAN (§5) — chain integrity and per-subject erasure are **built**; at-rest sealing across the Zone A boundary is not
4. Egress purity in the core (§6, inner ring) — **built**, AST-proven. The outer broker is not, and is only needed once something must legitimately talk to the world
5. Append-only audit log — the hash-chained disclosure log is **built**, with the count-anchor truncation defence

**Then, in whatever order the program's pain dictates**
6. First vertical module — `field-acoustics` is the first real capability
7. Parent PWA + the drop
8. Money, inventory, forms, calendar/attendance
9. Adjudication: commentary capture + anchoring, guest grants, local transcription pipeline
10. Aggregate exports for corporate
11. Local agent assistance behind the gate

**Deferred deliberately:** multi-org hosting, circuit-wide federation, and any live integration with an external platform. Each converts a private local system into a networked one and deserves its own decision.

---

## 10. Compliance map

| Regime | Applies to | Where it lands |
|---|---|---|
| FERPA | Education records | Disclosure log = egress log (§6); guardian access rights; retention/purge |
| COPPA | Students under 13 | School-consent pathway; no third-party trackers, ever |
| State student-privacy laws (NY Ed Law 2-d, CA SOPIPA, etc.) | Varies | Data inventory + no-sale/no-ads posture; parent-facing privacy notice |
| PCI-DSS | Payments | Tokenized only; stay SAQ-A by never touching card data |
| Photo/video release | Media of minors | Consent state on `MediaAsset`, enforced at egress |
| Records retention | All | Season-boundary purge job; graduated-student disposition policy |

Not legal advice — the state-law column in particular varies enough that the district's counsel should see the data inventory before parents see the app.

---

## 11. Operations

- **Backups:** 3-2-1, always sealed, one copy off-site, **restores tested on a schedule.** The hub is a single point of failure holding a season's work.
- **Availability:** a cold spare with a nightly restore is usually enough; a program can run a day on paper but not a week. Match the recovery target to what the director can actually tolerate during championship week.
- **Offline:** clients degrade to local replicas. Attendance at a stadium with no signal is the design case, not the edge case.
- **Upgrades:** signed artifacts pulled through the gate, staged, roll-back-able. No vendor tunnel into the box.
- **Season lifecycle:** graduation, roster turnover, staff departure, and purge are recurring scheduled events, not one-off scripts written in a panic each June.
- **Loss of the director:** the person who holds the most access is also the one likeliest to change jobs. Escrow and succession are operational requirements.

---

## 12. Decisions to lock now

1. **Trust boundary at the hub, not the client** — enables a real application; everything else follows.
2. **The relay can't read anything** — makes its compromise survivable and makes the transport swappable.
3. **Relationships over roles, every grant expires** — the only model that handles judges and clinicians cleanly.
4. **Classification at schema-definition time** — the one thing that is genuinely miserable to retrofit.
5. **Egress inexpressible in the core, gated at the perimeter** — import purity first, network policy only where the world must genuinely be reached.
6. **Commentary is the adjudication primitive; captions and ratings are projections over it** (§8.1) — the difference between supporting symphonic festival as a configuration and rebuilding for it later.
7. **Revocation is a dated predicate, never a deletion** (§7.1) — majority already works this way; guardianship termination by court order must work the same way.

## 13. Open questions

- **The auth model is scoped to a single process.** #127 holds the signing key in memory with nothing at rest, so tokens die with the process — correct for an app with no server, and stated as the design. The hub topology in §3 is a long-running multi-user process where sessions must survive a restart. Either the app stays single-process and the hub is a separate thing that fronts it, or authentication needs a second mode. Worth resolving before the hub exists, not after.
- **Does `rationale` (#125) generalize into the disclosure story?** It ships the reasoning beside the data, gated by a human seal rather than a predicate, with `draft | internal | shipped` states. FERPA §99.32 wants a disclosure record and §6 assumes the egress log supplies it — but "why were you refused" is a `rationale` question, not an egress-log question. The two may want to meet.
- The current build targets caption scoring. Does its model treat captions as projections over anchored commentary (§8.1), or as the base structure? If the latter, that is the one thing worth revisiting early — festival ratings and clinician feedback both fall out for free under the former.
- Score-position anchoring: align audio against a stored score, or judge-driven tap-to-mark, or both? Affects how much of the music library must be machine-readable.
- **Can `field-acoustics` and commentary share coordinates?** A judge's remark is anchored to a moment and a seat; the acoustic model predicts what arrived at that seat. Pairing them gives a claim no drill designer can currently make — and gives the model's `ASSUMED` rear hemisphere a source of validation data that would otherwise have to be measured in the field.
- Is "corporate" the circuit/association, the district, or a vendor? Changes what aggregates mean and who signs off on them.
- Does the org control its own hardware, or is the hub a district-managed VM? Changes the physical-trust assumption underneath Zone A.
- Are agents an implementation detail of the build, or a user-facing feature (a director querying their program in plain language)? The latter needs a local model of real capability inside Zone A.
- Single program, or does this eventually serve several under one hub? Deferred above, but it constrains the tenancy model if it's ever a yes.
