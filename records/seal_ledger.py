"""A second, independent record of every disposition `records/sealing.py` makes.

§16's diagnosis applied to sealing itself: `records/sealing.py`'s `Record` is a
**pure value type**. `seal()` and `reject()` enforce the rules — a named human,
a reason for a rejection, a digest over the body — but nothing stops a caller
from building `Record(..., state=State.SEALED, sealed_by="Alex Okonkwo",
over=<the right digest>)` directly, skipping every check in the module. The
`.servable` property still reads `True`, because it can only check the shape
that reached it; it has no way to ask whether `seal()` was ever actually
called. That is a declaration with no enforcement behind it — the exact pair
§16 names, missing its middle.

This module is the middle: an append-only, hash-chained log of dispositions,
built the way `records/disclosure.py` already builds one for reads (per-lane,
prev-hash chained, `verify()` that detects an edit or a reorder) — with one
property that log does not need and this one does: **appending refuses rather
than warns when the chain it would extend is already broken**, so a tampered
history can never be laundered by a new entry appended on top of it.

Two things this buys, together:

* **`attested()`** answers a question `Record.servable` structurally cannot:
  not just *"does this row's own fields look internally consistent"* but
  *"does an independent entry exist, in a chain that still verifies, saying
  a named human did this"*. A forged `Record` can get the first answer right
  by construction. It cannot get the second, because forging it does not also
  produce a matching, chain-linked `Entry`.
* **`unverifiable()`** is `records/sealing.py`'s `servable` promoted from a
  per-row property to the collection-level detector `docs/ARCHITECTURE.md`
  §16 describes at ~L1202: *"a row saying `sealed` whose signature does not
  verify comes back `servable=False`, and `unverifiable()` lists precisely
  those rows... That is declaration-versus-enforcement as a computed
  column."* Same shape, ported plain: no import of the fleet component that
  shape is modeled on, no fleet noun in anything a caller sees.

Records **rejections** too, not only seals (rule 10): a rejection is exactly
as durable a disposition as an approval, so it is exactly as worth attesting.

Stdlib only. No network, no store.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Sequence, Tuple

from .sealing import Record, State, _check_person

GENESIS = "0" * 64

#: The only two dispositions a record can have. `PENDING` and `DRAFT` have
#: nothing to attest to yet — there is no event, so there is nothing to chain.
_ATTESTABLE = {State.SEALED: "sealed", State.REJECTED: "rejected"}


class ChainTampered(ValueError):
    """Raised, not warned about. Two places this fires:

    * :meth:`Log.append` — extending a chain whose existing entries do not
      verify would make the tampering look like it happened inside intact
      history. Refused before the new entry is ever built.
    * nowhere else. Reading a broken chain does not raise — :func:`attested`
      and :func:`enforced_servable` fail closed by returning ``False``, which
      is already the refusal a boolean check can give. Raising *there* would
      just move the same refusal to a place a caller is more likely to catch
      and ignore.
    """


@dataclass(frozen=True)
class Entry:
    """One disposition. Immutable; its digest covers its predecessor's."""

    occurred_at: datetime
    subject_id: str
    kind: str
    event: str          # "sealed" | "rejected"
    by: str
    reason: str          # "" for a seal; a rejection's reason, carried verbatim
    body_digest: str     # `Record.over` at the moment of the disposition
    prev: str
    digest: str


def _digest(occurred_at: datetime, subject_id: str, kind: str, event: str,
            by: str, reason: str, body_digest: str, prev: str) -> str:
    # The body itself is deliberately not hashed into this and not carried by
    # the entry — same reasoning as `records/disclosure.py`: a ledger that
    # holds the content it is auditing is a second copy of that content, at
    # the same sensitivity, guarded by whoever remembered the audit trail
    # needs the same care as the record.
    material = "\x1f".join([
        occurred_at.isoformat(), subject_id, kind, event, by, reason,
        body_digest, prev,
    ])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Log:
    """One subject's chain of dispositions. Append-only: every operation
    returns a **new** `Log` — there is no method that rewrites or removes an
    entry, so a silent edit is detectable rather than merely against the
    rules."""

    entries: Tuple[Entry, ...] = ()

    @property
    def head(self) -> str:
        return self.entries[-1].digest if self.entries else GENESIS

    def verify(self) -> Tuple[bool, str]:
        """`(ok, reason)`. Catches an edited entry and a reordered one: each
        digest binds its own fields *and* the predecessor's digest, so
        changing either breaks the chain from that point forward."""
        prev = GENESIS
        for i, e in enumerate(self.entries):
            if e.prev != prev:
                return (False, f"entry {i} does not follow its predecessor")
            expected = _digest(e.occurred_at, e.subject_id, e.kind, e.event,
                               e.by, e.reason, e.body_digest, e.prev)
            if e.digest != expected:
                return (False, f"entry {i} has been altered")
            prev = e.digest
        return (True, f"{len(self.entries)} entries, chain intact")

    def append(self, rec: Record, *, at: Optional[datetime] = None) -> "Log":
        """Attest to a sealed or rejected `Record`.

        Refuses, rather than silently no-ops or warns, in three cases: a
        record with no disposition yet; a disposition attributed to a role or
        a machine (`records/sealing.py`'s `seal()`/`reject()` already refuse
        this — this is the same rule enforced again at the ledger's own
        boundary, for a `Record` built directly and never passed through
        either); and a chain that is already broken.
        """
        event = _ATTESTABLE.get(rec.state)
        if event is None:
            raise ValueError(
                f"a {rec.state.value} record has no disposition to attest; "
                "only a sealed or rejected record belongs in the ledger"
            )
        _check_person(rec.sealed_by or "")
        ok, why = self.verify()
        if not ok:
            raise ChainTampered(f"refusing to extend a broken chain: {why}")
        when = at if at is not None else rec.sealed_at
        if when is None:
            raise ValueError("a disposition needs a date to attest to")
        prev = self.head
        digest = _digest(when, rec.subject_id, rec.kind, event, rec.sealed_by,
                         rec.reason, rec.over or "", prev)
        e = Entry(when, rec.subject_id, rec.kind, event, rec.sealed_by,
                  rec.reason, rec.over or "", prev, digest)
        return Log(self.entries + (e,))


