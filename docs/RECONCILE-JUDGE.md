# The judge's assistant, against the decisions already settled

**Status:** reconciliation, not a decision record. **Three items need a human
and are marked.** One defect is demonstrated rather than argued. Nothing here
changes a canonical document; where this and `ARCHITECTURE.md` disagree, the doc
wins and this file is the defect.

Third and last of the lists `docs/RECONCILE-19.md` does not cover; see
`docs/RECONCILE-STUDENT.md` for the shared framing. Shorter than the others, and
the shortness is the finding: a judge does few things, all of them at one event,
and almost all of them are *writing* rather than reading.

The decisions reconciled against are not restated: §4 (ephemeral scoped grants),
§7.2 (the knock), §8.2 (sealing), §13 (SA-3), §18 item 7 (score-position
anchoring, closed — `records/marking.py`), and `voice.py`.

**This is the persona §7.2 is written for** — *"a declared purpose on entry,
reconciled on exit, announced loudly because the trust level is low. A grant
says what a guest may do; the reconciliation says what they did."*

---

## The eleven

| § | Capability | Verdict |
|---|---|---|
| J1 | Timecoded commentary capture | **Survives** — flagship; `records/marking.py` is built, and a `draft` always |
| J2 | Caption score entry | **Survives** — the system records a claim, never computes one |
| J3 | Sheet and rubric recall | **Survives** |
| J4 | Recall of their own commentary, this event | **Survives** |
| J5 | Tightening their own commentary prose | **Survives, with a defect** — see below |
| J6 | Their own purpose declaration and exit reconciliation | **Survives** — the knock, made legible |
| J7 | Their own calibration over time | **Survives only as owner == subject** |
| J8 | Anything about a named student | **Refused** |
| J9 | Placement prediction | **Refused** |
| J10 | Their own scores at earlier events here | **Needs a decision** |
| J11 | Another judge's scores or commentary | **Refused** |

---

## The defect, demonstrated

**`voice.py` has one ruleset and `personas.py` has four registers, and the judge
has neither.**

`personas.REGISTER` carries `STUDENT`, `STAFF`, `GUARDIAN`, `DIRECTOR`. There is
no `JUDGE`, and `get_persona` falls back to the default — while the module's own
docstring says the card is not shown to *"a student, guardian or judge."* Five
audiences, four registers, one ruleset.

The consequence is not cosmetic. `voice.peer_comparison` is calibrated for
prose served **to** a student; a judge writes **about** a performance, and the
same words carry different work. Three sentences, none of which compares two
students, all refused:

```
REFUSED  The trumpets were ahead of the pulse in bar 40.            ('ahead of')
REFUSED  The strongest moment was the closer.                       ('strongest')
REFUSED  Balance favoured the low brass more than the ballad wanted. ('more than')
```

The first compares a section to *the pulse*. The second compares moments within
one show. The third compares balance to an *intent*. Every one is craft
vocabulary about the work, which is precisely what UTETY's ground rule asks for
— *feedback is about the work, never the learner* — and the gate refuses it.

Worse than refusing: it refuses the **precise** phrasing and would pass a vaguer
one. A gate that penalises specificity teaches people to write around it, and
what they write instead is less useful to the student the commentary is for.

**Needs a human — 1.** Two ways out, and they are not equivalent.

- **Give the ruleset a register axis.** `guard()` already has the shape —
  `serves_value` is one such axis. A second would let `peer_comparison` apply to
  prose served to a student or guardian and not to a judge's commentary about a
  performance. The rules stay; their scope becomes explicit.
- **Route judge commentary outside the gate.** Cheaper, and it means the one
  persona §7.2 calls least trusted is the one nothing checks. Rule 18 applies:
  a gate with a hole shaped like a persona is a ledger for that persona.

The first is more work and is the one this document would argue for, but the
choice is a human's. What is not optional is choosing: today the gate would
refuse a judge's legitimate sentence, and nobody has noticed because no surface
routes one through it yet.

## J1 and J2 — write, not read

Every other persona's assistant mostly reads. The judge's mostly writes, and
that changes which rules bite.

**J1 is a `draft`, always.** Rule 10 is explicit and names this case —
*"a machine answer is a `draft` until a named human seals it. Transcripts
especially."* An ASR pass over a judge's dictation is a machine answer about a
student's performance, and §8.2 supplies the rest: **a role is not a signature**,
and a rejection is as durable as an approval. The assistant may transcribe; the
judge seals, by name.

