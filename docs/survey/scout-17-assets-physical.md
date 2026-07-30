# Scout 17 — Physical Assets: thousands of objects, their condition, custody, and failures

Slice: instrument/equipment inventory, condition history, custody, repair, consumables, uniforms
piece-level, tagging, audits, load lists — on a phone, in a parking lot, offline.

Read first: `docs/CAPABILITY-MAP.md` §5, §6, §20 (operational disasters), `CLAUDE.md`.

---

## Method and its limits — read this before trusting anything below

Two constraints shaped this scout, and both matter for how much weight to put on each claim:

1. **The session's WebSearch budget was already exhausted** (200/200) when this slice started. Zero
   web searches were performed. Discovery was done entirely through the **GitHub search API**
   (repository search, code search) plus the **GitLab API**.
2. **The egress proxy only permits `github.com`, `raw.githubusercontent.com`, and `gitlab.com`.**
   Everything else was refused at CONNECT: `grocy.info`, `koha-community.org`, `docs.inventree.org`,
   `en.wikipedia.org`, `sourceforge.net`, `collectionstrust.org.uk`, and every asset-tag vendor host
   I probed (`camcode.com`, `metalphoto.com`, `zebra.com`, `atlasrfidstore.com`, `nfpa.org`).

Consequences, stated plainly rather than papered over:

- **Every license, feature, and activity claim about a project below was verified by reading the
  repository itself** — the `LICENSE` file over `raw.githubusercontent.com`, or the actual source
  file implementing the feature via GitHub code search. This is *stronger* evidence than the
  marketing pages I could not reach. Where a claim is from a README rather than an implementing
  file, it is marked "(README)".
- **The tag-technology section is engineering judgement, not sourced research.** I could not reach a
  single vendor datasheet, standard, or field study. That section is explicitly labelled and comes
  with the verification list someone must actually do before spending money. Per `CLAUDE.md` #17,
  I am not going to launder unverified numbers into prose.
- Star counts and dates are from the GitHub API **as of 2026-07-30**.
- Domains I hunted that turned out to be **open-source deserts** are reported as such in
  "The desert" — a null result is a finding, not a gap in the search.

---

## Ranked table

