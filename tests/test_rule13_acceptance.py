"""Rule 13, attempted end to end: every seam pointed at a source that is not there.

`docs/BUILD-PLAN.md` row C3, and `willow-grove`'s constraint 1 supplies the
shape at source:

> *"Kill the database and open every pane. Any pane that shows a green state, a
> zero count, or an empty-but-fine message has failed. Do this as a test, not by
> hand: point the app at an unreachable DSN in CI and assert no surface reports
> health."*

Individual modules honour rule 13 and their own suites say so. What did not
exist here is the sweep: **one place that enumerates every seam this repository
consults and breaks each of them**, so that a seam added later without an
unknown state is caught by a test nobody had to remember to write. `SEAMS` below
is that enumeration and `test_every_seam_in_the_inventory_has_a_test` is the
middle rule 12 asks for — the list and the tests are a pair, and a list nothing
checks is the declaration-without-enforcement §16 keeps finding.

**Breakage is real, never skipped.** Sources are made unreachable by pointing a
checker at a directory that does not exist, by handing a predicate a callable
that raises, or by emptying a registry the way a failed load would leave it.
Nothing here is `skipif`.

**The dangerous mirror.** *Unknown* and *legitimately empty* must not compare
equal, and for several seams here they do. Those are not smoothed over: they are
listed in `CANNOT_DISTINGUISH` with the reason, and each carries a test that
asserts the two answers are **still** identical today. Every one of those tests
goes red the moment somebody teaches the seam to tell the difference — which is
the fix landing, not a regression, and the list is then wrong and must be
edited. `voice.KNOWN_MISSES` is the house precedent: publishing the misses is
the only honest way to state coverage, and a stale honesty list is worse than
none.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/test_rule13_acceptance.py -q
    python3 tests/test_rule13_acceptance.py
"""

from __future__ import annotations

import inspect
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import voice  # noqa: E402

import conform  # noqa: E402
import discipline  # noqa: E402
import purity  # noqa: E402
import sockets  # noqa: E402

#: `records/__init__.py` re-exports a *function* called `classify` and a
#: function called `dispatch`, both of which shadow the submodule of the same
#: name on the package — so `from records import classify` hands back the
#: function and `import records.classify as x` does too (`import a.b as c`
#: prefers the attribute). `import_module` reads `sys.modules` and gets the
#: module, which is what a test that patches module state needs.
classify_mod = import_module("records.classify")  # noqa: E402
from records import consent, crossing, disclosure, export, marking  # noqa: E402
from records import practice, receipts, rungs, sending, serving  # noqa: E402
from records import standing as standing_mod  # noqa: E402
from records import witness  # noqa: E402
from records import exit as exit_mod  # noqa: E402
from records.dispatch import dispatch  # noqa: E402

BEN = "student-ben"
LANE = "lane-ben"
AT = datetime(2026, 10, 12, 9, 0)
OPENED = datetime(2025, 8, 1)
DECOYS = Path(__file__).resolve().parent / "fixtures" / "decoys"


# --- the inventory ---------------------------------------------------------

