"""W-7, which was quoted in four documents and enforced by nobody.

**Found by inventory, 2026-07-31.** `records/conflict.py` had three ablation
mutations and no suite of its own — they all pointed at `tests/test_practice.py`,
because W-7 arrived while item 9 was being closed and its tests were written
where the work happened.

That is not a correctness gap: the guards were red. It is a *findability* gap,
and this repository has a name for the shape. Somebody grepping for what covers
W-7 finds a practice-logging suite, and the clause that says **the system
presents and a human decides** looks like a detail of streak counting. A clause
with no file of its own is one refactor from being moved somewhere worse.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.conflict import (  # noqa: E402
    Escalation, NotComputable, Precedent, Stake, as_consideration, halt,
    one_lane, ratify, refuse_to_rank, resolve,
)

BEN, ANA = "student-ben", "student-ana"
NOW = datetime(2026, 3, 20)


def test_an_escalation_cannot_carry_a_recommendation():
    """The refusal is structural: there is no field for an order and reaching
    for a recommendation gets the clause, not an AttributeError somebody papers
    over with getattr(..., None)."""
    e = halt(Stake.BETWEEN_WARDS, decision="last chair, trumpet",
             affects=[BEN, ANA], to_whom="dir-dana", at=NOW,
             considerations=["Ben has the earlier audition date",
                             "Ana covered the part in October"])
    assert "recommendation" not in {f.name for f in dataclasses.fields(Escalation)}
    try:
        e.recommendation
    except NotComputable as exc:
        assert "W-7" in str(exc)
        return
    raise AssertionError("an escalation produced a recommendation")


def test_considerations_are_unordered_so_they_cannot_be_handed_over_ranked():
    e = halt(Stake.BETWEEN_WARDS, decision="d", affects=[BEN, ANA],
             to_whom="dir-dana", at=NOW, considerations=["a", "b", "c"])
    assert isinstance(e.considerations, frozenset)


def test_the_staff_convenience_half_is_representable():
    """CLAUDE.md refusal 6 carries both halves and the second is the one that
    gets dropped: a rehearsal time or a route that is easier to run and worse
    for one student."""
    e = halt(Stake.WARD_VS_CONVENIENCE,
             decision="moving Tuesday sectionals to 6am to free the gym",
             affects=[BEN], to_whom="dir-dana", at=NOW)
    assert e.stake is Stake.WARD_VS_CONVENIENCE and e.affects == (BEN,)


def test_an_escalation_goes_to_a_named_person_never_a_role():
    for bad in ("staff", "the director", "an adult", "system", "  "):
        try:
            halt(Stake.WARD_VS_CONVENIENCE, decision="d", affects=[BEN],
                 to_whom=bad, at=NOW)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} received an escalation")


def test_a_collision_between_wards_names_two():
    try:
        halt(Stake.BETWEEN_WARDS, decision="d", affects=[BEN], to_whom="dir-dana",
             at=NOW)
    except ValueError:
        return
    raise AssertionError("one name was accepted as a collision between wards")


def test_an_escalation_must_say_what_was_being_decided():
    for bad in ("", "   "):
        try:
            halt(Stake.WARD_VS_CONVENIENCE, decision=bad, affects=[BEN],
                 to_whom="dir-dana", at=NOW)
        except ValueError:
            continue
        raise AssertionError("an escalation with no decision was accepted")


def test_refuse_to_rank_has_one_spelling():
    """Repeating an inline raise at each call site is how one of them ends up
    returning a sorted list during a busy afternoon."""
    try:
        refuse_to_rank("anything", [BEN, ANA])
    except NotComputable:
        return
    raise AssertionError("refuse_to_rank returned")


def test_one_lane_refuses_a_mixed_row_set_rather_than_filtering():
    """The middle three modules share (rule 12). Silently dropping the other
    lane's rows returns a number that looks like an own-lane statistic and is
    not — and the mixed set is the raw material for a ranking."""
    from dataclasses import dataclass

    @dataclass
    class Row:
        lane_id: str
        subject_id: str

    assert one_lane([Row("lane-ben", BEN), Row("lane-ben", BEN)], "a total") == "lane-ben"
    try:
        one_lane([Row("lane-ben", BEN), Row("lane-ana", ANA)], "a total")
    except NotComputable as exc:
        assert "a total" in str(exc)
    else:
        raise AssertionError("a mixed row set produced a lane")
    try:
        one_lane([], "a total")
    except ValueError:
        return
    raise AssertionError("an empty row set produced a lane")


def test_the_module_is_not_broken_shut():
    e = halt(Stake.WARD_VS_CONVENIENCE, decision="6am sectionals", affects=[BEN],
             to_whom="dir-dana", at=NOW)
    assert e.affects == (BEN,) and e.stake is Stake.WARD_VS_CONVENIENCE


# --- W-7's constructive half: precedent (PART-III-READ item 2) ---------------

LATER = datetime(2026, 3, 21)


def _decided(**kw):
    """An escalation resolved by the named human it went to."""
    e = halt(Stake.BETWEEN_WARDS, decision="last chair, trumpet",
             affects=[BEN, ANA], to_whom="dir-dana", at=NOW)
    return resolve(e, resolution=kw.get("resolution", "chose the earlier "
                   "audition date, having heard both"),
                   decided_by=kw.get("decided_by", "dir-dana"), at=LATER)


def test_a_recorded_precedent_is_not_standing_until_ratified():
    """'None takes force without signature' — resolve() records, it does not
    ratify; only a guardian's signature makes a precedent stand."""
    p = _decided()
    assert isinstance(p, Precedent) and p.standing is False
    r = ratify(p, signed_by="guardian-gemma", at=datetime(2026, 3, 22))
    assert r.standing is True and r.resolution == p.resolution


