"""The seal cascade, and every way to get a machine answer served without a human.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.sealing import (  # noqa: E402
    Record, State, draft, redraft, reject, seal,
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


def test_the_cascade_is_not_broken_shut():
    """Negative control: a cascade where nothing is ever servable would pass
    every assertion above."""
    assert seal(a_draft(), by="Alex Okonkwo", at=T0).servable


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
