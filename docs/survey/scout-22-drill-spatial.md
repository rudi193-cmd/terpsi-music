# Scout 22 — The field as a coordinate system

Slice: drill, dot books, spatial layout, and the propagation problem when a person disappears
from a formation.

Read before searching: `docs/CAPABILITY-MAP.md` §9 (Design and execution / Concerts) and §20
(Roster churn); `docs/ARCHITECTURE.md` §13 bullet *"Can `field-acoustics` and commentary share
coordinates?"*, §8.1–8.2 (commentary primitive), §15 (`P1–P5`), §16 (`docs/ARCHITECTURE.md:1215`
— *"Commentary claim ↔ acoustic prediction (§13) | Shared coordinates, so they can disagree in a
queryable way"*); `CLAUDE.md`.

## Method and its limits — read this before trusting a row

- **`mcp__github__get_file_contents` is blocked in this session.** It returns
  `Access denied: repository "..." is not configured for this session. Allowed repositories:
  rudi193-cmd/terpsi-music`. Every file I read came from `raw.githubusercontent.com` via WebFetch
  or from `mcp__github__search_code` fragments.
- **`mcp__github__search_code` works globally** and is the workhorse here. `search_repositories`
  ANDs every term across name/description/README, so 3+ word queries silently return
  `total_count: 0` — several of my nil results below are query artifacts, not absence, and I say
  so where that is a live risk.
- **WebSearch budget exhausted, as instructed.** Nothing outside github.com /
  raw.githubusercontent.com was reachable. This specifically blocks the non-GitHub half of the
  proprietary-format question (vendor sites, marching-arts forums, Ultimate Drill Book / Field
  Artist docs).
- **Tags.** `[repo]` = I fetched source or doc text from that repository. `[inference]` = I have
  the repository's search metadata (name, description, stars, language, dates, archived flag) but
  did **not** open a LICENSE file or the source I am characterising.
- Star counts and dates are as returned by the GitHub search API on **2026-07-30** and are the
  only figures in this document; I derived none of them from a tree.

---

## Ranked table

