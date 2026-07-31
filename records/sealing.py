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

**And a fourth, added when I-7 was enforced.** `reject()` and `redraft()` are
where a `lane_entry` is ended and amended in this tree, so they are where I-7's
supersession asymmetry lands: a record the lane's own subject authored cannot be
rejected or rewritten by the office. Before that check existed, a director could
call `reject()` on a student's own account of an incident, reach the **terminal**
state — *"a rejected record cannot be sealed"* — and leave the student's entry
permanently unservable. The predicate is `records/standing.py`'s
`may_supersede()`; this module calls it rather than re-deriving it (§16).

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
    #: Who wrote it — `lane_entry.author_id`, whose comment in the DDL reads
    #: *"author_id carries I-7."* `None` is the ordinary machine draft: a
    #: transcription nobody authored is the office's to reject, and that is the
    #: case `draft()` produces. A governed-authored entry is made by
    #: :func:`authored_by`, which is the only constructor that can set this to
    #: the subject.
    author_id: Optional[str] = None

    @property
    def servable(self) -> bool:
        """Only a sealed record whose body still matches what was sealed."""
        return self.state is State.SEALED and self.over == _digest(self.body)


def _digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def draft(subject_id: str, kind: str, body: str) -> Record:
    """A machine answered. This is not a record yet (§8.2)."""
    return Record(subject_id, kind, body, State.DRAFT)


def authored_by(subject_id: str, author_id: str, kind: str, body: str) -> Record:
    """An entry somebody wrote — the shape I-7 protects when the author is the
    subject.

    *"A student's account of an incident is as durable as a staff member's
    account of the student"* (§7.4, I-7). Which of the two this is depends on
    `author_id`, so it is required here and has no default: a constructor that
    let authorship be omitted would put every governed entry in the `None` case
    that :func:`draft` occupies, and the guard would silently never fire.
    """
    if not (author_id or "").strip():
        raise ValueError(
            "an authored entry names its author; I-7 turns on who wrote it"
        )
    return Record(subject_id, kind, body, State.DRAFT, author_id=author_id)


def _check_person(who: str) -> None:
    name = (who or "").strip()
    if not name:
        raise ValueError("a seal needs a name; an unsigned seal is not a seal")
    if name.lower() in _NOT_A_PERSON:
        raise ValueError(
            f"{who!r} is a role or a machine, not a person. §8.2 requires a named "
            "human, and 'the director' is not a signature"
        )


def _i7(rec: Record, by: str, act: str) -> None:
    """Refuse an office act against an entry the governed authored (I-7).

    The predicate is `records/standing.py`'s, called rather than copied. Only
    the *refusing* half is consulted here — authorship and the acting name are
    the whole input, and no edge can turn the answer around, which is why this
    needs neither an edge list nor an instant.

    `may_supersede` answers `UNKNOWN` for a record with no author, which is
    `draft()`'s ordinary case — a machine transcription nobody signed — and
    that must not block the office's own cascade. So only an explicit refusal
    stops an act here, and the branch says `REFUSED` rather than `not
    permitted`.
    """
    from .standing import Supersession, may_supersede

    check = may_supersede(author_id=rec.author_id, subject_id=rec.subject_id,
                          principal_id=by)
    if check.state is Supersession.REFUSED:
        raise PermissionError(f"{act} refused — {check.reason}")


def seal(rec: Record, *, by: str, at: datetime) -> Record:
    """A named human stands behind the draft.

    **Sealing is not superseding**, so I-7 is not consulted: a seal adds a
    signature and destroys nothing, and the entry's body is unchanged. Stating
    that here because the omission would otherwise read as an oversight.
    """
    _check_person(by)
    if rec.state is State.REJECTED:
        raise ValueError(
            "a rejected record cannot be sealed; re-draft it so the rejection "
            "stays on the record (rule 10)"
        )
    return Record(rec.subject_id, rec.kind, rec.body, State.SEALED,
                  sealed_by=by, sealed_at=at, reason=rec.reason,
                  over=_digest(rec.body), author_id=rec.author_id)


def reject(rec: Record, *, by: str, at: datetime, reason: str) -> Record:
    """A named human refuses it. **As durable as an approval** (rule 10).

    And **not available to the office over the governed's own entry** (I-7).
    Rejection is terminal here — `seal()` refuses a rejected record — so an
    office able to reject a student's account of an incident can make it
    permanently unservable without deleting a row. That is *amending entries
    about its own exercise* by the only spelling this module offers.
    """
    _check_person(by)
    if not (reason or "").strip():
        raise ValueError("a rejection without a reason is not a disposition (I-6)")
    _i7(rec, by, "rejection")
    return Record(rec.subject_id, rec.kind, rec.body, State.REJECTED,
                  sealed_by=by, sealed_at=at, reason=reason,
                  over=_digest(rec.body), author_id=rec.author_id)


def redraft(rec: Record, body: str, *, by: Optional[str] = None) -> Record:
    """Answer again after a rejection. The prior rejection is the caller's to keep.

    Deliberately returns a **new** `Record` rather than mutating: the rejected
    one still exists, and a history that shows only the accepted version is the
    audit trail rule 10 forbids.

    **I-7's other verb.** The clause forbids *deleting or amending*, and
    re-drafting somebody else's words is the amendment. `by` has no default
    that satisfies the check: `None` is not the author of a governed entry, so
    an office rewriting a student's account is refused whether it names itself
    or names nobody. It stays optional because a machine draft has no author to
    contradict.
    """
    _i7(rec, by or "", "re-draft")
    return Record(rec.subject_id, rec.kind, body, State.DRAFT,
                  author_id=rec.author_id)
