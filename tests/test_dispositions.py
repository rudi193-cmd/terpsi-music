"""Rule 15 and I-6: every ask gets a dated disposition, and silence is not one.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import inspect
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import dispositions  # noqa: E402
from records.dispositions import (  # noqa: E402
    Disposition, answer, ask, extend, state_at,
)

T0 = datetime(2026, 3, 1)
BEN = "student-ben"


def a_request(**kw):
    base = dict(asked_by="g-mother", asked_at=T0, within=timedelta(days=14),
                office="fees", escalates_to="director")
    base.update(kw)
    return ask(BEN, "fee_waiver", **base)


def test_a_timebound_is_required_at_issuance_and_has_no_default():
    """P-2: *"no system-wide default is proposed — a default would let issuers
    stop declaring."* So `within` must be passed explicitly."""
    params = inspect.signature(ask).parameters
    assert params["within"].default is inspect.Parameter.empty, (
        "ask() grew a default timebound; issuers will stop declaring one"
    )
    for bad in (timedelta(0), timedelta(days=-1)):
        try:
            a_request(within=bad)
        except ValueError:
            continue
        raise AssertionError(f"a timebound of {bad} was accepted")


def test_silence_becomes_an_answer_at_the_timebound_with_the_wait_recorded():
    r = a_request()
    assert state_at(r, T0 + timedelta(days=13)).disposition is Disposition.OPEN
    late = state_at(r, T0 + timedelta(days=20))
    assert late.disposition is Disposition.ESCALATED
    assert late.answered_by == "director"
    assert "20 days" in late.reason or "after" in late.reason
    assert late.answered_at == r.due_by, "escalation should date from the deadline"


def test_escalation_needs_no_scheduler():
    """Evaluated at an instant, like every other predicate here. No sweep, no
    job, no state transition anyone must remember to run."""
    r = a_request()
    assert state_at(r, T0 + timedelta(days=1)).disposition is Disposition.OPEN
    assert state_at(r, T0 + timedelta(days=99)).disposition is Disposition.ESCALATED
    assert r.disposition is Disposition.OPEN, "state_at mutated the request"


def test_an_office_cannot_lengthen_its_own_timebound():
    """I-6's last clause, and the one most likely to be quietly dropped —
    self-extension turns a guarantee into a preference."""
    r = a_request()
    try:
        extend(r, by="fees", to=T0 + timedelta(days=60), why="busy season")
    except ValueError as exc:
        assert "cannot extend its own" in str(exc)
    else:
        raise AssertionError("the owing office extended its own deadline")

    ok = extend(r, by="director", to=T0 + timedelta(days=30), why="awaiting documents")
    assert ok.due_by == T0 + timedelta(days=30)
    assert ok.extensions and ok.extensions[0][0] == "director"


def test_an_extension_is_recorded_not_merely_applied():
    r = extend(a_request(), by="director", to=T0 + timedelta(days=30), why="documents")
    r2 = extend(r, by="director", to=T0 + timedelta(days=45), why="still waiting")
    assert len(r2.extensions) == 2, "an extension overwrote its predecessor"
    assert [e[3] for e in r2.extensions] == ["documents", "still waiting"]


def test_an_extension_cannot_move_the_deadline_earlier():
    """Shortening is not extension, and would let an office manufacture an
    escalation it wanted."""
    try:
        extend(a_request(), by="director", to=T0 + timedelta(days=1), why="x")
    except ValueError:
        return
    raise AssertionError("an 'extension' moved the deadline earlier")


def test_an_office_cannot_be_its_own_escalation_basis():
    """Escalation that returns the request to the party that did not answer it
    is a loop wearing a guarantee."""
    try:
        a_request(office="fees", escalates_to="fees")
    except ValueError:
        return
    raise AssertionError("an office was accepted as its own escalation basis")


def test_a_disposition_needs_a_name_and_a_reason_either_way():
    """Rule 10: rejections recorded as durably as approvals."""
    for granted in (True, False):
        for by, reason in (("", "ok"), ("clerk", ""), ("  ", "  ")):
            try:
                answer(a_request(), granted=granted, by=by, at=T0, reason=reason)
            except ValueError:
                continue
            raise AssertionError(f"an unsigned or unreasoned disposition was accepted")
    r = answer(a_request(), granted=False, by="clerk", at=T0, reason="income above threshold")
    assert r.disposition is Disposition.REFUSED and r.reason


def test_an_answered_request_cannot_be_answered_again():
    r = answer(a_request(), granted=True, by="clerk", at=T0, reason="qualifies")
    try:
        answer(r, granted=False, by="someone", at=T0, reason="changed my mind")
    except ValueError:
        return
    raise AssertionError("a disposition was overwritten")


def test_an_escalated_request_is_not_silently_reopened():
    r = state_at(a_request(), T0 + timedelta(days=20))
    assert state_at(r, T0 + timedelta(days=21)).disposition is Disposition.ESCALATED


def test_the_module_is_not_broken_shut():
    r = answer(a_request(), granted=True, by="clerk", at=T0, reason="qualifies")
    assert r.disposition is Disposition.GRANTED
    assert state_at(r, T0 + timedelta(days=99)).disposition is Disposition.GRANTED, (
        "an answered request escalated anyway"
    )


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
