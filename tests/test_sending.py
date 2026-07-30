"""The eleven gates of `docs/PLAN-GUARDIANSHIP.md`, attempted rather than described.

G4 and G7 are checked **statically over the source**, because they are
properties of the module rather than of behaviour at runtime — a signature is a
thing a future edit can widen, and a comment saying "do not widen it" is not a
middle.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import inspect
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge  # noqa: E402
from records import sending  # noqa: E402
from records.sending import (  # noqa: E402
    ContactRestriction, Payload, SendList, Standing, deliver, recipients, who_could_see,
)

BEN = "student-ben"
MAR = datetime(2026, 3, 1)
JUN = datetime(2026, 6, 1)
OCT = datetime(2026, 10, 1)


def mother() -> Edge:
    return Edge("guardian_of", "g-mother", BEN, datetime(2025, 8, 1), created_at=datetime(2025, 8, 1))


def father() -> Edge:
    return Edge("guardian_of", "g-father", BEN, datetime(2025, 8, 1), created_at=datetime(2025, 8, 1))


def order(valid_at=MAR, created_at=MAR, invalid_at=None) -> ContactRestriction:
    return ContactRestriction("g-father", BEN, valid_at, created_at, invalid_at,
                              authority="court order 44-B")


# --- G1, G2: dated restriction, history stays answerable -------------------


def test_G1_a_restricted_guardian_is_absent_after_the_restriction():
    who = recipients(BEN, [mother(), father()], [order()], MAR + timedelta(days=1))
    assert who.state is Standing.DERIVED
    assert tuple(who) == ("g-mother",)
    assert who.suppressed == (("g-father", "court order 44-B"),)


def test_G2_and_present_before_it():
    """History stays answerable. The same query at an earlier instant must
    still say what was true then, which is what `invalid_at` buys and a delete
    would have destroyed (refusal 3)."""
    who = recipients(BEN, [mother(), father()], [order()], MAR - timedelta(days=1))
    assert set(who) == {"g-mother", "g-father"}


def test_G3_a_future_dated_restriction_takes_effect_on_the_day_with_no_job_run():
    """No scheduler, no nightly sweep, no state transition. The predicate is
    evaluated at an instant and the answer changes because the instant did."""
    future = order(valid_at=OCT, created_at=MAR)
    assert set(recipients(BEN, [mother(), father()], [future], JUN)) == {"g-mother", "g-father"}
    assert tuple(recipients(BEN, [mother(), father()], [future], OCT)) == ("g-mother",)


# --- G5: the two clocks ----------------------------------------------------


def test_G5_an_order_dated_in_march_and_delivered_in_october():
    """A June disclosure evaluates differently against `valid_at` and
    `created_at`, and both are retrievable.

    This is the gate that makes bitemporality load-bearing rather than
    decorative: in June the send to the father was *correct on what was known*
    and *wrong on what was true*, and an audit has to be able to say which.
    """
    late = order(valid_at=MAR, created_at=OCT)
    edges = [mother(), father()]

    as_known_in_june = recipients(BEN, edges, [late], JUN, known_as_of=JUN)
    assert set(as_known_in_june) == {"g-mother", "g-father"}, (
        "the system knew of no order in June — it cannot retroactively have obeyed one"
    )

    as_true_in_june = recipients(BEN, edges, [late], JUN, known_as_of=OCT)
    assert tuple(as_true_in_june) == ("g-mother",), (
        "with October's knowledge, the June send was to a restricted guardian"
    )


def test_G6_created_at_is_immutable():
    """An update raises rather than silently rewriting when the system learned
    something. Enforced by the dataclass being frozen, which is the cheapest
    possible version and is checked so it stays that way."""
    r = order()
    try:
        r.created_at = JUN  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("created_at was rewritable — G6 is not enforced")


# --- G4, G7: properties of the source --------------------------------------


def test_G4_no_student_scoped_handler_declares_or_reads_a_recipient():
    """Static, over the source. `deliver()` must have no recipient parameter,
    and none may be introduced later."""
    params = set(inspect.signature(deliver).parameters)
    forbidden = {"to", "recipient", "recipients", "guardians", "addressees", "send_to"}
    assert not (params & forbidden), (
        f"deliver() grew a recipient parameter: {sorted(params & forbidden)} — G4 is broken"
    )
    assert set(inspect.signature(Payload.__init__).parameters) - {"self"} == {
        "subject_id", "at", "body"
    }, "Payload grew a field; a 'to' on the payload defeats G4 as surely as one on the handler"


def test_G7_there_is_no_delete_path_for_a_guardianship_edge():
    """Refusal 3, checked over the module's source rather than trusted."""
    src = Path(sending.__file__).read_text(encoding="utf-8")
    bad = re.findall(r"\b(DELETE\s+FROM|\.remove\(|\.pop\(|del\s+\w+\[)", src, re.I)
    assert not bad, f"a delete path appeared in the send module: {bad}"