| # | Project | What it is | License (verified) | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Koha — offline circulation** ([Koha-Community/Koha](https://github.com/Koha-Community/Koha), `offline_circ/`) | ILS with a shipped, decades-old offline-checkout + queue-and-reconcile design | GPL-3.0-or-later | 579★, pushed 2026-07-29 | Parking-lot checkout/return; the reconciler | **steal-the-idea** (highest-value find) |
| 2 | **ODK Collect + Central** ([getodk/collect](https://github.com/getodk/collect), [getodk/central](https://github.com/getodk/central)) | Offline-first Android form capture; self-hosted server | Apache-2.0 | 777★ / 218★, both pushed within days | Annual audit walk; condition photos at issue/return; pre-performance checklists | **adopt** (field-capture layer) |
| 3 | **Snipe-IT** ([grokability/snipe-it](https://github.com/grokability/snipe-it)) | Mature IT asset management: checkout, audits with due dates, depreciation, labels | AGPL-3.0 | 14,552★, pushed 2026-07-30 | §5 catalog, audit workflow, depreciation, insurance schedule | **steal-the-idea** (model, not wholesale adopt) |
| 4 | **grocy** ([grocy/grocy](https://github.com/grocy/grocy)) | Household ERP; **battery tracking**, equipment, chores, consumables — PHP + SQLite | MIT | 9,312★, pushed 2026-07-30 | §5 consumables + **cable/battery tracking**; equipment manuals | **adopt** (consumables + batteries) |
| 5 | **InvenTree** ([inventree/InvenTree](https://github.com/inventree/InvenTree)) | Parts/stock system: serialized items, location tree, `minimum_stock` | MIT | 7,318★, pushed 2026-07-30 | Serialized instruments + consumable reorder thresholds | **steal-the-idea** (schema) |
| 6 | **Homebox** ([sysadminsmedia/homebox](https://github.com/sysadminsmedia/homebox)) | Single Go binary + SQLite inventory: QR labels, warranty, photos, `MaintenanceEntry` | AGPL-3.0 | 6,596★, pushed 2026-07-30 | Easiest self-host; repair history; warranty | **adopt-lite** / steal-the-idea |
| 7 | **Atlas CMMS** ([Grashjs/cmms](https://github.com/Grashjs/cmms)) | Self-hosted CMMS: work orders, parts, PM schedules, React Native app | AGPL-3.0 **+ commercial `LICENSE_KEY`** ⚠ | 708★, pushed 2026-07-29 | Repair tickets (vendor/cost/turnaround), preventive rotation | **steal-the-idea** (open-core — flagged) |
| 8 | **Loxya / Robert2** ([Loxya/Loxya](https://github.com/Loxya/Loxya)) | French **event/AV equipment rental**: per-event material lists, shortage alerts, damage on return | ⚠ **CC BY-NC-SA 4.0 — not open source** | 53★, pushed 2026-07-24 | Load lists, per-event manifests, damage-on-return | **read-only-interest** (license blocks reuse) |
| 9 | **html5-qrcode** ([mebjas/html5-qrcode](https://github.com/mebjas/html5-qrcode)) | In-browser camera QR/barcode decode, fully local | Apache-2.0 | 6,181★, pushed 2026-07-30 | Phone scanning with no signal | **adopt** (library) |
| 10 | **circulate** ([chicago-tool-library/circulate](https://github.com/chicago-tool-library/circulate)) | Real volunteer-run tool-library lending system | MIT | 107★, pushed 2026-07-08 | Volunteer-operated checkout UX; holds; fines | **steal-the-idea** |
| 11 | **lighterpack** ([galenmaly/lighterpack](https://github.com/galenmaly/lighterpack)) | Ultralight-backpacking gear lists with per-item **weights** and worn/consumable classes | GPL-2.0 | 807★, pushed 2026-07-29 | Load lists, trailer weight, "what leaves the building" | **steal-the-idea** |
| 12 | **zetavg/Inventory** ([zetavg/Inventory](https://github.com/zetavg/Inventory)) | React Native **UHF RFID** asset app on CouchDB/PouchDB | ⚠ **"All rights reserved" + hand-written exceptions — not open source** | 331★, pushed 2026-07-15 | Offline RFID audit on a phone | **read-only-interest** (license trap) |
| 13 | **shelf.nu** ([Shelf-nu/shelf.nu](https://github.com/Shelf-nu/shelf.nu)) | Asset management with QR tags, custody, bookings | AGPL-3.0 | 2,752★, pushed 2026-07-29 | Custody + booking model | **read-only-interest** (⚠ requires external Supabase — fails "one modest box, no cloud") |
| 14 | **CollectionSpace** ([collectionspace/services](https://github.com/collectionspace/services), `application`) | Museum collections mgmt: condition checks, location & movement control | ECL-2.0 (README) | Small but pushed 2026-07-09 | Condition reporting vocabulary; movement control | **read-only-interest** |
| 15 | **eLabFTW** ([elabftw/elabftw](https://github.com/elabftw/elabftw)) | Lab notebook + **Resources** (items) with bookings, QR, signed entries | AGPL-3.0 (README) | 1,385★, pushed 2026-07-30 | Chain-of-custody framing; item booking | **read-only-interest** |
| 16 | **NEED-PERC for Brass Band** ([Setakoma-Works/NEED-PERC-for-Brass-Band](https://github.com/Setakoma-Works/NEED-PERC-for-Brass-Band)) | Single HTML file: repertoire → percussion needs − owned = rental request | none stated ⚠ | 0★, pushed 2026-06-21 | Percussion planning per program | **steal-the-idea** (see Weirdest) |
| 17 | **OpenQuarterMaster** ([Epic-Breakfast-Productions/OpenQuarterMaster](https://github.com/Epic-Breakfast-Productions/OpenQuarterMaster)) | Modular inventory with storage-block model | GPL-3.0 | 73★, pushed 2026-07-24 | Storage-location modelling | **read-only-interest** |
| 18 | **trier-os** ([DougTrier/trier-os](https://github.com/DougTrier/trier-os)) | "Offline-first scan-to-execute" plant-floor PWA, SQLite | not verified | 17★, pushed 2026-07-04, created 2026-04 | Scan-to-execute phrasing | **read-only-interest** (too new/small to lean on) |
| 19 | **AVLedger** / **MyTailLog** ([Penaz89/AVLedger](https://github.com/Penaz89/AVLedger), [iiamit/MyTailLog](https://github.com/iiamit/MyTailLog)) | Aircraft maintenance logbooks (AD compliance, inspection intervals) | not verified; MyTailLog is Supabase-dependent | 0★ / 2★, 2026 | Airworthiness-style inspection intervals | **read-only-interest** (doctrine only) |
| 20 | **openMAINT** | Facility/asset CMMS often recommended for this shape | **could not verify** — lives on SourceForge, blocked | unknown | Repair + PM | **unverified — do not cite** |

---

## Top finds: concrete transplant and cost

### 1. Koha's offline circulation — the reconciler, already designed and already regretted

This is the single most valuable thing in the slice and it is not an adoption candidate. Koha is a
Perl ILS; nobody should run it to lend sousaphones. What it has is **thirty years of institutional
scar tissue on exactly the problem in the brief**: a volunteer at a desk, network down, items moving
in and out, and a database that must be correct afterwards. Verified in the tree at
`offline_circ/process.pl`, `offline_circ/enqueue_koc.pl`, `offline_circ/process_koc.pl`, plus a
documented `.koc` interchange format, and documented in the manual chapter I pulled from
`gitlab.com/koha-community/koha-manual` (`source/circulation.rst`, lines 3819–4100).

What to transplant, nearly verbatim:

- **Queued transactions are drafts until a human commits them.** The Koha tool offers two commit
  types: *"Send data to Koha"*, where "your account will need to be approved by an administrator",
  versus *"Apply directly to Koha"*. That is `CLAUDE.md` #10 already implemented in a shipping
  product. Terpsi should have exactly one of these paths for volunteers — send-for-approval — and
  reserve direct-apply for a named staff role.
- **Per-transaction dispositions, recorded durably, including the rejections.** Koha's processing
  sets each queued action to `"Success."`, `"Borrower not found."`, `"Item not found."`, or
  `"Item not issued."` (that last one means someone checked in an item that was never out). An audit
  trail that logs only the successes is not one (#10). Copy this status set almost directly:
  succeeded / student-not-found / item-not-found / item-was-not-out / conflicting-later-write.
- **Multi-device ordering is a real correctness bug, not a theoretical one.** The manual is blunt:
  if one device checks a book out and another checks the same book in, "you need to record the check
  out first and then the check in. Not the opposite! To do so, you need to group every transaction in
  one place, sort them all and then, process everything." Two volunteers with two phones at the
  equipment truck is the *normal* case, not the edge case. The reconciler must pool across devices
  and sort globally before applying — per-device sequential replay is wrong.
- **Offline cannot know what it cannot see, and must say so.** Koha documents that an offline check-in
  cannot confirm holds, so "the holds stay on the item and will need to be managed later", and that
  an expired patron card "won't know about it, so the checkout will be recorded regardless". This is
  `CLAUDE.md` #13 exactly: the offline path must return `unknown` for consent state, fee holds, and
  guardianship restrictions — never "no restrictions" — and flag the item for a human.
- **The hard-won negative result: browser LocalStorage is not a sufficient offline store.** Koha's
  built-in browser offline module "was deprecated in Koha version 23.11", with the reason stated
  twice in the manual: "The offline interface uses HTML LocalStorage, which depending on the browser
  and user setting, is limited to 2.5MB or 5MB per domain. This means that larger systems will not be
  able to synchronize their data." Terpsi's offline story must not be LocalStorage. Use IndexedDB
  (or SQLite via a wrapper) with an explicit quota and an explicit pre-download step, and treat the
  offline dataset as a deliberately scoped extract — today's roster and today's items — not a mirror.
- **The one thing to refuse to copy.** The manual recommends "a staff account dedicated to the
  offline circulation. So that, no matter who is at the circulation desk, they can all use the same
  login." That is a shared credential, and it annihilates per-actor attribution. In a system holding
  minors' records under `CLAUDE.md` #16 and §7's audit obligations, a shared offline login is a
  defect, not a convenience. Each volunteer's device binds to a named passkey identity per the
  architecture's §4.2 enrollment story; the queued entry carries who scanned it.

**Cost:** zero code, days of design. Reading `circulation.rst` §3819–4100 and the four `offline_circ`
scripts is an afternoon. The reconciler it implies is real work — call it the largest single piece of
this slice — but it is work that must happen regardless, and #12 requires naming the reconciler in
the same commit that creates the offline/online pair. This find is the specification for that.

### 2. ODK Collect + ODK Central — the annual audit walk and the condition photo

Apache-2.0, both verified. `getodk/collect` (777★, Kotlin, pushed 2026-07-29) is the Android app that
the global-health world uses to collect data where there is no signal and no power; the README's
framing is "designed to be used in resource-constrained environments with challenges such as
unreliable connectivity or power infrastructure" and "billions of data points in challenging
environments". It does barcode/QR scanning, photo capture, and GPS, holds completed forms locally,
and submits when connectivity returns. `getodk/central` (218★, pushed 2026-07-30) is the
self-hostable server it syncs to — Docker Compose on one box.

**Transplant:** do not rebuild offline field capture. Make the annual audit, the issue/return
condition documentation, and the pre-performance inspection checklist into ODK forms. A volunteer
walks the storage room with a phone in airplane mode, scans a QR, the form pre-fills the item from a
pre-downloaded CSV attachment, they pick a condition grade from a constrained list, take two photos,
and move on. Nothing is uploaded until they are back on the school network. Terpsi ingests
submissions from Central and writes them as **sidecars** (#11) that a named human promotes.

**Cost:** low-to-moderate. Building forms is XLSForm authoring, not programming — genuinely within
reach of a competent volunteer coordinator, which matters for the "no training" constraint. Two real
costs: (a) it is a second server process on the modest box (Central is Node + Postgres), and (b) the
form-attachment CSV is a **vendored copy of the item catalog**, which trips `CLAUDE.md` #12 — you
must name the reconciler that regenerates it and reconciles submissions back, in the same commit.
The other flag: photos taken at issue/return will contain students' hands, faces, and sometimes their
whole bodies in uniform. Those are `MEDIA_MINOR` and must carry consent state per §7.2 and the
architecture's `MediaAsset` rule; ODK's media goes to Central's blob store, so the egress broker has
to sit between Central and anything downstream, and exports are a distinct announced permission
class (#9).

### 3. Snipe-IT — the audit workflow, verified in source, and why not to adopt it whole

AGPL-3.0 verified from `LICENSE`. 14,552★ and pushed the day I looked. No open-core trap found: the
README describes no withheld features, and the audit machinery is right there in the tree.

I verified the audit workflow by reading it rather than trusting the feature list: assets carry
`last_audit_date` and `next_audit_date` (`app/Importer/AssetImporter.php`), there is a
`dueOrOverdueForAudit` query scope driven by settings and a scheduled command
`app/Console/Commands/SendUpcomingAuditReport.php` that mails the upcoming/overdue list, and
`resources/views/reports/audit.blade.php` renders item, location, last audit, next audit,
`days_to_next_audit`, and a note per row. That is §5's "annual audit workflow" as a dated,
per-item obligation with escalation — not a spreadsheet someone remembers in August.

**Transplant:** the *shape*. `next_audit_date` per item, a due/overdue scope, a scheduled report, and
an audit event that records a named auditor plus a note even when nothing changed. Pair it with §5's
"missing-instrument escalation": an item that fails two consecutive audits is not "missing", it is a
dated disposition with a named owner (#15).

**Why not adopt wholesale, at a cost that would surprise you:** Snipe-IT models checkout as state on
the asset row — `assigned_to` pointing at a user. That is precisely the "one row with a roster
column" that `CLAUDE.md` #8 forbids, and its check-in path clears that state rather than closing a
dated interval, which collides with #3 (never revoke by deleting). Retrofitting lane-per-student
custody and `invalid_at` intervals into someone else's Laravel schema is more expensive than writing
the custody table you actually want. Read it, copy the audit and depreciation fields, and write your
own assignment model as two lane entries with one referent.

### 4. grocy — a fridge app is the best open-source battery tracker in existence

MIT, verified from `LICENSE.md`. 9,312★, pushed 2026-07-30. PHP + SQLite, which is as close to "one
modest box" as this slice gets — no Postgres, no Node runtime, no queue worker.

§5 calls cable and battery tracking "the single most common day-of failure". The only mature
open-source implementation of battery lifecycle tracking I found anywhere is in a household
groceries app, and I verified it in the tree rather than from a feature list:
`views/batterytracking.blade.php`, `views/batteries.blade.php`, `views/batteryform.blade.php` with a
`charge_interval_days` field, `views/components/batterycard.blade.php` showing "Last charged", and
`views/batteriesjournal.blade.php` — a **journal**, i.e. a durable per-battery charge history with
filtering, not a last-charged timestamp. There is also an equipment module
(`views/equipment.blade.php`, `views/equipmentform.blade.php`) for gear-with-manuals, and — the
detail that makes it usable here — module **feature flags** (`GROCY_FEATURE_FLAG_EQUIPMENT` in
`views/layout/default.blade.php`), so the meal planner and recipes can be switched off entirely.
Barcode decoding is local via ZXing (README), and there is a PWA plus a separate GPL-3.0 Android
client ([patzly/grocy-android](https://github.com/patzly/grocy-android), offline support limited to
shopping lists per its README — so treat the Android client as online-only for our purposes).

**Transplant:** two options, and I'd take the second. (a) Run grocy alongside terpsi for consumables
and batteries — cheapest possible path to "reeds, valve oil, gaff tape, and the wireless-mic AAs",
and its "minimum stock → shopping list" flow is the reorder-threshold feature already built. (b)
Copy the *battery journal shape* into terpsi's own store: battery as a tracked entity with a charge
interval, a durable charge journal, and a due-state derived from the last journal entry. Option (a)
costs an extra service and a second source of truth — a canonical/vendored pair that #12 says must be
reconciled or not created. Option (b) is a day of modelling and no new pair.

Applied to the actual failure: the day-of failure is not "we had no batteries", it is "nobody knows
whether the pack in the drum-major's mic was charged Thursday or three weeks ago". A journal answers
that; a stock count does not.

### 5. InvenTree — the consumables and serialization schema, for free

MIT verified from `LICENSE`. 7,318★, pushed 2026-07-30. Django + Postgres.

Verified in source: `Part.minimum_stock`, a `DecimalField` with help text "Minimum allowed stock
level" (`src/backend/InvenTree/part/migrations/0114_alter_part_minimum_stock.py`). InvenTree's real
contribution is the **Part vs StockItem split**: a *part* is "Bb clarinet reed, strength 3" with a
reorder threshold, while a *stock item* is a specific physical quantity in a specific location, and
serialized stock items carry individual serial numbers. That distinction is exactly §5's split
between "consumables with reorder thresholds" and "serial-numbered instruments with condition
history", and getting it wrong early is expensive.

**One correction to the record, verified negatively:** the InvenTree mobile app
([inventree/inventree-app](https://github.com/inventree/inventree-app), Dart/Flutter, 131★) does
barcode scanning, but a code search for `offline` across its `lib/` returned **zero matches**. It is a
thin API client that needs the server reachable. Do not put it in the parking lot. If anyone in the
project has assumed "InvenTree has a mobile app, so mobile is solved", that assumption is wrong.

**Cost:** adopting InvenTree wholesale brings Django + Postgres and a manufacturing-oriented UI that
volunteers will not love. Stealing the two-level schema costs nothing.

### 6. Homebox — the cheapest self-host, with repair history already modelled

AGPL-3.0 verified from `LICENSE`. 6,596★, pushed 2026-07-30. **Single Go binary + SQLite**, under
50 MB idle (README) — the lowest-friction deployment of anything in this table, which is the single
biggest predictor of whether a volunteer-run program still has a working system in year three.

Verified in source: `backend/internal/data/ent/schema/maintenance_entry.go` defines a
`MaintenanceEntry` bound to an item; `backend/internal/data/repo/repo_maintenance_entry.go` states an
entry "represents a maintenance event" and sorts by scheduled *and* completion date;
`repo_maintenance.go` carries a `MaintenanceFilterStatus` of scheduled/completed/both, and
`backend/app/api/handlers/v1/v1_ctrl_maintenance.go` exposes it over the API. That is §5's
per-instrument repair history — "identifying the horn that is a money pit" — with the scheduled-vs-
completed distinction already correct. Homebox also does QR label generation, purchase price and
date, warranty tracking, attachments, and custom fields (README).

**Transplant:** the `MaintenanceEntry` shape (scheduled date, completed date, cost, description,
item edge) is directly liftable, and the sum of `cost` per item over a season *is* the money-pit
report. Add what Homebox lacks for this domain: vendor, warranty-claim reference, turnaround
(sent/returned dates), and the loaner assignment that covers the gap while the horn is away.

**Note on tombstones, which this project cares about (#20):** the original `hay-kot/homebox` (3,016★)
is **archived**, and `sysadminsmedia/homebox` is the named successor with the mapping stated in the
description. That is a competently executed tombstone in the wild and worth pointing at when §16's
retirement rules need an example.

### 7. Atlas CMMS — repair tickets and preventive rotation, with an open-core flag

AGPL-3.0 verified from `LICENSE` — **and** the README documents a commercial tier requiring a
`LICENSE_KEY` to "enable commercial features" (white-labelling, branding, "advanced features"). The
open-source core appears genuinely usable, but this is an open-core structure and should be recorded
as one rather than discovered later. Java Spring Boot + React + React Native (Expo), 708★, pushed
2026-07-29; the README claims mobile offline support, which I could **not** verify in source and
would test before believing.

**Transplant:** the work-order vocabulary — request → work order → assignment → parts consumed →
labour time → cost → closure, plus meter-based and calendar-based preventive schedules. §5's repair
tickets (vendor, cost, turnaround, warranty) and "usage rotation to spread wear" are both CMMS
concepts with forty years of prior art, and rotation-to-spread-wear in particular is a meter reading
(hours/events on an instrument) that nobody in the music-education market tracks.

**Cost:** heavy stack; do not adopt on a modest box next to everything else. Read the domain model.

### 8. Loxya / Robert2 — the live-event manifest, behind a license wall

This was the transplant I went hunting for: software written for the **AV / backline / event
equipment rental** world, where the daily job is "this show, on this date, needs these 340 things on
a truck, and here is what came back damaged". [Loxya/Loxya](https://github.com/Loxya/Loxya) is real
and maintained (53★, PHP, pushed 2026-07-24, formerly Robert2; forks and a Docker image exist, e.g.
`LaplancheMaxime/docker-robert2` and a GitLab fork under `sia-insa-lyon`). Features per README:
multiple equipment parks, per-event material lists with **shortage alerts** and category subtotals,
technician assignment, beneficiaries, material condition tracking on return, damage/fault tracking,
inventory counts, PDF documents.

**But: the `LICENCE` file is Creative Commons Attribution-NonCommercial-ShareAlike 4.0.** I fetched
and read it. That is not an open-source license — it fails the OSD on the NonCommercial term, CC
itself advises against using CC licenses for software, and "non-commercial" is dangerously ambiguous
for a school district or a booster organisation that charges fees. **Do not vendor, fork, or copy
code from Loxya.** Read the UI and the concepts.

**Transplant (ideas only):** the per-event material list with shortage alerts against availability is
the load-list feature §5 asks for, and it is the right shape — a manifest is a *reservation against a
calendar*, not a checklist. A trailer manifest for a competition Saturday should refuse to be
finalised when two ensembles have reserved the same timpani, and should print a return sheet whose
unchecked lines become the "what got left at the stadium" list.

### 9. html5-qrcode — the offline scan, solved, Apache-2.0

6,181★, pushed 2026-07-30, Apache-2.0 verified from `LICENSE`. Camera-based QR and 1D barcode
decoding entirely in the browser, no network round-trip. This is the boring correct answer to
"scanning on a phone with no signal" for the web-app path: the decode is local, so scanning works in
airplane mode, and only the *write* needs queueing. Pair with an IndexedDB queue (not LocalStorage —
see Koha above). **Cost:** an afternoon.

### 10. circulate — what volunteer-operated lending actually looks like

MIT, verified from `LICENSE.md` (the WebFetch summary said MIT; the file confirms it — "Copyright
2020 James Benton, Chicago Tool Library Co."). 107★, Rails, pushed 2026-07-08. This is the running
software of an actual tool library: memberships, checkout/return with fines, holds and waitlists,
renewal requests, appointment scheduling for pickup/dropoff, and **volunteer shift scheduling** in
the same app as the inventory.

**Transplant:** two specifics. (a) *Appointments for pickup and dropoff* — the uniform-crew problem
in §6 is a scheduling problem wearing an inventory costume, and combining them in one app is the
insight. (b) *Renewal requests requiring approval* — the summer-checkout-agreement flow in §5 is a
renewal with a disposition (#15).

**Cost:** not adoptable. The README warns "There is content and information hard-coded in many of the
views that is specific to The Chicago Tool Library", multi-tenancy is incomplete, and it depends on
SendGrid, S3, Square, and Google APIs — every one of which is a cloud dependency this project
refuses. Read it, deploy nothing.

### 11. lighterpack — gram-counting as a load list

GPL-2.0 verified from `LICENSE`. 807★, pushed 2026-07-29. Built for ultralight backpackers who weigh
their toothbrush. Every item has a weight, a category, a quantity, and flags for *worn* and
*consumable*; the app totals it and shows you where the weight is.

**Transplant:** a load list is a lighterpack list with an axle limit. §5 wants "trailer and truck:
load diagrams, load lists" — and the unspoken requirement is that an equipment truck has a legal
weight rating that a marching program can absolutely exceed with timpani, a podium, and forty
sandbags. Give load-list items a weight and a "must not exceed" total, and you have converted a
packing checklist into a safety check for free. The worn/consumable distinction maps cleanly too:
things that leave on a student's body versus things that get used up and do not come back.

---

## Tag technology that survives the field

**Status: engineering judgement, NOT verified in this session.** Every vendor, standards body, and
field-study host I tried was refused by the proxy (`camcode.com`, `metalphoto.com`, `zebra.com`,
`atlasrfidstore.com`, `nfpa.org`). What follows is reasoning to *test*, with the verification list
at the end. Per `CLAUDE.md` #17, do not let any of this become a quoted figure in a design doc until
someone reads a datasheet.

**The first principle, which is not about tags at all: the tag is a pointer, never the identity.**
The identity of record for an instrument is the manufacturer's serial number, stamped into metal at
the factory, plus an engraved or stamped school mark. Tags fall off; serials do not. Every tag
technology below should be modelled as a *revocable binding* between a tag ID and an item — the same
`invalid_at` treatment #3 requires for guardianship — because tags get replaced, cases get swapped,
and a re-tagged tuba must not become a second tuba. Build the re-tag flow before buying the first
label, or the audit will invent duplicates.

**Adhesive labels on a brass instrument will fail, and predictably.** Valve oil, slide grease, hand
sweat, daily wiping, polish, and lacquer are collectively the worst adhesive environment in the
building. The plausible design is: durable tag on the **case**, engraved/serial identity on the
**instrument**, and both recorded with their binding dated. This also means the audit has to handle
"case present, horn absent", which is the actual failure mode in a band room.

**Symbology.** QR is the right default: every volunteer's phone reads it, and `html5-qrcode` decodes
it offline. Data Matrix is the better choice where the mark must be small and abraded — it is what
aerospace and defence use for direct part marking — but volunteer-facing tooling for it is thinner.
Pick one, print it large, and include a **human-readable short ID under the code**, because the
single most common field failure is a code too scuffed to scan and a volunteer with no fallback.

**Materials, in rough order of survivability:** photosensitive anodised-aluminium plates (the
process behind military property plates) for trailers, road cases, field equipment, and podiums that
live outdoors; laminated polyester or polycarbonate with an over-laminate for cases and cabinets
indoors; and **not** paper or plain vinyl, which will not survive a season. Riveted or
mechanically-fastened plates beat adhesive on anything that lives on a trailer.

**Garments are the one place RFID clearly earns its cost.** The industry that has already solved
"track individual garments through repeated industrial laundering" is hospital linen and uniform
rental, using sewn-in UHF RFID laundry tags. Two payoffs for §6: the tag survives cleaning, and a
bin of returned jackets can be read *in bulk* rather than one at a time — which is the difference
between the uniform-return count taking an evening and taking ten minutes. This is also the only
place I'd spend money on a UHF reader.

**Metal and RF do not mix, and a sousaphone is a large piece of metal.** Plain UHF inlays stuck to a
brass bell will read poorly or not at all; on-metal tags with a spacer or ferrite layer exist for
this reason. NFC on metal likewise needs a ferrite shielding layer. Fibreglass flag poles and fabric
silks are RF-friendly by comparison; for poles, printed heat-shrink sleeves are more plausible than
adhesive wraps.

**Cables deserve their own answer** because §5 singles them out. Nothing adhesive survives being
coiled, uncoiled, walked on, and gaff-taped. Printed heat-shrink sleeves near each connector, plus a
colour band scheme, plus a per-cable ID in the store. And the honest observation: the day-of cable
failure is usually not a *missing* cable, it is a cable that was already intermittent and got packed
anyway. That is a condition-state problem, not an inventory-count problem — so cables need a
`suspect` state that survives being put back in the bin, and a pre-performance check that a
`suspect` cable never silently satisfies.

**What works with no signal, ranked by cost:** camera decode of QR/Data Matrix (free, works in
airplane mode, every volunteer already owns the hardware); NFC tap (free per read, offline by
construction, but requires touching each item and Android-only in practice); UHF RFID bulk read
(transformative for the annual audit and uniform returns, but needs a Bluetooth reader, and a reader
is a thing that a volunteer program will lose, break, or fail to charge). **Recommendation:** QR on
cases and equipment as the universal baseline; UHF RFID only for uniforms; NFC only where a tap is
genuinely easier than a scan. Do not build a system that *requires* a reader to function.

**Verification list before anyone spends money** — wash-cycle ratings for laundry tags from a vendor
datasheet; on-metal tag read range against an actual sousaphone; abrasion and solvent ratings for
plate materials; whether the chosen phone models read the chosen tags at the distance a volunteer
will actually hold them; and the MIL-STD-130 marking specifics if anyone wants to claim that lineage.

---

## Weirdest things I found

1. **A library catalogue is the most battle-tested offline-checkout design in open source — and it
   already deprecated the approach terpsi-music would have reached for first.** Koha ships a `.koc`
   offline transaction file format, a queue, an approval-gated commit, and a documented conflict
   taxonomy — then killed its own browser-based offline mode because "HTML LocalStorage ... is limited
   to 2.5MB or 5MB per domain". Someone already ran this experiment, wrote down the result, and
   published it in an RST file. Nobody searching for "band instrument inventory" would ever find it.

2. **The best open-source battery tracker in existence is a fridge app.** grocy — meal plans, recipes,
   groceries — contains `views/batterytracking.blade.php`, a `charge_interval_days` field, and
   `views/batteriesjournal.blade.php`, a filterable durable charge history per battery. §5 calls
   battery tracking the single most common day-of failure; the only mature implementation of it is in
   software for people who want to know when their milk expires. It even has feature flags to turn the
   groceries off.

3. **Ultralight backpackers built the load-list tool.** lighterpack (807★, GPL-2.0) exists because
   hikers weigh their gear in grams, and it gives every item a weight, a category, and worn/consumable
   flags. Point it at an equipment trailer and it becomes an axle-load safety check. The transplant
   from "people obsessed with carrying less" to "people who put a marimba on a trailer" is exact, and
   the gram-counting culture is the reason the data model has weights at all.

4. **A zero-star single HTML file solves a real band problem nobody else has modelled.**
   `Setakoma-Works/NEED-PERC-for-Brass-Band`: register each piece in the concert program with its
   required percussion, mark what the ensemble owns, and the summary tab deduplicates across the whole
   program and splits it into "needs rental" and "already owned" — with spec notes (octave range, head
   size, material) carried through so the output *is* the rental request. No server, no install, open
   `index.html`. It is the only thing I found anywhere that connects **repertoire** to **inventory**,
   which is a join no commercial product in this market makes, and it has zero stars.

5. **The best-fitting mobile RFID codebase I found is the one we are not allowed to use.**
   `zetavg/Inventory` (331★) is a polished React Native UHF RFID asset app on CouchDB/PouchDB — local-
   first replication and handheld RFID, i.e. precisely the architecture this slice wants. Its
   `LICENSE.txt` opens "All rights reserved" and then hand-writes exceptions permitting personal use,
   internal business use, and non-executable redistribution *by forking on GitHub*. It is
   source-available proprietary software wearing an open-source silhouette — 331 stars, a topic list
   full of `asset-management`, and no OSI license anywhere. Exactly the trap worth flagging: the
   license file is the only place the truth was written down.

---

## License traps, collected

- **Loxya/Robert2 — CC BY-NC-SA 4.0.** A Creative Commons NonCommercial license on application
  software. Not open source; NC is ambiguous for a fee-charging school program. Ideas only.
- **zetavg/Inventory — "All rights reserved"** with hand-written exceptions. Not open source. Cannot
  be vendored or redistributed. Read-only.
- **Atlas CMMS — AGPL-3.0 plus a commercial `LICENSE_KEY`.** Open-core. Core looks usable; record the
  structure now rather than discovering it during install acceptance.
- **shelf.nu — AGPL-3.0 but architecturally cloud-bound.** Self-hosting "requires an external Supabase
  instance" (README). A free license on software that cannot run without a third-party service fails
  the §6 posture regardless of the license text.
- **NEED-PERC — no license file.** Default: all rights reserved. Take the idea, not the file.
- **GLPI** (not tabled; core is GPL, vendor sells subscription plugins) and **Odoo** (LGPL community,
  features held in Enterprise) are both open-core in this space and were deliberately not pursued.

---

## The desert — domains I hunted that have no open-source answer

Reporting these as null results, because a null result changes the build/adopt decision:

- **Costume and wardrobe departments.** `costume inventory` returns 40 repositories, the best of which
  has one star. Piece-level garment tracking with alterations — §6's core ask — has **no** open-source
  implementation. The real tools (Costume Inventory Resources, Rentman, Flex) are all proprietary.
- **Theatre and film production inventory.** Two repositories, both empty or portfolios. Propared,
  Yesplan, and Flex are proprietary; Loxya is the only credible open thing in the adjacent
  event-rental space, and it is NC-licensed.
- **PPE / safety-critical inspection intervals** (climbing, scuba, fire turnout gear). Searches for
  turnout gear, PPE inspection, and climbing gear logs return **zero** usable repositories. The
  doctrine is transplantable — service life, inspection interval, quarantine state distinct from "in
  repair", batch/lot recall — but there is no code. This matters for guard equipment: rifles, sabres,
  and poles are thrown, and a cracked pole is a safety item, not a condition grade.
- **School device checkout** (Chromebook 1:1, textbook circulation) — the closest institutional
  analogue to instrument checkout with damage fees, and it is entirely Follett/Destiny-style
  proprietary territory.
- **Purpose-built band instrument inventory.** Four repositories, all zero-star toys. The market is
  Charms/Cut Time and spreadsheets. §5 is genuinely unserved by open source.
- **Military property accountability.** No code (DPAS/GCSS-Army are government systems), but the
  doctrine is the best-articulated version of what §5 needs and costs nothing to borrow: the **hand
  receipt** (custody signed for by name), the **sub-hand receipt** (a section leader signs for what
  they redistribute — which is how a drumline captain holding twelve harnesses should work without
  ever becoming a group grant under #5), the **component hand receipt** (a single item's parts listed
  and signed for individually — *this is the piece-level uniform record §6 asks for, already named*),
  **sensitive-item** handling with tighter audit intervals, and the **change-of-command 100%
  inventory**, which is the institutional-memory answer to a booster treasurer handoff and to §20's
  "staff departure mid-season".
- **Aviation maintenance.** Only tiny new repositories (AVLedger, MyTailLog). But two concepts are
  worth stealing outright: the **squawk / MEL (minimum equipment list)** — a documented list of what
  may be broken while the aircraft still flies, each deferral carrying a deadline — which is exactly
  "the third valve on the spare baritone sticks, it is playable, fix by October 3" as a *dated
  disposition* (#15) rather than a sticky note; and **life-limited parts** tracked by cycles rather
  than calendar time, which is §5's "usage rotation to spread wear" done properly.
- **Museum condition reporting.** CollectionSpace exists and is worth reading for two named
  procedures — *condition checking* (a dated assessment by a named checker, independent of any
  movement) and *location and movement control* (every move recorded, so the answer to "where is it"
  is always a dated event and never a mutable field). Both are better than what any asset tool does.
  Note for #14: museum condition grades are **named**, never bare integers and never colour-only.
  Terpsi's condition scale needs a prefix (`C1`–`C5`) and one mapping table.

---

## Fit notes against `CLAUDE.md` (where these transplants will fight the architecture)

- **#8, one lane per student.** Every asset tool I read models custody as a mutable field on the item
  (`assigned_to`). Terpsi needs the inverse: the item carries a dated custody *interval* ledger, and
  each interval is mirrored as a lane entry on that student's lane. A shared marimba used by two
  students is two lane entries with one referent — never a roster column on the marimba.
- **#3, never revoke by deleting.** Check-in must close an interval with `invalid_at`, not null out an
  assignment. Snipe-IT's and Homebox's flows both need this changed before their shapes are copied.
- **#6, never compute a priority between two students.** "Who gets the good horn" and "who gets the
  loaner while theirs is in the shop" are ranking questions. The system presents condition, history,
  and need; a human decides and the decision is recorded with their name. Any "best match" scoring in
  a borrowed codebase must be torn out, not configured off.
- **#13, absence surfaces as `unknown`.** The offline scanner cannot see fee holds, consent state, or
  a court-order restriction. It must record `unknown` and flag, exactly as Koha documents for holds
  and expired cards — never "no restrictions".
- **#10, draft until a named human seals it.** Queued offline transactions are drafts. Copy Koha's
  approval-gated commit and its rejection statuses; an audit trail that logs only the accepted scans
  is not one.
- **#12, name the middle.** Two pairs get created by this slice and both need a named reconciler in
  the same commit: the offline device queue versus the canonical store, and (if ODK is adopted) the
  form-attachment item extract versus the catalog.
- **#14, scales.** Condition is `C1`–`C5` with a prefix and one mapping table, never a bare 1–5 and
  never colour alone — a red dot on a jacket tag is not a condition grade.
- **#19, guards must be shown to fail.** The mutation tests this slice owes: replay an out-of-order
  multi-device queue and assert the reconciler refuses rather than guesses; attempt a group grant over
  "the drumline" and assert refusal at issuance; attempt a condition-photo export without the export
  permission and assert refusal plus announcement; delete a returned-item interval and assert refusal.
