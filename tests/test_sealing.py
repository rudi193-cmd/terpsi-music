"""The seal cascade, and every way to get a machine answer served without a human.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.sealing import (  # noqa: E402
    Record, State, authored_by, draft, redraft, reject, seal,
)

T0 = datetime(2026, 3, 1)
BEN = "student-ben"


def a_draft(body="GE2 phrasing improved through bar 40.") -> Record:
    return draft(BEN, "adjudication_commentary", body)


def test_a_machine_answer_is_a_draft_and_is_not_servable():
    d = a_draft()
    assert d.state is State.DRAFT
    assert not d.servable, "a machine answer was servable without a human"


def test_sealing_needs_a_name_and_a_role_is_not_a_name():
    d = a_draft()
    for who in ("", "   ", "system", "the director", "Director", "bot", "role:director"):
        try:
            seal(d, by=who, at=T0)
        except ValueError:
            continue
        raise AssertionError(f"{who!r} was accepted as a sealer — §8.2 needs a person")
    assert seal(d, by="Alex Okonkwo", at=T0).servable


def test_a_seal_does_not_survive_an_edit_to_what_was_sealed():
    """The quiet way a seal becomes meaningless: seal the text, then change it.
    The digest is over the body, so an edited record is no longer sealed."""
    sealed = seal(a_draft(), by="Alex Okonkwo", at=T0)
    assert sealed.servable
    edited = Record(sealed.subject_id, sealed.kind, "GE2 was outstanding.",
                    sealed.state, sealed.sealed_by, sealed.sealed_at,
                    sealed.reason, sealed.over)
    assert not edited.servable, "an edited body inherited its predecessor's seal"


def test_a_rejection_is_as_durable_as_an_approval():
    """Rule 10, and the half most cascades omit."""
    r = reject(a_draft(), by="Alex Okonkwo", at=T0, reason="not what the judge said")
    assert r.state is State.REJECTED
    assert r.sealed_by == "Alex Okonkwo" and r.sealed_at == T0
    assert r.reason == "not what the judge said"
    assert not r.servable


def test_a_rejection_without_a_reason_is_not_a_disposition():
    for reason in ("", "   "):
        try:
            reject(a_draft(), by="Alex Okonkwo", at=T0, reason=reason)
        except ValueError:
            continue
        raise AssertionError("a reasonless rejection was accepted (I-6)")


def test_a_rejected_record_cannot_be_sealed_into_existence():
    """The path that would erase the rejection: reject, then seal the same
    object. Re-drafting is the sanctioned route, and it leaves the rejection
    standing as a separate record."""
    r = reject(a_draft(), by="Alex Okonkwo", at=T0, reason="wrong")
    try:
        seal(r, by="Alex Okonkwo", at=T0)
    except ValueError:
        pass
    else:
        raise AssertionError("a rejected record was sealed — the rejection vanished")

    again = redraft(r, "GE2 phrasing improved through bar 36.")
    assert again.state is State.DRAFT
    assert r.state is State.REJECTED, "re-drafting mutated the rejection"


def test_pending_is_distinct_from_draft():
    """Nothing has answered yet, versus a machine answered and nobody reviewed.
    Collapsing them makes an unstarted transcript look like an unreviewed one."""
    p = Record(BEN, "transcript", "")
    assert p.state is State.PENDING and not p.servable
    assert a_draft().state is State.DRAFT


def test_there_is_no_auto_seal_path():
    """Static: no function in the module seals without a caller-supplied name."""
    import inspect

    from records import sealing
    src = inspect.getsource(sealing)
    assert "def seal(rec: Record, *, by: str, at: datetime)" in src, (
        "seal()'s signature changed; `by` must stay required and keyword-only"
    )
    assert "by: str = " not in src, "seal() grew a default sealer"


# --- I-7: the record binds the holder most ---------------------------------
#
# `docs/LANE-MODEL.md` listed the supersession asymmetry as stated and
# unenforced. `reject()` and `redraft()` are where a `lane_entry` is ended and
# amended in this tree, so this is where the clause lands.


def bens_own_account(body="I told Mr Nguyen before we boarded.") -> Record:
    """An entry the governed authored about the office — I-7's protected shape."""
    return authored_by(BEN, BEN, "incident_account", body)


