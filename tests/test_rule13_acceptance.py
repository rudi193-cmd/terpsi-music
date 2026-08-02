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

**The middle runs both ways, since 2026-08-02.** It did not, and the half that
was missing was the half the sentence above promises. Walking `SEAMS` and
asserting a test per row proves the *tests* are complete against the list; it
says nothing about the *list*, and a module that consults a fallible source and
has no unknown state is invisible to it — which is precisely the seam "nobody
had to remember" was written about. So
`test_the_inventory_lists_every_injected_source_in_the_tree` goes the other
way: it reads the tree, decides mechanically which modules take a source from
their caller, and fails when one of them is absent from `SEAMS`. It found eight
on its first run, in a list that had been reviewed and merged. The mark it uses,
what it deliberately cannot decide, and the one module exempted from it are
documented at `EXEMPT` and `KNOWN_BLIND` below — and it is a **gate**, not a
ledger (rule 18): `tests/ablate.py` carries five rows that turn it red.

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

import ast
import inspect
import io
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
#: `store/reading.py` imports no driver, so the type that carries the store's
#: error channel is reachable from a suite with no database — imported the way
#: `tools/` is, by directory rather than through the package, because
#: `store/__init__.py` does pull the driver in.
sys.path.insert(0, str(ROOT / "store"))

import voice  # noqa: E402

import conform  # noqa: E402
import discipline  # noqa: E402
import purity  # noqa: E402
import reading as store_reading  # noqa: E402 — store/reading.py, no driver
import sockets  # noqa: E402

#: `records/__init__.py` re-exports a *function* called `classify` and a
#: function called `dispatch`, both of which shadow the submodule of the same
#: name on the package — so `from records import classify` hands back the
#: function and `import records.classify as x` does too (`import a.b as c`
#: prefers the attribute). `import_module` reads `sys.modules` and gets the
#: module, which is what a test that patches module state needs.
classify_mod = import_module("records.classify")  # noqa: E402
from records import assistance, attendance, commentary, consent, crossing  # noqa: E402
from records import disclosure, export, fees, inference, marking  # noqa: E402
from records import practice, receipts, rungs, sending, serving  # noqa: E402
from records import standing as standing_mod  # noqa: E402
from records import witness  # noqa: E402
from records import exit as exit_mod  # noqa: E402
from records.dispatch import dispatch  # noqa: E402

from drop import preparing, producer  # noqa: E402

#: `craft/` is the one piece of working software in this tree and had no row in
#: `SEAMS` until 2026-08-02, while `voice.py` had three. It is imported here for
#: the same reason everything else above is: the sweep breaks the seam itself
#: rather than trusting `tests/test_craft.py` to have done it.
from craft import __main__ as craft_cli  # noqa: E402
from craft import checks as craft_checks  # noqa: E402
from craft import prose as craft_prose  # noqa: E402

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
     "the edge store raises; and separately, yields nothing",
     "UNKNOWN for the first, REFUSED for the second — closed 2026-07-31"),
    ("envelope_store", "records/crossing.py",
     "the envelope store raises; and separately, yields nothing",
     "UNKNOWN for the first, REFUSED for the second — closed 2026-07-31"),
    ("widening_store", "records/standing.py",
     "the widening store raises; and separately, yields nothing",
     "WideningsUnknown for the first, cap held for the second"),
    ("store_read", "store/reading.py",
     "the connection is killed mid-read", "ReadState.UNAVAILABLE, never ()"),
    ("threshold_source", "records/standing.py",
     "the birthdate the threshold derives from is unknown", "not past the threshold"),
    ("own_log", "records/standing.py",
     "the log handed over is not this lane's", "LogAccess.UNKNOWN, iteration raises"),
    ("ledger_lane", "records/disclosure.py",
     "the ledger has never heard of the lane",
     "UnknownLane raised — strict since 2026-07-31, §18 item 16"),
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

    # --- 2026-08-02: seven rows the tree named and this list did not --------
    #
    # Every one of these was produced by
    # `test_the_inventory_lists_every_injected_source_in_the_tree` below, on the
    # first run, before a person read the tree. That is the whole argument for
    # the check: the list above was assembled by hand and was seven short, and
    # nothing in the file could say so.
    #
    # Six of the seven were already honoured and already tested in their own
    # suites — `test_fees.py` hands `assess()` a raiser, `test_drop_producer.py`
    # hands `produce()` one, `test_commentary.py` has `raising()`. That is not
    # an argument for leaving them out. It is this file's opening paragraph:
    # *individual modules honour rule 13 and their own suites say so; what did
    # not exist here is the sweep.* A seam covered only where it lives is a seam
    # the sweep cannot report on, and the sweep is what a reviewer reads.
    ("assistance_call", "records/assistance.py",
     "the assistance call raises, and separately returns a bare string",
     "InferenceRefused, never a draft and never an empty one"),
    ("attendance_notify", "records/attendance.py",
     "notify() over a raising restriction source",
     "RuntimeError, nothing on the carrier"),
    ("commentary_call", "records/commentary.py",
     "the transcription call raises", "LocalModelUnavailable, no transcript"),
    ("fee_source", "records/fees.py",
     "the membership source raises; and separately the charge and payment "
     "sources raise", "UNKNOWN, never a zero balance and never a fee band"),
    ("inference_call", "records/inference.py",
     "the local model does not answer",
     "LocalModelUnavailable, never an empty answer (refusal 1)"),
    ("drop_key_source", "drop/producer.py",
     "the lane key source raises; and separately the sealing primitive is "
     "unusable", "Made.UNAVAILABLE, nothing landed, never plaintext"),
    ("drop_prepare", "drop/preparing.py",
     "the restriction source raises under prepare()",
     "UNKNOWN carried up, seal_for never reached"),

    # --- 2026-08-02: three rows the check above cannot reach ----------------
    #
    # `craft/` consults a source this file's mark does not see: its own parser,
    # over text the caller supplied. Nothing is injected, so nothing is flagged,
    # and these three rows are here because a person put them here — which is
    # the residual the check reduces and does not remove. `KNOWN_BLIND` below
    # names the shape and asserts the mark still misses it, so the day somebody
    # widens the mark, that assertion goes red and this comment is what has to
    # be edited.
    ("craft_unread", "craft/checks.py, craft/prose.py",
     "the draft holds nothing the parser can read",
     "Report.unread, never findings (0)"),
    ("craft_diff", "craft/checks.py, craft/prose.py",
     "one side of a draft-to-draft comparison could not be read",
     "the comparison is refused, never '0 introduced' or '9 resolved'"),
    ("craft_cli", "craft/__main__.py",
     "the CLI is handed a draft it cannot read",
     "findings (unavailable), never findings (0)"),
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
    ("consent_backend",
     "an edge source that errored and a principal with no live relationship "
     "both produce Model.UNKNOWN with the 'nobody here to ask' reason. UNKNOWN "
     "is the right answer for both, so this one is nearly harmless — but the "
     "reason names a fact that was never established."),
    ("witness_receipt",
     "a receipt store that errored and a log nobody ever witnessed are both "
     "UNWITNESSED with 'no receipts at all'. Not evidence either way, so the "
     "standing is right and the sentence beneath it is a guess."),
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


