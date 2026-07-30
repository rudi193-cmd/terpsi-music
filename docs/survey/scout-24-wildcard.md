# Scout 24 — The Wildcard

Brief: find open-source projects whose **mechanism** transplants into terpsi-music even
though their **domain** is absurd. Everything below was checked against its real
repository or its canonical documentation this session. Licenses and liveness are stated;
where I could not confirm something I say so rather than guessing.

Two conventions used throughout:

- **Lands** = where in `docs/ARCHITECTURE.md` / `CLAUDE.md` the mechanism attaches.
- Liveness: **alive** (recent pushes) · **dormant** (no pushes in ~1yr+) ·
  **finished** (deliberately complete — a compliment here).

Verification note, per `CLAUDE.md` #17: every star count, license and push date below
came from the GitHub API or the project's own files in this session. Two claims a
summarizer gave me turned out to be wrong on inspection (see `divinum-officium` license,
and Fossil's shun-list propagation) and both are corrected in place.

---

## Transplants

Ranked by how much they change what gets built, not by how interesting they are.

---

### 1. OpenSAFELY + Airlock — the export gate, already shipped, in a harder domain

- **What.** NHS platform for analysing ~58M patients' primary care records in which the
  researcher **never sees the data**. Analysis code is written against dummy data, submitted,
  run remotely, and only *aggregate* outputs come back — and those outputs must pass a
  human review gate called **Airlock** before they can leave the secure backend.
- **Repos.** `github.com/opensafely-core/airlock` (Python, 2.5k commits, pushed
  2026‑07‑29, alive; LICENSE present but GitHub reports no SPDX match — check before
  reuse), plus the wider `opensafely-core` org. Docs: `docs.opensafely.org`.
- **Mechanism that transfers.** Four things, and all four are already terpsi's design:
  1. **Read is cheap inside; export is a distinct, reviewed act.** Researchers can look at
     their outputs inside the perimeter freely. Getting them *out* is a separate request
     with a separate permission class. This is §7.2 / rule 9 verbatim, in production.
  2. **Two independent reviewers, and self-review is structurally impossible.** Airlock
     "is designed to enforce the number of required reviews, independent review, and
     ensure that researchers who are also output checkers are not able to review their
     own requests." That last clause is the interesting one: the *tool* enforces the
     separation rather than a policy asking people to be good.
  3. **Return is a first-class outcome, not an error.** A request comes back to the
     requester with a reason; they must strip a file, supply more justification, or re-run
     the job with different disclosure controls. Rejections are workflow states, and 2025
     changelog entries show them being *tuned* — i.e. read, which is exactly the thing
     §16 notes Nestor's `IDEAS.md` admits nobody does.
  4. **All platform activity is publicly logged and all research code is public by
     requirement.** Transparency is the enforcement, not a report.
- **Lands.** §7.2 (the knock, gate-the-export), rule 9, rule 10, §16's *"an audit trail
  that records only agreement is not one."* If you build one thing from this list,
  build Airlock's state machine: `request → independent review ×2 → release | return(reason)`.
- **Caveat worth stealing too:** their own docs record that the two-review rule was
  *relaxed* in March 2025 so a checker can return a request early without a second
  review. A gate that is too expensive gets loosened; design the cheap path first.

---

### 2. `statcheck` + `scrutiny` — a middle for prose claims about numbers

- **What.** `statcheck` (R, GPL‑3, `MicheleNuijten/statcheck`, pushed 2026‑07‑03, alive)
  reads a paper's *text*, extracts every reported statistical test, **recomputes the
  p-value from the reported test statistic and degrees of freedom**, and flags the
  disagreements. It is described by its author as "a spellchecker for statistics."
  `scrutiny` (R, `lhdjung/scrutiny`, CRAN, pushed 2026‑05‑05, alive) implements
  **GRIM/GRIMMER**: given a reported mean, SD, sample size and item count, it proves
  whether that mean is *arithmetically possible at all* — without any access to the data.
- **Mechanism that transfers.** A checker that reads prose, finds numeric claims, and
  recomputes them from their stated basis. GRIM adds the stronger move: proving a claim
  **impossible** from granularity alone (a mean of 3.47 over 12 students on an integer
  scale cannot exist).
- **Lands.** `CLAUDE.md` #17 — *"Do not quote a count you did not derive from the tree.
  Test counts, row counts, gate counts. This fleet has a documented history of figures in
  prose the code moved past; four instances in one session."* That rule is currently a
  **declaration with no enforcement** — precisely the pair §16 says must not be created
  without a middle. `tests/test_section_refs.py` checks that `§N` pointers resolve; there
  is no equivalent checking that "four guards" is four. statcheck is the shape of the
  missing test: scan `ARCHITECTURE.md` and `CLAUDE.md` for claim-shaped numerals near
  countable nouns (`\d+ (guards|tests|gates|sections|rows)`), derive the count from the
  tree, and fail on disagreement. GRIM is the shape of the second one: any statistic
  quoted about a cohort must be *possible* for that cohort's size.
- **Why it's the second-highest value item.** It is small, it is stdlib-able, and it
  closes the one gap the project has already diagnosed in itself.

---

### 3. The IANA time zone database — retirement without deletion, at 40 years

- **What.** `tzdb` (`github.com/eggert/tz`; public domain; alive, maintained continuously
  since 1986, through a change of maintainer and a lawsuit). Weird by any measure:
  a database of political decisions about clocks, distributed as text, depended on by
  every computer.
- **Three separate mechanisms transfer.**
  1. **A retired identifier becomes a `Link`, never a deletion.** From `theory.html`:
     *"If a name is changed, put its old spelling in the 'backward' file as a link to the
     new spelling. This means old spellings will continue to work."* `Asia/Calcutta` still
     resolves, seventeen years after it became `Asia/Kolkata`. This is §16's tombstone
     applied to **identifiers rather than documents** — and it is the piece §16 does not
     yet cover. terpsi will rename things (a student's chosen name, an ensemble, a fee
     code, a rubric caption); a rename that breaks old references is the same defect as a
     deleted repo.
  2. **The naming rule is a refusal.** Zones are named after cities, *never* countries:
     *"names are typically not tied to countries, to avoid incompatibilities when
     countries change their name."* And: *"There is no requirement that every country or
     national capital must have a timezone name."* Read this next to refusal #5 (no group
     grants — `"the drumline"` is not a scope, a name is). tzdb reached the same
     conclusion from pure engineering pressure: **name the smallest stable thing, because
     the aggregate will split.**
  3. **The `Makefile` checks the declarations against the data.** Verified from source:
     `check` depends on `links.ck` (via `checklinks.awk` — every `Link` target must
     exist), `tables.ck` (via `checktab.awk` — `zone.tab`/`zone1970.tab` reconciled
     against the actual zone data), `name-lengths.ck`, `sorted.ck`, `character-set.ck`,
     `mainguard.ck`, and — my favourite — `news.ck`, which asserts that the **release
     notes'** version lines are sorted and unique. This is UTETY's
     `test_allowlist_entries_exist` (§16: *"the only declaration in the fleet that is
     checked for rot"*) and it turns out tzdb has had a dozen of them for years.
- **Lands.** §16 (tombstones, rule 5 "check the middle for rot"), rule 20, refusal #5's
  naming discipline, and §11.1 (see next point).
- **Bonus, for §11.1 and rule 13.** `theory.html` is the best honest-limits document I
  found anywhere: *"many, perhaps most, of the tz database's pre-1970 and future
  timestamps are either wrong or misleading"* and *"Any attempt to pass the tz database
  off as the definition of time should be unacceptable to anybody who cares about the
  facts."* A project that has been correct-by-reputation for four decades saying that
  about itself is the tone §11.1 asks for when it says *"if the exit line cannot be
  written honestly that is the finding."*

---

### 4. Wikidata / Wikibase statement ranks — the retirement `invalid_at` cannot express

- **What.** Wikibase (GPL, the software behind Wikidata) gives every statement a **rank**:
  `preferred` · `normal` · `deprecated`. Deletion is discouraged in favour of ranking, and
  `deprecated` **requires** a qualifier `P2241 "reason for deprecated rank"` drawn from a
  maintained list of reasons.
- **The distinction, which is the whole find.** Wikidata's `Help:Deprecation` is explicit:
  `deprecated` is for statements *"known to include errors or that represent outdated
  knowledge (information that was never correct, but was at some point thought to be)"* —
  and it says, in terms, that deprecated rank must **never** be used for a fact that was
  once true and has since ended. For that case you keep `normal` rank and add
  `start time` / `end time` qualifiers. Two retirements, two mechanisms, and conflating
  them falsifies the record.
- **Lands. §7.1, and it is a gap.** Refusal #3 and §7.1 give the design exactly one
  retirement: `invalid_at`. That correctly models *"this guardianship ended by court
  order on this date."* It cannot model *"this guardian was entered in error; they were
  never this student's guardian."* Setting `invalid_at` on a mistaken edge asserts a
  relationship existed and then ended — which, in a custody dispute, is a false record
  that the system will faithfully preserve forever, and rule 16 guarantees nobody can
  remove it. You need a second, distinguishable retirement — call it `erroneous`,
  carrying a mandatory reason and *not* implying a period of validity — and the reason
  vocabulary should be closed, as Wikidata's is.
- **Second mechanism, free.** Wikidata additionally keeps the *superseded but once-true*
  value queryable at `normal` rank alongside the `preferred` current one, so "who was the
  emergency contact in March?" and "who is it now?" are the same query with a different
  rank filter. That is bitemporality expressed as data rather than as a schema.

---

### 5. Fossil's `shun` — the only deletion, and it deliberately does not spread

- **What.** Fossil SCM (BSD‑2, `fossil-scm.org`, alive and feature-stable; the same author
  as SQLite). Fossil's content store is append-only by design. The one way to remove an
  artifact is to add its hash to a **shun list**; the repository then refuses to push or
  pull it, and a `rebuild` physically drops the content — *but keeps the shun record.*
- **The correction that makes it interesting.** I expected the shun list to sync, and it
  does not, on purpose. Fossil's own `shunning.wiki`: *"The fact that the shunning list
  does not propagate is a security feature… If the shunning list propagated then a
  malicious user (or a bug in the fossil code) might introduce a shun record that would
  propagate through all repositories in a network and permanently destroy vital
  information."*
- **Mechanism that transfers.** Two halves, both load-bearing:
  1. **Erasure is expressed as an additive record, not a subtraction.** The content goes;
     the *fact that content was removed here* stays. That is a working answer to §5's
     *"erasure inside a hash chain — solved, and harder than stated above"*, and it is the
     shape a FERPA amendment or a court-ordered redaction wants: the hash-chain stays
     verifiable, the lane still says something was removed and when.
  2. **A destructive instruction must not be replicable.** If terpsi's drop/hub/edge
     topology (§3) ever syncs erasure orders, one bad order — or one bug — erases a
     student's record everywhere with no recovery. Fossil's answer: erasure is a *local
     administrative act*, performed once per replica by a human who can see what they are
     destroying. Slow, unglamorous, and correct.
- **Lands.** §5 (erasure in a hash chain), refusal #3, §3 (what the sync protocol is
  allowed to carry). Also worth reading beside it: Fossil ships
  `www/rebaseharm.md` — *"Rebase Considered Harmful"* — a doctrinal refusal of a
  feature every competitor has, argued in prose in the manual. That is the genre
  `CLAUDE.md` is written in.

