"""The paper door: the printed program, the printed roster, the W-6 lane export.

Print is a **backend**, not a report — the same document as `surfaces/web` in
the paper colour mode (`presentation/markup.py` carries the argument and the
prior art). `scout-21` recommends WeasyPrint on the parity argument: it consumes
the same CSS tokens as the browser surface, so one render-and-diff covers both
and print never becomes a second typesetting language.

Nothing here depends on WeasyPrint. This produces the HTML it would consume,
which is also the HTML a browser's own print dialogue consumes — so the paper
path has no unique code to rot.
"""

from .render import render  # noqa: F401
