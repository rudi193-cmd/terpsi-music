"""§9 item 10: the aggregate as a gated, announced, suppressed export.

The acceptance case is §18 item 14's own worked harm — *"one student in this
section carries an auto-injector"*, a count of 1 over a section of three — and
it appears here three times: as the small cell that must not be published, as
the residual that must not be recoverable by subtraction, and as the input that
must not be dropped when a lane cannot be read.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import csv
import dataclasses
import io
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Rung  # noqa: E402
from records.aggregate import (Aggregate, AggregateRequest, Audience,  # noqa: E402
                               CellFloor, CellState, Gate, NotGated, Read,
                               Reading, differencing_risk, release)
from records.aggregate import (_descriptor_for, _determined,  # noqa: E402
                               _many_lanes, _suppress)
from records.classify import Decision, classify  # noqa: E402
from records.conflict import NotComputable  # noqa: E402
from records.disclosure import Ledger  # noqa: E402
from records.export import verify  # noqa: E402
from records.practice import Session, own  # noqa: E402
from records.serving import Outcome  # noqa: E402

AT = datetime(2026, 7, 31, 9, 0)
WHO = "Dana Whitfield"


def floor(k=5):
    return CellFloor(k, "district data governance office", "2026.1",
                     "state education agency")


def ask(k=5, audience=Audience.BOOSTER, dimension="section",
        population="the 2026 marching ensemble"):
    return AggregateRequest("season participation report for the booster board",
                            audience, dimension, population, floor(k), WHO, AT)


def rows(cell, n, rung=Rung.L4, **kw):
    """`n` lanes contributing to one cell. One lane per student, W-1."""
    return [Reading(f"lane-{cell}-{i}", f"student-{cell}-{i}", cell, rung, **kw)
            for i in range(n)]


def made(readings, k=5, **kw):
    return release(ask(k=k, **kw), readings, into=Ledger())


def named(rel, name):
    return next(a for a in rel.artifacts if a.name == name)


def table(rel):
    """`{cell: (state, count-or-None)}` read back out of the rendered CSV."""
    got = list(csv.reader(io.StringIO(named(rel, "cells.csv").text)))
    assert got[0] == ["cell", "state", "count", "rung"]
    return {r[0]: (r[1], int(r[2]) if r[2] else None) for r in got[1:]}


#: The worked harm, as data. Three sections; the trumpet section has three
#: members and one of them carries an auto-injector.
def auto_injector():
    return rows("trumpet", 1) + rows("flute", 6) + rows("drums", 7)


# --- the gate's legitimacy conditions --------------------------------------


def test_an_aggregate_with_nowhere_to_announce_is_not_issued():
    """Rule 9's whole point: the harm is data leaving. An export nobody
    recorded is the one that cannot be answered for afterwards."""
    try:
        release(ask(), auto_injector(), into=None)
    except NotGated as exc:
        assert "announced" in str(exc)
        return
    raise AssertionError("an unannounced aggregate was issued")


def test_an_aggregate_over_no_readings_is_refused_rather_than_a_table_of_zeros():
    try:
        made([])
    except NotGated as exc:
        assert "no readings" in str(exc)
        return
    raise AssertionError("an aggregate over nothing produced a table")


def test_a_count_over_enforcement_content_is_refused():
    """`L5` is never rendered to anyone under any grant, and a count derived
    from the content of an enforced restriction is a rendering of it."""
    try:
        made(rows("trumpet", 6) + rows("drums", 6, rung=Rung.L5))
    except NotGated as exc:
        assert "L5" in str(exc)
        return
    raise AssertionError("an aggregate was drawn over enforcement content")


def test_an_aggregate_over_one_lane_is_that_students_record_with_a_table_round_it():
    try:
        made(rows("trumpet", 1))
    except NotGated as exc:
        assert "one lane" in str(exc)
        return
    raise AssertionError("a one-lane aggregate was issued")


def test_a_public_release_is_refused_because_nothing_here_sees_the_union():
    """Suppression has to be computed once over everything that will ever be
    published, and this module cannot see that set."""
    try:
        made(auto_injector(), audience=Audience.PUBLIC)
    except NotGated as exc:
        assert "public" in str(exc)
        return
    raise AssertionError("a public release was issued")


def test_an_aggregate_declares_a_purpose():
    for bad in ("", "   "):
        try:
            AggregateRequest(bad, Audience.BOOSTER, "section", "the ensemble",
                             floor(), WHO, AT)
        except ValueError as exc:
            assert "purpose" in str(exc)
            continue
        raise AssertionError(f"a purposeless aggregate was accepted: {bad!r}")


def test_an_aggregate_names_who_asked_and_what_population():
    for kw in ({"requested_by": ""}, {"population": " "}):
        base = dict(purpose="p", audience=Audience.BOOSTER, dimension="section",
                    population="the ensemble", floor=floor(), requested_by=WHO, at=AT)
        base.update(kw)
        try:
            AggregateRequest(**base)
        except ValueError:
            continue
        raise AssertionError(f"an unattributed aggregate was accepted: {kw}")


def test_a_cell_per_student_is_a_disclosure_with_a_table_around_it():
    for bad in ("student", "Students", "lane", "person", "ward"):
        try:
            ask(dimension=bad)
        except ValueError as exc:
            assert "not a dimension" in str(exc)
            continue
        raise AssertionError(f"{bad!r} was accepted as a dimension")


def test_a_cross_tab_is_refused_rather_than_suppressed_to_death():
    """*"A general engine will spend its life returning suppressed — and the
    one time it returns a number, that number is the disclosure."*"""
    for bad in ("section, grade", "section × grade", "section x grade"):
        try:
            ask(dimension=bad)
        except ValueError as exc:
            assert "more than one dimension" in str(exc)
            continue
        raise AssertionError(f"{bad!r} was accepted as one dimension")


