"""R16 and R17 — the two checks the fleet's fifteen-check rubric does not have.

`willow-2.0/SECURITY_AUDIT.md` is fifteen numbered checks and ARCHITECTURE §10
adopts it as an install gate rather than a document. §10 also names what it is
missing, in its own words:

> *"It has **no check for encryption at rest** and **no check that an egress
> test exists**. Both are the point of this design."*

So this module is those two, written as code because §10's own argument is that
a rubric run by hand is a document. The recommendation that they be added to the
fleet rubric is recorded in `docs/SECURITY-AUDIT.md`; editing another repository
is not this repository's act.

**R16 — data at rest is encrypted, with the key escrowed (§5).**
Written against the seam at-rest sealing will land on rather than against the
sealing itself, which is being built elsewhere. Two halves, and §5 is explicit
that the second is the larger gap: *"an untested restore is not a backup, and an
untested key recovery is not escrow."* A sealed store whose key is one file on
one director's box is not a pass; it is the failure mode §5 says ends a program.

*The false positive this check exists to refuse.* `records/sealing.py` is in the
tree and it is **not** at-rest sealing — it is rule 10's human seal over a
machine draft, `hashlib` and no cipher anywhere in it. A name-matching R16 would
report PASS today over a module that encrypts nothing. So the seam is recognised
by the verbs a sealing module must expose, never by its filename, and
`tests/test_audit.py` asserts `records/sealing.py` does not satisfy it.

**R17 — a structural no-egress test exists and fails when neutralised (§6, §10).**
The first half is easy and this repository already passes it: `tools/purity.py`
parses the inner ring for anything that reaches out, `tools/conform.py`'s
`check_no_egress` routes through it, and `tests/fixtures/decoys/` points it at
source that really does open sockets.

**The second half is the whole check**, and it is the half §10 says has been
breaking: *"nothing about a passing run distinguishes this fires correctly from
this never fires."* So R17 does not read the egress test. It reads the
**ablation registry** — is there a mutation that disables each way the egress
checker detects egress — and the **conformance record** — did the harness report
those mutations caught. Both are artifacts in the tree, parsed. Neither is prose
(rule 17), and neither is this module's own opinion of itself.

`UNKNOWN`, `NOT-APPLICABLE` and `ABSENT` are never `PASS` (rule 13). The
severity scale is `S0`–`S3` and the reason it is not `P0`–`P2` as the fleet
rubric spells it is in `docs/SECURITY-AUDIT.md`: `P1`–`P5` is provenance here
(§15), and a second meaning for one prefix is the collision rule 14 exists to
stop.

Stdlib only. No network. Parses; never imports what it inspects.

    python3 tools/audit.py
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

AUDIT_DOC = ROOT / "docs" / "SECURITY-AUDIT.md"
ESCROW_DOC = ROOT / "docs" / "ESCROW.md"
REGISTRY = ROOT / "tests" / "ablate.py"
CONFORMANCE = ROOT / "docs" / "conformance"


class Verdict(Enum):
    PASS = "PASS"
    FINDING = "FINDING"
    NOT_APPLICABLE = "NOT-APPLICABLE"   # cannot apply yet, with the condition
    ABSENT = "ABSENT"                   # the thing checked does not exist
    UNKNOWN = "UNKNOWN"                 # nothing here can decide it


class Severity(Enum):
    """Prefixed on purpose, and deliberately not `P`.

    The fleet rubric grades `P0`/`P1`/`P2`. `P1`–`P5` is provenance in this
    repository (§15), two scales would share one prefix, and §15's whole
    complaint is that `if level >= 3` reads correctly against either.
    """

    NONE = "—"
    S3 = "S3"    # low: a code smell, or a claim nothing enforces
    S2 = "S2"    # medium: exploitable under a condition that is not remote
    S1 = "S1"    # high: install-blocking
    S0 = "S0"    # critical


#: What `check_security_audit` treats as an open finding that fails a build.
FAILING = (Severity.S0, Severity.S1)


@dataclass(frozen=True)
class Result:
    id: str
    title: str
    verdict: Verdict
    severity: Severity
    evidence: str
    #: For `NOT-APPLICABLE` and `ABSENT`: what would make this check apply.
    condition: str = ""

    @property
    def passed(self) -> bool:
        """Rule 13. Four of the five states are not a pass, including the two
        that read most like one."""
        return self.verdict is Verdict.PASS


# --- R16 -------------------------------------------------------------------

#: The verbs a module has to expose before it is at-rest sealing rather than
#: something else called sealing. Recognition is by API, never by filename:
#: `records/sealing.py` is rule 10's human seal and satisfies none of these.
AT_REST_VERBS = frozenset({
    "seal_at_rest", "unseal_at_rest", "encrypt_at_rest", "decrypt_at_rest",
    "wrap_dek", "unwrap_dek", "rewrap", "seal_blob", "unseal_blob",
})

#: `\b\d+-of-\d+\b` in the escrow disposition. §5 asks for Shamir 2-of-3 or
#: 3-of-5; the check asks only that a threshold is stated, not which.
_SPLIT = re.compile(r"\b(\d+)-of-(\d+)\b")

#: §5: *"an untested key recovery is not escrow."* A disposition with no dated
#: rehearsal is a plan.
_REHEARSED = re.compile(r"\brehears\w*\b[^\n]{0,80}?(\d{4}-\d{2}-\d{2})", re.I)


def at_rest_seam(where: Optional[Path] = None) -> Tuple[Tuple[str, str], ...]:
    """`(module, verb)` for every at-rest sealing entry point in the tree.

    Parses; never imports. A module that reaches the network on import is not
    something a security check should be executing to find that out.
    """
    base = where if where is not None else ROOT / "records"
    out: List[Tuple[str, str]] = []
    if not base.exists():
        return ()
    for py in sorted(base.rglob("*.py")):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        rel = str(py.relative_to(ROOT)) if str(py).startswith(str(ROOT)) else str(py)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name in AT_REST_VERBS:
                out.append((rel, node.name))
    return tuple(out)


def escrow_disposition(doc: Optional[Path] = None) -> Tuple[bool, str]:
    """`(disposed, why)` for the key-escrow half of R16.

    Rule 15: every ask gets a dated disposition. A key-recovery plan with no
    threshold and no dated rehearsal is the ask, not the disposition.
    """
    path = doc if doc is not None else ESCROW_DOC
    facts = escrow_facts(path)
    if not facts.exists:
        return False, f"{path.name} does not exist; §5 records escrow as the largest gap"
    if not facts.threshold:
        return False, f"{path.name} states no k-of-n threshold"
    if not facts.rehearsed:
        return False, (f"{path.name} states {facts.threshold} and no dated rehearsal; "
                       "§5: an untested key recovery is not escrow")
    return True, (f"{path.name}: {facts.threshold}, {facts.holders} holder(s), "
                  f"rehearsed {facts.rehearsals[-1]}")


#: Where the store's write path lives. R16 has to see it — `records/` is pure by
#: construction (`tools/purity.py` holds it to zero writes), so a check looking
#: only there would report *nothing is stored* forever, no matter how much this
#: application stored.
STORE = ROOT / "store"

#: Directories whose callers are not a deployment. A write path exercised only
#: from here reaches a database that is created and dropped inside one test
#: module — see `AT_REST_BOUNDARY`.
_NOT_A_DEPLOYMENT = ("tests/", "docs/")


@dataclass(frozen=True)
class EscrowFacts:
    """What `docs/ESCROW.md` actually says, parsed. **No judgement in here.**

    Read by `tools/audit.py`'s R16 and by `tools/conform.py`'s `key-escrow` row,
    and read by both from **one** parser: the document and the conformance row
    are a pair, and two regexes over one file is the shape §16 is about. The
    judgement — which of `records/atrest.py`'s `EscrowState` this amounts to —
    is made once, in `conform.py`, from these facts.
    """

    exists: bool
    threshold: str          # "3-of-5", or "" when none is stated
    holders: int            # custodians the document enumerates
    rehearsals: Tuple[str, ...] = ()   # ISO dates, in the order they appear

    @property
    def recorded(self) -> bool:
        """A policy is recorded when a threshold is stated. Names and dates are
        install-acceptance acts (§11.1) and their absence is not its absence."""
        return self.exists and bool(self.threshold)

    @property
    def rehearsed(self) -> bool:
        return bool(self.rehearsals)


#: A custodian row in the share table: `| 1 | Program director | … |`.
_SHARE_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", re.M)


def escrow_facts(doc: Optional[Path] = None) -> EscrowFacts:
    """`docs/ESCROW.md`, as facts. Derived from the file, never restated."""
    path = doc if doc is not None else ESCROW_DOC
    if not path.exists():
        return EscrowFacts(False, "", 0, ())
    text = path.read_text(encoding="utf-8")
    split = _SPLIT.search(text)
    holders = {int(m.group(1)) for m in _SHARE_ROW.finditer(text)}
    return EscrowFacts(
        exists=True,
        threshold=split.group(0) if split else "",
        holders=len(holders),
        rehearsals=tuple(m.group(1) for m in _REHEARSED.finditer(text)),
    )


def anything_at_rest(where: Optional[Path] = None) -> int:
    """How many places the inner ring puts a byte on a disk.

    Derived from `tools/purity.py` rather than asserted, and it is what
    separates *"nothing is encrypted"* from *"nothing is stored"*. The first is
    a finding; the second is why R16 is `ABSENT` today rather than `FINDING`.
    """
    from purity import writes  # noqa: E402

    return len(writes([where if where is not None else ROOT / "records"]))


# --- the at-rest boundary, stated ------------------------------------------

#: **What R16 counts as "at rest", in this check's own terms.**
#:
#: *At rest* is a byte that outlives the process that wrote it. `store/` is a
#: write path — `purity.writes()` finds statements handed to a database in it —
#: but **a write path is not a store at rest until something durable is on the
#: other end of it.** In this tree every caller of that path is under `tests/`,
#: and `tests/cluster.py` creates a database per test module and drops it in
#: `__exit__`; the bytes are gone before the run that wrote them ends. Counting
#: those as records at rest would make CI go red waiting for a key ceremony that
#: happens in a room with five people in it (`docs/ESCROW.md`), which is a gate
#: nobody can turn green and therefore a gate everybody learns to ignore.
#:
#: So R16 reports the store's write sites and holds its *durable* count at the
#: number of non-test callers of that path, which is derived below and is zero.
#:
#: **The commit that flips it is named rather than left to be noticed**: the
#: first module outside `tests/` that calls the store's **record-write** path.
#: S-4's read-first vertical (`docs/PLAN-STORE.md`) deliberately is not that
#: commit — it reads, narrates and reconciles, and none of those puts a sealed
#: payload at rest (see the two verb sets below). The commit that flips R16 is
#: the *write* surface after it — an attendance mark, a human sealing a draft —
#: at which `durable` becomes nonzero, R16 becomes an open `S1` unless
#: `docs/ESCROW.md` carries a dated rehearsal by then, and §11.1's install
#: acceptance is where that rehearsal is asserted for a real deployment.
#: `tests/test_audit.py` exercises both sides of that transition, and the
#: narration-only side, against a synthetic tree — branches shown to fire rather
#: than waiting to.
#:
#: Stated as a **definition plus a rule**, and deliberately not as a claim about
#: this tree: the tree-specific half is measured in each result's evidence and
#: moves, while this sentence is what the measurement means and must not.
AT_REST_BOUNDARY = (
    "at rest = a byte that outlives the process that wrote it. The escrow fuse "
    "turns on the RECORD-write path (store.writing: a lane_entry draft and its "
    "sealed payload), not the narration/history path (disclosure_log, "
    "reconciled_session), which carries no sealed column — store/sealing_plan.py "
    "derives exactly one in the whole schema, lane_entry.payload, and it is on "
    "the record-write path. A write path is not a store at rest until a non-test "
    "caller drives the record-write path: tests/cluster.py creates a database per "
    "module and drops it. The first non-test record-write caller — the write "
    "surface after S-4 — makes the store's sealed payloads durable and R16 S1 "
    "without a dated rehearsal; a read-first surface that only narrates and "
    "reconciles (S-4) does not. §11.1's install acceptance is where the rehearsal "
    "is asserted for a deployment"
)

#: **The record-write path — the escrow-relevant one.** These writes put a
#: *record* at rest: a `lane_entry` draft, and through `seal_payloads` its sealed
#: payload — the one column `store/sealing_plan.py` derives as sealed in the whole
#: schema. A non-test caller of this path makes a sealed payload durable, which is
#: the commit R16's escrow fuse turns on. Recognised by an import of the writing
#: module or a call to one of its verbs, read by AST.
_WRITE_PATH_MODULE = "store.writing"
_WRITE_PATH_VERBS = frozenset({"insert_draft", "seal_payloads", "apply_all"})

#: **The narration/history path — deliberately NOT a record at rest.** `serve_field`
#: and `narrate` write `disclosure_log`; `land_reconciliation` writes
#: `reconciled_session`. Both are append-only *history* (§7.1: "the disclosure
#: log ... and reconciled sessions are history"), and neither carries a sealed
#: column — the one sealed column is on the record-write path above. So a surface
#: that only reads, narrates and reconciles (S-4's read-first vertical) puts no
#: escrow-dependent byte at rest, and R16 stays `S2` rather than flipping to `S1`
#: on it; the fuse still trips on the first record-write caller. `narration_callers()`
#: reports these separately so the evidence can say what it saw rather than fold
#: them into the durable count. **This is the boundary S-4 had to settle out loud
#: rather than by picking a number** (`docs/PLAN-STORE.md` S-4, and the report).
_NARRATION_MODULES = frozenset({"store.narration", "store.reconcile"})
_NARRATION_VERBS = frozenset({"narrate", "serve_field", "land_reconciliation"})


def _scan_callers(base: Path, store: Path, modules: frozenset,
                  verbs: frozenset) -> Tuple[Tuple[str, str], ...]:
    """`(module, how)` for every non-test module importing `modules` or calling
    `verbs`. The shared body of `durable_callers` and `narration_callers`, so the
    record-write scan and the narration scan cannot drift in how they read a tree.
    """
    out: List[Tuple[str, str]] = []
    skip = {store.resolve()}
    for py in sorted(base.rglob("*.py")):
        relpath = py.relative_to(base)
        rel = str(relpath)
        # Never count a file under a dot-directory: `.git`, and — the case that
        # bit — `.claude/worktrees/`, where an agent's checkout carries its own
        # copy of `store/`. Those copies are not deployment callers; counting
        # them flipped R16 to a false S1 whenever a worktree was present. The
        # skip mirrors `tools/manifest.py::_all_python`, and `.gitignore`
        # already excludes `.claude/worktrees/` for the same reason.
        if any(part.startswith(".") for part in relpath.parts):
            continue
        if rel.startswith(_NOT_A_DEPLOYMENT) or py.parent.resolve() in skip:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in modules:
                out.append((rel, f"imports {node.module}"))
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name in modules:
                        out.append((rel, f"imports {a.name}"))
            elif isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name in verbs:
                    out.append((rel, f"calls {name}()"))
    by_module: Dict[str, List[str]] = {}
    for module, how in sorted(set(out)):
        by_module.setdefault(module, []).append(how)
    return tuple((m, ", ".join(hows)) for m, hows in sorted(by_module.items()))


def durable_callers(where: Optional[Path] = None,
                    store: Optional[Path] = None) -> Tuple[Tuple[str, str], ...]:
    """`(module, how)` for every non-test module that reaches the **record-write**
    path — the escrow-relevant one.

    Zero of these means the write path exists and nothing in a deployment writes a
    record through it, which is the whole of `AT_REST_BOUNDARY`. Derived from the
    tree by AST so that the day somebody wires a write surface to the store, this
    check notices without anybody remembering to come back and edit it.

    **One entry per module**, with its reasons joined. A file that both imports
    the module and calls its verb is one caller; counting it twice made the
    evidence read *"2 non-test caller(s) (app/main.py, app/main.py)"*, which is a
    number a reader would go looking for a second file behind.
    """
    base = where if where is not None else ROOT
    return _scan_callers(base, store if store is not None else STORE,
                         frozenset({_WRITE_PATH_MODULE}), _WRITE_PATH_VERBS)


def narration_callers(where: Optional[Path] = None,
                      store: Optional[Path] = None) -> Tuple[Tuple[str, str], ...]:
    """`(module, how)` for every non-test module that narrates or reconciles.

    **Reported, and deliberately not counted as durable** — see `_NARRATION_VERBS`
    and `AT_REST_BOUNDARY`. A non-empty result here with `durable_callers()` still
    empty is exactly S-4: a read-first surface writes history (`disclosure_log`,
    `reconciled_session`) and no sealed payload, so R16 stays `S2`. Enumerated so
    the evidence names them rather than saying nothing wrote anything.
    """
    base = where if where is not None else ROOT
    return _scan_callers(base, store if store is not None else STORE,
                         _NARRATION_MODULES, _NARRATION_VERBS)


def store_writes(where: Optional[Path] = None) -> int:
    """Write sites in the store's package. A path, not yet a store at rest."""
    from purity import writes  # noqa: E402

    base = where if where is not None else STORE
    return len(writes([base])) if base.exists() else 0