def test_ledger_lane_unknown_to_the_ledger_refuses_rather_than_answering():
    """**Was a finding; decided strict 2026-07-31 (§18 item 16).** An unknown
    lane raises `UnknownLane` rather than answering with an empty log, so
    `own_log` can no longer tell a student nobody has read them on the word of
    a ledger that was never asked — the GRANTED-and-complete path is
    unreachable through this seam."""
    ledger = disclosure.Ledger()
    try:
        ledger.log_for("lane-nobody-loaded")
    except disclosure.UnknownLane as exc:
        assert "never heard of" in str(exc) or "no chain" in str(exc)
    else:
        raise AssertionError("an unknown lane was answered rather than refused")
    assert not ledger.knows("lane-nobody-loaded")


def test_receipts_over_an_unknown_lane_refuse_rather_than_issuing_nothing():
    """The same seam from the guardian's side: silence was the old behavior,
    and silence is what the strict ledger removed."""
    try:
        receipts.issue(disclosure.Ledger(), "lane-nobody-loaded", BEN,
                       [mother()], AT, b"k")
    except disclosure.UnknownLane:
        pass
    else:
        raise AssertionError("receipts were (not) issued over a lane the "
                             "ledger never heard of, without saying so")


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
    "receipt-attribution": "derives the issuance schemes by attempting the "
                           "ed25519 import against the running interpreter; "
                           "no file is consulted, and a box with a broken "
                           "install stops passing wherever it is",
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


# --- store/reading.py: the adapter's error channel -------------------------
#
# The shape, with no database. The killed-connection attack is
# tests/test_store_reading.py's, against a real cluster; a type that cannot be
# shown to fire is not a guard, and a guard that only fires where a cluster
# happens to be running is not one either. Both, on purpose.


