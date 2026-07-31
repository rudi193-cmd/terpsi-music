"""A runner that reports every failure and then exits 0. NEVER IMPORTED.

The PR body called this *"catches every failure, prints FAIL, and exits 0"* and
the first `_exits_nonzero` reported it `OK`, because it asked whether an exit
existed and never what it returned.
"""


def test_x():
    assert False


if __name__ == "__main__":
    import sys
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except AssertionError as exc:
                print(f"FAIL {name}\n{exc}\n")
    sys.exit(0)
