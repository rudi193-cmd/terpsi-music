# Crossings — one session's defects, and the six patterns under them

**Status:** findings record, not a specification. Nothing here governs anything.
`docs/ARCHITECTURE.md` governs; §16 is the section this is evidence for.

**What this is.** On 2026-07-30 a single session wrote the sensitivity ladder,
the lane model and its migration, §24 of the capability map, the craft checker,
and three drafts of a song. It also produced twenty-one defects, all of them
in work committed the same day. This records them, and the six patterns they
turned out to share — because the patterns are more useful than the fixes, and
because a defect list nobody generalises from is just an apology.

This document carries no numbered sections: a `§N` here always means
`docs/ARCHITECTURE.md`.

---

## The tally

Grouped by **how it was caught**, which is the only grouping that turned out to
matter.

| Caught by | Count | What |
|---|---|---|
| Executing the DDL | 4 | Rewritable disclosure log; `edge.target_id` with no FK; `target_kind` accepting `'Sandwich'`; classification registry empty against 87 columns |
| Running the checker | 6 | Copyright notice parsed as verse; `ght` flagged as an unsingable cluster; slant rule calling *waits*/*park* a rhyme; bridge stanzas compared to each other; closing-stop check firing per section; two `CHORUS` sections sharing a finding id |
| The checker, on the song | 1 | Second pre-chorus scanning 6 against the first's 8 |
| Applying the checklist by hand | 4 | Verse 3 at 6/5/5/5; only verse 1 rhyming; point-of-view wobble; one flat abstraction in a weak position |
| The section-reference guard | 3 | An unqualified reference to §20 of the capability map; a bare §8.2; and then this very row, which quoted the first defect verbatim and tripped the guard a third time |
| Deriving a count from the tree | 2 | CLAUDE.md's "17 sections" against 18; §18's "Ten tables" against twelve |
| Reading prose carefully | 1 | §6's eight data classes not covering the categories §20 of the capability map names |
| Ear alone | 1 | Verse 3 reading as static inventory |

**Nineteen of twenty-one were caught by something mechanical.** Two came from
reading. That ratio is the reason this document exists.

---

## Crossing one — the same failure, six times, and one fix that worked

| Where | The declaration | What was behind it |
|---|---|---|
| `quiet-corner` (§7.3) | Eight `session_scope` visibility fields | Nothing. A gate at the frontend request layer |
| §6, an earlier revision | A three-seam purity assertion quoted as live practice | A docstring example no app invokes |
| `openclaw-sap-gate` (§7.2) | Revocation | `rm` on a folder, leaving no dated record |
| `001_lanes.proposed.sql` | "APPEND-ONLY" above three tables | Nothing. `UPDATE` and `DELETE` both succeeded |
| same file | `target_kind` ∈ Lane / Ensemble / Event | A comment. Postgres accepted `'Sandwich'` |
| `lyrics/get-ready.txt` v1 | "No rights reserved by anyone but the author" | No author. The text is machine-generated |

One defect wearing six costumes: **a declaration with nothing behind it.** §18
of this document's parent calls it out as the fleet's tracked pattern, and the
vocabulary was already sharp before any of the above was written — *say
"enforcement" or "ledger."*

**The fix was also the same six times, and it is not "forbid the violation."**
It is *make the violation inexpressible.*

- `marching-arts` cannot reach the network because there is **no client to call**
- `access_grant` cannot express a group scope because there is **no column a set fits in**
- `L5` is not policy-excluded from grants; it is **absent from the CHECK**
- the append-only trigger does not warn; it **raises**
- `edge` has no `target_kind` because **which foreign key is set *is* the kind**, so it cannot disagree with the row it points at

Removing the *ability* survives a careless edit. Removing the *permission* does
not. Every durable guarantee in this repo is of the first kind, and every defect
above was of the second.

---

## Crossing two — the floor automates, the ceiling never does

The seam table in §24 of the capability map has seven rows. Six are arithmetic:
syllables against notes, consonants against tempo, breath against phrase. The
seventh is *the lyric's emotional turn and the music's harmonic turn arriving on
the same word*, and its requirements column reads **"Both, and taste."**

The same line is drawn, independently, in five other places:

- The `L`-rungs are mechanical; deciding a field belongs on one is judgement
- Hit Song Science's only solid result is negative — quality is not learnable from features
- The checker found five defects in the song and proposed **zero** replacements
- W-7: the system presents, a human decides — *never computes a priority*
- §8.2: a machine answer is a `draft` until a named human seals it

Five components, drawn by different hands for different reasons, putting the
boundary in the identical place. None of them pretends it sits higher than it
does, and that restraint is the reason any of them can be trusted at all.

---

## Crossing three — nothing was true until it ran

`001_lanes.proposed.sql` was internally consistent, argued for in prose, and
covered by a passing test suite. It was also wrong in four ways, one of which
left the FERPA §99.32 disclosure record silently rewritable. **None of the four
was visible from reading it.** All four surfaced within seconds of `psql`.

The checker, read carefully before it shipped, immediately announced that a
copyright notice had an inconsistent rhyme scheme.

The song, read three times and revised twice, gave up five more defects to
counting — including one introduced *three turns after* the rule it violated
had been explained in prose.

§10 already says it: **acceptance is mutation, not a green suite.** §18 item 0
exists because §14's entire "Exists" column was assembled from READMEs rather
than source. The rule was right every time it was tested today, and every time,
it was right about the person applying it.

---

## Crossing four — the clauses outlived their cases

The most interesting pattern of the six, and the least expected.

| Clause | Written about | Also settles |
|---|---|---|
| W-5 — *agency grows by signature, never by drift* | A guardian signing for a ward | Whether an adaptive tutor may fade a student's scaffolds on its own. It may not |
| §8.2 — *a draft until a named human seals it* | A judge confirming a transcription | Whether a machine critiquing a machine draft can produce a record. It cannot |
| §7 — refusal indistinguishability | A member declining a consent | Why declination records are `L5`, and why `MediaAsset`'s consent field needs a named seam |
| §7.1 — termination by date, never by delete | A court order arriving mid-season | The whole bitemporal split, including the three tables that must **not** take the pair |
| §6 — the friction floor | An agent agreeing fluently with a stressed director | Two models mirroring each other, a question nobody had asked when it was written |

Specifications normally rot toward the cases that produced them. These
generalised instead, and the reason is visible in how they are phrased: each
names a **relationship** — office over ward, machine to human, holder to
subject — rather than an incident. A clause pitched at the relationship reaches
cases its author never saw. A clause pitched at the incident does not.

Worth stating because it is a drafting instruction, not an observation.

---

## Crossing five — one rule, every altitude

*"I'm lonely" is a report. The untouched second toothbrush is the thing that
lands.*

That is lyric craft. It is also, unchanged:

- **Advocacy.** *The arts build well-rounded students* is gone before the next agenda item. *Forty-one kids spent nine months on eleven minutes* is not.
- **Component mapping.** **Exists** is a word. A file you opened is a fact (§18 item 0).
- **Counting.** "17 sections" was a claim. Eighteen came from the tree (CLAUDE.md rule 17).
- **Provenance.** `P1 Measured` and `P5 Assumed` are this distinction with a prefix on it (§15).
- **Testing.** A green suite is an assertion. A refused forbidden act is evidence (§10).

Five domains, one epistemic rule: **a specific beats a statement, and the
specific is the one that survives contact with someone checking.**

This is why §24 of the capability map reaches all ten rungs from student to
board. It is not a tool that happens to scale — it is one rule that was general
before anybody built anything on it.

---

## Crossing six — nothing audits itself, and the failure is always silent

§18's sharpest sentence: **an unverified table and a verified one look
identical.**

The same shape, five more times:

- The indistinguishability test passes if the predicate returns nothing to **anyone** (§7)
- The purity checker sees imports and is blind to filesystem writes (§6)
- `P2` decays into a lie without its label changing (§15)
- `privacy_tier: client_only` coexists with `local_processing: 0.96` and nothing objects (§6)
- A mirror cannot audit itself, which is why the friction floor runs **outside** the model it watches (§6)

And then, three times in one session, the section-reference guard caught its own
author writing a dangling reference. The second was inside a paragraph arguing
that self-audit fails. **The third was in the tally row above, which quoted the
first defect verbatim and thereby committed it again** — the checker cannot tell
a citation from a quotation of one, and the row describing the bug reproduced
the bug.

That last one is worth leaving in rather than smoothing over, because it is the
cleanest specimen in the file. A document *about* silent self-audit failure,
written by the author of the failures, failed the same way in the paragraph
where it was counting them. Nothing caught it except a fifty-line stdlib script
with no opinions.

**Which is the argument for the whole discipline, delivered by the tooling onto
the person making it.** Every guard written today carries a test that points it
at a decoy and confirms it complains, because a guard that has only ever
succeeded is indistinguishable from one that cannot fail.

---

## Provenance of this file

Written in the session it describes, by the author of every defect in it. That
is the worst possible vantage point for an audit and the best one for a
confession, and this is the second kind of document.

Every count above was derived from the tree at the time of writing. If a later
reader finds one wrong, that is crossing five arriving on schedule, and the
correction belongs here rather than in a commit message.