#: Every seam where this repository consults a backend, a source or a store,
#: with how it is broken here and the shape the answer must take when it is.
#: `slug` names the test that attempts it.
SEAMS = (
    ("restriction_backend", "records/sending.py",
     "the contact-restriction source raises", "SendList UNKNOWN"),
    ("send_path", "records/sending.py",
     "deliver() over a raising restriction source", "RuntimeError, nothing sent"),
    ("consent_backend", "records/consent.py",
     "no relationship survives the lookup", "Model.UNKNOWN, not askable"),
    ("consent_registry", "records/consent.py",
     "HOLDS and EXERCISES empty, as a failed load leaves them", "Model.UNKNOWN"),
    ("classification_registry", "records/classify.py",
     "the decided-case sets empty", "Decision.UNDECIDED, rung None"),
    ("serve_classification", "records/serving.py",
     "the field carries no rung", "Outcome.UNKNOWN"),
    ("entitlement_store", "records/serving.py",
     "the edge store yields nothing", "REFUSED — see CANNOT_DISTINGUISH"),
    ("envelope_store", "records/crossing.py",
     "the envelope store yields nothing", "REFUSED — see CANNOT_DISTINGUISH"),
    ("widening_store", "records/standing.py",
     "the widening store yields nothing", "INSTRUCTION/REFUSED, never PAYLOAD"),
    ("threshold_source", "records/standing.py",
     "the birthdate the threshold derives from is unknown", "not past the threshold"),
    ("own_log", "records/standing.py",
     "the log handed over is not this lane's", "LogAccess.UNKNOWN, iteration raises"),
    ("ledger_lane", "records/disclosure.py",
     "the ledger has never heard of the lane", "an empty log — see CANNOT_DISTINGUISH"),
    ("witness_receipt", "records/witness.py",
     "the receipt store yields nothing", "Standing.UNWITNESSED"),
    ("witness_chain", "records/witness.py",
     "the chain does not verify", "Standing.TAMPERED"),
    ("anchor_cadence", "records/witness.py",
     "scheduled anchors have no receipt", "Standing.GAPPED"),
    ("voice_rubric", "voice.py",
     "the ruleset is empty, as a failed load leaves it", "unavailable[refuse]"),
    ("voice_payload", "voice.py",
     "the payload has no field to check", "unknown, refused"),
    ("voice_raises", "voice.py", "the guard itself raises", "unknown, refused"),
    ("dispatch_join", "records/dispatch.py",
     "the rubric is empty under the only path that renders", "nothing released"),
    ("conform_egress", "tools/conform.py",
     "the scanned tree does not exist", "State.UNKNOWN"),
    ("conform_write_paths", "tools/conform.py",
     "the scanned tree does not exist", "State.UNKNOWN"),
    ("conform_revocation", "tools/conform.py",
     "the scanned tree does not exist", "State.UNKNOWN"),
    ("conform_suites", "tools/conform.py",
     "there are no test files to scan", "State.UNKNOWN"),
    ("conform_artifacts", "tools/conform.py",
     "the documents and harness checked are absent", "State.ABSENT"),
    ("conform_sweep", "tools/conform.py",
     "the whole tree is unreachable", "no check reports PASS"),
    ("sockets_manifest", "tools/sockets.py",
     "no manifest, and a manifest that declares nothing", "Verdict.VACUOUS"),
    ("sockets_unresolved", "tools/sockets.py",
     "the bind address comes from the environment", "UNRESOLVED finding"),
    ("unparseable_source", "tools/purity.py, tools/discipline.py, tools/sockets.py",
     "the source will not parse", "a finding on every gate"),
    ("rung_parse", "records/rungs.py",
     "the value is not a rung", "raises, never L1"),
    ("export_manifest", "records/export.py",
     "the bundle has no manifest, or one that lists nothing", "(False, why)"),
    ("empty_history", "records/practice.py, records/exit.py",
     "there are no rows to aggregate or transfer", "raises, never a zero"),
    ("score_position", "records/marking.py",
     "no score position is attached", "UNALIGNED — see CANNOT_DISTINGUISH"),
)

#: Seams that fail **closed** but cannot say *which* closed answer this is: the
#: unknown and the legitimate empty compare equal. Each row is asserted below to
#: be still true, so the list cannot rot into a claim about a fixed seam.
#:
#: None of these is a fail-open. Every one lands on refusal, unknown or
#: not-evidence. What is missing is the second half of rule 13 — the answer is
#: unknown-shaped, and the *reason* attached to it names a fact nobody
#: established.
CANNOT_DISTINGUISH = (
    ("entitlement_store",
     "an edge store that errored and a principal with no edge both arrive at "
     "serve() as an empty sequence, and both are REFUSED with the same reason. "
     "`serve()` cannot say 'no entitlement' rather than 'entitlement unknown' "
     "without an error channel on the edge source — the callable-or-sequence "
     "shape `sending.recipients` already carries."),
    ("envelope_store",
     "same shape one lane over: an envelope store that errored and a crossing "
     "nobody signed are both `()`, both REFUSED by W-3."),
    ("widening_store",
     "a widening store that errored and a category no guardian has widened both "
     "return None from `widens()`, and the self-edge cap holds for both."),
    ("consent_backend",
     "an edge source that errored and a principal with no live relationship "
     "both produce Model.UNKNOWN with the 'nobody here to ask' reason. UNKNOWN "
     "is the right answer for both, so this one is nearly harmless — but the "
     "reason names a fact that was never established."),
    ("witness_receipt",
     "a receipt store that errored and a log nobody ever witnessed are both "
     "UNWITNESSED with 'no receipts at all'. Not evidence either way, so the "
     "standing is right and the sentence beneath it is a guess."),
    ("ledger_lane",
     "**the sharp one.** `Ledger.log_for` returns `Log()` for a lane it has "
     "never heard of, which is the same object a lane with no entries yet "
     "returns. Downstream that is not a refusal: `own_log` serves it GRANTED "
     "and `complete`, so a lane missing from the ledger renders as *nobody has "
     "ever read you*, and `receipts.issue` hands out nothing without saying so. "
     "This is absence rendering as a result, one call short of a surface."),
    ("score_position",
     "`drift()` on a mark with no position is UNALIGNED and `usable`, whether "
     "the alignment was never derived or the score store could not be reached. "
     "The tap is authoritative in both cases, so nothing false is shown — but "
     "'no position' and 'position unknown' are one state."),
)


# --- fixtures --------------------------------------------------------------


def unreachable():
    """A source that is down. The failure a caller must not be able to swallow."""
    def _source():
        raise ConnectionError("the source is unreachable")
    return _source


def mother():
    return serving.Edge("guardian_of", "g-mother", BEN, OPENED, created_at=OPENED)


