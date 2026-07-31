# The student's assistant, against the decisions already settled

**Status:** reconciliation, not a decision record. **Three items need a human
and are marked.** Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

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
| S9 | Own practice record | **Survives, with a mechanism** |
| S10 | Practice streaks, milestones, cumulative hours | **Needs a decision** |
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
in their own lane.

**S10 needs a decision.** §1 of the capability map proposes practice streaks,
cumulative-hour milestones and chair-challenge standings. §9 of the architecture
already flags it against UTETY's ground rule — *feedback is about the work,
never the learner; no praise of the person, no leaderboards* — and observes that
*some of that is about the work and survives; some of it is a leaderboard with a
different name.*

Sharpen it: **a streak is a standing score of a person with the number left
in.** It persists across contexts, it rates the learner rather than the work,
and §13 prohibits exactly that. `voice.evaluative_praise` will not catch it,
because a streak counter says nothing — it just counts, and the student supplies
the praise.

**Needs a human — 1.** Cumulative hours *this season, for this student, shown
only to them* is arguably a record rather than a score. A streak with a flame
next to it is not. The line is real and somebody has to draw it. It is worth
drawing before the feature ships, because a streak is very hard to take away
once students have one.

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

**S13, comparison.** `peer_comparison`, refusal 6, and W-7. *"A comparison does
not stop being a ranking for being spelled out in words."*

**Needs a human — 2.** These three refusals are correct and they are also most
of what a teenager wants from a band app. The assistant's value therefore rests
entirely on S1–S6. If that is judged too thin to be worth building, the honest
outcome is **no student assistant**, not a student assistant that softens the
refusals — and that decision should be taken deliberately rather than reached by
degrees once the refusals start feeling unhelpful.

## What this does not cover

**Needs a human — 3.** Nothing here addresses the student who is also a
**section leader**. §16 of the capability map asks for *"their section's
attendance, sectional planning, peer feedback"* — a minor with access over other
minors. The first half must be N named edges, never a section scope (W-2,
refusal 5). The second half collides head-on with S13, refusal 4 and refusal 6:
`voice.peer_comparison` will refuse the sentences that feature exists to
produce. It is a separate persona wearing a student's account, and it is not
reconciled anywhere.