def r16_at_rest(records: Optional[Path] = None,
                escrow: Optional[Path] = None,
                store: Optional[Path] = None,
                tree: Optional[Path] = None) -> Result:
    """R16 — data at rest is encrypted, with the key escrowed (§5).

    **The at-rest count is the durable one, and `AT_REST_BOUNDARY` is where that
    word is defined.** Until S-1 there was no store and the question did not
    arise; `store/` now carries write sites, and whether they count as records at
    rest is the judgement this check has to make out loud rather than by picking
    a number. It is made by asking the tree who calls that path: nobody outside
    `tests/`, so nothing durable is written, so the count is zero and the
    condition names the commit that changes it.
    """
    title = "data at rest is encrypted, with the key escrowed"
    seam = at_rest_seam(records)
    disposed, why = escrow_disposition(escrow)
    ring_writes = anything_at_rest(records)
    staged = store_writes(store)
    callers = durable_callers(tree, store)
    narrators = narration_callers(tree, store)
    durable = ring_writes + (staged if callers else 0)

    # Said the same way in every branch, so a reader comparing two runs is
    # comparing the same measurement.
    narration_note = (
        f"; {len(narrators)} narration/reconcile caller(s)"
        + (f" ({', '.join(m for m, _ in narrators[:3])})" if narrators else "")
        + " write append-only history (disclosure_log, reconciled_session), which "
          "carries no sealed column and is not a record at rest"
        if narrators else "")
    measured = (
        f"purity.writes(): {ring_writes} site(s) in records/, {staged} in store/; "
        f"{len(callers)} non-test caller(s) of the store's record-write path"
        + (f" ({', '.join(m for m, _ in callers[:3])})" if callers
           else ", so those {} write(s) reach a database created and dropped "
                "inside one test module".format(staged))
        + narration_note
        + f". Boundary: {AT_REST_BOUNDARY}")

    if not seam and not durable:
        return Result(
            "R16", title, Verdict.ABSENT, Severity.NONE,
            f"no at-rest sealing entry point in records/ (looked for "
            f"{len(AT_REST_VERBS)} verb(s) by AST, found 0) and nothing durable "
            f"at rest to seal. records/sealing.py is rule 10's human seal, not a "
            f"cipher, and is deliberately not counted. {measured}. Escrow: {why}",
            condition="the first module that writes a record durably. R16 "
                      "becomes an open S1 at that commit unless sealing lands with it",
        )
    if not seam:
        return Result(
            "R16", title, Verdict.FINDING, Severity.S1,
            f"{durable} durable write site(s) and no at-rest sealing entry "
            f"point: records hit the disk in the clear. {measured}. Escrow: {why}",
        )
    if not disposed and not durable:
        # The seam landed ahead of the store, which is this repository's
        # deliberate ordering (item 4 note iii): the mechanism exists and no
        # master has been minted, no record is durably at rest, so a lost key
        # file cannot yet destroy anything. This check's own stated condition —
        # "R16 becomes an open S1 the day anything writes a record to disk" —
        # was written before the seam existed and the first implementation
        # flipped on seam presence instead. Caught when F3 merged: the doc's
        # reconciler went red on a severity the condition never promised.
        #
        # S-3 is the second time it needed saying more precisely. `store/` now
        # writes, so "anything writes a record to disk" reads as satisfied on a
        # careless count — and it is not, because the only writes are into
        # databases that are dropped at the end of the module that made them.
        #
        # S-4 is the third. The read-first vertical narrates and reconciles from a
        # deployment module (console/), so "a non-test caller drives the store's
        # writes" now reads as satisfied — and it is not, because narration and
        # reconciliation write history that carries no sealed column. The condition
        # names the RECORD-write path, which is the one the escrow ceremony guards.
        return Result(
            "R16", title, Verdict.FINDING, Severity.S2,
            f"sealing at {', '.join(m for m, _ in seam)}, nothing durably at "
            f"rest yet, and no rehearsed escrow disposition — {why}. {measured}",
            condition="the first non-test caller of the store's RECORD-write path "
                      "(store.writing) — the write surface after S-4, not S-4's "
                      "read-first vertical, which only narrates and reconciles. "
                      "This finding becomes S1 at that commit unless a recorded, "
                      "rehearsed escrow disposition exists by then; §11.1's install "
                      "acceptance is where the rehearsal is asserted for a deployment",
        )
    if not disposed:
        return Result(
            "R16", title, Verdict.FINDING, Severity.S1,
            f"sealing at {', '.join(m for m, _ in seam)}, {durable} durable "
            f"write site(s), and no rehearsed escrow disposition — {why}. §5: a "
            f"single file loss destroys every record, irrecoverably, by design. "
            f"{measured}",
        )
    return Result(
        "R16", title, Verdict.PASS, Severity.NONE,
        f"{len(seam)} sealing entry point(s): "
        f"{', '.join(f'{m}:{v}' for m, v in seam)}. Escrow: {why}. {measured}",
    )


