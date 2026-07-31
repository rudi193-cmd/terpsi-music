"""W-3, rule 15 and refusal 7 over the roll.

The forbidden acts attempted here, each asserted to be refused: a roster on the
referent, a mark rewritten in place, an absence read as unexcused because nobody
was asked, an attendance comparison across two lanes, and — the one this module
exists for — an attendance record handed to the send path.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import re
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records import attendance  # noqa: E402
from records.attendance import (  # noqa: E402
    AbsenceRequest, AttendanceEntry, Excusal, NoRoster, NotSendable, Presence,
    Referent, Signal, SignalKind, correct, excusal, headcount, notify, own,
    patterns, request_absence, roster, send_attendance, signal, take_roll,
)
from records.conflict import NotComputable  # noqa: E402
from records.dispositions import Disposition, answer  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.sending import Payload, Standing  # noqa: E402
from records.serving import Edge  # noqa: E402

BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"
SEASON = "2026-fall"
NOW = datetime(2026, 10, 12, 15, 30)
LATER = datetime(2026, 10, 13, 9, 0)


def rehearsal(label="Tuesday rehearsal") -> Referent:
    return Referent("ref-1", "Rehearsal", label, NOW, SEASON, created_at=NOW)


def marked(presence=Presence.ABSENT, subject=BEN, lane=LB) -> AttendanceEntry:
    return take_roll(rehearsal(), [(lane, subject, presence)],
                     author_id="staff-nguyen", at=NOW)[0]


# --- W-3: N entries, one referent, no roster ------------------------------


def test_a_shared_event_is_n_lane_entries_with_one_referent():
    """`docs/LANE-MODEL.md`'s stated cost: a rehearsal attended by 150 students
    writes 150 rows. The tuple's length is the number marked."""
    r = rehearsal()
    entries = take_roll(r, [(LB, BEN, Presence.PRESENT), (LA, ANA, Presence.ABSENT)],
                        author_id="staff-nguyen", at=NOW)
    assert len(entries) == 2
    assert {e.referent_id for e in entries} == {r.referent_id}
    assert {e.lane_id for e in entries} == {LB, LA}


def test_the_referent_carries_no_participants():
    """*"Anything later added to `referent` that names or counts participants
    reintroduces exactly the partition W-1 forbids."* Asserted, not trusted."""
    names = {f.name for f in dataclasses.fields(Referent)}
    assert names == {"referent_id", "kind", "label", "occurs_at", "season",
                     "created_at", "valid_at", "invalid_at"}
    for banned in ("roster", "members", "attendees", "students", "subjects",
                   "present", "absent", "headcount", "count", "lane_ids"):
        assert banned not in names, f"referent grew {banned!r} — W-3 is breached"


def test_asking_a_referent_for_its_roster_refuses_by_name():
    try:
        roster(rehearsal())
    except NoRoster as exc:
        assert "W-3" in str(exc)
        return
    raise AssertionError("a referent produced a roster")


def test_a_mark_has_nowhere_to_record_a_reason_or_a_judgement():
    """A reason is health- or discipline-adjacent (`L4`); a mark is `L3`.
    Composition is `max`, so a reason on the mark drags the row up a rung and
    toward every surface that renders attendance."""
    names = {f.name for f in dataclasses.fields(AttendanceEntry)}
    for banned in ("reason", "note", "notes", "comment", "excused", "unexcused",
                   "medical", "documentation", "body", "text"):
        assert banned not in names, f"a mark grew {banned!r}"


def test_a_student_marked_twice_on_one_roll_is_refused_not_deduplicated():
    try:
        take_roll(rehearsal(), [(LB, BEN, Presence.PRESENT), (LB, BEN, Presence.ABSENT)],
                  author_id="staff-nguyen", at=NOW)
    except ValueError as exc:
        assert "twice" in str(exc)
        return
    raise AssertionError("two disagreeing marks were silently collapsed")


def test_a_mark_without_a_lane_is_refused_from_the_first_write():
    try:
        take_roll(rehearsal(), [("", BEN, Presence.PRESENT)],
                  author_id="staff-nguyen", at=NOW)
    except ValueError as exc:
        assert "W-1" in str(exc)
        return
    raise AssertionError("a mark was written outside a lane")


