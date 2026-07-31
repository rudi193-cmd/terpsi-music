"""A read and the entry that narrates it commit together, or neither commits.

`docs/PLAN-STORE.md` decision 6: *"The disclosure log is written in the same
transaction as the read it narrates. A read that commits without its narration,
or a narration without its read, must be impossible **at the store** — not
reconciled after."* Reconciled-after is the version everybody builds: a log
writer called next to the reader, a nightly job that notices the gaps. It fails
in exactly the direction that matters, because the disclosure that goes
unrecorded is the one where something else also went wrong.

**How each half is made impossible.**

* *A read without its narration.* `serve_field` is the only public read that
  serves a field. It opens a transaction, reads, calls the caller's predicate,
  writes the entry, and commits. Anything that raises in between — the predicate,
  the insert, a foreign key — rolls the whole transaction back, and the served
  value is never returned to the caller, because it is returned only on the far
  side of the commit.
* *A narration without its read.* `narrate` requires a `Passage`, and a
  `Passage` is minted only by a read, only inside its transaction, carrying that
  transaction's id from `pg_current_xact_id()`. Once the transaction ends the id
  is no longer current, so a passage kept from an earlier call is refused by
  `NarrationWithoutRead`. It is the database's own transaction identity doing
  the work, not a flag this module sets.

**The same-transaction claim is checked against the database, not asserted.**
`Narrated.xid` is the transaction the read ran in, and the row's `xmin` after
commit is the transaction that wrote it. `tests/test_store_narration.py`
compares them. A claim of atomicity that is only a claim reads exactly like one
that is true, which is rule 18's whole distinction.

**The chain is `records/disclosure.py`'s and is not re-implemented.** The digest
comes from `records.disclosure.entry_for`, the same function `Log.record` calls;
this module supplies the `prev` it read from the store and projects the resulting
`Entry` onto the table's columns. The projection is the named middle for a real
pair (§16), and it is lossy in one direction only, stated here rather than
discovered later:

* The **table** has `recipient`, which the `Entry` has no field for. It is
  supplied by the caller and is not part of the digest — so an edit to it is
  detectable by nothing, which is a finding this commit records rather than
  fixes.
* The **type** has `subject_id`, which the table does not store. It is derivable:
  `lane.subject_id` is `UNIQUE`, so a lane names exactly one person. `unproject`
  takes it rather than guessing.

Neither `rung` nor `outcome` has a column of its own, so both are carried inside
`what` with a separator and parsed back out. That is a projection and it
round-trips, which `test_the_projection_round_trips` asserts; a column apiece
would be better and needs a migration, which is named in the report and is not
S-1's.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.disclosure import Entry, entry_for  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Outcome, Serving  # noqa: E402

from .reading import ReadState, Reading, StoreUnavailable, read, unavailable

#: How `what` carries the three facts the table has no columns for. Chosen for
#: legibility in `psql` over compactness — an audit table people cannot read is
#: an audit table nobody checks. Field names are SQL identifiers and rungs and
#: outcomes are single words, so none of them can contain this.
SEPARATOR = " | "

#: The genesis `prev` for a lane nobody has read yet. `records/disclosure.py`'s
#: constant, imported rather than respelled.
from records.disclosure import GENESIS  # noqa: E402


class NarrationWithoutRead(RuntimeError):
    """A disclosure entry offered without the read it claims to narrate.

    Raised when the passage's transaction is no longer the current one — which
    is what *"a narration without its read"* looks like from inside the
    database, whether it happened by a commit in between, a rollback, or a
    passage carried over from an earlier call.
    """


@dataclass(frozen=True)
class Passage:
    """Proof that a read is open in this transaction, right now.

    Minted only by `_open`, only after a read has been issued. Carries the
    transaction id the read ran in; `check` re-asks the database rather than
    trusting the field, so a passage cannot outlive its transaction.
    """

    xid: int
    lane_id: str
    field_name: str

    def check(self, conn) -> None:
        current = _xid(conn)
        if current != self.xid:
            raise NarrationWithoutRead(
                f"this passage was minted in transaction {self.xid} and the "
                f"connection is now in {current}. A disclosure entry belongs in "
                "the transaction of the read it narrates; written here it would "
                "be a record of a read that either never committed or committed "
                "without it (PLAN-STORE decision 6)")


class NarratedState(Enum):
    SERVED = "served"            # the read happened, the entry landed, both committed
    UNAVAILABLE = "unavailable"  # the store did not answer; nothing was narrated


@dataclass(frozen=True)
class Narrated:
    """What `serve_field` returns. Carries the read's state, so it fails closed."""

    state: NarratedState
    serving: Optional[Serving] = None
    entry: Optional[Entry] = None
    xid: Optional[int] = None
    reason: str = ""
    error: Optional[BaseException] = field(default=None, compare=False)

    @property
    def value(self) -> Optional[str]:
        """What was served. Raises when nothing was, rather than answering `None`.

        The same rule as `Reading.rows`: an unavailable store must not be able
        to present as a field with no value.
        """
        if self.state is not NarratedState.SERVED:
            raise StoreUnavailable(
                f"nothing was served: {self.reason}", self.error)
        return self.serving.value if self.serving else None


