"""Anchoring: what a witness buys, and the two things it does not.

The last section is the important one. It is written the way `corpus-lens`
writes `test_weekly_cadence_IS_reconstructable_documented_not_hidden` — tests
whose subject is a **limitation**, named so nobody later mistakes one for a bug
and closes the gap by deleting the assertion.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Principal, Rung, serve  # noqa: E402
from records.disclosure import Log  # noqa: E402
from records.witness import (  # noqa: E402
    Anchor, Evidence, Independence, Receipt, RecordingWitness, Standing,
    anchor_for, missing, schedule, standing,
)

T0 = datetime(2026, 3, 1)
WEEK = timedelta(days=7)
BEN = "student-ben"


def a_log(n=5) -> Log:
    fld = Field("lane-ben", BEN, "chair", Rung.L3, payload="Ben Alvarez",
                instruction="one member", provenance="P1")
    edges = [Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)]
    log = Log()
    for i in range(n):
        log = log.record(serve(fld, Principal("g-mother"), edges, T0),
                         principal_id="g-mother", subject_id=BEN,
                         field_name="chair", at=T0 + timedelta(minutes=i))
    return log


def receipt(log: Log, at=T0, kind="opentimestamps",
            independence=Independence.EVIDENTIARY) -> Receipt:
    return Receipt(anchor_for(log, at), kind, f"{kind}:ref", at, independence)


# --- the anchor carries nothing ------------------------------------------


def test_an_anchor_can_carry_only_a_digest_a_count_and_a_time():
    """The reason anchoring may cross the egress boundary at all. If an anchor
    could carry a subject id, publishing it would be a disclosure."""
    fields = {f.name for f in dataclasses.fields(Anchor)}
    assert fields == {"head", "count", "at"}
    for bad in ("not-a-digest", "", "z" * 64, "abc"):
        try:
            Anchor(bad, 1, T0)
        except ValueError:
            continue
        raise AssertionError(f"an anchor accepted {bad!r} as a head")


def test_an_anchor_matches_the_log_it_came_from():
    log = a_log(4)
    a = anchor_for(log, T0)
    assert a.count == 4 and a.head == log.entries[-1].digest


# --- an unwitnessed log is not evidence ------------------------------------


def test_a_log_nobody_has_witnessed_is_not_evidence():
    """Rule 13's shape applied to provability: there is no path returning
    WITNESSED for a record its author alone has ever seen."""
    e = standing(a_log(), [])
    assert e.standing is Standing.UNWITNESSED
    assert not e.is_evidence
    assert "proves nothing about when it was written" in e.reason


def test_a_convenient_test_double_cannot_be_counted_as_corroboration():
    """The failure a local witness invites. `RecordingWitness` is marked
    NON_EVIDENTIARY so a log witnessed only by the author's own process reads
    as unwitnessed rather than as fine."""
    log = a_log()
    w = RecordingWitness()
    r = w.publish(anchor_for(log, T0))
    assert r.independence is Independence.NON_EVIDENTIARY
    e = standing(log, [r])
    assert e.standing is Standing.UNWITNESSED
    assert "non-evidentiary" in e.reason


def test_a_witnessed_log_is_evidence_and_says_how_far():
    log = a_log(5)
    e = standing(log, [receipt(log)])
    assert e.standing is Standing.WITNESSED
    assert e.witnessed_to == 5 and e.is_evidence


def test_corroboration_counts_distinct_witnesses_not_receipts():
    """Two receipts from the same witness are one witness. An institution
    disputing a TSA disputes every receipt that TSA issued."""
    log = a_log()
    same = [receipt(log, T0), receipt(log, T0 + WEEK)]
    assert standing(log, same).corroborating_witnesses == 1
    mixed = [receipt(log, T0, "opentimestamps"), receipt(log, T0, "certified_mail")]
    assert standing(log, mixed).corroborating_witnesses == 2


# --- tampering, against a receipt rather than a self-supplied anchor -------


def test_truncation_after_witnessing_reads_as_tampered():
    """The attack §5 names, now with the anchor somewhere the same act cannot
    reach."""
    log = a_log(5)
    r = receipt(log)
    lopped = Log(log.entries[:2])
    assert lopped.verify()[0], "a truncated chain still self-verifies — that is the point"
    e = standing(lopped, [r])
    assert e.standing is Standing.TAMPERED and "witnessed 5" in e.reason


def test_a_rebuilt_log_of_the_same_length_reads_as_tampered():
    log = a_log(4)
    r = receipt(log)
    rebuilt = a_log(4)
    rebuilt = Log(tuple(dataclasses.replace(x, principal_id="someone-else")
                        for x in rebuilt.entries))
    e = standing(rebuilt, [r])
    assert e.standing is Standing.TAMPERED


def test_a_broken_chain_is_tampered_before_any_receipt_is_consulted():
    log = a_log(3)
    broken = Log(log.entries[:1] +
                 (dataclasses.replace(log.entries[1], principal_id="x"),) +
                 log.entries[2:])
    assert standing(broken, [receipt(log)]).standing is Standing.TAMPERED


# --- cadence is fixed, not activity-driven --------------------------------


def test_the_schedule_is_derived_from_the_calendar_not_from_the_log():
    """`corpus-lens`: content redaction does not scrub the shape of a week. A
    schedule computed from activity publishes the activity."""
    import inspect
    assert "log" not in inspect.signature(schedule).parameters, (
        "schedule() takes a log — the cadence would leak the shape of a week"
    )
    weeks = schedule(T0, T0 + timedelta(days=28), WEEK)
    assert len(weeks) == 5 and weeks[0] == T0


def test_a_missed_anchor_is_reported_rather_than_shrugged_off():
    log = a_log()
    on_time = [receipt(log, T0), receipt(log, T0 + WEEK), receipt(log, T0 + 3 * WEEK)]
    gaps = missing(on_time, T0, T0 + 3 * WEEK, WEEK)
    assert len(gaps) == 1 and gaps[0] == T0 + 2 * WEEK


def test_a_gapped_history_does_not_read_as_witnessed():
    """A witness log with holes nobody notices is the same as none."""
    log = a_log()
    e = standing(log, [receipt(log, T0), receipt(log, T0 + 3 * WEEK)],
                 start=T0, end=T0 + 3 * WEEK, every=WEEK)
    assert e.standing is Standing.GAPPED
    assert not e.is_evidence


def test_an_unbroken_cadence_reads_as_witnessed():
    log = a_log()
    rs = [receipt(log, T0 + i * WEEK) for i in range(4)]
    e = standing(log, rs, start=T0, end=T0 + 3 * WEEK, every=WEEK)
    assert e.standing is Standing.WITNESSED


# --- what this does NOT prove ---------------------------------------------


def test_anchoring_CANNOT_prove_everything_was_recorded_documented_not_hidden():
    """**A limitation, not a guarantee.**

    The institution's counter is not *"you forged that entry"* — it is *"you
    did not record the one that exonerates us."* Selective recording defeats
    every anchoring scheme, because an anchor attests to what a log contained,
    never to what the world contained.

    Two partial mitigations exist and are asserted below so they are not
    mistaken for a solution: recording happens at the predicate rather than by
    a human choosing to type, and refusals are logged as durably as
    disclosures, so a gap in a sequence is anomalous rather than invisible.

    Neither is proof. This test exists so that nobody reads `WITNESSED` as
    meaning the record is complete.
    """
    log = a_log(3)
    complete = standing(log, [receipt(log)])
    assert complete.standing is Standing.WITNESSED

    # The same log, with an inconvenient event simply never written. Anchored
    # at the shorter length, it is indistinguishable from an honest record.
    short = a_log(2)
    also_fine = standing(short, [receipt(short)])
    assert also_fine.standing is Standing.WITNESSED, (
        "if this ever fails, anchoring has started proving completeness and this "
        "test should be rewritten rather than deleted"
    )
    assert complete.standing == also_fine.standing


def test_anchoring_CANNOT_prove_the_anchor_was_published_when_it_says_documented():
    """The second limitation. `Receipt.accepted_at` is supplied by whoever
    built the receipt; only the witness's own external reference carries a time
    this system did not choose.

    So a receipt is worth exactly what its `witness_ref` can be redeemed for —
    an OpenTimestamps proof file, a TSA serial, a certified-mail number. A
    receipt whose ref cannot be checked outside is a note to self.
    """
    log = a_log()
    r = receipt(log, T0)
    forged = dataclasses.replace(r, accepted_at=datetime(2020, 1, 1))
    assert standing(log, [forged]).standing is Standing.WITNESSED, (
        "the module does not and cannot validate a witness's timestamp itself"
    )
    assert r.witness_ref, "a receipt with no external reference redeems nothing"


def test_the_module_is_not_broken_shut():
    """Negative control: a standing() that returned UNWITNESSED for everything
    would pass most of the assertions above."""
    log = a_log()
    assert standing(log, [receipt(log)]).is_evidence


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
