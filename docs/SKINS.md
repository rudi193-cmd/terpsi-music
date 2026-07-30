# Skins — what else this contract fits

**Status:** exploration, `draft`, unsealed. Governs nothing.
`docs/ARCHITECTURE.md` governs. No human has reviewed a row.

§15 takes the word from `safe-design`, where it is precise: **a skin fills the
contract, never extends it**, and every token resolves in every skin. Taken
seriously, "what else could this wear" is two questions, and the second is only
answerable after the first:

1. **What is the contract** — the part of this design that is not about music?
2. **Which candidates fill it**, and, more usefully, **which ones strain it**?

A skin that fits comfortably teaches nothing. The finding is where the contract
bends, so every candidate below is recorded with the clause it strains rather
than with a verdict.

---

## 0. One skin has already been worn, and nobody set out to wear it

`docs/EXTERNAL-ARM.md` records a Postgres store for **versioned documentation
for coding tools**, built without knowledge of this repository and then measured
against it. Same shape: an observation of a claim at a pinned version, where the
load-bearing question is *"is this still true?"* and the failure being designed
against is that question answered with silence.

No minors. No guardians. No judges. No music. That is `P2` decay (§15) and
declaration-versus-enforcement (§16) arriving independently in a domain that
shares none of this one's nouns — which is the strongest evidence available that
the contract is separable from the domain. It was separated by accident, by
someone who did not know it existed.

---

## 1. The contract, in three tiers

They do not transfer equally, and sorting candidates without separating them is
how a design gets described as universal when only a third of it is.

### Tier A — institutional. Transfers whole, to anything holding records.

Nothing here is about minors. It is about an institution being honest about what
it knows, what it does not, and what left the building.

- Revocation is a dated predicate, never a delete (§7.1)
- Narrate the read, gate the export (§7.2)
- The knock: a declared purpose, reconciled against the outcome on exit (§7.2)
- Absence surfaces as `unknown`, never as a result (§6 of the architecture)
- A machine answer is a `draft` until a named human seals it, and a rejection is
  recorded as durably as an approval (§8.2, §16)
- The canonical store is read-only to the app; promotion is a human act (§5 of the architecture)
- Every pair gets a named middle in the same commit (§16)
- A guard that cannot be shown to fail has not been shown to work (§10)
- Prefixed ordinal scales; provenance labels an answer, never gates it (§15)
- The exit line — sovereignty is the ability to leave (§11.1)

### Tier B — the ward tier. Transfers only where owner ≠ subject.

**W-4 and W-5, and — on the evidence below — nothing else.** A ward may request
and never authorize; agency widens by signature and never by drift. Both govern
the mechanics of a steward holding keys for someone who holds none, and with no
ward there is nobody left for either sentence to be about. `corpus-lens` names
owner ≠ subject as the fleet's hardest open gap and scopes itself out of it
deliberately; this is the part of the design that sits in that gap.

### Tier C — the assessment tier. Transfers only where someone is judged, and the judgment becomes their opinion of themselves.

Commentary as the primitive with rubrics and scores as projections over it
(§8.1), diagnose-never-score (§24 of the capability map), and the whole of
Terpsi. SA-3 sits here **and** in Tier A; W-7 has been moved out entirely.

### The first version of this split was wrong in three places

It put all of W-1 … W-7 plus I-6 and I-7 in Tier B, and W-7 in both B and C.
Two passes run independently over the tree objected, and they agree:

- **Tier B was over-broad by eight clauses.** Graded one at a time against a
  world with no minor in it, W-1, W-2, W-3, W-6, W-7, I-6, I-7 and I-10 all
  survive unchanged. The decisive evidence is in the tree rather than in the
  charter: `docs/LANE-MODEL.md` line 48 already builds the schema
  person-general — *"One lane per person, not one lane per ward. W-1 requires
  lanes for wards. This extends them to everyone — staff, guardians, judges,
  clinicians."* The clause was discovered through a charter about wards and
  implemented as a rule about anyone the institution holds a record on.
