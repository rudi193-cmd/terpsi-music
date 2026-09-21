"""D-3 — the cadence and padding control: constant size, and the leak that survives.

`docs/PLAN-DROP.md` D-3, from `scout-03` §2 and `scout-02-metadata.md`: §4.2's
primary control is not sealing the content — that is done — it is denying the
**shape**. `corpus-lens`'s observed fact is that a custody schedule was once
reconstructed from timing alone, so a guardian mailbox that receives traffic on
alternating weekends is the disclosure this system is built to prevent, and
content sealing does not touch it.

Two mechanisms, from SecureDrop's constant-size set at a coarser grain than the
paper's (the PQ key schedule is not needed here; the constant-size padded set
is):

* **Pad every held payload to a fixed size bucket, and answer every collection
  round with a fixed number of slots**, real payloads and random decoys filling
  it. A round over a mailbox with one payload and a round over a mailbox with
  three produce byte-identical responses — the size tracks the *bucket set*, not
  the store, which is the whole point and also the cost (`O(slots)` per round,
  `scout-03` §2's honest note).

* **Flush on a fixed cadence uncorrelated with the event that produced a drop**
  (`Cadence`). The flush happens at each slot whether or not there is anything to
  send, so the timing of a deposit never reaches the wire.

**And the honest half — the leak that survives, measured rather than implied.**
`corpus-lens` documents what its wall does *not* hide and has a test asserting
it. Here the surviving leak is the **cadence period itself**: padding hides which
mailbox and how much and when-within-the-week, but an observer watching the
flushes still learns that they happen once a week — the period is recoverable
from the flush times. `recovered_period()` is that measurement, and
`tests/test_drop_cadence.py` asserts the leak survives, so it is a disclosed
limit rather than an unlooked-for one.

Stdlib only. No network, no store, no model, no filesystem.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence, Tuple

#: The one payload size class. Every held payload is padded to exactly this many
#: bytes, so two payloads of unequal length occupy identical space. A payload
#: larger than this is refused rather than sealed into a bucket that would give
#: its size away — the size class is the disclosure boundary, not a soft target.
BUCKET = 8192

#: The fixed cardinality of a collection round. Every round returns exactly this
#: many bucket-sized entries — real payloads first, random decoys after — so a
#: round's total size is `SLOTS * BUCKET` regardless of how many payloads the
#: mailbox actually holds. SecureDrop's `MAX_MESSAGES`, at this app's grain.
SLOTS = 8

#: The header prefixed inside a padded entry: the real payload's length, so a
#: collector can recover it and a decoy (random bytes) does not parse to a valid
#: length that slices to the collector's own key. Four bytes, big-endian.
_HDR = 4


class TooLargeForBucket(ValueError):
    """A payload larger than the size class. Refused, not sealed into a bigger
    bucket that would leak its size — the constant-size guarantee is the point."""


class RoundTooSmall(ValueError):
    """More real payloads than the round has slots. A round that grew to fit its
    store would be the store-tracking size the padding exists to prevent."""


def pad(payload: bytes, *, bucket: int = BUCKET) -> bytes:
    """Pad one payload to exactly `bucket` bytes, length-prefixed.

    The fill is what makes two unequal payloads occupy identical space; drop it
    and the padded length tracks the content again, which is the mutation
    `tests/test_drop_cadence.py` attempts.
    """
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("pad() takes bytes; the drop pads opaque ciphertext")
    if _HDR + len(payload) > bucket:
        raise TooLargeForBucket(
            f"a {len(payload)}-byte payload does not fit the {bucket}-byte bucket "
            f"with its {_HDR}-byte header; refused rather than sealed into a "
            "larger bucket that would give its size away")
    header = struct.pack(">I", len(payload))
    filler = bytes(bucket - _HDR - len(payload))
    return header + bytes(payload) + filler


def unpad(entry: bytes, *, bucket: int = BUCKET) -> bytes:
    """Recover a payload from a padded entry. The inverse of `pad`."""
    if len(entry) != bucket:
        raise ValueError(f"a padded entry is {bucket} bytes; got {len(entry)}")
    (length,) = struct.unpack(">I", entry[:_HDR])
    if _HDR + length > bucket:
        raise ValueError("the length header does not fit the bucket; this is a "
                         "decoy or a corrupted entry, not a payload")
    return entry[_HDR:_HDR + length]


def collection_round(payloads: Sequence[bytes], *, slots: int = SLOTS,
                     bucket: int = BUCKET) -> Tuple[bytes, ...]:
    """One hand-over: `slots` bucket-sized entries, real payloads then decoys.

    The response size is `slots * bucket`, constant across mailboxes of every
    size, so two rounds over unequal stores are byte-identical in length. The
    decoy fill is the guard: without it a round would return only its real
    entries and its length would track the store — the size disclosure D-3
    exists to deny. Decoys are fresh random bytes the drop cannot tell from a
    real entry and a collector's key will not open.
    """
    real = [pad(p, bucket=bucket) for p in payloads]
    if len(real) > slots:
        raise RoundTooSmall(
            f"{len(real)} payloads and {slots} slots; a round that grew to fit "
            "its store would track the store's size (scout-03 §2)")
    out = list(real)
    while len(out) < slots:
        out.append(os.urandom(bucket))
    return tuple(out)


def round_size(*, slots: int = SLOTS, bucket: int = BUCKET) -> int:
    """The constant a collection round always sums to. Derived, not asserted."""
    return slots * bucket


# --- the fixed flush cadence, and the leak it does not hide -----------------


@dataclass(frozen=True)
class Cadence:
    """A fixed flush schedule, uncorrelated with any deposit.

    A flush happens at every slot in a window whether or not a mailbox has
    anything to send, so a deposit's timing never reaches the wire. What the
    flush schedule *does* disclose — its period — is the surviving leak, and
    `recovered_period` measures it rather than leaving it implied.
    """

    anchor: datetime
    every: timedelta

    def __post_init__(self):
        if self.every <= timedelta(0):
            raise ValueError("a flush cadence needs a positive period")

    def slots(self, since: datetime, until: datetime) -> Tuple[datetime, ...]:
        """The flush instants in `[since, until]`, on the fixed schedule.

        Independent of any deposit — the schedule is a function of the anchor and
        the period alone, which is what *uncorrelated with the event* means.
        """
        if until < since:
            raise ValueError("the window ends before it begins")
        out = []
        # Step from the anchor to the first slot at or after `since`.
        n = 0
        while self.anchor + n * self.every < since:
            n += 1
        t = self.anchor + n * self.every
        while t <= until:
            out.append(t)
            t = t + self.every
        return tuple(out)

    def is_slot(self, when: datetime) -> bool:
        """Whether `when` lands exactly on a flush instant."""
        delta = when - self.anchor
        return delta.total_seconds() % self.every.total_seconds() == 0


def recovered_period(flushes: Sequence[datetime]) -> timedelta:
    """The cadence an observer recovers from the flush times — the surviving leak.

    This is the honest, measured half of D-3 (`corpus-lens`-style). Padding and
    constant-size rounds hide which mailbox, how much, and when-within-the-week;
    they do **not** hide that flushes happen on a period, because an observer
    watching the wire sees the gaps between them. Given two or more flushes, the
    period is the gap — recovered here so a test can assert the leak exists
    rather than a prose note claiming it was considered.
    """
    if len(flushes) < 2:
        raise ValueError("a period needs at least two flushes to measure")
    ordered = sorted(flushes)
    gaps = {ordered[i + 1] - ordered[i] for i in range(len(ordered) - 1)}
    if len(gaps) != 1:
        raise ValueError(
            f"the flushes are not on a single cadence: gaps {sorted(gaps)}; a "
            "wandering schedule discloses more than a fixed one, not less")
    return gaps.pop()
