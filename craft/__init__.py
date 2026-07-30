"""Craft feedback for lyrics — the eight text-only checks of §24.

Diagnose, never score. Every function here reports where something is, and
none returns a quality judgement, a grade, or a total. That is a constraint
from the capability map, not a limitation of the implementation, and
`tests/test_craft.py` asserts it holds.

Stdlib only. No network, no model, no corpus download. The whole package is
import-pure in the sense §6 of the architecture requires, and there is a test
that fails the build if that stops being true.
"""

from craft.checks import Finding, Report, run_all, run_diff
from craft.text import Lyric, Line, Section, parse

__all__ = ["Finding", "Lyric", "Line", "Report", "Section", "parse", "run_all", "run_diff"]