def _xid(conn) -> int:
    """This transaction's id, assigning one if it has none yet.

    `pg_current_xact_id()` assigns rather than merely reporting, which is what
    makes it usable here: the transaction is going to write a disclosure entry,
    so the assignment costs nothing that was not about to happen anyway.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT pg_current_xact_id()::text")
        return int(cur.fetchone()[0])


# --- the projection (§16's middle, both directions) ------------------------


def project(entry: Entry, *, lane_id: str, recipient: str) -> Dict[str, Any]:
    """An `Entry` as the `disclosure_log` columns.

    `rung` and `outcome` go inside `what` because the table has no column for
    either — see the module docstring. A `None` rung is written `-`, which is
    what `records/disclosure.py`'s own digest material uses, so the two spellings
    of *unclassified* are one spelling.
    """
    rung = str(entry.rung) if entry.rung else "-"
    return {
        "occurred_at": entry.occurred_at,
        "principal_id": entry.principal_id,
        "lane_id": lane_id,
        "what": SEPARATOR.join([entry.field_name, rung, entry.outcome.value]),
        "recipient": recipient,
        "authority": entry.authority,
        "prev_hash": bytes.fromhex(entry.prev),
        "hash": bytes.fromhex(entry.digest),
    }


def unproject(row: Dict[str, Any], *, subject_id: str) -> Entry:
    """The `Entry` a `disclosure_log` row projects from.

    `subject_id` is supplied because the table does not store it — `lane_id`
    determines it (`lane.subject_id` is `UNIQUE`) and this function does not
    hold a connection to look it up. Guessing would be the store answering a
    question about a person from a row that does not name one.
    """
    field_name, rung_text, outcome_text = str(row["what"]).split(SEPARATOR)
    return Entry(
        occurred_at=row["occurred_at"],
        principal_id=str(row["principal_id"]),
        subject_id=subject_id,
        field_name=field_name,
        rung=None if rung_text == "-" else Rung[rung_text],
        outcome=Outcome(outcome_text),
        authority=row["authority"],
        prev=bytes(row["prev_hash"]).hex(),
        digest=bytes(row["hash"]).hex(),
    )


def head_for(conn, lane_id: str) -> Reading:
    """The lane's last disclosure hash, as a `Reading`.

    **Per lane, because `records/disclosure.Ledger` is per lane** and for its
    reason: a guardian holding receipts for global positions 5, 12 and 40 learns
    there were thirty-four entries about other children in between.
    """
    return read(conn,
                "SELECT hash FROM disclosure_log WHERE lane_id = %s "
                "ORDER BY seq DESC LIMIT 1",
                (lane_id,))


# --- the two halves --------------------------------------------------------


def narrate(conn, entry: Entry, *, passage: Passage, lane_id: str,
            recipient: str) -> int:
    """Write one disclosure entry. **Refuses without a live passage.**

    Returns the row's `seq`. Does not commit — the caller's transaction owns
    both halves, which is the whole point.
    """
    passage.check(conn)
    columns = project(entry, lane_id=lane_id, recipient=recipient)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO disclosure_log "
            "(occurred_at, principal_id, lane_id, what, recipient, authority, "
            " prev_hash, hash) "
            "VALUES (%(occurred_at)s, %(principal_id)s, %(lane_id)s, %(what)s, "
            "        %(recipient)s, %(authority)s, %(prev_hash)s, %(hash)s) "
            "RETURNING seq",
            columns)
        return cur.fetchone()[0]


def serve_field(conn, *, query: str, params: Sequence[Any],
                decide: Callable[[Tuple[Any, ...]], Serving],
                principal_id: str, subject_id: str, lane_id: str,
                field_name: str, at: datetime, recipient: str,
                authority: str = "") -> Narrated:
    """Read, decide, narrate, commit — in that order, in one transaction.

    `decide` is the caller's read predicate, which is `records/serving.py`'s and
    is not re-implemented here: this function hands it rows and records what it
    decided. **Every outcome is narrated**, including refusals and unknowns,
    because an audit trail that logs only disclosures cannot answer *"was this
    restriction working"* (rule 10).

    Rolls back on any failure and returns without a value, so a caller cannot
    hold a served field whose narration did not land.
    """
    try:
        passage = Passage(_xid(conn), lane_id, field_name)
        found = read(conn, query, params)
        if found.state is not ReadState.ROWS:
            conn.rollback()
            return Narrated(NarratedState.UNAVAILABLE, reason=found.reason,
                            error=found.error)

        serving = decide(found.rows)

        prev_reading = head_for(conn, lane_id)
        if prev_reading.state is not ReadState.ROWS:
            conn.rollback()
            return Narrated(NarratedState.UNAVAILABLE,
                            reason=f"the lane's chain head could not be read: "
                                   f"{prev_reading.reason}",
                            error=prev_reading.error)
        last = prev_reading.one()
        prev = bytes(last[0]).hex() if last else GENESIS

        entry = entry_for(serving, principal_id=principal_id,
                          subject_id=subject_id, field_name=field_name, at=at,
                          authority=authority, prev=prev)
        narrate(conn, entry, passage=passage, lane_id=lane_id,
                recipient=recipient)
    except Exception as exc:  # noqa: BLE001 — every failure rolls both halves back
        conn.rollback()
        return Narrated(NarratedState.UNAVAILABLE,
                        reason=f"the read was not narrated, so it did not "
                               f"commit: {exc!r}",
                        error=exc)
    conn.commit()
    return Narrated(NarratedState.SERVED, serving, entry, passage.xid,
                    "read and disclosure entry committed together")
