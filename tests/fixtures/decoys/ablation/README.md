# Decoys for the harness itself

`tests/ablate.py` checks that a guard can be shown to fail. Rule 19 applies to
it too, and these are what point at it.

`verdict()` has three outcomes and each needs its own decoy, or two of them are
decorative:

| file | what it decoys |
|---|---|
| `guarded.py` + `test_guarded.py` | a mutation a test catches by name → `caught` |
| `guarded.py` + `test_indifferent.py` | a mutation nothing looks at → `SURVIVES` |
| `unimportable.py` + `test_unimportable.py` | a mutation that stops the module importing → `NO NAMED FAILURE` |

The third is the one this directory exists for. It is the shape two shipped
mutations were actually in on 2026-07-31, both reported `caught`, because a
nonzero exit was the only thing the harness read.

Parsed and imported only by `tests/test_ablate.py`. Kept out of pytest by
`tests/fixtures/conftest.py`.
