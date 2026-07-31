# The safeguarding stance, against a student-facing assistant

**Status:** reconciliation, not a decision record. **Four items need a human and
are marked.** Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

**This file reconciles against `records/` as well as against the documents**,
and it did not when it was first written. Counted by reading the first draft
back, its citations were `personas.py`, `voice.py`, `ARCHITECTURE.md` and
`docs/FLEET-READS.md`, and no module in the tree at all. Reading the tree
moved one of the three mechanisms below from *checkable* to *not currently
representable*, and gave another one a type it turned out to already have. *The
module sweep* at the foot lists every module so a later one is a blank row
rather than a silence.

The stance being reconciled is not restated as if it were new. It lives in
`personas.py`'s `CANON_LOCKS` — *"never receives a disclosure"*, asserted by
`tests/test_voice.py` — in `voice.py`'s `confidant` rule, and in
`docs/FLEET-READS.md`, which records where the reasoning came from.

---

## What the stance says, and what it was reasoning about

> **`SAFEGUARDING` is "routed, never received"**, on the reasoning that *"in
> every leadership-implicating case on the public record, surfacing was
> external, so an intake would digitise a broken path rather than repair it."*

That argument is about building a **reporting channel** — a "report a concern"
form that collects allegations into a system the institution controls, in a
domain where the institution is sometimes the thing being reported. It holds
completely, and nothing below weakens it.

**What it never weighed is whether a conversational surface exists at all.**
The reasoning was written about an intake as a *feature*. A free-text prompt is
not a feature anyone designs as an intake; it becomes one because a child types
into it. The stance and the prompt were never in the same room.

## The argument that puts them in the same room

A student who wants to ask something asks *something*. If the program's own app
has no prompt, the question goes to a general-purpose assistant instead. That
produces three losses, and none of them is hypothetical:

- **The routing is gone.** `voice.py`, the `mirroring` flag with its comment
  naming *a student in crisis*, and `willow-gate`'s friction floor are good
  mechanisms that apply to zero conversations if the conversations happen
  somewhere else.
- **The data leaves anyway.** Refusal 1 forbids *this system* sending student
  data to a third party — and its enforcement is by assertion on
  `respond()`'s `provider_used`, not by trusting an environment variable, since
  `WILLOW_INFERENCE_PROVIDER` defaults to `auto` and is fail-open unconfigured.
  Either way it governs only this system's egress. It says nothing about a
  student carrying the data out themselves — a minor pasting *"my director said
  this about my accommodation"* into a hosted model is the same disclosure,
  reached by the absence of a local option rather than by a path this refusal
  can see.
- **Nobody learns it happened.** An external conversation leaves no trace here,
  so the program cannot even know the path exists.

So refusing to build a prompt does not produce abstinence. It produces
**displacement**, to somewhere with no gate, no named adult, and no log.

## What that licenses, and what it does not

**Licensed: the assistant is present, and is good.** A student surface with a
free-text prompt over the captive slice of §4 and the self edge of §18 item 12.

**Not licensed, and the distinction is the whole entry:**

- **Not an intake.** Nothing typed in that register is retained, indexed, or
  made searchable. The original reasoning stands untouched: this system does not
  collect allegations.
- **Not a confidant.** `voice.confidant` stays REFUSE. "They would use another
  assistant anyway" is a reason to be *available*; it is not a reason to compete
  on emotional pull. An assistant that invites disclosure is still an intake,
  and now a more effective one.
- **Not a classifier.** The assistant does not attempt to detect whether a child
  is in danger. A model judging that about a minor is its own harm, and its
  false negatives are unbearable. **Route without deciding.**

## The mechanism

The stance survives if three things hold, and each is checkable:

1. **No retention in that register.** Text in the confidant register is not
   written to any lane, log or index. What the disclosure log records is that a
   route was offered — never what was said.
2. **A named human is always one action away**, visibly, on every screen of the
   student surface — not surfaced on detection, because detection is refused.
   The route is ambient.
