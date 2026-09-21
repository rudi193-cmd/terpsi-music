"""What a place sounds like, and what is known about that.

**§9 foundation 6, scoped by reading the thing it points at.** That item names a
fleet app as *"the first real capability"*. The app was read at source before
this package was written, and what it turned out to be decided what this is:

> A **design-time forward simulator** for marching drill. It places anonymous
> performers on a field in feet, gives each an instrument with a radiated power
> spectrum and a bell axis, and sums octave-band energy at a grid of grandstand
> seats — direct sound plus one specular reflection off the far-side stand — to
> answer one counterfactual: *what changes in the audience when the ensemble
> stops facing the front sideline and turns in?* It holds no person data at all;
> a performer is `(instrument, x, y, facing)` and nothing else. It runs on numpy,
> scipy and matplotlib, and it renders through matplotlib colormaps.

Three facts follow, and together they set this package's scope.

**The physics does not come across, and copying it would be the pair §16 is
about.** It needs three numeric dependencies against a stdlib-plus-one budget,
and a numeric model reproduced in a second place is reconcilable only by a
differential suite — which that app already has, holding its own two
implementations to 4.97e-13 dB. A third implementation here would have no
middle, and rule 12 says: name the reconciler or do not create the pair.

**The performer model must not come across, and that is a domain refusal rather
than a budget one.** Over there a performer is an anonymous dot. Here, §9 of the
capability map has *"per-student coordinate lookup; digital dot books"* — a drill
coordinate **is** a named student's position, and a list of them in one object is
the roster column W-1 forbids. The one structure that looks most portable is the
one that would land hardest on the lane model.

**What does come across is the seat, and the honesty about where a number came
from.** §13 leaves open whether the acoustic model and commentary can share
coordinates — *"a judge's remark is anchored to a moment and a seat; the acoustic
model predicts what arrived at that seat"* — and `records/marking.py` already
requires `seat` on every `Mark` for exactly that. So the capability this package
builds is **the venue half of that join**: what is known about a listening
position, each quantity carrying its `P`-rung (§15), composing by the weakest
input, and answering `unknown` where nothing was ever measured.

### This is not a lane entry, and that is a design statement

A venue's acoustic character is a property of a **place**. Run the descriptor
through `records/classify.py` and it lands at `L2 internal` via step 2 — *"does
not name or resolve to a person"* — which is why this is a top-level package and
not a module under `records/`. Nothing here has a lane, a subject, a guardian or
an audit trail over a person, because there is no person in it.

That has to be **proved rather than promised**, so `readings.py` refuses any seat
argument carrying a lane or a subject, and the suite attempts the forbidden act
with a real `Mark` and requires the refusal.

### The capability this deliberately does not build

Per-student hearing exposure. §12 of the capability map wants a dB-and-duration
threshold for hearing conservation, and a figure attached to a **named** student
is a `HEALTH` lane entry — rung derived through `records/classify.py`, W-1
storage, the export gate, the whole apparatus. It is a real capability and it is
not this one. Building it inside a package that has no lane would be exactly the
mistake this docstring exists to refuse; when it is built it belongs in
`records/`, keyed by lane, joined to a venue profile by seat and never by name.

### And the reason this is a re-derivation rather than a port

The simulator floors its energy sums and reports `-300 dB` for an ensemble with
no performers. Inside a forward model that is correct: no sources really is
silence. This package is not a forward model — it is a **record of what is
known** — so absence of a measurement is absence of knowledge, and rule 13
applies without exception: *an unmeasured seat is `unknown`, never quiet.* Same
domain, opposite obligation, which is why the answer had to be rebuilt rather
than imported.

Stdlib only. No audio, no signal processing, no network, no measurement. A
reading arrives as data; who took it and with what is a deployment act.
"""

from __future__ import annotations

from .readings import (
    Answer,
    Profile,
    Quantity,
    Reading,
    at,
    known_seats,
    supersede,
    weakest,
)
from .sourcing import (
    THREE_STATE,
    divergence,
    from_three_state,
    to_three_state,
    unreachable,
)

__all__ = [
    "Answer", "Profile", "Quantity", "Reading", "at", "known_seats",
    "supersede", "weakest",
    "THREE_STATE", "divergence", "from_three_state", "to_three_state",
    "unreachable",
]
