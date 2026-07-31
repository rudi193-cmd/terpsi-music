# terpsi-music

A management application for a youth music program — rosters, guardianship,
medical forms, schedules, fees, and adjudication commentary. It holds **minors'
education records**, so FERPA and COPPA apply, and the privacy architecture is
the product rather than a feature of it.

The design question everything follows from (`docs/ARCHITECTURE.md` §1):

> How little can the server be permitted to know, and how narrow can its
> interface be, such that its full compromise is survivable?

Six populations with incompatible network positions — students, staff,
director, guardians, guest adjudicators, and the district. Everyone but the
guardians can be served on the local network. Guardians are simultaneously the
group that forces a reachable endpoint and the group most attractive to attack.
The answer is three zones: an on-premise hub holding all plaintext with **zero
inbound ports**, an untrusted relay that shuttles opaque blobs between mailbox
IDs, and edge devices holding an encrypted replica of their own slice.

**Status: design, plus one library.** No application exists yet. Four items
block a first commit and two of them are decisions rather than documents — §18.

## Where to start

| | |
|---|---|
| `docs/ARCHITECTURE.md` | Canonical. 18 sections. **Read §18 first** — the open list — then §14 for what exists versus what is proposed |
| `docs/CAPABILITY-MAP.md` | The domain surface. §24 is the craft-feedback capability, the only one not already built somewhere |
| `docs/SENSITIVITY.md` | The `L1`–`L5` rungs, the class-to-rung mapping, the sensitivity→trust crossing |
| `docs/LANE-MODEL.md` | The W-1/W-3 schema, with the DDL at `docs/schema/001_lanes.proposed.sql` |
| `docs/CROSSINGS.md` | Findings record — one session's defects and the six patterns under them |
| `docs/FLEET-READS.md` | The 36 fleet repositories this design rests on, and why none is readable right now |
| `docs/CRAFT-SOURCES.md` | What §24 claims already exists in the field, with its evidence and how weak that evidence is |
| `docs/SKINS.md` | Exploration — which parts of this are the contract and which are the domain, and what else could fill it |
| `CLAUDE.md` | Twenty rules, kept short on purpose. A pointer, not a summary |

**§14's "Exists" column is unverified** — assembled from READMEs and
pull-request descriptions, not from reading source. Treat it as a claim to
check, not a fact to build on.

## Running things

Everything here is stdlib-only Python. No dependencies, no network, no model.

```bash
python3 -m pytest tests/ -q
# or, with nothing installed at all:
for f in tests/*.py; do python3 "$f"; done
```

The one piece of working software is `craft/` — the eight text-only checks of
§24 of the capability map. It reads a lyric and reports where the craft is off.
It writes nothing, and it scores nothing.

```bash
python3 -m craft lyrics/get-ready.txt --intent lyrics/get-ready.intent
python3 -m craft lyrics/get-ready.txt --against <earlier-draft>
```

A finding you disagree with is not suppressed — you declare it, with a reason,
and the declaration is what gets kept. That is the mechanic, not a convenience.

The same tool wears a second skin with `--prose`, reading a document instead of
a lyric and checking the craft `CLAUDE.md` states in English — counts with no
derivation, a gate that does not say whether it is a gate or a ledger, absence
rendered as a result, a bare integer where a rung belongs, a retirement with no
tombstone. Same report, same ids, same declaration file.

```bash
python3 -m craft docs/ARCHITECTURE.md --prose --intent docs/prose.intent
```

The other working parts are the **presentation middle** and the **four doors**
`docs/survey/scout-21-surfaces-a11y.md` §3 names — `presentation/` holds the IR,
the palette and the one mapping table for `L1–L5`, `T0–T4` and `P1–P5`;
`surfaces/{tui,web,print,text}/` are thin renderers over it. Nothing there is an
application: no server, no session, no framework. Two middles keep the pairs
honest, and both run in CI.

```bash
python3 tools/manifest.py                # the declaration, against the tree
python3 presentation/render.py --check   # rendered artifacts, against their templates
```

The first reconciles `manifest.json` — surfaces, listeners, permissions —
against what the source actually opens, and reports the vacuous case as
`UNKNOWN` rather than as a pass. The second renders the four backend artifacts
and exits nonzero if a committed one differs by a byte.

The proposed migration runs against PostgreSQL 16 in CI, where eight forbidden
acts are attempted and asserted to fail. A guard that cannot be shown to fail
has not been shown to work.

## Fleet

Local overlay (`.mcp.json`, `.willow/`, `.cursor/`) is gitignored — materialised
by:

```bash
WILLOW_HOME=~/github/.willow willow-mcp project sync terpsi-music
```

Fleet repositories are read through the GitHub API, never cloned into this
workspace.
