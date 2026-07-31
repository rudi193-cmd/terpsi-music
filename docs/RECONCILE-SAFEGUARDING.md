# The safeguarding stance, against a student-facing assistant

**Status:** reconciliation, not a decision record. **Two items need a human and
are marked.** Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

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

Point 3 does not exist. `voice.refuses()` blocks a sentence; nothing routes.
**That is the build item this entry produces.**

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

**Needs a human — 1.** Whether the prompt exists at all. Everything above
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

**Needs a human — 2.** These cannot both be right as written. Either the stance
admits a narrow intake with its own reasoning, or §12's line is struck and the
capability is routed to whatever channel the school already runs. This entry
does not resolve it, and it is not about the assistant — it is older and larger.