# --- the threshold is a policy input ---------------------------------------


def test_there_is_no_default_threshold():
    """A `k` with a default is a number this repository cannot source
    (`scout-23`: the authoritative guidance returned HTTP 403, and rule 17
    says do not quote what you did not derive)."""
    try:
        CellFloor()
    except TypeError:
        pass
    else:
        raise AssertionError("CellFloor has a default k")
    src = (Path(__file__).resolve().parent.parent / "records" / "aggregate.py"
           ).read_text(encoding="utf-8")
    assert "k: int" in src and "k: int =" not in src


def test_a_threshold_that_cannot_suppress_is_not_a_threshold():
    for k in (-1, 0, 1):
        try:
            CellFloor(k, "office", "1", "state")
        except ValueError as exc:
            assert "suppresses nothing" in str(exc)
            continue
        raise AssertionError(f"k={k} was accepted")


def test_a_threshold_travels_with_its_publisher_version_and_jurisdiction():
    for kw in ({"publisher": ""}, {"version": " "}, {"jurisdiction": ""}):
        base = dict(k=5, publisher="office", version="1", jurisdiction="state")
        base.update(kw)
        try:
            CellFloor(**base)
        except ValueError as exc:
            assert "travel together" in str(exc)
            continue
        raise AssertionError(f"an unattributed threshold was accepted: {kw}")


def test_the_threshold_and_its_source_are_printed_for_the_reader():
    rel = made(auto_injector())
    for art in ("README.txt", "MANIFEST.txt"):
        assert "district data governance office" in named(rel, art).text
        assert "k=5" in named(rel, art).text


# --- multi-lane legitimacy, and the one-lane rule it must not weaken --------


def test_the_one_lane_rule_still_refuses_the_ungated_path():
    """`practice._one_lane` is untouched. An aggregate does not get to reuse
    that door; it gets its own, and the token is the difference."""
    sessions = [Session("lane-a", "student-a", AT.date(), 30),
                Session("lane-b", "student-b", AT.date(), 30)]
    try:
        own(sessions)
    except NotComputable as exc:
        assert "students" in str(exc)
        return
    raise AssertionError("a cross-lane practice statistic was computed")


def test_the_cross_lane_read_cannot_be_reached_without_the_gates_token():
    for token in (None, object(), "gate"):
        try:
            _many_lanes(auto_injector(), token)
        except NotGated as exc:
            assert "token" in str(exc)
            continue
        raise AssertionError(f"a cross-lane read went through with {token!r}")


def test_a_hand_built_gate_cannot_skip_the_conditions():
    """A `Gate` a caller constructed is the side door I-10 says the seam is
    not, so the conditions are re-checked by the type."""
    for kw in (dict(lanes=("lane-a",), ceiling=Rung.L2),
               dict(lanes=("lane-a", "lane-b"), ceiling=Rung.L4)):
        try:
            Gate(ask(), **kw)
        except NotGated:
            continue
        raise AssertionError(f"a hand-built gate was accepted: {kw}")


