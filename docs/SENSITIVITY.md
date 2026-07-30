# The sensitivity ladder — `L1`–`L5`

**Status:** definitions, proposed. This document is canonical for what the five
rungs *mean*. `docs/ARCHITECTURE.md` remains canonical for everything else and
is not to restate these definitions — §16's rule against the canonical/vendored
pair applies to this file as much as to any other.

**Why it exists.** §6 keys field classification onto this ladder and §15 makes
it one of three ordinal scales, but §18 item 1 records that nothing in the
fleet states what the levels *mean*. `willow-tech-manual` does not carry them.
Only behaviour is recorded. A ladder nobody has written down cannot classify a
field, which is why this blocks migration 001 and everything downstream.

**Addressing.** Rungs are addressed as `L1`…`L5`, never as bare integers, and
this document deliberately carries no numbered sections of its own — a `§N` in
this file always refers to `docs/ARCHITECTURE.md`.

---

## What was already fixed, before any of this was written

Three facts constrain the definitions rather than following from them. All three
are `P2 Cited` (§15) — taken from §6 and §15 of the architecture, which took
them from `marching-arts` PR descriptions. None has been confirmed against
source, and §18 item 0 applies in full.

| Fact | Source as cited |
|---|---|
| At `L3` and above the payload is `NULL` in the SELECT list; only a derived instruction is served | #112, via §6 |
| `L5` is never served to anyone under any grant | #112, via §6 |
| Sensitivity composes by `max` — a record holding one `L5` field is `L5` | §15 |

> **The first of those is now decided rather than cited. `L3`+ NULL is
> SCOPED — to principals without an entitlement edge. Decided 2026-07-30,
> closing §18 item 1a.**
>
> As quoted, "the payload is `NULL` in the SELECT list" is unqualified — it does
> not say *on which paths*. Read absolutely, a guardian could not be served
> their own child's name, which cannot be the shipped behaviour of a roster
> application. Scoped is the only coherent reading, and the definitions below
> now **state** it rather than assume it.
>
> **Why this stopped being a read.** It was filed as one file to open in
> `apps/marching-arts` and the highest-value item in the item-0 pass. That
> framing rested on treating #112 as an implementation to be consulted.
> `marching-arts` was a **spike** — a first test of whether the shape could
> stand up — so opening that file would have established what a prototype
> happened to do, which is not the same question. The rule was never decided
> anywhere; it was observed once and quoted as though settled.
>
> **Decided here, not inherited.** If `marching-arts` turns out to have
> implemented the absolute reading, that is a fact about the spike and does not
> reopen this. The rungs below are now canonical on their own authority.

---

## The five rungs

The scale answers one question: **how much of this may ever be rendered, and to
whom.** It does not answer what kind of data it is — that is the class
vocabulary in §6, which is an attribute mapped onto this ladder and never a
second ranking beside it.

Higher is **more restricted**. This runs opposite to `T0`–`T4` trust, where
higher is more privileged. That opposition is deliberate and is not to be
reconciled; see *Crossing to the trust ladder* below.

### `L1` — Open

Renderable to anyone, including outside the organisation, with no grant and no
session. Survives publication to a public website. Nothing about it becomes
sensitive by being combined with anything else at `L1`.

> *Worked example.* `Regional Championship · Oct 12 · Memorial Stadium · 7:15 pm
> · Northside Marching Band.` This is on a poster. Treating it as anything above
> `L1` produces a system that cannot tell parents where the bus is going.

### `L2` — Internal

Renderable to any authenticated member of the program without a per-subject
entitlement. Carries no individual identity and cannot be resolved to one by
anybody holding it. Operational data, inventory counts, repertoire, and
aggregates that have survived a re-identification check.

> *Worked example.* `Rehearsal · Tue 3:30–6:00 · practice field · Danzón No. 2 ·
> full ensemble.` Every member may see it; no member is named by it.

> **The re-identification check is the whole content of `DERIVED_ANON`.** An
> aggregate is not `L2` because it is an aggregate. "Three students on the
> Thursday trip declined the media release" over a section of four is a
> disclosure wearing a count. An aggregate drops to `L2` only after a check
> that it cannot be resolved to an individual, and until it passes it inherits
> the `max` of its inputs like anything else.

### `L3` — Attributed