def test_the_office_cannot_reject_the_students_own_account():
    """**The forbidden act, and it used to succeed.** Rejection is terminal here
    — `seal()` refuses a rejected record — so a director able to reject a
    student's account of an incident makes it permanently unservable without
    deleting a row. That is *amending an entry about the office's own exercise*
    by the only spelling this module offers."""
    try:
        reject(bens_own_account(), by="dana-reyes", at=T0,
               reason="does not match the staff account")
    except PermissionError as exc:
        assert "I-7" in str(exc)
        return
    raise AssertionError("the office rejected the ward's own entry")


def test_the_office_cannot_rewrite_the_students_own_account_either():
    """The clause forbids *deleting or amending*, and re-drafting somebody
    else's words is the amendment. `by=None` is not the author, so an office
    that names nobody is refused exactly like one that names itself."""
    for who in (None, "dana-reyes", "Alex Okonkwo"):
        try:
            redraft(bens_own_account(), "I did not say anything.", by=who)
        except PermissionError:
            continue
        raise AssertionError(f"{who!r} rewrote the ward's own entry")


def test_the_student_may_supersede_their_own_entry():
    """The companion assertion. A guard that refused everybody would pass the
    two above — I-7 makes the entry durable against the office, not frozen."""
    again = redraft(bens_own_account(), "I told him at the bus, not the band room.",
                    by=BEN)
    assert again.state is State.DRAFT and again.author_id == BEN
    withdrawn = reject(bens_own_account(), by=BEN, at=T0, reason="I got the day wrong")
    assert withdrawn.state is State.REJECTED


def test_no_edge_and_no_grant_turns_the_answer_around():
    """*"An authority that no office-derived grant confers"* — so the refusal
    branch consults no edges at all. A predicate that read them could be
    defeated by whoever holds the most."""
    import inspect
    from records.standing import Supersession, may_supersede

    guardian = [__import__("records").Edge("guardian_of", "g-mother", BEN,
                                           T0, created_at=T0)]
    check = may_supersede(author_id=BEN, subject_id=BEN, principal_id="g-mother",
                          edges=guardian, at=T0)
    assert check.state is Supersession.REFUSED and not check.permitted
    assert "edges" in inspect.signature(may_supersede).parameters, (
        "the parameter went away, so the refusal can no longer be shown to ignore it"
    )


def test_a_machine_draft_stays_the_offices_to_reject():
    """The asymmetry is the content of the clause. An unauthored transcription
    is `UNKNOWN` rather than refused, and the office's own cascade is
    untouched — otherwise I-7 would read *entries are immutable*."""
    d = a_draft()
    assert d.author_id is None
    assert reject(d, by="dana-reyes", at=T0, reason="mis-transcribed").state \
        is State.REJECTED
    assert redraft(d, "GE2 phrasing improved through bar 44.").state is State.DRAFT


def test_an_authored_entry_names_its_author():
    for bad in ("", "   "):
        try:
            authored_by(BEN, bad, "incident_account", "text")
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as an author; I-7 turns on it")


def test_authorship_survives_the_cascade():
    """A seal or a rejection that dropped `author_id` would make the guard fire
    once and never again, which is the *cannot fire* mode §16 names."""
    mine = bens_own_account()
    assert seal(mine, by="Alex Okonkwo", at=T0).author_id == BEN
    assert reject(mine, by=BEN, at=T0, reason="withdrawn").author_id == BEN
    assert redraft(mine, "another go", by=BEN).author_id == BEN


def test_the_cascade_is_not_broken_shut():
    """Negative control: a cascade where nothing is ever servable would pass
    every assertion above."""
    assert seal(a_draft(), by="Alex Okonkwo", at=T0).servable
    assert seal(bens_own_account(), by="Alex Okonkwo", at=T0).servable, (
        "sealing is not superseding; a signature on the ward's account destroys nothing"
    )


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