def test_an_aggregate_reads_every_contributing_lane():
    rel = made(auto_injector())
    assert len(rel.lanes) == 14
    assert len(set(rel.lanes)) == len(rel.lanes)


# --- suppression case 1: the small cell ------------------------------------


def test_the_worked_harm_never_reaches_the_artifact():
    """§18 item 14: *"one student in this section carries an auto-injector"*
    names nobody and identifies a child if the section has three members."""
    rel = made(auto_injector(), k=5)
    assert table(rel)["trumpet"] == ("suppressed", None)
    for cell, (state, count) in table(rel).items():
        if count is not None:
            assert count >= 5, f"{cell} published a count below the threshold"


def test_every_published_count_is_at_or_above_the_threshold():
    """The invariant, over a table with a cell at each interesting size."""
    for k in (2, 3, 5, 9):
        rel = made(rows("a", 1) + rows("b", 2) + rows("c", 8) + rows("d", 11), k=k)
        for cell, (_, count) in table(rel).items():
            assert count is None or count >= k, f"k={k}: {cell} leaked {count}"


def test_a_cell_nobody_is_in_is_absent_rather_than_a_published_zero():
    """Cells come from the readings, so a section with nobody in it produces no
    cell. Rendering it as `0` would be inventing a number — and a published `0`
    over a named cell is a statement about every member of that cell, which is
    §7's guarantee failing from the other side."""
    rel = made(rows("trumpet", 8) + rows("flute", 0) + rows("drums", 9), k=5)
    assert "flute" not in table(rel), "a cell with no members was invented"
    assert table(rel)["trumpet"][1] == 8


def test_a_zero_a_caller_does_supply_is_below_every_threshold():
    """`release()` cannot produce a zero cell, but `_suppress` is the rule and
    the rule has to hold for one — otherwise the day a caller counts a
    population rather than an attribute, `0 < k` is the branch that is not
    there."""
    state, settled = _suppress({"a": 0, "b": 9, "c": 11}, floor(5))
    assert settled
    assert state["a"] is not CellState.RELEASED


def test_a_suppressed_cell_is_named_and_counted_never_silently_dropped():
    """`records/export.py`'s `L5` handling is the model: a record that does not
    travel is reported by name and count rather than quietly omitted."""
    rel = made(auto_injector())
    man = named(rel, "MANIFEST.txt").text
    assert "suppressed:  2" in man
    assert "WITHHELD GROUPS" in man
    for c in rel.suppressed:
        assert c.key in man
        assert c.key in table(rel), "a suppressed cell vanished from the table"


def test_the_manifest_counts_cells_and_never_students():
    """A total is a number about people, and a manifest that reports one hands
    back what the suppression withheld."""
    rel = made(auto_injector())
    man = named(rel, "MANIFEST.txt").text
    assert "cells:       3" in man
    for total in ("14", "total:", "students:", "population size"):
        assert total not in man.split("FILES")[0], f"the manifest reports {total!r}"


def test_which_suppression_applied_to_which_cell_is_not_attributed():
    """The reason is itself a bound on the withheld number: a complementary
    suppression says the cell is at or above `k`, a small-cell one says it is
    below. Naming which is which hands half of it back."""
    rel = made(auto_injector(), k=5)
    assert {c.state for c in rel.suppressed} == {
        CellState.SUPPRESSED_SMALL, CellState.SUPPRESSED_COMPLEMENT}
    for art in rel.artifacts:
        assert CellState.SUPPRESSED_SMALL.value not in art.text
        assert CellState.SUPPRESSED_COMPLEMENT.value not in art.text
    assert {s for s, _ in table(rel).values() if s != "released"} == {"suppressed"}


# --- suppression case 2: the complement ------------------------------------


def test_a_lone_suppressed_cell_is_recoverable_and_so_a_second_is_suppressed():
    """The part naive implementations skip. Publishing flute and drums with a
    countable total gives trumpet away by subtraction."""
    rel = made(auto_injector(), k=5)
    assert rel.state is Aggregate.RELEASED
    assert len(rel.suppressed) == 2, "one suppressed cell is one subtraction away"
    assert table(rel)["flute"] == ("suppressed", None), \
        "a cell of 6 survived a threshold of 5 while trumpet stood alone"
    assert table(rel)["drums"] == ("released", 7)


