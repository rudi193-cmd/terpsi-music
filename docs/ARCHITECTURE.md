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

**Parents → SMS for almost everything, the drop for the rest.** See §4.1 and §4.2.

**Clinicians and judges → ephemeral scoped grants.**
On-site, event-bound. Either a kiosk device the org owns and wipes, or their own device on a guest SSID reaching the hub directly. The grant is a time-boxed relationship edge (`judge_at :: Event_X`, valid for the event window plus a commentary grace period) that expires on its own without anyone remembering to revoke it. Their scores and timecoded commentary are written locally; transmission to a circuit is a deliberate, reviewed export (§6), not a live integration.

This is the persona the knock (§7.2) is for: a declared purpose on entry, reconciled on exit, announced loudly because the trust level is low. A grant says what a guest *may* do; the reconciliation says what they *did*.

**Corporate / circuit / district → never connects.**
No accounts on this system. They receive signed, minimized, aggregated exports pushed through the egress gate with human approval. If they need individual-level data, that is a disclosure decision a human makes and the log records — not a query they run.

### 4.1 The traffic split, and why SMS collapses the problem

This document treated "parents need access" as one requirement. It is three, and they have wildly different weights:

| Class | Share of interactions | What it is |
|---|---|---|
| **Notification** | ~80% | Rehearsal moved. Bus is thirty minutes out. Lightning hold. Call time is now 5:15. |
| **Acknowledgment** | ~15% | Got it. He'll be there. She's sick tonight. |
| **Transactional** | ~5% | Pay a fee, sign a form, view a balance, upload a physical. |

**SMS handles the first two completely** — no app, no enrollment, no passkey, no VPN, no browser, no account. It works on a flip phone and it works for the grandparent listed as an emergency contact. And it is *push*: the hub dials out to a gateway and nothing on the school network ever listens, so the zero-inbound posture is preserved without building anything.

That leaves the relay serving only the transactional 5% — occasional, low-volume, and for a population that tolerates more friction at four interactions a year than at four a day. **This is a different and much smaller engineering problem than the one §4.2 was solving**, and the ranked options there should be read in that light.

#### The rule: SMS carries signals, never records

SMS is plaintext at the carrier, retained by the SMSC, rendered on a lock screen, and synced into iCloud and Google backups and onto whatever laptop is paired. `PII_MINOR`, `HEALTH`, `FINANCIAL`, and disciplinary content cannot go on it. *"Ben's insulin authorization expires Friday"* is a disclosure — to a carrier, and to whoever is holding the phone.

So the security model here is not encryption, it is **minimization**, and that is a coherent position rather than a concession. The envelope thesis says *make the relay incapable of reading anything*; a carrier cannot be made incapable, so instead the payload is made not worth reading. "Call time is 5:15" leaks nothing in plaintext. Anything sensitive becomes a one-time link into the local surface, or is not sent.

#### The gateway is a trust decision, and the local one is available

A hosted SMS vendor would hold a roster of every guardian's phone number alongside every message body — a Zone-B-class trust decision smuggled in as a convenience, and the largest hole available in this posture. The sovereign alternative is real: a cellular modem on the hub, or a dedicated Android handset in the band room acting as a gateway. No third party, no message contents leaving the organization.

Its honest constraint is **throughput**. A person-to-person SIM sending three hundred messages in ninety seconds looks exactly like spam and will be filtered or blocked. That constraint, not cost, decides the design:

- Tier aggressively so a genuine all-call is a rare event, not a daily one
- Stagger sends rather than fanning out at once
- If one message class truly needs guaranteed mass delivery — emergency, and only emergency — that is the single justified case for an A2P route, with everything else staying local

#### SMS also fixes enrollment, but must not become the credential

§4.2's enrollment story assumed parents attend the meeting where the invite is handed out. Many do not. SMS *is* the enrollment channel: text a one-time link, they tap it, they bind a passkey, done — no help desk, no meeting, no QR code.

It must stop there. **SMS OTP is the weakest widely-deployed second factor** — SIM swap and SS7 interception are not theoretical — and this credential governs access to a minor's records. SMS delivers the enrollment link; the passkey holds the identity. It bootstraps authentication rather than being authentication.

#### Three things it drags in

- **The send list is an access-control surface.** A guardian under a contact restriction must not receive *"Ben will be at the away game in Dayton until 10pm"* — a live location disclosure about a minor, pushed to a device, unrecallable. The dated-guardianship predicate of §7.1 must gate **who is messaged**, not only what can be read. This is the sharpest argument in this document for building §7.1 early.
- **The audience is whoever holds the phone**, including the student, on a lock screen, with no authentication. Another reason content stays minimal.
- **Consent to be texted is separate from consent to the data.** A guardian may be fully entitled to a record and never have agreed to be messaged. Opt-in and `STOP` handling are their own state, and 10DLC registration applies if any A2P route is used.

#### What SMS does not solve

Payments, signatures, capacity-limited signups, balance history, anything involving a document. Those stay on the interactive surface — which has just gone from load-bearing for every family every day to occasional.

### 4.2 The transactional remainder

Ranked options for the 5% that SMS cannot carry:

| Option | Network posture | Parent UX | Verdict |
|---|---|---|---|
| **(a)** Public web app via outbound tunnel (Cloudflare/Tailscale Funnel) | No inbound holes, but a public, queryable endpoint exists | Best — just a URL | Pragmatic v1; the endpoint is a real attack surface (credential stuffing, DoS, any 0-day in your stack) |
| **(b)** Mailbox relay + PWA replica | No inbound holes, no public query surface, relay sees only ciphertext | Good after install; requires enrollment | **Recommended target** |
| **(c)** Push-only encrypted digests + one-way intake | Minimal surface | Poor for anything interactive — payments, capacity-limited signups, real-time changes | Good fallback channel, bad primary |
| **(d)** VPN for every family | Strongest | Unworkable at 200 households with shared and borrowed devices | Rejected |

**Recommendation: build (b), ship (a) first if you must — but put the envelope and data classification in from day one** so that moving from (a) to (b) is a transport change, not a data migration. That single sequencing decision is the difference between a weekend and a rewrite.

Under (b), compromise of the drop yields: which mailboxes talked, when, and roughly how much. It does not yield names, students, schedules, medical notes, addresses, or balances.

**The metadata matters more than that paragraph originally allowed, and this fleet has the precedent.** `corpus-lens` is built around a single observed fact: *a custody schedule was once reconstructed from keystroke timing alone — content redaction does not scrub the shape of a week.*

Apply that here and it is not hypothetical. A guardian mailbox that receives traffic on alternating weekends. Attendance check-ins that cluster Tuesday and Thursday. A notification stream that goes quiet for a fortnight each month. **Timing alone reconstructs a custody arrangement**, in a system that holds custody-sensitive records and is explicitly designed to protect them (§7.1). The content being sealed does not help.

So padding to size buckets and flushing on a fixed schedule is not an optional hardening for the paranoid — it is the control for the disclosure this design most needs to prevent. Same for SMS: a per-guardian send that fires on exactly the days one parent has the student is a disclosure to the carrier and to anyone reading a phone bill. Send to both guardians on the same cadence, or send on a schedule uncorrelated with the event.

`corpus-lens` also models the honest way to state this: its README documents what the wall does *not* hide — weekly cadence survives, and there is a test asserting that it does. A limit you have measured and disclosed is a different artifact from one you have not looked for.

**Enrollment without a help desk.** Passkeys, not passwords and not VPN profiles. The director issues an invite (QR at a parent meeting, or a code in an existing communication channel); the parent registers a device-bound passkey. This is phishing-resistant, non-shareable, survives the parent who reuses one password everywhere, and — critically — is a workflow a non-technical guardian completes in under a minute. Multiple guardians per student each get their own credential; households split and custody arrangements change, so guardianship must be modeled as a set of independently revocable edges, never as one shared family login.

