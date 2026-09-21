"""Publication: what may cross, when it may cross, and what a pending one is.

Three families here, and each is an attempt at the forbidden act rather than a
demonstration that the ordinary path works (rule 19):

* **smuggling** — an anchor carrying a subject id, by subclass, by attribute,
  and by not being an anchor at all
* **the shape of a week** — an anchor published the day something happened, a
  tolerance wide enough to admit every moment, and two anchors in one slot
* **a proof that never came back** — which must be its own state, must never
  become a `witness.Receipt`, and must never let a log read as witnessed

The last section is limitations, written the way `tests/test_witness.py` writes
them: named, so nobody later mistakes one for a bug and closes it by deleting
the assertion.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import inspect
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Principal, Rung, serve  # noqa: E402
from records.disclosure import Ledger, Log  # noqa: E402
from records import publication, witness  # noqa: E402
from records.publication import (  # noqa: E402
    Cadence, NotPublishable, Payload, Proof, Publication, Status, Submission,
    derivation_artifact, payload_for, payloads_for, permitted, proof_artifact,
    receipts, reconcile, register, submission_artifact, unpublished,
)
from records.witness import (  # noqa: E402
    Anchor, Standing, anchor_for, anchor_for_ledger, derives, ledger_derivation,
    standing,
)

T0 = datetime(2026, 3, 2)          # a Monday, and the cadence's first slot
WEEK = timedelta(days=7)
BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"
CADENCE = Cadence(T0, WEEK)


def a_log(n=5) -> Log:
    fld = Field(LB, BEN, "chair", Rung.L3, payload="Ben Alvarez",
                instruction="one member", provenance="P1")
    edges = [Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)]
    log = Log()
    for i in range(n):
        log = log.record(serve(fld, Principal("g-mother"), edges, T0),
                         principal_id="g-mother", subject_id=BEN,
                         field_name="chair", at=T0 + timedelta(minutes=i))
    return log


def a_ledger(ben=3, ana=2) -> Ledger:
    led = Ledger()
    for lane, subject, n in ((LB, BEN, ben), (LA, ANA, ana)):
        fld = Field(lane, subject, "chair", Rung.L3, payload="x", instruction="y")
        edges = [Edge("guardian_of", "g-mother", subject, T0, created_at=T0)]
        for _ in range(n):
            led = led.record(serve(fld, Principal("g-mother"), edges, T0),
                             lane_id=lane, principal_id="g-mother",
                             subject_id=subject, field_name="chair", at=T0)
    return led


def sent(slot=T0, log=None, at=None) -> Submission:
    return Submission(anchor_for(log if log is not None else a_log(), slot),
                      at if at is not None else slot)


def proven(sub: Submission, attested=None) -> Proof:
    when = attested if attested is not None else sub.anchor.at + timedelta(hours=2)
    return Proof(sub.over, f"proofs/{sub.over[:12]}.ots", when, when)


# --- nothing but a digest, a count and a time -----------------------------


def test_only_three_fields_may_cross():
    assert publication.MAY_CROSS == ("head", "count", "at")
    fields = {f.name for f in dataclasses.fields(Payload)}
    assert fields == {"head", "count", "at"}


def test_an_anchor_carrying_a_subject_is_refused_at_the_gate():
    """The smuggle. Subclassing a frozen dataclass to hang a name off it costs
    four lines, and the published thing is on somebody else's calendar server
    the moment it leaves."""

    @dataclass(frozen=True)
    class Tagged(Anchor):
        subject_id: str = ""

    sneaky = Tagged("a" * 64, 3, T0, subject_id=BEN)
    ok, why = permitted(sneaky)
    assert not ok and "subject_id" in why
    try:
        payload_for(sneaky, CADENCE)
    except NotPublishable as exc:
        assert "subject_id" in str(exc)
    else:
        raise AssertionError("a subject id was published inside an anchor")


def test_a_smuggled_field_the_instance_does_not_carry_is_still_refused():
    """**The version that reads the type rather than the object**, and it needed
    its own test: an ordinary subclass puts its extra field in the instance
    dictionary, so the attribute check below catches it too and the field check
    can be removed without any test noticing. That is the ablation result
    `EXTERNAL-ARM.md` names — *a gate green because a different constraint was
    catching it*.

    A subclass with slots carries nothing in its dictionary and the value is
    still there, so only reading the declared fields refuses it.
    """

    @dataclass(frozen=True, slots=True)
    class Slotted(Anchor):
        subject_id: str = ""

    sneaky = Slotted("a" * 64, 3, T0, subject_id=BEN)
    assert getattr(sneaky, "__dict__", {}) == {}, "the instance is carrying it after all"
    assert sneaky.subject_id == BEN, "the smuggled value is readable"
    ok, why = permitted(sneaky)
    assert not ok and "subject_id" in why
    try:
        payload_for(sneaky, CADENCE)
    except NotPublishable:
        return
    raise AssertionError("a subject id was published inside a slotted anchor")


def test_a_field_hung_on_the_instance_is_refused():
    """`frozen=True` blocks assignment; `object.__setattr__` does not care, and
    the type still reports three fields."""
    a = Anchor("b" * 64, 3, T0)
    object.__setattr__(a, "note", "Ben's medication changed this week")
    ok, why = permitted(a)
    assert not ok and "note" in why
    try:
        payload_for(a, CADENCE)
    except NotPublishable:
        return
    raise AssertionError("an attribute set on the instance crossed the boundary")


def test_a_submission_cannot_be_built_around_a_smuggled_anchor():
    """The second door into the same room: the gate is on `payload_for`, so a
    caller who skips it and records a submission directly must be refused
    there too."""

    @dataclass(frozen=True)
    class Tagged(Anchor):
        lane_id: str = ""

    try:
        Submission(Tagged("c" * 64, 1, T0, lane_id=LB), T0)
    except NotPublishable:
        return
    raise AssertionError("a submission was recorded for an unpublishable anchor")


def test_a_per_lane_anchor_tuple_is_not_publishable():
    """`Ledger.anchors()` returns `(head, count)` per lane. Publishing those is
    a per-student activity series, and it is refused for being the wrong type
    rather than by anybody remembering."""
    led = a_ledger()
    for lane_id, pair in led.anchors():
        ok, why = permitted(pair)
        assert not ok and "not an anchor" in why


def test_the_wire_form_is_thirty_two_bytes_and_binds_all_three():
    """One call carrying 32 bytes, and all three fields inside them: a
    commitment that ignored the count could be redeemed for a different count."""
    p = payload_for(anchor_for(a_log(9), T0), CADENCE)
    assert len(p.commitment) == 32 and len(p.over) == 64
    same_head_fewer_entries = Payload(p.head, p.count - 1, p.at)
    later_slot = Payload(p.head, p.count, p.at + WEEK)
    other_head = Payload("f" * 64, p.count, p.at)
    for altered in (same_head_fewer_entries, later_slot, other_head):
        assert altered.over != p.over, "a field is not bound into the commitment"


def test_two_quiet_weeks_do_not_share_a_commitment():
    """**The reason the wire form is not the chain head.** Nothing written for a
    fortnight leaves the head and the count identical, so a head-only submission
    lets one proof stand in for both weeks and a skipped publication becomes
    invisible. Binding the slot gives each week its own digest."""
    log = a_log(4)
    first = payload_for(anchor_for(log, T0), CADENCE)
    second = payload_for(anchor_for(log, T0 + WEEK), CADENCE)
    assert first.head == second.head and first.count == second.count
    assert first.over != second.over, (
        "two slots with identical contents produced one digest; a reused proof "
        "would hide a missed publication"
    )


# --- the cadence is the calendar's, not the activity's --------------------


def test_publishing_off_the_calendar_is_refused():
    """`corpus-lens`: content redaction does not scrub the shape of a week. An
    anchor published the afternoon of an incident publishes the incident."""
    incident = T0 + timedelta(days=3, hours=4)
    try:
        payload_for(anchor_for(a_log(), incident), CADENCE)
    except NotPublishable as exc:
        assert "calendar" in str(exc)
        return
    raise AssertionError("an anchor was published off the schedule")


def test_the_gate_cannot_be_asked_without_a_calendar():
    """A cadence that could be omitted is a cadence that gets omitted."""
    params = inspect.signature(payload_for).parameters
    assert "cadence" in params
    assert params["cadence"].default is inspect.Parameter.empty


def test_a_tolerance_that_admits_every_moment_is_not_a_cadence():
    for tol in (WEEK / 2, WEEK, WEEK * 2):
        try:
            Cadence(T0, WEEK, tol)
        except ValueError:
            continue
        raise AssertionError(f"a tolerance of {tol} was accepted against a {WEEK} period")
    Cadence(T0, WEEK, timedelta(hours=1))     # the ordinary case still works


def test_two_anchors_in_one_slot_are_refused():
    """One slot carrying several anchors is several chains, and a weekly series
    of per-chain anchors is per-lane volume on a public calendar."""
    a = anchor_for(a_log(3), T0)
    b = anchor_for(a_log(4), T0)
    payloads_for([a], CADENCE)                # one is fine
    try:
        payloads_for([a, b], CADENCE)
    except NotPublishable as exc:
        assert "one slot" in str(exc) or "two anchors" in str(exc)
        return
    raise AssertionError("two anchors were published for one slot")


def test_the_cadence_takes_no_log_and_no_ledger():
    """A schedule computed from activity publishes the activity. Asserted over
    the whole module rather than one function, because the leak arrives by
    somebody adding a convenient parameter."""
    swept = 0
    for name, fn in vars(publication).items():
        if not callable(fn) or name.startswith("_"):
            continue
        if getattr(fn, "__module__", "") != publication.__name__:
            continue                          # imported; its home tests it
        if name == "derivation_artifact":
            continue                          # local-only, and marked so
        try:
            params = set(inspect.signature(fn).parameters)
        except (TypeError, ValueError):
            continue
        swept += 1
        assert not ({"log", "ledger"} & params), (
            f"{name}() takes a log or a ledger; the cadence would leak the shape "
            f"of a week"
        )
    assert swept > 5, f"the sweep looked at {swept} callables — it is decorative"


def test_the_schedule_has_one_implementation():
    """Rule 12 the other way round: not a middle for a pair, but a refusal to
    create the pair. A second schedule here would agree with `witness`'s until
    one of them was edited."""
    assert publication.schedule is witness.schedule
    assert publication.missing is witness.missing


def test_unpublished_slots_are_reported():
    subs = [sent(T0), sent(T0 + WEEK), sent(T0 + 3 * WEEK)]
    gaps = unpublished(subs, CADENCE, T0 + 3 * WEEK)
    assert gaps == (T0 + 2 * WEEK,)


# --- a proof that has not come back ---------------------------------------


def test_a_submission_with_no_proof_is_its_own_state():
    """Rule 13. Not witnessed, not fine, and not absent from the register."""
    sub = sent(T0)
    got = reconcile([sub], [], CADENCE, through=T0, as_of=T0 + timedelta(hours=1))
    assert [s.state for s in got] == [Publication.AWAITING_PROOF]
    assert not got[0].is_witness


def test_a_pending_submission_becomes_overdue_rather_than_staying_quiet():
    sub = sent(T0)
    got = reconcile([sub], [], CADENCE, through=T0, as_of=T0 + timedelta(days=9))
    assert got[0].state is Publication.OVERDUE
    assert "no proof has come back" in got[0].reason


def test_a_reference_without_a_time_is_not_a_proof():
    """A public timestamp is a promise first and a proof afterwards. The promise
    reads as awaiting, with its own sentence."""
    sub = sent(T0)
    promise = Proof(sub.over, "proofs/pending.ots", T0 + timedelta(minutes=5))
    got = reconcile([sub], [promise], CADENCE, through=T0,
                    as_of=T0 + timedelta(hours=1))
    assert got[0].state is Publication.AWAITING_PROOF
    assert "not a timestamp" in got[0].reason


def test_a_pending_submission_never_becomes_a_witness_receipt():
    """The join into `witness.standing()`, and the place this has to hold: a
    receipt manufactured from a pending submission would make an unwitnessed
    log read as witnessed."""
    log = a_log(5)
    sub = Submission(anchor_for(log, T0), T0)
    got = reconcile([sub], [], CADENCE, through=T0, as_of=T0 + timedelta(hours=1))
    assert receipts(got) == ()
    assert standing(log, receipts(got)).standing is Standing.UNWITNESSED


def test_a_slot_nobody_submitted_is_reported_as_such():
    got = reconcile([sent(T0)], [], CADENCE, through=T0 + WEEK, as_of=T0 + WEEK)
    states = [s.state for s in got]
    assert Publication.NOT_SUBMITTED in states
    assert any("nothing was submitted" in s.reason for s in got)


def test_a_proof_for_nothing_submitted_is_unsolicited():
    """Either the record of the submission was lost or the proof answers
    something else. Both are things to say out loud."""
    orphan = Proof("d" * 64, "proofs/d.ots", T0, T0)
    got = reconcile([], [orphan], CADENCE, through=T0, as_of=T0)
    assert {s.state for s in got} == {Publication.UNSOLICITED,
                                      Publication.NOT_SUBMITTED}, (
        "the orphan proof, and the slot it does not answer, are two facts and "
        "both belong on the register"
    )
    assert any("no record of submitting" in s.reason for s in got)


def test_a_proof_attested_before_the_entries_it_covers_is_mismatched():
    sub = sent(T0 + WEEK)
    early = Proof(sub.over, "proofs/early.ots", T0, T0 - timedelta(days=1))
    got = reconcile([sub], [early], CADENCE, through=T0 + WEEK, as_of=T0 + WEEK)
    answered = [s for s in got if s.submission is not None]
    assert [s.state for s in answered] == [Publication.MISMATCHED]
    assert "before the entries it covers existed" in answered[0].reason


def test_a_submission_off_the_calendar_is_reported_in_the_register():
    """`payload_for` refuses to make one. A submission recorded another way is
    still visible, because the register is what somebody reads later."""
    odd = Submission(anchor_for(a_log(), T0 + timedelta(days=2)), T0 + timedelta(days=2))
    got = reconcile([odd], [], CADENCE, through=T0 + WEEK, as_of=T0 + WEEK)
    assert any(s.state is Publication.OFF_CALENDAR for s in got)


def test_a_proven_submission_is_what_makes_the_log_evidence():
    """The negative control. A module that returned AWAITING for everything
    would pass most of the assertions above."""
    log = a_log(5)
    sub = Submission(anchor_for(log, T0), T0)
    got = reconcile([sub], [proven(sub)], CADENCE, through=T0, as_of=T0 + WEEK)
    assert got[0].state is Publication.PROVEN and got[0].is_witness
    rs = receipts(got)
    assert len(rs) == 1
    assert standing(log, rs).standing is Standing.WITNESSED


# --- the artifacts --------------------------------------------------------


def test_the_two_halves_of_a_publication_share_a_stem():
    """Rule 12's pair, named in the filenames: a directory listing shows which
    half is missing."""
    sub = sent(T0)
    a, b = submission_artifact(sub), proof_artifact(proven(sub))
    assert a.name.split(".")[0] == b.name.split(".")[0]
    assert a.name.endswith(".submission.txt") and b.name.endswith(".proof.txt")


def test_a_submission_artifact_says_the_proof_is_missing():
    got = submission_artifact(sent(T0)).text
    assert "STILL MISSING" in got and "not evidence" in got


def test_the_register_never_renders_a_pending_line_as_blank():
    """Rule 13 in a document. A line a reader cannot resolve into an outcome is
    the same defect as a function returning `None` for unknown."""
    sub = sent(T0)
    got = reconcile([sub], [], CADENCE, through=T0 + WEEK, as_of=T0 + WEEK)
    text = register(got, CADENCE, through=T0 + WEEK).text
    assert "OVERDUE" in text and "NOTHING WAS SENT" in text
    assert "has not been witnessed" in text


def test_the_register_carries_no_lane_no_student_and_no_name():
    """Not by redaction. A status is built from an anchor, and an anchor has no
    field to put one in — `records/serving.py`'s argument applied to a page."""
    led = a_ledger(ben=4, ana=7)
    a = anchor_for_ledger(led, T0)
    sub = Submission(a, T0)
    got = reconcile([sub], [proven(sub)], CADENCE, through=T0, as_of=T0 + WEEK)
    text = register(got, CADENCE, through=T0).text
    for leak in (LB, LA, BEN, ANA, "Ben", "chair"):
        assert leak not in text, f"{leak} reached the published register"


