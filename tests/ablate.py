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

**This harness edits the working tree, and until 2026-07-31 it could leave it
edited.** Two ways, both hit for real on the same day:

- **A signal.** `ablate()` restores in a `finally`, which `SIGTERM` does not
  run — a CI timeout or a killed shell left the mutation on disk. The failure is
  silent and the wrong way round: a mutated `tools/conform.py` with
  `Check.conforms` forced to `True` reports **14/14 pass** and will write that
  into a dated conformance record.
- **A second run.** Running the suite while ablating starts a second ablation,
  because `tests/test_conform.py` shells out to this script. The second run reads
  an already-mutated file as its *original* and restores the mutation
  permanently.

Three mechanisms now, each proven by doing the thing to it: the original is
written to `.ablate-inflight.json` **before** the edit and recovered at startup
(survives `SIGKILL`), `SIGTERM`/`SIGINT`/`SIGHUP` raise so the `finally` runs,
and `.ablate-lock` refuses a concurrent run while its holder is alive.

**Bytecode caching is off** for the same family of reason — see `run()`.

    python3 tests/ablate.py
"""

from __future__ import annotations

import atexit
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: What is mutated right now, and what it was. Written **before** the edit and
#: removed after the restore, so a run that is killed leaves a breadcrumb rather
#: than a corrupted file.
INFLIGHT = ROOT / ".ablate-inflight.json"

#: Held for the duration of a run. Two concurrent runs corrupt the tree: the
#: second reads an already-mutated file as its "original" and restores to that.
LOCK = ROOT / ".ablate-lock"

#: (target file, pattern, replacement, label, suite that must catch it)
MUTATIONS = [
    # records/rungs.py — the base every other module imports, and it carried no
    # mutation until 2026-07-31. Rule 14 is enforced by the *type*, so the
    # mutations are on the type.
    # Two mutations for rule 14, because the first version of this row was
    # itself the defect it was written to prevent. `class Rung(Enum)` ->
    # `IntEnum` alone does NOT restore the marching-arts defect: IntEnum
    # members must be int, the values here are names, and the class body
    # raises `ValueError: invalid literal for int()` at import. The suite then
    # went red with ZERO failing tests -- it died on line 25, the import --
    # and this harness reported `caught` because the return code was nonzero.
    # The exhaustive 25-pair sweep had never run under its own mutation.
    #
    # (a) restores the defect that actually happened: int base AND int values.
    ("records/rungs.py",
     'class Rung(Enum):\n    """A sensitivity rung. Values are names, deliberately not numbers."""\n\n'
     '    L1 = "open"\n    L2 = "internal"\n    L3 = "attributed"\n'
     '    L4 = "restricted"\n    L5 = "enforcement_only"',
     'class Rung(__import__("enum").IntEnum):\n    """A sensitivity rung."""\n\n'
     '    L1 = 1\n    L2 = 2\n    L3 = 3\n    L4 = 4\n    L5 = 5',
     "rule 14: rungs do not compare", "tests/test_rungs.py"),
    # (b) adds one operator and nothing else, so the module still imports and
    # the ONLY thing that changes is whether a comparison works. This is the
    # one that proves the sweep is doing the work rather than the import.
    ("records/rungs.py",
     '    def __str__(self) -> str:  # "L3", never "3"',
     '    def __lt__(self, other):\n        return _ASCENDING.index(self) < _ASCENDING.index(other)\n\n'
     '    def __str__(self) -> str:  # "L3", never "3"',
     "rule 14: one operator is enough", "tests/test_rungs.py"),
    ("records/rungs.py", 'raise ValueError("compose() of no rungs — an empty record is not L1")',
     "return Rung.L1", "compose() of nothing is not L1", "tests/test_rungs.py"),
    ("records/rungs.py", 'raise ValueError(f"not a rung: {value!r}") from None',
     "return Rung.L1", "parse refuses rather than defaulting", "tests/test_rungs.py"),
    ("records/rungs.py", "return _ASCENDING.index(a) > _ASCENDING.index(b)",
     "return _ASCENDING.index(a) >= _ASCENDING.index(b)",
     "outranks is strict", "tests/test_rungs.py"),
    ("records/rungs.py", "return _ASCENDING.index(a) >= _ASCENDING.index(floor)",
     "return _ASCENDING.index(a) > _ASCENDING.index(floor)",
     "at_least includes the floor", "tests/test_rungs.py"),
    ("records/rungs.py", "return max(rungs, key=_ASCENDING.index)",
     "return min(rungs, key=_ASCENDING.index)",
     "composition is max", "tests/test_rungs.py"),
    ("records/rungs.py", "DERIVE_AT = Rung.L3", "DERIVE_AT = Rung.L4",
     "the derive floor is L3", "tests/test_rungs.py"),
    ("records/rungs.py", "        return self.name", "        return self.value",
     "a rung prints as its name", "tests/test_rungs.py"),
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
    # `"and r.live_at(at)"` alone appears twice in records/sending.py — once in
    # recipients() and once in who_could_see() — so it mutated the first site
    # and left the second unablated for as long as this row existed. Split, so
    # both dated checks are pointed at. Found by the uniqueness check below.
    ("records/sending.py",
     "             and r.live_at(at)\n             and r.known_at(horizon)),",
     "             and r.known_at(horizon)),",
     "restriction dates, on the send path", "tests/test_sending.py"),
    ("records/sending.py",
     "             and r.live_at(at) and r.known_at(at)),",
     "             and r.known_at(at)),",
     "restriction dates, on the who-could-see path", "tests/test_sending.py"),
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
    # `return None  # (` commented out the opening paren and left the rest of
    # the string dangling, so the mutated file raised IndentationError and did
    # not parse. Red, therefore reported `caught`, therefore W-7's sharpest
    # mechanism -- `recommendation` raising rather than returning None -- had
    # never been shown to fail. Replace the whole call so the file compiles.
    ("records/conflict.py",
     '        raise NotComputable(\n            "W-7: the system presents and a human decides. There is no "\n'
     '            "recommendation here and adding one would be the violation."\n        )',
     "        return None",
     "an escalation yields no recommendation", "tests/test_conflict.py"),
    ("records/conflict.py", "if not who or who.lower() in _NOT_A_PERSON:", "if False:",
     "escalation names a person", "tests/test_conflict.py"),
    ("records/conflict.py",
     "if self.stake is Stake.BETWEEN_WARDS and len(set(self.affects)) < 2:",
     "if False:", "a collision names two", "tests/test_conflict.py"),
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
    # The harness's own verdict, watched by tests/test_ablate.py. Not the
    # circular case below: the mutation is on the artifact and a *different*
    # file notices. Both replacements keep tests/ablate.py parsing on purpose —
    # a mutation that broke this file could not be recovered by it, because
    # _recover() runs from the file the mutation just broke.
    # Both patterns carry the line *under* the one being changed, so they
    # contain a real newline and cannot match their own single-line entries in
    # this table. That is not decoration: the first version of these two matched
    # here instead of in verdict(), mutated the table, and read SURVIVES.
    ("tests/ablate.py",
     '    if not any(line.startswith("FAIL ") for line in output.splitlines()):\n'
     '        return "NO NAMED FAILURE"',
     '    if False:\n        return "NO NAMED FAILURE"',
     "a nonzero exit is not a named failure", "tests/test_ablate.py"),
    ("tests/ablate.py",
     '    if not any(line.startswith("FAIL ") for line in output.splitlines()):\n'
     '        return "NO NAMED FAILURE"',
     '    if not any("FAIL " in line for line in output.splitlines()):\n'
     '        return "NO NAMED FAILURE"',
     "FAIL must begin the line", "tests/test_ablate.py"),
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
    # tools/audit.py — R16 and R17, the two checks §10 says the fleet rubric is
    # missing. Every branch of both, because a check whose comfortable answer is
    # the only one it has ever produced is the thing R17 itself is about.
    ("tools/audit.py", "        return self.verdict is Verdict.PASS",
     "        return self.verdict is not Verdict.FINDING",
     "ABSENT and UNKNOWN are not a pass", "tests/test_audit.py"),
    # The one mutation here that ADDS rather than removes. `seal` is the verb
    # records/sealing.py exposes, and it is rule 10's human seal over a machine
    # draft -- hashlib, no cipher. Putting it in the required set is the tidy-up
    # a later reader would make, and it turns R16 into a PASS over a repository
    # that encrypts nothing.
    ("tools/audit.py",
     '    "seal_at_rest", "unseal_at_rest", "encrypt_at_rest", "decrypt_at_rest",',
     '    "seal", "seal_at_rest", "unseal_at_rest", "encrypt_at_rest", "decrypt_at_rest",',
     "R16 matches a verb, not a filename", "tests/test_audit.py"),
    ("tools/audit.py", "    if not seam and not at_rest:", "    if not seam:",
     "R16: stored unsealed is not the same as unstored", "tests/test_audit.py"),
    ("tools/audit.py", "    if not disposed:", "    if False:",
     "R16: sealed without escrow is a finding", "tests/test_audit.py"),
    ("tools/audit.py", "    if not rehearsed:", "    if False:",
     "R16: an unrehearsed plan is not escrow", "tests/test_audit.py"),
    ("tools/audit.py", "    if uncovered:", "    if False:",
     "R17: an unablated detection site", "tests/test_audit.py"),
    ("tools/audit.py",
     "            if target == site[0] and (site[1] in pattern or site[1] in repl):",
     "            if True:",
     "R17: a mutation covers the site it names", "tests/test_audit.py"),
    ("tools/audit.py", "    if missing:", "    if False:",
     "R17: the record must report them caught", "tests/test_audit.py"),
    ("tools/audit.py", "    newest = records[-1]", "    newest = records[0]",
     "R17 reads the newest record", "tests/test_audit.py"),
    ("tools/audit.py",
     '        return not self.status.lower().startswith(("closed", "fixed", "withdrawn"))',
     '        return self.status.lower().startswith("open")',
     "a status nobody updated reads as open", "tests/test_audit.py"),
    # tools/conform.py — the security-audit row, which moved from UNKNOWN to a
    # gate on 2026-07-31.
    ("tools/conform.py", "    if not path.exists():", "    if False:",
     "a missing audit is ABSENT", "tests/test_conform.py"),
    ("tools/conform.py", "    if hot:", "    if False:",
     "an open high finding fails the build", "tests/test_conform.py"),
    ("tools/conform.py", "    if age > STALE_AFTER_DAYS:", "    if False:",
     "a stale audit is not a pass", "tests/test_conform.py"),
    # The artifact, not the guard. Both of these mutate the document and ask a
    # different file to notice -- the shape the §14 header-figure mutation
    # established, after the first attempt at it disabled an assertion and asked
    # the assertion to catch itself.
    ("docs/SECURITY-AUDIT.md",
     "**ABSENT** | — | No at-rest sealing entry point exists",
     "**PASS** | — | No at-rest sealing entry point exists",
     "the recorded R16 verdict is reconciled", "tests/test_audit.py"),
    ("docs/SECURITY-AUDIT.md", "| `TM-DEPS-01` | R14 | `S3` | open |",
     "| `TM-DEPS-01` | R14 | `S1` | open |",
     "an open S1 in the document fails conformance", "tests/test_conform.py"),
]


def _recover() -> str:
    """Restore anything a previous run left mutated.

    **The `finally` in `ablate()` is not enough and today proved it twice.** A
    `SIGTERM` — a CI timeout, a killed shell — terminates the interpreter without
    running `finally`, so the mutated file stays on disk. And a mutated
    `tools/conform.py` does not look broken: with `Check.conforms` forced to
    `True` it reports **14/14 pass** and writes that into a conformance record.

    So the original is written to a sidecar *before* the edit, and recovered
    here. This runs at startup, before anything is mutated.
    """
    if not INFLIGHT.exists():
        return ""
    try:
        state = json.loads(INFLIGHT.read_text(encoding="utf-8"))
        (ROOT / state["target"]).write_text(state["original"], encoding="utf-8")
        INFLIGHT.unlink()
        return state["target"]
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(
            f"  {INFLIGHT.name} is unreadable ({exc}). A previous run was killed "
            f"mid-mutation and this file is the only record of the original. "
            f"Restore by hand (git checkout) before running again."
        )


def _acquire_lock() -> None:
    """Refuse to run beside another ablation.

    Two runs mutating the same tree is not a race that produces a wrong answer;
    it produces a **wrong file**. The second run reads a mutated file as its
    baseline and "restores" the mutation permanently. Found by running the suite
    in the background while ablating in the foreground — the suite's own
    `check_ablation` shells out to this script.

    **The first version of this lock was itself a race** — `docs/SECURITY-AUDIT.md`
    TM-RACE-01, found 2026-07-31. It read `LOCK.exists()` and then wrote, which
    is check-then-act: two runs starting together both saw no lock, both wrote
    their pid, and both proceeded into the tree the lock exists to protect. A
    lock that can be held twice is a ledger of intent, not a lock. Acquisition
    is now a single `O_CREAT|O_EXCL` open, which the kernel makes atomic; the
    liveness check only runs once that open has already failed.
    """
    for attempt in (1, 2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if attempt == 2:
                raise SystemExit(
                    f"  {LOCK.name} keeps reappearing between the liveness check "
                    f"and the acquire. Something is creating it; remove it by hand."
                )
            try:
                pid = int(LOCK.read_text(encoding="utf-8").strip())
                os.kill(pid, 0)
            except (ValueError, OSError):
                LOCK.unlink(missing_ok=True)   # stale; the holder is gone
                continue
            raise SystemExit(
                f"  another ablation is running (pid {pid}). Two runs mutating one "
                f"tree corrupt it — the second restores the first's mutation. "
                f"Wait, or remove {LOCK.name} if that process is gone."
            )
        else:
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            atexit.register(lambda: LOCK.unlink(missing_ok=True))
            return


def _restore_on_signal() -> None:
    """Make `finally` run when the process is asked to stop."""
    def handler(signum, frame):
        raise SystemExit(f"  interrupted by signal {signum}; restoring")
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError):
            pass          # not on the main thread, or unsupported


def run(suite: str) -> tuple:
    """`(passed, output)` for one suite.

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
                       capture_output=True, cwd=ROOT, env=env, text=True)
    return r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def verdict(passed: bool, output: str) -> str:
    """What a suite's exit status and output say about a mutation.

    **A nonzero exit is not by itself evidence that a guard fired.** Until
    2026-07-31 this harness read `returncode == 0` and nothing else, so a
    mutation that broke the module's import, or produced a file that did not
    parse, was indistinguishable from one a test caught. Two shipped mutations
    were in that state and the report called both `caught`:

    * `class Rung(Enum)` -> `IntEnum` raised `ValueError` at import, because
      `IntEnum` members must be `int` and the rungs carry names. The 25-pair
      comparison sweep — the reason `tests/test_rungs.py` exists — had never
      executed under its own mutation.
    * `return None  # (` commented out an opening paren and left the rest of a
      string dangling, so `records/conflict.py` did not parse at all.

    So `caught` now requires a **named** failure: a line beginning `FAIL `,
    which every standalone runner in `tests/` prints and nothing else does.
    That is scout-13 row B once more — *"a mutation which kills no gate is a
    failed mutation, not a passing one"* — arriving through the import system
    rather than through a `sed` that stopped matching.

    The companion half of this change is in the runners themselves: they now
    catch `Exception` rather than only `AssertionError`, so a test that reaches
    an un-guarded path and raises `IndexError` is *reported* as a failure and
    the file keeps going. Before that, the first such test aborted the run and
    every later test in the file silently did not execute.
    """
    if passed:
        return "SURVIVES"
    if not any(line.startswith("FAIL ") for line in output.splitlines()):
        return "NO NAMED FAILURE"     # an error, not a pass — see above
    return "caught"


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


