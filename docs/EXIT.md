# The exit line

**§18 item 5. Written 2026-07-30, before the first install, which is when §11.1 requires it.**

`awesome-sovereign-software` sets the criterion and it is the fleet's, not this document's: **sovereignty is the ability to leave**, every listed entry documents how you walk away with your data, and *"if an exit line cannot be written honestly, the app does not get listed."*

That last clause is the reason this file says what it says. §11.1 offers a model sentence and the honest version today is shorter, because most of what the model sentence describes does not exist yet.

---

## The line

> **Your program's records leave as plain files.** Each student's record exports as a folder containing `entries.csv` — one row per record, opened by any spreadsheet — plus a `README.txt` carrying the exit terms written down the day the record was opened, and a `MANIFEST.txt` with a checksum and a count for every file so you can tell whether anything went missing. Nothing in that folder requires this software to read. The per-student export is built (`records/export.py`) and tested. **A whole-program export is not built**, because there is no store yet to export from.

**What that sentence deliberately does not claim.** No SQLite file, no `terpsi export --all`, no PDF, no media directory, no transcripts. §11.1's model sentence names all of those. Writing them here today would be the failure this file exists to prevent — a promise that reads well and is not true.

---

## The five-point test, answered as of 2026-07-30

| Criterion | State | What is actually true |
|---|---|---|
| Runs without an account | **UNKNOWN** | On-site personas and device-held guardian passkeys are the design (§4). Nothing is built, so this is a plan and not an answer. |
| Runs without a server | **UNKNOWN** | The hub is the org's and §4.1 keeps notification off any hosted dependency. Same status: designed, unbuilt. |
| No subscription for core function | **PASS, structurally** | There is no paid path and nothing to gate. The risk §11.1 names is the hosted SMS route, and §4.1 already forbids records on SMS — so the feature most likely to acquire a subscription is the one carrying least. |
| **Data readable without the app** | **PASS for one student · ABSENT for the program** | `records/export.py` renders a W-6 transfer as CSV and plain text with a checksummed manifest, and `tests/test_export.py` asserts the CSV parses with the stdlib reader and that nothing is dropped by rung. There is no whole-program export because there is no store. |
| **Survives the vendor** | **UNKNOWN** | Nothing runs yet, so nothing has been shown to keep running. This becomes answerable at the first install and not before. |

**One PASS, one PASS-and-ABSENT, three UNKNOWN.** That is the honest state and it is worse than §11.1's model sentence implies. It is also better than it was this morning, when the row that matters most — *data readable without the app* — was `ABSENT` in both halves.

`tools/conform.py` runs this as a check (`exit-line`) and writes it into a dated record, so the row above stops being a claim in a document and starts being something with a series behind it.

---

## The smaller scale, which matters more

§11.1 is explicit that the program-level export is the *easier* obligation:

> *"A program-level export answers what happens when the organisation leaves the software. **W-6 answers what happens when a student leaves the organisation**, and it is the harder of the two: it must run every June, per graduate, unattended, and hand over a record the recipient can read without this application."*

That is the half that is built, and the ordering was not an accident. **The per-graduate export is a precondition of enrolment, not an end-of-life feature** — *"a lane opened without a written exit is invalidly opened."* `records/exit.py` enforces that at construction: there is no way to build a `Lane` without `exit_terms` and a threshold. `records/export.py` turns the resulting transfer into files.

Three properties of that bundle are worth stating here because they are where this kind of export usually goes wrong:

- **Full history, unfiltered.** Nothing is dropped by rung. `L5` — enforcement material, the contents of an order — is the single exception, and it is **named and counted in the manifest**, never silently omitted. A quiet drop is how a "safe subset" export gets built by accident, and the recipient could not tell.
- **The exit terms travel in the first file**, in the words used when the lane was opened. Rows without the promise they were kept under are data, not an exit.
- **The bundle can check itself.** A manifest with per-file digests and a record count, because a bundle that lost a file in transit is otherwise just a smaller bundle. `export.verify()` is the recipient's half.

---

## Regressions

§11.1 carries a caution worth adopting whole:

> *"Its **Delisted** section records sovereignty regressions with a date, a reason, and a source, and removing an entry without accounting for it fails CI. Regressions are normal; unrecorded ones are the problem."*

So this section exists before there is anything to put in it. **An install that quietly acquires a hosted dependency between seasons has regressed**, and the place to say so is here, dated, with what changed.

| Date | What regressed | Why | Source |
|---|---|---|---|
| — | *(none recorded)* | | |

An empty table is a claim like any other. It means nobody has recorded a regression — not that none has happened — and it should be read the way §14's `UNVERIFIED` is read.

---

## What has to be true before this line can grow

In the order they unblock each other:

1. **§18 item 4 — which surfaces exist.** The account and server rows cannot be answered until something runs.
2. **A store.** The whole-program export has nothing to read. `docs/schema/001_lanes.proposed.sql` is the shape and it is still proposed, gated on items 3 and 4.
3. **Media and transcripts.** §11.1's sentence includes commentary audio and its transcript. `records/marking.py` anchors commentary; nothing captures or exports the audio.
4. **A restore test.** §11 requires restores tested on a schedule and §11.1 says the exit line should be *"tested like a restore."* Exporting is half of leaving; the other half is somebody opening the folder on a different machine and finding their record in it.

**Point 4 is the one most likely to be skipped**, because an export that is never opened looks identical to one that works.
