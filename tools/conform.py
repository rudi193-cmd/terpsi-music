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

def check_no_egress(where: Optional[Path] = None) -> Check:
    """§6 core purity. Delegates to `tools/purity.py`, which is pointed at
    decoys in `tests/fixtures/decoys/` and shown to complain.

    **The version that lived here returned PASS** for a directory holding
    `__import__("socket")`, `subprocess.run(["curl", …])` and a subpackage
    importing `socket` — dynamic imports were invisible, `subprocess` was not in
    the set, and the scan globbed `*.py` rather than `**/*.py`.
    """
    from purity import counted, egress  # noqa: E402

    targets = [where] if where is not None else [ROOT / "records"]
    found = egress(targets)
    n = counted(targets)
    what = "core purity: the inner ring cannot reach out"
    if found:
        return Check("no-egress", what, State.FAIL,
                     "; ".join(str(t) for t in found[:4]))
    if not n:
        return Check("no-egress", what, State.UNKNOWN,
                     "no files scanned; nothing was checked")
    return Check("no-egress", what, State.PASS,
                 f"{n} module(s) scanned recursively by AST; no egress import, "
                 "no dynamic import of one, no process spawn")


def check_write_paths(where: Optional[Path] = None) -> Check:
    """§6's *declared write paths*, against a core that declares none.

    **The version that lived here took no path argument**, so it could not be
    pointed at a decoy at all, and it matched substrings — a docstring saying
    *"never calls `open(`"* failed the file while `Path.open()`, `os.rename`
    and `tempfile` passed it.

    Reads are reported separately and do not fail. A write check that cries wolf
    on every `open()` is a write check somebody switches off.
    """
    from purity import counted, reads, writes  # noqa: E402

    targets = [where] if where is not None else [ROOT / "records"]
    found = writes(targets)
    n = counted(targets)
    what = "declared write paths (§6)"
    if found:
        return Check("write-paths", what, State.FAIL,
                     f"records/ writes and nothing declares it: "
                     + "; ".join(str(t) for t in found[:4]))
    if not n:
        return Check("write-paths", what, State.UNKNOWN,
                     "no files scanned; nothing was checked")
    r = reads(targets)
    return Check("write-paths", what, State.UNKNOWN,
                 f"{n} module(s) scanned by AST: no writes"
                 + (f", {len(r)} read(s)" if r else ", no reads")
                 + " — but no manifest exists to declare against, so this is not "
                   "evidence the mechanism works")


def check_revocation_is_dated(where: Optional[Path] = None) -> Check:
    """§7.1 / refusal 3: standing ends by a date, never by a delete.

    **The version that lived here was wrong in both directions at once.** It
    matched a regex over lines, so a docstring reading *"never call
    `edges.remove(`"* failed the file — and it missed `del edges[0]`,
    `self._edges.remove()` (a leading underscore is a word character, so
    `\\bedges` finds no boundary), an executed `DELETE FROM edge`, and an
    entire subdirectory.
    """
    from discipline import counted, deletions  # noqa: E402

    targets = [where] if where is not None else [ROOT / "records"]
    what = "revocation by date, never by delete (§7.1)"
    src = (ROOT / "records" / "serving.py").read_text(encoding="utf-8")
    if where is None and not all(d in src for d in ("valid_at", "invalid_at", "created_at")):
        return Check("dated-revocation", what, State.FAIL,
                     "Edge does not carry all three dates")
    found = deletions(targets)
    n = counted(targets)
    if found:
        return Check("dated-revocation", what, State.FAIL,
                     "; ".join(str(d) for d in found[:4]))
    if not n:
        return Check("dated-revocation", what, State.UNKNOWN,
                     "no files scanned; nothing was checked")
    if where is not None:
        return Check("dated-revocation", what, State.PASS,
                     f"{n} module(s) scanned by AST; nothing deleted")
    # The load-bearing half needs a store, and there is not one.
    return Check("dated-revocation", what, State.UNKNOWN,
                 f"{n} module(s): Edge carries valid_at/invalid_at/created_at and "
                 "nothing deletes standing — but revocation-by-delete is a property "
                 "of a store and there is no store, so this is narrower than it reads")


def check_suite_runs_standalone(where: Optional[Path] = None) -> Check:
    """§17 propagates the acceptance shape, not just the tests.

    **The version that lived here asked whether the string `__main__` appeared
    anywhere in the file**, so it passed a suite that only mentions it in a
    docstring, a suite whose runner is `pass`, and — worst — a suite whose runner
    catches every failure and exits 0. A runner that cannot fail the process is
    worse than no runner, because the record then carries a row saying the suite
    runs alone.
    """
    from discipline import Runner, runners  # noqa: E402

    targets = [where] if where is not None else [ROOT / "tests"]
    what = "every test file runs standalone and can fail"
    got = runners(targets)
    if not got:
        return Check("standalone-suites", what, State.UNKNOWN,
                     "no test files found; nothing was checked")
    bad = [s for s in got if not s.ok]
    if bad:
        return Check("standalone-suites", what, State.FAIL,
                     "; ".join(f"{s.module} — {s.runner.value}" for s in bad[:4]))
    return Check("standalone-suites", what, State.PASS,
                 f"{len(got)} test file(s): each has a __main__ runner that exits "
                 "nonzero on failure")


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


