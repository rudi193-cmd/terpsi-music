"""§9 foundation 6: what a place sounds like, and what is known about that.

The forbidden acts are attempted here rather than described: a mark used as a
seat, an unmeasured seat asked for a level, a citation with nobody to check it,
a card built over a venue nobody has been to, and the word `measured` matched
across two ladders that disagree about it.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import ast
import dataclasses
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from presentation.parity import parity, strip_colour  # noqa: E402
from records.classify import Descriptor, classify  # noqa: E402
from records.marking import (  # noqa: E402
    P_ASSUMED, P_CITED, P_ESTIMATED, P_FITTED, P_MEASURED, Mark,
)
from records.rungs import Rung  # noqa: E402
from surfaces.print.render import render as print_render  # noqa: E402
from surfaces.text.render import render as text_render  # noqa: E402
from venue.card import headline, profile_card, seat_row  # noqa: E402
from venue.readings import (  # noqa: E402
    UNKNOWN_TEXT, Answer, Profile, Quantity, Reading, at, known_seats,
    supersede, weakest,
)
from venue.sourcing import (  # noqa: E402
    THREE_STATE, divergence, from_three_state, to_three_state, unreachable,
)

PACKAGE = ROOT / "venue"
SEAT = "press-box-4"
FAR = "row-40-side-1"
WHEN = datetime(2026, 9, 12, 19, 30, tzinfo=timezone.utc)


def measured(seat=SEAT, q=Quantity.LEVEL, value=97.4):
    return Reading(seat, q, value, P_MEASURED,
                   source="sound level meter cal. 2026-09-12, operator R. Diaz")


def profile(*readings, name="Memorial Stadium"):
    return Profile(name, readings)


def furnished():
    """A seat with three readings at three different rungs."""
    return profile(
        measured(),
        Reading(SEAT, Quantity.BACKGROUND, 61.0, P_FITTED,
                note="fitted from three empty-stadium sweeps"),
        Reading(SEAT, Quantity.ARRIVAL_SPREAD, 51.0, P_ASSUMED,
                note="asserted from the design model, never measured here"),
    )


# --- nothing here names a person, and it is proved rather than promised ----


def test_no_type_here_has_a_field_that_could_name_a_person():
    banned = {"lane_id", "subject_id", "student_id", "subject", "ward",
              "guardian_id", "roster", "participants", "names"}
    for cls in (Reading, Profile, Answer):
        fields = {f.name for f in dataclasses.fields(cls)}
        overlap = fields & banned
        assert not overlap, f"{cls.__name__} can hold {sorted(overlap)}"


def test_a_mark_cannot_be_used_as_a_seat():
    """The realistic mistake: a caller holds the mark and passes the whole thing.

    §13 pairs a remark with what arrived at its seat. The join is the caller's
    act, made with `mark.seat`; handing the mark itself would put a lane-scoped
    record and a venue reading in one object.
    """
    mark = Mark("show-2026-10-12@94500", 94500, SEAT,
                lane_id="lane-ben", subject_id="student-ben")
    for call in (lambda: at(furnished(), mark, Quantity.LEVEL),
                 lambda: Reading(mark, Quantity.LEVEL, 97.4, P_ASSUMED),
                 lambda: seat_row(furnished(), mark)):
        try:
            call()
        except ValueError as exc:
            assert "lane_id" in str(exc), f"refused for the wrong reason: {exc}"
            continue
        raise AssertionError("a mark was accepted as a seat")


def test_a_mark_without_a_lane_is_still_not_a_seat():
    """An ensemble mark has no lane and is still an object about a performance.

    `subject_id` is `None` on it but the attribute is present, and presence is
    what the guard checks — a seat is a string, and a record that merely happens
    to be empty of a subject today is not one.
    """
    mark = Mark("show-2026-10-12@94500", 94500, SEAT)
    try:
        at(furnished(), mark, Quantity.LEVEL)
    except ValueError as exc:
        assert "lane_id" in str(exc)
        return
    raise AssertionError("an unlaned mark was accepted as a seat")


def test_the_package_imports_nothing_that_decides_about_a_person():
    """The seam, read from the source rather than trusted.

    `card.py` builds IR cells directly instead of through `cell(serving)`. That
    is only defensible while this package cannot reach a read decision at all,
    so the absence of those imports is the thing that makes it true.
    """
    forbidden = {"records.serving", "records.consent", "records.sending",
                 "records.export", "records.disclosure", "records.orders",
                 "records.standing", "records.conflict"}
    seen = set()
    for py in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                seen |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                seen.add(node.module)
    overlap = seen & forbidden
    assert not overlap, f"venue/ reaches a decision about a person: {sorted(overlap)}"


def test_a_venue_reading_classifies_below_the_lane():
    """Derived through `records/classify.py`, not asserted (rule 17).

    This is the reason `venue/` is a top-level package rather than a module under
    `records/`, so the rung is taken from the classifier rather than stated in a
    docstring and believed.
    """
    got = classify(Descriptor(name="seat_level_dba"))
    assert got.rung is Rung.L2, f"a venue reading classified {got.rung}"
    assert "does not name or resolve to a person" in got.reason


def test_a_row_built_here_carries_no_lane_and_no_referent():
    row = seat_row(furnished(), SEAT)
    assert row.lane_id == "" and row.referent == ""


def test_the_package_reaches_nothing_and_writes_nothing():
    import purity  # noqa: E402

    assert purity.egress([PACKAGE]) == (), "venue/ reaches out"
    assert purity.writes([PACKAGE]) == (), "venue/ writes"
    assert purity.counted([PACKAGE]) >= 4, "nothing was scanned; a vacuous pass"


# --- rule 13: an unmeasured venue is unknown, never quiet ------------------


def test_an_unmeasured_seat_is_unknown_not_quiet():
    got = at(profile(), FAR, Quantity.LEVEL)
    assert not got.known and got.reading is None
    assert got.text == UNKNOWN_TEXT
    assert "not quiet" in got.why
    for wrong in ("0", "0.0", "0 dBA", "-300"):
        assert wrong not in got.text


def test_a_characterised_seat_missing_a_quantity_is_unknown_and_says_which():
    got = at(furnished(), SEAT, Quantity.BRIGHTNESS)
    assert not got.known and got.text == UNKNOWN_TEXT
    assert "brightness" in got.why and "never recorded" in got.why


def test_an_answer_cannot_both_carry_a_reading_and_explain_its_absence():
    try:
        Answer(SEAT, Quantity.LEVEL, measured(), why="also unknown")
    except ValueError:
        return
    raise AssertionError("an answer was built holding both states")


def test_an_unknown_answer_must_say_why():
    try:
        Answer(SEAT, Quantity.LEVEL, None, why="")
    except ValueError:
        return
    raise AssertionError("a blank unknown was accepted")


def test_a_reading_with_nothing_in_it_is_refused():
    for bad in (None, float("nan"), float("inf"), float("-inf"), True, "97.4"):
        try:
            Reading(SEAT, Quantity.LEVEL, bad, P_ASSUMED)
        except ValueError:
            continue
        raise AssertionError(f"a reading of {bad!r} was accepted")


def test_the_provenance_of_no_readings_is_refused_and_is_not_p1():
    try:
        weakest(())
    except ValueError as exc:
        assert "unmeasured" in str(exc)
        return
    raise AssertionError("composing nothing returned a rung")


def test_a_card_over_a_venue_nobody_has_been_to_says_so():
    view = profile_card(profile(), [FAR, SEAT], when=WHEN)
    assert "not quiet" in view.note
    cells = [c for row in view.rows for c in row.cells]
    assert cells, "a card with no cells"
    assert all(c.value == UNKNOWN_TEXT for c in cells), "a value appeared from nowhere"
    assert view.badges == (), "an unmeasured venue rendered a provenance badge"


def test_a_card_over_no_seats_is_refused():
    for call in (lambda: profile_card(furnished(), []),
                 lambda: seat_row(furnished(), SEAT, quantities=())):
        try:
            call()
        except ValueError:
            continue
        raise AssertionError("an empty card was built and would render as clean")


def test_a_profile_with_nothing_in_it_has_no_headline():
    assert headline(profile()) is None
    assert known_seats(profile()) == ()


# --- rule 14: rungs travel with their prefix, and are not restated here ----


def test_a_reading_refuses_a_rung_that_is_not_on_the_ladder():
    for bad in ("3", "L3", "P9", "", "P0", "p1", "T0"):
        try:
            Reading(SEAT, Quantity.LEVEL, 97.4, bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as a P-rung")


def test_a_bare_integer_is_not_a_rung():
    for bad in (1, 5, 3.0, True):
        try:
            Reading(SEAT, Quantity.LEVEL, 97.4, bad)
        except (ValueError, TypeError):
            continue
        raise AssertionError(f"{bad!r} travelled as a bare rung")


def test_the_ladder_is_not_spelled_a_second_time_in_this_package():
    """Rule 12: the `P`-ladder has an owner and this package imports it.

    Read from source, because a second spelling would work perfectly right up
    until the two disagreed on a printed program.
    """
    for py in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                name = getattr(target, "id", "")
                assert not name.startswith("P_"), (
                    f"{py.name} defines {name}; the P-ladder lives in "
                    "records/marking.py and is imported")


def test_every_badge_on_a_card_carries_its_prefix_on_both_backends():
    view = profile_card(furnished(), [SEAT, FAR], read_by="director", when=WHEN)
    renderings = {"text": text_render(view), "print": print_render(view)}
    findings = parity(view, renderings)
    assert findings == (), f"parity findings: {findings}"


def test_forced_monochrome_loses_no_rung():
    view = profile_card(furnished(), [SEAT], when=WHEN)
    plain = strip_colour(text_render(view))
    for prefix in (P_MEASURED, P_FITTED, P_ASSUMED):
        assert prefix in plain, f"{prefix} survives only as colour"


def test_the_card_never_names_a_colour():
    for py in sorted(PACKAGE.rglob("*.py")):
        body = py.read_text(encoding="utf-8").lower()
        for word in ("#ff", "rgb(", "\x1b[", "colour=", "color="):
            assert word not in body, f"{py.name} knows about colour"


# --- §15: composition is by the weakest input ------------------------------


def test_provenance_composes_by_the_weakest_input():
    assert weakest(furnished().readings) == P_ASSUMED
    assert weakest((measured(),)) == P_MEASURED
    assert weakest((measured(),
                    Reading(SEAT, Quantity.BACKGROUND, 61.0, P_CITED,
                            source="circuit sound-check sheet, 2025 finals"))) == P_CITED
    assert weakest((Reading(SEAT, Quantity.ARRIVAL, 44.0, P_ESTIMATED,
                            note="from a comparable stadium"),
                    measured())) == P_ESTIMATED


def test_the_headline_is_the_weakest_reading_and_not_the_first():
    card = furnished()
    assert card.readings[0].provenance == P_MEASURED
    assert headline(card).text.startswith(P_ASSUMED)


def test_a_card_declares_the_rung_it_is_worth():
    view = profile_card(furnished(), [SEAT], when=WHEN)
    assert P_ASSUMED in view.note and "weakest" in view.note


# --- §15: a cited rung has to survive its source disappearing --------------


def test_a_reading_claiming_a_checkable_source_must_name_one():
    for rung in (P_MEASURED, P_CITED):
        for blank in ("", "   "):
            try:
                Reading(SEAT, Quantity.LEVEL, 97.4, rung, source=blank)
            except ValueError as exc:
                assert "source" in str(exc) or "survive" in str(exc)
                continue
            raise AssertionError(f"{rung} was accepted with nobody to check it")


def test_a_fitted_or_assumed_reading_needs_no_citation():
    """The other half. A guard that refused everything would also pass the test
    above, and would make the weakest rungs unusable — which is the failure §15
    names: withholding a weakly sourced number is the error."""
    for rung in (P_FITTED, P_ESTIMATED, P_ASSUMED):
        assert Reading(SEAT, Quantity.LEVEL, 97.4, rung).provenance == rung


# --- supersession is a decision, not a write -------------------------------


def test_two_readings_of_one_thing_are_refused():
    try:
        profile(measured(), measured(value=99.1))
    except ValueError as exc:
        assert "supersede" in str(exc)
        return
    raise AssertionError("one seat carried two levels and neither was chosen")


def test_supersede_replaces_without_mutating_the_original():
    before = furnished()
    after = supersede(before, Reading(SEAT, Quantity.ARRIVAL_SPREAD, 28.0,
                                      P_FITTED, note="re-derived"))
    assert at(before, SEAT, Quantity.ARRIVAL_SPREAD).reading.value == 51.0
    assert at(after, SEAT, Quantity.ARRIVAL_SPREAD).reading.value == 28.0
    assert len(after.readings) == len(before.readings)
    assert weakest(after.readings) == P_FITTED


# --- the named middle (rule 12): three states against five rungs -----------


def test_measured_there_is_cited_here_and_not_measured():
    """The finding §14's row does not carry: the two ladders share a word.

    That vocabulary defines `measured` as a published dataset with a citation
    someone can check, which is `P2` here. Matching on the word would promote
    every citation in the fleet to the rung reserved for this program's own
    instruments.
    """
    assert from_three_state("measured") == P_CITED
    assert from_three_state("measured") != P_MEASURED
    assert from_three_state("fitted") == P_FITTED
    assert from_three_state("assumed") == P_ASSUMED


def test_two_of_the_five_rungs_cannot_arrive_through_the_translation():
    assert set(unreachable()) == {P_MEASURED, P_ESTIMATED}
    reachable = {from_three_state(s) for s in THREE_STATE}
    assert reachable & set(unreachable()) == set()
    assert len(reachable) == 3


def test_translating_back_refuses_rather_than_rounding():
    for rung in unreachable():
        try:
            to_three_state(rung)
        except ValueError as exc:
            assert "no counterpart" in str(exc)
            continue
        raise AssertionError(f"{rung} was rounded to a neighbouring state")
    assert to_three_state(P_CITED) == "measured"
    assert to_three_state(P_FITTED) == "fitted"
    assert to_three_state(P_ASSUMED) == "assumed"


def test_an_unknown_vocabulary_is_refused_and_never_guessed():
    for bad in ("MEASURED-ISH", "estimated", "cited", "", "P2"):
        try:
            from_three_state(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was translated to a rung by guessing")


def test_the_middle_reports_the_divergence_rather_than_hiding_it():
    findings = divergence()
    assert findings, "a middle that reports clean is claiming the ladders agree"
    joined = "\n".join(findings)
    assert "word collision" in joined
    assert P_MEASURED in joined and P_ESTIMATED in joined


# --- a seat is a place -----------------------------------------------------


def test_a_blank_seat_is_refused():
    for bad in ("", "   ", "\t"):
        try:
            Reading(bad, Quantity.LEVEL, 97.4, P_ASSUMED)
        except ValueError:
            continue
        raise AssertionError(f"a reading placed at {bad!r} was accepted")


def test_a_seat_is_a_string_and_not_a_number():
    for bad in (4, None, ("row", 40)):
        try:
            at(furnished(), bad, Quantity.LEVEL)
        except (TypeError, ValueError):
            continue
        raise AssertionError(f"{bad!r} was accepted as a seat")


# --- quantities ------------------------------------------------------------


def test_no_two_quantities_are_the_same_member():
    """The aliasing defect this suite caught on the first run.

    `LEVEL` and `BACKGROUND` are both dBA, and an `Enum` whose members share a
    value makes the second an alias for the first — a background reading
    silently became a second level reading and the duplicate check refused it.
    """
    members = list(Quantity)
    assert len(members) == len({m.name for m in members}) == 6
    assert Quantity.LEVEL is not Quantity.BACKGROUND
    assert Quantity.ARRIVAL is not Quantity.ARRIVAL_SPREAD


def test_a_quantity_owns_its_unit_and_a_reading_cannot_restate_it():
    fields = {f.name for f in dataclasses.fields(Reading)}
    assert "unit" not in fields, "a reading can carry a unit that disagrees"
    assert Reading(SEAT, Quantity.ARRIVAL, 44.0, P_ASSUMED).unit == "ms"
    assert measured().text == "97.4 dBA"


def test_a_quantity_this_package_does_not_characterise_is_refused():
    for bad in ("LEVEL", "level", 1, None):
        try:
            Reading(SEAT, bad, 97.4, P_ASSUMED)
        except (ValueError, TypeError):
            continue
        raise AssertionError(f"{bad!r} was accepted as a quantity")


def test_the_module_is_not_broken_shut():
    p = furnished()
    assert known_seats(p) == (SEAT,)
    assert at(p, SEAT, Quantity.LEVEL).text == "97.4 dBA"
    view = profile_card(p, [SEAT, FAR], read_by="director", when=WHEN)
    assert len(view.rows) == 2 and len(view.rows[0].cells) == 6
    assert text_render(view) and print_render(view)


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
