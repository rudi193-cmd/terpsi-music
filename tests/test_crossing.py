"""The crossing W-3 permits: every way to forge one, and the seal that holds.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Outcome, Principal, Rung, serve  # noqa: E402
from records.crossing import Envelope, permits  # noqa: E402

T0 = datetime(2026, 3, 1)
LATER = T0 + timedelta(days=60)
BEN, SIB = "student-ben", "student-sibling"


def env(**kw) -> Envelope:
    base = dict(from_lane="lane-sib", to_lane="lane-ben",
                purpose="shared bus roster for the Dayton trip",
                signed_by="g-mother", signed_at=T0, expires_at=T0 + timedelta(days=30))
    base.update(kw)
    return Envelope(**base)


def mother() -> Edge:
    return Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)


def ben_field() -> Field:
    return Field("lane-ben", BEN, "chair", Rung.L3,
                 payload="Ben Alvarez · trumpet 2", instruction="one member of this section")


# --- the four things an envelope must carry --------------------------------


def test_an_envelope_must_name_both_lanes():
    for kw in ({"from_lane": ""}, {"to_lane": ""}, {"from_lane": "lane-ben"}):
        try:
            env(**kw)
        except ValueError:
            continue
        raise AssertionError(f"an envelope was built with {kw}")


def test_an_envelope_without_a_purpose_is_a_standing_crossing():
    for p in ("", "   "):
        try:
            env(purpose=p)
        except ValueError:
            continue
        raise AssertionError("a purposeless envelope was accepted")


def test_an_envelope_without_a_future_expiry_is_a_standing_grant():
    """W-5: agency grows by signature, never by drift. An envelope that never
    expires is the drift."""
    for exp in (T0, T0 - timedelta(days=1)):
        try:
            env(expires_at=exp)
        except ValueError:
            continue
        raise AssertionError("an envelope with no future expiry was accepted")


def test_a_role_cannot_sign_an_envelope():
    for who in ("", "system", "guardian", "the director", "staff"):
        try:
            env(signed_by=who)
        except ValueError:
            continue
        raise AssertionError(f"{who!r} signed a crossing")


# --- the crossing itself ---------------------------------------------------


def test_without_an_envelope_a_crossing_is_refused():
    s = serve(ben_field(), Principal("g-mother"), [mother()], T0, lane_id="lane-sib")
    assert s.outcome is Outcome.REFUSED
    assert "envelope" in s.reason


def test_with_an_envelope_the_crossing_is_representable_at_last():
    """The permission half of W-3, which had no way to exist. A real sibling
    case could previously only be served by not recording that it happened."""
    s = serve(ben_field(), Principal("g-mother"), [mother()], T0,
              lane_id="lane-sib", envelopes=[env()])
    assert s.outcome is Outcome.PAYLOAD
    assert "crossing permitted by envelope" in s.reason
    assert "Dayton" in s.reason, "the purpose is not carried into the narration (§7.2)"


def test_an_expired_envelope_does_not_permit():
    s = serve(ben_field(), Principal("g-mother"), [mother()], LATER,
              lane_id="lane-sib", envelopes=[env()])
    assert s.outcome is Outcome.REFUSED


def test_an_envelope_is_directional():
    """One signature must not open two seals. An envelope letting the sibling's
    lane read Ben's does not let Ben's read the sibling's."""
    assert permits([env()], from_lane="lane-ben", to_lane="lane-sib", at=T0) is None
    assert permits([env()], from_lane="lane-sib", to_lane="lane-ben", at=T0) is not None


def test_the_signers_standing_is_checked_at_use_not_at_signing():
    """Refusal 3, applied to the envelope. A guardian whose standing has ended
    cannot keep a crossing open by having signed it while they still had it."""
    ended = Edge("guardian_of", "g-mother", BEN, T0,
                 invalid_at=T0 + timedelta(days=5), created_at=T0)
    long_env = env(expires_at=T0 + timedelta(days=300))
    assert permits([long_env], from_lane="lane-sib", to_lane="lane-ben",
                   at=T0 + timedelta(days=1), signer_edges=[ended],
                   subject_id=BEN) is not None
    assert permits([long_env], from_lane="lane-sib", to_lane="lane-ben",
                   at=T0 + timedelta(days=10), signer_edges=[ended],
                   subject_id=BEN) is None, (
        "a crossing outlived the standing of the guardian who signed it"
    )


def test_a_crossing_does_not_widen_anything_else():
    """The envelope opens the seal and nothing more. An L4 field still needs a
    declared purpose, and L5 is still never served."""
    health = Field("lane-ben", BEN, "allergy", Rung.L4, category="health",
                   payload="tree-nut allergy", instruction="carries an auto-injector")
    s = serve(health, Principal("g-mother"), [mother()], T0,
              lane_id="lane-sib", envelopes=[env()])
    assert s.outcome is Outcome.INSTRUCTION, "the envelope widened L4's purpose rule"

    order = Field("lane-ben", BEN, "restriction", Rung.L5, payload="court order")
    s2 = serve(order, Principal("g-mother"), [mother()], T0,
               lane_id="lane-sib", envelopes=[env()])
    assert s2.outcome is Outcome.REFUSED and "L5" in s2.reason


def test_the_crossing_is_not_broken_open():
    """Negative control: same-lane reads must be unaffected by all of this."""
    s = serve(ben_field(), Principal("g-mother"), [mother()], T0, lane_id="lane-ben")
    assert s.outcome is Outcome.PAYLOAD
    assert "crossing" not in s.reason


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
