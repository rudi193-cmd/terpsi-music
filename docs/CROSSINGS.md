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

### Addendum, 2026-07-30 — the sentence above was not true of everything

The tally is a snapshot of the session it names and is left unchanged. This is a
later specimen, filed here because it is the cleanest one yet and because it
falsifies the paragraph directly above it.

`tests/test_serving.py` documented §18 item 12 — the subject having no standing
in their own lane — and closed with a tripwire meant to fire the moment that
changed:

```python
assert not any(k in ("self", "subject_of") for k in ("guardian_of", "staff_of")), (
    "if a self edge now exists, item 12 has moved and this test should too"
)
```

It compares two hardcoded tuples. Neither has anything to do with the edge
vocabulary the predicate actually reads. **It is a tautology**, it passed on the
day the `self` edge shipped, and it could never have failed on any input in any
version of this repository.

Three things make it the sharpest instance in the file:

1. **It was written to catch exactly the change it did not catch.** Not a guard
   that drifted — a guard that was born unable to fire, with a failure message
   describing the event it would not detect.
2. **It postdates the paragraph above.** *"Every guard written today carries a
   test that points it at a decoy"* — this one did not, and was written in the
   same repository by the same author, after that sentence was committed.
3. **The mutation harness could not have caught it either.** `tests/ablate.py`
   mutates the *predicate* and asks whether a suite notices. This defect is in
   the suite, and no mutation of `records/serving.py` can reach an assertion
   that never reads it. **Ablation proves a guard is load-bearing; it says
   nothing about an assertion that is not attached to one.** That is a hole in
   the method this repository leans on hardest, and it was found by hand, while
   changing the thing the test claimed to watch.

The replacement asserts against the predicate in both directions: a subject with
no edge is refused, and a subject with one is served *and names the edge*. It can
fail, which is the only property that was ever wanted.

### Addendum, 2026-08-01 — the checker printed the sentence `voice.py` refuses

Also filed here rather than in the tally, which stays a snapshot of the session
it names.

`voice.py` carries a rule called `false_all_clear`. It refuses six phrasings in
assistant text, one of them the literal string `no findings`, with the reason
*"a lookup that failed is unknown, not clear, and absence never renders as a
result."* It has been in the tree since the voice module was written, it has a
fixture, and it ablates red.

`craft/__main__.py` printed this, for a file it could not parse:

```
=== unavailable
  No song sections found. …returning unavailable rather than no findings (§6).

=== findings (0)
```

The banner says the checker read nothing. The next line puts a count on it. The
count is a result, and the thing it is a result about never happened — the same
sentence the module two directories up refuses by name, printed by the tool
that ships in the same package.

**The diff side was worse, and it was worse in the flattering direction.**
`run_diff` in both skins read `.findings` off each side and subtracted, ignoring
whether either side had been read at all. So `--against` an unreadable earlier
draft reported *"0 resolved, 9 introduced"* — every finding in the newer draft
blamed on a revision that did not add any of them — and a revision the parser
could not read reported
*"9 resolved, 0 introduced"*, every finding cleared, by a comparison against
nothing. `run_diff`'s own docstring is the accusation:

> *a tool reporting only the wins is flattering rather than teaching*

Four things about it worth keeping:

1. **The rule was not missing. It was applied one layer too low.** `run_all`
   gets rule 13 exactly right — `Report.unavailable` exists for this, the
   docstrings argue for it, and `test_an_unparseable_file_is_unavailable_not_clean`
   has guarded it since the checker was written. Both callers then dropped the
   field on the floor. **A refusal that is not read is not a refusal**, which is
   crossing one arriving at a new address: *a declaration with nothing behind
   it*, where this time the declaration is a struct field and what is behind it
   is one `if` nobody wrote.
2. **Neither surface had a test.** `craft/__main__.py` had no test of any kind —
   the suites imported `run_all` and `run_diff` and never the CLI — and no file
   under `craft/` carried an ablation row. 477 mutations on this branch at the
   moment these five landed, none of them aimed at the one piece of working
   software in the repository. The guards were dense where the design is and
   absent where the code is.
3. **`unavailable` was doing two jobs.** A draft that could not be read and a
   draft that was read with 34 words of unknown stress both land in the same
   list, and the song in this repo is permanently in the second state. A caller
   keying off `if report.unavailable` would have printed *unavailable* for every
   real lyric. That is why the fix is a second field (`Report.unread`) rather
   than a test on the first, and why both suites now assert the partial case
   stays comparable.
4. **One defect, two skins, and the fix is a middle rather than two edits**
   (§16). `checks.diff_declined` is imported by `prose.run_diff`, and
   `test_the_two_skins_refuse_a_comparison_through_one_middle` asserts it is the
   same object and that the string `def diff_declined` does not appear in
   `prose.py`. The pair was already there; only the middle is new.