- **W-7's dual membership was an axis error, not genuine.** Its forbidden act
  is computing a priority between two people; nothing in it requires a rubric
  or a judgment. The pull toward Tier C came from the youth-sports strain,
  which resembles assessment and is really scarce-resource allocation. The
  proof is in this file's own table: camp, scouting and church programs are
  scored A and B with no C, and they are where W-7 is exercised hardest — the
  bunk assignment, the last seat in the van. **W-7 belongs in B alone.**
- **SA-3 is broader in its source than the tier list allowed.** `CLAUDE.md`
  rule 4 forbids a standing cross-context score of *"a judge, clinician,
  student, or staff member"* — three of the four are not wards, and staff are
  not judged in any assessment sense. §13's own worked case is a judge's
  reliability curve, which resolves as owner == subject. It is A **and** C.

**I-6 and I-7 move to Tier A**, and the document already had the argument
without following it: §10 reaches into the same charter for I-12 to justify a
Tier A item. Nothing structurally separates I-12 from I-6 and I-7 — all three
sit above the ward clauses, and both read as ordinary due process between an
institution and anyone it holds power over. An adult chorus still owes a dated
disposition on a fee waiver, and still must not delete a member's account of
an incident.

**And one obligation has no home in any tier.** §17's template contract — every
instance runs the conformance suite, promotion writes a record — runs on a
different axis entirely: who *reuses the software*, not who the data contract
protects. Forcing it into Tier A would repeat the W-7 mistake in reverse.
Escrow (§5 of the architecture) and the three-key egress model
(§6 of the architecture) are smaller instances of the same thing:
institutional in character, and simply absent from Tier A's list.

**The tiers are the axes.** A candidate needing all three is a sibling. One
needing A and C but not B is an adult skin. A and B but not C is custodial —
and that combination is now the common case rather than the exception.

---

## 2. Domain skins — the contract holds, with named strains

| Candidate | The ward | The transient guest | Tiers | Where it strains |
|---|---|---|---|---|
| Youth sports club / travel team | Player | Referee, tournament official, showcase scout | A B C | **W-7, badly** — see below |
| Speech, debate, robotics, academic competition | Competitor | Judge, with a ballot | A B C | Least strain of any candidate here |
| Youth theatre | Cast member | Guest director, one-act festival adjudicator | A B C | Casting is W-7, episodic rather than weekly |
| Competitive dance, gymnastics, cheer | Athlete | Adjudicator, guest choreographer | A B C | `MEDIA_MINOR` becomes the primary artifact, not a byproduct |
| Camp, scouting, outdoor programs | Camper | Visiting instructor, contracted medic | A B | Offline stops being a mode and becomes the only mode |
| Church and community youth programs | Participant | Visiting leader, volunteer | A B | No SIS to import from, so the guardianship graph starts messy |
| Multi-agency wraparound / system-of-care coordination | Youth under a joint plan | Partner-agency caseworker, holding a case-length grant into another institution's lane | A B | **W-1/W-3 and SA-3 — refuses** |
| Youth chess and esports ranking circuits | Ranked competitor | Fair-play reviewer, granted backward into one closed match | A B C | **SA-3 — refuses** |
| Cadet corps — JROTC, Civil Air Patrol | Cadet | Liaison instructor: on-site daily, institutionally external, reporting up another chain | A B C | **W-7 and SA-3, by outside regulation — refuses** |
| Youth crisis text line, peer warmline | Texter, often anonymous | On-call supervisor paged into one escalated conversation | A B | **W-1/W-2 and §4.1 — no shape for it** |
| Child performer work-permit and earnings trust | Performer | On-set studio teacher, who outranks the production for the grant's duration | A B | W-4's guardian carve-out, inverted |
| Wilderness therapy, therapeutic residential placement | Participant, often placed against their wishes | State licensing inspector, adversarial by design | A B C | W-6's exit, against a structural incentive to withhold |

