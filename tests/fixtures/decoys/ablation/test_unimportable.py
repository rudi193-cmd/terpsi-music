"""Would catch the mutation if it ever reached a test. It does not."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unimportable import Band  # noqa: E402


def test_bands_do_not_compare():
    try:
        Band.LOW < Band.HIGH  # noqa: B015
    except TypeError:
        return
    raise AssertionError("bands compared")


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