#: How old an audit may be before this check stops believing it.
#:
#: **The honest limit, stated rather than implied.** What you actually want is
#: *"the audit is no more than N commits behind this tree"*, and that is not
#: decidable from a tree: the audit pins the commit it was written at, and
#: whether the eleven commits since touched anything it examined is a judgement
#: about diffs, not a fact a checker can read. So staleness here is measured in
#: days, which is a weaker property honestly reported rather than a stronger one
#: asserted. The pin is still checked, for the one thing it does decide — that
#: the audit describes a commit this history contains.
STALE_AFTER_DAYS = 90


def check_security_audit(doc: Optional[Path] = None) -> Check:
    """§10: the fifteen-check rubric, run here and treated as an install gate.

    **This row said `UNKNOWN` until 2026-07-31**, on the honest grounds that the
    rubric was *"named in §14 as reusable and has not been run here"*. It has
    now been run — `docs/SECURITY-AUDIT.md` — and this check is what makes the
    result a gate rather than a document, which is the distinction §10 asks for
    and rule 18 asks to be said out loud.

    It grades the *document*, not the tree. That is deliberate and it is the
    limit: R1–R15 are judgements about source that a human made by reading, and
    a check that re-derived them would be a second implementation of the audit
    with nothing reconciling the two (§16). What is mechanical is whether an
    audit exists, whether it is stale, and whether anything in it at `S1` or
    above is still open — and an open high finding fails the build.

    R16 and R17 inside that document are themselves runnable (`tools/audit.py`),
    and `tests/test_audit.py` is the middle that keeps the recorded verdicts and
    the live ones from drifting apart.
    """
    from audit import FAILING, audit_commit, audit_date, findings  # noqa: E402

    path = doc if doc is not None else ROOT / "docs" / "SECURITY-AUDIT.md"
    what = "the fifteen-check rubric run here, as a gate (§10)"
    if not path.exists():
        return Check("security-audit", what, State.ABSENT,
                     f"{path.name} does not exist; §10 treats the rubric as an "
                     "install gate and there is nothing to gate on")

    text = path.read_text(encoding="utf-8")
    when, pin = audit_date(text), audit_commit(text)
    if when is None or pin is None:
        return Check("security-audit", what, State.UNKNOWN,
                     f"{path.name} carries no {'date' if when is None else 'commit pin'}; "
                     "an audit that does not say what it examined cannot be gated on")

    found = findings(text)
    hot = [f for f in found if f.open and f.severity in FAILING]
    if hot:
        return Check("security-audit", what, State.FAIL,
                     "open " + ", ".join(f"{f.severity.value} {f.id}" for f in hot[:4])
                     + f" in {path.name}")

    age = (datetime.now(timezone.utc).date()
           - datetime.strptime(when, "%Y-%m-%d").date()).days
    if age > STALE_AFTER_DAYS:
        return Check("security-audit", what, State.UNKNOWN,
                     f"{path.name} is dated {when}, {age} days old against a "
                     f"{STALE_AFTER_DAYS}-day limit. Commits-behind is not decidable "
                     "from a tree, so the limit is a date and this is a weaker "
                     "property than it reads")

    r = subprocess.run(["git", "merge-base", "--is-ancestor", pin, "HEAD"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return Check("security-audit", what, State.UNKNOWN,
                     f"{path.name} pins `{pin}`, which is not an ancestor of HEAD; "
                     "the audit describes a tree this one does not contain")

    return Check("security-audit", what, State.PASS,
                 f"{path.name} dated {when} at `{pin}`, {age} day(s) old; "
                 f"{len(found)} finding(s) recorded, "
                 f"{sum(1 for f in found if f.open)} open, none at S1 or above")


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
    check_component_map, check_declared_sockets, check_security_audit,
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
    # `if path.exists(): raise` then write was check-then-act, and the window
    # between them is exactly one second wide because the stamp has second
    # resolution — TM-RACE-02 in docs/SECURITY-AUDIT.md. `open("x")` is one
    # atomic O_EXCL create and raises the same FileExistsError, so append-only
    # stops being a convention two callers could step over.
    try:
        with path.open("x", encoding="utf-8") as fh:
            fh.write(render(checks, at))
    except FileExistsError:
        raise FileExistsError(
            f"{path.name} exists; conformance records are append-only and a run "
            "does not overwrite an earlier one"
        ) from None
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
