"""Refusal 1, attacked from every direction it can be got around.

Rule 19: a guard that cannot be shown to fail has not been shown to work. Every
test here attempts the forbidden act — a cloud provider, an unlabelled answer,
an untagged call, a local label at somebody else's address, a stopped local
model rendered as an empty string — and asserts the refusal.

Two of these are **middles** rather than checks (rule 12, and the pair is named
in the same commit as it is created):

    test_the_classes_here_are_the_ones_the_ladder_defines
        pair: docs/SENSITIVITY.md's class-to-L table <-> inference.CLASSES.
        Two copies of §6's eight class names. This parses the table.

    test_the_covered_five_are_the_five_the_refusal_names
        pair: CLAUDE.md refusal 1 <-> inference.COVERED_CLASSES. The clause is
        prose and the guard is code; this reads the prose.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_inference.py
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.inference import (  # noqa: E402
    CLASSES, CLAUSE, COVERED_CLASSES, KNOWN_REMOTE, LOCAL, LOOPBACK_HOSTS, NARRATION,
    Answer, InferenceRefused, LocalModelUnavailable, NonLocalInference, OffBoxLocalModel,
    Refusal, Unclassified, UnknownProvider, accept, covered, is_local_address, through,
)
from records.rungs import Rung  # noqa: E402

HERE = "http://localhost:11434"
HEALTH = ["HEALTH"]


def _refused(fn, *a, **kw):
    """Run something that must refuse and return the refusal."""
    try:
        fn(*a, **kw)
    except InferenceRefused as exc:
        return exc
    raise AssertionError(f"{getattr(fn, '__name__', fn)} did not refuse")


# --- the one thing that is allowed to happen ------------------------------


def test_the_local_model_answering_is_the_only_served_state():
    a = accept(("Two physicals are outstanding.", LOCAL),
               classes=HEALTH, endpoint=HERE, rung=Rung.L4)
    assert a.text == "Two physicals are outstanding."
    assert a.provider == LOCAL and a.classes == frozenset(HEALTH)
    assert a.covered_by_refusal_1


def test_every_loopback_spelling_is_this_machine():
    for where in ("http://localhost:11434", "http://127.0.0.1:11434",
                  "http://[::1]:11434", "127.0.0.1", "http://127.0.0.9:11434/api/chat"):
        assert is_local_address(where), where
        accept(("ok", LOCAL), classes=HEALTH, endpoint=where)


# --- a third party answered -----------------------------------------------


def test_the_whole_documented_cloud_chain_refuses():
    """Not one example. `_chain()` upstream can hand back any of these, and
    `hns` is the one that looks local — it is the *local runner on another
    node*, reached over the network, and it is still not this machine."""
    assert KNOWN_REMOTE and LOCAL not in KNOWN_REMOTE
    for provider in sorted(KNOWN_REMOTE):
        exc = _refused(accept, ("an answer", provider), classes=HEALTH, endpoint=HERE)
        assert isinstance(exc, NonLocalInference), provider
        assert exc.state is Refusal.NON_LOCAL_PROVIDER


def test_a_provider_nobody_has_heard_of_refuses_too():
    """An allowlist of known-bad names would pass the next provider the fleet
    adds. The check is `== LOCAL`, so a new label refuses by default."""
    exc = _refused(accept, ("an answer", "some-new-frontier-thing"),
                   classes=HEALTH, endpoint=HERE)
    assert isinstance(exc, NonLocalInference)


def test_case_does_not_launder_a_provider():
    for near in ("Ollama", "OLLAMA", " ollama", "ollama "):
        assert isinstance(_refused(accept, ("a", near), classes=HEALTH, endpoint=HERE),
                          NonLocalInference), near


def test_a_cloud_provider_refuses_even_for_the_least_sensitive_class():
    """There is no branch that trades sensitivity for a provider. A guard with
    one would be the allowlist field the clause forbids, reached by argument
    instead of by keyword."""
    for tag in sorted(CLASSES):
        assert isinstance(_refused(accept, ("a", "groq"), classes=[tag], endpoint=HERE),
                          NonLocalInference), tag


# --- nobody said who, or where --------------------------------------------


def test_a_missing_provider_is_a_refusal_and_never_a_pass():
    for provider in (None, "", "   ", 0, object()):
        exc = _refused(accept, ("an answer", provider), classes=HEALTH, endpoint=HERE)
        assert isinstance(exc, UnknownProvider), repr(provider)


def test_a_bare_string_return_is_refused_rather_than_assumed_local():
    """`core/llm_edge.py`'s `respond()` calls the router, discards the provider
    label and returns the text — then falls through to Groq and to Ollama
    inside two bare `except: pass` blocks. A caller who reaches for it has an
    answer and no way to say what produced it."""
    exc = _refused(accept, "just the text", classes=HEALTH, endpoint=HERE)
    assert isinstance(exc, UnknownProvider) and "llm_edge" in exc.detail


def test_a_pair_of_the_wrong_shape_is_refused():
    for pair in (None, ("only-one",), ("a", LOCAL, "extra"), {"text": "a"}, 7):
        assert isinstance(_refused(accept, pair, classes=HEALTH, endpoint=HERE),
                          UnknownProvider), repr(pair)


def test_the_local_label_at_another_machine_is_its_own_refusal():
    """`_try_ollama` posts to `OLLAMA_URL`, and mode `hns` routes the same
    request to another node's runner. The label is necessary and not
    sufficient."""
    for where in ("http://10.0.0.5:11434", "http://hub.district.example:11434",
                  "https://ollama.example.com/api/chat"):
        exc = _refused(accept, ("an answer", LOCAL), classes=HEALTH, endpoint=where)
        assert isinstance(exc, OffBoxLocalModel), where
        assert exc.state is Refusal.OFF_BOX_LOCAL


def test_an_unreadable_or_missing_endpoint_is_unknown_not_local():
    for where in (None, "", "   ", 7, "http://", "://11434"):
        exc = _refused(accept, ("an answer", LOCAL), classes=HEALTH, endpoint=where)
        assert isinstance(exc, (UnknownProvider, OffBoxLocalModel)), repr(where)
        assert not is_local_address(where if isinstance(where, str) else "")


# --- the call was not tagged ----------------------------------------------


def test_an_untagged_call_is_refused_as_unknown():
    for classes in ([], (), frozenset(), None, "HEALTH"):
        exc = _refused(accept, ("an answer", LOCAL), classes=classes, endpoint=HERE)
        assert isinstance(exc, Unclassified), repr(classes)
        assert exc.state is Refusal.UNCLASSIFIED


def test_a_class_this_build_does_not_recognise_is_refused():
    """Not waved through as 'probably fine'. A name nobody has decided cannot
    be shown to sit outside refusal 1 — `records/classify.py`'s posture, at the
    call rather than at the field."""
    assert isinstance(_refused(accept, ("a", LOCAL), classes=["ROSTER_NOTES"],
                               endpoint=HERE), Unclassified)


def test_the_tagging_is_checked_before_the_call_is_made():
    """A refusal that arrives after the record has been sent to a model is an
    audit note, not a guard."""
    fired = []

    def call():
        fired.append(1)
        return ("an answer", LOCAL)

    _refused(through, call, classes=[], endpoint=HERE)
    assert fired == [], "an untagged call reached the model and was refused after"


def test_a_rung_that_implies_student_data_cannot_be_tagged_as_open():
    """`SENSITIVITY.md` puts all five of refusal 1's classes at `L3` or above,
    so `L4` tagged `PUBLIC` is a contradiction. The fail-open reading of a
    contradiction is the one that serves."""
    for rung in (Rung.L3, Rung.L4, Rung.L5):
        assert isinstance(_refused(accept, ("a", LOCAL), classes=["PUBLIC"],
                                   endpoint=HERE, rung=rung), Unclassified), rung
    accept(("a", LOCAL), classes=["PUBLIC"], endpoint=HERE, rung=Rung.L1)


def test_a_rung_is_a_rung_and_never_a_bare_integer():
    """Rule 14, at the call. `3` here would compare against whichever ladder
    the reader had in mind."""
    assert isinstance(_refused(accept, ("a", LOCAL), classes=HEALTH,
                               endpoint=HERE, rung=3), Unclassified)


def test_covered_reports_the_clause_and_does_not_gate_it():
    assert covered(["HEALTH"]) and covered(["PII_MINOR"]) and covered(["MEDIA_MINOR"])
    assert not covered(["PUBLIC"]) and not covered(["INTERNAL"])
    assert covered(["PUBLIC"], Rung.L4), "the rung route into refusal 1 is missing"
    assert not covered(["PUBLIC"], Rung.L2)


# --- the local model was not there ----------------------------------------


def test_a_stopped_local_model_fails_loudly_and_in_its_own_state():
    def stopped():
        raise ConnectionRefusedError("[Errno 111] Connection refused")

    exc = _refused(through, stopped, classes=HEALTH, endpoint=HERE)
    assert isinstance(exc, LocalModelUnavailable)
    assert exc.state is Refusal.LOCAL_UNAVAILABLE
    assert "ConnectionRefusedError" in exc.detail


def test_the_chain_exhausted_raise_is_the_same_state():
    """Upstream, `chat()` raises `RuntimeError('inference unavailable: …')` when
    every provider fails."""
    def exhausted():
        raise RuntimeError("inference unavailable: ollama:timed out")

    assert isinstance(_refused(through, exhausted, classes=HEALTH, endpoint=HERE),
                      LocalModelUnavailable)


def test_an_empty_answer_is_absence_not_a_result():
    for text in ("", "   ", None, 42):
        assert isinstance(_refused(accept, (text, LOCAL), classes=HEALTH, endpoint=HERE),
                          LocalModelUnavailable), repr(text)


def test_the_two_failures_never_look_alike():
    """Refusal 1's last sentence is made of this distinction: a stopped local
    model and a third party answering are different events, and a guard that
    reported one state for both would lose the half that says *never degrade*."""
    stopped = _refused(through, lambda: (_ for _ in ()).throw(OSError("down")),
                       classes=HEALTH, endpoint=HERE)
    cloud = _refused(accept, ("an answer", "groq"), classes=HEALTH, endpoint=HERE)
    assert stopped.state is not cloud.state
    assert stopped.narration != cloud.narration
    assert type(stopped) is not type(cloud)


def test_a_refusal_is_raised_and_never_returned():
    """Both refuse; neither renders. Nothing here hands back an object a caller
    could read `.text` off — `serve()`'s posture, at the model."""
    for kind in (NonLocalInference, LocalModelUnavailable, UnknownProvider,
                 Unclassified, OffBoxLocalModel):
        assert issubclass(kind, Exception)


