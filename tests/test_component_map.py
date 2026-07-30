"""§14's Exists column must say whether anyone looked.

§18 item 0's complaint, in its own words: *"an unverified table and a verified
one look identical."* Until 2026-07-30 every **Exists** row in §14 rendered the
same whether its source had been opened or inferred from a README, and §9's
phasing rests on that column.

The fix is the shape `kartikeya.resolve_sandbox_config` uses for the same
defect — **claim plus provenance** — reduced to what a markdown table can carry:

    VERIFIED <ISO date> at `<commit>`   the source was opened, here is when and which
    UNVERIFIED                           nobody has opened it

A row may carry exactly one. The point is not that everything is verified — 32
of 40 are not — but that the two states stop being indistinguishable, which is
the whole of item 0.

Stdlib only. Runs under pytest or directly:

    python3 -m pytest tests/ -q
    python3 tests/test_component_map.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"

_SEPARATOR = re.compile(r"^\|[\s\-:|]+\|\s*$")
#: "VERIFIED 2026-07-30 at `c8c96b4`" — the date and the pin are both required,
#: because "we checked it once" is not a citation (§15). Markdown emphasis is
#: tolerated around the token and the date (`**VERIFIED 2026-07-30**`) because
#: the table is written by hand and a bold marker is not a semantic difference.
_VERIFIED = re.compile(
    r"VERIFIED\*{0,2}\s+\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}\s+at\s+`([0-9a-f]{7,40})`"
)
_UNVERIFIED = re.compile(r"\bUNVERIFIED\b")


def section_14() -> list[str]:
    """Lines between the §14 heading and the §15 heading."""
    lines = ARCHITECTURE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## 14."))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("## 15."))
    return lines[start:end]


def rows() -> list[str]:
    return [
        l for l in section_14()
        if l.startswith("|") and not _SEPARATOR.match(l)
    ]


def exists_rows() -> list[str]:
    """Rows asserting a component exists — the ones item 0 is about."""
    return [l for l in rows() if "Exists" in l or "exists" in l]


# --- the checks ------------------------------------------------------------


def test_the_parser_finds_the_table():
    """Guards the regexes: a parser matching nothing would pass everything
    below for the wrong reason — the trap this repository keeps meeting."""
    assert len(rows()) >= 40, f"only found {len(rows())} rows in §14 — parser broken?"
    assert len(exists_rows()) >= 20, f"only {len(exists_rows())} exists-rows — parser broken?"


def test_every_exists_row_declares_whether_anyone_looked():
    """Item 0, made checkable. A row claiming a component exists must say
    whether that claim was verified at source or is still a citation."""
    bad = [
        l for l in exists_rows()
        if not _VERIFIED.search(l) and not _UNVERIFIED.search(l)
    ]
    assert not bad, "§14 rows claiming existence with no verification state:\n" + "\n".join(
        f"  {l[:110]}" for l in bad
    )


def test_no_row_claims_both_states():
    """A row that reads VERIFIED and UNVERIFIED at once is worse than either,
    because a reader will believe whichever they saw first."""
    both = [l for l in exists_rows() if _VERIFIED.search(l) and _UNVERIFIED.search(l)]
    assert not both, "rows claiming both states:\n" + "\n".join(f"  {l[:110]}" for l in both)


def test_verified_rows_pin_a_commit():
    """'We checked it' decays the way §15 says a `P2` claim decays. A date and
    a commit make the check re-runnable by someone who doubts it."""
    claimed = [l for l in rows() if "VERIFIED" in l and "UNVERIFIED" not in l]
    assert claimed, "no verified rows at all — has the marking been reverted?"
    unpinned = [l for l in claimed if not _VERIFIED.search(l)]
    assert not unpinned, (
        "VERIFIED without a date and a `commit` pin:\n"
        + "\n".join(f"  {l[:110]}" for l in unpinned)
    )


def test_the_check_can_actually_fail():
    """Rule 19. Feed the parser a row of each broken shape and confirm each is
    seen, including the one that looks verified and is not pinned."""
    naked = "| §99 something | `some-repo` | **Exists.** |"
    assert not _VERIFIED.search(naked) and not _UNVERIFIED.search(naked)

    unpinned = "| §99 something | `some-repo` | **Exists.** VERIFIED yesterday |"
    assert not _VERIFIED.search(unpinned), "a date-less VERIFIED slipped through"

    good = "| §99 something | `some-repo` | **Exists.** VERIFIED 2026-07-30 at `abc1234` |"
    m = _VERIFIED.search(good)
    assert m and m.group(1) == "2026-07-30" and m.group(2) == "abc1234"


def test_the_coverage_is_reported_not_hidden():
    """Not an assertion about the ratio — 32 of 40 unverified is the honest
    state today and forcing it upward would only encourage marking things
    verified. This asserts the ratio is *derivable*, so a reader can see how
    much of §14 is still a citation rather than having to count by hand."""
    ex = exists_rows()
    verified = [l for l in ex if _VERIFIED.search(l)]
    assert ex, "no exists-rows — parser broken"
    assert 0 <= len(verified) <= len(ex)
    # A future reader should be able to run this file and read the number off.
    print(f"§14: {len(verified)}/{len(ex)} exists-rows verified at source")


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}\n{exc}\n")
    raise SystemExit(1 if failures else 0)
