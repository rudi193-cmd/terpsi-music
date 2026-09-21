"""A venue profile as a surface shows it, through the presentation IR.

**Why this builds `Cell` directly, when `presentation/ir.py` says not to.** That
module's rule is *"there is no constructor taking a `Field`, and none should be
added: a surface that could read a field directly would be a second read path,
and the second one never has the rules."* The subject of that rule is a person's
field, and the rules it protects are the lane's — consent, guardianship, the
export gate, the narration. A `Reading` is none of those things: run its
descriptor through `records/classify.py` and it lands at `L2` via step 2, *"does
not name or resolve to a person"*. There is no lane to gate and therefore no
second read path to open. Routing a stadium's background level through the read
predicate would not add a rule; it would require inventing a subject for a
number that has none.

So the seam is drawn where it actually is, and the suite holds it there: a row
built here carries no `lane_id` and no `referent`, and this package imports
nothing that decides about a person.

**What it still owes the IR, and does.** Rule 14 in full — every `P`-rung renders
as a badge with its prefix, resolved through `presentation/scales.py`, so the
same information survives greyscale, a printed program and `TERM=dumb`. Nothing
here knows about colour; the module names a rung and the token table says what a
rung looks like. And rule 13 — a quantity nobody measured renders through
`unknown_cell`, which is the same word the rest of the system uses for absence,
rather than a blank or a zero.

The headline rung is the **weakest** reading on the card (§15), because a card is
worth its weakest input and a reader who sees one strong number at the top has
been told the wrong thing about the rest.

Stdlib only.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from presentation.ir import (  # noqa: E402
    Badge, Cell, Row, Shown, View, badge, unknown_cell, view,
)

from .readings import Answer, Profile, Quantity, at, weakest  # noqa: E402


def _cell(answer: Answer) -> Cell:
    """One quantity, or the honest absence of it."""
    if not answer.known:
        return unknown_cell(answer.quantity.label, answer.why)
    r = answer.reading
    why = r.source.strip() or r.note.strip()
    return Cell(label=r.quantity.label, shown=Shown.SERVED, value=r.text,
                badges=(badge(r.provenance),), why=why)


def seat_row(profile: Profile, seat, quantities: Optional[Sequence[Quantity]] = None
             ) -> Row:
    """One listening position, every quantity asked for, measured or not.

    `quantities` defaults to all of them, so a card over a seat with one reading
    shows five `unknown` cells rather than one confident line. That is the
    intended reading: the seat is mostly uncharacterised and the surface says so.
    """
    wanted = tuple(Quantity) if quantities is None else tuple(quantities)
    if not wanted:
        raise ValueError(
            "a card over no quantities renders as a seat with nothing wrong with "
            "it; ask for the quantities you want reported unknown")
    answers = [at(profile, seat, q) for q in wanted]
    return Row(heading=answers[0].seat, cells=tuple(_cell(a) for a in answers))


def profile_card(profile: Profile, seats: Sequence, *,
                 quantities: Optional[Sequence[Quantity]] = None,
                 read_by: str = "", when: Optional[datetime] = None) -> View:
    """What is known about a venue, seat by seat.

    The note carries the card's own rung — the weakest reading on it — or says
    the venue is uncharacterised. **Not a blank in either case**: a card whose
    note is empty is indistinguishable from a card nobody ran, which is the
    absence-as-result failure the note exists to prevent.
    """
    if not seats:
        raise ValueError(
            "a card over no seats has nothing to report and would render as a "
            "venue with no problems (rule 13)")
    rows = [seat_row(profile, s, quantities) for s in seats]
    readings = [r for r in profile.readings
                if r.seat in {row.heading for row in rows}]
    if readings:
        rung = weakest(readings)
        note = (f"This card is {rung} — no stronger than its weakest reading. "
                "Quantities marked unknown were never measured here.")
    else:
        note = ("Nothing has been measured at these seats. An unmeasured venue "
                "is unknown, not quiet.")

    return view(f"{profile.venue} — what these seats hear", rows,
                note=note, read_by=read_by, at=when)


def headline(profile: Profile) -> Optional[Badge]:
    """The rung the whole profile is worth, or `None` where nothing is known.

    `None` rather than a badge, because inventing a rung to have something to
    render is the same error `presentation/ir.py` refuses when a decision carries
    no rung — and here the honest answer has a home already: the caller renders
    `unknown_cell`.
    """
    if not profile.readings:
        return None
    return badge(weakest(profile.readings))
