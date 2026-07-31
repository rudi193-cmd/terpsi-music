# Escrow — the master key's custody

**Status:** policy, decided by the maintainer 2026-07-31 (§18 item 18, gate
G-A; the options considered are in `docs/PLAN-STORE.md`). Names and the first
rehearsal are install-acceptance acts (§11.1) and are deliberately not here —
until the first dated rehearsal is recorded in this file, the disposition
reads as **recorded and unrehearsed**, and `tools/audit.py` correctly refuses
to count that as escrow. §5: *an untested key recovery is not escrow.*

## The shape: 3-of-5

Chosen for the reason §18 item 15 chose the witness composite: the failure
modes differ, and a recovery two years out uses whichever custodians
survived. Any three of the five reconstruct the master; no two suffice; no
single office holds a quorum with itself.

| share | custodian (role) | why this role |
|---|---|---|
| 1 | Program director | operates the box; first to need a recovery |
| 2 | District administrator | survives a change of director |
| 3 | Guardian-council seat | the adverse interest — recovery cannot happen with only the institution in the room |
| 4 | District counsel | legally legible custody; survives both offices |
| 5 | Sealed deposit (attorney or safe-deposit) | survives everyone; the share nobody carries home |

The guardian-council seat is re-appointed as families graduate; the
re-appointment re-issues share 3 and is recorded here with its date. A share
holder who leaves the role surrenders nothing — the shares are rotated
(`records/atrest.py::rewrap` is the mechanism) and the old set is dead.

## Rehearsal

Annual, on the program calendar rather than triggered by activity (the
shape-of-a-week rule, applied to key ceremonies). The first rehearsal is
performed at install acceptance and recorded below with its date; a
disposition whose latest rehearsal is older than a year reads `STALE`.
A missed rehearsal is an ask with a dated disposition owed (rule 15), not a
silence.

## Rehearsals recorded

*None yet. The first entry is written at install acceptance, and until it is,
the honest state of this plan is unrehearsed — recorded here so nobody reads
a table of policy as a table of practice.*

**This section is read by machine.** `tools/audit.py::escrow_facts` parses the
threshold above, the custodian rows, and any `rehearsed <date>` here; R16 and
`tools/conform.py`'s `key-escrow` row both read that one parse rather than the
file twice. With no dated rehearsal the row is `UNKNOWN` — `records/atrest.py`'s
own state for *recorded and never rehearsed* — and adding a dated line below
turns it `PASS` on the next run. So the format matters: a rehearsal is recorded
as a line containing the word *rehearsed* and an ISO date.

## What this document does not decide

Where the box lives, where the master key file sits on it, and who performs
the ceremony — deployment acts, recorded where deployment is recorded. The
share *count* and *threshold* above are policy and are this document's to
state; the share *values* never appear anywhere, this file included
(refusal 2).