3. **The assistant's only move is to surface the route.** `voice.confidant`
   already refuses the register; what is missing is the *positive* half — the
   refusal must hand over to a person rather than simply declining.

### Point 1 is not currently representable, and that is a finding

`records/disclosure.py` is the log, and **an entry in it is a disclosure
decision, not an event**: `record()` takes a `Serving` and writes
`(occurred_at, principal_id, subject_id, field_name, rung, outcome, authority)`,
chained. *"A route was offered"* has no `field_name`, no `rung`, and no
`Serving` behind it. There is nowhere in the type for it to go, and the
temptation — invent a pseudo-field, give it a rung, write it in — would put a
non-disclosure into a chain whose whole claim is that it records disclosures.

**Needs a human — 1.** Where the offer is recorded, if anywhere. Two things make
this harder than it looks:

- The subject reads their own disclosure log at every rung (§18 item 12,
  `standing.py`). So an offer recorded in the student's lane is **an offer the
  student can see the record of**, and so can anyone the student later shows it
  to. A log entry saying *a route was offered on 12 October* is not what was
  said, and in a household where the concern is a household concern it is close
  enough to be the same harm.
- Recording nothing means the program cannot know the route is working, which is
  the third loss this entry opened with — *nobody learns it happened* — arriving
  from the other direction.

The module has the right instinct already, in a neighbouring case: a read that
returned no payload is recorded **by rung and outcome, never by whether a value
existed**, precisely so the audit trail does not become the leak. The analogous
move here is an aggregate with no subject in it. Nobody has designed one, and
this entry should not invent it in passing.

### Point 2 already has a type, built for a different clause

**`records/conflict.py` refuses a role where a person is required, and its
refusal list contains the exact word this entry would have used.**
`Escalation.to_whom` is validated at construction against `_NOT_A_PERSON`, which
carries `"staff"`, `"the director"`, `"the office"` — and `"someone"` and
`"an adult"`. The error text is the clause: *"a role is how an escalation
reaches nobody."*

That was written for W-7, where the system halts between wards and hands the
decision to a human. It is the same shape as mechanism 2 and it is stricter than
the prose here, which said *"a named human is always one action away"* and would
have been satisfied by a screen reading **talk to an adult**. The tree already
refuses that string. **A safeguarding route should be constructed through the
same validation rather than beside it**, which makes the ambient route a typed
object with a person's name in it, not a label.

Note what this does *not* make the route: an `Escalation` is a halt in a
decision, and a safeguarding route is not a decision the system was making. The
reusable part is the validation and the named-person requirement, not the class.

### Point 3 does not exist, and now has an address

`voice.refuses()` refuses a sentence; nothing routes. **That is the build item
this entry produces**, and since this file was written the place it belongs
acquired a name: `records/dispatch.py` runs `serve()` first and the voice gate
second, and exposes `Dispatch.blocked_by_voice`. So there is already one point
in the tree that knows a refusal happened for a voice reason rather than an
entitlement reason — which is exactly the distinction the positive half needs,
and it is one call site rather than every surface.

**Needs a human — 2.** Whether the route hangs off `dispatch()` or off the
surface. Hanging it off `dispatch()` makes it uniform and testable and makes
every persona's refusals eligible for it, including a guardian's, which is very
likely wrong. Hanging it off the surface makes it a student-surface decision and
puts it back where rule 19 has the least purchase. This is the one place in this
entry where the cheaper option is not obviously the worse one.

## The canon lock

`CANON_LOCKS` carries *"never receives a disclosure"* and `tests/test_voice.py`
asserts it. A free-text prompt makes the literal reading false the first time a
student types into it, and a lock that is false is worse than no lock.

**Proposed:** sharpen rather than remove.

| | |
|---|---|
| now | `"never receives a disclosure"` |
| proposed | `"never solicits a disclosure"`, `"never retains a disclosure"`, `"never is the endpoint"` |

Three locks where there was one, each with a mechanism behind it — solicitation
by `voice.confidant`, retention by the no-write rule, endpoint by the ambient
route. The current lock reads as stronger and is the only one of the four that
cannot be enforced once a prompt exists.

