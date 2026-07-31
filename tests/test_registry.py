"""The middle between the two enforcements of one mapping, shown to fail.

§9 item 2 said the class-to-`L` mapping was *written but unenforced*. It is now
enforced twice — `records/classify.py` runs the procedure, `migrations/001_lanes.sql`
seeds a `(class, rung)` per column — and two implementations with nothing between
them is the pair §16 forbids. `tools/registry.py` is the middle.

Every check here is pointed at the forbidden act rather than at the tree:
`tests/fixtures/decoys/registry_drift.sql` is a registry that has drifted seven
distinct ways, each of which reads as reasonable in isolation. A middle written
only against a seed that already agrees passes on the day it ships and every day
after, whether or not it works (`tests/test_sockets.py`'s argument, one subject
over).

**The three formerly-undecided rows are held below as decided.** They were a
real finding — `reconciled_session.declared`, `.observed` and `.diff` seeded
`L4` where the class derives `L3`, nothing recording which rule — until
2026-07-31, when the maintainer recorded the composition route. The pinning
assertions failed that day exactly as written, and were flipped to hold the
decision: the enumeration is what the build checks, and it grew by human act.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_registry.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import registry as R  # noqa: E402
from conform import State, check_classification_registry  # noqa: E402
from records.classify import Descriptor, classify  # noqa: E402
from records.rungs import Rung  # noqa: E402

DECOY = ROOT / "tests" / "fixtures" / "decoys" / "registry_drift.sql"

#: The elevation nobody has explained. Both values are carried here so a reader
#: of this file sees the finding without running anything (rule 17: the pair
#: comes from the seed, and the row count below is derived).
#: Was `UNEXPLAINED` — the three reconciled_session columns, pinned UNDECIDED
#: until 2026-07-31, when the maintainer recorded the composition route
#: (registry Route.COMPOSITION). Kept as the decided set so the flip is
#: visible in history rather than deleted.
DECIDED_BY_COMPOSITION = {
    ("reconciled_session", "declared"),
    ("reconciled_session", "observed"),
    ("reconciled_session", "diff"),
}


def _real() -> R.Reconciliation:
    return R.check()


def _decoy() -> R.Reconciliation:
    return R.check(schema=DECOY)


def _states(r):
    return {(j.table, j.column): j.agreement for j in r.judgements}


# --- the tree, reconciled --------------------------------------------------


def test_the_registry_and_the_procedure_agree_on_every_field_but_the_named_ones():
    """The verdict. Nothing here is a literal: the counts come from the file."""
    r = _real()
    assert r.verdict is R.Verdict.CLEAN, [str(f) for f in r.findings]
    assert not r.findings, [str(f) for f in r.findings]

    # `schema_text()`, not `SCHEMA`: the schema is every migration in filename
    # order and stopped being one file at 004. Reading 001 alone here compared a
    # reconciliation over 120 columns against a seed of 116 and failed for the
    # right reason on the wrong subject.
    sql = R.schema_text()
    seeded = R.classified(sql)
    declared = R.declared_columns(sql)
    assert len(r.judgements) == len(declared) == len(seeded), (
        len(r.judgements), len(declared), len(seeded))
    assert r.agreed + len(r.of(R.Agreement.UNDECIDED)) == len(r.judgements)


def test_the_session_columns_are_elevated_by_the_recorded_composition_rule():
    """**Was the pinned finding; decided 2026-07-31.** The three jsonb columns
    are `L4` with the class left `PII_MINOR`, by the composition rule the seed
    already applied to `lane_entry.payload` — recorded in the seed comment, in
    `Route.COMPOSITION`, and in §18 item 18's G-B. This test went red the day
    the elevation was recorded, exactly as its docstring promised, and now
    holds the decision: the three are ELEVATED with the rule named, and
    nothing is UNDECIDED."""
    r = _real()
    elevated = {(j.table, j.column) for j in r.of(R.Agreement.ELEVATED)}
    assert DECIDED_BY_COMPOSITION <= elevated
    assert not r.of(R.Agreement.UNDECIDED), [
        (j.table, j.column) for j in r.of(R.Agreement.UNDECIDED)]
    for j in r.of(R.Agreement.ELEVATED):
        if (j.table, j.column) in DECIDED_BY_COMPOSITION:
            assert "composition" in j.note.lower(), j.note

def test_the_ten_recorded_elevations_are_the_ones_the_seed_makes():
    """Both directions. Every enumerated elevation is elevated by the registry,
    and every elevation the registry makes is enumerated — an enumeration that
    could only grow would let a rung be raised with no rule named."""
    r = _real()
    elevated = {(j.table, j.column) for j in r.of(R.Agreement.ELEVATED)}
    assert elevated == set(R.ELEVATIONS), (
        f"only in the seed: {sorted(elevated - set(R.ELEVATIONS))}; "
        f"only in ELEVATIONS: {sorted(set(R.ELEVATIONS) - elevated)}")
    for j in r.of(R.Agreement.ELEVATED):
        assert j.derived == "L3" and j.seeded in ("L4", "L5"), j
        assert ("L5 rule 3" in j.note) or ("composition" in j.note.lower()), j.note


def test_every_recorded_route_reaches_the_rung_it_is_used_for():
    """An `L5` rule cannot justify an `L4`, and the clause cannot justify `L5` —
    which no purpose unlocks and no signature widens."""
    for key, e in sorted(R.ELEVATIONS.items()):
        assert R.REACHES[e.route] is e.rung, key
    assert R.REACHES[R.Route.CLAUSE] is Rung.L4
    assert set(R.REACHES) == set(R.Route)


# --- the leg to the document -----------------------------------------------


def test_the_bridge_derives_the_documented_rung_for_every_class():
    """`CLASS_FACTS` records what a class asserts about a field and no rungs.
    This is what stops it being a third copy: the rung comes out of
    `records/classify.py` and has to equal the document's table."""
    documented = R.documented_rungs(R.SENSITIVITY.read_text(encoding="utf-8"))
    assert set(documented) == set(R.CLASS_FACTS), (
        sorted(set(documented) ^ set(R.CLASS_FACTS)))
    assert not R.bridge(documented)
    for data_class, rung in sorted(documented.items()):
        assert str(R.derive("a_field", data_class).rung) == rung, data_class