def test_G9_no_grant_is_constructible_over_a_group():
    """W-2 at the read. `recipients()` takes a subject id and there is no
    signature that accepts a section, a roster or a list of students."""
    params = inspect.signature(recipients).parameters
    assert "subject_id" in params
    for name in ("subjects", "section", "roster", "group", "cohort"):
        assert name not in params, f"recipients() accepts {name!r} — W-2 is breached"
    # And a list passed as the id resolves to nobody rather than to everybody.
    who = recipients([BEN, "student-other"], [mother()], [], MAR)  # type: ignore[arg-type]
    assert tuple(who) == (), "a list of students matched edges — group scoping is possible"


# --- G11: the failure that must not read as permission ---------------------


def test_G11_an_errored_backend_is_unknown_not_no_restrictions():
    def broken():
        raise ConnectionError("consent store unreachable")

    who = recipients(BEN, [mother(), father()], broken, MAR)
    assert who.state is Standing.UNKNOWN
    assert who.guardians == ()
    assert "unreachable" in who.reason


def test_G11_an_unknown_send_list_cannot_be_iterated_into_silence():
    """The failure this shape exists to prevent: `for g in recipients(...)`
    quietly sending to nobody because a backend was down, which from the loop
    alone is indistinguishable from a student with no guardians."""
    def broken():
        raise ConnectionError("down")

    who = recipients(BEN, [mother()], broken, MAR)
    try:
        list(who)
    except RuntimeError as exc:
        assert "not derived" in str(exc)
        return
    raise AssertionError("an UNKNOWN send list iterated as empty — G11 is decorative")


def test_an_empty_derived_list_is_different_from_unknown():
    """The other half. A student genuinely without reachable guardians must
    still be iterable, or the distinction collapses in the other direction."""
    who = recipients(BEN, [], [], MAR)
    assert who.state is Standing.DERIVED
    assert list(who) == []


# --- G8, G10 ---------------------------------------------------------------


def test_G8_reinstatement_leaves_the_prior_restriction_readable_in_sequence():
    lifted = order(valid_at=MAR, created_at=MAR, invalid_at=JUN)
    assert tuple(recipients(BEN, [mother(), father()], [lifted], MAR + timedelta(days=1))) \
        == ("g-mother",)
    assert set(recipients(BEN, [mother(), father()], [lifted], OCT)) \
        == {"g-mother", "g-father"}, "reinstatement did not restore reachability"
    assert lifted.valid_at == MAR, "the prior restriction lost its dates on reinstatement"


def test_G10_who_could_see_answers_with_a_reason_including_the_suppressed():
    rows = who_could_see(BEN, [mother(), father()], [order()], MAR + timedelta(days=1))
    by_id = {r[0]: r for r in rows}
    assert by_id["g-mother"][1] is True
    assert by_id["g-father"][1] is False, "the restricted guardian vanished from the answer"
    assert "court order 44-B" in by_id["g-father"][2], (
        "a suppression with no stated reason cannot be checked"
    )