Counts in this addendum were derived from the tree on 2026-08-02, on the branch
this landed on rather than the one it was written on: 482 mutations in
`tests/ablate.py` after this change, five of them the first to point at
`craft/`. The figures in the original commit message (120 before, 125 after)
were true of `claude/wall-emptiness-8gj70w` and were stale the moment the change
was carried here — which is rule 17 charging a toll on a port, and the reason
the number is re-derived rather than copied across with the code.

### Addendum, 2026-08-02 — the inventory was the authority on its own completeness

`tests/test_rule13_acceptance.py` is the sweep: it enumerates every seam this
repository consults and breaks each one for real. Its docstring states the
property it is for:

> *so that a seam added later without an unknown state is caught by a test
> nobody had to remember to write*

It names its own middle, which is what §16 asks. The middle is
`test_every_seam_in_the_inventory_has_a_test`, and it walks `SEAMS` and asserts
a test exists for each row.

**It only ran one way.** Walking the list and finding a test for each row proves
the tests are complete *against the list*. Nothing walked the tree and asserted
a row for each seam, so the list was the only authority on whether the list was
complete — and the case the docstring promises to catch, a module consulting a
fallible source with **no** unknown state, is exactly the case that leaves no
trace in the list. The promise was kept for seams somebody had already
remembered, which is the set that needed no promise.

Three things worth keeping from the fix:

1. **Half a middle passes for a whole one, because it is green.** A pair with
   one reconciler in one direction looks identical, in a test run, to a pair
   with a reconciler. This is crossing four — a declaration with an enforcement
   attached to it — arriving in the one file in the tree written to catch it,
   and it survived a review and a merge.
2. **The obvious mark was the wrong mark, and measuring said so.** The tempting
   definition of *consults a fallible source* is *"the module has an
   `UNKNOWN`-shaped enum member or an `unavailable` field."* Measured against
   this tree it flags 27 modules, 18 of them absent from `SEAMS` — but the fatal
   objection is not the noise. It can only see modules that **already** have an
   unknown state, so by construction it can never reach the case the docstring
   is about. It would have been a green check pointed away from its own subject.
   The mark that shipped is *a function takes the source as a parameter*, which
   is independent of whether an unknown state exists.
3. **It found eight on its first run.** `drop/preparing.py`,
   `drop/producer.py`, `records/assistance.py`, `records/attendance.py`,
   `records/commentary.py`, `records/fees.py`, `records/inference.py`,
   `store/narration.py`. Six of the eight were already honoured and already
   tested in their own suites — which is not a defence, it is this file's
   subject: a seam covered only where it lives is a seam the sweep cannot report
   on, and the sweep is what a reviewer reads. Seven are rows now; the eighth is
   exempt with a reason and a debt, because breaking it needs a cluster.

And the residual, said out loud rather than rounded off: the mark does not reach
`craft/`, whose fallible source is its own parser over caller-supplied text.
`craft/` is inventoried because a person put it there, one addendum above, after
it shipped the defect. `KNOWN_BLIND` names that shape and asserts the mark still
misses it, so the day somebody widens the mark, the list of published misses
goes red rather than quietly becoming a lie. That is `voice.KNOWN_MISSES`'s
discipline applied to a check's own blind spot.

Counts derived from the tree on 2026-08-02: `SEAMS` 43 rows, `CANNOT_DISTINGUISH`
3, `EXEMPT` 1, `KNOWN_BLIND` 2, and 487 mutations in `tests/ablate.py` — five of
them aimed at the completeness check itself, because a check that finds nothing
today and cannot be shown to fail is a ledger (rule 18).

*The three mutation figures in the two addenda above were each written on a
branch that did not yet carry the other's rows — 473, 478 and 483 — and every
one was stale at the merge. Corrected here to the merged tree: 487. That is
crossing five arriving twice in one session, in the file that predicts it, and
the mechanism is worth naming because it is not carelessness: a count derived
correctly from the tree you are standing on is still a claim about a tree that
is about to change under you. Parallel branches make rule 17 a merge-time
obligation, not only a writing-time one.*

### Addendum, 2026-08-02 — a refusal whose scope was not the scope of the act

The sharpest defect of the session, and the one nothing in the tree could see.

`records/retention.py` refuses carefully. `assess()` places a record on four
standings, `due()` returns only `DUE`, and `dispose()` raises `NotDue` for
anything else — `LIVE`, `RETAINED` and `UNKNOWN` are all kept, which is the
fail-closed direction. Five mutations covered that ladder and every one went red.