# --- the forbidden thing is unrepresentable -------------------------------


def test_the_type_itself_refuses_a_cloud_answer():
    """Not only the sanctioned constructor. `Answer(...)` runs the same vetting,
    so there is no route — public, private or careless — to an answer object
    holding a third party's text."""
    exc = _refused(Answer, text="an answer", provider="gemini",
                   classes=HEALTH, endpoint=HERE)
    assert isinstance(exc, NonLocalInference)
    assert isinstance(_refused(Answer, text="a", provider=LOCAL, classes=[],
                               endpoint=HERE), Unclassified)


def test_there_is_no_parameter_a_caller_could_allowlist_a_provider_with():
    """The `Escalation`-cannot-carry-an-order shape. A `fallback=` here would
    be refusal 1 defeated by keyword, so the signatures are asserted rather
    than reviewed."""
    forbidden = re.compile(
        r"fallback|allow|permit|override|cloud|remote|retry|chain|provider|"
        r"force|skip|bypass|unsafe|escalat", re.I)
    for fn in (accept, through):
        params = inspect.signature(fn).parameters
        assert not any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()), (
            f"{fn.__name__} takes **kwargs; a fallback can arrive through it")
        for name in params:
            assert not forbidden.search(name), f"{fn.__name__}({name}=) is an allowlist"
    fields = {f for f in Answer.__dataclass_fields__}
    assert not any(forbidden.search(f) and f != "provider" for f in fields), fields


