"""Four doors, and the parity that makes the ASCII one the instrument.

The load-bearing test in this file is `test_forced_monochrome_loses_nothing`:
render every rung badge with colour forced off and assert the literal prefix is
still there. `scout-21` §5 is explicit that nothing off the shelf does this —
axe-core, WAVE and the commercial suites flag adjacent things and every source
concedes WCAG 1.4.1 needs human judgement — so the enforcement for §15's added
requirement is written here or it does not exist.

Rule 19: the deliberately-broken renderings below are this file's decoys. A
parity checker that has only ever seen correct output is indistinguishable from
one that cannot see a missing prefix.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import ast
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from presentation import ir  # noqa: E402
from presentation.parity import Finding, parity, strip_colour  # noqa: E402
from presentation.scales import LEVELS  # noqa: E402
from records import dispositions, sealing  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Edge, Field, Principal, serve  # noqa: E402
from surfaces.print.render import render as render_print  # noqa: E402
from surfaces.text.render import render as render_text  # noqa: E402
from surfaces.tui.render import Profile, render as render_tui  # noqa: E402
from surfaces.web.render import render as render_web  # noqa: E402

AT = datetime(2026, 7, 14, 15, 30, tzinfo=timezone.utc)

#: Never in a string a student, guardian or judge can see (CLAUDE.md, "Working
#: here"). Word-boundary and case-sensitive: these are proper nouns, and a
#: substring match would fail on "honest" for one of them.
FLEET_NOUNS = ("Willow", "Grove", "Jeles", "Kart", "SOIL", "LOAM", "FRANK",
               "Nest", "Nestor", "SAFE", "SAP")


def _lane_view():
    """One lane, one moment, every state a cell can be in.

    Not a fixture of convenience: the parity claim is only as good as the view
    it is made over, so this carries a served payload, a derived instruction, a
    refusal, an unknown, a seal and an open disposition.
    """
    edge = Edge("staff_of", "staff-nguyen", "student-ben", AT - timedelta(days=200),
                created_at=AT - timedelta(days=200))
    staff = Principal("staff-nguyen", frozenset({"health"}))
    stranger = Principal("judge-ruiz")

    attendance = Field("lane-ben", "student-ben", "attendance", Rung.L3,
                       payload="present", provenance="P1")
    medical = Field("lane-ben", "student-ben", "medical", Rung.L4, category="health",
                    payload="epinephrine auto-injector",
                    instruction="one student carries an auto-injector", provenance="P2")
    money = Field("lane-ben", "student-ben", "fee balance", Rung.L4, category="money",
                  payload="41.00", provenance="P3")
    unclassified = Field("lane-ben", "student-ben", "rubric", None)

    rec = sealing.seal(sealing.draft("student-ben", "attendance", "present"),
                       by="Dana Nguyen", at=AT)
    req = dispositions.ask("student-ben", "fee_waiver", asked_by="guardian-alvarez",
                           asked_at=AT, within=timedelta(days=14),
                           office="bursar", escalates_to="principal")

    cells = (
        ir.cell(serve(attendance, staff, [edge], AT), label="attendance",
                seal=ir.seal_of(rec)),
        ir.cell(serve(medical, staff, [edge], AT), label="medical"),
        ir.cell(serve(medical, stranger, [], AT), label="medical (no edge)"),
        ir.cell(serve(money, staff, [edge], AT), label="fee balance",
                dated=ir.dated_of(req)),
        ir.cell(serve(unclassified, staff, [edge], AT), label="rubric"),
    )
    row = ir.Row("Ben Alvarez — trumpet 2", cells, referent="rehearsal-2026-07-14",
                 lane_id="lane-ben")
    return ir.view("Roster — Tuesday rehearsal", [row], read_by="staff-nguyen", at=AT)


def _every_badge_view():
    """A view carrying every rung on all three ladders, so the parity check is
    made over the whole table rather than the three badges a lane happened to
    produce."""
    cells = tuple(
        ir.Cell(label=lv.prefix, shown=ir.Shown.SERVED, value="sample",
                badges=(ir.Badge(lv),))
        for lv in LEVELS
    )
    return ir.view("Badge legend", [ir.Row("every rung", cells)],
                   read_by="tech", at=AT)


def _renderings(view):
    return {
        "text": render_text(view),
        "tui": render_tui(view, Profile.XTERM256),
        "web": render_web(view),
        "print": render_print(view),
    }


# --- the parity claim -----------------------------------------------------


def test_forced_monochrome_loses_nothing():
    """Every rung, every backend, colour stripped, prefix still there."""
    for view in (_lane_view(), _every_badge_view()):
        found = parity(view, _renderings(view))
        assert found == (), [f"{f.code}: {f.detail}" for f in found]


def test_the_tui_is_the_text_backend_with_colour_added_and_nothing_else():
    """Not a resemblance — an identity. A TUI that built its own lines could
    drift by one field and nothing would notice until a director could not see
    a seal state the export had."""
    view = _lane_view()
    assert strip_colour(render_tui(view, Profile.XTERM256)) == render_text(view)
    assert render_tui(view, Profile.ASCII) == render_text(view)


def test_the_ascii_profile_emits_no_escape_at_all():
    """`TERM=dumb` as a forced condition, not a hope (scout-21 row 8)."""
    out = render_tui(_every_badge_view(), Profile.ASCII)
    assert "\x1b" not in out


def test_the_colour_profile_does_paint_something():
    """A parity test passes trivially if the coloured backend was never
    coloured. This is the control."""
    assert "\x1b[38;5;" in render_tui(_every_badge_view(), Profile.XTERM256)


def test_a_badge_that_drops_its_prefix_is_caught():
    """**The mutation scout-21 §2.2 asks for**, run as a test: a rendering in
    which the badge is colour and nothing else."""
    view = _every_badge_view()
    good = _renderings(view)
    stripped = {name: re.sub(r"\b([LTP][0-9])\b", "", out) for name, out in good.items()}
    found = parity(view, stripped)
    assert found, "a rendering with every prefix removed passed the parity check"
    assert {f.code for f in found} >= {"PREFIX_ABSENT", "SCALE_PREFIX_ABSENT"}


def test_a_badge_that_lies_about_its_own_text_is_caught():
    """The checker re-derives what a badge must read from the one table, so a
    badge object claiming to have rendered something is not believed."""
    class ColourOnlyBadge:
        """A badge that renders as a token name. The forbidden act."""

        def __init__(self, level):
            self.level = level

        @property
        def text(self):
            return self.level.token

    view = _every_badge_view()
    liar = ir.view(view.title, [ir.Row(
        "every rung",
        tuple(ir.Cell(label=c.label, shown=c.shown, value=c.value,
                      badges=(ColourOnlyBadge(c.badges[0].level),))
              for c in view.rows[0].cells))])
    rendering = "\n".join(b.text for b in liar.badges)
    found = parity(liar, {"text": rendering, "web": rendering})
    assert any(f.code == "PREFIX_ABSENT" for f in found), found


def test_a_parity_check_with_nothing_to_compare_is_not_a_pass():
    """`tools/sockets.py`'s vacuous case, in the presentation layer."""
    found = parity(_every_badge_view(), {})
    assert found and found[0].code == "NOTHING_RENDERED"


