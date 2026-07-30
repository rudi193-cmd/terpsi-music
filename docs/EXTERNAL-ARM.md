# Findings from an independent implementation

**Status:** external review. Not canonical, not a decision record. `docs/ARCHITECTURE.md` governs.

A Postgres store for a different domain — versioned documentation for coding
tools — was built without knowledge of this repository, then measured against
it. Same shape of problem: an observation of a claim at a pinned version, where
the load-bearing question is *"is this still true?"* and the failure being
designed against is that question answered with silence.

This file records what that arm found here. It is filed under the same rule the
survey files itself under: **treat every row as a lead with a citation, not a
finding.**

## Provenance

| Claim class | Worth |
| --- | --- |
| Defects verified in *this* tree | `measured` — reproduced here, in this repository |
| Counts and results from the other implementation | `measured` **in a different tree**, and per rule 17 not derived from this one |
| Characterisations of the 24 scouts | `assumed` — read by agents and summarised twice before reaching this file |

Nothing below asks you to trust the other implementation's numbers. Where they
matter, the mechanism is described so it can be rebuilt rather than cited.

---

## 1. One defect, verified and fixed in this pull request

`scout-13-verify-verifier.md` §7 named two scripts "in this directory" and
neither was in the tree. The only non-markdown files in the repository were
`.gitignore` and `tests/test_section_refs.py`.

That mattered more than a missing file usually does, for three reasons:

- The report's own epistemic hierarchy puts the four-mutant table at the top as
  the one result **derived by running code** rather than by citation. It was the
  single claim that could not be re-run.
- The report is the one about verifying verifiers.
- `test_section_refs.py` already checks the survey index against the tree **in
  both directions**, with a companion test proving that check can fail. The
  discipline was present and its scope stopped at `scout-*.md`.

Addressed here by restoring `trigger_mutation_demo.py` — stdlib-only,
self-testing, and its output now reproduces the table. One cell is corrected: a
*named* `CHECK` is caught by the manifest too, where the table said `(n/a)`,
because it survives in `sqlite_master.sql`. `sqlglot_probe.py` is marked
`NOT RETAINED` with its finding held as unreproduced rather than quietly
dropped.

`tests/test_claimed_artifacts.py` is the middle for the class. Deliberately
narrow: it fires only on a section titled "Artifacts in this directory", because
the survey cites hundreds of filenames belonging to other repositories and those
are correctly absent. It is checked in both directions and carries a test
asserting it can fail.

## 2. Corrections this arm suggests for the canonical documents

**§16's three failure modes are missing a fourth.** *Absent · mis-aimed · cannot
fire* are all properties of the **middle**. The rename case is a property of the
**stimulus**: the middle fired correctly and the mutant was a no-op. A harness
scoring that as a kill inflates its denominator, which is how #211's mutation
record came to be wrong. Proposed fourth mode: **the mutation that was a no-op**,
with the fix being *ablation as the primary operator* plus the rule that **a
mutation which kills no gate is a failed mutation, not a passing one** — the only
thing that catches an ineffective mutant in general.

**§10's diagnosis of #211 is one degree too gentle.** It reads *"three mutations
that renamed a SQL trigger rather than disabling it, so it kept firing under the
new name."* That frames a rename as a mutation that failed to disable. It is
weaker than that: a rename is **not a mutation of the guard at all**. Row A of
the restored demo shows it — renamed, still firing, forbidden act still refused.

**§18 item 0 belongs in "the four that block."** It is filed as a standing
caveat. But §9's foundation list is ordered by what §14 says exists, and §14 is
75 rows assembled from READMEs and merged pull-request descriptions. If three of
those rows are wrong the phasing is wrong, and nothing currently distinguishes a
verified row from an unverified one — which is item 0's own sentence. Cheaper
than `L1–L5` and upstream of it.

**Two claims carry unread sources and should say so where they sit.** §8 and the
§10 compliance map both assert PCI **SAQ-A**; scout-18 records that nobody in
these sessions could read the standard. And `FundraisingCredit` is already in
§8's money model while the IRS constraint on individual fundraising accounts is
unresearched — the one place a schema decision is pending on law rather than on
design. Neither needs resolving today; both need the `P2` label visible at the
point of use rather than only in a scout.