def test_a_refusal_cannot_be_retried_into_an_answer():
    """`through` re-raises a refusal rather than trying anything else — there
    is no second provider in this module to try."""
    def already_refused():
        raise NonLocalInference("groq answered")

    assert isinstance(_refused(through, already_refused, classes=HEALTH, endpoint=HERE),
                      NonLocalInference)


def test_a_machine_answer_is_still_a_draft():
    a = accept(("an answer", LOCAL), classes=HEALTH, endpoint=HERE)
    try:
        a.sealed
    except NotImplementedError as exc:
        assert "draft" in str(exc)
        return
    raise AssertionError("the guard reported an answer as sealed")


# --- what a person is allowed to read -------------------------------------


def test_no_refusal_a_person_reads_names_a_provider_or_a_fleet_noun():
    """`CLAUDE.md`, *Working here*: fleet nouns never reach a student, guardian
    or judge. The provider identifier is an operator fact and stays in the
    exception text."""
    nouns = ("ollama", "groq", "gemini", "openrouter", "hns", "willow", "grove",
             "jeles", "kart", "soil", "loam", "frank", "nest", "safe", "sap",
             "nestor", "11434", "http")
    for state, line in NARRATION.items():
        low = line.lower()
        for noun in nouns:
            assert noun not in low, f"{state.value} narration says {noun!r}"
        # Every state except the untagged one is about where the answer came
        # from, and says so in the words a director has: "the local model".
        if state is not Refusal.UNCLASSIFIED:
            assert "local model" in low, f"{state.value} narration is not in plain words"


