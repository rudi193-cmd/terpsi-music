# Security audit — terpsi-music

- **date** `2026-07-31`
- **commit** `d2817f289b63909e3fde6d198086c23178594273`
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
carrying this file — an audit cannot pin the commit it is part of. The fixes
recorded below land in that carrying commit, so a finding marked closed is
closed one commit after the tree the pin names.
`tools/conform.py::check_security_audit` checks the pin for the one thing it
decides: that this history contains it.

**Not a clean bill.** *Findings: 5 recorded, 4 closed, 1 open* — the four were
fixed in the commit that carries this file, and the figures are counted from the
findings table below by `tests/test_audit.py::test_the_findings_summary_is_derived`
rather than typed. Two checks report a state that is not a pass. A rubric run
that came back with nothing would be the outcome §10 warns about, not a good
one.

---

## What was examined

Every figure in this section was derived from the tree today; the command is
beside each one (rule 17).

| Surface | Size | How counted |
|---|---|---|
| Tracked Python | 95 files | `git ls-files '*.py' \| wc -l`, with this commit staged |
| Application modules | 19 in `records/` | `tools/purity.py` scan, the figure the conformance record carries |
| Checkers | 5 in `tools/` | `git ls-files 'tools/*.py' \| wc -l` |
| Prose tooling | 5 in `craft/`, plus `voice.py` and `personas.py` | `git ls-files 'craft/*.py' \| wc -l` |
| Suites | 33 files under `tests/` | `git ls-files 'tests/test_*.py' \| wc -l` (32) plus `tests/ablate.py` |
| Test functions | 538 collected | `python3 -m pytest -q --collect-only`, run today at the commit that carries this file |
| Ablation mutations | 136 rows | derived today: `tools/audit.py` parses `MUTATIONS` by AST and reports the length, and `tests/ablate.py` prints the same figure at the end of a run |
| Distinct top-level imports | 41, of which 0 are third-party | derived today by an AST walk over all 95 files, compared against `sys.stdlib_module_names` |

**There is no server, no database connection, no HTTP surface, no template
engine, and no dependency manifest.** Six of the fifteen fleet checks are aimed
at things this tree does not yet have — counted from the verdict column below,
and re-counted by `tests/test_audit.py::test_the_tally_matches_the_table` so the
figure cannot drift away from the table it describes. Each is recorded
`NOT-APPLICABLE` with the condition that ends that state. `NOT-APPLICABLE` and
`ABSENT` are not `PASS` (rule 13); the point of writing the condition down is
that the check re-enters scope by itself rather than when somebody remembers.

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

Verdicts are `PASS`, `FINDING`, `NOT-APPLICABLE`, `ABSENT`, `UNKNOWN`. Four of
the five are not a pass.