---

### 6. `git-annex` — refuses to drop the last copy, and `dead` is a status

- **What.** git-annex (GPL‑3, Joey Hess, alive) manages large files under git without
  putting content in git.
- **Mechanisms that transfer.**
  1. **A destructive operation must *prove*, at the moment of the operation, that the
     thing survives elsewhere.** `git-annex drop` refuses unless it can verify that
     `numcopies`/`mincopies` other repositories still hold the content — verified by
     asking them, not by consulting a cached belief. `--force` exists and is loud.
  2. **A repository trust ladder — `trusted` / `semitrusted` (default) / `untrusted` /
     `dead` — where the levels change what checking is *skipped*.** `trusted` means
     "don't bother verifying," which is why `git-annex trust` now requires `--force`:
     the project learned that a trust assertion is a data-loss primitive.
  3. **`dead` is a status, not a removal.** A drive that fell in a lake becomes `dead`;
     its history of having held content remains.
- **Lands.** §11.1 (the exit line: you may only remove a recording from the hot store
  after proving the archive copy verifies *now*), rule 14 (`T0–T4` is a real ladder with
  real semantics — copy the discipline that a higher rung means *less checking*, which
  makes raising a rung a privileged act), refusal #3 (`dead` ≈ `invalid_at` for devices).

---