def himself():
    return standing_mod.self_edge(BEN, valid_at=OPENED, created_at=OPENED)


def health_field(**kw):
    base = dict(lane_id=LANE, subject_id=BEN, name="allergy", rung=rungs.Rung.L4,
                category="health", payload="peanut", provenance="P1")
    base.update(kw)
    return serving.Field(**base)


def a_log():
    return disclosure.Log().record(
        serving.Serving(serving.Outcome.PAYLOAD, "x", rungs.Rung.L3, "read"),
        principal_id="staff-nguyen", subject_id=BEN, field_name="chair", at=AT)


def broken_tree():
    """A directory that is not there. The unreachable DSN, as a path.

    Checked rather than assumed: a scan of a directory that turned out to exist
    would pass for the wrong reason, which is the shape this whole file is
    about.
    """
    p = Path(tempfile.gettempdir()) / "terpsi-no-such-tree-8f3a1c"
    assert not p.exists(), f"{p} exists; this fixture is no longer unreachable"
    return p


def written(where: Path, name: str, body: str) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    p = where / name
    p.write_text(body, encoding="utf-8")
    return p


# --- records/sending.py: the contact-restriction backend -------------------


def test_restriction_backend_that_errors_is_unknown_and_not_an_empty_list():
    """G11 at the seam: *a consent or guardianship backend that errored
    surfaces as unknown, never as 'no restrictions'.*"""
    who = sending.recipients(BEN, [mother()], unreachable(), AT)
    assert who.state is sending.Standing.UNKNOWN
    assert who.guardians == ()
    assert "ConnectionError" in who.reason
    try:
        list(who)
    except RuntimeError as exc:
        assert "not derived" in str(exc)
    else:
        raise AssertionError("an unknown send list iterated as an empty one")


def test_restriction_backend_unknown_is_not_the_same_value_as_no_restrictions():
    """The dangerous mirror. A student whose guardians are genuinely
    unrestricted and a student whose restriction source is down must not
    produce equal answers — an equality that held would let a caller compare
    against `()` and be wrong half the time."""
    down = sending.recipients(BEN, [mother()], unreachable(), AT)
    clear = sending.recipients(BEN, [mother()], [], AT)
    assert down != clear
    assert down.state is not clear.state
    assert tuple(clear) == ("g-mother",)


def test_send_path_over_a_broken_backend_sends_to_nobody_and_says_so():
    sent = []
    payload = sending.Payload(BEN, AT, "call time moved to 5:15")
    try:
        sending.deliver(payload, [mother()], unreachable(),
                        lambda who, body: sent.append(who))
    except RuntimeError:
        assert sent == [], f"a message went out under an unknown send list: {sent}"
    else:
        raise AssertionError("deliver() proceeded with an undetermined recipient set")


# --- records/consent.py: which consent model governs -----------------------


def test_consent_backend_with_no_relationship_is_unknown_and_not_askable():
    g = consent.governs(rungs.Rung.L3, "g-mother", BEN, [], AT)
    assert g.model is consent.Model.UNKNOWN
    assert not g.may_ask, (
        "a surface would have prompted somebody whose authority is unestablished"
    )


def test_consent_registry_that_failed_to_load_does_not_default_to_a_model():
    """Both wrong answers are bad in different directions (§13). An emptied
    registry must not pick either."""
    holds, exercises = consent.HOLDS, consent.EXERCISES
    try:
        consent.HOLDS = frozenset()
        consent.EXERCISES = frozenset()
        g = consent.governs(rungs.Rung.L3, "g-mother", BEN, [mother()], AT)
        assert g.model is consent.Model.UNKNOWN
        assert not g.may_ask
    finally:
        consent.HOLDS, consent.EXERCISES = holds, exercises


def test_consent_with_an_unclassified_field_is_unknown_not_a_guess():
    g = consent.governs(None, "g-mother", BEN, [mother()], AT)
    assert g.model is consent.Model.UNKNOWN
    assert "sensitivity" in g.reason


def test_consent_unknown_is_distinguishable_from_a_decided_model():
    down = consent.governs(rungs.Rung.L3, "g-mother", BEN, [], AT)
    live = consent.governs(rungs.Rung.L3, "g-mother", BEN, [mother()], AT)
    assert down != live and live.model is consent.Model.SESSION


# --- records/classify.py: the decided-case registry ------------------------


def test_classification_registry_that_failed_to_load_returns_undecided():
    """`SENSITIVITY.md`: an unclassified field is a build failure, not a
    default. An emptied registry is the failed-load case and must reach the
    same answer as an undecided category."""
    common, protected = classify_mod.COMMON, classify_mod.PROTECTED_STATUS
    try:
        classify_mod.COMMON = frozenset()
        classify_mod.PROTECTED_STATUS = frozenset()
        got = classify_mod.classify(classify_mod.Descriptor(
            "allergy", identifies_a_person=True, category="health"))
        assert got.decision is classify_mod.Decision.UNDECIDED
        assert got.rung is None, f"an unloaded registry invented {got.rung}"
        assert got.needs_a_human
    finally:
        classify_mod.COMMON, classify_mod.PROTECTED_STATUS = common, protected


