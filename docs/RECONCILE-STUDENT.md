# The student's assistant, against the decisions already settled

**Status:** reconciliation, not a decision record. **Four items need a human
and are marked.** Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

**This file reconciles against `records/` as well as against the documents**,
and the second half was added after the first draft shipped without it. The
first draft cited `ARCHITECTURE.md` throughout and named four modules, counted
by reading it back; `ls records/` gives eighteen. Four §18 items had been closed
*in code* before this branch was cut, and one row argued against behaviour that
already ships. See *the module sweep* at the foot of this file — a document
that reconciles only against documents reconciles against the wrong artifact.

`docs/RECONCILE-19.md` does this for the thirteen capabilities of
§19 of the capability map, and that section is the **director's** assistant —
natural-language query for directors, practice plans, budget forecasting,
rehearsal summarization. `personas.py` states the assistant also faces students,
guardians and judges, and no capability list exists for any of the three. This
is the first of them.

The decisions reconciled against are not restated: §4 (the captive slice), §18
item 12 (the self edge, closed), §7.4 (the ward clauses), §13 (no standing
cross-context scores), §15 (the scales), and `voice.py`'s rule table.

---

## What is already fixed

More is settled here than for any other persona, which is why this list is
short on architecture and long on refusals.

**Visibility** is the self edge of §18 item 12: `L1`–`L3` in full, `L4` as the
derived instruction unless a guardian signs a per-category `Widening`, `L5`
never — and, load-bearingly, **the subject reads their own disclosure log at
every rung**. `principal.purposes` is never consulted before the W-6 threshold:
a ward declaring a purpose over its own record is the ward authorizing itself.

**Scope** is §4's captive slice: their schedule, their assignments, their own
inventory, announcements addressed to them. No roster browsing, no contact
directory, no other students' data — *"a student-facing directory of minors is a
liability with no compensating benefit."*

**Register** is already written, in `personas.py`: *"plain, second person,
short. names one next action. never a comparison."*

---

## The thirteen

| § | Capability | Verdict |
|---|---|---|
| S1 | Schedule and call-time query | **Survives** — and it is the flagship |
| S2 | What to bring, from their own inventory and the event | **Survives** |
| S3 | Own-lane status lookup ("is my form in") | **Survives**, capped by the self edge |
| S4 | "Who has looked at my record" | **Survives** — the capability no comparable product has |
| S5 | "Why can't I see that" | **Survives, with a mechanism** |
| S6 | Announcements addressed to them | **Survives** |
| S7 | Requesting a widening from a guardian | **Survives as a request, never an authorization** |
| S8 | Routing a concern to a named adult | **Survives as a route** — see `RECONCILE-SAFEGUARDING.md` |
| S9 | Own practice record | **Survives** — `records/practice.py` is built |
| S10 | Practice streaks, milestones, cumulative hours | **Shipped; a proposal to reopen §18 item 9** |
| S11 | "How am I doing" | **Refused** |
| S12 | Chair or placement prediction | **Refused** |
| S13 | Comparison to the section or to a named peer | **Refused** |

---

## The flagship is the boring one

**S1 survives and everything depends on it.** A hosted assistant will invent
Saturday's call time with total confidence; this one knows it. Students will use
whichever is *right* about what to bring and when the bus leaves, and every
safety property in `RECONCILE-SAFEGUARDING.md` is downstream of them being here
at all. **If the local assistant is worse at the boring questions, nothing else
in this document matters**, because the traffic will be somewhere else.

That makes S1–S3 and S6 the acceptance bar, not the warm-up.

## The capability nobody else can offer

**S4.** Item 12's clause — *a student who cannot read their `L4` medical field
can still see that the athletic director read it on October 12* — is already
built. `dispatch()` writes the disclosure entry on every read, and `standing.py`
gives the subject the log at every rung.

An assistant whose answer to *"has anyone looked at my medical form"* is a dated
list is a different object from a band app. It is also the one place where the
assistant's usefulness and the architecture's whole thesis point the same way.