# --- R17 -------------------------------------------------------------------

#: The ways `tools/purity.py` detects egress, and for each one the anchor a
#: mutation must touch to disable it. **This is the load-bearing table.** R17
#: is not "are there mutations"; it is "is each detection path individually
#: shown to fail", and a registry can grow to a hundred rows while leaving one
#: of these unablated — which is the shape `records/sending.py` was in when a
#: pattern matched two sites and only the first was ever mutated.
REQUIRED_EGRESS_SITES: Tuple[Tuple[str, str, str], ...] = (
    ("tools/purity.py", "rglob",
     "recursion — the original globbed *.py and a subpackage importing socket "
     "was invisible"),
    ("tools/purity.py", "_DYNAMIC",
     '__import__("socket") carries a string where an import carries a name'),
    ("tools/purity.py", "_SPAWN_MODULES",
     'subprocess.run(["curl", …]) is a network call with no socket import in '
     "the file"),
    ("tools/conform.py", "no-egress",
     "a scan of zero files must report UNKNOWN, not PASS (rule 13)"),
)

#: The conformance rows R17 reads. `no-egress` says the egress test ran and
#: held; `ablation` says the mutation harness ran and every mutation was caught.
#: Either one alone is half an answer.
REQUIRED_ROWS = ("no-egress", "ablation")

