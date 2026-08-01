"""The local terminal driver: knock, read a lane-scoped field, render, reconcile.

A thin loop over `console/session.py`, deliberately **not** a framework
(`docs/PLAN-STORE.md` S-4 note 4: the vertical's value is the end-to-end path, not
a rich UI). `scout-21`'s Textual/htmx belong on the far side of `presentation/`'s
IR and are a maintainer decision this commit does not take. This driver opens the
app-role connection, declares a purpose, reads one classified field through the
store, prints it through the text backend, and prints its own exit reconciliation.

**No listener** (decision 8): it reaches out to a local store and accepts nothing.
`store/connecting.py::app_connection` opens the one declared outbound connection.

**No cluster is a loud unknown, never a silent success** (rule 13). A driver that
printed a clean empty view when it could not reach the store would be the exact
shape §7 is written against, so it reports UNKNOWN and exits nonzero.

    python3 -m console --principal <uuid> --purpose "…" --event <id> \\
                       --lane <uuid> --subject <uuid> [--column kind] [--colour]
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from console.render import exit_line, rendered  # noqa: E402
from console.session import open_session  # noqa: E402


def _arg(argv, name: str, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv) -> int:
    principal = _arg(argv, "--principal")
    purpose = _arg(argv, "--purpose")
    event = _arg(argv, "--event")
    lane = _arg(argv, "--lane")
    subject = _arg(argv, "--subject")
    table = _arg(argv, "--table", "lane_entry")
    column = _arg(argv, "--column", "kind")
    recipient = _arg(argv, "--recipient", "director_of")
    colour = "--colour" in argv

    missing = [n for n, v in (("--principal", principal), ("--purpose", purpose),
                              ("--event", event), ("--lane", lane),
                              ("--subject", subject)) if not v]
    if missing:
        print(f"UNKNOWN — the driver needs {', '.join(missing)}; a session with "
              "no declared purpose or principal is not a knock (§7.2)")
        return 2

    at = datetime.now(timezone.utc)
    try:
        session = open_session(principal_id=principal, purpose=purpose,
                               event_id=event, lanes=(lane,), at=at)
    except Exception as exc:  # noqa: BLE001 — a store that is not there is UNKNOWN
        print(f"UNKNOWN — the store could not be opened, which is not an empty "
              f"result (rule 13): {exc!r}")
        return 2

    # A successful `read` commits `disclosure_log` in its own transaction, so the
    # knock's exit half must run on **every** path out of here, not only the happy
    # one: a narrated read with no `reconciled_session` row is §7.2 left half-done.
    # `close` reconciles once (it is idempotent) and is fail-closed (its own
    # UNKNOWN, no row, on a store error), so calling it in `finally` is safe on the
    # happy path, the render-failed path, and the read-failed path alike.
    failed = None
    reconciliation = None
    try:
        session.read(table=table, column=column, lane_id=lane, subject_id=subject,
                     at=at, recipient=recipient)
        print(rendered(session.compose(title="Lane view", at=at), colour=colour))
    except Exception as exc:  # noqa: BLE001 — the run did not finish; still reconcile
        failed = exc
        print(f"UNKNOWN — the session did not complete its read, which is not an "
              f"empty result (rule 13): {exc!r}")
    finally:
        reconciliation = session.close(at)
        print(exit_line(reconciliation))
        try:
            session.conn.close()
        except Exception:  # noqa: BLE001
            pass
    if failed is not None:
        return 2
    return 0 if reconciliation.reconciled else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
