# The guardian's assistant, against the decisions already settled

**Status:** reconciliation, not a decision record. **Six items need a human and
are marked.** Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

**This file reconciles against `records/` as well as against the documents.**
The second half was added after the first draft shipped without it. Reading the
diff back, it moved the GU7 and GU10 rows and opened the last two items on the
list. *The module sweep* at the foot names every module in the tree so that a
later one is a blank row rather than a silence.

Second of the three lists `docs/RECONCILE-19.md` does not cover; see
`docs/RECONCILE-STUDENT.md` for the first and for the shared framing. The
decisions reconciled against are not restated: §4.1 and §4.2 (the traffic split
and the transactional remainder), §7.1 (dated guardianship), §7.4 (the ward
clauses), §13, §15, §18 item 10 (which consent model governs — closed,
`records/consent.py`), `docs/PLAN-GUARDIANSHIP.md`'s G1–G13, and `voice.py`.

**Register** is already written, in `personas.py`: *"complete sentences, no
jargon, no program shorthand. a named person."*

---

## The thirteen

| § | Capability | Verdict |
|---|---|---|
| GU1 | Schedule and call time for their student | **Survives** — flagship, as for the student |
| GU2 | What their student needs to bring | **Survives** |
| GU3 | Balance, fees, what is owed | **Survives, with a mechanism** |
| GU4 | Outstanding forms and what needs signing | **Survives** |
| GU5 | "Who *can* see my child's record" | **Survives** — `who_could_see` is built |
| GU6 | Checking their receipts against the lane | **Survives, with a mechanism** |
| GU7 | Signing a `Widening` their student requested | **Survives** (W-5) |
| GU8 | Absence requests and their dated disposition | **Survives, with a mechanism** (I-6, `records/dispositions.py`) |
| GU9 | Travel and consent | **Survives** |
| GU10 | "Who *did* look at my child's record" | **Needs a decision** |
| GU11 | "How is my child doing" | **Refused** |
| GU12 | "Will they make the trip / the chair" | **Refused** |
| GU13 | Anything about another student, or the other guardian | **Refused** |

---

## The finding this list produced

**A conversational surface converts every push restriction into a pull that no
restriction covers.**

`sending.py` is explicit that the two are separable: *"a guardian may be
restricted from being **messaged** even while their standing continues."* A
`ContactRestriction` is its own object, consulted by `recipients()`. And
`serving.serve()` takes `edges` — it never sees a `ContactRestriction` at all.

So a restricted guardian still holds a live `guardian_of` edge, `serve()`
entitles them, and **the assistant answers.** G1 keeps them off the send list
and does nothing about the query.

For SMS that separation is coherent: a court order restricting contact is not
automatically an order restricting a parent from reading a schedule, and
conflating them would be its own harm. What changes is that
`docs/PLAN-GUARDIANSHIP.md`'s motivating case is a *location* disclosure —
*"Ben will be at the away game in Dayton until 10pm"* — described as pushed to a
device and **unrecallable**. Pulled on demand it is the same fact, repeatable,
and available at the moment it is most useful to someone a court has restricted.

**Needs a human — 1.** Whether an on-demand answer counts as *messaging* or as
*reading*. The distinction was cheap when the only channel was a push. An
assistant makes it load-bearing, and the two predicates currently give different
answers to the same question about the same person. Whichever way it goes,
`serve()` and `recipients()` should be made to agree deliberately rather than by
neither consulting the other.

Note that this is not a defect in either module. Both do what they were built to
do, and the gap is between them — which is rule 12's pair, arriving because a
surface was added that reads through one and not the other.

**The send side had the matching half, found it by ablation, and closed it.**
`docs/PLAN-GUARDIANSHIP.md` records two mutants passing all of G1–G11 — one
ignoring edge dates entirely, one messaging *every* edge holder — because
**every one of the original eleven is about a *restriction* and none is about
the standing edge itself.** *"The plan reasoned carefully about what suppresses
a recipient and never wrote down what makes one."*

**G12 and G13 were added in response**, `records/sending.py` requires
`e.kind == "guardian_of"` and `e.live_at(at)`, and `tests/ablate.py` carries a
mutation for each. That half is shut.

**The read side has no equivalent, and the asymmetry is the finding.** Of the
mutations `tests/ablate.py` points at `records/serving.py`, **none involves a
restriction at all** — because `serve()` has no restriction to mutate. So the
send side got a gap found by ablation and closed within the day, and the read
side cannot get the same treatment: there is nothing there to break.

That is a sharper statement of *needs a human 1* than the one above it. The
question is not whether the two predicates should agree. It is that **G12 and
G13 are the worked template** — a gate naming what constitutes standing, and a
mutation that fails without it — and the read side needs the analogous pair
before anything reads through `serve()` on a guardian's behalf.