_RECORD_ROW = re.compile(r"^\|\s*\*\*(\w+)\*\*\s*\|\s*`([a-z0-9-]+)`")


def registry(path: Optional[Path] = None) -> Tuple[Tuple[str, ...], ...]:
    """The ablation table, read out of `tests/ablate.py` by AST.

    Parsed rather than imported: importing the harness to ask what it mutates
    is one `main()` away from mutating the tree in order to inspect it.
    """
    src = (path if path is not None else REGISTRY)
    if not src.exists():
        return ()
    tree = ast.parse(src.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "MUTATIONS" for t in node.targets):
            rows = []
            for elt in getattr(node.value, "elts", []):
                parts = []
                for item in getattr(elt, "elts", []):
                    try:
                        parts.append(ast.literal_eval(item))
                    except ValueError:
                        parts.append("")
                rows.append(tuple(str(p) for p in parts))
            return tuple(rows)
    return ()


def egress_coverage(rows: Sequence[Sequence[str]]) -> Dict[Tuple[str, str], List[str]]:
    """Which required detection site each mutation ablates.

    A row counts for a site when it targets that file **and** its pattern or
    replacement names the anchor. Matching on the label would be matching on
    prose, which is the thing rule 17 says not to trust.
    """
    found: Dict[Tuple[str, str], List[str]] = {
        (target, anchor): [] for target, anchor, _ in REQUIRED_EGRESS_SITES}
    for row in rows:
        if len(row) < 4:
            continue
        target, pattern, repl, label = row[0], row[1], row[2], row[3]
        for site in found:
            if target == site[0] and (site[1] in pattern or site[1] in repl):
                found[site].append(label)
    return found


