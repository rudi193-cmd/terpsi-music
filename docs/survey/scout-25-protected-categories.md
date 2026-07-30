# Scout 25 — Protected-category vocabulary, and the classification rung §18 item 11 opened

**Date:** 2026-07-30 · **Slice:** whether an existing standard already names the categories §6's eight data classes omit — confidential addresses, housing status, foster placement, undocumented families, chosen name — and at what rung anyone else puts them.

**This report post-dates `OPEN-SOURCE-SURVEY.md`.** The survey summarises scouts 01–24 and was written before this one existed; it is not a summary of this file, and this file is not covered by its findings.

---

## Method note, and why this report is weaker than the twenty-four before it

**Every source below was read as a search-engine summary of a page this session could not open.** That is a weaker rung than any tag scout-23 defines, and it is the first thing to know about every row here.

`WebFetch` returned HTTP 403 for every host attempted, including `nces.ed.gov`, `ceds.ed.gov` and `en.wikipedia.org`. This is the environment's network policy, not a bad URL or a transient failure — the proxy's own log names it:

```
connect_rejected — gateway answered 403 to CONNECT   host: nces.ed.gov:443
```

`curl` through the same proxy failed identically (`CONNECT tunnel failed, response 403`). `add_repo` refuses cross-owner adds — *"session already has repos from owner(s) [rudi193-cmd]"* — so the GitHub-hosted standards bodies (Ed-Fi, CEDS) were unreachable by the route scout-23 used when its WebSearch budget ran out. **Both of the previous scouts' fallbacks were closed simultaneously.** Search summaries were the only channel open.

Tags, extending scout-23's legend downward:

- **`[search-summary]`** — a search engine's synopsis of a page that was not opened. Weaker than `[inference]`, because an inference at least declares itself as reasoning; a summary reads like a quotation and is not one. **Every external row in this report carries this tag.**
- **`[tree]`** — derived by reading or running this repository. The only claims here that are not `[search-summary]`.

Under §15's vocabulary every external claim below is **`P2 Cited` at best**, and arguably below it, since the cited source was never opened. `docs/CRAFT-SOURCES.md` marks §24's citations the same way for the same reason. **Nothing here should land as a finding, and no schema decision should rest on it.**

Project rules this slice is answerable to, by CLAUDE.md number: **#13** (absence surfaces as `unknown`, never as a result), **#14** (scales never compare as bare integers), **#17** (do not quote a count you did not derive from the tree), **#20** (leave a tombstone when retiring anything).

---

## Ranked table

| # | Source | What it is | Reached? | Maps to | Verdict |
|---|---|---|---|---|---|
| 1 | **CEDS** (Common Education Data Standards) `[search-summary]` | US national voluntary vocabulary for education data elements | **NO** — `ceds.ed.gov` 403 | §18 item 11; scout-23's own open thread | **unreached — still the highest-value unread source** |
| 2 | **Washington OCIO 141.10 / SLDS privacy classifications** `[search-summary]` | Four-category state classification, Category 4 = *Confidential Information Requiring Special Handling* | summary only | the shape of item 11's fix | **steal-the-idea** (the axis, not the vocabulary) |
| 3 | **Ed-Fi `StudentCharacteristicDescriptor`** `[search-summary]` | Extensible descriptor mechanism for student characteristics | summary only; **descriptor values not obtained** | item 11 vocabulary | **read-only-interest** — scout-23 already rates Ed-Fi a vocabulary donor |
| 4 | **pyAMPACT** `[search-summary]` | Score-audio alignment exporting note-linked performance data to MEI via a `<when>` element | summary only | §18 item 7 | **lead only** — the one candidate not already in the survey |

Four rows is not a survey. It is what one blocked channel yields, and the table is short because the sources were closed, not because the field is small.

---

## 1 · Item 11 may be an axis problem, not a vocabulary problem

This is the one observation in this report worth the reading time, and the part of it that matters is `[tree]`.

§18 item 11 says §6's eight classes do not cover what §20 of the capability map names, and frames the resolution as *"needs a decision on new classes."* Washington's model suggests the framing is off by a dimension.

**Washington classifies by consequence of disclosure, not by data type.** Category 4 — *Confidential Information Requiring Special Handling* — is reportedly defined not by what the data is but by what follows if it leaks: information for which *"serious consequences could arise from unauthorized disclosure, such as threats to health and safety, or legal sanctions."* `[search-summary]`

That is the property item 11's five categories share. As *types* they are unremarkable — an address is an address, a name is a name — which is exactly why they fall to `PII_MINOR` and land at `L3`. What unites them is that disclosure is dangerous, and type-keyed classification cannot see that.

**This repository already has a consequence-keyed mechanism.** `docs/SENSITIVITY.md` puts records at `L5` per record under three rules, precisely because no class reaches that rung (§18 item 1b). Checked against item 11's five `[tree]`:

