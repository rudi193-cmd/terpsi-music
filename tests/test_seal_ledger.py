"""The seal ledger, attacked: a forged `Record` and a tampered `Entry`.

Mirrors `tests/test_disclosure.py`'s attacks (edit, reorder, no rewrite
method) and adds the ones specific to this module: a chain refuses to be
extended once it is broken, and a `Record` built by hand rather than by
`records/sealing.seal()` reports `servable=True` while `unverifiable()` still
finds it.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.sealing import Record, State, draft, reject, seal  # noqa: E402
from records.seal_ledger import (  # noqa: E402
    ChainTampered, Entry, Ledger, Log, attested, enforced_servable, unverifiable,
)

T0 = datetime(2026, 3, 1)
BEN = "student-ben"
MAYA = "student-maya"


def a_draft(subject=BEN, body="GE2 phrasing improved through bar 40.") -> Record:
    return draft(subject, "adjudication_commentary", body)


def _digest_of(body: str) -> str:
    import hashlib
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# --- honest path -------------------------------------------------------


def test_a_sealed_record_is_appended_and_attested():
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    ledger = Ledger().append(sealed, at=T0)
    assert ledger.verify()[0]
    assert attested(sealed, ledger)
    assert enforced_servable(sealed, ledger)
    assert unverifiable([sealed], ledger) == ()


def test_a_rejection_is_appended_exactly_as_durably_as_a_seal():
    """Rule 10, at the ledger. The rejection is not less recorded than an
    approval would have been."""
    rejected = reject(a_draft(), by="Alex Okonkwo", at=T0, reason="not what the judge said")
    ledger = Ledger().append(rejected, at=T0)
    log = ledger.log_for(BEN)
    assert len(log.entries) == 1
    assert log.entries[0].event == "rejected"
    assert log.entries[0].reason == "not what the judge said"
    # A rejection is never servable, ledger or no ledger.
    assert not enforced_servable(rejected, ledger)


def test_a_draft_or_pending_record_has_nothing_to_attest():
    for rec in (a_draft(), Record(BEN, "transcript", "")):
        try:
            Ledger().append(rec, at=T0)
        except ValueError:
            continue
        raise AssertionError(f"{rec.state} record was appended — nothing happened yet")


# --- the ledger catches a forged Record ---------------------------------


def test_a_forged_record_reports_servable_but_is_not_attested():
    """The whole reason this module exists. `seal()` was never called — the
    Record is built directly, the way nothing in `records/sealing.py` stops
    anyone from doing. Its own `.servable` cannot tell the difference."""
    body = "GE2 phrasing improved through bar 40."
    forged = Record(BEN, "adjudication_commentary", body, State.SEALED,
                    sealed_by="Alex Okonkwo", sealed_at=T0, over=_digest_of(body))
    assert forged.servable, "the fixture is wrong: this must look servable on its face"

    empty_ledger = Ledger()
    assert not attested(forged, empty_ledger)
    assert not enforced_servable(forged, empty_ledger)
    assert unverifiable([forged], empty_ledger) == (forged,)


def test_unverifiable_finds_the_forged_row_and_not_the_honest_one():
    """`docs/ARCHITECTURE.md` §16's worked example, ported: `rita`'s row comes
    back `servable=True` because an entry backs it; `mallory`'s comes back
    `servable=False` because none does, even though both rows look identical
    on their own terms."""
    honest = seal(a_draft(subject="student-rita"), by="Alex Okonkwo", at=T0)
    ledger = Ledger().append(honest, at=T0)

    body = "forged phrase"
    forged = Record("student-mallory", "adjudication_commentary", body, State.SEALED,
                    sealed_by="Alex Okonkwo", sealed_at=T0, over=_digest_of(body))

    got = unverifiable([honest, forged], ledger)
    assert got == (forged,), f"expected only the forged row, got {got!r}"


# --- the chain itself ----------------------------------------------------


def test_an_altered_entry_is_detected():
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    log = Log().append(sealed, at=T0)
    tampered = dataclasses.replace(log.entries[0], by="mallory")
    broken = Log((tampered,))
    ok, why = broken.verify()
    assert not ok and "altered" in why


def test_a_reordered_chain_is_detected():
    log = Log()
    log = log.append(seal(a_draft(body="first"), by="Alex Okonkwo", at=T0), at=T0)
    log = log.append(seal(a_draft(body="second"), by="Alex Okonkwo", at=T0 + timedelta(minutes=1)),
                     at=T0 + timedelta(minutes=1))
    swapped = Log((log.entries[1], log.entries[0]))
    assert not swapped.verify()[0]


def test_there_is_no_method_that_rewrites_or_removes_an_entry():
    forbidden = {"update", "delete", "remove", "pop", "clear", "insert", "__setitem__"}
    assert not (forbidden & set(dir(Log))), f"Log exposes {forbidden & set(dir(Log))}"
    assert Log.__dataclass_params__.frozen  # type: ignore[attr-defined]
    assert Entry.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_an_entry_cannot_be_edited_in_place():
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    log = Log().append(sealed, at=T0)
    try:
        log.entries[0].by = "someone-else"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("an entry was rewritten in place")


# --- fail-closed: a broken chain refuses to be extended -------------------


def test_appending_onto_a_broken_chain_is_refused_not_warned():
    """§16: 'the ledger refuses rather than warns... a new entry can never
    launder a tampered history.' Checked directly: append() must raise, not
    print, not silently succeed, not return a Log that happens to verify."""
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    log = Log().append(sealed, at=T0)
    tampered = dataclasses.replace(log.entries[0], by="mallory")
    broken = Log((tampered,))
    assert not broken.verify()[0], "fixture is wrong: this chain must already be broken"

    second = seal(a_draft(body="a second, unrelated draft"), by="Alex Okonkwo",
                  at=T0 + timedelta(minutes=1))
    try:
        broken.append(second, at=T0 + timedelta(minutes=1))
    except ChainTampered:
        pass
    else:
        raise AssertionError("append() extended a chain it had already found broken")


def test_a_broken_chain_attests_to_nothing_it_contains():
    """The read-side half of fail-closed: even an entry that, read alone,
    looks like it matches a record must not count once the chain around it
    does not verify."""
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    log = Log().append(sealed, at=T0)
    tampered_entry = dataclasses.replace(log.entries[0])  # same fields
    # Break the chain by forging `prev` rather than the matching entry, so the
    # single entry that *would* match `sealed` is exactly the one sitting in
    # a broken chain.
    broken_head = dataclasses.replace(tampered_entry, prev="f" * 64)
    broken = Log((broken_head,))
    assert not broken.verify()[0]

    ledger = Ledger(((BEN, broken),))
    assert not attested(sealed, ledger), "a broken chain attested to an entry inside it"
    assert not enforced_servable(sealed, ledger)


# --- the machine-cannot-seal rule, enforced again at the ledger boundary --


def test_the_ledger_refuses_a_machine_attributed_disposition():
    """`seal()`/`reject()` already refuse this (`tests/test_sealing.py`). This
    checks the ledger refuses it too, for a `Record` that reached `append()`
    without ever going through either — the same forged-construction path
    `test_a_forged_record_reports_servable_but_is_not_attested` uses, but
    this time the forger tries to also get an entry appended."""
    body = "a machine wrote this and nobody reviewed it"
    forged = Record(BEN, "adjudication_commentary", body, State.SEALED,
                    sealed_by="system", sealed_at=T0, over=_digest_of(body))
    try:
        Ledger().append(forged, at=T0)
    except ValueError:
        pass
    else:
        raise AssertionError("the ledger attested a disposition credited to 'system'")


# --- per-subject partitioning (W-1) ---------------------------------------


def test_two_subjects_do_not_share_a_chain_or_leak_positions():
    ledger = Ledger()
    ledger = ledger.append(seal(a_draft(subject=BEN), by="Alex Okonkwo", at=T0), at=T0)
    ledger = ledger.append(seal(a_draft(subject=MAYA), by="Alex Okonkwo", at=T0), at=T0)
    ledger = ledger.append(seal(a_draft(subject=BEN, body="a second Ben entry"),
                                by="Alex Okonkwo", at=T0 + timedelta(minutes=1)),
                           at=T0 + timedelta(minutes=1))
    assert len(ledger.log_for(BEN).entries) == 2
    assert len(ledger.log_for(MAYA).entries) == 1
    assert ledger.log_for("student-nobody").entries == ()


def test_tampering_one_subjects_chain_does_not_verify_a_different_subject_as_broken():
    ledger = Ledger()
    ledger = ledger.append(seal(a_draft(subject=BEN), by="Alex Okonkwo", at=T0), at=T0)
    ledger = ledger.append(seal(a_draft(subject=MAYA), by="Alex Okonkwo", at=T0), at=T0)
    ben_log = ledger.log_for(BEN)
    tampered = dataclasses.replace(ben_log.entries[0], by="mallory")
    lanes = dict(ledger.lanes)
    lanes[BEN] = Log((tampered,))
    broken_ledger = Ledger(tuple(sorted(lanes.items())))

    assert broken_ledger.log_for(MAYA).verify()[0], "Maya's chain should be untouched"
    ok, why = broken_ledger.verify()
    assert not ok and BEN in why


# --- negative control: the detector is not broken shut --------------------


def test_the_detector_is_not_broken_shut():
    """If `unverifiable()` always came back non-empty, every assertion above
    that checks for an *empty* result would still pass. This is the case that
    catches that: an honest, fully-attested seal must never appear."""
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    ledger = Ledger().append(sealed, at=T0)
    assert unverifiable([sealed], ledger) == ()
    assert enforced_servable(sealed, ledger)


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
