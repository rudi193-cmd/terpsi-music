# Terpsi Music — Full Application Architecture

**Status:** strawman for argument, not a decision record.
**Scope:** the complete system, so that any single first module can be built without retrofitting.

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

### Escrow — the failure mode that ends the program

Encrypted student records with lost keys are destroyed student records. The root key must be recoverable without any single person: split it (Shamir, 2-of-3 or 3-of-5) across the director, a district/board administrator, and a sealed offline share. Test the reconstruction annually, on the calendar, as a drill. **An untested restore is not a backup, and an untested key recovery is not escrow.**

---

## 6. Egress gates

The hub's application containers have **no route to the internet**. The only reachable external destination is the local broker. This is enforced at the network namespace, not by asking the code nicely.

### Policy model

Every outbound call is a triple: **destination × data class × purpose.** No triple, no traffic.

Data classes, tagged on every field at schema definition time — retrofitting classification across an existing schema is miserable, which is why it belongs in the first module:

- `PUBLIC` — performance dates, venue, ensemble name
- `INTERNAL` — non-identifying operational data
- `PII_MINOR` — anything identifying a student
- `PII_GUARDIAN` — contacts, addresses, relationships
- `HEALTH` — allergies, medications, conditions, emergency instructions
- `FINANCIAL` — balances, payment references
- `MEDIA_MINOR` — photos and recordings containing identifiable students
- `DERIVED_ANON` — aggregates that survive a re-identification check

### Enforcement tiers

1. **Allowed** — pre-approved, logged. Payment tokenization, the drop, OS updates from pinned mirrors.
2. **Approval-required** — queued for the director, with a human-readable rendering of exactly what is about to leave and to whom. Circuit score submissions, district reports, anything `PII_*` crossing to a named external party.
3. **Denied by default** — everything else. Including, loudly, any destination that appeared without being added deliberately.

Plus: outbound payload scanning for identifier patterns before release (catches accidents, not adversaries), an append-only hash-chained log, and a **kill switch** the director can hit to freeze all egress while the system continues to work locally. During a season, "works locally with no internet" is not a degraded mode — it is Tuesday.

### The compliance dividend

FERPA §99.32 requires maintaining a record of disclosures of education records. **The egress log is that record**, generated as a byproduct rather than assembled under pressure during an audit. Design the log entries to be human-readable from the start — who, what, to whom, when, under what authority — and one regulatory obligation is satisfied by infrastructure you needed anyway.

### Agents run behind the same gate

Given this repo's MCP wiring: an agent with tool access and a network route is an exfiltration channel wearing a helpful hat, and prompt injection via any ingested content turns it into a live one. So:

- Anything touching `PII_*`, `HEALTH`, or `MEDIA_MINOR` is served by a **local** model inside Zone A. No exceptions, no "just this once for the summary."
- External model APIs are a destination like any other: allowlisted for `PUBLIC` / `DERIVED_ANON` only, gated, logged.
- Agent tool-calls are constrained by the same authorization tuples as the human they act for — an agent cannot read what its principal cannot read.

---

## 7. Authorization

Roles alone will not express this. The defining requirement is **outsiders holding narrow, time-boxed access into someone else's program**, which is a relationship problem, not a role problem.

Use relationship-based access control (Zanzibar-style — OpenFGA or SpiceDB, or a modest hand-rolled tuple store to keep dependencies thin):

```
guardian_of      : Person:Ann      → Student:Ben
staff_of         : Person:Chris    → Ensemble:Drumline      [season-bounded]
director_of      : Person:Dana     → Program:Marching
judge_at         : Person:Erin     → Event:Regional_Oct12   [expires +36h]
clinician_for    : Person:Frank    → Session:Brass_Sep03    [expires +24h]
```

Properties worth insisting on: every grant carries an expiry (guest grants die on their own); permissions derive from edges rather than being stamped on people; the family circle is a set of individual guardian edges, so one guardian's revocation never touches another's; and every access decision is answerable after the fact — "who could see Ben's medical form on October 12, and why."

---

## 8. Domain model

Sketch, not schema.

- **Org** → **Program** → **Ensemble** → **Season** → **Event**
- **Person** (+ `Student` / `Guardian` / `Staff` / `Guest` facets — one human, many roles, never duplicated rows)
- **Enrollment**, **Guardianship**, **Eligibility**
- **Inventory:** `Instrument`, `Uniform`, `LibraryItem` (score/part), with `Assignment` and condition history — the "who has the school tuba" question is perennial and currently lives in a spreadsheet
- **Money:** `FeeSchedule`, `Charge`, `Payment`, `FundraisingCredit`, `TripAccount`
- **Ops:** `Rehearsal`, `Attendance`, `Absence`, `Form` / `Consent`, `MedicalNote`, `Travel`
- **Performance:** `Repertoire`, `Chart` / `Drill`, `Recording`, `Rubric`, `Caption`, `Score`, `Commentary` (timecoded)
- **Comms:** `Announcement`, `Thread`, `Acknowledgement`

Two constraints that shape everything: **payment card data never enters the system** — hosted fields, tokens only, staying in PCI SAQ-A territory; and **`MediaAsset` carries consent state as a first-class field**, because a photo of a minor whose family declined the release is a problem you cannot solve after publication.

---

## 9. Phasing

The ordering principle: build the things that are expensive to retrofit first, regardless of which module ships first.

**Foundation — hard to add later, so add it now**
1. Person / relationship graph with time-boxed edges (§7)
2. Data classification on every field (§6)
3. Envelope + key hierarchy, even while everything is still on one LAN (§5)
4. Egress broker as the only network path — trivial when there are two destinations, miserable when there are twenty
5. Append-only audit log

**Then, in whatever order the program's pain dictates**
6. First vertical module (yours — whichever it is, it plugs into 1–5)
7. Parent PWA + the drop
8. Money, inventory, forms, calendar/attendance
9. Adjudication + guest grants
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
5. **No direct internet route from application code** — enforced by the network, not by convention.

## 13. Open questions

- Which competitive context — caption-based circuit scoring vs. festival ratings? Changes the adjudication model materially.
- Is "corporate" the circuit/association, the district, or a vendor? Changes what aggregates mean and who signs off on them.
- Does the org control its own hardware, or is the hub a district-managed VM? Changes the physical-trust assumption underneath Zone A.
- Are agents an implementation detail of the build, or a user-facing feature (a director querying their program in plain language)? The latter needs a local model of real capability inside Zone A.
- Single program, or does this eventually serve several under one hub? Deferred above, but it constrains the tenancy model if it's ever a yes.
