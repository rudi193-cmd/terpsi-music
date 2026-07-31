# Security audit — terpsi-music

- **date** `2026-07-31`
- **commit** `a2bd22c1c51380daf4c38127a898d43fe5ff03e5`
- **rubric** `willow-2.0/SECURITY_AUDIT.md`, fifteen checks `R1`–`R15`, adopted by ARCHITECTURE §10 as an install gate rather than a document
- **added here** `R16` (encryption at rest, key escrowed) and `R17` (a structural no-egress test that fails when neutralised), both runnable at `tools/audit.py`

**Status: findings record, and a gate.** This document governs nothing about the
design — `docs/ARCHITECTURE.md` governs — but `tools/conform.py`'s
`security-audit` row reads it, and an open finding at `S1` or above fails the
build. That is the difference §10 asks for between a rubric and a ledger, and
rule 18 asks it to be said in one direction or the other: this is enforcement,
via `tools/conform.py::check_security_audit`, wired into `CHECKS` and mutated in
`tests/ablate.py`.

**The pin names the tree that was read**, which is the parent of the commit
carrying this file — an audit cannot pin the commit it is part of.
`tools/conform.py::check_security_audit` checks the pin for the one thing it
decides: that this history contains it.

**This is the re-run the last revision said it owed.** The prior pin
(`d2817f2`) named a tree that predated the store, the two accepted dependencies,
the console surface and the HTML surface — so several rows described a tree that
no longer existed (`R14`'s *"no `requirements.txt`"* was the clearest). This
revision re-pins to a tree that contains all of them and re-derives every row
against it. What moved as a result is named where it moved: `R1` and `R6` were
`NOT-APPLICABLE` and are now real `PASS`es (SQL is executed, HTML is emitted);
`R14` closed with `TM-DEPS-01`; and `R10`/`R11` read `PASS` at this pin because
the fixes that closed `TM-TMP-01`, `TM-RACE-01` and `TM-RACE-02` are ancestors
of it rather than, as before, the carrying commit itself. The findings table
below keeps those as closed history; the rubric row describes the tree the pin
names.

**Not a clean bill.**
*Findings: 5 recorded, 5 closed, 0 open* — every `TM-` finding raised against
this tree has been fixed. The one row that is still not a pass is `R16`
(`FINDING`/`S2`), which is not a `TM-` finding but the added at-rest check, and
turns on an escrow rehearsal that is an install-acceptance act (§11.1), not a
commit. The figures here are counted from the tables below by
`tests/test_audit.py` rather than typed. A rubric run that came back with
nothing would be the outcome §10 warns about, not a good one.

---

## What was examined

Every figure in this section was derived from the tree at the pin; the command
is beside each one (rule 17).

| Surface | Size | How counted |
|---|---|---|
| Tracked Python | 187 files | `git ls-files '*.py' \| wc -l` |
| — of which decoys | 40 files | `git ls-files 'tests/fixtures/decoys/*.py' \| wc -l` — fixtures built to be caught, some deliberately unparseable; excluded from the scans below |
| — of which application + tooling + suites | 147 files | the remainder, all of which parse (`ast.parse` over each, 0 failures) |
| Records modules | 27 in `records/` | `git ls-files 'records/*.py' \| wc -l` |
| Store modules | 11 in `store/` | `git ls-files 'store/*.py' \| wc -l` — the declared exception to §6's no-egress inner ring |
| Console surface | 4 in `console/` | `git ls-files 'console/*.py' \| wc -l` — the director TUI, a local terminal loop |
| Checkers | 10 in `tools/` | `git ls-files 'tools/*.py' \| wc -l` |
| Prose tooling | 5 in `craft/`, plus `voice.py` and `personas.py` | `git ls-files 'craft/*.py' \| wc -l` |
| Migrations | 4 in `migrations/` | `git ls-files 'migrations/*.sql' \| wc -l` — applied and attacked in CI |
| Suites | 62 `test_*.py`, plus `tests/ablate.py` and `tests/ablate_store.py` | `git ls-files 'tests/test_*.py' \| wc -l` and `git ls-files 'tests/ablate*.py'` |
| Test functions | 1359 collected | `python3 -m pytest -q --collect-only`, run at the pin |
| Ablation mutations | 445 rows | `tools/audit.py` parses `MUTATIONS` by AST; `tests/ablate.py` prints the same figure at the end of a run |
| Distinct top-level imports | 60 roots over the 147 non-decoy files, of which **2 are third-party** | an AST walk over every non-decoy file, roots compared against `sys.stdlib_module_names` and this repository's own packages |

**The two third-party imports are `cryptography` and `psycopg`**, each declared
in `requirements.txt` with an exact pin (`cryptography==41.0.7`,
`psycopg[binary]==3.1.18`) and each admitted at exactly one seam — `cryptography`
for the at-rest Fernet seal (`records/atrest.py`), `psycopg` for the store
driver (`store/`). `tools/imports.py` fails the build on any import that is not
stdlib, one of these two declared roots, or local; the derivation above finds 0
undeclared third-party roots.

**There is now a database, a migration chain and an HTML surface; there is still
no server and no listener.** `manifest.json` declares `listeners: []`, and
`tools/sockets.py` scanning the tree finds zero — so the checks aimed at a live
network surface (`R5`, `R8`) stay `NOT-APPLICABLE` with the condition that ends
that state, counted from the verdict column below and re-counted by
`tests/test_audit.py::test_the_tally_matches_the_table`. `NOT-APPLICABLE` and
`ABSENT` are not `PASS` (rule 13); writing the re-entry condition down is what
lets the check re-enter scope by itself rather than when somebody remembers.

### The severity scale, and why it is not the fleet's

The fleet rubric grades `P0` / `P1` / `P2`. **`P1`–`P5` is provenance in this
repository** (§15, `docs/SENSITIVITY.md`), so importing the fleet's spelling
would put two scales under one prefix — precisely the collision rule 14 exists
to prevent, and §15's complaint that `if level >= 3` reads correctly against
either. So severities here are `S0`–`S3`, and the crossing is stated once:

| Here | Fleet rubric | Means |
|---|---|---|
| `S0` | `P0` | Critical. Nothing installs. |
| `S1` | `P1` | High. Install-blocking; `tools/conform.py` fails the build while one is open. |
| `S2` | `P2` | Medium. Exploitable under a condition that is not remote. |
| `S3` | — | Low. A code smell, or a claim nothing enforces. |

---

## Rubric results

Verdicts are `PASS`, `FINDING`, `NOT-APPLICABLE`, `ABSENT`, `UNKNOWN`.

| check | what was examined | verdict | severity | evidence |
|---|---|---|---|---|
| `R1` | SQL construction — every `.py` in the tree, the `store/` query sites, the four files in `migrations/`, and the psql attack steps in `.github/workflows/tests.yml` | **PASS** | — | The store executes SQL now: 31 `execute`/`cursor` call sites across `store/`. Every value is parameterised (`%s` / `ANY(%s)`), and the one place dynamic identifiers are needed — `store/writing.py`'s insert — composes them through `psycopg.sql.Identifier`/`Placeholder`, never string interpolation. The two identifier-interpolations that remain are on trusted constants, not caller data: `store/migrate.py:149` interpolates the module constant `LEDGER`, and `store/roles.py:116` interpolates a caller-supplied `app_password` into `ALTER ROLE … PASSWORD` (which cannot be parameterised) only when one is passed, guarded against an embedded apostrophe. CI applies all four migrations to PostgreSQL 16 and then attacks the constraints directly — §10's *acceptance is mutation* — which is a stronger check than reading. |
| `R2` | Shell and process spawning — `subprocess`, `os.system`, `shell=True`, `popen`, across all 187 files | **PASS** | — | 12 process-spawn call sites in application and tooling code, all in `tools/` (`conform.py` 8, `purity.py` 3, `audit.py` 1), derived by grep and confirmed list-form `subprocess.run` with `sys.executable`, `git` or `psql` as `argv[0]`. 0 matches for `grep -rnE "shell\s*=\s*True\|os\.system\|os\.popen" --include=*.py` outside the decoys. `records/`, `store/` and `console/` spawn nothing — `tools/purity.py` asserts the inner ring's silence structurally rather than by reading. |
| `R3` | Path handling — every `open`, `read_text`, `write_text` and `Path` construction outside the decoys | **PASS** | — | Two paths arrive from outside the process, both on a command line an operator types: `craft/__main__.py`'s `argparse` file argument, and `console/__main__.py`'s lane/subject/column selectors (which are identifiers, not paths). There is no confinement boundary for either to escape — no upload directory, no per-user root, no served filesystem — so traversal has no meaning here yet. Every other path is derived from `__file__`. No symlink is followed deliberately and none is created. |
| `R4` | Credentials in version control — the full tracked file list and a keyword sweep | **PASS** | — | No key, token, password or credential in any tracked file. The sweep's matches are prose, classification rules (`records/classify.py` grades key material `L5`), a field name (`records/fees.py:434` `CARD_TOKEN = "card_token"`), and — the one worth stating — `store/roles.py`, which sets **no** app-role password unless a caller supplies one at deploy time: *"a default password in a source tree is a credential in a source tree"*, so `app_password=None` leaves authentication to the cluster's `pg_hba.conf`. No `.pem`, `.key` or `secrets` file is tracked. Related closed finding at `TM-ROOT-01`: the trust root was unexcluded, not committed. |
| `R5` | CORS — every listener and every HTTP surface | **NOT-APPLICABLE** | — | No HTTP server, no framework, no response headers. `manifest.json` declares `listeners: []` and `tools/sockets.py` scanning `records/`, `store/`, `tools/`, `console/`, `presentation/`, `surfaces/`, `voice.py` and `personas.py` finds zero listeners — the outbound scan finds only the one declared database connection (`store/connecting.py`). **Applies when** the first listener is declared — `§18` item 4, and `tools/manifest.py` fails the build if one appears undeclared. |
| `R6` | XSS — every rendering path, including the HTML surface `presentation/markup.py` and `surfaces/web/` | **PASS** | — | An HTML surface exists now (`presentation/markup.py`, rendered by `surfaces/web/render.py`), and every interpolated value passes through stdlib `html.escape` — every field value, label, badge, heading, referent, title, note, and the reader/timestamp. `tests/test_surfaces.py::test_a_value_containing_markup_is_escaped` feeds `<script>alert(1)</script>` through the surface and asserts it emerges `&lt;script&gt;`, and `test_neither_html_surface_emits_script` asserts no surface emits a `<script>` or `javascript:` at all — the guard shown to fail, not trusted (rule 19). Nothing serves the string: `manifest.json` declares no listener, so the document is generated but not remotely reachable. |
| `R7` | Unsigned or dynamic code execution — `eval`, `exec`, `pickle`, `marshal`, dynamic import | **PASS** | — | Zero calls to `eval`, `exec` or `__import__` in tracked source (the matches are all string literals in test banned-lists). `importlib.util` loads `tests/ablate.py` by path once so the harness can be tested without running it; `pickle` round-trips an enum member once in `tests/test_rungs.py` with no external input. The store deserialises JSON through `psycopg.types.json`, not `pickle`. Nothing is deserialised from outside the process, because nothing enters the process from outside it. Four suites assert their checkers never import what they inspect. |
| `R8` | Authentication on tool surfaces — MCP servers, RPC, any callable exposed beyond the process | **NOT-APPLICABLE** | — | No MCP server, no `sap/` directory, no exposed tool surface. The console is a local terminal loop reading `stdin`, not a served endpoint. The fleet's live `W-MCP-01` is inherited by an install that touches `willow-2.0`'s shared servers, and §10 records it as a live condition for this design — but nothing in this tree is that surface. **Applies when** serve mode or any parent-facing path lands, which §10 names as the trigger `W-MCP-01` itself declares. |
| `R9` | Exception handling — every `except` in the tree | **PASS** | — | Zero bare `except:` in code (the one grep match is prose in `records/inference.py` describing the anti-pattern it refuses). 17 `except Exception` outside tests, and every one is rule 13 as a handler — a failed source becomes `Source.UNKNOWN`, `Standing.UNKNOWN`, a named `*Unavailable`/`*Unknown` raise, or an `unavailable(...)` return, never an empty result. The two that end in `pass` are both `finally`-block cleanup — `store/session.py` resetting the acting-principal GUC and `console/__main__.py` closing the connection on exit — swallowing only so a cleanup failure cannot mask the caller's real exception, after the return value is already decided. |
| `R10` | Temp files and predictable paths | **PASS** | — | `TM-TMP-01` (a fixed sidecar name under `gettempdir()`) is closed, and at this pin every temporary tree uses `tempfile.mkdtemp`/`TemporaryDirectory`, which creates `0700`. The two sidecars in the repository root (`.ablate-lock`, `.ablate-inflight.json`) are predictable by design, are `.gitignore`d, and hold repository source rather than secrets. |
| `R11` | Races and locks — every check-then-act on a shared file | **PASS** | — | `TM-RACE-01` (the ablation lock) and `TM-RACE-02` (the conformance record's append rule) are both closed — each replaced with an atomic `O_EXCL` create. No threads, no `asyncio`, no `multiprocessing` in the tree, so concurrency reaches this code only through the filesystem, and the two filesystem races that existed are the two that were fixed. The store's own check-then-act on roles was closed by `TM-RACE`-class reasoning in S-1's `O_EXCL`-equivalent advisory-lock path, attacked in CI. |
| `R12` | `safe_integration.py` `status()` correctness | **NOT-APPLICABLE** | — | This is not a SAFE app: there is no `safe_integration.py`. `manifest.json` exists but is this repository's own surface/outbound/write-path declaration reconciled by `tools/manifest.py`, not a SAFE-app manifest carrying a `status()` entry point. **Applies when** the repository ships as a SAFE app, which `§18` item 4 owns. |
| `R13` | Entry point in the manifest is importable | **NOT-APPLICABLE** | — | `manifest.json` now exists and is reconciled against the tree (`tools/manifest.py`), but it declares surfaces, outbound and write-paths — not an importable entry-point module — so there is no declared entry point to import and check. The nearest decidable things hold: all 147 non-decoy Python files parse, and `tools/conform.py`'s `standalone-suites` row reports each suite carries a `__main__` runner that exits nonzero on failure. **Applies when** a manifest declares an entry point — `§18` item 4. |
| `R14` | Dependency pinning | **PASS** | — | `TM-DEPS-01` is closed. `requirements.txt` declares exactly two dependencies, each with an exact `==` pin and a stated reason, and `tools/imports.py` fails the build on any import that is not stdlib, one of those two declared roots, or local — the set of admitted third-party roots derived from the file so the gate and the declaration cannot drift. Derived at this pin: of 60 distinct top-level import roots across the 147 non-decoy files, exactly 2 resolve to a third party and both are declared. The supply-chain risk `R14` targets is now both bounded (two pinned deps) and enforced (the gate). |
| `R15` | Hardcoded developer home paths | **PASS** | — | Zero matches for `/home/`, `/Users/`, `C:\Users` or a `~/`-prefixed path in any tracked file outside the decoys. Every root is `Path(__file__).resolve().parent.parent`. No environment variable is read for a path; the store's DSN is read from the environment at run time and carries no path. |
| `R16` | Encryption at rest and key escrow — `records/` and `store/` scanned by AST for a sealing seam and its callers; `docs/ESCROW.md`; `store/sealing_plan.py` for which columns seal | **FINDING** | `S2` | The sealing seam exists (`records/atrest.py`) and is wired to the store (S-3: `migrations/004_sealed_payloads.sql`, `store/writing.py`). Escrow is **recorded and unrehearsed** — 3-of-5, `docs/ESCROW.md`, gate G-A — which is `UNKNOWN`, not a disposition (§5: *an untested key recovery is not escrow*). **Nothing durable is at rest**: `store/sealing_plan.py` derives exactly **1 of 120** classified columns as sealing (`lane_entry.payload`, on the record-write path), and the scan finds **0** non-test callers of that record-write path. S-4's console vertical is a caller — but of the narration/history path (`disclosure_log`, `reconciled_session`), which carries no sealed column — so it is a `narration_callers()` entry, not a `durable_callers()` one, and the fuse does not turn on it. **Becomes `S1` and fails the build** at the first non-test caller of the record-write path — the write surface after S-4 — without a dated rehearsal; §11.1's install acceptance is where the rehearsal is asserted for a deployment. See below. |
| `R17` | A structural no-egress test that fails when neutralised — `tools/purity.py`, `tools/conform.py::check_no_egress`, the ablation registry, and the newest conformance record | **PASS** | — | 4 mutations covering 4 required egress-detection sites, read out of `tests/ablate.py` by AST and derived at this pin (445 rows in the registry), and the newest conformance record (`2026-07-31T072706Z.md`) reports `no-egress=PASS` and `ablation=PASS`. See below. |

**Tally: 12 pass, 1 finding, 4 not-applicable, 0 absent, 0 unknown, of 17
checks** — counted from the verdict column above. (Was 7 pass / 4 findings / 6
not-applicable at the `d2817f2` pin: `R1` and `R6` entered scope as the store
and the HTML surface landed, `R14` closed, and `R10`/`R11` read `PASS` at this
later pin because their fixes are now ancestors of it rather than the carrying
commit — history in the findings table and the rows.)

Rule 17 applies to a document
describing its own table as much as to one describing a tree, so the figures are
re-derived from the table by
`tests/test_audit.py::test_the_tally_matches_the_table`, and
`test_the_document_records_all_seventeen_checks` fails if a row goes missing
entirely.

---

## Findings

| id | check | severity | status | one line |
|---|---|---|---|---|
| `TM-RACE-01` | R11 | `S2` | closed 2026-07-31 | The ablation lock was check-then-act, so it could be held twice. |
| `TM-TMP-01` | R10 | `S2` | closed 2026-07-31 | A fixed sidecar name under `gettempdir()`, written through symlinks. |
| `TM-RACE-02` | R11 | `S3` | closed 2026-07-31 | The conformance record's append-only rule was check-then-act too. |
| `TM-ROOT-01` | R4 | `S2` | closed 2026-07-31 | Nothing kept the trust root out of the tree. Mitigated by `.gitignore`; enforced by `.githooks/pre-commit` (per-clone install, one residual named below). |
| `TM-DEPS-01` | R14 | `S3` | closed 2026-07-31 | The stdlib-only posture was prose in docstrings; `tools/imports.py` now enforces it — every import resolves to stdlib, a `requirements.txt`-declared dependency, or a local module, or it fails the build. |

Every `TM-` finding raised against this tree is closed. The rubric rows above
read `PASS` for `R4`, `R10`, `R11` and `R14` because the pin names a tree that
already carries these fixes; this table is the history of what was found, and
`tests/test_audit.py::test_the_findings_summary_is_derived` counts it. The one
row that is not a pass — `R16` — is the added at-rest check, tracked in its own
section rather than as a `TM-` id, because what it waits on is a rehearsal, not a
patch.

### `TM-RACE-01` — the ablation lock could be held twice (`S2`, closed)

**File:** `tests/ablate.py`, `_acquire_lock()`

The lock exists because two concurrent ablations do not produce a wrong answer,
they produce a **wrong file**: the second run reads an already-mutated module as
its baseline and restores the mutation permanently. The docstring records that
this was hit for real.

The acquisition was `if LOCK.exists(): …` followed by `LOCK.write_text(...)`.
Two runs starting together both see no lock, both write their pid, and both walk
into the tree — the precise failure the lock was added to prevent, surviving
inside the fix for it. `tools/conform.py`'s `check_ablation` shells out to this
harness, so an ablation running beside a conformance run is the ordinary case
rather than a contrived one.

**Fixed** by making acquisition a single `os.open(..., O_CREAT | O_EXCL, 0o600)`
— atomic in the kernel — with the liveness check for a stale holder moved to
after that open has already failed.

**Why it is `S2` and not lower.** It corrupts source in the working tree, and it
does it in the component whose whole job is to decide whether the other guards
work. §10 names this family exactly: six defects in the verification apparatus
and zero in the code under verification.

### `TM-TMP-01` — a predictable sidecar path in a world-writable directory (`S2`, closed)

**File:** `tests/test_ablate.py`, `_sidecar()`

    return Path(tempfile.gettempdir()) / "ablate-selftest-inflight.json"

A constant name in `/tmp` is two defects. Two concurrent test processes collide
on it, which reintroduces `TM-RACE-01`'s shape at a different scale. And on a
shared machine a local user can pre-create that name as a symlink: `write_text`
follows links and creates with the process umask, so the write lands wherever
the link points, with whatever mode the umask allows.

**Fixed** with one `tempfile.mkdtemp(prefix="ablate-selftest-")` per test
process — an unpredictable name, created `0700` before anything is written into
it — removed at exit.

**Scope, honestly.** Test-only code, and it needs a local unprivileged attacker
on a shared box. It is graded `S2` rather than `S3` because the class is
arbitrary-file-write and the fix is four lines, not because the exposure here is
large.

### `TM-RACE-02` — the append-only conformance record was check-then-act (`S3`, closed)

**File:** `tools/conform.py`, `write()`

`if path.exists(): raise FileExistsError` and then `path.write_text(...)`.
Records are named to the second, so the window is exactly one second wide and
two runs started together would have one silently overwrite the other. That
matters more than the width suggests: the series is what answers *when did it
stop conforming*, and a record that can be overwritten answers only *does it*.

**Fixed** with `path.open("x")`, one atomic `O_EXCL` create raising the same
`FileExistsError`, so `tests/test_conform.py::test_a_record_is_never_overwritten`
now guards a mechanism rather than a convention.

> **And the fix introduced a defect of its own, caught by running it — recorded
> rather than quietly amended.** Rendering moved *inside* the `open("x")` block,
> and `render()` asks git whether the working tree is dirty. The empty record
> file, freshly created and untracked, **is** a dirty tree — so the first record
> written after the fix reported dirty from a clean checkout. It was discarded
> and is not in the series.
>
> The interesting part is why nothing caught it.
> `test_the_record_says_when_the_tree_was_dirty` calls `render()` directly, so
> the ordering it exists to depend on was invisible to it. And the obvious
> replacement — write a record, compare its flag against git — **passes under
> the defect**, because this repository is dirty whenever `tests/ablate.py` is
> mutating it and the two answers agree for the wrong reason. So
> `test_write_reports_the_tree_it_found_not_the_one_it_made` builds a clean git
> repository of its own to write into, which is the only place the two orderings
> disagree. That test is ablated.
>
> This is §10's family arriving one more time inside the same commit: a defect
> in the verification apparatus, not in the thing verified, and a first attempt
> at the test that could not fail.

### `TM-ROOT-01` — nothing kept the trust root out of the tree (`S2`, closed)

**File:** `.gitignore`

CLAUDE.md refusal 2 is *never commit the trust root* — `mcp_apps/`,
`_net_leases/`, and any grant material. Neither path was in `.gitignore`. Nothing
had been committed (checked: neither path exists in the working tree or in
`git ls-files`), so this was an unenforced refusal rather than an exposure.

**Fixed** by adding `mcp_apps/`, `_net_leases/`, `*.grant` and `*.lease`.

**The mitigation now has its enforcement half — rule 18.** `.gitignore` stops
`git add -A`; it does not stop `git add -f`, and it has no opinion about a file
already staged. `.githooks/pre-commit` is the gate: it reads the staged set —
what is actually about to be committed — and refuses the trust root there,
naming the path and refusal 2. `tests/test_trust_root_hook.py` runs it against
the force-add case `.gitignore` cannot catch and against a clean control, so the
guard is shown to fail rather than trusted to exist.

**The gitlink gap, closed 2026-07-31 after review.** The first patterns matched
`mcp_apps/*` but not a **bare** `mcp_apps` or `_net_leases` — the shape of a
submodule gitlink, a single index entry with nothing after the name — so a
force-added submodule pointer at the trust-root path slipped the gate. Both
automated review passes on PR #16 caught it. The patterns now match each
directory name four ways (exact, under, nested-exact, nested-under), and
`test_a_bare_gitlink_at_the_trust_root_path_is_refused` stages a genuine
mode-160000 entry and asserts the refusal.

**One residual, stated rather than closed over.** The hook is a gate only where
`core.hooksPath` points at it (`scripts/install-hooks.sh`, one act per clone).
Uninstalled, it is a ledger — so the enforcement is per-clone, not automatic
across every checkout, and a clone that never ran the install script is back to
the `.gitignore` mitigation alone. Wiring the install into a repository
bootstrap (a `make setup`, or CI asserting `core.hooksPath`) would make it
automatic; that step is not written, and this is where it is recorded.

### `TM-DEPS-01` — the stdlib-only posture was unenforced (`S3`, closed 2026-07-31)

**Files:** `tools/imports.py` (the gate), `tests/test_imports.py`,
`tests/fixtures/decoys/imports_undeclared.py`, `tools/conform.py`
(`check_stdlib_only`); originally the tree and the docstrings that assert the
posture.

`R14` in the fleet rubric is about lower-bound version specifiers pulling
unexpected code. **At the old `d2817f2` pin** the repository had no dependency
manifest at all and nothing to declare — so the supply-chain risk was absent by
construction and the finding was the other half: nothing *enforced* the posture,
so a later `import numpy` would have sailed in. Between that pin and this one the
tree gained `requirements.txt` and its two dependencies.

**Closed by making it a gate.** `tools/imports.py` reconciles every top-level
import against the standard library, the dependencies `requirements.txt`
declares (derived from the file, not hard-coded, so the gate and the
declaration cannot drift), and this repository's own modules. An undeclared
import is a build failure. `tools/drivers.py` answers *where* the one declared
driver may be imported; this answers *whether* an import is declared at all, and
the two compose. The decoy `imports_undeclared.py` imports `requests` and
`flask` and is caught; the mutation in `tests/ablate.py` that judges every
import resolved turns `tests/test_imports.py` red.

**A note on how this was found, because it is the finding.** The instruction
this audit first ran under said to `pip install -r requirements.txt`, on the
grounds that the repository had exactly one declared dependency. At that pin
there was no `requirements.txt` and no declared dependency. That is rule 17
arriving from outside the tree rather than from inside it — a figure carried in
prose that the code had not reached — and the fix is the gate that makes the
posture checkable rather than asserted.

---

## `R16` — encryption at rest, with the key escrowed

**Verdict today: `FINDING` at `S2`.** Reported by
`tools/audit.py::r16_at_rest`, and this section and the table row above agree
(`tests/test_audit.py::test_the_document_records_what_the_checks_report_today`
reads the table and would fail if they did not).

Four things are derived rather than assumed:

- **A sealing seam exists.** The check walks `records/` with `ast` and looks for
  any of 9 verbs a sealing module must expose (`seal_at_rest`, `wrap_dek`,
  `unseal_blob`, `rewrap`, …). `records/atrest.py` satisfies it.
- **It is wired.** S-3 routed the store's payload writes through it:
  `migrations/004_sealed_payloads.sql` gives `lane_entry.payload` a sealed form
  and tombstones the clear column, and `store/writing.py` seals before the
  `INSERT`. That is the difference between a mechanism and a gate (rule 18).
- **The boundary is the record-write path, not any store write, and it is
  derived not asserted.** `store/sealing_plan.py` reports **1 of 120** classified
  columns sealing at rest — `lane_entry.payload` — and it is on the record-write
  path (`store/writing.py`'s `insert_draft`/`seal_payloads`). The narration and
  history tables (`disclosure_log`, `reconciled_session`) carry **no** sealed
  column; they are protected by row-level security policies, not by at-rest
  encryption. So `tools/audit.py::AT_REST_BOUNDARY` turns the escrow fuse on the
  record-write path: `durable_callers()` counts callers of that path and finds
  **0**; `narration_callers()` reports the history writers separately and finds
  **1** (`console/session.py`, S-4). A surface that only reads, narrates and
  reconciles puts no escrow-dependent byte at rest, which is why S-4 landing did
  not flip this to `S1`.
- **The escrow disposition is recorded and unrehearsed.** Gate G-A picked `E-1`
  (3-of-5, five named custodian roles) and `docs/ESCROW.md` records zero
  rehearsals, deliberately. Rule 15 says every ask gets a dated disposition;
  §5's standard is that *an untested key recovery is not escrow*. So the check
  reads the threshold and the rehearsal dates out of that file and finds the
  first and not the second.

**The false positive this check is built to refuse.** `records/sealing.py` is in
the tree, is named sealing, and is not this: it is rule 10's named-human seal
over a machine draft, `hashlib` and no cipher anywhere in it. An `R16` matching
on filenames would report `PASS` today, over a repository that encrypts nothing
— the most flattering possible wrong answer. So the seam is recognised by the
verbs a sealing module exposes and never by its name, and
`tests/test_audit.py::test_the_human_seal_is_not_at_rest_sealing` asserts the
real module does not satisfy it. That test is ablated.

**The condition that ends `S2`,** stated so the check re-enters scope by itself:
the first module outside `tests/` that calls the store's **record-write** path —
the write surface after S-4 (an attendance mark, a human sealing a draft). At
that commit `R16` becomes an open `S1` finding unless `docs/ESCROW.md` carries a
dated rehearsal by then, and `tools/conform.py` fails the build while an `S1` is
open. §11.1's install acceptance is where the rehearsal is asserted for a real
deployment.

**Both sides of that transition are driven, not waited for.**
`tests/test_audit.py` builds a synthetic tree with a seam, a store and a
tests-only caller (`S2`), moves one file with a **record-write** call into a
deployment package (`S1`), dates a rehearsal in the escrow document (`PASS`), and
— the boundary S-4 settled — asserts a narration-only caller stays `S2`. The
condition is therefore a branch that has been shown to fire rather than one
nobody has run, which is what R17 is about, applied to R16.

## `R17` — a structural no-egress test that fails when neutralised

**Verdict today: `PASS`.** Reported by
`tools/audit.py::r17_no_egress_neutralised`.

The first half of `R17` — *does an egress test exist* — is the easy half and this
repository has had it: `tools/purity.py` parses the inner ring for anything that
reaches out, `tools/conform.py::check_no_egress` routes through it, and
`tests/fixtures/decoys/` points it at source that really does open sockets and
spawn `curl`.

**The second half is the check.** §10: *"nothing about a passing run
distinguishes* this fires correctly *from* this never fires." So `R17` does not
read the egress test at all. It reads two artifacts:

- **the ablation registry**, parsed out of `tests/ablate.py` by AST — never
  imported, because importing a mutation harness to ask what it mutates is one
  `main()` away from mutating the tree in order to inspect it;
- **the newest conformance record**, parsed for the `no-egress` and `ablation`
  rows.

And it requires coverage per **detection site**, not per count. The registry
could grow to two hundred rows with one of these unablated, which is the state
`records/sending.py` was in when one pattern matched two call sites and only the
first was ever mutated:

| site | anchor | what a mutation there restores |
|---|---|---|
| `tools/purity.py` | `rglob` | the scan globbed `*.py`, so a subpackage importing `socket` was invisible |
| `tools/purity.py` | `_DYNAMIC` | `__import__("socket")` carries a string where an `import` carries a name |
| `tools/purity.py` | `_SPAWN_MODULES` | `subprocess.run(["curl", …])` is a network call with no socket import in the file |
| `tools/conform.py` | `no-egress` | a scan of zero files must report `UNKNOWN`, not `PASS` (rule 13) |

All 4 are covered by exactly one mutation each — derived by AST from the 445-row
registry, not read off a label — and the newest record reports both rows `PASS`.
`tests/test_audit.py::test_a_registry_missing_an_egress_mutation_is_a_finding`
removes a required row and asserts the check turns `FINDING`, so the coverage
map is shown to fail rather than trusted.

**What `R17` does not establish.** That `tools/purity.py` detects egress it has
never been shown a decoy for. Its `EGRESS_MODULES` list is an allowlist's
inverse and can rot; a network module nobody thought of is egress nobody checks.
That limit belongs to `purity.py` and is recorded in `§16`'s terms there, not
resolved here.

## The recommendation to the fleet

§10's recommendation stands, and this document is the argument for it rather
than a substitute: **`R16` and `R17` belong in
`willow-2.0/SECURITY_AUDIT.md`, not in a local fork of it.** Adding them here
only would create exactly the vendored pair §16 records four failures of — a
fleet rubric and an app rubric, drifting, with nothing reconciling them.

Editing that repository is not this repository's act and has not been done. What
is recorded here is what an implementation of the two checks looks like once it
is written against real source: `R16` needs the seam recognised by API and not by
name and its fuse turned on the record-write path rather than any store write,
and `R17` needs the neutralisation half read out of a registry and a dated
record rather than asserted in prose. Both are portable; neither is specific to
this domain.

---

## What this audit does not cover

- **The fleet's own findings are inherited, not re-audited.** `W-MCP-01`,
  `W-SQL-01` and `W-EXC-01` are conditions on `willow-2.0`, and §10 records
  `W-MCP-01` as a live condition for any install that touches those servers.
  Nothing in this tree is that surface, and reading `willow-2.0`'s source was
  out of scope here.
- **`R1`–`R15` are judgements a human made by reading**, and the gate in
  `tools/conform.py` grades this document rather than re-deriving them. A check
  that re-derived them would be a second implementation of the audit with
  nothing reconciling the two (§16). The limit is named rather than hidden: this
  audit goes stale, and staleness is measured in days
  (`conform.STALE_AFTER_DAYS`) because *"N commits behind"* is not decidable
  from a tree.
- **No dynamic analysis of the application.** No console session or HTML render
  was executed against a running system as part of this audit; every verdict
  above is from source. The exception is the store, which is not read-only:
  `.github/workflows/tests.yml` applies all four migrations to PostgreSQL 16 and
  attacks the constraints, the lane seal, and the disclosure log directly on
  every push — a running-system check that is stronger than `R1` and is already
  someone else's.