### 7. Divinum Officium — the same date, computed under six different rulebooks

- **What.** `DivinumOfficium/divinum-officium` (Perl + text data; 29,665 commits; pushed
  **2026‑07‑30**, i.e. today; 453 stars; alive). It renders the Roman Breviary and Missal
  for any date under *six co-existing rubric editions* — pre-Trent monastic, Trident 1570,
  Trident 1910, Divino Afflatu, Reduced 1955, Rubrics 1960 — plus Monastic and Dominican
  variants. Older rubrics are never retired when a newer edition supersedes them; the
  1570 calendar is still computed, correctly, from the 1570 rules.
  There is a `regress/` directory of golden-output regression tests (I could not enumerate
  it — this session's GitHub access is scoped to terpsi-music — but it is referenced from
  the repo root along with CI config).
  **License: there is no `LICENSE` or `LICENSE.md` file and the GitHub API reports no
  detected license.** An earlier summarizer told me "MIT"; that was wrong. Treat as
  unlicensed source; the underlying liturgical texts are public domain.
- **Mechanism that transfers.** **Rubric version as a first-class query parameter, with
  every historical version retained and independently testable.** Not "we migrated the
  rules in 2019" — six rulebooks resident simultaneously, selected per request.
- **Lands.** §8.1 / §13 / adjudication, and it is a design decision the docs have not
  taken yet. A judge's commentary from the 2023 season was written against the 2023
  caption rubric; a fee waiver was granted under the 2024 handbook; eligibility was
  assessed under last year's academic policy. Re-rendering any of those under today's
  rules is a falsification, and re-rendering them under *no* rules is `unknown` (rule 13).
  Every seal (§16 `sealed`) should therefore carry the identifier of the rubric edition in
  force, and the rubric editions should live in the tree, all of them, forever, each with
  its own golden tests. This also gives §15's provenance ladder something concrete to
  cite: *"scored under `rubric:2023.2`"* is a checkable claim.

---

### 8. KosherJava `zmanim` — `null` rather than a plausible answer, and named opinions instead of one

- **What.** `KosherJava/zmanim` (LGPL‑2.1, alive). Computes Jewish prayer times from
  astronomy and halachic opinion.
- **Two mechanisms, both already doctrine here but not yet implemented anywhere.**
  1. **Absence is returned as absence, argued explicitly.** The API returns `null` for a
     zman that does not occur — north of the Arctic Circle the sun does not rise; the
     16° twilight dip does not happen in **London** between 4 June and 8 July. The
     author's published rationale is the exact argument of `CLAUDE.md` #13: *"While an
     inconvenience to developers who have to code for this, the alternative of a default
     date would mean that developers unaware of this would return incorrect zmanim,
     something far worse than a program error from a NullPointerException."* Note that the
     limit is *documented as a surprise* — the London case exists to stop implementers
     assuming the edge case is polar and therefore theirs to ignore.
  2. **When authorities disagree, return all of them, named.** The library does not pick a
     posek. It exposes `getSunriseGRA()` vs the Magen Avraham variants and dozens more as
     separate, individually-named methods, and the README carries the maintainer's
     refusal to be the authority: *"While I did my best to get accurate results, please
     double check before relying on these zmanim for halacha lemaaseh."*
