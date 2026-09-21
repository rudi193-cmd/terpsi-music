"""The same lines as the text backend, with colour added and nothing else.

**The TUI cannot carry information the text backend lacks**, because it does not
build any: it takes `presentation.lines.view_lines` and wraps badge segments in
SGR codes. `strip_colour(render(view)) == text.render(view)` is therefore an
identity, and `tests/test_surfaces.py` asserts it rather than hoping.

`termenv`'s idea, not its code (`scout-21` row 8, Go, MIT): a colour **profile**
that can be forced, so the `TERM=dumb` path is a tested condition rather than a
hope. `Profile.ASCII` here produces exactly the text backend's bytes.

Stdlib only.
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from presentation.ir import View  # noqa: E402
from presentation.lines import Segment, view_lines  # noqa: E402
from presentation.tokens import Palette, load  # noqa: E402

_RESET = "\x1b[0m"


class Profile(Enum):
    """What the terminal can do. Forced in tests, never sniffed from `TERM`."""

    ASCII = "ascii"        # black and white only — the parity condition
    XTERM256 = "xterm256"


def _paint(seg: Segment, palette: Palette, profile: Profile) -> str:
    if profile is Profile.ASCII or seg.token is None:
        return seg.text
    return f"\x1b[38;5;{palette.resolve(seg.token).xterm256}m{seg.text}{_RESET}"


def render(view: View, profile: Profile = Profile.XTERM256,
           palette: Palette = None) -> str:
    """The view, painted. Under `Profile.ASCII` this is the text backend."""
    pal = load() if palette is None else palette
    return "\n".join("".join(_paint(seg, pal, profile) for seg in line)
                     for line in view_lines(view)) + "\n"
