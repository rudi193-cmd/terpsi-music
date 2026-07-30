"""§18 item 6: the conformance suite, and the record it writes.

§17 measures the gap precisely and it is not the gate:

> *"PR #113 measured that `promote_check.py` **returns an exit code and writes
> nothing**, and that Nestor and Jeles both cleared all eight gates in #88 while
> **neither left a record.** The gate exists; the ledger does not."*

So the deliverable here is the ledger, and rule 18 requires being straight about
which half each check is. Every check below reports one of four states and
**`UNKNOWN` is not a pass**:

* `PASS` — a check ran and the thing held
* `FAIL` — a check ran and the thing did not hold
* `UNKNOWN` — nothing here can decide it (rule 13). Most of §17's propagating
  guarantees are in this state today and saying so is the entire point
* `ABSENT` — the thing being checked does not exist yet, which is a different
  fact from a check that could not run

**A conformance record that only ever says PASS is not a record.** This one is
expected to be mostly not-PASS on the day it is written, and a run that reported
otherwise would be the thing §17 warns about — a template whose conformance
check is a formality, making the second app a copy and the fifth a dialect.

**The record is dated, pinned, and never overwritten.** Each run writes a new
file under `docs/conformance/`, because *"this app conforms"* has to be a dated
fact rather than an exit code somebody saw once. A record that could be
overwritten would answer *"does it conform"* and never *"when did it stop."*

    python3 tools/conform.py            # run and print
    python3 tools/conform.py --write    # run and write a dated record

Stdlib only. No network.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
RECORDS = ROOT / "docs" / "conformance"


class State(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"   # nothing here can decide it — not a pass (rule 13)
    ABSENT = "ABSENT"     # the thing checked does not exist yet


@dataclass(frozen=True)
class Check:
    id: str
    what: str          # the §17 guarantee, in its own words
    state: State
    evidence: str      # what was actually looked at, not what was assumed

    @property
    def conforms(self) -> bool:
        return self.state is State.PASS


# --- checks that genuinely run ---------------------------------------------

#: Modules that reach the network. `records/` claims *stdlib only, no network*
#: in every docstring; this is the difference between the claim and the check.
_EGRESS = {"socket", "http", "urllib", "requests", "httpx", "aiohttp", "ftplib",
           "smtplib", "telnetlib", "asyncio", "websockets", "xmlrpc"}


def check_no_egress(where: Optional[Path] = None) -> Check:
    """§6 core purity, as an AST scan rather than a docstring.

    Takes a directory so the check itself can be pointed at a decoy and shown
    to complain (rule 19). A checker that has only ever passed is
    indistinguishable from one that cannot fail — which this repository has now
    found three times in its own tests.
    """
    offenders = []
    for py in sorted((where or (ROOT / "records")).glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                if m.split(".")[0] in _EGRESS:
                    offenders.append(f"{py.name}:{node.lineno} imports {m}")
    if offenders:
        return Check("no-egress", "core purity: the inner ring cannot reach out",
                     State.FAIL, "; ".join(offenders))
    n = len(list((where or (ROOT / "records")).glob("*.py")))
    return Check("no-egress", "core purity: the inner ring cannot reach out",
                 State.PASS, f"{n} modules scanned by AST; no network import")


def check_write_paths() -> Check:
    """§6's *declared write paths*. §14 records this as open fleet-wide —
    *'the AST checker sees imports, not filesystem writes'* — so the honest
    answer here is a scan for the writes and no declaration to compare them to.
    """
    writers = []
    for py in sorted((ROOT / "records").glob("*.py")):
        src = py.read_text(encoding="utf-8")
        for pat in ("open(", ".write_text(", ".write_bytes(", "os.remove", "shutil."):
            if pat in src:
                writers.append(f"{py.name}:{pat}")
    if writers:
        return Check("write-paths", "declared write paths (§6)", State.FAIL,
                     f"records/ writes and nothing declares it: {'; '.join(writers)}")
    return Check("write-paths", "declared write paths (§6)", State.UNKNOWN,
                 "records/ performs no filesystem writes, so there is nothing to "
                 "declare — but no manifest exists to declare against, so this is "
                 "not evidence the mechanism works")


def check_revocation_is_dated() -> Check:
    """§7.1 / refusal 3: revocation sets a date and never deletes."""
    src = (ROOT / "records" / "serving.py").read_text(encoding="utf-8")
    if "invalid_at" not in src:
        return Check("dated-revocation", "revocation by date, never by delete (§7.1)",
                     State.FAIL, "Edge carries no invalid_at")
    bad = []
    for py in sorted((ROOT / "records").glob("*.py")):
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b(edges|edge)\s*\.\s*(remove|pop|clear)\s*\(", line):
                bad.append(f"{py.name}:{i}")
    if bad:
        return Check("dated-revocation", "revocation by date, never by delete (§7.1)",
                     State.FAIL, f"standing removed rather than dated: {'; '.join(bad)}")
    return Check("dated-revocation", "revocation by date, never by delete (§7.1)",
                 State.PASS,
                 "Edge carries valid_at/invalid_at/created_at; no module removes an edge")


def check_suite_runs_standalone() -> Check:
    """§17 propagates the acceptance shape, not just the tests. Every test file
    must run without pytest, so an instance cannot conform by having a runner."""
    missing = [p.name for p in sorted((ROOT / "tests").glob("test_*.py"))
               if '__main__' not in p.read_text(encoding="utf-8")]
    if missing:
        return Check("standalone-suites", "every test file runs standalone",
                     State.FAIL, f"no __main__ block: {', '.join(missing)}")
    n = len(list((ROOT / "tests").glob("test_*.py")))
    return Check("standalone-suites", "every test file runs standalone",
                 State.PASS, f"{n} test files, each with a __main__ runner")


def check_ablation() -> Check:
    """§10 / rule 19: acceptance is mutation, not a green suite."""
    ablate = ROOT / "tests" / "ablate.py"
    if not ablate.exists():
        return Check("ablation", "every guard shown to fail (rule 19)", State.ABSENT,
                     "tests/ablate.py does not exist")
    r = subprocess.run([sys.executable, str(ablate)], capture_output=True,
                       text=True, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
    if r.returncode != 0:
        return Check("ablation", "every guard shown to fail (rule 19)", State.FAIL,
                     tail[0][:200])
    return Check("ablation", "every guard shown to fail (rule 19)", State.PASS,
                 tail[0].strip())


def check_exit_line() -> Check:
    """§11.1: the exit line is written before the first install."""
    doc = ROOT / "docs" / "EXIT.md"
    if not doc.exists():
        return Check("exit-line", "the exit line and its export (§11.1)", State.ABSENT,
                     "docs/EXIT.md does not exist; §11.1 requires it before the "
                     "first install and this is §18 item 5")
    text = doc.read_text(encoding="utf-8")
    return Check("exit-line", "the exit line and its export (§11.1)",
                 State.PASS if "## The line" in text else State.FAIL,
                 f"docs/EXIT.md, {len(text.splitlines())} lines")


def check_declared_sockets() -> Check:
    """§18 item 4 note (ii): every listener the source opens must be declared.

    **Built before the manifest, on purpose.** §4.3's worked failure is a
    declaration that shipped first with nothing pointed at it. A `VACUOUS`
    result — no manifest, no listeners — reports `UNKNOWN` rather than `PASS`,
    because a check with nothing to check has not checked anything.
    """
    from sockets import Verdict, check as scan_check  # noqa: E402

    r = scan_check([ROOT / "records", ROOT / "tools", ROOT / "voice.py",
                    ROOT / "personas.py"])
    what = "listening sockets are declared (§4.3, item 4 note ii)"
    if r.verdict is Verdict.VACUOUS:
        return Check("declared-sockets", what, State.UNKNOWN,
                     "no manifest and no listeners: nothing was checked. The "
                     "checker is wired and shown to fail (tests/fixtures/decoys), "
                     "so the first surface item 4 lands is caught on arrival")
    if r.findings:
        return Check("declared-sockets", what, State.FAIL,
                     "; ".join(f.detail for f in r.findings[:3]))
    return Check("declared-sockets", what, State.PASS,
                 f"{len(r.listeners)} listener(s), all declared; 0 outbound")


def check_component_map() -> Check:
    """Item 0: an unverified table and a verified one must not look identical."""
    r = subprocess.run([sys.executable, str(ROOT / "tests" / "test_component_map.py")],
                       capture_output=True, text=True, cwd=ROOT)
    line = next((l for l in (r.stdout or "").splitlines() if l.startswith("§14:")), "")
    return Check("component-map", "§14 says whether anyone looked (item 0)",
                 State.PASS if r.returncode == 0 else State.FAIL,
                 line or "test_component_map.py")


# --- checks nothing here can decide ----------------------------------------


def _unknown(cid: str, what: str, why: str) -> Callable[[], Check]:
    return lambda: Check(cid, what, State.UNKNOWN, why)


UNDECIDABLE: Tuple[Callable[[], Check], ...] = (
    _unknown("manifest", "manifest with a build-failing cloud-permission check (§6)",
             "no manifest exists in this repository; §18 item 4 has to say what "
             "surfaces exist before one can declare them"),
    _unknown("security-audit", "SECURITY_AUDIT.md against the shared rubric (§10)",
             "willow-2.0's 15-check rubric is named in §14 as reusable and has "
             "not been run here; UNVERIFIED at source"),
    _unknown("sidecar-only", "canonical store read-only; agent writes are sidecar (§5)",
             "there is no store, so the rule cannot be violated or demonstrated"),
    _unknown("knock-enforcing", "the knock wired in enforcement mode (§7.2)",
             "session reconciliation lives in willow-gate and is not wired here"),
    _unknown("allowlist-rot", "allowlist rot tests (§16)",
             "no destination allowlist exists; §14 records the fleet-wide version "
             "as unique to UTETY"),
    _unknown("named-middles", "a named middle for every pair the app creates (§16)",
             "not mechanically decidable. Four middles are named and tested "
             "(crossing, standing.is_self_edge, marking.drift, practice._one_lane); "
             "whether that is *every* pair is a reading, not a check"),
)


CHECKS: Tuple[Callable[[], Check], ...] = (
    check_no_egress, check_write_paths, check_revocation_is_dated,
    check_suite_runs_standalone, check_ablation, check_exit_line,
    check_component_map, check_declared_sockets,
) + UNDECIDABLE


# --- the record ------------------------------------------------------------


def _commit() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                       text=True, cwd=ROOT)
    return r.stdout.strip()[:12] if r.returncode == 0 else "unknown"


def _dirty() -> bool:
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                       text=True, cwd=ROOT)
    return bool(r.stdout.strip())


def run(skip: Tuple[str, ...] = ()) -> List[Check]:
    """Run the checks. `skip` drops slow ones by id and is for callers that are
    testing this module rather than the repository.

    A skipped check is **omitted**, never reported as passing — a conformance
    record with a hole in it is honest and one with an invented row is not.
    """
    named = {f"check_{s.replace('-', '_')}" for s in skip}
    return [c() for c in CHECKS if getattr(c, "__name__", "") not in named]


def render(checks: List[Check], at: datetime) -> str:
    tally = {s: sum(1 for c in checks if c.state is s) for s in State}
    commit, dirty = _commit(), _dirty()
    digest = hashlib.sha256(
        "\x1f".join(f"{c.id}={c.state.value}" for c in checks).encode()
    ).hexdigest()[:16]

    lines = [
        f"# Conformance record — {at.date().isoformat()}",
        "",
        f"- **at** `{at.isoformat()}`",
        f"- **commit** `{commit}`{'  **(working tree dirty — this record describes uncommitted state)**' if dirty else ''}",
        f"- **outcome digest** `{digest}`",
        "",
        f"**{tally[State.PASS]} pass · {tally[State.FAIL]} fail · "
        f"{tally[State.UNKNOWN]} unknown · {tally[State.ABSENT]} absent** "
        f"of {len(checks)} checks.",
        "",
        "`UNKNOWN` is not a pass. A record that read all-pass on the day it was "
        "first written would be the formality §17 warns about, not a check.",
        "",
        "| | check | §17 guarantee | evidence |",
        "|---|---|---|---|",
    ]
    for c in checks:
        ev = c.evidence.replace("|", "\\|")
        lines.append(f"| **{c.state.value}** | `{c.id}` | {c.what} | {ev} |")
    lines += ["", "---", "",
              "Written by `tools/conform.py`. Records are never overwritten: "
              "*\"does it conform\"* is answerable from any one of them, and "
              "*\"when did it stop\"* only from the series."]
    return "\n".join(lines) + "\n"


def write(checks: List[Check], at: datetime) -> Path:
    RECORDS.mkdir(parents=True, exist_ok=True)
    stamp = at.strftime("%Y-%m-%dT%H%M%SZ")
    path = RECORDS / f"{stamp}.md"
    if path.exists():
        raise FileExistsError(
            f"{path.name} exists; conformance records are append-only and a run "
            "does not overwrite an earlier one"
        )
    path.write_text(render(checks, at), encoding="utf-8")
    return path


def main(argv: List[str]) -> int:
    at = datetime.now(timezone.utc).replace(microsecond=0)
    checks = run()
    width = max(len(c.id) for c in checks)
    for c in checks:
        print(f"  {c.state.value:<8} {c.id:<{width}}  {c.evidence[:90]}")
    fails = [c for c in checks if c.state is State.FAIL]
    print(f"\n  {sum(c.conforms for c in checks)}/{len(checks)} pass, "
          f"{len(fails)} fail, "
          f"{sum(1 for c in checks if c.state is State.UNKNOWN)} unknown")
    if "--write" in argv:
        print(f"  record: {write(checks, at).relative_to(ROOT)}")
    # A FAIL is a build failure. UNKNOWN is not, because most of §17's
    # guarantees are undecidable here today and failing on that would make the
    # gate unusable — which is how a gate ends up being switched off.
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
