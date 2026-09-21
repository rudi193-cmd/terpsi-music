"""The knock's exit, at the store: declared against observed, and the row it lands.

`docs/ARCHITECTURE.md` §7.2 — *"a declared purpose on entry, reconciled on exit."*
`records/commentary.py` already built the reconciliation as a type over the
`reconciled_session` shape (`Declaration`, `GuestSession`, `Observed`,
`ExitReconciliation`), with the observed half a **filter over the disclosure
chain** rather than a second summary. This module is where that filter meets the
store: the chain is `disclosure_log` rather than an in-memory `Ledger`, and the
diff is written to `reconciled_session`.

**It is not a second session model** (rule 12; `commentary.GuestSession<->reconciled_session`
is the named middle). Every type here is `records/commentary.py`'s, imported and
not respelled — `observed()` and `reconcile_exit()` are *its* functions, called
over a `Ledger` this module rebuilds from the store so that a guest whose
reconciliation came from a separate summary could never be shown a different
history from the one the institution keeps (J6). The one thing this module adds
is the rebuild, and the rebuild reads the disclosure log rather than inventing a
record beside it.

**Why a rebuilt `Ledger` and not a fresh count.** `commentary.observed` filters a
`Ledger` by principal and window; re-implementing that filter as a `SELECT … GROUP
BY` here would be a second spelling of the reconciliation rule, which is the pair
§16 forbids. So the store rebuilds the `Ledger` from `disclosure_log` — the same
`unproject` the narration seam round-trips through — and hands it to the function
that already knows how to reconcile it. The store composes rows; it does not
recompute the diff.

**The `reconciled_session` row is history, not a record at rest** (§7.1: *"the
disclosure log, the consent chain, and reconciled sessions are history and must
not"* be superseded). It carries no sealed payload — `store/sealing_plan.py`
derives exactly one sealed column in the whole schema, `lane_entry.payload`, and
this is not it — so landing one does not turn R16's escrow fuse (`tools/audit.py`
`AT_REST_BOUNDARY`, and `store/narration.py`'s narration writes for the same
reason). It is append-only: `reconciled_session_append_only` refuses an `UPDATE`
or `DELETE`, and the app role holds neither.

**An open session does not land a row.** `reconcile_exit` returns `UNKNOWN` for a
session that has not closed (rule 13), and `land()` refuses to write that state:
a `reconciled_session` row is the record of a *finished* session, and a row that
said `unknown` would read afterwards like a session nobody reconciled rather than
one still in progress.

Stdlib, the driver's SQL, and `records/commentary.py`. No model, no network.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from psycopg.types.json import Json

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.commentary import (ExitReconciliation, ExitState,  # noqa: E402
                                GuestSession, observed, reconcile_exit)
from records.disclosure import GENESIS, Log, Ledger  # noqa: E402

from .narration import unproject
from .reading import ReadState, read


class NotClosed(ValueError):
    """A reconciliation that would be landed for a session still open.

    Its own type, because *the session is still in progress* and *the store
    failed* are different reasons not to have a row, and a caller deciding what
    to show the guest needs to tell them apart (rule 13).
    """


class ReconciliationUnavailable(RuntimeError):
    """The store could not be read to reconcile, so there is no observed half.

    Raised rather than reconciling against an empty chain, which would report a
    session that touched every lane as having touched none — absence rendered as
    a clean result, in the one place §7.2 exists to prevent it.
    """

    def __init__(self, reason: str, cause: Optional[BaseException] = None):
        super().__init__(reason)
        self.cause = cause


def _subject_of(conn, lane_id: str) -> str:
    """The lane's subject, for `unproject`. `lane.subject_id` is `UNIQUE`.

    Looked up rather than guessed: `disclosure_log` does not store the subject
    and `commentary.unproject` refuses to invent one. `observed()` does not use
    it, but the `Entry` type requires it, and a placeholder would be a person id
    that is not the person's — the kind of quiet wrong this tree is written
    against.
    """
    got = read(conn, "SELECT subject_id FROM lane WHERE lane_id = %s", (lane_id,))
    if got.state is not ReadState.ROWS:
        raise ReconciliationUnavailable(
            f"the lane for {lane_id} could not be read: {got.reason}", got.error)
    row = got.one()
    if row is None:
        raise ReconciliationUnavailable(
            f"disclosure_log names lane {lane_id} and the lane table does not; "
            "the observed half cannot be built from a chain that points at no lane")
    return str(row[0])


def ledger_from_log(conn, session: GuestSession) -> Ledger:
    """Rebuild the disclosure `Ledger` for this principal from `disclosure_log`.

    Only this principal's entries are read — the RLS `disclosure_log_lane_seal`
    already scopes the read to lanes the acting principal reaches, and the
    `principal_id` filter narrows it to *their* entries there, which is what
    `commentary.observed` filters on. A lane another principal read during the
    same evening is not something this guest touched, and both layers agree.

    The rows come back as `commentary.Entry` objects through the narration seam's
    `unproject`, so the rebuilt chain is the same shape `observed()` filters —
    not a bespoke tuple this module would then have to keep in step with it.
    """
    got = read(
        conn,
        "SELECT seq, occurred_at, principal_id, lane_id, what, recipient, "
        "authority, prev_hash, hash FROM disclosure_log "
        "WHERE principal_id = %s ORDER BY lane_id, seq",
        (session.declared.principal_id,))
    if got.state is not ReadState.ROWS:
        raise ReconciliationUnavailable(
            f"disclosure_log could not be read for the exit reconciliation: "
            f"{got.reason}", got.error)

    by_lane: Dict[str, List] = {}
    subjects: Dict[str, str] = {}
    for (seq, occurred_at, principal_id, lane_id, what, recipient,
         authority, prev_hash, hash_) in got.rows:
        lane = str(lane_id)
        if lane not in subjects:
            subjects[lane] = _subject_of(conn, lane)
        entry = unproject(
            {"occurred_at": occurred_at, "principal_id": principal_id,
             "what": what, "recipient": recipient, "authority": authority,
             "prev_hash": prev_hash, "hash": hash_},
            subject_id=subjects[lane])
        by_lane.setdefault(lane, []).append(entry)
    return Ledger(tuple(sorted(
        (lane, Log(tuple(entries))) for lane, entries in by_lane.items())))


def reconcile(conn, session: GuestSession) -> ExitReconciliation:
    """§7.2's diff, computed over the store's chain. **`commentary`'s, not a copy.**

    Rebuilds the `Ledger` from `disclosure_log` and hands it to
    `commentary.reconcile_exit`, which is the same function the adjudication
    session uses. The declared half is the session's `Declaration`; the observed
    half is this principal's entries in the window; the diff is theirs to
    compute, and this module does not.
    """
    ledger = ledger_from_log(conn, session)
    return reconcile_exit(session, ledger)


# --- the row (§7.2, and §7.1's "history, not state") -----------------------


def _digest(opened_at: datetime, closed_at: Optional[datetime], principal_id: str,
            declared: dict, observed_: dict, diff: dict, prev: str) -> str:
    """One reconciled-session hash, over its predecessor.

    Its own small chain, per principal, so a session's exit record cannot be
    silently removed any more than a disclosure entry can. The material is the
    row's own facts and `prev`; the jsonb is hashed by its sorted, separatored
    text so the digest does not depend on Python's dict ordering.
    """
    def flat(d: dict) -> str:
        return "\x1e".join(f"{k}={d[k]!r}" for k in sorted(d))

    material = "\x1f".join([
        opened_at.isoformat(),
        closed_at.isoformat() if closed_at else "-",
        principal_id, flat(declared), flat(observed_), flat(diff), prev,
    ])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _head(conn, principal_id: str) -> str:
    """This principal's last reconciled-session hash, or `GENESIS`.

    Per principal, because the `reconciled_session` RLS seal is per principal and
    for the same reason the disclosure chain is per lane: a count carried across
    principals leaks how many other sessions ran in between.
    """
    got = read(conn,
               "SELECT hash FROM reconciled_session WHERE principal_id = %s "
               "ORDER BY seq DESC LIMIT 1",
               (principal_id,))
    if got.state is not ReadState.ROWS:
        raise ReconciliationUnavailable(
            f"the reconciled-session chain head could not be read: {got.reason}",
            got.error)
    row = got.one()
    return bytes(row[0]).hex() if row and row[0] is not None else GENESIS


def _declared_json(session: GuestSession) -> dict:
    d = session.declared
    return {"principal_id": d.principal_id, "purpose": d.purpose,
            "event_id": d.event_id, "lanes": list(d.lanes),
            "opened_at": d.opened_at.isoformat()}


def _observed_json(o) -> dict:
    return {"principal_id": o.principal_id, "lanes": list(o.lanes),
            "entries": o.entries}


def _diff_json(r: ExitReconciliation) -> dict:
    return {"state": r.state.value, "undeclared": list(r.undeclared),
            "unvisited": list(r.unvisited), "reason": r.reason}


def land_reconciliation(conn, session: GuestSession,
                        reconciliation: ExitReconciliation, *,
                        at: datetime) -> int:
    """Write one `reconciled_session` row. Returns its `seq`. **Does not commit.**

    The caller owns the transaction, so the read that built the observed half and
    the row that records it share one — the same discipline `store/narration.py`
    holds for a read and its disclosure entry, for the same reason: a diff
    committed against a chain that then changed is a diff about a history that no
    longer exists.

    Refuses an open session (`NotClosed`): a `reconciled_session` row is the
    record of a session that finished, and `reconcile_exit` returns `UNKNOWN`
    until it has. The state written is therefore always `RECONCILED` or
    `DIVERGED`, never `UNKNOWN`.
    """
    if session.open:
        raise NotClosed(
            "a reconciled_session row records a closed session; this one is still "
            "open and reconcile_exit returned its UNKNOWN state (rule 13). Close "
            "the session first — an exit record for a session nobody exited is "
            "the premature pass §7.2 is written against")
    if reconciliation.state is ExitState.UNKNOWN:
        raise NotClosed(
            "the reconciliation is UNKNOWN, which is not a state a finished "
            "session lands in; refusing to write it as though the session had "
            "been reconciled")

    declared = _declared_json(session)
    observed_ = _observed_json(reconciliation.seen)
    diff = _diff_json(reconciliation)
    prev = _head(conn, session.declared.principal_id)
    digest = _digest(session.declared.opened_at, session.closed_at,
                     session.declared.principal_id, declared, observed_, diff, prev)

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO reconciled_session "
            "(opened_at, closed_at, principal_id, declared, observed, diff, "
            " prev_hash, hash) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING seq",
            (session.declared.opened_at, session.closed_at,
             session.declared.principal_id, Json(declared), Json(observed_),
             Json(diff), bytes.fromhex(prev), bytes.fromhex(digest)))
        return cur.fetchone()[0]
