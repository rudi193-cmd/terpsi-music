"""The dispatcher `voice.py` was written for and did not have.

PR #4 shipped `voice.guard()` and said so plainly:

> *"The gate is not yet routed through anything, because there is no dispatcher
> in this repo to route it through. `guard()` and `refuses()` are the shape the
> dispatcher must use; until one exists this is enforcement-ready rather than
> enforcing, and calling it otherwise would be the exact thing rule 18
> forbids."*

`records/` is now that dispatcher for the read path. This module is the join:
the serving decision decides *whether a value may leave*, and the voice gate
decides *whether the prose carrying it may leave*. Both must pass.

**The order is not arbitrary.** `serve()` runs first, because a refusal there
means there is no prose to check and running a text filter over a value the
principal was never entitled to would be a disclosure to the filter. The voice
gate runs second, on the rendered sentence, *after the seal and before
dispatch* — the point `voice.py` names.

**Fail-closed is inherited, not re-implemented.** `voice.refuses()` already
treats a raise as a refusal and an unreadable payload as `unknown`; this calls
that rather than re-deriving the posture, because two implementations of
fail-closed is exactly the pair §16 warns about.

Stdlib only.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import voice  # noqa: E402

from .disclosure import Log  # noqa: E402
from .serving import Edge, Field, Outcome, Principal, Serving, serve  # noqa: E402


@dataclass(frozen=True)
class Dispatch:
    """What actually leaves, and everything that decided it."""

    released: bool
    text: Optional[str]
    serving: Serving
    voice_findings: tuple = ()
    reason: str = ""
    log: Optional[Log] = None

    @property
    def blocked_by_voice(self) -> bool:
        return self.serving.outcome in (Outcome.PAYLOAD, Outcome.INSTRUCTION) \
            and not self.released


def dispatch(
    fld: Field,
    principal: Principal,
    edges: Sequence[Edge],
    at: datetime,
    render: Callable[[Serving], str],
    *,
    lane_id: Optional[str] = None,
    envelopes: Sequence = (),
    log: Optional[Log] = None,
    authority: str = "",
) -> Dispatch:
    """Decide, render, gate, record. In that order, and all four every time.

    `render` turns a `Serving` into the sentence a human would read. It is
    supplied by the caller because rendering is a surface concern and §18 item
    4 has not landed — but the gate runs over whatever it produces, so a future
    surface cannot route around this by rendering somewhere else.
    """
    decision = serve(fld, principal, edges, at, lane_id=lane_id, envelopes=envelopes)

    recorded = None
    if log is not None:
        recorded = log.record(decision, principal_id=principal.id,
                              subject_id=fld.subject_id, field_name=fld.name,
                              at=at, authority=authority)

    # Nothing to render, nothing to gate. The refusal is the outcome.
    if decision.outcome in (Outcome.REFUSED, Outcome.UNKNOWN):
        return Dispatch(False, None, decision, (), decision.reason, recorded)

    text = render(decision)

    # The voice gate, after the seal and before dispatch. `serves_value` tells
    # the ruleset this sentence carries a payload rather than an instruction,
    # because the rules that matter differ between the two.
    refused, findings = voice.refuses(
        voice.guard(field="text", serves_value=decision.outcome is Outcome.PAYLOAD),
        {"text": text},
    )
    if refused:
        return Dispatch(False, None, decision, tuple(findings),
                        f"voice gate refused: {'; '.join(findings)[:200]}", recorded)

    return Dispatch(True, text, decision, tuple(findings), decision.reason, recorded)