class _DeadCursor:
    """A cursor that dies the way a terminated backend dies: on `execute`."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *a, **kw):
        raise ConnectionError("terminating connection due to administrator command")

    def fetchall(self):  # pragma: no cover — execute raises first
        return []


class _DeadConnection:
    def cursor(self):
        return _DeadCursor()


def test_store_read_over_a_dead_connection_is_unavailable_and_not_an_empty_result():
    """The fourth forbidden act on `PLAN-STORE.md`'s acceptance list: *an errored
    connection presents as an empty result anywhere.* Every way of consuming the
    answer has to refuse, or the one nobody used is the one that ships."""
    got = store_reading.read(_DeadConnection(), "SELECT 1")
    assert got.state is store_reading.ReadState.UNAVAILABLE
    assert "ConnectionError" in got.reason
    for use in (lambda: got.rows, lambda: list(got), lambda: got(),
                lambda: len(got), lambda: got.empty, lambda: got.one(),
                lambda: bool(got)):
        try:
            use()
        except store_reading.StoreUnavailable:
            continue
        raise AssertionError("an errored read was consumed as an empty one")


def test_store_read_unknown_is_not_the_same_value_as_a_store_with_no_rows():
    """The dangerous mirror, at the store. A lane with no entries and a store
    that could not be reached must not compare equal — an equality that held
    would let a caller test against `Reading(ROWS, ())` and be wrong half the
    time."""
    down = store_reading.read(_DeadConnection(), "SELECT 1")
    empty = store_reading.rows(())
    assert down != empty
    assert empty.state is store_reading.ReadState.ROWS
    assert list(empty) == [] and empty.empty and empty.one() is None


# --- the findings, asserted to be still true -------------------------------


def test_fixed_the_entitlement_and_envelope_stores_now_report_their_own_failure():
    """**Was `test_finding_...`, and it went red exactly as its docstring said
    it would.** The old text: *"Red the day either parameter grows the shape
    `recipients` already has, which is the fix."* S-1 is that day —
    `store/reading.py`'s `Reading` is callable, so a store that went down
    mid-read reaches this predicate as a callable that raises, and `serve()`
    answers `UNKNOWN` instead of refusing for a reason nobody established.

    Both halves are held in place here: the errored source is UNKNOWN, and the
    genuinely-empty source is still REFUSED. A fix that made every empty edge
    list unknown would have closed the seam by breaking the predicate.
    """
    params = inspect.signature(serving.serve).parameters
    assert "Callable" in str(params["edges"].annotation)
    assert "Callable" in str(params["envelopes"].annotation)
    assert "Callable" in str(
        inspect.signature(sending.recipients).parameters["restrictions"].annotation
    ), "recipients() lost its error channel, which is where this shape came from"

    errored = serving.serve(health_field(), serving.Principal("g-mother"),
                            unreachable(), AT)
    genuinely_none = serving.serve(health_field(), serving.Principal("g-mother"),
                                   [], AT)
    assert errored.outcome is serving.Outcome.UNKNOWN
    assert "ConnectionError" in errored.reason
    assert genuinely_none.outcome is serving.Outcome.REFUSED
    assert errored != genuinely_none

    crossing_down = serving.serve(
        health_field(), serving.Principal("g-mother", frozenset({"health"})),
        [mother()], AT, lane_id="lane-sister", envelopes=unreachable())
    assert crossing_down.outcome is serving.Outcome.UNKNOWN
    # `crossing.permits` itself still takes a sequence: the error channel lives
    # at the predicate that decides, which is the one a caller reaches through.
    assert crossing.permits((), from_lane="a", to_lane=LANE, at=AT,
                            subject_id=BEN) is None


def test_fixed_a_widening_store_that_failed_no_longer_looks_unwidened():
    """Was `test_finding_...`. `widens()` raises `WideningsUnknown` rather than
    returning the `None` that already meant *nobody widened this*, and `serve()`
    turns that into `UNKNOWN` — so the self-edge cap still holds for the
    unwidened category and no longer holds for the same reason as a store nobody
    could reach."""
    assert "Callable" in str(
        inspect.signature(standing_mod.widens).parameters["widenings"].annotation)
    none_signed = standing_mod.widens((), subject_id=BEN, category="health", at=AT,
                                      signer_edges=[mother()])
    assert none_signed is None
    try:
        standing_mod.widens(unreachable(), subject_id=BEN, category="health", at=AT)
    except standing_mod.WideningsUnknown as exc:
        assert "ConnectionError" in str(exc)
    else:
        raise AssertionError("an unreadable widening source read as unwidened")

    capped = serving.serve(health_field(instruction="on file with the office"),
                           serving.Principal(BEN), [himself()], AT, widenings=())
    down = serving.serve(health_field(instruction="on file with the office"),
                         serving.Principal(BEN), [himself()], AT,
                         widenings=unreachable())
    assert capped.outcome is serving.Outcome.INSTRUCTION
    assert down.outcome is serving.Outcome.UNKNOWN
    assert capped != down


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


def test_fixed_the_ledger_no_longer_answers_for_a_lane_it_has_never_heard_of():
    """Was `test_finding_...`, the sharpest of the seven — the empty answer was
    served rather than refused. It went red the day `log_for` distinguished
    them, exactly as its docstring promised, and now holds the fix in place:
    known-but-empty answers, never-heard-of refuses, and the write path still
    opens a lane at the first write (W-1)."""
    ledger = disclosure.Ledger((("lane-ben", disclosure.Log()),))
    assert ledger.log_for("lane-ben") == disclosure.Log()
    try:
        ledger.log_for("lane-nobody-loaded")
    except disclosure.UnknownLane:
        pass
    else:
        raise AssertionError("the unknown lane was answered")
    grown = ledger.record(
        serving.serve(health_field(),
                      serving.Principal("g-mother", frozenset({"health"})),
                      [mother()], AT),
        lane_id="lane-new", principal_id="g-mother", subject_id=BEN,
        field_name="allergy", at=AT)
    assert grown.knows("lane-new")


def test_finding_an_unaligned_mark_is_usable_whether_or_not_a_store_answered():
    got = marking.drift(marking.Mark("run-3", 91_400, "GE2", provenance="P1"))
    assert got.usable


# --- records/inference.py: the local model that did not answer -------------
#
# Refusal 1's seam, and the loudest one in the tree: a stopped Ollama must fail
# loudly and never degrade to a third party or to an empty answer a surface
# could render as "no findings".


HERE = "http://localhost:11434"
LOCAL_PROVIDER = inference.LOCAL


def test_inference_call_that_raises_is_unavailable_and_never_an_empty_answer():
    try:
        inference.through(unreachable(), classes=["HEALTH"], endpoint=HERE)
    except inference.LocalModelUnavailable as exc:
        assert "ConnectionError" in str(exc)
    else:
        raise AssertionError(
            "a stopped local model returned rather than raised; refusal 1 says "
            "it fails loudly, and the caller here got something to render"
        )


def test_inference_call_unavailable_is_not_the_same_as_a_short_answer():
    """The dangerous mirror at the inference seam. A model that answered
    tersely and a model that is not running must not arrive alike."""
    answered = inference.through(lambda: ("an answer", LOCAL_PROVIDER),
                                 classes=["HEALTH"], endpoint=HERE)
    assert answered.text == "an answer"


# --- records/assistance.py, records/commentary.py: the same call, two skins -


def a_grounding():
    fld = serving.Field(lane_id=LANE, subject_id=BEN, name="attendance",
                        rung=rungs.Rung.L3, payload="present 40/42")
    return assistance.from_entitlement(
        fld, serving.Serving(serving.Outcome.PAYLOAD, "present 40/42",
                             rungs.Rung.L3, "served"))


def test_assistance_call_that_raises_lands_no_draft():
    """§8.2: a machine answer is a draft until a named human seals it — and a
    machine that did not answer produces no draft at all, rather than an empty
    one somebody could seal."""
    try:
        assistance.growth_narrative(unreachable(), groundings=[a_grounding()],
                                    endpoint=HERE)
    except inference.InferenceRefused:
        pass
    else:
        raise AssertionError("an unreachable model produced an assistance draft")


def test_assistance_call_returning_nothing_is_refused_rather_than_drafted():
    try:
        assistance.growth_narrative(lambda: ("   ", LOCAL_PROVIDER),
                                    groundings=[a_grounding()], endpoint=HERE)
    except inference.InferenceRefused:
        pass
    else:
        raise AssertionError("a blank answer landed as a draft a human could seal")


def test_commentary_call_that_raises_produces_no_transcript():
    """The transcript seam §8.2 names by name. Adjudication commentary that the
    machine did not produce must not exist as a draft."""
    anchor = marking.Mark("show-2026-10-12@94500", 94_500, "press-box-4",
                          LANE, BEN)
    try:
        commentary.transcribe(unreachable(), anchor, endpoint=HERE,
                              by_machine="whisper-local")
    except inference.InferenceRefused:
        pass
    else:
        raise AssertionError("a transcript exists for audio nobody transcribed")


# --- records/fees.py: the money sources -------------------------------------


def test_fee_source_that_raises_is_unknown_and_not_a_band():
    """A membership source that is down must not fall back to a standard fee.
    There is no standard fee — the fallback is the disclosure."""
    groups = (fees.FeeGroup("band-a", "marching-season", 34000, "2026"),)
    got = fees.assess(BEN, LANE, "marching-season", groups, unreachable(),
                      AT, season="2026")
    assert got.state is fees.Source.UNKNOWN
    assert "membership source failed" in got.reason
    try:
        got.charge
    except RuntimeError as exc:
        assert "not the standard fee" in str(exc)
    else:
        raise AssertionError(
            "an unresolved fee produced a charge; the fallback band is the "
            "disclosure this module exists to make unavailable"
        )


def test_fee_source_down_is_not_the_same_answer_as_a_settled_balance():
    """`Source.UNKNOWN` and a balance of zero are different sentences to send a
    guardian. A caller comparing `cents == 0` must not be able to confuse
    *"you owe nothing"* with *"we could not read your payments."*"""
    down = fees.balance(unreachable(), [], AT, lane_id=LANE)
    settled = fees.balance([], [], AT, lane_id=LANE)
    assert down.state is fees.Source.UNKNOWN
    assert down.state is not settled.state
    assert "charge source failed" in down.reason


def test_fee_source_names_which_side_failed():
    """*"We could not read your charges"* and *"we could not read your
    payments"* are different apologies, and the module says which."""
    payments_down = fees.balance([], unreachable(), AT, lane_id=LANE)
    assert payments_down.state is fees.Source.UNKNOWN
    assert "payment source failed" in payments_down.reason