def test_the_bridge_catches_the_document_moving_under_the_code():
    """A table row edited from `L3` to `L2` must fail here rather than silently
    re-classifying every `PII_MINOR` column in the seed."""
    findings = R.bridge({**R.documented_rungs(R.SENSITIVITY.read_text(encoding="utf-8")),
                         "PII_MINOR": "L2"})
    assert any(f.code == "bridge" and "PII_MINOR" in f.detail for f in findings), findings


def test_a_class_in_one_vocabulary_and_not_the_other_is_a_finding():
    findings = R.bridge({"PUBLIC": "L1"})
    assert any(f.code == "vocabulary" for f in findings), findings


def test_the_derived_anon_facts_carry_the_re_identification_caveat():
    """The class is *aggregates that survive the check*, not *aggregates*. The
    facts encode both halves, and flipping the second raises the rung — which is
    what makes the encoding a claim rather than a spelling."""
    facts = dict(R.CLASS_FACTS["DERIVED_ANON"])
    assert facts["passed_reidentification_check"] is True
    assert facts["derived_from"], "the class does not record that it is derived"
    unchecked = dict(facts, passed_reidentification_check=False)
    assert classify(Descriptor("a_field", **unchecked)).rung is Rung.L3
    assert classify(Descriptor("a_field", **facts)).rung is Rung.L2


# --- the middle routes through the procedure, not a lookup ------------------


def test_the_decided_field_name_cases_are_applied_and_not_bypassed():
    """`sis_legal_name` at `L4` is correct **because** it goes through
    `classify.py`. A middle that compared against the class table would report
    the legal record as an unexplained elevation, and would report a
    `chosen_name` elevated to `L4` as fine."""
    assert _states(_decoy())[("person", "sis_legal_name")] is R.Agreement.AGREES
    assert _states(_decoy())[("person", "chosen_name")] is R.Agreement.AGREES
    assert str(R.derive("sis_legal_name", "PII_MINOR").rung) == "L4"
    assert str(R.derive("chosen_name", "PII_MINOR").rung) == "L3"


# --- the checker can fail (rule 19) -----------------------------------------


