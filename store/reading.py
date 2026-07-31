"""Errored and empty are different facts, and the type says so.

`docs/PLAN-STORE.md` decision 5: *"Every store read distinguishes errored from
empty at the type level — the callable-or-sequence shape `records/sending.py`
already carries."* The acceptance list names the failure directly: **an errored
connection presenting as an empty result anywhere** is one of the seven
forbidden acts, written before this code existed.

**Why a type and not a convention.** The ordinary spelling of a read is

    rows = cur.fetchall()          # [] when the store answered "none"
    ...                            # [] when the driver raised and somebody caught it

and by the time those two `[]`s meet the caller there is nothing to tell them
apart. Every failure this repository has recorded at a seam has that shape: a
consent backend that errored read as *no restrictions*, a ledger that had never
heard of a lane read as *nobody has ever read you*, an unparseable file read as
*clean*. So `read()` returns a `Reading` and there is no path by which a caller
obtains a tuple of rows without having been handed a state alongside it.

**Three ways to consume one, and each fails closed.**

* `reading.rows` — available only when the state is `ROWS`; raises otherwise.
* `for row in reading` — raises on `UNAVAILABLE`, so the loop cannot run zero
  times and look like a store that answered.
* `reading()` — **the callable shape**, so a `Reading` can be handed straight to
  `records/serving.py`'s predicates as their edge or envelope source. That is
  what carries the error channel across the seam rather than stopping it at the
  store: an unreachable edge store now reaches `serve()` as `Outcome.UNKNOWN`
  instead of arriving as `()` and being refused for the wrong reason.

**Empty is still a real answer.** `Reading(ROWS, ())` is a store that looked and
found nothing, it iterates zero times without complaint, and it does not compare
equal to `Reading(UNAVAILABLE, ())`. That inequality is the whole point and
`tests/test_store_reading.py` asserts it rather than trusting the dataclass.

**What counts as unavailable.** Any exception the driver raises, and any
exception at all from the cursor — a connection killed mid-read, a syntax error,
a permission denied. The distinction between *the store is down* and *the query
was wrong* is real and is carried in `reason` and `error`; it is deliberately
**not** carried in the state, because every one of them means the same thing to
a caller deciding what to serve: this answer was not established.

**Stdlib only, and deliberately.** This module imports no driver: `read()` takes
a connection and catches `Exception`, so the type that carries the error channel
can be imported and exercised by a suite with no database — which is how
`tests/test_rule13_acceptance.py` reaches it. The real killed-connection attack
lives in `tests/test_store_reading.py` against a real cluster, and both are
needed: one proves the shape, the other proves it fires.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Sequence, Tuple


class ReadState(Enum):
    ROWS = "rows"                # the store answered. The tuple is the answer.
    UNAVAILABLE = "unavailable"  # it did not. Not an empty answer (rule 13).


class StoreUnavailable(RuntimeError):
    """A read that did not happen, raised where a caller tried to use it as one.

    Carries the originating exception on `.cause` so an operator gets the
    driver's message and not a paraphrase of it.
    """

    def __init__(self, reason: str, cause: Optional[BaseException] = None):
        super().__init__(reason)
        self.cause = cause


@dataclass(frozen=True)
class Reading:
    """One read: its state, and its rows when it has any.

    Frozen, and `rows` is deliberately not the first positional field — a
    caller writing `Reading(some_rows)` gets a `TypeError` about the state
    rather than a plausible object with the wrong meaning.
    """

    state: ReadState
    _rows: Tuple[Any, ...] = ()
    reason: str = ""
    error: Optional[BaseException] = field(default=None, compare=False)

    # --- the three ways to consume one -------------------------------------

    @property
    def rows(self) -> Tuple[Any, ...]:
        """The rows. Raises when there are none *because nothing was read*."""
        if self.state is not ReadState.ROWS:
            raise StoreUnavailable(
                f"this read is {self.state.value}, not rows: {self.reason}. An "
                "errored read is not an empty result", self.error)
        return self._rows

    def __iter__(self):
        return iter(self.rows)

    def __call__(self) -> Tuple[Any, ...]:
        """The callable-or-sequence shape `records/sending.py` carries.

        A `Reading` passed as `edges=` or `envelopes=` to `records.serving.serve`
        is called by the predicate; an unavailable one raises here and the
        predicate answers `UNKNOWN` rather than refusing as though the principal
        genuinely held nothing. That is the closure `PLAN-STORE.md` decision 5
        promises, and it is one method.
        """
        return self.rows

    def __len__(self) -> int:
        """Length of an unavailable read raises rather than answering `0`.

        `if not reading:` is the shortest way to write the bug this module
        exists to prevent, so the falsy path is closed too.
        """
        return len(self.rows)

    # --- the questions worth asking about one ------------------------------

    @property
    def available(self) -> bool:
        return self.state is ReadState.ROWS

    @property
    def empty(self) -> bool:
        """*The store looked and found nothing.* Raises when nothing looked."""
        return len(self.rows) == 0

    def one(self) -> Optional[Any]:
        """The single row, `None` for an established absence, raising otherwise."""
        got = self.rows
        if len(got) > 1:
            raise ValueError(f"{len(got)} rows where one was expected")
        return got[0] if got else None


def rows(found: Sequence[Any], reason: str = "") -> Reading:
    """An established answer, empty or not."""
    got = tuple(found)
    return Reading(ReadState.ROWS, got, reason or f"{len(got)} row(s)")


def unavailable(reason: str, error: Optional[BaseException] = None) -> Reading:
    """An answer that was not established. Never `rows(())`."""
    return Reading(ReadState.UNAVAILABLE, (), reason, error)


def read(conn, sql: str, params: Sequence[Any] = ()) -> Reading:
    """Run one query and return a `Reading`. **Never raises on the store's behalf.**

    The `except Exception` is deliberate and is the same call
    `records/sending.py::recipients` makes: *any* failure is unknown rather than
    empty, and narrowing it to the driver's own exception class would let a
    `MemoryError` or a killed backend surfacing as a bare `OSError` become an
    empty result. The rule is about what the caller can distinguish, not about
    which library was at fault.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            found = cur.fetchall()
    except Exception as exc:  # noqa: BLE001 — see the docstring
        return unavailable(f"the store did not answer: {exc!r}", exc)
    return rows(found)


def guarded(fn: Callable[[], Sequence[Any]]) -> Reading:
    """Wrap a caller's own read in the same channel.

    For the reads that are not one statement — a cursor walked in pieces, a
    `COPY`. The callable runs, and anything it raises becomes `UNAVAILABLE`
    rather than an empty tuple.
    """
    try:
        return rows(fn())
    except Exception as exc:  # noqa: BLE001
        return unavailable(f"the store did not answer: {exc!r}", exc)