def ablate(target: str, pattern: str, repl: str, label: str, suite: str,
           inflight=None) -> str:
    """Mutate one file, run one suite, restore, and say what happened.

    `inflight` names the breadcrumb file. It is a parameter rather than a
    constant because `tests/test_ablate.py` calls this against the decoys while
    a real run may be holding `INFLIGHT`, and two writers to one sidecar is the
    concurrency defect this sidecar was added to fix.
    """
    sidecar = INFLIGHT if inflight is None else Path(inflight)
    path = ROOT / target
    original = path.read_text(encoding="utf-8")
    seen = original.count(pattern)
    if seen == 0:
        return "NOT APPLIED"          # an error, not a pass — see the docstring
    if seen > 1:
        # `str.replace(..., 1)` takes the FIRST occurrence and "the file
        # changed" was the only check, so a pattern in two places mutated one
        # site and reported on the other. `records/sending.py` carried
        # `and r.live_at(at)` in both recipients() and who_could_see(), and the
        # second half had never been ablated; it survived the moment it was.
        # An error, not a pass, for the same reason NOT APPLIED is one.
        return f"AMBIGUOUS x{seen}"
    mutated = original.replace(pattern, repl, 1)
    sidecar.write_text(json.dumps({"target": target, "original": original}),
                       encoding="utf-8")
    try:
        path.write_text(mutated, encoding="utf-8")
        return verdict(*run(suite))
    finally:
        path.write_text(original, encoding="utf-8")
        sidecar.unlink(missing_ok=True)


def main() -> int:
    _restore_on_signal()
    _acquire_lock()
    recovered = _recover()
    if recovered:
        print(f"  recovered {recovered} — a previous run was killed mid-mutation")
    dropped = _purge_bytecode()
    if dropped:
        print(f"  purged {dropped} stale .pyc before mutating")
    print("  control".ljust(38), end="")
    healthy = all(run(s)[0] for s in (
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
