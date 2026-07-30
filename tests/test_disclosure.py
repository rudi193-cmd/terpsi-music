"""The disclosure log, attacked.

PR #3 found by executing the DDL that a table called append-only in a comment
accepted `UPDATE` and `DELETE`. This asserts the property rather than the
comment, and adds the one the chain alone does not give: truncation.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Outcome, Principal, Rung, serve  # noqa: E402
from records.disclosure import Log, verify_against  # noqa: E402

T0 = datetime(2026, 3, 1)
BEN = "student-ben"


def a_read(purposes=frozenset(), rung=Rung.L3, **kw):
    fld = Field(lane_id="lane-ben", subject_id=BEN, name="chair", rung=rung,
                payload="Ben Alvarez · trumpet 2",
                instruction="one member of this section", **kw)
    edges = [Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)]
    return serve(fld, Principal("g-mother", purposes), edges, T0)


def a_log(n=3) -> Log:
    log = Log()
    for i in range(n):
        log = log.record(a_read(), principal_id="g-mother", subject_id=BEN,
                         field_name="chair", at=T0 + timedelta(minutes=i))
    return log


# --- append-only, enforced -------------------------------------------------


def test_there_is_no_method_that_rewrites_or_removes_an_entry():
    """The property PR #3 found missing when it ran the DDL. Checked over the
    type rather than trusted to a comment."""
    forbidden = {"update", "delete", "remove", "pop", "clear", "insert", "__setitem__"}
    assert not (forbidden & set(dir(Log))), f"Log exposes {forbidden & set(dir(Log))}"
    assert Log.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_an_entry_cannot_be_edited_in_place():
    log = a_log()
    try:
        log.entries[0].principal_id = "someone-else"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("an entry was rewritten in place")


def test_recording_returns_a_new_log_and_leaves_the_old_one_intact():
    first = a_log(2)
    second = first.record(a_read(), principal_id="g-mother", subject_id=BEN,
                          field_name="chair", at=T0 + timedelta(hours=1))
    assert len(first.entries) == 2 and len(second.entries) == 3
    assert first.verify()[0] and second.verify()[0]


# --- the chain -------------------------------------------------------------


def test_an_altered_entry_is_detected():
    log = a_log()
    tampered = dataclasses.replace(log.entries[1], principal_id="someone-else")
    broken = Log(log.entries[:1] + (tampered,) + log.entries[2:])
    ok, why = broken.verify()
    assert not ok and "altered" in why


def test_a_reordered_chain_is_detected():
    log = a_log()
    swapped = Log((log.entries[1], log.entries[0]) + log.entries[2:])
    assert not swapped.verify()[0]


def test_truncation_is_invisible_to_the_chain_alone_and_caught_by_the_anchor():
    """The one a hash chain does not give you. Lopping entries off the end
    leaves a shorter chain that verifies perfectly — which is why §5's count
    anchor exists, and why `verify()` alone is not the check."""
    log = a_log(5)
    anchor = log.anchor()

    lopped = Log(log.entries[:3])
    assert lopped.verify()[0], "a truncated chain should still self-verify — that is the point"

    ok, why = verify_against(lopped, anchor)
    assert not ok and "truncated" in why


def test_the_anchor_catches_a_rebuilt_prefix():
    """Rebuilding the log with different content but the same length would pass
    a count check alone. The anchored digest is what closes that."""
    log = a_log(4)
    anchor = log.anchor()
    rebuilt = Log()
    for i in range(4):
        rebuilt = rebuilt.record(a_read(), principal_id="someone-else", subject_id=BEN,
                                 field_name="chair", at=T0 + timedelta(minutes=i))
    assert rebuilt.verify()[0]
    assert not verify_against(rebuilt, anchor)[0]


# --- what the log must NOT do ----------------------------------------------


def test_the_log_does_not_store_the_disclosed_value():
    """A log carrying what was disclosed is a second copy of the thing it is
    auditing, at the same rung, in a table people treat as safe because it is
    'just the audit trail'."""
    log = a_log(1)
    e = log.entries[0]
    assert not hasattr(e, "payload") and not hasattr(e, "value")
    assert "Ben Alvarez" not in repr(e), "the disclosed value is in the log"


def test_a_refusal_and_an_absence_are_indistinguishable_in_the_log_too():
    """§7's guarantee, applied to the audit trail — the place it is easiest to
    break, because logging feels like a neutral act.

    If the log records something different for the student who declined than
    for the student with nothing to decline, the audit trail has re-created the
    signal the guarantee suppresses, and the log becomes the leak."""
    declined = Field(lane_id="lane-ben", subject_id=BEN, name="media_release",
                     rung=Rung.L4, category="health",
                     payload="media release refused", instruction=None)
    nothing = Field(lane_id="lane-ben", subject_id=BEN, name="media_release",
                    rung=Rung.L4, category="health", payload=None, instruction=None)
    edges = [Edge("staff_of", "staff-nguyen", BEN, T0, created_at=T0)]
    p = Principal("staff-nguyen")

    la = Log().record(serve(declined, p, edges, T0), principal_id="staff-nguyen",
                      subject_id=BEN, field_name="media_release", at=T0)
    lb = Log().record(serve(nothing, p, edges, T0), principal_id="staff-nguyen",
                      subject_id=BEN, field_name="media_release", at=T0)
    assert la.entries[0].digest == lb.entries[0].digest, (
        "the log distinguishes a refusal from an absence — §7's guarantee is broken "
        "by the audit trail"
    )


def test_every_outcome_is_recorded_not_only_disclosures():
    """Rule 10: an audit trail that logs only agreement is not one. A log that
    recorded only payloads could not answer 'was this restriction working'."""
    log = Log()
    for rung in (Rung.L3, Rung.L5):
        log = log.record(a_read(rung=rung), principal_id="g-mother", subject_id=BEN,
                         field_name="chair", at=T0)
    assert len(log.entries) == 2
    assert {e.outcome for e in log.entries} == {Outcome.PAYLOAD, Outcome.REFUSED}
    assert sum(1 for e in log.entries if e.disclosed) == 1


def test_the_log_is_not_broken_shut():
    """Negative control: a log that recorded nothing would pass every check."""
    log = a_log(3)
    assert len(log.entries) == 3 and log.verify()[0]
    assert verify_against(log, log.anchor())[0]


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