| # | Project | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | `OpenMarch/schema` [repo] | **Format** + Zod/JSON-Schema validator for marching-arts show data (`.om`/`.omz`/`.omt`) | Apache-2.0 | Created 2026-01-09, pushed 2026-05-22, 0 stars, TS | §9 drill chart distribution; per-student coordinate lookup | **adopt** |
| 2 | `OpenMarch/OpenMarch` [repo] | **Application** — drill-writing editor, SQLite `.dots`, per-marcher coordinate-sheet PDF, mobile dot-book upload | AGPL-3.0 | 88 stars, pushed 2026-07-27, 135 open issues, TS/Electron | §9 drill revisions, dot books, coordinate sheets | **steal-the-idea** (schema + shapes; not the app) |
| 3 | `skybrush-io/studio-blender` [repo] | **Application/addon** — storyboard of formations, transition mapping, min-distance + max-velocity validation | GPL-3.0-or-later | 85 stars, pushed 2026-07-28, Python | Transition feasibility; spacing/collision; the hole in the drill as data | **steal-the-idea** (cloud matcher disqualifies adoption) |
| 4 | `salsa-rs/salsa` [repo, license inferred] | **Library/framework** — demand-driven incremental recomputation, red-green, durability | Apache-2.0/MIT [inference] | 2919 stars, updated 2026-07-29, Rust | **The propagation problem** — which coordinate sheets are stale | **steal-the-idea** |
| 5 | `Universite-Gustave-Eiffel/NoiseModelling` [repo] | **Application + Java library** — outdoor propagation (CNOSSOS-EU), GIS-native receivers, full source-directivity subsystem | GPL-3.0 | 229 stars, pushed 2026-07-28, Java | `field-acoustics`; the `ASSUMED` rear hemisphere | **steal-the-idea** (physics aimed elsewhere) |
| 6 | `ros2/geometry2` (tf2) [repo, license inferred] | **Library** — named coordinate frames, timestamped transforms, `canTransform(...)` with a reason string | BSD-3-Clause [inference] | Active, C++/Python | §13 judge's seat ↔ acoustic frame, **disagreeing queryably** | **steal-the-idea** |
| 7 | `floodlight-sports/floodlight` [repo] | **Library** — `XY` (many bodies × frames), `Pitch.from_template`, `Teamsheet`, Voronoi space control, velocity/acceleration | MIT | 126 stars, pushed 2026-05-04, Python | Spatiotemporal representation; spacing; identity↔column indirection | **adopt** (as a model; Python) |
| 8 | `PixarAnimationStudios/OpenUSD` [repo, license inferred] | **Format + library** — layer composition, sparse overrides, **Layer Offset**, TimeSamples | Modified Apache-2.0 [inference] | 7409 stars, updated 2026-07-29, C++ | Drill revisions as overlays; **music cuts as time offsets** | **steal-the-idea** |
| 9 | `OSGeo/PROJ` [repo, license inferred] | **Library** — coordinate operations carrying accuracy, and the **"Ballpark transformation"** concept | X/MIT [inference] | 2001 stars, updated 2026-07-30, C++ | §15 `P1–P5`; `CLAUDE.md` #13 absence-as-`unknown` | **steal-the-idea** |
| 10 | `netbox-community/netbox` [repo] | **Application** — `RackElevationSVG`, cable-trace SVG, power feeds, all rendered from a relational model | Apache-2.0 | 21215 stars, updated 2026-07-30, Django | §9 pit setup diagrams, cable runs, load-in; §9 riser configs | **steal-the-idea** |
| 11 | `penrose/penrose` [repo] | **Application/library** — Domain/Substance/Style; `ensure` (hard) vs `encourage` (soft), numerically optimised layout | MIT | Active [inference], TypeScript | Declarative pit/stage/riser diagrams from structured data | **steal-the-idea** |
| 12 | `PedestrianDynamics/jupedsim` [repo] | **Library** — `JourneyDescription` over waypoint/queue/exit stages, collision-free speed model | LGPL-3.0 | 86 stars, pushed 2026-07-27, C++20 + Python | §9 gate and hold-area movement plans; stadium egress | **read-only-interest** |
| 13 | `snowleopard/build` [repo, license inferred] | **Research artifact** — *Build Systems à la Carte*: scheduler × rebuilder taxonomy, verifying vs constructive traces | MIT [inference] | 275 stars, updated 2026-06-22, TeX/Haskell | Naming what the propagation engine **is** (`CLAUDE.md` #18) | **read-only-interest** |
| 14 | `TimelyDataflow/differential-dataflow` [repo, license inferred] | **Library** — incremental view maintenance over changing collections | MIT [inference] | 2992 stars, updated 2026-07-29, Rust | Propagation, if the drill is modelled as a relation | **read-only-interest** |
| 15 | `jackdpage/pylux` [repo] | **Application** — console export → SVG plot + Jinja-templated paperwork | GPL-3.0 | 7 stars, updated 2026-07-11, Python | §9 stage plots and generated paperwork | **read-only-interest** |
| 16 | `microsoft/LabanotationSuite` [inference] | **Application/research** — Kinect → Labanotation → robot gesture | MIT [inference] | 51 stars, updated 2026-06-07, JS/Python | Movement notation, **limb orientation not field position** | **read-only-interest** |
| 17 | `chengji253/RVO2-python` [inference] | **Library** — ORCA reciprocal velocity obstacles | Apache-2.0 [inference] | 64 stars, updated 2026-07-04, Python | Collision-free transitions between sets | **read-only-interest** |
| 18 | `Marc-AntoinePlourde/ShapeBookMaker` [inference] | **Script** — "shape book for the staff or … a series of dot book for each of the players" | none seen [inference] | 0 stars, created 2026-01-23, Python | Dot books | **read-only-interest** (evidence of demand, not a dependency) |
| 19 | `PawanGu/iso9613` [inference] | **Research prototype** — ISO 9613-1/-2 reference implementation + Streamlit | none seen [inference] | 0 stars, created 2026-05-25, Python | Outdoor propagation, simpler than CNOSSOS | **read-only-interest** |
| 20 | `skybrush-io/libskybrush` [inference] | **Library** — C parser for the Skybrush binary show format | not checked | 1 star, updated 2026-07-27, C | A precedent for a compact binary trajectory container | **read-only-interest** |

---

## Top finds, with the transplant and the cost

### 1. `OpenMarch/schema` — the open drill format exists, and its shape is already the shape this repo demands

This is the single most consequential correction to the premise. There **is** an open, versioned,
Apache-2.0 interchange format for marching drill. `README.md` describes it as *"the OpenMarch
Universal Standard"* and explicitly positions it as MusicXML's analogue for performer
coordinates: a standard that lets tools be built without OpenMarch itself. It ships
`schema.json`, a narrower `schema-tempo.json`, a Zod source of truth in `src/schema.ts`, a
`scripts/validate.ts`, and a `SCHEMA_VERSION` carried in-band as `omSchemaVersion`. Containers:
`.om` (plain), `.omz` (gzip, sniffed on read), `.omt` (tempo only), with `.omp` — a package
bundling show data, audio and images — marked *"Coming soon."*

The top-level fields are `omSchemaVersion`, `metadata`, `performers`, `pages`, `tempoSections`,
`coordinates`, `measures`. What matters for us is that **`coordinates` is a flat array of
`{marcherId, pageId, xSteps, ySteps, rotation_degrees?}`** — one row per person per set, sparse,
addressable, with no roster column anywhere. That is `CLAUDE.md` #8 already satisfied by an
outside format: a set is not a row with 150 columns, it is 150 rows sharing a `pageId` referent.
A `performer` carries `{id, label, section, name?, notes?}`; a `page` carries
`{id, duration, startBeatIndex, name, isSubset?}`; `measures` carry `rehearsalMark`. The
coordinate frame is declared once in `metadata.performanceArea` (field dimensions, checkpoints,
origin) and coordinates are **steps from the origin, not pixels** — so the frame is data, not a
rendering assumption.

**Transplant.** Adopt the format as the on-disk and interchange representation for `Chart`/`Drill`
(`ARCHITECTURE.md:687`). Two properties fall out for free that we would otherwise argue about:
`label` is separate from `name`, which is exactly the chosen-name-versus-SIS-record split in §20,
and `rehearsalMark` on measures is the same anchor the commentary primitive wants (§8.1 —
*"measure 112, at the tempo change"* is the addressable unit). The `startBeatIndex` +
`tempoSections` model means a coordinate and a judge's remark can both be anchored to a beat
index rather than wall-clock, which is the join §13 is asking for.

**Cost.** Small and mostly honest. It is a **young, unproven format**: created 2026-01-09, last
pushed 2026-05-22, zero stars, zero forks, one contributing organisation. Treat §14's "Exists"
discipline as applying here too — this is a claim to check, and `CLAUDE.md` #12 applies the
moment we vendor it: a copy of `schema.json` in our tree plus our own validator is a pair, and
the middle is a conformance test that reads the upstream `SCHEMA_VERSION` and fails on drift. The
format also has **no notion of provenance, sealing, or `invalid_at`** — it is a design document,
not a record, so everything in §8.2's `draft | sealed | pending` cascade and `CLAUDE.md` #3 has
to be added by us on our side of the boundary.

### 2. `OpenMarch/OpenMarch` — the shapes to copy, and one defect to copy nothing from

The editor is AGPL-3.0, TypeScript/Electron, 88 stars, pushed 2026-07-27. Its SQLite schema
(`apps/desktop/electron/database/migrations/schema.ts`) is the most useful artifact in this whole
slice, because it is a working answer to *how do you store a drill*.

`marchers` carries `drill_prefix` and `drill_order` — the identity-to-drill-label indirection.
`pages` carries `start_beat` and `is_subset`. `marcher_pages` is the coordinate table and the
schema comment states the invariant plainly: *"There should be a MarcherPage for every Marcher
and Page combination (M \* P)."* It carries `x, y, rotation_degrees`, plus a path model —
`path_data_id → pathways.path_data`, `path_start_position`, `path_end_position`, with a CHECK
constraint pinning those to `[0,1]`. `midsets` hangs off `marcher_pages.id` with its own
`x, y, progress_placement` — an intermediate position partway through a transition, i.e.
keyframes between keyframes. `shapes` / `shape_pages` (an `svg_path`) / `shape_page_marchers`
(with `position_order`) model a form as a curve plus an ordered assignment of people onto it.
`field_properties` stores the coordinate system as `json_data` plus an optional background image
blob. Undo is **statement-level, via SQL triggers**: `history_undo` / `history_redo` /
`history_stats` store reverse SQL keyed by a `history_group`, and `transactionWithHistory`
asserts *"the group was not changed by the function"* and that it incremented exactly once.

Distribution is real, not aspirational. `apps/desktop/src/components/exporting/` contains
`MarcherCoordinateSheet.tsx`, `CoordinateSheetTemplates.tsx` and `ExportCoordinatesModal.tsx`,
which build per-marcher SVG pages through a `ReadableCoords` class and emit *"PDF files for each
marcher or a single overview PDF."* That is per-student coordinate lookup and printed dot books,
already built. Separately, `apps/desktop/src/components/mobile/` converts the local database to
the open schema (`dots-to-om.ts` → `toCompressedOpenMarchBytes`) and **uploads it as a revision**
via `postApiEditorV1ProductionsProductionIdRevisions`, with `RevisionsList`, and checksum-based
sync so audio and background images are not re-uploaded per revision
(`audioSyncOnUpload.ts`, `backgroundImageSyncOnUpload.ts`). So drill revisions are a
first-class, listable, server-side object — which is §9's *"show design versioning"* in working
code.

**Transplant.** Take four shapes verbatim and write none of them from scratch: (a) the M×P
coordinate table with a stated invariant; (b) `pathways` + `path_start/end_position` +
`midsets`, which is a compact, storable answer to "how did they get there" without a general
animation engine; (c) `drill_prefix`/`drill_order` as the label indirection, so a dot sheet reads
`T7` while the record is a named person in their own lane; (d) the checksum-sync pattern for
revisions, which is how you distribute a rewritten drill over a stadium's non-existent bandwidth
(§22 item 8, genuine offline operation).

**Cost, and a hard stop.** Three things.

First, **the revision server is not open source.** The desktop client calls
`/api/editor/v1/productions/{id}/revisions` against `OPENMARCH_APP_BASE_URL`; there is no server
repository in the `OpenMarch` organisation — the org contains exactly `OpenMarch`, `schema`,
`plugins`, `.github`, and three archived repositories (`om-schema` MIT, `website`,
`musicxml-parser`). So the mobile dot-book path as shipped is a **hosted upload of student
positions**, which is a §6 egress question, not a feature. We would build that half ourselves.
The per-marcher PDF export path, by contrast, looks entirely local.

Second, **`electron/database/repair.ts` is a direct violation of `CLAUDE.md` #3**:
`DELETE FROM marcher_pages WHERE marcher_id NOT IN (SELECT id FROM marchers)` and the matching
statement for `page_id`. Removing a marcher removes their coordinate history. For a drill editor
that is defensible; for a system holding minors' education records it is exactly the
delete-instead-of-`invalid_at` that §7.1 exists to prevent, and it is the case a court order
arriving mid-season proves. **If we take the M×P table, we must invert this: a departed student's
`marcher_pages` rows get `invalid_at`, and the schema comment becomes "there should be a
MarcherPage for every (Marcher, Page) combination that was ever valid."** That also satisfies
`CLAUDE.md` #16 — the record of the drill they were in outlives their membership in it.

Third, AGPL-3.0 on the editor. The format (Apache-2.0) is the part to depend on.

### 3. `skybrush-io/studio-blender` — the closest working analogue to a drill, and why we cannot use it

A GPLv3 Blender addon for *"designing and validating drone shows"*: 85 stars, pushed 2026-07-28.
Structurally it is a drill writer with different bodies. `StoryboardEntry`
(`src/modules/sbstudio/plugin/model/storyboard.py`) is a set: `frame_start`, `duration`,
`frame_end = frame_start + duration - 1`, a `formation` reference, and — the interesting fields —
`transition_type` (`MANUAL`, *"maps nth vertex to nth vertex"*, vs `AUTO`, *"finds optimal
mapping"*), `transition_schedule` (`SYNCHRONIZED` | `STAGGERED`),
`transition_velocity_profile` (`LINEAR`, `SMOOTH_FROM_LEFT`, `SMOOTH_FROM_RIGHT`, `SMOOTH`),
`pre_delay_per_drone_in_frames` / `post_delay_per_drone_in_frames`, a `schedule_overrides`
collection of per-body departure/arrival adjustments, and a `locked` flag. Transitions are
implicit in the gap between consecutive entries.

Two things here are worth more than the rest of this report combined.

**The `mapping` field.** Stored as JSON, documented as *"Mapping where the i-th element is the
index of the drone that marker i was matched to"* — **or `-1` if unmatched.** That is the hole in
the drill, as a first-class, queryable value. When a student quits, you do not have a missing row
or a null coordinate; you have a *form position with no body assigned*, which is precisely the
object a director needs to see and precisely the object a downstream coordinate sheet must be
able to report as affected. Every other representation I found either drops the position or
drops the person.

**`RecalculateTransitionsOperator` and its `scope` enum.** `ALL`, `CURRENT_FRAME`, `TO_SELECTED`,
`FROM_SELECTED`, `FROM_SELECTED_TO_END`, and it skips `locked` entries. This is a hand-rolled,
human-chosen invalidation scope: the designer tells the tool how far the damage spread. It is the
naive version of the propagation problem, and its existence in a mature tool is the strongest
evidence I have that **nobody has built the non-naive version.** It is also the perfect foil for
finding #4.

The safety subsystem is the transition-feasibility answer:
`src/modules/sbstudio/plugin/model/safety_check.py` and the matching panel inspect *"the minimum
distance and maximum velocity of the drones in the current Blender frame"*, and the docs state
the overlay *"always shows you the minimum distance between all drone pairs on the current frame.
This drone pair is also highlighted with red, along with a red line connecting them."* There is a
`get_proximity_warning_threshold`, an altitude warning, and `use_custom_spacing` on takeoff/land
formations. Min pairwise distance + max velocity per frame **is** "can 150 people get from set 12
to set 13 in 16 counts without colliding," expressed as two scalars you can assert on.

**Transplant.** Steal the storyboard entry's field list, the `mapping` array with `-1`, the
per-body `schedule_overrides`, and the two-scalar safety check evaluated per count. The safety
check in particular is directly testable in the `CLAUDE.md` #19 sense: a guard that computes
min-pairwise-distance can be shown to fail by moving two dots together.

**Cost, stated bluntly.** `AUTO` transition matching is **not local**.
`src/modules/sbstudio/plugin/operators/recalculate_transitions.py` contains the comment
*"# Auto mapping with our API"* and the call `get_api().match_points(source, target, radius=0)`;
`src/modules/sbstudio/api/studio.py` is an HTTP client (`self._send_request("queries/version")`)
against the Skybrush Studio server, raising `SkybrushStudioAPIError`. **The repository's README
does not disclose this** — it describes GPLv3 free software and mentions no hosted service. So
the optimiser, the one genuinely hard algorithm, is a cloud call. For us that is not a licensing
inconvenience, it is `CLAUDE.md` refusal #1: shipping 150 students' field positions to a third
party to compute who goes where. **The pattern is adoptable; the code path is not, and the
`MANUAL` path is the only one we could run.** Note also that computing an optimal assignment
between two sets of dots is a linear-assignment problem with well-known local solutions, so this
is a build, not a research project.

### 4. `salsa-rs/salsa` — the actual answer to the propagation problem

2919 stars, Rust, updated 2026-07-29. A framework for *"on-demand, incrementalized
computation"* — the engine under `rust-analyzer`. Concepts, from `book/src/overview.md`: `inputs`
(the base facts), `tracked functions` that *"monitor which inputs they access and memoize
results"*, `tracked structs`, `interned structs` for identity-cheap equality, and `accumulators`
as *"a side-channel mechanism for reporting errors or metadata separate from a function's main
return value."* The rebuild decision is *"called the red-green algorithm, and it's where the name
Salsa comes from."*

Map it onto the drill directly. Inputs: the drill revision, the roster, each student's
enrollment interval. Tracked function: `coordinate_sheet(student, revision) -> Sheet`, which
reads only the `coordinates` rows for that student. Now the propagation problem is solved by
construction and — this is the part no drill tool does — **solved with the right granularity in
both directions.** Rewriting sets 12–20 does not invalidate anyone's sets 1–11. And because
red-green re-verifies by comparing recomputed values rather than trusting timestamps, a rewrite
that happens to leave trumpet 7's dots untouched **leaves trumpet 7's sheet green**, so she is
not handed a reprint she does not need, and the "your dot book is stale" notification does not
go to 150 families when it should go to 40. That is the difference between a system that knows
which sheets are stale and a system that says "the drill changed, reprint everything."

Two further pieces earn their keep. `durability`
(`book/src/reference/durability.md`): *"Durability specifies the probability that an input's
value will change"*, and when a computation reads only high-durability inputs, *"if no high
durability input has changed, it can skip traversing their dependencies."* Field geometry, the
step size, the venue — `Durability::HIGH`. The roster — low. That is a cheap, declarative way to
stop a roster edit from walking the whole graph. And `accumulators` are the natural home for
`CLAUDE.md` #13: a sheet whose rubric or consent backend failed to load accumulates an
`unavailable` diagnostic **beside** the value rather than returning an empty result.

**Transplant.** Not the crate — the algorithm and its vocabulary. Build the drill-to-sheet
relation as a memoized dependency graph with value-equality re-verification and per-input
durability, over whatever store we choose. Concretely: a `stale_sheets(revision)` query that
returns named students, and — per `CLAUDE.md` #19 — a test that rewrites one marcher's dots on
one set and asserts that exactly one sheet is reported stale and the other 149 are not. That test
is the acceptance criterion for this entire capability, and it is a mutation test, not a green
suite.

**Cost.** Real design work, and honesty about which of §16's shapes we are creating.
Cross-language: salsa is Rust, so if the app is not Rust we are reimplementing, and a
reimplementation of an upstream algorithm is a `CLAUDE.md` #12 pair whose middle is a
differential test against a reference. The graph must be persistent, not process-lifetime — salsa
assumes an in-memory database rebuilt per session, and we need "which sheets went stale while I
was asleep." And per `CLAUDE.md` #18: until sheet generation actually routes through this graph
it is a **ledger**, not enforcement, and must be described that way.

Read `snowleopard/build` (finding #13, 275 stars, updated 2026-06-22) before writing a line of
it — not for code, for names. *Build Systems à la Carte* factors every build system into a
**scheduler** × a **rebuilder**, and distinguishes **verifying traces** from **constructive
traces**. Being able to write "this is a suspending scheduler with a verifying-trace rebuilder"
in `docs/ARCHITECTURE.md` is exactly the precision §16 and `CLAUDE.md` #18 are asking for, and it
costs one afternoon of reading.

### 5. `NoiseModelling` + tf2 + PROJ — the answer to §13, assembled from three unrelated libraries

§13 asks whether `field-acoustics` and commentary can share coordinates, and §16's table
(`ARCHITECTURE.md:1215`) demands they *"disagree in a queryable way."* Nothing in the open does
this. Three libraries together say how.

**`NoiseModelling` supplies the acoustics and, unexpectedly, the `ASSUMED` rear hemisphere.**
GPLv3, Java, 229 stars, pushed 2026-07-28, maintained by UMRAE (Université Gustave Eiffel) and
Lab-STICC (CNRS). It implements CNOSSOS-EU, handles ground porosity, diffraction over vertical
and horizontal edges, and *"homogeneous and favorable"* meteorological conditions; receivers are
**point geometries or a regular/Delaunay grid in GIS tables**; it runs headless via CLI, as a
Java API, or through Groovy WPS scripts. The find is
`noisemodelling-emission/src/main/java/org/noise_planet/noisemodelling/emission/directivity/`:
a `DirectivitySphere` interface documented as *"Interface that returns the attenuation in dB due
to a specific directivity pattern"* at a given `(phi, theta, frequency)`, with implementations
`DiscreteDirectivitySphere` (a table of `DirectivityRecord`s — *"the attenuation value for a
specific angle (theta, phi) — a point of the directivity sphere"* — interpolated, and it degrades
to a zero-attenuation record when the lookup misses), `OmnidirectionalDirection`, a
`RailwayCnossosDirectivitySphere`, a `DIRECTIVITY` database table, and a `PlotDirectivity`
function that draws the polar graph. A marching brass player *is* a directional source, and this
is the exact data structure for one: a per-angle, per-frequency table whose rear hemisphere can
be populated by measurement or by assumption, **per record**. That means the `P1–P5` rung can
attach to individual directivity records rather than to the whole model — the front hemisphere
`MEASURED`, the rear `ASSUMED`, in one table, with §15's rule that the word `ASSUMED` is written
out satisfied by the rendering layer.

**tf2 supplies the queryable disagreement.** `ros2/geometry2` (note: `ros/geometry2` is
**archived** — the noetic-devel one; use the ros2 org). Its core is
`canTransform(target_frame, source_frame, time, error_msg)` alongside
`lookupTransform`, and the failure taxonomy is the whole point: `LookupException` (a frame I have
never heard of), `ConnectivityException` (two frames that exist but are not connected),
`ExtrapolationException` (a time outside what I hold), `InvalidArgumentException`. Model the
judge's seat as a named frame, the field origin as another, the pit and the press box as others.
Then *"was this remark and this prediction talking about the same place at the same instant?"* is
a `canTransform` call that either succeeds or returns a **named, distinguishable reason for
refusing** — not a null, not a silent zero. `ConnectivityException` is the honest answer when
nobody surveyed the seat; `ExtrapolationException` is the honest answer when the remark
timestamps outside the drill's beat range. That is §16's "disagree in a queryable way", and it is
also `CLAUDE.md` #13 with four distinct flavours of `unknown` instead of one.

**PROJ supplies the provenance vocabulary.** From `docs/source/glossary.rst`, a *Ballpark
transformation* aligns frames without attempting a datum shift, and *"Its accuracy is unknown,
and could lead in some cases to errors of a few hundreds of metres."* PROJ then makes that
label operational: `--no-ballpark` and `--hide-ballpark` refuse or hide such operations,
`--accuracy` sets a floor, `--only-best` / `errorIfBestTransformationNotAvailable` control
whether a degraded path is silently substituted, `--grid-check
none|discard_missing|sort|known_available` governs missing data, and
`PROJ_ERR_COORD_TRANSFM_NO_OPERATION` fires when *"no match the required accuracy, or if ballpark
transformations were asked to not be used and they would be only such candidate."* This is a
mature library that (a) attaches an accuracy in metres to every candidate coordinate operation,
(b) names the worst rung, and (c) offers a **caller-side switch between "serve it labelled" and
"refuse it."** §15 says provenance labels but never gates — *"the headline reads `ASSUMED`,
loudly, rather than the result being withheld"* — and PROJ is the counterexample worth arguing
with: it lets the caller choose per query, and that flexibility may be what an export gate
(`CLAUDE.md` #9) needs even if a screen does not.

**Cost.** This is three transplants, not a dependency. NoiseModelling is GPLv3 Java aimed at
road and rail traffic over city-scale terrain; running it for a stadium means treating each
player as a point source with a custom directivity table and accepting that **CNOSSOS's emission
models are irrelevant to us — only the propagation and directivity halves transfer.** tf2 is a
ROS 2 C++/Python library and pulling ROS into this application is absurd; take
`canTransform`-with-a-reason and the four exception types as an interface contract, which is
maybe 200 lines. PROJ we would use only if we ever relate field coordinates to real-world
geodesy (venue surveys, wind logs) — otherwise it is vocabulary. And per `CLAUDE.md` #14, none of
`L1–L5`, `T0–T4`, `P1–P5` may be compared as bare integers or coloured-only, so a directivity
record's rung needs the prefix and a glyph.

### 6. The two transplants nobody would search for: NetBox and Penrose for §9's diagrams

§9 asks for pit setup diagrams, load-in sequences, cable runs, stage setup and riser
configurations per piece. The domain-adjacent answer (`pylux`, finding #15, GPLv3, 7 stars) is
real but thin: it imports an ETC Eos console ASCII export — patch, groups, palettes, cues — and
renders an SVG plot from user-supplied fixture vector files plus *"plaintext documentation from
Jinja template files."* Good pattern, tiny project.

**`netbox-community/netbox` is the industrial-strength version of the same idea, and it is a
data-centre tool.** Apache-2.0, Django, 21215 stars, updated 2026-07-30. `netbox/dcim/svg/racks.py`
contains `class RackElevationSVG`, building a drawing with `svgwrite` sized from
`unit_width`, `legend_width`, `rack.u_height` and `RACK_ELEVATION_BORDER_WIDTH`;
`netbox/dcim/models/racks.py` exposes it as *"Return an SVG of the rack elevation"*, served at
`dcim-api:rack-elevation?face=...&render=svg` and lazily loaded per face (front/rear). There is a
parallel `cable_trace` SVG with its own stylesheet, downloadable, that renders a **traced path
through cables and termination points** rather than a drawn picture. Plus a
`devicetype-library` (1569 stars, 1368 forks) of community-contributed equipment definitions.

Translate the nouns: rack → riser or pit table; device type → keyboard, gong, sub, mixer; cable
with A/B terminations → an XLR or power run; cable path tracing → "what is this snake channel
plugged into and where does it land"; power feed with utilisation → the venue's available
circuits versus what the pit draws. Riser configurations per piece are rack elevations per
production. And the deliverable is the point: **a downloadable SVG rendered from the relational
model, so the pit diagram cannot drift from the equipment inventory** — which incidentally closes
a §16 pair we would otherwise create between "the inventory" (§5 of the capability map) and "the
setup diagram."

**`penrose/penrose`** (MIT, TypeScript) is the other half. Its three-language split — Domain
(the abstract types and predicates), Substance (the concrete instances: *these* twelve
instruments, *these* four cable runs), Style (shapes plus layout rules) — with `ensure` for hard
constraints and `encourage` for soft objectives, and layout produced by **numerical optimisation
rather than a hand-placed template.** `ensure` a three-foot aisle and no cable crossing a
walkway; `encourage` keyboards stage-left and even spacing. The same `ensure`/`encourage`
distinction is the right vocabulary for drill spacing too: *ensure* two steps of interval,
*encourage* even distribution — and it makes explicit which failures are violations and which are
preferences, a distinction `CLAUDE.md` #18 would call the difference between a gate and a
suggestion.

**Cost.** NetBox is a whole Django application; we would take the model shape and the
`svgwrite`-from-data pattern, not the dependency — call it a week to have riser and cable-run
SVGs generated from the equipment tables, and it composes with `CLAUDE.md` #11 because a diagram
is a derived sidecar, never canonical. Penrose is a genuine dependency if used, browser-oriented,
and its optimiser is nondeterministic enough that a printed load-in diagram should be pinned once
generated rather than re-solved on every view.

### 7. `floodlight` — the spatiotemporal model, and the identity-to-column problem named

MIT, Python, 126 stars, pushed 2026-05-04, out of the German Sport University's data science
group. Core objects: `XY` (a positions matrix for many bodies over frames), `Pitch`, `Teamsheet`,
`Code`, `Events`, loaded from six commercial tracking vendors' formats into one representation.
Models: `kinematics.DistanceModel` / `VelocityModel` / `AccelerationModel` (with a `difference`
parameter, `'central'` or `'forward'`), `kinetics` (metabolic power),
`geometry.CentroidModel`, and `space.DiscreteVoronoiModel` — a tessellation on a hexagonal or
rectangular mesh where *"Euclidean distance is used, which corresponds to a classical Voronoi
tessellation. Alternatively, motion-based models can be selected that account for player velocity
and acceleration."*

Three transplants. **`Pitch.from_template("dfl", length=..., width=..., sport=...)`** — the
coordinate frame is a *named template* with dimensions, and the library's entire reason for
existing is converting between vendors' incompatible pitch frames. That is `field_properties` done
right, and it is the same problem as an NCAA field versus a high-school field versus an indoor
floor. **`Teamsheet`** is the mapping from a person's identity to their column index in the `XY`
matrix — the indirection that `OpenMarch`'s `drill_prefix` also encodes, here named as its own
object. It is worth naming because when a student quits, the `Teamsheet` changes and every stored
`XY` matrix's column layout is now ambiguous; making that a first-class object rather than an
implicit convention is what stops a silent off-by-one from handing trumpet 8 trumpet 7's dots.
**`DiscreteVoronoiModel`** on the motion-based setting is a spacing and interval analysis: whose
region collapsed, where the form is crowded, computed from positions plus velocities rather than
distances alone.

**Cost.** Low, and the value is the model more than the code. It is Python, MIT, small, and
assumes a fixed frame rate over continuous tracking data rather than sparse keyframes at set
boundaries — so we would interpolate our sets into an `XY` before using the models, which is
exactly what `midsets` and `pathways` (finding #2) already describe how to do. Its `Pitch`
templates are all sports fields, none of them a marching grid in 8-to-5 steps; adding one is
trivial.

### 8. OpenUSD — a music cut is a Layer Offset, and a drill revision is a sparse override

7409 stars, C++, updated 2026-07-29. I include it for one idea that reframes §9's *"show design
versioning: drill revisions, music cuts, effect changes"* as a solved problem in a different
industry.

USD composes a scene from a stack of **layers**, where a weaker layer supplies the base and a
stronger layer contributes sparse `over` opinions on just the properties it changes. A drill
revision is that: not a new copy of the drill, and not a diff you have to apply, but an overlay
that says *these eleven marchers on these nine sets*, resolved at read time. Whose opinion won is
inspectable — `UsdProperty::GetPropertyStack` returns the contributing layers, though the
docstring is emphatic that it *"should only be used for debugging/diagnostic purposes, not for
value resolution … since the makeup of an attribute's PropertyStack may itself be time-varying"*,
so it is an audit trail rather than a fast query. And the piece I did not expect: a sublayer
reference can carry a **Layer Offset**, described in `docs/glossary.rst` as *"an offset and
scaling of time to be applied during attribute value resolution for all data composed from the
target layer."* **A music cut is a Layer Offset.** Cutting sixteen bars does not require rewriting
every coordinate's beat index; it is a time offset and scale on the layer, composed at read.
Alongside that, positions are `TimeSamples` and interpolation is a stage-level property
(`SetInterpolationType` / `GetInterpolationType`, held versus linear).

**Cost.** Do not take the dependency. OpenUSD is an enormous C++ VFX runtime, its licence is a
modified Apache-2.0 with its own conditions [inference — I did not open the file], and
`aousd/specifications-public` (4 stars, created 2026-06) shows the normative spec effort is only
just beginning. Take three ideas: revisions as sparse overlays rather than copies; a musical cut
as a time offset on a layer rather than a rewrite of every anchor; and a diagnostic
"which revision set this coordinate" query that is explicitly *not* the fast path.

---

## What does NOT exist in the open. Bluntly.

1. **No open reverse-engineering of any proprietary drill format.** Not Pyware 3D's `.3dj`, not
   its production files, not Field Artist, not Ultimate Drill Book. Searches for `pyware`, `3dj`,
   and combinations across GitHub code returned nothing but SEO spam pages, expired-domain
   wordlists, and coincidental substring hits. There is no `libpyware`, no format note, no
   partial parser. The dominant tool in this domain has a **completely closed file format with no
   open reader, and no one has tried.** Caveat: GitHub code search covers indexed default
   branches, and WebSearch was unavailable, so a forum thread or a gist could exist beyond my
   reach — but a maintained project would have surfaced.
2. **No open tool or format for set-by-set rehearsal marking and cleaning tracking.** §9 asks for
   it; nothing in the open does it, in-domain or by analogy. `OpenMarch` has `notes` fields on
   `marcher_pages` and `pages` and nothing more. This is greenfield, and it is small: a
   (set, section-or-student, session, state) table with a dated disposition per `CLAUDE.md` #15.
3. **No open drill-revision propagation or staleness engine.** This is the finding. The best
   in-domain tool (`studio-blender`) asks the human to choose a recalculation scope from a
   five-item enum. Nothing computes which downstream coordinate sheets are stale. Nothing in
   marching, dance, choreography, drone-show, crowd-simulation, or theatre tooling treats a
   spatiotemporal document as a dependency graph. **The technique is mature and lives entirely in
   build systems and compilers** (findings #4, #13, #14) and has never been pointed at a
   formation. §22 could plausibly gain an eleventh entry.
4. **No open parade or marching-order planning tool.** Nil results, and the query was simple
   enough that I believe it.
5. **No coordinate bridge between an adjudicator's position and an acoustic prediction, anywhere,
   in any domain.** The acoustics (NoiseModelling) and the frame algebra (tf2) exist as separate
   mature libraries with no connection between them. §13's question has no prior art; the claim
   §13 says *"no drill designer can currently make"* is correctly stated.
6. **No open outdoor propagation model built for musical sources.** CNOSSOS-EU is road and rail;
   ISO 9613-2 assumes point sources and neutral-to-downwind conditions. The
   `DirectivitySphere` machinery transfers; the emission models do not. A marching ensemble as a
   moving array of directional sources over a grass field into a raked stand is not modelled by
   anything published.
7. **No open dot-book application.** Two toy repositories exist
   (`Marc-AntoinePlourde/ShapeBookMaker`, 0 stars, created 2026-01;
   `blackpearlrgh/marching-band-dot-book`, a 2015 Google Code export). The real ones are
   proprietary phone apps. `OpenMarch`'s per-marcher PDF export is the only working open path,
   and its *mobile* path routes through an unpublished server.
8. **Dance notation does not solve this, and I want to be clear about why.** Labanotation has
   real digital implementations — `microsoft/LabanotationSuite` (51 stars), `furylynx/MAE` (a C++
   Movement Analysis Engine), `koke1997/LabanCompiler` (video → Labanotation),
   `dancescores/LabanLite` (an ASCII-safe linear encoding), several Unity and Three.js
   visualisers, and a cluster of pose-estimation-to-Laban research prototypes. Every one of them
   notates **a single body's limb orientation, support and level over time**, because that is
   what the notation is for and what robot-gesture research wants from it. Labanotation's floor
   plan is a secondary staff and none of the digital implementations model it as queryable data.
   **For 150 bodies' positions on a field, the notation systems are the wrong tool and the sports
   and swarm libraries are the right one.** I chased this hard because the brief asked me to; the
   honest answer is that it is a dead end for this slice, and a live one for anyone modelling
   colour guard body work.

---

## Gaps — what I could not verify

- **`get_file_contents` was blocked all session** (repo allowlist: `rudi193-cmd/terpsi-music`).
  I could not list directory trees. Everything is from `raw.githubusercontent.com` fetches and
  `search_code` fragments, so my picture of each repository's layout is inferred from paths that
  happened to match a query.
- **Licences I did NOT confirm from a LICENSE file** — all marked `[inference]` in the table and
  asserted from ecosystem convention only: `salsa`, `differential-dataflow`, `snowleopard/build`,
  `ros2/geometry2`, `OSGeo/PROJ`, `OpenUSD`, `LabanotationSuite`, `RVO2-python`. Confirm before
  any of these enters a dependency list or an exit-plan line (§11.1). PROJ and OpenUSD in
  particular have non-standard licence texts.
- **`penrose/penrose` activity is unverified.** I fetched its README (MIT, `ensure`/`encourage`
  confirmed) but the repository never appeared in a `search_repositories` result, so I have no
  star count, push date, or archived flag for it. Treat "active" as unsupported.
- **`OpenMarch/OpenMarch` `packages/path-utility` is unread.** The raw README 404'd. I know the
  package exists (`config`, `core`, `metronome`, `musicxml-parser`, `path-utility`, `ui`) and that
  `pathways.path_data` holds path geometry, but I have not seen its segment types or its
  interpolation API. This is the piece most likely to matter for midset interpolation.
- **`libskybrush`'s binary trajectory format is unread** — I have only its one-line description.
  If a compact on-wire format for many bodies' trajectories is wanted, that is the next thing to
  open.
- **I did not verify whether OpenMarch's coordinate-sheet PDF export is fully offline.** The code
  path looks local (SVG built in-renderer, PDF written by a utility process) but I did not trace
  it end to end. The mobile path is unambiguously a server upload.
- **I did not check whether `OpenMarch/schema` is published to npm/PyPI**, nor read
  `OpenMarch/plugins` (1 star) which may be the extension point that matters most for us.
- **Fleet repositories were out of reach.** `CLAUDE.md` says fleet repos are read through the
  GitHub API, but this session's allowlist blocks them, so I could not read `field-acoustics`
  itself — its three provenance rungs, its `ASSUMED` rear hemisphere, or whether it already has a
  coordinate frame. **Every claim I make about how these findings fit `field-acoustics` is derived
  from `docs/ARCHITECTURE.md` prose, not from that repository's source.** §18 item 0 applies with
  full force.
- **WebSearch unavailable**, so: vendor documentation for the proprietary tools, marching-arts
  forum reverse-engineering discussion, DCI/BOA/WGI circuit rule documents, and any
  non-GitHub-hosted format notes are all unchecked. My "no reverse-engineering exists" claim is a
  GitHub-scoped claim.
- **Crowd simulation is under-covered.** I verified JuPedSim. `Vadere` and `Menge` returned nil on
  multi-word queries, which is very likely a query artifact given the `search_repositories` AND
  behaviour — do not read those nils as absence.

---

## Weirdest things I found

1. **A data-centre inventory tool renders the pit setup.** `netbox-community/netbox`'s
   `RackElevationSVG` and its cable-trace SVG generate downloadable, styled diagrams from a
   relational model of racks, devices, cables with A/B terminations, and power feeds with
   utilisation. Swap "rack" for "riser" and "cable" for "XLR run" and §9's pit diagrams, cable
   runs and per-piece riser configurations are a solved problem with 21215 stars behind it. Plus
   a 1368-fork community library of equipment definitions, which is precisely the shape a
   shared instrument/equipment catalogue would want.
2. **A music cut is a Layer Offset.** OpenUSD's sublayer references carry *"an offset and scaling
   of time to be applied during attribute value resolution for all data composed from the target
   layer."* Cutting sixteen bars from the opener becomes a two-number annotation on a revision
   layer instead of a rewrite of every coordinate's beat anchor. A film-industry composition
   primitive is the cleanest available model for the single most disruptive edit in this domain.
3. **PROJ has a formal, named epistemic rung called a "Ballpark transformation"** — glossed as
   *"Its accuracy is unknown"* — plus `--no-ballpark`, `--accuracy`, `--only-best`, and an error
   code for *"no match the required accuracy."* A geodesy library has independently built §15's
   `P`-ladder, given the worst rung a memorable name, and made refusal-versus-labelling a
   caller-side switch. It is the best available argument with §15's own claim that provenance
   never gates.
4. **A hole in the drill already has a canonical representation, in drone-show software.**
   Skybrush's `mapping` array — *"the i-th element is the index of the drone that marker i was
   matched to"*, or **`-1` if unmatched** — is exactly the object §20's *"a hole in the drill"*
   describes. A form position that exists with nobody assigned to it, as data, queryable, per
   set. Every other representation I found loses either the position or the person.
5. **Sports analytics named the identity-to-column problem `Teamsheet`.** `floodlight` separates
   the `XY` positions matrix from the `Teamsheet` that says which column is which human, because
   six commercial vendors each order their columns differently. That indirection is the exact
   failure surface when a student quits mid-season and the matrix reshapes — and a soccer library
   built for reconciling vendor formats is where I found it named, along with a Voronoi space-control
   model that reads directly as an interval-and-spacing analysis.
6. **The best in-domain tool asks a human where the damage spread.** `studio-blender`'s
   `RecalculationScope` enum — `ALL` / `CURRENT_FRAME` / `TO_SELECTED` / `FROM_SELECTED` /
   `FROM_SELECTED_TO_END` — is a mature, well-engineered project's answer to the propagation
   problem, and it is "ask the designer." That absence, in the most sophisticated tool in the
   adjacent field, is the strongest single piece of evidence that the incremental-computation
   transplant is the real opportunity in this slice.
