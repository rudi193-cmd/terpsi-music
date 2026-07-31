"""The paper colour mode of the one HTML document.

Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from presentation.ir import View  # noqa: E402
from presentation.markup import document  # noqa: E402

STYLESHEET = "print.css"


def render(view: View) -> str:
    return document(view, stylesheet=STYLESHEET, mode="print")
