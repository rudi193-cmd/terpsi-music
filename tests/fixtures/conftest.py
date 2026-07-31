"""Keep pytest out of the decoys.

`tests/fixtures/decoys/runners/test_*.py` are **deliberately broken suites** —
one has no runner, one has an empty runner, one swallows every failure, and two
contain failing tests on purpose. `tools/discipline.py` finds them by globbing
`test_*.py`, so they have to keep that name to be realistic decoys, which is
exactly what makes pytest collect them.

Ignoring them here rather than renaming them is the point: a decoy that does not
look like the real thing does not prove the checker recognises the real thing.

The other decoys need no entry — they are parsed, never imported, and none of
them is named `test_*`.
"""

collect_ignore_glob = ["*"]