def test_a_suppressed_cell_is_never_the_only_one():
    """The invariant behind the case above, over several shapes."""
    for readings in (rows("a", 1) + rows("b", 9) + rows("c", 9),
                     rows("a", 4) + rows("b", 20) + rows("c", 21) + rows("d", 30),
                     rows("a", 0) + rows("b", 7) + rows("c", 8)):
        rel = made(readings, k=5)
        if rel.suppressed and rel.state is Aggregate.RELEASED:
            assert len(rel.suppressed) >= 2, f"one lonely suppression in {readings[0].cell}"


def test_a_residual_of_zero_determines_every_suppressed_cell_at_once():
    """Two suppressed cells are not enough when the published cells account for
    the whole total: the reader knows both are zero. Reached through `_suppress`
    because `release()` cannot build a zero cell — see the test above."""
    state, settled = _suppress({"a": 0, "b": 0, "c": 9, "d": 11}, floor(5))
    assert settled
    assert state["c"] is CellState.SUPPRESSED_COMPLEMENT, \
        "a and b are both zero against the published total, and nothing moved"
    assert state["d"] is CellState.RELEASED, "the pass suppressed more than it had to"


def test_a_table_that_cannot_reach_a_fixpoint_is_unreleasable():
    """Three cells of one each with `k=2`: every cell is determined and there is
    nothing left to suppress. Publishing anything gives all three away."""
    rel = made(rows("a", 1) + rows("b", 1) + rows("c", 1), k=2)
    assert rel.state is Aggregate.UNRELEASABLE
    assert not rel.released
    assert all(count is None for _, count in table(rel).values())


def test_the_interval_check_names_its_two_cases():
    """`_determined` directly, so the arithmetic is tested rather than inferred
    from a table that happens to exercise it."""
    assert _determined(3, [4]), "one suppressed cell against a known total"
    assert _determined(0, [4, 4]), "a residual of zero pins every cell"
    assert not _determined(3, [4, 4]), "[0,3] over two cells is not a number"
    assert _determined(2, [1, 1]), "k=2 with a residual of 2 makes both a 1"
    assert not _determined(7, [4, 7]), "a complement cell widens the interval"
    assert not _determined(5, [])


# --- suppression case 3: an input that could not be read -------------------


def test_an_unreadable_lane_stops_every_count_rather_than_shrinking_one():
    """The subtlest failure in aggregation: dropping the row leaves a smaller
    number that looks complete, and the reader has no way to tell."""
    unreadable = Reading("lane-x", "student-x", "drums", Rung.L4,
                         state=Read.UNREADABLE, why="the lane's key is unavailable")
    rel = made(rows("trumpet", 6) + rows("flute", 7) + rows("drums", 6) + [unreadable])
    assert rel.state is Aggregate.INCOMPLETE
    assert not rel.released, "a count survived an incomplete population"
    assert all(count is None for _, count in table(rel).values())
    assert table(rel)["drums"][0] == "incomplete"
    for n in ("6", "7"):
        assert f",{n}," not in named(rel, "cells.csv").text


def test_the_affected_cell_is_marked_and_says_why():
    unreadable = Reading("lane-x", "student-x", "drums", Rung.L4,
                         state=Read.UNREADABLE, why="the lane's key is unavailable")
    rel = made(rows("trumpet", 6) + rows("flute", 7) + [unreadable])
    assert [c.key for c in rel.incomplete] == ["drums", "flute", "trumpet"]
    assert "the lane's key is unavailable" in named(rel, "MANIFEST.txt").text
    assert "UNAVAILABLE GROUPS" in named(rel, "MANIFEST.txt").text


def test_an_unreadable_lane_that_cannot_name_its_cell_makes_the_whole_thing_unknown():
    """No cell to mark and no total to stand on. Rule 13: unavailable, not
    empty."""
    blind = Reading("lane-x", "student-x", None, Rung.L4,
                    state=Read.UNREADABLE, why="the lane could not be reached")
    rel = made(rows("trumpet", 6) + rows("flute", 7) + [blind])
    assert rel.state is Aggregate.UNKNOWN
    assert not rel.released
    assert "unavailable one" in named(rel, "README.txt").text
    assert "This is not an" in named(rel, "README.txt").text