**Honest caveat.** A browser-delivered decryptor (the fallback for parents who won't install anything) means the code doing the decryption is served by the thing you don't trust. That is a real weakening. Keep it for low-sensitivity content only — the public performance schedule, a general announcement — and require the installed client for anything protected.

### 4.3 What exists, and what the relay is not

**`willow-mcp` serve mode is a real remote-access path.** HTTP with OAuth 2.0 + PKCE against Google or Apple, then a separate, operator-confirmed **identity binding** mapping that identity to an `app_id` before any permission applies. `confirm-binding` is deliberately not an MCP tool — a remote caller must never confirm its own binding — and an authenticated-but-unbound caller is denied exactly like an unmanifested one. It also tracks `email_basis` (`asserted` / `first_auth_only` / `relay` / `unavailable`) rather than trusting an IdP email uniformly, and annotates `email_drift` instead of silently updating.

Two things follow for the parent problem. Google as IdP is *convenient* in a district on Google Workspace for Education and *wrong* everywhere else, so it cannot be the only enrollment path — which is what §4.1's passkey recommendation is for. And serve mode binds `127.0.0.1` by default; making it reachable by 200 households is precisely the exposure §4.1 exists to avoid, so it is the transport for the **staff** path of §4, not the parent one.

**Grove is not the drop.** The catalog describes Grove as *encrypted peer-to-peer* and Willow Grove as carrying *encrypted u2u direct messages*. The implementation's own README corrects this: u2u is **authenticated, not confidential** — `json.dumps(packet)` onto a plain TCP socket, with `cryptography` used only for Ed25519 signing. Origin and integrity are verified; the body is plaintext on the wire, readable by anyone on the LAN segment. Adding confidentiality is described as an open decision, not a shipped feature.

So the relay remains unbuilt, and reusing u2u for it would be a serious error. What u2u *does* supply is the harder half of a mailbox relay — signed identity, verified origin, per-contact consent flags defaulting to False so a newly admitted contact can deliver nothing until granted. A confidentiality layer over that is a smaller job than a relay from scratch.

> **Divergence to fix.** `catalog.json` still advertises encryption that the code does not implement, for two entries. Sibling repo `safe-app-grove`, named as Grove's canonical repository, does not resolve — consistent with the survey finding in #119 that two of four claimed canonical repos 404. Both are `FLEET_SEAMS`-class findings: the declaration and the enforcement disagree, and the declaration is the customer-facing one.

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

### What the vault already provides

`willow-data-vault` is the box, and it is Zone A under a different name — "the *named boundary*" that gate `store_scope`, kart bubblewrap, and consent were already protecting. It adds a lifecycle axis this document did not have:

| Layer | Lifecycle |
|---|---|
| Compute / agents — MCP server, Kart sandbox (§5.1) | ephemeral, replaceable |
| Apps — `SAFE/apps/<app_id>/` | replaceable payloads |
| **The vault** — schemas, KB, DBs, secrets, user files | **persistent, sovereign** |

Secrets are Fernet ciphertext in `vault.db`, meaningless without `vault.key` (mode `0600`, generated locally, never committed). The framing is exactly this document's thesis, arrived at independently: *copy the box's `vault.db` without the key and every secret is unreadable — which turns "agents can't carry it out" from a policy promise into a cryptographic one.* `willow-mcp` fails closed on a keyless vault, and `vault.db` + `vault.key` are written only as an atomic pair.

### 5.1 The sandbox is where anything expensive runs

`kartikeya` is the execution layer under the vault's compute row: a task queue plus a **bubblewrap-sandboxed worker** with an explicit mount, credential, and network policy. Three properties matter here.

**Network-isolated by default.** A task reaches the network only if its stored text carries `# allow_net` — and Kart treats that as a *request*, calling back to the host authorizer, which rechecks capability, consent, lease, signature, task hash, expiry, and a one-use nonce. Kart's own docs are careful to say that who may *write* that directive is the host's call, which is the same boundary willow-mcp names as its residual (§6).

**Credentials reach only network-enabled tasks**, so a purely local job cannot see a secret it has no use for.

**Resource caps are real** — a delegated cgroup parent where available, `prlimit`/`ulimit` inside the sandbox otherwise. That is not a nicety on a single-box hub: commentary transcription and acoustic simulation are the two genuinely expensive things this system will run, and neither may be permitted to starve attendance-taking on a competition morning. Cap them, and make the cap part of install acceptance rather than something discovered under load.

### The canonical store is read-only to the app; apps write sidecars

Two independent builds state this rule, which makes it a fleet convention rather than one app's preference. `law-gazelle`: *Nest SQLite (canonical private data) → Law Gazelle (reads only) → LLM/TUI*, with a separate `gazelle_state.db` taking sidecar writes, and explicitly **agent write path: sidecar only**. `nest-seed`: *the DB is canonical — apps read it, never mutate it*, with fleet promotion as a later, separate layer.

Adopt it here, because it buys three things this design wants and does not otherwise have:

- **An agent cannot corrupt the system of record**, regardless of what it is talked into. The strongest prompt-injection outcome against a read-only canonical store is a bad sidecar.
- **Restore is meaningful.** A canonical store that only a narrow, audited path writes is one whose backups are trustworthy; a store every feature mutates is one where a bad week is indistinguishable from a bad restore.
- **The disclosure question stays answerable.** Sidecars carry who-wrote-what-when without polluting the record they annotate.

For this domain the split falls out naturally: roster, guardianship, consent, health, and adjudication results are canonical; practice logs, triage state, drafts, annotations, and anything an agent produces are sidecar until a human promotes them.

### The fleet already has a rule that covers this data

`willow-compose` — the constellation's own queryable memory, 29,432 code pieces braided with the human and collaboration corpora — states what it deliberately excludes:

> The private layer. Family specifics, medical, legal, schedules, names — surfaced during the assembly, kept out of every durable artifact on purpose. The family-data apps themselves live sovereign and local, outside this corpus by design. **You protect the spec by refusing to expose it.**

**By that definition terpsi-music is a family-data app**: minors, medical forms, schedules, names, guardians. So the constraint is not a new one this document is proposing — it is an existing fleet policy that already names this class of application and puts it outside the shared corpus. Record it that way, and note the consequence: nothing from a program's canonical store is ever a candidate for corpus ingestion, promotion, or the knowledge base, however useful the aggregate would be.

That also settles a question §19 might otherwise have gotten wrong. A director's assistant may query the program's own store locally; it may not enrich the fleet corpus with what it learns there.

Two things that follow from the vault, and neither is covered yet:

- **This seals secrets, not records.** `vault.key` protects the Fernet secret store. A SOIL collection's `store.db` — where a roster, medical notes, and adjudication commentary would live — is not described as encrypted at rest. The per-record DEK hierarchy above is therefore still a proposal, not a restatement. Decide deliberately whether student records need more than filesystem permissions plus a `0700` box, because "the box is sovereign" and "the box is encrypted" are different claims and only the first is currently true.
- **There is no escrow.** See below; it is the largest remaining gap in this design.

### Escrow — the failure mode that ends the program, and the one thing nothing covers

`vault.key` is generated locally, lives only in the box, is `0600`, and is never committed. Every one of those properties is correct and together they mean **a single file loss destroys every secret in the box, irrecoverably, by design.**

For a personal sovereign box that is an acceptable trade: the owner bears their own risk. For an organization holding minors' education records it is not. The director who owns the box changes jobs, the box's drive fails in October, the person who knew where the key was is on leave. Encrypted student records with lost keys are destroyed student records, and a program cannot answer a FERPA inspection request with "the key was on the machine that died."

So this remains a genuine addition rather than a restatement: the box's key material must be recoverable **without any single person**. Split it (Shamir, 2-of-3 or 3-of-5) across the director, a district or board administrator, and a sealed offline share. Test the reconstruction annually, on the calendar, as a drill. **An untested restore is not a backup, and an untested key recovery is not escrow.**

Note that escrow is in tension with sovereignty and the tension is real, not sloppy: every share is a copy that can be compelled or stolen. The resolution is that shares are held by parties inside the institution that already holds the records, not by a vendor — recovery stays within the same trust boundary the data already sits in.

---

## 6. Egress gates

The hub's application containers have **no route to the internet**. The only reachable external destination is the local broker. This is enforced at the network namespace, not by asking the code nicely.

### Three rings, and the inner one is strongest

`marching-arts` does not gate egress. It makes egress **inexpressible**: stdlib-only and import-pure, with an AST walk proving no module can reach the network (#112). There is no destination to allow or deny because there is no client to call one. That check is not app-local — it is `safe_app_common.no_egress`, the fleet's canonical implementation, with `DEFAULT_FORBIDDEN` as a frozen set of egress-capable module roots.

The middle ring is the one this document originally missed. `safe-app-common` has apps declare a **core/seam partition**: the seams are the outward-facing files, they are named explicitly, and the direction is enforced — `assert_does_not_import(core, modules, {"web", "serve", "willow_bridge"})` means seam→core and never the reverse. A seam is still held to `assert_file_no_egress`.

UTETY shows what that buys, in a student-data app that is the closest existing analogue to this one. `knowledge.py` is the single place anything leaves the device, deliberately outside `core/`, and its send path takes only a concept-query string. **Student PII cannot be transmitted because it is not a parameter.** That is categorically stronger than gating a call that *could* carry PII: there is no argument to review, no policy to get right, and no way to pass the wrong thing by mistake.

| Ring | Mechanism | Applies to |
|---|---|---|
| Core | Import purity, AST-proven (`safe_app_common.no_egress`) | Data, schema, math. Cannot express egress at all. |
| Seam | Named, narrow, no egress-capable imports, typed so sensitive values are not passable | The one or two places something legitimately leaves |
| Perimeter | `willow-gate` — trust ladder, export gating, PGP ledger | Agents and tool calls |

A component that fails the core test is not thereby acceptable at the seam — it is a component that needs a reason.

### The perimeter is `willow-gate`, and it is not a network broker

This document proposed a destination-allowlisting network-namespace broker. That is not what exists, and what exists is aimed at the more relevant threat. `willow-gate` gates **agents**: symmetric 13-field check-in/check-out, identity bound by HMAC over the header rather than asserted, a claimed `trust_level` capped at a registered ceiling, export gating, and a PGP-encrypted ledger.

Two properties to carry into this design:

- **`bind_tools` makes gating structural rather than remembered.** It returns a `GatedSession` holding the tool callables privately, so `call()` authorizes before invoking and there is no un-gated path to the function. This is the same move as #127's authenticate-at-the-read: *the module can be bypassed, the gate cannot.* Two independent components arriving at that pattern is a strong signal it should be the default for anything new here.
- **Enforcement and audit are different states of the same component.** Wired into a pre-tool hook, a denied call never runs. Un-wired, `willow-gate` is a loud ledger that records and announces but cannot stop what it is never asked about. Any claim in this document that something is "gated" must say which of the two it means.

A destination allowlist is still wanted for the genuinely outward traffic of §6's policy model — payment tokenization, the drop, circuit submissions — but it is a smaller, later thing than this document implied, and it sits outside the app rather than around it.

### The residual, and why it is a deployment requirement here

`willow-mcp` states its own weakness plainly, and it is the single most important operational fact for this design: **on a host where the agent and the MCP server run as the same uid, the agent can write the very files that authorize its egress.** Leases make a self-grant expire and leave a record, and a `PreToolUse` hook blocks the obvious attempts, but the operating system is not stopping it. `WILLOW_MCP_STRICT_TRUST_ROOT=1` refuses egress when the keys are self-writable — and it ships **off by default**, because turning it on before uid separation exists would deny egress on every current install (tracked as B-32).

For a personal box, off-by-default is a reasonable trade. For a hub holding minors' education records it is not. So this is a hard requirement of any school deployment, not a hardening option:

- `mcp_apps/` and `mcp_apps/_net_leases/` owned by a uid the application does not run as
- `WILLOW_MCP_STRICT_TRUST_ROOT=1`
- the trust root outside any directory bound read-write into a task sandbox — *put data in the repo; put the gate outside it*
- **the trust root not in a git repository at all**, and not on a remote
- `diagnostic_summary`'s `checks.net_lease.self_writable` clean, checked as part of install acceptance rather than trusted

That second bullet is not hypothetical, and it is the reason to state it as a requirement rather than a preference. `willow-config` **is** `~/.willow`, version-controlled and pushed — and `mcp_apps/`, the manifest ACL that grants `task_net`, is tracked inside it. willow-mcp's own severance documentation says exactly why that is the wrong place: *the trust root must live somewhere neither this process nor the Kart sandbox can write; a repo directory is the wrong place for it, however convenient, because repos are bound read-write into task sandboxes.*

So the fleet's guidance and the fleet's own home disagree, and the home is what runs. A committed authorization surface is writable by anything that can write the working tree, restorable by anything that can `git checkout`, and mirrored to a remote. For a personal box that is a manageable trade. For a hub holding education records it is not, and a school install must not inherit the layout by copying it.

Worth separating cleanly for that install: **contract and config are exactly the things that benefit from version control** — `willow.md`, `settings.global.json`, `kart-sandbox.json`, personas, skills, templates. The *grants* are not. Track the first set; keep `mcp_apps/` and `_net_leases/` out of the tree, owned by a uid the application does not run as.

**Severance is the mechanism for "this org's data stays local," and it is asserted rather than assumed.** Naming the fleet an install is cut off from turns the claim into something checked across four surfaces, with the right asymmetry: store and Postgres hold *data*, so a violation degrades; `trust_root` and `egress` hold *authority*, so a violation breaks. A server reporting `ok` while wired to the fleet would be worse than no check at all. Every school install should assert severance, and an unasserted one should not pass acceptance.

### Policy model — superseded by willow-mcp's three keys

This document proposed a destination × data class × purpose triple. `willow-mcp` implements something better, and the improvement is that **no single authority can open the door**:

| Key | Question | Turned by |
|---|---|---|
| `task_net` | May this app *ever* request egress? | operator, once, in the manifest — deliberately excluded from `full_access` |
| `consent.internet` | Is egress permitted *right now*? | operator, flipped freely in `settings.global.json` |
| egress lease | For *this app*, until *when*? | operator CLI, expires on its own |
| signed task envelope | This submitter, this exact task, scope, expiry, nonce? | operator, one use |

The load-bearing sentence is *an agent may request egress and may never grant it to itself*: `grant-net` is local-CLI only, no MCP tool can mint a lease, and the Ed25519 signing key lives outside `WILLOW_HOME`.

`consent.internet` is the kill switch this document asked for, already built — `{"consent": {"internet": false}}` stops network tasks immediately without editing a manifest. And the reading discipline is the right one everywhere: a missing file, an unparseable file, a non-boolean (`"true"`, `1`), an expired lease, a deadline with no timezone, or a lease naming a different app than the file it sits in all read as denied. **Absence is not consent, and a name is not an identity.**

Destination still wants expressing for the genuinely outward traffic — payment tokenization, circuit submissions, the drop — but as adapters in the integration ledger, where the rule is already *earned, not scaffolded*: four adapters live, six declared stubs that refuse fail-closed and name what would earn them.

**Purpose is not a field on a call; it is a property of a session, and §7.2 is where it lives.** Declared on entry, reconciled on exit.

### The redaction funnel exists; it does not know about students

Tool responses pass a single funnel that redacts credential-shaped values — provider keys, PEM blocks, tokens, JWTs — to `[REDACTED:<kind>]`, with per-tool exemptions that are receipted as `credential_returned` so an exception is loud rather than silent.

**That is exactly the mechanism §6's outbound scanning wanted, aimed at a different noun.** The funnel is one place; adding student-identifier patterns to it is a smaller change than building the scanner this document imagined. The classes above are what it would key on.

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
- **The existing fallback chain must be disabled, not merely unused.** `willow-seed` documents a "free fleet fallback": when local Ollama is unavailable, inference routes to Groq → Cerebras → SambaNova on keys from `credentials.json`. That is a sensible default for a personal box and a **silent FERPA disclosure** on a school hub — it fires exactly when the local model is down, which is when nobody is watching, and it produces no error. A rule that says *local models only* is satisfied by a running Ollama and defeated by a stopped one. Remove the fallback keys, assert their absence in install acceptance, and let local inference **fail loudly** instead of degrading to a third party.
- Agent tool-calls are constrained by the same authorization tuples as the human they act for — an agent cannot read what its principal cannot read.
- Agents knock like anyone else (§7.2), and being the least trusted rung, they are the loudest.

**Put a verified corpus in front of the model.** `jeles` is the pattern: a *nugget* is a human-verified question/answer pair carrying `sources`, `verified_by`, and `verified_at`, and the corpus **sits in front of live search rather than replacing it** — a confident match answers instantly, with citations, no model call at all. Two ask modes with different logging rules: a passive background check never logs a miss; a deliberate ask treats a miss, or a match below threshold, as a real *gap* worth tracking. Local logging is synchronous and the source of truth; any fleet forward is best-effort, never blocks, never raises.

For a director asking questions of their own program, that ordering is the whole design. The recurring questions — when is the fee deadline, who repairs a sousaphone, what is the eligibility rule — should answer from verified content with a citation and a named verifier, deterministically, with no inference involved. The model is the fallback for the tail, not the front door. And the gap log becomes a program artifact in its own right: what this program keeps asking that nobody has answered yet.

`verified_by` / `verified_at` is also the same shape as `rationale`'s human seal (#125) — two components independently deciding that an answer is only trustworthy when a person's name is attached to it.

**Converge the provenance vocabulary before adding a fourth.** The fleet expresses "how much should I trust this" in several incompatible ways, and a music program touches at least three of them in a single view. §15 settles the scale, its direction, and how it composes.

**The friction floor belongs here too.** `willow-gate`'s sibling module watches a different surface from access: whether the agent has stopped being *other* and started reflecting the user back, smoothed, while the user is escalating. Model-free, deterministic, running outside the model it watches — because a mirror cannot audit itself. It flags for a human and never blocks.

That is not a general-purpose nicety in this domain. The highest-stakes moments in a music program are a student in crisis, a conflict with a parent, a disciplinary decision, and a death in the program. An assistant that agrees fluently with a stressed director in exactly those moments is a real harm vector, and flagging rather than blocking is the correct posture for a detector that will sometimes be wrong.

---

## 7. Authorization

Roles alone will not express this. The defining requirement is **outsiders holding narrow, time-boxed access into someone else's program**, which is a relationship problem, not a role problem.

This is the section most superseded by what exists. `marching-arts` P1/P2 is the resolver, and it is stricter than what follows.

### What the resolver already guarantees

- **One predicate: `(allow₁ OR allow₂ OR …) AND NOT (deny₁ OR deny₂ OR …)`.** Denies negate the *union* of allows. Dropping the parentheses around the joined denies binds only the first term, the rest silently stop applying, nothing raises, and every row they were meant to withhold becomes visible. That specific failure has a regression test — which is the right response to a bug whose signature is *silence*.
- **Guarantees are mechanisms, not prose.** `source` is `NOT NULL` with a non-blank `CHECK`; a sealed grant without a signer is refused by `CHECK`; `COUNT(*)` runs under the predicate rather than beside it; **roles grant nothing on their own**.
- **Refusal is indistinguishable from absence.** A member who declined and a member who is absent produce the same rows, the same count, and the same subject list — tested as indistinguishability, because if they differed, declining would itself become the signal and every member who exercised the choice would be marked by exercising it. This is the same principle §18 of the capability map asks for around fee waivers, generalized: **the system must not leak the fact of a refusal.** Any new surface — a roster view, an export, an aggregate count — inherits that obligation.

  > **What that test does not prove.** Indistinguishability is a statement about two *negatives* being identical. **If the predicate returned nothing to anyone, it would still pass** — every principal's count would be zero, every subject list empty, and all of them equal. It is necessary and not sufficient, and it needs a companion assertion that an entitled principal sees exactly the rows they should.
  >
  > This is not a hypothetical failure mode in this codebase. `willow-mcp` #211 records six defects found in verification apparatus against zero in the code under verification, and one of them is precisely this shape: *a fixture with no row the principal could not already see, so the tripwire meant to force a roles table could not fail.* The check worth running is not another test — it is confirming the existing indistinguishability fixture contains a principal who can actually see something.
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
- **The predicate must gate outbound sends, not only reads.** A restricted guardian still on the SMS list receives a live location disclosure about a minor, pushed to a device, with no way to recall it (§4.1). A read gate that does not also derive the send list is not protecting the thing that actually leaves.
- A restriction that must take effect at a future date has nowhere to live until it does.
- Reinstatement — orders get modified — has to reconstruct what deletion discarded.

The recommendation is that guardianship terminate by **setting a date, never by removing the edge**, so that revocation-by-order and revocation-by-majority are the same mechanism with different sources. Erasure of a guardianship record remains available separately, under §5's per-subject partitioning, as a distinct act with its own authority.

**Use the fleet's spelling, because the mechanism already exists.** `willow-2.0`'s `20260522_bitemporal_all_tables.sql` puts `valid_at` / `invalid_at` on seventeen tables — *when the record became true*, and *when it was superseded, NULL meaning still active* — with supersession as a nullable timestamp rather than a delete. That is the proposal above, already built, under better names. Adopt them rather than inventing `effective_from`/`effective_until`.

Its **exclusion list is the more instructive half.** `frank_ledger`, `hook_executions`, and `routing_decisions` are deliberately left out, because they are append-only audit and *records are never superseded* — a historical fact is not mutable state. The same split applies here: guardianship, enrollment, staff assignment, and fee schedules are state and take the pair; the disclosure log, the consent chain, and reconciled sessions (§7.2) are history and must not.

**One caveat worth carrying.** The migration backfills `valid_at` from `created_at`, so on legacy rows the two axes coincide, and the tables lacking `created_at` end up with only one axis. For guardianship you need both, and the case that proves it is ordinary: **a court order dated in March, delivered to the program in October.** *When the restriction took effect* and *when this system learned of it* are different dates, and a disclosure made in June was either compliant or not depending on which one you ask about. Keep `created_at` immutable alongside the pair, and never update it.

This is the one place in this domain where the failure is a safety failure rather than a bug, and it is worth having the mechanism before the case arrives — because when it arrives it will arrive urgently.

**The fleet has already named this as its hardest open problem.** `corpus-lens` scopes itself to *owner == subject* — studying yourself — and says so explicitly: *pointing it at another person (a child, a partner, an employee) is a different consent object and is out of scope by design.* Its "named and deliberately unbuilt" list puts it plainly:

> The guardian-consent model (owner ≠ subject) — **the biggest gap between this toolkit and any family-facing instrument**; not solved, so not shipped.

Every persona in this document is owner ≠ subject. A school holds records *about* minors; a director reads data they are not the subject of; a guardian consents on behalf of someone else. `marching-arts` P2 is the fleet's first real attempt at that model — guardianship edges, consent never requested by its beneficiary, expiry at majority. **This app is where that gap either gets closed or gets shipped unsolved**, and §7.1's dated termination is the part of it still missing.

### 7.2 The knock — sessions are reconciled, not merely authorized

`willow-gate` does something no other component here does, and this document read past it. Every session **knocks**: thirteen fields declaring intent on entry, thirteen declaring outcome on exit, and the gate diffs them. Trust is bound rather than asserted — the `signature` is an HMAC over the header keyed by a secret the gate holds, and a claimed `trust_level` is capped at a registered ceiling, so *"Elder" is not a text field anyone can type.*

**Everything else in this design gates the attempt. This is the only thing that checks the result against the promise.** A permission check asks *may you?*; the knock asks *may you, and did you do what you said you would?*

#### It is the purpose mechanism §6 was missing

§6 asks for a destination × data class × **purpose** triple and never says where purpose lives or what enforces it. It lives here. A session declares what it is for; a session that did something else produces a diff, whether or not the permission system would have allowed it.

That matters most for exactly the personas that made this domain hard. **A judge arriving on-site is a session knocking**: declares Event 42, these captions, this window; exits having read three sheets, written twelve commentary rows, and exported nothing. A guest who declared *score ensemble 7* and touched forty members' medical records generates a reconciliation failure **even if the grant technically permitted it**. For transient outsiders whose behaviour cannot be fully constrained in advance, detection is the half that actually protects anyone.

#### Two inversions, both correct and both counter-instinctive

- **Announcement is loudest for the least trusted.** Most systems log administrators exhaustively and guests barely. This does the reverse. The judge on a borrowed tablet for one evening is precisely the session worth narrating.
- **Drift and fail budgets *tighten* as trust rises** — the most powerful rung held to the strictest tolerances, not the loosest. The director has the most access and therefore the least slack, because the director's compromise is the catastrophic one. Every instinct says trusted users earn less scrutiny; the compromise math says the opposite.

#### Read is universal; export is the gated act

Level 0 is refused a session and **still reads**, loudly, by a path the gate never claimed to mediate. What it cannot do is take information anywhere else: export and exfiltration are what the gate holds.

This document was built the other way round — §4 and §7 concentrate on gating reads. The knock's position is better, and it should be adopted: **narrate the read, gate the export.** The realistic harms in a music program are not someone glancing at a schedule; they are the roster on a thumb drive, the spreadsheet mailed to a vendor, the season's medical forms copied off before someone leaves. Concentrating enforcement where data *leaves* produces a system that is simultaneously less obstructive day to day and more honest about where the risk actually sits.

The read side does not become free — refusal indistinguishability (§7), the L-ladder, and the consent predicate all still govern what a read returns. What changes is where the *ceremony* goes: reconciliation and announcement at the boundary, not friction on every glance.

#### `law-gazelle` is the worked example, in a comparable domain

The previous version of this section said the mechanism existed but nothing bound guests to it. That was wrong: `law-gazelle` — a local-first case command center for private legal matter data, including co-parent and family-law matters — already wires the gate in **enforcement** mode. `GAZELLE_GATE=1` routes every `tools/call` through `willow-gate` before dispatch, a denied call never runs, clients check in with a signed 13-field header and check out through the paired call, and **if the gate is enabled but misconfigured the server refuses to start.**

Its trust mapping is the template:

| Operation | Minimum rung |
|---|---|
| Read tools | Rookie |
| Sidecar writes | Steady |
| Local-AI tools (`query`) | Veteran |
| `gazelle_save` / `gazelle_commit` — **counted as exports** | Steady, denied below |

Note what that last row does: it classifies *save and commit* as exports rather than writes, and gates them accordingly. That is the read-versus-export principle expressed as a concrete permission table, in an app handling custody matters — the same population this design worries about in §7.1 and §20. Judges and clinicians want the identical shape: read at the guest rung, commentary writes one rung up, export gated hard and announced.

#### A fifth gate exists, and its default fails open

`openclaw-sap-gate` implements SAP/1.0 — SAFE Authorization Protocol for MCP tool calls — as a four-step chain: the SAFE folder exists, `safe-app-manifest.json` is present, its `.sig` is present, and `gpg --verify` passes with the signer matching `SAP_PGP_FINGERPRINT`.

Two properties are worth recording before anything here depends on it.

**`SAP_PGP_FINGERPRINT` defaults to empty, and empty means *any valid signature passes*.** That is a fail-open default in an authorization gate, and it runs directly against the discipline the rest of the fleet holds — willow-mcp reads a missing or unparseable file as *denied* on the principle that **absence is not consent**. Unpinned, SAP authorizes anyone who can produce a well-formed signature with any key. Any install here must pin the fingerprint, and the pin belongs in install acceptance rather than in a setup guide.

**The protocol it implements is no longer published.** The README cites an SAP/1.0 RFC and an enforcement skill, neither of which resolves — the repos were retired once their content had been absorbed. The consequence is narrow but real: SAP/1.0 now exists only as its implementation, so the empty-fingerprint default cannot be classified. If the spec required a pin, that default is a defect; if the spec was silent, it is a gap in the protocol. Same symptom, different fix, and no artifact left to distinguish them. Anything here that depends on SAP should first restate the four-step chain as a local, versioned contract it can test against.

**Revocation is deleting the folder or the `.sig`** — which leaves no dated record, and therefore cannot answer *was this app authorized on October 12*. For agent authorization that may be an acceptable trade; for anything touching education records it is the exact failure §7.1 is written against. If SAP ever gates a path that touches student data, revocation needs the `valid_at`/`invalid_at` treatment rather than `rm`.

Counting: `willow-gate`'s HMAC knock, willow-mcp's manifest ACL, the three-key egress chain, `law-gazelle`'s wiring of the first, and now SAP's GPG-signed manifests. Five mechanisms answering overlapping questions with different failure modes. That is a `FLEET_SEAMS` entry waiting to be written, and this design should name which one it depends on rather than inheriting all five.

#### Enforcement or ledger — say which

`willow-gate` prevents only when a harness routes every call through it before the tool runs; un-wired, it is a loud ledger that records and announces but cannot stop what it is never asked about. `bind_tools` is that harness in-process, holding the callables privately so there is no un-gated path to them.

**Every claim in this document that something is "gated" must name which of the two it is.** A ledger is a legitimate and useful thing to have; a ledger described as a gate is not.

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
| FERPA | Education records | Disclosure record = reconciled sessions (§7.2), not merely an event log; guardian access rights; retention/purge |
| COPPA | Students under 13 | School-consent pathway; no third-party trackers, ever |
| State student-privacy laws (NY Ed Law 2-d, CA SOPIPA, etc.) | Varies | Data inventory + no-sale/no-ads posture; parent-facing privacy notice |
| PCI-DSS | Payments | Tokenized only; stay SAQ-A by never touching card data |
| Photo/video release | Media of minors | Consent state on `MediaAsset`, enforced at egress |
| Records retention | All | Season-boundary purge job; graduated-student disposition policy |

Not legal advice — the state-law column in particular varies enough that the district's counsel should see the data inventory before parents see the app.

### Two artifacts to reuse rather than write

**`willow-2.0/TRUST.md` is the privacy notice, already drafted.** Three tables — *what stays local* (with the specific store named), *what can leave, opt-in only* (with the exact condition per feature), and *how to verify the code yourself* — plus an explicit honesty note that demo data is seeded and labelled. Retarget it at guardians and at a district technology review and it is most of what either audience needs. Its structure is the valuable part: not a policy, a **map of every path data can take, each with the switch that opens it.**

**`willow-2.0/SECURITY_AUDIT.md` is a reusable acceptance rubric.** Fifteen numbered checks — SQL construction, shell injection, path traversal, credentials in version control, CORS, XSS, unsigned execution, MCP tool auth, exception swallowing, temp-file predictability, race conditions, manifest correctness, dependency pinning, hardcoded home paths — with findings carrying IDs, severity, and status. Run it against this app before a school install, and treat the result as an install gate rather than a document.

**Add a line the rubric does not have: the verification apparatus was itself verified.** `willow-mcp` #211 reports that across three merged PRs in one session, **six defects were found in the verification apparatus and zero in the code under verification** — a differential reference generated before the thing it checked changed; a fixture writing a hash chain with the same function it read it back with, so a rename was invisible *and self-consistent*; a fixture that could not fail; a killed mutation harness that left a mutation in the tree and turned every subsequent number into fiction; three mutations that renamed a SQL trigger rather than disabling it, so it kept firing under the new name; and counts in prose that nothing checks.

That is the empirically observed failure mode here, and it is the one that matters most for an institution accepting this software: **"the tests pass" is exactly the claim that has been breaking.** So acceptance cannot rest on a green suite. For every mechanism this document calls a guarantee — the resolver predicate, the consent triggers, the chain anchors, the egress gate, the guardianship dates — the gate is *mutate it and watch the suite go red*. A guard that cannot be shown to fail has not been shown to work, and nothing about a passing run distinguishes **this fires correctly** from **this never fires**.

The related trap, worth naming because this codebase has hit it more than once: **duplication with a gate, where the gate is what fails.** The hook exists in a bundled copy and a repo copy, and the entry point loads the one the tests do not exercise. `libs/subject-consent` is canonical with a vendored fork in UTETY. `marching-arts` carries a TypeScript port of a Python core that #120 found had drifted behind, and #123 found three defects in browser code that had never executed. Anything this system duplicates inherits that shape, and the mitigation is not another test — it is mutating the equivalence check to confirm it can still fail.

**One finding in it is a live condition for this design.** W-MCP-01 records that `willow-2.0`'s `sap/` MCP servers expose knowledge read/write and task submission with no per-client authentication, judged acceptable because the design is portless, and states the trigger explicitly: *future fix needed if network transport is added.* Serve mode and any parent-facing path are that trigger. `willow-mcp` appears to answer it with OAuth plus operator-confirmed identity binding — but `willow-2.0` still owns the shared fleet Postgres schema, so an install that touches those servers inherits the P1 rather than the fix.

---

## 11. Operations

- **Backups:** 3-2-1, always sealed, one copy off-site, **restores tested on a schedule.** The hub is a single point of failure holding a season's work.
- **Availability:** a cold spare with a nightly restore is usually enough; a program can run a day on paper but not a week. Match the recovery target to what the director can actually tolerate during championship week.
- **Offline:** clients degrade to local replicas. Attendance at a stadium with no signal is the design case, not the edge case.
- **Upgrades:** signed artifacts pulled through the gate, staged, roll-back-able. No vendor tunnel into the box.
- **Season lifecycle:** graduation, roster turnover, staff departure, and purge are recurring scheduled events, not one-off scripts written in a panic each June.
- **Loss of the director:** the person who holds the most access is also the one likeliest to change jobs. Escrow and succession are operational requirements.

### 11.1 The exit plan is a shipping requirement

`awesome-sovereign-software` states the fleet's own criterion, and it is stricter than anything in this document: **sovereignty is the ability to leave**, every listed entry documents how you walk away with your data, and *if an exit line cannot be written honestly, the app does not get listed.*

This design has escrow (§5) — how to recover a key you still hold. It did not have **exit** — how a program leaves entirely. Those are different, and the second is the one an institution will actually need:

- A director changes jobs and the successor prefers something else.
- The district standardises on a vendor.
- The booster dissolves, or the program is cut.
- The software stops being maintained.

In every case the education records must survive, in a form a person can read **without this application**, and FERPA retention obligations continue regardless of what the program is running. So the exit line has to be written now, tested like a restore, and hold against the five-point test the fleet already publishes:

| Criterion | What it demands here |
|---|---|
| Runs without an account | On-site personas already do; guardian passkeys are device-held, not vendor accounts |
| Runs without a server | The hub is the org's; §4.1 keeps notification off any hosted dependency |
| No subscription for core function | No feature may become unavailable on non-payment — least true of anything with a hosted SMS route |
| **Data readable without the app** | SQLite plus documented schema, exportable to CSV/PDF per record type — including commentary audio and its transcript |
| **Survives the vendor** | The box keeps working with the network cut and nobody maintaining it |

**Write the exit line before the first install, not at the end.** Something as specific as: *your program's records are one SQLite file per store plus a media directory; `terpsi export --all` writes CSV per table, PDF per student record, and the original audio; the schema is documented in `docs/`; nothing requires this software to read.* If that sentence cannot be written honestly, that is the finding.

One caution the same list supplies: its **Delisted** section records sovereignty regressions with a date, a reason, and a source, and *removing an entry without accounting for it fails CI*. Regressions are normal; unrecorded ones are the problem. An install that quietly acquires a hosted dependency between seasons has regressed, and something should say so out loud.

---

## 12. Decisions to lock now

1. **Trust boundary at the hub, not the client** — enables a real application; everything else follows.
2. **The relay can't read anything** — makes its compromise survivable and makes the transport swappable.
3. **Relationships over roles, every grant expires** — the only model that handles judges and clinicians cleanly.
4. **Classification at schema-definition time** — the one thing that is genuinely miserable to retrofit.
5. **Egress inexpressible in the core, gated at the perimeter** — import purity first, network policy only where the world must genuinely be reached.
6. **Commentary is the adjudication primitive; captions and ratings are projections over it** (§8.1) — the difference between supporting symphonic festival as a configuration and rebuilding for it later.
7. **Revocation is a dated predicate, never a deletion** (§7.1) — majority already works this way; guardianship termination by court order must work the same way, and it must derive the send list as well as the read.
8. **SMS carries signals, never records** (§4.1) — where the transport cannot be made incapable, the payload is made not worth reading. Minimization is the mechanism, and it is what shrinks the parent problem from daily to occasional.
9. **Sessions declare a purpose and are reconciled against it** (§7.2) — the only check in this design that compares outcome to promise, and the disclosure artifact a regulator actually wants.
10. **Narrate the read, gate the export** (§7.2) — the harm is in data leaving, not in someone glancing at a schedule. Concentrating ceremony at the boundary is both less obstructive and more honest.
11. **The exit line is written before the first install** (§11.1) — sovereignty is the ability to leave, and if the line cannot be written honestly that is the finding.
12. **A guard that cannot be shown to fail has not been shown to work** (§10) — acceptance is mutation, not a green suite; the observed failure mode in this fleet is defects in the verification apparatus rather than in the code it verifies.
13. **Ordinal scales never compare as raw integers, and provenance never gates** (§15) — two existing five-level scales already run in opposite directions; a third arrives only with prefixes and a single mapping table.

## 13. Open questions

- **Whose consent is it?** This was filed as "the auth model is scoped to a single process," which misread it. #127's memory-only signing key is not a limitation working around the absence of a server — it is SAFE's thesis: *Session-Authorized, Fully Explicit*, consent expiring with the session, the app asking again tomorrow. Tokens dying with the process is the framework behaving correctly. The real question is narrower and harder: **SAFE's model is a data subject authorizing access to their own data, and this domain is an institution holding records about minors.** A parent viewing their student's balance fits the session model cleanly. A director opening the roster at 6 a.m. is not the data subject and cannot be asked to re-consent on the students' behalf every morning; the consent that governs them is the guardian's, granted elsewhere and enforced by predicate. Both mechanisms are built. What is not written down is which one governs which surface, and a system that guesses will eventually ask the wrong person.
- **Does a 200-household deployment change the session model's shape?** Not its principle — its ergonomics. Re-authorizing per stream per session is right; re-authorizing eight streams every morning before seeing a schedule change is how a family stops opening the app.
- **Does `rationale` (#125) generalize into the disclosure story?** It ships the reasoning beside the data, gated by a human seal rather than a predicate, with `draft | internal | shipped` states. FERPA §99.32 wants a disclosure record and §6 assumes the egress log supplies it — but "why were you refused" is a `rationale` question, not an egress-log question. The two may want to meet.
- The current build targets caption scoring. Does its model treat captions as projections over anchored commentary (§8.1), or as the base structure? If the latter, that is the one thing worth revisiting early — festival ratings and clinician feedback both fall out for free under the former.
- Score-position anchoring: align audio against a stored score, or judge-driven tap-to-mark, or both? Affects how much of the music library must be machine-readable.
- **Can `field-acoustics` and commentary share coordinates?** A judge's remark is anchored to a moment and a seat; the acoustic model predicts what arrived at that seat. Pairing them gives a claim no drill designer can currently make — and gives the model's `ASSUMED` rear hemisphere a source of validation data that would otherwise have to be measured in the field.
- **Should adjudicators be calibrated?** `oakenscrolls-office` is a working calibration ledger — state a claim with confidence, grade it when the world weighs in, and a reliability diagram shows whether your 70% means 70%, scored by Brier and log loss, append-only so a revised number never erases the original. Point that engine at adjudication and the question becomes: does this judge's caption score predict placement, and are they consistently high, low, or noisy against the panel? That is a real capability with an existing implementation, and also the most politically delicate feature in this entire document — a circuit may want it badly and individual judges may not. Decide who may see a judge's own reliability curve before building it, because the answer is probably *the judge, and no one else by default*. Note the same repo's citation pattern is directly reusable: resolution evidence pinned to a source *and the git commit of the catalog that vouched for it*, read from local clones with no network.
- **Does the practice loop violate a fleet ground rule?** UTETY's ground rule 2 is *feedback is about the work, never the learner* — no praise of the person, no leaderboards — with a policy test linting content against self-directed praise. The capability map proposes practice streaks, cumulative-hour milestones, and chair-challenge standings. Some of that is about the work and survives; some of it is a leaderboard with a different name. Reconcile before building, because the rule is enforced by test in a sibling app and this would be the second student-facing app in the fleet.

---

## 14. Fleet components this maps onto

Written after reading the READMEs of the components below; contents inferred from those, not from source.

| This document | Component | Status |
|---|---|---|
| §5 the box / Zone A | `willow-data-vault` | **Exists.** Three-layer lifecycle, `vault.key` + Fernet, fail-closed on a keyless vault |
| §5 at-rest sealing of *records* | — | **Open.** The vault seals secrets; collection stores are not described as encrypted |
| §5 escrow | — | **Open, and the largest gap.** Single-file key loss is unrecoverable by design |
| §6 core purity | `safe-app-common.no_egress` | **Exists**, canonical, with the core/seam partition this document lacked |
| §6 the un-passable seam | UTETY `knowledge.py` | **Exists** as a proven pattern in a student-data app |
| §6 perimeter | `willow-gate` | **Exists**, as an agent trust gate rather than a network broker |
| §7.2 session reconciliation (the knock) | `willow-gate` | **Exists.** 13 fields in, 13 out, diffed; bound trust; louder for the least trusted; budgets tighten as trust rises |
| §7.2 guest sessions reconciled | `law-gazelle` | **Exists as a worked example** in a comparable domain — gate in enforcement mode, trust ladder mapped to operations, save/commit classed as exports, refuses to start if misconfigured |
| §5 canonical vs sidecar | `law-gazelle`, `nest-seed` | **Convention, stated twice.** Canonical store read-only to the app; agent write path is sidecar only |
| §5.1 compute isolation | `kartikeya` | **Exists.** Bubblewrap, network-isolated by default, credentials only to net-enabled tasks, cgroup/prlimit caps |
| §6 verified answers before inference | `jeles` | **Exists.** Nuggets with sources and a named verifier, in front of search; gaps logged local-first |
| Library digitization | `nest-seed` | **Exists.** Regex → local embeddings → generative only on the ambiguous tail, degrading gracefully |
| Question banks / assessment | `civics-check` | **Exists as a pattern.** Authoritative sources compiled to a catalog; never hand-edit the output |
| Consent-scoped activity capture | `ask-jeles` learning events | **Exists.** Off by default every launch, never persisted across launches, records shape not content |
| Mirror detection near high-stakes decisions | `willow_gate.friction_floor` | **Exists.** Flags for a human, never blocks, runs outside the watched model |
| §6 destination allowlist | — | **Open**, and smaller than this document implied |
| §7 authorization + consent | `marching-arts` P1/P2, `libs/subject-consent` | **Exists** |
| §7.1 dated guardianship | `willow-2.0` `valid_at`/`invalid_at` | **Mechanism exists** on 17 tables, with append-only audit deliberately excluded. Binding guardianship to it does not |
| §10 privacy notice | `willow-2.0/TRUST.md` | **Reusable structure** — every path data can take, each with its switch |
| Install acceptance gate | `willow-2.0/SECURITY_AUDIT.md` | **Reusable rubric**, 15 checks. W-MCP-01's trigger condition applies here |
| Verifying the verifier | `willow-mcp` #211 | **Open.** Six apparatus defects to zero code defects across three PRs; no mutation gate exists for this app's guarantees yet |
| Allow-side coverage of the resolver | — | **Unknown.** Indistinguishability passes even if the predicate returns nothing to anyone; check the fixture has a principal who can see something |
| §10 COPPA / under-13 | SAFE `HARD_STOPS`, UTETY ground rule 4 | **Exists** as governance, above app level |
| §8.1 commentary primitive | — | **Open** |
| §1–§2 practice + mastery | UTETY (BKT, item sets, on-device store) | **Adjacent.** Different subject matter, same shape — worth reading before rebuilding |
| Library vs. learner split | UTETY ↔ Jeles | **Settled pattern.** UTETY holds the learner, Jeles holds the sources — the repertoire library may want the same seam |
| §6 kill switch | `consent.internet` | **Exists** |
| §6 three-key egress + envelope | `willow-mcp` | **Exists**, stronger than proposed |
| §6 outbound scanning | the redaction funnel | **Exists for credentials.** Needs the student-identifier classes |
| §3 hardening | `WILLOW_MCP_STRICT_TRUST_ROOT`, severance | **Exists, off by default.** Mandatory here — see §6 residual |
| §4 staff remote access | `willow-mcp` serve mode (OAuth + confirmed binding) | **Exists** |
| §4.1 parent notification + acknowledgment (~95%) | SMS, ideally a local SIM gateway | **Open, but small.** No app, no enrollment, no inbound; constrained by carrier throughput, not cost |
| §4.2 the transactional relay (~5%) | — | **Open.** Grove's u2u is signed, *not* confidential — reusable identity, missing confidentiality |
| §7 finance module | `private-ledger` | **Exists as a template**, with the injected-`ingest` bridge pattern |
| §10 / §17 aggregate exports | `nest_promote`, `nest_digest` | **Exists as a pattern.** Promote *structure* — counts, categories, never content; the full digest is local-CLI only, never returned over MCP |
| Guardianship / family graph | `the-squirrel` | **Adjacent**, though it serves a web port rather than staying import-pure |
| Judge calibration | `oakenscrolls-office` | **Exists as an engine** — see §13 and §15 |
| §15 `P1–P5` provenance | `field-acoustics` (3 rungs), evidence tiers, `jeles`, `oakenscrolls-office` | **Partial and divergent.** Four vocabularies, no mapping; the `Cited` and `Estimated` rungs have nowhere to sit today |
| §15 scale-direction convention | — | **Open.** `T0–T4` and `L1–L5` already oppose; no prefix rule or mapping table exists yet |
| §11.1 exit plan | `awesome-sovereign-software` | **Criterion exists**, five-point test plus a required exit line. No exit line written for this app yet |
| Owner ≠ subject consent | `corpus-lens` (names it unsolved), `marching-arts` P2 | **The fleet's stated hardest gap.** This app is where it closes or ships unsolved |
| Cloud inference fallback | `willow-seed` (Groq/Cerebras/SambaNova) | **Must be disabled, not unused.** Fires exactly when the local model is down |
| Trust-root placement | `willow-config` | **Counter-example.** `~/.willow` is a tracked repo with a remote, and `mcp_apps/` is in it — against willow-mcp's own severance guidance |
| Contract + sandbox policy | `willow-config` (`willow.md`, `settings.global.json`, `kart-sandbox.json`) | **Exists.** These are the right things to version; the grants are not |
| §15 rendering the scales | `safe-design` | **Exists.** Semantic tokens, lookup-time aliases, structurally guaranteed backend parity, ASCII path |
| §5 exclusion of family data from the corpus | `willow-compose` | **Exists as stated policy.** This app is a family-data app by its definition |
| Fifth authorization mechanism | `openclaw-sap-gate` (SAP/1.0) | **Exists**, with a fail-open default fingerprint and revocation-by-deletion |
| §17 district / equity data | `almanac-data/education-almanac` | **Not yet.** One national UNESCO entry; the NCES and state coverage the README describes is not in the catalog |

**Read before building:** `willow-grove`'s `FLEET_SEAMS.md` and `DESIGN_CONSTRAINTS.md`. The fleet already maintains a repo whose entire job is recording where two components each do half a job and the halves do not meet, with `file:line` citations and a re-verify command per finding. A new app is exactly the thing that creates a fifth such seam.
- Is "corporate" the circuit/association, the district, or a vendor? Changes what aggregates mean and who signs off on them.
- Does the org control its own hardware, or is the hub a district-managed VM? Changes the physical-trust assumption underneath Zone A.
- Are agents an implementation detail of the build, or a user-facing feature (a director querying their program in plain language)? The latter needs a local model of real capability inside Zone A.
- Single program, or does this eventually serve several under one hub? Deferred above, but it constrains the tenancy model if it's ever a yes.

---

## 15. Ordinal scales, and how they must not be confused

Three ordinal scales run through this system. A fourth quantity looks like one and is not.

### The direction hazard, first

Two five-level scales already exist and **they run in opposite directions**:

| Scale | Range | Higher means | Owner |
|---|---|---|---|
| Trust rung | 0 Exiled → 4 Elder | **more privileged** | `willow-gate` |
| Sensitivity | L1 → L5 | **more restricted** — L5 never served to anyone | `marching-arts` |

Both are small integers, both are called "level," and they point opposite ways. `if level >= 3` is correct against one and catastrophic against the other, and it reads perfectly in review either way. Adding a third five without settling this makes that collision near-certain.

The resolution is *not* to force them into agreement — sensitivity and privilege genuinely oppose, and bending one to match would make its own semantics worse. Instead:

- **Never compare raw integers across scales.** A single mapping — which trust rung a given sensitivity requires — lives in one place, and every gate calls it. `law-gazelle`'s permission table (§7.2) is that mapping, written out.
- **Prefix every rung so a bare integer cannot travel**: `L1–L5` sensitivity, `T0–T4` trust, `P1–P5` provenance.
- **Composition differs per scale**, which is the strongest reason they can never be merged:

| Scale | Composes by | Because |
|---|---|---|
| Sensitivity | `max` | a record holding one L5 field is L5 |
| Trust | `min(claimed, registered ceiling)` | trust is capped, never asserted |
| Provenance | `min` | a result is worth its weakest input |

If two scales do not compose the same way, folding them together loses information.

### Provenance is epistemic, not authorization

Trust and sensitivity **gate** — they decide what happens. Provenance does not gate anything; it qualifies an answer that is being served regardless. `field-acoustics` already has this right and it should be stated as the principle: the headline reads `ASSUMED`, **loudly**, rather than the result being withheld.

Low provenance is not a permission problem. Withholding a weakly-sourced number is the error; showing it with its weakness attached is the point. **Provenance is a label that travels with a value, never a condition on serving it.**

### `P1–P5`

The fleet's `measured | fitted | assumed` with the two rungs it currently collapses pulled out:

| | Rung | Means |
|---|---|---|
| **P1** | Measured | Instrumented here — this ensemble, this event, this instrument |
| **P2** | Cited | Someone else measured it; resolvable reference, named publisher, pinned version |
| **P3** | Fitted | Derived from local data by a stated model |
| **P4** | Estimated | Extrapolated from analogous cases, not this one |
| **P5** | Assumed | Asserted, no evidentiary basis, and declared as such |

**Cited** is doing real work that has nowhere to sit today: `oakenscrolls-office` pins resolution evidence to a source *and the git commit of the catalog that vouched for it*, and `jeles` pins `verified_by` with citations. Both are stronger than an assumption and weaker than a local measurement.

> **P2 decays silently, and nothing currently detects it.** A citation whose source has been deleted is a `P5` assumption still wearing a `P2` label — the rung does not fall on its own. This is not hypothetical in this fleet: `openclaw-sap-gate` ships on PyPI citing an SAP/1.0 RFC that no longer resolves, `catalog.json` names a canonical Grove repository that 404s, and #119 found two of four claimed canonical repos already gone. Repos get deleted once their value is extracted, which is reasonable; the citations pointing at them do not update, which is the problem.
>
> So `P2` requires storing enough to survive its source disappearing: not a URL, but a resolved content hash, a pinned commit, or the quoted claim itself. `oakenscrolls-office` is closest — a pinned catalog commit at least records *what was read* even when it can no longer be re-fetched. **"Catalog, don't host" has exactly this vulnerability**, and a program relying on a cited eligibility rule or a licensing term three seasons later will meet it.
>
> Minimum viable check: a periodic liveness pass that demotes an unresolvable `P2` to `P5` **loudly**, rather than letting it keep the higher rung by inertia.

**Estimated** matters because extrapolating from a different ensemble at a different venue is a categorically different claim than fitting to this one — and in this domain that distinction is the difference between a defensible design decision and a guess wearing a number.

Propagates by `min`. A headline is its weakest input, and says so.

### Confidence is not a rung

`oakenscrolls-office`'s 50–99% is **continuous**, and it is a claim about the future graded against an outcome. That is what makes calibration possible at all; collapsing it into five ordinal rungs would destroy the only thing it is for.

`willow-2.0`'s evidence-tiers migration already has the right pattern — `tier` **and** `confidence` as two columns side by side, one ordinal and one continuous, neither pretending to be the other. Copy that shape: carry `provenance` and `confidence` together, and only populate `confidence` where a resolution mechanism actually exists to grade it against.

### Where all of it collides

Adjudication, in a single row. A judge's caption score is a **claim**. `oakenscrolls-office` grades claims against outcomes. `field-acoustics` predicts what actually arrived at that judge's seat, carrying its own `P`-rung. So one commentary record can eventually hold the score, the judge's stated confidence, the provenance of the model that corroborates or contradicts it, and — a season later — the resolution.

That join is what makes judge calibration (§13) a measurement rather than a rhetorical position. It is also why these scales have to stay distinct: that row needs all four quantities to mean different things.

### Rendering them

`safe-design` is where these become visible, and it already holds the vocabulary: semantic tokens `grant` / `deny` / `warn` / `meter_fill`, aliased onto `healthy` / `down` / `degraded` / `accent`. Three properties transfer directly:

- **Aliases resolve at lookup, never at definition** — a skin that repaints `healthy` moves `grant` with it, and setting an alias directly is refused with an error naming the canonical token. A `P5 ASSUMED` badge and a denied state can therefore share semantics without either hardcoding the other's color.
- **Parity is structural.** The Textual and CSS backends resolve every token through the same `xterm256()`, so they cannot disagree — neither converts — and a test exists to catch anyone who breaks it. Six personas across a TUI, a browser, and a printed program need exactly that guarantee.
- **A skin fills the contract, never extends it.** Every token resolves in every skin, so a consumer can rely on a token existing forever.

The repo also documents the cost of not doing this: twenty-one terminal UIs in `safe-app-store` re-derived the same palette by hand, and `story-timeline/app.py` alone carries sixty hardcoded colors.

**One requirement this document adds.** None of these three scales may be encoded by colour alone. A sensitivity band, a trust rung, and a `P`-rung each need a glyph or a label carrying the same information — for colour-vision deficiency, for the printed program, for a phone in direct sun at a stadium, and for the `TERM=dumb` ASCII path `safe-design` already supports. `field-acoustics` gets this right by writing the word `ASSUMED`; the rule should be general.
