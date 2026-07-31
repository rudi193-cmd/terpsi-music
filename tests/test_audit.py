"""R16 and R17, each pointed at a tree where it must complain.

Rule 19, and §10's version of it: *a guard that cannot be shown to fail has not
been shown to work.* Both of these checks report a comfortable answer against
this repository today — R16 `ABSENT` because there is nothing at rest yet, R17
`PASS` because the egress mutations are in the registry and the record says they
were caught. Neither of those answers is evidence of anything until the check
has been shown to produce the other ones.

So every branch of both checks is driven here against a synthetic tree, and the
one false positive that would quietly destroy R16 gets a test of its own:
`records/sealing.py` is called sealing and encrypts nothing.

**This file also carries the middle** for the pair `tools/audit.py` creates with
`docs/SECURITY-AUDIT.md` — a check and a document recording what the check said.
§16: name the reconciler in the same commit, or do not create the pair.
`test_the_document_records_what_the_checks_report_today` is that reconciler.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import audit  # noqa: E402
from audit import (  # noqa: E402
    AT_REST_VERBS, REQUIRED_EGRESS_SITES, Severity, Verdict, at_rest_seam,
    audit_commit, audit_date, egress_coverage, escrow_disposition, findings,
    r16_at_rest, r17_no_egress_neutralised, recorded, registry, record_rows,
)

AUDIT_DOC = ROOT / "docs" / "SECURITY-AUDIT.md"

#: A sealing module as it will look when the parallel work lands: the verbs,
#: and a body that does something to bytes.
SEALED = """\
def seal_at_rest(blob, dek):
    return bytes(b ^ 7 for b in blob)


def unseal_at_rest(blob, dek):
    return seal_at_rest(blob, dek)
"""

#: The same seam plus a store: something actually writes a record to disk,
#: which is the condition under which unescrowed sealing is the state that
#: ends a program (S1) rather than a mechanism ahead of its store (S2).
SEALED_AND_WRITING = SEALED + """\

def persist(path, blob, dek):
    with open(path, "wb") as f:
        f.write(seal_at_rest(blob, dek))
"""

ESCROW_OK = """\
# Escrow

