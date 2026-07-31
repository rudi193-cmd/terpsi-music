"""Who is acting, for the length of one transaction, and nothing longer.

`migrations/003_row_security.sql` compiles the lane seal into row-level security
policies, and every one of them begins by asking `acting_principal()` — a
per-transaction GUC, `terpsi.principal_id`. This module is the only thing that
sets it.

**A connection is not an identity.** The application holds one database role,
`terpsi_app`, for every principal it ever serves; the principal is a property of
the *request*, not of the pool. So the identity is set per transaction and ends
with the transaction — `SET LOCAL`, spelled `set_config(..., is_local => true)`
because `SET LOCAL` takes no bound parameter and a principal id interpolated
into DDL-shaped text is the one place this store would learn to concatenate SQL.

**There is no session-level setter here, and the absence is the design.** A
connection that carries a principal between transactions is a connection whose
identity outlives the request that established it — the pooled-connection defect,
where request *n+1* reads under request *n*'s principal because the reset was in
a `finally` that a raised exception skipped. `SET LOCAL` cannot outlive its
transaction: the reset is the database's, not this module's.

**An unnamed principal is refused here, loudly, rather than sent as blank.** The
policies fail closed on a NULL principal and would refuse the read anyway, so
this refusal buys nothing at the store — it buys the *message*. A caller who
reaches the database with `principal_id=None` gets a `NoPrincipal` naming the
seam, instead of an empty result set that reads exactly like a lane they are not
entitled to (rule 13: absence surfaces as unknown, never as a result).

**What this module does not do.** It does not decide who the principal *is*.
Authenticating a person and mapping them onto a `person_id` is a surface's job
and §18 item 4's; this takes the id it is given. It also does not narrate: the
disclosure entry is `store/narration.py`'s and is written in the same
transaction as the read, which is the transaction this GUC is scoped to.

Stdlib only. The caller supplies the connection.
"""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from typing import Optional

#: The GUC the policies read. A custom parameter with a prefix, which is the
#: only kind PostgreSQL lets an unprivileged role set at all. Written once here
#: and once in `migrations/003_row_security.sql`; that is a pair of literals and
#: `tests/test_store_rowsecurity.py` reconciles them.
GUC = "terpsi.principal_id"


class NoPrincipal(ValueError):
    """A transaction that would act on lane-scoped rows without naming anybody.

    Its own type rather than a bare `ValueError`, because the caller that wants
    to distinguish *"nobody is logged in"* from *"this uuid is malformed"* is
    the surface, and both arrive here as the same refusal today.
    """


def _as_principal(principal_id) -> str:
    """The canonical text of a principal id, or `NoPrincipal`.

    Parsed as a `uuid` rather than passed through, so a malformed id is refused
    at this seam. The policies' own `acting_principal()` swallows an unparseable
    GUC and returns NULL — fail-closed, and silent — so if this function let one
    through, the resulting empty read would be indistinguishable from a genuine
    refusal. One of the two layers has to be loud and it is this one.
    """
    if principal_id is None:
        raise NoPrincipal(
            "no acting principal was named for this transaction. An anonymous "
            f"session reaches no lane-scoped row ({GUC} unset is refused by "
            "every policy in migrations/003_row_security.sql), and a read that "
            "returns nothing for that reason is indistinguishable from a lane "
            "this principal is not entitled to (rule 13)")
    text = str(principal_id).strip()
    if not text:
        raise NoPrincipal(
            "the acting principal is blank. A blank principal is not an "
            "anonymous one and it is not a wildcard; it is a caller that lost "
            "an id somewhere upstream")
    try:
        return str(uuid.UUID(text))
    except (ValueError, AttributeError, TypeError):
        raise NoPrincipal(
            f"{principal_id!r} is not a person id. `person.person_id` is a uuid "
            "and the policies cast the GUC to one; an unparseable principal "
            "reads as NULL there, which is a silent empty result") from None


def name_principal(conn, principal_id) -> str:
    """Name the acting principal for the transaction the connection is in.

    The whole mechanism, in one statement. `acting()` is this plus a reset;
    callers whose transaction *ends* inside their own scope — `serve_field`,
    which commits — take this form, because for them the reset is the commit and
    a context manager would set the GUC again on the way out, opening a fresh
    transaction to do it.

    Returns the canonical principal text so a caller can log what it named.
    """
    text = _as_principal(principal_id)
    with conn.cursor() as cur:
        cur.execute("SELECT set_config(%s, %s, true)", (GUC, text))
    return text


@contextmanager
def acting(conn, principal_id):
    """Name the acting principal for the current transaction.

        with acting(conn, guardian_id):
            rows = read(conn, "SELECT kind FROM lane_entry WHERE lane_id = %s", ...)

    Yields the canonical principal text. **Does not open, commit or roll back a
    transaction** — the caller owns it, for the same reason `store/writing.py`
    does not commit: a read and the disclosure entry that narrates it share one
    transaction (`docs/PLAN-STORE.md` decision 6), and a helper that committed
    on the caller's behalf would split them.

    The GUC is set `LOCAL`, so a `COMMIT` or `ROLLBACK` inside the block clears
    it and the next statement reads no rows. That is not a bug to work around:
    a principal established for one transaction has no standing in the next one,
    and the read that comes back empty is the seam telling the caller so.
    """
    text = name_principal(conn, principal_id)
    try:
        yield text
    finally:
        # Belt and braces. `SET LOCAL` ends with the transaction on its own; this
        # closes the window inside a long transaction that does several things
        # under several principals, where the block's end is the only boundary.
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT set_config(%s, %s, true)", (GUC, ""))
        except Exception:  # noqa: BLE001 — an aborted transaction cannot be reset
            # A transaction that failed inside the block is already aborted and
            # will be rolled back by the caller, which clears the GUC anyway.
            # Swallowing here rather than masking the caller's own exception.
            pass


def principal_of(conn) -> Optional[str]:
    """The principal this transaction is acting as, or `None` for none.

    `None` means the GUC is unset, blank or unparseable — the three cases
    `acting_principal()` in SQL folds together, folded the same way here so the
    two spellings of *no principal* cannot drift. A caller wanting the loud
    version calls `acting()`, which refuses at the seam.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT current_setting(%s, true)", (GUC,))
        raw = cur.fetchone()[0]
    if raw is None or not str(raw).strip():
        return None
    try:
        return str(uuid.UUID(str(raw).strip()))
    except (ValueError, AttributeError, TypeError):
        return None