def test_the_monochrome_backend_is_singled_out():
    """Losing a badge in the text backend is a different finding from losing it
    in a coloured one, because that backend is the floor."""
    view = _every_badge_view()
    rendered = _renderings(view)
    rendered["text"] = rendered["text"].replace("L4 Restricted", "")
    found = parity(view, rendered)
    assert any(f.code == "MONOCHROME_LOSS" for f in found), found


# --- print is a colour mode, not an export --------------------------------


def test_the_printed_document_and_the_screen_document_share_a_body():
    """`scout-21` §2.1: the paper artifact renders through the same provider as
    the screen. The prior art's own `// TODO: Migrate older prints to print
    theme` is what happens when they are two paths."""
    view = _lane_view()
    web, printed = render_web(view), render_print(view)
    assert web != printed
    body_w = web.split("<body>", 1)[1]
    body_p = printed.split("<body>", 1)[1]
    assert body_w == body_p, "the paper lost or gained something the screen has"
    assert 'data-color-mode="print"' in printed
    assert 'data-color-mode="screen"' in web


def test_neither_html_surface_emits_script():
    """§4.2's caveat, in its smallest form: a surface with no script has nothing
    to swap."""
    view = _lane_view()
    for out in (render_web(view), render_print(view)):
        assert "<script" not in out.lower() and "javascript:" not in out.lower()
        assert "onclick" not in out.lower()


def test_a_value_containing_markup_is_escaped():
    """A payload is a student's data, not a template."""
    view = ir.view("t", [ir.Row("r", (ir.Cell(
        label="note", shown=ir.Shown.SERVED, value="<script>alert(1)</script>"),))])
    out = render_web(view)
    assert "<script>" not in out and "&lt;script&gt;" in out