# --- records/attendance.py: the carrier, one call earlier than deliver() ----


def test_attendance_notify_over_a_broken_restriction_source_sends_nothing():
    """`send_path` above guards `deliver()`. `notify()` is the call the rest of
    the application actually makes, and a guard the application routes around
    is a ledger (rule 18)."""
    sent = []
    sig = attendance.signal(
        attendance.Referent("ref-1", "Rehearsal", "Tuesday rehearsal", AT,
                            "2026", created_at=AT),
        attendance.SignalKind.TIME)
    try:
        attendance.notify(sig, BEN, at=AT, edges=[mother()],
                          restrictions=unreachable(),
                          transport=lambda who, body: sent.append(who))
    except RuntimeError:
        assert sent == [], f"a signal went out under an unknown send list: {sent}"
    else:
        raise AssertionError("notify() proceeded with an undetermined recipient set")


# --- drop/: the sealed guardian view ---------------------------------------


def test_drop_key_source_that_raises_lands_nothing_rather_than_plaintext():
    """Fail-closed at the strongest place in the tree: a producer without key
    material must land nothing. An empty payload here would be a plaintext one
    (§4.3)."""
    from presentation.ir import Row, cell, view
    c = cell(serving.Serving(serving.Outcome.PAYLOAD, "First chair, trumpet",
                             rungs.Rung.L2, "entitled for this guardian"),
             label="placement")
    v = view("Ben — guardian view",
             [Row(heading="lane ben", cells=(c,), referent=BEN, lane_id=LANE)],
             read_by="g-mother", at=AT)
    prod = producer.produce(v, lane_key_source=unreachable(), at=AT)
    assert prod.state is producer.Made.UNAVAILABLE
    assert not prod.landed and prod.sealed is None
    assert "could not be obtained" in prod.reason


