"""The presentation IR — a structured description of what a surface shows.

`scout-21` §3: *"a domain view returns a structured description — rows, fields,
rung badges with their prefixes, seal state, disposition dates — and the four
backends are thin renderers over it."* This is that description.

**It is built from a decision, never from a record.** `cell()` takes a
`records.serving.Serving`, so the only way a payload reaches a surface is for the
read predicate to have decided to hand it over. There is no constructor taking a
`Field`, and none should be added: a surface that could read a field directly
would be a second read path, and the second one never has the rules.

**Four things it refuses, and each is a way absence becomes a result.**

* A served cell whose value is `None` — rendering "nothing" as though it were
  the fact. Rule 13.
* A refused or unknown cell carrying a value — the leak that would make §7's
  indistinguishability guarantee decorative.
* A rung the mapping table does not know — a badge with no prefix to render.
* A cell with no state at all.

**What it deliberately does not do.** It does not re-derive `voice.py`'s
`no_provenance` refusal for a served value carrying no `P`-rung. That rule has
an owner and a gate (`records/dispatch.py`); a second implementation here would
be exactly the pair §16 warns about, and the two would disagree within a month.
The IR carries what it was handed and says what it is.

Nothing here knows about colour. A cell names a rung; `presentation/scales.py`
says what the badge reads; `presentation/tokens.yaml` says what it looks like.

Stdlib only.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.dispositions import Disposition, Request  # noqa: E402
from records.sealing import Record, State  # noqa: E402
from records.serving import Outcome, Serving  # noqa: E402

from .scales import Level, Scale, level  # noqa: E402


class Shown(Enum):
    """What happened to this cell, from the reader's side.

    Four states rather than three: a refusal and an unknown look the same to a
    principal and must not look the same to an auditor, and collapsing them is
    how *"we could not decide"* comes to read as *"there is nothing there."*
    """

    SERVED = "served"            # the fact itself
    DERIVED = "derived"          # the instruction; the fact never left
    REFUSED = "refused"          # enforced, and correctly uninformative
    UNKNOWN = "unknown"          # nothing here could decide (rule 13)


#: What a reader sees where a value is not being shown. Fixed strings, because
#: a refusal that varies with what was refused is a side channel.
REFUSED_TEXT = "not served"
UNKNOWN_TEXT = "unknown"

_FROM_OUTCOME = {
    Outcome.PAYLOAD: Shown.SERVED,
    Outcome.INSTRUCTION: Shown.DERIVED,
    Outcome.REFUSED: Shown.REFUSED,
    Outcome.UNKNOWN: Shown.UNKNOWN,
}


@dataclass(frozen=True)
class Badge:
    """A rung, as a surface shows it. Always a prefix, on every backend."""

    level: Level

    @property
    def text(self) -> str:
        return self.level.text

    @property
    def scale(self) -> Scale:
        return self.level.scale

    @property
    def token(self) -> str:
        return self.level.token


@dataclass(frozen=True)
class Seal:
    """A state, and the name and date that make it evidence.

    §15: *"the seal state says whether a person has stood behind it"* and
    `verifier` says **which** human, and when. A surface that renders `sealed`
    without the name has dropped the half that makes it evidence.
    """

    state: State
    by: Optional[str] = None
    at: Optional[datetime] = None

    @property
    def text(self) -> str:
        if self.state is State.SEALED and self.by:
            when = f" {self.at.date().isoformat()}" if self.at else ""
            return f"sealed by {self.by}{when}"
        if self.state is State.REJECTED and self.by:
            when = f" {self.at.date().isoformat()}" if self.at else ""
            return f"rejected by {self.by}{when}"
        return self.state.value


@dataclass(frozen=True)
class Dated:
    """A dated disposition (rule 15). The date is not optional on any of them.

    `OPEN` renders its due date because *"silence is not an answer"* only means
    something if the reader can see the clock. `ESCALATED` renders the date the
    clock ran out.
    """

    disposition: Disposition
    due_by: datetime
    decided_at: Optional[datetime] = None

    @property
    def text(self) -> str:
        if self.disposition is Disposition.OPEN:
            return f"open, due {self.due_by.date().isoformat()}"
        when = (self.decided_at or self.due_by).date().isoformat()
        return f"{self.disposition.value} {when}"


@dataclass(frozen=True)
class Cell:
    """One field, one decision, and everything a reader needs to weigh it."""

    label: str
    shown: Shown
    value: str
    badges: Tuple[Badge, ...] = ()
    seal: Optional[Seal] = None
    dated: Optional[Dated] = None
    why: str = ""                # the predicate's reason; narrated, never guessed

    def __post_init__(self):
        if not isinstance(self.shown, Shown):
            raise ValueError(f"{self.label!r}: a cell with no state")
        if self.shown in (Shown.SERVED, Shown.DERIVED) and not self.value:
            raise ValueError(
                f"{self.label!r}: shown as {self.shown.value} with nothing to show. "
                "An empty served value renders as absence and reads as a fact")
        if self.shown is Shown.REFUSED and self.value != REFUSED_TEXT:
            raise ValueError(
                f"{self.label!r}: a refusal that says more than {REFUSED_TEXT!r} "
                "distinguishes itself from other refusals, which is the side "
                "channel §7's indistinguishability guarantee closes")
        if self.shown is Shown.UNKNOWN and self.value != UNKNOWN_TEXT:
            raise ValueError(
                f"{self.label!r}: absence renders as {UNKNOWN_TEXT!r} and as "
                "nothing else (rule 13)")


@dataclass(frozen=True)
class Row:
    """One referent — a student's lane entry, a schedule line, a mark.

    **One row is one lane.** W-1/W-3: a shared event is two lane entries with
    one referent, so two students are two rows carrying the same `referent`, and
    there is no participant list on a row to become a roster column.
    """

    heading: str
    cells: Tuple[Cell, ...]
    referent: str = ""
    lane_id: str = ""


@dataclass(frozen=True)
class View:
    """What one surface shows one principal at one moment."""

    title: str
    rows: Tuple[Row, ...] = ()
    note: str = ""
    #: Narrated on every read (§7.2). A surface that shows a view without it has
    #: dropped the narration, not merely the caption.
    read_by: str = ""
    at: Optional[datetime] = None

    @property
    def badges(self) -> Tuple[Badge, ...]:
        return tuple(b for row in self.rows for c in row.cells for b in c.badges)


def badge(key) -> Badge:
    """A badge for `"L3"`, `Rung.L3`, `"P2"` or `"T0"`. Refuses a bare integer."""
    return Badge(level(key))


def cell(serving: Serving, *, label: str, seal: Optional[Seal] = None,
         dated: Optional[Dated] = None) -> Cell:
    """One decision, as a surface shows it.

    The rung badge comes from the decision, not from the caller, so a surface
    cannot label an `L4` field `L2` by passing a different string. Where the
    decision carries no rung — an unclassified field, which is a build failure
    upstream — no rung badge is emitted and the cell reads `unknown`: inventing
    a rung to have something to render is the same error as defaulting one to
    `L1`.
    """
    shown = _FROM_OUTCOME[serving.outcome]
    badges = []
    if serving.rung is not None:
        badges.append(badge(serving.rung))
    if serving.provenance:
        badges.append(badge(serving.provenance))

    if shown in (Shown.SERVED, Shown.DERIVED):
        if serving.value is None:
            raise ValueError(
                f"{label!r}: {serving.outcome.value} with no value. The predicate "
                "decided to serve something and there is nothing to serve")
        value = serving.value
    else:
        if serving.value is not None:
            raise ValueError(
                f"{label!r}: {serving.outcome.value} carrying a value. A refusal "
                "that leaks its payload is not a refusal")
        value = REFUSED_TEXT if shown is Shown.REFUSED else UNKNOWN_TEXT

    return Cell(label=label, shown=shown, value=value, badges=tuple(badges),
                seal=seal, dated=dated, why=serving.reason)


def seal_of(record: Record) -> Seal:
    """A `records.sealing.Record`'s state, with the name and date that go with it."""
    return Seal(record.state, record.sealed_by, record.sealed_at)


def dated_of(request: Request) -> Dated:
    """A `records.dispositions.Request`'s clock, as a surface shows it."""
    return Dated(request.disposition, request.due_by, request.answered_at)


def unknown_cell(label: str, why: str) -> Cell:
    """A cell for something that could not be decided at all — a backend that
    could not reach a source, a rubric that failed to load.

    Exists so that a surface with nothing to say has a *thing to render* that is
    not a blank. A blank cell is indistinguishable from a cell with nothing in
    it, which is rule 13's whole subject.
    """
    return Cell(label=label, shown=Shown.UNKNOWN, value=UNKNOWN_TEXT, why=why)


def view(title: str, rows: Sequence[Row], *, note: str = "", read_by: str = "",
         at: Optional[datetime] = None) -> View:
    return View(title=title, rows=tuple(rows), note=note, read_by=read_by, at=at)