## GU7, and the second thing a guardian signs

**This list had one guardian signature on it and the tree has two.** GU7 names
`Widening`. `records/crossing.py` carries the other: an `Envelope`, which is the
only way W-3's permitted lane crossing can exist at all.

The module's own account of why it was written is worth quoting, because it is
the same failure this file is correcting one level down. `docs/LANE-MODEL.md`
encoded W-3's prohibition, and encoded its closing sentence —
*"a shared event is two lane entries with one referent"* — and dropped the
middle one. `envelope` and `crossing` appear
zero times in `docs/schema/001_lanes.proposed.sql`, so the prohibition had a
mechanism and **the permission was unrepresentable** — *"a real sibling case can
only be served by not recording that it happened, which is the worse of the two
failures."*

Four things are required and none has a default, each being the one a hurried
implementation would omit: both lanes named, a purpose, an expiry, and a
guardian's signature that is *"not a role, not staff, not the system."*

**Needs a human — 2.** Whether a guardian assistant composes envelopes. The
household case is ordinary — two children in the same program, one event, a
parent who wants one answer — and it is exactly the case that produces a
standing envelope if the interface makes expiry feel like paperwork. The W-5
clause that governs GU7 governs this too: **the assistant may compose the request
and may never be what makes it live.**

The two objects are deliberately alike — `Widening`'s docstring says it is
*"shaped after `crossing.Envelope`, and for the same reason"*, and both carry a
purpose, an expiry and a signature that a role cannot supply. **The difference
is the axis, and it is where the erosion would happen.** A `Widening` names one
category over one subject; an `Envelope` names *two lanes*, and an envelope
naming one lane is a wildcard over the other. A guardian composing by
conversation will describe the outcome they want — *"let me see both of them in
one place"* — and the assistant turning that into a durable cross-lane
permission has written the wildcard the type refuses to have a field for.

## GU5, and the capability that is already built

**G10** requires `who_could_see(student, field, at)` to answer *"with a reason,
as a query rather than an investigation."* It exists. A guardian asking *"who
can see Ben's medical form"* gets a list with reasons, without anybody running a
report.

This is the guardian's counterpart to the student's disclosure log, and it is
the same architectural thesis pointing the same way: the system can explain
itself to the people it holds records about.

**One edge, and it is sharp.** `Recipients.suppressed` records *"who was
excluded, and why — for G10, never for sending."* So the machinery can report
that the other guardian was suppressed. **Telling guardian A that guardian B is
under a restriction is a disclosure about B**, and in a split household it is
exactly the disclosure most likely to cause harm. G10's answer is scoped to who
*could see a field*; the suppression list belongs to the send path. They must not
be joined in an answer, and nothing currently stops a surface joining them.

## GU6, and the honest limit

Guardians already hold receipts (`records/receipts.py`) — one per write into
their student's lane, carrying the lane, the position, the entry digest and the
time. Positions are per-lane, so holding 1, 2, 3 and 5 shows that **4 is
missing**, without the institution's cooperation and without learning anything
about any other student.

An assistant can do that check. What it must say while doing it is the module's
own stated limit: **receipts detect removal, never omission.** An entry never
written produces no receipt and its absence is invisible; a guardian holding
1..N cannot tell whether N is everything. The assistant must not let "your
receipts check out" be heard as "the record is complete", and the authenticity
claim is likewise no stronger than an HMAC — anyone with the key can mint one.

## GU3, and the waiver that must stay invisible

§18 of the capability map asks for **fee waivers that are structurally invisible
to peers**, and §7's refusal-indistinguishability principle generalises it: *the
system must not leak the fact of a refusal.*

A balance answer is where that leaks. *"Nothing is owed"* and *"nothing is owed
because a waiver was applied"* must be the same sentence, and an assistant that
volunteers the second has undone the control in the friendliest possible voice.

**The mechanism is that the assistant renders `Serving.value` and never
composes a fuller explanation from adjacent fields it can also see.** Same rule
as the student surface's S5, arriving through a different door.

## GU10 — the one item 12 left open

*"Whether a **guardian** may read the lane's log is also open and is not this
item — a guardian reading it learns which staff member is looking at a record,
which is nearer §13's prohibited standing scores than it appears, and guardians
already hold receipts."*

**Needs a human — 3.** This is quoted rather than resolved. The thing that has
changed since it was written is that **the log now exists**, so the question is
no longer about a hypothetical. `records/disclosure.py` carries a `Ledger` whose
`log_for(lane_id)` returns one lane's chain, which means the object a guardian
would be granted is already the right shape and already scoped — W-1 holds
whichever way GU10 goes, and the open question is narrower than it reads.

