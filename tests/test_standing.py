"""§18 item 12: the subject's standing in their own lane.

Every guard here has a mutation in `tests/ablate.py`. Stdlib only.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Outcome, Principal, Rung, serve  # noqa: E402
from records.disclosure import Log  # noqa: E402
from records.standing import (  # noqa: E402
    SELF, SELF_CAP, LogAccess, Widening, is_self_edge, own_log,
    past_threshold, self_edge, widens,
)

T0 = datetime(2026, 3, 1)
LATER = T0 + timedelta(days=200)
BEN, LB = "student-ben", "lane-ben"
MAJORITY = datetime(2028, 6, 1)


def me(valid_at=T0, **kw):
    return self_edge(BEN, valid_at=valid_at, created_at=T0, **kw)


def mum(**kw):
    return Edge("guardian_of", "g-mother", BEN, T0, created_at=T0, **kw)


def chair(rung=Rung.L3, category=None):
    return Field(LB, BEN, "chair", rung, category=category,
                 payload="Ben Alvarez, trumpet 2",
                 instruction="one member of this section")


def health():
    return Field(LB, BEN, "allergy", Rung.L4, category="health",
                 payload="tree-nut anaphylaxis; carries epinephrine",
                 instruction="one student on this vehicle carries an auto-injector")


def signed(category="health", by="g-mother", subject=BEN):
    return Widening(subject, category, "the student asked to read their own file",
                    by, T0, T0 + timedelta(days=365))


# --- L1-L3: the subject reads their own record ----------------------------


def test_the_subject_reads_their_own_L3_field_in_full():
    """The behaviour item 12 was filed against. Ben sits in the chair."""
    s = serve(chair(), Principal(BEN), [me()], LATER)
    assert s.outcome is Outcome.PAYLOAD, (
        "the subject was served the derived form about their own name"
    )
    assert s.via_edge == SELF


def test_the_self_edge_is_dated_like_every_other_edge():
    """Refusal 3's shape: standing ends by `invalid_at`, never by deletion. A
    safety plan in which the subject is the risk is rare and real, and this is
    where it lives."""
    ended = me(invalid_at=T0 + timedelta(days=10))
    s = serve(chair(), Principal(BEN), [ended], LATER)
    assert s.outcome is Outcome.INSTRUCTION
    assert "no live entitlement edge" in s.reason

    before = serve(chair(), Principal(BEN), [me(valid_at=LATER)], T0)
    assert before.outcome is Outcome.INSTRUCTION


def test_the_read_names_the_self_edge_so_the_log_can_narrate_it():
    """The reason this is an edge and not a `principal.id == subject_id`
    special-case. §7.2 must answer "who could see this on October 12, and why";
    a special-case answers `via_edge=None`, which in the disclosure log is
    indistinguishable from an unentitled read."""
    s = serve(chair(), Principal(BEN), [me()], LATER)
    entry = Log().record(s, principal_id=BEN, subject_id=BEN,
                         field_name="chair", at=LATER).entries[0]
    assert entry.authority == SELF, "the log could not name the subject's own standing"


# --- the forged self edge -------------------------------------------------


def test_a_self_edge_held_by_somebody_else_is_not_an_edge():
    """The cheap attack: the kind names a relationship and nothing was checking
    that the relationship held."""
    forged = Edge(SELF, "staff-nguyen", BEN, T0, created_at=T0)
    assert not is_self_edge(forged)
    s = serve(chair(), Principal("staff-nguyen"), [forged], LATER)
    assert s.outcome is Outcome.INSTRUCTION, (
        "a forged self edge entitled a staff member through the subject's own door"
    )


def test_self_edge_constructor_cannot_produce_a_forged_one():
    e = self_edge(BEN, valid_at=T0, created_at=T0)
    assert is_self_edge(e) and e.principal_id == e.subject_id == BEN


# --- L4: the cap ----------------------------------------------------------


def test_the_subject_gets_the_instruction_at_L4_not_the_payload():
    s = serve(health(), Principal(BEN), [me()], LATER)
    assert s.outcome is Outcome.INSTRUCTION
    assert str(SELF_CAP) in s.reason and "guardian" in s.reason


def test_a_ward_declaring_a_purpose_over_itself_is_W4_and_unlocks_nothing():
    """**The load-bearing one.** W-4 is *a ward may request, never authorize*.
    A minor declaring a 'health' purpose over their own record is the ward
    authorizing itself, so `principal.purposes` is never consulted for a
    pre-threshold self edge. Reading it would be W-4 defeated by a keyword
    argument."""
    loud = Principal(BEN, frozenset({"health", "money", "discipline", "likeness"}))
    s = serve(health(), Principal(BEN), [me()], LATER)
    t = serve(health(), loud, [me()], LATER)
    assert t.outcome is s.outcome is Outcome.INSTRUCTION
    assert t.reason == s.reason, "declaring purposes over your own record changed the answer"


def test_a_guardian_signature_widens_it_for_that_category_only():
    w = signed("health")
    got = serve(health(), Principal(BEN), [me(), mum()], LATER, widenings=[w])
    assert got.outcome is Outcome.PAYLOAD
    assert got.via_purpose == "health" and "g-mother" in got.reason

    money = dataclasses.replace(health(), name="balance", category="money")
    assert serve(money, Principal(BEN), [me(), mum()], LATER,
                 widenings=[w]).outcome is Outcome.INSTRUCTION


def test_a_widening_is_checked_against_the_signers_standing_at_use():
    """Refusal 3 applied to a signature: a guardian whose standing has ended
    cannot keep a widening open by having signed it while they still had it."""
    gone = mum(invalid_at=T0 + timedelta(days=10))
    s = serve(health(), Principal(BEN), [me(), gone], LATER, widenings=[signed()])
    assert s.outcome is Outcome.INSTRUCTION


def test_an_expired_widening_does_not_widen():
    stale = Widening(BEN, "health", "one-off", "g-mother", T0, T0 + timedelta(days=1))
    s = serve(health(), Principal(BEN), [me(), mum()], LATER, widenings=[stale])
    assert s.outcome is Outcome.INSTRUCTION


def test_a_widening_cannot_be_signed_by_the_subject_or_by_a_role():
    for bad in (BEN, "guardian", "system", "  ", "role:guardian"):
        try:
            Widening(BEN, "health", "p", bad, T0, T0 + timedelta(days=30))
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} signed a widening")


def test_a_widening_cannot_name_a_wildcard_category():
    for bad in ("*", "all", "ANY", ""):
        try:
            Widening(BEN, bad, "p", "g-mother", T0, T0 + timedelta(days=30))
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as a category")


def test_a_widening_without_a_future_expiry_is_a_standing_grant():
    try:
        Widening(BEN, "health", "p", "g-mother", T0, T0)
    except ValueError:
        return
    raise AssertionError("a widening with no future expiry was accepted (W-5)")


def test_an_uncategorised_L4_field_cannot_be_widened():
    """`L4` means identifies an individual *and* carries a category. A missing
    category is a misclassification, and matching on it would widen on the
    strength of a defect."""
    assert widens([signed()], subject_id=BEN, category=None, at=LATER,
                  signer_edges=[mum()]) is None


# --- L5 and the floor are unchanged ---------------------------------------


def test_L5_is_still_never_served_to_the_subject():
    """No signature widens `L5`, including the subject's own standing — the
    sensitivity counterpart of a prohibited scope."""
    order = Field(LB, BEN, "restriction_contents", Rung.L5, category="legal",
                  payload="findings", instruction="a restriction is in force")
    s = serve(order, Principal(BEN), [me(), mum()], LATER, widenings=[signed("legal")])
    assert s.outcome is Outcome.REFUSED


def test_below_the_derive_floor_needs_no_edge_at_all():
    """Three-fifths of item 12 was already decided by the ladder, and this is
    the bottom two."""
    open_field = Field(LB, BEN, "call_time", Rung.L2, payload="5:45pm")
    assert serve(open_field, Principal(BEN), [], LATER).outcome is Outcome.PAYLOAD


# --- W-6's threshold ------------------------------------------------------


def test_the_cap_lifts_at_the_threshold_and_the_edge_becomes_ordinary():
    after = MAJORITY + timedelta(days=1)
    eligible = Principal(BEN, frozenset({"health"}))
    s = serve(health(), eligible, [me()], after, threshold=MAJORITY)
    assert s.outcome is Outcome.PAYLOAD and s.via_purpose == "health"

    # And it is a lift of the cap, not a bypass of the ladder: past the
    # threshold the subject still needs the declared purpose, like anyone else.
    bare = serve(health(), Principal(BEN), [me()], after, threshold=MAJORITY)
    assert bare.outcome is Outcome.INSTRUCTION


def test_the_threshold_is_a_date_compared_on_every_read_not_a_flag():
    eligible = Principal(BEN, frozenset({"health"}))
    day_before = serve(health(), eligible, [me()], MAJORITY - timedelta(days=1),
                       threshold=MAJORITY)
    assert day_before.outcome is Outcome.INSTRUCTION
    assert past_threshold(MAJORITY, MAJORITY) and not past_threshold(T0, MAJORITY)


def test_an_unknown_threshold_is_not_a_reached_one():
    """`None` reads as not yet. A birthdate the system has not learned must not
    graduate anybody."""
    assert not past_threshold(LATER, None)
    eligible = Principal(BEN, frozenset({"health"}))
    assert serve(health(), eligible, [me()], LATER).outcome is Outcome.INSTRUCTION


# --- the subject's own disclosure log -------------------------------------


def busy_log(n=3, subject=BEN):
    log = Log()
    s = serve(health(), Principal("staff-nguyen", frozenset({"health"})),
              [Edge("staff_of", "staff-nguyen", subject, T0, created_at=T0)], LATER)
    for _ in range(n):
        log = log.record(s, principal_id="staff-nguyen", subject_id=subject,
                         field_name="allergy", at=LATER)
    return log


def test_the_subject_sees_reads_of_a_field_they_cannot_read_themselves():
    """The decision, in one assertion. A student who cannot read their own `L4`
    medical field can still see that it was read, by whom, and when."""
    assert serve(health(), Principal(BEN), [me()], LATER).outcome is Outcome.INSTRUCTION

    view = own_log(busy_log(), BEN, BEN, LATER, [me()])
    assert view.state is LogAccess.GRANTED and view.complete
    seen = list(view)
    assert len(seen) == 3
    assert {e.field_name for e in seen} == {"allergy"}
    assert {e.principal_id for e in seen} == {"staff-nguyen"}
    assert {e.rung for e in seen} == {Rung.L4}


def test_the_view_carries_no_value_because_the_log_never_did():
    view = own_log(busy_log(), BEN, BEN, LATER, [me()])
    for e in view:
        assert not hasattr(e, "value") and "anaphylaxis" not in repr(e)


def test_a_refused_view_cannot_be_mistaken_for_an_empty_log():
    """`sending.SendList`'s shape. An empty log and a refused one are different
    facts and must not both arrive as `()`."""
    view = own_log(busy_log(), "staff-nguyen", BEN, LATER,
                   [Edge("staff_of", "staff-nguyen", BEN, T0, created_at=T0)])
    assert view.state is LogAccess.REFUSED and view.total == 3
    try:
        list(view)
    except PermissionError:
        return
    raise AssertionError("a refused log view iterated as an empty list")


def test_an_ended_self_edge_ends_the_log_view_too():
    view = own_log(busy_log(), BEN, BEN, LATER,
                   [me(invalid_at=T0 + timedelta(days=10))])
    assert view.state is LogAccess.REFUSED


def test_an_unscoped_log_fails_closed_rather_than_being_filtered():
    """§5. Filtering a mixed log at the read re-creates the global-chain defect
    `Ledger` exists to prevent."""
    mixed = Log(busy_log().entries + busy_log(1, "student-ana").entries)
    view = own_log(mixed, BEN, BEN, LATER, [me()])
    assert view.state is LogAccess.UNKNOWN
    assert view.total == 4, "the count was hidden along with the entries"


def test_an_empty_log_is_granted_and_empty_not_unknown():
    view = own_log(Log(), BEN, BEN, LATER, [me()])
    assert view.state is LogAccess.GRANTED and view.total == 0 and view.complete


# --- what this does NOT do ------------------------------------------------


def test_the_subject_CANNOT_see_reads_of_another_students_lane_documented():
    """**A limitation stated as one.** W-3: lanes are mutually sealed. A shared
    event is two lane entries with one referent, so a rehearsal Ben and Ana both
    attended appears in Ben's log as Ben's entry. He learns nothing about hers,
    and `own_log` has no parameter that would let him."""
    import inspect
    params = list(inspect.signature(own_log).parameters)
    assert "lane_id" not in params and "subject_ids" not in params
    view = own_log(busy_log(1, "student-ana"), BEN, BEN, LATER, [me()])
    assert view.state is LogAccess.UNKNOWN


# --- I-7's supersession asymmetry, as a predicate --------------------------


def director() -> Edge:
    return Edge("director_of", "dana-reyes", BEN, T0, created_at=T0)


def test_no_office_derived_grant_confers_authority_over_the_wards_own_entry():
    """The clause at source: *"no office's Force extends to deleting or amending
    entries about its own exercise."* So the refusing branch consults no edges,
    and holding more of them cannot turn the answer around."""
    from records.standing import Supersession, may_supersede

    for holder, edges in (("dana-reyes", [director()]),
                          ("g-mother", [mum()]),
                          ("staff-nguyen", [Edge("staff_of", "staff-nguyen", BEN,
                                                 T0, created_at=T0)]),
                          ("nobody-at-all", [])):
        check = may_supersede(author_id=BEN, subject_id=BEN, principal_id=holder,
                              edges=edges, at=LATER)
        assert check.state is Supersession.REFUSED, f"{holder} superseded the ward's entry"
        assert not check.permitted


def test_the_author_supersedes_their_own_entry():
    """The asymmetry, not immutability. Without this branch the clause would
    read *entries are frozen*, and a student could not correct their own
    account."""
    from records.standing import Supersession, may_supersede

    check = may_supersede(author_id=BEN, subject_id=BEN, principal_id=BEN)
    assert check.state is Supersession.PERMITTED and check.permitted


def test_an_office_authored_entry_is_the_offices_to_supersede():
    """The other side of the asymmetry, and the reason a live edge is still
    required: a staff note about Ben is amendable by staff with standing, and by
    nobody who has none."""
    from records.standing import Supersession, may_supersede

    with_standing = may_supersede(author_id="staff-nguyen", subject_id=BEN,
                                  principal_id="dana-reyes", edges=[director()],
                                  at=LATER)
    assert with_standing.permitted

    without = may_supersede(author_id="staff-nguyen", subject_id=BEN,
                            principal_id="dana-reyes", edges=[], at=LATER)
    assert without.state is Supersession.REFUSED

    ended = may_supersede(author_id="staff-nguyen", subject_id=BEN,
                          principal_id="dana-reyes",
                          edges=[Edge("director_of", "dana-reyes", BEN, T0,
                                      invalid_at=T0 + timedelta(days=5),
                                      created_at=T0)],
                          at=LATER)
    assert ended.state is Supersession.REFUSED, "an ended office kept its authority"


def test_an_entry_whose_authorship_nobody_recorded_is_unknown():
    """Rule 13. An unauthored entry is not thereby the office's to amend, and
    `UNKNOWN` is not a permission — `permitted` is false for it."""
    from records.standing import Supersession, may_supersede

    for kw in ({"author_id": None}, {"author_id": "  "}, {"subject_id": None}):
        args = dict(author_id="staff-nguyen", subject_id=BEN,
                    principal_id="dana-reyes", edges=[director()], at=LATER)
        args.update(kw)
        check = may_supersede(**args)
        assert check.state is Supersession.UNKNOWN, f"{kw} decided rather than deferring"
        assert not check.permitted


def test_supersession_is_a_dated_act():
    """An office claim with no instant cannot be checked against dated standing,
    so it is unknown rather than allowed."""
    from records.standing import Supersession, may_supersede

    check = may_supersede(author_id="staff-nguyen", subject_id=BEN,
                          principal_id="dana-reyes", edges=[director()])
    assert check.state is Supersession.UNKNOWN


def test_a_forged_self_edge_confers_no_supersession_authority():
    forged = Edge(SELF, "staff-nguyen", BEN, T0, created_at=T0)
    from records.standing import Supersession, may_supersede

    check = may_supersede(author_id="dana-reyes", subject_id=BEN,
                          principal_id="staff-nguyen", edges=[forged], at=LATER)
    assert check.state is Supersession.REFUSED


def test_the_module_is_not_broken_shut():
    assert serve(chair(), Principal(BEN), [me()], LATER).outcome is Outcome.PAYLOAD
    assert serve(health(), Principal(BEN), [me(), mum()], LATER,
                 widenings=[signed()]).outcome is Outcome.PAYLOAD
    assert own_log(busy_log(), BEN, BEN, LATER, [me()]).state is LogAccess.GRANTED


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