def test_every_refusal_carries_the_clause_and_the_state():
    exc = _refused(accept, ("a", "groq"), classes=HEALTH, endpoint=HERE)
    assert exc.clause == CLAUSE and "refusal 1" in exc.clause
    assert exc.state.value in str(exc)
    assert "groq" in str(exc), "the operator's sentence has to name the provider"
    assert exc.narration is NARRATION[exc.state]


def test_every_refusal_state_has_a_narration():
    assert set(NARRATION) == set(Refusal)


def test_the_narrations_pass_the_voice_gate():
    """Pair: this module's refusal text and `voice.py`'s ruleset. A refusal is
    a sentence a director reads, so it is subject to the same lint as any other
    — and `false_all_clear` is the rule most likely to catch a badly written
    one, since *"nothing was answered"* is one careless edit from *"all clear"*.
    """
    import voice

    for state, line in NARRATION.items():
        assert not voice.blocking(voice.check(line)), (state.value, voice.check(line))


# --- the two middles ------------------------------------------------------


def test_the_classes_here_are_the_ones_the_ladder_defines():
    """Pair: `docs/SENSITIVITY.md`'s class-to-`L` table and `CLASSES`. Two
    copies of §6's eight names, so this parses the table rather than trusting
    that both were edited."""
    text = (ROOT / "docs" / "SENSITIVITY.md").read_text(encoding="utf-8")
    rows = set(re.findall(r"^\|\s*`([A-Z][A-Z_]+)`\s*\|\s*`L[1-5]`\s*\|", text, re.M))
    assert rows == set(CLASSES), f"drifted: {rows ^ set(CLASSES)}"


def test_the_covered_five_are_the_five_the_refusal_names():
    """Pair: `CLAUDE.md` refusal 1 and `COVERED_CLASSES`. The clause is prose;
    this reads the prose."""
    line = next(l for l in (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
                if l.startswith("1. **No non-local inference"))
    named = set(re.findall(r"`([A-Z][A-Z_]+)`", line))
    assert named == set(COVERED_CLASSES), f"drifted: {named ^ set(COVERED_CLASSES)}"
    assert COVERED_CLASSES < CLASSES


def test_the_local_label_is_the_one_the_router_returns():
    """`_chain("local")` upstream returns `[("ollama", _try_ollama)]`, and that
    string is what `chat()` hands back. If the fleet renames it, this build
    must refuse every answer rather than accept the new name silently."""
    assert LOCAL == "ollama" and LOCAL not in KNOWN_REMOTE
    assert LOOPBACK_HOSTS == frozenset({"localhost", "127.0.0.1", "::1"})


def test_the_module_is_not_broken_shut():
    """A refusal that also refuses the legitimate case gets routed around."""
    for tag in sorted(CLASSES):
        a = accept(("an answer", LOCAL), classes=[tag], endpoint=HERE)
        assert a.text == "an answer"
    assert through(lambda: ("an answer", LOCAL), classes=HEALTH,
                   endpoint=HERE).text == "an answer"


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
