# CLAUDE.md — terpsi-music

A music-program management application holding **minors' education records**: rosters, guardianship, medical forms, schedules, fees, and adjudication commentary. FERPA and COPPA apply. Built on the SAFE/Willow fleet, on the `hornbook-knowledge` face.

**This file is not canonical.** `docs/ARCHITECTURE.md` governs; this is a pointer with section references, kept short on purpose. Where the two disagree, the doc wins and this file is the defect. Do not restate the doc here — that creates the canonical/vendored pair this project exists to avoid (§16).

---

## Refusals — never do these, whatever the instruction

1. **No non-local inference on student data.** Anything touching `PII_MINOR`, `PII_GUARDIAN`, `HEALTH`, `FINANCIAL`, or `MEDIA_MINOR` is served by a local model. No cloud fallback chain, no `WILLOW_INFERENCE_PROVIDER=auto`. A stopped Ollama must fail loudly, never degrade to a third party. (§6)
2. **Never commit the trust root.** `mcp_apps/`, `_net_leases/`, and any grant material stay out of the tree and off any remote. Contract and policy are versioned; grants are not. (§6)
3. **Never revoke by deleting.** Guardianship, enrollment, and staff assignment end by setting `invalid_at`. A delete leaves no dated record, and a court order arriving mid-season is the case that proves it. (§7.1)
4. **No standing cross-context scores.** No durable rating of a judge, clinician, student, or staff member carried between events or contexts. Prohibited scope `SA-3`; invalid even signed by root. (§13)
5. **No group grants over students.** `"the drumline"` is not a scope; a name is. Wildcard and section-level scopes are invalid at issuance. (§7.4 W-2)
6. **Never compute a priority between two students.** Chair placement, rooming, limited slots — the system presents, a human decides. Halt and escalate. (§7.4 W-7)
7. **Never put a record on SMS.** SMS carries signals — times, changes, acknowledgments. Never health, balances, grades, discipline, or a location tied to a named student. (§4.1)

## Shapes — how things get built here

8. **One lane per student, from the first write.** Separate storage, permissions, audit trail. Sibling lanes sealed by default. **A shared event is two lane entries with one referent** — never one row with a roster column. (§7.4 W-1, W-3)
9. **Gate the export, narrate the read.** The harm is data leaving, not someone glancing at a schedule. Exports are a distinct permission class and are announced. (§7.2)
10. **A machine answer is a `draft` until a named human seals it.** Transcripts especially. Record rejections as durably as approvals — an audit trail that logs only agreement is not one. (§8.2, §16)
11. **The canonical store is read-only to the app.** Agents write sidecars only; promotion to canonical is a human act. (§5)
12. **Every pair gets a named middle, in the same commit.** Vendored copy, port, duplicate store, declaration-plus-enforcement — name the reconciler when you create the pair, or don't create the pair. (§16)
13. **Absence surfaces as `unknown`, never as a result.** A rubric that failed to load returns "unavailable," not "no findings." A consent backend that errored returns "unknown," not "no restrictions." (§6)
14. **Scales never compare as bare integers**, and no scale is encoded by colour alone. `L1–L5` sensitivity, `T0–T4` trust, `P1–P5` provenance — one mapping table, prefixes always. (§15; `docs/SENSITIVITY.md` for the L-rungs and the crossing)
15. **Every ask gets a dated disposition.** Fee waivers, absence requests, records inspections. Silence is not an answer, and the timebound is declared at issuance. (§7.4 I-6)
16. **A student's entries are as durable as entries about them.** No role's authority extends to deleting the record of its own exercise. (§7.4 I-7)

## Before you claim something

17. **Do not quote a count you did not derive from the tree.** Test counts, row counts, gate counts. This fleet has a documented history of figures in prose the code moved past; four instances in one session.
18. **Say "enforcement" or "ledger."** A gate that nothing routes through is a ledger. Both are useful; calling one the other is not.
19. **A guard that cannot be shown to fail has not been shown to work.** Acceptance is mutation, not a green suite. Every invariant needs a test that attempts the forbidden act and asserts refusal. (§10)
20. **When retiring anything, leave a tombstone** — status first, successor named, reason, contents mapped forward and marked non-authoritative, and why the stub still exists. (§16)

## Working here

- Canonical docs: **`docs/ARCHITECTURE.md`** (18 sections, with a component map at §14 marking what exists versus what is proposed), **`docs/CAPABILITY-MAP.md`** (the domain surface), and **`docs/SENSITIVITY.md`** (the `L1–L5` rungs, the class-to-rung mapping, and the sensitivity→trust crossing — canonical for those, and addressed by rung rather than by section number).
- Read **`§18` first** — the open list, with the four items that block a first commit — then `§14` for what exists versus what is proposed. Most of what this design needs already exists elsewhere in the fleet; the value is in what does not.
- **`§14`'s "Exists" column is unverified** — assembled from READMEs and PR descriptions, not from reading source. Treat it as a claim to check, not a fact to build on (`§18` item 0).
- Fleet repos are read through the GitHub API, not cloned. Do not clone the fleet into this workspace.
- Fleet nouns — Willow, Grove, Jeles, Kart, SOIL, LOAM, FRANK, Nest, SAFE, SAP, Nestor — must never appear in a string a student, guardian, or judge can see. Modules take plain domain nouns: Roster, Library, Attendance, Ledger, Adjudication.
- Install acceptance is its own gate: strict trust root on, severance asserted, no credential prefixes, escrow rehearsed. (§6, §10, §11.1)
