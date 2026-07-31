"""A mode that is not a literal. NEVER IMPORTED.

Unresolvable is not a pass: the same rule the socket checker applies to a bind
whose host comes from the environment.
"""

import os

MODE = os.environ.get("TERPSI_MODE", "a")


def touch(path):
    with open(path, MODE) as fh:
        return fh
