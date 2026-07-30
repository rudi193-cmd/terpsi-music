"""CLI: python3 -m craft <file> [--prose] [--against <earlier draft>] [--intent <file>]

Prints findings, declared intents, and notes. Prints no score, no total, and
no verdict, which is a constraint from §24 rather than an omission.

`--prose` swaps the checks for the document skin (`craft/prose.py`) and
changes nothing else: same report shape, same intent-file format, same
declaration mechanic. That is the whole claim of `docs/SKINS.md` §5.1 — the
subject changes and the contract does not.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from craft import checks, prose
from craft.checks import load_intents


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="craft", description="Craft feedback. Diagnoses; never scores."
    )
    ap.add_argument("lyric", metavar="FILE", help="the draft to read")
    ap.add_argument("--prose", action="store_true",
                    help="read it as a document rather than as a lyric")
    ap.add_argument("--against", metavar="EARLIER",
                    help="an earlier draft; reports what the revision moved")
    ap.add_argument("--intent", metavar="FILE",
                    help="declared intents: '<finding-id>  <reason>' per line")
    args = ap.parse_args(argv)

    skin = prose if args.prose else checks

    text = _read(args.lyric)
    intents = load_intents(_read(args.intent)) if args.intent else {}
    report = skin.run_all(text, intents)

    if args.against:
        introduced, notes = skin.run_diff(_read(args.against), text)
        print(f"=== revision: {args.against} → {args.lyric}")
        for n in notes:
            print(n)
        if introduced:
            print("\n--- introduced by this revision")
            for f in introduced:
                print(f)
        print()

    if report.unavailable:
        print("=== unavailable")
        for u in report.unavailable:
            print(f"  {u}")
        print()

    if report.findings:
        print(f"=== findings ({len(report.findings)})")
        for f in sorted(report.findings, key=lambda f: (f.line or 0, f.id)):
            print(f)
            print(f"    declare intent: add `{f.id}  <why>` to your intent file")
        print()
    else:
        print("=== findings (0)\n")

    if report.declared:
        print(f"=== declared intentional ({len(report.declared)})")
        for f, reason in report.declared:
            print(f"[{f.id}] {f.where}\n    kept on purpose: {reason}")
        print()

    if report.notes:
        print("=== notes")
        for n in report.notes:
            print(f"  {n}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
