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
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
# `records` too, for checks that read the core rather than parse it. Running
# `python3 tools/conform.py` puts only `tools/` on the path, so a check
# importing the package worked under the test suite (which inserts ROOT) and
# died from the command line — the two ways this file is run disagreeing.
sys.path.insert(0, str(ROOT))
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
    """§6's *declared write paths*, reconciled against the manifest that declares them.

    **The version that lived here took no path argument**, so it could not be
    pointed at a decoy at all, and it matched substrings — a docstring saying
    *"never calls `open(`"* failed the file while `Path.open()`, `os.rename`
    and `tempfile` passed it.

    **It then spent a month reporting `UNKNOWN` for an honest reason**: it
    scanned `records/`, found no writes, and said so while noting that *"the
    manifest declares no write paths to reconcile against, so this is not
    evidence the mechanism works."* That is rule 18's distinction, correctly
    stated — a ledger, not a gate. Gate G-C landed the declaration with
    `store/`, so this row becomes a gate: `tools/manifest.py` reconciles every
    writer in the scanned tree against `manifest.json`'s `write_paths`, both
    directions, and a disagreement is `FAIL`.

    `where` still points the *inner-ring* half at a tree, because the two
    questions are different and only one of them has an answer over an arbitrary
    directory: **does `records/` write** (a property of a path) and **is every
    writer declared** (a property of this repository and its manifest). Over a
    tree that is not there, both are unknown.
    """
    from manifest import MANIFEST, reconcile, sources  # noqa: E402
    from purity import counted, reads, writes  # noqa: E402

    targets = [where] if where is not None else [ROOT / "records"]
    found = writes(targets)
    n = counted(targets)
    what = "declared write paths (§6, gate G-C)"
    if found:
        return Check("write-paths", what, State.FAIL,
                     f"{targets[0].name}/ writes and nothing declares it: "
                     + "; ".join(str(t) for t in found[:4]))
    if not n:
        return Check("write-paths", what, State.UNKNOWN,
                     "no files scanned; nothing was checked")
    r = reads(targets)
    inner = (f"{n} module(s) in the inner ring scanned by AST: no writes"
             + (f", {len(r)} read(s)" if r else ", no reads"))

    if not MANIFEST.exists():
        return Check("write-paths", what, State.UNKNOWN,
                     inner + " — and no manifest to reconcile the rest of the "
                             "tree against, so this is not evidence the "
                             "mechanism works")
    scanned = sources(ROOT)
    if not scanned:
        return Check("write-paths", what, State.UNKNOWN,
                     inner + " — the reconciliation scanned no files at all")
    outer = reconcile(manifest=MANIFEST, paths=scanned, surfaces_at=ROOT / "surfaces")
    bad = [f for f in outer.findings if f.code.startswith("WRITE")]
    if bad:
        return Check("write-paths", what, State.FAIL,
                     inner + " — and " + "; ".join(f.detail for f in bad[:3]))
    declared = len((read_manifest_write_paths() or ()))
    return Check("write-paths", what, State.PASS,
                 inner + f"; {declared} write path(s) declared in manifest.json "
                         f"and reconciled against {len(scanned)} scanned "
                         "module(s), both directions")