def test_the_derivation_stays_local_and_says_so():
    """The other side of the same split. The working *does* name lanes and
    counts — that is what makes the anchor checkable — so it is marked local and
    is never what the register or the submission is built from."""
    led = a_ledger(ben=4, ana=7)
    a = anchor_for_ledger(led, T0)
    local = derivation_artifact(led, a)
    assert "NOT FOR PUBLICATION" in local.text
    assert LB in local.text and LA in local.text
    assert local.name.endswith(".local.txt")
    assert LB not in submission_artifact(Submission(a, T0)).text


# --- one anchor for the programme, not one per child ----------------------


def test_the_ledger_anchors_once_rather_than_once_per_lane():
    led = a_ledger(ben=4, ana=7)
    a = anchor_for_ledger(led, T0)
    assert isinstance(a, Anchor) and a.count == 11
    assert len(led.anchors()) == 2, "the ledger under test has two lanes"
    ok, why = permitted(a)
    assert ok, why


def test_a_kept_derivation_redeems_the_anchor_and_a_doctored_one_does_not():
    led = a_ledger(ben=4, ana=7)
    a = anchor_for_ledger(led, T0)
    ok, why = derives(ledger_derivation(led), a)
    assert ok, why

    rows = list(ledger_derivation(led))
    rows[0] = (rows[0][0], rows[0][1], rows[0][2] - 1)
    bad, why = derives(tuple(rows), a)
    assert not bad and "does not produce" in why


