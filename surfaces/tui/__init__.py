"""The terminal door: staff, techs, the on-site director, off-site over the tailnet.

A skeleton over the IR, not an application. `scout-21` recommends Textual with
`pytest-textual-snapshot`; nothing here depends on either, and this module is
what such an application would render. Choosing the framework is not this
commit; the manifest declares no listener because nothing here opens one.

**This is not the accessible surface** and the decision record says so out loud
rather than letting *"it's a TUI, it's text, it's fine"* stand. See
`surfaces/text/`.
"""

from .render import render  # noqa: F401
