"""`tokens.yaml`, read by a parser that refuses what it does not understand.

**Why a parser and not a dependency.** This repository carries no third-party
package and the posture is the point (§6, and `.github/workflows/tests.yml` says
so of the suite). A YAML library would be the first, for a file this module can
read in eighty lines.

**Why a strict subset rather than a lenient reader.** A lenient parser meeting a
construct it does not implement produces *something*, and for a palette that
something is a colour nobody chose. Every line here is either understood or
named in an error: no lists, no flow style, no anchors, no multi-line scalars,
no tabs, no duplicate keys. Rule 13, applied to a file format — a token that
could not be read is not a token that is white.

**Two properties this file enforces that a YAML library would not.**

* **The ladder is monotonic in luminance.** `caution_0`…`caution_4` must fall
  strictly, computed by the sRGB relative-luminance formula. That is the
  property that makes greyscale, print and `TERM=dumb` lossless, and it is
  exactly the property a repaint breaks silently.
* **An alias may not be defined.** §15's rule from `safe-design`: aliases
  resolve at lookup, and setting one directly is refused *with the canonical
  token named*, so the error tells the author where to make the change.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

TOKENS = Path(__file__).resolve().parent / "tokens.yaml"

#: Every token carries all three, because a backend missing one has to render
#: *something* and the something is always wrong.
REQUIRED = ("hex", "xterm256", "mono")

#: The emphasis ladder, in the order it must fall.
LADDER: Tuple[str, ...] = tuple(f"caution_{i}" for i in range(5))


class TokenError(ValueError):
    """A palette that could not be read. Never downgraded to a default."""


@dataclass(frozen=True)
class Token:
    name: str
    hex: str
    xterm256: int
    mono: str          # the ASCII fill: the monochrome channel, never blank

    @property
    def luminance(self) -> float:
        """sRGB relative luminance, 0–1. The channel that survives everything."""
        r, g, b = (int(self.hex[i:i + 2], 16) / 255 for i in (1, 3, 5))

        def lin(c: float) -> float:
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


@dataclass(frozen=True)
class Palette:
    version: str
    tokens: Dict[str, Token]
    aliases: Dict[str, str]

    def resolve(self, name: str) -> Token:
        """A token or an alias. **One hop, and the hop happens here** — an alias
        chain would let a skin move a canonical token by editing an alias."""
        if name in self.tokens:
            return self.tokens[name]
        if name in self.aliases:
            target = self.aliases[name]
            if target not in self.tokens:
                raise TokenError(
                    f"alias {name!r} points at {target!r}, which is not a token")
            return self.tokens[target]
        raise TokenError(f"no token or alias named {name!r}")


def _scalar(raw: str, where: str):
    """A quoted string, a bare word, or an integer. Nothing else."""
    raw = raw.strip()
    if not raw:
        raise TokenError(f"{where}: a key with no value; absence is not a colour")
    if raw[0] in "[{&*|>":
        raise TokenError(
            f"{where}: {raw[0]!r} starts a YAML construct this reader does not "
            "implement (lists, flow style, anchors, block scalars). It is refused "
            "rather than guessed at")
    if raw[0] in "\"'":
        quote = raw[0]
        end = raw.find(quote, 1)
        if end < 0:
            raise TokenError(f"{where}: unterminated {quote} string")
        return raw[1:end]
    raw = raw.split(" #", 1)[0].strip()
    if raw.lstrip("-").isdigit():
        return int(raw)
    return raw


def parse(text: str) -> Palette:
    """The subset, and nothing but."""
    top: Dict[str, object] = {}
    section: Optional[str] = None
    for n, line in enumerate(text.splitlines(), start=1):
        where = f"tokens.yaml line {n}"
        if "\t" in line:
            raise TokenError(f"{where}: a tab; indentation here is spaces only")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent not in (0, 2, 4):
            raise TokenError(f"{where}: indent {indent}; this reader knows 0, 2 and 4")
        if ":" not in stripped:
            raise TokenError(f"{where}: {stripped!r} is not `key: value`")
        key, _, rest = stripped.partition(":")
        key, rest = key.strip(), rest.strip()

        if indent == 0:
            if key in top:
                raise TokenError(f"{where}: {key!r} is declared twice")
            if rest:
                top[key] = _scalar(rest, where)
                section = None
            else:
                top[key] = {}
                section = key
        elif indent == 2:
            if section is None or not isinstance(top.get(section), dict):
                raise TokenError(f"{where}: {key!r} is indented under no block")
            block = top[section]
            if key in block:
                raise TokenError(
                    f"{where}: {key!r} is declared twice in {section!r}; a palette "
                    "whose second definition silently wins is a palette nobody can "
                    "review")
            block[key] = _scalar(rest, where) if rest else {}
        else:  # indent == 4
            if section is None:
                raise TokenError(f"{where}: {key!r} is indented under no block")
            parent = list(top[section].values())[-1] if top[section] else None
            if not isinstance(parent, dict):
                raise TokenError(f"{where}: {key!r} is indented under a scalar")
            if key in parent:
                raise TokenError(f"{where}: {key!r} is declared twice")
            parent[key] = _scalar(rest, where)

    return _build(top)


def _build(top: Dict[str, object]) -> Palette:
    for required in ("version", "tokens", "aliases"):
        if required not in top:
            raise TokenError(f"tokens.yaml declares no {required!r}")

    tokens: Dict[str, Token] = {}
    for name, body in top["tokens"].items():
        if not isinstance(body, dict):
            raise TokenError(f"token {name!r} is a scalar, not a block")
        missing = [f for f in REQUIRED if f not in body]
        if missing:
            raise TokenError(
                f"token {name!r} declares no {', '.join(missing)} — a backend "
                "missing one of the three has to render something, and the "
                "something is always wrong")
        if not isinstance(body["xterm256"], int):
            raise TokenError(f"token {name!r}: xterm256 is not a number")
        if not str(body["hex"]).startswith("#") or len(str(body["hex"])) != 7:
            raise TokenError(f"token {name!r}: hex is not #rrggbb")
        tokens[name] = Token(name, str(body["hex"]), int(body["xterm256"]),
                             str(body["mono"]))

    aliases: Dict[str, str] = {}
    for name, target in top["aliases"].items():
        if name in tokens:
            raise TokenError(
                f"{name!r} is an alias and is also defined in `tokens:`. Aliases "
                f"resolve at lookup, never at definition — repaint {target!r} "
                "instead, and every alias onto it moves with it")
        if not isinstance(target, str):
            raise TokenError(f"alias {name!r} does not name a token")
        aliases[name] = target

    palette = Palette(str(top["version"]), tokens, aliases)
    _check_ladder(palette)
    for name in aliases:
        palette.resolve(name)      # a dangling alias is a load failure, not a lookup one
    return palette


def _check_ladder(palette: Palette) -> None:
    """The emphasis ladder falls strictly in luminance, and every rung is there.

    A ladder with two rungs at the same luminance is two rungs that are one rung
    in greyscale, on paper, and under a stadium light — which is the whole
    failure `L1–L5` may not be encoded by colour alone is written against.
    """
    missing = [name for name in LADDER if name not in palette.tokens]
    if missing:
        raise TokenError(f"the emphasis ladder is missing {', '.join(missing)}")
    lums = [palette.tokens[name].luminance for name in LADDER]
    for (a, la), (b, lb) in zip(zip(LADDER, lums), zip(LADDER[1:], lums[1:])):
        if not la > lb:
            raise TokenError(
                f"{a} ({la:.3f}) does not out-lighten {b} ({lb:.3f}); the ladder "
                "is not monotonic in luminance and does not survive greyscale")
    monos = [palette.tokens[name].mono for name in LADDER]
    if len(set(monos)) != len(monos) or any(not m.strip() for m in monos):
        raise TokenError(
            f"the ASCII fills {monos} are not distinct and non-blank; the "
            "monochrome channel has to carry every distinction the colour does")


def load(path: Optional[Path] = None) -> Palette:
    p = TOKENS if path is None else Path(path)
    if not p.exists():
        raise TokenError(f"{p} does not exist; a missing palette is not a default one")
    return parse(p.read_text(encoding="utf-8"))


if __name__ == "__main__":  # pragma: no cover - a look at the palette
    pal = load()
    print(f"  {pal.version}")
    for name, tok in pal.tokens.items():
        print(f"  {name:<12} {tok.hex}  xterm {tok.xterm256:<4} mono {tok.mono!r}  "
              f"lum {tok.luminance:.3f}")
    for alias, target in pal.aliases.items():
        print(f"  {alias:<12} -> {target}")
