"""ASCII, forced monochrome. The screen-reader path and the parity instrument.

`scout-21` §3, point 5: *"the text backend is not a fourth chore, it is the test
instrument."* And its caveat, which the decision record is required to carry
rather than discover: **a TUI is not accessible because it is text.** There is
no accessibility tree for a terminal, no roles, no ARIA; box-drawing is
announced glyph by glyph. So the screen-reader story for this application lives
here and in the browser surface, never in `surfaces/tui/`.

If a rung is legible here, it is legible everywhere. If it is not, the invariant
is broken and CI says so.
"""

from .render import render  # noqa: F401
