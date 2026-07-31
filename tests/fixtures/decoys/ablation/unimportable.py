"""The shape the review found: a mutation that stops the module importing.

`IntEnum` members must be `int`. These carry names, so swapping the base class
raises `ValueError` while the class body executes — before any test runs. This
is `records/rungs.py`'s shipped mutation, kept here as a decoy rather than as a
memory.
"""

import enum


class Band(enum.Enum):
    LOW = "low"
    HIGH = "high"