**Youth sports is the sharpest strain in the set, and it is worth stating
plainly.** W-7 says the system presents and a human decides where two wards'
interests collide. Chair placement in a band is episodic — a handful of decisions
a season, each one a discrete event. **A starting lineup is that same decision
made weekly, in public, and published.** The strain is not that the system might
compute a priority; it is that in this domain *the presentation is itself the
ranking*, and there is no neutral way to render a depth chart. Either the clause
is wrong for the domain or the domain cannot have the feature it exists for.
That is a genuine incompatibility, not a configuration, and it is the most
useful thing in this table because it is the first candidate that the contract
refuses rather than accommodates.

**Speech and debate fits better than music does, in one specific respect.**
Survey finding 1.10 — *rubrics need versions, and a seal must cite one* — is
already how that domain operates: ballots are versioned instruments and the
judge's commentary is the ballot rather than an annotation beside it. §8.1's
"commentary is the primitive, scores are projections" is not a reframing there.
It is a description.

**Dance and gymnastics move an open item to a blocking one.** Video review is
the coaching method rather than an artifact produced alongside it, so §5 of the architecture's
at-rest sealing of records — listed **Open** in §14, on the grounds that the
vault seals secrets and not collection stores — stops being deferrable. A skin
can inherit an open item; it cannot inherit one that its primary artifact sits
on top of.

### Four candidates the contract refuses outright

Youth sports was the first. Four more turned up, and three of them refuse for
the same reason from different directions.

**Multi-agency wraparound is a double bind.** W-1 and W-3 make the lane the unit
of storage and audit, seal sibling lanes by default, and require a shared event
to be two entries against one referent rather than one row several parties read.
Coordinated cross-agency care runs the other way by construction: the whole
intervention *is* the shared view, and reconstructing it from separately sealed
lanes is the silo the model exists to break. Loosen W-1/W-3 and the guarantee
the design rests on is gone; keep it and the domain cannot do the one thing it
is for. Then the standardised needs-and-strengths instruments common to this
kind of coordination produce exactly one composite score following a child from
agency to agency — SA-3, on a clinical rather than adjudicative motive, which is
not a carve-out the clause grants.

**Chess and esports refuse on SA-3 alone, and most cleanly of any candidate.** A
persistent rating carried across events is not a byproduct of a ranking circuit;
it is the product, and seeding, matchmaking and eligibility all run on it. The
charter holds a durable rating carried between contexts invalid even signed by
root. So either the system cannot run the competition it exists for, or SA-3
does not reach standing skill ratings the way it reaches ratings *of* judges and
staff — and nothing in the clause carves that out. **This is the cleanest test
case in the file for whether SA-3 means what it says**, because there is no
privacy argument to hide behind: everyone involved wants the number published.

**Cadet corps is the sharper version of the youth-sports finding.** Advancement
in programs of this shape is commonly governed by a cumulative order-of-merit
list, ranking cadets against each other for a fixed number of slots — W-7's
forbidden computation and SA-3's forbidden standing score at once. The
difference from a starting lineup is that a sports program could in principle
stop publishing one. Here the ranking is plausibly a compliance artifact of a
regulation the local program did not write and reports *upward*, to the same
external chain the guest instructor belongs to. Refusing to compute it may put
the program out of compliance with the reason the guest is present at all.

**The crisis text line is different in kind: not refused, unshaped.** W-1 opens
a lane under a name and W-2 requires a grant to name one ward — *"'the children'
is not a scope; a name is."* A genuinely anonymous texter has no name to grant
against, and a session identifier is not what W-2 means by naming a subject. The
clause forecloses wildcard and group scopes; it does not supply a shape for a
ward with no identity at all, and anonymity is precisely what makes the service
usable to a frightened minor. Compounding it, §4.1 holds that SMS carries
signals and never records — but for a text-native service the conversation *is*
the record, and there is no lower-sensitivity channel to move it to. **A clause
with no answer for a case is a different finding from a clause that refuses
it**, and this is the only instance of the first kind in the file.

