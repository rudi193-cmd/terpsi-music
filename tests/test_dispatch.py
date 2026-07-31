"""The join: the serving decision, the voice gate, and the log, in one path.

PR #4 shipped `voice.guard()` and said *"the gate is not yet routed through
anything… until one exists this is enforcement-ready rather than enforcing, and
calling it otherwise would be the exact thing rule 18 forbids."* This is the
dispatcher. After this file, `voice.py` is a **gate**.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import voice  # noqa: E402
from records import Edge, Field, Outcome, Principal, Rung  # noqa: E402
from records.disclosure import Log  # noqa: E402
from records.dispatch import dispatch  # noqa: E402

T0 = datetime(2026, 3, 1)
BEN = "student-ben"


def chair(**kw) -> Field:
    base = dict(lane_id="lane-ben", subject_id=BEN, name="chair", rung=Rung.L3,
                payload="Ben Alvarez · trumpet 2",
                instruction="one member of this section", provenance="P1")
    base.update(kw)
    return Field(**base)


def mother():
    return [Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)]


def render(s):
    return f"Chair: {s.value} ({s.provenance} measured, from the roster import)."


def go(fld=None, principal=None, edges=None, r=render, log=None):
    return dispatch(fld or chair(), principal or Principal("g-mother"),
                    edges if edges is not None else mother(), T0, r,
                    log=log if log is not None else Log())


# --- both halves must pass -------------------------------------------------


def test_a_clean_entitled_read_is_released():
    d = go()
    assert d.released and "Ben Alvarez" in d.text


def test_the_voice_gate_blocks_a_sentence_the_predicate_would_have_allowed():
    """The whole point of routing it. The principal is entitled, the rung
    permits, and the *prose* is still refused — which is a decision `serve()`
    cannot make and `voice.py` could not previously enforce."""
    d = go(r=lambda s: f"{s.value} is better than most of his section. (P1 measured)")
    assert not d.released
    assert d.blocked_by_voice, "the block was attributed to the wrong half"
    assert d.serving.outcome is Outcome.PAYLOAD, "the predicate had allowed it"
    assert "peer_comparison" in d.reason


def test_the_predicate_blocks_before_anything_is_rendered():
    """Order matters. A refusal means there is no prose to check, and running a
    text filter over a value the principal was never entitled to would be a
    disclosure to the filter."""
    rendered = []

    def spy(s):
        rendered.append(s.value)
        return "anything"

    d = dispatch(chair(rung=Rung.L5), Principal("g-mother"), mother(), T0, spy, log=Log())
    assert not d.released
    assert rendered == [], "the renderer saw a value the predicate had refused"
    assert not d.blocked_by_voice


def test_a_served_value_must_carry_its_provenance():
    """§15, enforced at the dispatch point. Found by routing: the gate's rule
    requires a `P`-rung on any sentence carrying a value, and nothing upstream
    supplied one — `Field` had no provenance at all until this path existed."""
    d = go(r=lambda s: f"Chair: {s.value}")
    assert not d.released
    assert "no_provenance" in d.reason


def test_the_rule_is_named_for_the_scale_it_actually_checks():
    """It was called `no_rung` and matched `P1`-`P5`. In this repository a rung
    is `L1`-`L5` (`SENSITIVITY.md` is canonical), so a caller supplying a
    perfectly good `L3` was refused with a message about provenance — §15's own
    three-scale hazard, inside the module written to enforce the fleet's rules.

    Renamed 2026-07-30. This asserts the name and the scale agree."""
    findings = voice.check("Saturday is clear.", serves_value=True)
    assert any(f.startswith("no_provenance") for f in findings)
    assert not any(f.startswith("no_rung") for f in findings)
    assert voice._PROVENANCE.search("P2 cited")
    assert not voice._PROVENANCE.search("L3"), (
        "the provenance pattern matches an L-rung — the scales are confused again"
    )


# --- the log sees everything, released or not ------------------------------


def test_every_dispatch_is_logged_including_the_refusals():
    log = Log()
    d1 = go(log=log)
    d2 = dispatch(chair(rung=Rung.L5), Principal("g-mother"), mother(), T0, render,
                  log=d1.log)
    assert len(d2.log.entries) == 2
    assert {e.outcome for e in d2.log.entries} == {Outcome.PAYLOAD, Outcome.REFUSED}
    assert d2.log.verify()[0]


def test_a_voice_refusal_still_logs_the_serving_decision():
    """The predicate decided to disclose and the gate stopped the sentence. The
    log must record what was *decided*, or an audit cannot tell a refusal at
    the predicate from a block in the prose."""
    d = go(r=lambda s: f"{s.value} is better than most. (P1 measured)")
    assert not d.released
    assert d.log.entries[-1].outcome is Outcome.PAYLOAD


def test_dispatch_forwards_the_self_edge_threshold():
    """§18 item 12 must be reachable through the join, not only through serve().

    `dispatch()` accepted neither `threshold` nor `widenings` nor `known_as_of`,
    so a post-W-6 subject reading their own `L4` field got the derived
    instruction through the only path that renders, gates and logs — while
    `serve()` called directly returned the payload. Fail-closed, and still
    wrong: the log records what THIS function decided, so §7.2's narration
    disagreed with the predicate it claims to narrate.
    """
    fld = chair(rung=Rung.L4, category="health",
                payload="carries an auto-injector",
                instruction="has a health plan on file")
    subject = Principal(id=BEN, purposes=frozenset({"health"}))
    self_edge = [Edge("self", BEN, BEN, T0, created_at=T0)]
    reached = datetime(2026, 1, 1)

    d = dispatch(fld, subject, self_edge, T0, render, threshold=reached, log=Log())
    assert d.serving.outcome is Outcome.PAYLOAD, d.serving.reason
    assert d.log.entries[-1].outcome is Outcome.PAYLOAD, (
        "the log must record the decision the predicate would make"
    )


def test_dispatch_forwards_a_guardian_widening():
    """The other half of item 12: a signature the join could not see."""
    from records.standing import Widening

    fld = chair(rung=Rung.L4, category="health",
                payload="carries an auto-injector",
                instruction="has a health plan on file")
    subject = Principal(id=BEN)
    edges = [Edge("self", BEN, BEN, T0, created_at=T0),
             Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)]
    w = Widening(subject_id=BEN, category="health", purpose="self-care",
                 signed_by="g-mother", signed_at=T0,
                 expires_at=datetime(2026, 12, 1))

    d = dispatch(fld, subject, edges, T0, render, widenings=[w])
    assert d.serving.outcome is Outcome.PAYLOAD, d.serving.reason
    assert d.serving.via_purpose == "health"


def test_dispatch_forwards_the_knowledge_horizon():
    """G5's second clock. An edge this system had not yet learned of cannot
    have entitled a read that already happened, and the join must be able to
    ask that question — `known_as_of` was not in its signature either.

    The horizon must differ from `at`, or this asserts nothing: `serve()`
    defaults it to `at`, so `known_as_of=at` makes dropping the argument a
    no-op. The first version of this test did exactly that and only "failed"
    against the unfixed source because the old signature raised `TypeError` —
    a red test for the wrong reason. Ablation caught it: SURVIVES.
    """
    read_at = datetime(2026, 6, 1)      # the read happens in June
    learned = datetime(2026, 4, 1)      # the edge was recorded in April
    audit_horizon = datetime(2026, 3, 1)  # what did we know in March?
    edges = [Edge("guardian_of", "g-mother", BEN, T0, created_at=learned)]

    d = dispatch(chair(), Principal(id="g-mother"), edges, read_at, render,
                 known_as_of=audit_horizon)
    assert d.serving.outcome is not Outcome.PAYLOAD, (
        "an edge this system had not yet learned of cannot entitle the read"
    )


def test_dispatch_forwards_the_grant_ceiling():
    """The rung ceiling has to be reachable through the join, for the same
    reason `threshold` did: the log records the decision **this** function made,
    so a ceiling the join cannot see makes §7.2's narration disagree with the
    predicate it claims to narrate.

    And `None` is forwarded *as `None`*. Normalising it to `()` here would deny
    on behalf of every surface that has not been asked about grants yet;
    normalising the other way would be the fail-open. The join does neither.
    """
    from records import Grant

    edges = [Edge("staff_of", "staff-nguyen", BEN, T0, created_at=T0)]
    who = Principal("staff-nguyen")
    capped = [Grant("staff-nguyen", "lane-ben", Rung.L2, "dana-reyes", T0,
                    datetime(2026, 12, 1), created_at=T0)]

    d = dispatch(chair(), who, edges, T0, render, grants=capped, log=Log())
    assert d.serving.outcome is not Outcome.PAYLOAD, d.serving.reason
    assert "ceiling" in d.serving.reason
    assert d.log.entries[-1].outcome is d.serving.outcome, (
        "the log must record the decision the predicate would make"
    )

    unconsulted = dispatch(chair(), who, edges, T0, render, grants=None)
    assert unconsulted.serving.outcome is Outcome.PAYLOAD


def test_an_instruction_carries_the_fields_provenance():
    """A value that leaves the system says where it came from.

    `_derived_or_refused` set `provenance` on neither branch, so every
    INSTRUCTION reported `None` — indistinguishable from a field that genuinely
    carried no provenance.
    """
    fld = chair(rung=Rung.L4, category="health", provenance="P2",
                instruction="has a health plan on file")
    d = dispatch(fld, Principal(id="g-mother"), mother(), T0, render)
    assert d.serving.outcome is Outcome.INSTRUCTION, d.serving.reason
    assert d.serving.provenance == "P2"


def test_a_refusal_does_not_carry_the_fields_provenance():
    """The asymmetry, asserted so it is not 'tidied up' later.

    A refusal served nothing. Attaching the field's provenance would make a
    refusal over a `P1` field distinguishable from one over a field carrying
    none — a side channel in the function whose job is to close them.
    """
    fld = chair(rung=Rung.L4, category="health", provenance="P1",
                instruction=None)
    d = dispatch(fld, Principal(id="g-mother"), mother(), T0, render)
    assert d.serving.outcome is Outcome.REFUSED, d.serving.reason
    assert d.serving.provenance is None


def test_dispatch_is_not_broken_shut():
    """Negative control: a dispatcher that released nothing would pass every
    refusal test above."""
    assert go().released


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