def test_an_unreadable_reading_says_why_it_could_not_be_read():
    try:
        Reading("lane-x", "student-x", "drums", Rung.L4, state=Read.UNREADABLE)
    except ValueError as exc:
        assert "rule 13" in str(exc)
        return
    raise AssertionError("an absence with no reason was accepted")


def test_a_reading_that_was_read_names_the_cell_it_falls_in():
    """An unnamed cell is an unreadable one and has its own state; letting a
    read reading carry no cell would give absence a second, quieter spelling."""
    for cell in (None, "   "):
        try:
            Reading("lane-x", "student-x", cell, Rung.L4)
        except ValueError as exc:
            assert "unreadable one" in str(exc)
            continue
        raise AssertionError(f"a read reading with cell={cell!r} was accepted")


def test_an_input_below_the_verified_tier_is_not_dropped_either():
    """I-10: *"exports are treaty-scoped, drawn from verified-tier records
    only, and the seam is not a side door."* Excluding a `P4` row would make the
    count smaller and leave it looking complete, so it marks the cell instead."""
    rel = made(rows("trumpet", 6) + rows("flute", 7) + rows("drums", 6, provenance="P4"))
    assert rel.state is Aggregate.INCOMPLETE
    assert not rel.released
    assert Reading("l", "s", "c", Rung.L4, provenance="P1").verified_tier
    assert Reading("l", "s", "c", Rung.L4, provenance="P2").verified_tier
    for weak in ("P3", "P4", "P5"):
        assert not Reading("l", "s", "c", Rung.L4, provenance=weak).verified_tier