### Two that invert W-4, which matters more after the retiering

W-4 is now one of only two clauses genuinely in the ward tier, so a domain that
inverts it is attacking a load-bearing member rather than an inherited one.

**Child performer programs and therapeutic placement both break the same
assumption**: that the registered guardian is a safe default recipient of a
ward's request. Earnings-trust regimes exist because of a documented pattern of
guardians spending a child performer's own money; therapeutic placement is
frequently made by a guardian against the participant's wishes. In both, a
design whose only path from request to authorization runs through the guardian
has no expressed persona for **a ward who needs protection from their own
guardian**, on exactly the `FINANCIAL` and record-access asks where it bites.
I-6's dated disposition inherits the same assumption.

Therapeutic placement adds a second, harder strain on W-6: the lane must
transfer whole at the threshold, and this class of program has a general
reported history of participants being unable to obtain their discharge records
— partly because those records would support a later claim against the program.
That is a **structural incentive to withhold**, not an unbuilt feature, and the
design has no answer for an operator who does not want the exit to work.

---

## 3. Skins that tighten the ward tier until it becomes the product

These need Tier B *more* than this design does, and mostly shed Tier C.

**Foster care, CASA, kinship placement.** The ward case stops being an analogy.
§7.1's proving case — *a court order dated in March, delivered to the program in
October* — is not the edge case that justifies bitemporality here; it is the
daily traffic there, and the two-axis requirement (when it took effect, when this
system learned of it) is the schema rather than a caveat on it. **I-7 becomes the
load-bearing clause**: a ward's entries about the office are as durable as the
office's entries about the ward, and the population most likely to have its
account of an incident deleted is the one being written about. Tier C mostly
drops away — nobody is being scored — and what remains is the hardest version of
the tier this design is least sure of.

**Early intervention and pediatric therapy** — speech, OT, ABA. The clinician is
*already* the transient guest with a session, a rubric, and a grace period; §7.2's
knock describes existing practice rather than proposing new ceremony. §8.1's
anchored commentary is the session note, anchored to video instead of to a
measure number, which sidesteps §18 item 7 entirely: video has a timeline that
needs no score alignment. `HEALTH` dominates, so §5 of the architecture's at-rest gap blocks here
too.

**Special education and IEP management.** This is not a speculative skin. §7.3
names `quiet-corner` — the same author's K–12 student-records application — as
the known-bad precedent, with a per-field `session_scope` vocabulary declared and
enforced nowhere, and a documented backup path that is a plaintext export moved
by USB or emailed to oneself. **The corrective already exists at file level.** If
an argument is wanted for which skin to build second, it is here, because it is
the only candidate whose negative example is documented rather than imagined.

**Juvenile diversion and restorative justice.** The skin with the highest stakes
and the highest chance of the contract being overridden by whoever buys it. SA-3
stops being a design preference: a durable rating of a young person carried
between contexts is precisely what a risk-assessment instrument is, and the
charter holds such a scope invalid *even fully signed by root*, recording the
attempt as a failed issuance with the signatory named. That is a strong position
to hold in a domain where those instruments are in production and procurement
asks for them by name. Recorded here as the place where the contract would be
tested by an institution rather than by a developer.

---

## 4. The adult skin, as a deliberate negative result

Community chorus, amateur ensemble, adult continuing education. Owner == subject
for nearly every record. **The experiment has been run**, clause by clause, and
it produced the retiering above.

Forty-six items were graded against a world with no minor in it: `CLAUDE.md`'s
twenty rules, §12's sixteen decisions, and the ten Ward Case clauses
(W-1 … W-7 plus I-6, I-7, I-10). Denominators counted from the tree, not
estimated.

| Verdict | Count |
|---|---|
| **Survives** unchanged — it was never a child-protection rule | 38 |
| **Weakens** — keeps the mechanism, loses its sharpest instance | 6 |
| **Dissolves** — nobody left for the sentence to govern | 2 |
| **Inverts** as a primary verdict | 0 |

