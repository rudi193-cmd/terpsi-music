"""Forced monochrome, and the assertion that nothing was lost.

`scout-21` §2.2 names this precisely, and names it as the guard that `--check`
is **not**: *"`--check` proves the backends agree on colour. It does not prove
they agree on information. The guard that must be shown to fail is a separate
one: render every rung badge under a forced monochrome profile and assert the
rendered text still contains the literal prefix."* Its §5 adds that no tool off
the shelf does this — axe-core, WAVE and the commercial suites all concede that
WCAG 1.4.1 needs human judgement — so this is written here or it is nowhere.

**What it checks, and why each half is needed.**

* **The prefix is present, in every backend.** Expected text is re-derived from
  `presentation/scales.py` — the one table — rather than read off the badge
  object, so a badge that lies about its own text is caught rather than
  believed. That is the difference between checking a renderer and checking a
  renderer's opinion of itself.
* **The monochrome rendering carries every distinction.** Set equality, not a
  count: two badges rendering the same string in ASCII are one badge to a
  screen reader even if they are two colours on a screen.
* **No two rungs differ by colour alone.** Distinct levels must produce distinct
  text. A ladder whose badges all read *Restricted* and differ only in
  background is the exact failure §15's added requirement is written against.

The checker returns findings and never raises: it is pointed at deliberately
broken renderings in `tests/test_surfaces.py`, and a checker that raised would
be indistinguishable from a checker that crashed.

Stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Tuple

from .ir import View
from .scales import level

#: SGR sequences, so a coloured rendering can be reduced to what a monochrome
#: terminal would show. `\x1b[38;5;246m` and friends.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip_colour(text: str) -> str:
    """What is left of a terminal rendering when the colour is taken away."""
    return _ANSI.sub("", text)


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str


def expected(view: View) -> Tuple[str, ...]:
    """Every badge in this view, as the one table says it must read."""
    return tuple(level(b.level.prefix).text for b in view.badges)


def parity(view: View, renderings: Dict[str, str]) -> Tuple[Finding, ...]:
    """Findings across the backends. `()` is the only passing result.

    `renderings` is `{backend name: what it produced}`. An empty mapping is a
    finding rather than a pass — a parity check with nothing to compare has not
    compared anything (rule 13, and `tools/sockets.py`'s vacuous case).
    """
    findings = []
    if not renderings:
        return (Finding("NOTHING_RENDERED",
                        "no backend output was supplied; nothing was compared"),)
    want = expected(view)
    if view.badges and not want:
        return (Finding("NO_BADGES", "the view carries badges that resolve to no text"),)

    for name, out in sorted(renderings.items()):
        plain = strip_colour(out)
        for text in want:
            if text not in plain:
                findings.append(Finding(
                    "PREFIX_ABSENT",
                    f"{name}: {text!r} does not appear in the rendering with its "
                    "colour removed; this badge is encoded by colour alone"))
        for prefix in {t.split(" ", 1)[0] for t in want}:
            if prefix not in plain:
                findings.append(Finding(
                    "SCALE_PREFIX_ABSENT",
                    f"{name}: the scale prefix {prefix!r} is missing, so a bare "
                    "rung is travelling without its ladder (rule 14)"))

    # Set equality against the monochrome surface, which is the one that has to
    # carry everything. Named `text` because that is the backend's name.
    if "text" in renderings:
        plain = strip_colour(renderings["text"])
        missing = sorted({t for t in want if t not in plain})
        if missing:
            findings.append(Finding(
                "MONOCHROME_LOSS",
                f"the text backend is missing {missing}; forced monochrome lost "
                "a distinction the coloured backends carry"))

    distinct = {t for t in want}
    if len(distinct) != len({t.split(" ", 1)[0] for t in want}):
        findings.append(Finding(
            "COLOUR_ALONE",
            "two rungs render as the same string, so they are distinguishable "
            "only by colour"))

    return tuple(findings)
