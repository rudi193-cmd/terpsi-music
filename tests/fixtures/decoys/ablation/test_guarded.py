"""Catches the guard's removal with an assertion, so the runner names it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guarded import rank  # noqa: E402


def test_an_unknown_value_is_refused():
    try:
        rank("z")
    except ValueError:
        return
    raise AssertionError("rank() accepted a value that is not one")


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