def record_rows(where: Optional[Path] = None) -> Tuple[Optional[Path], Dict[str, str]]:
    """`(newest conformance record, {check id: state})`.

    The record is the harness's own report, dated and pinned and never
    overwritten. Reading the newest one answers *did the mutations get caught*
    without this module running the harness and grading itself.
    """
    base = where if where is not None else CONFORMANCE
    if not base.exists():
        return None, {}
    records = sorted(base.glob("*.md"))
    if not records:
        return None, {}
    newest = records[-1]
    states = {}
    for line in newest.read_text(encoding="utf-8").splitlines():
        m = _RECORD_ROW.match(line)
        if m:
            states[m.group(2)] = m.group(1)
    return newest, states


def r17_no_egress_neutralised(reg: Optional[Path] = None,
                              records: Optional[Path] = None) -> Result:
    """R17 — a structural no-egress test exists and fails when neutralised."""
    title = "a structural no-egress test exists and fails when neutralised"
    rows = registry(reg)
    if not rows:
        return Result(
            "R17", title, Verdict.ABSENT, Severity.NONE,
            f"no ablation registry at {REGISTRY.relative_to(ROOT)}",
            condition="a mutation harness exists in the tree",
        )

    coverage = egress_coverage(rows)
    uncovered = [site for site, labels in coverage.items() if not labels]
    covering = sum(len(labels) for labels in coverage.values())

    newest, states = record_rows(records)
    if newest is None:
        return Result(
            "R17", title, Verdict.UNKNOWN, Severity.NONE,
            f"{covering} mutation(s) cover {len(coverage) - len(uncovered)} of "
            f"{len(coverage)} egress detection site(s), and no conformance record "
            f"exists to say whether the harness reported them caught",
            condition="one run of `python3 tools/conform.py --write`",
        )

    if uncovered:
        return Result(
            "R17", title, Verdict.FINDING, Severity.S1,
            f"{len(uncovered)} egress detection site(s) with no mutation against "
            f"them: " + "; ".join(f"{t} ({a})" for t, a in uncovered)
            + f" — of {len(rows)} registry row(s) read from "
              f"{REGISTRY.relative_to(ROOT)}",
        )

    missing = [r for r in REQUIRED_ROWS if states.get(r) != "PASS"]
    if missing:
        return Result(
            "R17", title, Verdict.FINDING, Severity.S1,
            f"{newest.name} reports " + ", ".join(
                f"{r}={states.get(r, 'no row')}" for r in missing)
            + " — the neutralisation half is unproven whatever the registry says",
        )

    return Result(
        "R17", title, Verdict.PASS, Severity.NONE,
        f"{covering} mutation(s) over {len(coverage)} egress detection site(s), "
        f"read by AST from {REGISTRY.relative_to(ROOT)} ({len(rows)} rows total); "
        f"{newest.name} reports "
        + ", ".join(f"{r}={states[r]}" for r in REQUIRED_ROWS),
    )