Split 3-of-5 across the director, the district administrator and a sealed
offline share. Rehearsed 2026-06-01; next drill 2027-06-01.
"""


def _tree(d, files):
    p = Path(d)
    for name, text in files.items():
        (p / name).write_text(text, encoding="utf-8")
    return p


# --- R16: the false positive it exists to refuse ---------------------------


def test_the_human_seal_is_not_at_rest_sealing():
    """**The whole reason R16 matches on verbs and not on filenames.**

    `records/sealing.py` is in this tree, is named sealing, and is rule 10's
    named-human seal over a machine draft — `hashlib`, no cipher, nothing
    encrypted. A check keying on the module name reports PASS today over a
    store that does not exist yet, which is the most flattering possible wrong
    answer.
    """
    real = ROOT / "records" / "sealing.py"
    assert real.exists(), "the decoy for this test is the real module; it moved"
    # Asserted per-file since 2026-07-31: a true seam (records/atrest.py) now
    # exists in the tree, so "the directory scan finds nothing" stopped being
    # the property. The property is and was: the human seal, alone, matches no
    # verb — and the true seam is recognised (the test below this one).
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(real, Path(d) / "sealing.py")
        assert not at_rest_seam(Path(d)), (
            "records/sealing.py satisfied R16 — the check is matching on a name"
        )
    assert "seal" not in AT_REST_VERBS, (
        "the bare verb `seal` is in the required set, so the human seal counts"
    )


def test_a_real_sealing_module_is_found():
    """The other direction: the seam is recognised when something lands on it.
    A check that never finds anything is indistinguishable from a broken one."""
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"atrest.py": SEALED})
        got = at_rest_seam(p)
    assert {v for _, v in got} == {"seal_at_rest", "unseal_at_rest"}, got


# --- R16: every branch --------------------------------------------------------


def test_nothing_stored_and_nothing_sealing_is_absent_not_a_pass():
    """Rule 13. Nothing is at rest, so nothing is unencrypted — and that is a
    different fact from encryption being present."""
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"quiet.py": "X = 1\n"})
        got = r16_at_rest(records=p, escrow=p / "nope.md")
    assert got.verdict is Verdict.ABSENT and not got.passed
    assert got.condition, "an ABSENT with no condition never becomes applicable"


def test_a_store_with_no_sealing_is_a_high_finding():
    """The commit this check is written for: something starts writing records
    to a disk and no sealing arrives with it."""
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"store.py": "def save(p, t):\n    p.write_text(t)\n"})
        got = r16_at_rest(records=p, escrow=p / "nope.md")
    assert got.verdict is Verdict.FINDING and got.severity is Severity.S1
    assert "no at-rest sealing" in got.evidence


def test_sealing_without_escrow_is_a_high_finding_once_anything_is_at_rest():
    """§5: *a single file loss destroys every secret in the box, irrecoverably,
    by design.* Sealed and unescrowed is the state that ends a program — once
    a record is actually at rest for the key to strand."""
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"atrest.py": SEALED_AND_WRITING})
        got = r16_at_rest(records=p, escrow=p / "nope.md")
    assert got.verdict is Verdict.FINDING and got.severity is Severity.S1
    assert "escrow" in got.evidence.lower()


def test_a_seam_ahead_of_its_store_is_a_finding_not_yet_a_high_one():
    """The mechanism-before-store ordering this repo builds by (item 4 note
    iii). No master minted, nothing at rest — a lost key file cannot destroy
    records that do not exist, so the severity is S2 with the S1 condition
    named on the finding itself. Went red on F3's merge until the check
    honoured its own stated condition."""
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"atrest.py": SEALED})
        got = r16_at_rest(records=p, escrow=p / "nope.md")
    assert got.verdict is Verdict.FINDING and got.severity is Severity.S2
    assert "S1" in got.condition


def test_sealing_with_a_rehearsed_split_passes():
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"atrest.py": SEALED, "ESCROW.md": ESCROW_OK})
        got = r16_at_rest(records=p, escrow=p / "ESCROW.md")
    assert got.verdict is Verdict.PASS, got.evidence
    assert "3-of-5" in got.evidence


def test_an_unrehearsed_escrow_plan_is_not_escrow():
    """§5 states the rule this branch is: *an untested key recovery is not
    escrow.* A document describing a split nobody has ever reconstructed is a
    plan, and R16 must not accept it as a disposition."""
    with tempfile.TemporaryDirectory() as d:
        p = _tree(d, {"atrest.py": SEALED,
                      "ESCROW.md": "Split 2-of-3 across the director and two others.\n"})
        disposed, why = escrow_disposition(p / "ESCROW.md")
        got = r16_at_rest(records=p, escrow=p / "ESCROW.md")
    assert not disposed and "rehears" in why.lower()
    assert got.verdict is Verdict.FINDING


def test_a_missing_escrow_document_says_so_rather_than_passing():
    disposed, why = escrow_disposition(ROOT / "docs" / "does-not-exist.md")
    assert not disposed and "does not exist" in why


# --- R17: the registry half ---------------------------------------------------


def test_the_real_registry_covers_every_egress_detection_site():
    """The positive result, derived rather than asserted: read the table out of
    `tests/ablate.py` and confirm each way the egress checker detects egress has
    a mutation against it."""
    coverage = egress_coverage(registry())
    uncovered = [site for site, labels in coverage.items() if not labels]
    assert not uncovered, f"no mutation ablates: {uncovered}"
    assert len(coverage) == len(REQUIRED_EGRESS_SITES)


def test_a_registry_missing_an_egress_mutation_is_a_finding():
    """**The load-bearing test.** R17's claim is not *there are mutations* — it
    is *each detection path is individually shown to fail*, and a registry can
    grow while one site quietly loses its only row."""
    rows = [r for r in registry() if "_DYNAMIC" not in r[1]]
    coverage = egress_coverage(rows)
    assert [s for s, labels in coverage.items() if not labels], (
        "dropping the dynamic-import mutation left the coverage map full"
    )

    with tempfile.TemporaryDirectory() as d:
        thin = Path(d) / "ablate.py"
        thin.write_text(
            "MUTATIONS = [\n"
            '    ("records/rungs.py", "a", "b", "unrelated", "tests/test_rungs.py"),\n'
            "]\n", encoding="utf-8")
        got = r17_no_egress_neutralised(reg=thin)
    assert got.verdict is Verdict.FINDING and got.severity is Severity.S1
    assert "egress detection site" in got.evidence


def test_no_registry_at_all_is_absent():
    with tempfile.TemporaryDirectory() as d:
        got = r17_no_egress_neutralised(reg=Path(d) / "gone.py")
    assert got.verdict is Verdict.ABSENT and not got.passed


def test_the_registry_is_read_by_ast_and_not_by_grep():
    """A mutation table quoted in a docstring is not a mutation table. Parsing
    is what tells the difference, and this asserts the parse actually happened
    rather than a substring search having got lucky."""
    rows = registry()
    assert rows and all(len(r) == 5 for r in rows), "MUTATIONS is not 5-tuples"
    assert all(isinstance(part, str) for r in rows for part in r)


# --- R17: the conformance-record half -----------------------------------------


def test_a_record_reporting_a_failed_ablation_is_a_finding():
    """The half §10 says has been breaking. The registry can be complete and
    the harness can still be reporting that a mutation survived — and R17 must
    read the report rather than the intention."""
    with tempfile.TemporaryDirectory() as d:
        rec = Path(d)
        (rec / "2026-07-31T000000Z.md").write_text(
            "| | check | guarantee | evidence |\n|---|---|---|---|\n"
            "| **PASS** | `no-egress` | core purity | 19 modules |\n"
            "| **FAIL** | `ablation` | rule 19 | a guard survived |\n",
            encoding="utf-8")
        got = r17_no_egress_neutralised(records=rec)
    assert got.verdict is Verdict.FINDING and got.severity is Severity.S1
    assert "ablation=FAIL" in got.evidence


def test_a_record_missing_the_egress_row_is_a_finding():
    """A row that is absent and a row that says PASS are different facts."""
    with tempfile.TemporaryDirectory() as d:
        rec = Path(d)
        (rec / "2026-07-31T000000Z.md").write_text(
            "| **PASS** | `ablation` | rule 19 | all guards red |\n",
            encoding="utf-8")
        got = r17_no_egress_neutralised(records=rec)
    assert got.verdict is Verdict.FINDING
    assert "no-egress=no row" in got.evidence


def test_no_conformance_record_is_unknown_not_a_pass():
    with tempfile.TemporaryDirectory() as d:
        got = r17_no_egress_neutralised(records=Path(d))
    assert got.verdict is Verdict.UNKNOWN and not got.passed


def test_the_newest_record_is_the_one_read():
    """Records are dated, never overwritten, and a check reading an arbitrary
    one of them would answer *did it ever conform* rather than *does it*."""
    with tempfile.TemporaryDirectory() as d:
        rec = Path(d)
        (rec / "2026-01-01T000000Z.md").write_text(
            "| **FAIL** | `ablation` | x | old |\n", encoding="utf-8")
        (rec / "2026-07-31T000000Z.md").write_text(
            "| **PASS** | `ablation` | x | new |\n", encoding="utf-8")
        newest, states = record_rows(rec)
    assert newest.name == "2026-07-31T000000Z.md" and states["ablation"] == "PASS"


# --- the document, and the middle ---------------------------------------------


def test_the_document_records_what_the_checks_report_today():
    """**The reconciler** (§16, rule 12). `tools/audit.py` computes R16 and R17;
    `docs/SECURITY-AUDIT.md` records them. That is a pair, and a pair without a
    middle is how this fleet has lost four out of four. This is the middle: the
    recorded verdict and the live one, compared, in the same commit that made
    them two things.
    """
    text = AUDIT_DOC.read_text(encoding="utf-8")
    said = recorded(text)
    for result in audit.run():
        assert result.id in said, f"{result.id} is not recorded in {AUDIT_DOC.name}"
        assert said[result.id] == result.verdict.value, (
            f"{result.id}: the document says {said[result.id]}, the check says "
            f"{result.verdict.value} — one of them is out of date"
        )


def test_the_tally_matches_the_table():
    """Rule 17 turned on the document itself.

    The summary line is a count of the table three screens above it, which is
    exactly the shape that goes stale — a row's verdict changes and the sentence
    describing the table keeps its old arithmetic. The first version of this
    document shipped with the wrong figure in it, which is why this test exists
    rather than a proofread.
    """
    import re

    text = AUDIT_DOC.read_text(encoding="utf-8")
    m = re.search(
        r"\*\*Tally: (\d+) pass, (\d+) findings?, (\d+) not-applicable, "
        r"(\d+) absent, (\d+) unknown, of\s+(\d+)\s*\n?checks\*\*", text)
    assert m, "no tally line in the shape this test can read"
    said = dict(zip(("PASS", "FINDING", "NOT-APPLICABLE", "ABSENT", "UNKNOWN"),
                    (int(g) for g in m.groups()[:5])))
    table = recorded(text)
    for verdict, claimed in said.items():
        actual = sum(1 for v in table.values() if v == verdict)
        assert actual == claimed, (
            f"the tally says {claimed} {verdict}, the table has {actual}"
        )
    assert int(m.group(6)) == len(table), "the total does not match the row count"


def test_the_findings_summary_is_derived():
    """The other count in this document that describes this document."""
    import re

    text = AUDIT_DOC.read_text(encoding="utf-8")
    m = re.search(r"\*Findings: (\d+) recorded, (\d+) closed, (\d+) open\*", text)
    assert m, "no findings summary in the shape this test can read"
    got = findings(text)
    assert len(got) == int(m.group(1)), "recorded count is wrong"
    assert sum(1 for f in got if not f.open) == int(m.group(2)), "closed count is wrong"
    assert sum(1 for f in got if f.open) == int(m.group(3)), "open count is wrong"


def test_the_document_records_all_seventeen_checks():
    said = recorded(AUDIT_DOC.read_text(encoding="utf-8"))
    missing = [f"R{n}" for n in range(1, 18) if f"R{n}" not in said]
    assert not missing, f"no verdict recorded for {missing}"


def test_no_check_is_silently_passed():
    """Rule 13 at the level of the document. `NOT-APPLICABLE` and `ABSENT` are
    legitimate answers and neither is `PASS`; what is not legitimate is a check
    that could not run being recorded as one that ran."""
    said = recorded(AUDIT_DOC.read_text(encoding="utf-8"))
    allowed = {v.value for v in Verdict}
    strange = {k: v for k, v in said.items() if v not in allowed}
    assert not strange, f"verdicts outside the vocabulary: {strange}"


def test_every_not_applicable_carries_the_condition_that_ends_it():
    """A `NOT-APPLICABLE` with no condition is a check quietly retired. §16's
    tombstone rule, at the scale of a table row."""
    text = AUDIT_DOC.read_text(encoding="utf-8")
    bad = []
    for line in text.splitlines():
        if "**NOT-APPLICABLE**" in line or "**ABSENT**" in line:
            if "applies when" not in line.lower():
                bad.append(line.split("|")[1].strip())
    assert not bad, f"no re-entry condition recorded for: {bad}"


def test_the_document_carries_a_date_and_a_commit_pin():
    text = AUDIT_DOC.read_text(encoding="utf-8")
    assert audit_date(text), "no date; the gate cannot judge staleness"
    assert audit_commit(text), "no commit pin; the audit does not say what it read"


def test_an_open_high_finding_is_visible_to_the_parser():
    """The parser is what the gate rests on, so point it at a finding table
    holding the thing that must fail a build."""
    got = findings(
        "| `TM-XXX-01` | R9 | `S1` | open | it is bad |\n"
        "| `TM-XXX-02` | R9 | `S2` | closed 2026-07-31 | it was bad |\n")
    assert len(got) == 2
    assert got[0].open and got[0].severity is Severity.S1
    assert not got[1].open


def test_a_status_nobody_updated_reads_as_open():
    """The default direction. A finding whose status went blank must not read
    as resolved — that is the failure mode that makes an audit flattering."""
    got = findings("| `TM-XXX-03` | R9 | `S2` | needs a decision | x |\n")
    assert got and got[0].open


# --- the checker's own posture ------------------------------------------------


def test_the_checker_parses_and_never_imports_what_it_inspects():
    """Same rule `tests/test_purity.py`, `tests/test_sockets.py` and
    `tests/test_discipline.py` hold their checkers to. Executing a module to
    find out whether it reaches the network is how you find out by doing it."""
    import ast

    banned = {"exec", "eval", "__import__", "import_module", "runpy"}
    tree = ast.parse((ROOT / "tools" / "audit.py").read_text(encoding="utf-8"))
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            called.add(f.attr if isinstance(f, ast.Attribute)
                       else getattr(f, "id", ""))
    assert not (called & banned), f"tools/audit.py calls {sorted(called & banned)}"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
