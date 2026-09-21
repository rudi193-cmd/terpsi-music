"""Drop — the drop producer core (item 7's in-repo half).

Plain domain noun, no fleet nouns in any string a student, guardian or judge can
see (`CLAUDE.md`, *Working here*). This package is the **producer** side of
`docs/ARCHITECTURE.md` §4.2's option (b): a guardian-scoped view sealed into an
opaque, size-bucketed payload (D-1); the hold / hand-over / delete drop as a
local, ephemeral store with an owner-bound credential (D-2); the cadence and
padding control (D-3); and the who-gets-a-drop gate, reused from
`records/sending.py` (D-4). `docs/PLAN-DROP.md` is the spec.

What a listener, a network, or an identity system would add is not here and is
tombstoned in `docs/PLAN-DROP.md`: no inbound listener, no hosted relay, no
passkeys, no PWA client, no SMS. Nothing in this package reaches the network,
opens a store, loads a model, or writes a byte to disk — the hold is in memory
and drops with the process (the R16 decision, `docs/PLAN-DROP.md`, R16 note).
"""

from .producer import (Made, Production, TwoStudents, STYLESHEET, produce,
                       _one_student)
from .store import Drop, DropUnavailable, Handle, OwnerCredential
from .cadence import (BUCKET, SLOTS, Cadence, RoundTooSmall, TooLargeForBucket,
                      collection_round, pad, recovered_period, round_size, unpad)
from .preparing import Prepared, PreparedDrops, prepare

__all__ = [
    "Made", "Production", "TwoStudents", "STYLESHEET", "produce", "_one_student",
    "Drop", "DropUnavailable", "Handle", "OwnerCredential",
    "BUCKET", "SLOTS", "Cadence", "RoundTooSmall", "TooLargeForBucket",
    "collection_round", "pad", "recovered_period", "round_size", "unpad",
    "Prepared", "PreparedDrops", "prepare",
]