The module also supplies a fact that cuts *toward* granting it: a read returning
no payload is recorded **by rung and outcome, never by whether a value existed**,
so the log a guardian would see cannot be mined for which fields their child has.
The §7 indistinguishability guarantee survives the disclosure of the log itself.

Two observations that belong to the item and were not available when it was
written:

- The assistant makes it *askable*. "Has anyone opened Ben's file this week" is a
  natural sentence a guardian will say to a prompt and would never have filed a
  request for. Deferring the decision means the surface answers or refuses by
  accident.
- A guardian watching which staff member reads a record repeatedly is
  constructing exactly the standing cross-context judgement §13 prohibits — of a
  staff member, by a parent, with no seal and nobody to ask.

**And `records/consent.py` (§18 item 10, closed 2026-07-30) supplies a
vocabulary this question did not have.** `governs()` decides *whom to ask* per
principal: `self` and `guardian_of` **hold** the authority and are asked at the
door under SAFE's session model; `staff_of`, `director_of`, `judge_at` and
`clinician_for` **exercise** an authority granted elsewhere and are never
prompted. That split is the sharp edge of GU10 restated — the staff member whose
read a guardian would be watching is someone the system has already classified
as *exercising the guardian's own authority*. Whether it follows that the
guardian may see them exercise it, or that they may not because the reads are
the staff member's and not theirs, is precisely the open question. It is now at
least a question with two named sides rather than an intuition.

## The persona with an end date

**Needs a human — 4.** Every other assistant on this list is bounded by *what*
it may answer. The guardian's is additionally bounded by *when it ceases to be
a guardian's*, and nothing in this document says what that looks like from the
inside.

`records/exit.py` is unambiguous about the event. At the threshold written into
the office at entry — majority, graduation, transfer, withdrawal — *"keys to the
lane issue to its subject or named successor, full history intact; the
guardian's standing ends or reduces to what the new owner grants back."* And the
term is not negotiated at the threshold: `open_lane()` requires `exit_terms`, so
it was written when the lane was opened.

So a guardian assistant has a date on which it becomes a **student** assistant
over the same record, with the former guardian holding whatever the new owner
grants back — possibly nothing. Three things follow and none is written:

- **The transition is a disclosure event about the child, to the parent.** *"You
  can no longer see this"* on a birthday is a true sentence and a hard one, and
  the interface that says it is not designed.
- **Silence is worse than the sentence.** An assistant that simply starts
  refusing has produced the failure §7 spends its length avoiding: a refusal
  indistinguishable from an absence, at the one moment the guardian has a
  correct explanation available.
- **`transfer()` hands the graduate their own past, and the guardian's copy is
  not addressed.** Receipts they already hold, answers they already read, a
  conversation history if one is kept. The clause covers the lane. It does not
  cover what a surface accumulated beside it, and a conversational surface
  accumulates a great deal.

That last point is this document's version of the rule that a guarantee lives in
a mechanism. For the record itself the enforcement is real and early: `Lane`
cannot be constructed without `exit_terms`, so W-6 is satisfied at the call. For
the assistant's own residue there is no equivalent call, and therefore nothing
on either the enforcement or the ledger side.

## The refusals

**GU11, "how is my child doing."** `evaluative_praise` and `peer_comparison`.
This is what a parent most wants and the answer is no. The honest framing is the
same as the student's S11: it is a real cost, not a technicality, and it will
read as evasive to someone who is worried.

**GU12, prediction.** `voice.prediction`, and `RECONCILE-19.md`'s refusal of
19.3b transfers unchanged — it arrives before the thing it predicts and has
nobody's name on it. *"Will they make the chair"* is also a ranking, so
`records/conflict.py` refuses it structurally: `refuse_to_rank()` raises
`NotComputable`, and the `Escalation` a halt returns cannot carry an order.

## GU8, and the clauses that erode quietly

`records/dispositions.py` implements I-6 and adds constraints an assistant
composing a request must respect, both read off the module:

- **A request without a timebound cannot be constructed.** There is no default,
  deliberately — `P-2` of Schedule A says a default *"would let issuers stop
  declaring."* So an assistant offering to file an absence request must obtain a
  date, and cannot quietly supply one.
- **The office cannot lengthen its own timebound.** `extend()` requires a
  *different* office and records the extension. An assistant must never present
  extension as a thing the answering office can do for itself, which is the
  shape *"the single most eroded rule in any queue"* takes when a helpful
  interface offers it.

**GU13, another student or the other guardian.** No roster, no directory, and
critically **no visibility of the other guardian's activity**. Households split;
guardianship is *"a set of independently revocable edges, never one shared
family login"* (§4.2). An assistant that answers *"did Ben's father see this"* has
turned two independent credentials into one household view, and in the custody
case that is the whole harm.

