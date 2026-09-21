"""The screen colour mode of the one HTML document.

Stdlib only. No network: this returns a string, and what serves it is not a
surface concern — `manifest.json` declares no listener and `tools/manifest.py`
fails the build if one appears here undeclared.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from presentation.ir import View  # noqa: E402
from presentation.markup import document  # noqa: E402

#: The committed, rendered stylesheet — not a hand-written one. Repainting a
#: token regenerates it and `presentation/render.py --check` fails the build if
#: the two halves are committed apart.
STYLESHEET = "/static/web.css"


def render(view: View) -> str:
    return document(view, stylesheet=STYLESHEET, mode="screen")
