"""The browser door: guardians for the transactional 5%, and the judge kiosk.

**One renderer, two entry points, two session models** (`scout-21` §3, point 3).
The judge is on-site on hardware the organisation owns and wipes, under the
knock (§7.2), at a large touch size and high contrast. The guardian is off-site
on an unknown phone behind a passkey. Both get this HTML; neither shares the
other's trust path, and nothing in this module decides which is which — that is
a session question and a session is not a surface.

Server-rendered, no JavaScript, no build step. GOV.UK's rule, adopted: the
service is functional using only HTML. `scout-21` also names what this must not
become — a terminal served into a browser, which gives a guardian a fixed-cell
grid with no form controls, no autofill, no passkey UI, a subprocess per
session, and no print.
"""

from .render import render  # noqa: F401