def test_an_empty_programme_anchors_to_something_rather_than_nothing():
    """§5: emptied and never-written are different facts, and a count of zero is
    the fact that says so."""
    a = anchor_for_ledger(Ledger(), T0)
    assert a.count == 0 and len(a.head) == 64


# --- what this does NOT do ------------------------------------------------


def test_this_module_CANNOT_publish_anything_documented_not_hidden():
    """**A limitation by design, asserted so it is not closed by accident.**

    Nothing here opens a socket, so nothing here submits anything. The seam is a
    deployment act: it takes `payload.commitment`, hands it to a witness, and
    hands back a `Proof`. A future edit that made this module perform the call
    itself would put an egress path in `records/`, which `tools/purity.py`
    refuses — this test says the same thing in the module's own terms.
    """
    src = (Path(__file__).resolve().parent.parent / "records" / "publication.py")
    text = src.read_text(encoding="utf-8")
    for banned in ("import socket", "urllib", "requests", "subprocess", "http.client"):
        assert f"\n{banned}" not in text and f"import {banned}" not in text
    assert "No network" in text


def test_a_proven_anchor_still_CANNOT_prove_the_record_is_complete_documented():
    """**The limit no witness removes**, restated here because this module is
    where somebody will look for it. A proof attests to what the log contained.
    It says nothing about what the world contained.

    Two publications, one over a log missing an inconvenient entry, are
    indistinguishable — and both read PROVEN.
    """
    full, short = a_log(4), a_log(3)
    a, b = Submission(anchor_for(full, T0), T0), Submission(anchor_for(short, T0), T0)
    for sub in (a, b):
        got = reconcile([sub], [proven(sub)], CADENCE, through=T0, as_of=T0 + WEEK)
        assert got[0].state is Publication.PROVEN, (
            "if this ever fails, publication has started proving completeness and "
            "this test should be rewritten rather than deleted"
        )


def test_the_module_is_not_broken_shut():
    sub = sent(T0)
    assert isinstance(payload_for(sub.anchor, CADENCE), Payload)
    got = reconcile([sub], [proven(sub)], CADENCE, through=T0, as_of=T0 + WEEK)
    assert got[0].is_witness and len(receipts(got)) == 1


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
