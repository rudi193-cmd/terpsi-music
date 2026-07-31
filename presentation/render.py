"""The named middle for the template/rendered pair: render, and diff.

Rule 12 says a pair gets a named middle **in the same commit**. The pair here is
`presentation/templates/` and `presentation/rendered/` — a generated file and
the thing that generates it, which is the fleet's most reliably-drifting shape.
The middle is `whiskers`' idea, and only its idea (`scout-21` row 2, MIT, not
vendored): render the template, compare against the committed output, and
**exit 1 on any difference**. Repainting a token without regenerating fails the
build; editing a generated file by hand fails the build.

    python3 presentation/render.py --check    # CI: diff, exit 1 on drift
    python3 presentation/render.py --write     # regenerate after a token change

**Why the outputs are committed at all.** A build step that produces them would
make the palette a thing you have to run something to see. Committed, a reviewer
reads the diff — five files move together or the build fails — which is the
discipline, and the reason it costs something.

**The template language is deliberately tiny and strict.** `{{name}}` and
`{{#rows}}…{{/rows}}`, nothing else. An unknown variable **raises**; it does not
render empty. A template that silently drops a variable produces a stylesheet
missing one rung of a five-rung ladder, and the rung that goes missing is the
one nobody looked at.

Stdlib only.
"""

from __future__ import annotations

import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from presentation.scales import LEVELS  # noqa: E402
from presentation.tokens import Palette, load  # noqa: E402

TEMPLATES = HERE / "templates"
RENDERED = HERE / "rendered"

_SECTION = re.compile(r"\{\{#(\w+)\}\}\n?(.*?)\{\{/\1\}\}\n?", re.DOTALL)
#: An opening tag on its own. A nested section is detected by its *opening*
#: rather than by a whole inner section: the outer match is non-greedy, so it
#: closes on the first `{{/…}}` and the body of a nested pair holds only the
#: inner opener. Looking for the pair found nothing, the leftover-braces check
#: raised instead, and the nested-section refusal was dead code that a test
#: appeared to cover.
_OPEN = re.compile(r"\{\{#\w+\}\}")
_VAR = re.compile(r"\{\{([^{}#/]+)\}\}")
_ANY = re.compile(r"\{\{.*?\}\}", re.DOTALL)


class TemplateError(ValueError):
    """A template this renderer will not guess at."""


def _substitute(body: str, row: Dict[str, object], where: str) -> str:
    def one(m):
        name = m.group(1).strip()
        if name not in row:
            raise TemplateError(
                f"{where}: {{{{{name}}}}} is not in the context. An unknown "
                "variable is refused rather than rendered empty — a stylesheet "
                "missing one rung of a five-rung ladder still looks like a "
                "stylesheet")
        return str(row[name])

    return _VAR.sub(one, body)


def render(template: str, context: Dict[str, object], where: str = "template") -> str:
    """`{{var}}` and `{{#section}}…{{/section}}`. Nothing else, and no guessing."""
    def section(m):
        name, body = m.group(1), m.group(2)
        rows = context.get(name)
        if not isinstance(rows, (list, tuple)):
            raise TemplateError(f"{where}: {{{{#{name}}}}} names no list in the context")
        if _OPEN.search(body):
            raise TemplateError(f"{where}: nested sections are not implemented")
        return "".join(_substitute(body, dict(context, **row), where) for row in rows)

    out = _SECTION.sub(section, template)
    out = _substitute(out, context, where)
    leftover = _ANY.search(out)
    if leftover:
        raise TemplateError(f"{where}: {leftover.group(0)!r} was not understood")
    return out


def context(palette: Palette) -> Dict[str, object]:
    """Everything a backend template may know: the palette and the one table.

    A template cannot reach anything else — no student, no record, no clock —
    because this dictionary is the whole world a template has.
    """
    rows: List[Dict[str, object]] = []
    for lv in LEVELS:
        tok = palette.resolve(lv.token)
        rows.append({
            "scale": lv.scale.value,
            "prefix": lv.prefix,
            "key": lv.prefix.lower(),
            "text": lv.text,
            # Padded forms, so a template does no arithmetic and a column can
            # never be produced by counting spaces in a text editor.
            "text_pad": lv.text.ljust(24),
            "scale_pad": lv.scale.value.ljust(14),
            "token": lv.token,
            "weight": lv.weight,
            "hex": tok.hex,
            "xterm256": tok.xterm256,
            "mono": tok.mono,
        })
    return {
        "version": palette.version,
        "levels": rows,
        "paper": palette.resolve("page_paper").hex,
        "ink": palette.resolve("page_ink").hex,
    }


@dataclass(frozen=True)
class Drift:
    name: str
    diff: str


def outputs(palette: Palette = None) -> Dict[str, str]:
    """Every backend artifact, rendered in memory. Keyed by filename."""
    pal = load() if palette is None else palette
    ctx = context(pal)
    if not TEMPLATES.exists():
        raise TemplateError(f"{TEMPLATES} does not exist")
    out = {}
    for t in sorted(TEMPLATES.iterdir()):
        if t.is_file():
            out[t.name] = render(t.read_text(encoding="utf-8"), ctx, t.name)
    if not out:
        raise TemplateError(
            "no templates found; a render of nothing is not a render that agreed")
    return out


def check() -> Tuple[Drift, ...]:
    """What the committed output would have to change to match the templates."""
    drifts = []
    for name, text in outputs().items():
        target = RENDERED / name
        committed = target.read_text(encoding="utf-8") if target.exists() else ""
        if text != committed:
            diff = "".join(difflib.unified_diff(
                committed.splitlines(keepends=True), text.splitlines(keepends=True),
                fromfile=f"rendered/{name} (committed)",
                tofile=f"rendered/{name} (from template)"))
            drifts.append(Drift(name, diff or "(committed file is absent)"))
    return tuple(drifts)


def write() -> Tuple[str, ...]:
    RENDERED.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in outputs().items():
        (RENDERED / name).write_text(text, encoding="utf-8")
        written.append(name)
    return tuple(written)


def main(argv: Sequence[str]) -> int:
    if "--write" in argv:
        for name in write():
            print(f"  wrote    rendered/{name}")
        return 0
    drifts = check()
    for d in drifts:
        print(f"  DRIFT    rendered/{d.name}")
        print(d.diff)
    if drifts:
        print(f"\n  {len(drifts)} rendered file(s) disagree with their template. "
              "Run `python3 presentation/render.py --write` and commit both halves.")
        return 1
    n = len(outputs())
    print(f"  {n} rendered file(s) match their templates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