Then `purge()` handed the decision to `atrest.destroy(lane_id=…)`, which drops
**every** wrapping under the lane:

```python
kept = tuple(w for w in keyring.wrappings if w.lane_id != lane)
```

A lane is one student (rule 8). So a `Disposition` scoped to one season and one
kind destroyed the key opening that student's every sealed payload, in every
season, of every kind. Run against `lane_entry` with every migration in the
tree today applied: a live medical note reading `epi-pen in the case` came back
`key_destroyed` after purging an unrelated aged-out attendance record.
`assess()` had just called it `live`, `due()` had excluded it, and `dispose()`
would have raised on it.

**Refusal 3 held throughout, and saying so precisely is the point.** Nothing was
deleted. Both rows stayed. The `Erasure` was dated, attributed, and outlived
what it erased. Every property the module was built to guarantee was intact.
What failed was that a record-scoped refusal governed a student-scoped act — and
because the act was correct and the refusal was correct, the defect existed only
in the *join* between them, where neither module's tests look.

**Why the mutation harness could not have caught it, again.** The 2026-07-30
addendum says ablation proves a guard is load-bearing and says nothing about an
assertion not attached to one. This is the sibling case: the assertion existed
and was attached to a real guard, but its *scope* was wrong.
`test_purge_destroys_only_the_lanes_it_was_given` compares `lane-a` against
`lane-b` and passes honestly. The forbidden act was inside a lane, and no
mutation of a correct predicate can reach a test that never asks the question.
**Ablation proves a guard fires. It cannot tell you the guard is aimed at the
right thing.**

The fix is crossing one's, applied at the join: `purge()` now requires the
lane's full record set and refuses unless every record in it is due, with a lane
the caller cannot enumerate refused as unknown rather than read as empty. The
key-model fix that would make the refusal unnecessary — seal per `(lane,
season)` — is recorded as §18 item 19 rather than chosen quietly, because a
conservative fix that goes unnamed reads afterwards as the design.

One thing found on the way that belongs here: **there is no `season` column
anywhere in `migrations/`.** The word appears in two SQL comments and nowhere
else. The axis the whole retention predicate turns on is carried by the record
types in `records/` and by nothing durable.

### Addendum, 2026-08-02 — two more declarations with nothing behind them

Both are crossing one, and both are recorded because the pattern is the useful
part, not the two small fixes.

`store/roles.py`'s `RoleState` was documented *"What the cluster looks like
after `ensure_roles`. **Reported, not assumed.**"* Its `created` field earned
that — `after - before`, both halves read from `pg_roles`. Its `app_privileges`
field was the module constant `APP_HOLDS`, and it was not merely assumed:
`store/migrate.py` orders `ensure_roles` → `apply_all` → `apply_grants`, so at
the moment the value was constructed there was no table to hold a privilege on
and no grant had been issued. The field said `("SELECT", "INSERT")` about a role
that held nothing, one line under a sentence promising it did not do that.
`held_by_app()` — further down the same module, asking `information_schema` —
was already the
honest answer and already what the tests used.

`records/aggregate.py`'s `CellResult.contributors` was documented as *"what the
announcement is written from."* The announcement is written by `_announce`,
which walks `readings` directly, and could not have been written from a per-cell
set of lane ids that carries no subject.

**Both were removed rather than corrected, and the reason is the same one this
file has recorded five times:** a field with nothing behind it is not inert, it
is an invitation. `docs/CROSSINGS.md` crossing one — remove the ability, not the
permission.

**The audit that found the second one got it wrong in a way worth keeping.** It
reported `contributors` as never populated. It was populated, at both
construction sites, **positionally** — which is why `grep -rn contributors`
returns two hits and why an AST sweep counting attribute reads and keyword
arguments classified it as dead. So the field was not a dormant default: every
release carried lane ids on the value `_render` hands to `_readme`, `_table` and
`_manifest`, in the module whose entire purpose is that identifiers do not reach
a booster board. Nothing read it, which is the only reason it leaked nothing.

The generalisation is the one this file exists for: **a sweep that looks for a
name cannot see a value passed without one.** The mechanised never-read check
that found most of this session's findings had a blind spot of exactly the shape it
was built to detect, and it took a second reader to see it. The replacement
guard asserts over *field values* rather than field names, so a field re-added
under any other name is caught — the retired `contributors` being the case that
proves the name was never the invariant.

---

## Provenance of this file

Written in the session it describes, by the author of every defect in it. That
is the worst possible vantage point for an audit and the best one for a
confession, and this is the second kind of document.

Every count above was derived from the tree at the time of writing. If a later
reader finds one wrong, that is crossing five arriving on schedule, and the
correction belongs here rather than in a commit message.
