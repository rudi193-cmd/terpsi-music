# The guardian's assistant, against the decisions already settled

**Status:** reconciliation, not a decision record. **Four items need a human and
are marked.** Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

Second of the three lists `docs/RECONCILE-19.md` does not cover; see
`docs/RECONCILE-STUDENT.md` for the first and for the shared framing. The
decisions reconciled against are not restated: §4.1 and §4.2 (the traffic split
and the transactional remainder), §7.1 (dated guardianship), §7.4 (the ward
clauses), §13, §15, `docs/PLAN-GUARDIANSHIP.md`'s G1–G11, and `voice.py`.

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
| GU8 | Absence requests and their dated disposition | **Survives** (I-6) |
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

**Needs a human — 2.** This is quoted rather than resolved. Two observations
that belong to it and were not available when it was written:

- The assistant makes it *askable*. "Has anyone opened Ben's file this week" is a
  natural sentence a guardian will say to a prompt and would never have filed a
  request for. Deferring the decision means the surface answers or refuses by
  accident.
- A guardian watching which staff member reads a record repeatedly is
  constructing exactly the standing cross-context judgement §13 prohibits — of a
  staff member, by a parent, with no seal and nobody to ask.

## The refusals

**GU11, "how is my child doing."** `evaluative_praise` and `peer_comparison`.
This is what a parent most wants and the answer is no. The honest framing is the
same as the student's S11: it is a real cost, not a technicality, and it will
read as evasive to someone who is worried.

**GU12, prediction.** `voice.prediction`, and `RECONCILE-19.md`'s refusal of
19.3b transfers unchanged — it arrives before the thing it predicts and has
nobody's name on it.

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

**Needs a human — 3.** Whether that is enough to be worth building, or whether a
guardian assistant without generated language is just a search box with a
friendly label. That is a product judgement, and it is the one place in this
document where the architecture does not force the answer.

**Needs a human — 4.** If a model *is* wanted on the guardian surface, it runs
on the device — a parent's phone, possibly old, possibly cheap — or the timing
control breaks. Nobody has sized that. It is a feasibility question, not a design
one, and it should be answered before the surface is committed to rather than
after.
