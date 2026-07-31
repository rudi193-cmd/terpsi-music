# The annual deposit

**Status:** procedure. `docs/ARCHITECTURE.md` governs; this is the operating
detail for one leg of a decision recorded there (§18 item 15), and where the two
disagree the architecture wins and this file is the defect.

**What it is for.** §18 item 15 decided a composite rather than a counterparty:
a public timestamp weekly, this deposit annually, guardian receipts
continuously. They fail differently on purpose. The weekly publication is cheap
and frequent and trusts nobody, and it asks a courtroom to understand what a
digest is. This leg asks nobody to understand anything: a sealed envelope, a
date stamped by the postal service or logged by a law office, and a page a
person can read.

**What it is not.** It is not a backup. Nothing here preserves the records
themselves — a deposit is a dated copy of the *codes*, and a programme that
loses its records and keeps its deposits has lost its records. Escrow is a
separate obligation and §5 carries it.

**This procedure is performed by people, and that is deliberate.** The weekly
leg is machine work with a machine's failure modes. This one is annual, manual,
and slow enough that a person notices when it does not happen.

---

## What is deposited

**One page, and its enclosures.** The page is the publication register that
`records/publication.py` renders — every scheduled week of the year, in order,
each line reading in words what happened to it. The register is built from
anchors, and an anchor holds a code, a number of entries and a date. It cannot
hold a name, a lane or a note, because those are not fields it has.

The enclosures are the proof files the weekly leg received, one per published
week, exactly as they arrived.

**Three things are deliberately not deposited:**

| | not deposited | why |
|---|---|---|
| 1 | the records themselves | this is a witness, not a copy. A sealed envelope of student records in a law office is a second store of minors' data with none of §5's protections |
| 2 | the derivation | the working behind a whole-programme code names every lane and how many entries each held, week by week. That is one child's year, so `derivation_artifact()` marks it local and it stays where the records are |
| 3 | any signature key | the deposit proves a date. A key in the envelope would let the holder mint what the envelope exists to bound |

**How the page reads.** A juror should be able to follow it without being
taught anything. The register says, in its own words, that a short code is
computed from the records as they stood on a given day; that any later change
to those records produces a different code; and that the code cannot be turned
back into a name, a note or a number. Then it lists the days.

A line that was never published says so in those words — *nothing was sent* —
rather than being omitted. A page with a quiet gap invites the reading that
nothing happened that week, and the schedule runs whether or not anything
happened, so a gap is a missed publication and never a quiet week.

## When

**On the calendar, once a year, on a date fixed at the start.** The same rule
as the weekly leg and for the same reason: a deposit made in the month a
programme is in trouble tells a reader when the programme was in trouble. The
date is chosen once, written into the programme's own calendar, and does not
move because a year was busy or quiet.

Pick a date away from the season's edges — not the week of a championship,
not the first week of term. The point is a date nobody has a reason to move.

The register covers the twelve months ending on that date, and the periods abut
rather than overlap: a year that is not inside any deposit is a year with no
legible witness, and the person reading the series two years later is the one
who finds out.

## Who performs it

**A named person, and a named second.** Not a role — `docs/ARCHITECTURE.md` is
consistent that a role is not a person, and *the director* is a chair rather
than somebody who can be asked what they did in March.

* **The custodian.** Usually the person who holds the programme's records.
  They print the register, gather the proof files, seal them and send them.
* **The witness to the act.** A second named person, not reporting to the
  first, who sees the envelope sealed and signs the log line. A deposit
  performed alone is a deposit whose only account is the account of the person
  with the most to gain from it.
* **The recipient.** Either the programme's own address by certified mail, or a
  law office that will log receipt. The law office is the stronger of the two,
  because certified mail to yourself proves a date and leaves custody with the
  party the deposit exists to bind.

Where the institution is a school or district, the custodian and the witness
should sit on different sides of the records office — one from the programme,
one from the administration that would be asked about it later.

## The receipt of deposit

**What comes back is the point, and it is kept like a proof file.**

* **Certified mail:** the article number and the dated delivery record.
* **A law office:** a letter or docket line naming what was received, from
  whom, and on what date — and stating that the envelope was received sealed.

The receipt is filed beside the year's register, under the same name, so the
two read as a pair and a missing half is visible in a directory listing. That
is the same shape the weekly leg uses for its own pair, where a submission file
and a proof file share a stem.

**A deposit with no receipt is not a deposit.** It is a claim that an envelope
was sent, which is the state the weekly leg calls *sent, no proof back yet* —
and it is recorded in those words rather than as a completed act. The custodian
chases it; if a receipt never arrives, the entry stands as unanswered and the
next section applies.

## A missed deposit

**Every ask gets a dated disposition, and this is an ask the programme makes of
itself.** So the deposit is raised as a request against the fixed date, with the
timebound declared when it is raised — `records/dispositions.py` is the
mechanism and this is one of its cases. Three outcomes, and only one of them is
silence:

| state | what it means | what happens |
|---|---|---|
| **answered** | the deposit was made and a receipt is filed | the request closes, dated, with the receipt named |
| **open** | the date has not arrived | nothing, and the request is visible in the meantime |
| **unanswered past the date** | the date passed and no receipt is filed | it escalates to the office above the custodian, and the escalation is dated |

**An unanswered deposit is never closed by making a later one.** The later
deposit is its own request with its own date. The gap stays on the record,
because a year with no legible witness is a fact about that year and cannot be
repaired by a subsequent envelope — the whole value of a dated series is that
its holes are visible.

**What surfaces it.** Two things, and neither is somebody remembering:

1. **The register itself.** A year whose weeks are printed and whose deposit
   line is unanswered reads as unanswered on its own page.
2. **The disposition.** Silence is not an answer, so the request escalates on
   its own timebound rather than waiting to be asked about.

## What this leg does not prove

The same limit as every other witness, restated here because this is the page a
lawyer reads first. A deposit shows that what was written existed by the date
on the envelope and has not changed since. It cannot show that everything which
happened was written down. Selective recording defeats every scheme of this
kind, and the mitigations for it — recording at the predicate rather than by
somebody choosing to type, and refusals recorded as durably as disclosures —
live elsewhere and are not proof.
