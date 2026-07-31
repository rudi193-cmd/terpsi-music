"""Refusal 1, asserted on what actually answered — not on what was configured.

The clause (`CLAUDE.md` refusal 1, §6): *"Anything touching `PII_MINOR`,
`PII_GUARDIAN`, `HEALTH`, `FINANCIAL`, or `MEDIA_MINOR` is served by a local
model. No cloud fallback chain, no `WILLOW_INFERENCE_PROVIDER=auto`. A stopped
Ollama must fail loudly, never degrade to a third party."*

**Why an assertion and not a setting.** The upstream router's `chat()` reads
`os.environ.get("WILLOW_INFERENCE_PROVIDER", "auto")`, and `auto` is *local
first, then the cloud chain*. So the deployment note version of this refusal —
"set the variable" — is satisfied by a box where somebody exported it and
defeated by a box where nobody did. Worse, the failure fires **exactly when the
local model is down**, which is when nobody is watching, and it produces no
error: the caller gets a fluent answer and no signal at all.

The one thing that survives all of that is the return shape. `respond()` and
`chat()` return `(response_text, provider_used)` — *who actually answered*, per
call, after the chain has already run. This module is that pair, checked. The
environment variable stays an off-switch and is never the enforcement, because
an off-switch is a thing somebody has to have flipped and this is a thing the
code cannot get past.

**Four ways this refuses, and none of them is a served answer.**

* `Unclassified` — the call did not say what it touches. Absence is `unknown`
  and `unknown` does not serve (rule 13). There is no untagged path.
* `UnknownProvider` — nothing said who answered, or nothing said where. The
  hazard is concrete rather than theoretical: `core/llm_edge.py`'s `respond()`
  calls the router, **discards the provider label**, returns a bare string, and
  on any exception falls through to Groq and then to Ollama inside two bare
  `except: pass` blocks. A caller who reaches for that function has a fluent
  answer and no way to say what produced it. Here that is a refusal.
* `NonLocalInference` — a third party answered. Refused whatever the tags say.
* `LocalModelUnavailable` — the local model did not answer. **Its own state,
  narrated differently**, because "a stopped local model" and "a cloud model
  answered" are the two halves of refusal 1's last sentence and collapsing them
  loses the distinction the clause is made of.

**The forbidden thing is unrepresentable, not merely refused.** `Answer` runs
the same vetting in `__post_init__`, so there is no constructor — sanctioned or
otherwise — that yields an answer from a provider that is not the local one.
There is no `fallback=`, no `allow=`, no `provider=` override, no retry-with-
another path, and no `**kwargs` for one to arrive through later; the shape is
`records/conflict.py`'s, where an `Escalation` cannot carry an order because
there is no field for one.

**The label alone is not sufficient, and the source says why.** `_try_ollama`
posts to `os.environ.get("OLLAMA_URL", "http://localhost:11434")`, and mode
`hns` routes the same request to *another node's* Ollama over the network. So
`provider_used == "ollama"` can mean a machine that is not this one. The caller
therefore declares the address it called, and an address that is not this host
is refused as `OFF_BOX_LOCAL` — a distinct state, because "a model in the
building" is what the clause protects and "a model with a familiar label" is
not.

**Enforcement or ledger (rule 18), stated exactly.** For anything that routes
through it this is enforcement, and it cannot be routed around, because the
type is the gate. **But nothing in this repository infers yet**, so the set of
call sites it currently governs is empty. That ordering is deliberate: the
guard exists before the path, so a path cannot be born unguarded. What keeps
that true as paths arrive is `tools/providers.py`, which fails a build that
reaches a model without coming through here.

Stdlib only. No network, no keys, no client: this module never builds a
request. It is handed what a call returned, and decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, FrozenSet, Optional, Sequence, Tuple

from .rungs import DERIVE_AT, Rung, at_least

# --- what the clause names -------------------------------------------------

#: The provider label the local runner returns upstream. An internal
#: identifier: it belongs in an exception and a log, never in a sentence a
#: director, guardian or student reads (`CLAUDE.md`, *Working here*).
LOCAL = "ollama"

#: Labels the upstream chain can hand back instead. Not an allowlist and not
#: used to decide anything — `_vet` refuses everything that is not `LOCAL`,
#: including a label nobody has seen before. This exists so a refusal can say
#: *which* third party answered, and so `tests/test_inference.py` can prove the
#: refusal covers the whole documented chain rather than the one example.
KNOWN_REMOTE = frozenset({"gemini", "groq", "openrouter", "fleet", "hns"})

#: §6's eight data classes. `docs/SENSITIVITY.md`'s *class-to-`L` mapping* is
#: canonical; this is a second copy, and the pair's named middle (rule 12) is
#: `test_inference.py::test_the_classes_here_are_the_ones_the_ladder_defines`,
#: which parses that table and fails when the two drift.
CLASSES = frozenset({
    "PUBLIC", "INTERNAL", "DERIVED_ANON",
    "PII_MINOR", "PII_GUARDIAN", "HEALTH", "FINANCIAL", "MEDIA_MINOR",
})

#: The five refusal 1 names verbatim. Their rungs in that same table are `L3`,
#: `L3`, `L4`, `L4`, `L4` — which is why a rung at or above `L3` with none of
#: them declared is a contradiction rather than a quiet pass.
COVERED_CLASSES = frozenset({
    "PII_MINOR", "PII_GUARDIAN", "HEALTH", "FINANCIAL", "MEDIA_MINOR",
})

#: Stamped on every refusal, the way `voice.POLICY_VERSION` is: a refusal is
#: only re-checkable against the clause that was in force when it was made.
CLAUSE = (
    "CLAUDE.md refusal 1 (§6): anything touching PII_MINOR, PII_GUARDIAN, "
    "HEALTH, FINANCIAL or MEDIA_MINOR is served by a local model; no cloud "
    "fallback chain, and a stopped local model fails loudly rather than "
    "degrading to a third party."
)

#: Addresses that are this machine. `0.0.0.0` is deliberately absent: it is
#: every interface, which is a listener's answer to a different question.
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


# --- the refusal states ----------------------------------------------------


class Refusal(Enum):
    """Why an answer did not become an `Answer`. Every one of these refuses."""

    UNCLASSIFIED = "unclassified"        # nobody said what the call touches
    UNKNOWN_PROVIDER = "unknown_provider"  # nobody said who, or where, answered
    NON_LOCAL_PROVIDER = "non_local_provider"  # a third party answered
    OFF_BOX_LOCAL = "off_box_local"      # the local label, at another machine
    LOCAL_UNAVAILABLE = "local_unavailable"  # the local model did not answer


#: What a director, guardian or student may be shown. No provider identifier,
#: no fleet noun, no host: those are operator facts and belong in the exception
#: text and the log. `tests/test_inference.py` asserts this both ways.
NARRATION = {
    Refusal.UNCLASSIFIED: (
        "Refused: the request did not say what kind of record it touches, so "
        "it cannot be shown to be allowed. Unknown is not permission."),
    Refusal.UNKNOWN_PROVIDER: (
        "Refused: nothing recorded which model produced this, so it cannot be "
        "shown to have come from the local model."),
    Refusal.NON_LOCAL_PROVIDER: (
        "Refused: this answer came from a model outside the program's own "
        "equipment. Student records are answered by the local model only."),
    Refusal.OFF_BOX_LOCAL: (
        "Refused: the model that answered was not running on the program's own "
        "equipment. Student records are answered by the local model only."),
    Refusal.LOCAL_UNAVAILABLE: (
        "No answer: the local model did not respond. Nothing was sent anywhere "
        "else, and nothing was answered from anywhere else."),
}


class InferenceRefused(Exception):
    """Base of the four. Carries the clause, the state, and the narration.

    `str(exc)` is the operator's sentence and **may** name a provider or a
    host, because an operator with a refusal and no identifier has to go
    guessing. `narration` is the one a person reads and names neither.
    """

    state: Refusal = Refusal.UNKNOWN_PROVIDER

    def __init__(self, detail: str):
        super().__init__(f"{self.state.value}: {detail} — {CLAUSE}")
        self.clause = CLAUSE
        self.detail = detail

    @property
    def narration(self) -> str:
        return NARRATION[self.state]


class Unclassified(InferenceRefused):
    """The call did not declare what it touches, or declared something unknown."""

    state = Refusal.UNCLASSIFIED


class UnknownProvider(InferenceRefused):
    """Nothing says who answered, or from where. Rule 13: not a pass."""

    state = Refusal.UNKNOWN_PROVIDER


class NonLocalInference(InferenceRefused):
    """A third party answered. The disclosure has already happened; this stops
    it from also being *served*, and says so loudly enough to be noticed."""

    state = Refusal.NON_LOCAL_PROVIDER


class OffBoxLocalModel(InferenceRefused):
    """The local label, at an address that is not this machine."""

    state = Refusal.OFF_BOX_LOCAL


class LocalModelUnavailable(InferenceRefused):
    """The local model did not answer. Distinct on purpose: this is the state
    refusal 1's last sentence is about, and it must never look like the one
    where something else answered instead."""

    state = Refusal.LOCAL_UNAVAILABLE


# --- the address, parsed without importing a network module ----------------


def _host_of(endpoint: str) -> Optional[str]:
    """`"http://localhost:11434"` → `"localhost"`; unreadable → `None`.

    Hand-parsed rather than `urllib.parse.urlparse`, and that is not taste:
    `tools/purity.py` counts any `urllib` import in the inner ring as egress,
    and a guard that made `records/` fail the no-egress check to inspect a
    string would have bought one rule with another.
    """
    if not isinstance(endpoint, str):
        return None
    rest = endpoint.strip()
    if not rest:
        return None
    if "://" in rest:
        rest = rest.split("://", 1)[1]
    rest = rest.split("/", 1)[0].split("?", 1)[0]
    if "@" in rest:                      # user:pass@host
        rest = rest.rsplit("@", 1)[1]
    if rest.startswith("["):             # [::1]:11434
        host, _, _ = rest.partition("]")
        return host[1:].strip().lower() or None
    host = rest.split(":", 1)[0].strip().lower()
    return host or None


def is_local_address(endpoint: str) -> bool:
    """Whether `endpoint` names this machine.

    `127.0.0.0/8` is accepted by prefix; every other host, and anything that
    cannot be read as a host at all, is not local. Unresolvable is not a pass —
    `tools/sockets.py` takes the same line about a bind whose host comes from
    the environment.
    """
    host = _host_of(endpoint)
    if host is None:
        return False
    return host in LOOPBACK_HOSTS or host.startswith("127.")


# --- the classification linkage --------------------------------------------


def _tags(classes: Sequence[str]) -> FrozenSet[str]:
    """Normalise the declared classes, refusing an absent or unknown tag."""
    if isinstance(classes, str) or classes is None:
        raise Unclassified(
            "classes must be a collection of §6 class names, not "
            f"{type(classes).__name__} — one string is a typo away from a "
            "silently empty tag")
    tags = frozenset(str(c).strip().upper() for c in classes if str(c).strip())
    if not tags:
        raise Unclassified(
            "the call declared no data classes; an untagged call is unknown, "
            "and unknown does not serve (rule 13)")
    unknown = tags - CLASSES
    if unknown:
        raise Unclassified(
            f"{sorted(unknown)} are not §6 classes; a class this build does not "
            "recognise cannot be shown to be outside refusal 1")
    return tags


def covered(classes: Sequence[str], rung: Optional[Rung] = None) -> bool:
    """Whether refusal 1 names this call.

    **This does not decide whether the local-only rule applies** — it always
    applies, and there is no branch here that lets a cloud provider serve
    anything. It decides whether the refusal cites refusal 1 by name or cites
    the plainer fact that this build has no non-local inference path at all. A
    function that gated the rule would be the allowlist the clause forbids,
    wearing a predicate's name.
    """
    tags = _tags(classes)
    if tags & COVERED_CLASSES:
        return True
    return rung is not None and at_least(rung, DERIVE_AT)


def _vet(text, provider, classes, endpoint, rung) -> Tuple[str, str, FrozenSet[str], str]:
    """Every clause, in the order a refusal is most usefully learned in."""
    tags = _tags(classes)

    if rung is not None and not isinstance(rung, Rung):
        raise Unclassified(
            f"rung must be a Rung, not {type(rung).__name__} — rule 14, and a "
            "bare integer here would compare against the wrong ladder")

    # The rung and the classes have to agree. `SENSITIVITY.md` puts all five of
    # refusal 1's classes at `L3` or above, so an `L3`+ call tagged only
    # `PUBLIC` is a contradiction, and the fail-open reading of a contradiction
    # is the one that serves.
    if (rung is not None and at_least(rung, DERIVE_AT)
            and not (tags & COVERED_CLASSES)):
        raise Unclassified(
            f"{rung} with classes {sorted(tags)}: the ladder puts every class "
            "refusal 1 names at L3 or above, so this tagging cannot be right")

    if not isinstance(provider, str) or not provider.strip():
        raise UnknownProvider(
            f"no provider label ({provider!r}); the answer cannot be shown to "
            "have come from the local model")

    if provider != LOCAL:
        raise NonLocalInference(
            f"{provider!r} answered"
            + (" (a documented member of the upstream cloud chain)"
               if provider in KNOWN_REMOTE else
               " (a provider this build has never heard of)")
            + f"; only {LOCAL!r} on this host may")

    if not isinstance(endpoint, str) or not endpoint.strip():
        raise UnknownProvider(
            f"no endpoint ({endpoint!r}); the local label is not by itself "
            "evidence of a local model, because OLLAMA_URL can address another "
            "machine and the 'hns' mode routes to one by design")

    if not is_local_address(endpoint):
        raise OffBoxLocalModel(
            f"{provider!r} answered at {endpoint!r}, which is not this host")

    if not isinstance(text, str) or not text.strip():
        raise LocalModelUnavailable(
            "the local model returned nothing; an empty answer is absence, and "
            "absence is not a result (rule 13)")

    return text, provider, tags, endpoint


# --- the only thing that can hold an answer --------------------------------


@dataclass(frozen=True)
class Answer:
    """A machine answer that has been shown to come from the local model.

    Constructing one runs the whole vetting, so this type cannot exist in a
    state refusal 1 forbids — whatever route it was built by. It is still a
    `draft` in §8.2's sense: passing this guard says where the answer came
    from, never that anybody has sealed it.
    """

    text: str
    provider: str
    classes: FrozenSet[str]
    endpoint: str
    rung: Optional[Rung] = None

    def __post_init__(self):
        text, provider, tags, endpoint = _vet(
            self.text, self.provider, self.classes, self.endpoint, self.rung)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "classes", tags)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "endpoint", endpoint)

    @property
    def covered_by_refusal_1(self) -> bool:
        return covered(self.classes, self.rung)

    @property
    def sealed(self) -> bool:
        """There is no seal here, and asking is the error.

        A property rather than an absent attribute, for `conflict.py`'s reason:
        a caller reaching for one gets the clause instead of an
        `AttributeError` they will paper over with `getattr(..., False)`.
        """
        raise NotImplementedError(
            "a machine answer is a draft until a named human seals it "
            "(CLAUDE.md rule 10, §8.2); this guard says which model answered, "
            "not that anyone approved it — use records.sealing.seal()")


# --- the two ways in -------------------------------------------------------


def accept(pair, *, classes: Sequence[str], endpoint: str,
           rung: Optional[Rung] = None) -> Answer:
    """Vet a `(response_text, provider_used)` pair. The whole enforcement.

    `pair` is what the upstream router returns. A bare string — what
    `core/llm_edge.py`'s `respond()` hands back after discarding the label — is
    refused as `UnknownProvider` rather than assumed local.

    There is no `fallback`, no `allow`, no `retry_with`, and no `**kwargs`.
    Every parameter is named here on purpose so that adding one is a visible
    edit to a signature that `tests/test_inference.py` asserts the shape of.
    """
    # Tagging first, so that "an untagged call is refused" holds whatever else
    # is wrong with the pair — otherwise a malformed return would decide which
    # refusal a caller learns about, and the mandatory one would be the loser.
    _tags(classes)
    if isinstance(pair, str) or not isinstance(pair, (tuple, list)) or len(pair) != 2:
        raise UnknownProvider(
            f"expected (response_text, provider_used), got {type(pair).__name__}"
            + (" — llm_edge.respond() drops the provider label and returns the "
               "text alone" if isinstance(pair, str) else ""))
    text, provider = pair[0], pair[1]
    return Answer(text=text, provider=provider, classes=classes,
                  endpoint=endpoint, rung=rung)


def through(call: Callable[[], object], *, classes: Sequence[str], endpoint: str,
            rung: Optional[Rung] = None) -> Answer:
    """Run a caller's inference call and vet what it returns.

    `call` takes no arguments and returns the pair; the caller closes over its
    own prompt, model and client, because this module builds no requests.

    **This is where a stopped local model becomes loud.** Upstream, every
    provider in the chain is tried inside `try/except` and the exception is
    appended to a list; if all of them fail, `chat()` raises `RuntimeError`.
    Here that raise is `LocalModelUnavailable` — its own state, distinct from
    the one where something else answered, and never an empty answer that a
    surface could render as *"no findings"*.
    """
    # The tagging is checked *before* the call, so an untagged call cannot send
    # a student's record to a model and be refused afterwards. A refusal that
    # arrives after the disclosure is an audit note, not a guard.
    _tags(classes)
    try:
        pair = call()
    except InferenceRefused:
        raise
    except Exception as exc:
        raise LocalModelUnavailable(
            f"the inference call raised {type(exc).__name__}: {exc}") from exc
    return accept(pair, classes=classes, endpoint=endpoint, rung=rung)
