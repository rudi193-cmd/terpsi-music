"""D-1 — the sealed guardian view: one student's rendered slice, sealed for hand-over.

`docs/PLAN-DROP.md` D-1. The guardian-scoped assembly — the entries a single
guardian is entitled to about a **single student**, decided by the read
predicate, composed into a `presentation.View`, and sealed with
`records/atrest.py` into an opaque `Sealed` payload — is the plaintext the drop
carries. Fleet provenance (the briar-mailbox / SecureDrop shape) is cited in
`docs/survey/scout-03-relay-localfirst.md`; nothing here is a fleet noun.

**One student per payload — never a roster row (W-1/W-3).** The IR already
refuses a participant list on a `Row` (`presentation/ir.py`), so a shared event
is two lane entries with one referent rather than one row with a roster column.
This module adds the seam a drop needs on top of that: a view that names *two*
students is refused before anything is sealed. That is D-1's forbidden act, and
`_one_student` is the guard `tests/test_drop_producer.py` attempts to defeat.

**It seals a derived view, not a record.** This is the R16-relevant fact and it
is deliberate: `produce()` never touches `store/writing.py`'s record-write path,
so `tools/audit.py::durable_callers()` stays empty and R16 stays `FINDING`/`S2`
(`docs/PLAN-DROP.md`, *R16 note*). The bytes it produces are handed to the drop
(`drop/store.py`), which holds them **ephemerally** — nothing here or there puts
a byte on a disk.

**Fail-closed, the `jeles-remote` bar (§4.3).** If the sealing primitive is not
usable on this box, or the lane key material cannot be obtained, `produce()`
returns `UNAVAILABLE` and lands **nothing** — never a plaintext payload and
never an empty one dressed as a result (rule 13). The producer without its key
material refuses to operate and says why, exactly as `records/atrest.available()`
fails loud rather than degrading.

Reuses, never rebuilds (§16):

* `records/atrest.py` — `seal_bytes`, `LaneKey`, `Sealed`, `available`. The
  family-circle seal is a lane seal; the payload is sealed under one lane key,
  which is one student's key (W-1).
* `presentation/markup.py` — `document()`, escaped HTML, R6-audited. The
  guardian's rendered view is the plaintext this seals.
* `presentation/ir.py` — the `View`/`Row`/`Cell` a decision composes into.

Stdlib, `records/`, and `presentation/`. No network, no store, no model, no
filesystem.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records.atrest import LaneKey, Sealed, available, seal_bytes  # noqa: E402

from presentation.ir import View  # noqa: E402
from presentation.markup import document  # noqa: E402

#: The stylesheet the sealed document references. A plain string href, escaped
#: into the markup like any other; a drop client renders it, and no file is
#: opened here (this module writes nothing to disk — see the R16 note above).
STYLESHEET = "drop.css"


class TwoStudents(ValueError):
    """A view that names or resolves to a second student (W-1/W-3).

    D-1's forbidden act. A payload seals **one** student's lane; a view whose
    rows carry more than one referent would put two students under one lane key,
    which is rule 8's roster column moved down to the seal. Refused before any
    ciphertext exists, so the leak is unsealable rather than merely unsent.
    """


class Made(Enum):
    """What `produce()` did. **Never one boolean, and absence is its own state.**

    `UNAVAILABLE` is not `SEALED` with an empty payload: a producer that could
    not obtain its key material and one that sealed nothing are different facts,
    and collapsing them is the rule-13 shape this module exists to refuse.
    """

    SEALED = "sealed"            # a payload exists and is carried on `.sealed`
    UNAVAILABLE = "unavailable"  # no key material; nothing landed (rule 13)


@dataclass(frozen=True)
class Production:
    """The result of one production. Carries the payload only on `SEALED`.

    The invariant is `presentation/ir.py`'s, one tier over: a `SEALED` result
    with no payload renders as a seal over nothing, and an `UNAVAILABLE` result
    carrying ciphertext is the plaintext-fallback fail-closed exists to forbid.
    """

    state: Made
    sealed: Optional[Sealed]
    reason: str

    def __post_init__(self):
        if self.state is Made.SEALED and self.sealed is None:
            raise ValueError(
                "a SEALED production with no payload seals nothing; either a "
                "payload landed or the state is UNAVAILABLE (rule 13)")
        if self.state is Made.UNAVAILABLE and self.sealed is not None:
            raise ValueError(
                "an UNAVAILABLE production carrying a payload is the plaintext "
                "fallback the fail-closed bar refuses (§4.3)")

    @property
    def landed(self) -> bool:
        return self.state is Made.SEALED


def _one_student(view: View) -> str:
    """The single student a view is about, or `TwoStudents` if it is about two.

    Referents that are blank are ignored — a schedule line or a note need not
    name a student — but two *distinct* named referents is the forbidden act.
    The check reads the referents the IR already carries rather than a roster
    column, because the IR has no roster column to read (W-3).
    """
    students = {row.referent for row in view.rows if row.referent}
    if len(students) > 1:
        raise TwoStudents(
            f"this view names {len(students)} students ({', '.join(sorted(students))}) "
            "and a payload seals one lane, one student (W-1/W-3). Refused before "
            "sealing, so two students cannot share one lane key")
    return next(iter(students), "")


def produce(view: View, *, lane_key_source: Callable[[], LaneKey],
            at: datetime, available: Callable[[], bool] = available) -> Production:
    """Seal one guardian's view of one student into an opaque payload.

    `lane_key_source` is a callable rather than a `LaneKey` for the reason
    `records/sending.py` and `records/serving.py` take callables: a source that
    **raises** surfaces as `UNAVAILABLE`, never as a key that happened to be
    absent (rule 13). The single student's lane key is what binds the payload to
    one student, and obtaining it is where fail-closed lives.

    Order is load-bearing. The primitive is checked first (fail-closed, the
    `jeles-remote` bar): a box that cannot seal lands nothing before it looks at
    a view. Then the one-student seam runs, before any key is touched, so the
    forbidden act is refused whether or not a key is available.
    """
    if not available():
        return Production(
            Made.UNAVAILABLE, None,
            "the sealing primitive is not usable on this box; landing nothing "
            "rather than a plaintext payload (fail-closed, §4.3; rule 13)")
    # The forbidden-act seam, before any key material is obtained.
    _one_student(view)
    try:
        lane_key = lane_key_source()
    except Exception as exc:  # noqa: BLE001 — any failure is unavailable, not a key
        return Production(
            Made.UNAVAILABLE, None,
            f"the lane key material could not be obtained ({exc!r}); landing "
            "nothing rather than a plaintext payload (rule 13)")
    plaintext = document(view, stylesheet=STYLESHEET, mode="screen").encode("utf-8")
    sealed = seal_bytes(plaintext, lane_key=lane_key, at=at)
    return Production(
        Made.SEALED, sealed,
        f"sealed {len(sealed.ciphertext)} byte(s) for lane {sealed.lane_id}")
