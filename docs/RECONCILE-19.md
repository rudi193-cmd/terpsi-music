# §19 of the capability map, against the decisions already settled

**Status:** reconciliation, not a decision record. Two items need a human and
are marked. Nothing here changes a canonical document; where this and
`ARCHITECTURE.md` disagree, the doc wins and this file is the defect.

§19 of the capability map lists thirteen things an assistant would do. Several
collide with decisions already settled for the adjudication core, and the
collision has one shape every time: **a derived number about how well a person
or an ensemble performed.**

The decisions being reconciled against are not restated here — they live in
§15 (the scales and how they must not be confused), §13 (no standing
cross-context scores), §7.4 (the clauses governing an office over a ward), and
in the marching-arts build plan. What follows is only the reconciliation.

---

## The thirteen

| § | Capability | Verdict |
|---|---|---|
| 19.1 | Natural-language query for directors | **Survives** |
| 19.2 | Practice plans from adjudication and clinician commentary | **Survives** — and it is the flagship |
| 19.3a | Caption-level trend analysis | **Survives, with a mechanism** |
| 19.3b | Score progression forecasting | **Refused** |
| 19.4 | Attendance/engagement risk prediction | **Survives only as a type** |
| 19.5 | Instrumentation gap forecasting | **Survives** |
| 19.6 | Repertoire "calibrated to measured ensemble ability" | **Needs a decision** |
| 19.7 | Budget and enrollment forecasting | **Survives** |
| 19.8 | Rehearsal and meeting summarization | **Survives** |
| 19.9 | Commentary summarization sliced by section | **Survives, with a mechanism** |
| 19.10 | Longitudinal growth narratives | **Needs a decision** |
| 19.11 | Program notes and newsletter drafting | **Survives** — it is an export |
| 19.12 | Schedule conflict detection | **Survives** |
| 19.13 | Anomaly detection as a check-in prompt | **Survives** — best-stated item in the section |

---

## The refusal

**19.3b, score progression forecasting.** A projected score competes with a
caption score, and is worse than one produced after the fact on three counts.
It arrives *before* the performance, so it anchors the people about to be
judged. It has **nobody's name on it**, so there is no seal and no one to ask —
which is the same objection §16's `sealed / draft / pending` distinction exists
to raise. And fitted to a near one-dimensional sheet, it is a placement
prediction wearing the costume of eight captions.

It also runs directly into §13's prohibition on standing cross-context scores:
a forecast is a rating of an ensemble carried from the events it was fitted on
into an event that has not happened.

The line between this and 19.3a is sharp and worth writing down:

> *"GE2 has moved 1.4 points across six weeks, aggregated per sheet"* is a
> description of what happened.
> *"GE2 will be 82 on Saturday"* is a competing score.

The first survives. The second is refused.

## Mechanisms, where a sentence is not enough

**19.3a — trend analysis** renders its aggregation in the same string as the
figure or it does not render. §15 settles that a rank correlation is not one
number until you say what you grouped by; this is that rule applied at the
surface. `voice.py` enforces it for anything the assistant says.

**19.4 — risk prediction.** The capability map already says the right thing:
*"surfaced as a check-in prompt rather than a flag."* That is currently a
sentence and needs to be a type. **The output object carries no numeric
field** — a name and a prompt, nothing scoreable, nothing sortable. If a model
computes a risk score internally it does not survive the boundary. Otherwise
"surfaced as a prompt" is a rendering choice, and rendering choices get changed
by whoever builds the dashboard in year two.

Note the direction hazard §15 raises while you are here: on a risk scale higher
is worse and on every other scale in this system higher is better. Two scales
pointing opposite ways in one view is how a check-in prompt becomes a
leaderboard.

**19.9 — commentary summarization by section** must not aggregate into a score.
Eight commentary rows into a paragraph is description; eight rows into
"brass: 7/10" is 19.3b through a side door. Same mechanism as 19.4: no numeric
field on the type.

**19.2 — the practice loop** survives intact and is the reason to build any of
this. Two constraints, both already required elsewhere: the output is *tasks*,
never a rating, and it is a `draft` until a named human seals it (§8.2, §16).
A rejected draft is recorded as durably as an accepted one.

---

## The two that need a human

**19.6 — repertoire "calibrated to measured ensemble ability."** That phrase
contains a number about how good the band is. Two readings:

- *Calibrated to roster facts* — who plays what, ranges, section sizes, years
  of experience. Survives cleanly; instrumentation data, not evaluation.
- *Calibrated to a derived ability score* — refused for the same reasons as
  19.3b, and additionally a standing cross-context score under §13.

The capability map does not say which, and the difference is the whole
decision. The reading that seems intended is the first; the sentence as written
says the second.

**19.10 — longitudinal growth narratives for conferences.** A narrative about a
student's growth, drafted by a machine, read to a parent. Three things must be
true and only the first is currently stated:

1. Drafted from that student's own lane and no other (§7.4 W-1, W-3).
2. Sealed by a named human before it reaches a parent — it is an export, so it
   is announced and gated (§7.2), never graduating out of that.
3. **Contains no comparative language.** *"Improved more than most of the
   section"* is ranked peer data in prose, and the objection does not care
   whether the ranking is rendered as a number.

The third is the one that will be violated by accident, because comparative
phrasing is what makes a narrative read well. `voice.py` catches the
anticipated forms and publishes the ones it misses; if 19.10 is wanted, that
check has to exist before the feature does.

---

## What the exercise found about §19 of the capability map itself

§19 of the capability map reads as written from a capability list rather than
run past §7, §13, §15 or the settled adjudication decisions. Three of thirteen
collide, and all three collide in the same place — which suggests the section
needs one pass, not thirteen.

The pass is: **for every item, name the object it produces.** If the object is
a number about how well a person or ensemble performed, it is refused however
it is rendered. If it is a description, a task, a logistics fact, or a prompt
to go and talk to somebody, it survives. That single question resolves twelve
of the thirteen. 19.6 needs a human because its sentence is ambiguous about
which object it means.
