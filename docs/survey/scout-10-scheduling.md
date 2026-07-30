# Scout 10 — Constraint Satisfaction & Optimization, Within Refusal #6

Scope: the combinatorial problems in `CAPABILITY-MAP.md` §3 (Scheduling/Calendar/Attendance), §8 (Travel/rooming), §9 (Competition ops), §15 (Clinicians/staff), read against `ARCHITECTURE.md` §7.4 W-7 and `CLAUDE.md` refusal #6.

Verification method: every repo below was confirmed to exist via the GitHub API (`search_repositories` with `repo:` qualifiers) on 2026-07-30, with language / star / last-push metadata taken from that response. Licenses were read from the repo's actual `LICENSE` file over `raw.githubusercontent.com` where reachable; where the file 404s or the fetch was blocked I say so explicitly rather than guess. Two capability claims (CPMpy's explanation tools, CPMpy's solution enumeration) were confirmed by reading source paths and doc text, not READMEs.

**Budget note:** the session's WebSearch allowance (200 calls) was exhausted by earlier agents partway through this sweep. Roughly the last third of the work was done with GitHub code/repo search and direct WebFetch instead. Three intended lines of inquiry went uncovered as a result and are listed under *Gaps* at the end.

---

## Ranked table

| # | Project | What | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **CPMpy** (`CPMpy/cpmpy`) | Python CP modelling layer over 15 backends; ships MUS/MCS/MSS/MARCO explanation tools + `solveAll` + diverse-solutions recipe | **Apache-2.0** (read from repo) | 374★, pushed 2026-07-24 | Rotating pull-out (flagship), all conflict problems, facility contention, infeasibility explanation | **adopt** |
| 2 | **OR-Tools / CP-SAT** (`google/or-tools`) | The solver underneath everything; `enumerate_all_solutions`, assumption-based infeasibility subsets | **Apache-2.0** | 13,831★, pushed 2026-07-29 | Same as above; the engine | **adopt** (as CPMpy's backend, not directly) |
| 3 | **good-enough-golfers** (`islemaster/good-enough-golfers`) | Social Golfer / Kirkman's Schoolgirl solver, genetic, client-side browser, forbidden-pairs support. Written for a teacher grouping 28 students into rotating discussion groups | **MIT** (read from `LICENSE`) | 38★, pushed 2026-04-11 | Four-year repertoire rotation; rotating sectionals; the *interaction model* for present-don't-decide | **steal-the-idea** (and possibly adopt the UI pattern) |
| 4 | **XCP-explain** (`CPMpy/XCP-explain`) | ECAI-2024/CP-2023 tutorial: MUS/MCS, step-wise explanations, constraint relaxation, **counterfactual solutions** — all driven by a **nurse rostering** use case with benchmark instances | **NONE FOUND** — no `LICENSE` file (404), none stated in README. Zenodo DOI only | 28★, pushed 2026-07-22 | Directly: "why is there no schedule", "what would have to change" | **read-only-interest** (license blocks reuse; reimplement against CPMpy proper) |
| 5 | **music21** (`cuthbertLab/music21`) | Parse MusicXML/Humdrum/MIDI; `instrument` module; partition score by instrument | **BSD-3-Clause** | 2,545★, pushed 2026-07-29 | Instrumentation gap analysis (§9 design/execution) | **adopt** |
| 6 | **UniTime** (`UniTime/unitime`) | Full university timetabling suite: course + exam + **student** scheduling, room/event management, interactive conflict resolution | **Apache-2.0** | 346★, pushed 2026-07-29, 210 forks, 4 open issues | Facility booking, athletics contention, block/AB awareness; a constraint vocabulary to mine | **steal-the-idea** (do not adopt: Java/JSP/Hibernate monolith) |
| 7 | **matching** (`daffidwilde/matching`) | Gale-Shapley, hospital-residents, student-allocation, stable roommates. JOSS-published | **MIT** (read from `LICENSE`) | 167★, pushed 2026-03-20 | Rooming lists, clinician/studio-teacher pairing — **and the fairness debate itself** | **steal-the-idea** (see warning below) |
| 8 | **Temoa** (`TemoaProject/temoa`) | Energy-system optimizer implementing **Modelling to Generate Alternatives (MGA)** — deliberately generates near-optimal solutions that are *maximally different in decision space* | not verified this pass | 113★, pushed 2026-07-24 | The formal answer to "a set, not an optimum" | **steal-the-idea** |
| 9 | **Timefold Solver** (`TimefoldAI/timefold-solver`) | Live fork of OptaPlanner; employee rostering w/ skills, school timetabling, conference scheduling quickstarts | **Apache-2.0 Community / proprietary Enterprise — OPEN-CORE TRAP** | 1,730★, pushed 2026-07-30 | Chaperone shifts w/ skill matching (CDL/first aid/sewing) | **read-only-interest** (see trap notes) |
| 10 | **FET** (`lalescu.ro/liviu/fet`) | Mature school timetabler, very large constraint palette, C++/Qt desktop | **AGPL-3.0-or-later — FLAGGED** | initial release 2002, still maintained | Its ~60-item constraint palette is the best available taxonomy of what school scheduling actually needs | **read-only-interest** (AGPL + desktop GUI + emits one timetable) |
| 11 | **fairpyx** (`ariel-research/fairpyx`) | Course-seat allocation: iterated maximum matching, round-robin, fair-division mechanisms | **MIT** (read from `LICENSE`) | 4★, 28 forks, pushed 2026-05-18 | Limited trip slots, oversubscribed sectionals — the *mechanism* layer | **steal-the-idea** (research-grade, tiny) |
| 12 | **adaptive_scheduler** (`observatorycontrolsystem/adaptive_scheduler`) | Las Cumbres Observatory telescope-network scheduler; OR-Tools kernel, SCIP/CBC free backends | **GPL-3.0 — FLAGGED** | pushed within the last year | Existence proof for allocating scarce slots against *granted entitlements* rather than merit | **read-only-interest** |
| 13 | **KidneyExchange** (`JohnDickerson/KidneyExchange`) | Max-weight, failure-aware, **fairness-aware**, and individually-rational matching solvers + dynamic simulator | not verified this pass | 16★, pushed 2025-07-11 | Nothing directly — but it is the canonical codebase of the "should we weight the people?" argument | **read-only-interest** |
| 14 | **RobinX** (`Robin-X/RobinX`) | XML format + validator/evaluator for round-robin sports timetabling; **3-field classification** of scheduling problems | **NONE FOUND** — no `LICENSE` file (404) | 3★, pushed 2026-05-11 | Athletics fixture contention; the classification notation is the real prize | **read-only-interest** |
| 15 | **XHSTT / HSEval** (`utwente.nl/hstt`) | Standard XML archive for high-school timetabling; 15 constraint types; solution evaluator | archive terms, not software licensing | long-standing academic benchmark | A ready-made constraint vocabulary and a *test corpus* for the pull-out solver | **steal-the-idea** |
| 16 | **kidney_solver** (`jamestrimble/kidney_solver`) | PICEF/PIEF cycle-and-chain formulations | **requires Gurobi (commercial)** | 9★, pushed 2026-06-17 | — | **read-only-interest** |

### Dead ends worth recording as tombstones
- `apache/incubator-kie-optaplanner` — **archived**, confirmed via API (`"archived": true`). OptaPlanner is retired; its README redirects to `incubator-kie-drools`. Any doc in this fleet citing OptaPlanner is citing a corpse.
- `TimefoldAI/timefold-solver-python` — **archived**, confirmed via API. The Python route into Timefold is not a live path; Timefold is a JVM dependency.

---

## Top finds, with concrete transplant and cost

### 1. CPMpy — adopt. This is the whole answer, and it is Apache-2.0.

CPMpy is a NumPy-flavoured constraint-modelling layer in pure Python that compiles to a backend of your choice (OR-Tools CP-SAT by default; also Choco, MiniZinc, Z3, PySAT, Exact, HiGHS, SCIP, and commercial ones you would not enable). It satisfies the deployment constraint in §6 without argument: `pip install cpmpy ortools`, no network, no model weights, no third party — the solver is a C++ library in-process. A modest on-prem box is the *normal* deployment, not a degraded one.

What makes it the top find is not the modelling layer, it is `cpmpy/tools/explain/`. I read the module paths and docstrings directly rather than trusting the README:

- `mus.py` — *"Re-implementation of MUS-computation techniques in CPMPy: Deletion-based MUS, QuickXplain, Optimal MUS, Native MUS for given solvers"*
- `mcs.py` — `mcs(soft, hard=[], solver="ortools")`, *"Compute Minimal Correction Subset of unsatisfiable model"*
- `mss.py` — `mss_opt`, `mss_grow`, `mss_grow_naive`
- `marco.py` — *"Re-implementation of MUS-enumeration using MARCO"*
- `utils.py` — `make_assump_model`, which wraps your constraints in assumption literals so the above can operate

`marco.py` is the load-bearing one and I want to be precise about why. A single MUS says *"these three constraints cannot all hold."* MUS **enumeration** says *"here are all four distinct minimal ways your requirements conflict."* The dual, MCS/MSS, says *"here are the minimal sets you could drop to make it feasible."* Enumerating those means the system hands the director the complete menu of relaxations and picks none of them. That is refusal #6's "the system presents, a human decides" implemented as an algorithm rather than as a UI convention.

Solution enumeration is confirmed in `cpmpy/model.py`: `solveAll(solver=None, display=None, time_limit=None, solution_limit=None)`, with `display` taking either an expression list or a callback. From `docs/multiple_solutions.md`, the K-diverse recipe is six lines:

```python
K = 3
store = []
while len(store) < K and s.solve():
    store.append(x.value())
    s.maximize(cp.sum([cp.sum(x != sol) for sol in store]))
```

Note what that objective is and is not: `cp.sum(x != sol)` is a **uniform** Hamming count over the assignment matrix. It contains no per-student coefficient. It is invariant under relabelling students. This matters enormously and I develop it in the design section below.

One more thing already in the tree: `examples/csplib/` contains `prob028_bibd.py` (Balanced Incomplete Block Design) and `prob044_steiner.py` (Steiner triple systems). Those are not decoration — they are the exact combinatorial designs the flagship problem reduces to.

**Transplant for the flagship (rotating pull-out lessons).** The problem the directors are solving on graph paper has a very small, very clean model, and the "never misses the same academic class twice" condition is literally `AllDifferent`:

```
x[student, lesson_index]  ∈ {periods 1..P}   # which academic period this lesson displaces
AllDifferent(x[s, :])            for each student s      # never miss the same class twice
Count(x[:, w] == p) <= capacity  for each week w, period p   # teacher/room capacity
x[s, i] not in unavailable[s]                            # IEP/504 holds, athletics, job shifts
```

Per-student rows are all-different; columns are capacity-limited. That is a **Latin-rectangle completion** problem. It is well within CP-SAT's reach at school scale, and it is *student-anonymous by construction* — every student's row carries the identical constraint. The A/B-day and block-schedule variants change the index set on `w`, not the model.

**Cost.** Low, and I want to be honest about which parts are low. The dependency is small and permissive. The model above is on the order of 40 lines. The genuinely expensive parts are the three that are not solver work: (a) getting the academic master schedule in at all, which is an SIS import and therefore an I-10 treaty-crossing problem, not a scheduling problem; (b) modelling the *unavailability* sources faithfully — religious observance, IEP service minutes, athletics, a job — each of which is a separate data-acquisition negotiation; (c) the sidecar/seal plumbing, since per #11 the solver may only write sidecars and per #10 its output is a `draft`. Budget the solver at days and the surrounding obligations at weeks. Do not let the small model size mislead anyone about the total.

**Watch item.** CP-SAT's own assumption mechanism (`SufficientAssumptionsForInfeasibility()`) returns a subset that is *minimized but not guaranteed minimal*, and it is **incompatible with parallelism — workers must be set to 1**. If you reach past CPMpy to CP-SAT directly for explanations you inherit both caveats. CPMpy's `mus()` gives you an actually-minimal set. Prefer CPMpy's.

### 2. good-enough-golfers — steal the idea, and steal the *stance*.

MIT, JavaScript, entirely client-side, 38 stars, pushed 2026-04-11. It solves the Social Golfer Problem and Kirkman's Schoolgirl Problem: arrange N people into G groups over R rounds so no pair meets more than once. The origin story, from its own README, is that the author's father needed to sort 28 students into discussion groups of 4 across a term, with rotation, *plus* forbidden pairings for particular students. That is this domain, with the serial numbers filed off.

Two things to take. First the algorithm family: repeat-pairing penalised **exponentially** under a genetic search. Exponential penalty on repeats is exactly the right shape for "never repeats a piece in four years" and for rotating sectional groupings — it makes a second repeat far worse than a first, which is how directors actually feel about it, without ever comparing two students.

Second, and more valuable, the **stance**, which is in the name. The tool declines to find the optimum. Its README argues that exact solutions are prohibitively slow while approximations are fast and good enough for real use. A project forbidden from computing an optimum over students has an unexpected ally here: *"good enough" is not a compromise, it is the compliant answer.* A solver that returns a handful of feasible-and-decent arrangements, re-rollable on demand, has computed no priority. A solver that returns "the optimal assignment" has. This project should adopt "good enough, re-rollable" as its stated posture in the architecture doc, and cite this as prior art that the posture is *usable*, not just permissible.

**Transplant.** For the four-year repertoire rotation, note first that the naive form does not touch students at all: "no piece programmed within four consecutive years" is a constraint on the *piece sequence*, entirely student-free, and should be modelled that way. The per-student form only becomes necessary at the edges — fifth-year students, mid-year transfers, a student who repeats a grade — and those are precisely the cases where you present options rather than decide. For rotating sectionals and small-ensemble groupings, port the exponential-repeat-penalty objective into the CPMpy model rather than depending on the JS.

**Cost.** Very low as an idea transplant; the model is a page. Adopting the actual code means taking on a browser-side JS/genetic implementation that would sit awkwardly beside a Python CP stack and would need its own sidecar/seal wiring — probably not worth it, but read its UI: the re-roll button is the interaction pattern this project needs.

### 3. XCP-explain — the right content, blocked by the wrong license situation.

This is the ECAI-2024 / CP-2023 hands-on tutorial from the CPMpy group, and its entire worked example is **nurse rostering** — the closest published analogue to a chaperone/volunteer shift problem with skills and availability. It covers MUS/MCS extraction, step-wise explanations, constraint relaxation, and **counterfactual solutions**. That last one is the director's real question, and it is not "what is optimal": it is *"what would have to be different for Maya's lesson to move out of third period?"* A counterfactual answers with a change to the constraints, not with a ranking of Maya against anyone.

**But:** there is no `LICENSE` file in the repo — I fetched the path and got a 404 — and the README states no license either, offering only a Zenodo DOI and a citation request. Unlicensed published code is not permissively licensed code; default copyright applies and reuse is not granted. So this is **read-only-interest**: read the notebooks, learn the technique, then implement against `cpmpy.tools.explain`, which *is* Apache-2.0 and which contains the same primitives. Alternatively, ask the authors to add a license — they are the same group that maintains CPMpy under Apache-2.0, so this is plausibly an oversight rather than a decision.

**Cost.** Reading: an afternoon. Reimplementing the counterfactual and relaxation-suggestion layer on top of `cpmpy.tools.explain`: call it a week, and it is the highest-value week in this whole report after the base model.

### 4. UniTime — mine it, do not adopt it.

Apache-2.0, 346 stars, 210 forks, pushed 2026-07-29, and remarkably only 4 open issues. It is a real, deployed, comprehensive system covering course timetabling, exam timetabling, **student** scheduling, and room/event management with multiple departmental schedule managers coordinating against each other. That last property is the interdepartmental fight in §3 ("shared-student negotiation with athletics and drama") already modelled by someone who shipped it.

Adopting it is not on the table: it is a large Java/JSP/Hibernate application with its own data model, and dropping it into this stack would create exactly the vendored-copy pair that §16 exists to prevent, with no plausible reconciler. What to take instead is its **decomposition** — that facility booking, event management, and class placement are separate solvers sharing a room/time calendar, rather than one monolithic timetable — and its treatment of a room as a contended resource with an owning department and a request/approval flow. That last maps cleanly onto §7.4 I-6: a facility request is an *ask*, and every ask gets a dated disposition.

**Cost.** Zero to read; the risk is the temptation to adopt. I flag that explicitly.

### 5. Timefold — the open-core trap, stated precisely.

Timefold is the live fork of the now-archived OptaPlanner (I confirmed `apache/incubator-kie-optaplanner` is archived via the API). Community Edition is Apache-2.0; **Enterprise Edition is proprietary and requires a commercial license for production use**. That is an open-core model and it should be flagged as such in any doc that names Timefold.

I could not verify the exact per-feature split — `timefold.ai/license` and the Enterprise docs page both returned 403 to my fetches, and my search budget was gone by then. So I will not list the split. What I can state from the pages that did resolve is the structural fact: Community is Apache-2.0, Enterprise is not, and the boundary is a per-feature boundary rather than a support-only boundary, which is the kind that bites you after you have built on it. **Anyone considering Timefold must verify which specific features are Enterprise-gated before writing a line against it.** Add to that: it is a JVM dependency, and the Python binding repo is archived.

Its employee-scheduling-with-skills quickstart remains the best reference model for the chaperone/volunteer problem (CDL, first aid, sewing, truck driving as required skills against shift demands). Read the model, build it in CPMpy.

### 6. music21 — adopt, for the one hard problem that is unambiguously safe.

BSD-3-Clause, 2,545 stars, pushed 2026-07-29. Parses MusicXML and friends and exposes an `instrument` module plus score-partitioning by instrument. "Can this ensemble play this chart with two bassoons and no oboe" decomposes into: music21 extracts required parts and doublings from the chart; the roster and inventory supply what is available; the coverage question is a bipartite matching (a clarinettist can cover bass clarinet, a trombonist cannot cover oboe) solved as flow or in CP-SAT.

This is worth calling out because it is the one item on the list where optimization is fully clear of refusal #6 — **as long as you stop at the right place.** Reporting the *gap* ("the chart wants one oboe and one bassoon; you have no oboe and two bassoons; the oboe line is cued in the Eb clarinet part") is a statement about a chart and an inventory. No student appears. That can be fully automated and needs no human seal to be safe. Deciding *which student* covers the bass clarinet line is an assignment among students and therefore a presented choice. Draw the line at the gap report, and the capability becomes one of the few in §9 that can ship without the escalation machinery.

**Cost.** Low. music21 is heavy-ish as a dependency but pure Python and offline. The doubling/cue-coverage knowledge is domain data you will have to enter by hand — a table of which instruments can cover which parts — and that table is the actual work, not the code.

---

## The design question: how a solver presents alternatives without ranking students

This is the part I was asked to take seriously, so here is a concrete, testable answer rather than a posture.

### The precise technical property you want is *anonymity*

Refusal #6 forbids computing a priority *between two students*. It does not forbid computing feasibility, and it does not forbid every objective function. The distinguishing property, which social choice theory already names, is **anonymity**: the model must be invariant under permutation of student identities. Swap any two students' identifiers, re-solve, and the set of feasible solutions must come back as exactly the corresponding permutation of the original set. If it does not, the model contains a term that distinguishes those two students, and *that term is the forbidden priority*, wherever it happens to live in the code.

This gives a crisp rule for review: **no objective coefficient, tie-break, or constraint weight may be indexed by student identity.** Aggregates over periods, rooms, slots, skills, or shifts are fine. `minimize(number of distinct academic periods displaced across the season)` is fine. `minimize(sum over students of weight[student] * periods_missed[student])` is a priority between students and is forbidden even if every weight is currently 1.0, because the shape invites the weights to diverge later.

And it gives you the guard that `CLAUDE.md` #19 demands — a test that attempts the forbidden act and asserts refusal, rather than a green suite. The mutation is a permutation:

```
for each pair (a, b) of students in a fixture:
    S1 = solver.feasible_set(instance)
    S2 = solver.feasible_set(instance with a,b identifiers swapped)
    assert S2 == permute(S1, a, b)     # else: the model ranked a against b
```

That test can fail, it fails loudly when someone adds a seniority weight or a "good attendance gets first pick" term, and it is the difference between an enforcement and a ledger (#18). I would make this the acceptance test for the whole scheduling subsystem.

### Seven mechanisms, in the order you should reach for them

**1. Solve for feasibility, not optimality.** Model everything as hard constraints and call `solveAll(solution_limit=K)`. You get a *set* of schedules with no ordering among them, because nothing ordered them. This is the default and it should be the default — the absence of an objective is not a missing feature here, it is the compliance property.

**2. Retrieve the set by diversity, never by top-K.** Top-K requires an objective and therefore a ranking. K-diverse requires only a distance over the assignment matrix. CPMpy's recipe maximises uniform Hamming distance from solutions already found, which is anonymous by inspection. Present a handful of *structurally different* schedules rather than a ranked shortlist. This is the same technique the energy-policy people call **Modelling to Generate Alternatives** (Temoa, find #8), where the entire point is that presenting one optimum to a policymaker is epistemically dishonest about a decision space with many near-equal options. Their argument transfers verbatim to a band director, and it is a better argument than "we are not allowed to rank," because it is about the *quality* of the decision rather than a rule.

**3. Present the set without re-introducing an order in the UI.** A list is a ranking. If you render K options top to bottom, you have ranked them in the only place the director actually looks. So either randomise the presentation order and label it as arbitrary, or — better — present the options by their **differences over resources**: "Option A clears third period entirely but puts four lessons in the band room during athletics' field time. Option B keeps the band room free on Tuesdays but displaces three lessons into fourth-period science." Those sentences compare *schedules*, not students. Any option summary that names a student as better or worse off has smuggled the ranking back in.

**4. When infeasible, return the conflict — not the best compromise.** This is the most important inversion in the whole design. The tempting behaviour when no schedule exists is to relax something and return the least-bad schedule, and *that is precisely the forbidden computation*, because choosing what to relax is choosing whose interest yields. The compliant behaviour is to return the **MUS**: "these constraints cannot all hold." Then enumerate the **MCSes** with MARCO: "here are the four minimal sets of requirements you could drop; each restores feasibility." The director picks. `cpmpy.tools.explain` gives you all of this under Apache-2.0. Note what this does to W-7: an MUS is the *machine-readable content of the escalation*. "Halt and escalate" stops being a dead end and becomes a dated, minimal, auditable statement of why the system stopped — which is also what makes it satisfy I-6, since the escalation is itself an ask that now carries a timebound and a disposition.

**5. Let the human's decision re-enter as a constraint, not as a weight.** The interactive loop is: solver emits K feasible drafts plus the conflict set; the director decides something ("Maya's lesson must not be in third period"); that decision is added as a *hard constraint*; re-solve. Three properties fall out at once. The priority stays in the director's head and never enters the model, so anonymity is preserved across the whole loop. The added constraint is a durable dated record of who decided what, which is what I-7 and #16 want anyway. And the audit trail records rejections as durably as approvals (#10), because a rejected option is a constraint that was *not* added and can be logged as such. Annie MOORE, the refugee-placement system, is the deployed precedent for exactly this loop — machine recommendation plus substantial staff autonomy to interactively fine-tune — though the software itself is proprietary and only the design papers are public.

**6. If you must reduce K to 1, use a seeded lottery, not a score.** Sometimes one schedule has to ship. Breaking the tie by *any* computed quantity over students is the forbidden act. Breaking it by a public, seeded, recorded random draw is not: it is auditable, it is reproducible from the record, and it is provably not a priority. This is the school-choice mechanism-design answer (random serial dictatorship and its relatives), and `fairpyx` is where to read implementations. One trap to state explicitly: **the seed must not be derived from student identifiers.** A hash of student names is a deterministic function of identity — that is a priority with extra steps. Seed from the event ID plus a published nonce. Note also that the anonymity test in the previous section applies to the *feasible set*, not to the lottery draw; the draw is where symmetry is deliberately and visibly broken, and it must be the only such place.

**7. The one optimization that survives: leximin over the anonymous profile.** If aggregate fairness genuinely must be optimized, the admissible form is leximin (or maximin) over the **sorted** vector of outcomes — minimise the worst-off count of displaced periods, then the second-worst, and so on. Sorting discards identity, so the objective is anonymous by construction: it cares *how bad the worst case is*, never *whose* it is. This is the real fairness-without-ranking formulation and it is worth having in the toolkit. But it still selects a unique winner, so it must feed the **present** step and never the **decide** step: leximin picks a schedule to *show*, alongside others, not a schedule to enact.

### Where this bites hardest, and where it does not

Three §3/§8 capabilities are irreducibly W-7 conflicts and must run the full present-and-escalate machinery: **rooming lists** and **limited trip slots** (both named explicitly in W-7), and **chair placement** (named in refusal #6). Do not let the rooming-list rule constraints in §8 — grade, gender, requested roommates, staff adjacency — fool anyone into thinking a solver may resolve them; the constraints are legitimate filters, but the choice among feasible roomings is a human act.

By contrast, several of the named hard problems turn out to be *fully* clear of refusal #6 once modelled correctly, and it is worth saying so loudly so the compliance burden lands where it belongs:

- **Instrumentation gap analysis** — a statement about a chart and an inventory. No student in the model.
- **Four-year repertoire rotation**, in its base form — a constraint on the *piece sequence*, not on students.
- **Facility booking against athletics** — contention between *departments over rooms*. Bands, teams, and rooms may be prioritized against each other freely; refusal #6 is about students.
- **Bus and equipment manifests, head counts** — reconciliation and counting, not allocation.
- **Rotating pull-out scheduling**, in the model given above — every student's row carries an identical `AllDifferent`. It is anonymous by construction. Only the *infeasible* case escalates, which is exactly when a human should be looking anyway.

That last point is the happy finding of this whole sweep: **the flagship problem is compliant in its natural formulation.** The refusal does not cost you the flagship. It costs you the right to auto-resolve the flagship when it fails — and MUS enumeration turns that cost into a feature.

---

## Weirdest things I found

**1. Kirkman's Schoolgirl Problem, solved for a teacher, in MIT-licensed JavaScript.** `good-enough-golfers` traces to an 1850 recreational-mathematics puzzle about fifteen schoolgirls walking in rows of three, and its modern incarnation exists because one person's father needed to sort 28 students into rotating discussion groups. A 176-year-old combinatorics problem with a browser UI and a re-roll button is the closest thing to a shipped implementation of "present, don't decide" that I found anywhere, and it comes from recreational maths rather than from operations research or from ethics.

**2. Energy-policy modellers built the anti-optimum on purpose, and named it.** Modelling to Generate Alternatives exists because presenting a single optimal decarbonisation pathway to a legislator was recognised as *misleading* about a decision space full of near-equal options. Temoa implements it. The entire justification — that the optimum is an artefact of the objective and that a decision-maker deserves the alternatives — is written up in the energy-systems literature and transfers to a band director's graph paper without modification. This project would benefit from citing an argument for presenting alternatives that is about decision quality rather than about a prohibition.

**3. Radio-telescope schedulers allocate scarce slots against *granted entitlements* rather than merit.** LCO's `adaptive_scheduler` (GPL-3.0, OR-Tools kernel) schedules a global telescope network where the scarce good was already divided by a time-allocation committee into per-proposal fractions, and the solver's job is to honour those grants, not to judge whose science is better. That is structurally the same move as issuing a named, timebound grant per student and letting the solver satisfy grants rather than rank holders — an existence proof from astronomy that a scheduler can be entirely indifferent to the merit of the parties it serves.

**4. The kidney-exchange literature is the explicit ethical argument this project settles by fiat.** `JohnDickerson/KidneyExchange` ships max-weight, **fairness-aware**, failure-aware, and individually-rational solvers side by side, because the field has an open, published, unresolved fight about whether to weight patients — by age, by waiting time, by expected graft survival. Refusal #6 declines to have that fight. Reading a codebase where the fight is a *runtime flag* is the sharpest available illustration of what the refusal is buying, and I would put it in front of anyone who thinks refusal #6 is excessive caution.

**5. Round-robin sports timetabling has a formal three-field grammar for scheduling problems.** RobinX classifies any round-robin problem as tournament-format / constraints-in-use / objective, with a queryable archive on top. It has 3 stars and no license file. A classification notation for scheduling constraints is exactly what §16 would call a named middle between "what the director asked for" and "what the model encodes" — and it exists, in obscurity, for sports fixtures.

**6. Nurse rostering is where counterfactual scheduling explanations actually got built.** XCP-explain's worked example answers "what would have to change for this nurse to get that weekend off" — the same sentence a parent asks a band director, on a problem shape with the same skills-plus-availability structure as the chaperone problem. Health-care rostering, not education, is where the explanation tooling matured.

---

## Gaps — what the exhausted search budget cost

Three lines I intended to pursue and did not, listed so they are not mistaken for dead ends:

1. **Court docket scheduling.** Wanted for its treatment of *entitlement to a date* and of continuances — the closest institutional analogue to I-6's "every ask gets a dated disposition." Not searched.
2. **School-choice assignment mechanisms as deployed** (Boston, NYC, Amsterdam), and their public fairness debates over lottery versus priority. `fairpyx` and `matching` are the code-shaped edge of this; the deployment write-ups and the political arguments are where the real material is. Only partially covered.
3. **Prison and hospital visitation scheduling.** Wanted specifically because visitation systems allocate scarce slots to *people with a relationship to a person in custody*, which is a guardianship-shaped constraint. Searched once, found nothing, budget ran out before I could rephrase.

One further verification debt, small but real: Temoa's and KidneyExchange's licenses were not read this pass, and the Timefold Community/Enterprise **feature** split could not be fetched. None of those three is a recommended adoption, so the debt is tolerable — but the Timefold split must be verified by whoever evaluates it, not inherited from this document.