| check | what was examined | verdict | severity | evidence |
|---|---|---|---|---|
| `R1` | SQL construction — every `.py` in the tree, plus `docs/schema/001_lanes.proposed.sql` and the psql steps in `.github/workflows/tests.yml` | **NOT-APPLICABLE** | — | No code in this tree executes SQL: no driver is imported (0 of 40 top-level imports is a database module) and no cursor exists. The only SQL is DDL and the CI attack script, both static text with no interpolation from any caller. **Applies when** a module first opens a connection — `§18` item 3's migration is the commit. |
| `R2` | Shell and process spawning — `subprocess`, `os.system`, `shell=True`, `popen`, across all 95 files | **PASS** | — | 9 process-spawn call sites, derived by AST rather than by grep (`purity.scan_source` over every tracked file, `Reach.SPAWN`, excluding the decoys) — all `subprocess.run` with a list and `sys.executable` or `git` as `argv[0]`. 0 matches for `grep -rnE "shell\s*=\s*True\|os\.system\|os\.popen" --include=*.py`. All 9 sit in `tools/conform.py`, `tests/ablate.py`, `tests/test_ablate.py` and `tests/test_conform.py`; `records/` spawns nothing, which `tools/purity.py` asserts structurally rather than by reading. |
| `R3` | Path handling — every `open`, `read_text`, `write_text` and `Path` construction outside the decoys | **PASS** | — | One path arrives from outside the process: `craft/__main__.py:23`, an operator-named file on an `argparse` command line. There is no confinement boundary for it to escape — no upload directory, no per-user root, no served filesystem — so traversal has no meaning here yet. Every other path is derived from `__file__`. No symlink is followed deliberately and none is created. |
| `R4` | Credentials in version control — the full tracked file list and a keyword sweep | **PASS** | — | No key, token, password or credential in any tracked file. Derived: `grep -rniE "password\|secret\|token\|api[_-]?key\|passwd\|private_key\|BEGIN RSA\|credential" --include=*.py` excluding the decoys returns 8 lines, every one of them prose or a classification rule (`records/classify.py:98` classifies key material as `L5`). No `.pem`, `.key` or `secrets` file is tracked. Related finding at `TM-ROOT-01` below: the trust root was unexcluded, not committed. |
| `R5` | CORS — every listener and every HTTP surface | **NOT-APPLICABLE** | — | No HTTP server, no framework, no response headers. `tools/sockets.py` scans `records/`, `tools/`, `voice.py` and `personas.py` and finds zero listeners, which the conformance record reports as `UNKNOWN` rather than `PASS` for exactly this reason. **Applies when** the first listener is declared — `§18` item 4. |
| `R6` | XSS — every rendering path | **NOT-APPLICABLE** | — | No web frontend, no template engine, no HTML emitted anywhere in the tree. The only rendering is markdown written by `tools/conform.py` for its own records. **Applies when** a guardian-facing or judge-facing surface exists (`§4`). |
| `R7` | Unsigned or dynamic code execution — `eval`, `exec`, `pickle`, `marshal`, dynamic import | **PASS** | — | Zero calls to `eval`, `exec` or `__import__` in tracked source. `importlib.util` appears once, at `tests/test_ablate.py:39`, loading `tests/ablate.py` by path so the harness can be tested without running it. `pickle` appears once, at `tests/test_rungs.py:187`, round-tripping an enum member with no external input. Nothing is deserialised from outside the process, because nothing enters the process from outside it. Three suites already assert their checkers never import what they inspect; `tests/test_audit.py` now holds `tools/audit.py` to the same rule. |
| `R8` | Authentication on tool surfaces — MCP servers, RPC, any callable exposed beyond the process | **NOT-APPLICABLE** | — | No MCP server, no `sap/` directory, no exposed tool surface. The fleet's live `W-MCP-01` is inherited by an install that touches `willow-2.0`'s shared servers, and §10 records it as a live condition for this design — but nothing in this tree is that surface. **Applies when** serve mode or any parent-facing path lands, which §10 names as the trigger `W-MCP-01` itself declares. |
| `R9` | Exception handling — every `except` in the tree | **PASS** | — | Zero bare `except:`. Two `except Exception` outside `tests/`, and both are the opposite of the fleet's `W-EXC-01`: `records/sending.py:120` converts a failed restriction lookup into `Standing.UNKNOWN` with the exception in the message, and `voice.py:194` converts a raising guard into a refusal. Both are rule 13 implemented as a handler — the failure is reported as unknown, never as an empty result. |
| `R10` | Temp files and predictable paths | **FINDING** | `S2` | One fixed name in a world-writable directory: `TM-TMP-01`. Fixed in this commit. Everything else uses `tempfile.TemporaryDirectory`, which creates `0700`. The two sidecars in the repository root (`.ablate-lock`, `.ablate-inflight.json`) are predictable by design, are `.gitignore`d, and hold repository source rather than secrets. |
| `R11` | Races and locks — every check-then-act on a shared file | **FINDING** | `S2` | Two: `TM-RACE-01` and `TM-RACE-02`, both fixed in this commit. No threads, no `asyncio`, no `multiprocessing` in the tree, so concurrency reaches this code only through the filesystem — which is where both defects were. |
| `R12` | `safe_integration.py` `status()` correctness | **NOT-APPLICABLE** | — | This is not a SAFE app: there is no `safe_integration.py` and no app manifest. **Applies when** the repository ships as a SAFE app, which `§18` item 4 owns. |
| `R13` | Entry point in the manifest is importable | **NOT-APPLICABLE** | — | There is no manifest, so there is no declared entry point to check. The nearest decidable thing was checked and holds: all 95 tracked Python files parse (`ast.parse` over each, run today, 0 unparseable), and `tools/conform.py`'s `standalone-suites` row reports that each of the 32 suites has a `__main__` runner that exits nonzero on failure. **Applies when** a manifest exists — `§18` item 4. |
| `R14` | Dependency pinning | **FINDING** | `S3` | `TM-DEPS-01`. There is no `requirements.txt`, no `pyproject.toml`, and no lock file — and no third-party import either: derived today, of 41 distinct top-level imports across 95 files, 0 resolve outside `sys.stdlib_module_names` and this repository's own packages. So the supply-chain risk `R14` targets is absent by construction, and the finding is the other half: nothing enforces the stdlib-only posture, which is asserted in 57 files as counted from the tree today. Open. |
| `R15` | Hardcoded developer home paths | **PASS** | — | Zero matches for `/home/`, `/Users/`, `C:\Users` or a `~/`-prefixed path in any tracked file. Derived: `grep -rnE "/home/\|/Users/\|C:\\\\Users\|~/[a-zA-Z]" --include=*.py`. Every root is `Path(__file__).resolve().parent.parent`. No environment variable is read for a path. |
| `R16` | Encryption at rest and key escrow — `records/` scanned by AST for a sealing seam; `docs/ESCROW.md`; `tools/purity.py` over `records/` **and `store/`**; the store's write path scanned for non-test callers | **FINDING** | `S2` | ~~No at-rest sealing entry point exists~~ **The seam landed 2026-07-31** (`records/atrest.py`, §9 foundation 3) and **is wired to the store the same day** (S-3: `migrations/004_sealed_payloads.sql`, `store/writing.py`). Escrow policy is now **recorded and unrehearsed** — 3-of-5, `docs/ESCROW.md`, gate G-A — which is `UNKNOWN`, not a disposition (§5: *an untested key recovery is not escrow*). **Nothing durable is at rest**, and that is the judgement this row now turns on rather than a raw write count: `purity.writes()` finds 8 sites in `store/` and **0 non-test callers of that path**, so every byte it has written went into a database `tests/cluster.py` created and dropped inside one module. The boundary is stated in `tools/audit.py::AT_REST_BOUNDARY` and both sides of it are driven in `tests/test_audit.py`. **Becomes `S1` and fails the build** at the first non-test caller of the store's write path (`PLAN-STORE`'s S-4) without a dated rehearsal; §11.1's install acceptance is where the rehearsal is asserted for a deployment. The first version of this row flipped to `S1` on seam presence alone — corrected when F3 merged, because the condition above is what this row had promised. |
| `R17` | A structural no-egress test that fails when neutralised — `tools/purity.py`, `tools/conform.py::check_no_egress`, the ablation registry, and the newest conformance record | **PASS** | — | 4 mutations covering 4 required egress-detection sites, read out of `tests/ablate.py` by AST and derived today (136 rows in the registry), and the newest conformance record reports `no-egress=PASS` and `ablation=PASS`. See below. |

**Tally: 7 pass, 4 findings, 6 not-applicable, 0 absent, 0 unknown, of 17 checks** — counted from the verdict column above. (Was 3 findings and 1 absent until 2026-07-31: R16 moved when the at-rest seam landed, per its own condition — history in the R16 row.)

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
| `TM-DEPS-01` | R14 | `S3` | open | The stdlib-only posture is prose in docstrings; nothing checks it. |

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
already staged. `.githooks/pre-commit` (written 2026-07-31) is the gate: it
reads the staged set — what is actually about to be committed — and refuses the
trust root there, naming the path and refusal 2. `tests/test_trust_root_hook.py`
runs it against the force-add case `.gitignore` cannot catch and against a
clean control, so the guard is shown to fail rather than trusted to exist.

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

### `TM-DEPS-01` — the stdlib-only posture is unenforced (`S3`, open)

**Files:** the tree; and the docstrings that assert the posture, counted today
by reading each tracked file for the phrase — 57 files.

`R14` in the fleet rubric is about lower-bound version specifiers pulling
unexpected code. This repository inverts the problem: there is no dependency
manifest at all, and today there is nothing to declare.
Derived today by an AST walk: 0 of 41 distinct top-level imports across 95 tracked files resolve outside the standard library and this repository's own packages.

**A note on how this was found, because it is the finding.** The instruction
this audit ran under said to `pip install -r requirements.txt` first, on the
grounds that the repository has exactly one declared dependency. There is no
`requirements.txt` and there are no declared dependencies. That is rule 17
arriving from outside the tree rather than from inside it, and it is the same
defect the tree keeps recording: a figure carried in prose that the code moved
past, or in this case never reached.

The finding proper is that no check asserts the posture, which as counted from
the tree today is asserted in 57 tracked Python
files. `tools/purity.py` catches an import of `requests`, `httpx` or
`boto3` — but only because those are network modules on its egress list. A
`pyyaml`, a `jinja2`, or a `pytest` import in a shipped module would pass every
gate in this tree.

**Not fixed here, deliberately.** The obvious fix — walk every import against
`sys.stdlib_module_names` and fail on a stranger — is a new conformance check
with its own ablation, and adding it inside an audit commit would mean the audit
shipped a guard nobody reviewed as a guard. Left open with the fix named.

**Severity `S3`** because the exposure today is zero and the risk is future
drift. It is the kind of finding that becomes `S1` the first time an install
runs `pip install` against something this repository did not write down.

---

## `R16` — encryption at rest, with the key escrowed

**Verdict today: `FINDING` at `S2`.** Reported by
`tools/audit.py::r16_at_rest`.

**This section said `ABSENT` until 2026-07-31 and disagreed with its own table
row, which had already moved to `FINDING`/`S2` when the seam landed.** The
reconciler between this document and the live checks
(`tests/test_audit.py::test_the_document_records_what_the_checks_report_today`)
reads the *table*, so the prose drifted for exactly as long as nobody read it —
the pair-without-a-middle shape §16 is about, inside the audit document itself.
Recorded rather than quietly corrected.

Four things are derived rather than assumed:

- **A sealing seam exists.** The check walks `records/` with `ast` and looks for
  any of 9 verbs a sealing module must expose (`seal_at_rest`, `wrap_dek`,
  `unseal_blob`, `rewrap`, …). `records/atrest.py` satisfies it.
- **It is wired.** S-3 routed the store's payload writes through it:
  `migrations/004_sealed_payloads.sql` gives `lane_entry.payload` a sealed form
  and tombstones the clear column, and `store/writing.py` seals before the
  `INSERT`. That is the difference between a mechanism and a gate (rule 18), and
  it changed on this commit.
- **Nothing durable is at rest**, which is the judgement this row turns on and is
  stated in the check's own terms at `tools/audit.py::AT_REST_BOUNDARY`: *at rest
  is a byte that outlives the process that wrote it.* `purity.writes()` finds 8
  sites in `store/`, and the scan for non-test callers of that path finds **0**,
  so the only databases those writes have ever reached were created and dropped
  inside a single test module. Counting them would make this an install-blocking
  `S1` that no commit can clear — what clears it is five people in a room — and a
  gate nobody can turn green is a gate everybody learns to ignore.
- **The escrow disposition is recorded and unrehearsed.** Gate G-A picked `E-1`
  (3-of-5, five named custodian roles) on 2026-07-31 and `docs/ESCROW.md` records
  zero rehearsals, deliberately. Rule 15 says every ask gets a dated disposition;
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
the first module outside `tests/` that calls the store's write path —
`docs/PLAN-STORE.md`'s S-4, the TUI vertical. At that commit `R16` becomes an
open `S1` finding unless `docs/ESCROW.md` carries a dated rehearsal by then, and
`tools/conform.py` fails the build while an `S1` is open. §11.1's install
acceptance is where the rehearsal is asserted for a real deployment.

**Both sides of that transition are driven, not waited for.**
`tests/test_audit.py` builds a synthetic tree with a seam, a store and a
tests-only caller (`S2`), moves one file into a deployment package (`S1`), and
dates a rehearsal in the escrow document (`PASS`). The condition is therefore a
branch that has been shown to fire rather than one nobody has run — which is what
R17 is about, applied to R16.

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

All 4 are covered by exactly one mutation each — derived by AST from the 136-row
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
name, and `R17` needs the neutralisation half read out of a registry and a dated
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
- **No dynamic analysis.** Nothing here was executed against a running system,
  because there is no running system. Every verdict above is from source.
- **The DDL was read, not attacked.** `.github/workflows/tests.yml` executes
  `docs/schema/001_lanes.proposed.sql` against PostgreSQL 16 and attacks eight
  constraints on every push; that is a stronger check than `R1` and it is
  somebody else's, already running.