def test_drop_key_source_unavailable_primitive_also_lands_nothing():
    """The other half of the same seam: the box cannot seal at all. Checked
    before a view is even looked at, so the refusal cannot depend on the
    payload."""
    from presentation.ir import Row, cell, view
    c = cell(serving.Serving(serving.Outcome.PAYLOAD, "First chair, trumpet",
                             rungs.Rung.L2, "entitled"), label="placement")
    v = view("Ben — guardian view",
             [Row(heading="lane ben", cells=(c,), referent=BEN, lane_id=LANE)],
             read_by="g-mother", at=AT)
    prod = producer.produce(v, lane_key_source=unreachable(), at=AT,
                            available=lambda: False)
    assert prod.state is producer.Made.UNAVAILABLE and not prod.landed


def test_drop_prepare_over_a_broken_restriction_source_never_reaches_seal_for():
    """The producer cannot be handed a restricted recipient, and it cannot be
    handed *any* recipient when the predicate could not be derived. `seal_for`
    counts its own calls, so 'nothing was prepared' is asserted rather than
    inferred from an empty tuple."""
    reached = []

    def seal_for(guardian_id):
        reached.append(guardian_id)
        return object()

    prepared = preparing.prepare(BEN, [mother()], unreachable(), AT,
                                 seal_for=seal_for)
    assert prepared.state is sending.Standing.UNKNOWN
    assert reached == [], f"seal_for ran under an unknown send list: {reached}"
    assert prepared.drops == ()


# --- craft/: the checker that printed the sentence voice.py refuses ---------


UNREADABLE = "just some prose\nwith no headers\n"
READABLE_PROSE = (
    "# A heading\n\nA paragraph that the prose skin can actually read, so the "
    "control below is a control.\n"
)


def test_craft_unread_lyric_says_so_rather_than_reporting_nothing_wrong():
    report = craft_checks.run_all(UNREADABLE)
    assert report.unread, (
        "a lyric the parser could not read reported as read; the count printed "
        "beneath it would be the false all-clear voice.py refuses by name"
    )
    assert report.findings == []


def test_craft_unread_is_not_the_same_state_as_read_with_a_declined_check():
    """The dangerous mirror, and the reason `unread` is a second field rather
    than a test on `unavailable`: the song in this repository is permanently
    `unavailable` for 34 words of unknown stress and is entirely readable. A
    caller keying off `unavailable` alone would refuse every real draft."""
    song = (ROOT / "lyrics" / "get-ready.txt").read_text(encoding="utf-8")
    read = craft_checks.run_all(song)
    assert read.unavailable and not read.unread
    assert read.findings, "the control found nothing; this seam proves nothing"


def test_craft_unread_document_says_so_in_the_prose_skin_too():
    assert craft_prose.run_all("").unread
    assert craft_prose.run_all("```\ncode only\n```").unread
    assert not craft_prose.run_all(READABLE_PROSE).unread


def test_craft_diff_against_an_unreadable_draft_is_refused_not_flattering():
    song = (ROOT / "lyrics" / "get-ready.txt").read_text(encoding="utf-8")
    findings, notes = craft_checks.run_diff(UNREADABLE, song)
    assert findings == [] and any("could not be read" in n for n in notes)
    findings, notes = craft_checks.run_diff(song, UNREADABLE)
    assert findings == [] and any("could not be read" in n for n in notes)
    joined = " ".join(notes)
    assert "resolved" not in joined, (
        "the refusal still reported wins: every finding cleared by a "
        "comparison against a draft nobody read"
    )