**Two of forty-six are actually about children: W-4 and W-5.** Everything else
is an institutional-honesty rule that was discovered through a charter about
wards and happens to be stated with a child as its example.

The six that weaken are worth naming, because "weakens" is where the design's
real motivation lives: rules 1, 3 and 7 of `CLAUDE.md` and decisions 7, 8 and 14
of §12. Each keeps its general mechanism and loses the case that made anyone
build it — the court order arriving mid-season, the contact-restricted guardian
receiving a live location disclosure about a minor. An adult ensemble still
needs dated termination and still must not put a balance on SMS; it simply
never produces the instance that makes those obligations feel urgent.

The one inversion is secondary and sits inside W-4: the clause as a *permission*
(a ward may request, never authorize) dissolves, while the same doctrine as a
*prohibition* — consent is never requested by its beneficiary — inverts, because
an adult beneficiary is exactly the right person to ask. One sentence, two
verdicts, depending on which way it is phrased.

> **A byproduct, and it is a live gap in the current design rather than in the
> skin.** `docs/SENSITIVITY.md` maps eight classes onto the ladder and none of
> them is adult identity: `PII_MINOR` is *anything identifying a student* and
> `PII_GUARDIAN` is *contacts, addresses, relationships*. A staff member's own
> home address is therefore **unclassified** — not exempt, unclassified — and
> rule 14 says nothing may be classified against a ladder by inference. This is
> adjacent to §18 item 11, which holds the vocabulary open for protected-status
> categories, but it is a different hole: item 11 is about categories that land
> a rung too low, and this is a category with no class at all. It belongs on
> that open list, and this file governs nothing, so it is recorded here rather
> than filed.

---

## 5. Instrument skins — where the novelty actually is

Everything above is §17's template argument restated with different nouns. The
three pieces of working software in this tree generalise on a **different axis**,
and on the evidence available that is the more interesting direction.

### 5.1 `craft/` — diagnose-never-score, over any made thing

§24 of the capability map already names a tree of makers — student, peer, student
leader, staff, arranger, director — and observes that *above the student rung
almost nobody has ever been taught the craft*. Every rung above the bottom one is
an unbuilt skin of a tool that is already built and already runs.

Off the domain entirely, the mechanic fits any artifact with a craft and no
grader: the code-review comment, the incident report, the program note, the grant
application, the performance review. The transferable property is not the checks
— those are Anglo-American popular song and §24 of the capability map says
so. It is that **the
declaration is the artifact**: the output is evidence about the *maker* rather
than about the made thing, and *"whether a student can say I know, I meant it"*
survives every change of subject.

**And one such skin is already half-built here without being called one.**
`tests/test_section_refs.py` and `tests/test_claimed_artifacts.py` are craft
checks over this repository's own prose — the same shape as `METER` and
`STRUCTURE`, aimed at section references and claimed artifacts instead of at
syllables. Rules 17, 18 and 20 of `CLAUDE.md` are three more craft checks, stated
in English and not yet in code.

**That skin is now built: `craft/prose.py`, run with `--prose`.** Six rules —
`COUNT` (17), `GATE` (18), `TOMBSTONE` (20), `ABSENCE` (13), `RUNG` (14), and a
`STATUS` check for the house convention that a document declares its own weight.
It imports `Finding`, `Report` and `load_intents` from the lyric side rather
than reimplementing them, so the declaration mechanic, the report shape and the
intent format have one implementation and two callers — which is why this cost
less than any domain skin in this file. It deliberately does not check
§-references or claimed artifacts, because the two tests above already do, and a
second copy would be the pair this repo keeps recording.

What it found on its first run over this tree is in `docs/prose.intent`, which
is the more interesting artifact: the declarations, not the findings. Three
worth naming here, since they are about the canonical documents rather than
about the checker:

- §7.2 writes **"Level 0 is refused a session"** — a bare position on a scale, in
  the same document whose §15 requires `T0`. Rule 14, in the file that states it.
- `OPEN-SOURCE-SURVEY.md` twice reports **"Nothing found"** as a result, in a
  document whose own status line says no human has verified a row. Whether that
  means *the scouts looked and there is nothing* or *nobody looked here* is
  exactly the distinction rule 13 exists to preserve, and the sentence cannot
  carry it.
- Two of §18's struck items are missing a part of their own tombstone — item 1 a
  reason, item 3 a status word — against the discipline §18's preamble sets for
  itself.

None of those is severe. The point is that they are the class of defect this
repo has recorded four times in prose and never had a check for.

### 5.2 `voice.py` — refusals that live in sentences

Its premise is domain-free: every refusal in `CLAUDE.md` has a *sentence* that
performs it with no handler called and no permission checked, invisible to a
static check because it is generated at run time. Any assistant with a duty of
care has that property — crisis triage, HR, tutoring, healthcare intake, a
manager's coaching tool.

The rule table is the skin. The contract is the rest of the file: `REFUSE`/`FLAG`
separated so a detector that will sometimes be wrong flags rather than blocks;
fail-closed on a payload it cannot read as well as one it fails; a policy version
stamped on every refusal; and near-boundary benign fixtures chosen hard on
purpose, because an easy benign set makes a damaging filter look excellent.

**The rarest part is `KNOWN_MISSES`, and it is the most portable.** Publishing
your own false negatives with denominators, and asserting in the suite that each
listed miss is *still* genuinely missed so the honesty list cannot go stale, is a
discipline almost nothing in this class ships. It costs one list and one test.

### 5.3 `personas.py` — a canon lock derived from a location

Terpsi is under the floor. She has never seen a show, so she cannot be asked *was
it good* — the refusals are not asserted, they are **structurally unavailable**,
which is §16's own preferred fix (*make the violation inexpressible, not
forbidden*) applied to character rather than to code.

That is a reusable move and I did not find it named anywhere in this tree: any
domain with a judged population can build the same character by asking what its
equivalent of the pit is — the position from which the assistant is
constitutively unable to render the verdict everyone will want from it.
`CANON_LOCKS` is testable because the location makes the locks inevitable; a card
that merely instructed the same abstinence would be a hope, which is what the
module's own docstring says a persona is.

---

## 6. The middle, and why this file is not a plan

§16 rule 1: name every pair you create, and name its middle in the same commit.
**This file proposes pairs and ships no middles.** That is not fixed by writing
more of this file. The middle for terpsi-music ↔ any skin is the conformance
suite, and §18 item 6 records that it does not exist — `promote_check.py` returns
an exit code and writes nothing.

So the honest state of every row above: a pair with a delay fuse. Until the suite
exists, §17's warning applies verbatim — *the second app is a copy, the fifth is
a dialect.* The order is item 6 first. This is a survey of what would be worth
conforming, not a licence to start one.

**Rule 4 cuts the other way and points at the answer.** *Prefer not creating the
pair* — the cheapest middle is the one you do not need. Two of the three
instrument skins are **not new pairs at all**: `craft/` over `docs/` and a second
rule table for `voice.py` are new *inputs* to existing tools, sharing one
implementation and one suite. That is why they cost less than every domain skin
above them, and it is the recommendation this file arrives at.

**That one has been done.** `craft/prose.py` and `tests/test_prose.py` are the
first skin actually worn on purpose, and it cost one module and one suite
because it created no pair — the report shape, the id scheme and the
declaration file all came from the lyric side unchanged. It turns five of
`CLAUDE.md`'s twenty rules from English into checks, and the sixth check is the
house status convention that was never written down as a rule at all.

The next cheapest thing is the same move again: **a second rule table for
`voice.py`.** No new module, no new suite, no pair — a different domain's
refusals in the existing shape, with its own `KNOWN_MISSES` published beside
them. Every domain skin in this file costs more than both put together, and
none of them can start until §18 item 6 exists.