def test_a_referent_with_no_season_cannot_be_constructed():
    """Retention's axis (§10). Not a purge, but the field a purge needs."""
    try:
        Referent("ref-2", "Rehearsal", "Tuesday", NOW, "", created_at=NOW)
    except ValueError as exc:
        assert "season" in str(exc)
        return
    raise AssertionError("a referent with no season was accepted")


# --- refusal 3 over a correction ------------------------------------------


def test_a_correction_supersedes_and_never_overwrites():
    entry = marked(Presence.ABSENT)
    closed, later = correct(entry, Presence.PRESENT, by="director-shaw", at=LATER)
    assert closed.presence is Presence.ABSENT, "the original mark was rewritten"
    assert closed.invalid_at == LATER and closed.corrected_by == "director-shaw"
    assert later.presence is Presence.PRESENT and later.invalid_at is None
    assert not closed.live_at(LATER) and later.live_at(LATER)


def test_own_attendance_counts_the_correction_once():
    entry = marked(Presence.ABSENT)
    closed, later = correct(entry, Presence.PRESENT, by="director-shaw", at=LATER)
    got = own([closed, later], at=LATER)
    assert got.events == 1 and got.present == 1 and got.absent == 0


# --- rule 15: the ask, and the answer nobody invented ---------------------


def test_an_absence_request_carries_a_timebound_declared_at_issuance():
    ar = request_absence(BEN, rehearsal(), asked_by="guardian-alvarez",
                         asked_at=NOW, within=timedelta(days=3),
                         office="attendance-office", escalates_to="director-shaw")
    assert ar.request.due_by == NOW + timedelta(days=3)
    assert ar.referent_id == "ref-1" and ar.season == SEASON


def test_request_absence_has_no_default_timebound_of_its_own():
    """A wrapper with a default would defeat `dispositions.ask` one call earlier
    — I-6's *"a default would let issuers stop declaring."*"""
    p = inspect.signature(request_absence).parameters
    assert p["within"].default is inspect.Parameter.empty
    assert p["within"].kind is inspect.Parameter.KEYWORD_ONLY


def test_the_request_carries_a_pointer_to_a_reason_and_never_the_text():
    names = {f.name for f in dataclasses.fields(AbsenceRequest)}
    assert "reason_entry_id" in names
    for banned in ("reason", "reason_text", "documentation", "diagnosis", "note"):
        assert banned not in names, f"AbsenceRequest grew {banned!r}"


def test_an_unconsulted_request_source_is_unknown_never_unexcused():
    """**The forbidden act, in the register that benches a student.** `None`
    means nobody was asked; `()` means asked and there is nothing."""
    entry = marked(Presence.ABSENT)
    assert excusal(entry, None, LATER) is Excusal.UNKNOWN
    assert excusal(entry, (), LATER) is Excusal.NOT_EXCUSED


def test_a_granted_request_excuses_and_an_open_one_is_awaited():
    entry = marked(Presence.ABSENT)
    ar = request_absence(BEN, rehearsal(), asked_by="guardian-alvarez",
                         asked_at=NOW, within=timedelta(days=3),
                         office="attendance-office", escalates_to="director-shaw")
    assert excusal(entry, [ar], LATER) is Excusal.AWAITED
    granted = AbsenceRequest(
        answer(ar.request, granted=True, by="office-lee", at=LATER,
               reason="family bereavement, verified"),
        ar.referent_id, ar.season)
    assert excusal(entry, [granted], LATER) is Excusal.EXCUSED


def test_silence_past_the_timebound_excuses_rather_than_refusing():
    """Rule 15: silence is not an answer. `dispositions.state_at` escalates it,
    and an escalated request must not read as a refusal on the attendance side —
    the office's failure to answer would otherwise land on the student."""
    entry = marked(Presence.ABSENT)
    ar = request_absence(BEN, rehearsal(), asked_by="guardian-alvarez",
                         asked_at=NOW, within=timedelta(days=1),
                         office="attendance-office", escalates_to="director-shaw")
    way_later = NOW + timedelta(days=30)
    from records.dispositions import state_at
    assert state_at(ar.request, way_later).disposition is Disposition.ESCALATED
    assert excusal(entry, [ar], way_later) is Excusal.EXCUSED


