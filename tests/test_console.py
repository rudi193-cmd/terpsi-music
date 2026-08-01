"""The console's own guards, and its rendering — the half that needs no cluster.

`tests/test_store_knock.py` drives the whole vertical against a real PostgreSQL:
the read through row-level security and the predicate, the narration in one
transaction, the exit that lands a `reconciled_session` row. This file is the
part that turns on Python alone, so it runs in the guards job and is where
`tests/ablate.py` points its console mutations (rule 19):

* the knock in enforcement mode — a session opens with a declared purpose or it
  does not open, and a closed session refuses a further read;
* a close that could not reconcile is `UNKNOWN`, never a quiet success (rule 13);
* the view narrates the read and renders with rung and provenance prefixes, and
  monochrome is byte-for-byte the text backend (the parity floor);
* no fleet noun reaches a string the director sees.

No database. The store-touching acts are stubbed or absent; the guards here fire
before the store is reached, which is the point of testing them separately.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.commentary import ExitState, knock  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Outcome, Serving  # noqa: E402

from console.render import exit_line, rendered  # noqa: E402
from console.session import (DirectorSession, ReadWithoutDeclaration,  # noqa: E402
                             SessionClosed, Served, open_session)
from store.narration import Narrated, NarratedState  # noqa: E402

AT = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
PRINCIPAL = "11111111-3333-3333-3333-333333333333"
LANE = "22222222-1111-1111-1111-111111111111"
SUBJECT = "11111111-1111-1111-1111-111111111111"
EVENT = "event-42"

# Fleet nouns that must never reach a string a director sees.
FLEET = ("Willow", "Grove", "Jeles", "Kart", "SOIL", "LOAM", "FRANK", "Nest",
         "SAFE", "SAP", "Nestor")


class _RaisingConn:
    """A connection that fails every read. Stands in for a store that went away."""

    def cursor(self, *a, **k):
        raise RuntimeError("the store is not reachable")

    def rollback(self):
        pass

    def commit(self):
        raise AssertionError(
            "close() committed against a store that could not be read; a "
            "reconciliation that failed must not land a row")


def _served_cell_session():
    """A session with one served read appended, built without a database."""
    guest = knock(PRINCIPAL, purpose="review event 42", event_id=EVENT,
                  lanes=(LANE,), at=AT)
    session = DirectorSession(_RaisingConn(), guest)
    serving = Serving(Outcome.PAYLOAD, "allergy", Rung.L3,
                      "L3 with a live entitlement edge", via_edge="guardian_of",
                      provenance="P2")
    narrated = Narrated(NarratedState.SERVED, serving, None, 7, "committed")
    from console.session import _cell_of
    session._served.append(
        Served(narrated, _cell_of(narrated, label="kind"), LANE, SUBJECT))
    return session


# --- the knock in enforcement mode ----------------------------------------


def test_a_session_cannot_open_without_a_declared_purpose():
    """§7.2 at the door: no declaration, no session, and therefore no read."""
    for blank in ("", "   "):
        try:
            open_session(principal_id=PRINCIPAL, purpose=blank, event_id=EVENT,
                         lanes=(LANE,), at=AT, conn=_RaisingConn())
        except ReadWithoutDeclaration:
            continue
        raise AssertionError(f"a session opened with purpose {blank!r}")


def test_a_declared_session_opens_without_touching_the_store():
    """The knock itself reaches no database — the refusal is at the door, before
    the connection is used, so a session with a purpose is built even against a
    connection that fails every read."""
    session = open_session(principal_id=PRINCIPAL, purpose="review event 42",
                           event_id=EVENT, lanes=(LANE,), at=AT,
                           conn=_RaisingConn())
    assert session.open and session.purpose == "review event 42"


def test_a_closed_session_refuses_a_further_read():
    """A read after close falls outside the reconciled window — a new session's
    read, not this one's. Refused before the store is touched (conn=None)."""
    guest = knock(PRINCIPAL, purpose="review", event_id=EVENT, lanes=(LANE,), at=AT)
    session = DirectorSession(_RaisingConn(), guest)
    session.close(AT)  # reconcile fails against the stub → UNKNOWN, session closed
    assert not session.open
    try:
        session.read(table="lane_entry", column="kind", lane_id=LANE,
                     subject_id=SUBJECT, at=AT, recipient="director_of")
    except SessionClosed:
        return
    raise AssertionError("a closed session served a read")


# --- close reconciles, or says UNKNOWN — never silently fine (rule 13) -----