## 3. What the other arm has that these documents do not

Stated narrowly, and each is a mechanism that was built and broken rather than a
proposal.

**A negative control for the instrument.** A verdict is licensed only if the
instrument first demonstrates it can say *no*. In that domain: probe a flag that
cannot exist before probing the real one; if the impossible flag is accepted, the
artifact accepts anything and **no answer is permitted** — recorded as
`indeterminate / permissive_parser`, never as present or absent. Mutation
testing showed the control was load-bearing twice: it also supplies the
rejection signature every *absence* verdict is compared against, so removing it
broke all absence cases rather than one.

The transplant is rule 13 with an instrument attached. "Absence surfaces as
`unknown`" is a statement about the answer; a negative control is what
distinguishes *we looked and it was not there* from *this instrument would have
said yes to anything*.

**Claim strength computed from coverage, not asserted.** A pairwise comparison
of two versions licenses "gone **by** V", not "gone **in** V". The store counts
the versions between the last confirmed presence and the first confirmed absence,
counts how many were actually checked, and emits the weaker claim when they
differ — strengthening on its own when the gap is filled. A writer cannot
overclaim because the strength is derived. Any released-version ordering that
cannot be determined downgrades every such claim for that subject, because an
unplaced version could sit in any gap.

**Doc absence is actively wrong, measured.** In that domain, `yapf --verify` was
live through 0.40.1, absent from *every* version's help output, and genuinely
gone at 0.40.2 — a help-scraping store would have called it removed nine
releases early. The generalisation for §15: absence from a document is evidence
about the document.

**A recorded recall limit rather than a footnote.** The same store refuses to
report a removal it is fairly sure of, because the artifact's rejection message
did not match the control's. Measured across three invocation shapes, only 6, 16
or 20 of 31 candidate flags reach any verdict at all. The middle figure is the
trap: it looks acceptable by accident.

## 4. Where this repository was ahead, and the other arm was wrong

Recorded because a review that only finds fault in one direction is not one.

- The other arm shipped **a fifth provenance vocabulary** into a fleet §14
  already records as having four and no mapping — a bare single-character tier
  compared with a `greatest()` call. §15's direction hazard, walked into by
  someone who had read neither §15 nor the tally.
- It has **no `Cited` rung**, so an in-source deprecation attribute and a
  changelog entry are filed as *fitted* because there was nowhere better. §15
  names that gap precisely.
- It has **no seal**: provenance only, with no separation of *where a value came
  from*, *how sure the claim is*, and *whether a person stood behind it*.
- It has **no schema-object manifest** — behaviour gates only — which is the
  blind spot row A of the restored demo exists to show.
- Its citation-decay model has three states against `almanac-template`'s seven.

The two arms did converge, from unrelated directions, on the distinction §7.1
currently cannot express: *ended* versus *entered in error*. This arm reached it
through Wikidata's deprecation rank; scouts 05 and 24 reached it independently.
Three arrivals is a strong signal for `invalidation_kind` landing before the
first migration.

## 5. One methodological observation

Across five independent workstreams in the other implementation, **harnesses that
under-report their own failure occurred fourteen times.** Always the same shape —
the run establishes nothing and prints something indistinguishable from success —
and not once found by reading. A sentinel computed from the results it polices. A
gate green because a different constraint was catching it. A dropped scratch
database turning every refusal gate green, because an error is not evidence of a
working constraint.

This is corroboration rather than discovery: §10 already records #211's six
apparatus defects against zero code defects, and `PROTECTED_AGENTS.md` I-12
already defines compliance as an adversarial test per clause. What the second
site adds is that **the base rate is high enough that a green suite offered as
evidence should be assumed unable to fail until shown otherwise** — which is
rule 19, and is the argument for the control specimen scout-13 recommends: one
deliberately-broken guard whose passing **voids the run**, so a green result
means two things rather than one.