def test_a_provenance_that_is_not_on_the_ladder_is_refused():
    """Rule 14: no scale is addressed as a bare integer or an invented word."""
    for bad in ("3", "high", "P9"):
        try:
            Reading("l", "s", "c", Rung.L4, provenance=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as a provenance rung")


# --- DERIVED_ANON through the real classifier ------------------------------


def test_a_released_cell_serves_at_L2_and_the_classifier_is_what_said_so():
    rel = made(auto_injector(), k=5)
    drums = next(c for c in rel.cells if c.key == "drums")
    assert drums.rung is Rung.L2
    got = classify(_descriptor_for("drums", (Rung.L4,) * 7, True))
    assert got.decision is Decision.DECIDED and got.rung is Rung.L2
    assert drums.why == got.reason


def test_a_suppressed_cell_inherits_the_max_of_its_inputs_until_the_check_passes():
    """The class table has always said so; §18 item 14 is that the numbered
    steps did not, and `classify.py` step 2a is the gate."""
    rel = made(auto_injector(), k=5)
    trumpet = next(c for c in rel.cells if c.key == "trumpet")
    assert trumpet.rung is Rung.L4, "a suppressed health cell reached L2"
    assert "re-identification check has not passed" in trumpet.why
    assert classify(_descriptor_for("trumpet", (Rung.L4,), False)).rung is Rung.L4


def test_the_ladder_is_not_the_gate_and_the_suppression_is():
    """A table whose inputs are already `L2` produces suppressed cells that are
    also `L2`. The rung lets them through; suppression is what does not."""
    rel = made(rows("a", 1, rung=Rung.L2) + rows("b", 9, rung=Rung.L2)
               + rows("c", 9, rung=Rung.L2), k=5)
    a = next(c for c in rel.cells if c.key == "a")
    assert a.rung is Rung.L2 and a.suppressed and a.count is None


def test_the_rule_is_not_re_implemented_here():
    """Rule 12: the pair is *suppression decides* and *the ladder classifies*,
    and `_descriptor_for` is the named middle. A local `max` over the inputs
    would be the second spelling §16 keeps recording."""
    src = (Path(__file__).resolve().parent.parent / "records" / "aggregate.py"
           ).read_text(encoding="utf-8")
    assert "compose" not in src, "aggregate.py composes rungs itself"
    assert "_descriptor_for" in src and "classify(" in src


def test_a_cell_with_no_inputs_is_refused_rather_than_classified_L2():
    """The fail-open `classify` would otherwise take: an empty `derived_from`
    passes step 2 and lands at `L2` with nothing having looked at it."""
    try:
        _descriptor_for("phantom", (), True)
    except NotGated as exc:
        assert "no inputs" in str(exc)
        return
    raise AssertionError("a cell with no inputs was classified")


def test_every_rung_renders_with_its_prefix():
    """Rule 14, at the last place a rung can lose it before a person reads."""
    for _, (_, _) in table(made(auto_injector())).items():
        pass
    text = named(made(auto_injector()), "cells.csv").text
    for line in text.splitlines()[1:]:
        assert line.rsplit(",", 1)[-1].startswith("L")


# --- the announcement ------------------------------------------------------


def test_every_contributing_lane_is_announced_in_its_own_chain():
    """W-1: a trail per lane, never one trail with a column naming which
    student a row is about."""
    rel = made(auto_injector())
    assert len(rel.announced.lanes) == len(rel.lanes) == 14
    assert rel.announced.verify()[0]
    for lane_id, log in rel.announced.lanes:
        assert len(log.entries) == 1
        assert log.entries[0].field_name == "aggregate:section"
        assert "booster_organisation" in log.entries[0].authority
        assert "season participation report" in log.entries[0].authority


def test_a_suppressed_lane_is_announced_as_loudly_as_a_released_one():
    """Rule 10: an audit trail that records only agreement is not one, and this
    one has to answer *was the suppression working*."""
    rel = made(auto_injector(), k=5)
    by_lane = dict(rel.announced.lanes)
    assert by_lane["lane-trumpet-0"].entries[0].outcome is Outcome.REFUSED
    assert by_lane["lane-drums-0"].entries[0].outcome is Outcome.PAYLOAD
    assert by_lane["lane-flute-0"].entries[0].outcome is Outcome.REFUSED


def test_a_lane_that_could_not_be_read_is_announced_unknown():
    blind = Reading("lane-x", "student-x", None, Rung.L4,
                    state=Read.UNREADABLE, why="the lane could not be reached")
    rel = made(rows("trumpet", 6) + rows("flute", 7) + [blind])
    by_lane = dict(rel.announced.lanes)
    assert by_lane["lane-x"].entries[0].outcome is Outcome.UNKNOWN
    assert by_lane["lane-trumpet-0"].entries[0].outcome is Outcome.UNKNOWN


def test_the_announcement_carries_no_payload():
    """The log must not become a second copy of what it audits."""
    rel = made(auto_injector())
    for _, log in rel.announced.lanes:
        for e in log.entries:
            assert not hasattr(e, "value")
            assert "auto" not in e.field_name


def test_the_artifact_is_built_over_the_announcement_and_cannot_precede_it():
    """The manifest carries the chain head the announcement produced, so an
    aggregate that was never announced has nothing to write there."""
    before = Ledger()
    rel = release(ask(), auto_injector(), into=before)
    from records.witness import anchor_for_ledger
    head = anchor_for_ledger(rel.announced, AT).head
    stale = anchor_for_ledger(before, AT).head
    assert head in named(rel, "MANIFEST.txt").text
    assert stale not in named(rel, "MANIFEST.txt").text
    assert head != stale


def test_the_announcement_appends_to_a_ledger_that_already_has_entries():
    first = made(auto_injector())
    second = release(ask(), auto_injector(), into=first.announced)
    assert second.announced.verify()[0]
    for _, log in second.announced.lanes:
        assert len(log.entries) == 2


# --- the artifact ----------------------------------------------------------


def test_the_bundle_is_csv_and_plain_text_and_checks_itself():
    rel = made(auto_injector())
    assert {a.name for a in rel.artifacts} == {"README.txt", "cells.csv",
                                               "MANIFEST.txt"}
    assert {a.media_type for a in rel.artifacts} == {"text/plain", "text/csv"}
    ok, why = verify(rel.artifacts)
    assert ok, why


def test_the_manifest_format_has_one_reader():
    """Rule 12 again: two writers of one manifest format, and
    `records/export.py`'s `verify` is the middle. A second verifier here would
    be the pair."""
    rel = made(auto_injector())
    short = tuple(a for a in rel.artifacts if a.name != "cells.csv")
    ok, why = verify(short)
    assert not ok and "missing" in why


def test_no_lane_id_or_student_id_reaches_an_artifact():
    rel = made(auto_injector())
    for art in rel.artifacts:
        assert "lane-" not in art.text, f"{art.name} names a lane"
        assert "student-" not in art.text, f"{art.name} names a student"


def test_no_lane_id_or_student_id_reaches_a_cell_result():
    """The value the artifacts are rendered *from*, not only the text they came out as.

    `_render` builds every file in the bundle out of the cell tuple, so an
    identifier that reaches a `CellResult` is one format string away from a
    published file. The text scan above cannot stand in for this and the gap is
    not hypothetical: `why` is rendered only for an *incomplete* cell, so a lane
    id sitting in the `why` of a released table passes that scan untouched and
    is still an identifier in the value a booster board's report is built from.

    Asserted over the field **values** rather than the field names, so a field
    added later under some other name is caught too. The retired `contributors`
    is the case that proves the name is not the invariant: it held exactly this
    and no test named it, because no test knew it was there.
    """
    unreadable = Reading("lane-x", "student-x", "drums", Rung.L4,
                         state=Read.UNREADABLE, why="the lane's key is unavailable")
    blind = Reading("lane-y", "student-y", None, Rung.L4,
                    state=Read.UNREADABLE, why="the lane could not be reached")
    for rel in (made(auto_injector()),
                made(rows("trumpet", 6) + rows("flute", 7) + [unreadable]),
                made(rows("trumpet", 6) + rows("flute", 7) + [blind])):
        for cell in rel.cells:
            for fld in dataclasses.fields(cell):
                shown = repr(getattr(cell, fld.name))
                assert "lane-" not in shown, (
                    f"CellResult.{fld.name} names a lane on cell {cell.key!r}: "
                    f"{shown}")
                assert "student-" not in shown, (
                    f"CellResult.{fld.name} names a student on cell "
                    f"{cell.key!r}: {shown}")


def test_no_fleet_noun_reaches_a_surface_a_booster_board_reads():
    fleet = ("Willow", "Grove", "Jeles", "Kart", "SOIL", "LOAM", "FRANK",
             "Nest", "SAFE", "SAP", "Nestor")
    for art in made(auto_injector()).artifacts:
        for noun in fleet:
            assert noun not in art.text, f"{art.name} says {noun}"


def test_the_reader_is_told_the_withholding_is_a_rule_and_not_an_omission():
    text = named(made(auto_injector()), "README.txt").text
    assert "withheld" in text
    assert "subtraction" in text
    assert "student's own file" in text


def test_this_module_never_touches_the_filesystem():
    """§6's core/seam partition. The caller writes; this never does."""
    src = (Path(__file__).resolve().parent.parent / "records" / "aggregate.py"
           ).read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    for banned in ("open(", "write_text", "write_bytes", "Path(", "os.", "shutil"):
        assert banned not in body, f"records/aggregate.py reaches the filesystem: {banned}"


# --- the differencing ledger, named as a ledger ----------------------------


def test_two_releases_over_one_population_are_reported():
    by_section = made(auto_injector())
    by_grade = release(ask(dimension="grade"), auto_injector(), into=Ledger())
    got = differencing_risk((by_section, by_grade))
    assert len(got) == 1
    assert got[0].dimensions == ("grade", "section")


def test_releases_over_different_populations_are_not_reported():
    a = made(auto_injector())
    b = release(ask(population="the concert ensemble"), auto_injector(),
                into=Ledger())
    assert differencing_risk((a, b)) == ()


def test_the_differencing_check_is_a_ledger_and_says_so():
    """Rule 18: a gate that nothing routes through is a ledger. Both are
    useful; calling one the other is not."""
    from records import aggregate
    assert "ledger, not an enforcement" in aggregate.differencing_risk.__doc__
    src = (Path(__file__).resolve().parent.parent / "records" / "aggregate.py"
           ).read_text(encoding="utf-8")
    assert src.count("differencing_risk") == 2, \
        "release() consults the differencing check; it is enforcement now, and " \
        "the docstring says ledger"


# --- not broken shut -------------------------------------------------------


def test_the_module_is_not_broken_shut():
    """Every guard above refuses something. This one requires that a legitimate
    aggregate still comes out, with a number in it."""
    rel = made(rows("a", 9) + rows("b", 11) + rows("c", 14), k=5)
    assert rel.state is Aggregate.RELEASED
    assert len(rel.released) == 3 and not rel.suppressed
    assert {c: n for c, (_, n) in table(rel).items()} == {"a": 9, "b": 11, "c": 14}
    assert verify(rel.artifacts)[0]
    assert all(a.text.strip() for a in rel.artifacts)


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