# --- the send path ---------------------------------------------------------


def test_deliver_sends_only_to_the_derived_list():
    sent = []
    who = deliver(Payload(BEN, MAR + timedelta(days=1), "Bus leaves at 6."),
                  [mother(), father()], [order()], lambda to, body: sent.append(to))
    assert sent == ["g-mother"]
    assert who.suppressed and who.suppressed[0][0] == "g-father"


def test_deliver_refuses_to_send_at_all_when_the_list_is_unknown():
    """Fail closed on the send path. A partial send is worse than none: the
    guardian who *was* reached cannot be un-reached."""
    sent = []

    def broken():
        raise TimeoutError("consent store")

    try:
        deliver(Payload(BEN, MAR, "Bus leaves at 6."), [mother()], broken,
                lambda to, body: sent.append(to))
    except RuntimeError:
        assert sent == [], "a message went out while the restriction set was unknown"
        return
    raise AssertionError("deliver() sent with an unknown recipient set")


# --- two gates the plan does not have, found by ablation -------------------
#
# Mutating `records/sending.py` to ignore guardianship-edge dates, and to treat
# every edge kind as a recipient, both left the suite green. Neither is covered
# by G1-G11: every gate in the plan is about a *restriction*, and none is about
# the standing edge itself. Proposed as G12 and G13; see §18 item 13.


def test_G12_an_ended_guardianship_is_not_messaged():
    """Refusal 3: guardianship ends by setting `invalid_at`. The send path must
    honour that as strictly as the read path does — an ex-guardian who is still
    receiving location messages about a minor is the exact harm §7.1 is for.

    G1-G11 test restrictions on a *live* guardian. None ends the guardianship.
    """
    ended = Edge("guardian_of", "g-father", BEN, datetime(2025, 8, 1), invalid_at=MAR, created_at=datetime(2025, 8, 1))
    who = recipients(BEN, [mother(), ended], [], OCT)
    assert tuple(who) == ("g-mother",), "an ended guardianship still received a message"
    assert set(recipients(BEN, [mother(), ended], [], datetime(2026, 1, 1))) == {
        "g-mother", "g-father"
    }, "history stopped being answerable for the standing edge"


def test_G13_only_guardians_are_messaged_not_every_edge_holder():
    """A judge holds a live `judge_at` edge and a clinician a `clinician_for`.
    Neither is a recipient of a student-scoped message, and nothing in G1-G11
    says so — a predicate that messaged every edge holder passed every gate.

    *"Ben will be at the away game in Dayton until 10pm"* delivered to a judge
    is a live location disclosure about a minor, pushed to a device,
    unrecallable (§4.1).
    """
    others = [
        Edge("judge_at", "judge-okonkwo", BEN, datetime(2025, 8, 1), created_at=datetime(2025, 8, 1)),
        Edge("clinician_for", "clin-reyes", BEN, datetime(2025, 8, 1), created_at=datetime(2025, 8, 1)),
        Edge("staff_of", "staff-nguyen", BEN, datetime(2025, 8, 1), created_at=datetime(2025, 8, 1)),
        Edge("director_of", "director-shaw", BEN, datetime(2025, 8, 1), created_at=datetime(2025, 8, 1)),
    ]
    who = recipients(BEN, [mother()] + others, [], MAR)
    assert tuple(who) == ("g-mother",), (
        f"a non-guardian was messaged about a student: {tuple(who)}"
    )


# --- negative control ------------------------------------------------------


def test_the_predicate_is_not_broken_shut():
    """Every refusal above is vacuous if nobody is ever reachable."""
    who = recipients(BEN, [mother(), father()], [], MAR)
    assert set(who) == {"g-mother", "g-father"}


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}\n{exc}\n")
    raise SystemExit(1 if failures else 0)