def test_the_decoy_is_caught_row_by_row():
    """Every drift in the fixture, asserted by name. A checker that noticed one
    of them and reported the file would look identical from the verdict."""
    got = _states(_decoy())
    assert got[("person", "allergy_note")] is R.Agreement.DISAGREES
    assert got[("person", "safeguarding_note")] is R.Agreement.UNDECIDED
    assert got[("person", "chair_assignment")] is R.Agreement.UNDECIDED
    assert got[("person", "favourite_colour")] is R.Agreement.UNCLASSIFIED
    assert got[("person", "a_column_that_moved")] is R.Agreement.STALE
    assert got[("person", "chair")] is R.Agreement.AGREES


def test_a_rung_below_the_class_is_a_disagreement_and_not_an_elevation():
    """The asymmetry that makes elevation safe to permit. `HEALTH` served at
    `L3` is the direction a mistake discloses in, and no rule lowers a rung."""
    r = _decoy()
    bad = [f for f in r.findings if "allergy_note" in f.detail]
    assert bad and bad[0].code == "disagrees", r.findings
    assert "below what the class derives" in bad[0].detail


def test_an_unclassified_column_and_a_class_nobody_decided_are_different_facts():
    """Rule 13, twice. A column with no row is a build failure; a class the
    procedure cannot decide is `UNDECIDED` — and neither is a rung."""
    r = _decoy()
    assert [j.field for j in r.of(R.Agreement.UNCLASSIFIED)] == ["person.favourite_colour"]
    unknown = [j for j in r.of(R.Agreement.UNDECIDED)
               if j.column == "safeguarding_note"]
    assert unknown and unknown[0].derived is None, unknown
    assert "cannot classify" in unknown[0].note
    # Exactly these three codes. Asserted as a set rather than a membership:
    # dropping `unclassified` from what becomes a finding is silent otherwise,
    # and so is a `stale elevation` fired against a schema that never had one.
    assert {f.code for f in r.findings} == {"disagrees", "unclassified", "stale"}, \
        [str(f) for f in r.findings]


def test_an_elevation_with_no_recorded_rule_does_not_pass():
    r = _decoy()
    j = [x for x in r.judgements if x.column == "chair_assignment"][0]
    assert j.agreement is R.Agreement.UNDECIDED
    assert (j.seeded, j.derived) == ("L4", "L3")
    assert j.agreement is not R.Agreement.AGREES


def test_a_recorded_elevation_the_registry_stopped_making_is_a_finding():
    """The enumeration cannot outlive the seed it explains. Scoped to tables the
    file declares, so reconciling a partial schema does not report elevations it
    was never shown."""
    sql = R.SCHEMA.read_text(encoding="utf-8").replace(
        "('declination','subject_matter','PII_MINOR','L5'),",
        "('declination','subject_matter','PII_MINOR','L3'),")
    r = R.reconcile(sql, R.SENSITIVITY.read_text(encoding="utf-8"))
    assert any(f.code == "stale elevation" and "subject_matter" in f.detail
               for f in r.findings), r.findings


def test_the_middle_is_not_broken_shut():
    """Negative control. A checker that called everything a disagreement would
    pass every failure test above."""
    r = _real()
    assert r.of(R.Agreement.AGREES), "nothing agreed; the middle refuses everything"
    assert len(r.of(R.Agreement.AGREES)) > len(r.of(R.Agreement.UNDECIDED))
    assert not r.of(R.Agreement.DISAGREES)


# --- absence is not a clean bill (rule 13) ---------------------------------


def test_a_registry_that_cannot_be_parsed_is_vacuous_and_never_clean():
    with tempfile.TemporaryDirectory() as d:
        empty = Path(d) / "001_lanes.sql"
        empty.write_text("-- nothing here at all\n", encoding="utf-8")
        r = R.check(schema=empty)
        assert r.verdict is R.Verdict.VACUOUS and not r.ok
        assert r.findings and r.findings[0].code == "unreadable"


def test_a_missing_source_is_vacuous_and_never_clean():
    with tempfile.TemporaryDirectory() as d:
        r = R.check(schema=Path(d) / "nothing.sql")
        assert r.verdict is R.Verdict.VACUOUS and not r.ok