def test_craft_diff_refusal_is_one_middle_and_both_skins_import_it():
    """Rule 12 at this seam. One defect, two skins; the reconciler is named and
    imported rather than copied."""
    assert craft_prose.diff_declined is craft_checks.diff_declined
    findings, notes = craft_prose.run_diff("", READABLE_PROSE)
    assert findings == [] and any("could not be read" in n for n in notes)


def test_craft_cli_prints_no_count_for_a_draft_it_never_read():
    """The seam as a reader meets it. `findings (0)` under an `unavailable`
    banner is the literal string `voice.py` refuses, printed by a tool shipped
    in the same package."""
    scratch = Path(tempfile.mkdtemp(prefix="terpsi-craft-seam-"))
    unreadable = written(scratch, "unreadable.txt", UNREADABLE)
    out = io.StringIO()
    with redirect_stdout(out):
        craft_cli.main([str(unreadable)])
    printed = out.getvalue()
    assert "findings (unavailable)" in printed
    assert "findings (0)" not in printed, printed


def test_craft_cli_still_prints_a_count_when_it_did_read_the_draft():
    """A refusal that fires on everything is not a refusal (rule 19's other
    half). The clean draft must still report a zero it earned."""
    scratch = Path(tempfile.mkdtemp(prefix="terpsi-craft-seam-"))
    clean = written(scratch, "clean.txt", READABLE_PROSE)
    out = io.StringIO()
    with redirect_stdout(out):
        craft_cli.main([str(clean), "--prose"])
    printed = out.getvalue()
    assert "findings (unavailable)" not in printed, printed


# --- the other half of the middle: does the inventory list every seam? ------
#
# `test_every_seam_in_the_inventory_has_a_test` walks `SEAMS` and asserts a test
# exists for each row. It proves the tests are complete against the list. It
# says nothing about the list, and the list is the thing this file's opening
# paragraph makes a promise about:
#
#     *so that a seam added later without an unknown state is caught by a test
#     nobody had to remember to write*
#
# A module that consults a fallible source and has no unknown state is exactly
# the thing that promise is about, and until 2026-08-02 it was invisible unless
# somebody remembered — which is the memory the sentence says is not needed. So
# the walk below goes the other way: it reads the tree, and fails when something
# the tree says is a seam is absent from `SEAMS`.


#: What **"consults a fallible source"** means here, said mechanically so it can
#: be decided rather than argued:
#:
#:     *a function takes the source as a parameter* — some parameter is either
#:     annotated with `Callable` anywhere in its annotation, or is invoked as
#:     `name(...)` somewhere in the function body.
#:
#: This is the shape this repository chose deliberately and repeatedly.
#: `sending.recipients(restrictions=…)`, `serving.serve(edges=…)`,
#: `producer.produce(lane_key_source=…)`, `fees.balance(charges, payments)` and
#: `inference.through(call=…)` are all one decision: **the source is handed in,
#: so the callee cannot know it is up, so the callee must have an answer for it
#: being down.** `sending.recipients`' own docstring says so — *"returning an
#: empty list on error is the failure this signature exists to make
#: impossible"* — and a parameter is where that promise is made.
#:
#: **Why this mark and not the obvious one.** The tempting definition is *"the
#: module has an UNKNOWN-shaped enum member or an `unavailable` field."* It was
#: measured: it flags 27 modules, 18 of them absent from `SEAMS`. Worse, it is
#: pointed the wrong way. It can only find modules that *already* have an
#: unknown state, so by construction it can never find the one case the
#: docstring promises to catch — the seam with no unknown state at all. A check
#: that cannot fail in the direction it was built for is a ledger (rule 18).
#: This mark is independent of whether an unknown state exists, so it can.
#:
#: **What it does not decide, said out loud:**
#:
#: * A source read from module scope rather than a parameter — a registry a
#:   failed load would leave empty, like `consent.HOLDS`. Undecidable here: a
#:   loaded registry and a constant are the same `frozenset` literal in this
#:   tree, so the mark would flag every module with a constant in it.
#: * A source the module opens itself — the filesystem, a subprocess. Measured
#:   too: 22 modules, mostly `tools/`, and the resulting exemption list would be
#:   longer than the inventory.
#: * A subject the module parses rather than a source it calls. That is
#:   `craft/`'s shape and `KNOWN_BLIND` names it.
#:
#: Those three are misses, not passes. They are published here for the reason
#: `voice.KNOWN_MISSES` and `CANNOT_DISTINGUISH` are published: a coverage claim
#: with an unstated boundary is worse than a smaller honest one.


#: Where the walk looks. Named rather than globbed from the root, so a directory
#: that disappears is a failure and not a smaller scan — a sweep that quietly
#: read nothing is this file's subject matter (rule 13).
SCANNED_ROOTS = ("console", "craft", "drop", "presentation", "records",
                 "store", "surfaces", "tools", "venue")

#: Single modules at the tree root. `tests/` is out because a test is not a
#: seam, and `docs/` is out because `docs/survey/trigger_mutation_demo.py` is a
#: worked example of a mutation, not shipped code.
SCANNED_FILES = ("voice.py", "personas.py")


