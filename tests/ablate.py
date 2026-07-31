"""Ablate each guard in the predicates and require the suite to notice.

Rule 19: *a guard that cannot be shown to fail has not been shown to work.*
`docs/survey/trigger_mutation_demo.py` establishes the method against a SQLite
schema; this applies it to the two predicates in `records/`.

**The load-bearing part is the applied-mutation check.** A `sed` expression that
no longer matches its target leaves the file unchanged, the suite green, and the
report reading `SURVIVES` — which is scout-13 row B exactly: *"a mutation which
kills no gate is a failed mutation, not a passing one."* This harness had that
defect on its first run, after a refactor moved a condition across two lines,
and reported a false survivor that was nearly written up as a finding.

So every mutation is verified to have changed the file before its result counts,
and a mutation that does not apply is an **error**, not a pass.

    python3 tests/ablate.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (target file, pattern, replacement, label, suite that must catch it)
MUTATIONS = [
    ("records/serving.py", "if fld.rung is NEVER_SERVED:", "if False:",
     "L5 never-served", "tests/test_serving.py"),
    ("records/serving.py", "if lane_id is not None and lane_id != fld.lane_id:", "if False:",
     "W-3 lane seal", "tests/test_serving.py"),
    ("records/serving.py", "if fld.rung is None:", "if False:",
     "rule 13 unclassified", "tests/test_serving.py"),
    ("records/serving.py", "if fld.category and fld.category in principal.purposes:", "if True:",
     "L4 declared purpose", "tests/test_serving.py"),
    ("records/serving.py", "and e.live_at(at) and e.known_at(horizon)", "and e.known_at(horizon)",
     "edge validity dates", "tests/test_serving.py"),
    ("records/serving.py", "and e.live_at(at) and e.known_at(horizon)", "and e.live_at(at)",
     "edge knowledge horizon", "tests/test_serving.py"),
    ("records/serving.py", "e.subject_id == subject_id and ", "",
     "edge subject check", "tests/test_serving.py"),
    ("records/sending.py", "and r.live_at(at)", "",
     "restriction dates", "tests/test_sending.py"),
    ("records/sending.py", "and r.known_at(horizon)", "",
     "restriction created_at clock", "tests/test_sending.py"),
    ("records/sending.py", "if self.state is not Standing.DERIVED:", "if False:",
     "UNKNOWN iterates as empty", "tests/test_sending.py"),
    ("records/sending.py", "and e.live_at(at)\n", "\n",
     "guardianship edge dates", "tests/test_sending.py"),
    ("records/sending.py", 'if e.kind == "guardian_of" and e.subject_id == subject_id',
     "if e.subject_id == subject_id",
     "guardian-only recipients", "tests/test_sending.py"),
    ("records/classify.py", "if d.derived_from and not d.passed_reidentification_check:",
     "if False:", "re-identification gate", "tests/test_classify.py"),
    ("records/classify.py", "if d.name in NOT_ELEVATED:", "if False:",
     "chosen-name inversion", "tests/test_classify.py"),
    ("records/classify.py", "Decision.UNDECIDED, None,", "Decision.DECIDED, Rung.L3,",
     "refusal to guess a rung", "tests/test_classify.py"),
    ("records/classify.py", "if d.is_key_material:", "if False:",
     "L5 override rule 1", "tests/test_classify.py"),
    ("records/disclosure.py", "if e.digest != expected:", "if False:",
     "chain tamper detection", "tests/test_disclosure.py"),
    ("records/disclosure.py", "if len(log.entries) < count:", "if False:",
     "truncation via the anchor", "tests/test_disclosure.py"),
    ("records/sealing.py", "if name.lower() in _NOT_A_PERSON:", "if False:",
     "a role is not a name", "tests/test_sealing.py"),
    ("records/sealing.py", "return self.state is State.SEALED and self.over == _digest(self.body)",
     "return self.state is State.SEALED",
     "seal does not survive an edit", "tests/test_sealing.py"),
    ("records/sealing.py", "if rec.state is State.REJECTED:", "if False:",
     "rejected cannot be sealed", "tests/test_sealing.py"),
    ("records/dispositions.py", "if by == req.office:", "if False:",
     "office cannot extend itself", "tests/test_dispositions.py"),
    ("records/dispositions.py", "if req.disposition is not Disposition.OPEN or when < req.due_by:",
     "if True:", "silence escalates", "tests/test_dispositions.py"),
    ("records/dispositions.py", "if office == escalates_to:", "if False:",
     "self-escalation refused", "tests/test_dispositions.py"),
    ("records/exit.py", 'if not (self.exit_terms or "").strip():', "if False:",
     "W-6 exit required at opening", "tests/test_exit.py"),
    ("records/exit.py", "and e.principal_id != recipient", "",
     "recipient keeps their standing", "tests/test_exit.py"),
    ("records/crossing.py", "if not env.live_at(at):", "if False:",
     "envelope expiry", "tests/test_crossing.py"),
    ("records/crossing.py", "if env.from_lane != from_lane or env.to_lane != to_lane:",
     "if False:", "envelope direction", "tests/test_crossing.py"),
    ("records/crossing.py", "if not standing:", "if False:",
     "signer standing at use", "tests/test_crossing.py"),
    ("records/dispatch.py", "if refused:", "if False:",
     "voice gate blocks dispatch", "tests/test_dispatch.py"),
    ("records/dispatch.py", "if decision.outcome in (Outcome.REFUSED, Outcome.UNKNOWN):",
     "if False:", "predicate blocks before render", "tests/test_dispatch.py"),
    ("records/witness.py", "if not evidentiary:", "if False:",
     "unwitnessed is not evidence", "tests/test_witness.py"),
    ("records/witness.py", "if r.independence is Independence.EVIDENTIARY",
     "if True", "a test double counts as a witness", "tests/test_witness.py"),
    ("records/witness.py", "if len(log.entries) < r.anchor.count:", "if False:",
     "truncation after witnessing", "tests/test_witness.py"),
    ("records/witness.py", "if gaps:", "if False:",
     "a gapped cadence", "tests/test_witness.py"),
    ("records/witness.py", "kinds = len({r.witness_kind for r in evidentiary})",
     "kinds = len(evidentiary)",
     "corroboration counts witnesses", "tests/test_witness.py"),
    ("records/receipts.py", 'if e.kind != "guardian_of" or e.subject_id != subject_id:',
     "if False:", "receipts go to guardians only", "tests/test_receipts.py"),
    ("records/receipts.py", "if not e.live_at(at):", "if False:",
     "ended standing gets no receipt", "tests/test_receipts.py"),
    ("records/receipts.py", "if len(lanes) > 1 or len(holders) > 1:", "if False:",
     "gaps refuses a mixed sequence", "tests/test_receipts.py"),
    ("records/receipts.py", "if r.position > len(log.entries):", "if False:",
     "removal contradicts a receipt", "tests/test_receipts.py"),
    ("records/receipts.py", "if not r.matches(entry):", "if False:",
     "substitution contradicts a receipt", "tests/test_receipts.py"),
    ("records/serving.py", "if e.kind == SELF and e.principal_id != e.subject_id:",
     "if False:", "a forged self edge", "tests/test_standing.py"),
    ("records/consent.py", "if at_least(rung, Rung.L4) and not past_threshold(at, threshold):",
     "if False:", "the subject's cap as a consent question", "tests/test_consent.py"),
    ("records/consent.py", "if e.kind not in HOLDS:", "if False:",
     "who holds the authority", "tests/test_consent.py"),
    ("records/consent.py", "and e.live_at(at) and not (e.kind == SELF and not is_self_edge(e))",
     "and e.live_at(at)", "a forged self edge cannot consent", "tests/test_consent.py"),
    ("records/consent.py", "return self.model is Model.SESSION",
     "return self.model is not Model.DELEGATED",
     "UNKNOWN is not askable", "tests/test_consent.py"),
    ("records/practice.py", "if len(lanes) > 1:", "if False:",
     "a statistic reads one lane", "tests/test_practice.py"),
    ("records/practice.py", "if (as_of - days[-1]).days <= 1:", "if True:",
     "a broken streak is not current", "tests/test_practice.py"),
    ("records/conflict.py", "raise NotComputable(\n            \"W-7: the system presents",
     "return None  # (\n            \"W-7: the system presents",
     "an escalation yields no recommendation", "tests/test_practice.py"),
    ("records/conflict.py", "if not who or who.lower() in _NOT_A_PERSON:", "if False:",
     "escalation names a person", "tests/test_practice.py"),
    ("records/conflict.py",
     "if self.stake is Stake.BETWEEN_WARDS and len(set(self.affects)) < 2:",
     "if False:", "a collision names two", "tests/test_practice.py"),
    # Staleness is checked *before* drift. Swapping the order lets a position
    # derived against a superseded score report AGREES, which is the more
    # dangerous answer — it is internally consistent and points at a bar that
    # no longer exists.
    ("records/marking.py",
     "if score_in_force is not None and p.against != score_in_force:",
     "if False:", "a stale position is caught", "tests/test_marking.py"),
    ("records/marking.py", "if abs(d) > tolerance_ms:", "if False:",
     "a diverged alignment is caught", "tests/test_marking.py"),
    ("records/marking.py", "if outranks(position.provenance, mark.provenance):",
     "if False:", "an alignment cannot outrank its tap", "tests/test_marking.py"),
    ("records/marking.py", "if outranks(self.provenance, P_CITED):", "if False:",
     "an alignment cannot claim P1", "tests/test_marking.py"),
    ("records/marking.py", "if (self.subject_id is None) != (self.lane_id is None):",
     "if False:", "a mark naming a student is lane-scoped", "tests/test_marking.py"),
    ("records/marking.py", 'if not (self.against or "").strip():', "if False:",
     "a position names its score", "tests/test_marking.py"),
    ("records/export.py",
     "served = [e for e in transfer.entries if getattr(e, \"rung\", None) is not NEVER_SERVED]",
     "served = list(transfer.entries)",
     "L5 never leaves in the payload", "tests/test_export.py"),
    ("records/export.py", "if got.digest != digest:", "if False:",
     "an altered file fails verification", "tests/test_export.py"),
    ("records/export.py", "if got is None:", "if False:",
     "a missing file fails verification", "tests/test_export.py"),
    ("records/export.py", "if not transfer.complete:", "if False:",
     "an incomplete transfer exports nothing", "tests/test_export.py"),
    ("tools/conform.py", "return 1 if fails else 0", "return 0",
     "a failing check fails the build", "tests/test_conform.py"),
    ("tools/conform.py", "return self.state is State.PASS", "return True",
     "UNKNOWN is not a pass", "tests/test_conform.py"),
    # The socket checker, against tests/fixtures/decoys — source that really
    # does open sockets, parsed and never imported.
    ("tools/sockets.py", "return _UNRESOLVED if value is None else value",
     "return value or _UNRESOLVED",
     'bind(("", 8560)) is all-interfaces, not unresolved', "tests/test_sockets.py"),
    ("tools/sockets.py", "if wider:", "if False:",
     "a wider host than declared", "tests/test_sockets.py"),
    ("tools/sockets.py", "if not e.resolved:", "if False:",
     "an unresolvable bind is not a pass", "tests/test_sockets.py"),
    ("tools/sockets.py", "return self.port == e.port and self.host == e.host",
     "return self.port == e.port",
     "a declared port is not enough", "tests/test_sockets.py"),
    ("tools/sockets.py", "return self.verdict is Verdict.CLEAN",
     "return self.verdict is not Verdict.FINDINGS",
     "a vacuous scan is not a clean one", "tests/test_sockets.py"),
    ("tools/sockets.py", 'if name == "listen" and host == _UNRESOLVED:',
     "if False:", "a backlog is not an address", "tests/test_sockets.py"),
    ("tools/sockets.py", "for e in outbound:", "for e in ():",
     "outbound is a finding", "tests/test_sockets.py"),
    # tools/purity.py — the two checks that lived in conform.py and shipped
    # broken. Each mutation restores one of the holes the decoys found.
    ("tools/purity.py", "files = [base] if base.is_file() else sorted(base.rglob(\"*.py\"))",
     "files = [base] if base.is_file() else sorted(base.glob(\"*.py\"))",
     "a subpackage is scanned", "tests/test_purity.py"),
    ("tools/purity.py", "if name in _DYNAMIC:", "if False:",
     "a dynamic import is egress", "tests/test_purity.py"),
    ("tools/purity.py", "elif owner in _SPAWN_MODULES and name in _SPAWN_CALLS:",
     "elif False:", "a process spawn is egress", "tests/test_purity.py"),
    ("tools/purity.py", "if mode is None:", "if False:",
     "a non-literal mode is a write", "tests/test_purity.py"),
    ("tools/purity.py", "elif any(m in mode for m in _WRITE_MODES):",
     "elif False:", "open(w) is a write", "tests/test_purity.py"),
    ("tools/purity.py", "elif name in _UNAMBIGUOUS_WRITES:", "elif False:",
     "write_text is a write", "tests/test_purity.py"),
    ("tools/purity.py",
     "elif name in _OWNED_WRITES and (owner in _FS_OWNERS or _on_a_path(node.func)):",
     "elif name in _OWNED_WRITES:",
     "dataclasses.replace is not os.replace", "tests/test_purity.py"),
    ("tools/purity.py", "return self.reach in (Reach.WRITE, Reach.UNKNOWN_MODE)",
     "return self.reach in (Reach.WRITE, Reach.UNKNOWN_MODE, Reach.READ)",
     "a read is not a write", "tests/test_purity.py"),
    ("tools/conform.py", "    if not n:\n        return Check(\"no-egress\", what, State.UNKNOWN,",
     "    if False:\n        return Check(\"no-egress\", what, State.UNKNOWN,",
     "a scan of nothing is not a pass", "tests/test_purity.py"),
    # tools/discipline.py — the last two checks, each mutation restoring one of
    # the holes the decoys found.
    ("tools/discipline.py", "if isinstance(node, ast.Delete):", "if False:",
     "del is a deletion", "tests/test_discipline.py"),
    ("tools/discipline.py", "if _is_standing(who):", "if False:",
     "removing standing is a deletion", "tests/test_discipline.py"),
    ("tools/discipline.py", "for arg in list(node.args) + [k.value for k in node.keywords]:",
     "for arg in list(ast.walk(tree)):",
     "a DELETE in prose is not a deletion", "tests/test_discipline.py"),
    ("tools/discipline.py", "if not _exits_nonzero(node.body):", "if False:",
     "a swallowing runner is caught", "tests/test_discipline.py"),
    # _exits_nonzero has two conditions and the first version checked one.
    # These three restore each hole the review found.
    ("tools/discipline.py", "    if isinstance(arg, ast.Constant):\n        return arg.value not in (0, None, False)",
     "    if isinstance(arg, ast.Constant):\n        return True",
     "exit(0) is not a failing exit", "tests/test_discipline.py"),
    ("tools/discipline.py", "    if arg is None:\n        return False",
     "    if arg is None:\n        return True",
     "a bare exit is not a failing exit", "tests/test_discipline.py"),
    ("tools/discipline.py", 'return owner in ("sys", "os") and func.attr in ("exit", "_exit")',
     'return func.attr in ("exit", "_exit")',
     "logger.exit() is not sys.exit", "tests/test_discipline.py"),
    ("tools/discipline.py", 'return n in STANDING_NAMES or n.rsplit("_", 1)[-1] in STANDING_NAMES',
     "return n in STANDING_NAMES",
     "a prefix does not hide a removal", "tests/test_discipline.py"),
    ("tools/discipline.py", "    if isinstance(node, ast.JoinedStr):", "    if False:",
     "an f-string DELETE is found", "tests/test_discipline.py"),
    ("tools/discipline.py", "if not body:", "if False:",
     "an empty runner is caught", "tests/test_discipline.py"),
    ("tools/discipline.py", 'isinstance(left, ast.Name) and left.id == "__name__"',
     "isinstance(left, ast.Name)",
     "the guard's left side is __name__", "tests/test_discipline.py"),
    ("tools/discipline.py", 'and comps[0].value == "__main__")', "and True)",
     "the guard's right side is __main__", "tests/test_discipline.py"),
    ("tools/discipline.py", "if not any(s in p.relative_to(base).parts for s in skip))",
     "if not any(s in p.parts for s in skip))",
     "the exclusion does not block inspection", "tests/test_discipline.py"),
    ("tools/sockets.py",
     "            if not any(d.covers(e) for e in listeners):", "            if False:",
     "a stale declaration is a finding", "tests/test_sockets.py"),
    # Mutate the *document*, not the test. The first attempt here disabled the
    # assertion in test_component_map.py and asked test_component_map.py to
    # notice — circular, and the harness reported SURVIVES for it, correctly.
    # A guard's mutation belongs on the artifact the guard watches.
    ("docs/ARCHITECTURE.md", "VERIFIED-COUNT: 10 of 40", "VERIFIED-COUNT: 40 of 40",
     "§14's header figure is enforced", "tests/test_component_map.py"),
    # The join forwards every argument `serve()` takes. Each of the next two
    # reverts one to the value it effectively had when `dispatch()` did not
    # accept it at all — which is how §18 item 12 came to be unreachable
    # through the only path that renders, gates and logs.
    ("records/dispatch.py", "threshold=threshold, widenings=widenings)",
     "threshold=None, widenings=())",
     "the join forwards the self-edge threshold", "tests/test_dispatch.py"),
    ("records/dispatch.py", "known_as_of=known_as_of, envelopes=envelopes,",
     "known_as_of=None, envelopes=envelopes,",
     "the join forwards the knowledge horizon", "tests/test_dispatch.py"),
    ("records/serving.py",
     "via_edge=edge.kind if edge else None,\n                       provenance=fld.provenance)",
     "via_edge=edge.kind if edge else None)",
     "an instruction carries its provenance", "tests/test_dispatch.py"),
    # The only mutation in this list that ADDS something rather than removing
    # it. The refusal branch must stay provenance-free, so the ablation is the
    # symmetry a later reader would "tidy up" — and the test has to notice.
    ("records/serving.py",
     "no derived instruction authored\",\n                   via_edge=edge.kind if edge else None)",
     "no derived instruction authored\",\n                   via_edge=edge.kind if edge else None, provenance=fld.provenance)",
     "a refusal leaks no provenance", "tests/test_dispatch.py"),
    ("records/serving.py", "if edge.kind == SELF and not past_threshold(at, threshold):",
     "if False:", "the self edge's L3 cap", "tests/test_standing.py"),
    ("records/serving.py", "if edge.kind == SELF and not past_threshold(at, threshold):",
     "if edge.kind == SELF:", "W-6 threshold lifts the cap", "tests/test_standing.py"),
    ("records/standing.py", "if not w.live_at(at):", "if False:",
     "widening expiry", "tests/test_standing.py"),
    ("records/standing.py", "if standing:", "if True:",
     "widening signer standing at use", "tests/test_standing.py"),
    ("records/standing.py", "if name == self.subject_id:", "if False:",
     "W-4: a ward cannot sign its own widening", "tests/test_standing.py"),
    ("records/standing.py", "if cat in _WILDCARDS:", "if False:",
     "a widening names one category", "tests/test_standing.py"),
    ("records/standing.py", "if self.state is not LogAccess.GRANTED:", "if False:",
     "a refused log view iterates", "tests/test_standing.py"),
    ("records/standing.py", "if len(subjects) > 1:", "if False:",
     "own_log fails closed on an unscoped log", "tests/test_standing.py"),
    ("records/standing.py", "if not holds:", "if False:",
     "own_log needs a live self edge", "tests/test_standing.py"),
    ("records/standing.py", "return threshold is not None and at >= threshold",
     "return threshold is None or at >= threshold",
     "an unknown threshold is not a reached one", "tests/test_standing.py"),
]


def run(suite: str) -> bool:
    """True when the suite passes.

    **Bytecode caching is disabled, and it is not a tidiness measure.** This
    harness mutates a file, runs a suite, and restores the file — the whole
    cycle inside one second. CPython validates a cached `.pyc` against
    `(mtime_seconds, size)`, so a mutation whose replacement is the *same length*
    as the original can leave a `.pyc` that survives the restore, and the next
    subprocess then executes code that is on nobody's disk.

    The failure it produces is silent and points the wrong way: a mutation
    reported as `caught` when the running code was never mutated, or as
    `SURVIVES` when it was. That is scout-13 row B again — *"a mutation which
    kills no gate is a failed mutation, not a passing one"* — arriving through
    the interpreter rather than through a `sed` that stopped matching.

    Found the ordinary way, 2026-07-31: a stale `__pycache__` entry made
    `tools/conform.py` return `PASS` from a branch the source could not reach,
    and it reproduced outside pytest, which is what ruled out test pollution.
    """
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-B", str(ROOT / suite)],
                       capture_output=True, cwd=ROOT, env=env)
    return r.returncode == 0


def _purge_bytecode() -> int:
    """Drop every `__pycache__` before the first mutation.

    A cache written before this run is keyed to the *unmutated* file and can
    outlive a same-size mutation. Clearing once at the start costs a second of
    recompilation and removes the class of problem.
    """
    n = 0
    for d in ROOT.rglob("__pycache__"):
        if ".git" in d.parts:
            continue
        for f in d.glob("*.pyc"):
            f.unlink()
            n += 1
    return n


def ablate(target: str, pattern: str, repl: str, label: str, suite: str) -> str:
    path = ROOT / target
    original = path.read_text(encoding="utf-8")
    mutated = original.replace(pattern, repl, 1)
    if mutated == original:
        return "NOT APPLIED"          # an error, not a pass — see the docstring
    try:
        path.write_text(mutated, encoding="utf-8")
        return "SURVIVES" if run(suite) else "caught"
    finally:
        path.write_text(original, encoding="utf-8")


def main() -> int:
    dropped = _purge_bytecode()
    if dropped:
        print(f"  purged {dropped} stale .pyc before mutating")
    print("  control".ljust(38), end="")
    healthy = all(run(s) for s in (
        "tests/test_serving.py", "tests/test_sending.py", "tests/test_classify.py",
        "tests/test_disclosure.py", "tests/test_sealing.py", "tests/test_dispositions.py",
        "tests/test_exit.py", "tests/test_crossing.py", "tests/test_dispatch.py",
        "tests/test_witness.py", "tests/test_receipts.py"))
    print("green" if healthy else "RED — every result below is meaningless")
    if not healthy:
        return 1

    bad = []
    for target, pat, repl, label, suite in MUTATIONS:
        result = ablate(target, pat, repl, label, suite)
        print(f"  {label:<36}{result}")
        if result != "caught":
            bad.append((label, result))

    print()
    if bad:
        for label, why in bad:
            print(f"  FAIL {label}: {why}")
        return 1
    print(f"  all {len(MUTATIONS)} guards ablate red; the suites are not decorative")
    return 0


def test_every_guard_can_be_shown_to_fail():
    """The whole harness, as one assertion, so CI runs it with the rest."""
    assert main() == 0, "a guard survived ablation, or a mutation failed to apply"


if __name__ == "__main__":
    raise SystemExit(main())