# --- reading the audit document --------------------------------------------

#: A finding row: `| \`TM-RACE-01\` | R11 | \`S2\` | closed 2026-07-31 | … |`
_FINDING_ROW = re.compile(
    r"^\|\s*`(TM-[A-Z]+-\d+)`\s*\|\s*([^|]*?)\s*\|\s*`(S[0-3])`\s*\|\s*([^|]*?)\s*\|")

#: A rubric row: `| \`R11\` | … | **PASS** | … |`
_RUBRIC_ROW = re.compile(
    r"^\|\s*`(R\d{1,2})`\s*\|[^|]*\|\s*\*\*([A-Z-]+)\*\*\s*\|")

_DATE = re.compile(r"^-\s+\*\*date\*\*\s+`(\d{4}-\d{2}-\d{2})`", re.M)
_COMMIT = re.compile(r"^-\s+\*\*commit\*\*\s+`([0-9a-f]{7,40})`", re.M)


@dataclass(frozen=True)
class Finding:
    id: str
    check: str
    severity: Severity
    status: str

    @property
    def open(self) -> bool:
        """Anything that does not say closed is open. The default direction
        matters: a status nobody updated must not read as resolved."""
        return not self.status.lower().startswith(("closed", "fixed", "withdrawn"))


def recorded(text: str) -> Dict[str, str]:
    """`{R-id: verdict}` as the audit document states them.

    One implementation, two callers — `tools/conform.py` gates on it and
    `tests/test_audit.py` reconciles it against what the checks report today.
    A second parser would be the pair §16 keeps recording.
    """
    return {m.group(1): m.group(2) for m in
            (_RUBRIC_ROW.match(line) for line in text.splitlines()) if m}