# --- one lane per statistic ----------------------------------------------


def test_an_attendance_statistic_spanning_two_lanes_refuses():
    entries = take_roll(rehearsal(), [(LB, BEN, Presence.PRESENT),
                                      (LA, ANA, Presence.ABSENT)],
                        author_id="staff-nguyen", at=NOW)
    try:
        own(entries)
    except NotComputable as exc:
        assert "lanes" in str(exc)
        return
    raise AssertionError("an attendance statistic was computed across lanes")


def test_an_attendance_pattern_across_students_is_refused_by_name():
    entries = take_roll(rehearsal(), [(LB, BEN, Presence.ABSENT),
                                      (LA, ANA, Presence.ABSENT)],
                        author_id="staff-nguyen", at=NOW)
    try:
        patterns(entries)
    except NotComputable as exc:
        assert "W-7" in str(exc)
        return
    raise AssertionError("a cross-student attendance pattern was produced")


# --- the count, through the re-identification gate ------------------------


def test_a_headcount_over_a_small_section_does_not_reach_L2():
    """A count over a section of three is not anonymous. §7's judge gets *"a
    count, a section, a chair number with no name"* — and that derived form is
    only `L2` once the cohort clears a declared floor."""
    three = [(f"lane-{i}", f"student-{i}", Presence.PRESENT) for i in range(3)]
    entries = take_roll(rehearsal(), three, author_id="staff-nguyen", at=NOW)
    got = headcount(entries, rehearsal(), floor=5)
    assert got.rung is Rung.L3 and not got.servable
    assert got.present == 3


def test_a_headcount_over_a_full_ensemble_is_servable():
    many = [(f"lane-{i}", f"student-{i}", Presence.PRESENT) for i in range(40)]
    entries = take_roll(rehearsal(), many, author_id="staff-nguyen", at=NOW)
    got = headcount(entries, rehearsal(), floor=5)
    assert got.rung is Rung.L2 and got.servable and got.present == 40


def test_a_headcount_has_no_default_suppression_floor():
    p = inspect.signature(headcount).parameters
    assert p["floor"].default is inspect.Parameter.empty


# --- refusal 7: the record cannot reach the carrier -----------------------


def guardian() -> Edge:
    return Edge("guardian_of", "guardian-alvarez", BEN, datetime(2020, 1, 1),
                created_at=datetime(2020, 1, 1))


def sent():
    out = []
    return out, lambda who, body: out.append((who, body))


def test_a_signal_carries_a_time_and_names_no_student():
    out, transport = sent()
    sig = signal(rehearsal("Tuesday rehearsal"), SignalKind.TIME)
    who = notify(sig, BEN, at=NOW, edges=[guardian()], restrictions=[],
                 transport=transport)
    assert who.state is Standing.DERIVED and len(out) == 1
    body = out[0][1]
    assert "Tuesday rehearsal" in body
    for leaked in (BEN, "absent", "present", "balance", "lane-"):
        assert leaked not in body, f"a signal body carried {leaked!r}"


def test_a_change_signal_carries_two_times_and_nothing_else():
    sig = signal(rehearsal(), SignalKind.CHANGE, was=datetime(2026, 10, 12, 13, 30))
    body = sig.body()
    assert "moved from" in body and "1:30 pm" in body and "3:30 pm" in body


def test_a_signal_has_no_free_text_field():
    """**The seam.** The body is rendered from the referent's two published
    columns; there is no parameter through which a record could be passed."""
    names = {f.name for f in dataclasses.fields(Signal)}
    assert names == {"kind", "referent_id", "label", "occurs_at", "was"}
    for banned in ("body", "text", "message", "content", "presence", "reason",
                   "note", "payload", "subject_id"):
        assert banned not in names, f"Signal grew {banned!r} — refusal 7's seam is open"


