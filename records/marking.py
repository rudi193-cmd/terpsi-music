"""§18 item 7: where a judge's remark is pinned, in time and in the score.

The item asked which of two anchoring schemes to build — align audio against a
stored score, or judge-driven tap-to-mark. **Decided 2026-07-30: both, designed
together now**, one mark type carrying each, so the two cannot diverge into a
migration later.

**The timecode is authoritative and the score position is derived.** That
asymmetry is the whole design and it is not a convenience:

* A judge taps at a moment. That tap is `P1 measured` — it is what happened,
  observed directly, and it stays true whatever the score turns out to say.
* A score position is produced by aligning audio against a stored score. That
  is `P3 fitted` — a model's answer, and models are wrong about repeats, cuts,
  fermatas and a band that drops a bar.

So an alignment may **add** a position to a mark and may never **replace** the
timecode. If the alignment is wrong, the remark is still anchored; if the
timecode were derived from the score, a bad alignment would move a judge's words
to a passage they were not about — which is the failure that makes an
adjudication record worthless in a dispute.

**Rule 12: the pair gets a named middle, in the same commit.** Two spellings of
one location is exactly the pair §16 is about, and the middle is `drift()` — it
asks what the alignment claims the position's time is and compares it to the tap
that is actually true. A mark whose halves disagree is `DIVERGED` and says so,
rather than presenting whichever half the caller happened to read.

**The second failure mode is staleness, and it is the common one.** A score is
edited between the read-through and the show — a cut, an added repeat, a
transposition. Every derived position taken against the old score is now wrong
*and still verifies*, because it is internally consistent. So a position carries
the identity of the score it was derived against, and `stale()` compares that to
the score in force. This is the same shape as `sealing.py`'s digest: a derived
thing must not outlive the thing it was derived from.

**W-3 applies and is not optional here.** A moment in a show involves more than
one student, and *"a shared event is two lane entries with one referent."* So a
`Mark` carries a `referent` — the moment itself, shared — and a mark that names
a student is lane-scoped. There is no participant list on a mark, because a
participant list is the roster column W-1 forbids.

**And a mark is about the work.** It has no field for a student's quality and no
comparison between two of them; ordering is `records/conflict.py`'s refusal, and
`voice.py` refuses the prose form.

Stdlib only. No audio, no network, no model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

#: The `P`-ladder (§15), spelled the way `voice.py` matches it. Never compared
#: as bare integers (rule 14) — `outranks()` is the only ordering.
P_MEASURED = "P1"   # observed directly; a judge's tap
P_CITED = "P2"      # attested by a source
P_FITTED = "P3"     # a model's output; an alignment
P_ESTIMATED = "P4"
P_ASSUMED = "P5"

_P_ORDER = (P_MEASURED, P_CITED, P_FITTED, P_ESTIMATED, P_ASSUMED)


def outranks(a: str, b: str) -> bool:
    """True when `a` is the *stronger* provenance. `P1` outranks `P5`."""
    if a not in _P_ORDER or b not in _P_ORDER:
        raise ValueError(f"not a P-ladder rung: {a!r}, {b!r}")
    return _P_ORDER.index(a) < _P_ORDER.index(b)


@dataclass(frozen=True)
class ScorePosition:
    """Where in the written music, and how that was arrived at.

    Never constructed by a judge — this is an alignment's output. `against`
    identifies the score edition it was derived from, and it is required
    because a position without one cannot be told from a stale position.
    """

    measure: int
    beat: float
    against: str                  # the score edition this was derived against
    maps_to_ms: int               # what the alignment says this position's time is
    provenance: str = P_FITTED
    by: str = ""                  # the aligner that produced it

    def __post_init__(self):
        if self.measure < 1:
            raise ValueError("measures are 1-based; measure 0 is not a place")
        if self.beat < 1:
            raise ValueError("beats are 1-based")
        if not (self.against or "").strip():
            raise ValueError(
                "a derived position must name the score it was derived against; "
                "without it a stale position is indistinguishable from a live one"
            )
        if self.provenance not in _P_ORDER:
            raise ValueError(f"{self.provenance!r} is not a P-ladder rung (rule 14)")
        if outranks(self.provenance, P_CITED):
            raise ValueError(
                "an alignment cannot claim P1 measured; the tap is what was "
                "observed and the position is what a model inferred from it"
            )


@dataclass(frozen=True)
class Mark:
    """A remark anchored to a moment, and optionally to a place in the score.

    `at_ms` and `seat` are required: §13's pairing with `field-acoustics` needs
    both — *"a judge's remark is anchored to a moment and a seat; the acoustic
    model predicts what arrived at that seat."*
    """

    referent: str                 # the moment, shared across lanes (W-3)
    at_ms: int
    seat: str
    lane_id: Optional[str] = None   # set when the mark names a student
    subject_id: Optional[str] = None
    position: Optional[ScorePosition] = None
    provenance: str = P_MEASURED

    def __post_init__(self):
        if self.at_ms < 0:
            raise ValueError("a mark before the performance started is not a mark")
        if not (self.seat or "").strip():
            raise ValueError("a mark must record where it was heard from")
        if (self.subject_id is None) != (self.lane_id is None):
            raise ValueError(
                "a mark naming a student is lane-scoped (W-1); one without the "
                "other is a lane entry with no lane or a lane with no subject"
            )
        if self.provenance not in _P_ORDER:
            raise ValueError(f"{self.provenance!r} is not a P-ladder rung (rule 14)")

    @property
    def anchored(self) -> bool:
        """Always true. The timecode is required, so a mark is never unanchored.

        Stated as a property rather than left implicit because the alternative
        design — a mark anchored *only* by score position — is the one this
        module exists to refuse, and a reader should see that it cannot happen.
        """
        return True


def align(mark: Mark, position: ScorePosition) -> Mark:
    """Add a derived score position to a mark. Never replaces the timecode.

    Returns a new `Mark`; the original is unchanged, so an alignment run that
    turns out to be wrong is discarded rather than reversed.
    """
    if outranks(position.provenance, mark.provenance):
        raise ValueError(
            f"a derived position ({position.provenance}) cannot outrank the "
            f"observation it was derived from ({mark.provenance})"
        )
    return Mark(mark.referent, mark.at_ms, mark.seat, mark.lane_id,
                mark.subject_id, position, mark.provenance)


# --- the named middle (rule 12) --------------------------------------------


class Agreement(Enum):
    UNALIGNED = "unaligned"  # no score position; the tap stands alone
    AGREES = "agrees"
    DIVERGED = "diverged"    # the halves disagree beyond tolerance
    STALE = "stale"          # derived against a score no longer in force


@dataclass(frozen=True)
class Reconciliation:
    state: Agreement
    drift_ms: Optional[int]
    reason: str

    @property
    def usable(self) -> bool:
        """Whether the score position may be shown beside the remark.

        `UNALIGNED` is usable — the mark still has its timecode, which is the
        authoritative half. What is not usable is a position that disagrees with
        the tap or was taken against a different score.
        """
        return self.state in (Agreement.UNALIGNED, Agreement.AGREES)


def drift(mark: Mark, *, score_in_force: Optional[str] = None,
          tolerance_ms: int = 250) -> Reconciliation:
    """Reconcile a mark's two halves. The middle rule 12 requires.

    **Staleness is checked before drift**, because a position derived against a
    superseded score can agree perfectly and still be wrong — internally
    consistent and pointing at a bar that no longer exists. Reporting `AGREES`
    there would be the more dangerous answer.
    """
    p = mark.position
    if p is None:
        return Reconciliation(Agreement.UNALIGNED, None,
                              "no score position; the tap is the whole anchor and "
                              "is still authoritative")
    if score_in_force is not None and p.against != score_in_force:
        return Reconciliation(
            Agreement.STALE, p.maps_to_ms - mark.at_ms,
            f"derived against {p.against!r} while {score_in_force!r} is in force; a "
            "cut or an added repeat moves every position taken against the old one")
    d = p.maps_to_ms - mark.at_ms
    if abs(d) > tolerance_ms:
        return Reconciliation(
            Agreement.DIVERGED, d,
            f"the alignment places m{p.measure} b{p.beat:g} {d}ms from where the "
            "judge tapped; the tap is what was observed")
    return Reconciliation(Agreement.AGREES, d,
                          f"m{p.measure} b{p.beat:g}, within {tolerance_ms}ms of the tap")


def realign(mark: Mark, position: ScorePosition) -> Mark:
    """Replace a stale or diverged position with a freshly derived one.

    Separate from `align()` on purpose. Overwriting a position is a different
    act from adding one — it discards a previous claim — and giving it its own
    name means a call site cannot do it by accident.
    """
    return Mark(mark.referent, mark.at_ms, mark.seat, mark.lane_id,
                mark.subject_id, position, mark.provenance)


def shared(referent: str, marks: Tuple[Mark, ...]) -> Tuple[Mark, ...]:
    """The lane entries for one moment (W-3).

    *"A shared event is two lane entries with one referent."* This returns them;
    it does not merge them, and there is no function here that produces a single
    row with a participant list, because that row is the roster column W-1
    forbids.
    """
    return tuple(m for m in marks if m.referent == referent)
