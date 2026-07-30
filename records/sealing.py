"""A machine answer is a `draft` until a named human seals it.

§8.2 and rule 10. `Nestor`'s cascade — `sealed` / `draft` / `pending` — verified
at `111c187`; this is that shape for this domain, with the half rule 10 insists
on and cascades usually omit: **rejections are recorded as durably as
approvals.** An audit trail that logs only agreement is not one.

Three properties the type enforces rather than documents:

* **There is no auto-seal path.** `seal()` requires a named person. A role is
  not a name (`"the director"` is not a signature), and a machine cannot seal
  at all — the parameter has no default and no machine identity is accepted.
* **A seal is an act with a date**, and it names what was sealed, so a later
  edit produces a different digest and cannot inherit the old seal.
* **Rejection is a terminal state that keeps its reason**, not a return to
  `draft`. A draft that was rejected and re-drafted must not look like a draft
  that was never reviewed.

Stdlib only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

#: Identities that are not a person. A seal by any of these is refused.
_NOT_A_PERSON = frozenset({
    "system", "machine", "agent", "automation", "bot", "service",
    "the director", "the staff", "director", "staff", "admin", "role:director",
})


class State(Enum):
    PENDING = "pending"    # awaiting a machine answer
    DRAFT = "draft"        # a machine answered; nobody has stood behind it
    SEALED = "sealed"      # a named human stood behind it, on a date
    REJECTED = "rejected"  # a named human refused it, on a date — terminal


@dataclass(frozen=True)
class Record:
    """A transcript, a commentary, an extracted fact — anything a machine drafted."""

    subject_id: str
    kind: str
    body: str
    state: State = State.PENDING
    sealed_by: Optional[str] = None
    sealed_at: Optional[datetime] = None
    reason: str = ""
    #: Digest of the body at the moment it was sealed or rejected. A later edit
    #: changes the body and this no longer matches, so a seal cannot be
    #: inherited by text nobody approved.
    over: Optional[str] = None

    @property
    def servable(self) -> bool:
        """Only a sealed record whose body still matches what was sealed."""
        return self.state is State.SEALED and self.over == _digest(self.body)


def _digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def draft(subject_id: str, kind: str, body: str) -> Record:
    """A machine answered. This is not a record yet (§8.2)."""
    return Record(subject_id, kind, body, State.DRAFT)


def _check_person(who: str) -> None:
    name = (who or "").strip()
    if not name:
        raise ValueError("a seal needs a name; an unsigned seal is not a seal")
    if name.lower() in _NOT_A_PERSON:
        raise ValueError(
            f"{who!r} is a role or a machine, not a person. §8.2 requires a named "
            "human, and 'the director' is not a signature"
        )


def seal(rec: Record, *, by: str, at: datetime) -> Record:
    """A named human stands behind the draft."""
    _check_person(by)
    if rec.state is State.REJECTED:
        raise ValueError(
            "a rejected record cannot be sealed; re-draft it so the rejection "
            "stays on the record (rule 10)"
        )
    return Record(rec.subject_id, rec.kind, rec.body, State.SEALED,
                  sealed_by=by, sealed_at=at, reason=rec.reason, over=_digest(rec.body))


def reject(rec: Record, *, by: str, at: datetime, reason: str) -> Record:
    """A named human refuses it. **As durable as an approval** (rule 10)."""
    _check_person(by)
    if not (reason or "").strip():
        raise ValueError("a rejection without a reason is not a disposition (I-6)")
    return Record(rec.subject_id, rec.kind, rec.body, State.REJECTED,
                  sealed_by=by, sealed_at=at, reason=reason, over=_digest(rec.body))


def redraft(rec: Record, body: str) -> Record:
    """Answer again after a rejection. The prior rejection is the caller's to keep.

    Deliberately returns a **new** `Record` rather than mutating: the rejected
    one still exists, and a history that shows only the accepted version is the
    audit trail rule 10 forbids.
    """
    return Record(rec.subject_id, rec.kind, body, State.DRAFT)