def read_manifest_write_paths():
    """The declared write paths, or `None` when the manifest cannot say.

    Separated so the count in the evidence above comes from the file rather than
    from a literal — rule 17 inside a checker's own sentence, which is where
    §18 item 6 found the last instance of it.
    """
    from manifest import MANIFEST, read  # noqa: E402

    data, _ = read(MANIFEST)
    if data is None or "write_paths" not in data:
        return None
    return tuple(data["write_paths"])


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

    **The target list is derived from the tree, and was not.** Until the
    manifest landed this named four paths by hand, so the two packages item 4
    created — `presentation/` and `surfaces/`, the ones most likely to listen —
    would have been outside the scan on the day they arrived. `manifest.sources`
    enumerates instead, and `tests/test_manifest.py` asserts the complement is
    enumerable.
    """
    from manifest import sources  # noqa: E402
    from sockets import Verdict, check as scan_check  # noqa: E402

    files = list(sources(ROOT))
    r = scan_check(files, ROOT / "manifest.json")
    what = "listening sockets are declared (§4.3, item 4 note ii)"
    if r.verdict is Verdict.VACUOUS or not files:
        return Check("declared-sockets", what, State.UNKNOWN,
                     "no manifest and no listeners: nothing was checked. The "
                     "checker is wired and shown to fail (tests/fixtures/decoys), "
                     "so the first surface item 4 lands is caught on arrival")
    if r.findings:
        return Check("declared-sockets", what, State.FAIL,
                     "; ".join(f.detail for f in r.findings[:3]))
    return Check("declared-sockets", what, State.PASS,
                 f"{len(files)} source file(s) scanned; {len(r.listeners)} "
                 f"listener(s) and {len(r.outbound)} outbound connection(s), "
                 "every one declared")


def check_manifest() -> Check:
    """§6's manifest, with a cloud permission failing the build — and the rest
    of the declaration reconciled against the tree (`tools/manifest.py`).

    This row was `UNKNOWN` with the words *"no manifest exists in this
    repository; §18 item 4 has to say what surfaces exist before one can
    declare them"* until item 4 closed. It is the declaration half only: the
    manifest may not *ask* for a third-party model, and asserting the provider
    actually used at run time is a different gate that does not exist yet.
    """
    from manifest import reconcile, sources  # noqa: E402

    r = reconcile(manifest=ROOT / "manifest.json", paths=sources(ROOT),
                  surfaces_at=ROOT / "surfaces")
    what = "manifest with a build-failing cloud-permission check (§6)"
    if r.vacuous:
        return Check("manifest", what, State.UNKNOWN,
                     "; ".join(f.detail for f in r.findings[:2])
                     or "nothing was checked")
    if r.findings:
        return Check("manifest", what, State.FAIL,
                     "; ".join(f.detail for f in r.findings[:3]))
    return Check("manifest", what, State.PASS,
                 f"{len(r.surfaces_declared)} surface(s) declared and present, "
                 f"{r.scanned} source file(s) reconciled: no listener, no "
                 "outbound, no cloud permission, no unknown key")


def check_stdlib_only() -> Check:
    """TM-DEPS-01 (§10): every import is stdlib, a declared dependency, or
    local — the enforcement half of a posture that was asserted in dozens of
    docstrings and enforced by nobody until `tools/imports.py`. A finding is an
    undeclared import; the set of admitted third-party roots is derived from
    `requirements.txt`, so the gate and the declaration cannot drift.
    """
    from imports import (Verdict, check as imports_check, _default_paths,  # noqa: E402
                         ROOT as IMPORTS_ROOT)

    # Re-root the path shape under conform.ROOT so the acceptance test — which
    # points conform.ROOT at an empty tree — scans *that* tree, finds nothing,
    # and reports UNKNOWN rather than PASS over the real tree (rule 13). In an
    # ordinary run conform.ROOT == IMPORTS_ROOT and the list is unchanged.
    targets = [ROOT / p.relative_to(IMPORTS_ROOT) for p in _default_paths()]
    r = imports_check([p for p in targets if p.exists()],
                      requirements=ROOT / "requirements.txt", where=ROOT)
    what = "every import is stdlib, declared, or local (TM-DEPS-01, §10)"
    if r.verdict is Verdict.VACUOUS:
        return Check("stdlib-only", what, State.UNKNOWN,
                     "no Python scanned; a scan of nothing is not a pass")
    if r.findings:
        return Check("stdlib-only", what, State.FAIL,
                     "; ".join(f"{f.module}:{f.line} imports {f.root!r} "
                               "(undeclared)" for f in r.findings[:3]))
    return Check("stdlib-only", what, State.PASS,
                 f"{r.scanned} file(s): every import stdlib / declared / local; "
                 "the two declared roots are cryptography and psycopg")


def check_trust_root_committed() -> Check:
    """Refusal 2 (`TM-ROOT-01`): the trust root is never *committed*, checked over
    the tree git tracks rather than the staged set. `.githooks/pre-commit` gates a
    commit on an installed clone; `tools/trustroot.py` catches a trust-root path
    that reached a commit through an uninstalled one, so the two enforcements
    compose — and this row is what makes the committed-tree half a gate the
    conformance record carries rather than a suite-only check (rule 18). A tree
    git cannot list is `UNKNOWN`, never clean (rule 13), which is also what the
    acceptance sweep sees when `conform.ROOT` points at a tree that is not there.
    """
    from trustroot import Verdict as _TRV, scan as _tr_scan  # noqa: E402

    r = _tr_scan(where=ROOT)
    what = "the trust root is never committed (TM-ROOT-01, refusal 2, §6)"
    if r.verdict is _TRV.UNKNOWN:
        return Check("trust-root", what, State.UNKNOWN, r.detail)
    if r.verdict is _TRV.FINDINGS:
        return Check("trust-root", what, State.FAIL, r.detail)
    return Check("trust-root", what, State.PASS, r.detail)


def check_local_inference(where: Optional[Path] = None) -> Check:
    """Refusal 1 (§6): nothing reaches a model except through the guard.

    **Built before there is anything to find, and the state says so.** No
    inference path exists in this repository, so the honest verdict today is
    `UNKNOWN` — a scan over a tree with nothing to scan has not checked
    anything, the shape `check_declared_sockets` reports for a manifest that
    does not exist yet. What it buys is arrival: `records/inference.py` makes
    an unguarded *answer* unrepresentable, and this makes an unguarded *call
    site* a build failure the day somebody writes one.
    """
    from providers import Verdict, check as reach_check  # noqa: E402

    targets = [where] if where is not None else [
        ROOT / "records", ROOT / "tools", ROOT / "craft", ROOT / "voice.py",
        ROOT / "personas.py"]
    r = reach_check(targets)
    what = "every inference path routes through the refusal-1 guard (§6)"
    if r.verdict is Verdict.VACUOUS:
        return Check("local-inference", what, State.UNKNOWN,
                     f"{r.scanned} module(s) scanned by AST and none reaches a "
                     "model: nothing was checked. The guard (records/inference.py) "
                     "and this tripwire are wired and shown to fail against "
                     "tests/fixtures/decoys, so the first inference path is "
                     "caught on arrival")
    if r.findings:
        return Check("local-inference", what, State.FAIL,
                     "; ".join(str(f) for f in r.findings[:3]))
    calls = [x for x in r.reaches if x.kind.value != "router_import"]
    return Check("local-inference", what, State.PASS,
                 f"{len(calls)} call(s) reach a model across {r.scanned} "
                 "module(s); every one goes through records.inference")


def check_anchor_payload() -> Check:
    """§5/§6: an anchor may cross the egress boundary *because* it carries a
    digest, a count and a time and nothing else. So the check is not that the
    rule is written down — it is that something carrying a fourth field is
    refused when handed to the gate.

    This one really runs: it builds an anchor with a subject id on it and asks
    to publish it. A `PASS` here means the attempt was made and refused.
    """
    from records.publication import (Cadence, NotPublishable,  # noqa: E402
                                     payload_for, permitted)
    from records.witness import Anchor  # noqa: E402

    what = "an anchor crosses because it carries nothing else (§5, §6)"
    at = datetime(2026, 1, 5, tzinfo=timezone.utc)
    cadence = Cadence(at, timedelta(days=7))

    @dataclass(frozen=True)
    class Tagged(Anchor):
        subject_id: str = ""

    refused = []
    smuggled = Tagged("a" * 64, 3, at, subject_id="a-named-student")
    try:
        payload_for(smuggled, cadence)
    except NotPublishable as exc:
        refused.append(f"subclass field: {exc}"[:80])

    hung = Anchor("b" * 64, 3, at)
    object.__setattr__(hung, "note", "a named student")
    try:
        payload_for(hung, cadence)
    except NotPublishable:
        refused.append("instance attribute")

    try:
        payload_for(Anchor("c" * 64, 3, at + timedelta(days=2)), cadence)
    except NotPublishable:
        refused.append("off the calendar")

    honest = payload_for(Anchor("d" * 64, 3, at), cadence)
    if len(refused) != 3:
        return Check("anchor-payload", what, State.FAIL,
                     f"only {len(refused)} of 3 forbidden publications refused: "
                     f"{'; '.join(refused)}")
    if len(honest.commitment) != 32 or not permitted(Anchor("d" * 64, 3, at))[0]:
        return Check("anchor-payload", what, State.FAIL,
                     "the gate refused an ordinary anchor, or the payload is not "
                     "32 bytes; a gate that refuses everything is switched off next")
    return Check("anchor-payload", what, State.PASS,
                 "three attempts made and refused (a subclass field, an attribute "
                 "hung on the instance, a publication off the calendar); an "
                 "ordinary anchor yields 32 bytes")


def check_anchor_published() -> Check:
    """§18 item 15's weekly half, and the part this tree cannot answer.

    The payload, the register and the states around a pending proof are built
    and tested. Whether anchors are *being submitted every week* is a fact about
    a running deployment's seam, and there is no seam here — by design, since a
    module that made the call would be an egress path in `records/`.
    """
    core = ROOT / "records" / "publication.py"
    if not core.exists():
        return Check("anchor-published", "anchors are published on the calendar "
                     "(§18 item 15)", State.ABSENT,
                     "records/publication.py does not exist")
    return Check("anchor-published",
                 "anchors are published on the calendar (§18 item 15)",
                 State.UNKNOWN,
                 "the payload, the register and the pending states exist and are "
                 "shown to fail (tests/test_publication.py); whether a deployment "
                 "submits weekly is a property of a seam this tree deliberately "
                 "does not contain")


def check_receipt_attribution() -> Check:
    """§18 item 15's standing dependency: *a deployment wants Ed25519 here.*

    Reported as its own row rather than left to be inferred from a docstring.
    `ABSENT` is the honest state — the socket exists and the primitive does not
    — and it is deliberately not `UNKNOWN`, because this is decided and missing
    rather than undecidable.
    """
    from records.receipts import Issuance, schemes  # noqa: E402

    what = "guardian receipts a third party can attribute (§18 item 15)"
    have = schemes()
    if any(s.startswith("ed25519") or s.startswith("ecdsa") for s in have):
        return Check("receipt-attribution", what, State.PASS,
                     f"issuance schemes available: {', '.join(have)}")
    return Check("receipt-attribution", what, State.ABSENT,
                 f"the only issuance scheme here is {', '.join(have)}, which is "
                 f"{Issuance.SELF_VERIFIABLE.value}: the programme can check its "
                 "own receipts and a third party cannot attribute one. The seam "
                 "(records.receipts.Signer) is built and no primitive is wired")


def check_deposit_procedure() -> Check:
    """The annual half of the composite. A procedure, not code — so what is
    checkable is that it exists and says who, when, what, and how a missed one
    surfaces."""
    doc = ROOT / "docs" / "WITNESS-DEPOSIT.md"
    what = "the annual deposit is written down (§18 item 15)"
    if not doc.exists():
        return Check("deposit-procedure", what, State.ABSENT,
                     "docs/WITNESS-DEPOSIT.md does not exist; the decided "
                     "composite has an annual leg and no procedure")
    text = doc.read_text(encoding="utf-8")
    required = ("## What is deposited", "## When", "## Who performs it",
                "## The receipt of deposit", "## A missed deposit")
    absent = [h for h in required if h not in text]
    if absent:
        return Check("deposit-procedure", what, State.FAIL,
                     "the procedure omits: " + ", ".join(absent))
    return Check("deposit-procedure", what, State.PASS,
                 f"docs/WITNESS-DEPOSIT.md, {len(text.splitlines())} lines, all "
                 f"{len(required)} required sections present. Whether a deposit "
                 "was performed is not decidable from a tree")


def check_classification_registry(schema: Optional[Path] = None,
                                  doc: Optional[Path] = None) -> Check:
    """§9 item 2's pair, and the middle between its two halves.

    The class-to-`L` mapping is implemented twice — `records/classify.py` runs
    `SENSITIVITY.md`'s procedure, and `migrations/001_lanes.sql` seeds a
    `(class, rung)` for every column — so `tools/registry.py` reconciles the two
    against the document's own table and against the DDL's column list.

    **`UNDECIDED` is not a pass and not a build failure.** An elevation above
    the rung a class derives is permitted by step 3's clause and step 4's rules,
    both human-evaluated at schema-definition time; where nothing records which
    applies, this row says so with both values rather than picking one. A
    disagreement — a rung below what the class derives, an unclassified column,
    a row for a column nothing declares — is a `FAIL`.
    """
    from registry import Agreement, Verdict, check as registry_check  # noqa: E402

    # conform.ROOT, explicitly — registry's module default reads its own tree,
    # and a check that scans the installed copy reports health out of a source
    # that is not there. Invisible while this row was UNKNOWN; the sweep caught
    # it the day the row first turned PASS (same class as check_manifest).
    #
    # The **directory**, not `001_lanes.sql`. Naming one file was correct while
    # the schema was one file, and became a second way to believe in an old
    # schema the moment migration 004 seeded four columns: this row would have
    # gone on reporting 116 reconciled fields out of a tree that had 120.
    r = registry_check(
        schema if schema is not None else ROOT / "migrations",
        doc if doc is not None else ROOT / "docs" / "SENSITIVITY.md")
    what = "the class-to-L mapping is enforced in one place (§9 item 2, §16)"
    if r.verdict is Verdict.VACUOUS:
        return Check("classification-registry", what, State.UNKNOWN,
                     "; ".join(f.detail for f in r.findings[:2])
                     or "nothing was read")
    if r.findings:
        return Check("classification-registry", what, State.FAIL,
                     "; ".join(str(f) for f in r.findings[:3]))
    undecided = r.of(Agreement.UNDECIDED)
    if undecided:
        return Check(
            "classification-registry", what, State.UNKNOWN,
            f"{r.agreed} of {len(r.judgements)} field(s) reconciled "
            f"({len(r.of(Agreement.ELEVATED))} elevated by a recorded rule); "
            f"{len(undecided)} undecided and named: "
            + ", ".join(f"{j.field} registry={j.seeded} derives={j.derived}"
                        for j in undecided[:4]))
    return Check("classification-registry", what, State.PASS,
                 f"{len(r.judgements)} field(s): the seed, records/classify.py "
                 f"and SENSITIVITY.md's table agree "
                 f"({len(r.of(Agreement.ELEVATED))} elevated by a recorded rule)")


def check_key_escrow() -> Check:
    """§5's escrow gap, and §10's proposed **R16 — data at rest is encrypted,
    with the key escrowed.**

    **This row read `ABSENT` until S-3, on grounds that stopped being true.** Its
    evidence was *"no keyring and no sealed store exist here, so no master has a
    disposition to report"*, and both halves have since moved: gate G-A picked
    `E-1`, 3-of-5, recorded in `docs/ESCROW.md` on 2026-07-31, and
    `migrations/004_sealed_payloads.sql` means a sealed store now **can** exist.
    A row still saying `ABSENT` would be claiming nothing had been decided about
    a policy that had been decided, which is worse than saying nothing.

    **So it reads `UNKNOWN`, and `UNKNOWN` is the whole point.** It is neither
    `PASS` nor `ABSENT`, and neither by accident:

    * not `ABSENT`, because a policy *is* recorded — a threshold, five
      custodians, an annual drill — and absence is a different fact from
      unrehearsed (rule 13, which is why `records/atrest.py` has four escrow
      states and not a boolean);
    * not `PASS`, because §5 is flat about it: *an untested key recovery is not
      escrow.* `docs/ESCROW.md`'s "Rehearsals recorded" section says *none yet*
      and says so on purpose, *"so nobody reads a table of policy as a table of
      practice."* The first rehearsal is an install-acceptance act (§11.1) — it
      happens in a room with five people in it, and CI cannot hold it.

    **The state name is `records/atrest.py`'s, not a second vocabulary.** The
    mapping from the document's facts to an `EscrowState` is made here, once,
    and the member is imported so it cannot drift from the module that defines
    the ladder. The tree deliberately holds **no keyring** (refusal 2: no key
    material in the tree, ever), so the disposition lives in a document rather
    than in a `Keyring`, and `escrow_survey` over an empty one is still consulted
    — it is the answer for the masters this tree depends on, and there are none.

    The row goes green the day `docs/ESCROW.md` gains a dated rehearsal, and
    `tests/test_conform.py` drives that transition against a synthetic document
    rather than waiting for the ceremony.
    """
    what = "data at rest is sealed and its key escrowed (§5; §10's R16)"
    src = ROOT / "records" / "atrest.py"
    if not src.exists():
        return Check("key-escrow", what, State.ABSENT,
                     "records/atrest.py does not exist; §9's foundation 3 is "
                     "unbuilt and nothing can seal at rest")

    from records.atrest import (EscrowState, Keyring, available,  # noqa: E402
                                escrow_survey)

    from audit import ESCROW_DOC, escrow_facts  # noqa: E402

    at = datetime.now(timezone.utc)
    # This repository holds no keyring and must not (refusal 2: no key material,
    # no grant material, in the tree). The survey of an empty one is empty, and
    # an empty survey is the honest input here rather than a vacuous one.
    survey = escrow_survey(Keyring(), at=at)
    primitive = ("the sealing primitive is usable" if available()
                 else "the sealing primitive is NOT usable on this box")
    facts = escrow_facts()
    # Relative when it is inside the tree, absolute when a test has pointed the
    # module at a synthetic document. `relative_to` raises rather than falling
    # back, and a check that crashed on its own evidence line would be a check
    # nobody could drive the transition of.
    try:
        cite = ESCROW_DOC.relative_to(ROOT)
    except ValueError:
        cite = ESCROW_DOC

    # What a sealed store would be sealed *for*, derived rather than assumed:
    # the columns store/sealing_plan.py says seal. Zero of them means no sealed
    # store is possible yet and the old ABSENT reading was right.
    try:
        from store.sealing_plan import sealed_columns  # noqa: E402
        sealable = sealed_columns()
    except Exception as exc:  # noqa: BLE001 — an unreadable plan is unknown, not empty
        return Check("key-escrow", what, State.UNKNOWN,
                     f"the sealing plan could not be read ({exc!r}), so whether a "
                     "sealed store can exist here is not established. That is not "
                     "the same as no store existing (rule 13)")

    if survey:
        undecided = [m for m, state, _ in survey
                     if state is not EscrowState.RECORDED]
        if undecided:
            return Check("key-escrow", what, State.FAIL,
                         f"{len(undecided)} of {len(survey)} master(s) have no "
                         f"rehearsed escrow: {', '.join(undecided[:3])}")
        return Check("key-escrow", what, State.PASS,
                     f"{len(survey)} master(s), each with a rehearsed disposition "
                     "inside its declared window")

    at_rest_possible = (
        f"{len(sealable)} column(s) seal at rest "
        f"({', '.join(f'{t}.{c}' for t, c in sealable) or 'none'}), so a sealed "
        f"store can exist here")

    if not facts.exists or not facts.recorded:
        return Check("key-escrow", what, State.ABSENT,
                     f"{cite} records no k-of-n threshold, so no policy is "
                     f"decided; {primitive}. {at_rest_possible}. §5 calls "
                     f"single-file key loss the failure mode that ends the "
                     f"program — records/atrest.py reports "
                     f"{EscrowState.ABSENT.value.upper()} for any master with "
                     f"none, and that guard is ablated")

    if not facts.rehearsed:
        return Check(
            "key-escrow", what, State.UNKNOWN,
            f"{cite}: policy recorded, threshold {facts.threshold}, "
            f"{facts.holders} custodian(s), {len(facts.rehearsals)} rehearsal(s) "
            f"on record. That is records/atrest.py's "
            f"{EscrowState.UNKNOWN.value.upper()} — recorded and never rehearsed "
            f"— and §5 is why it is not a pass: an untested key recovery is not "
            f"escrow. {at_rest_possible}, so this is not "
            f"{EscrowState.ABSENT.value.upper()} either. The first rehearsal is "
            f"an install-acceptance act (§11.1); {primitive}")

    return Check("key-escrow", what, State.PASS,
                 f"{cite}: {facts.threshold} across {facts.holders} custodian(s), "
                 f"last rehearsed {facts.rehearsals[-1]}. {at_rest_possible}; "
                 f"{primitive}")


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
    if r.returncode == 1:
        return Check("security-audit", what, State.UNKNOWN,
                     f"{path.name} pins `{pin}`, which is not an ancestor of HEAD; "
                     "the audit describes a tree this one does not contain")
    if r.returncode != 0:
        # Exit 1 is git answering *no*; anything else is git unable to answer —
        # a shallow clone with the pin outside its horizon, or a sha it has
        # never seen. Reporting that as "not an ancestor" asserted a negative
        # nobody established (rule 13), and it shipped: CI's checkout was
        # shallow, every ancestry question came back 128, and the gate called
        # a true pin foreign. The workflow now fetches full history; this
        # branch stays for every other shallow context.
        return Check("security-audit", what, State.UNKNOWN,
                     f"{path.name} pins `{pin}` and this clone cannot decide "
                     "ancestry (shallow history or unknown sha) — undecidable, "
                     "not foreign")

    return Check("security-audit", what, State.PASS,
                 f"{path.name} dated {when} at `{pin}`, {age} day(s) old; "
                 f"{len(found)} finding(s) recorded, "
                 f"{sum(1 for f in found if f.open)} open, none at S1 or above")


def check_row_security_differential() -> Check:
    """§16's pair, created by S-2, and the middle that makes it legal (rule 12).

    `migrations/003_row_security.sql` compiles the lane seal and the crossing
    envelope into row-level security policies; `records/serving.py` and
    `records/crossing.py` decide the same things in Python. Two implementations
    of one rule is the pair this repository exists to refuse building without a
    reconciler, and `tests/test_store_differential.py` is the reconciler: one
    case set through both layers, failing on any disagreement in either
    direction.

    **This row is `UNKNOWN` without a cluster and never `PASS`.** The suite exits
    `2` and says so (`tests/cluster.py`'s discipline), and a conformance record
    that reported a middle as holding on a machine where it did not run would be
    the formality §17 warns about. `PASS` here means the suite was executed
    against a real PostgreSQL and every case agreed.
    """
    suite = ROOT / "tests" / "test_store_differential.py"
    what = "one read predicate, two implementations, one middle (§16, rule 12)"
    if not suite.exists():
        return Check("row-security-differential", what, State.ABSENT,
                     f"{suite.name} does not exist; migrations/003_row_security.sql "
                     "would be a second implementation with nothing reconciling it")
    r = subprocess.run([sys.executable, str(suite)], capture_output=True,
                       text=True, cwd=ROOT)
    lines = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    cases = next((l for l in lines if "case(s) driven" in l), "")
    if r.returncode == 2:
        return Check("row-security-differential", what, State.UNKNOWN,
                     "no PostgreSQL to run the differential against, so the two "
                     "implementations were not compared: "
                     + (lines[-1] if lines else "the suite reported UNKNOWN"))
    if r.returncode != 0:
        failed = [l for l in lines if l.startswith("FAIL")]
        return Check("row-security-differential", what, State.FAIL,
                     "; ".join(failed[:3]) or (lines[-1] if lines else "the suite failed"))
    return Check("row-security-differential", what, State.PASS,
                 (cases or "the case set") + " through records/serving.py with "
                 "real rows and through the cluster under RLS; no disagreement "
                 "in either direction")


def check_knock_enforcing() -> Check:
    """§7.2's knock, wired in enforcement mode by S-4 — no longer a ledger.

    This row read `UNKNOWN` with the words *"session reconciliation lives in
    willow-gate and is not wired here … so by rule 18 it is a ledger and not
    enforcement until a surface exists (§18 item 4)."* The surface exists:
    `console/session.py` opens a session over the store, and a session cannot
    read without a declared purpose (`ReadWithoutDeclaration`) and cannot close
    without reconciling declared against observed and landing the
    `reconciled_session` row (`store/reconcile.py`). Something routes through the
    knock, so this becomes a gate.

    **`PASS` means the cluster suite ran and the knock enforced.** Like
    `check_row_security_differential`, this needs a real PostgreSQL:
    `tests/test_store_knock.py` exits `2` with `UNKNOWN` where there is none, and
    a conformance record that reported enforcement holding on a machine where it
    did not run would be the formality §17 warns about. The pure-Python half —
    a read refused before the store is touched — is ablated in `tests/ablate.py`
    and caught by `tests/test_console.py`, which needs no database.
    """
    suite = ROOT / "tests" / "test_store_knock.py"
    what = "the knock wired in enforcement mode (§7.2)"
    if not suite.exists():
        return Check("knock-enforcing", what, State.ABSENT,
                     f"{suite.name} does not exist; the knock has no surface "
                     "routing through it, so it is a ledger (§18 item 4)")
    r = subprocess.run([sys.executable, str(suite)], capture_output=True,
                       text=True, cwd=ROOT)
    lines = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    if r.returncode == 2:
        return Check("knock-enforcing", what, State.UNKNOWN,
                     "no PostgreSQL to route a session through the knock, so "
                     "enforcement was not exercised: "
                     + (lines[-1] if lines else "the suite reported UNKNOWN"))
    if r.returncode != 0:
        failed = [l for l in lines if l.lower().startswith("fail")]
        return Check("knock-enforcing", what, State.FAIL,
                     "; ".join(failed[:3]) or (lines[-1] if lines else "the suite failed"))
    return Check("knock-enforcing", what, State.PASS,
                 (lines[-1] if lines else "the suite passed")
                 + " — a session refused a read without a declared purpose and "
                   "reconciled declared against observed on exit, landing the "
                   "reconciled_session row (console/session.py, store/reconcile.py)")


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


#: Every middle rule 12 requires that this repository has actually named and
#: tested. **A list, so the figure beside it is derived** — it read *"Seventeen
#: middles"* as a word beside a list of seventeen, which is a count in prose one
#: commit away from the code moving past it (rule 17). Whether the list is
#: *complete* is still a reading and the check still says so.
NAMED_MIDDLES: Tuple[str, ...] = (
    "crossing", "standing.is_self_edge", "standing.may_supersede",
    "serving._acting_ward", "serving._ceiling", "marking.drift",
    "practice._one_lane", "publication.reconcile",
    "inference.CLASSES<->SENSITIVITY.md",
    "inference.COVERED_CLASSES<->CLAUDE.md refusal 1",
    "providers.GUARD_ENTRIES<->records.inference", "scales.drift",
    "render.check", "manifest.reconcile",
    "registry.reconcile<->migrations/001_lanes.sql+records/classify.py",
    "atrest.reconcile", "atrest.composes",
    "venue.sourcing.divergence<->records.marking P1-P5",
    "commentary.SA3_CLAUSE<->§13",
    "commentary.GuestSession<->reconciled_session",
    "aggregate._descriptor_for<->classify step 2a",
    "aggregate._legitimate<->rule 9 gate",
    # S-2's, and the largest pair this repository has deliberately created: the
    # read predicate exists twice (`docs/PLAN-STORE.md` decision 4), once in
    # SQL and once in Python, and the differential suite is what keeps the two
    # from drifting. It carries its own conformance row —
    # `row-security-differential` — because a middle nobody runs is a middle in
    # name, which is the distinction rule 18 asks to be said out loud.
    "test_store_differential<->serving.serve+migrations/003_row_security.sql",
    "imports.declared_roots<->requirements.txt",
)

UNDECIDABLE: Tuple[Callable[[], Check], ...] = (
    _unknown("sidecar-only", "canonical store read-only; agent writes are sidecar (§5)",
             "**this row's old evidence — 'there is no store, so the rule cannot "
             "be violated or demonstrated' — stopped being true on 2026-07-31.** "
             "There is one, and half the rule is now enforced: store/writing.py "
             "lands application writes as drafts and cannot spell 'sealed', the "
             "app role holds INSERT and SELECT and no UPDATE or DELETE, and "
             "migration 002 makes a sealed row rewritable by nobody. What is "
             "still unbuilt is the other half — nothing yet *promotes* a draft, "
             "because the seal is records/sealing.py's and S-3 wires it. So the "
             "cascade has a floor and no ceiling: rule 18 says that is a partial "
             "enforcement and not a pass, and this row stays UNKNOWN until a "
             "named human's seal is what moves a row"),
    _unknown("allowlist-rot", "allowlist rot tests (§16)",
             "no destination allowlist exists; §14 records the fleet-wide version "
             "as unique to UTETY"),
    _unknown("named-middles", "a named middle for every pair the app creates (§16)",
             f"not mechanically decidable. {len(NAMED_MIDDLES)} middles are named "
             "and tested (" + ", ".join(NAMED_MIDDLES) + "); "
             "whether that is *every* pair is a reading, not a check"),
)


CHECKS: Tuple[Callable[[], Check], ...] = (
    check_no_egress, check_write_paths, check_revocation_is_dated,
    check_suite_runs_standalone, check_ablation, check_exit_line,
    check_component_map, check_classification_registry,
    check_row_security_differential, check_knock_enforcing,
    check_declared_sockets, check_manifest, check_key_escrow,
    check_security_audit, check_stdlib_only, check_trust_root_committed,
    check_local_inference,
    check_anchor_payload, check_anchor_published, check_receipt_attribution,
    check_deposit_procedure,
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
    # **Rendered before the file is created, and the order is load-bearing.**
    # `render()` asks git whether the tree is dirty, and an empty record file
    # sitting untracked in `docs/conformance/` *is* a dirty tree — so calling
    # `render()` inside the `open("x")` block makes every record report dirty,
    # including the ones written from a clean checkout. That regression shipped
    # for exactly one run while TM-RACE-02 was being fixed; the discarded record
    # is not in the series and `test_write_reports_the_tree_it_found_not_the_one_it_made`
    # is why it cannot happen again.
    text = render(checks, at)
    # `if path.exists(): raise` then write was check-then-act, and the window
    # between them is exactly one second wide because the stamp has second
    # resolution — TM-RACE-02 in docs/SECURITY-AUDIT.md. `open("x")` is one
    # atomic O_EXCL create and raises the same FileExistsError, so append-only
    # stops being a convention two callers could step over.
    try:
        with path.open("x", encoding="utf-8") as fh:
            fh.write(text)
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