**Two properties of `records/disclosure.py` the assistant inherits and must not
undo.** The log is hash-chained and append-only in the sense rule 18 asks for —
`append()` returns a new log and no method rewrites an entry — after PR #3 found
by executing the DDL that a table called append-only in a comment was
`UPDATE`-able. And **a read that returned no payload is recorded by rung and
outcome, never by whether a value existed**, so a refusal and an absence produce
the same rows. That second one is the §7 indistinguishability guarantee living
inside the audit trail, and it is exactly the property a friendly rendering
breaks: *"nobody has looked, and there is nothing there to look at"* re-creates
in one sentence the signal the log was built not to carry.

**And the log is only worth its anchor.** `records/witness.py` supplies what §5
specified and stopped short of — an anchor is a digest, a count and a time, with
nothing in it to leak, published on a **fixed calendar cadence** rather than
when something happens, because a count that jumps the week of an incident is
itself a channel. `standing()` is what separates *"here is my log"* from *"here
is my log, and it could not have been written later"*. A student's disclosure
log is the one artifact in this design whose value depends on someone outside
the institution having seen its shape, and the assistant should say the weaker
thing when the anchor is missing rather than the stronger one always.

**One caution.** The log is the read side of §7.2's *narrate the read*, and
`ARCHITECTURE.md` §18 item 12 already carries the unresolved half: a
safeguarding read appears in the subject's own log like any other, and there is
no suppression mechanism, *deliberately* — a `suppressed_from_subject` flag is a
backdoor that ends up on everything, and a "one entry withheld" count tips off
as loudly as the entry. Surfacing this to students conversationally does not
create that tension, but it does make it visible to the population it concerns.

## S5, with its mechanism

`Serving` carries `reason`, `rung`, `via_edge` and `via_purpose`. A refusal can
therefore explain itself rather than shrug — *"that is `L4`; you can see the
summary, and a guardian can sign for the rest."*

**The mechanism is that the explanation must be the `Serving`'s own reason
string, never a re-derivation.** A surface that composes its own explanation
from the outcome has built a second, unverified account of the rules, and the
two will drift. This is rule 12's pair: `serve()` decides, the surface renders,
and the reason travels with the decision.

**The named middle already exists and this entry originally missed it.**
`records/dispatch.py` is the join `voice.py` was written for and did not have —
PR #4 said so in as many words, *"enforcement-ready rather than enforcing"* —
and it fixes the order rather than leaving it to a caller: `serve()` first,
because running a text filter over a value the principal was never entitled to
*is a disclosure to the filter*, then the voice gate on the rendered sentence,
after the seal and before dispatch. Fail-closed is inherited from
`voice.refuses()` rather than re-implemented, because two implementations of
fail-closed is the pair §16 warns about. **A student surface routes through
`dispatch()` or it is a second dispatcher.**

**Two smaller modules bear on how a refusal may be phrased, counted from the
sweep at the foot of this file.** `records/rungs.py`
makes rule 14 structural — `Rung` carries non-ordinal values, so `Rung.L3 <
Rung.L4` raises and ordering exists only through `outranks()`/`at_least()`,
which say the scale's name at the call site. An assistant rendering *"that is
more sensitive than your schedule"* is doing by prose what the type refuses to
do by operator. And `records/classify.py` returns `UNDECIDED` for a field
outside its decided cases — a build failure, not a default — so *"why can't I
see that"* has a third answer besides *entitled* and *refused*: **nobody has
classified it yet**, which the assistant must say rather than round to a no.

## S7, and W-4

A student may ask their guardian to sign a `Widening`. `standing.py` already
makes this expressible and already refuses the failure mode: `Widening` rejects
a self-signature **at construction**, so a ward cannot widen its own access.

The assistant's role is to compose the request. **It must not argue for it** —
"you have been responsible, you should be allowed to see this" is W-5 exactly:
*the steward may propose a widening, citing the record; it may never enact one.
A clean track record is evidence for a proposal, never a grant in itself.*

## S9 and S10 — where the leaderboard hides

**S9 survives**: a student may see their own practice record. It is their entry
in their own lane, and `records/practice.py` already builds it — `own()` returns
sessions, minutes and streaks over a single lane, and `_one_lane()` raises
rather than filtering if asked to span two.

