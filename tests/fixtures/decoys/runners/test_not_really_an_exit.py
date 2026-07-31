"""A runner whose `exit` belongs to something else. NEVER IMPORTED.

`logger.exit()` is not `sys.exit`. The first version matched any attribute
named `exit`.
"""


def test_x():
    assert False


class _Logger:
    def exit(self):
        return None


logger = _Logger()

if __name__ == "__main__":
    logger.exit()
