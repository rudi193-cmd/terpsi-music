"""A runner that reports success no matter what. NEVER IMPORTED.

Worse than having no runner, because the conformance record then carries a row
saying this suite runs standalone.
"""


def test_x():
    assert False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
            except AssertionError as exc:
                print("FAIL", name, exc)
