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

**But the fleet does have a template for a justified hosted component, and the relay should be held to it.** `jeles-remote` is the only remote-hosted service in the constellation — a FastAPI proxy on Fly.io fronting ~65 institutional search APIs — and it is a deliberate, tightly-argued exception rather than a lapse:

| Property | How it is achieved |
|---|---|
| Holds no state | Stateless; no volumes, no database, `min_machines_running = 0` — it is not even running between calls |
| Cannot reach the sensitive corpus | **By absence, not by gate**: *"no local knowledge base, no corpus access, no Postgres, no Ollama, no filesystem-backed credential store"* |
| Refuses to run misconfigured | *"The service refuses to start at all"* without `JELES_REMOTE_SECRET` |
| Touches only public data | Every call is an outbound request to a public institutional API |

That second row is the un-passable-parameter discipline again (§6), applied to a whole deployment: the corpus cannot leak through this service because the corpus is not in it.

**The drop can meet every one of those criteria**, and should be required to. Stateless, opaque payloads, no schema of the domain, no ability to enumerate, refuses to start without its keys. jeles-remote does not solve confidential transport — but it establishes the bar under which this fleet permits a hosted thing to exist at all, and §4.2's relay is the next candidate to clear it.

So the relay remains unbuilt, and reusing u2u for it would be a serious error. What u2u *does* supply is the harder half of a mailbox relay — signed identity, verified origin, per-contact consent flags defaulting to False so a newly admitted contact can deliver nothing until granted. A confidentiality layer over that is a smaller job than a relay from scratch.

**And the same app opens a port its manifest says it cannot.** `safe-app-willow-grove` declares `"privacy_tier": "local_only"`, `"local_processing": 1.0`, `"surfaces": ["tui"]`, permissions limited to `lan_listen` / `lan_send`, and its `CLAUDE.md` rule #1 reads:

> **No web ports for the dashboard.** Portless means portless.

`bridge/__main__.py` starts an aiohttp server on `0.0.0.0:8560` — all interfaces — and `bridge/matrix.py` makes outbound POSTs to an arbitrary configured homeserver. `bridge/app.py` opens a UDP socket to `8.8.8.8:80` to discover the local IP. The rule is scoped to *the dashboard*, so it is arguably not violated; a reader of the manifest would still conclude this app cannot open a port, and it can.

> **VERIFIED 2026-07-30 at `a2e11b3`, and this paragraph understates it three ways.** There are **two** all-interface listeners (`bridge/app.py:137` and `:214`), not one. The `8.8.8.8` probe is opened in **`grove/mcp_local.py:317`** as well as `bridge/app.py:60` — outside the bridge, in the app's own namespace, so the *"scoped to the dashboard"* defence above does not hold for it. And the app carries **no purity test at all**. See `docs/FLEET-READS.md`.

Its own `SECURITY_AUDIT.md` knows, and says so honestly: `u2u/` and `bridge/` are *"**Scanned, not Reviewed**… they make the repo's only cryptographic trust decisions and deserve a dedicated pass."* That is a disclosure rather than a defect — but it is **prose in an audit file, not an assertion**, and nothing fails if the bridge grows a new capability tomorrow. Which is §16's distinction exactly: an acknowledged missing middle is still a missing middle.

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

  > **And the anchor's custody was never specified — corrected 2026-07-30.** *"A **surviving** anchor"* — surviving where? An anchor held in the same vault as the chain dies with it, and one act makes the log read as never-written. This clause designs the data structure and skips the counterparty, which is the whole evidentiary question. `records/witness.py` supplies the mechanism; **§18 item 15** is the decision about who holds it.

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

#### `kart-sandbox.json` is the boundary in concrete form

The mount policy is a versioned data file, extensible "for new fleet paths without code changes," with security notes carrying decision dates and FRANK citations. Several of its properties should be inherited directly:

- **A no-network task gets zero credentials.** `~/.config/gh`, `~/.netrc`, and every entry in `credential_env_prefixes` are bound only under `allow_net`. Credentials follow the network grant rather than the process.
- **Private keys never enter the sandbox** — `~/.ssh` is unbound; SSH git works through `SSH_AUTH_SOCK` with `known_hosts` read-only, and only on `allow_net`.
- **`/tmp` and `/dev/shm` are private tmpfs, not host binds** — which matters directly here, because transcription and audio alignment write large intermediates derived from `MEDIA_MINOR`.
- **The sovereign data is read-only to arbitrary tasks** — the SAFE store, agents, and data vault are bound read-only under a note that names the reason: *the sovereign data must not be mutable by an arbitrary task.* That is §5's canonical-versus-sidecar rule enforced at the mount layer rather than by convention.

**One gap this design has to close.** The tier that makes local inference work is `allow_localhost`, and the file is honest about what it costs:

> `# allow_localhost` shares the host network namespace (loopback Ollama works) but still strips credentials and does not bind gh/netrc/ssh. **Weaker than `--unshare-net` isolation**; prefer over `allow_net` for embed-only work.

Sharing the host network namespace means a task holding `MEDIA_MINOR` audio can reach the network — it simply has no credentials to authenticate with. For embedding work on a personal box that is a sensible trade. For judge commentary over a performance by identifiable minors it is not, because §6's guarantee is *this data cannot leave*, not *this data cannot leave authenticated*. The fix is a tier that reaches Ollama without the host netns — a unix socket into the sandbox, or a loopback-only namespace — and until it exists, local transcription is running one policy tier weaker than §6 claims.

**And a school profile must be its own file, not this one.** The operator desk binds `~/github` read-write as a single-session host, offers personal paths (`Desktop`, `.kaggle`, `.fly`, `Ashokoa`), and lists `ANTHROPIC_`, `OPENAI_`, `AWS_`, `DISCORD_`, and `GITHUB_` among its credential prefixes. A hub holding education records should ship a much shorter policy whose credential list is empty, and the diff between the two is itself an install-acceptance artifact.

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

That also settles a question §19 of the capability map might otherwise have gotten wrong. A director's assistant may query the program's own store locally; it may not enrich the fleet corpus with what it learns there.

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

The middle ring is the one this document originally missed. `safe-app-common` has apps declare a **core/seam partition**: the seams are the outward-facing files, they are named explicitly, and the direction is enforced — seam→core and never the reverse — with a seam still held to `assert_file_no_egress`.

> **Correction, and it is the same defect this document keeps recording.** An earlier revision quoted `assert_does_not_import(CORE, NO_EGRESS, {"web", "serve", "willow_bridge"})` as live practice. That exact call exists **only in the docstring example inside `safe_app_common/no_egress.py`** — no app invokes it that way. `private-ledger` splits it into three single-element calls; `oakenscrolls-office` makes one, naming only `willow_bridge`. The three-seam set is aspirational documentation, and this document cited it as an enforced assertion after spending several sections warning against exactly that.
>
> **How widely the discipline actually applies:** seven files across thirty-six repos carry any structural declaration at all — `assert_does_not_import`, `assert_file_no_egress`, `NO_EGRESS`, or `_EGRESS_ALLOWED`. Three of the twenty-seven apps in `safe-app-store` have a `test_no_egress.py`. **VERIFIED 2026-07-30** at `b1825f7` — exactly three: `oakenscrolls-office`, `private-ledger`, `marching-arts`. Every bridge in `willow-2.0`, `willow-mcp`, `safe-app-willow-grove`, and `willow-bot` is undeclared, because **those repos have no purity checker of any kind.** The core/seam discipline is real and it is confined to the `safe-app-common` sub-fleet: private-ledger, oakenscrolls-office, marching-arts, UTETY, subject-consent. Inheriting it is a choice terpsi-music makes explicitly, not a property of being in the fleet.

### The import checker has a filesystem-shaped blind spot

`assert_file_no_egress` proves a module cannot open a socket. **It proves nothing about what that module writes, or where.** Both `willow_bridge.py` implementations write to `~/.willow/signals/*.json` — outside the app's own vault root, into a directory another process reads. That is a cross-app data handoff the AST scan cannot see, because it is not an import.

For this domain that is the gap that matters most. A commentary transcript or a roster export dropped into a shared directory has left the app just as surely as if it had been POSTed, and every guarantee in §6 is silent about it. So the rule needs a second half: **an outward module declares the paths it writes as well as the modules it imports**, and anything outside the app's own store root is an egress event subject to §7.2's export gating.

One more hole worth closing while here. The shared checker treats `subprocess` as egress and says why — *"an out-of-process shell is egress by another door."* Three of the fleet's bridges use it (`openclaw_discord_bridge.py`, `willow-bot`'s `fleet_bridge.py`, `node9_policy_bridge.py`) and **none of them sits in a repo that runs the checker.** The rule is right and unenforced where it would bite.

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

That second bullet is not hypothetical. `willow-config` **is** `~/.willow`, version-controlled and pushed — and `mcp_apps/`, the manifest ACL that grants `task_net`, is tracked inside it.

**The sandbox half of that concern is already closed, and this document previously overstated it.** `kart-sandbox.json` binds `{{HOME}}/.willow` read-write, then lays a read-only bind back over the trust root specifically:

> `$WILLOW_HOME/mcp_apps` (willow-mcp gate ACLs + `_identity_bindings`) is ro-bound over the fleet-home rw mount inside bwrap so Kart tasks cannot rewrite manifests or mint confirmed OAuth bindings (FRANK baf2f63a / #777). Host stdio/serve still writes via process outside the sandbox.

So a sandboxed task cannot rewrite a manifest or mint an identity binding, and the "repos are bound read-write into task sandboxes" objection does not apply here as written. What remains is narrower and still real for a school install:

- The authorization surface is in **git, on a remote** — restorable by anyone who can `git checkout`, and mirrored off the box.
- The **host process outside the sandbox still writes it**, which is willow-mcp's own B-32 residual, unchanged.

For a personal box both are manageable. For a hub holding education records, keep the grants out of version control regardless of the sandbox binding — the bwrap layer protects against a task, not against a checkout, a clone, or a restore.

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

**That mapping is written, and it is `docs/SENSITIVITY.md`** — which is canonical for what the five rungs mean, for all eight classes' rungs, and for the sensitivity→trust crossing. This section is not to restate it; where the two disagree, that document wins and this one is the defect (§16). Note in particular that no class maps to `L5`: that rung is reached per record, under three rules stated there.

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
- **`privacy_tier` in a SAFE manifest is not a validated invariant, so this app needs its own check.** Across the store, `"privacy_tier": "client_only"` coexists with `"permissions": ["cloud_llm_free", …]`, and several apps declare `client_only` alongside `"local_processing": 0.96` — the manifest conceding four percent is not local while the tier claims otherwise. Nothing rejects the combination. terpsi-music must ship a test that **fails the build** if any cloud or network permission appears in its own manifest, because the vocabulary will not enforce it.
- **The existing fallback chain must be disabled, not merely unused.** `willow-seed` documents a "free fleet fallback": when local Ollama is unavailable, inference routes to Groq → Cerebras → SambaNova on keys from `credentials.json`. That is a sensible default for a personal box and a **silent FERPA disclosure** on a school hub — it fires exactly when the local model is down, which is when nobody is watching, and it produces no error. A rule that says *local models only* is satisfied by a running Ollama and defeated by a stopped one. Remove the fallback keys, assert their absence in install acceptance, and let local inference **fail loudly** instead of degrading to a third party.

  There is a second instance, and it is committed to a public repo: `apps/semantic-translator/.mcp.json` sets **`"WILLOW_INFERENCE_PROVIDER": "auto"`** (alongside absolute `/home/<user>/…` paths, which is the fleet's own R15 violated in public). **An app holding student records cannot have an inference provider that selects itself.** Provider must be named explicitly, and `auto` must be rejected at startup rather than resolved at first call.

  > **Built 2026-07-31, and one clause of the paragraph above is weaker than what shipped.** *"Rejected at startup"* is a check on configuration, and configuration is the thing that was found to be bypassable four ways (`docs/FLEET-READS.md`, read again 2026-07-31). `records/inference.py` asserts instead on **what actually answered** — the `provider_used` half of the router's return, plus the address it answered at — so a variable nobody exported, a `mode=` passed at the call, and a provider label from a machine that is not this one all refuse. The variable stays an off-switch and is never the enforcement. Startup rejection is still worth doing when there is a startup; it is a second line, not this one. `tools/providers.py` is the half that watches for a call site skipping the guard, and it is wired into `tools/conform.py` as `local-inference`.
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
self             : Student:Ben     → Student:Ben           [capped at L3 until the threshold]
guardian_of      : Person:Ann      → Student:Ben
staff_of         : Person:Chris    → Ensemble:Drumline      [season-bounded]
director_of      : Person:Dana     → Program:Marching
judge_at         : Person:Erin     → Event:Regional_Oct12   [expires +36h]
clinician_for    : Person:Frank    → Session:Brass_Sep03    [expires +24h]
```

**`self` was added 2026-07-30 and the first five were the whole list until then** — which meant the subject was a stranger to their own lane. §18 item 12 records how that was found and what it cost to close; `records/standing.py` is canonical. Two properties of it belong here rather than there, because they are properties of *this* vocabulary:

- **It is capped, not equal.** Before W-6's threshold a `self` edge reaches `L3`; above that the subject is served the derived instruction unless a guardian signs a per-category widening. The cap lifts at the threshold by date comparison, which is the same predicate majority expiry already uses — no flag, no job.
- **`principal.purposes` is not read for a pre-threshold `self` edge.** W-4 is *a ward may request, never authorize*; a minor declaring a purpose over their own record is self-authorization, and honouring the declaration would defeat the clause with a keyword argument.

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

Note what that last row does: it classifies *save and commit* as exports rather than writes, and gates them accordingly. That is the read-versus-export principle expressed as a concrete permission table, in an app handling custody matters — the same population this design worries about in §7.1 and in §20 of the capability map. Judges and clinicians want the identical shape: read at the guest rung, commentary writes one rung up, export gated hard and announced.

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

### 7.3 `quiet-corner` is the known-bad precedent, and it is the closest sibling this app has

`quiet-corner` is a local-first K–12 student-records application by the same author — observations, standards, meetings, IEP status, behavioral notes. It is the nearest thing in the fleet to terpsi-music, and its central defect is precisely the one this design must not repeat.

Its config schema declares a **`session_scope`** with a per-field visibility vocabulary:

`roster_visible` · `attendance_visible` · `standards_visible` · `knowledge_graph_visible` · `iep_visible` · `behavior_visible` · `parent_contact_visible` · `archive_visible`

**Nothing enforces any of it.** The records view references none of those keys and loads every store unconditionally; IEP status renders as a decorative label. `docs/backend-architecture.md` states the gate exists — *"A 'session scope' preference system gates sensitive data visibility (IEPs, behavioral notes, etc.), implemented at the frontend request layer"* — and a frontend request layer is not an access control at all.

Two lessons, and they point opposite directions:

- **The vocabulary is good and worth taking.** Those eight fields are a well-chosen sensitivity partition for exactly this domain, arrived at by someone who has held the data. They map cleanly onto the L-ladder.
- **The enforcement location is the failure.** A scope that lives in the client is a preference. This is why §7's resolver compiles to one SQL predicate, and why §7.2's gate sits at the read: the same author, on the same kind of data, has already shipped the client-side version and documented it as though it were a control.

`quiet-corner`'s own `ROADMAP.md` states the gap without flinching — *"No accounts / auth. Data lives in one browser profile with no lock,"* called **"the most serious trust gap for a tool holding minors' records"** — and notes no written FERPA/COPPA posture exists, *"cheap to write now while the answer is simply 'nothing leaves the device.'"* There is no encryption at rest, and the documented backup path is a plaintext JSON export the guide suggests a teacher move by USB or **email to themselves**.

That last detail is the sharpest argument in this document for §11.1's exit line being a *designed* artifact. An export is going to exist. If nobody specifies it, it will be a plaintext blob of minors' records travelling by email.

And one more instance of the tracked pattern: the same roadmap asserts *"the app makes zero third-party requests at runtime and holds no data off-device"* while the data layer ships a complete REST client against `http://127.0.0.1:8432` behind a `USE_API` flag defaulting false, targeting a backend that does not exist in the repo. **A dormant network path is still a network path**, and in this design it is the seam that later becomes confidential transport (§4.2) — so it gets designed deliberately or not created.

**The fleet has already named this as its hardest open problem.** `corpus-lens` scopes itself to *owner == subject* — studying yourself — and says so explicitly: *pointing it at another person (a child, a partner, an employee) is a different consent object and is out of scope by design.* Its "named and deliberately unbuilt" list puts it plainly:

> The guardian-consent model (owner ≠ subject) — **the biggest gap between this toolkit and any family-facing instrument**; not solved, so not shipped.

Every persona in this document is owner ≠ subject. A school holds records *about* minors; a director reads data they are not the subject of; a guardian consents on behalf of someone else. `marching-arts` P2 is the fleet's first real attempt at that model — guardianship edges, consent never requested by its beneficiary, expiry at majority. **This app is where that gap either gets closed or gets shipped unsolved**, and §7.1's dated termination is the part of it still missing.

A sweep of the rest of the fleet confirms there is nothing to inherit. The coded consent model is the SAFE manifest's `data_streams`, whose retention vocabulary has exactly **two values — `session` and `permanent`** — and **no dated or revocable consent exists anywhere in the fleet.** The only staged model the author has written lives in a lesson plan, not in code: `DispatchesFromReality` distinguishes *legal* consent (clicking "I Agree") from *informed* consent, and walks six lifecycle checkpoints — Creation, Indexing, Monetization, Scraping, Training, Deployment — under the question **"At which stage should you have been asked?"**, with three audit questions: *Who knows this is happening? Who agreed to it? Who benefits?*

Those are the right questions and they are the right shape — a consent with stages and a time axis.

**Correction: there is a precedent, and this document asserted three times that there was not.** It is not in code, which is why a code sweep missed it. `Willow` — the constitution seat — carries `PROTECTED_AGENTS.md`, *"Powers Over Agents,"* Draft 0.6, unratified: a charter fragment whose subject is authority itself, with guardianship treated as *"the maximal one, not the only one."* Its **Part III — The Ward Case** is the doctrine §7.1 was proposing to invent. §7.4 adopts it.

### 7.4 The Ward Case, adopted

`PROTECTED_AGENTS.md` Part III states seven clauses that govern any office over an agent who holds no keys of their own. Every student in this system is such an agent. The clauses are quoted in their machine register; the human register the fragment also carries is worth reading beside them, because *"a clause that cannot survive translation between the two registers is not yet a clause."*

| | Clause | What it requires here |
|---|---|---|
| **W-1** | *A lane, not an account* — separate storage, permissions and audit trail **from the steward's first act**, no shared "family" partition | #115's per-subject partitioning, but from the first write rather than retrofitted when erasure is requested |
| **W-2** | *Grants name one ward* — *"'The children' is not a scope; a name is."* Wildcard and group scopes **invalid at issuance** | No grant over "the drumline," "the freshmen," or "the roster." Section-level convenience grants are void |
| **W-3** | *Lanes are mutually sealed* — default deny between wards; **"a shared event is two lane entries with one referent"** | Two students at one rehearsal is two records. This is a schema rule, and retrofitting it is a migration |
| **W-4** | *A ward may request, never authorize* | Already enforced by trigger in P2 |
| **W-5** | *Agency grows by signature, never by drift* — *"the steward may propose a widening, citing the record; it may never enact one. A clean track record is evidence for a proposal, never a grant in itself"* | A student's good attendance never widens their own access. The system may surface the case; a guardian signs it |
| **W-6** | *The exit transfers the lane whole* — keys issue to the subject at the threshold, **full history intact**; *"a lane opened without a written exit is invalidly opened"* | Graduation is not a retention policy. It is handing a student their own record with the keys |
| **W-7** | *Conflicts stop* — where two wards' interests collide, or a ward's against the guardian's convenience, the steward **halts and escalates, "never computes a priority"** | No automated tie-break between students. Chair placement, travel rooming, limited trip slots — the system presents, a human decides |

Three of the general invariants bear directly and were not in this document:

- **I-7 — the record binds the holder most.** *"Entries authored by the governed about the office are as durable as entries authored by the office about the governed."* A student's account of an incident is as durable as a staff member's account of the student. No office's force extends to deleting entries about its own exercise.
- **I-6 — every ask gets an answer.** *"Silence is not a disposition."* Every request — a fee waiver, an absence, a records inspection — carries a declared timebound and auto-escalates to the office's basis if unanswered, with the wait itself recorded. And the office **cannot lengthen its own timebound**.
- **I-10 — crossings run on treaty.** Imports *"enter at the lowest confidence tier and are corroborated before they bear weight"*; exports are treaty-scoped, drawn from verified-tier records only, and *"the seam is not a side door."* That is the doctrine for the SIS import and the circuit submission alike, and it maps onto §15's `P`-ladder and §16's seal state without translation.

**And the no-apex clause settles §4's district question.** *"Every root is someone else's governed… A charter that stops at its own keyholder has not described authority; it has described a ceiling with weather above it."* The director is root within the program and an agent under the district, the state, and FERPA. That is not a caveat to the trust model; it is part of it.

**W-6 is also the reason §11.1's exit line is not enough on its own.** A program-level export answers *what happens when the organisation leaves the software*. W-6 answers *what happens when a student leaves the organisation* — and requires the second, at the threshold, with history intact and keys transferred. A system that can export a whole program but cannot hand one graduate their own past has satisfied the smaller obligation and missed the larger one.

## 8. Domain model

Sketch, not schema — **and the lane half is now schema.** `docs/LANE-MODEL.md`
and `migrations/001_lanes.sql` are canonical for `Lane`, `Person`,
the referent, the entitlement edges, and the grant table; this section is not
to restate their fields (§16). What follows stays a sketch for everything the
proposed migration does not reach — inventory, money, ops, performance, comms.

- **Org** → **Program** → **Ensemble** → **Season** → **Event**
- **Lane** — per §7.4 W-1/W-3, the unit of storage and audit is one ward's lane, created at first write and sealed against sibling lanes by default. **A shared event is two lane entries with one referent** — a rehearsal attended by 150 students is 150 entries against one `Rehearsal`, not one row with a roster column. Retrofitting this is a migration, so it is a schema decision rather than a modelling preference.
- **Person** (+ `Student` / `Guardian` / `Staff` / `Guest` facets — one human, many roles, never duplicated rows). **Reconciling the same human across sources is `Nestor`'s `EntityResolver`, already built** — its shipped example maps `Amazon` / `Amazon.com Inc` / `AMZN` / `AWS` onto one canonical entity behind a human seal. Substitute a student arriving as *Robert Smith* from the SIS, *Bobby Smith* on a booster spreadsheet, and *R. Smith* on a competition registration. A confident match returns the canonical record with the sealer's provenance; anything below threshold comes back as an **unsealed suggestion**, never a silent merge — the correct default when a wrong merge combines two children's records.
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

**There is a transplantable model for this already.** `story-timeline` uses record types `timeline`, `timeline_entry`, and a first-class **`provenance`** record, with a relation vocabulary including `derived_from`, `appears_on_timeline`, `supports_scene`, and — the one worth taking verbatim — **`contradicts_or_tensions_with`**. Three judges disagreeing about the same passage is that relation exactly, and it is the structure that makes a disagreement queryable instead of a reader's impression. What the model lacks is time-coding: its entries carry no timestamps, so score-position anchoring (§8.1) is the piece terpsi-music adds rather than inherits.

**Rubrics, captions, ratings, and scores are projections over commentary**, not parallel structures beside it. Caption scoring is structured judgment; the festival tape is unstructured judgment; both are assessment attached to a moment in a performance. Modeled this way, a symphonic festival is a *configuration* — a different rubric, ratings instead of caption numbers, more talking and fewer digits — rather than a second application. Marching, indoor, and concert festival all fall out of one model.

What this unlocks, none of which the tape could do: deliver each section only the remarks touching their parts; scrub to a comment and hear the ensemble at that instant; diff the same passage across judges who disagreed; and — the genuinely new one — query every comment about brass balance across a full season to see whether the thing you have been fixing since September is actually moving.

### 8.2 Commentary processing runs locally, without exception

A recording of a judge's voice over a performance by identifiable minors is `MEDIA_MINOR` twice over. **Alignment, diarization, and transcription all run in Zone A on the hub.** Sending this audio to a hosted transcription API would make the entire privacy posture theater — it is the single most sensitive artifact the system produces and the most tempting one to hand to a convenient cloud endpoint. Local speech models are now good enough that this is a real option rather than a compromise.

Pipeline, entirely inside the trust boundary: ingest judge audio and performance audio → align → diarize → transcribe → anchor to score position → index. Transcripts inherit the classification of their source audio; nothing about "it's only text now" declassifies it.

**And a transcript is a `draft`, not a record.** This document previously described the pipeline without saying what its output *is* in trust terms, which left a machine transcription of a human's words looking like the human's words. `Nestor`'s cascade supplies the missing state (§16):

| State | For commentary |
|---|---|
| `draft` | The transcription, as produced. Queued, usable for search and routing, **never rendered as what the judge said.** |
| `sealed` | The judge confirmed this text. Served verbatim thereafter, carrying their name. |
| `pending` | Alignment or transcription produced nothing usable — said plainly, not guessed at. |

The consequences are practical. A caption comment routed into a student's practice queue (§1 of the capability map) should carry its state, because *"the low brass was late at 112"* attributed to a named adjudicator is a different object from an ASR guess at those words. A `draft` can inform; only a `sealed` remark should be quoted back to a student or shown to a parent.

Sealing also has a natural moment: the commentary grace period after an event (§4) is exactly when a judge could confirm their own transcript, while they still remember the performance. That turns a review chore into the thing that makes their commentary durable and attributable — and it is the only point at which the person who said the words is still available to confirm them.

**Rejection matters here more than sealing.** `reject_match` — *this correct remark is attached to the wrong passage* — is the common adjudication error, and it must not destroy the remark. That distinction is already built.

---

## 9. Phasing

The ordering principle: build the things that are expensive to retrofit first, regardless of which module ships first.

**Foundation — hard to add later, so add it now**
1. Person / relationship graph with time-boxed edges (§7) — ~~**built** (P1/P2)~~ ~~**spike-evidenced, not built**~~ **the enforcement half is built, 2026-07-31.** (§18 item 2, 2026-07-30: P1/P2 is `marching-arts`, which was a spike and retires. Nothing of it is inherited, so this was **to build**, less nothing — including the dated-guardianship gap in §7.1.) What exists now: the dated `Edge` with both clocks on both events, `records/orders.py`'s order-based ending, and the three predicates over the acting principal that `LANE-MODEL.md` had listed as stated-and-unenforced. What does **not** exist and is deliberately named: there is no store, so every predicate takes the rows from its caller and the store-side compilation of the same predicate (§7's resolver shape, #127's authenticate-at-the-read) is still to write
2. Data classification on every field (§6) — ~~the L-ladder is **built**~~ ~~the L-ladder is **decided and unbuilt**~~ **status: decided, enforced twice, and reconciled** (2026-07-31). `docs/SENSITIVITY.md` stays canonical for the five rungs, *Protected status*, and the scoped `L3`+ NULL reading (§18 items 1, 1a, 11). What is retired is the second half of this line — ~~the class-to-L mapping is **written but unenforced**, and enforcement is the work~~ — because enforcement then landed **twice, independently**: `records/rungs.py` and `records/classify.py` run the five-step procedure and return `UNDECIDED` where the clause needs a human, and `migrations/001_lanes.sql` seeds `field_classification` with a class and a rung for every column its DDL declares. Two implementations of one mapping with nothing between them is the pair §16 forbids, so **the successor to this item is the middle: `tools/registry.py`**, which parses the seed as text, asks `records/classify.py` what the same field derives, and holds both against this document's class table. It is enforcement rather than a ledger because CI routes through it — `tools/conform.py`'s `classification-registry` row, and `tests/test_registry.py`, which also points it at a drifted registry and requires it to complain. Counts derived by running it over the tree on 2026-07-31: **116 fields**, 106 agreeing outright, 7 elevated to `L5` by a recorded rule (`declination`'s six columns and `consent_chain.disposition`, all under `SENSITIVITY.md`'s `L5` rule 3), and **3 undecided** — `reconciled_session.declared`, `.observed` and `.diff` are seeded `L4` where `PII_MINOR` derives `L3`, and no document records which rule reaches it. That is a finding, not a pass: the conformance row reads `UNKNOWN`, and the two candidate readings are set out in `tests/test_registry.py`
3. Envelope + key hierarchy, even while everything is still on one LAN (§5) — chain integrity and per-subject erasure are **built**; at-rest sealing across the Zone A boundary is not
4. Egress purity in the core (§6, inner ring) — **built**, AST-proven, and **unaffected by item 2**: the checker is `safe_app_common.no_egress`, a fleet library rather than anything in the spike. Note what "built" means here — it exists *in the fleet*, and §6 records that inheriting it "is a choice terpsi-music makes explicitly, not a property of being in the fleet." The outer broker is not built, and is only needed once something must legitimately talk to the world
5. Append-only audit log — the hash-chained disclosure log is **built**, with the count-anchor truncation defence

**Then, in whatever order the program's pain dictates**
6. First vertical module — `field-acoustics` is the first real capability
7. Parent PWA + the drop
8. Money, inventory, forms, calendar/attendance
9. Adjudication: commentary capture + anchoring, guest grants, local transcription pipeline
10. Aggregate exports for corporate
11. Local agent assistance behind the gate

**This app is also the template** (§17): what it lands in foundation 1–5 is what every later SAFE app inherits, so those five are built to be propagated rather than to be sufficient here.

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

**`willow-2.0/SECURITY_AUDIT.md` is a reusable acceptance rubric.** Fifteen numbered checks — SQL construction, shell injection, path traversal, credentials in version control, CORS, XSS, unsigned execution, MCP tool auth, exception swallowing, temp-file predictability, race conditions, manifest correctness, dependency pinning, hardcoded home paths — with findings carrying IDs, severity, and status. ~~Run it against this app before a school install, and treat the result as an install gate rather than a document.~~

> **Run 2026-07-31; `docs/SECURITY-AUDIT.md` is the result, and it is a gate.** All fifteen were applied to this tree by reading source rather than by citing the rubric. Counting the audit's own verdict column across all seventeen: seven pass, three carry findings, six are `NOT-APPLICABLE` and one is `ABSENT` — each of the last seven with the condition that ends that state written beside it, because a check that cannot apply yet is not a check that passed (rule 13). Four findings were closed in the same commit — counted from the audit's findings table, which `tests/test_audit.py` re-derives: a check-then-act ablation lock that could be held twice, a fixed sidecar name under `gettempdir()` that a symlink could redirect, the conformance record's append-only rule (check-then-act as well), and a `.gitignore` that did not exclude the trust root refusal 2 forbids committing. One stays open at `S3` — the stdlib-only posture is asserted in the docstrings and nothing checks it. **The severity scale is re-lettered `S0`–`S3` rather than the fleet's `P0`–`P2`**, because `P1`–`P5` is provenance here (§15) and one prefix carrying two scales is the collision rule 14 exists to stop; the crossing is stated in the audit. And this is enforcement rather than a ledger: `tools/conform.py`'s `security-audit` row parses that document — its date, its commit pin, its open findings — and **fails the build while anything at `S1` or above is open.** That row read `UNKNOWN` until this was done, on the honest ground that the rubric had never been run here.

**The rubric is missing the two checks this app needs most.** R1–R15 covers injection, traversal, credentials, CORS, XSS, unsigned execution, API auth, swallowed exceptions, temp paths, races, entry points, dependency pinning, and dev paths. It has **no check for encryption at rest** and **no check that an egress test exists**. Both are the point of this design, so the recommendation is concrete: add **R16 — data at rest is encrypted, with the key escrowed (§5)** and **R17 — a structural no-egress test exists and fails when neutralised (§6, §10)** to the fleet rubric rather than to a local fork of it.

> **Both are built here as checks, 2026-07-31 — `tools/audit.py`, ablated in `tests/ablate.py`, reconciled against the audit document by `tests/test_audit.py`.** The recommendation above is unchanged and unpaid: adding them to *this* repository only would create the vendored pair §16 records four failures of, so what is recorded in the audit is the recommendation plus a worked implementation to carry over. Editing another repository is not this repository's act, and it has not been done.
>
> **R16 reports `ABSENT`,** which is the honest answer and not a pass. There is no at-rest sealing seam in `records/` and nothing at rest to seal — `purity.writes()` over `records/` reports zero write sites — and no escrow disposition exists, which §5 already names as this design's largest gap. The check is written against the seam at-rest sealing will land on; the condition that ends `ABSENT` is the first commit in which anything under `records/` writes a record to a disk, and at that commit R16 becomes an open `S1` unless sealing and a dated escrow disposition arrive with it. **The false positive it is built to refuse is the interesting part:** `records/sealing.py` is in the tree and is *not* this — it is rule 10's named-human seal over a machine draft, `hashlib` and no cipher — so R16 recognises the seam by the verbs a sealing module exposes and never by its filename.
>
> **R17 reports `PASS`,** and only the second half of it was work. The egress test already existed. What R17 adds is the neutralisation half, read mechanically rather than believed: it parses the ablation registry for a mutation against each of the four ways `tools/purity.py` detects egress, and parses the newest conformance record for the `no-egress` and `ablation` rows. Coverage is required **per detection site, not per count** — a registry can grow without bound while one site stays quietly unablated, which is the state `records/sending.py` was in when one pattern matched two call sites and only the first was ever mutated.

It also carries the fleet's canonical fail-closed idiom, worth stating as house style: *fail at startup, not at request time. A missing secret is a hard configuration error.* `jeles-remote` implements exactly that — it *"refuses to start at all"* without its shared secret — so the idiom is real practice, not just a documented aspiration. Every gate in this document should behave that way: `SAP_PGP_FINGERPRINT` unpinned (§7.2), `WILLOW_INFERENCE_PROVIDER` set to `auto` (§6), and a manifest declaring a cloud permission should each refuse to start.

**The counter-pattern, from the same repo, is worth naming too.** A `jeles-remote` source missing its API key *"silently returns no results; nothing else breaks."* That is convenient and it is the same failure family as §7's indistinguishability caveat and §15's decaying `P2`: **an absence rendered as a negative answer.** A caller cannot distinguish *this source found nothing* from *this source was never asked*. In a program context the equivalents are unforgiving — a rubric that did not load returning "no findings," a consent backend that failed open returning "no restrictions," an eligibility check that could not reach the SIS returning "eligible." Wherever a component can be absent, the absence must be reported as *unknown*, never as a result.

**Add a line the rubric does not have: the verification apparatus was itself verified.** `willow-mcp` #211 reports that across three merged PRs in one session, **six defects were found in the verification apparatus and zero in the code under verification** — a differential reference generated before the thing it checked changed; a fixture writing a hash chain with the same function it read it back with, so a rename was invisible *and self-consistent*; a fixture that could not fail; a killed mutation harness that left a mutation in the tree and turned every subsequent number into fiction; three mutations that renamed a SQL trigger rather than disabling it, so it kept firing under the new name; and counts in prose that nothing checks.

**The charter already requires this, in stronger terms.** `PROTECTED_AGENTS.md` I-12 — the eternity clause — states: *"Compliance requires at least one adversarial test per clause: a test that attempts the forbidden act and asserts refusal."* So mutation is not a local rule this document invented for acceptance; it is the fragment's own definition of what compliance means. Every ward clause in §7.4 and every invariant it cites needs a test that tries the forbidden thing and asserts the refusal.

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

**And this obligation has a second, smaller scale that matters more.** W-6 (§7.4) requires that a ward's lane transfer *whole* at the threshold written in at entry — *"keys to the lane issue to its subject or named successor, full history intact."* A program-level export answers what happens when the organisation leaves the software. W-6 answers what happens when **a student leaves the organisation**, and it is the harder of the two: it must run every June, per graduate, unattended, and hand over a record the recipient can read without this application. *"A lane opened without a written exit is invalidly opened"* — so the graduate's export is not an end-of-life feature. It is a precondition of enrolling them.

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
14. **The Ward Case governs** (§7.4) — one lane per student from the first write, no group grants, sealed sibling lanes, agency widened only by signature, conflicts escalated never computed, and the lane handed over whole at the exit.
15. **A machine answer is a draft until a named human seals it** (§16, §8.2) — and rejection is recorded as durably as approval, because an audit trail that records only agreement is not one.
16. **Every pair gets a named, mutation-tested middle** (§16) — the fleet builds in halves, and every failure in this document is a reconciler that was absent, mis-aimed, or unable to fire.

## 13. Open questions

- **Whose consent is it?** This was filed as "the auth model is scoped to a single process," which misread it. #127's memory-only signing key is not a limitation working around the absence of a server — it is SAFE's thesis: *Session-Authorized, Fully Explicit*, consent expiring with the session, the app asking again tomorrow. Tokens dying with the process is the framework behaving correctly. The real question is narrower and harder: **SAFE's model is a data subject authorizing access to their own data, and this domain is an institution holding records about minors.** A parent viewing their student's balance fits the session model cleanly. A director opening the roster at 6 a.m. is not the data subject and cannot be asked to re-consent on the students' behalf every morning; the consent that governs them is the guardian's, granted elsewhere and enforced by predicate. Both mechanisms are built. What is not written down is which one governs which surface, and a system that guesses will eventually ask the wrong person.
- **Does a 200-household deployment change the session model's shape?** Not its principle — its ergonomics. Re-authorizing per stream per session is right; re-authorizing eight streams every morning before seeing a schedule change is how a family stops opening the app.
- **Does `rationale` (#125) generalize into the disclosure story?** It ships the reasoning beside the data, gated by a human seal rather than a predicate, with `draft | internal | shipped` states. FERPA §99.32 wants a disclosure record and §6 assumes the egress log supplies it — but "why were you refused" is a `rationale` question, not an egress-log question. The two may want to meet.
- The current build targets caption scoring. Does its model treat captions as projections over anchored commentary (§8.1), or as the base structure? If the latter, that is the one thing worth revisiting early — festival ratings and clinician feedback both fall out for free under the former.
- Score-position anchoring: align audio against a stored score, or judge-driven tap-to-mark, or both? Affects how much of the music library must be machine-readable.
- **Can `field-acoustics` and commentary share coordinates?** A judge's remark is anchored to a moment and a seat; the acoustic model predicts what arrived at that seat. Pairing them gives a claim no drill designer can currently make — and gives the model's `ASSUMED` rear hemisphere a source of validation data that would otherwise have to be measured in the field.
- **Adjudicator calibration, as this document proposed it, is a prohibited scope — corrected.** `PROTECTED_AGENTS.md` Schedule A lists **SA-3, standing cross-context scores**: *"any durable rating of an agent carried between contexts or offices; the durable form of compounded offices (I-4)."* An envelope naming a listed scope is **invalid even fully signed by root**, and the attempt is recorded as a failed issuance with the signatory named. A judge is an agent under the fragment's definitions, and a reliability curve carried across events is exactly that rating. This document hedged toward *"the judge, and no one else by default"*; the charter is harder — the program may not hold it at all. **What survives is the judge running their own ledger**, owner == subject, which is `corpus-lens`'s scoping and `oakenscrolls-office`'s actual design. The engine is unchanged; the ownership is not the program's to choose. Original note retained below for the reasoning, not the conclusion.
- ~~**Should adjudicators be calibrated?**~~ `oakenscrolls-office` is a working calibration ledger — state a claim with confidence, grade it when the world weighs in, and a reliability diagram shows whether your 70% means 70%, scored by Brier and log loss, append-only so a revised number never erases the original. Point that engine at adjudication and the question becomes: does this judge's caption score predict placement, and are they consistently high, low, or noisy against the panel? That is a real capability with an existing implementation, and also the most politically delicate feature in this entire document — a circuit may want it badly and individual judges may not. Decide who may see a judge's own reliability curve before building it, because the answer is probably *the judge, and no one else by default*. Note the same repo's citation pattern is directly reusable: resolution evidence pinned to a source *and the git commit of the catalog that vouched for it*, read from local clones with no network.
- **Does the practice loop violate a fleet ground rule?** UTETY's ground rule 2 is *feedback is about the work, never the learner* — no praise of the person, no leaderboards — with a policy test linting content against self-directed praise. The capability map proposes practice streaks, cumulative-hour milestones, and chair-challenge standings. Some of that is about the work and survives; some of it is a leaderboard with a different name. Reconcile before building, because the rule is enforced by test in a sibling app and this would be the second student-facing app in the fleet.

---

## 14. Fleet components this maps onto

Written after reading the READMEs of the components below; contents inferred from those, not from source.

> **Every row claiming existence now says whether anyone looked (2026-07-30).**
> §18 item 0's complaint was that *"an unverified table and a verified one look
> identical"*, and §9's phasing rests on this column. So each such row carries
> exactly one of:
>
> - **`VERIFIED <date> at `<commit>`** — the source was opened in a clone at that
>   commit. The date and the pin are both required: *"we checked it once"* decays
>   the way §15 says a `P2` claim decays, and a pin makes the check re-runnable
>   by someone who doubts it.
> - **`UNVERIFIED`** — nobody has opened it. This is the honest state of most of
>   the table and is not a defect; it is the thing that used to be invisible.
>
> **VERIFIED-COUNT: 11 of 41** (2026-07-31). `tests/test_component_map.py`
> enforces the convention — a row claiming existence with neither token fails the
> build, as does a `VERIFIED` without a commit. It deliberately does **not**
> assert a coverage ratio, because a test that demanded more green would be an
> incentive to mark things verified rather than to read them.
>
> **The figure above is derived and enforced, after drifting once.** This line
> read *"8 of 40"* while the table held ten verified rows and a pull request
> body quoted ten — a figure in prose the code moved past, which is the exact
> defect §18 item 0 exists to name, sitting inside the note that exists to fix
> it. The machine-readable `VERIFIED-COUNT:` marker is now compared against the
> parser's own tally by `test_the_header_figure_matches_the_table`, so the
> sentence cannot drift from the rows again. Rule 18: this paragraph used to be
> a ledger and is now a gate.
>
> The shape is taken from `kartikeya.resolve_sandbox_config`, which solved the
> identical problem for sandbox policy — *return the value with the source that
> supplied it* — reduced to what a markdown table can carry. See
> `docs/FLEET-READS.md`.

| This document | Component | Status |
|---|---|---|
| §5 the box / Zone A | `willow-data-vault` | **VERIFIED 2026-07-30** at `b634de0` — three-layer architecture and `vault.key`/Fernet confirmed; nine files, schema and bootstrap only, *"never data"*. **Exists** as a blueprint; there is no at-rest sealing implementation in it, consistent with §9's foundation 3 |
| §5 at-rest sealing of *records* | — | **Open.** The vault seals secrets; collection stores are not described as encrypted |
| §5 escrow | — | **Open, and the largest gap.** Single-file key loss is unrecoverable by design |
| §6 core purity | `safe-app-common.no_egress` | **VERIFIED 2026-07-30** at `2b3d088` — `src/safe_app_common/no_egress.py` present with `tests/test_no_egress_checker.py` beside it. **Exists**, canonical, with the core/seam partition this document lacked |
| §6 the un-passable seam | UTETY `knowledge.py` | **Exists** as a proven pattern in a student-data app · `UNVERIFIED` |
| §6 perimeter | `willow-gate` | **Exists**, as an agent trust gate rather than a network broker · `UNVERIFIED` |
| §7.2 session reconciliation (the knock) | `willow-gate` | **Exists.** 13 fields in, 13 out, diffed; bound trust; louder for the least trusted; budgets tighten as trust rises · `UNVERIFIED` |
| §7.2 guest sessions reconciled | `law-gazelle` | **Exists as a worked example** in a comparable domain — gate in enforcement mode, trust ladder mapped to operations, save/commit classed as exports, refuses to start if misconfigured · `UNVERIFIED` |
| §5 canonical vs sidecar | `law-gazelle`, `nest-seed` | **Convention, stated twice.** Canonical store read-only to the app; agent write path is sidecar only |
| §5.1 compute isolation | `kartikeya` | **Exists.** Bubblewrap, network-isolated by default, credentials only to net-enabled tasks, cgroup/prlimit caps · `UNVERIFIED` |
| §6 verified answers before inference | `jeles` | **Exists.** Nuggets with sources and a named verifier, in front of search; gaps logged local-first · `UNVERIFIED` |
| Library digitization | `nest-seed` | **Exists.** Regex → local embeddings → generative only on the ambiguous tail, degrading gracefully · `UNVERIFIED` |
| Question banks / assessment | `civics-check` | **Exists as a pattern.** Authoritative sources compiled to a catalog; never hand-edit the output · `UNVERIFIED` |
| Consent-scoped activity capture | `ask-jeles` learning events | **Exists.** Off by default every launch, never persisted across launches, records shape not content · `UNVERIFIED` |
| Mirror detection near high-stakes decisions | `willow_gate.friction_floor` | **Exists.** Flags for a human, never blocks, runs outside the watched model · `UNVERIFIED` |
| §6 destination allowlist | — | **Open**, and smaller than this document implied |
| §7 authorization + consent | ~~`marching-arts` P1/P2~~ (spike, retires — §18 item 2), `libs/subject-consent` | ~~**Exists**~~ **Spike-evidenced; both paths VERIFIED present 2026-07-30** at `b1825f7`. Nothing inherited; `libs/subject-consent` is the only live source and its placement is item 8. The spike's band scale is **not** this document's L-ladder — see `FLEET-READS.md` · `UNVERIFIED` |
| §7.1 dated guardianship | `willow-2.0` `valid_at`/`invalid_at` | **VERIFIED 2026-07-30** at `4147013` — 17 tables counted from `migrations/20260522_bitemporal_all_tables.sql`, append-only audit excluded by name. **Mechanism exists**; ~~binding guardianship to it does not~~ **bound 2026-07-31** — `records/orders.py` is the act: an order sets `invalid_at` from its own date, records itself as the authority, carries a second knowledge clock for the *ending*, and is refused if it would leave the lane with no live guardian and no named state. Note the source carries **no interval-ordering CHECK**; `001_lanes.proposed.sql` adds ten |
| §7.4 guardianship doctrine | `Willow` `PROTECTED_AGENTS.md` Part III | **VERIFIED 2026-07-30** at `c8c96b4` — read at source, all seven clauses present and faithfully rendered in §7.4. **Exists as charter, unratified.** Seven ward clauses plus twelve invariants; this document had asserted three times there was no precedent |
| Prohibited scopes registry | `Willow` Schedule A (SA-1…SA-5) | **Drafted, unratified.** Validated before any envelope issues; `envelopes/pre-approved.json` is the enforcement surface |
| Stakes classification | `Willow` Schedule B (SB-1…SB-5) | **Drafted.** A music program touches four of the five classes |
| Retirement artifact | `Willow` `PROTECTED_PERSONS.md` | **Exists as a model.** The five-part tombstone that would have prevented the dead-link tally · `UNVERIFIED` |
| Shared-edge placement | `Nestor` → `Die-Namic-Systems`, sole occupant | **Decided, and unexecuted — checked 2026-07-30.** The repository is at `rudi193-cmd/nestor`; §17's prose is future tense. The decision stands; the move has not happened, and this row read as a statement about the tree would be wrong |
| Second shared edge | `libs/subject-consent` | **Unresolved.** Same property as Nestor, still a folder in an app store, already vendored once |
| Per-graduate lane export (W-6) | — | **Open**, and a precondition of enrolment rather than an end-of-life feature |
| §10 privacy notice | `willow-2.0/TRUST.md` | **Reusable structure** — every path data can take, each with its switch |
| Install acceptance gate | `willow-2.0/SECURITY_AUDIT.md` | **Reusable rubric**, 15 checks. W-MCP-01's trigger condition applies here |
| Verifying the verifier | `willow-mcp` #211 | **Open.** Six apparatus defects to zero code defects across three PRs; no mutation gate exists for this app's guarantees yet · `UNVERIFIED` |
| Allow-side coverage of the resolver | — | **Unknown.** Indistinguishability passes even if the predicate returns nothing to anyone; check the fixture has a principal who can see something |
| §10 COPPA / under-13 | SAFE `HARD_STOPS`, UTETY ground rule 4 | **Exists** as governance, above app level · `UNVERIFIED` |
| §8.1 commentary primitive | — | **Open** |
| §1–§2 practice + mastery | UTETY (BKT, item sets, on-device store) | **Adjacent.** Different subject matter, same shape — worth reading before rebuilding |
| Assistant surface | `safe-app-store` `apps/jarvis` | **Considered 2026-07-31, excluded by refusal 1 — recorded rather than forgotten.** **Exists**; VERIFIED 2026-07-31 at `a8bc2c5` — README and manifest read; src not audited. A browser-tab voice assistant: vendored cloud-SDK inference behind a pasted key, which is the exact posture refusal 1 keeps away from a lane. It enters this app only if rebuilt against the local-model rule; it is never linked. What ports is the idea, not the code: memory as a *queried* predicate store — compound indices, a `live` flag, retrieval as an index range rather than a scan — the right shape for any assistant surface here. The maintainer knows this app well; that familiarity is a resource, and this row is where it points |
| Library vs. learner split | UTETY ↔ Jeles | **Settled pattern.** UTETY holds the learner, Jeles holds the sources — the repertoire library may want the same seam |
| §6 kill switch | `consent.internet` | **Exists** · `UNVERIFIED` |
| §6 three-key egress + envelope | `willow-mcp` | **VERIFIED 2026-07-30** at `3815449` — `confirm-binding` carries *"Do not wire this into an `@mcp.tool()`"*; `compute_email_basis` returns all four values and drift is surfaced, not applied. **Exists**, stronger than proposed |
| §6 outbound scanning | the redaction funnel | **Exists for credentials.** Needs the student-identifier classes · `UNVERIFIED` |
| §3 hardening | `WILLOW_MCP_STRICT_TRUST_ROOT`, severance | **Exists, off by default.** Mandatory here — see §6 residual · `UNVERIFIED` |
| §4 staff remote access | `willow-mcp` serve mode (OAuth + confirmed binding) | **Exists** · `UNVERIFIED` |
| §4.1 parent notification + acknowledgment (~95%) | SMS, ideally a local SIM gateway | **Open, but small.** No app, no enrollment, no inbound; constrained by carrier throughput, not cost |
| §4.2 the transactional relay (~5%) | — | **Open.** Grove's u2u is signed, *not* confidential — reusable identity, missing confidentiality |
| Criteria for a justified hosted component | `jeles-remote` | **Exists as precedent.** Stateless, scales to zero, corpus absent rather than gated, refuses to start unconfigured · `UNVERIFIED` |
| §7 finance module | `private-ledger` | **Exists as a template**, with the injected-`ingest` bridge pattern · `UNVERIFIED` |
| §10 / §17 aggregate exports | `nest_promote`, `nest_digest` | **Exists as a pattern.** Promote *structure* — counts, categories, never content; the full digest is local-CLI only, never returned over MCP · `UNVERIFIED` |
| Guardianship / family graph | `the-squirrel` | **Adjacent**, though it serves a web port rather than staying import-pure |
| Judge calibration | `oakenscrolls-office` | **Exists as an engine** — see §13 and §15 · `UNVERIFIED` |
| §15 `P1–P5` provenance | `field-acoustics` (3 rungs), evidence tiers, `jeles`, `oakenscrolls-office` | **Partial and divergent.** Four vocabularies, no mapping; the `Cited` and `Estimated` rungs have nowhere to sit today |
| §15 scale-direction convention | — | **Open.** `T0–T4` and `L1–L5` already oppose; no prefix rule or mapping table exists yet · `UNVERIFIED` |
| §11.1 exit plan | `awesome-sovereign-software` | **Criterion exists**, five-point test plus a required exit line. No exit line written for this app yet · `UNVERIFIED` |
| Owner ≠ subject consent | `corpus-lens` (names it unsolved), `marching-arts` P2 | **The fleet's stated hardest gap.** This app is where it closes or ships unsolved |
| §7.3 sensitivity field vocabulary | `quiet-corner` `session_scope` | **Vocabulary worth taking, enforcement is the known-bad precedent** — declared per-field, enforced nowhere |
| Dated / staged consent | `DispatchesFromReality` (prose only) | **No code anywhere in the fleet.** `data_streams` retention has two values; must be invented here |
| §8.1 commentary relations | `story-timeline` (`provenance`, `contradicts_or_tensions_with`) | **Transplantable**, minus time-coding |
| §8.2 trust state of a transcript | `Nestor` cascade (`sealed`/`draft`/`pending`) | **VERIFIED 2026-07-30** at `111c187` — all three states present. **Exists.** A transcription is a draft until the speaker seals it |
| §16 declaration vs enforcement, computed | `Nestor` `Curator.servable` / `unverifiable()` | **VERIFIED 2026-07-30** at `111c187` — `curator.py:82` and `:118`. **Exists.** The detector for this document's entire finding class |
| Roster identity reconciliation | `Nestor` `EntityResolver` | **Exists.** Sealed canonical mapping; sub-threshold returns a suggestion, never a silent merge · `UNVERIFIED` |
| Three-way finance reconciliation | `Nestor` `Reconciler` | **Exists.** Sealed baseline, tolerance band, flagged variation, ledgered · `UNVERIFIED` |
| §15 `P2` liveness sweep | `almanac-template` (`status` + `observed` + daily reachability job) | **Exists as a pattern**, files an issue when a source rots · `UNVERIFIED` |
| Export / publication boundary | `yggdrasil-training-data` | **VERIFIED 2026-07-30** at `c183222` — `route()` fails closed and unknown records are not written; the bypass is `if hint == "slm": dest = "slm"`, skipping `route()` for three of four source files. **Pattern exists**, fail-closed on unknown — but carries a trusted-source bypass not to reproduce |
| Cloud inference fallback | `willow-seed` (Groq/Cerebras/SambaNova) | **VERIFIED 2026-07-30** at `a9274e8`, **corrected same day**: `willow-seed` has *no code* for it; the live router is `willow-2.0/core/inference_router.py`, providers appear in 24 Python files, and an off-switch **does** exist — `WILLOW_INFERENCE_PROVIDER=local` yields Ollama only. **The default is `auto`**, so the rule is fail-open-when-unconfigured, which is what refusal 1 already forbids by name. `respond()` returns `(text, provider_used)`, so it is enforceable by assertion |
| Trust-root placement | `willow-config` + `kart-sandbox.json` | **Half closed.** `mcp_apps/` is ro-bound against sandboxed tasks; still in git, on a remote, and host-writable |
| Sandbox mount policy | `kart-sandbox.json` | **Exists**, versioned and data-driven — no-network tasks get zero credentials, sovereign data read-only, tmpfs `/tmp` · `UNVERIFIED` |
| Network-isolated local inference | — | **Open.** `allow_localhost` shares the host netns, so a `MEDIA_MINOR` task can reach the network uncredentialed |
| Contract + sandbox policy | `willow-config` (`willow.md`, `settings.global.json`, `kart-sandbox.json`) | **Exists.** These are the right things to version; the grants are not · `UNVERIFIED` |
| §15 rendering the scales | `safe-design` | **VERIFIED 2026-07-30** at `457cb7e` — three backends (`css`, `textual`, `curses`), and parity is **enforced** by `test_css_and_textual_agree_on_every_token`, not merely structural. **Exists.** Semantic tokens, lookup-time aliases, ASCII path |
| §5 exclusion of family data from the corpus | `willow-compose` | **Exists as stated policy.** This app is a family-data app by its definition · `UNVERIFIED` |
| Fifth authorization mechanism | `openclaw-sap-gate` (SAP/1.0) | **VERIFIED 2026-07-30** at `82d80d9` — and this row was **wrong**: the fingerprint default is ~~fail-open~~ **fail-closed** (`gate.py:102` *"unset ⇒ fail-closed deny"*, with `test_no_fingerprint_pinned_fails_closed`). The comment says fail-closed was *"preserved"*, so the claim may have been true of an earlier revision — §15's `P2` decay. **Exists**, four-step chain, revocation-by-deletion (which refusal 3 forbids) |
| Purity checking, fleet-wide | `safe-app-common` | **Confined.** 7 declaring files across 36 repos; 3 of 27 store apps have a purity test; four major repos have no checker |
| Write-path declaration | — | **Open fleet-wide**, and half closed here. §14's own sentence — *"the AST checker sees imports, not filesystem writes"* — was true of this repository's checker too until `tests/fixtures/decoys/` said so. `tools/purity.py` now scans by AST, recursively, mode-aware, with a read/write split so it does not cry wolf on every `open()`. The **declaration** half has nothing to compare against, so `conform.py` reports `UNKNOWN` |
| Allowlist rot-checking | UTETY `test_allowlist_entries_exist` | **Unique in the fleet.** A stale allowlist silently widens the door |
| §17 district / equity data | `almanac-data/education-almanac` | **Seeded, not worked.** One UNESCO entry. Five sibling verticals are worked and US-federal-heavy, so the pattern and the machinery both exist |
| §15 citation decay vocabulary | `almanac-template/schema/catalog-entry.schema.json` | **Solved, adopt wholesale.** Seven decay states, observed-vs-status separation, fingerprint drift, recovery authenticity ladder |

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

- **Never compare raw integers across scales.** A single mapping — which trust rung a given sensitivity requires — lives in one place, and every gate calls it. `law-gazelle`'s permission table (§7.2) is that mapping, written out. **For this app it lives in `docs/SENSITIVITY.md`**, in that table's shape, and it is a mapping rather than an enforcement until a harness routes reads through it.
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
>
> **That check exists in the fleet, and it is better than the one proposed above — adopt it wholesale.** `almanac-template`'s `catalog-entry.schema.json` is a worked solution to citation decay, and it makes distinctions this document had not:
>
> **Decay has seven states, not two.** `status` ∈ `live · revised · moved · redirected · superseded · dark · frozen`. A source that still resolves but stopped being updated (`frozen`) is a different claim from one that moved, one that was replaced (`superseded`), and one that is gone (`dark`). "Resolvable" was never the right binary — the climate vertical already carries a `frozen` entry alongside sixteen live ones.
>
> **Machine facts and interpretation are separated.** *`observed` records only machine facts; `status` derives interpretation from those facts* — and `status_source` ∈ `auto · curator` records which of the two set it. That is the same discipline as #128's correction trigger landing a `draft` stub because the database can see *that* something changed and cannot know *what was wrong*.
>
> **Drift is detected, not just reachability.** `observed.fingerprint_result` ∈ `match · drift · no-baseline`. A source that returns HTTP 200 with different content is caught, and `no-baseline` handles entries catalogued after the failure — the fingerprint *"captures baseline metrics while the resource was live"* and is deliberately absent otherwise. That is §5's emptied-is-not-absent rule, applied to citations.
>
> **Recovery has its own authenticity ladder**, ordered and separate from the measurement ladder above: `recovery.authenticity` ∈ `hash-verified · cross-archive · timestamped · asserted`, with the schema noting that recovery candidates are ranked *"by authenticity tier, never by authority or operator."* When a cited rubric or licensing term goes dark and you fall back to an archived copy, that copy's own trustworthiness is a separate axis from the original's — and `asserted` is the floor, which is `P5` by another name.
>
> A daily job probes every source and opens a GitHub issue when one goes dark (`scripts/check_links.py`, `link-check.yml`). Anything here citing an external authority — state standards, circuit rubrics, licensing terms, district calendars — should carry this shape rather than a URL, and be swept on the same cadence.
>
> The tally, meanwhile, keeps growing: beyond the SAP RFC and the canonical Grove repo, **fifteen further store manifests name a `repository` that does not exist** — `safe-app-private-ledger`, `safe-app-the-squirrel`, `safe-app-utety-chat`, `safe-app-ask-jeles`, and a dozen more. Eighteen-odd dead canonical links is not an accident rate; it is a missing sweep.

**Estimated** matters because extrapolating from a different ensemble at a different venue is a categorically different claim than fitting to this one — and in this domain that distinction is the difference between a defensible design decision and a guess wearing a number.

Propagates by `min`. A headline is its weakest input, and says so.

### Confidence is not a rung

`oakenscrolls-office`'s 50–99% is **continuous**, and it is a claim about the future graded against an outcome. That is what makes calibration possible at all; collapsing it into five ordinal rungs would destroy the only thing it is for.

`willow-2.0`'s evidence-tiers migration already has the right pattern — `tier` **and** `confidence` as two columns side by side, one ordinal and one continuous, neither pretending to be the other. Copy that shape: carry `provenance` and `confidence` together, and only populate `confidence` where a resolution mechanism actually exists to grade it against.

### And human verification is a third axis, not a rung

`Nestor`'s `sealed | draft | pending` (§16) is neither provenance nor confidence. Provenance says *where a value came from*; confidence says *how sure the claim is*; the seal state says **whether a person has stood behind it** — and no amount of the first two produces the third.

A `P1 Measured` reading can be `draft`: instrumented properly, never reviewed. A `P5 Assumed` value can be `sealed`: someone looked at it, agreed it was the right assumption, and put their name on it. Those are different objects and collapsing them loses the thing that matters for a record about a minor.

So the full descriptor for any served value is three fields and a name:

| Field | Answers |
|---|---|
| `provenance` (`P1–P5`) | Where did this come from? |
| `confidence` (0–1, optional) | How sure is the claim, where gradeable? |
| `seal_state` (`sealed`/`draft`/`pending`) | Has a human stood behind it? |
| `verifier` | **Which** human, and when? |

And `servable` alongside `seal_state`, for the same reason `Nestor` carries it: a stored status and an enforceable one are not the same question.

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

---

## 16. The bilateral pattern, and the middle

> **Evidence for this section is in `docs/CROSSINGS.md`** — twenty-one defects from a single session, grouped by how each was caught, and the six patterns under them. Crossing one is this section's subject with six worked instances and the one fix that held: *make the violation inexpressible, not forbidden.* It is a findings record and governs nothing.

This section is a reading key for the rest of the document. It was the last thing noticed and it should probably have been the first.

### The fleet builds in pairs

Almost every structure in this constellation is two-sided, deliberately:

| One side | Other side | Where |
|---|---|---|
| Blueprint | The populated box | `willow-data-vault` — *"Repo = how to build the box. Box = the instance that stays home."* |
| Canonical | Vendored | `libs/subject-consent` ↔ UTETY; `oakenscrolls-office` ↔ its store copy |
| Python core | TypeScript port | `marching-arts` |
| Repo copy | Bundled copy | willow-mcp's `PreToolUse` hook |
| Local organ | Remote proxy | `jeles` ↔ `jeles-remote` |
| The learner | The sources | UTETY ↔ Jeles |
| Private | Public | `private-ledger` ↔ `public-ledger` |
| SOIL | LOAM | Local structured state ↔ knowledge graph |
| `facts` (about a person) | `rationale` (about the software) | #125 — *"two tables, two gates, and the difference is the design"* |
| `observed` (machine fact) | `status` (interpretation) | `almanac-template` |
| `tier` (ordinal) | `confidence` (continuous) | evidence-tiers migration |
| `valid_at` | `invalid_at` | The bitemporal migration |
| Core | Seam | `safe-app-common` |
| Enforcement | Ledger | `willow-gate`'s two modes |
| Propose | Ratify | Dual Commit |
| Declaration | Enforcement | Manifests ↔ gates, everywhere |
| Owner == subject | Owner ≠ subject | `corpus-lens`'s scoping |
| Thirteen fields in | Thirteen fields out | The knock (§7.2) |

Even the sigil is a pair: **Δ and Σ** — the difference and the sum.

### A pair is only as good as its middle

Splitting a thing in two creates a new obligation: **something must reconcile the halves.** Where the fleet builds that middle, it works well —

- the knock's exit diff, comparing declared intent against outcome (§7.2)
- `test_bundled_hook_is_identical_to_the_repo_copy`
- `test_the_consent_core_is_the_canonical_copy_not_a_fork`, which refuses any load path containing `utety`
- the five-tier differential holding two acoustic implementations to 4.97e-13 dB
- `fingerprint_result` ∈ `match · drift · no-baseline`, comparing a live baseline against current content (§15)
- `check_links.py`'s daily sweep, opening an issue when a source goes dark

### Every failure in this document is a middle that was absent, mis-aimed, or unable to fire

That is the whole diagnosis, and the three modes are worth separating because they need different fixes:

| Mode | Instance | Fix |
|---|---|---|
| **Absent** | `catalog.json` advertises encryption `u2u` does not implement; a docstring says four guards where five are wired; `oakenscrolls-office`'s "keep in sync" with nothing syncing it; `quiet-corner`'s `session_scope` declared per-field and honoured nowhere | Build the middle, or stop making the claim |
| **Mis-aimed** | #120's differential reported 14,650 disagreements that were **entirely SQL text** — zero row sets, zero counts. Real, and comparing spelling rather than behaviour | Re-aim at the property that matters, and say which one it compares |
| **Cannot fire** | #211's tripwire fixture *"with no row the principal could not already see, so [it] could not fail"*; §7's refusal indistinguishability, which passes even if the predicate returns nothing to anyone | Mutate it and confirm it goes red (§10) |

A middle that cannot fail is worse than no middle, because it reports success.

### The middles themselves come in pairs, and drift

Three worked examples from the fleet's own bridges, in ascending order of how much they should worry us:

**A middle that covers direction but not content.** `private-ledger` runs six purity tests including `test_willow_bridge_is_pure_injection`, which calls `assert_file_no_egress` on the bridge itself. `oakenscrolls-office` runs two: it enforces that the core does not import the bridge, and **never checks the bridge**. Its docstring promises *"no willow import here, ever"* — a guarantee the test does not keep. The file is clean today; nothing fails if someone adds `import requests` tomorrow.

**A middle duplicated, with neither copy checked.** `nest-seed/bridge.py` connects the local PII zone to the fleet knowledge base, and its docstring states the stake plainly: *"the Nest DB holds a person's legal filings, messages, journals — content that must never leave this machine."* It has a behaviour test and **no purity test**. The same file is vendored into `willow-mcp`, a repo with no checker at all. Canonical and vendored, the middle copied along with the code, and neither instance verified.

**A rule copied by hand, already diverged.** The standalone `oakenscrolls-office` carries its own AST scanner rather than importing `safe-app-common`, with a **narrower forbidden set** than the shared one. Two copies of the same rule, drifted — which is this section's thesis applied to the enforcement layer itself.

### The engine for all of this already exists, and it is called Nestor

This section was written as a specification. It turns out to describe a shipped component — `Nestor`, *"meaning infrastructure, **in medio, fides**"* — which answers exactly one question about any machine-produced answer: **has a human checked this?**

Not as a score. As a state, and the state is never a guess:

| | State | Meaning |
|---|---|---|
| ✓ | `sealed` | A human verified it. Served verbatim, instantly, with their name attached. |
| ~ | `draft` | A machine produced it. Queued for review, **never served as verified**. |
| ! | `pending` | Nothing to offer — *"said plainly rather than improvised."* |

That third state is §6's rule about absence, implemented as a value rather than left to a convention.

**And its `servable` column is the instrument for this entire section.** `Curator` reports `servable` next to `status`, *"because they are not the same question"* — a row saying `sealed` whose signature does not verify comes back `servable=False`, and `unverifiable()` lists precisely those rows:

```
sealed   servable=True   rita      the annual invoice
sealed   servable=False  mallory   forged phrase        <- unverifiable() finds this
```

**That is declaration-versus-enforcement as a computed column.** Every divergence recorded in this document is a row whose `status` claims one thing and whose `servable` would say another — a catalog advertising encryption, a docstring counting four guards where five are wired, a `session_scope` honoured nowhere, a bridge whose docstring promises *"no willow import here, ever."* The pattern §16 describes has a working detector; it has simply never been pointed at prose.

Three properties to carry into anything built here:

- **Rejection is first-class, and it has two kinds.** `reject_pair` retires a wrong mapping everywhere; `reject_match` says *this correct answer is wrong for this query* and leaves the seal intact. The justification is the sentence this design should adopt outright: *"otherwise the audit trail only ever records agreement."* An approval log is not an audit log.
- **Fail-safe direction is chosen per operation.** A rejection is honoured **even when its signature does not verify**, because *"suppressing an answer degrades to human review, which is the safe state; serving an unverified one does not."* Withholding and asserting are not symmetric, and the defaults should not be either.
- **The ledger refuses rather than warns.** Appending is denied if the ledger is a symlink or not a regular file — *"the trail must not be redirectable or suppressible"* — and the existing chain is verified before extension, so a new entry can never launder a tampered history. `NESTOR_SEAL_KEY` binds a seal to a key the store does not hold, so a row edited to `status='sealed'` in the database will not verify and will not be served. Same shape as #127: the module can be bypassed, the gate cannot.

Two honest limits it records about itself, both worth inheriting as habits: *"no value of [the threshold] is good at both jobs"* — 0.92 gives 16.4% false seals against 23.6% recall, 0.96 gives 0.4% against 2.4% — so the threshold is exposed rather than tuned for you; and `IDEAS.md` notes that **nothing consumes rejections as signal**, recorded but unread. A stack of rejections against one query is the strongest available evidence that a threshold is wrong for that domain.

### The only declaration in the fleet that is checked for rot

UTETY's `knowledge.py` names an `_EGRESS_ALLOWED` allowlist and pairs it with `test_allowlist_entries_exist`, whose comment carries the lesson:

> A stale allowlist (file renamed/moved) would **silently widen the door**.

That is a middle for the middle. Every other declaration in this fleet is a list someone wrote once; this is the only one where a rename cannot quietly enlarge the permitted set. Anything here that maintains an allowlist — egress destinations, seam paths, exempted tools, sensitivity mappings — inherits that requirement, because **an allowlist that no longer matches the tree fails open by default.**

### How a document should die

The fleet has one worked example of a retired artifact, and it is the answer to the eighteen dead canonical links this document keeps counting. `PROTECTED_PERSONS.md` was superseded when its subject widened from persons to any keyless principal. Rather than being deleted or quietly left to rot, it stays at its path as a tombstone that does five things:

1. **States its status in the first line** — *"This file is retired. Do not cite it as doctrine."*
2. **Names its successor** and where the canonical text now lives.
3. **Explains why it was superseded**, so a reader can judge whether the reasoning still applies to them.
4. **Maps every clause forward** — all eleven, old ID to new ID — and marks the map *"informative only — the canonical text governs,"* so the tombstone cannot become a competing authority.
5. **Says why it still exists**: *"kept only so existing references to the path do not dangle. Nothing new should link here."*

That is a middle for the pair *(old reference, new location)* — the pair created every time something is retired. Deleting a repo once its value is extracted is reasonable; deleting it without leaving this is what produced the tally. **Adopt the shape for anything this project retires**, and note that it is cheap: five short sections, written once, at the moment the author still remembers why.

### One word, four meanings, two of them opposite

`seam` is not used consistently in this fleet, and the ambiguity is not cosmetic:

| Sense | Meaning | Where |
|---|---|---|
| 1 | A **declared outward boundary** — the module allowed to face out | `safe-app-common`, `private-ledger`, UTETY |
| 2 | An **injected abstraction pointing inward** — *"The seam points inward only: nothing here reaches for a socket"* | `marching-arts` `connection.ts`, `almanac_seam.py` (which lives *inside* the no-egress set) |
| 3 | A **design document** describing an integration surface between two repos | `willow-mcp/docs/design/*-seam.md` |
| 4 | A **defect** — *"where two Willow components each do half a job and the halves do not meet"* | `willow-grove/FLEET_SEAMS.md` |

Senses 1 and 4 are inverses: in the first a seam is what makes a boundary safe, in the last a seam is the absence of one. Calling a module "a seam" therefore tells a reader neither which direction it points nor whether anything checks it.

**So this document does not adopt the word as a load-bearing term.** UTETY's approach is the one to copy — *name the mechanism, not the shape.* `_EGRESS_ALLOWED` says what it does and can be tested; "seam" says only that something is at an edge.

### What this obliges here

terpsi-music will create pairs — it cannot avoid them, and mostly should not:

| Pair | Its middle |
|---|---|
| Canonical store ↔ sidecar (§5) | A promotion path a human signs, with the sidecar never silently becoming canonical |
| Core ↔ seam (§6) | `assert_does_not_import`, direction enforced seam→core |
| Read ↔ export (§7.2) | The knock's reconciliation, exports counted as exports |
| Declared purpose ↔ actual session (§7.2) | The exit diff |
| Guardian edge ↔ send list (§7.1) | One predicate deriving both, never two lists |
| Commentary claim ↔ acoustic prediction (§13) | Shared coordinates, so they can disagree in a queryable way |
| Judge's stated score ↔ later outcome (§13) | The calibration ledger |
| Cited authority ↔ its current state (§15) | `status` + `observed` + the sweep |

**The rules that follow:**

1. **Name every pair you create, and name its middle in the same commit.** A pair shipped without a reconciler is a divergence with a delay fuse.
2. **The middle must be mutation-tested.** §10's rule is this rule; a reconciler that has never been shown to fail has not been shown to work.
3. **The middle must state which property it compares** — spelling or behaviour, reachability or content, presence or equality. #120's lesson is that a differential *cannot tell you which it did*.
4. **Prefer not creating the pair.** The cheapest middle is the one you do not need. Every vendored copy, every port, every duplicate store is a standing obligation, and this codebase has four such pairs already carrying known drift.
5. **Check the middle for rot, not just for correctness.** An allowlist that no longer matches the tree fails open. `test_allowlist_entries_exist` is the pattern, and it is currently unique in the fleet.
6. **Name the mechanism, not the shape.** `_EGRESS_ALLOWED` is testable; "seam" is four things, two of them opposite.


---

## 17. This app as the template

The intent is that terpsi-music is built from scratch, in its own org, and becomes the reference the rest of the constellation follows as it consolidates onto the faces of the die. That makes it two things at once — an application for running a music program, and the worked example of how a SAFE app should be built. This section is about the second job.

### The fleet has already run this play once, successfully

`almanac-template` → eleven verticals, propagated by `propagate-engine.sh`, with the discipline stated in the `almanac-data` meta repo: **engine PRs merge to the template first, then propagate outward; catalog changes stay within individual verticals.** One canonical engine, many instances, changes flowing one direction only. That is precisely this plan, applied to catalogs rather than apps.

Two things differ, and both shape what the template can be.

### Apps are heterogeneous, so template the guarantees, not the app

Eleven almanacs are one thing holding different content. `marching-arts`, `UTETY`, `private-ledger`, and `law-gazelle` are genuinely different applications. A template that fits all four is either very thin or it does not fit.

So what propagates is the part that is identical everywhere and expensive to retrofit:

| Propagates | Does not |
|---|---|
| Purity checker wired, `test_no_egress`, **declared write paths** (§6) | Domain model |
| Manifest with a build-failing check on cloud permissions (§6) | Storage shape |
| `SECURITY_AUDIT.md` against the shared rubric, plus R16 and R17 (§10) | UI and surfaces |
| Canonical store read-only; agent write path is sidecar only (§5) | Repertoire, roster, rubrics — anything domain |
| The knock wired in **enforcement** mode, with `law-gazelle`'s trust table as the shape (§7.2) | |
| The exit line and its export (§11.1) | |
| Allowlist rot tests (§16) | |
| A named middle for every pair the app creates (§16) | |
| Dated predicates for revocation, never deletes (§7.1) | |

That is `safe-app-common` grown from a library into a scaffold — a natural next size for a thing that already exists and already owns the canonical purity check.

### Where the shared parts live, and what that costs the template

`Nestor` is going to be the only repo under `Die-Namic-Systems`, directly — and the reason is structural rather than filing convenience. **It is the one component in the fleet that is not *about* something.** Almanacs are about public data, `hornbook-knowledge` about learners, `willow-memory` about the system's own history; every app is about music, predictions, or legal matters. Nestor is about verification, full stop, in the same posture `PROTECTED_AGENTS.md` adopts when it declares itself *"system- and species-agnostic: it names no product, no model, no vendor, and no family."*

A thing that belongs to every face cannot sit on one. Giving it an org of its own states that in the structure instead of in a README, and makes it the fleet's **single named cross-face dependency** — the clean opposite of four things called Grove.

**Sole-occupancy promotes it from library to supply chain, which raises the bar on three things this document had recorded as footnotes:**

| | Why it matters more now |
|---|---|
| `nestor @ git+…/Nestor@master` — unpinned, mutable branch | Violates the fleet's own R14 in the dependency every app imports. One force-push moves what every consumer resolves. Fix before the move, not after |
| README states **96 tests** in three places; #124 recorded the suite at 123 | Cosmetic in an app. In the component whose subject *is* verification, it is the wrong advertisement |
| Cleared all eight promote gates in #88, left no record (`promote_check.py` writes nothing) | The artifact being promoted to infrastructure has no promotion record |

**And it exposes an inconsistency worth settling before the migration, not during it.** Nestor is not the only cross-face dependency. `libs/subject-consent` has the identical property — not about a domain, needed by multiple faces, already vendored into UTETY with `marching-arts` carrying a test that refuses any load path containing `utety`. It currently lives as a folder inside an app store.

So the fleet has **two** shared edges and is promoting one. Either `subject-consent` joins that tier or the rule for what earns its own org needs stating out loud — and given that it is the guardian-consent core for systems holding minors' records, it has the stronger claim of the two.

> **Settled 2026-07-30 (§18 item 8): the rule gets stated; `subject-consent` stays a library.** The paragraph above argued its way to *"it has the stronger claim of the two"* and that framing is what needed correcting — the two claims are not the same kind of claim, so comparing their strength was the wrong question.
>
> **The rule: an org of its own is earned by being depended upon *as infrastructure*, not by being shared.** Precisely — a component gets sole occupancy when consumers must be able to *pin, audit and reason about its supply chain independently of any application that uses it.* Nestor qualifies because it is the thing that says whether other things are correct: a consumer who cannot audit Nestor's provenance separately from the app under test has no verification at all, only a claim. That is a property of what Nestor **is**, and it is why §17's sentence about it — *"a thing that belongs to every face cannot sit on one"* — is about position rather than about breadth of use.
>
> **`libs/subject-consent` is shared and is not infrastructure.** It is a domain library about guardianship, which is a *subject* — the same category as almanacs being about public data and `hornbook-knowledge` about learners. Being needed by several faces makes it a **dependency**, and the fleet already has a good answer for those: version it, pin it, resolve it by URL. Sole occupancy would say something about it that is not true, and §17's own criterion — *"the one component in the fleet that is not **about** something"* — excludes it by name.
>
> **The half of the original argument that survives, and it is the load-bearing half.** *"The guardian-consent core for systems holding minors' records"* is a statement about **stakes**, not about placement, and stakes are answered by the version discipline rather than by the org chart. So the obligation transfers rather than disappearing: `subject-consent` must be **pinned to an immutable ref by every consumer**, which is exactly the defect §17 already records against Nestor one row above — `nestor @ git+…/Nestor@master`, an unpinned mutable branch, *"violates the fleet's own R14 in the dependency every app imports."* A library holding the consent core for minors' records resolving to `master` is the same defect with higher stakes, and moving it to its own org would not have fixed it. **That is the finding this item produces**, and it is worth more than the placement decision was.
>
> **What this costs, stated rather than discovered:** `subject-consent` stays somewhere apps reach into, so the vendoring pressure that produced this fleet's four drifting canonical/vendored pairs still points at it. Rule 12 is the mitigation and it is not automatic — the moment a second app copies it instead of depending on it, the pair exists and needs a named middle in the same commit. **`terpsi-music` will be that second app**, so this is a live obligation here and not a note about somebody else.

**What this costs §17's template:** propagation now crosses an org boundary. Locally that is free — everything is a peer under `~/github/`, and `kart-sandbox.json` binds by path with no org in it. For CI it is fine, since public repos resolve by URL. The tax lands on remote and cloud agent sessions, where `add_repo` refuses cross-tier and a session can hold one owner's repos or another's, not both. So a conformance suite that lives with the template and is *run* by instances in a different org is reaching across the one boundary that is awkward for agents — which argues for the suite being **installed as a dependency** (versioned, pinned, resolvable by URL) rather than read from a sibling checkout.

### A template without a conformance check is just the first copy

This is the failure to design against, and the evidence is domestic. This fleet carries **four canonical/vendored pairs already drifting**, and every one began as *"keep in sync"* in a README. A template propagated by hand is that same pair, once per instance.

The almanac side has the answer in two scripts — `propagate-engine.sh` to push, `status-all.sh` to check. The app side is half-built: PR #113 measured that `promote_check.py` *"returns an exit code and **writes nothing**,"* and that Nestor and Jeles both cleared all eight gates in #88 while **neither left a record.** The gate exists; the ledger does not.

So two requirements, and they are the whole difference between a template and a first copy:

1. **Every instance runs the conformance suite in its own CI**, against the template's version of it — not a copy of it.
2. **Promotion writes a record**, so "this app conforms" is a dated fact rather than an exit code someone saw once.

Without those, the second app is a copy, the fifth is a dialect, and the constellation ends up reading `FLEET_SEAMS.md` about its own template.

### "From scratch" should not mean rewriting the resolver

Building fresh in the target org is right: the guarantees become structural from the first commit instead of retrofitted onto a playground app, and §9's foundation list is exactly the part that is expensive to add later.

But the 197 tests in `apps/marching-arts` encode bugs found the hard way, and they encode them **nowhere else**:

- denies that silently stopped binding when the parentheses came off the joined clause
- a guardian trigger that stopped firing the moment the chain name gained a partition suffix, letting a minor self-consent with nothing raised
- a conversion window that answers *nobody*, permanently, on a birthdate corrected two seasons late

Each is a regression test standing in for an afternoon of debugging and a reasoned decision. **Carry the suite across even if every other line is rewritten** — it is the most valuable artifact in the playground copy and the easiest thing to lose in a clean rebuild.

### Consolidation is §16's fourth rule at fleet scale

Collapsing forty repos into a handful of bunches per face is *prefer not creating the pair*, applied to the whole constellation. Fewer repos, fewer edges, fewer middles to maintain — and each consolidation **retires** a seam rather than documenting one.

Which suggests the measure. `willow-grove/FLEET_SEAMS.md` currently records four breaks. A consolidation that is drawn correctly makes that document **shorter**; one that only moves code around makes it longer, and the bunches were cut in the wrong places. That is a cheap, honest metric available before the first migration and after each one.

---

## 18. Before the first commit

Everything above argues about design. This section is the short list of things that are **not yet decided or not yet written**, and which of them stop work. It is the last section on purpose: a document whose other sixteen sections mostly discovered that the answers already existed owes a plain statement of what does not.

**This section decays and should show it.** Each item carries a state. When one closes, strike it and note the resolution rather than deleting the line — the tombstone discipline of §16, applied to this document's own open list. An item silently removed is indistinguishable from one that was never there.

### 0 · Read §14 as a claim, not as ground truth

**State: standing caveat, and its stated obstacle was false — corrected 2026-07-30.** `docs/FLEET-READS.md` said the pass could not be run remotely because there was no organisation to read the repositories from. They are on GitHub under the same account as this one, several of them public; three have now been cloned and read from a remote session, and ~~four~~ ~~ten~~ **eleven** rows are verified (the *four* was true when written and drifted; the *ten* was true until the `apps/jarvis` row was added 2026-07-31; the figure is now derived and enforced — see §14's note). The pass is open, not blocked — **twenty-eight repositories read as of 2026-07-30, with every exists-row now marked `VERIFIED` or `UNVERIFIED`**, including one verified *negative* (`willow-tech-manual` does not carry the L-ladder, so `SENSITIVITY.md` was correctly written from scratch). Of the 36 names, eight do not resolve at all and two are unreachable cross-tier; see `docs/FLEET-READS.md`. §14's component map was assembled from READMEs and merged pull-request descriptions — **not from reading or running source.** Every row asserting that something exists is a `P2 Cited` claim (§15) whose source was read and never executed.

That is the exact defect #124 named: *a figure carried from a summary rather than from the thing that produced it.* Before anything is built on the strength of that table, one pass should open the code behind each **Exists** row and either confirm it or downgrade it — and the pass itself should leave a record, because an unverified table and a verified one look identical.

> **The pass cannot be run from a remote session, and that is a property of the fleet rather than of any one session.** It requires reading thirty-six repositories that have no GitHub organisation to be read from; locally they are flat peers under `~/github/`, which is reachable from a local session and invisible to a remote one. Until an organisation exists, §14's table stays `P2 Cited` for every remote session, and anything written in one rests on the summary rather than the source **by construction, not by carelessness**. Documents produced under that constraint should say so in their own provenance note rather than leaving the reader to infer it.

### The four that block — one closed, three open

**~~1 · `L1–L5` is undefined.~~**
**State: closed 2026-07-30. Resolved by `docs/SENSITIVITY.md`, which is canonical for the five definitions.**
~~§6 keys classification onto the sensitivity ladder and §15 makes it one of three ordinal scales, but nothing in the fleet states what the five levels *mean*. All that is recorded is behavioural: at L3 and above the payload is `NULL` in the SELECT list and only a derived instruction is served, and L5 is never served to anyone under any grant (#112). `willow-tech-manual` does not carry the definitions. **No field can be classified against a ladder nobody has written down**, so this blocks the first migration and everything downstream of it. Resolution: write the five definitions with one worked example each, in the app that owns the resolver.~~

The document defines `L1` Open, `L2` Internal, `L3` Attributed, `L4` Restricted, `L5` Enforcement-only; maps all eight §6 classes onto them; writes the sensitivity→trust crossing §15 asked to live in exactly one place; and carries the composition, prefix, fail-closed, and declassification rules. `tests/test_sensitivity_ladder.py` asserts the ladder is whole and that no rung takes a name another scale owns.

**Two residuals, carried forward rather than closed with it:**

- ~~**1a · The `L3`+ NULL rule is ambiguous as cited, and the definitions assume a reading.**~~ **State: closed 2026-07-30 — SCOPED, decided rather than inherited.** ~~"The payload is `NULL` in the SELECT list" does not say *on which paths*. Read absolutely, a guardian cannot be served their own child's name; read as scoped to principals without an entitlement edge, it is correct. `SENSITIVITY.md` assumes scoped and flags it. **If the absolute reading is right, `L3` and `L4` are wrong.** This is one file in `apps/marching-arts` and it is the highest-value item in the item-0 pass.~~
  **Why it was never a read.** This item assumed #112 was an implementation to consult. It was a **spike** (item 2), so opening that file would have established what a prototype happened to do — a different question from what the rule should be. The rule was never decided anywhere; it was observed once and quoted as settled. `SENSITIVITY.md` now states scoped on its own authority, and a contrary finding in `marching-arts` is a fact about the spike and does not reopen this. **The "highest-value item in the item-0 pass" was not an item-0 item at all**, which is worth remembering when reading the other 34 `Exists` rows.
- **1b · `L5` is unreachable by class.** None of §6's eight classes maps to it, so the document assigns it per record under three rules — key material, the content of an enforced external restriction, and anything whose rendering would reveal a refusal. The alternative is a ninth class. Deliberate, and worth revisiting if a fourth trigger appears.

**~~2 · The disposition of `apps/marching-arts`.~~**
**State: closed 2026-07-30. It was a spike; it retires. `terpsi-music` is a fresh build, and the first commit is an empty tree rather than a move.**

~~§17 says "from scratch." Nothing says whether the playground copy is deleted on promotion or kept. This decides whether the first commit is a move or an empty tree — and §16 rule 4 is explicit that leaving two live copies behind a "keep in sync" note is the option with a measured failure rate in this fleet (four pairs, four drifts). If it is kept, it needs a named middle in the same commit; if it is retired, it needs the five-part tombstone.~~

**The disposition, from the maintainer.** `marching-arts` was the first test of
whether the shape could stand up. `terpsi-music` is where it comes together
fresh, for real testing, and migrates to the organisation once it holds. So:
retire, and **the findings carry forward while the code does not.** No
extraction, no port, no shared library — a port is how this fleet has lost four
pairs out of four, and `marching-arts` is itself already carrying a TypeScript
port of a Python core that #120 found had drifted.

**This decision has a consequence larger than the item.** A spike proving
something *can* stand up is not a component that exists, so §14's `Exists` and
§9's *built* are the wrong labels wherever they rest on it — corrected in place
at both sites. That is a stronger correction than item 0's pass would have
produced, and it arrived by asking the maintainer rather than by reading source.

**The five-part tombstone cannot be written from here.** `marching-arts` lives
in `safe-app-store`, which no remote session can reach (`FLEET-READS.md`). What
is recorded here is the disposition; the stub is an act in that repository, and
when it is written it needs: status first, `terpsi-music` named as successor,
spike-completed as the reason, its findings mapped forward and marked
non-authoritative, and why the stub still exists (§16, rule 20).

**~~3 · No schema for the lane model.~~**
**State: closed 2026-07-31. `docs/LANE-MODEL.md` is canonical for the reasoning; the DDL is `migrations/001_lanes.sql`, with a five-part tombstone at the old `docs/schema/` path.**
~~W-1 and W-3 (§7.4) are schema decisions, not modelling preferences: a lane per ward from the first write, and *a shared event is two lane entries with one referent.* §8 is an entity sketch with no fields, keys, or migrations. Migration 001 cannot be written from what is on the page, and retrofitting either clause later is a data migration across every table that references a student.~~

~~Twelve~~ **Fourteen** tables, ~~93~~ **116** columns, all classified in a seeded registry. W-1, W-2, W-3, W-4, W-5 and W-6 are encoded structurally rather than as policy — `lane_entry.lane_id` NOT NULL, a grant table with a single lane column and no join table to put a set in, a `referent` with no participant column, an envelope with two NOT NULL lane references that must differ, a widening whose category cannot be a wildcard, and `exit_terms` NOT NULL with a non-blank CHECK. `access_grant.max_rung` and `self_widening.max_rung` both omit `L5`, and `crossing_envelope` has no rung column at all, so the ladder's top rung is unreachable through a grant, a widening or a crossing by construction. §7.1's state/history split is applied: ten tables take `valid_at`/`invalid_at`, three deliberately do not, and the three carry a `BEFORE UPDATE OR DELETE` trigger because omitting the pair does not stop an `UPDATE`.

> **The count above was wrong in this document's first version of this entry — it said ten, and the tree said twelve.** That is rule 17's defect, committed in the same session that corrected an instance of it in CLAUDE.md. Recorded rather than quietly amended, because the useful part of a tally of these is that it keeps growing. **The correction to fourteen is not a third instance**: the two new tables were added at promotion, and the figure was derived from the tree and from a live instance rather than carried forward.

The DDL has been **executed** against PostgreSQL 16 and every constraint attacked directly: **27 forbidden acts refused, each by the guard named in its error**, and six legitimate writes asserted still to land. `tests/test_lane_model.py` guards the same invariants as text with no database — 17 checks, five of them decoys that attempt a forbidden shape and assert the guard notices — and eight rows in `tests/ablate.py` mutate the DDL itself and require that suite to go red. `.github/workflows/tests.yml` runs all of it on every push.

**Three things gated adoption. All three are answered, and the answers were not all the expected ones:**

- **~~It rests on a paraphrase.~~ Cleared, and it was not a formality.** Part III was opened at source (`c8c96b4`). W-1…W-7 read as written, and **two clauses had lost their second halves in the gloss** — W-3's *"a crossing requires a guardian-signed envelope naming both lanes, purpose, and expiry"* and W-5's per-matter widening. Both were prohibitions in the paraphrase and permissions in the clause. That is the general finding and it is bigger than this item: **a summary keeps prohibitions and drops permissions**, and a schema built from one forbids without providing the sanctioned path. The fix is the thirteenth and fourteenth tables.
- **~~Three~~ ~~Four~~ Three invariants are stated and unenforced** — I-7's supersession asymmetry, W-3's default deny, and the rung ceiling. ~~the `self` edge's holder~~ came off the list on 2026-07-31: `edge_self_holder_is_subject` is the trigger the DDL's own comment promised *"when this migration stops being proposed."* Writing it found the row it was not written to refuse — `('guardian_of', Ben, Ben's lane)`, a ward holding guardianship over itself, which would have made the ward a valid signer of its own crossing envelope. The rule is an equivalence and both directions are refused. The remaining three are predicates over the acting principal and belong with the read predicate.
- **~~It is gated on blockers 2 and 4.~~** Neither gates the DDL's *location*. Blocker 2's disposition is recorded above and the act belongs to another repository; blocker 4 decides which surfaces read this schema, not whether it exists. What blocker 4 still gates is the first directory layout, which is item 4's own entry.

**~~4 · Which surfaces exist.~~**
**State: closed 2026-07-31, by maintainer decision. The answer is `docs/survey/scout-21-surfaces-a11y.md` §3, adopted as written: four rendering backends — TUI, server-rendered HTML, print, text/ASCII — over one presentation-IR middle, with three trust paths and the `presentation/` + `surfaces/` layout that section names.** Not "a TUI or a browser app": §4 assigns five transports to six personas, so the surface count follows from the transport count, and the judge and the guardian share a backend while never sharing a trust path.

~~Six personas (§4), `safe-design` ready with tokens and structurally-parity backends, and nothing recorded about whether this is a TUI, a browser application, both, or a TUI plus the parent PWA of §4.2. The answer sets the first directory layout and determines which of `safe-design`'s backends is load-bearing.~~

**The corrections below survive the closing, and two become obligations of the first surfaces commit:** the manifest this item owns is written against `tools/sockets.py`, which exists first so the manifest cannot be born wrong (iii); and rule 12's socket-reconciliation test lands in the same commit as the manifest, in this repository's own CI rather than the store's (ii).

> **(i) The enumeration above is missing a surface, and it is the untrusted
> one.** "TUI, browser, both, or TUI plus the parent PWA" has no place for
> clinicians and judges. §4 already settled what they get — *"a kiosk device
> the org owns and wipes, or their own device on a guest SSID reaching the hub
> directly"* — and a judge on a borrowed tablet for one evening is not running
> a TUI. That is a **third surface, browser by necessity**, and §7 singles it
> out as the session most worth narrating precisely because it is least
> trusted. Most of the six personas are already decided in §4; this item reads
> as more open than it is, and the part genuinely undecided is narrower: what
> operators use, and whether the guest surface is a separate app or a
> restricted mode of the same one.
>
> **(ii) `surfaces` is a manifest field, and this fleet's precedent for it
> failed — and the mechanism of that failure is now read at source.**
> `willow-grove/DESIGN_CONSTRAINTS.md` (*"Design constraints for the fresh
> build"* — which is this repository) carries the same requirement as its
> constraint 4, *"Ship a manifest that something actually validates"*, reached
> from a code review rather than from this discussion. It supplies what was
> missing here: **the store's lint skips by construction.**
> `safe-app-store/tools/catalog_lint.py:71-73` errors on a missing manifest
> only when the catalog entry carries a local `path`, and the enforcing ACL
> lives in `willow-mcp` `gate.py` rather than in the store — so an
> external-repo app falls between the declaration surface and the enforcement
> surface. That is a middle that exists and **cannot fire for a whole class of
> entries**, and it is the argument for this repository validating its own
> manifest in its own CI rather than relying on the store's. §4.3 records `safe-app-willow-grove` declaring `"surfaces":
> ["tui"]` with `lan_listen`/`lan_send` and *"portless means portless"*, while
> `bridge/__main__.py` starts an aiohttp server on `0.0.0.0:8560`. Whatever is
> decided here becomes a declaration of the same kind, for an app with more
> surfaces than that one and at least two that listen. **Rule 12 applies in the
> same commit:** a test enumerating listening sockets that fails on any the
> manifest does not account for. Without it this repository ships the exact
> declaration-without-enforcement pair its own §16 is written about.
>
> Egress purity is not the obstacle to a browser surface and should not be
> raised as one: §6's inner ring forbids *outbound* — there is no client to
> call out. A local listener is `lan_listen`, a permission.
>
> **(iii) The enforcement half of (ii) is built, 2026-07-30, and the decision is
> still open — that ordering is the point.** `tools/sockets.py` enumerates every
> listener and every outbound connection the source can open and reconciles them
> against a manifest. There is no manifest yet, because item 4 owns it.
>
> **§4.3's failure was not a lie; it was an ordering.** `safe-app-willow-grove`
> declared `"surfaces": ["tui"]` and *"portless means portless"*, then opened two
> all-interface listeners and an `8.8.8.8` probe — because the declaration
> shipped first and nothing was ever pointed at it. A checker that exists before
> the first manifest means **the manifest cannot be born wrong**: whatever this
> item decides gets written against something that already refuses.
>
> Three properties, each with a decoy in `tests/fixtures/decoys/` that trips it:
>
> - **It parses and never imports.** A checker that imported a module to inspect
>   it would execute the code under inspection, and for a network module that
>   means opening the socket it was written to detect.
> - **A declared port is not enough; the host must match, and wider is a
>   finding.** Declaring `8560` and binding `0.0.0.0:8560` is the willow-grove
>   case exactly — true to a checker comparing ports, false to anyone on the LAN
>   segment.
> - **A bind it cannot resolve is not a pass.** `bind((HOST, PORT))` from the
>   environment is `UNRESOLVED`, which is a finding — rule 13 at the one place
>   where guessing means an open port nobody wrote down.
>
> **And the vacuous case is reported as vacuous.** No manifest and no listeners
> means nothing was checked, which is not the same as nothing being wrong;
> `conform.py` renders it `UNKNOWN`, never `PASS`. The moment a listener appears
> with nothing declaring it, the result is `FAIL` — nobody has to remember to
> switch the check on when this item closes.
>
> **The decoy earned its keep on the first run**, and the bug is worth recording
> because it is the shape this repository keeps finding. The literal extractor
> read `_const(x) or _UNRESOLVED` — the obvious spelling — and an empty string is
> falsy, so `bind(("", 8560))`, **all-interfaces spelled as a blank**, was
> silently reclassified as *could not resolve*. Without a decoy the checker would
> have shipped reporting the exact case it was written for as unknown, and looked
> like it worked. That is `§16`'s *mis-aimed middle* in three characters of
> idiom.

**~~11 · The class vocabulary does not cover the categories §20 of the capability map names.~~**
**State: closed 2026-07-30. The vocabulary does not need new members. `docs/SENSITIVITY.md` *Protected status* is canonical for the resolution.**

~~Resolved against this item's own third option rather than its conclusion.~~
The decision: **step 3 of *Classifying a new field* is a definition and its four
familiar examples are illustrative**, so confidential addresses, McKinney-Vento
housing status, foster placement and documentation status reach `L4` *through
the clause* rather than through a class. This item reasoned its way to "`L4`
with a declared purpose" correctly and then inferred "which means new classes";
that inference is what was wrong. Read as a closed enumeration, the clause would
make every future protected category a schema change — the wrong failure
direction for this population.

**One member left the list.** Chosen name is inverted relative to the other
four: the harm is *non-use*, and elevating it makes a deadnaming program
**more** likely by pushing the printing path back to the legal name. The
protected half is the **SIS legal record**, which is `L4`. This item's own prose
had it — *"a legal name served to the program-printing path is the outing"* —
without drawing the consequence.

**Carried forward:** what *checks* a general clause. A lookup table is
mechanically verifiable; a clause is a judgment (rule 19). Recorded in
`SENSITIVITY.md`'s "does not decide" list, not here.

~~The original statement follows.~~
**State: was open; needs a decision, and it is larger than it looks.**
§6's eight classes were mapped onto the ladder in `docs/SENSITIVITY.md` faithfully, and the mapping is sound for what the classes describe. The problem is what they omit. §20 of the capability map lists **confidential address programs (Safe at Home), McKinney-Vento housing status, undocumented families, foster placement changes, and chosen name distinct from the SIS legal record.** None has a class. Every one lands at `PII_MINOR` or `PII_GUARDIAN`, and therefore at `L3` — the rung whose rule is *served in full to any principal holding a current edge*.

That is wrong by at least one rung in every case and dangerously wrong in two. A Safe at Home address exists because disclosing it can get someone killed; `L3` serves it to every staff member with a roster edge. A legal name served to the program-printing path is the outing that §20 of the capability map asks to be handled deliberately. And §18 of the capability map's *"fee waivers that are structurally invisible to peers"* is already load-bearing on `L5`'s rule 3, which arrived from a different direction and covers only the refusal, not the status.

Three ways to close it, and this is the decision: add classes to §6's vocabulary; add a per-field rung override that outranks the class mapping; or treat "protected status" as a fourth `L5` trigger alongside the existing three. The third is cheapest and probably wrong, because these must be *served* to somebody — a chaperone needs the accommodation even when nobody may see the status. That points at `L4` with a declared purpose, which means new classes.

~~**Nothing should classify a field in these categories until this closes.** The ladder is right; the vocabulary feeding it has a hole in exactly the population the program is most obliged to protect.~~

**That hold is lifted as of 2026-07-30.** Fields in these categories may now be
classified, at `L4`, against `SENSITIVITY.md`'s *Protected status* table. The
diagnosis in the struck sentence was half right: the ladder is indeed right, and
the vocabulary feeding it had no hole — the *route into* the ladder did, because
classification consulted the class mapping and never reached step 3's clause.

**~~12 · The subject has no standing in their own lane.~~**
**State: closed 2026-07-30. `records/standing.py` is canonical for the resolution; `docs/SENSITIVITY.md`'s `L4` note and §7's edge block carry the rung consequences.**

**The decision: a `self` edge, capped at `L3` until W-6's threshold.** `L1`–`L3` served in full; `L4` served as the derived instruction unless a guardian signs a per-category `Widening`; `L5` unchanged, never served to anyone including the subject; the cap lifts at the threshold by date comparison and `self` then behaves like any other edge. **And the subject reads their own disclosure log at every rung** — a student who cannot read their `L4` medical field can still see that the athletic director read it on October 12.

**This item's own framing is what kept it open.** It asked *whether* the subject has standing, and three-fifths of that was already decided by the ladder: `L5` is checked before the edge check and is never served to anyone, and `L1`/`L2` sit below the derive floor and need no edge at all. The live question was only `L3` and `L4`, and it was never a yes/no — every other principal's standing is rung-shaped, and there was no reason the subject's would not be. **A binary question about a graded system will stay open**, because neither answer is true.

**Why the first option and not the second.** A `self` edge is *dated*, so the threshold is a date compared on every read rather than an event somebody runs; it is *auditable*, and `principal.id == subject_id` would log `via_edge=None`, indistinguishable in the disclosure log from an unentitled read — §7.2's *narrate the read* silently broken by the fix; it can be *ended* by `invalid_at` (refusal 3), which is where a safety plan in which the subject is the risk has to live; and it is already a row.

**Why not the third — deliberate no-standing.** It makes I-7 unverifiable by the party it protects. *"A student's entries are as durable as entries about them"* is a claim a student cannot check without reading their lane, and rule 19 says a guarantee that cannot be shown to hold is not one. It also makes W-6 the worst moment in the design: years of records, first sight, all at once, nobody left to ask.

**W-4 survives, and one consequence of that is load-bearing.** For a pre-threshold `self` edge, `principal.purposes` is **never consulted** — a minor declaring a purpose over their own `L4` record is the ward authorizing itself, and honouring the declaration would defeat *a ward may request, never authorize* with a keyword argument. Only a guardian's signature widens. W-5 survives because nothing here lifts a cap for good behaviour; a cap set identically for every student at enrolment is not drift.

**Two things this closing found**, recorded because of how:

- **A forged `self` edge.** `Edge("self", "staff-nguyen", "student-ben", …)` would entitle a staff member through the subject's own door. The kind names a relationship and nothing was checking that the relationship held. Guarded in `is_self_edge()`, ablated, and named in `LANE-MODEL.md` as a fourth stated-and-unenforced invariant — the first added by *widening* the schema rather than by reading it, since a CHECK cannot reach `lane.subject_id`.
- **The tripwire could not fire.** `test_a_student_CANNOT_read_their_own_record_documented_not_hidden` closed with `assert not any(k in ("self", "subject_of") for k in ("guardian_of", "staff_of"))`, written to fail once a `self` edge existed. It compares two hardcoded tuples: a tautology that passed after the edge shipped. §16's *cannot fire* mode, in the test written to detect the change, in this repository, after it had already quoted `willow-mcp` #211's version of the same defect. Replaced by `test_the_subjects_standing_is_an_edge_and_is_not_ambient`, which asserts both halves against the predicate.

**Carried forward, not closed by this.** A safeguarding read — a counsellor opening a record because of a referral — appears in the subject's own log like any other, and there is no suppression mechanism. That is deliberate: a `suppressed_from_subject` flag is a backdoor that ends up on everything, and a *"one entry is withheld"* count tips off as loudly as the entry would. It is a real tension and it is named here rather than solved by a field nobody asked for. Whether a **guardian** may read the lane's log is also open and is not this item — a guardian reading it learns which staff member is looking at a record, which is nearer §13's prohibited standing scores than it appears, and guardians already hold receipts.

The `Widening` is a **fourteenth table**, on the same footing as the crossing envelope's thirteenth. Both were written in `records/` first — as types, while the DDL was still proposed — and both became SQL on 2026-07-31 when it was promoted: `self_widening` and `crossing_envelope` in `migrations/001_lanes.sql`. The type and the table say the same thing with one exception, named where it is made: `self_widening.max_rung` admits `L4` and nothing else, because what `records/standing.py` supplies by control flow a table has to say in a CHECK.

**~~13 · `PLAN-GUARDIANSHIP.md`'s gate set is incomplete in two places.~~**
**State: closed 2026-07-30. `PLAN-GUARDIANSHIP.md` §2 now carries G12 and G13, and §6 puts them in step 1 where they belong.**
Building `records/sending.py` against G1–G11 and then ablating it left two mutants alive. Neither is covered by any of the eleven gates, because **every gate in the plan is about a *restriction* and none is about the standing edge itself**:

- **G12 — an ended guardianship must not be messaged.** Refusal 3 ends guardianship by setting `invalid_at`. G1–G11 all test restrictions on a *live* guardian; none ends the guardianship. A predicate ignoring edge dates entirely passed all eleven.
- **G13 — only guardians are messaged.** A predicate that messaged every edge holder — `judge_at`, `clinician_for`, `staff_of`, `director_of` — also passed all eleven. *"Ben will be at the away game in Dayton until 10pm"* delivered to a judge is §4.1's own worked harm.

Both have tests in `tests/test_sending.py` and are now written into the plan itself, which is what this item was waiting for — a gate living only in a test file is one refactor from being deleted as redundant.

**Writing them down produced one more finding than the gates themselves.** §6's sequencing put six gates in the safety core, and **the two it was missing were the cheapest in the step** — an edge-kind check and a date comparison — while a predicate lacking both passed all six. Ordering by cost would have put them first; ordering by *what the plan had already thought about* left them out. That is the general shape of the defect: **a gate set assembled by asking "what could go wrong" enumerates failures and skips the conditions under which the thing should happen at all**, which is the same reading §7's indistinguishability note warns about one section down — a suite asserting only *nothing was sent* passes when nothing is ever sent.

**14 · The classification procedure omits the re-identification gate its own class table requires.**
**State: corrected in `SENSITIVITY.md` 2026-07-30; recorded here because of how it was found.**
`SENSITIVITY.md`'s class table has always said `DERIVED_ANON` is `L2` *"only after the re-identification check"* and *"inherits `max` of inputs until it passes."* Its five-step *Classifying a new field* procedure carried no such step, so a derived field answered *no* at step 2 and landed at `L2` with nothing having looked at it.

**A document disagreeing with itself, where one half is a table and the other a procedure.** Both were written in the same file on the same day and neither review caught it, because reading a procedure and reading a table are different acts and nobody did both against each other. It surfaced within minutes of implementing the procedure in `records/classify.py`, which is the argument for slices in one line.

The fail-open is not theoretical: a count is exactly the shape that re-identifies. *"One student in this section carries an auto-injector"* names nobody and identifies a child if the section has three members — and §17's small-cell suppression exists because this fleet already knows that.

Step 2a added. `records/classify.py` implements it, and a derived field now inherits `max` of its inputs until the check passes.

**~~15 · Who witnesses the anchor.~~**
**State: decided 2026-07-31, by maintainer decision — the composite this item's own analysis argued for: rows 1, 4 and 5 together.** OpenTimestamps weekly (cheap-and-frequent, trusts nobody); certified mail to self or an annual deposit with an attorney (legible-and-rare — a jury understands it without being taught what a hash is); guardian receipts continuously (adverse-interest, and already built). They fail differently, which is the point: a dispute two years out uses whichever survived.

~~**What the decision does not close, carried as tasks rather than questions:** the weekly publication call and the annual-deposit procedure are unwired — `records/witness.py` supplies the anchor shape and nothing yet publishes one on the calendar cadence the module requires; and row 5's **Ed25519 issuance dependency stands** — until it lands, receipts carry weight by distribution and adversity, not attribution, and no deployment claim should rest on a third party attributing one.~~ **All three closed 2026-07-31.** The wiring is `records/publication.py` and `docs/WITNESS-DEPOSIT.md` (order item 3, built and merged). The Ed25519 dependency was **accepted by maintainer decision the same day** — the repository's first and only dependency, pinned with its reason in `requirements.txt` — and `records/receipts.py` carries `Ed25519Signer`: the issuing side holds the seed, the holder's object cannot mint, `schemes()` derives availability by attempting the import rather than trusting the requirements file, and a broken install *refuses* with the cause attached rather than falling back to HMAC. `tools/conform.py`'s `receipt-attribution` row moved from `ABSENT` to `PASS` on the merits. The limit no witness removes (below) is unchanged by the decision and travels with it.

> **Wired 2026-07-31 — `records/publication.py` and `docs/WITNESS-DEPOSIT.md`, with one of the three tasks still open and now stated precisely.**
>
> **The weekly leg.** Everything up to and after the call is built; the call itself is a deployment act, because a module in `records/` that made it would be an egress path in the ring §6 says cannot express one. `payload_for()` returns thirty-two bytes and the caller transmits them. Three things it enforces rather than documents, each with a test that attempts the act and is refused: **an anchor carrying a fourth field does not cross** — read off the type, so a subclass and a value hung on the instance are both refused, and both shapes are needed because an ordinary subclass is caught by the second check and hides the first (`EXTERNAL-ARM.md`'s *"a gate green because a different constraint was catching it"*, found by ablation here); **a publication off the calendar is refused**, so the cadence is enforcement rather than convention, and a tolerance of half a period or more is rejected at construction because it admits every moment; and **two anchors in one slot are refused**, since a weekly series of per-lane anchors is per-student volume on a public calendar.
>
> **What crosses is a commitment over the three fields, not the chain head — and that was a finding, not a preference.** Two quiet weeks produce an identical head and count, so a head-only submission lets one proof stand in for both and a skipped publication becomes invisible. Binding the slot gives every week its own digest and binds the time the programme claims to the time the witness attests. The count and the head stay on the box: a *published series of counts* is a volume signal arriving through the one field nobody reads as content.
>
> **A pending proof is its own state.** `AWAITING_PROOF`, `OVERDUE`, `NOT_SUBMITTED`, `MISMATCHED`, `UNSOLICITED` and `OFF_CALENDAR` join `PROVEN`, and only `PROVEN` yields a `witness.Receipt` — so a submission whose proof never came back cannot make a log read `WITNESSED`. A returned reference with no attested time is a promise and reads as awaiting, because a public timestamp is a promise first and a proof afterwards. Rule 12's middle for the submission/proof pair is `reconcile()`, which reports every slot rather than whichever half the caller read; the two artifacts share a filename stem for the same reason.
>
> **A whole-programme anchor did not exist, and `Ledger.anchors()` was a trap.** It returns one `(head, count)` per lane with a note that publishing them individually leaks which lanes exist — it leaks more: a weekly per-lane series is one child's activity, week by week, on a public chain. `anchor_for_ledger()` folds the lanes into one anchor. Its working names every lane and count, which is exactly what must not travel, so the derivation is a **local** artifact and the register is built from anchors alone — not by redaction but because a status has no field to put a lane in.
>
> **The annual leg** is `docs/WITNESS-DEPOSIT.md`: what is printed (the register, and the proof files; never the records, never the derivation, never a key), when (a fixed calendar date, chosen away from the season's edges, for the same anti-shape reason as the weekly leg), who performs it (a named custodian and a named witness to the act, not a role), and what comes back. A missed deposit surfaces as a dated disposition against the fixed date rather than as somebody remembering — and a later deposit is a new request, never a repair of the gap.
>
> **Ed25519 remains open, and the honest form of it is a dependency decision rather than a task.** The seam is built: `receipts.Signer`, `Issuance.ATTRIBUTABLE`/`SELF_VERIFIABLE`/`UNAVAILABLE`, and a receipt that carries which one issued it **inside its tag**, so a receipt cannot be promoted by editing a caption. The stdlib has no asymmetric primitive; vendoring curve arithmetic into a records module would be the worst version of §16's copied pair; and this repository's CI installs nothing, so a conditional import would produce attributable receipts on one box and self-verifiable ones on another under the same code. So: **`AsymmetricUnavailable` refuses rather than falling back**, a verifier that cannot read a receipt's scheme raises rather than answering `False` (*cannot check* and *forged* are different facts), and `tools/conform.py` carries `receipt-attribution` as **`ABSENT`** — decided and missing, not undecidable. The plug is a maintainer's call about a dependency, and until it is made no deployment claim may rest on a third party attributing a receipt.

The purpose of this system is provability — an institution that does not follow its own rules, and no way to show it. Every mechanism below rests on a record being **believable later**, and a record its author controls is weak evidence. The institution's response to an inconvenient log is not to dispute an entry; it is to say the log is yours, you built it, you can make it say anything.

§5 specifies a `(head, count)` anchor and never says where it lives. `records/witness.py` now supplies the shape — anchors carry a digest, a count and a time and **nothing else**, which is why publishing one may cross the egress boundary at all; cadence is derived from the calendar rather than from activity, because an anchor series that tracks activity is `corpus-lens`'s shape-of-a-week leak; and an unwitnessed log reads as `UNWITNESSED`, never as fine.

**What was undecided was the counterparty.** Candidates, with what each actually survives:

| | mechanism | trusts | note |
|---|---|---|---|
| 1 | **OpenTimestamps** — Merkle-aggregated, committed to a public chain | nobody | free, no account, one call carrying 32 bytes |
| 2 | **RFC 3161 timestamp authority** | the TSA | legally legible; may not outlive the vendor |
| 3 | **Public append-only publication** — the anchor committed to a public repository | the host | cheap, matches how this fleet already works; arguably still yours |
| 4 | **Certified mail to self, or annual deposit with an attorney** | the postal service, a lawyer | a jury understands it without being taught what a hash is |
| 5 | **Guardian receipts** — each guardian holds a receipt for entries about their own child | nobody | the only counterparty whose interest is genuinely adverse to the institution's, and it falls out of the lane model |

**They fail differently, so the answer is probably not one of them.** A dispute two years out uses whichever survived. The shape worth arguing about is cheap-and-frequent plus legible-and-rare plus adverse-interest: 1 weekly, 4 annually, 5 continuously.

**Row 5 is built** — `records/receipts.py`, 2026-07-30 — and building it changed what this table should say about it. It is not merely a fifth candidate of equal kind: **it gives a property no anchor gives at all.** Positions are per-lane, so a guardian holding receipts for 1, 2, 3 and 5 can see that 4 is missing — without the institution's cooperation, without a third party, and without learning anything about any other student. Every other row on this list detects tampering only when someone thinks to compare the log against the witness, and the party motivated to compare is the one holding the log. Row 5 puts the detection in the hands of the party who is not.

Its own limit is the mirror of that strength and is asserted by name in `tests/test_receipts.py`: **receipts detect removal, never omission.** An entry never written produces no receipt, and a guardian holding 1..N cannot tell whether N is everything. This is the same limit as the paragraph below, arriving from the other side — which is the argument for the plural answer rather than against row 5.

Authenticity is weaker than the rest of the module and says so: issuance is HMAC-tagged because the stdlib carries no asymmetric primitive, so the institution can verify its own receipts and a mismatch is something it must explain — but anyone with the key can mint one, and a third party cannot attribute. **A deployment wants Ed25519 here**; until then row 5's weight comes from distribution and adversity, not from unforgeable maths. That is a dependency this item now carries and did not before.

**Building it also found a defect in §5's own implementation**, recorded because of how it was found. `disclosure.Log` was a single global chain carrying a `subject_id` per entry — §5 line 271 requires that any chained artifact inherit *per-subject partitioning*, and a column naming which student a row concerns is rule 8's roster-column shape in the audit table. It leaks in exactly the way that matters here: a guardian holding global positions 5, 12 and 40 learns that thirty-four entries concerned other children. `Ledger` supplies one chain per lane. **The general shape is that a mechanism designed to be handed to an outside party audits the store that feeds it**, and nothing before this slice had that pressure on the log.

**And the limit no witness removes**, recorded here rather than discovered later: anchoring proves what was written existed. It cannot prove everything was written. Selective recording defeats every scheme, because an anchor attests to what a log contained and never to what the world contained. The partial mitigations are real and are not proof — recording happens at the predicate rather than by a human choosing to type, and refusals are logged as durably as disclosures so a gap is anomalous. `tests/test_witness.py` asserts the limitation by name so nobody mistakes `WITNESSED` for *complete*.

**~~16 · The ledger answers for lanes it has never heard of.~~**
**State: decided strict 2026-07-31, by maintainer decision. `records/disclosure.py` is canonical for the resolution.**

Found by order item 5's rule-13 sweep, and the sharpest of its findings because the empty answer was *served* rather than refused: `Ledger.log_for` returned the same empty `Log()` for a lane with no entries and a lane the ledger had never heard of. Downstream, `own_log` rendered the second GRANTED and complete — a student told nobody has ever read them, by a ledger that was never asked — and `receipts.issue` handed a guardian nothing without saying so. Absence rendering as a result, one call short of a surface.

**The decision: strict.** An unknown lane raises `UnknownLane` (rule 13 — the ledger cannot speak for a lane it does not carry, and must say so rather than answer). `knows()` exists for callers who need to ask first. **The one legitimate exception is the write path**: W-1 opens a lane at the first write, so `record()` still creates; reads never do. The tests that held the finding in place went red the day the fix landed — exactly as their docstrings promised — and were rewritten to hold the fix; the `ledger_lane` row left `CANNOT_DISTINGUISH`, and a mutation reverting `log_for` to the forgiving read is in the ablation table.

**17 · Whether the canonical store is sealed at rest, and who holds the escrow.**
**State: open, and the mechanism is built ahead of the decision on purpose.** `records/atrest.py` and `docs/AT-REST.md`, 2026-07-31, close §9's foundation 3 — *"at-rest sealing across the Zone A boundary is not [built]"* — and closing it made two decisions this document owes and does not have. (Numbered 17 because 16 belongs to a sibling slice landing in the same session; the gap is a collision, not a removal.)

§5 poses the first itself and does not answer it: *"decide deliberately whether student records need more than filesystem permissions plus a `0700` box, because 'the box is sovereign' and 'the box is encrypted' are different claims and only the first is currently true."* Nothing routes through the new module, so by rule 18 it is a **mechanism and a ledger of key state, not a gate** — and it was written that way deliberately, in the ordering §18 item 4 note (iii) argues for: *a checker that exists before the first manifest means the manifest cannot be born wrong.* Whatever the deployment decides, it gets written against something that already refuses.

**Five things §5 underspecifies were decided in the code and are recorded in `docs/AT-REST.md`** rather than left to be inferred from the source: the middle key tier is keyed by **lane and not by access circle** (a circle key spans students, so one ward's erasure would take six others' with it — rule 8's roster column moved down a layer); lane keys are **random and wrapped, never HKDF-derived** (a derived key is recomputable from the master forever, so §5's own *"one member's history is deletable without touching anyone else's"* cannot hold); wrapping is **symmetric** because §5's X25519/HPKE property is unused inside Zone A and the accepted dependency carries no HPKE; the record cipher is **Fernet** with the context bound *inside* the authenticated plaintext, since Fernet has no AAD; and **where the master lives is not decided here at all**, because the module is a core that takes key material as an argument.

**The escrow half is the part that stays open, and it is deliberate.** §5 calls single-file key loss *"the failure mode that ends the program"* and proposes shares across the director, a board administrator and a sealed offline share, rehearsed annually — how many, whose, and on what calendar are a maintainer's decision. So the module carries the *shape* of a disposition and no policy, and reports `ABSENT` for a master with none. `tools/conform.py` reads that row `ABSENT` today, which is the honest answer and the one that will keep appearing until somebody decides. §10's proposed **R16 — data at rest is encrypted, with the key escrowed** is the rubric line this answers half of.

**And §5's crossing-to-B/C column is still unbuilt**, which is worth stating because the two are easy to conflate: sealing *at rest* and sealing *per family circle for a crossing* are different operations, and the second is the one that wants the asymmetric property. It belongs beside `records/crossing.py` when there is something to cross to.

### The three to state, which do not block day one

**~~5 · The exit line is unwritten.~~**
**State: written 2026-07-30. `docs/EXIT.md` is canonical; `records/export.py` is the code.** The line is deliberately shorter than §11.1's model sentence, because most of what that sentence describes does not exist and writing it would be the failure this item exists to prevent. **One PASS, one PASS-and-ABSENT, three UNKNOWN** against the five-point test — the per-student export is built and tested, the whole-program export has no store to read.

The harder half is the one that landed. W-6's per-graduate bundle renders as CSV and plain text with a checksummed manifest, carries the exit terms in the words written at opening, and **drops nothing by rung** — `L5` is the single exception and is *named and counted in the manifest*, never silently omitted, because a quiet drop is how a "safe subset" export gets built by accident and the recipient could not tell.

**`records/export.py` touches no filesystem**, and that is §6's core/seam partition rather than a style choice: it returns `(name, media type, text)` and the caller writes. A module that opened files would be a write path nothing declared, which is a check `tools/conform.py` now runs. `docs/EXIT.md` also opens the **regression ledger** §11.1 asks for, empty, with a note that an empty table is a claim like any other.

**~~6 · No conformance suite.~~**
**State: the ledger half is built 2026-07-30 — `tools/conform.py`. The propagation half stays open and is now item 6b.**

§17 measured the gap as *"the gate exists; the ledger does not,"* and the ledger is what this adds: thirteen checks against §17's propagating guarantees, each reporting `PASS`, `FAIL`, `UNKNOWN` or `ABSENT`, written to a dated, commit-pinned, never-overwritten record under `docs/conformance/`. *"Does it conform"* is answerable from any one record; *"when did it stop"* only from the series.

**Today it reads 6 pass · 0 fail · 7 unknown, and a run that read all-pass would be the thing §17 warns about.** `UNKNOWN` is not a pass (rule 13), and `tests/test_conform.py` asserts that unknowns still exist — so *the work got done* and *the checks got softened* stop looking identical from outside. Seven of §17's guarantees are genuinely undecidable here (no manifest, no store, no allowlist, no wired knock), and `FAIL` fails the build while `UNKNOWN` does not, because a gate that always fails is a gate that gets switched off.

**6b — an instance must run the *template's* suite, not a copy of it.** That is the second of §17's two requirements and it needs the versioned-dependency shape §17 already argues for, which needs a template repository to depend on. Not blocked on anything here; blocked on the migration.

> **Found while building it, and it is the item's own subject.** §14's note claimed *"8 of 40"* verified rows while the table held ten and PR #7's body quoted ten — a figure in prose the code moved past, inside the note written to stop exactly that. Worse, the test meant to watch it asserted `0 <= len(verified) <= len(ex)`: a subset count is always within its own bounds, so the guard could not fail on any table. **The third tautology found in this repository's own tests.** The note now carries a machine-readable `VERIFIED-COUNT:` marker compared against the parser's tally, and the mutation lives on the *document* — the first attempt mutated the test and asked the same test to notice, which the harness correctly reported as `SURVIVES`.

**~~7 · Score-position anchoring is unchosen~~**
**State: chosen 2026-07-30 — both, designed together. `records/marking.py` is canonical.**

One `Mark` carries a required timecode and seat and an **optional, derived** score position, so the two cannot diverge into a migration later. The asymmetry is the design and is not a convenience: **a tap is `P1 measured` and an alignment is `P3 fitted`.** An alignment may *add* a position and may never *replace* the timecode — if the alignment is wrong the remark is still anchored, whereas a timecode derived from the score would move a judge's words to a passage they were not about, which is what makes an adjudication record worthless in a dispute. `align()` refuses a position whose provenance outranks the observation it came from.

**Rule 12's middle is `drift()`**, in the same commit: it compares what the alignment says the position's time is against the tap that is actually true, and reports `AGREES`, `DIVERGED`, `STALE` or `UNALIGNED` rather than presenting whichever half the caller read. **Staleness is checked before drift**, because a position derived against a superseded score can agree perfectly and still point at a bar a cut removed — reporting `AGREES` there is the more dangerous answer. Every derived position names the score edition it was taken against, for the same reason `sealing.py` digests a body: a derived thing must not outlive the thing it was derived from.

W-3 is structural here rather than remembered — a `Mark` carries a shared `referent` and marks naming a student are lane-scoped, with no participant list, because that list is the roster column W-1 forbids.

> **Reclassified 2026-07-30: still not day-one, no longer separable.** §24 of the capability map's craft-feedback capability rests on seven checks at the lyric/music seam — stress against meter, vowel against pitch, breath against phrase — and every one anchors to a position in *both* the text and the score. None can be built without this. It remains outside the first commit; it stops being a body of work that can be deferred indefinitely without deciding what it blocks. Left in this list rather than moved up, with the change recorded here.

### The three that need a choice, not research

**~~8 · `libs/subject-consent`'s placement~~ (§17)**
**State: settled 2026-07-30. The rule is stated in §17; `subject-consent` stays a library.** An org of its own is earned by being depended upon *as infrastructure* — a component consumers must pin and audit independently of any application using it — not by being widely shared. Nestor qualifies because it is the thing that says whether other things are correct. `subject-consent` is a domain library about guardianship, which is a subject, and §17's own criterion excludes it by name.

**The finding is worth more than the placement was.** *"The guardian-consent core for systems holding minors' records"* is a claim about **stakes**, and stakes are answered by version discipline rather than by the org chart — so the obligation transfers: it must be **pinned to an immutable ref by every consumer**. That is the identical defect §17 already records one row above against `nestor @ git+…/Nestor@master`, with higher stakes, and moving it would not have fixed it.

**~~9 · Practice logging against UTETY's no-leaderboard rule~~**
**State: closed 2026-07-30 — and two things in the framing were wrong, both of which made it easier. `records/practice.py` and `records/conflict.py`.**

**The standings half was never a UTETY question.** It is already forbidden here by CLAUDE.md refusal 6 and W-7 — *never compute a priority between two students* — and chair-challenge standings are exactly that. The item asked whether to adopt a sibling app's ground rule while our own charter had already refused it, which is the stronger authority. **And the content half was already covered**: `voice.py` refuses `evaluative_praise`, `peer_comparison` and `ordering_two_students` in prose, with a policy version stamped on every refusal.

**What neither covered is what this closes: a leaderboard is not prose.** It is a sorted list, and no text rule can see one — `ORDER BY minutes DESC` produces no sentence to refuse. The enforcement had to be structural, and the lane model already supplied it: **every own-work statistic reads one lane and every comparison needs two, so W-3's seal already forbids the ranking.** §13 never noticed because it filed the question under content. `_one_lane()` is the middle and it raises rather than filtering, because a filtered aggregate returns a number that looks like an own-work statistic and is not.

**W-7 had no implementation anywhere** — quoted in four documents, enforced by nobody, rule 18's distinction with nothing on the enforcement side. `records/conflict.py` is the type that makes it structural: an `Escalation` **cannot carry an order**, there is no field for one, and reaching for `.recommendation` raises with the clause attached rather than returning `None` for somebody to paper over. It covers both halves of refusal 6, including the frequent one — a student's interest against staff convenience.

**~~10 · Whose consent governs which surface~~ (§13)**
**State: written 2026-07-30. `records/consent.py` is canonical.**

**The axis is not "is this the data subject."** That was the obvious reading and it is wrong on §13's own example — a *parent* is not the data subject and fits the session model cleanly. The axis is **whether this principal holds the authority the consent is about**: `self` and `guardian_of` hold it and are asked at the door under SAFE's session-expiring model; `staff_of`, `director_of`, `judge_at` and `clinician_for` exercise an authority granted elsewhere and are never prompted.

**It is rung-dependent for the subject**, which falls out of item 12 rather than being invented: a minor holds the authority over their own record to `L3` and not above, so the same principal on the same lane is governed by the session model for a call time and the delegated model for a diagnosis. **And `UNKNOWN` is not askable** — the counterintuitive half, since a prompt feels like the conservative move when unsure. It is not: a prompt shown to someone who does not hold the authority manufactures a consent record that looks valid, which is §13's *"eventually ask the wrong person"* arriving as a safety feature.

### What is not on this list

Authorization, consent chains, egress purity, the disclosure log, and the acoustic model. Those exist and are, by every account read, stricter than this document originally proposed. The work ahead is mostly **binding** — connecting what is built to a domain — rather than building. Item 0 exists because that sentence is itself a claim assembled from prose.