def test_an_undecided_classification_is_not_an_l1_or_an_l2():
    """The mirror for the classifier: the unknown answer must not compare equal
    to the ordinary lowest rung, which is what a guessing classifier returns."""
    undecided = classify_mod.classify(classify_mod.Descriptor(
        "immunisation_exemption", identifies_a_person=True, category="belief"))
    open_field = classify_mod.classify(classify_mod.Descriptor(
        "call_time", publishable=True))
    assert undecided != open_field
    assert undecided.rung is None and open_field.rung is rungs.Rung.L1


def test_a_build_refuses_to_ship_the_undecided_field_by_name():
    ds = [classify_mod.Descriptor("call_time", publishable=True),
          classify_mod.Descriptor("x", identifies_a_person=True, category="belief")]
    assert [d.name for d in classify_mod.unclassified(ds)] == ["x"]


# --- records/serving.py: the read predicate --------------------------------


def test_serve_classification_absent_is_unknown_and_serves_nothing():
    got = serving.serve(health_field(rung=None), serving.Principal("g-mother"),
                        [mother()], AT)
    assert got.outcome is serving.Outcome.UNKNOWN
    assert got.value is None and not got.disclosed


def test_serve_unknown_is_distinguishable_from_an_enforced_refusal():
    """Rule 18's distinction, at the outcome level: a refusal is enforcement and
    an unknown is nothing having been decided. A caller narrating the read has
    to be able to tell them apart, and the disclosure log records whichever it
    is given."""
    unknown = serving.serve(health_field(rung=None), serving.Principal("g-mother"),
                            [mother()], AT)
    refused = serving.serve(health_field(rung=rungs.NEVER_SERVED),
                            serving.Principal("g-mother"), [mother()], AT)
    assert unknown.outcome is not refused.outcome
    assert unknown != refused


def test_entitlement_store_yielding_nothing_never_serves_the_payload():
    """The store is unreachable, so the caller has no edges to pass. The answer
    must not be the value. It is REFUSED here rather than UNKNOWN — see
    CANNOT_DISTINGUISH."""
    got = serving.serve(health_field(), serving.Principal("g-mother"), [], AT)
    assert got.outcome is not serving.Outcome.PAYLOAD
    assert got.value is None


def test_envelope_store_yielding_nothing_never_crosses_a_lane():
    got = serving.serve(health_field(), serving.Principal("g-mother", frozenset({"health"})),
                        [mother()], AT, lane_id="lane-sister", envelopes=())
    assert got.outcome is serving.Outcome.REFUSED
    assert "W-3" in got.reason


def test_widening_store_yielding_nothing_leaves_the_self_cap_in_place():
    got = serving.serve(health_field(instruction="on file with the office"),
                        serving.Principal(BEN), [himself()], AT, widenings=())
    assert got.outcome is serving.Outcome.INSTRUCTION
    assert got.value != "peanut"


def test_threshold_source_unknown_is_not_a_threshold_reached():
    """A birthdate nobody could look up must not lift the cap. `past_threshold`
    reads None as not-yet, which is the fail-closed direction."""
    assert not standing_mod.past_threshold(AT, None)
    unknown_age = serving.serve(health_field(), serving.Principal(BEN), [himself()],
                                AT, threshold=None)
    known_past = serving.serve(health_field(), serving.Principal(BEN, frozenset({"health"})),
                               [himself()], AT, threshold=AT - timedelta(days=1))
    assert unknown_age.outcome is not serving.Outcome.PAYLOAD
    assert known_past.outcome is serving.Outcome.PAYLOAD


# --- records/standing.py: the subject's own log ----------------------------


def test_own_log_over_a_log_that_is_not_this_lane_is_unknown():
    other = disclosure.Log().record(
        serving.Serving(serving.Outcome.PAYLOAD, "x", rungs.Rung.L3, "read"),
        principal_id="staff", subject_id="student-sister", field_name="chair", at=AT)
    got = standing_mod.own_log(other, BEN, BEN, AT, [himself()])
    assert got.state is standing_mod.LogAccess.UNKNOWN
    assert not got.complete
    try:
        list(got)
    except PermissionError:
        return
    raise AssertionError("an unknown log view iterated as an empty one")


def test_own_log_unknown_is_distinguishable_from_a_log_with_no_reads():
    """The mirror. *Nobody has read you* and *we could not tell you who has*
    are the two answers a student most needs kept apart."""
    empty = standing_mod.own_log(disclosure.Log(), BEN, BEN, AT, [himself()])
    unknown = standing_mod.own_log(disclosure.Log(), BEN, BEN, AT, [])
    assert empty.state is standing_mod.LogAccess.GRANTED and empty.complete
    assert list(empty) == []
    assert unknown.state is not empty.state and unknown != empty