def test_an_attendance_record_cannot_be_made_into_a_signal():
    """The forbidden act. An `AttendanceEntry` has a `referent_id` and would
    duck-type through an attribute-based constructor, carrying a presence into
    the only object this module lets near a carrier."""
    try:
        signal(marked(Presence.ABSENT), SignalKind.TIME)  # type: ignore[arg-type]
    except NotSendable as exc:
        assert "record" in str(exc)
        return
    raise AssertionError("an attendance record became a signal")


def test_an_attendance_record_cannot_be_handed_to_notify():
    out, transport = sent()
    for bad in (marked(Presence.ABSENT), "Ben was absent tonight",
                Payload(BEN, NOW, "Ben was absent tonight")):
        try:
            notify(bad, BEN, at=NOW, edges=[guardian()], restrictions=[],  # type: ignore[arg-type]
                   transport=transport)
        except NotSendable:
            continue
        raise AssertionError(f"{type(bad).__name__} reached the send path")
    assert out == [], "something was transmitted"


def test_send_attendance_exists_so_the_refusal_is_findable_by_name():
    """`practice.standings`'s argument: a missing name reads as *not built yet*
    and invites a local reimplementation."""
    try:
        send_attendance(marked(Presence.ABSENT))
    except NotSendable as exc:
        assert "record" in str(exc) and "4.1" in str(exc)
        return
    raise AssertionError("send_attendance() sent something")


def test_notify_has_no_body_override_and_no_recipient_parameter():
    """Static, over the signature — `test_sending.py`'s G4 shape. A `body`
    parameter here would defeat the seam one call before `deliver()`."""
    params = set(inspect.signature(notify).parameters)
    for banned in ("body", "text", "message", "content", "to", "recipient",
                   "recipients", "guardians"):
        assert banned not in params, f"notify() grew {banned!r}"


def code_of(fn) -> str:
    """A function's executable source, with its docstring removed.

    The prose in this tree explains the guards, so `signal()`'s docstring names
    the type it exists to keep out — and a naive grep over `inspect.getsource`
    then fails on the sentence that documents the rule. Parsing and dropping the
    docstring keeps the check aimed at code, which is the thing that can widen.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn))).body[0]
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        tree.body = tree.body[1:]
    return ast.unparse(tree)


def test_the_send_path_never_mentions_a_record_type():
    """Static, over the code. `AttendanceEntry` must not be *referenced* by
    `signal`, `Signal.body` or `notify` — a signature is a thing a future edit
    can widen and a comment is not."""
    for fn in (signal, notify, Signal.body):
        assert "AttendanceEntry" not in code_of(fn), (
            f"{fn.__qualname__} references the record type; the send path must not"
        )
    body = code_of(Signal.body)
    assert "presence" not in body and "reason" not in body


def test_the_module_writes_no_payload_outside_notify():
    """`Payload(` appears exactly once in the module, inside `notify`, so there
    is one place a message is constructed and it is the one under test."""
    src = Path(attendance.__file__).read_text(encoding="utf-8")
    assert len(re.findall(r"\bPayload\(", src)) == 1
    assert "Payload(" in inspect.getsource(notify)


def test_the_module_deletes_nothing():
    """Refusal 3 over this module's source, the way `test_sending.py` checks G7."""
    src = Path(attendance.__file__).read_text(encoding="utf-8")
    bad = re.findall(r"\b(DELETE\s+FROM|\.remove\(|\.pop\(|del\s+\w+\[)", src, re.I)
    assert not bad, f"a delete path appeared in the attendance module: {bad}"


def test_the_module_is_not_broken_shut():
    """§7's own caveat: indistinguishability passes vacuously if nothing is ever
    served. A companion who can genuinely see something."""
    out, transport = sent()
    entries = take_roll(rehearsal(), [(LB, BEN, Presence.PRESENT)],
                        author_id="staff-nguyen", at=NOW)
    assert own(entries, at=NOW).rate == 1.0
    notify(signal(rehearsal(), SignalKind.ACKNOWLEDGMENT), BEN, at=NOW,
           edges=[guardian()], restrictions=[], transport=transport)
    assert len(out) == 1 and out[0][0] == "guardian-alvarez"


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