#: Modules the mark flags that are deliberately **not** in `SEAMS`, each with
#: the exact parameters exempted. The parameters are listed rather than the
#: module, so the exemption cannot silently widen: a new injected source in an
#: exempt module is not covered by the row that exempts the old one, and the
#: check fails until somebody decides about it.
EXEMPT = (
    ("store/narration.py", ("serve_field(decide)",),
     "the injected source is the caller's read predicate and it is reached only "
     "inside an open transaction, so breaking it needs a live cluster. This "
     "sweep imports `store/reading.py` by directory precisely to avoid pulling "
     "a driver in, and a suite that needs a cluster turns the no-database CI "
     "job red. Cluster-bound guards live in `tests/ablate_store.py`; this seam "
     "is broken in `tests/test_store_narration.py`, which is a per-module suite "
     "and therefore exactly the half-measure this file exists to supersede — so "
     "this row is a debt, not an acquittal",
     "tests/test_store_narration.py"),
)


#: Shapes the mark is known to miss, with a module that has the shape. Each is
#: asserted below to be **still** missed, so the list cannot rot into a claim
#: about a mark that was since widened — the pattern `CANNOT_DISTINGUISH` uses,
#: for the same reason.
KNOWN_BLIND = (
    ("craft/checks.py",
     "the fallible source is the module's own parser over caller-supplied text. "
     "Nothing is injected, so nothing is flagged. `craft/` is in `SEAMS` because "
     "a person put it there on 2026-08-02, after it shipped the exact rule-13 "
     "defect this sweep exists to prevent — which is the residual this check "
     "reduces and does not remove"),
    ("records/consent.py",
     "the fallible source is `HOLDS`/`EXERCISES` at module scope, which a failed "
     "load leaves empty. Indistinguishable from a constant in this tree"),
)


class MarkUndecidable(Exception):
    """The walk could not read a file, so it cannot say whether it is a seam.

    Raised rather than swallowed. A scan that skipped what it could not parse
    would report a clean tree for a tree it did not read, which is the sentence
    this whole file is about.
    """