- **Lands.** Rule 13 (`unknown` is a value, not a convention — and it needs a *reason*, as
  Nestor's `pending` does), and refusal #6 / W‑7. #6 says *"the system presents, a human
  decides."* zmanim shows the API shape that makes that survivable: not one blended
  number with a confidence, but **n named positions a human can choose between**, each
  attributable to whoever holds it. Apply directly to conflicting rubric interpretations,
  two judges' captions, and any place where the fleet is tempted to average.

---

### 9. DataSHIELD `nfilter` — the redaction funnel's missing rule

- **What.** DataSHIELD (`datashield/dsBase`, GPL, alive; R). Federated analysis across
  cohorts where the server returns only non-disclosive summaries.
- **Mechanism that transfers.** Server-side **disclosure traps** with configurable
  thresholds: `nfilter.tab` (minimum non-zero cell count in any returned contingency
  table, default 3), `nfilter.glm` (max model parameters as a fraction of n, default 0.33,
  to stop a saturated model being fitted and read back as individual data). Critically:
  *"If any of the input variables do not pass the disclosure controls then **all** the
  output values are replaced with NAs"* — the whole result is withheld, not the offending
  cell, because a partially-suppressed table is a puzzle with one answer.
- **Lands.** §6's redaction funnel, which the docs say *"exists; it does not know about
  students."* This is what it needs to know. Any aggregate over a cohort — waiver uptake,
  free-lunch eligibility, medical flags, absence counts by section — is disclosive at
  small n, and music program sections *are* small n. "Everyone in the drumline returned
  the medical form except one" is a health disclosure about a named student assembled
  from two non-disclosive facts. Related and worth pairing: `sdcMicro`/`sdcTable` (R, GPL)
  implement **secondary suppression** — the arithmetic that decides which *additional*
  cells must be hidden so the totals do not reconstruct the one you hid.
- **Note.** This also constrains §17's district view and §19's "insight" surface more than
  the capability map currently admits.

---

### 10. `panelot` / `stratification-app` — the auditable lottery, for when ranking is forbidden

- **What.** `sortitionfoundation/stratification-app` (GPL‑3, Python, pushed 2026‑07‑28,
  alive) selects citizens' assembly members by **stratified lottery**, implementing the
  leximin algorithm from Flanigan et al., *"Fair algorithms for selecting citizens'
  assemblies,"* Nature 2021 — the algorithm maximises the *minimum* probability of
  selection any willing participant receives, subject to declared demographic quotas. The
  companion tool `panelot.org` / *"Fair Sortition Made Transparent"* (NeurIPS 2021) adds
  the transparency half: it makes the lottery itself inspectable rather than a black box.
- **Mechanism that transfers.** When you must allocate a scarce good among people and you
  are **forbidden to rank them**, the defensible construct is: declared quotas + a lottery
  + a **published per-person selection probability**. Nobody was scored; everybody can be
  told what their chance was and why.
- **Lands.** Refusal #6 and §7.4 W‑7 — *"Never compute a priority between two students.
  Chair placement, rooming, limited slots — the system presents, a human decides. Halt and
  escalate."* That rule is correct and it is also incomplete: there are 40 kids and 12 hotel
  beds and a bus with 51 seats, and "halt and escalate" hands a director a decision with no
  defensible instrument. This is the instrument. It does not compute a priority; it
  computes a *probability*, declares it in advance, and produces an outcome nobody has to
  justify as a judgement about a child. Escalating to a human *with a lottery they can
  run* is a materially different escalation from escalating to a human with a blank page.

---

### 11. `kep-hierarchical` — if you must allocate on merit, the criteria hierarchy is published policy

- **What.** `jamestrimble/kep-hierarchical` and `jamestrimble/kidney_solver` (Python;
  academic, dormant). The former re-implements the **hierarchical optimisation model of
  the UK National Living Donor Kidney Sharing Scheme** — the five official objective
  criteria, applied lexicographically, from Manlove & O'Malley, *J. Exp. Algorithmics*
  2015.
- **Mechanism that transfers.** For an allocation nobody can avoid and everybody will
  contest: **the objective criteria are an ordered, published, externally-authored list;
  the code implements them literally and lexicographically; the run is reproducible from
  its inputs; and the tie-breaks are part of the published policy rather than an
  implementation detail.** The software has no opinion. It is a calculator for someone
  else's ranked criteria, and its correctness claim is "this is what the scheme says,"
  not "this is optimal."
- **Lands.** Refusal #6's escape hatch, beside #10. If a program insists on merit-ordered
  chair placement, this is the only shape that is honest about it: the criteria come from
  the handbook (with a rubric version, per #7), the order is declared before the season,
  the run is reproducible, and the system still produces a *proposal* a human seals
  (rule 10). The tie-break is where cruelty hides; publish it.

---

### 12. IANA root KSK ceremony — `coen` + `dnssec-keytools`, and the Internal Witness

- **What.** Two real repos: `iana-org/dnssec-keytools` (Python; pushed 2025‑12; the tooling
  that manages the DNSSEC root Key Signing Key) and `iana-org/coen` — **Ceremony Operating
  ENvironment** — a *reproducible* ISO image, so that the environment in which the
  irreversible act is performed *"generates the same hash any time the COEN ISO image is
  built."* Licenses: GitHub reports no SPDX match for either; both are public and
  ICANN-published. Alive, low-traffic, exactly as you'd want.
- **Mechanism that transfers.** The full ceremony shape, and one role in particular:
  - **A written script enumerating every step**, prepared and published in advance.
  - **A named Internal Witness whose only job is to confirm the Ceremony Administrator
    followed the script.** Not a second operator — a second *reader*. The actor and the
    checker of the actor are different people with different jobs.
  - **Third-party audit by two firms**, unaffiliated with either operator, plus video.
  - **The environment is reproducible**, so "we ran the script" is a verifiable claim
    about *which software* ran, not just which steps.
- **Lands.** §11.1 (*"escrow rehearsed"* — this is what rehearsed means), §6/§10 install
  acceptance, and the promotion-to-canonical human act in §5. Also the honest reading of
  rule 10: a seal by a named human is the *minimum*; for the acts that cannot be undone —
  key rotation, escrow, a lane handed over at exit, a bulk export under litigation hold —
  the Internal Witness role is the cheap upgrade. §16 will like that it is a *middle for
  the pair (script, execution)* rather than a second signature on the same act.

---

### 13. `in-toto` — declared intent reconciled against what actually happened

- **What.** `in-toto/in-toto` + `in-toto/specification` (Apache‑2, CNCF, alive). The
  project owner writes a **layout** naming the steps of a process and who is authorised to
  perform each; each actor emits **link metadata** recording the command it ran and the
  files it touched; an independent verifier then checks the chain against the layout —
  including that artifacts flowed from step to step untampered, and that no step happened
  that was not authorised.
- **Mechanism that transfers.** Declare intent up front, in a machine-readable artifact;
  collect evidence of what actually happened; have a **third component** compare them.
  Note the asymmetry in-toto gets right: the verifier is neither the declarer nor the
  actor.
- **Lands.** §7.2 — *"Sessions declare a purpose and are reconciled against it"* and the
  **exit diff**, which §16 lists as an existing middle. in-toto is the same mechanism with
  a spec, a threat model, five years of adversarial attention, and a rule language for
  authorising artifacts per step. Read it before writing the knock's reconciler; in
  particular steal the property that *an unauthorised step is a verification failure*, not
  an unlogged event.

---

### 14. `diffoscope` — a reconciler that says *what* differs, recursively

- **What.** `diffoscope` (GPL‑3+, Reproducible Builds project, alive). Recursively unpacks
  archives, ISOs, PDFs, binaries — transforming each into a human-readable form — to
  answer "why are these two builds not identical?" Reports as text or HTML, scriptable by
  exit code.
- **Mechanism that transfers.** A differential whose output is **a located, typed
  explanation at every nesting level**, not a boolean and not a text diff of the wrong
  representation.
- **Lands.** §16 rule 3 — *"The middle must state which property it compares."* The
  documented failure it fixes is §16's own: *"#120's differential reported 14,650
  disagreements that were **entirely SQL text** — zero row sets, zero counts. Real, and
  comparing spelling rather than behaviour."* diffoscope exists because that exact failure
  is endemic to naive differencing, and its answer is to make the *transformation* explicit
  before comparing. Any middle this project builds — canonical↔sidecar, declared
  purpose↔actual session, guardian edge↔send list — should name its transformation the way
  diffoscope's comparators do.

---

### 15. `leap-seconds.list` — a data file that declares its own expiry

- **What.** The IERS/NIST leap second table, shipped with tzdata and NTP. Format
  (verified against the file and the Meinberg reference): a line beginning `#@` carries
  the file's **expiration date** in NTP seconds; a `#h` line carries a hash. *"Applications
  should use the expiration date to determine if the leap second file is still valid, or
  not."* The expiry is bumped **at least twice a year whether or not a leap second is
  announced** — so a stale copy is always detectable, and an unchanged file still proves
  someone looked.
- **Mechanism that transfers.** Some facts cannot be derived, only received. For those,
  the *table itself* carries an expiry, so a stale copy fails closed instead of being
  silently trusted, and a "nothing changed" refresh is distinguishable from "nobody
  refreshed."
- **Lands.** Rule 13 and §16 rule 5 (*"an allowlist that no longer matches the tree fails
  open"*). Everything in this design that is a received table rather than a computed fact
  should carry `#@`: consent/guardianship snapshots at the edge devices (§3 — buses and
  stadiums, offline), sensitivity mappings, the eligibility and rubric tables from #7,
  the district's fee-waiver rules. An edge device holding a three-month-old guardianship
  cache must answer `unknown`, not `no restrictions`. That is the exact wording of rule 13
  and this is the one-line mechanism that implements it.

---

### 16. Arches — the ontology outlives the application

- **What.** `archesproject/arches` (AGPL‑3, Python, pushed 2026‑07‑29, alive). Heritage
  inventory platform built by the **Getty Conservation Institute and World Monuments
  Fund**, whose entire data layer is **CIDOC CRM**: every node in an Arches "Resource
  Model" graph is a CRM class, every edge a CRM property. Its stated design principle:
  *"In order to increase portability, interoperability and longevity, data should be
  structured to be self-describing and independent of any particular software
  application."*
- **Mechanism that transfers.** Two things.
  1. **The schema is authored in a published external ontology, so an export is
     meaningful without the exporting software.** Institutions that must hand records to a
     successor in 40 years cannot ship a database dump whose column names only the app
     understands.
  2. **CIDOC CRM is event-centric**: you cannot state "current owner" as an attribute; you
     state a dated *acquisition event* with participants. Ownership is only ever
     representable as a transfer with a time and actors.
- **Lands.** §11.1 (the exit line, written before the first install — an export that needs
  terpsi to interpret is not an exit) and rule 8: *"A shared event is two lane entries with
  one referent — never one row with a roster column."* CRM reached that conclusion for
  museum objects decades ago and has the vocabulary for it already; #4's Wikidata ranks and
  CRM's dated events are the same instinct twice. Also note the honest cost: CRM-shaped
  data is verbose and slow to author, which is why Arches separates the graph designer from
  the data-entry UI — a pair, with the graph as the canonical half.

---

### 17. Arlo — declare the risk limit first; if the evidence can't reach it, escalate to the full count

- **What.** `votingworks/arlo` (AGPL‑3). Software for conducting **risk-limiting audits**
  of elections; used for Georgia's 2020 audit. You declare a risk limit up front; the tool
  samples paper ballots and compares them to the recorded tallies; if the sample confirms
  the reported winner to within the declared limit, the audit stops. **If it cannot, the
  audit escalates to a full hand count** — in Georgia's case, five million ballots.
- **Mechanism that transfers.** The threshold is chosen and published *before* the
  evidence is gathered, and the failure branch is a *named, budgeted, more expensive
  procedure* rather than a softer conclusion. There is no "probably fine."
- **Lands.** Rule 19 (*"a guard that cannot be shown to fail has not been shown to
  work"*), rule 13, and §16's own admission that Nestor exposes its threshold rather than
  tuning it for you — *"no value of [the threshold] is good at both jobs."* Arlo is what
  that looks like operationally: the threshold is an input, chosen by the accountable
  party, before the run; and the escalation path is designed, staffed and costed in
  advance. Apply to §8.2 transcription confidence and to any sampling-based acceptance in
  §10: pick the risk limit before the season, and write down what the full hand count is.

---

### 18. Sunrise CMS — a municipality's cemetery records, which must outlive everyone

- **What.** `cityssm/sunrise-cms` (MIT, TypeScript, ~2,000 commits, alive). Cemetery
  management, written and run by the **City of Sault Ste. Marie, Ontario**. Tracks
  cemeteries, burial sites, **contracts**, and work-order activities (interments, grave
  maintenance).
- **Mechanism that transfers.** Two modest but real ones.
  1. **The occupant and the rights-holder are separate parties with separate durations.**
     A burial site has an interred person (permanent) and a *contract* held by a living
     person who can change, transfer, die, or dispute. That is structurally the
     student ↔ guardian split of §7.1: the subject of the record is not the party with
     authority over it, and the authority is a dated instrument, not an attribute.
  2. **Designed down, deliberately, for institutional survival.** From the README: maps
     are optional; *"it does not need an expensive server to run, requires no separate
     database server, and could run on a modest workstation."* A system a small
     municipality can still run in 2050 with whoever is on staff then. Compare §3's drop
     and §11.1's exit: the cheapest deployment that a successor can operate is a
     *feature*, and this is a live example of a public body choosing it.
- **Lands.** §7.1, §11.1, and as an existence proof for the capability map's §20 items
  about graduation and records disposition.

---

### 19. Genebank passport data — the accession record survives the accession

- **What.** GRIN-Global (USDA/CGIAR genebank management system) and Genesys PGR (the
  global accession portal). Both are open platforms; **I did not confirm the licenses**,
  so verify before relying on code. The *rule* is documented and is the find.
- **Mechanism that transfers.** From the genebank documentation: *"The records about
  material that is removed from a collection must not be deleted from databases, as they
  can potentially be tracked to other collections where the material is still actively
  maintained,"* and *"the passport data is never discarded and becomes part of the
  historical archive of the genebank and allows for checking whether material was already
  received, accepted or rejected by the genebank in the past."* Removal is expressed by
  setting a `HISTORIC` flag; accession identifiers are not reused.
- **Lands.** Refusal #3 and rule 16, with a *reason* they don't currently state. The
  argument here is not compliance — it is that **the record of a thing you no longer hold
  is the only way to find that thing elsewhere, and the only way to know you already
  rejected it.** Rephrase for terpsi: the record of a departed student is how you answer
  the alumnus who asks for their recordings in 2041 (capability map §20), and the record of
  a rejected fee-waiver request is how you avoid re-litigating it. Also note the second
  half — *rejected* is a retained state, which is rule 15's dated disposition and §16's
  *"an audit trail that records only agreement is not one."*

---

### 20. Umbrella — the gesture that makes the screen safe

- **What.** `securityfirst/Umbrella_android` (GPL‑3, Kotlin, 291 stars, **last push
  2024‑05 — dormant**; also `_ios`, `_web`, `_content`). Digital and physical security
  guidance for people working in high-risk countries — journalists, activists — with
  checklists, incident forms, and *"the ability to hide the app when crossing a border
  with a simple gesture."*
- **Mechanism that transfers.** A **single, always-available, no-confirmation gesture that
  leaves nothing on screen** — designed for the moment when the threat is the person
  standing next to you, not the network.
- **Lands.** §4 access paths, and the capability map's §20 family cases: a court order
  restricting contact, a confidential-address (Safe at Home) student, a guardian looking
  over a student's shoulder on a bus. The wider pattern (quick-exit buttons, avoiding
  history entries, neutral app names and notifications) is standard in domestic-abuse
  tooling and absent from every SIS I know of. Pair with refusal #7: SMS carries signals,
  never records — a *notification preview* on a lock screen is a record leaving, and it is
  the same threat model.
- Dormant, so read it for the pattern, not the dependency.

---

### Also-rans, kept short because their transplant is narrower

- **`Iconclass`** — `iconclass/data`, **CC0‑1.0**, alive. 28,000 hierarchical alphanumeric
  concepts describing *what a picture is about*, from 1970s Dutch art history. Mechanism:
  a notation where the code's structure *is* the hierarchy, so `11H(FRANCIS)3` is
  simultaneously an identifier and a path. Relevant if the caption/commentary taxonomy of
  §8.1 ever needs to be hierarchical and citable — and a warning, because such notations
  are unreadable to the humans who must type them, which is why Iconclass also ships a
  14,000-term "entry vocabulary" as the human-facing half. That's a pair with a middle.
- **`sdcMicro` / `sdcTable`** (R, GPL) — secondary cell suppression; see #9.
- **`dondeng/four_eyes`** (Ruby gem, maker-checker) — exists, small, and I would not build
  on it; #1 and #12 are better sources for the same idea.

---

## Governance as a checked artifact

`CLAUDE.md` is a numbered refusal list paired with `tests/test_section_refs.py`, which
asserts its `§N` pointers resolve *and* asserts that the checker itself can fail
(`test_the_check_can_actually_fail`, `test_statute_citations_are_skipped_but_bare_refs_are_not`).
That is rarer than it should be. Here is the prior art, best first.

### Debian Policy ↔ `lintian` — the largest declaration/enforcement pair in open source

The **Debian Policy Manual** is normative prose. **`lintian`** is a static checker with a
tag per violation. Three properties worth copying:

1. **Tags cite the policy section.** Run `lintian -i` and a policy violation prints the
   clause it violates. The tag database records its source (`policy`, `devref`), so you can
   list every tag derived from the Policy Manual.
2. **The policy's own changelog names its enforcer.** Policy's `upgrading-checklist.html`
   annotates changed clauses with the lintian tag that covers them, in square brackets —
   the declaration points forward at its enforcement, in the same document, at the moment
   the clause changes. That is `CLAUDE.md`'s §-pointer discipline, inverted and running
   since the 1990s.
3. **The gap is stated rather than implied.** The checklist says plainly that *"the lack of
   such an annotation does not mean that no Lintian tag exists to cover the requirement"* —
   an honest admission that the mapping is partial. Compare `CLAUDE.md` #18: say
   "enforcement" or "ledger." Debian's version is "annotated" or "not yet."

**Lands.** §16 rules 1 and 5. If terpsi's refusal list grows, each refusal wants a tag ID
and each tag wants to name the refusal — and the *unannotated* refusals should be listed,
not left to be discovered.

### `python/peps` — `check-peps.py`, governance metadata validated in CI

`python/peps` ships `check-peps.py`, run in CI, validating each PEP's RFC‑2822 headers:
required headers present, correct order, valid statuses, well-formed dates and author
emails, and constraints on how PEPs may link to each other. PEP 1 is the governing prose;
`check-peps.py` is its enforcement; a PEP cannot merge with a malformed status or a
malformed relationship. I could not confirm from the search whether `Superseded-By`/
`Replaces` *targets* are checked for existence — worth reading the script before citing
it for that specifically. **Lands.** §16's tombstone: five sections, one of which is
"names its successor." A successor pointer that can dangle is a middle that cannot fail.

### W3C ReSpec `data-tests` + the W3C testing policy — a requirement linked to the test that proves it

ReSpec (`speced/respec`) supports a `data-tests` attribute on a testable assertion, taking
a list of test URLs; it renders as a disclosure under the requirement listing the tests
that verify it, and it errors if `testSuiteURI` is unset. Around it sits W3C's **testing
policy**: *"All normative spec changes are generally expected to have a corresponding pull
request in web-platform-tests, either in the form of new tests or modifications to
existing tests, or must include the rationale for why test updates are not required."*

**Lands.** `CLAUDE.md` #19 — *"every invariant needs a test that attempts the forbidden act
and asserts refusal"* — and it supplies the missing artifact: the invariant should carry
the *identifier of the test that mutates it*, in the document, so an invariant with no
test is visible as a gap in the prose rather than discoverable only by reading the suite.
And note the escape hatch's shape: not "you may skip tests" but "you must write down why."

### seL4 — a machine-checked proof with a maintained, published list of what it does not prove

seL4 (GPL‑2, alive) is a microkernel with a machine-checked Isabelle/HOL proof of
functional correctness. The relevant artifact is not the proof: it is
`sel4.systems/Verification/assumptions.html`, **"What the Proofs Assume."** It says which
assumptions apply to which proof (the information-side-channel assumption applies only to
the confidentiality proof, not to correctness or integrity), and it states plainly that the
assumption *"the binary-level model of the hardware captures all relevant information
channels… is known not to be the case."* Also stated: the proof does not cover
register save/restore or the context switch on kernel exit, and *"you have to trust that
the researchers got all necessary conditions and got them right."*

**Lands.** The best available model for §14's "Exists" column and `§18` item 0. The
strongest verification claim in computing is shipped with an itemised list of its own
holes, per-property, and the holes are maintained. This is the tone to write §14 in.

### `tzdb`'s `Makefile`, `sqllimits1.test`, `git`'s doc checks

Three cheap, unglamorous, decades-old instances of the same idea:

- **tzdb** — `links.ck`, `tables.ck`, `name-lengths.ck`, `sorted.ck`, `character-set.ck`,
  `mainguard.ck`, `news.ck` (verified in the `Makefile` this session). Data checked against
  documented convention; `Link` targets checked for existence; even the release notes
  checked for ordering.
- **SQLite** — `limits.html` documents the implementation limits;
  `test/sqllimits1.test` exists *to verify that the documented limits are the enforced
  limits*, per compile-time knob (`SQLITE_MAX_LENGTH`, `SQLITE_MAX_COLUMN`,
  `SQLITE_MAX_ATTACHED`, …), including that the default per-connection limits equal the
  compile-time hard limits. **This is the single best answer to the brief's "README
  documents its own limits, with a test asserting the limit."** The doc is not a promise;
  it is a test fixture.
- **git** — `check-builtins.sh` reconciles the registered builtin command list against
  the source, one half of the (implementation, documentation) pair. I could not confirm
  the `make check-docs` target's exact behaviour from the search results, so treat the
  documentation half as unverified.

### Elm — governance enforced by the compiler, and the cost of it

Elm forbids "native"/kernel JavaScript in published packages; since 0.19 the *compiler*
restricts the capability to a small set of official libraries, so no third-party package
can reach outside the language's guarantees. The invariant (no runtime exceptions from
package code) is enforced at publication, not by review.

**Lands.** §6's *"egress inexpressible in the core"* — the strongest version of that is a
language or packaging layer in which the forbidden act cannot be written, not a scanner
that looks for it afterwards. **And read the reception before copying it**: this policy
produced real, sustained anger ("Elm 0.19 Broke Us", "Why I'm leaving Elm"), largely
because the capability was reserved to a named list of accounts. The lesson for a fleet
consolidating onto a template (§17): a prohibition that some repos are exempt from is read
as a hierarchy, not a safety property. If terpsi's core cannot import the seam, that must
be true of every app including the reference one.

### SQLite's Code of Ethics — a refusal list, and what happened to it

In 2018 D. Richard Hipp adopted **Chapter 4 of the Rule of St. Benedict** — the
"instruments of good works" — as SQLite's Code of Conduct: a numbered list of ~70
injunctions, monastic, 1,500 years old. After sustained criticism SQLite adopted the
Mozilla Community Participation Guidelines as its *Code of Conduct* and renamed the
Benedictine text a **Code of Ethics**, which still stands at `sqlite.org/codeofethics.html`
with a note that the founders continue to hold to it.

**Why it belongs in this section rather than in delight.** It is the cleanest natural
experiment in the genre `CLAUDE.md` is written in. A numbered, absolute, unapologetically
value-laden list of refusals is a *good* artifact and it was received badly for a
structural reason: it was published in the slot reserved for **conditions of
participation**. The fix was not to weaken it but to **split the pair** — one document
saying what the maintainers hold themselves to, another saying what is required of
contributors — and to say which is which. terpsi's list is currently in a
maintainer-facing file (`CLAUDE.md`) and reads correctly there. If any of it moves toward a
contributor-facing or student-facing surface, split it first.

---

## Deliberately finished software

The brief wants a relay *"small enough to read in an afternoon and boring enough to never
need a feature."* Four candidates, with the mechanism each one proves.

### `ii` — IRC as a directory tree, under 500 lines, MIT

`git.suckless.org/ii`. Authors Anselm Garbe and Nico Golde. It connects to IRC and
**exposes the protocol as the filesystem**: a directory per server / channel / nick, an
`in` FIFO you write to, an `out` file you read. Under 500 lines of C, and the discipline is
visible in the history — there is a commit literally titled *"restructuring to stay under
500 lines ;)"*. A self-imposed line budget, enforced by refactoring rather than by
declining features.

**Lands.** §4.3 / the relay. `ii`'s real transferable idea is not smallness, it is that
**the interface is files, so the client is `cat` and the log is the transcript and the
audit trail is `ls -l`.** A relay that cannot read anything (§12 decision 2) and whose
state is a directory tree is a relay whose correctness a director's IT contractor can
verify without reading code. Also: `Maildir`'s lock-free unique-filename convention is the
same family, and a lane-per-student store shaped like a maildir is readable in a century
with `ls`.

### qmail — a security guarantee since 1997, and an author who published his own failure

`cr.yp.to/qmail`. Public domain. **Finished.** Bernstein's *"Some thoughts on security
after ten years of qmail 1.0"* (ACM CSAW 2007) is the paper this project should read for
tone: it reviews the architecture, then **"articulates partitioning standards that qmail
fails to meet"** — the author's own software, measured against the author's own standard,
found wanting, in print — and then analyses why qmail survived the failure anyway. Ten
years, a million-plus deployments, four known bugs, no security holes, under a standing
cash guarantee.

**Lands.** `CLAUDE.md`'s "Before you claim something" section and §14's unverified Exists
column. The move to copy is not the guarantee; it is publishing the standard you fail.

### WireGuard — one refusal, held absolutely

~4,000 lines against OpenVPN's hundred thousand-plus, and **no cipher agility and no
negotiation whatsoever** — the whitepaper (`wireguard.com/papers/wireguard.pdf`) argues
that configurable cryptography has caused more real vulnerabilities than fixed good
defaults, and that with no negotiation there is no downgrade attack *on the negotiation*.
When a primitive breaks, the protocol version changes and everyone moves at once; there are
no stragglers on deprecated ciphers.

**Lands.** §12's decision list, which is exactly this genre — a small set of choices held
absolutely so that everything downstream simplifies. And specifically §5/§6: refusing
configurability at the trust boundary means there is no `WILLOW_INFERENCE_PROVIDER=auto`
to remove later (refusal #1). The general form: **a system with no fallback chain has no
silent-degradation mode.**

### Fossil — feature-stable, and refuses a feature everyone else has

BSD‑2. Append-only content store, single-file repository carrying its own wiki, tickets and
forum, and a manual page arguing that rebase is an anti-pattern. See transplant #5.
**Lands.** §7.4's "the lane handed over whole at the exit" — a single-file, self-describing
repository containing the record *and* its discussion *and* its history is the literal
artifact §11.1 is asking for.

### Honourable, non-software: the Unicode Stability Policy

Not code, but the strongest "finished" commitment I found: **once a character is encoded it
is never removed, and its name never changes.** Corrections are handled *additively* —
`NameAliases.txt` carries a normative alias, and errata are noted in comments — because the
published name is immutable even when it is wrong. **Lands.** §16's tombstone rules and
refusal #3: a correction that overwrites is indistinguishable from a falsification. The
alias mechanism is how you correct a record you are not allowed to edit, and terpsi will
need it the first time a legal name, a birthdate, or an adjudication caption is entered
wrong. Note how it composes with transplant #4: Wikidata's `deprecated` + reason and
Unicode's immutable-name-plus-alias are the same answer at two granularities.

---

## Pure delight, no transplant

Kept because they are wonderful, and marked because they buy nothing.

- **The Rule of St. Benedict as a software Code of Ethics.** Chapter 4's "instruments of
  good works," ~70 numbered injunctions, adopted verbatim by the most widely deployed
  database engine on earth, and still hosted at `sqlite.org/codeofethics.html`. Somewhere
  in a monastery in 516 AD, someone wrote a numbered refusal list, and it is in your phone.
- **U+FE18.** Its official Unicode name contains a typo — `BRAKCET` — and because names are
  immutable it can never be fixed. A formal alias exists to say what it *should* say. A
  permanent, load-bearing, globally-shipped acknowledgment that the record is wrong and the
  record stands.
- **tzdb on itself:** *"Any attempt to pass the tz database off as the definition of time
  should be unacceptable to anybody who cares about the facts."* Forty years of being the
  definition of time, and that sentence in the manual.
- **`news.ck`.** A `Makefile` target whose entire job is to assert that the *release notes*
  are sorted and have no duplicate version lines. Someone got burned once.
- **Divinum Officium** computes, today, in Perl, the office for any date under the rubrics
  of 1570 — and also under those of 1888, 1911, 1955 and 1960, simultaneously, with
  regression tests, and it was pushed to this morning.
- **Iconclass** has a code for what a picture is about, and there are 28,000 of them,
  released CC0 by Dutch art historians, and one of them is specifically for *"Francis of
  Assisi preaching to the birds."*
- **`ii`'s commit message:** *"restructuring to stay under 500 lines ;)"*

### Two cautionary cases, not projects

Both are widely documented, neither is open source, and both argue for a rule this project
already has.

- **The Post Office Horizon scandal (UK).** Branch accounting data could be altered
  remotely by the supplier without the branch's knowledge, while the system's audit trail
  was treated in court as authoritative. Sub-postmasters were prosecuted and imprisoned on
  it. This is the strongest existing argument for §16's Nestor properties — *"the trail
  must not be redirectable or suppressible,"* a seal bound to a key the store does not
  hold — and for `CLAUDE.md` #16: *"no role's authority extends to deleting the record of
  its own exercise."* Note which role it was: not the user, the *vendor*. Read it beside
  the fleet's own §5 rule that the canonical store is read-only to the app.
- **Facebook's 2014 "Year in Review."** Eric Meyer's *"Inadvertent Algorithmic Cruelty"* —
  a cheerful auto-generated retrospective built around a photograph of his daughter, who
  had died that year. It produced the vocabulary the capability map's §20 needs: Meyer and
  Sara Wachter-Boettcher's *Design for Real Life* replaces "edge case" with **"stress
  case"** — design for the person having the worst day of their life, not the average
  persona — and Michael Massimi's HCI work names the field **thanatosensitive design**
  (*"Dealing with Death in Design: Developing Systems for the Bereaved"*, CHI 2011).
  The concrete rules that fall out and that terpsi can implement: a death is a **dated
  fact that fans out to suppress generated content** (birthdays, streaks, "on this day,"
  practice-streak nudges, fee reminders, absence chasers), the suppression must be
  **automatic and immediate rather than a per-feature opt-out**, and the state must be
  **enterable by one person once** — nobody should have to report a death twice, and
  nobody should have to report it to a form that asks them to confirm they are sure.
  Adjacent live prior art: **Chayn** (`github.com/chaynhq`, survivor-led, open source)
  publishes trauma-informed design principles — Safety, Trustworthy, Plurality, Agency,
  Open and Accountable, Solidarity, Empathy, **Friction**, Privacy, Hope — and the
  presence of *Friction* as a virtue is the one most software gets backwards; and GOV.UK's
  own *"Distress and design"* work (`publicpolicydesign.blog.gov.uk`, 2023) plus DWP's
  bereavement content design, whose finding is that in these flows the words must be
  blunt: *"There's no room for doubt or misunderstanding."* Capability map §22 item 10
  says *"programs remember which tools made a terrible week worse."* This paragraph is the
  literature for that sentence.

---

## What I looked for and did not find

Stated so nobody re-runs these searches.

- **Open-source software for the two-person rule as a general mechanism.** Beyond
  `dondeng/four_eyes` (a small Ruby maker-checker gem) and branch protection, there is no
  general library. The good prior art is procedural and domain-specific: the KSK ceremony
  (#12), Airlock's independent review (#1). Build it; don't shop for it.
- **Open-source blood-bank cross-match software with bedside two-person verification.**
  The GitHub "blood bank" topic is student CRUD projects. The dual-ID-scan
  closed-loop-verification pattern exists only in commercial LIS products.
- **Open-source hospice / bereavement / memorial records software.** I found none.
  Bereavement tracking exists only in commercial hospice suites. The gap in the capability
  map's §20 ("the death of a student — which programs do face and which no software handles
  gracefully") appears to be real across the whole open-source landscape, not just in
  music-program tools. That is either a warning or an opportunity.
- **Lighthouse / long-duration-instrument software** with a transplantable mechanism. The
  nearest thing — sequential, order-enforced chart corrections (S‑57 update files) — I
  could not confirm as an enforced invariant in open-source code within budget.
- **Divinum Officium's `regress/` contents.** GitHub API access in this session is scoped
  to `terpsi-music`, so I could not enumerate it. The directory is referenced from the
  repo root; someone should read it before citing its test count (#17).
