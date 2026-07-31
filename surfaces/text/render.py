"""The plainest possible rendering: segments, concatenated.

There is no colour here to force off, which is the point — this backend cannot
degrade, so what it shows is the floor every other backend has to reach.

Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from presentation.ir import View  # noqa: E402
from presentation.lines import view_lines  # noqa: E402


def render(view: View) -> str:
    """The view as text a terminal, a pipe or a screen reader can take."""
    return "\n".join("".join(seg.text for seg in line)
                     for line in view_lines(view)) + "\n"