# --- records/witness.py: the anchor and its receipts -----------------------


def test_witness_receipt_store_yielding_nothing_is_unwitnessed_not_witnessed():
    ev = witness.standing(a_log(), [])
    assert ev.standing is witness.Standing.UNWITNESSED
    assert not ev.is_evidence
    assert ev.witnessed_to == 0


def test_a_local_test_double_does_not_count_as_a_witness():
    """The failure a convenient double invites: the seam is reachable, the
    receipt is real, and it proves nothing."""
    log = a_log()
    double = witness.RecordingWitness()
    receipt = double.publish(witness.anchor_for(log, AT))
    ev = witness.standing(log, [receipt])
    assert ev.standing is witness.Standing.UNWITNESSED
    assert "non-evidentiary" in ev.reason


def test_witness_unwitnessed_is_distinguishable_from_witnessed():
    log = a_log()
    head, count = log.anchor()
    real = witness.Receipt(witness.Anchor(head, count, AT), "tsa", "serial-1", AT)
    assert witness.standing(log, [real]).standing is witness.Standing.WITNESSED
    assert witness.standing(log, []) != witness.standing(log, [real])


def test_witness_chain_that_does_not_verify_is_tampered_not_witnessed():
    log = a_log()
    head, count = log.anchor()
    real = witness.Receipt(witness.Anchor(head, count, AT), "tsa", "serial-1", AT)
    truncated = disclosure.Log(())
    assert witness.standing(truncated, [real]).standing is witness.Standing.TAMPERED


def test_anchor_cadence_with_missing_receipts_is_gapped_not_witnessed():
    log = a_log()
    head, count = log.anchor()
    start, week = AT, timedelta(days=7)
    real = witness.Receipt(witness.Anchor(head, count, start), "tsa", "serial-1", start)
    ev = witness.standing(log, [real], start=start, end=start + week * 3, every=week)
    assert ev.standing is witness.Standing.GAPPED
    assert witness.missing([real], start, start + week * 3, week)


# --- records/disclosure.py: the ledger -------------------------------------


def test_ledger_lane_unknown_to_the_ledger_reads_as_a_log_with_no_reads():
    """**Finding, not a passing test.** This asserts the gap so it cannot be
    lost: `Ledger.log_for` answers for a lane it has never heard of, `own_log`
    serves that answer GRANTED and complete, and a student is told nobody has
    read them by a ledger that was never asked. See CANNOT_DISTINGUISH."""
    ledger = disclosure.Ledger()
    view = standing_mod.own_log(ledger.log_for("lane-nobody-loaded"), BEN, BEN, AT,
                                [himself()])
    assert view.state is standing_mod.LogAccess.GRANTED
    assert view.complete and list(view) == []


def test_receipts_over_an_unknown_lane_issue_nothing_without_saying_so():
    """The same seam from the guardian's side."""
    assert receipts.issue(disclosure.Ledger(), "lane-nobody-loaded", BEN,
                          [mother()], AT, b"k") == ()


def test_a_truncated_log_fails_against_its_anchor():
    log = a_log()
    anchor = log.anchor()
    ok, why = disclosure.verify_against(disclosure.Log(()), anchor)
    assert not ok and "truncated" in why


# --- voice.py: the rubric --------------------------------------------------


def test_voice_rubric_that_did_not_load_reports_unavailable_not_no_findings():
    """Rule 13's own sentence, as a test. An empty ruleset returning `[]` is
    the sentence *no findings* produced by a check that never ran."""
    compiled = voice._COMPILED
    try:
        voice._COMPILED = []
        found = voice.check("You're having a great season!")
        assert found, "an empty ruleset cleared a sentence it never looked at"
        assert "unavailable" in found[0]
        assert voice.blocking(found), "the unavailable finding did not block"
        assert not voice.ok("anything at all")
    finally:
        voice._COMPILED = compiled


def test_the_unavailable_finding_is_not_the_shape_of_a_clean_check():
    compiled = voice._COMPILED
    try:
        voice._COMPILED = []
        unavailable = voice.check("Your call time moved. Nothing else changed.")
    finally:
        voice._COMPILED = compiled
    clean = voice.check("Your call time moved. Nothing else changed.")
    assert clean == [], f"the control sentence is not clean: {clean}"
    assert unavailable != clean


def test_voice_payload_it_cannot_read_is_unknown_and_refuses():
    refused, findings = voice.refuses(voice.guard(field="text"), {"body": "hello"})
    assert refused and "unknown" in findings[0]


def test_voice_raises_in_the_guard_is_a_refusal_not_a_pass():
    def explodes(payload):
        raise RuntimeError("rubric store unreachable")

    refused, findings = voice.refuses(explodes, {"text": "hello"})
    assert refused and "unknown" in findings[0]