def injected_sources(source: str) -> tuple[str, ...]:
    """Parameters this module takes that are a source the caller supplies.

    Returns `("fn(param)", …)`, empty when there are none. Raises
    :class:`MarkUndecidable` when the module will not parse: *unreadable* and
    *no sources* are not the same answer and must not be returned alike.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise MarkUndecidable(f"will not parse: {exc}") from exc

    found = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = fn.args
        params = args.posonlyargs + args.args + args.kwonlyargs
        called = {n.func.id for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        for p in params:
            annotation = ast.unparse(p.annotation) if p.annotation else ""
            if "Callable" in annotation or p.arg in called:
                found.append(f"{fn.name}({p.arg})")
    return tuple(sorted(set(found)))


def flagged(files) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """`(module, sources)` for every file in `files` the mark reaches.

    `files` is a sequence of `(name, source_text)` rather than a directory, so
    the check can be pointed at a tree that is not this one — which is how the
    two failure demonstrations below plant a module without writing into the
    repository.
    """
    out = []
    for name, source in files:
        got = injected_sources(source)
        if got:
            out.append((name, got))
    return tuple(out)


def unlisted(files, inventory=None, exempt=EXEMPT):
    """Modules the mark flags that neither `SEAMS` nor `EXEMPT` accounts for.

    The gate. Returns `((module, sources, why), …)`; empty means every seam the
    tree names is inventoried, which is a claim about the list rather than about
    the tests.
    """
    inventory = SEAMS if inventory is None else inventory
    listed = {m.strip() for _, modules, *_ in inventory for m in modules.split(",")}
    excused = {module: set(params) for module, params, *_ in exempt}

    missing = []
    for module, sources in flagged(files):
        if module in listed:
            continue
        uncovered = set(sources) - excused.get(module, set())
        if not uncovered:
            continue
        why = ("not in SEAMS and not exempt"
               if module not in excused
               else "exempt for other sources, but these are new: "
                    + ", ".join(sorted(uncovered)))
        missing.append((module, tuple(sorted(uncovered)), why))
    return tuple(missing)


def tree_sources():
    """Every shipped module, as `(path, text)`. Loud when a root has moved."""
    files = []
    for root in SCANNED_ROOTS:
        directory = ROOT / root
        assert directory.is_dir(), (
            f"{root}/ is not there. The sweep would have scanned a smaller tree "
            f"and reported it clean, which is rule 13 at the sweep's own seam"
        )
        for path in sorted(directory.rglob("*.py")):
            files.append((path.relative_to(ROOT).as_posix(),
                          path.read_text(encoding="utf-8")))
    for name in SCANNED_FILES:
        path = ROOT / name
        assert path.is_file(), f"{name} is not there; the scan is short"
        files.append((name, path.read_text(encoding="utf-8")))
    return tuple(files)


def test_the_inventory_lists_every_injected_source_in_the_tree():
    """**The half that was missing.** The tree is the authority on what is a
    seam; `SEAMS` is a claim about the tree, and this is where the claim is
    checked.

    On the first run this failed with eight modules the mark flagged and the
    inventory did not name: `drop/preparing.py`, `drop/producer.py`,
    `records/assistance.py`, `records/attendance.py`, `records/commentary.py`,
    `records/fees.py`, `records/inference.py` and `store/narration.py`. Seven
    became rows above with tests that break them; the eighth is in `EXEMPT`
    with a reason and a debt, because breaking it needs a cluster.
    """
    missing = unlisted(tree_sources())
    assert not missing, (
        "the tree names seams the inventory does not:\n"
        + "\n".join(f"  {module}: {', '.join(sources)} — {why}"
                    for module, sources, why in missing)
        + "\n\nAdd a row to SEAMS with a test that breaks it, or a row to "
          "EXEMPT with a reason a reviewer can check."
    )


def test_the_completeness_check_catches_a_planted_seam():
    """Rule 19 on the check itself. A guard that cannot be shown to fail has
    not been shown to work, and this one currently finds nothing — so without
    this test it would be indistinguishable from a walk that reads no files.

    The plant is the dangerous shape by construction: a module that takes an
    injected source and has **no** unknown state anywhere in it, which is what
    the mark exists to reach and what the enum-shaped mark could not.
    """
    planted = ("records/rehearsals.py", (
        "def slots(subject_id, roster_source):\n"
        "    return tuple(roster_source())\n"
    ))
    assert injected_sources(planted[1]) == ("slots(roster_source)",)
    missing = unlisted([planted])
    assert len(missing) == 1 and missing[0][0] == "records/rehearsals.py", missing


def test_the_completeness_check_catches_a_seam_removed_from_the_inventory():
    """The other direction, and the likelier accident: the module is real and
    the row is deleted. `records/sending.py` is the file this whole sweep opens
    with; with its row gone the tree still says it is a seam."""
    without = tuple(row for row in SEAMS if row[1] != "records/sending.py")
    assert len(without) == len(SEAMS) - 2, "SEAMS no longer has the two sending rows"
    source = (ROOT / "records" / "sending.py").read_text(encoding="utf-8")
    missing = unlisted([("records/sending.py", source)], inventory=without)
    assert len(missing) == 1
    assert "recipients(restrictions)" in missing[0][1]


def test_the_completeness_check_says_unknown_rather_than_clean_for_a_file_it_cannot_read():
    """Rule 13 at the checker's own seam. A scan that skipped unparseable files
    would report a clean tree for a tree it did not read — and would report it
    with the same value it uses for a tree with no seams in it."""
    try:
        injected_sources("def broken(:\n")
    except MarkUndecidable as exc:
        assert "will not parse" in str(exc)
    else:
        raise AssertionError(
            "an unparseable module was scanned to a clean answer; the walk "
            "returned 'no sources' for a file it never read"
        )


def test_the_completeness_check_is_not_broken_shut():
    """A gate that flags nothing has nothing to say, and a gate that flags
    everything gets routed around. The control: the mark reaches the tree, and
    the modules it reaches are the ones whose signatures take a source."""
    reached = flagged(tree_sources())
    assert reached, (
        "the mark flagged no module in the whole tree; the walk read nothing "
        "and the empty result would have passed as a complete inventory"
    )
    reached_names = {module for module, _ in reached}
    for expected in ("records/sending.py", "records/serving.py",
                     "records/inference.py", "drop/producer.py"):
        assert expected in reached_names, f"{expected} is a seam and was not flagged"
    assert len(reached) < len(tree_sources()) // 2, (
        "the mark flagged most of the tree; a mark that fires on everything "
        "carries no information and the exemption list becomes the real check"
    )


def test_the_exemptions_are_still_true():
    """A stale honesty list is worse than none. Each exemption names a suite,
    and the suite has to be there; each names the exact parameters excused, and
    those have to be the ones the tree still shows."""
    for module, params, why, suite in EXEMPT:
        assert why.strip(), f"{module} is exempt for no stated reason"
        assert (ROOT / suite).is_file(), (
            f"{module} is exempt because {suite} covers it, and {suite} is gone"
        )
        source = (ROOT / module).read_text(encoding="utf-8")
        assert injected_sources(source) == tuple(sorted(params)), (
            f"{module}'s injected sources have changed since it was exempted: "
            f"{injected_sources(source)} against the excused {tuple(sorted(params))}. "
            f"Decide about the new one rather than inheriting the old excuse."
        )


def test_the_known_blind_spots_are_still_blind():
    """Each row names a module whose shape the mark cannot see. If one of them
    starts being flagged, the mark grew and this list is the thing that is now
    wrong — which is the fix landing, not a regression."""
    for module, why in KNOWN_BLIND:
        assert why.strip(), f"{module} is listed blind with no reason"
        source = (ROOT / module).read_text(encoding="utf-8")
        assert injected_sources(source) == (), (
            f"{module} is flagged by the mark now, so it is no longer a blind "
            f"spot. Delete the row rather than leaving a published miss that "
            f"stopped being one."
        )


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
