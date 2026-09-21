"""D-3 acceptance: cadence and padding (`docs/PLAN-DROP.md` D-3).

Rule 19. D-3's forbidden act is a drop whose size or timing tracks its contents.
One test requires byte-identical sizes across unequal stores; a second asserts
the **surviving leak** — the weekly cadence — so the limit is measured, not
glossed (`corpus-lens`).

Stdlib and `drop/`. Runs under pytest or directly:

    python3 -m pytest tests/test_drop_cadence.py -q
    python3 tests/test_drop_cadence.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drop.cadence import (BUCKET, SLOTS, Cadence, RoundTooSmall,  # noqa: E402
                          TooLargeForBucket, collection_round, pad,
                          recovered_period, round_size, unpad)


# --- forbidden act: a size that tracks the store ----------------------------


def test_a_round_is_constant_size_across_unequal_stores():
    """Acceptance test 3. A mailbox with one payload and a mailbox with three
    hand over byte-identical responses: the size tracks the bucket set, not the
    store."""
    thin = collection_round([b"one"])
    fat = collection_round([b"one", b"two-is-longer", b"three-is-longer-still"])
    thin_bytes = b"".join(thin)
    fat_bytes = b"".join(fat)
    assert len(thin_bytes) == len(fat_bytes) == round_size(), (
        f"unequal stores handed over unequal sizes: {len(thin_bytes)} vs "
        f"{len(fat_bytes)} (round_size {round_size()})")
    assert len(thin) == len(fat) == SLOTS


def test_padding_makes_unequal_payloads_equal_length():
    short = pad(b"x")
    long = pad(b"x" * 4000)
    assert len(short) == len(long) == BUCKET, "the bucket does not equalise sizes"
    assert unpad(short) == b"x"
    assert unpad(long) == b"x" * 4000


def test_a_payload_too_large_for_the_bucket_is_refused():
    try:
        pad(b"x" * (BUCKET + 1))
    except TooLargeForBucket:
        return
    raise AssertionError("an over-large payload was sealed into a bigger bucket, "
                         "leaking its size")


def test_a_round_that_would_grow_to_fit_its_store_is_refused():
    try:
        collection_round([b"p"] * (SLOTS + 1))
    except RoundTooSmall:
        return
    raise AssertionError("a round grew past its slots — the size would track the store")


def test_the_real_payloads_are_recoverable_from_a_round():
    payloads = [b"first", b"second"]
    a_round = collection_round(payloads)
    assert [unpad(a_round[i]) for i in range(len(payloads))] == payloads


# --- the flush cadence is uncorrelated with deposits ------------------------


def test_the_flush_schedule_is_a_function_of_the_anchor_and_period_alone():
    """A flush happens at every slot in a window regardless of any deposit, so a
    deposit's timing never reaches the wire."""
    anchor = datetime(2026, 1, 4, 3, 0)   # a Sunday, 3am
    weekly = Cadence(anchor, timedelta(weeks=1))
    window = weekly.slots(datetime(2026, 1, 1), datetime(2026, 2, 5))
    assert window == (
        datetime(2026, 1, 4, 3, 0), datetime(2026, 1, 11, 3, 0),
        datetime(2026, 1, 18, 3, 0), datetime(2026, 1, 25, 3, 0),
        datetime(2026, 2, 1, 3, 0)), window
    assert weekly.is_slot(datetime(2026, 1, 18, 3, 0))
    assert not weekly.is_slot(datetime(2026, 1, 18, 4, 0))


# --- the honest half: the leak that survives, measured ----------------------


def test_the_surviving_leak_is_the_weekly_cadence():
    """`corpus-lens`-style. Padding hides which mailbox, how much, and
    when-within-the-week; it does **not** hide that flushes happen once a week.
    The period is recoverable from the flush times, and this asserts it does —
    a disclosed limit rather than an unlooked-for one."""
    weekly = Cadence(datetime(2026, 1, 4, 3, 0), timedelta(weeks=1))
    flushes = weekly.slots(datetime(2026, 1, 1), datetime(2026, 3, 5))
    leak = recovered_period(flushes)
    assert leak == timedelta(weeks=1), (
        f"an observer recovers the cadence from the flushes: {leak}")
    # And the leak is the *only* thing recoverable from the schedule: the flush
    # count over the window is one per week regardless of how many drops each
    # flush carried.
    assert len(flushes) == 9, f"a week per flush, nothing per-drop: {len(flushes)}"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
