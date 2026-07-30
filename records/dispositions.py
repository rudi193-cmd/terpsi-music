"""Every ask gets a dated disposition. Silence is not an answer.

Rule 15 and I-6. A fee waiver, an absence request, a records inspection: each
carries a **timebound declared at issuance**, and if it runs out the request
escalates to the office's basis with **the wait itself recorded**.

Two clauses do the work, and both are the kind that erode quietly:

* **The timebound is declared at issuance or the request is invalid.** `P-2` in
  `Willow`'s Schedule A is explicit that no system-wide default is proposed,
  *"because a default would let issuers stop declaring."* So there is no
  default here either — a request without a timebound cannot be constructed.
* **The office cannot lengthen its own timebound.** I-6's last clause, and the
  single most eroded rule in any queue: the ability to extend one's own
  deadline turns a guarantee into a preference. Extension is possible only by
  a *different* office, and it is recorded.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple


class Disposition(Enum):
    OPEN = "open"            # within its timebound, unanswered
    GRANTED = "granted"
    REFUSED = "refused"
    ESCALATED = "escalated"  # the timebound ran out; silence became an answer


@dataclass(frozen=True)
class Request:
    """An ask, with the clock declared when it was made."""

    subject_id: str
    kind: str            # fee_waiver, absence, records_inspection
    asked_by: str
    asked_at: datetime
    due_by: datetime     # declared at issuance; no default exists
    office: str          # who owes the answer
    escalates_to: str    # the office's basis (I-6)
    disposition: Disposition = Disposition.OPEN
    answered_by: str = ""
    answered_at: Optional[datetime] = None
    reason: str = ""
    #: Every extension: (by_whom, from_when, to_when, why). Append-only.
    extensions: Tuple = ()

    def __post_init__(self):
        if self.due_by <= self.asked_at:
            raise ValueError("a timebound must be in the future of the ask")


def ask(subject_id: str, kind: str, *, asked_by: str, asked_at: datetime,
        within: timedelta, office: str, escalates_to: str) -> Request:
    """Make a request. `within` is required — there is no default timebound.

    P-2: *"the timebound is a required envelope declaration; an envelope issued
    without one is invalid at issuance… no system-wide default is proposed — a
    default would let issuers stop declaring."*
    """
    if within <= timedelta(0):
        raise ValueError("a timebound must be positive")
    if office == escalates_to:
        raise ValueError(
            "an office cannot be its own escalation basis; I-6's escalation would "
            "return the request to the party that did not answer it"
        )
    return Request(subject_id, kind, asked_by, asked_at, asked_at + within,
                   office, escalates_to)


def answer(req: Request, *, granted: bool, by: str, at: datetime, reason: str) -> Request:
    """Answer it. A reason is required either way (rule 10)."""
    if req.disposition is not Disposition.OPEN:
        raise ValueError(f"already disposed: {req.disposition.value}")
    if not (by or "").strip() or not (reason or "").strip():
        raise ValueError("a disposition needs a name and a reason")
    return replace(req,
                   disposition=Disposition.GRANTED if granted else Disposition.REFUSED,
                   answered_by=by, answered_at=at, reason=reason)


def state_at(req: Request, when: datetime) -> Request:
    """The request as of `when`, escalating if its timebound has passed.

    **Silence is not an answer, and it is not a no-op either.** An unanswered
    request past its due date becomes `ESCALATED` with the wait recorded — no
    scheduler, no sweep, evaluated at an instant like every other predicate
    here.
    """
    if req.disposition is not Disposition.OPEN or when < req.due_by:
        return req
    waited = when - req.asked_at
    return replace(req, disposition=Disposition.ESCALATED,
                   answered_by=req.escalates_to, answered_at=req.due_by,
                   reason=f"no disposition within the declared timebound; "
                          f"escalated to {req.escalates_to} after {waited}")


def extend(req: Request, *, by: str, to: datetime, why: str) -> Request:
    """Lengthen the timebound. **The owing office may not do this.**

    I-6: *"the office cannot lengthen its own timebound."* The clause that
    turns a guarantee into a preference the moment it is dropped, so it is
    enforced here rather than noted.
    """
    if by == req.office:
        raise ValueError(
            f"{by!r} owes this answer and cannot extend its own timebound (I-6)"
        )
    if not (why or "").strip():
        raise ValueError("an extension without a reason is not a disposition")
    if to <= req.due_by:
        raise ValueError("an extension must move the timebound later")
    return replace(req, due_by=to,
                   extensions=req.extensions + ((by, req.due_by, to, why),))
