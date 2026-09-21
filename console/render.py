"""The terminal side of the director session: a `View` to bytes, and the exit line.

The session (`console/session.py`) produces a `presentation.View` and an
`ExitReconciliation`; this turns them into what a local terminal shows. It adds
nothing to either — the text is `surfaces/text`'s, the colour is `surfaces/tui`'s,
and the exit narration is `records/commentary.py`'s `ExitReconciliation.narration`,
which is written to be read by the person whose session it was (§7.2, J6).

**Monochrome is the floor, and it is exact.** `surfaces/tui` under `Profile.ASCII`
is byte-for-byte `surfaces/text` — the identity `tests/test_surfaces.py` asserts —
so a director on a `TERM=dumb` terminal or a screen reader loses colour and loses
nothing else. That is why this module renders through the shared IR and never
formats a field itself.

Stdlib and the surfaces. No store, no records — a renderer that could reach a
record would be a second read path, and the second one never has the rules.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.commentary import ExitReconciliation  # noqa: E402
from presentation.ir import View  # noqa: E402
from surfaces.text import render as text_render  # noqa: E402
from surfaces.tui.render import Profile, render as tui_render  # noqa: E402


def rendered(view: View, *, colour: bool = False) -> str:
    """The view as terminal text. `colour=False` is the parity floor.

    Under `colour=False` this is `surfaces/text` exactly; under `colour=True` it
    is `surfaces/tui`'s painted lines, which strip back to the same bytes.
    """
    if not colour:
        return text_render(view)
    return tui_render(view, Profile.XTERM256)


def exit_line(reconciliation: ExitReconciliation) -> str:
    """What the director is shown on the way out — their own reconciliation.

    `ExitReconciliation.narration` names no lane identifier (a lane id is another
    student's key); it says what the session declared and what it did, and whether
    the two matched. An `UNKNOWN` reconciliation says the session is unreconciled
    rather than fine, which is the state a close that could not read the store
    lands in.
    """
    return reconciliation.narration