def test_a_close_that_cannot_reconcile_is_unknown_and_lands_no_row():
    """The store is unreachable at exit. The session closed, so it is not open —
    but whether it did what it declared is *unknown*, not reconciled. The stub
    connection's `commit()` asserts no row was landed."""
    guest = knock(PRINCIPAL, purpose="review", event_id=EVENT, lanes=(LANE,), at=AT)
    session = DirectorSession(_RaisingConn(), guest)
    result = session.close(AT)
    assert result.state is ExitState.UNKNOWN, result
    assert not result.reconciled
    assert "unknown" in exit_line(result).lower() or "still open" in exit_line(result).lower()


def test_close_is_idempotent():
    guest = knock(PRINCIPAL, purpose="review", event_id=EVENT, lanes=(LANE,), at=AT)
    session = DirectorSession(_RaisingConn(), guest)
    first = session.close(AT)
    assert session.close(AT) is first


# --- the view: narrated, prefixed, and monochrome is the floor ------------


def test_the_view_narrates_the_read_and_carries_the_prefixes():
    session = _served_cell_session()
    view = session.compose(title="Lane view", at=AT)
    text = rendered(view, colour=False)
    assert PRINCIPAL in text, "the view does not say who read it (§7.2)"
    assert "[L3 " in text, "the sensitivity rung lost its prefix (rule 14)"
    assert "[P2 " in text, "the provenance rung lost its prefix (rule 14)"
    assert "allergy" in text, "the served value did not render"


def test_monochrome_is_byte_for_byte_the_text_backend():
    """The parity floor: colour adds nothing the text backend lacks."""
    from surfaces.tui.render import Profile, render as tui
    view = _served_cell_session().compose(title="Lane view", at=AT)
    painted = tui(view, Profile.XTERM256)
    ascii_ = tui(view, Profile.ASCII)
    stripped = _strip_sgr(painted)
    assert ascii_ == rendered(view, colour=False)
    assert stripped == rendered(view, colour=False)


def _strip_sgr(text: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_no_fleet_noun_reaches_the_rendered_view():
    session = _served_cell_session()
    text = rendered(session.compose(title="Lane view", at=AT), colour=True)
    line = exit_line(session.close(AT))
    for noun in FLEET:
        assert noun not in text, f"{noun!r} in the rendered view"
        assert noun not in line, f"{noun!r} in the exit line"


def test_the_driver_reconciles_on_exit_even_when_render_fails():
    """§7.2 on the driver shell, the gap both PR reviews caught (rule 19).

    A successful `read` commits `disclosure_log` in its own transaction; if
    rendering then raises, the driver must still call `close()` so the read is
    reconciled. A narrated read with no `reconciled_session` row is the knock
    left half-done. Driven through `console.__main__.main()` — the shell itself,
    not `DirectorSession` in isolation — with a spy session and a rendering that
    raises, so it is the driver's own control flow that is exercised.
    """
    from console import __main__ as driver

    closed = []

    class _DoneConn:
        def close(self):
            pass

    class _SpySession:
        conn = _DoneConn()

        def read(self, **kw):
            pass                        # a read that "committed" — the hazard case

        def compose(self, **kw):
            return object()

        def close(self, at):
            closed.append(at)           # the exit half that must run anyway
            return "reconciled"

    def _render_boom(*a, **kw):
        raise RuntimeError("render failed after the read committed")

    argv = ["--principal", PRINCIPAL, "--purpose", "review event 42",
            "--event", EVENT, "--lane", LANE, "--subject", SUBJECT]
    saved = (driver.open_session, driver.rendered, driver.exit_line)
    try:
        driver.open_session = lambda **kw: _SpySession()
        driver.rendered = _render_boom
        driver.exit_line = lambda r: "exit"
        rc = driver.main(argv)
    finally:
        driver.open_session, driver.rendered, driver.exit_line = saved

    assert closed, (
        "the driver did not reconcile after a render failure: a read committed "
        "disclosure_log but close() was skipped — §7.2's exit half missing on "
        "the failure path")
    assert rc == 2, f"a run that did not complete should report UNKNOWN (2), got {rc}"


# The __main__ runner stays LAST — the harness caught that trap already.
if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"\ntest_console: {sum(1 for n in globals() if n.startswith('test_')) - failures}"
          f"/{sum(1 for n in globals() if n.startswith('test_'))} passed")
    raise SystemExit(1 if failures else 0)