def test_a_document_whose_table_moved_out_of_reach_is_vacuous():
    """The third leg going missing must not read as two legs agreeing."""
    with tempfile.TemporaryDirectory() as d:
        doc = Path(d) / "SENSITIVITY.md"
        doc.write_text("# The ladder\n\nNo table here.\n", encoding="utf-8")
        r = R.check(doc=doc)
        assert r.verdict is R.Verdict.VACUOUS and not r.ok


# --- wired into the conformance record --------------------------------------


def test_the_conform_row_passes_on_the_merits_since_the_composition_call():
    """Rule 18: this is enforcement because CI routes through it. The row read
    `UNKNOWN` naming the three session fields until 2026-07-31; the maintainer
    recorded the composition rule and it now reads `PASS` — earned by a
    decision landing, not by a check softening, which is what this test's
    previous version was written to distinguish."""
    got = check_classification_registry()
    assert got.state is State.PASS, got
    # Derived, not quoted (rule 17). This assertion read `"116" in evidence`
    # until migration 004 seeded four columns and the number moved; a literal
    # here is a count in prose the code walks past, which is the defect rule 17
    # names and this file is otherwise careful about.
    seeded = len(R.classified(R.schema_text()))
    assert "0 undecided" in got.evidence or f"{seeded} field(s)" in got.evidence, \
        got.evidence


def test_the_conform_row_fails_on_the_decoy():
    got = check_classification_registry(schema=DECOY)
    assert got.state is State.FAIL
    assert "allergy_note" in got.evidence or "favourite_colour" in got.evidence


UNDECIDED_ONLY = """\
CREATE TABLE person (
    person_id uuid PRIMARY KEY,
    chair_assignment text
);
INSERT INTO field_classification (table_name, column_name, data_class, rung) VALUES
    ('person','person_id','PII_MINOR','L3'),
    ('person','chair_assignment','PII_MINOR','L4');
"""


def test_an_undecided_field_still_reads_unknown_not_pass():
    """The real tree stopped supplying an UNDECIDED case on 2026-07-31 (the
    composition call decided the last three), and the ablation harness
    noticed the same day: the mutation forcing UNDECIDED→PASS survived,
    because no input exercised the branch on a clean registry. So the branch
    gets a synthetic input with exactly one drift — an L4 elevation nothing
    records — and no FAIL-grade rows to mask it. This test is now what
    catches that mutation; a guard whose forbidden input the tree no longer
    produces still needs one from somewhere (rule 19)."""
    with tempfile.TemporaryDirectory() as d:
        schema = Path(d) / "undecided_only.sql"
        schema.write_text(UNDECIDED_ONLY, encoding="utf-8")
        got = check_classification_registry(schema=schema)
    assert got.state is State.UNKNOWN, got
    assert "person.chair_assignment" in got.evidence, got.evidence


def test_the_conform_row_is_unknown_when_there_is_nothing_to_read():
    with tempfile.TemporaryDirectory() as d:
        got = check_classification_registry(schema=Path(d) / "gone.sql")
        assert got.state is State.UNKNOWN and "missing" in got.evidence


def test_the_conform_row_can_pass():
    """A state nothing in this tree produces today, so it is produced here. A
    checker whose `PASS` branch has never run is a branch nobody has seen."""
    with tempfile.TemporaryDirectory() as d:
        sql = Path(d) / "001.sql"
        sql.write_text(
            "CREATE TABLE person (\n"
            "    person_id uuid PRIMARY KEY,\n"
            "    venue     text\n"
            ");\n"
            "INSERT INTO field_classification (table_name, column_name, data_class, rung)"
            " VALUES\n"
            "    ('person','person_id','PII_MINOR','L3'),\n"
            "    ('person','venue','PUBLIC','L1');\n",
            encoding="utf-8")
        got = check_classification_registry(schema=sql)
        assert got.state is State.PASS, got.evidence
        assert "2 field(s)" in got.evidence


# --- one parser, not two ----------------------------------------------------


def test_the_schema_reader_has_exactly_one_implementation():
    """The pair this file's subject is about, applied to the reader itself.
    `tests/test_lane_model.py` uses these functions; it must be the same objects
    and not a second copy that drifts in the direction where a phantom column
    reads as classified."""
    sys.path.insert(0, str(ROOT / "tests"))
    import test_lane_model as L  # noqa: E402

    for name in ("classified", "columns", "strip_comments", "tables"):
        assert getattr(L, name) is getattr(R, name), name


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
