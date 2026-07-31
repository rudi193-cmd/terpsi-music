"""A director's session over the store: knock, read, narrate, reconcile.

**The first surface with real data behind it** (`docs/PLAN-STORE.md` S-4), and the
one place §7.2's knock stops being a ledger and starts enforcing. Everything this
session does exists already; this module is the wire, not a new mechanism:

* the **knock** is `records/commentary.py`'s `Declaration`/`GuestSession` — the
  same reconciled-session model adjudication uses, not a second one;
* the **acting principal** is `store/session.py`'s, set per transaction by
  `serve_field`;
* the **read** goes through `store/narration.py`'s `serve_field`, so it passes
  the cluster's row-level security *and* `records/serving.py`'s predicate, and
  lands its disclosure entry in the same transaction;
* the **render** is `presentation/`'s IR into `surfaces/text` — nothing here
  knows about colour and nothing in the surface knows about students;
* the **exit** is `store/reconcile.py`, which diffs the declared purpose against
  the disclosure chain and lands the `reconciled_session` row.

**The knock, in enforcement mode (rule 18).** A `DirectorSession` cannot read
without a declared purpose — `ReadWithoutDeclaration` refuses it before the store
is touched — and it cannot read after it has closed. On close it *reconciles*, and
a close that could not reconcile returns its own `UNKNOWN` state rather than a
quiet success (rule 13). So a session that read without declaring is refused, and
a session that closed without reconciling is visibly unreconciled — which is the
two halves §7.2's *"may you, and did you do what you said you would"* is made of.

**Read-first, and the escrow fuse stays intact.** This session reads, narrates
and reconciles; it never calls `store/writing.py`'s record-write path
(`insert_draft`, `seal_payloads`). Narration and reconciliation write only the
append-only history tables — `disclosure_log`, `reconciled_session` — which carry
no sealed payload (`store/sealing_plan.py` derives exactly one sealed column,
`lane_entry.payload`, and neither table is it). So R16's at-rest escrow fuse
(`tools/audit.py`) stays `S2`, not `S1`: the write surface that would flip it —
attendance marks, a human sealing a draft — waits on install acceptance and the
escrow rehearsal (§11.1), and is not built here.

**No framework, no listener.** The store is a local connection and this is a
local terminal session (`docs/PLAN-STORE.md` decision 8): `manifest.json` still
declares zero listeners, and the connection is opened through
`store/connecting.py::app_connection` so `tools/sockets.py` sees the one declared
outbound module and not a second `connect()` here.

Stdlib, the store, `records/`, and `presentation/`. No model, no network of its
own.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.commentary import (Declaration, ExitReconciliation,  # noqa: E402
                                ExitState, GuestSession, Observed, close as
                                _close_guest, knock)
from records.marking import P_CITED  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import (Edge, Field, Outcome, Principal, Serving,  # noqa: E402
                             serve)

from presentation.ir import Cell, Row, View, cell, unknown_cell, view  # noqa: E402

from store.classification import classification_of  # noqa: E402
from store.connecting import app_connection  # noqa: E402
from store.narration import Narrated, NarratedState, serve_field  # noqa: E402
from store.reading import read  # noqa: E402
from store.session import name_principal  # noqa: E402
from store.reconcile import (ReconciliationUnavailable, land_reconciliation,  # noqa: E402
                             reconcile)


class ReadWithoutDeclaration(RuntimeError):
    """A read attempted by a session that declared no purpose (§7.2).

    The knock in enforcement mode: *"a session declares what it is for."* A read
    with nothing declared has nothing for the exit to reconcile against, so it is
    refused at the door rather than allowed to run and diff against an empty
    declaration afterwards.
    """


class SessionClosed(RuntimeError):
    """A read attempted after the session closed and was reconciled.

    A closed session's window is fixed; a read after it would fall outside the
    window the reconciliation already diffed, so it is a new session's read and
    not this one's. Refused rather than silently widening a closed window.
    """


@dataclass(frozen=True)
class Served:
    """One narrated read, as the session hands it back: the store result and the cell."""

    narrated: Narrated
    cell: Cell
    lane_id: str
    subject_id: str

    @property
    def outcome(self) -> Optional[Outcome]:
        s = self.narrated.serving
        return s.outcome if s is not None else None


def _edge_source(conn, subject_id: str):
    """A callable yielding this subject's edges as `records.serving.Edge`.

    Passed to `serve()` as its entitlement source, so an errored edge read
    reaches the predicate as `UNKNOWN` rather than as *no edge* — the callable
    shape `store/reading.py` carries and `records/serving.py` consumes. Read as
    the acting principal, inside `serve_field`'s transaction, so the row-level
    security seal applies to the edges too.

    The join maps `edge.target_lane_id` to `lane.subject_id`, which is the same
    adaptation `tests/test_store_differential.py` makes: `Edge.subject_id` is the
    student, and the table stores the lane.
    """
    def source() -> Tuple[Edge, ...]:
        got = read(
            conn,
            "SELECT e.kind, e.holder_id, l.subject_id, e.valid_at, e.invalid_at, "
            "       e.created_at "
            "  FROM edge e JOIN lane l ON l.lane_id = e.target_lane_id "
            " WHERE l.subject_id = %s",
            (subject_id,))
        return tuple(
            Edge(kind, str(holder), str(subject), valid_at, invalid_at,
                 created_at=created_at)
            for kind, holder, subject, valid_at, invalid_at, created_at in got.rows)
    return source


def _cell_of(narrated: Narrated, *, label: str) -> Cell:
    """A `presentation.Cell` from a narrated read. Absence renders as its own state.

    An unavailable read — a killed connection, a query the store refused — is a
    cell that reads `unknown`, never a blank and never a value; a served or
    refused read is `presentation.cell`'s to shape, and it is the one that refuses
    to render a refusal with a value or a served value that is `None`.
    """
    if narrated.state is not NarratedState.SERVED or narrated.serving is None:
        return unknown_cell(label, narrated.reason or "the store did not answer")
    return cell(narrated.serving, label=label)


@dataclass
class DirectorSession:
    """A knock, a run of reads, and a reconciled exit — over one store connection.

    Built by :func:`open_session`, which opens the app-role connection and knocks.
    The connection is the session's; `close()` reconciles, lands the
    `reconciled_session` row, commits, and hands the connection back to be closed.
    """

    conn: object
    guest: GuestSession
    purposes: frozenset = frozenset()
    _served: List[Served] = field(default_factory=list)
    _reconciled: Optional[ExitReconciliation] = None

    # --- the guards the knock enforces ------------------------------------

    @property
    def open(self) -> bool:
        return self.guest.open and self._reconciled is None

    @property
    def purpose(self) -> str:
        return self.guest.declared.purpose

    def _require_open_and_declared(self) -> None:
        if not self.open:
            raise SessionClosed(
                "this session has closed and been reconciled; a read now falls "
                "outside the window §7.2 already diffed, so it is a new session's "
                "read and needs a new knock")
        if not (self.guest.declared.purpose or "").strip():
            raise ReadWithoutDeclaration(
                "this session declared no purpose, so a read has nothing for the "
                "exit to reconcile against (§7.2). The knock is enforced: a "
                "session reads only what it declared it came to do")

    # --- the read (RLS + the predicate, narrated in one transaction) ------

    def read(self, *, table: str, column: str, lane_id: str, subject_id: str,
             at: datetime, recipient: str, category: Optional[str] = None,
             authority: str = "") -> Served:
        """Read one classified field from one lane, decided by `serve`, narrated.

        The rung is the classification registry's for this column
        (`store/classification.py`), never the caller's — a surface cannot serve
        an `L4` field as though it were `L2` by naming a lower rung. The query
        runs as the acting principal, so an unentitled director's read returns no
        row from the cluster (the RLS lane seal); the predicate then refuses it in
        Python too, and both layers are the point.

        **`table` and `column` are composed into the SQL as identifiers, and the
        allowlist closes injection**: `classification_of` refuses any pair the
        registry does not carry *before* the query is built, so only real,
        classified schema identifiers reach the f-string. A surface cannot use the
        driver's `sql.Identifier` — `tools/drivers.py` confines the driver to
        `store/` — so the registry check is the quoting's job here, and it runs
        first.
        """
        self._require_open_and_declared()
        # Raises UnclassifiedColumn for any (table, column) the registry does not
        # carry — the allowlist that makes the composed SQL below safe.
        _, rung_text = classification_of(table, column)
        rung = Rung[rung_text]
        principal_id = self.guest.declared.principal_id

        def decide(rows: Sequence) -> Serving:
            if not rows:
                # RLS returned nothing: an established refusal, not an errored
                # read. The store *answered* — with no row this principal reaches
                # — which is a decision, not an absence rendered as one.
                return Serving(
                    Outcome.REFUSED, None, rung,
                    "the store returned no row this principal reaches; the lane "
                    "seal (migrations/003_row_security.sql) refused the read")
            value = rows[0][0]
            fld = Field(
                lane_id=lane_id, subject_id=subject_id, name=column, rung=rung,
                category=category,
                payload=None if value is None else str(value),
                provenance=P_CITED)
            return serve(fld, Principal(principal_id, self.purposes),
                         _edge_source(self.conn, subject_id), at,
                         lane_id=lane_id, grants=None)

        narrated = serve_field(
            self.conn,
            query=f"SELECT {column} FROM {table} WHERE lane_id = %s",
            params=(lane_id,), decide=decide, principal_id=principal_id,
            subject_id=subject_id, lane_id=lane_id, field_name=column, at=at,
            recipient=recipient, authority=authority)
        served = Served(narrated, _cell_of(narrated, label=column),
                        lane_id, subject_id)
        self._served.append(served)
        return served

    # --- the view (§7.2, narrate the read) --------------------------------

    def compose(self, *, title: str, at: datetime) -> View:
        """The reads so far, as a `presentation.View`. Rendering is the driver's.

        `read_by` is the declared principal and `at` is the moment: a view that
        cannot say who read it is one nobody can audit, so the IR carries both
        and `surfaces/text` renders them on their own line (§7.2, narrate the
        read).
        """
        rows: List[Row] = []
        for s in self._served:
            heading = f"lane {s.lane_id}"
            rows.append(Row(heading=heading, cells=(s.cell,),
                            referent=s.subject_id, lane_id=s.lane_id))
        return view(title, rows, read_by=self.guest.declared.principal_id, at=at)

    # --- the exit (declared vs observed vs diff) --------------------------

    def close(self, at: datetime) -> ExitReconciliation:
        """Close, reconcile against the disclosure chain, and land the row.

        Returns the `ExitReconciliation` — `RECONCILED` or `DIVERGED` on success.
        **A close that could not reconcile returns its own `UNKNOWN` state and
        lands no row** (rule 13): the store failed, which is not the same fact as
        a session that matched what it declared, and a `reconciled_session` row
        saying otherwise would be the premature pass §7.2 exists to prevent.
        """
        if self._reconciled is not None:
            return self._reconciled
        closed = _close_guest(self.guest, at)
        self.guest = closed
        try:
            # The exit reads the disclosure chain and the reconciled-session head,
            # both of which are row-security-sealed to the acting principal. The
            # last read's `SET LOCAL` ended at its commit, so name the principal
            # again for this transaction — the same principal the reconciliation
            # is about, so it sees exactly its own entries and its own chain head.
            name_principal(self.conn, closed.declared.principal_id)
            result = reconcile(self.conn, closed)
            land_reconciliation(self.conn, closed, result, at=at)
            self.conn.commit()
        except (ReconciliationUnavailable, Exception) as exc:  # noqa: BLE001
            self.conn.rollback()
            result = ExitReconciliation(
                ExitState.UNKNOWN, closed.declared,
                Observed(closed.declared.principal_id, (), 0), (), (),
                f"the session closed but the store could not be reconciled, so "
                f"whether it did what it declared is unknown, not fine: {exc!r}")
        self._reconciled = result
        return result


def open_session(*, principal_id: str, purpose: str, event_id: str,
                 lanes: Sequence[str] = (), at: datetime,
                 purposes: Sequence[str] = (),
                 conn=None) -> DirectorSession:
    """Open a director session: connect as the app role, then knock (§7.2).

    `conn` is injectable so a test can hand in a connection on a throwaway
    database; a deployment leaves it `None` and gets `store/connecting.py`'s
    app-role connection, which holds `INSERT` and `SELECT` and nothing else.

    `purposes` are the categories this declared purpose covers, consulted by
    `serve()` at `L4`. They are kept distinct from the declared `purpose` string
    on purpose: the string is what the exit reconciles against, and the set is
    what a read at `L4` is checked against — two different questions §7.2 keeps
    apart.

    **A session cannot open without a declared purpose** (`ReadWithoutDeclaration`),
    which is the knock in enforcement mode: a session that never declared has
    nothing for the exit to reconcile against, so it is refused at the door and
    never reaches a read. The refusal is named here as well as in the knock so a
    caller sees the console's enforcement rather than a bare `ValueError` from the
    session model.
    """
    if not (purpose or "").strip():
        raise ReadWithoutDeclaration(
            "a session opens with a declared purpose or it does not open: §7.2's "
            "knock declares intent on entry, and a session with nothing declared "
            "cannot read, because there would be nothing for the exit to "
            "reconcile against")
    guest = knock(principal_id, purpose=purpose, event_id=event_id,
                  lanes=tuple(lanes), at=at)
    connection = conn if conn is not None else app_connection()
    return DirectorSession(connection, guest, frozenset(purposes))