**S10 is not open, and this entry reopens it rather than discovering it.**
§18 item 9 is **closed** as of 2026-07-30 — *"the standings half was never a
UTETY question; it is already forbidden by refusal 6 and W-7"* — and the line was
drawn in code:

| | |
|---|---|
| refused | `standings()`, and any statistic reading more than one lane (W-3's seal) |
| permitted | `OwnPractice.streak_days`, `longest_streak_days`, and `THRESHOLDS = (5, 10, 25, 50, 100, 250)` |

**So own-lane streaks ship today.** What follows is a proposal to reopen that,
and it is stated as one because this file's header says the doc wins and this
file is the defect — arriving at a settled question without noticing is exactly
the defect that header describes.

**The argument for reopening: a streak is a standing score of a person with the
number left in.** It persists across contexts, it rates the learner rather than
the work, and §13 prohibits exactly that. `voice.evaluative_praise` cannot catch
it, because a streak counter says nothing — it just counts, and **the student
supplies the praise.** That last step is what item 9's closing did not consider:
it reasoned about whether the *system* rates a person, and a counter does not, so
it passed. The rating happens in the student's head, reliably, which is the
entire design intent of a streak.

**The argument against, which item 9 has on its side.** `practice.py`'s rule is
structural rather than remembered — *every own-work statistic reads one lane and
every comparison needs two* — and a streak genuinely reads one lane. Prohibiting
it needs a second rule about **what a single-lane statistic may be shaped like**,
which is a weaker kind of rule: judgement rather than a predicate, and rule 19
says a judgement is the hard thing to check.

**Needs a human — 1.** Whether that is worth reopening item 9 for. Cumulative
hours *this season, shown only to them* is arguably a record rather than a score;
a streak with a flame next to it is not. **The narrower change, if the argument
lands, is dropping `streak_days` and keeping `THRESHOLDS`** — milestones are
absolute and bounded, a streak is unbounded and resets, and the reset is where
the pressure lives. Worth settling before a surface renders it, because a streak
is very hard to take away once students have one.

## The refusals

**S11, "how am I doing."** `evaluative_praise` and `peer_comparison` between
them refuse nearly every phrasing. This is the most-wanted question on the list
and the answer is no. Worth being honest that this is a real cost, not a
technicality: the assistant will feel evasive to a student who wants
reassurance, and no amount of tone fixes that.

**S12, chair or placement prediction.** `voice.prediction`, and `RECONCILE-19.md`'s
reasoning for refusing 19.3b transfers without modification — a projected
placement arrives *before* the thing it predicts, so it anchors the person about
to be judged, and it has nobody's name on it. That entry's line applies here verbatim:
a description of what happened survives; a competing score does not.

**S13, comparison.** `peer_comparison`, refusal 6, and W-7 — and **the strongest
mechanism is the one this row originally missed.** `records/conflict.py`
implements W-7 structurally: the functions that would rank return an
`Escalation`, and an `Escalation` has no field an order fits in. Its
`recommendation` is a property that raises rather than an absent attribute, *"so
a caller reaching for a recommendation gets the clause, not an `AttributeError`
they will paper over with `getattr(..., None)`."* `refuse_to_rank()` gives the
refusal one spelling.

That module's own docstring is the correction to this file: until it was
written, W-7 was prose everywhere and code nowhere — the ledger half of rule 18
with nothing on the other side. The figure is counted from the tree rather than
quoted from the module: 20 files carry the clause today, counted by grep. Of
those, 15 are documents repeating the guarantee, counted the same way, and the
rest sit under `records/` or `tests/`. These lists were among the fifteen. They cited a regex over prose as though it were the gate, when the gate
is unrepresentability and the regex is the backstop. *"A comparison does not
stop being a ranking for being spelled out in words"* — and a ranking does not
stop being computable for being unsayable.

**Needs a human — 2.** These three refusals are correct and they are also most
of what a teenager wants from a band app. The assistant's value therefore rests
entirely on S1–S6. If that is judged too thin to be worth building, the honest
outcome is **no student assistant**, not a student assistant that softens the
refusals — and that decision should be taken deliberately rather than reached by
degrees once the refusals start feeling unhelpful.

## The capability the list omitted, and the module that named it

**Needs a human — 3.** There is no entry for *"what happens to this when I
leave"*, and `records/exit.py` is the reason that is a defect rather than a
scope decision. W-6 is not an aspiration there: `open_lane()` requires
`exit_terms` and a `Threshold`, and **there is no way to construct a `Lane`
without them** — *"the exit is enforced at opening, not at graduation,"* because
by the time a student graduates it is far too late to discover nobody wrote down
what leaving means.

So every student's lane already carries, in the tree, a written answer to a
question this list did not ask. §7.4 calls the per-graduate half the harder one
— *"a system that can export a whole program but cannot hand one graduate their
own past has satisfied the smaller obligation and missed the larger one"* — and
a student asking their own assistant is the cheapest path to that answer there
will ever be.

**Why it was missed is the more useful part.** Counted, this list has thirteen rows
because §19 of the capability map has thirteen, and the thirteen there were
derived from a director's capabilities. A student capability with no director counterpart therefore has
nothing to be modelled on and does not appear. That is a defect in the method,
not an oversight in the row, and it is the reason the next section exists.

## What this does not cover

**Needs a human — 4.** Nothing here addresses the student who is also a
**section leader**. §16 of the capability map asks for *"their section's
attendance, sectional planning, peer feedback"* — a minor with access over other
minors. The first half must be N named edges, never a section scope (W-2,
refusal 5). The second half collides head-on with S13, refusal 4 and refusal 6:
`voice.peer_comparison` will refuse the sentences that feature exists to
produce. It is a separate persona wearing a student's account, and it is not
reconciled anywhere.

## The module sweep

Every module under `records/`, listed by `ls`, with what it does to this
document. The point of listing all of them rather than the relevant ones is that
**a module added later becomes a visible blank row rather than a silent
absence** — which is how the first draft of this file came to argue against
shipped code.

| module | bearing on the student surface |
|---|---|
| `classify.py` | **Cited** — S5's third answer, `UNDECIDED` |
| `conflict.py` | **Cited** — S13, and the strongest mechanism on the list |
| `consent.py` | **Bears, not worked.** `governs()` puts `self` among the principals who *hold* authority and are asked at the door. A student prompt is that door |
| `crossing.py` | **Bears, not worked.** A sibling's event read across lanes needs a guardian-signed `Envelope` with both lanes, a purpose and an expiry. A student asking *"why can't I see my sister's call time"* is asking about this |
| `disclosure.py` | **Cited** — S4, and its indistinguishability property |
| `dispatch.py` | **Cited** — S5's named middle, and the route the surface must take |
| `dispositions.py` | **Bears, not worked.** S3's *"is my form in"* reads a queue that I-6 timebounds. What a student sees when the timebound lapses is unwritten |
| `exit.py` | **Cited** — the omitted capability, *needs a human 3* |
| `export.py` | **Bears, not worked.** The other half of `exit.py`: `bundle()` produces the graduate's own copy, and nothing here says what a student may ask for before they leave |
| `marking.py` | **Bears, not worked.** A judge's remark is a lane entry about this student. Whether the subject reads it, and at which rung, is not on this list |
| `practice.py` | **Cited** — S9 and S10, including where this file was wrong |
| `receipts.py` | **Bears, not worked.** Guardians hold receipts. Whether the subject holds their own is not decided anywhere, and it is the same argument as S4 |
| `rungs.py` | **Cited** — S5, rule 14 as a type |
| `sealing.py` | **Bears, not worked.** Rule 10 says a machine answer is a `draft`. Nothing in S1–S6 says how a student surface *shows* that, and an unmarked draft is the failure rule 10 exists for |
| `sending.py` | **Bears, not worked.** S6's announcements are its output. G12/G13 govern who receives; nothing governs how the assistant renders one |
| `serving.py` | **Cited** — S5, and the reason string that must not be recomposed |
| `standing.py` | **Cited** — S4 and S7's `Widening` |
| `witness.py` | **Cited** — S4, the anchor the log is worth |

Counted off the table above, 8 rows say *bears, not worked* and 10 say *cited*.
None of the eight is a refusal or a decision; they are places where a surface
would have to choose and this document does not say what. **That is the honest
state of the student list**, and it was not visible while the file reconciled
against prose.