def test_dispatch_join_releases_nothing_when_the_rubric_is_unavailable():
    """End to end, through the only path that renders, gates and logs. This is
    the pane in `willow-grove`'s constraint 1: the source is down and the
    surface must not report health."""
    compiled = voice._COMPILED
    try:
        voice._COMPILED = []
        out = dispatch(health_field(), serving.Principal("g-mother", frozenset({"health"})),
                       [mother()], AT, lambda s: f"Allergy: {s.value}. P1, measured.")
        assert not out.released
        assert out.text is None
        assert out.blocked_by_voice
    finally:
        voice._COMPILED = compiled


# --- tools/conform.py: the conformance record ------------------------------


def test_conform_egress_over_a_tree_that_is_not_there_is_unknown():
    got = conform.check_no_egress(broken_tree())
    assert got.state is conform.State.UNKNOWN and not got.conforms
    assert "nothing was checked" in got.evidence


def test_conform_write_paths_over_a_tree_that_is_not_there_is_unknown():
    got = conform.check_write_paths(broken_tree())
    assert got.state is conform.State.UNKNOWN and not got.conforms


def test_conform_revocation_over_a_tree_that_is_not_there_is_unknown():
    got = conform.check_revocation_is_dated(broken_tree())
    assert got.state is conform.State.UNKNOWN and not got.conforms


def test_conform_suites_with_no_test_files_is_unknown_not_pass():
    with tempfile.TemporaryDirectory() as d:
        got = conform.check_suite_runs_standalone(Path(d))
    assert got.state is conform.State.UNKNOWN and not got.conforms


def test_conform_artifacts_that_are_absent_report_absent_not_pass():
    real = conform.ROOT
    try:
        with tempfile.TemporaryDirectory() as d:
            conform.ROOT = Path(d)
            assert conform.check_exit_line().state is conform.State.ABSENT
            assert conform.check_ablation().state is conform.State.ABSENT
    finally:
        conform.ROOT = real


#: Checks that consult no tree: they attempt a forbidden act against code
#: already imported and report whether it was refused. Over an unreachable
#: ROOT their PASS is still derived from a real attempt, so the sweep's rule
#: — nothing *reads* health out of a source that is not there — does not
#: reach them. Each entry carries its reason; an entry without one is a
#: finding, and `test_the_behavioral_exemptions_really_are_behavioral`
#: asserts membership is earned rather than declared.
BEHAVIORAL_CHECKS = {
    "anchor-payload": "builds an anchor carrying a subject_id in memory and "
                      "asserts the gate refuses it; no file is consulted",
}


def test_conform_sweep_no_check_reports_health_over_an_unreachable_tree():
    """`willow-grove` constraint 1's check, applied to every pane there is:
    *point the app at an unreachable DSN in CI and assert no surface reports
    health.* A check that raises counts as not-health; a check that returns PASS
    does not, whatever it says in its evidence — unless it is a behavioral
    check (`BEHAVIORAL_CHECKS`), whose PASS is an attempt refused in memory
    rather than a claim read from the missing tree."""
    real = conform.ROOT
    healthy, seen = [], []
    try:
        with tempfile.TemporaryDirectory() as d:
            conform.ROOT = Path(d)
            for factory in conform.CHECKS:
                try:
                    got = factory()
                except Exception as exc:  # a loud failure is not a passing check
                    seen.append((getattr(factory, "__name__", "?"), type(exc).__name__))
                    continue
                seen.append((got.id, got.state.value))
                if got.conforms and got.id not in BEHAVIORAL_CHECKS:
                    healthy.append(got)
    finally:
        conform.ROOT = real
    assert seen, "the sweep ran no checks at all, which proves nothing"
    assert not healthy, (
        "a conformance check reported PASS over a tree that is not there: "
        + "; ".join(f"{c.id} — {c.evidence[:80]}" for c in healthy)
    )


def test_the_behavioral_exemptions_really_are_behavioral():
    """The exemption list is itself a seam: an entry that names a check which
    *does* read the tree would quietly re-open the hole the sweep closes. So:
    every exempted id must exist in the registry, and its source must consult
    neither `ROOT` nor the filesystem."""
    import inspect
    by_id = {}
    for factory in conform.CHECKS:
        try:
            src = inspect.getsource(factory)
        except (OSError, TypeError):
            src = ""
        name = getattr(factory, "__name__", "")
        for cid in BEHAVIORAL_CHECKS:
            if f'"{cid}"' in src or f"'{cid}'" in src:
                by_id[cid] = src
    for cid, reason in BEHAVIORAL_CHECKS.items():
        assert reason and reason.strip(), f"{cid}: an exemption with no reason"
        assert cid in by_id, f"{cid}: exempted but no such check in the registry"
        src = by_id[cid]
        for marker in ("ROOT", "read_text", "open(", "glob", "exists()"):
            assert marker not in src, (
                f"{cid}: exempted as behavioral but its source touches "
                f"{marker!r} — it reads the tree, so the sweep must judge it"
            )