def findings(text: str) -> Tuple[Finding, ...]:
    out = []
    for line in text.splitlines():
        m = _FINDING_ROW.match(line)
        if m:
            out.append(Finding(m.group(1), m.group(2), Severity(m.group(3)),
                               m.group(4)))
    return tuple(out)


def audit_date(text: str) -> Optional[str]:
    m = _DATE.search(text)
    return m.group(1) if m else None


def audit_commit(text: str) -> Optional[str]:
    m = _COMMIT.search(text)
    return m.group(1) if m else None


# --- the two, together -----------------------------------------------------


CHECKS = (r16_at_rest, r17_no_egress_neutralised)


def run() -> Tuple[Result, ...]:
    return tuple(c() for c in CHECKS)


def main() -> int:
    """Prints; decides nothing. The gate is `tools/conform.py`, which reads the
    document these two are written into — so that a verdict has to be recorded
    before it can be enforced, rather than being a number a run printed once."""
    results = run()
    for r in results:
        print(f"  {r.verdict.value:<15} {r.id}  {r.severity.value:<3} {r.title}")
        print(f"      {r.evidence}")
        if r.condition:
            print(f"      applies when: {r.condition}")
    return 0


def test_the_two_checks_report_a_state_that_is_not_a_pass_by_default():
    """A smoke test so this module is exercised by the ordinary suite as well
    as by `tests/test_audit.py`. Nothing here asserts a verdict — that would
    freeze today's answer into the check."""
    for r in run():
        assert isinstance(r.verdict, Verdict)
        assert (r.verdict is Verdict.PASS) == r.passed


if __name__ == "__main__":
    raise SystemExit(main())