@dataclass(frozen=True)
class Ledger:
    """One chain per subject (W-1) — partitioned from the start.

    `records/disclosure.py` documents building a single global chain first and
    finding two things wrong with it only after `records/receipts.py` needed
    positions to mean something: it is the roster-column shape rule 8
    forbids, and positions in a shared chain leak how many entries *other*
    students have between the ones you can see. Both apply here identically,
    so this one starts per-subject rather than re-discovering the same defect.
    """

    lanes: Tuple[Tuple[str, Log], ...] = ()

    def _index(self) -> Dict[str, Log]:
        return dict(self.lanes)

    def log_for(self, subject_id: str) -> Log:
        """This subject's chain. No entries yet is an empty chain, not an
        error — and not the same object as another subject's."""
        return self._index().get(subject_id, Log())

    def append(self, rec: Record, *, at: Optional[datetime] = None) -> "Ledger":
        by_subject = self._index()
        by_subject[rec.subject_id] = self.log_for(rec.subject_id).append(rec, at=at)
        return Ledger(tuple(sorted(by_subject.items())))

    def verify(self) -> Tuple[bool, str]:
        for subject_id, log in self.lanes:
            ok, why = log.verify()
            if not ok:
                return (False, f"subject {subject_id}: {why}")
        return (True, f"{len(self.lanes)} lane(s), all chains intact")


# --- the detector: declaration vs enforcement -------------------------------


def attested(rec: Record, ledger: Ledger) -> bool:
    """Whether an entry independent of `rec` itself backs its claim to be
    sealed.

    Fail-closed twice: a chain that does not verify attests to nothing it
    contains, regardless of what any individual entry claims (§16's *"the
    ledger refuses rather than warns"*, read from the query side); and a
    `Record` that never passed through `seal()` — however consistent its own
    fields look — has no `Entry` to match, because the entry is only ever
    produced by `Log.append`, which is only ever reached from an already-valid
    disposition.

    A subject with no chain at all (`ledger.log_for` returning an empty `Log`)
    reads as **not attested**, not as unknown. That is a definite fact, not
    a gap in what this function could determine: no entry exists, full stop,
    which is different from *"a backend that should answer this failed to
    load"* (rule 13) — there is no backend here to fail, only a chain that is
    either present and intact, present and broken, or empty.
    """
    if rec.state is not State.SEALED:
        return False
    log = ledger.log_for(rec.subject_id)
    ok, _ = log.verify()
    if not ok:
        return False
    for e in log.entries:
        if (e.event == "sealed" and e.kind == rec.kind
                and e.by == rec.sealed_by and e.body_digest == rec.over):
            return True
    return False


def enforced_servable(rec: Record, ledger: Ledger) -> bool:
    """The question `.servable` alone cannot answer: declared **and** attested.

    `Record.servable` is the record's own claim about itself, computed
    correctly from whatever fields it happens to hold — which is exactly why
    it is not enough on its own. This is `docs/ARCHITECTURE.md` §16's second,
    independent check: *"a stored status and an enforceable one are not the
    same question."*
    """
    return rec.servable and attested(rec, ledger)


def unverifiable(records: Sequence[Record], ledger: Ledger) -> Tuple[Record, ...]:
    """Rows that declare `servable=True` and cannot be proven so.

    The collection-level form of the check above — declaration-versus-
    enforcement as a computed column, applied to a whole set of records
    instead of one at a time. A record built through `draft()` → `seal()` and
    appended to `ledger` never appears here. A `Record` constructed directly
    with `state=State.SEALED` and a correct `over`, but never appended, always
    does — its own `.servable` reads `True` and nothing independent backs it.
    """
    return tuple(r for r in records if r.servable and not enforced_servable(r, ledger))