Names or identifies an individual, or is trivially resolvable to one. Served in
full only to a principal holding a **current entitlement edge** to that subject
(§7's `guardian_of`, `staff_of`, `director_of`, `judge_at`, `clinician_for`).
On any path without such an edge the payload is `NULL` and, where an operational
need exists, a derived instruction is served in its place.

> *Worked example.* `Ben Alvarez · trumpet 2 · present at Tuesday's rehearsal.`
> His guardian and his staff see it. A judge at Saturday's event does not — and
> what that judge's session gets is not an error but the derived form: a count,
> a section, a chair number with no name on it.

### `L4` — Restricted

Identifies an individual **and** carries a category the law follows — health,
money, discipline, or their likeness. Served only to a principal holding a
current edge **and** a purpose declared for that category on entry (§7.2's
knock). Even for an entitled principal, the derived instruction is the normal
serving mode and the payload is the exception: the accommodation, not the
diagnosis.

> *Worked example.* `Ben Alvarez carries epinephrine for a tree-nut allergy.`
> What the bus chaperone's surface renders is *"one student on this vehicle
> has an epinephrine auto-injector in the blue medical bag; the trip binder
> names them."* The chaperone can act. The diagnosis was never on the screen.
> A staff member with a declared medical purpose gets the payload; the same
> staff member, on the same device, ten minutes earlier under an attendance
> purpose, does not.

> **This is the rung that makes the ladder worth having.** `L4` is not "`L3`
> but more so." It is the claim that most operational needs around sensitive
> categories are satisfied by an instruction rather than by the datum, and that
> serving the datum is a decision requiring its own declared reason. A design
> that renders the diagnosis to everyone who might need to act on it has not
> classified anything; it has added a label to a leak.

### Protected status — the categories that reach `L4` without a class

**Decided 2026-07-30, closing §18 item 11.** Item 11 asked whether §6's
vocabulary needs new classes for the categories §20 of the capability map
names. It does not. They reach `L4` through step 3 of *Classifying a new
field*, because **"a category the law follows" is a definition and the four
familiar examples are illustrative.** Read as a closed enumeration it would
make every future protected category a schema change, which is the wrong
failure direction for exactly the population this program is most obliged to
protect.

| Field carries | Rung | Served as |
|---|---|---|
| Confidential address program participation (Safe at Home) | `L4` | the substitute address, and the fact that mail routes differently |
| McKinney-Vento housing status | `L4` | the fee waiver, the transport arrangement, the instrument locker |
| Foster placement, and a change of placement | `L4` | the current contact edges, dated — never the placement history |
| Immigration or documentation status | `L4` | the trip requirement met or unmet — never the status |

Each is `L4` for the same reason `HEALTH` is: **the operational need is
satisfied by the instruction, and serving the datum needs its own declared
purpose.** A liaison acts on the locker without the housing status crossing a
screen. This is why `L5` is wrong for all four — enforcement-only is never
served, and a status nobody may render cannot produce a fee waiver.

> **The chosen-name inversion.** Item 11 listed *"chosen name distinct from the
> SIS legal record"* among the five, and its own prose already named the danger
> correctly — *"a legal name served to the program-printing path is the
> outing."* Made explicit, because the two halves pull opposite ways:
>
> - **The chosen name is not elevated.** It stays at its class rung. The harm
>   here is *non-use* — a printed program that deadnames a student — and
>   restricting the chosen name makes that **more** likely, because the
>   program-printing path then falls back to the legal name it can still reach.
> - **The SIS legal record is `L4`**, by this section. It is the protected
>   half.
>
> Four of item 11's five are facts to protect. The fifth is a fact to *use*,
> whose counterpart is the fact to protect. Classifying it like the other four
> would have inverted the guarantee while appearing to strengthen it.

**What this does not license.** Reaching `L4` by clause rather than by class
means a human decides at schema-definition time, and step 5 still applies — the
§6 class is recorded alongside the rung, and these fields remain `PII_MINOR` or
`PII_GUARDIAN` for egress and retention. The rung moved; the class did not.

### `L5` — Enforcement-only

Never rendered on any surface, to any principal, under any grant, including the
director and including root. Consumed only by the code that enforces something.
There is no purpose that unlocks it and no signature that widens it — this is
the sensitivity counterpart of §13's prohibited scopes, which are invalid even
signed by root.

> *Worked example.* **The contents of a court order restricting a guardian's
> contact.** Its *effect* is load-bearing on every read and every outbound send:
> the restricted guardian is not on the list, per §7.1, and the predicate
> derives that on each evaluation. Its *content* — the findings, the
> allegations, the history — is rendered to nobody in this system. A band
> program needs the restriction enforced. No one in a band program needs the
> findings, and the director least of all, because the director is the person
> most likely to be in a room with both parents.

**Three rules put a record at `L5`.** The class vocabulary in §6 does not reach
this rung — no data class maps to `L5` — so it is assigned per record, by rule:

1. **Key material and authentication secrets.** Vault keys, HMAC secrets, the
   Ed25519 signing key, session proofs.
2. **The content of an external restriction** whose effect the system enforces
   and whose substance it has no business rendering — court orders, safeguarding
   directions, district directives naming a student.
3. **Any record whose rendering would reveal a refusal.** §7's indistinguishability
   guarantee is that a member who declined and a member who is absent produce
   the same rows, the same count, and the same subject list. A per-person
   declination record — a media release refused, a fee waiver taken, a consent
   withdrawn — is enforced and never shown, because a surface that can display
   it has re-created the signal the guarantee exists to suppress.

> **Rule 3 has a seam with §8 and it should be named rather than discovered.**
> §8 requires that `MediaAsset` carry consent state as a first-class field.
> That field is a gate input and is legitimate. What is `L5` is the
> *per-person declination record* behind it, not the asset's publishability.
> The distinction to hold: the publishing path may ask *may this asset be
> published* and receive an answer; no path may ask *who declined* and receive
> one. If those two ever collapse into one query, the guarantee is gone and the
> `MediaAsset` field is where it will happen.

---

## The class-to-`L` mapping

§6 requires this mapping be "written down once, in the schema, rather than
inferred per feature." Here it is once, and the schema is to reference it rather
than restate it.

| Class (§6) | Rung | Note |
|---|---|---|
| `PUBLIC` | `L1` | Performance dates, venue, ensemble name |
| `INTERNAL` | `L2` | Non-identifying operational data |
| `DERIVED_ANON` | `L2` | **Only after the re-identification check.** Inherits `max` of inputs until it passes |
| `PII_MINOR` | `L3` | Anything identifying a student |
| `PII_GUARDIAN` | `L3` | Contacts, addresses, relationships |
| `HEALTH` | `L4` | Allergies, medications, conditions, emergency instructions |
| `FINANCIAL` | `L4` | Balances, payment references |
| `MEDIA_MINOR` | `L4` | Photos and recordings containing identifiable students |

Eight classes, four rungs. `L5` is unreached by class and assigned by the three
rules above.

**`quiet-corner`'s vocabulary corroborates this**, which is the reason §7.3 says
those eight fields "map cleanly onto the L-ladder" and are worth taking. Mapped
out, so that the claim is checkable rather than asserted:

| `session_scope` field | Rung |
|---|---|
| `roster_visible` | `L3` |
| `attendance_visible` | `L3` |
| `standards_visible` | `L3` |
| `knowledge_graph_visible` | `L3` |
| `parent_contact_visible` | `L3` |
| `iep_visible` | `L4` |
| `behavior_visible` | `L4` |
| `archive_visible` | `max` of contents |

Two independently-derived partitions landing on the same cut is the strongest
evidence available here that the cut is in the right place. It is also the
extent of the evidence: both were produced by the same author, and neither has
been run.

---

## Rules that travel with the ladder

**Composition is `max`, everywhere.** A record is the `max` of its fields; a
row set is the `max` of its rows; a join is the `max` of its sides; a projection
does not lower a rung. A transcript inherits its source audio (§8.2 — nothing
about "it's only text now" declassifies it). The only operation that lowers a
rung is an explicit, dated, human-sealed declassification.

**Never a bare integer, never a colour alone.** `L3`, not `3`. `if level >= 3`
is correct against this scale and catastrophic against `T0`–`T4`, and it reads
perfectly in review either way (§15). No rung is encoded by colour without its
prefix beside it; the ASCII path in `safe-design` must carry the same
distinction the colour does.

**Absence fails closed, twice over.** An unclassified field is a **build
failure**, not a default — the same posture as §6's manifest test that fails the
build rather than warning. If one reaches runtime unclassified anyway, it reads
as `L5` and is not served. A classifier that errors returns `unknown` and
denies; it never returns `L1` (CLAUDE.md rule 13, §6's *absence is not consent*).

**Declassification is an act with a name and a date.** No rung falls by
inertia, on a schedule, or as a side effect of aggregation. This mirrors §15's
finding that `P2` decays silently and nothing detects it — the sensitivity
ladder is built so it cannot decay at all, because the failure direction here is
disclosure rather than a stale citation.

**Majority does not declassify.** A student turning eighteen changes who holds
the entitlement edge, not what the data is. W-6 transfers the lane whole, with
history intact and keys to the subject; the rungs on those fields are unchanged
by the transfer. Conflating the two would mean a graduate's medical history
became `L3` on a birthday.

---

## Crossing to the trust ladder

§15 requires that the mapping from a sensitivity rung to the trust rung it
demands live in exactly one place and that every gate call it. This is that
place. It is written in the shape of `law-gazelle`'s permission table (§7.2),
which is the fleet's worked example of the same crossing.

| Rung | Minimum trust | Edge required | Purpose required |
|---|---|---|---|
| `L1` | `T0` | no | no |
| `L2` | `T1` | no | no |
| `L3` | `T1` | **yes** — current edge to the subject | no |
| `L4` | `T2` | **yes** | **yes** — declared for the class, on entry |
| `L5` | — | never served | — |

Three things this table is not:

- **It is not the export rule.** Export is a distinct permission class, gated
  and announced (§7.2's *narrate the read, gate the export*). Everything at
  `L3` and above is approval-required on export under §6's tier 2 regardless of
  what this table permits for a read. Reading a roster and taking one are
  different acts and this table governs only the first.
- **It is not enforcement.** It is a mapping. Whether it enforces depends on
  whether a harness routes every read through it — §7.2's *enforcement or
  ledger, say which*. Wired into `Store.predicate` alongside the existing
  authentication-at-the-read (#127), it enforces. Consulted politely by callers,
  it is a ledger with opinions.
- **It is not a licence to compare rungs numerically.** `L3` requiring `T1` is a
  lookup in this table, not arithmetic between two scales. There is no
  expression in which an `L` and a `T` are both operands.

> **The rung names in the trust column are `P2 Cited` and partially inferred.**
> §15 gives the endpoints — `T0` Exiled, `T4` Elder. `law-gazelle`'s table
> (§7.2) names Rookie, Steady, and Veteran without numbering them. The
> assignment of Rookie to `T1` and Steady to `T2` used above is the obvious
> reading and has not been checked against `willow-gate`. If the middle rungs
> number differently, this table's trust column shifts and its structure does
> not.

---

## Classifying a new field

1. **Can it be published?** → `L1`.
2. **Does it name, or resolve to, a person?** No → `L2`. Yes → continue.
3. **Does it carry a category the law follows?** No → `L3`. Yes → `L4`.
   Health, money, discipline and likeness are the common four. **They are
   examples of the clause, not the whole of it** — see *Protected status*
   below, which reaches `L4` through this step and not through a class.
4. **Would rendering it reveal a refusal, expose enforcement substance, or
   disclose key material?** → `L5`, by the rule that applies.
5. **Record the class from §6 alongside the rung.** The rung governs serving;
   the class governs egress policy and retention. Both are attributes of the
   field, set at schema-definition time, and neither is derivable from the other
   in the general case.

Step 4 runs last and overrides. A field can be `PII_MINOR` by class, `L3` by
step 2, and still land at `L5` because rendering it would identify who declined.

---

## What this document does not decide

- ~~**Whether the `L3`+ NULL rule is absolute or scoped to unentitled paths.**~~
  **Decided 2026-07-30: scoped.** See the top of this file. It moved out of
  this list rather than off it, because a reader who remembers the caveat needs
  to find where it went (rule 20).
- **Whether the class vocabulary needs a ninth member for `L5`.** This document
  assigns `L5` per record by rule instead, on the grounds that its three
  triggers have nothing in common as *kinds of data* — a signing key and a
  declination record are the same rung for entirely different reasons.
- **How a classifier evaluates step 3's general clause.** *Protected status*
  settles that the clause governs and the four examples do not bound it. It
  does not settle what checks that. A lookup table is mechanically verifiable;
  a general clause is a judgment, and rule 19 says a guard that cannot be shown
  to fail has not been shown to work. The likely shape is that the clause stays
  human-evaluated at schema-definition time and the *enumeration of decided
  cases* — the table above — is what the build checks, growing by human act.
  That is a real decision and it is not made here.
- **The numbering of the middle trust rungs.** See the caveat above.
- **Where the derived instruction for an `L4` field is authored.** That a
  diagnosis yields an accommodation is asserted here; who writes that mapping,
  whether it is per-field or per-record, and whether a machine may draft it
  (§8.2 says a draft is not a record) is a separate decision and a real one.
- **Retention.** Rungs govern serving. How long a thing is kept is the class's
  business and §11.1's.

---

## Provenance of this file

Written without access to any fleet repository — there is no organisation to
read them from, so §18 item 0's verification pass could not be run and cannot be
run from a remote session at all. Every claim here about what `marching-arts`,
`willow-gate`, `law-gazelle`, or `quiet-corner` actually do is `P2 Cited` at
best, sourced from `docs/ARCHITECTURE.md`, which sourced it from READMEs and
merged pull-request descriptions.

The definitions themselves are not cited and are not claimed to be: nothing in
the fleet defines these five levels, which is why §18 called for a document
rather than a decision. They are `P5 Assumed` in §15's register — asserted, with
a stated basis, and declared as such.
