"""One layout, as segments. The medium is the backend's business; this is not.

The TUI and the text backend are the same rendering with and without colour, and
the cheapest way to guarantee that is to make it true by construction: both
consume the segments below, the text backend concatenates them, and the TUI
wraps the badge segments in SGR codes and concatenates them. So

    strip_colour(tui.render(view)) == text.render(view)

is an identity rather than an aspiration, and `tests/test_surfaces.py` asserts
it. A TUI that built its own lines could drift by one field and nothing would
notice until a director could not see a seal state that the export had.

A `Segment` carries a **token name**, never a colour. Naming `caution_3` is not
knowing what `caution_3` looks like — the domain rule ("nothing in the domain
knows about colour") holds one layer further out than it has to, and it costs
nothing.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .ir import Cell, Shown, View

#: Column at which a cell's value starts, so a badge column lines up under a
#: heading on a terminal that cannot draw a table.
_LABEL = 18
_VALUE = 38


@dataclass(frozen=True)
class Segment:
    """A run of text, and the token a backend may paint it with."""

    text: str
    token: Optional[str] = None


def cell_segments(cell: Cell) -> Tuple[Segment, ...]:
    """One field, on one line: label, value, badges, seal, disposition.

    Every part is present or explicitly absent. A cell with no seal renders
    `seal unknown` rather than nothing, because a missing seal state and an
    unsealed record are different facts and the blank version of this line
    cannot tell them apart (rule 13, §15's *human verification is a third
    axis*).
    """
    out: List[Segment] = [Segment("  " + cell.label.ljust(_LABEL - 2))]
    # A trailing space before the pad, so a long value never touches its badge:
    # `auto-injector[L4 Restricted]` reads as one token to a screen reader.
    out.append(Segment((cell.value + " ").ljust(_VALUE - _LABEL)))
    for b in cell.badges:
        out.append(Segment("[" + b.text + "] ", b.token))
    out.append(Segment(" seal " + (cell.seal.text if cell.seal else "unknown")))
    if cell.dated is not None:
        out.append(Segment(" · " + cell.dated.text))
    if cell.shown is Shown.UNKNOWN and cell.why:
        out.append(Segment(" · " + cell.why))
    return tuple(out)


def _rstrip(line: List[Segment]) -> Tuple[Segment, ...]:
    """Trailing whitespace, removed **here** rather than in a backend.

    Not tidiness. `surfaces/tui` paints these segments and `surfaces/text`
    concatenates them, and if either trimmed its own output the two would
    differ by whitespace — or, worse, the TUI would trim through an SGR reset.
    One
    normalisation, in the middle, and the identity holds for free.
    """
    while line and not line[-1].text.strip():
        line.pop()
    if line:
        line[-1] = Segment(line[-1].text.rstrip(), line[-1].token)
    return tuple(line) or (Segment(""),)


def view_lines(view: View) -> Tuple[Tuple[Segment, ...], ...]:
    """The whole view, one tuple of segments per line."""
    lines: List[Tuple[Segment, ...]] = [
        (Segment(view.title),),
        (Segment("=" * len(view.title)),),
    ]
    read = view.read_by or "unknown"
    when = view.at.isoformat() if view.at else "unknown"
    # §7.2, narrate the read. Not a caption: a view that cannot say who is
    # reading it is a view nobody can audit, so it renders `unknown` loudly
    # rather than omitting the line.
    lines.append((Segment(f"read by {read} at {when}"),))
    if view.note:
        lines.append((Segment(view.note),))
    for row in view.rows:
        lines.append((Segment(""),))
        heading = row.heading
        if row.referent:
            heading += f"  (referent {row.referent})"
        lines.append((Segment(heading),))
        for cell in row.cells:
            lines.append(cell_segments(cell))
    return tuple(_rstrip(list(line)) for line in lines)
