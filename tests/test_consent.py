"""§18 item 10: which consent model governs which surface.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Rung  # noqa: E402
from records.consent import Governance, Model, governs  # noqa: E402
from records.standing import self_edge  # noqa: E402

T0 = datetime(2026, 3, 1)
LATER = T0 + timedelta(days=200)
MAJORITY = datetime(2028, 6, 1)
BEN = "student-ben"


def edge(kind, who, subject=BEN, **kw):
    return Edge(kind, who, subject, T0, created_at=T0, **kw)


def me(**kw):
    return self_edge(BEN, valid_at=T0, created_at=T0, **kw)


# --- §13's two worked examples --------------------------------------------


def test_a_parent_viewing_their_students_balance_is_the_session_model():
    """§13's own example, and the one that shows the axis is not
    is-this-the-data-subject: a parent is not the subject and fits the session
    model cleanly, because they hold the authority the consent is about."""
    g = governs(Rung.L4, "g-mother", BEN, [edge("guardian_of", "g-mother")], LATER)
    assert g.model is Model.SESSION and g.may_ask


def test_a_director_opening_the_roster_is_the_delegated_model():
    """The other half. A director cannot be asked to re-consent on forty
    students' behalf every morning — that asks the wrong person in a form that
    makes yes the only workable answer."""
    g = governs(Rung.L3, "dir-dana", BEN, [edge("director_of", "dir-dana")], LATER)
    assert g.model is Model.DELEGATED and not g.may_ask


def test_every_exercising_kind_is_delegated():
    for kind in ("staff_of", "director_of", "judge_at", "clinician_for"):
        g = governs(Rung.L3, "p", BEN, [edge(kind, "p")], LATER)
        assert g.model is Model.DELEGATED, f"{kind} was asked to consent"


# --- the cap arrives as a consent question --------------------------------


def test_the_subject_holds_the_authority_up_to_L3():
    g = governs(Rung.L3, BEN, BEN, [me()], LATER)
    assert g.model is Model.SESSION and g.via_edge == "self"


def test_the_same_subject_is_delegated_at_L4_before_the_threshold():
    """Item 12's cap, in a second place. The same principal on the same lane is
    governed by the session model for a call time and by the delegated model for
    a diagnosis — W-4, not a special case invented here."""
    g = governs(Rung.L4, BEN, BEN, [me()], LATER)
    assert g.model is Model.DELEGATED and not g.may_ask
    assert "W-4" in g.reason


def test_the_threshold_restores_the_subjects_own_authority_at_L4():
    after = MAJORITY + timedelta(days=1)
    g = governs(Rung.L4, BEN, BEN, [me()], after, threshold=MAJORITY)
    assert g.model is Model.SESSION


def test_an_unknown_threshold_does_not_restore_it():
    assert governs(Rung.L4, BEN, BEN, [me()], LATER).model is Model.DELEGATED


# --- rule 13: the third state is not a default ----------------------------


def test_an_unrecognised_relationship_is_unknown_and_not_askable():
    """Both wrong guesses are bad in different directions: SESSION asks someone
    who may not hold the authority, DELEGATED asks nobody and leans on a grant
    that may not exist. So neither is the default."""
    g = governs(Rung.L3, "p", BEN, [edge("volunteer_at", "p")], LATER)
    assert g.model is Model.UNKNOWN and not g.may_ask


def test_unknown_is_never_askable_which_is_the_counterintuitive_half():
    """A prompt feels like the conservative move when unsure. It is not: a
    prompt shown to someone who does not hold the authority manufactures a
    consent record that looks valid."""
    assert not Governance(Model.UNKNOWN, "x").may_ask
    assert not Governance(Model.DELEGATED, "x").may_ask
    assert Governance(Model.SESSION, "x").may_ask


def test_no_relationship_at_all_is_unknown_not_delegated():
    g = governs(Rung.L3, "stranger", BEN, [], LATER)
    assert g.model is Model.UNKNOWN


def test_an_unclassified_field_cannot_have_a_governing_consent():
    assert governs(None, "g-mother", BEN, [edge("guardian_of", "g-mother")],
                   LATER).model is Model.UNKNOWN


# --- edges are dated, and a forged one is not an edge ---------------------


def test_an_ended_relationship_governs_nothing():
    ended = edge("guardian_of", "g-mother", invalid_at=T0 + timedelta(days=10))
    assert governs(Rung.L3, "g-mother", BEN, [ended], LATER).model is Model.UNKNOWN


def test_a_forged_self_edge_does_not_confer_session_consent():
    """The same attack item 12 closed, arriving at the other predicate. A staff
    member holding a row that says `self` must not be handed the subject's own
    authority to consent."""
    forged = Edge("self", "staff-nguyen", BEN, T0, created_at=T0)
    g = governs(Rung.L3, "staff-nguyen", BEN, [forged], LATER)
    assert g.model is Model.UNKNOWN, "a forged self edge was asked to consent"


# --- a principal holding more than one edge -------------------------------


def test_a_guardian_who_is_also_staff_is_still_a_guardian():
    """The delegated path must not narrow someone who holds the authority
    outright. A band parent who chaperones is the ordinary case, not the edge
    case."""
    both = [edge("staff_of", "g-mother"), edge("guardian_of", "g-mother")]
    for order in (both, list(reversed(both))):
        g = governs(Rung.L4, "g-mother", BEN, order, LATER)
        assert g.model is Model.SESSION, "a guardian was routed down the staff path"


# --- what this does NOT do ------------------------------------------------


def test_this_decides_whom_to_ask_and_never_what_is_served_documented():
    """**A boundary, asserted so it is not eroded.** `serve()` is the only gate.
    If this module ever returns a payload, a rung, or a decision about a field,
    a second and weaker authorization path has appeared beside the predicate —
    §16's shape, arriving as a convenience.

    Written twice. The first version ended `assert ... or True`, which is a
    tautology and could not fail — the same defect `CROSSINGS.md`'s addendum
    describes, committed two hours after describing it. This version names three
    conditions that can each be violated by a real edit."""
    import inspect
    import records.consent as mod

    assert set(mod.Governance.__dataclass_fields__) == {"model", "reason", "via_edge"}, (
        "Governance grew a field; if it now carries a value or a rung this module "
        "has become a second serving path"
    )
    leaked = [n for n in ("Field", "Serving", "Outcome", "serve")
              if hasattr(mod, n)]
    assert not leaked, f"the consent router imported serving machinery: {leaked}"
    params = set(inspect.signature(mod.governs).parameters)
    assert "fld" not in params and "field" not in params, (
        "governs() took a field; it decides whom to ask, not what is served"
    )


def test_standing_not_reachability_decides_here_too():
    """A guardian under a contact restriction may not be messaged. Whether they
    still hold the authority to consent is a different question, and `governs()`
    takes edges, never restrictions."""
    import inspect
    assert "restrictions" not in inspect.signature(governs).parameters


def test_the_module_is_not_broken_shut():
    assert governs(Rung.L3, "g-mother", BEN,
                   [edge("guardian_of", "g-mother")], LATER).may_ask
    assert governs(Rung.L3, "staff-n", BEN,
                   [edge("staff_of", "staff-n")], LATER).model is Model.DELEGATED


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