## The transport collision

§4.2's recommended target is **(b) mailbox relay + PWA replica**, and its
metadata control is not optional: padding to size buckets and flushing on a
**fixed schedule**, because *"timing alone reconstructs a custody
arrangement"* — a guardian mailbox receiving traffic on alternating weekends.

**A conversational assistant is bursty and interactive by construction.** Run
over the relay it either defeats the timing control by flushing on demand, or it
answers at the next scheduled flush and is not an assistant. This is a direct
collision between the guardian assistant and the control §4.2 calls the one this
design most needs.

**The resolution that dissolves it, rather than trading against it:** the
guardian assistant answers **from the local replica, on the device, with no
round trip at all.** §4.2 already specifies that replica — *"reads are local and
instant; writes queue and flush when connectivity allows."* A read that never
leaves the device generates no traffic, so there is no timing to analyse.

**And it may need no model.** GU1–GU4, GU6 and GU8 are retrieval and arithmetic
over local structured data; the register — *complete sentences, no jargon, no
program shorthand, a named person* — is a template's job, not a model's. If the
guardian assistant is retrieval plus templates, then **refusal 1 and the timing
control both stop applying**, because nothing is inferred and nothing is sent.

**Needs a human — 5.** Whether that is enough to be worth building, or whether a
guardian assistant without generated language is just a search box with a
friendly label. That is a product judgement, and it is the one place in this
document where the architecture does not force the answer.

**Needs a human — 6.** If a model *is* wanted on the guardian surface, it runs
on the device — a parent's phone, possibly old, possibly cheap — or the timing
control breaks. Nobody has sized that. It is a feasibility question, not a design
one, and it should be answered before the surface is committed to rather than
after.

## The module sweep

Every module under `records/`, listed by `ls`, with what it does to this
document. Listing all of them rather than the relevant ones is the mechanism:
**a module added later is a blank row rather than a silence**, which is how the
first draft of this file came to name a single guardian signature when the tree
held two.

| module | bearing on the guardian surface |
|---|---|
| `classify.py` | **Bears, not worked.** A field returning `UNDECIDED` is a build failure, not a refusal. A guardian asking about a newly added form is the likeliest way anyone meets one |
| `conflict.py` | **Cited** — GU12, structurally |
| `consent.py` | **Cited** — GU10, and the hold/exercise split |
| `crossing.py` | **Cited** — GU7's second signature, *needs a human 2* |
| `disclosure.py` | **Cited** — GU10, `Ledger.log_for` and the indistinguishability property |
| `dispatch.py` | **Bears, not worked.** It is the route a read must take, and the finding above is that `serve()` never sees a `ContactRestriction`. The gap is upstream of the dispatcher, not in it |
| `dispositions.py` | **Cited** — GU8, I-6, and the clauses that erode |
| `exit.py` | **Cited** — *needs a human 4*, the persona with an end date |
| `export.py` | **Bears, not worked.** `bundle()` produces artifacts and touches no filesystem. What a guardian may ask for a copy of, before the threshold, is not on this list |
| `marking.py` | **Bears, not worked.** A judge's remark is a lane entry about their child, carrying a `seat` and possibly a fitted `ScorePosition`. Whether a guardian reads adjudication commentary is nowhere decided, and GU11's refusal does not settle it — a remark about the work is not a rating of the learner |
| `practice.py` | **Bears, not worked.** `own()` reads one lane, which is the child's. Whether the guardian sees it is the same question as GU10 in a lower-stakes register, and answering the easy one first would be useful |
| `receipts.py` | **Cited** — GU6, and the honest limit |
| `rungs.py` | **Bears, not worked.** Rule 14 as a type. The register — *complete sentences, no jargon* — is in direct tension with `L4`, and rendering a rung to a parent without either jargon or a false ordering is unsolved |
| `sealing.py` | **Bears, not worked.** A `draft` shown to a guardian who reads it as the institution's position is rule 10's failure with a witness |
| `sending.py` | **Cited** — the finding, G12 and G13 |
| `serving.py` | **Cited** — the finding, and its other half |
| `standing.py` | **Cited** — GU5 and GU7 |
| `witness.py` | **Bears, not worked.** Receipts detect removal and anchors establish anteriority; together they are a stronger claim than either. Nothing here says whether a guardian gets the second |

Counted off the table, 10 rows say *cited* and 8 say *bears, not worked*, and
none says *no bearing* — the guardian is the only persona in the design that
touches every part of it. The rows that bear rather than being cited are the
ones with no counterpart in §19 of the capability map to have been modelled on,
which is the same defect
in method that `RECONCILE-STUDENT.md` names in its omitted-capability section.