**Needs a human — 3.** Whether the prompt exists at all. Everything above
assumes it does. If the answer is no, the student surface is structured queries
only, this entry is withdrawn, and the original stance needs no change.

## The load-bearing assumption, marked

*"They would otherwise use a general-purpose assistant"* is doing the work in
this entry and it is **`assumed`** (§15). Not measured, not fitted. Every
conclusion here inherits that rung, and by `min()` the entry is worth no more.

It is also **checkable**: a program can ask its own students what they already
use. Until someone does, this entry rests on a plausible claim about teenagers
rather than on an observation of these ones.

## A collision that predates this entry

§12 of the capability map asks for **"anonymous concern reporting for hazing and
harassment"**, and lists **"mandated reporting workflows — handled with extreme
care around who sees what."** Anonymous concern reporting *is* an intake — the
exact feature the stance refuses, sitting in the capability map, unreconciled.

**Needs a human — 4.** These cannot both be right as written. Either the stance
admits a narrow intake with its own reasoning, or §12's line is struck and the
capability is routed to whatever channel the school already runs. This entry
does not resolve it, and it is not about the assistant — it is older and larger.

## The module sweep

Every module under `records/`, listed by `ls`, with what it does to this
document. All of them rather than the relevant ones, so that **a module added
later is a blank row rather than a silence.** This file had no such section and
no module citations at all until it was reconciled against the tree, which is
why two of its three mechanisms changed on contact.

| module | bearing on the safeguarding stance |
|---|---|
| `classify.py` | **No bearing.** Nothing typed in the confidant register becomes a field |
| `conflict.py` | **Cited** — point 2's type, and the refusal list that already contains *"an adult"* |
| `consent.py` | **Bears, not worked.** `governs()` puts `self` among the principals asked at the door. A student surface with a prompt on it is that door, and a consent screen appearing beside a free-text box is the shape *"not a confidant"* is guarding against |
| `crossing.py` | **No bearing** |
| `disclosure.py` | **Cited** — point 1, and why it is not currently representable |
| `dispatch.py` | **Cited** — point 3's address, `blocked_by_voice` |
| `dispositions.py` | **Bears, and it is uncomfortable.** I-6 gives requests a dated disposition and an office. A route is deliberately *not* a request into a queue — that is the whole of *routed, never received* — so the module that would make a concern trackable is the module this stance refuses to use. Worth stating plainly, because "why can't we just track it" is the question this entry will be asked |
| `exit.py` | **No bearing** |
| `export.py` | **No bearing.** There is nothing retained to export, which is the point |
| `marking.py` | **No bearing** |
| `practice.py` | **No bearing** |
| `receipts.py` | **No bearing.** A receipt is minted for a write, and there is no write |
| `rungs.py` | **Bears, not worked.** If an offer is ever recorded (*needs a human 1*), it needs a rung, and there is no rung for a thing that is not a field. That is the same finding from the other side |
| `sealing.py` | **Bears, not worked.** If the assistant composes any text in this register — even *"here is who to talk to"* — rule 10 makes it a `draft`, and a `draft` shown to a child in distress as though it were the program's position is the failure rule 10 exists for. The likeliest resolution is that the route is a fixed string a named human sealed once, not a generated sentence |
| `sending.py` | **No bearing.** Refusal 7 already keeps records off SMS, and there is no record here |
| `serving.py` | **Bears, not worked.** The captive slice is served through it; the confidant register is orthogonal to it. Nothing joins them and nothing should |
| `standing.py` | **Cited** — the subject reads their own log, which is what makes *needs a human 1* hard |
| `witness.py` | **No bearing.** An anchor covers the chain; the point of this entry is that nothing enters the chain |

Counted off the table, 4 rows say *cited*, 5 say *bears, not worked*, and 9 say
*no bearing*. The large *no bearing* column is this entry's thesis stated as a
table: **a stance whose content is that nothing is retained should touch almost
no module that retains anything.** A future version of this table with fewer
blanks in that column is evidence the stance eroded, and that is a cheaper
signal to watch than re-reading the prose.
