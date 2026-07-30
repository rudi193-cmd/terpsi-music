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
- Absence surfaces as `unknown`, never as a result (§6)
- A machine answer is a `draft` until a named human seals it, and a rejection is
  recorded as durably as an approval (§8.2, §16)
- The canonical store is read-only to the app; promotion is a human act (§5)
- Every pair gets a named middle in the same commit (§16)
- A guard that cannot be shown to fail has not been shown to work (§10)
- Prefixed ordinal scales; provenance labels an answer, never gates it (§15)
- The exit line — sovereignty is the ability to leave (§11.1)

### Tier B — the ward tier. Transfers only where owner ≠ subject.

W-1 … W-7, plus I-6 and I-7 (§7.4). This is the tier that makes terpsi-music
something other than a competent privacy posture. It requires a population that
**holds no keys of its own** and a steward acting over them. `corpus-lens` names
this as the fleet's hardest open gap and scopes itself out of it deliberately.

### Tier C — the assessment tier. Transfers only where someone is judged, and the judgment becomes their opinion of themselves.

SA-3 (no standing cross-context scores, invalid even signed by root), W-7 (never
compute a priority between two wards), commentary as the primitive with rubrics
and scores as projections over it (§8.1), diagnose-never-score (§24 of the
capability map), and the whole of Terpsi.

**The three tiers are the axes.** A candidate needing all three is a sibling. One
needing A and C but not B is an adult skin. A and B but not C is custodial.

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
the coaching method rather than an artifact produced alongside it, so §5's
at-rest sealing of records — listed **Open** in §14, on the grounds that the
vault seals secrets and not collection stores — stops being deferrable. A skin
can inherit an open item; it cannot inherit one that its primary artifact sits
on top of.

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
needs no score alignment. `HEALTH` dominates, so §5's at-rest gap blocks here
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
for nearly every record. Tier B dissolves: W-4 (*a ward may request, never
authorize*) becomes meaningless, and consent-never-requested-by-its-beneficiary
**inverts** — here the beneficiary is exactly the right person to ask.

Tier A survives whole. Tier C survives intact, because adults are still judged,
and an adult amateur reading a caption sheet in a parking lot is the same event
that produced Terpsi.

**The value of this skin is diagnostic and it needs no build.** Read the design
with the ward tier deleted and see what still stands. Anything that survives was
never a child-protection rule — it was an institutional-honesty rule wearing one,
and knowing which is which is worth more than a fifth domain. It is the cheapest
experiment in this file.

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
— those are Anglo-American popular song and §24 says so. It is that **the
declaration is the artifact**: the output is evidence about the *maker* rather
than about the made thing, and *"whether a student can say I know, I meant it"*
survives every change of subject.

**And one such skin is already half-built here without being called one.**
`tests/test_section_refs.py` and `tests/test_claimed_artifacts.py` are craft
checks over this repository's own prose — the same shape as `METER` and
`STRUCTURE`, aimed at section references and claimed artifacts instead of at
syllables. Rules 17, 18 and 20 of `CLAUDE.md` are three more craft checks, stated
in English and not yet in code. `craft/` pointed at `docs/` is the shortest path
from here to a second instance, and the corpus is already written.

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

If only one thing is done with this document: **point `craft/` at `docs/`.** It
creates no pair, needs no decision from §18, has a corpus already in the tree,
and would turn three of `CLAUDE.md`'s twenty rules from English into a check.

---

## 7. What this rests on

Read from **this repository's tree only**. No fleet repository was read; per §18
item 0 and `docs/FLEET-READS.md` none is readable from a session like this one,
so every characterisation of a fleet component here is inherited from
`ARCHITECTURE.md` at `P2` and is not re-verified.

| Claim class | Rung |
|---|---|
| §0's account of the external arm — that it happened, and its shape | `P1` for the fact, `P2` for anything about the other arm's contents |
| The contract in §1 — which clause sits in which tier | `P3` Fitted — derived from this tree by reading, and it is an interpretation |
| Every candidate domain in §2, §3, §4, and every strain named in them | `P4` Estimated |
| §5's claims about `craft/`, `voice.py`, `personas.py` | `P1` — read from source in this tree today |

**§2 and §3 are `P4` and the distinction matters.** Nobody in foster care, junior
debate, or a dance studio was consulted; no such program's records were examined;
no practitioner has seen a line of this. The strains are **predictions
extrapolated from analogous cases**, which is precisely what §15 reserves that
rung for, and a domain fit is the kind of claim that gets confirmed by one
conversation with a person who does the work and by nothing else.

Counts derived from the tree today, per rule 17: ten rules in `voice.py`'s table
plus two checks outside it (`naked_statistic`, `no_rung`); six check functions in
`craft/checks.py` plus two declared diff names.

> **Byproduct, unrelated to skins.** Those two diff names are a small live
> instance of §16. `craft.checks.CHECKS` and `DIFF_CHECKS` are declared
> vocabularies that nothing consumes — no `Finding` is ever constructed with
> `check="DIFF"` or `check="DELTA"` (`run_diff` returns findings carrying their
> original check names), and no test reads either tuple. Harmless today, and it
> is declaration-without-enforcement in the library that is this design's one
> worked example.

**Seal state: `draft`.** Nothing here has a named human behind it.
