"""The lane crossing W-3 permits, which had no way to exist.

W-3 at source (`willows-grove` `governance/PROTECTED_AGENTS.md` Part III, blob `2886a41`;
re-anchored 2026-09-11 — see `docs/PART-III-READ.md`, which records that the
commit this line used to cite resolves in no repository reachable from here):

> *"Lanes are mutually sealed. Between wards, default deny; **a crossing
> requires a guardian-signed envelope naming both lanes, purpose, and expiry.**
> A shared event is two lane entries with one referent."*

`docs/LANE-MODEL.md` encoded the first sentence and the third. The middle one was
absent from all twelve tables — `envelope` and `crossing` appeared zero times in
the DDL — so the prohibition was enforced and the **permission was
unrepresentable**. A real sibling case could only be served by not recording that
it happened, which is the worse of the two failures.

This was the thirteenth table as a type before it was one in SQL; since
2026-07-31 it is `crossing_envelope` in `migrations/001_lanes.sql`, and the
columns there are the fields below. Four things are required and none has a
default, because each is the one a hurried implementation would omit:

* **both lanes named** — an envelope naming one lane is a wildcard over the other
* **a purpose** — a crossing "because it is convenient" is W-7's territory
* **an expiry** — an envelope without one is a standing grant, which W-5 forbids
* **a guardian's signature** — not a role, not staff, not the system

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from .serving import Edge

_NOT_A_PERSON = frozenset({
    "system", "machine", "agent", "automation", "the guardian", "guardian",
    "staff", "the director", "director", "role:guardian",
})


@dataclass(frozen=True)
class Envelope:
    """A guardian-signed permission for one lane to be read from another."""

    from_lane: str
    to_lane: str
    purpose: str
    signed_by: str
    signed_at: datetime
    expires_at: datetime

    def __post_init__(self):
        if not self.from_lane or not self.to_lane:
            raise ValueError("an envelope must name both lanes (W-3)")
        if self.from_lane == self.to_lane:
            raise ValueError("an envelope naming one lane twice is not a crossing")
        if not (self.purpose or "").strip():
            raise ValueError(
                "an envelope without a purpose is a standing crossing; W-3 requires one"
            )
        name = (self.signed_by or "").strip()
        if not name or name.lower() in _NOT_A_PERSON:
            raise ValueError(
                f"{self.signed_by!r} is not a guardian's signature; a role cannot sign"
            )
        if self.expires_at <= self.signed_at:
            raise ValueError(
                "an envelope without a future expiry is a standing grant (W-5)"
            )

    def live_at(self, when: datetime) -> bool:
        return self.signed_at <= when < self.expires_at


def permits(
    envelopes: Sequence[Envelope],
    *,
    from_lane: str,
    to_lane: str,
    at: datetime,
    subject_id: str,
    signer_edges: Sequence[Edge] = (),
) -> Optional[Envelope]:
    """The live envelope permitting this crossing, or `None`.

    **Direction matters.** An envelope permitting lane A to read lane B does not
    permit B to read A. Treating it as symmetric would mean one signature opened
    two seals, which is the cheap violation W-3 exists to make unwritable.

    **And the signer's standing is checked at the instant of use, not of
    signing.** A guardian whose standing has since ended cannot keep a crossing
    open by having signed it while they still had it — that is refusal 3's whole
    point, applied to the envelope rather than to the edge.

    **`subject_id` is required and used to have a `None` default**, which meant
    the standing check was skipped entirely for any caller who did not pass it.
    That is the hole a court order walks through: an envelope signed in
    September by a guardian whose standing ended in March still opened the seal,
    because nobody had named whose seal it was. `serve()` always passed it, so
    the defect was invisible from the read path and live for every direct
    caller. The parameter is now the missing-parameter form of the same
    discipline `deliver()` uses for recipients: you cannot ask whether a
    crossing is permitted without saying **whose lane is being opened**.
    """
    for env in envelopes:
        if env.from_lane != from_lane or env.to_lane != to_lane:
            continue
        if not env.live_at(at):
            continue
        standing = any(
            e.kind == "guardian_of" and e.principal_id == env.signed_by
            and e.subject_id == subject_id and e.live_at(at)
            for e in signer_edges
        )
        if not standing:
            continue
        return env
    return None
