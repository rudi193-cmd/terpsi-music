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
    if not path.exists():
        return False, f"{path.name} does not exist; §5 records escrow as the largest gap"
    text = path.read_text(encoding="utf-8")
    split = _SPLIT.search(text)
    rehearsed = _REHEARSED.search(text)
    if not split:
        return False, f"{path.name} states no k-of-n threshold"
    if not rehearsed:
        return False, (f"{path.name} states {split.group(0)} and no dated rehearsal; "
                       "§5: an untested key recovery is not escrow")
    return True, f"{path.name}: {split.group(0)}, rehearsed {rehearsed.group(1)}"


def anything_at_rest(where: Optional[Path] = None) -> int:
    """How many places the inner ring puts a byte on a disk.

    Derived from `tools/purity.py` rather than asserted, and it is what
    separates *"nothing is encrypted"* from *"nothing is stored"*. The first is
    a finding; the second is why R16 is `ABSENT` today rather than `FINDING`.
    """
    from purity import writes  # noqa: E402

    return len(writes([where if where is not None else ROOT / "records"]))


def r16_at_rest(records: Optional[Path] = None,
                escrow: Optional[Path] = None) -> Result:
    """R16 — data at rest is encrypted, with the key escrowed (§5)."""
    title = "data at rest is encrypted, with the key escrowed"
    seam = at_rest_seam(records)
    disposed, why = escrow_disposition(escrow)
    at_rest = anything_at_rest(records)

    if not seam and not at_rest:
        return Result(
            "R16", title, Verdict.ABSENT, Severity.NONE,
            f"no at-rest sealing entry point in records/ (looked for "
            f"{len(AT_REST_VERBS)} verb(s) by AST, found 0) and nothing at rest to "
            f"seal: purity.writes() over records/ reports 0 write site(s). "
            f"records/sealing.py is rule 10's human seal, not a cipher, and is "
            f"deliberately not counted. Escrow: {why}",
            condition="the first module that writes a record to a disk. R16 "
                      "becomes an open S1 at that commit unless sealing lands with it",
        )
    if not seam:
        return Result(
            "R16", title, Verdict.FINDING, Severity.S1,
            f"{at_rest} write site(s) in records/ and no at-rest sealing entry "
            f"point: records hit the disk in the clear. Escrow: {why}",
        )
    if not disposed and not at_rest:
        # The seam landed ahead of the store, which is this repository's
        # deliberate ordering (item 4 note iii): the mechanism exists and no
        # master has been minted, no record is at rest, so a lost key file
        # cannot yet destroy anything. This check's own stated condition —
        # "R16 becomes an open S1 the day anything writes a record to disk" —
        # was written before the seam existed and the first implementation
        # flipped on seam presence instead. Caught when F3 merged: the doc's
        # reconciler went red on a severity the condition never promised.
        return Result(
            "R16", title, Verdict.FINDING, Severity.S2,
            f"sealing at {', '.join(m for m, _ in seam)}, nothing at rest yet "
            f"(purity.writes() over records/: 0 site(s)), and no escrow "
            f"disposition — {why}",
            condition="the first module that writes a record to a disk. This "
                      "finding becomes S1 at that commit unless a recorded, "
                      "rehearsed escrow disposition exists by then",
        )
    if not disposed:
        return Result(
            "R16", title, Verdict.FINDING, Severity.S1,
            f"sealing at {', '.join(m for m, _ in seam)}, {at_rest} write "
            f"site(s), and no escrow disposition — {why}. §5: a single file "
            f"loss destroys every record, irrecoverably, by design",
        )
    return Result(
        "R16", title, Verdict.PASS, Severity.NONE,
        f"{len(seam)} sealing entry point(s): "
        f"{', '.join(f'{m}:{v}' for m, v in seam)}. Escrow: {why}",
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