---

## 7. What this rests on

Read from **this repository's tree only**. No fleet repository was read; per §18
item 0 and `docs/FLEET-READS.md` none is readable from a session like this one,
so every characterisation of a fleet component here is inherited from
`ARCHITECTURE.md` at `P2` and is not re-verified.

**How this version was produced, since it changes what the rows are worth.**
The first version was written by reading the tree directly. The three passes
that revised it — the additional domains, the adult-skin diagnostic, and the
attack on the tier split — were each run by a separate agent over the same
tree, with instructions to be adversarial and to mark interpretation as
interpretation. Two of them arrived independently at the same objection to the
tier split, from different directions: one by grading clauses against a world
with no minor in it, the other by testing each tier for leaks. **That
convergence is the main reason the retiering is stated as a correction rather
than as an alternative reading** — though two passes agreeing is weaker
evidence than one practitioner disagreeing would be, and neither pass consulted
one. Every load-bearing quotation they returned was checked against the file it
came from before it was used here; the `LANE-MODEL.md` line and the missing
adult class in `SENSITIVITY.md` are `P1`, read at source.

Self-references are by name rather than by number. A bare `§N` in this file
means `ARCHITECTURE.md`, and this document's own numbered sections would collide
with it — section five is envelope security there and instrument skins here.
`tests/test_section_refs.py` holds that line, and **it caught this file citing
itself, twice, after the file had been reported as passing.** The report was
made from a truncated view of the suite output rather than from the suite. That
is rule 17's defect in its purest form — a status quoted from a summary rather
than derived from the thing that produced it — committed in the commit that
added a document about not doing that. Recorded rather than quietly fixed,
because the useful part of the tally is that it keeps growing.

| Claim class | Rung |
|---|---|
| The external arm — that it happened, and its shape | `P1` for the fact, `P2` for anything about the other arm's contents |
| The three-tier contract — which clause sits in which tier | `P3` Fitted — derived from this tree by reading, and it is an interpretation |
| Every candidate domain, and every strain named against it | `P4` Estimated |
| The claims about `craft/`, `voice.py`, `personas.py` | `P1` — read from source in this tree today |

**The domain sections are `P4` and the distinction matters.** Nobody in foster care, junior
debate, or a dance studio was consulted; no such program's records were examined;
no practitioner has seen a line of this. The strains are **predictions
extrapolated from analogous cases**, which is precisely what §15 reserves that
rung for, and a domain fit is the kind of claim that gets confirmed by one
conversation with a person who does the work and by nothing else.

Counts derived from the tree today, per rule 17: ten rules in `voice.py`'s table
plus two checks outside it (`naked_statistic`, `no_rung`); six check functions in
`craft/checks.py` plus two declared diff names; six rules in `craft/prose.py`.
The adult skin's forty-six is twenty numbered rules in `CLAUDE.md`, sixteen
decisions in §12, and ten Ward Case clauses — each counted in the file it lives
in, not carried from the pass that graded them.

> **Byproduct, unrelated to skins.** Those two diff names are a small live
> instance of §16. `craft.checks.CHECKS` and `DIFF_CHECKS` are declared
> vocabularies that nothing consumes — no `Finding` is ever constructed with
> `check="DIFF"` or `check="DELTA"` (`run_diff` returns findings carrying their
> original check names), and no test reads either tuple. Harmless today, and it
> is declaration-without-enforcement in the library that is this design's one
> worked example.
>
> The skin does not inherit it: `prose.RULES` is derived from the registry that
> holds the callables rather than written beside it, and
> `test_the_vocabulary_cannot_outlive_what_produces_it` asserts both that
> derivation and that every declared rule actually produces a finding. The
> drift is not expressible there. That is the §16 fix — *make the violation
> inexpressible, not forbidden* — applied to the defect noticed while writing
> the first version of this file.

**Seal state: `draft`.** Nothing here has a named human behind it.
