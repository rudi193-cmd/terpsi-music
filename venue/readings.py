"""A listening position, what is known about it, and how well it is known.

The types are small on purpose. Everything hard in this module is a refusal.

**A quantity owns its unit.** `Reading` has no unit field, so a level in dBA and
a level in dB cannot be two readings of the same quantity that happen to
disagree. §16's lesson from `docs/CROSSINGS.md` — *make the violation
inexpressible, not forbidden* — costs one mapping here and removes a whole class
of arithmetic that would otherwise need a check.

**A reading carries its `P`-rung and the rung is not restated here.** The ladder
lives in `records/marking.py` and is imported. A second spelling of `P1–P5` in
this package would be the pair §16 records four failures of, and it would surface
as a badge disagreeing with itself on a printed program.

**Provenance composes by the weakest input.** §15's composition table: sensitivity
by `max`, trust by `min(claimed, ceiling)`, provenance by `min` — *"a result is
worth its weakest input."* A venue profile whose level is instrumented and whose
background is asserted is an assumed profile, and says so.

**An unmeasured seat is `unknown`, never quiet.** There is no default reading, no
zero, no floor. `at()` returns an `Answer` that either holds a reading or holds
nothing and says why, and an `Answer` cannot be built holding both or neither.
This is rule 13, and it is the one place where this package deliberately behaves
*differently* from the forward model it derives from — see the package docstring.

**Nothing here may name a person.** A seat is a plain string. That is not enough
on its own, because a `Mark` has a `seat` and a caller holding one may reach for
the whole object, so `_seat()` refuses anything carrying a lane or a subject
before it refuses anything else. The join between a judge's remark and what
arrived at that seat is made by the **caller**, passing `mark.seat`; it is not
made here, because making it here would put a lane-scoped record and a venue
reading in one object.

Stdlib only.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.marking import (  # noqa: E402
    P_ASSUMED, P_CITED, P_ESTIMATED, P_FITTED, P_MEASURED, outranks,
)

#: The `P`-ladder, every rung taken from the ladder's owner rather than spelled
#: again here. Membership only — ordering is always `records.marking.outranks`,
#: so this tuple's order carries no meaning and cannot become a second one.
_LADDER: Tuple[str, ...] = (P_MEASURED, P_CITED, P_FITTED, P_ESTIMATED, P_ASSUMED)

#: Rungs whose claim does not survive its source going away unless something is
#: stored with it. §15: *"`P2` requires storing enough to survive its source
#: disappearing: not a URL, but a resolved content hash, a pinned commit, or the
#: quoted claim itself."* `P1` is here for the same reason in the other
#: direction — an instrumented reading with no record of the instrument, the day
#: or the operator is an assertion wearing the strongest rung on the ladder.
NEEDS_A_SOURCE: Tuple[str, ...] = (P_MEASURED, P_CITED)

#: Attribute names that mean an object is about a person. Checked before type,
#: because a `Mark` is not a string and the useful error is the domain one.
_PERSON_BEARING: Tuple[str, ...] = (
    "lane_id", "subject_id", "student_id", "subject", "ward", "guardian_id",
)


class Quantity(Enum):
    """What can be characterised at a listening position.

    The six are derived from what the fleet simulator's result object actually
    exposes — level, brightness, mean arrival, arrival spread, reflected-to-direct
    ratio — plus the one a *record* needs and a forward model has no way to
    produce: the background level with nothing playing. That last one is what
    makes "quiet" a measurement rather than an absence, and §9 of the capability
    map already asks for it under *"wind and weather logs"*.

    Each member carries `(label, unit)`. **The unit is on the member and never on
    a reading**, so a level in dBA and a level in dB cannot be two readings of one
    quantity that happen to disagree — the mismatch is not refused, it is
    unsayable.

    The pair is also why the values are pairs rather than bare units: `LEVEL` and
    `BACKGROUND` are both dBA, and an `Enum` whose two members share a value
    silently makes the second an **alias for the first**. That happened here on
    the first run — a background reading overwrote a level reading and the
    duplicate check reported it, correctly, as the same quantity twice.
    """

    LEVEL = ("level", "dBA")                   # A-weighted level at the seat
    BRIGHTNESS = ("brightness", "dB")          # high-band to low-band energy ratio
    ARRIVAL = ("arrival", "ms")                # mean arrival time of the ensemble
    ARRIVAL_SPREAD = ("arrival spread", "ms")  # spread of arrivals; the wash
    REFLECTED_RATIO = ("reflected ratio", "dB")  # reflected relative to direct
    BACKGROUND = ("background", "dBA")         # ambient with nothing playing

    def __init__(self, label: str, unit: str):
        self._label = label
        self._unit = unit

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def label(self) -> str:
        """Plain domain language, for a surface. `"arrival spread"`."""
        return self._label


def _seat(seat) -> str:
    """A listening position, refusing anything that is about a person.

    The order matters. A `records.marking.Mark` carries a `seat` and a
    `subject_id`, and a caller with one in hand may pass the mark where the seat
    was meant. Refusing it *by name* — rather than letting `isinstance` say
    "not a string" — is the difference between an error a reader learns the rule
    from and one they work around by adding `.seat` without asking why.
    """
    for attr in _PERSON_BEARING:
        if hasattr(seat, attr):
            raise ValueError(
                f"a seat is a place, and {type(seat).__name__} carries {attr!r}. "
                "Nothing in this package may name a person; if you are holding a "
                "mark, pass its seat and make the join yourself"
            )
    if not isinstance(seat, str):
        raise TypeError(f"a seat is identified by a string, not {type(seat).__name__}")
    text = seat.strip()
    if not text:
        raise ValueError("a reading with no place is not a reading")
    return text


@dataclass(frozen=True)
class Reading:
    """One quantity, at one seat, with the rung that says how it is known."""

    seat: str
    quantity: Quantity
    value: float
    provenance: str
    source: str = ""        # the citation, the instrument and day, or blank
    note: str = ""

    def __post_init__(self):
        object.__setattr__(self, "seat", _seat(self.seat))
        if not isinstance(self.quantity, Quantity):
            raise ValueError(
                f"{self.quantity!r} is not a quantity this package characterises")
        if self.value is None or isinstance(self.value, bool):
            raise ValueError(
                f"{self.quantity.label} at {self.seat!r} has no value. A reading "
                "with nothing in it renders as absence and reads as a fact "
                "(rule 13); leave it out and let the seat answer unknown")
        if not isinstance(self.value, (int, float)) or not math.isfinite(self.value):
            raise ValueError(
                f"{self.quantity.label} at {self.seat!r} is {self.value!r}, which "
                "is not a finite measurement")
        if self.provenance not in _LADDER:
            raise ValueError(
                f"{self.provenance!r} is not a P-ladder rung (rule 14); rungs are "
                "addressed as P1–P5 and never as bare integers")
        if self.provenance in NEEDS_A_SOURCE and not self.source.strip():
            raise ValueError(
                f"{self.provenance} claims someone can check this and names "
                "nobody. §15: a cited rung has to store enough to survive its "
                "source disappearing — the pinned reference, or the quoted claim")

    @property
    def unit(self) -> str:
        return self.quantity.unit

    @property
    def text(self) -> str:
        """The value with its unit. Never the value alone."""
        return f"{self.value:g} {self.unit}"


@dataclass(frozen=True)
class Profile:
    """What is known about one venue.

    Readings are unique on `(seat, quantity)`. A second reading of the same thing
    is a *supersession* and goes through :func:`supersede`, which is a separate
    named act for the same reason `records/marking.py` separates `realign` from
    `align`: overwriting a claim discards a previous one, and a call site should
    not be able to do that by accident.
    """

    venue: str
    readings: Tuple[Reading, ...] = ()

    def __post_init__(self):
        if not (self.venue or "").strip():
            raise ValueError("a profile is about a named place")
        object.__setattr__(self, "readings", tuple(self.readings))
        seen = set()
        for r in self.readings:
            if not isinstance(r, Reading):
                raise ValueError(f"{r!r} is not a reading")
            key = (r.seat, r.quantity)
            if key in seen:
                raise ValueError(
                    f"{r.quantity.label} at {r.seat!r} is already in this profile. "
                    "A re-measurement supersedes the earlier claim and that is a "
                    "decision — call supersede()")
            seen.add(key)


@dataclass(frozen=True)
class Answer:
    """What this package says about one quantity at one seat.

    Two states and no third. A known answer holds a reading; an unknown answer
    holds nothing and says why. The constructor refuses both other shapes,
    because an answer that is unknown *and* carries a value is the leak, and one
    that is known and carries nothing is absence rendered as a result.
    """

    seat: str
    quantity: Quantity
    reading: Optional[Reading] = None
    why: str = ""

    def __post_init__(self):
        if self.reading is not None and self.why:
            raise ValueError(
                "an answer that both carries a reading and explains its absence "
                "is two answers")
        if self.reading is None and not self.why:
            raise ValueError(
                "an unknown answer must say what is unknown and why; a blank is "
                "indistinguishable from a value nobody looked at (rule 13)")

    @property
    def known(self) -> bool:
        return self.reading is not None

    @property
    def text(self) -> str:
        """What a reader sees. `"unknown"` where nothing is known — never `0`."""
        return self.reading.text if self.reading is not None else UNKNOWN_TEXT


#: The one word for an absent measurement, matching `presentation/ir.py` so the
#: two cannot drift into "unknown" and "unmeasured" meaning the same thing on
#: two surfaces.
UNKNOWN_TEXT = "unknown"


def at(profile: Profile, seat, quantity: Quantity) -> Answer:
    """What this profile says about `quantity` at `seat`.

    **There is no default.** A seat nobody measured, a quantity nobody recorded,
    and a venue with no profile at all each come back unknown with the reason
    attached. The failure this refuses is the one §6 names by example — *an
    eligibility check that could not reach the SIS returning "eligible"* — in its
    acoustic form: a stadium nobody has been to is not a quiet stadium.
    """
    place = _seat(seat)
    if not isinstance(quantity, Quantity):
        raise ValueError(f"{quantity!r} is not a quantity this package characterises")
    for r in profile.readings:
        if r.seat == place and r.quantity is quantity:
            return Answer(place, quantity, r)
    if not any(r.seat == place for r in profile.readings):
        return Answer(place, quantity, None,
                      why=f"{place!r} has never been characterised at "
                          f"{profile.venue}; an unmeasured seat is unknown, "
                          "not quiet")
    return Answer(place, quantity, None,
                  why=f"{place!r} is characterised at {profile.venue} but its "
                      f"{quantity.label} was never recorded")


def known_seats(profile: Profile) -> Tuple[str, ...]:
    """Every seat this profile has anything at all about, in order.

    Enumerable on purpose: *"no findings over zero seats and over nineteen are
    the same sentence and different facts."* A caller that wants to say a venue
    is unprofiled should be able to see that it is.
    """
    return tuple(sorted({r.seat for r in profile.readings}))


def weakest(readings: Sequence[Reading]) -> str:
    """The rung a set of readings is worth — the weakest of them (§15).

    **Composing nothing is refused rather than answered.** An empty set is not
    `P1`, and returning the strongest rung for the emptiest input is how a
    profile nobody has touched comes to render as instrumented. `records/rungs.py`
    refuses the same thing for the same reason on the other ladder.
    """
    rungs = [r.provenance for r in readings]
    if not rungs:
        raise ValueError(
            "the provenance of no readings — an unmeasured venue has no rung, "
            "and the strongest one is the worst possible default (rule 13)")
    worst = rungs[0]
    for rung in rungs[1:]:
        if outranks(worst, rung):    # `worst` is the stronger, so `rung` is worse
            worst = rung
    return worst


def supersede(profile: Profile, reading: Reading) -> Profile:
    """Replace an earlier claim about the same seat and quantity.

    Returns a new profile; the original is unchanged, so a re-measurement that
    turns out to be wrong is discarded rather than reversed. Separate from
    construction because discarding a claim is a decision, not a write.
    """
    if not isinstance(reading, Reading):
        raise ValueError(f"{reading!r} is not a reading")
    kept = tuple(r for r in profile.readings
                 if not (r.seat == reading.seat and r.quantity is reading.quantity))
    return Profile(profile.venue, kept + (reading,))