# --- nothing in a backend knows about students ----------------------------


def test_no_surface_imports_the_domain():
    """The division `scout-21` §3 names. A backend that could reach a record
    would be a second read path, and the second one never has the rules."""
    offenders = []
    for py in sorted((ROOT / "surfaces").rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "records":
                        offenders.append(f"{py.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "records":
                    offenders.append(f"{py.name}: from {node.module}")
    assert offenders == [], offenders


def test_the_check_above_would_catch_an_import_if_there_were_one():
    """A scan that has only ever seen clean files is not a scan (rule 19)."""
    tree = ast.parse("from records.serving import serve\nimport records\n")
    hits = [n for n in ast.walk(tree)
            if (isinstance(n, ast.ImportFrom) and (n.module or "").startswith("records"))
            or (isinstance(n, ast.Import)
                and any(a.name.startswith("records") for a in n.names))]
    assert len(hits) == 2


def test_the_domain_knows_about_no_colour():
    """The other direction, and the one that would rot first: a hex or an SGR
    code in `records/` means the ladder is being rendered where it is decided."""
    offenders = []
    for py in sorted((ROOT / "records").rglob("*.py")):
        text = py.read_text(encoding="utf-8")
        if re.search(r"#[0-9a-fA-F]{6}\b", text) or "\\x1b[" in text:
            offenders.append(py.name)
        for word in ("xterm", "ansi_", "rgb("):
            if word in text:
                offenders.append(f"{py.name}: {word}")
    assert offenders == [], offenders


# --- no fleet noun reaches a surface --------------------------------------


def _fleet_hits(text: str):
    return sorted({n for n in FLEET_NOUNS if re.search(rf"\b{n}\b", text)})


def test_no_fleet_noun_reaches_a_rendered_surface():
    """CLAUDE.md: fleet nouns never appear in a string a student, guardian or
    judge can see. A CSS comment is such a string — it is served to the browser
    and travels with the printed stylesheet."""
    view = _lane_view()
    for name, out in _renderings(view).items():
        assert _fleet_hits(out) == [], f"{name}: {_fleet_hits(out)}"
    for artifact in sorted((ROOT / "presentation" / "rendered").iterdir()):
        text = artifact.read_text(encoding="utf-8")
        assert _fleet_hits(text) == [], f"{artifact.name}: {_fleet_hits(text)}"


def test_no_fleet_noun_is_in_the_palette_or_the_one_table():
    """The two places a noun would enter a rendering without anyone rendering
    it deliberately: a token name and a rung's word."""
    text = (ROOT / "presentation" / "tokens.yaml").read_text(encoding="utf-8")
    assert _fleet_hits(text) == []
    for lv in LEVELS:
        assert _fleet_hits(lv.text) == []


def test_the_fleet_noun_check_can_fail():
    assert _fleet_hits("served by the Grove bridge") == ["Grove"]
    assert _fleet_hits("honest, safest, nested") == [], "the check matches substrings"


# --- the doors are on `ls` ------------------------------------------------


def test_four_doors_and_each_one_renders():
    """`scout-21` §3: the layout should make the four doors visible on `ls`."""
    doors = sorted(p.name for p in (ROOT / "surfaces").iterdir()
                   if p.is_dir() and not p.name.startswith(("_", ".")))
    assert doors == ["print", "text", "tui", "web"]
    view = _lane_view()
    for name, out in _renderings(view).items():
        assert out.strip(), f"the {name} door rendered nothing"


def test_every_state_a_cell_can_be_in_reaches_the_surface():
    """A parity claim made over a view with no refusal in it would not have
    checked the case that matters."""
    view = _lane_view()
    shown = {c.shown for row in view.rows for c in row.cells}
    assert shown == set(ir.Shown), sorted(s.value for s in shown)
    out = render_text(view)
    assert ir.REFUSED_TEXT in out and ir.UNKNOWN_TEXT in out


def test_the_read_is_narrated_even_when_nobody_said_who():
    """§7.2. A view that cannot say who is reading it says `unknown` rather
    than dropping the line, because a missing narration and an anonymous read
    are different facts."""
    out = render_text(ir.view("t", []))
    assert "read by unknown at unknown" in out


def test_the_module_is_not_broken_shut():
    assert isinstance(Finding("X", "y").code, str)
    assert "L3 Attributed" in render_text(_lane_view())


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
