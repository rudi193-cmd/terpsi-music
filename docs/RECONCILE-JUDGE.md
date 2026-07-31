# The judge's assistant, against the decisions already settled

**Status:** reconciliation, not a decision record. **Four items need a human
and are marked.** One defect is demonstrated rather than argued. Nothing here
changes a canonical document; where this and `ARCHITECTURE.md` disagree, the doc
wins and this file is the defect.

**This file reconciles against `records/` as well as against the documents**,
and the second half arrived after the first draft. *The module sweep* at the
foot names every module in the tree, so that a later one is a blank row rather
than a silence.

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

**`records/sealing.py` is that cascade built, and the first draft of this file
cited the clause without it.** Three properties, each of them enforcement at
the call rather than a description in a docstring:

- **There is no auto-seal path.** `seal()` requires a named person, the
  parameter has no default, and a machine identity is refused outright —
  `"the director"` is not a signature and neither is `"system"`.
- **A seal names what was sealed**, by digest, so a later edit produces a
  different digest and **cannot inherit the old seal**. This is the mechanism J5
  needs and did not have: tightened prose is a new body, so the tightening
  cannot arrive wearing the original's signature.
- **Rejection is terminal and keeps its reason**, never a return to `draft`, so
  a transcript that was rejected and re-drafted does not look like one nobody
  reviewed.

Only `SEALED` is `servable`. An assistant that renders an unsealed transcript to
anyone — including back to the judge as though it were the record — is reading a
state the type already distinguishes.

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

**That sentence now has a mechanism under it, and this list originally cited
only prose.** `records/conflict.py` makes the refusal structural rather than
remembered: `refuse_to_rank()` raises `NotComputable`, and where a halt returns
something it returns an `Escalation` — a frozen type with **no field an order
fits in**, whose `recommendation` is a property that raises rather than an
absent attribute, *"so a caller reaching for a recommendation gets the clause,
not an `AttributeError` they will paper over with `getattr(..., None)`."*

The judge surface is where that matters most, because it is the one persona
whose *job* is to produce an order. Everywhere else the refusal is enforcement
over something nobody asked for. Here it draws the line through the middle of the work, and a
line drawn by a regex over prose would be in the wrong place: that regex is a
ledger over sentences, and a suggested score is a ranking whether or not it is
ever spelled out in one.

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

**Half of that question already has a shape, in `records/export.py`.** `bundle()`
returns artifacts — a name, a media type and text — and **touches no
filesystem**, and `verify()` checks a bundle it did not produce. So *"terpsi is
the source of an export rather than the host of a record"* is not a thing to be
designed either; it is a call, with the write left to a seam. What remains for a
human is not the mechanism but the offer: whether a judge is told, at the door,
that their calibration leaves with them and nothing stays. That belongs beside
the purpose declaration in J6, not in a settings screen nobody opens.

## J6 — the knock, made legible

The declared purpose on entry and the reconciliation on exit already exist as
mechanism. What an assistant adds is that the guest can *see* their own
reconciliation: **here is what you said you were here for, and here is what you
touched.**

**And the reconciliation has a source that this file did not name.**
`records/disclosure.py` is the log every read writes to, hash-chained and
append-only in the sense rule 18 asks for — `append()` returns a new log and
nothing rewrites an entry, after PR #3 found by executing the DDL that a table
called append-only in a comment was `UPDATE`-able. The exit reconciliation is a
filter over that chain, not a second record kept for the purpose. **A guest
whose reconciliation came from a separate summary could be shown a different
history from the one the institution keeps**, which is the failure the whole
knock exists to make impossible.

**Needs a human — 3, and `records/consent.py` produced it.** `governs()` places
`judge_at` among the principals who *exercise* an authority granted elsewhere,
and are therefore **never prompted** — the guardian's consent is what governs,
and asking the judge to consent on a student's behalf is asking the wrong person
in a form that makes yes the only workable answer. That is right, and it sits
awkwardly beside §7.2's declared purpose on entry, which is a prompt at the door
to the least-trusted principal in the design.

They are not in contradiction: one asks *whose authorization permits this*, the
other asks *what did you come here to do*. **But they are the same screen**, and
a guest who answers one will experience it as answering both. A surface that
lets a declared purpose read as a consent has built the weaker authorization
path §16 warns about, wearing the friendliest possible label. Which prompt the
judge sees at the door, and how the two are kept visibly separate, is a design
decision nobody has taken.

Across `RECONCILE-STUDENT.md`, `RECONCILE-GUARDIAN.md` and this file, that is
the strongest argument for a guest-facing assistant at all. §7.2 wants the least-trusted session narrated loudest; a
narration the guest reads is louder than one filed where only staff look, and it
costs nothing to show a person their own audit trail.

## J10 — the cross-event question

**Needs a human — 4.** A judge asking *"what did I give this ensemble last
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

## The module sweep

Every module under `records/`, listed by `ls`, with what it does to this
document. All of them rather than the relevant ones, so that **a module added
later is a blank row rather than a silence** — the failure this file's first
draft made by reconciling against `ARCHITECTURE.md` and not against the tree.

| module | bearing on the judge surface |
|---|---|
| `classify.py` | **No bearing.** The judge writes about a performance and the fields they touch are the sheet's, not a student's record |
| `conflict.py` | **Cited** — J2, the refusal that runs through the middle of the job |
| `consent.py` | **Cited** — *needs a human 3*, the door with two prompts on it |
| `crossing.py` | **Bears, not worked.** A remark about a moment involving several students fans out to one lane entry each, sharing a referent, and no envelope is signed for that — it is W-1 satisfied by fan-out, not W-3 permitted by crossing. Worth confirming rather than assuming, because the fan-out is what makes it legal |
| `disclosure.py` | **Cited** — J6, the source the reconciliation is a filter over |
| `dispatch.py` | **Bears, not worked.** The read path for J3 and J4. The demonstrated defect is upstream of it: the voice gate it runs second has no judge register to run in |
| `dispositions.py` | **No bearing.** No queue on this surface |
| `exit.py` | **No bearing on the judge's own record.** The grant expires on its own (§4); a lane is not opened for a guest |
| `export.py` | **Cited** — *needs a human 2*, and half of it is already answered |
| `marking.py` | **Cited** — J1, `at_ms`, `seat`, and the `P1`/`P3` refusal in `align()` |
| `practice.py` | **No bearing** |
| `receipts.py` | **Bears, not worked.** A judge writes into a student's lane, so a receipt is minted for a guardian. Whether the judge sees the receipt for their own write — the guest's copy of *what I touched* in J6 — is unwritten |
| `rungs.py` | **Bears, not worked.** J8 refuses anything about a named student, and the sheet is nonetheless a lane entry with a rung. Which rung adjudication commentary lands at is not decided in this file or anywhere else it cites |
| `sealing.py` | **Cited** — J1 and J5, and the digest whose enforcement keeps a tightening from inheriting a signature |
| `sending.py` | **No bearing.** Nothing is sent to a judge |
| `serving.py` | **Bears, not worked.** J3, J4 and J10 all read through it; J10's open question is exactly a `serve()` call outside a grant that expired on its own |
| `standing.py` | **Bears, not worked.** `judge_at :: Event_X` is the edge, and this file discusses the grant's expiry without naming the module that holds it |
| `witness.py` | **No bearing.** Anchoring is the institution's obligation, not a guest's |

Counted off the table, 6 rows say *cited*, 6 say *bears, not worked*, and 6 say
*no bearing*. The last group is the useful one: this is the only persona for
which a third of the tree is genuinely irrelevant, and that is the same fact as
the opening line — a judge does few things, at one event, mostly writing.
