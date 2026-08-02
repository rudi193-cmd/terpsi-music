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
    # The lane seal is one branch with two disjuncts and each is a separate
    # guard. Splitting them is the same lesson `and r.live_at(at)` taught in
    # records/sending.py: a pattern covering two conditions mutates as one and
    # leaves the other unablated.
    ("records/serving.py",
     "    if (lane_id is not None and lane_id != fld.lane_id) or (\n"
     "            ward is not None and ward != fld.subject_id):",
     "    if (lane_id is not None and lane_id != fld.lane_id) or (\n"
     "            False):",
     "W-3 default deny between wards", "tests/test_serving.py"),
    ("records/serving.py",
     "    if (lane_id is not None and lane_id != fld.lane_id) or (\n"
     "            ward is not None and ward != fld.subject_id):",
     "    if (False) or (\n"
     "            ward is not None and ward != fld.subject_id):",
     "W-3 lane seal", "tests/test_serving.py"),
    ("records/serving.py",
     "        if lane_id is None:\n            # An unnamed origin is unknown",
     "        if False:\n            # An unnamed origin is unknown",
     "an unnamed origin lane is not a wildcard", "tests/test_serving.py"),
    ("records/serving.py",
     "        if is_self_edge(e) and e.principal_id == principal_id and e.live_at(at):",
     "        if e.kind == SELF and e.principal_id == principal_id and e.live_at(at):",
     "a forged self edge does not make a ward", "tests/test_serving.py"),
    ("records/serving.py",
     "        if is_self_edge(e) and e.principal_id == principal_id and e.live_at(at):",
     "        if is_self_edge(e) and e.principal_id == principal_id:",
     "an ended self edge is not a ward's seal", "tests/test_serving.py"),
    # The rung ceiling. `None` and `()` are different instructions and the
    # first mutation collapses them, which is the fail-open a single sentinel
    # would have shipped.
    ("records/serving.py", "    if grants is not None:", "    if False:",
     "the grant ceiling is consulted", "tests/test_serving.py"),
    ("records/serving.py", "        if not at_least(cap, fld.rung):", "        if False:",
     "the ceiling refuses above itself", "tests/test_serving.py"),
    ("records/serving.py", "        if cap is None:", "        if False:",
     "no live grant is not an unlimited one", "tests/test_serving.py"),
    ("records/serving.py",
     "            and g.live_at(at)]",
     "            ]",
     "a grant's own dates", "tests/test_serving.py"),
    ("records/serving.py",
     "        if self.max_rung is NEVER_SERVED:",
     "        if False:",
     "L5 is unreachable through a grant", "tests/test_serving.py"),
    ("records/serving.py",
     "        if not lane or lane.lower() in _WILDCARDS:",
     "        if False:",
     "W-2: a grant names one lane", "tests/test_serving.py"),
    ("records/serving.py",
     "        if self.max_rung is Rung.L4 and not (self.purpose or \"\").strip():",
     "        if False:",
     "L4 without a purpose is not a grant", "tests/test_serving.py"),
    ("records/serving.py",
     "        if self.ended_known_at is not None and horizon < self.ended_known_at:",
     "        if False:",
     "the ending's own knowledge clock", "tests/test_orders.py"),
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
    # I-7, at the two verbs the clause names: *deleting or amending*.
    ("records/sealing.py", "    _i7(rec, by, \"rejection\")", "    pass",
     "I-7: the office cannot reject the ward's entry", "tests/test_sealing.py"),
    ("records/sealing.py", "    _i7(rec, by or \"\", \"re-draft\")", "    pass",
     "I-7: the office cannot rewrite the ward's entry", "tests/test_sealing.py"),
    ("records/standing.py", "    if author_id == subject_id:", "    if False:",
     "I-7's supersession asymmetry", "tests/test_standing.py"),
    ("records/standing.py", "    if principal_id == author_id:", "    if False:",
     "an author supersedes their own entry", "tests/test_standing.py"),
    ("records/standing.py",
     "    if not (author_id or \"\").strip() or not (subject_id or \"\").strip():",
     "    if False:",
     "unrecorded authorship is unknown, not the office's", "tests/test_standing.py"),
    ("records/standing.py", "    if not standing:", "    if False:",
     "superseding an office entry needs live standing", "tests/test_standing.py"),
    # `if at is None:` -> `if False:` would make `e.live_at(None)` raise, and a
    # crash is not a guard firing (see `verdict`). Flip the *answer* instead, so
    # the module still runs and only the decision changes.
    ("records/standing.py",
     "        return MaySupersede(\n            Supersession.UNKNOWN,\n"
     "            \"supersession is a dated act and no instant was supplied\")",
     "        return MaySupersede(\n            Supersession.PERMITTED,\n"
     "            \"supersession is a dated act and no instant was supplied\")",
     "an undated supersession is not permitted", "tests/test_standing.py"),
    # records/orders.py — §7.1's ending, bound.
    ("records/orders.py", "        if matches:", "        if False:",
     "an order ends a guardianship at all", "tests/test_orders.py"),
    ("records/orders.py", "                invalid_at=order.effective_at,",
     "                invalid_at=order.received_at,",
     "the ending takes the order's date, not the post's", "tests/test_orders.py"),
    ("records/orders.py",
     "                ended_by=f\"{order.authority} ({order.order_id})\",",
     "                ended_by=None,",
     "an ending records its authority", "tests/test_orders.py"),
    # Refusal 3, as the mutation rather than as the branch. `if len(after) !=
    # len(edges): -> if False:` SURVIVES and correctly: nothing in the function
    # can produce a shorter list, so the branch is a tripwire no mutation of the
    # *rest* of the code reaches, and a guard that cannot be made to fire has
    # not been shown to work. So the mutation is the forbidden act itself —
    # revocation by dropping the row — and the tripwire is what catches it.
    ("records/orders.py",
     "            ended.append(closed)\n            after.append(closed)",
     "            ended.append(closed)",
     "an ending never shortens the graph", "tests/test_orders.py"),
    ("records/orders.py", "    if standing.state is GuardianshipState.UNKNOWN:",
     "    if False:", "an order may not orphan a lane", "tests/test_orders.py"),
    ("records/orders.py", "    if not ended:", "    if False:",
     "an order against no standing is unknown", "tests/test_orders.py"),
    ("records/orders.py", "                   and e.invalid_at is None)",
     "                   )",
     "an ended standing is not re-ended", "tests/test_orders.py"),
    ("records/orders.py", "        if self.state is not Ended.APPLIED:", "        if False:",
     "a refused ending iterates", "tests/test_orders.py"),
    ("records/orders.py", "        if self.state is GuardianshipState.UNKNOWN:",
     "        if False:", "an unknown guardianship iterates", "tests/test_orders.py"),
    ("records/orders.py", "    if said:", "    if False:",
     "a declared state is read", "tests/test_orders.py"),
    ("records/orders.py", "    if order.kind is not OrderKind.SUPERSEDES:", "    if False:",
     "supersede takes a superseding order", "tests/test_orders.py"),
    ("records/orders.py",
     "        if self.kind is OrderKind.SUPERSEDES and not (self.successor_id or \"\").strip():",
     "        if False:",
     "a superseding order names its successor", "tests/test_orders.py"),
    ("records/orders.py",
     "        if not name or name.lower() in _NOT_A_PERSON:\n            raise ValueError(\n"
     "                f\"{self.authority!r} is not an authority;",
     "        if False:\n            raise ValueError(\n"
     "                f\"{self.authority!r} is not an authority;",
     "an order names its authority", "tests/test_orders.py"),
    ("records/orders.py", "        if not (self.reason or \"\").strip():", "        if False:",
     "a lane's unguarded state names a reason", "tests/test_orders.py"),
    ("records/dispatch.py", "threshold=threshold, widenings=widenings, grants=grants)",
     "threshold=threshold, widenings=widenings, grants=None)",
     "the join forwards the grant ceiling", "tests/test_dispatch.py"),
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
    # records/publication.py — the egress gate over an anchor, the calendar the
    # gate enforces, and the states around a proof that has not come back. Each
    # mutation is an attempt at one of the three things §18 item 15's weekly
    # leg must refuse.
    ("records/publication.py", "    extra = [n for n in declared if n not in MAY_CROSS]",
     "    extra = []", "a smuggled field is refused", "tests/test_publication.py"),
    ("records/publication.py",
     '    hung = sorted(k for k in getattr(anchor, "__dict__", {}) if k not in MAY_CROSS)',
     "    hung = []", "a field hung on the instance is refused",
     "tests/test_publication.py"),
    ("records/publication.py", "    if not isinstance(anchor, Anchor):", "    if False:",
     "only an anchor may be published", "tests/test_publication.py"),
    ("records/publication.py", "    if not cadence.is_slot(anchor.at):", "    if False:",
     "publication off the calendar", "tests/test_publication.py"),
    ("records/publication.py", "        if self.tolerance * 2 >= self.every:", "        if False:",
     "a tolerance that admits every moment", "tests/test_publication.py"),
    ("records/publication.py", "        if key in seen:", "        if False:",
     "two anchors in one slot", "tests/test_publication.py"),
    ("records/publication.py",
     '        "\\x1f".join([head, str(count), at.isoformat()]).encode("utf-8")).digest()',
     '        head.encode("utf-8")).digest()',
     "the slot is bound into the commitment", "tests/test_publication.py"),
    ("records/publication.py",
     "        ok, why = permitted(self.anchor)\n        if not ok:",
     "        ok, why = permitted(self.anchor)\n        if False:",
     "a submission around a smuggled anchor", "tests/test_publication.py"),
    ("records/publication.py", "        return self.state is Publication.PROVEN",
     "        return self.state is not Publication.NOT_SUBMITTED",
     "only a proven publication is a witness", "tests/test_publication.py"),
    ("records/publication.py", "        for s in statuses if s.state is Publication.PROVEN)",
     "        for s in statuses if s.state is not Publication.NOT_SUBMITTED)",
     "a pending submission yields no receipt", "tests/test_publication.py"),
    ("records/publication.py", "        if best.attested_at is None:", "        if False:",
     "a promise is not a timestamp", "tests/test_publication.py"),
    ("records/publication.py", "        if best.attested_at < sub.anchor.at:", "        if False:",
     "a proof attested too early", "tests/test_publication.py"),
    ("records/publication.py", "            if waited > window:", "            if False:",
     "a pending submission goes overdue", "tests/test_publication.py"),
    ("records/publication.py", "        if not cadence.is_slot(sub.anchor.at):", "        if False:",
     "an off-calendar submission is reported", "tests/test_publication.py"),
    ("records/witness.py", "    if got != anchor.head:", "    if False:",
     "a doctored derivation does not redeem", "tests/test_publication.py"),
    ("records/witness.py",
     "    return Anchor(head, sum(c for _, _, c in ledger_derivation(ledger)), at)",
     "    return Anchor(head, 0, at)",
     "a programme anchor counts every lane", "tests/test_publication.py"),
    # records/receipts.py — the issuance seam. §18 item 15 records the Ed25519
    # dependency; these are the guards that keep its absence legible instead of
    # silently equivalent to the symmetric path.
    ("records/receipts.py", "    if v.issuance is not receipt.issuance or receipt.scheme != v.scheme:",
     "    if False:", "cannot-check is not not-authentic", "tests/test_receipts.py"),
    ("records/receipts.py", "    if (key is None) == (signer is None):", "    if False:",
     "issuance is chosen, not defaulted", "tests/test_receipts.py"),
    ("records/receipts.py",
     '    def tag(self, material: str) -> str:\n        raise NoSigner(',
     '    def tag(self, material: str) -> str:\n        return "ed25519:" + "0" * 128\n        raise NoSigner(',
     "an absent signer refuses rather than falling back", "tests/test_receipts.py"),
    ("records/receipts.py",
     "    return \"\\x1f\".join([lane_id, str(position), digest, issued_at.isoformat(),\n"
     "                        to_guardian, issuance.value])",
     "    return \"\\x1f\".join([lane_id, str(position), digest, issued_at.isoformat(),\n"
     "                        to_guardian])",
     "the issuance claim is inside the tag", "tests/test_receipts.py"),
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
    # The one-lane rule moved to records/conflict.py on 2026-07-31, when
    # attendance and fees became its second and third callers (rule 12). One
    # guard, three suites — each row proves that suite notices, because a
    # shared middle whose only ablation points at one caller is a middle whose
    # other callers are decorative.
    ("records/conflict.py", "if len(lanes) > 1:", "if False:",
     "a statistic reads one lane", "tests/test_practice.py"),
    ("records/conflict.py", "if len(lanes) > 1:", "if False:",
     "an attendance statistic reads one lane", "tests/test_attendance.py"),
    ("records/conflict.py", "if len(lanes) > 1:", "if False:",
     "a balance reads one lane", "tests/test_fees.py"),
    ("records/conflict.py", "if len(lanes) > 1:", "if False:",
     "one_lane refuses rather than filtering", "tests/test_conflict.py"),
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
    # records/inference.py — refusal 1, enforced on what answered. Every clause
    # here has a mutation, because this is the one guard in the tree whose
    # subject is a disclosure that has *already happened* by the time it runs:
    # a hole does not produce a wrong answer, it produces a fluent one.
    ("records/inference.py", "    if provider != LOCAL:", "    if False:",
     "only the local provider may answer", "tests/test_inference.py"),
    ("records/inference.py", "    if not tags:", "    if False:",
     "an untagged call is unknown", "tests/test_inference.py"),
    ("records/inference.py", "    if unknown:", "    if False:",
     "an unrecognised class is unknown", "tests/test_inference.py"),
    ("records/inference.py",
     "    if not isinstance(provider, str) or not provider.strip():",
     "    if False:", "a missing provider label is unknown", "tests/test_inference.py"),
    ("records/inference.py", "    if not is_local_address(endpoint):", "    if False:",
     "the local label at another machine", "tests/test_inference.py"),
    ("records/inference.py",
     "    if not isinstance(text, str) or not text.strip():",
     "    if False:", "an empty answer is absence", "tests/test_inference.py"),
    ("records/inference.py",
     "    if (rung is not None and at_least(rung, DERIVE_AT)\n"
     "            and not (tags & COVERED_CLASSES)):",
     "    if False:", "the rung and the classes must agree", "tests/test_inference.py"),
    # The refusal must arrive *before* the record reaches a model. Removing this
    # line still refuses -- from accept(), afterwards -- which is an audit note
    # rather than a guard, and only the fired-flag test can tell the two apart.
    ("records/inference.py", "    _tags(classes)\n    try:\n        pair = call()",
     "    try:\n        pair = call()",
     "the tagging is checked before the call", "tests/test_inference.py"),
    ("records/inference.py",
     '        raise LocalModelUnavailable(\n'
     '            f"the inference call raised {type(exc).__name__}: {exc}") from exc',
     '        raise NonLocalInference(\n'
     '            f"the inference call raised {type(exc).__name__}: {exc}") from exc',
     "a stopped local model has its own state", "tests/test_inference.py"),
    # The ADD mutation: refusal 1 defeated by keyword rather than by branch.
    # `records/conflict.py`'s shape is that the wrong answer has no field to
    # live in, so the ablation is the field a later reader would add for
    # "resilience".
    ("records/inference.py",
     "def through(call: Callable[[], object], *, classes: Sequence[str], endpoint: str,",
     "def through(call: Callable[[], object], *, classes: Sequence[str], endpoint: str,\n"
     "            fallback=None,",
     "no parameter can allowlist a provider", "tests/test_inference.py"),
    # The type, not only the constructor. With the vetting gone from
    # __post_init__ an Answer holding a third party's text becomes
    # representable, and accept() is left as the only thing standing.
    ("records/inference.py",
     "        text, provider, tags, endpoint = _vet(\n"
     "            self.text, self.provider, self.classes, self.endpoint, self.rung)",
     "        text, provider, tags, endpoint = (\n"
     "            self.text, self.provider, frozenset(self.classes), self.endpoint)",
     "the type itself vets", "tests/test_inference.py"),
    # tools/imports.py — TM-DEPS-01's gate. The fail-open direction: a check
    # that judges every import resolved never flags the undeclared one, and the
    # decoy's `requests`/`flask` stop being findings.
    ("tools/imports.py",
     "        out.append(Reach(kind, module, line, root, detail, root in allowed))",
     "        out.append(Reach(kind, module, line, root, detail, True))",
     "an undeclared import is a finding", "tests/test_imports.py"),
    # TM-ROOT-01's committed-tree half: a path with a trust-root component is a
    # finding. Neutering the component match lets `mcp_apps/` and a bare gitlink
    # slip, which the acceptance tests attempt (refusal 2, §6).
    ("tools/trustroot.py",
     "    if any(part in _TRUST_ROOT_DIRS for part in parts):",
     "    if False:",
     "a committed trust-root path is a finding", "tests/test_trustroot.py"),
    # tools/providers.py — the tripwire. Its mutations are the fail-open
    # direction first: a checker that clears everything is silent in exactly
    # the direction nobody notices.
    ("tools/providers.py", "        guarded = id(node) in inside", "        guarded = True",
     "an unguarded call is a finding", "tests/test_providers.py"),
    ("tools/providers.py",
     '        prefix = dotted.rsplit(".", 1)[0] if "." in dotted else ""\n'
     "        is_guard = (dotted in entries\n"
     "                    or (_tail(dotted) in GUARD_ENTRIES\n"
     '                        and (prefix in modules or prefix.split(".")[0] in modules)))',
     '        prefix = ""\n        is_guard = bool(entries or modules)',
     "importing the guard is not going through it", "tests/test_providers.py"),
    ("tools/providers.py",
     "        marker = _endpoint_in(node) if _tail(dotted) in _SENDERS else None",
     "        marker = None",
     "a provider reached without the router", "tests/test_providers.py"),
    ("tools/providers.py", "    if not calls:", "    if False:",
     "a scan of nothing is not clean", "tests/test_providers.py"),
    ("tools/conform.py",
     '    if r.verdict is Verdict.VACUOUS:\n'
     '        return Check("local-inference", what, State.UNKNOWN,',
     '    if False:\n        return Check("local-inference", what, State.UNKNOWN,',
     "refusal 1 is UNKNOWN, not PASS, while nothing infers", "tests/test_providers.py"),
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
    ("tools/purity.py",
     "return self.reach in (Reach.WRITE, Reach.UNKNOWN_MODE, Reach.UNPARSEABLE,\n"
     "                              Reach.DB_WRITE, Reach.UNKNOWN_SQL)",
     "return self.reach in (Reach.WRITE, Reach.UNKNOWN_MODE, Reach.UNPARSEABLE,\n"
     "                              Reach.DB_WRITE, Reach.UNKNOWN_SQL, Reach.READ)",
     "a read is not a write", "tests/test_purity.py"),
    # --- the store's declaration seam (G-C) -------------------------------
    #
    # Each of these restores a hole the write-path reconciliation was written to
    # close, and each must be caught by the suite named beside it. The first is
    # the one the gate is *for*: with the finding suppressed, a module writing
    # outside the declaration passes.
    ("tools/manifest.py",
     "        if not any(_covers(d, module) for d in paths):",
     "        if False:",
     "G-C: an undeclared write path fails the build", "tests/test_manifest.py"),
    ("tools/purity.py",
     "            if name in _SQL_EXECUTORS:\n                out.extend(_sql_touches(node, module))",
     "            if False:\n                out.extend(_sql_touches(node, module))",
     "a write to a database is a write", "tests/test_purity.py"),
    ("tools/purity.py",
     "    receiver_is_path = isinstance(call.func, ast.Attribute)\n    index = 0 if receiver_is_path else 1",
     "    index = 1",
     "path.open('w') is a write, and the mode is not always second",
     "tests/test_purity.py"),
    # tools/drivers.py — the tripwire on the second dependency. Two mutations,
    # because the checker has two ways to go quiet: admit everything, or see
    # nothing.
    ("tools/drivers.py",
     'ALLOWED: Tuple[str, ...] = ("store/",)',
     'ALLOWED: Tuple[str, ...] = ("store/", "")',
     "the driver is admitted in store/ and nowhere else", "tests/test_drivers.py"),
    ("tools/drivers.py",
     "        elif isinstance(node, ast.Call):\n            name = _dotted(node.func)",
     "        elif False:\n            name = _dotted(node.func)",
     "a dynamic import of the driver is still an import", "tests/test_drivers.py"),
    # store/ — the two guards that are pure Python and can be ablated without a
    # database. The role split, the migration refusals, the narration pairing
    # and the killed-connection channel are ablated in the schema job instead:
    # they need a cluster, and a mutation whose suite cannot run is a mutation
    # that reports SURVIVES for the wrong reason.
    ("store/reading.py",
     "        if self.state is not ReadState.ROWS:\n            raise StoreUnavailable(",
     "        if False:\n            raise StoreUnavailable(",
     "an errored read is not an empty result",
     "tests/test_rule13_acceptance.py"),
    # store/sealing_plan.py and store/writing.py — S-3's seam. Every mutation
    # here is caught by tests/test_sealing_plan.py, which needs no database:
    # the derivation is over migration text and the seam's refusals happen
    # before a statement is built. The acts that need a cluster are ablated in
    # the workflow's "Ablate the sealing guards" step, for the reason stated
    # above — a mutation whose suite cannot run reports SURVIVES for the wrong
    # reason.
    #
    # The exclusions, one at a time. Each is a separate guard and a pattern
    # covering two would leave one unablated -- the lesson `and r.live_at(at)`
    # taught in records/sending.py.
    ("store/sealing_plan.py", "        if sql_type != CONTAINER_TYPE:",
     "        if False:",
     "a predicate column is not a payload", "tests/test_sealing_plan.py"),
    ("store/sealing_plan.py", "        if _is_key(column, rest, body):",
     "        if False:",
     "a key the store joins on is never sealed", "tests/test_sealing_plan.py"),
    ("store/sealing_plan.py", "        if len(_lane_columns(body, table)) != 1:",
     "        if False:",
     "a row with no single lane has no key to seal under",
     "tests/test_sealing_plan.py"),
    ("store/sealing_plan.py", "        if _CHAIN_COLUMNS & set(cols):",
     "        if False:",
     "chain material is not sealed under the key an erasure destroys",
     "tests/test_sealing_plan.py"),
    # The circularity, restored. Without this branch the sealing migration's own
    # tombstone reads as evidence that the column should not have been sealed,
    # and the derivation reports the opposite of what it did.
    ("store/sealing_plan.py",
     "def _is_sealing_constraint(expression: str) -> bool:\n    if _TOMBSTONE.match(expression):",
     "def _is_sealing_constraint(expression: str) -> bool:\n    if False:",
     "the derivation does not read its own output",
     "tests/test_sealing_plan.py"),
    # The seam itself. This is the one that matters: with it gone the caller's
    # clear payload goes straight into the INSERT and the store holds L4 health
    # facts in the clear.
    ("store/writing.py",
     "    body = {k: v for k, v in values.items() if k not in sealed_here}",
     "    body = dict(values)",
     "the clear column does not survive the seam", "tests/test_sealing_plan.py"),
    # `if not sealed_here:` -> `if True:`, not a `return` moved above it: the
    # moved return leaves the next line indented under an empty `if` and the
    # module stops importing, which is a crash rather than a guard firing. The
    # harness reported NO NAMED FAILURE and was right to.
    ("store/writing.py", "    if not sealed_here:\n        return dict(values)",
     "    if True:\n        return dict(values)",
     "a sealed-class table routes through the seam at all",
     "tests/test_sealing_plan.py"),
    ("store/writing.py", "        if lane_key is None:", "        if False:",
     "a payload is not sealed under no key", "tests/test_sealing_plan.py"),
    ("store/writing.py",
     "        if lane_at is not None and str(lane_at) != lane_key.lane_id:",
     "        if False:",
     "one lane, one key, at the seam", "tests/test_sealing_plan.py"),
    ("store/writing.py",
     "            if spelled in values:\n                raise EnvelopeColumnRefused(",
     "            if False:\n                raise EnvelopeColumnRefused(",
     "an envelope column is not a caller's to write",
     "tests/test_sealing_plan.py"),
    ("store/writing.py", "        if payload is None:\n            raise PayloadMissing(",
     "        if False:\n            raise PayloadMissing(",
     "a lane_entry with no payload is refused", "tests/test_sealing_plan.py"),
    ("records/serving.py",
     '        return None, f"the {what} source failed: {exc!r}"',
     "        return (), None",
     "an entitlement source that errored is not a principal with no edge",
     "tests/test_rule13_acceptance.py"),
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
    ("docs/ARCHITECTURE.md", "VERIFIED-COUNT: 41 of 41", "VERIFIED-COUNT: 42 of 42",
     "§14's header figure is enforced", "tests/test_component_map.py"),
    # The join forwards every argument `serve()` takes. Each of the next two
    # reverts one to the value it effectively had when `dispatch()` did not
    # accept it at all — which is how §18 item 12 came to be unreachable
    # through the only path that renders, gates and logs.
    ("records/dispatch.py", "threshold=threshold, widenings=widenings, grants=grants)",
     "threshold=None, widenings=(), grants=grants)",
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
    # Rule 13, watched by tests/test_rule13_acceptance.py. Every replacement
    # below is the *naive* implementation — the one a hurried author writes,
    # where a source that could not be reached returns the same value as a
    # source that answered "nothing". None of them breaks an import or a parse,
    # so a nonzero exit here is a named failure rather than a crash.
    ("records/sending.py",
     'return SendList(Standing.UNKNOWN, (), f"restriction source failed: {exc!r}")',
     'return SendList(Standing.DERIVED, (), f"restriction source failed: {exc!r}")',
     "a failed restriction source is unknown", "tests/test_rule13_acceptance.py"),
    ("records/serving.py",
     'return Serving(Outcome.UNKNOWN, None, None,\n'
     '                       "field carries no classification; refusing rather than guessing")',
     'return Serving(Outcome.PAYLOAD, fld.payload, None,\n'
     '                       "field carries no classification; refusing rather than guessing")',
     "an unclassified field is not served", "tests/test_rule13_acceptance.py"),
    ("tools/conform.py",
     '        return Check("standalone-suites", what, State.UNKNOWN,\n'
     '                     "no test files found; nothing was checked")',
     '        return Check("standalone-suites", what, State.PASS,\n'
     '                     "no test files found; nothing was checked")',
     "a scan of no suites is not a pass", "tests/test_rule13_acceptance.py"),
    ("voice.py", "    if not _COMPILED:", "    if False:",
     "an unloaded rubric is unavailable", "tests/test_rule13_acceptance.py"),
    ("tools/sockets.py",
     '    if "listeners" not in data:\n        return None',
     "    if False:\n        return None",
     "a manifest declaring nothing declared nothing", "tests/test_rule13_acceptance.py"),
    ("tools/purity.py",
     "if t.reach in (Reach.EGRESS, Reach.SPAWN, Reach.UNPARSEABLE))",
     "if t.reach in (Reach.EGRESS, Reach.SPAWN))",
     "an unreadable file is not clean", "tests/test_rule13_acceptance.py"),
    # The schema, mutated as an artifact — the same shape as the
    # ARCHITECTURE.md row above, and for the same reason. tests/test_lane_model.py
    # is a checker over SQL text, so ablating *it* and asking it to notice would
    # be the circular case; the mutation belongs on the file it watches.
    #
    # Every replacement leaves the DDL valid SQL that a reviewer would wave
    # through. That is the point: each one is a softening that looks reasonable
    # in isolation, which is the failure mode the guard exists for.
    ("migrations/001_lanes.sql",
     "        CHECK (from_lane_id <> to_lane_id),",
     "        CHECK (from_lane_id IS NOT NULL),",
     "W-3: an envelope names two different lanes", "tests/test_lane_model.py"),
    ("migrations/001_lanes.sql",
     "    to_lane_id    uuid        NOT NULL REFERENCES lane(lane_id),",
     "    to_lane_id    uuid        REFERENCES lane(lane_id),",
     "W-3: an envelope's second lane is not optional", "tests/test_lane_model.py"),
    ("migrations/001_lanes.sql",
     "    CONSTRAINT self_widening_max_rung CHECK (max_rung IN ('L4')),",
     "    CONSTRAINT self_widening_max_rung CHECK (max_rung IN ('L4', 'L5')),",
     "the ladder: a widening cannot reach L5", "tests/test_lane_model.py"),
    ("migrations/001_lanes.sql",
     "        CHECK (signed_by <> subject_id),",
     "        CHECK (signed_by IS NOT NULL),",
     "W-4: the widening's signer is not its subject", "tests/test_lane_model.py"),
    ("migrations/001_lanes.sql",
     "        CHECK (lower(btrim(category)) NOT IN ('*', 'all', 'any', 'every')),",
     "        CHECK (btrim(category) IS NOT NULL),",
     "W-2: a widening names one matter", "tests/test_lane_model.py"),
    # AFTER rather than BEFORE: the trigger still exists, still fires, and no
    # longer stops the row. A grep for the trigger's name finds it either way.
    ("migrations/001_lanes.sql",
     "CREATE TRIGGER self_widening_guardian_signed\n    BEFORE INSERT OR UPDATE ON self_widening",
     "CREATE TRIGGER self_widening_guardian_signed\n    AFTER INSERT OR UPDATE ON self_widening",
     "W-5: the widening's signature is checked before the write",
     "tests/test_lane_model.py"),
    ("migrations/001_lanes.sql",
     "CREATE TRIGGER edge_self_holder_is_subject\n    BEFORE INSERT OR UPDATE ON edge",
     "CREATE TRIGGER edge_self_holder_is_subject\n    AFTER INSERT OR UPDATE ON edge",
     "a forged self edge is refused at the write", "tests/test_lane_model.py"),
    ("migrations/001_lanes.sql",
     "    ('self_widening','max_rung','INTERNAL','L2'),\n", "",
     "a new column arrives unclassified", "tests/test_lane_model.py"),
    # The two maintainer decisions of 2026-07-31, each held by a mutation on
    # the code that implements it rather than on the test that watches it.
    ("records/disclosure.py",
     "        index = self._index()\n        if lane_id not in index:",
     "        index = self._index()\n        if False:",
     "an unknown lane is refused, not answered empty (item 16)",
     "tests/test_rule13_acceptance.py"),
    ("records/receipts.py",
     "        except InvalidSignature:\n            return False\n        return True",
     "        except InvalidSignature:\n            return True\n        return True",
     "a bad signature does not attribute (item 15)", "tests/test_receipts.py"),
    ("records/receipts.py",
     "        if self.private_seed is None:\n            raise NoSigner(",
     "        if self.private_seed is None and False:\n            raise NoSigner(",
     "a public-key-only signer cannot mint (item 15)", "tests/test_receipts.py"),
    # presentation/ — the middle §18 item 4 landed. Rule 14 is enforced by the
    # type in records/rungs.py; here it is enforced by the *badge*, which is
    # the last place a rung can lose its prefix before a human reads it.
    ("presentation/scales.py", "if isinstance(key, (bool, int, float)):", "if False:",
     "a bare integer is refused by type", "tests/test_presentation.py"),
    ("presentation/scales.py", 'return f"{self.prefix} {self.word or UNNAMED}"',
     "return self.word or UNNAMED",
     "a badge carries its prefix", "tests/test_presentation.py"),
    ("presentation/scales.py", '("T0", "Exiled"), ("T1", None), ("T2", None), ("T3", None), ("T4", "Elder"),',
     '("T0", "Exiled"), ("T1", "Rookie"), ("T2", "Steady"), ("T3", "Veteran"), ("T4", "Elder"),',
     "an unverified rung name is not rendered", "tests/test_presentation.py"),
    ("presentation/scales.py", "if not _more_restricted(Rung[b], Rung[a]):", "if False:",
     "drift sees a reordered ladder", "tests/test_presentation.py"),
    ("presentation/scales.py", "if set(p_here) != set(_P_ORDER):", "if False:",
     "drift sees a missing provenance row", "tests/test_presentation.py"),
    ("presentation/scales.py", 'if lv.token != f"caution_{lv.weight}":', "if False:",
     "drift sees a token that outranks its weight", "tests/test_presentation.py"),
    ("presentation/scales.py",
     "        rows.append(Level(Scale.TRUST, prefix, word,\n"
     "                          f\"caution_{len(_T_ORDER) - 1 - i}\", len(_T_ORDER) - 1 - i))",
     "        rows.append(Level(Scale.TRUST, prefix, word, f\"caution_{i}\", i))",
     "the trust ladder renders opposite", "tests/test_presentation.py"),
    ("presentation/tokens.py", "if not la > lb:", "if False:",
     "a flattened luminance ladder", "tests/test_presentation.py"),
    ("presentation/tokens.py", 'if raw[0] in "[{&*|>":', "if False:",
     "an unimplemented YAML construct", "tests/test_presentation.py"),
    ("presentation/tokens.py", '            if key in block:', "            if False:",
     "a duplicate token definition", "tests/test_presentation.py"),
    ("presentation/tokens.py", "        if missing:", "        if False:",
     "a token missing a channel", "tests/test_presentation.py"),
    ("presentation/tokens.py", "        if name in tokens:", "        if False:",
     "an alias defined as a token", "tests/test_presentation.py"),
    ("presentation/tokens.py", '        if "\\t" in line:', "        if False:",
     "a tab in the palette", "tests/test_presentation.py"),
    ("presentation/render.py", "        if name not in row:", "        if False:",
     "an unknown template variable", "tests/test_presentation.py"),
    ("presentation/render.py", "        if _OPEN.search(body):", "        if False:",
     "a nested template section", "tests/test_presentation.py"),
    ("presentation/ir.py",
     "        if self.shown in (Shown.SERVED, Shown.DERIVED) and not self.value:",
     "        if False:",
     "a served cell with nothing to show", "tests/test_presentation.py"),
    ("presentation/ir.py", "        if self.shown is Shown.UNKNOWN and self.value != UNKNOWN_TEXT:",
     "        if False:", "absence renders as the word unknown", "tests/test_presentation.py"),
    ("presentation/ir.py", "        if serving.value is not None:", "        if False:",
     "a refusal carrying its payload", "tests/test_presentation.py"),
    ("presentation/ir.py", "        if serving.value is None:", "        if False:",
     "a served decision with no value", "tests/test_presentation.py"),
    # surfaces/ — the parity claim, which is the one guard no off-the-shelf
    # linter makes (scout-21 §5).
    ("presentation/parity.py", "            if text not in plain:", "            if False:",
     "a prefix missing from a rendering", "tests/test_surfaces.py"),
    ("presentation/parity.py", "        missing = sorted({t for t in want if t not in plain})",
     "        missing = []",
     "the monochrome backend is singled out", "tests/test_surfaces.py"),
    ("presentation/parity.py", "    if not renderings:", "    if False:",
     "a parity check of nothing", "tests/test_surfaces.py"),
    ("presentation/parity.py", "    for prefix in unknown:", "    for prefix in ():",
     "a badge on no ladder", "tests/test_surfaces.py"),
    ("surfaces/tui/render.py",
     'return f"\\x1b[38;5;{palette.resolve(seg.token).xterm256}m{seg.text}{_RESET}"',
     'return f"\\x1b[38;5;{palette.resolve(seg.token).xterm256}m'
     '{seg.text.replace(seg.token[-1], \'\')}{_RESET}"',
     "the TUI adds colour and nothing else", "tests/test_surfaces.py"),
    # Mutating the shared `document()` is NOT this guard: it moves both halves
    # and the two stay equal, which is what the first version of this row did
    # and why it read SURVIVES. The failure mode is the paper path drifting
    # ALONE — the prior art's own `// TODO: Migrate older prints to print
    # theme` — so the mutation belongs in the print door.
    ("surfaces/print/render.py",
     '    return document(view, stylesheet=STYLESHEET, mode="print")',
     '    return document(view, stylesheet=STYLESHEET, mode="print").replace(\n'
     '        \'<dd class="badges">\', \'<dd class="badges" hidden>\')',
     "the paper and the screen share a body", "tests/test_surfaces.py"),
    # tools/manifest.py — the declaration, against the tree.
    ("tools/manifest.py", "        if name not in declared:", "        if False:",
     "a door on disk nobody declared", "tests/test_manifest.py"),
    ("tools/manifest.py", "        if name not in present:", "        if False:",
     "a declared door with no directory", "tests/test_manifest.py"),
    ("tools/manifest.py", "        if any(shape in name.lower() for shape in CLOUD_SHAPED):",
     "        if False:", "a cloud permission", "tests/test_manifest.py"),
    ("tools/manifest.py", "        elif name not in ALLOWED_PERMISSIONS:", "        elif False:",
     "a permission nobody recognises", "tests/test_manifest.py"),
    ("tools/manifest.py", 'if provider != "local":', "if False:",
     "a non-local inference provider", "tests/test_manifest.py"),
    ("tools/manifest.py", 'if inference.get("cloud_fallback") is not False:', "if False:",
     "a fallback not declared false", "tests/test_manifest.py"),
    ("tools/manifest.py", "        if key not in REQUIRED_KEYS:", "        if False:",
     "a typo'd manifest key", "tests/test_manifest.py"),
    ("tools/manifest.py", "        if key not in data:", "        if False:",
     "a missing manifest key", "tests/test_manifest.py"),
    ("tools/manifest.py", "    if not files:", "    if False:",
     "a scan of nothing is not a pass", "tests/test_manifest.py"),
    ("tools/manifest.py", "        return not self.present or self.scanned == 0",
     "        return False",
     "the vacuous case is not clean", "tests/test_manifest.py"),
    ("tools/manifest.py", "    return tuple(p for p in _all_python(base) if _excused(p.relative_to(base)) is None)",
     "    return tuple(p for p in _all_python(base) if 'presentation' not in p.parts)",
     "the scan covers the whole tree", "tests/test_manifest.py"),
    # tools/registry.py — the middle between the two implementations of the
    # class-to-L mapping. Every mutation below is a fail-open: each makes the
    # reconciliation report agreement it did not find, which is the only
    # direction that matters for a check whose failure mode is a rung quietly
    # dropping. The elevation rows are the delicate half — a middle that
    # permits an elevation and a middle that permits anything upward look the
    # same against a seed that has not drifted yet.
    ("tools/registry.py", "    if seeded == derived:", "    if True:",
     "the seeded rung is the derived one", "tests/test_registry.py"),
    ("tools/registry.py", "    if not outranks(seeded_rung, got.rung):", "    if False:",
     "only an elevation may differ from the class", "tests/test_registry.py"),
    ("tools/registry.py", "    decided = ELEVATIONS.get((table, column))",
     "    decided = Elevation(seeded_rung, Route.CLAUSE, 'assumed')",
     "an elevation cites a rule somebody recorded", "tests/test_registry.py"),
    ("tools/registry.py",
     "        if got.rung is None or str(got.rung) != documented[data_class]:",
     "        if False:",
     "classify.py and SENSITIVITY.md derive the same rung", "tests/test_registry.py"),
    ("tools/registry.py", "    if not seed or not declared or not documented:",
     "    if False:",
     "a registry nobody could read is not clean", "tests/test_registry.py"),
    ("tools/registry.py",
     "    for state in (Agreement.DISAGREES, Agreement.UNCLASSIFIED, Agreement.STALE):",
     "    for state in (Agreement.DISAGREES,):",
     "an unclassified column fails the build", "tests/test_registry.py"),
    ("tools/registry.py", "        if key[0] in present:", "        if True:",
     "a stale elevation is scoped to the schema read", "tests/test_registry.py"),
    # tools/conform.py — the row, not the reconciliation. A middle that works
    # and a row that reports it as PASS anyway is the state §17 measured:
    # the gate exists, the ledger says something else.
    ("tools/conform.py",
     "    undecided = r.of(Agreement.UNDECIDED)\n    if undecided:",
     "    undecided = r.of(Agreement.UNDECIDED)\n    if False:",
     "an undecided field is not a passing row", "tests/test_registry.py"),
    # records/atrest.py — §9 foundation 3. Every key these mutations touch is
    # generated in memory by the suite; nothing here reads or writes key
    # material, and refusal 2 keeps it that way.
    #
    # The hierarchy.
    ("records/atrest.py", "    if isinstance(lane_key, MasterKey):", "    if False:",
     "the master key never seals a record", "tests/test_atrest.py"),
    ("records/atrest.py", "    if name.lower() in _WILDCARDS:", "    if False:",
     "a section is not a lane (W-1)", "tests/test_atrest.py"),
    ("records/atrest.py", "    if keyring.state_of(kid) is not KeyState.UNKNOWN:",
     "    if False:", "one key id, one lane", "tests/test_atrest.py"),
    ("records/atrest.py", '    if _SEP in name or "\\x00" in name:', "    if False:",
     "an id cannot forge the binding", "tests/test_atrest.py"),
    ("records/atrest.py", "    if not isinstance(payload, (bytes, bytearray)):",
     "    if False:", "the core does not guess an encoding", "tests/test_atrest.py"),
    # Key material is L5 and a traceback is a rendering.
    ("records/atrest.py",
     '        return f"MasterKey(key_id={self.key_id!r}, material=<withheld>)"',
     '        return f"MasterKey(key_id={self.key_id!r}, material={self.material!r})"',
     "a master key does not render", "tests/test_atrest.py"),
    ("records/atrest.py",
     '                f"scheme={self.scheme!r}, material=<withheld>)")',
     '                f"scheme={self.scheme!r}, material={self.material!r})")',
     "a lane key does not render", "tests/test_atrest.py"),
    ("records/atrest.py",
     '                f"plaintext={\'<withheld>\' if self.plaintext is not None else None})")',
     '                f"plaintext={self.plaintext!r})")',
     "an opened payload does not render", "tests/test_atrest.py"),
    # The three unreadable states. Each mutation collapses one into another,
    # which is the failure rule 13 names: an absence rendered as a result.
    ("records/atrest.py", "        return (Agreement.KEY_DESTROYED,",
     "        return (Agreement.KEY_UNKNOWN,",
     "destroyed is not unknown", "tests/test_atrest.py"),
    ("records/atrest.py", "            return KeyState.DESTROYED",
     "            return KeyState.UNKNOWN",
     "three key states, not two", "tests/test_atrest.py"),
    ("records/atrest.py", "    if header != expected:", "    if False:",
     "a relabelled envelope is misbound", "tests/test_atrest.py"),
    # Rule 12's key-id <-> scheme middle, and the path that routes through it.
    ("records/atrest.py", "    if w.scheme != sealed.scheme:", "    if False:",
     "the key-id/scheme pair is compared", "tests/test_atrest.py"),
    ("records/atrest.py", "    if w.lane_id != sealed.lane_id:", "    if False:",
     "a key id pointed at another lane", "tests/test_atrest.py"),
    ("records/atrest.py", "    agreement, why = reconcile(sealed, keyring)",
     '    agreement, why = (Agreement.AGREES, "")',
     "unseal routes through the middle", "tests/test_atrest.py"),
    # Rotation and revocation.
    ("records/atrest.py", "    if wrapping.under_master != master.key_id:",
     "    if False:", "a rotation that has not landed", "tests/test_atrest.py"),
    ("records/atrest.py", "    if was.key_id == now.key_id:", "    if False:",
     "a rotation needs a new name", "tests/test_atrest.py"),
    ("records/atrest.py", "    if rotated == 0:", "    if False:",
     "a rewrap rotating nothing is a silent no-op", "tests/test_atrest.py"),
    ("records/atrest.py", "    if not keyring.keys_for(lane_id):", "    if False:",
     "rotation does not mint a first key", "tests/test_atrest.py"),
    ("records/atrest.py", "    if from_key.lane_id != to_key.lane_id:", "    if False:",
     "no reseal across lanes", "tests/test_atrest.py"),
    ("records/atrest.py", "        if s.key_id != from_key.key_id:", "        if False:",
     "a reseal skips no payload", "tests/test_atrest.py"),
    # Erasure, and the record that outlives the key.
    ("records/atrest.py", "    if not doomed:", "    if False:",
     "an erasure against nothing", "tests/test_atrest.py"),
    ("records/atrest.py",
     "    kept = tuple(w for w in keyring.wrappings if w.lane_id != lane)",
     "    kept = keyring.wrappings",
     "an erasure erases", "tests/test_atrest.py"),
    ("records/atrest.py", '    if not (reason or "").strip():', "    if False:",
     "an erasure carries a reason", "tests/test_atrest.py"),
    ("records/atrest.py", "    if name.lower() in _NOT_A_PERSON:", "    if False:",
     "a role does not erase or escrow", "tests/test_atrest.py"),
    # Rule 12's erasure <-> chain middle. Each branch of composes().
    ("records/atrest.py", "    if not chain_ok:", "    if False:",
     "an erasure must not break the chain", "tests/test_atrest.py"),
    ("records/atrest.py", "    if chain_ok and anchor is not None:", "    if False:",
     "truncation caught by the anchor", "tests/test_atrest.py"),
    ("records/atrest.py",
     "    if still:\n        return Erasability(\n            Composition.ERASURE_INCOMPLETE,\n"
     '            f"{len(still)} payload(s) for {lane_id} still readable after the "',
     "    if False:\n        return Erasability(\n            Composition.ERASURE_INCOMPLETE,\n"
     '            f"{len(still)} payload(s) for {lane_id} still readable after the "',
     "a readable payload after an erasure", "tests/test_atrest.py"),
    ("records/atrest.py",
     "    if held:\n        return Erasability(\n            Composition.ERASURE_INCOMPLETE,\n"
     '            f"an erasure is recorded for {lane_id} and {len(held)} wrapping(s) "',
     "    if False:\n        return Erasability(\n            Composition.ERASURE_INCOMPLETE,\n"
     '            f"an erasure is recorded for {lane_id} and {len(held)} wrapping(s) "',
     "a partial erasure is not a whole one", "tests/test_atrest.py"),
    ("records/atrest.py", "    if erasure is None:\n        if held:",
     "    if erasure is None:\n        if False:",
     "not-erased is not unrecorded", "tests/test_atrest.py"),
    # Escrow, surfaced rather than solved.
    ("records/atrest.py", "        return (EscrowState.ABSENT,",
     "        return (EscrowState.RECORDED,",
     "an absent escrow is not a recorded one", "tests/test_atrest.py"),
    ("records/atrest.py", "    if d.rehearsed_at is None:", "    if False:",
     "an unrehearsed escrow is not escrow", "tests/test_atrest.py"),
    ("records/atrest.py", "    if at >= d.next_rehearsal_due:", "    if False:",
     "an overdue drill is stale", "tests/test_atrest.py"),
    ("records/atrest.py", "        if self.next_rehearsal_due <= self.decided_at:",
     "        if False:", "the next drill is declared at issuance",
     "tests/test_atrest.py"),
    ("records/atrest.py",
     '        if not self.holders or not all((h or "").strip() for h in self.holders):',
     "        if False:", "an escrow disposition names a holder",
     "tests/test_atrest.py"),
    ("records/atrest.py", "    if current is None:", "    if False:",
     "no rehearsal without a disposition", "tests/test_atrest.py"),
    ("records/atrest.py", "                 for m in keyring.masters())",
     "                 for m in ())",
     "the escrow survey is derived", "tests/test_atrest.py"),
    # The tie-break `max(..., key=...)` does not have: a rehearsal recorded on
    # the day of the disposition it rehearses loses to the disposition, and the
    # drill reads as never having happened. Found by the test, not by review.
    ("records/atrest.py",
     "    return max(((when, i, obj) for i, (when, obj) in enumerate(dated)))[2]",
     "    return max(dated, key=lambda p: p[0])[1]",
     "a same-day rehearsal is the later record", "tests/test_atrest.py"),
    # The conformance row. Since S-3 the honest answer is UNKNOWN — a policy is
    # recorded (3-of-5, docs/ESCROW.md) and has never been rehearsed — and BOTH
    # walls are mutated, because the row's whole value is that it is neither of
    # the two comfortable answers. It read ABSENT until 2026-07-31 and the
    # mutation above it moved with the row rather than being deleted.
    ("tools/conform.py",
     '        return Check(\n            "key-escrow", what, State.UNKNOWN,',
     '        return Check(\n            "key-escrow", what, State.PASS,',
     "an unrehearsed escrow row is not a pass", "tests/test_atrest.py"),
    ("tools/conform.py",
     '    if not facts.exists or not facts.recorded:\n        return Check("key-escrow", what, State.ABSENT,',
     '    if False:\n        return Check("key-escrow", what, State.ABSENT,',
     "a policy nobody recorded is absent, not unknown", "tests/test_conform.py"),
    ("tools/conform.py", "    if not facts.rehearsed:", "    if True:",
     "a rehearsed escrow row is a pass", "tests/test_conform.py"),
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
    ("tools/audit.py", "    if not seam and not durable:", "    if not seam:",
     "R16: stored unsealed is not the same as unstored", "tests/test_audit.py"),
    ("tools/audit.py", "    if not disposed:", "    if False:",
     "R16: sealed without escrow is a finding", "tests/test_audit.py"),
    ("tools/audit.py", "    if not facts.rehearsed:\n        return False,",
     "    if False:\n        return False,",
     "R16: an unrehearsed plan is not escrow", "tests/test_audit.py"),
    # R16's at-rest boundary (S-3), mutated in **both** directions, because the
    # two failures point opposite ways and one mutation would only show one.
    #
    # (a) Counting the store's writes as durable regardless of who drives them
    #     makes the real tree read S1: an install-blocking finding no commit can
    #     clear, because what clears it is a key ceremony in a room. A gate
    #     nobody can turn green is a gate everybody learns to ignore.
    ("tools/audit.py",
     "    durable = ring_writes + (staged if callers else 0)",
     "    durable = ring_writes + staged",
     "an ephemeral test database is not a record at rest", "tests/test_audit.py"),
    # (b) Not counting them at all makes R16 blind to the store forever, which
    #     is the failure that matters: S-4 wires a surface to it and nothing
    #     notices.
    ("tools/audit.py",
     "    durable = ring_writes + (staged if callers else 0)",
     "    durable = ring_writes",
     "the store's writes count once something drives them",
     "tests/test_audit.py"),
    # And the detector under both: a caller scan that finds nothing makes (a)
    # and (b) indistinguishable. Since S-4 the scan is shared by `durable_callers`
    # and `narration_callers` in `_scan_callers`, so this disables the call route
    # for both — and `test_the_first_non_test_caller` still fails, because the
    # record-write caller reached by a bare call (app/handler.py) goes unseen.
    ("tools/audit.py",
     "                if name in verbs:\n                    out.append((rel, f\"calls {name}()\"))",
     "                if False:\n                    out.append((rel, f\"calls {name}()\"))",
     "a call into the store's write path is a caller", "tests/test_audit.py"),
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
    # Restores the observer effect exactly: render inside the open, so the
    # record file git is being asked about already exists when it is asked.
    # The probe suite builds its own clean repository for this, because this
    # one is dirty whenever this harness is running and would agree with the
    # defect.
    ("tools/conform.py", "            fh.write(text)",
     "            fh.write(render(checks, at))",
     "a record does not report the tree it made", "tests/test_conform.py"),
    # The artifact, not the guard. Both of these mutate the document and ask a
    # different file to notice -- the shape the §14 header-figure mutation
    # established, after the first attempt at it disabled an assertion and asked
    # the assertion to catch itself.
    # --- §9 item 8: attendance, fees, and step 2a over an aggregate --------
    #
    # records/classify.py's aggregate gate. Both new modules route their
    # cross-lane figures through it, so a hole here is a hole in two places.
    ("records/classify.py", "    if compose(*over) is NEVER_SERVED:", "    if False:",
     "counting does not declassify L5", "tests/test_classify.py"),
    ("records/classify.py", "    passed = cohort >= floor", "    passed = True",
     "the suppression floor applies", "tests/test_classify.py"),
    ("records/classify.py", "    if floor < 2:", "    if False:",
     "a floor of nothing is not a floor", "tests/test_classify.py"),
    # And the two callers, ablated at their own call sites: a gate both modules
    # route through can be correct while a caller passes it the wrong rung.
    ("records/attendance.py",
     '    c = aggregate("headcount", over=(Rung.L3,), cohort=cohort, floor=floor)',
     '    c = aggregate("headcount", over=(Rung.L2,), cohort=cohort, floor=floor)',
     "a headcount inherits the mark's rung", "tests/test_attendance.py"),
    ("records/fees.py",
     '    c = aggregate("program_total", over=(Rung.L4,), cohort=cohort, floor=floor)',
     '    c = aggregate("program_total", over=(Rung.L2,), cohort=cohort, floor=floor)',
     "a total inherits FINANCIAL's rung", "tests/test_fees.py"),
    # A balance is L4 because money is one of step 3's four categories. Drop
    # the category and it lands at L3 -- served in full to anyone holding an
    # edge, with no purpose declared, which is a balance on a chaperone's phone.
    ("records/fees.py",
     'BALANCE = Descriptor("balance", identifies_a_person=True, category="money")',
     'BALANCE = Descriptor("balance", identifies_a_person=True)',
     "a balance carries money's category", "tests/test_fees.py"),
    ("records/fees.py", "        if not self.servable:", "        if False:",
     "an unservable total yields no number", "tests/test_fees.py"),
    # records/attendance.py — refusal 7's seam. Both isinstance checks, because
    # they are two doors into one room and closing one is the shape of guard
    # this tree keeps finding half-ablated.
    ("records/attendance.py", "    if not isinstance(referent, Referent):",
     "    if False:", "a record cannot become a signal", "tests/test_attendance.py"),
    ("records/attendance.py", "    if not isinstance(sig, Signal):", "    if False:",
     "only a signal reaches the carrier", "tests/test_attendance.py"),
    # W-3 and rule 13 over the roll.
    ("records/attendance.py", "        if subject_id in seen:", "        if False:",
     "two marks for one student are not collapsed", "tests/test_attendance.py"),
    ("records/attendance.py", '        if not (lane_id or "").strip():',
     "        if False:", "a mark outside a lane (W-1)", "tests/test_attendance.py"),
    ("records/attendance.py", '        if not (self.season or "").strip():',
     "        if False:", "a referent carries a season (§10)", "tests/test_attendance.py"),
    ("records/attendance.py", "    if requests is None:", "    if False:",
     "an unconsulted request source is unknown", "tests/test_attendance.py"),
    # Restores revocation-by-rewrite exactly: the correction becomes the record
    # and the original mark stops having existed (refusal 3).
    ("records/attendance.py", "    closed = replace(entry, invalid_at=at, corrected_by=by)",
     "    closed = later", "a correction supersedes, never overwrites",
     "tests/test_attendance.py"),
    # records/fees.py — the PAN refusal, in both directions. A check that
    # matches everything and a check that matches nothing are both broken, and
    # only one of them is noticed by the test that says the guard fires.
    ("records/fees.py", "    return total % 10 == 0", "    return False",
     "Luhn catches a card number", "tests/test_fees.py"),
    ("records/fees.py", "    return total % 10 == 0", "    return True",
     "Luhn does not fail an invoice number", "tests/test_fees.py"),
    # The partial guard somebody would plausibly write: close the token field
    # and leave the memo line, which is where a PAN would actually go.
    ("records/fees.py", "    for f in _fields(obj):",
     '    for f in [x for x in _fields(obj) if x.name == "token_ref"]:',
     "every string field is scanned, not just the token", "tests/test_fees.py"),
    ("records/fees.py",
     "        if self.tender is Tender.CARD_TOKEN and not (self.token_ref or \"\").strip():",
     "        if False:", "a card payment carries a token", "tests/test_fees.py"),
    ("records/fees.py", "    if isinstance(value, bool) or not isinstance(value, int):",
     "    if False:", "money is integer minor units", "tests/test_fees.py"),
    # The design error this module was written twice to avoid: no membership
    # falling back to the standard band, which makes the absence of a row mean
    # something. This mutation is the first draft of that line, restored.
    ("records/fees.py", "    bands = [g for g in for_activity if g.group_id in live]",
     "    bands = [g for g in for_activity if g.group_id in live] or for_activity",
     "no live band is unknown, not the standard fee", "tests/test_fees.py"),
    ("records/fees.py", "    if len(bands) > 1:", "    if False:",
     "two live bands escalate rather than minimise", "tests/test_fees.py"),
    # Rule 13 where it bills a family.
    ("records/fees.py",
     "        if self.state is not Source.DERIVED or self._cents is None:",
     "        if False:", "an unknown balance is not zero", "tests/test_fees.py"),
    ("records/fees.py", "        if lane_id is None:", "        if False:",
     "an empty result from an unnamed lane is unknown", "tests/test_fees.py"),
    # Revocation by rewriting the amount — the money-side spelling of refusal 3.
    ("records/fees.py",
     "    return replace(payment, invalid_at=at, reversed_by=by, reversal_reason=why)",
     "    return replace(payment, cents=0, reversed_by=by, reversal_reason=why)",
     "a reversal dates, never rewrites", "tests/test_fees.py"),
    # The openSIS widget, and the two rankings.
    ("records/fees.py", '    raise NotDisclosable(\n        "no roster or search surface',
     '    return (\n        "no roster or search surface',
     "no surface filters students by money", "tests/test_fees.py"),
    ("records/fees.py", '    refuse_to_rank("a need ranking for aid", applicants)',
     "    return tuple(sorted(applicants))",
     "aid is not ranked between students", "tests/test_fees.py"),
    ("records/fees.py", '    refuse_to_rank("a payment-plan priority", students)',
     "    return tuple(sorted(students))",
     "a payment plan is not a priority", "tests/test_fees.py"),
    ("docs/SECURITY-AUDIT.md",
     "| **FINDING** | `S2` | The sealing seam exists",
     "| **PASS** | `S2` | The sealing seam exists",
     "the recorded R16 verdict is reconciled", "tests/test_audit.py"),
    ("docs/SECURITY-AUDIT.md",
     "| `TM-DEPS-01` | R14 | `S3` | closed 2026-07-31 |",
     "| `TM-DEPS-01` | R14 | `S1` | open |",
     "an open S1 in the document fails conformance", "tests/test_conform.py"),
    # venue/ — §9 foundation 6. The package has no lane and no person in it, so
    # every guard here is either rule 13 (absence is not a value), rule 14 (a
    # rung travels with its prefix), or the one boundary that keeps it that way.
    #
    # The first mutation is the one worth reading. It does not disable a check;
    # it supplies a *default*, which is how this failure actually arrives —
    # nobody writes `if False:` over rule 13, they write a sensible-looking
    # fallback for the case where there is nothing to show.
    ("venue/readings.py",
     "        return self.reading.text if self.reading is not None else UNKNOWN_TEXT",
     '        return self.reading.text if self.reading is not None else "0 dBA"',
     "rule 13: an unmeasured seat is not quiet", "tests/test_venue.py"),
    ("venue/readings.py", "        if self.reading is not None and self.why:",
     "        if False:",
     "an answer is not both known and unknown", "tests/test_venue.py"),
    ("venue/readings.py", "        if self.reading is None and not self.why:",
     "        if False:",
     "an unknown answer says why", "tests/test_venue.py"),
    # Composition, and the two ways it goes wrong. Inverting the comparison
    # makes a profile report its *strongest* reading, which is the number a
    # reader most wants to be told and the one they are least entitled to.
    ("venue/readings.py",
     "        if outranks(worst, rung):    # `worst` is the stronger, so `rung` is worse",
     "        if outranks(rung, worst):",
     "§15: provenance composes by the weakest input", "tests/test_venue.py"),
    ("venue/readings.py",
     '        raise ValueError(\n'
     '            "the provenance of no readings — an unmeasured venue has no rung, "\n'
     '            "and the strongest one is the worst possible default (rule 13)")',
     "        return P_MEASURED",
     "the provenance of nothing is not P1", "tests/test_venue.py"),
    ("venue/readings.py", "        if self.provenance not in _LADDER:", "        if False:",
     "rule 14: a rung is on the ladder or it is not a rung", "tests/test_venue.py"),
    ("venue/readings.py",
     "        if self.provenance in NEEDS_A_SOURCE and not self.source.strip():",
     "        if False:",
     "§15: a cited rung names something checkable", "tests/test_venue.py"),
    # The boundary. Without it a `Mark` is a duck-typed seat: it has `.seat`,
    # it stringifies, and nothing else in the package would notice.
    ("venue/readings.py", "        if hasattr(seat, attr):", "        if False:",
     "a seat is a place and never a person", "tests/test_venue.py"),
    ("venue/readings.py",
     "        if not isinstance(self.value, (int, float)) or not math.isfinite(self.value):",
     "        if False:",
     "a reading of nothing is not a reading", "tests/test_venue.py"),
    ("venue/readings.py", "            if key in seen:", "            if False:",
     "one seat, one quantity, one claim", "tests/test_venue.py"),
    ("venue/readings.py", "    if not text:", "    if False:",
     "a reading with no place is refused", "tests/test_venue.py"),
    # The named middle. This is the mutation the whole of `venue/sourcing.py`
    # exists for: matching `measured` to `P1` on the strength of the shared word
    # is not a typo, it is the reading a careful person arrives at.
    ("venue/sourcing.py", '    "measured": P_CITED,', '    "measured": P_MEASURED,',
     "rule 12: `measured` there is P2 Cited here", "tests/test_venue.py"),
    ("venue/sourcing.py", "    if rung in _UNREACHABLE:", "    if False:",
     "an unreachable rung is refused, not rounded", "tests/test_venue.py"),
    ("venue/sourcing.py",
     '        raise ValueError(\n'
     '            f"{state!r} is not one of the three states {THREE_STATE}; a rung "\n'
     '            "cannot be derived from a vocabulary nothing here knows")',
     "        return P_ASSUMED",
     "an unknown vocabulary is unknown, not assumed", "tests/test_venue.py"),
    ("venue/card.py", "    if not seats:", "    if False:",
     "a card over no seats is not a clean venue", "tests/test_venue.py"),
    ("venue/card.py", "    if not wanted:", "    if False:",
     "a card over no quantities reports nothing", "tests/test_venue.py"),
    ("venue/card.py", "    if not answer.known:", "    if False:",
     "an unmeasured quantity renders as unknown", "tests/test_venue.py"),

    # ---------------------------------------------------------------- §9 item 9
    # records/commentary.py — adjudication. Three families: the primitive's
    # attribution and provenance, refusal 4's unrepresentable score, and the
    # guest session whose observed half must stay a filter over the chain.
    #
    # The primitive.
    ("records/commentary.py",
     '        if not (self.body or "").strip():', "        if False:",
     "an empty remark is absence", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        if not isinstance(self.capture, Capture):", "        if False:",
     "a capture mode is a Capture", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        if self.capture is Capture.MACHINE:\n            if name:",
     "        if self.capture is Capture.MACHINE:\n            if False:",
     "rule 10: a transcript is not the judge's", "tests/test_commentary.py"),
    ("records/commentary.py", "        elif not name:", "        elif False:",
     "a person's remark names the person", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        if p_outranks(_PROVENANCE_OF[self.capture], self.anchor.provenance):",
     "        if False:",
     "words cannot outrank their tap", "tests/test_commentary.py"),
    # W-1 / W-3. The fan-out is the only multi-anchor constructor, so its two
    # guards are what keep it from becoming a roster row with a timestamp.
    ("records/commentary.py", "    if not marks:", "    if False:",
     "W-3: a fan-out over nothing", "tests/test_commentary.py"),
    ("records/commentary.py", "    if len(referents) != 1:", "    if False:",
     "W-3: one referent, shared", "tests/test_commentary.py"),
    ("records/commentary.py",
     "    if len(set(lanes)) != len(lanes):", "    if False:",
     "W-3: one lane entry each", "tests/test_commentary.py"),
    ("records/commentary.py",
     "    if remark.capture is Capture.MACHINE:\n        return draft(subject, KIND, remark.body)",
     "    if False:\n        return draft(subject, KIND, remark.body)",
     "a transcript enters authored by nobody", "tests/test_commentary.py"),
    # Refusal 4 / SA-3. The properties are the enforcement; a mutation that
    # makes one return is exactly the `getattr(..., None)` the shape refuses.
    ("records/commentary.py",
     '        refuse_standing_score("Remark.rating", self.subject_id or "this performer")',
     "        return None",
     "SA-3: a rating cannot be read", "tests/test_commentary.py"),
    ("records/commentary.py",
     '    refuse_to_rank("comparing two adjudication remarks", subjects)',
     "    return None",
     "refusal 6: two remarks do not order", "tests/test_commentary.py"),
    # The gate commentary leaves through.
    ("records/commentary.py", "    if rung is None:", "    if False:",
     "rule 13: no rung was decided", "tests/test_commentary.py"),
    ("records/commentary.py",
     "    if remark.addresses is not Addressed.LANE:\n        raise Unlaned(",
     "    if False:\n        raise Unlaned(",
     "an unlaned remark has no lane path", "tests/test_commentary.py"),
    ("records/commentary.py",
     "    if record.body != remark.body:", "    if False:",
     "a seal names what was sealed", "tests/test_commentary.py"),
    ("records/commentary.py", "    if not record.servable:", "    if False:",
     "§8.2: only sealed is servable", "tests/test_commentary.py"),
    ("records/commentary.py",
     '    return f"{body} [{serving.provenance or remark.provenance}]"',
     "    return body",
     "§15: provenance travels with the value", "tests/test_commentary.py"),
    # §7.2's knock.
    ("records/commentary.py",
     '        if not (self.purpose or "").strip():', "        if False:",
     "a knock declares a purpose", "tests/test_commentary.py"),
    ("records/commentary.py",
     '        if not (self.event_id or "").strip():', "        if False:",
     "a guest grant is to an event", "tests/test_commentary.py"),
    ("records/commentary.py",
     '        bad = [ln for ln in self.lanes\n'
     '               if not (ln or "").strip() or ln.strip().lower() in _WILDCARDS]',
     "        bad = []",
     "W-2: a group is not a scope", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        if len(set(self.lanes)) != len(self.lanes):", "        if False:",
     "a lane declared twice", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        if self.closed_at is not None and self.closed_at < self.declared.opened_at:",
     "        if False:",
     "a session closes after it opens", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        return self.closed_at is None or when <= self.closed_at",
     "        return True",
     "§4: the window is time-boxed", "tests/test_commentary.py"),
    ("records/commentary.py", "    if not session.within(at):", "    if False:",
     "a capture outside its session", "tests/test_commentary.py"),
    ("records/commentary.py",
     "    if remark.addresses is not Addressed.LANE:\n        return ledger",
     "    if False:\n        return ledger",
     "an ensemble remark writes no lane row", "tests/test_commentary.py"),
    # J6: the observed half is a filter over the chain. If it stops filtering by
    # principal, a guest is shown somebody else's reads as their own — which is
    # the failure a separate summary would have caused, arriving by the other road.
    ("records/commentary.py",
     "               if e.principal_id == session.declared.principal_id\n"
     "               and session.within(e.occurred_at)]",
     "               if session.within(e.occurred_at)]",
     "J6: observed is this guest's only", "tests/test_commentary.py"),
    ("records/commentary.py", "    if session.open:", "    if False:",
     "rule 13: an open session is unknown", "tests/test_commentary.py"),
    ("records/commentary.py", "    if undeclared:", "    if False:",
     "§7.2: undeclared lanes diverge", "tests/test_commentary.py"),
    # The transcription seam.
    ("records/commentary.py",
     "        if self.record.state is not State.DRAFT:", "        if False:",
     "a transcript arrives as a draft", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        if self.record.author_id is not None:", "        if False:",
     "a transcript is the machine's", "tests/test_commentary.py"),
    ("records/commentary.py",
     '        if not (self.by_machine or "").strip():', "        if False:",
     "a transcript names its transcriber", "tests/test_commentary.py"),
    ("records/commentary.py",
     "        raise NotImplementedError(\n"
     '            "a transcript is not attributed to the person who spoke; it is a "',
     "        return NotImplementedError(\n"
     '            "a transcript is not attributed to the person who spoke; it is a "',
     "said_by raises rather than answers", "tests/test_commentary.py"),
    # Refusal 1's tagging is this module's contribution: the guard cannot know
    # what a call touches, so a seam that mis-tags defeats it while passing.
    ("records/commentary.py",
     "    answer: Answer = through(call, classes=TRANSCRIPT_CLASSES,",
     '    answer: Answer = through(call, classes=("PUBLIC",),',
     "refusal 1: the seam tags the call", "tests/test_commentary.py"),
    ("records/commentary.py",
     "TRANSCRIPT_RUNG = compose(Rung.L3, Rung.L4)", "TRANSCRIPT_RUNG = Rung.L1",
     "the transcript rung is composed", "tests/test_commentary.py"),
    # records/aggregate.py — §9 item 10, the gated aggregate export. Every
    # mutation below is a fail-open in one of exactly three directions, because
    # those are the only three ways an aggregate leaks: it publishes a number it
    # should have withheld, it publishes a number that gives a withheld one away
    # by subtraction, or it publishes a number that looks complete over a
    # population it could not read. The third is the one naive implementations
    # ship, so it gets the decoy treatment: `lost = []` is character for
    # character what a hurried author writes.
    ("records/aggregate.py", "if n < floor.k else CellState.RELEASED",
     "if False else CellState.RELEASED",
     "small-cell suppression", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "        if not _determined(residual, bounds):\n            return state, True",
     "        if True:\n            return state, True",
     "complementary suppression runs at all", "tests/test_aggregate.py"),
    ("records/aggregate.py", "        if low >= high:", "        if False:",
     "a suppressed cell's interval collapsing to a point", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "                if s in (CellState.SUPPRESSED_SMALL, CellState.SUPPRESSED_COMPLEMENT)]",
     "                if s is CellState.SUPPRESSED_SMALL]",
     "a complement counts as a suppression", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "        if not candidates:\n            return state, False",
     "        if not candidates:\n            return state, True",
     "nothing left to suppress is unreleasable", "tests/test_aggregate.py"),
    # The decoy. `lost = []` drops the row that could not be read and returns a
    # smaller number that looks complete — rule 13 in the one place a reader
    # cannot possibly notice.
    ("records/aggregate.py",
     "    lost = [r for r in readings if r.state is Read.UNREADABLE or not r.verified_tier]",
     "    lost = []",
     "rule 13: an unread lane is not a smaller number", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "    lost = [r for r in readings if r.state is Read.UNREADABLE or not r.verified_tier]",
     "    lost = [r for r in readings if r.state is Read.UNREADABLE]",
     "I-10: an unverified input is not dropped either", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "        return not stronger_provenance(P_CITED, self.provenance)",
     "        return True", "the verified tier is P1 and P2", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "    if spoiled:\n        for key in state:",
     "    if False:\n        for key in state:",
     "an unreadable input stops every count", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "    if spoiled:\n        return tuple(out), Aggregate.INCOMPLETE",
     "    if False:\n        return tuple(out), Aggregate.INCOMPLETE",
     "an incomplete aggregate says so", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    if blind or not by_cell:", "    if not by_cell:",
     "a reading that cannot name its cell is unknown", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "            counts[key] if cell_state is CellState.RELEASED else None,",
     "            counts[key],",
     "a suppressed cell carries no number", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "        passed = cell_state is CellState.RELEASED and settled",
     "        passed = True",
     "step 2a: what passed the re-identification check", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    if not inputs:", "    if False:",
     "a derived cell with no inputs is not L2", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    if into is None:", "    if False:",
     "rule 9: an unannounced export is not issued", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    if not readings:", "    if False:",
     "an aggregate over nothing is not a table of zeros", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    if enforcement:", "    if False:",
     "no count over enforcement content", "tests/test_aggregate.py"),
    ("records/aggregate.py", "        if len(self.lanes) < 2:", "        if False:",
     "an aggregate is a many-lane read", "tests/test_aggregate.py"),
    ("records/aggregate.py", "        if self.request.audience is Audience.PUBLIC:",
     "        if False:", "a public release is refused", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    if not isinstance(gate, Gate):", "    if False:",
     "W-3: the cross-lane read needs the token", "tests/test_aggregate.py"),
    # The audience ceiling is a tripwire — nothing in the module can make it
    # fire, exactly like records/orders.py's "an ending never shortens the
    # graph". So the mutation is the forbidden act rather than the branch:
    # move an audience's ceiling below what an aggregate serves at.
    ("records/aggregate.py", "    Audience.BOOSTER: Rung.L2,", "    Audience.BOOSTER: Rung.L1,",
     "the audience ceiling is enforced", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    gate = _legitimate(request, readings, into)",
     "    gate = Gate(request, tuple(sorted({r.lane_id for r in readings})),\n"
     "                CEILING[request.audience])",
     "release() routes through the gate", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     '    for r in sorted(readings, key=lambda r: (r.lane_id, r.subject_id, r.cell or "")):',
     "    for r in sorted([x for x in readings if x.state is Read.READ],\n"
     '                    key=lambda r: (r.lane_id, r.subject_id, r.cell or "")):',
     "a lane that could not be read is announced too", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     "        outcome = _outcome(cell.state) if r.state is Read.READ else Outcome.UNKNOWN",
     "        outcome = Outcome.PAYLOAD",
     "a suppressed lane is announced as a refusal", "tests/test_aggregate.py"),
    ("records/aggregate.py", "    head = anchor_for_ledger(announced, request.at).head",
     '    head = "0" * 64',
     "the manifest is built over the announcement", "tests/test_aggregate.py"),
    ("records/aggregate.py", '        shown = "suppressed" if c.suppressed else c.state.value',
     "        shown = c.state.value",
     "which suppression applied is not attributed", "tests/test_aggregate.py"),
    # An identifier on a `CellResult`, which is the value every artifact is
    # rendered from. The retired `contributors` field held exactly this and was
    # read by nothing, so no mutation could reach it; the field is gone and the
    # act is ablated instead, through the one field a careless author would
    # actually reach for.
    #
    # **It is aimed past the artifact scan on purpose.** `why` renders only for
    # an *incomplete* cell — `_manifest`'s UNAVAILABLE GROUPS block is its only
    # appearance — so on a released table this mutation puts three lane ids in
    # the value the booster board's report is built from and leaves every
    # rendered byte unchanged. `test_no_lane_id_or_student_id_reaches_an_artifact`
    # cannot see it. That is the gap `..._reaches_a_cell_result` was added to
    # close, and this row is the evidence the gap was real.
    ("records/aggregate.py",
     "        why = reason if cell_state is not CellState.INCOMPLETE else (\n"
     "            spoiled[key].why if key in spoiled\n"
     '            else "another cell in this table has an input that could not be read")',
     "        why = (reason if cell_state is not CellState.INCOMPLETE else (\n"
     "            spoiled[key].why if key in spoiled\n"
     '            else "another cell in this table has an input that could not be read")\n'
     "            ) + f\" [lanes: {', '.join(sorted(r.lane_id for r in rows))}]\"",
     "no lane id rides into the artifact layer on a cell", "tests/test_aggregate.py"),
    ("records/aggregate.py", "        if self.k < 2:", "        if False:",
     "a threshold that cannot suppress", "tests/test_aggregate.py"),
    ("records/aggregate.py", '            if not (getattr(self, name) or "").strip():',
     "            if False:", "a threshold travels with its source",
     "tests/test_aggregate.py"),
    ("records/aggregate.py", "        if dim in NOT_A_DIMENSION:", "        if False:",
     "a cell per student", "tests/test_aggregate.py"),
    ("records/aggregate.py", '        if "," in dim or "×" in dim or " x " in dim:',
     "        if False:", "a cross-tab is refused", "tests/test_aggregate.py"),
    ("records/aggregate.py", '        if not (self.purpose or "").strip():', "        if False:",
     "an aggregate declares a purpose", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     '        if self.state is Read.UNREADABLE and not (self.why or "").strip():',
     "        if False:", "an absence says why", "tests/test_aggregate.py"),
    ("records/aggregate.py",
     '        if self.state is Read.READ and not (self.cell or "").strip():',
     "        if False:", "a reading that was read names its cell",
     "tests/test_aggregate.py"),
    ("records/aggregate.py", "        stronger_provenance(P_CITED, self.provenance)",
     "        None",
     "rule 14: a provenance is on the ladder", "tests/test_aggregate.py"),
    ("records/aggregate.py", "        if len(group) > 1:", "        if False:",
     "the differencing ledger reports an overlap", "tests/test_aggregate.py"),
    # --- console/ — the knock in enforcement mode (S-4) --------------------
    #
    # The two pure-Python guards of the director session. The cluster half — the
    # read through RLS and the predicate, the narration, the reconciled_session
    # row — is attacked in tests/test_store_knock.py, run by the schema job, for
    # the reason the store's other cluster guards are: a mutation whose suite
    # cannot run reports SURVIVES for the wrong reason.
    ("console/session.py", '    if not (purpose or "").strip():', "    if False:",
     "a session cannot open without a declared purpose (§7.2)",
     "tests/test_console.py"),
    ("console/session.py", "        if not self.open:", "        if False:",
     "a closed session refuses a further read", "tests/test_console.py"),
    # The driver reconciles on EVERY exit after the door opened — a read commits
    # disclosure_log, so a failure before close() must not leave it unreconciled
    # (§7.2, the gap both PR #16 reviews caught). Skipping close() in the finally
    # is what the acceptance test attempts and refuses.
    ("console/__main__.py", "        reconciliation = session.close(at)",
     "        reconciliation = None",
     "the driver reconciles on every exit path (§7.2)", "tests/test_console.py"),
    # --- the drop producer core (docs/PLAN-DROP.md D-1..D-4) ----------------
    #
    # Each row restores one of the four slices' forbidden acts and points at the
    # suite that must notice. All are pure Python — no cluster — so they run in
    # the control and ablate red without a database.
    #
    # D-1, drop/producer.py. The two invariants: fail-closed without the sealing
    # primitive (acceptance test 2), and one student per payload (the W-1/W-3
    # forbidden act). The availability guard is `if not available()` -> `if
    # False`, so a box that reports its primitive unusable proceeds to seal
    # instead of landing nothing.
    ("drop/producer.py", "    if not available():", "    if False:",
     "the producer fails closed without its sealing primitive",
     "tests/test_drop_producer.py"),
    ("drop/producer.py", "    if len(students) > 1:", "    if False:",
     "a two-student view is refused before sealing (W-1/W-3)",
     "tests/test_drop_producer.py"),
    # D-2, drop/store.py. Non-enumerability is structural (the slot is keyed by
    # the owner's secret material, so B's slot is unformable from A's handle) and
    # authenticated (a forged credential is refused). Plus the fail-closed drop
    # half: a credential with no material is not a credential.
    ("drop/store.py", "        if registered != credential.material:",
     "        if False:",
     "a forged owner credential cannot bind to a mailbox",
     "tests/test_drop_store.py"),
    ("drop/store.py",
     '    return hashlib.sha256(b"drop-slot:" + material).hexdigest()',
     '    return "one-shared-slot"',
     "a handle reads only its own mailbox (structural non-enumerability)",
     "tests/test_drop_store.py"),
    ("drop/store.py", "        if not self.material:", "        if False:",
     "a credential with no key material is refused (fail-closed)",
     "tests/test_drop_store.py"),
    # D-3, drop/cadence.py. Two ways a size could track its contents: a round
    # that does not pad to a constant number of slots, and a bucket that does not
    # equalise unequal payloads.
    ("drop/cadence.py", "    while len(out) < slots:", "    while False:",
     "a collection round is a constant number of slots",
     "tests/test_drop_cadence.py"),
    ("drop/cadence.py", "    filler = bytes(bucket - _HDR - len(payload))",
     '    filler = b""',
     "the bucket equalises unequal payload sizes",
     "tests/test_drop_cadence.py"),
    # D-4, drop/preparing.py. The forbidden act is preparing a restricted (or
    # lapsed) guardian a drop — restored by re-adding the suppressed to the
    # reachable set. And the fail-closed half: an UNKNOWN prepared set must not
    # iterate as empty (rule 13).
    ("drop/preparing.py", "    reachable = tuple(who)",
     "    reachable = tuple(who) + tuple(s[0] for s in who.suppressed)",
     "a restricted guardian is never prepared a drop",
     "tests/test_drop_preparing.py"),
    ("drop/preparing.py", "        if self.state is not Standing.DERIVED:",
     "        if False:",
     "an unknown prepared set does not iterate as empty (rule 13)",
     "tests/test_drop_preparing.py"),
    # §9 item 11 — records/assistance.py, the gated assistance seam. Each
    # mutation restores one of the four things A-1..A-4 refuse, and each is
    # caught by tests/test_assistance.py.
    #
    # A-1: the capability reaches a model only through inference.through. This
    # reuses inference's own local-provider guard and points it at the assistance
    # suite — the shared-middle, multiple-suites idiom (records/conflict.py's
    # one_lane): if the capability bypassed the gate, mutating this guard could
    # not turn the assistance suite red, so that it does IS the proof.
    ("records/inference.py", "    if provider != LOCAL:", "    if False:",
     "assistance refuses a cloud provider through the gate", "tests/test_assistance.py"),
    # A-2: assistance lands as a draft, and a draft is never servable.
    ("records/assistance.py", "        if self.record.state is not State.DRAFT:",
     "        if False:", "assistance lands only as a draft", "tests/test_assistance.py"),
    ("records/assistance.py", "        return False", "        return True",
     "a machine draft is not servable", "tests/test_assistance.py"),
    # A-3: the unattended loop, made unrepresentable. from_sealed refuses an
    # unsealed draft; the student's-own-draft branch is its own refusal (a
    # distinct narration, so neutering it is caught even though it falls through
    # to the generic loop refusal); and assist takes Grounding values only.
    ("records/assistance.py", "    if record.servable:", "    if True:",
     "an unsealed draft cannot ground assistance", "tests/test_assistance.py"),
    ("records/assistance.py",
     "    if record.author_id is not None and record.author_id == record.subject_id:",
     "    if False:", "a student's own draft is its own refusal", "tests/test_assistance.py"),
    ("records/assistance.py", "        if not isinstance(g, Grounding):",
     "        if False:", "a non-grounding cannot seed assistance", "tests/test_assistance.py"),
    # A-4: grounded only in an entitled read; no standing score; no ranking; and
    # one lane per narrative (through conflict.one_lane, the promoted middle).
    ("records/assistance.py", "    if decision.outcome not in _ENTITLED:",
     "    if False:", "assistance grounds only in an entitled read", "tests/test_assistance.py"),
    ("records/assistance.py",
     '        refuse_standing_score("AssistanceDraft.score", self.record.subject_id or "this student")',
     "        return 0", "a narrative carries no standing score", "tests/test_assistance.py"),
    ("records/assistance.py",
     "    refuse_to_rank(\"comparing two students' growth narratives\", subjects)",
     "    return None", "two narratives cannot be ordered", "tests/test_assistance.py"),
    ("records/conflict.py", "if len(lanes) > 1:", "if False:",
     "a growth narrative reads one lane", "tests/test_assistance.py"),
    # --- §10 season-boundary purge (records/retention.py) -------------------
    #
    # Each row restores one forbidden act the purge is built to refuse: an early
    # purge, a purge of the record of a purge, a seasonless sweep, an erasure
    # from a bare lane id with no dated record, and a horizon that is ignored so
    # a still-retained record reads as due. All pure Python (the erasure path
    # imports `cryptography`, which is declared), so they ablate red in control.
    ("records/retention.py", "if standing is not Standing.DUE:", "if False:",
     "dispose refuses a not-due record — no early purge (§10, refusal 3)",
     "tests/test_retention.py"),
    ("records/retention.py", "if isinstance(record, Disposition):", "if False:",
     "the record of a purge is not itself purgeable (rule 16 / I-7)",
     "tests/test_retention.py"),
    ("records/retention.py", "if not season:", "if False:",
     "a seasonless record is refused, not swept (rule 13)",
     "tests/test_retention.py"),
    ("records/retention.py", "if not isinstance(d, Disposition):", "if False:",
     "purge drives only dated dispositions, never a bare lane id (rule 15)",
     "tests/test_retention.py"),
    ("records/retention.py",
     "    standing = Standing.DUE if now >= retain_until else Standing.RETAINED",
     "    standing = Standing.DUE if now >= ended else Standing.RETAINED",
     "the retention horizon is honored, not just the season end (§10)",
     "tests/test_retention.py"),
    ("records/retention.py", "    if dt.tzinfo is None:", "    if False:",
     "a naive now/invalid_at is refused, not compared (clean, not a crash)",
     "tests/test_retention.py"),
    # The three above the line are all record-scoped, and every one of them held
    # while `purge()` erased a whole student: `atrest.destroy` drops every
    # wrapping for a lane, so a `Disposition` about one aged-out attendance
    # record took the key opening that student's live medical note with it. The
    # rows below point at the lane-scoped guard that closes it. Two of the three
    # are about *absence* rather than about a not-due record, because a missing
    # or empty enumeration is the way past the third that costs a caller nothing
    # to write (rule 13).
    ("records/retention.py", "if assessed.standing is not Standing.DUE:",
     "if False:",
     "a lane is erased only when every record in it is due (rule 8)",
     "tests/test_retention.py"),
    ("records/retention.py", "if held is None:", "if False:",
     "an unenumerated lane is unknown, not empty (rule 13)",
     "tests/test_retention.py"),
    ("records/retention.py", "if not held:", "if False:",
     "a lane listed as holding nothing is not a lane with nothing in it",
     "tests/test_retention.py"),
    # Rule 12's middle for §18 item 19 <-> records/retention.py, and the
    # mutation lives on the **document** for the reason item 6 records: the
    # first attempt at the VERIFIED-COUNT row mutated the test and asked the
    # same test to notice, which the harness correctly reported as SURVIVES.
    ("docs/ARCHITECTURE.md", "`LaneNotDue`", "`LaneNotYetDue`",
     "§18 item 19 names the refusals records/retention.py raises",
     "tests/test_retention.py"),

    # craft/ — the one piece of working software in the tree, and it carried no
    # mutation at all until 2026-08-01. The rows below cover rule 13 on the
    # checker itself: a draft that could not be read must not report as a draft
    # with nothing in it. All five restore a defect that shipped.
    ("craft/checks.py", "        report.unread = True", "        report.unread = False",
     "rule 13: an unread lyric says so", "tests/test_craft.py"),
    ("craft/checks.py", "        if report.unread:", "        if False:",
     "rule 13: a one-sided lyric diff is refused", "tests/test_craft.py"),
    ("craft/__main__.py", "    if report.unread:", "    if False:",
     "rule 13: the CLI prints no false count", "tests/test_craft.py"),
    # Two `report.unread = True` in prose.py, so the pattern carries the line
    # after it. A bare one returns AMBIGUOUS x2, which is an error here rather
    # than a pass — the harness's own lesson, applied on the way in.
    ("craft/prose.py",
     '        report.unread = True\n        report.unavailable.append(\n'
     '            "Empty document.',
     '        report.unread = False\n        report.unavailable.append(\n'
     '            "Empty document.',
     "rule 13: an unread document says so", "tests/test_prose.py"),
    ("craft/prose.py", "    declined = diff_declined(before_report, after_report)",
     "    declined = []",
     "rule 13: a one-sided document diff is refused", "tests/test_prose.py"),

    # The rule-13 sweep's *other* half, added 2026-08-02. The middle that was
    # there walked SEAMS and asserted a test for each row; nothing walked the
    # tree and asserted a row for each seam, so the list was the authority on
    # its own completeness. These five aim at the walk rather than at what it
    # walks — the guard is in a test file because the inventory is, and
    # `tests/ablate.py` already carries rows against itself for the same reason.
    ("tests/test_rule13_acceptance.py",
     "        missing.append((module, tuple(sorted(uncovered)), why))",
     "        pass",
     "rule 13 sweep: an uninventoried seam is reported",
     "tests/test_rule13_acceptance.py"),
    ("tests/test_rule13_acceptance.py",
     "        raise MarkUndecidable(f\"will not parse: {exc}\") from exc",
     "        return ()",
     "rule 13 sweep: a module the walk cannot read is unknown, not clean",
     "tests/test_rule13_acceptance.py"),
    ("tests/test_rule13_acceptance.py",
     '    ("store/narration.py", ("serve_field(decide)",),',
     '    ("store/narration.py", ("serve_field(decide)", "serve_field(ghost)"),',
     "rule 13 sweep: an exemption cannot excuse a source the tree lacks",
     "tests/test_rule13_acceptance.py"),
    ("tests/test_rule13_acceptance.py",
     'KNOWN_BLIND = (\n    ("craft/checks.py",',
     'KNOWN_BLIND = (\n    ("records/sending.py",',
     "rule 13 sweep: a published miss that stopped being one goes red",
     "tests/test_rule13_acceptance.py"),
    ("tests/test_rule13_acceptance.py",
     'SCANNED_ROOTS = ("console", "craft", "drop", "presentation", "records",',
     'SCANNED_ROOTS = ("console", "craft", "drop", "presentation",',
     "rule 13 sweep: a scan that shrank is not a clean tree",
     "tests/test_rule13_acceptance.py"),
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


#: Suites that run **this harness** — directly, or through `tools/conform.py`'s
#: `check_ablation`. They cannot be part of the control run: starting them here
#: starts a second ablation, which `_acquire_lock` refuses, correctly. Both are
#: run by the ordinary suite and by CI, so nothing goes unchecked; what is given
#: up is only checking them *first*.
REENTRANT = ("tests/test_ablate.py", "tests/test_conform.py")


def control_suites() -> list:
    """Every suite a mutation points at, minus the re-entrant two.

    Derived, not hand-kept. A hand-kept list is how a suite came to be mutated
    without ever being run green first — and a suite that is already red reports
    `caught` for every mutation aimed at it, because the harness sees a nonzero
    exit and a `FAIL ` line that belongs to somebody else.
    """
    return sorted({m[4] for m in MUTATIONS} - set(REENTRANT))


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
    # **Every suite a mutation points at, and that is the point.** A suite that
    # is already red reports `caught` for every mutation aimed at it, because
    # `verdict()` sees a nonzero exit and a named failure — the mutation's or
    # somebody else's. That happened here on 2026-07-31: `tests/test_presentation.py`
    # was red for an unrelated reason and eighteen mutations pointed at it all
    # read `caught` while proving nothing. The control list had been a hand-kept
    # subset; it is now derived from MUTATIONS, so a new mutation cannot arrive
    # pointing at a suite nobody checked first.
    # **And the derived list has to be the one that decides.** Until 2026-07-31
    # the line below was followed by a second assignment to `healthy` over a
    # hand-kept twelve, so the derived run's verdict was computed, discarded,
    # and the hand-kept subset decided — twelve of the thirty-four suites a
    # mutation points at. Every suite outside that twelve could be red while the
    # control printed `green`, which is the exact state this paragraph says was
    # fixed. A leftover line, and the comment above it read as enforcement while
    # the code was a ledger (rule 18).
    healthy = all(run(s)[0] for s in control_suites())
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
