# Scout 02 — Traffic-analysis resistance & metadata minimization for the drop

Slice: padding to size buckets, cadence uncorrelated with events, identical sends to both
guardians, and a **written statement of what the defense does not hide, with a test asserting it**.
Grounded in `docs/ARCHITECTURE.md` §4.1 (SMS carries signals, never records; the send list is an
access-control surface) and §4.2 (option (b) mailbox relay; the `corpus-lens` custody-from-keystroke-
timing precedent; "padding to size buckets and flushing on a fixed schedule is not an optional
hardening").

---

## 0. The finding that reorders everything else

**At this scale the strongest available design is also the cheapest, so almost every project below
is overkill and should be read for mechanism, not adoption.**

Derived, not quoted — computed in this session from the brief's own parameters (200 households, a
handful of transactional interactions per family per year, taken as 6):

| Design | Envelope | Per-client/yr | Server egress/yr |
|---|---|---|---|
| Broadcast the **entire** weekly batch to every client (trivial PIR) | 4 KiB | 4.7 MiB | 0.92 GiB |
| Broadcast the entire weekly batch to every client | 16 KiB | 18.8 MiB | 3.66 GiB |
| Broadcast the entire weekly batch to every client | 20480 B (Mixmaster's size) | 23.4 MiB | 4.58 GiB |
| Constant-rate: 1 fixed envelope per household per weekly slot, always | 4 KiB | 0.20 MiB | 0.040 GiB |
| Constant-rate: 1 fixed envelope per household per weekly slot, always | 16 KiB | 0.81 MiB | 0.159 GiB |

Weekly system-wide volume is ~23 messages. **A design where every client downloads every envelope
every week costs under 20 MiB per family per year.** That is the information-theoretic optimum for
recipient privacy — the drop learns *nothing* about who a message is for, because everyone fetches
everything — and it is achievable with a static file and a cron job. Every PIR scheme, mixnet, and
padding state machine below exists to make this affordable at millions of users. We have 200.

Corollary: **do not build a mixnet, do not build PIR, do not adopt a padding state machine.** Build
a fixed-size envelope, a fixed weekly slot clock, an unconditional per-guardian-edge write, and a
broadcast fetch. Then spend the saved effort on the honest statement and its test, which is the part
nobody ships.

---

## 1. Ranked table

Verification note: GitHub and `raw.githubusercontent.com` were reachable this session; the GitHub
API, `spec.torproject.org`, `docs.cwtch.im`, `docs.strongswan.org`, `linddun.org`, `wikipedia.org`
and `wsjt.sourceforge.io` were all refused by the egress proxy (403 on CONNECT). Rows marked
**(spec-only)** were confirmed from search results and cross-references, not by fetching the primary
source; rows marked *license unverified* mean the repo page showed a LICENSE file without naming it.
Star counts and commit counts are as shown on the repo page at fetch time.

| # | Project | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | `agl/pond` | Messaging system: everything padded to a **fixed 16 KiB**, connections **exponentially distributed** in time, identical traffic profile per connection | *unverified* (Go) | **In stasis** — README: "Pond is in stasis… new users should look elsewhere" | The whole §4.2(b) design, exactly | **steal-the-idea** (the design is the spec we want) |
| 2 | `freedomofpress/securedrop-protocol` | 3-endpoint protocol (send/fetch/download); sources and journalists issue **structurally identical requests**; messages padded to fixed size; server pads to a **fixed number of messages**; receiver generates **fake challenges** for non-existent messages; has a **"Known Limitations"** section | AGPL family (repo) | Active; formal analysis Jan 2025, spec v0.2 | Closest architectural sibling; the fetch design and the disclosure practice | **adopt (design) + steal (docs)** |
| 3 | `Whonix/kloak` | Keystroke-timing anonymizer; random delay up to `-d` ms (default 100 ms) | BSD-3-Clause, C, 96★ | Maintained by Whonix (upstream `vmonaco/kloak` is not) | **The disclosure template.** Has a literal **"When does it fail"** section: too-small delays, held-key repeats, stylometry, higher-level behavioural patterns; states "kloak does not protect against all forms of keystroke biometrics" | **adopt the doc pattern** |
| 4 | `threatcl/threatcl` | Threat model as **HCL text files**, `threatcl validate` in CI, org-wide **invariants** ("all internet-facing features must document audit logging"), JSON/OTM export, GitHub Action | MIT, Go, 463★ | Active, 344 commits | The **named middle** (§16 / CLAUDE.md #12) between the written statement and the test | **adopt** |
| 5 | `gchers/fbleau` | Estimates **information leakage in bits** of a black box from a CSV of `(secret, observation-vector)` rows, via ML-error/leakage equivalence; picks the faster-converging of NN and frequentist estimators | MIT, Rust + Python bindings, 10★ | Small but installable (`cargo install fbleau`, `pip install fbleau`) | Turns "we think timing is hidden" into a **number in CI** | **adopt as test instrument** |
| 6 | `cmla-psu/statdp` | "Statistical Counterexample Detector for Differential Privacy" — generates test databases and hunts counterexamples to a claimed privacy guarantee | MIT, Python, 28★ | Low commit count, usable | CLAUDE.md #19 verbatim: a guard that cannot be shown to fail has not been shown to work | **steal-the-idea** (adopt if we ever assert an ε) |
| 7 | RFC 8467 — EDNS(0) padding policies **(spec-only)** | Recommends padding queries to a multiple of **128 octets**, responses to **468 octets**; chosen by an explicit **"cost to attacker" (% of pairs in the same size bucket) vs "cost to defender" (size expansion)** evaluation | IETF | Published Oct 2018, Experimental | **How to justify our bucket size in writing**, with a metric instead of a vibe | **steal the method** |
| 8 | `maybenot-io/maybenot` | Padding/blocking **state-machine framework** descended from Tor's circuit-padding framework and WTF-PAD; crates: framework, FFI, **simulator**, machines, gen, CLI. Ships in Mullvad's DAITA | MIT **and** Apache-2.0, Rust, 162★ | Very active | Absurd overkill as a live defense. The **simulator** is the interesting part: takes a real base packet trace, emits the defended trace | **steal-the-idea (simulator)**, do not adopt the framework |
| 9 | `katzenpost/katzenpost` | Production-oriented mixnet. **Pigeonhole**: "encrypted, append-only streams composed of **fixed-size, padded Boxes**" sharded by consistent hashing, with separate read and write capabilities; decoy traffic generator; **explicitly ephemeral** (Boxes GC'd after ~2 weeks) | AGPL-3.0, Go, 156★ | Active (8,354 commits) | The dead-drop data model: read-cap/write-cap split + fixed-size Boxes maps cleanly onto per-guardian mailboxes | **steal-the-idea** |
| 10 | Signal sealed sender + Martiny et al. attack **(spec-only)** | Sealed sender hides the sender; the attack recovers communicating pairs and whole groups because **delivery receipts** fire predictably and cannot be disabled | — | Published; Signal unchanged on receipts | **The cautionary tale we are one design decision away from.** Any "read receipt" / "guardian opened the form" feature reintroduces the leak the padding removed | **read-only interest (as a prohibition)** |
| 11 | NIP-59 gift wrap (`nostr-protocol/nips/59.md`) | "clients SHOULD randomize `created_at` in up to **two days in the past** in both the seal and the gift wrap"; independent random timestamps per layer | public-domain-ish spec | Live, widely implemented | A three-line, real-world, deployed rule for **timestamp decorrelation** across nested envelopes | **adopt (the rule)** |
| 12 | RFC 9347 IP-TFS / AGGFRAG **(spec-only)**, with strongSwan support | Traffic-flow confidentiality by **fixed-size packets at a constant send rate** in an IPsec tunnel; aggregates/fragments inner packets to fill the constant rate. Non-congestion-controlled mode sends at a fixed rate regardless of loss | IETF; strongSwan is GPL-2.0 | RFC 2023; strongSwan documents AGGFRAG/IP-TFS | The **off-site staff mesh-VPN path** of §4, not the parent path. Also: the canonical statement that constant-rate is a legitimate, standards-track control | **read-only interest → possible adopt for staff tunnel** |
| 13 | `brave/sta-rs` (STAR) | Threshold aggregation: a submitted value is **only recoverable if at least k clients submitted the same value** | MPL-2.0, Rust, 62★ ("not audited") | Active, 799 commits | **k-threshold flushing**: do not release a batch containing fewer than k households | **steal-the-idea** |
| 14 | `scidsg/hushline` | Self-hostable anonymous tip line, Docker Compose, Tor onion option, in-repo `docs/THREAT-MODEL.md` that says out loud: "traffic correlation by powerful adversaries remain out of scope" and "Conversation participants, timestamps, unread/activity state, and message counts remain server-visible metadata" | AGPL-3.0, Python/Flask + JS, 130★ | Very active (6,052 commits) | Nearest **deployable** sibling in our language; and a second worked example of the honest statement | **read the code + steal the doc** |
| 15 | `dedis/purb` (Padmé) | Length-hiding padding: round up so the length has ⌊log₂ l⌋ − ⌊log₂⌊log₂ l⌋⌋ − 1 trailing zero bits | BSD-3-Clause, Go, 30★ | 142 commits, quiet | Size bucketing. **But see §2.3 — Padmé is the wrong tool here** and I computed why | **read-only interest** |
| 16 | Tor circuit-padding framework / `padding-spec` **(spec-only)** | Client+middle-relay padding state machines, three states (Start/Burst/Gap) + END, negotiated per circuit; generalization of WTF-PAD | Tor (BSD-3) | Shipped in tor | Ancestor of #8; the design vocabulary (machine, state, histogram) if we ever need more than one cadence | **read-only interest** |
| 17 | `vuvuzela/vuvuzela` | Metadata-private messaging; README concedes it **cannot** encrypt idle-user and active-user counts and instead **adds differentially-private noise** to them | AGPL-3.0, Go, 2.5k★ | **Last pushed 2019**; org has no Karaoke/Stadium code | The honest framing to copy verbatim: *here are the two things we cannot hide, here is the noise we add instead, and yes this is less privacy than hiding them* | **steal the framing** |
| 18 | `UCL-InfoSec/loopix` | Loopix reference implementation: clients emit **loop** cover traffic (back to self, detects active attacks) and **drop** cover traffic, at Poisson rates independent of user activity | BSD-2-Clause, 72★ | Research code, quiet | The distinction between cover traffic that only pads and cover traffic that also **detects** an attacking relay (loops) | **steal-the-idea (loops)** |
| 19 | `privacylab/talek` | Private publish/subscribe with **hidden access patterns** via information-theoretic PIR; "topic handles" = a stream from one author to a few readers | MIT, Go, 52★ | 574 commits, quiet | Needs ≥3 **non-colluding** servers → structurally incompatible with "on-prem single box". The **topic handle** abstraction is still the right shape for a guardian mailbox | **read-only interest** |
| 20 | `ahenzinger/simplepir` | Single-server PIR, ~10 GB/s/core, but **16–121 MB one-time client download** plus ~245–345 KB per query | MIT, Go + C, 100★, "research prototype" | Active-ish | Single-server PIR is the only PIR shape our topology allows — and its client hint alone costs more than a **year** of broadcasting the whole mailbox (§0) | **read-only interest** |
| 21 | `Bitmessage/PyBitmessage` | Every message floods to every node; recipient identity hidden because everyone tries to decrypt everything; PoW for spam control | MIT, Python, 2.9k★ | Long-lived, 4,142 commits on v0.6 | **The design §0 says we should actually build**, minus the P2P and the PoW. Proof that flood-to-all is a real deployed answer, not a thought experiment | **steal-the-idea** |
| 22 | RFC 9458 Oblivious HTTP **(spec-only)** | Relay sees the client IP but not the request; gateway sees the request but not the client; neither can link them | IETF; multiple implementations | RFC 2024, deployed (Mozilla, Google Safe Browsing, Apple) | We have **one box**, so we cannot get the role split. But OHTTP is the standardized, citable way to state the drop's design brief: *who* and *what* must not meet in one place | **read-only interest** |
| 23 | `SabaEskandarian/Express` | Metadata-hiding dead drops for whistleblowers, 2 servers | Go + C, 20★ | 91 commits; README: "**DO NOT USE THIS SOFTWARE TO SECURE ANY SORT OF REAL-WORLD COMMUNICATIONS!** … It is full of security vulnerabilities" | Two-server assumption fails on-prem. Cited here mainly as an exemplary self-limiting README | **read-only interest** |
| 24 | Mixmaster **(spec-only)** | Every packet is **exactly 20480 bytes**, always 20 headers, payload padded to a constant 10236+4 bytes; anything larger is chunked | historical | Effectively dead | The oldest and bluntest size-bucket design: **one bucket**. Chunk, don't grow | **steal-the-idea** |
| 25 | `nymtech/nym` | Production mixnet, Sphinx packets shuffled through mix layers | GPL-3.0 (apps) / Apache-2.0 or MIT (libs), Rust, 1.8k★ | Very active, 11,048 commits | Absurd overkill; a token-incentivized public network is the opposite of "survive the vendor disappearing" | **read-only interest** |
| 26 | `briar/briar` | Mirror of `code.briarproject.org`; syncs over Tor, "protecting users and their relationships from surveillance" | Java, 668★ | Active, 7,609 commits | Relationship-graph hiding for non-technical users; but requires an installed app per family | **read-only interest** |
| 27 | `arx-deidentifier/arx` | k-anonymity, ℓ-diversity, t-closeness, δ-presence, (ε,δ)-DP over tabular data; Maven-consumable core | Apache-2.0, Java, 732★ | Active, 4,306 commits | **Audit the send log itself**: is the per-slot send table k-anonymous over households? Java is a bad fit for a Python repo | **steal-the-idea** |
| 28 | `nilmtk/nilmtk` | Non-intrusive load monitoring toolkit: disaggregates a household's single meter trace into appliance-level events | Apache-2.0, Python, 942★ | Active, 1,918 commits | **The attacker's toolkit, and therefore our test harness pattern.** Occupancy-from-meter is the same inference as custody-from-cadence | **steal-the-idea (build the adversary)** |
| 29 | `kgoba/ft8_lib` | FT8/FT4 encoder/decoder in C for microcontrollers | MIT, C, 291★ | 114 commits | FT8 is a **fixed-length transmission in a fixed slot on a shared clock** — a deployed, decades-refined constant-rate channel used by non-technical operators. See "weirdest" §4 | **steal-the-idea** |
| 30 | `psal/anonymouth` | Adversarial-stylometry tool: shows which stylistic features to change to defeat authorship attribution | AGPL-3.0, Java, 1.9k★ | Minimally maintained | The disclaimer is the artifact: "**WE CAN IN NO WAY GUARANTEE THAT YOUR DOCUMENT IS ANONYMOUS OR NOT ANONYMOUS**" | **read-only interest** |
| 31 | Anonymity Trilemma (eprint 2017/954) **(spec-only)** | Proof: strong anonymity, low bandwidth overhead, low latency — choose two | paper | IEEE S&P 2018 | The citation that makes our written statement defensible rather than apologetic: we *chose* latency | **read-only interest (cite it)** |
| 32 | `Yawning/obfs4` | Censorship-circumvention transport, "look-like-nothing" | GPL-3.0, Go, 202 commits | Maintained-ish | **Negative example.** The README describes what it is and is silent on limitations, threat model, and what it does not hide — the exact gap CLAUDE.md #18 forbids | **read-only interest (as anti-pattern)** |

---

## 2. Top finds, with the concrete transplant and its cost

### 2.1 `agl/pond` — the design already exists, and it is dead, which makes it safe to copy

Pond's technical doc is the closest thing to a written specification of what §4.2 is asking for.
Two mechanisms, stated plainly: *"The actual messages between the user and the server might be very
small, but those messages will be padded to 16KB before being encrypted"* and, at the application
layer, *"Messages are protocol buffers which are padded to a fixed size (currently 16KB less 512
bytes)"*. Then the cadence: *"The time between each connection is exponentially distributed"* — and
critically, the **reason**, which is not the reason I expected: *"The connections are randomly timed,
rather than having a constant period, in order to avoid the server learning when the user is sending
messages."* Pond deliberately rejected a constant period, because a constant period plus a
send-triggered extra connection is worse than pure Poisson.

And then the disclosure, in the same document: *"Since a global, passive attacker can deanonymise
Tor, that attacker is capable of violating this assumption and breaking Pond"* and *"An attacker who
can monitor the network of the server **and** the user can tell when the user is sending messages."*
That is the artifact §4.2 wants — a limit stated in the design doc, in the author's own voice.

**Transplant.** Adopt three constants and one prohibition: (a) one envelope size, 16 KiB, chunk
anything larger; (b) client fetch/put on a schedule drawn from the client's own clock, not triggered
by a user action; (c) the put happens on the schedule whether or not there is anything to put — the
"nothing to say" envelope is indistinguishable from the "signed medical form" envelope; (d) never add
a feature that causes an extra connection.

**Cost.** 0.81 MiB per household per year at one 16 KiB envelope per weekly slot (derived, §0). The
real cost is latency: a parent who signs a form on Tuesday sees it land at the hub at the next slot.
That is acceptable for the 5% transactional traffic §4.1 carved out, and unacceptable for anything
else — which is precisely why §4.1's split is load-bearing for this whole defense. **If any
notification ever migrates from SMS onto the drop, the cadence has to be re-argued.** Worth writing
into the tombstone/decision record now.

**Caveat, blunt:** Pond is in stasis and says so; we are copying a design, not depending on code.
Its Go implementation is not a dependency candidate.

### 2.2 `freedomofpress/securedrop-protocol` — the closest sibling, and it already does the two hardest things

Two mechanisms here are directly transplantable and neither is obvious.

First, **role symmetry**: *"messaging protocol steps are role-agnostic and turn-specific… sources and
journalists execute the same fetching step (5), sending step (6), and receiving step (7), in any
order."* Sources and journalists are indistinguishable on the wire. Our analogue is guardian versus
staff versus the hub itself — if the director's client speaks a different dialect to the drop than a
guardian's client, the drop learns roles, and roles plus timing is most of the custody inference.

Second, and this is the one to steal: **the fetch is padded on the server side, and the client emits
fake challenges.** *"the server pads to fixed number of messages"*, and the receiver generates
challenges for messages that do not exist. This is the read side of the problem, which padding the
*write* side does nothing about. §4.2 of our doc says "which mailboxes talked, when, and roughly how
much" — but a fetch is a talk. If a guardian's client asks "anything for me?" only when the app is
opened, the fetch pattern is the custody schedule even if every envelope is 16 KiB.

Third, the practice: an explicit **"Known Limitations"** section listing key-compromise
impersonation, the absence of quantum-resistant authentication and message-fetching, and a
scalability ceiling. Not an audit file, not a blog post — in `docs/protocol.md`, next to the design.

**Transplant.** (a) Constant-shape fetch: every client fetches every slot, and the response is always
the same number of envelopes (see §0 — at our scale, make it *all* of them and the problem
disappears). (b) One request grammar for every persona. (c) A `docs/` section titled with the words
"does not hide", modelled on their "Known Limitations".

**Cost.** Under the §0 broadcast design, near zero — the padding is free because the whole batch is
smaller than a photo. Under a per-recipient design, the cost is a fixed `N_max` envelopes per
response, and choosing `N_max` badly leaks the busiest week.

### 2.3 Padmé is the wrong tool for this job, and I can show the arithmetic

Padmé (`dedis/purb`, BSD-3-Clause) rounds a length up so that its binary representation has
⌊log₂ l⌋ − ⌊log₂⌊log₂ l⌋⌋ − 1 trailing zeros. It is the right answer when your objects span many
orders of magnitude and you cannot afford a fixed size — encrypted files at rest, PURBs, `age`-style
blobs.

I implemented the rule and measured it over 512 B – 4 MiB: **worst-case overhead 6.25% (at
L = 32769 B), and 305 distinct output sizes.** Three hundred and five buckets, across 200 households
transacting a handful of times a year, is not a defense — it is a fingerprint with a 6% tax. A signed
consent PDF and a scanned immunization record land in different buckets, and the bucket is a content
disclosure about a minor.

**Transplant.** Use Padmé *only* for the rare large object (an uploaded physical), and only **after**
it has been chunked into fixed 16 KiB envelopes, where it governs nothing observable. For the
transactional channel: **one size, one bucket**, Mixmaster-style. Record in the decision log that
Padmé was evaluated and rejected with this number, so nobody re-proposes it.

**Cost.** Chunking a 3 MB scan into 16 KiB envelopes yields ~192 envelopes, which is itself a
size signal unless the upload is spread across slots. This is a real unsolved corner: large uploads
are the one place where the fixed-size discipline visibly strains. Options are rate-limited
multi-slot upload (slow, honest) or a separate declared-large-object lane (fast, and a disclosed
leak). **This belongs in the "does not hide" statement either way.**

### 2.4 `Whonix/kloak` — the paragraph heading we should literally copy

kloak is a 96-star C program that inserts random delay between a physical key event and its delivery
to the application, defaulting to 100 ms because *"[it] was shown to achieve about a 20-30% reduction
in identification accuracy and doesn't create too much lag."* Note the shape of that sentence: a
number, a measured effect, and the cost. That is what a defense's documentation looks like when
someone has actually looked.

Then the section that matters: **"When does it fail"** — too-small delays; repeated keystrokes from a
held key are not obfuscated; stylometry still identifies you; higher-level behavioural patterns
survive. Concluding: *"kloak does not protect against all forms of keystroke biometrics that can be
used for identification."*

**Transplant.** A `docs/` section literally titled **"When does it fail"** (or "What the cadence does
not hide"), sitting beside the padding implementation, structured as: the parameter, the measured
effect, the residual, and the named test that pins each residual. Draft contents in §3 below.

**Cost.** None technically. The cost is political — writing down that a determined observer can still
tell an enrolled family from a non-enrolled one is the kind of sentence procurement reviewers quote
back. Worth it: CLAUDE.md #13 (absence surfaces as `unknown`) and #18 (say "enforcement" or "ledger")
both point the same way, and `corpus-lens` has already set the in-fleet precedent §4.2 cites.

### 2.5 `gchers/fbleau` + `cmla-psu/statdp` + `nilmtk` — how to make the test a mutation test, not a green tick

CLAUDE.md #19: a guard that cannot be shown to fail has not been shown to work; acceptance is
mutation. For a traffic defense that means the test needs an **adversary**, and the adversary needs
to succeed when the defense is off.

Three sources, three roles.

`nilmtk` (Apache-2.0, Python, 942★) supplies the *pattern*: the NILM literature's whole game is
inferring household occupancy from a single aggregate meter trace, which is structurally the same
inference as custody-from-cadence — one low-dimensional time series, one private schedule. The
transplantable practice is that the community built and maintains the **attacker's** toolkit as
first-class open-source infrastructure, and evaluates every defense against it. We should ship the
attacker in `tests/`.

`gchers/fbleau` (MIT, Rust with `pip install fbleau`) supplies the *number*. It consumes a CSV whose
first column is the secret and whose remaining columns are the observation vector, and estimates
leakage. Feed it `(custody_pattern_label, [slot_index, envelope_count, byte_count, fetch_count])` and
it reports how many bits the drop's view carries about the custody label. That converts "we padded
it" into a figure in CI — and satisfies CLAUDE.md #17, because the figure is derived from the tree
rather than asserted in prose.

`cmla-psu/statdp` (MIT, Python, 28★) supplies the *stance*: it is a counterexample hunter for privacy
claims. We are unlikely to assert a formal ε, so this is steal-the-idea rather than adopt — but if
the batching ever gains a noise parameter (Vuvuzela-style, §2.6), StatDP is how you find out the
claim is false.

**Cost.** A `dev` extra with `scikit-learn` (and optionally `fbleau`), plus a synthetic-household
generator. Real risk: **flaky privacy tests.** A classifier-AUC assertion with a tolerance band will
go red on an unrelated change and get quarantined, at which point the guard is a ledger, not
enforcement (#18). Mitigation: fixed seeds, fixed trial counts, and the assertion expressed as a
bound on a many-trial mean, with the mutation arm (defense off ⇒ adversary wins) as a required
companion in the same test file.

### 2.6 `vuvuzela/vuvuzela` — the exact rhetorical move for what cannot be hidden

Vuvuzela's README does the thing: it names two quantities it **cannot** encrypt — the number of idle
users and the number of active users — says the servers therefore *"generate noise that perturbs this
metadata so that it is difficult to exploit,"* and then concedes that noise provides *"less privacy
than encrypting all of the metadata."* Named residual, named mitigation, named cost. Last pushed
2019; there is no Karaoke or Stadium code in the org, so those remain papers.

**Transplant.** Our irreducibles are the same shape: the count of enrolled households, and whether a
given household's client checked in this slot. We cannot hide either with 200 mailboxes on one box.
So: state them, and where we mitigate, say by how much. The Vuvuzela three-part sentence is the
template.

**Cost.** None. It is a paragraph.

### 2.7 The one design decision this slice must escalate

"Send to both guardians identically" and §4.1's rule that *"a guardian under a contact restriction
must not receive"* are in direct tension. If the restricted guardian's mailbox is simply skipped,
the **envelope count per student per slot** is the restriction — which is to say, the drop learns the
custody order from the very control designed to enforce it. Discovered while working out the write
path; flagging rather than deciding, because it is a §7.4 W-7-adjacent judgement about a named
student.

The mechanism that resolves it exists (Katzenpost's read-cap/write-cap split, §1 row 9): write an
envelope to **every** live guardian edge every slot unconditionally, and let the restricted edge hold
a well-formed envelope the holder has no capability to open — or that decrypts to a no-op. Uniform on
the wire, empty in effect. But "we deliberately deliver an undecryptable envelope to a
court-restricted guardian" is a sentence a human has to approve, it interacts with the dated
`invalid_at` predicate of §7.1, and it must never be describable to a guardian in fleet nouns.
Escalate to the §7.1 work, do not build it in this slice.

---

## 3. The deliverable this slice is actually for

### 3.1 Draft: "What the cadence does not hide"

Written as bullets, each with a test name, so the statement and the suite are a pair with a middle
(CLAUDE.md #12). Every item is a real residual of the §0 design, not a hedge.

1. **That a household is enrolled.** A mailbox exists, and it fetches. Enrolment is visible to the
   drop and to any observer of the drop's host. Not mitigated.
2. **How many households are enrolled.** Batch size and mailbox count bound it. Not mitigated.
3. **Whether a household's client is reachable in a given slot.** A family on holiday stops
   fetching. This leaks absence, not custody — *provided* fetches are unconditional. The distinction
   is the whole defense and must be tested, not assumed.
4. **Anything on SMS.** The drop's padding covers the drop. §4.1's channel is plaintext at the
   carrier and the **send list is visible to the carrier** — a per-guardian send that fires on the
   days one parent has the student is the original disclosure, restated. The written statement must
   say that the cadence defense **does not extend to SMS**, and that SMS's own control is "send to
   both guardians on the same cadence."
5. **Emergency traffic.** Any authorized bypass of the slot clock (lightning hold, bus incident) is
   an observable event correlated with a real-world fact. Disclose the existence of the bypass and
   the conditions, or do not build it.
6. **Cumulative volume, if fetches are ever made conditional.** A household that transacts twice and
   one that transacts twenty times become distinguishable over a year the moment a client skips a
   slot for lack of content.
7. **That a connecting device belongs to a terpsi-music family.** One well-known host means the
   guardian's ISP and DNS resolver learn the association. Only Tor or an OHTTP-style role split
   (RFC 9458) addresses this, and neither is available on one on-prem box. Not mitigated.
8. **Large uploads.** See §2.3 — a multi-slot chunked upload is visible as a multi-slot chunked
   upload. Disclosed, not mitigated.
9. **The hub's own LAN traffic.** Out of scope; the direct path of §4 is a different threat model.

### 3.2 Draft: the test, and its mutation arm

`tests/test_traffic_shape.py`, pytest, no network:

- **Fixtures**: synthetic households. `HH_ALT` has alternating-weekend custody; `HH_SPLIT` has a
  Tuesday/Thursday pattern; `HH_QUIET` goes dark a fortnight a month. Drive the *real* enqueue and
  flush code paths, not a model of them.
- **Observation**: exactly what the drop can see — `(slot_index, mailbox_id, envelope_count,
  byte_count, fetch_count)`. Nothing else. If the test can see more than the drop, it proves nothing.
- **`test_custody_label_not_recoverable`**: a fixed-seed classifier over those features must not beat
  chance at the custody label, asserted as a bound on the mean over N seeded trials.
- **`test_defense_off_custody_label_IS_recoverable`** — the mutation arm, and the point of the
  exercise. With padding and the slot clock disabled by a test-only switch, the *same* classifier
  must exceed a high threshold. If it does not, the harness is measuring nothing and the suite fails.
  This is what makes the first test enforcement rather than a ledger (#18, #19).
- **`test_disclosed_residual_enrollment_is_detectable`**: asserts residual 1 above **is** detectable.
  A positive test on a disclosed leak. If a future change accidentally hides it, this goes red and
  someone updates the statement — which is how a declaration is kept from rotting (§16).
- **`test_statement_and_tests_reconcile`**: parse the "does not hide" bullet list out of the doc,
  assert every bullet names a test that exists and every such test is named by a bullet. This is the
  **named middle**. The repo already has the pattern to extend — `tests/test_section_refs.py`.
- Optional CI reporting step: emit the observation CSV and run `fbleau` to print estimated bits of
  leakage about the custody label. Report, do not gate, until the variance is understood.

`threatcl` (#4) is the upgrade path if the bullet list outgrows Markdown: the same statement as
validated HCL with org-wide invariants, checked by `threatcl validate` in CI.

---

## 4. Weirdest things I found

1. **`nilmtk` — smart-meter load disaggregation as the exact same attack.** An Apache-2.0, 942-star
   Python toolkit whose purpose is inferring what happens inside a house from one aggregate
   time series; the adjacent literature is explicitly about **occupancy detection** and
   battery-based load hiding designed to *"[create] a delusion that the home is always occupied."*
   Change the noun and that is our requirement sentence. The transplantable practice is that this
   community treats the **attacker** as maintained infrastructure and evaluates defenses against it.
   Absurd as a dependency; the single best argument I found for shipping the adversary in `tests/`.

2. **FT8, via `kgoba/ft8_lib` (MIT, C, 291★).** Amateur radio's dominant weak-signal mode is a
   fixed-length transmission in a fixed slot on a wall clock shared by every station on the band.
   Every transmission is the same duration and the same structure; you do not transmit when you have
   something to say, you transmit in your slot. It is a constant-rate, fixed-size, non-technical-user
   protocol with decades of field refinement and a microcontroller-sized implementation. The design
   §4.2 asks for has been running on shortwave for years. (Protocol constants live in a Princeton
   QEX paper the README links; I could not fetch it — the parameters above are the shape, not
   quoted figures.)

3. **`psal/anonymouth`'s all-caps disclaimer.** A 1.9k-star AGPL authorship-obfuscation tool from
   Drexel whose README shouts *"WE CAN IN NO WAY GUARANTEE THAT YOUR DOCUMENT IS ANONYMOUS OR NOT
   ANONYMOUS."* Note "**or not anonymous**" — it refuses to claim either direction. That is
   CLAUDE.md #13 (absence surfaces as `unknown`, never as a result) written in 1990s-web voice, and
   it is the correct thing for our statement to say about residuals we have not measured.

4. **`brave/sta-rs` — k-anonymity enforced by cryptography rather than policy.** A measurement is
   *unrecoverable* unless k clients submitted the same value; the threshold is not a rule the server
   follows, it is arithmetic the server cannot evade. Transplanted: refuse to flush a batch
   containing fewer than k households — and if a slot has one household's envelope, that is a
   disclosure whether or not the payload is sealed. "Enforcement, not ledger" (#18) as a
   cryptographic primitive.

5. **`Yawning/obfs4` as the anti-pattern, and Signal's delivery receipts as the cautionary tale.**
   obfs4 is a widely-deployed anti-censorship transport whose README explains what it is and says
   nothing about what it does not hide — the exact gap this slice exists to close. And sealed sender,
   the flagship metadata defense in the most-scrutinized messenger in existence, was substantially
   undone by **delivery receipts**, a helpful UX feature that fires predictably and cannot be
   disabled. The nearest-miss for us is obvious and named: a "guardian viewed the form" indicator
   would reintroduce, as a feature, precisely the timing correlation the padding removes.

---

## 5. Unverified / dropped — do not cite these as confirmed

- **Karaoke and Stadium** (DP-for-metadata and distributed metadata-private messaging): papers only.
  The `vuvuzela` GitHub org contains `vuvuzela`, `alpenhorn`, `crypto`, `internal`, `net`,
  `concurrency`, `configs` — **no Karaoke or Stadium code.**
- **WeFDE** (per-feature leakage measurement in bits for website fingerprinting): the repo path I
  tried 404s. Cannot confirm a canonical repository; not named as a candidate. `fbleau` covers the
  same need and is confirmed.
- **Herd / Aqua / Riffle / XRD / Trellis / Yodel / DP5 / Pung / Riposte**: not searched to
  confirmation before the session's web-search budget ran out. Likely paper-or-research-code only,
  and all fail the single-box constraint. Left as a lead for a follow-up scout.
- **LINDDUN** privacy threat modelling (its "Detectability" category is exactly this threat):
  `linddun.org` and Wikipedia were both refused by the egress proxy. Plausible and probably valuable
  as the documentation framework — **verify before citing.**
- **Tor `padding-spec` / proposal 254**, **RFC 8467**, **RFC 9347 + strongSwan AGGFRAG**, **RFC
  9458**, **NIP-59 timestamp rule**, **Mixmaster's 20480**, **the Martiny et al. sealed-sender
  attack**, **the anonymity trilemma**: all confirmed via search results and cross-references, but
  the primary sources were not fetched (proxy 403 or budget). Quotations attributed to them above
  come from search-result text, not from the documents. **Re-verify before any of them lands in
  `docs/`** — CLAUDE.md #17.
- `agl/pond` **license** and `jedisct1/rust-padme-padding` **license** were not confirmed (LICENSE
  file present, type not shown). Immaterial: neither is a dependency candidate.
- Python is this repo's language (`tests/test_section_refs.py`, pytest). Padmé is ~5 lines of Python;
  the Go/Rust libraries are references, not dependencies.