def test_the_record_of_such_a_run_reads_as_unknown_rather_than_as_conformance():
    """The rendered artifact is the surface here, and it must not read green."""
    checks = [conform.Check("a", "w", conform.State.UNKNOWN, "nothing was checked"),
              conform.Check("b", "w", conform.State.ABSENT, "does not exist")]
    text = conform.render(checks, datetime(2026, 7, 31, tzinfo=timezone.utc))
    assert "0 pass · 0 fail · 1 unknown · 1 absent" in text
    assert "`UNKNOWN` is not a pass" in text


# --- tools/sockets.py: the listener manifest -------------------------------


def test_sockets_manifest_absent_with_no_listeners_is_vacuous_not_clean():
    r = sockets.check([DECOYS / "clean.py"], broken_tree() / "manifest.json")
    assert r.verdict is sockets.Verdict.VACUOUS and not r.ok


def test_sockets_manifest_that_declares_nothing_at_all_is_not_a_clean_bill():
    """A manifest whose `listeners` key is missing — misspelled, nested, or not
    written yet — declared nothing. It was read as declaring none, and a typo
    then bought a `CLEAN` that an absent manifest could not."""
    with tempfile.TemporaryDirectory() as d:
        silent = written(Path(d), "manifest.json", '{"surfaces": ["console"]}')
        empty = written(Path(d), "empty.json", '{"listeners": []}')
        assert sockets.declared_from(silent) is None
        assert sockets.declared_from(empty) == ()
        assert sockets.check([DECOYS / "clean.py"], silent).verdict is sockets.Verdict.VACUOUS
        assert sockets.check([DECOYS / "all_interfaces.py"], silent).findings


def test_sockets_unresolved_bind_is_a_finding_not_a_pass():
    with tempfile.TemporaryDirectory() as d:
        m = written(Path(d), "manifest.json", '{"listeners": []}')
        r = sockets.check([DECOYS / "unresolved_bind.py"], m)
    assert "UNRESOLVED" in {f.code for f in r.findings}
    assert not r.ok


# --- source that will not parse, on all three static gates -----------------