**And the anchor already exists.** §18 item 7 closed 2026-07-30 —
`records/marking.py` — so J1's *"timecoded"* is not a thing to be designed. A
`Mark` carries a **required** `at_ms` and `seat`, an **optional derived**
`ScorePosition`, and `drift()` reconciles the two. Three properties of it bear
directly on what an assistant may do here:

- **The tap is `P1 measured`; an alignment is `P3 fitted`,** and `align()`
  refuses a position whose provenance outranks the observation it came from. An
  assistant that "corrects" where a remark was anchored is overwriting the `P1`
  half with an inference, which the module already forbids at the call.
- **A mark naming a student is lane-scoped and there is no participant list**
  (W-1). A judge's remark about a moment involving three students is three lane
  entries with one `referent`, and an assistant composing a single note about
  "the trumpets" must not be what writes it.
- **`seat` is required**, which §13 wants for the `field-acoustics` pairing —
  *the acoustic model predicts what arrived at that seat.* An assistant capturing
  commentary without it silently costs a capability nobody will notice missing.

**J5 is the sharp one against this.** *Tightening a judge's own commentary
prose* operates on the `P1` half — the words a human actually said about a
performance. Editing them is not the same act as deriving a score position from
them, and the seal in §8.2 is what makes the difference legible: the judge seals
the tightened text, or it stays a `draft` and the original stands.

**J2 records a claim and never computes one.** A judge ordering ensembles is
their job. The system computing an order is refusal 6, and the distinction is
the whole of adjudication: *"the system presents, a human decides."* The
assistant must never suggest a score, never complete a partially-entered sheet
by inference, and never surface what a comparable ensemble scored while a sheet
is open.

## J7 — the capability that survives only by ownership

§13's calibration item was **corrected in place**, and the correction matters
here. Adjudicator calibration as originally proposed is `SA-3`, a **prohibited
scope** — *"any durable rating of an agent carried between contexts or
offices"* — **invalid even fully signed by root**, with the attempt recorded as
a failed issuance naming the signatory.

What survives is *"the judge running their own ledger, owner == subject."* The
engine is unchanged; the ownership is not the program's to choose.

So a judge's assistant may help them see whether their own 70% means 70% — and
**terpsi may not hold that ledger, show it to a circuit, or retain it after the
event.** The capability is real and the custody is the constraint.

**Needs a human — 2.** §4 puts this persona on *"a kiosk device the org owns and
wipes, or their own device on a guest SSID."* An owner-is-subject ledger cannot
live on a kiosk that gets wiped, and putting it on the judge's own device makes
terpsi a source of an export rather than a host of a record. Which of those is
being offered has to be decided before J7 is built, because the answer changes
whether terpsi stores anything at all.

## J6 — the knock, made legible

The declared purpose on entry and the reconciliation on exit already exist as
mechanism. What an assistant adds is that the guest can *see* their own
reconciliation: **here is what you said you were here for, and here is what you
touched.**

Across `RECONCILE-STUDENT.md`, `RECONCILE-GUARDIAN.md` and this file, that is
the strongest argument for a guest-facing assistant at all. §7.2 wants the least-trusted session narrated loudest; a
narration the guest reads is louder than one filed where only staff look, and it
costs nothing to show a person their own audit trail.

## J10 — the cross-event question

**Needs a human — 3.** A judge asking *"what did I give this ensemble last
year"* is asking for their own prior claim about a named program. It is not
`SA-3` — it is not a rating of an agent — but it is durable and cross-context,
and it anchors the judgement about to be made in exactly the way
`RECONCILE-19.md` refuses 19.3b for.

The grant makes it awkward too: `judge_at :: Event_X` is time-boxed to one event
window plus a commentary grace period. Answering a question about last year
means reading outside the grant that expired on its own, which is the property
§4 chose it for.

## The refusals

**J8, anything about a named student.** A judge adjudicates a performance. The
grant is to an *event*, not to a roster, and nothing in a caption sheet requires
a student's name, medical status or fee balance.

**J9, placement prediction.** `voice.prediction`, and `RECONCILE-19.md`'s
refusal of 19.3b transfers unchanged — a projected placement arrives before the
performance and anchors the people about to be judged. From a judge it would
anchor the judgement itself.

**J11, another judge's scores or commentary during the event.** Panel
independence is the point of a panel. This is not currently written down as a
rule anywhere, and it should be — it is the one refusal on this list that rests
on adjudication convention rather than on a clause in this repository.