| §20 category | reached by an existing `L5` rule? |
|---|---|
| Safe at Home confidential address | **arguably rule 2** — the content of an external restriction the system enforces |
| McKinney-Vento housing status | no |
| foster placement | no |
| undocumented family status | no |
| chosen name distinct from the SIS record | no |

So the decision item 11 needs may be **a fourth `L5` rule** rather than four new classes — a far smaller change, in a mechanism that exists, at a rung whose semantics are already written. Item 1b already anticipates the shape: *"worth revisiting if a fourth trigger appears."* This is a candidate fourth trigger.

**Stated as a question for a human, not as a proposal.** Two things argue against it and are not resolved here:

- `L5` is *enforcement-only* — never served to anyone under any grant. A housing-status flag that no surface may render is useless to the liaison whose job is to act on it. Either the rung is wrong for these categories, or `L5` needs a served-to-a-named-role carve-out, which is a larger change than the one it was meant to avoid.
- Rule 2 covering Safe at Home is *arguable*, not settled. A confidential address is the subject of an order; whether the address is "the content of the restriction" or merely governed by it is the kind of distinction §7.4 warns does not survive translation between registers.

**Nothing in those categories should be classified until this closes** — which is item 11's own instruction, unchanged by this report.

## 2 · The harm model, corroborated from an unrelated direction

Searches on chosen-name handling returned the same shape independently of the classification question `[search-summary]`: the recurring pattern is that the legal name is held in a separately-gated compartment, and the named failure is a record *inadvertently outing a student* to anyone who can see it.

This corroborates §20 rather than adding to it, and it is worth one line because it arrived from a different literature than the one scout-12 and scout-23 read. Two arrivals is not three, and scout-13's standard applies: corroboration, not discovery.

## 3 · Item 7 was already covered — one addition, and it is a lead

Search on score-position anchoring largely re-found the survey's own work `[tree]`: **Matchmaker** appears in both scout-07 and scout-15, **AMPACT** in scout-15, and scout-07 carries a rated table whose verdicts are mostly `adopt`. The survey was thorough here and this report adds nothing to it.

The one candidate not in the tree is **pyAMPACT** `[search-summary]`, reportedly exporting note-linked performance data to MEI through a `<when>` element that binds a time-point in an external audio representation to a symbolic event in the score. If that is accurate it is the two-sided anchor §18 item 7 describes — *"anchors to a position in both the text and the score"* — in an existing format rather than a designed one.

**Filed as a lead for scout-07 to absorb, not as a finding.** It was not opened.

## 4 · The negative result, recorded rather than dropped

**CEDS was not reached, and that is the most useful sentence in this report.**

scout-23 §7 flagged it: *"not reached at all — likely the best US vocabulary for guardian-relationship and restricted-contact enumerations; worth a look."* This session was the look, and it failed on network policy rather than on judgment. The thread is exactly as open as scout-23 left it.

Recorded here per rule #20's discipline rather than allowed to look like an absence of interest. Under rule #13 the correct reading of this section is **`unknown`, not "no vocabulary exists."** A search that could not open its sources returns unavailable, not no-findings — and a reader arriving at a four-row table in a repository whose other scouts run to hundreds of rows should be told which of those two they are looking at.

**What would close it:** a session whose network policy permits `ceds.ed.gov` and `nces.ed.gov`, or a human with a browser and ten minutes. The specific asks are CEDS's option sets for homelessness, foster care, migrant status and address confidentiality, and whether any carries a sensitivity or handling attribute alongside the enumeration — because a vocabulary that names the category without ranking its disclosure risk resolves half of item 11 and leaves §1 above untouched.

---

## 5 · One thing this scout noticed about the tree on its way past

Not this slice's subject, and recorded because the next person will otherwise find it the expensive way `[tree]`.

**Scout reports cite `§N` and nothing verifies those citations.** `tests/test_section_refs.py` sweeps `docs/*.md` — non-recursive — so all twenty-five files under `docs/survey/` are outside it. Derived by running `other_docs()`: it returns 8 documents, none of them a scout.

That is the same pointer-nobody-verifies the file exists to prevent, one directory down, and this report has just added a twenty-fifth citing file to it. The reason it is not fixed in the same commit is that the fix is not obvious: scout reports cite §N of *both* canonical documents and of *each other*, and a sweep with a single default would need the routing table extended before it could pass. That is a design decision about what `§N` means inside a scout, which belongs to whoever owns §16 — but the gap should be named rather than left for the next reader to trip over.

## 6 · What this report does not establish

Stated plainly, because a short report that reads as thorough is the failure mode scout-13 names.

- **No source below row 4 was opened.** No enumeration was read at source, no license verified, no repository activity confirmed.
- **No count here comes from an external source.** The only counts are `[tree]` ones, derived by running code.
- **Nothing here is a finding.** The strongest claim is §1's, and it is a reframing of an open item plus a table computed from this repository — the external half is one summarised sentence about one state's policy.
- **The four rows are not a ranking of a field.** They are the four sources one blocked channel surfaced.
