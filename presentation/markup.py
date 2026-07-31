"""One HTML document, in two colour modes. Print is not an export.

`scout-21` §2.1, the first thing that transfers from the best available prior
art: **print is a `ColorMode`, not an export.** The paper artifact renders
through the same provider as the screen, and the empirical argument for it is in
the same repository — `libs/printing/src/render.tsx` carries
`// TODO: Migrate older prints to print theme` over a report ported from another
surface, an unmigrated pair named in a comment with no test failing.

So `surfaces/web` and `surfaces/print` are **one renderer with two arguments**.
They differ in a stylesheet and a mode attribute; the body is byte-identical, and
`tests/test_surfaces.py` asserts that by diffing the two documents. A print path
that could diverge from the screen path would diverge, and the direction it
drifts is always the same: the paper loses a distinction the screen had.

No JavaScript is emitted here and none may be. §4.2's honest caveat is that a
browser-delivered decryptor is served by the thing you do not trust; the smaller
version of the same posture is that a surface with no script has nothing to
swap.

Stdlib only.
"""

from __future__ import annotations

from html import escape
from typing import List

from .ir import Cell, Row, Shown, View

#: Body classes per state, so a stylesheet can style a refusal without the
#: refusal's text changing. The text is fixed (see `ir.REFUSED_TEXT`).
_STATE_CLASS = {
    Shown.SERVED: "served",
    Shown.DERIVED: "derived",
    Shown.REFUSED: "refused",
    Shown.UNKNOWN: "unknown",
}


def _badges(cell: Cell) -> str:
    out = []
    for b in cell.badges:
        out.append(
            f'<span class="badge badge-{escape(b.level.prefix.lower())}" '
            f'data-scale="{escape(b.scale.value)}">{escape(b.text)}</span>'
        )
    return "".join(out)


def _cell(cell: Cell) -> str:
    seal = cell.seal.text if cell.seal else "unknown"
    dated = f'<dd class="dated">{escape(cell.dated.text)}</dd>' if cell.dated else ""
    return (
        f'<div class="cell {_STATE_CLASS[cell.shown]}">'
        f'<dt>{escape(cell.label)}</dt>'
        f'<dd class="value">{escape(cell.value)}</dd>'
        f'<dd class="badges">{_badges(cell)}</dd>'
        f'<dd class="seal">seal {escape(seal)}</dd>'
        f'{dated}'
        f'</div>'
    )


def _row(row: Row) -> str:
    referent = (f'<p class="referent">referent {escape(row.referent)}</p>'
                if row.referent else "")
    cells = "".join(_cell(c) for c in row.cells)
    return (f'<section class="row"><h2>{escape(row.heading)}</h2>{referent}'
            f'<dl>{cells}</dl></section>')


def body(view: View) -> str:
    """The document body. **Identical for screen and paper**, by construction."""
    read = escape(view.read_by or "unknown")
    when = escape(view.at.isoformat() if view.at else "unknown")
    parts: List[str] = [
        f'<h1>{escape(view.title)}</h1>',
        f'<p class="narration">read by {read} at {when}</p>',
    ]
    if view.note:
        parts.append(f'<p class="note">{escape(view.note)}</p>')
    parts.extend(_row(r) for r in view.rows)
    return "".join(parts)


def document(view: View, *, stylesheet: str, mode: str) -> str:
    """A whole page. `mode` is `screen` or `print`, and it is a colour mode."""
    if mode not in ("screen", "print"):
        raise ValueError(f"{mode!r} is not a colour mode; screen or print")
    return (
        "<!doctype html>\n"
        f'<html lang="en" data-color-mode="{escape(mode)}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{escape(view.title)}</title>\n"
        f'<link rel="stylesheet" href="{escape(stylesheet)}">\n'
        "</head>\n"
        f"<body>{body(view)}</body>\n"
        "</html>\n"
    )