def test_unparseable_source_is_a_finding_on_every_gate_that_scans_it():
    """A file nobody can read cannot be shown to be clean. All three scanners
    said so; the **egress gate** then dropped that answer on the floor, because
    an unparseable file reached `writes()` and not `egress()` — a PASS on the
    gate refusal 1 rests on, over a file nothing could read."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        written(p, "broken.py", "def broken(:\n")
        assert purity.egress([p]), "the egress gate saw nothing in an unreadable file"
        assert purity.writes([p])
        assert discipline.deletions([p])
        assert conform.check_no_egress(p).state is conform.State.FAIL
        assert conform.check_write_paths(p).state is conform.State.FAIL
        assert conform.check_revocation_is_dated(p).state is conform.State.FAIL
        found = sockets.scan_source("def broken(:\n", "broken.py")
        assert found and "unparseable" in found[0].how


# --- the rest of the tree: absence is never a zero -------------------------


def test_rung_parse_refuses_a_value_that_is_not_a_rung_rather_than_defaulting():
    for bad in ("L9", "", "3", "restricted"):
        try:
            rungs.parse(bad)
        except ValueError:
            continue
        raise AssertionError(f"parse({bad!r}) invented a rung")
    try:
        rungs.compose()
    except ValueError:
        return
    raise AssertionError("compose() of nothing returned a rung")


def test_export_manifest_absent_or_empty_fails_verification():
    ok, why = export.verify([export.Artifact("entries.csv", "text/csv", "a,b\n")])
    assert not ok and "MANIFEST" in why
    ok, why = export.verify([export.Artifact("MANIFEST.txt", "text/plain", "nothing here\n")])
    assert not ok and "lists no files" in why


def test_empty_history_raises_rather_than_reporting_a_zero():
    """A student with no sessions has no own-work statistic, and a lane with no
    entries has no transfer. Both are absences and neither is a zero."""
    for call in (lambda: practice.own([]),
                 lambda: exit_mod.transfer(
                     exit_mod.open_lane(LANE, BEN, at=OPENED,
                                        threshold=exit_mod.Threshold.MAJORITY,
                                        exit_terms="everything, as CSV, on request"),
                     entries=[], edges=[], at=AT)):
        try:
            call()
        except ValueError:
            continue
        raise AssertionError("an empty history was aggregated into a result")


def test_a_mark_with_no_score_position_makes_no_claim_about_the_score():
    got = marking.drift(marking.Mark("run-3", 91_400, "GE2", provenance="P1"))
    assert got.state is marking.Agreement.UNALIGNED
    assert got.drift_ms is None


# --- the findings, asserted to be still true -------------------------------


def test_finding_entitlement_and_envelope_stores_cannot_report_their_own_failure():
    """Asserted over the signature, because that is where the gap lives.

    `recipients()` takes its restrictions as *a sequence or a callable*, and the
    callable is the entire error channel: a source that raises becomes UNKNOWN.
    `serve()` takes `edges` and `envelopes` as sequences only, so a caller has
    exactly one way to say *nobody is entitled* and *nobody answered* — the
    empty sequence — and the predicate answers REFUSED to both. Red the day
    either parameter grows the shape `recipients` already has, which is the fix.
    """
    params = inspect.signature(serving.serve).parameters
    assert "Callable" not in str(params["edges"].annotation)
    assert "Callable" not in str(params["envelopes"].annotation)
    assert "Callable" in str(
        inspect.signature(sending.recipients).parameters["restrictions"].annotation
    ), "recipients() lost its error channel; this finding is now about both"
    down = serving.serve(health_field(), serving.Principal("g-mother"), [], AT)
    assert down.outcome is serving.Outcome.REFUSED
    assert crossing.permits((), from_lane="a", to_lane=LANE, at=AT) is None


def test_finding_a_widening_store_that_failed_looks_like_an_unwidened_category():
    assert "Callable" not in str(
        inspect.signature(standing_mod.widens).parameters["widenings"].annotation)
    down = standing_mod.widens((), subject_id=BEN, category="health", at=AT)
    none_signed = standing_mod.widens((), subject_id=BEN, category="health", at=AT,
                                      signer_edges=[mother()])
    assert down is None and none_signed is None


def test_finding_consent_cannot_tell_an_errored_lookup_from_no_relationship():
    errored = consent.governs(rungs.Rung.L3, "g-mother", BEN, [], AT)
    genuinely_none = consent.governs(rungs.Rung.L3, "stranger", BEN, [mother()], AT)
    assert errored.model is genuinely_none.model is consent.Model.UNKNOWN
    assert errored.reason == genuinely_none.reason


def test_finding_witness_cannot_tell_an_errored_receipt_store_from_no_receipts():
    """The mildest row on the list: UNWITNESSED is the right standing either
    way. What is wrong is the sentence under it — *no receipts at all* asserts
    something nobody established."""
    assert "Callable" not in str(
        inspect.signature(witness.standing).parameters["receipts"].annotation)
    ev = witness.standing(a_log(), [])
    assert ev.standing is witness.Standing.UNWITNESSED
    assert "no receipts at all" in ev.reason


def test_finding_the_ledger_answers_for_a_lane_it_has_never_heard_of():
    """The sharpest of the seven, because the empty answer is served rather than
    refused. Red the day `log_for` distinguishes them, and that is the fix."""
    ledger = disclosure.Ledger((("lane-ben", disclosure.Log()),))
    known_but_empty = ledger.log_for("lane-ben")
    never_heard_of = ledger.log_for("lane-nobody-loaded")
    assert known_but_empty == never_heard_of == disclosure.Log()


def test_finding_an_unaligned_mark_is_usable_whether_or_not_a_store_answered():
    got = marking.drift(marking.Mark("run-3", 91_400, "GE2", provenance="P1"))
    assert got.usable


# --- the list and the tests are a pair, so this is the middle (rule 12) ----


def test_every_seam_in_the_inventory_has_a_test():
    names = [n for n in globals() if n.startswith("test_")]
    for slug, module, breakage, expected in SEAMS:
        assert any(slug in n for n in names), (
            f"{module} seam {slug!r} is inventoried and untested: break it "
            f"({breakage}) and assert {expected}"
        )


def test_every_finding_in_the_list_has_a_test_that_will_go_red_when_it_is_fixed():
    names = [n for n in globals() if n.startswith("test_finding_")]
    assert len(names) >= len(CANNOT_DISTINGUISH) - 1, (
        "CANNOT_DISTINGUISH names more seams than there are tests holding them "
        "in place; a finding nothing asserts is a note, and notes rot"
    )
    for slug, why in CANNOT_DISTINGUISH:
        assert any(slug in s for s, *_ in SEAMS), (
            f"{slug!r} is listed as indistinguishable and is not in SEAMS"
        )
        assert why.strip(), f"{slug!r} carries no reason"


def test_the_suite_is_not_broken_shut():
    """Every refusal above is vacuous if nothing is ever served, witnessed or
    cleared. The control: with every source reachable, the answers arrive."""
    who = sending.recipients(BEN, [mother()], [], AT)
    assert tuple(who) == ("g-mother",)
    served = serving.serve(health_field(), serving.Principal("g-mother", frozenset({"health"})),
                           [mother()], AT)
    assert served.outcome is serving.Outcome.PAYLOAD and served.value == "peanut"
    assert voice.check("Call time is 5:15 at the band room.") == []
    assert conform.check_no_egress().state is conform.State.PASS
    assert consent.governs(rungs.Rung.L3, "g-mother", BEN, [mother()], AT).may_ask


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