def test_a_precedent_carries_no_recommendation_for_a_new_case():
    """Refusal 6, one indirection later: a ratified precedent is the tempting
    place to reach for 'so do that again', and it raises like the escalation."""
    r = ratify(_decided(), signed_by="guardian-gemma", at=datetime(2026, 3, 22))
    assert "recommendation" not in {f.name for f in dataclasses.fields(Precedent)}
    try:
        r.recommendation
    except NotComputable as exc:
        assert "W-7" in str(exc)
        return
    raise AssertionError("a precedent produced a recommendation for a new case")


def test_an_unratified_precedent_cannot_be_cited_as_a_consideration():
    """A merely recorded resolution has no standing to be cited as one; letting
    it in would be a precedent taking force without the signature the clause
    requires."""
    try:
        as_consideration(_decided())
    except NotComputable as exc:
        assert "no force" in str(exc)
        return
    raise AssertionError("an unratified precedent was cited as a consideration")


def test_a_standing_precedent_surfaces_only_as_an_unordered_consideration():
    """The one way a precedent touches a later conflict — and the weakest: a
    plain string in the next escalation's unordered frozenset, no arrow at an
    answer. Assembling considerations is not ranking them."""
    r = ratify(_decided(), signed_by="guardian-gemma", at=datetime(2026, 3, 22))
    cite = as_consideration(r)
    assert isinstance(cite, str) and "earlier audition" in cite
    e = halt(Stake.BETWEEN_WARDS, decision="last chair again, next season",
             affects=[BEN, ANA], to_whom="dir-dana", at=LATER,
             considerations=[cite, "Ana covered the part in October"])
    assert isinstance(e.considerations, frozenset) and cite in e.considerations
    # the precedent entered as context, not as a ruling: the new escalation
    # still cannot be asked for an order.
    try:
        e.recommendation
    except NotComputable:
        return
    raise AssertionError("a precedent-informed escalation produced a recommendation")


def test_a_role_cannot_ratify_a_precedent():
    """'The guardian may ratify' — a role is how a ratification reaches nobody."""
    p = _decided()
    for bad in ("the guardian", "system", "staff", "  "):
        try:
            ratify(p, signed_by=bad, at=datetime(2026, 3, 22))
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} ratified a precedent")


def test_an_affected_ward_cannot_ratify_its_own_precedent():
    """W-4: a ward may request, never authorize. A student named in the
    conflict cannot sign the precedent of their own conflict into standing."""
    p = _decided()
    try:
        ratify(p, signed_by=BEN, at=datetime(2026, 3, 22))
    except ValueError:
        return
    raise AssertionError("an affected ward ratified its own precedent")


def test_a_precedents_decider_is_a_named_person():
    """A W-7 resolution is a named human's decision; a role decided nothing."""
    e = halt(Stake.BETWEEN_WARDS, decision="d", affects=[BEN, ANA],
             to_whom="dir-dana", at=NOW)
    for bad in ("system", "the director", "staff", "  "):
        try:
            resolve(e, resolution="x", decided_by=bad, at=LATER)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was recorded as deciding a conflict")


def test_an_affected_ward_cannot_be_recorded_as_the_decider():
    """W-4 again, on the deciding end: a student cannot be the one who decided
    their own conflict."""
    e = halt(Stake.BETWEEN_WARDS, decision="d", affects=[BEN, ANA],
             to_whom="dir-dana", at=NOW)
    try:
        resolve(e, resolution="x", decided_by=BEN, at=LATER)
    except ValueError:
        return
    raise AssertionError("an affected ward was recorded as deciding its own conflict")


def test_a_rejection_is_recorded_as_durably_as_an_approval():
    """Rule 10: an audit trail that logs only agreement is not one. 'Declined to
    split the section' is a resolution, and an empty one is not."""
    p = _decided(resolution="declined to move the sectional; the route change "
                 "was worse for Ben and only easier to run")
    assert p.resolution.startswith("declined")
    e = halt(Stake.WARD_VS_CONVENIENCE, decision="d", affects=[BEN],
             to_whom="dir-dana", at=NOW)
    for empty in ("", "   "):
        try:
            resolve(e, resolution=empty, decided_by="dir-dana", at=LATER)
        except ValueError:
            continue
        raise AssertionError("an empty resolution was accepted as a decided case")


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
