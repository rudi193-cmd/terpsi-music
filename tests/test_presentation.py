"""The middle: the one mapping table, the palette, the IR, and render-and-diff.

Rule 19 throughout — every guard below is pointed at the forbidden act and the
refusal is asserted, not the happy path. `tests/ablate.py` carries the other
half: each of these guards is mutated in the source and this file has to notice.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from presentation import ir, render, scales, tokens  # noqa: E402
from presentation.scales import Scale, UNNAMED  # noqa: E402
from presentation.tokens import TokenError  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Outcome, Serving  # noqa: E402

AT = datetime(2026, 7, 14, 15, 30, tzinfo=timezone.utc)


def _palette():
    return tokens.load()


# --- rule 14: prefixes always, and never a bare integer -------------------


def test_a_bare_integer_is_refused_by_type_not_parsed():
    """`level(3)` is the idiom rule 14 exists to stop. Answering it correctly
    would be worse than failing: it would make the rule a convention again.

    **The message is asserted, not only the exception.** Ablation found this
    test passing with the numeric branch removed, because the *"not a rung
    prefix"* fallback also raises `TypeError` — a guard proven by a second
    guard, which is not proof of either. The refusal has to name the rule it is
    refusing on, or a reader gets a type error and a shrug.
    """
    for bare in (3, 0, 1.0, True):
        try:
            scales.level(bare)
        except TypeError as exc:
            assert "bare number" in str(exc) and "rule 14" in str(exc), str(exc)
            continue
        raise AssertionError(f"level({bare!r}) returned a rung for a bare number")


def test_a_stringified_integer_is_refused_too():
    for bare in ("3", "0", ""):
        try:
            scales.level(bare)
        except ValueError:
            continue
        raise AssertionError(f"level({bare!r}) resolved without a scale prefix")


def test_the_domains_own_rung_type_is_accepted():
    """A `Rung` already carries its scale, so it needs no prefix string — and
    accepting it is what keeps callers from stringifying one by hand."""
    assert scales.level(Rung.L4).prefix == "L4"
    assert scales.level(Rung.L4) is scales.level("L4")


def test_two_levels_do_not_compare_with_an_operator():
    """The same structural refusal `records/rungs.py` makes, one layer out: a
    rendering table that could sort its own rungs would be a second ordering."""
    a, b = scales.level("L1"), scales.level("L5")
    for op, sym in ((lambda x, y: x < y, "<"), (lambda x, y: x > y, ">"),
                    (lambda x, y: x <= y, "<="), (lambda x, y: x >= y, ">=")):
        try:
            op(a, b)
        except TypeError:
            continue
        raise AssertionError(f"L1 {sym} L5 did not raise")


def test_every_badge_carries_its_prefix_and_no_two_read_alike():
    """The whole forced-monochrome guarantee in two assertions."""
    seen = set()
    for lv in scales.LEVELS:
        assert lv.text.startswith(lv.prefix + " "), f"{lv.text!r} has no prefix"
        assert lv.text not in seen, f"{lv.text!r} appears twice; colour is the difference"
        seen.add(lv.text)
    assert len(seen) == len(scales.LEVELS)


def test_the_three_prefixes_do_not_collide_across_scales():
    """`level()` takes a prefix and nothing else, which is only safe while the
    three ladders share no key."""
    assert len({lv.prefix for lv in scales.LEVELS}) == len(scales.LEVELS)


# --- rule 13: an unverified name is not rendered as a verified one --------


def test_the_middle_trust_rungs_are_not_given_invented_names():
    """§15 names only `T0` Exiled and `T4` Elder, and `docs/SENSITIVITY.md`
    records that Rookie/Steady/Veteran *"has not been checked."* Rendering an
    unverified name as though it were verified is `P2` decay wearing a badge."""
    middle = [lv for lv in scales.of_scale(Scale.TRUST) if lv.prefix in ("T1", "T2", "T3")]
    assert len(middle) == 3
    for lv in middle:
        assert lv.word is None
        assert lv.text == f"{lv.prefix} {UNNAMED}"
    assert scales.level("T0").word == "Exiled" and scales.level("T4").word == "Elder"


def test_the_unreconciled_scale_is_declared_rather_than_assumed_clean():
    """`drift()` cannot check the trust ladder — its owner is outside this
    repository. Saying so is the difference between a gap and a hole."""
    assert Scale.TRUST in scales.UNRECONCILED
    assert Scale.SENSITIVITY not in scales.UNRECONCILED
    assert Scale.PROVENANCE not in scales.UNRECONCILED


# --- rule 12: the named middle between this table and the domain's ladders -


def test_the_table_agrees_with_the_domain_today():
    assert scales.drift() == (), f"the rendering table has drifted: {scales.drift()}"


def test_drift_notices_a_reordered_sensitivity_ladder():
    """The forbidden act: a table that renders `L1` with more caution than
    `L5`. Nothing in the badge would look wrong; the printed program would."""
    real = scales.LEVELS
    try:
        rows = list(real)
        l_rows = [r for r in rows if r.scale is Scale.SENSITIVITY]
        flipped = tuple(r for r in rows if r.scale is not Scale.SENSITIVITY) + \
            tuple(reversed(l_rows))
        scales.LEVELS = flipped
        found = scales.drift()
        assert found, "a reversed sensitivity ladder produced no finding"
        assert any("more restricted" in f for f in found), found
    finally:
        scales.LEVELS = real


def test_drift_notices_a_provenance_row_that_is_not_in_the_domain():
    real = scales.LEVELS
    try:
        scales.LEVELS = tuple(r for r in real if r.prefix != "P3")
        found = scales.drift()
        assert any("provenance rows" in f for f in found), found
    finally:
        scales.LEVELS = real


def test_drift_notices_a_token_that_does_not_match_its_weight():
    real = scales.LEVELS
    try:
        scales.LEVELS = tuple(
            scales.Level(r.scale, r.prefix, r.word, "caution_0", r.weight)
            if r.prefix == "L5" else r for r in real)
        assert any("L5 names caution_0" in f for f in scales.drift())
    finally:
        scales.LEVELS = real


# --- the direction hazard (§15, scout-21 §2.5) ----------------------------


def test_emphasis_is_caution_and_the_two_ladders_run_opposite():
    """If `L5` and `T4` were both the heaviest thing on the page a reader would
    learn the wrong reflex. The heaviest rung on each ladder is the one to slow
    down at, which makes trust run opposite to its own ordinal."""
    assert scales.heaviest(Scale.SENSITIVITY).prefix == "L5"
    assert scales.heaviest(Scale.TRUST).prefix == "T0"
    assert scales.heaviest(Scale.PROVENANCE).prefix == "P5"
    trust = scales.of_scale(Scale.TRUST)
    assert [lv.weight for lv in trust] == [4, 3, 2, 1, 0], (
        "the trust ladder's emphasis follows its ordinal; it must invert"
    )


# --- the palette, and the parser that refuses what it cannot read ---------


def test_the_committed_palette_loads():
    pal = _palette()
    assert pal.version and len(pal.tokens) >= len(tokens.LADDER)


def test_the_ladder_is_monotonic_in_luminance():
    """The property that survives greyscale, print, protanopia and TERM=dumb."""
    pal = _palette()
    lums = [pal.tokens[n].luminance for n in tokens.LADDER]
    assert lums == sorted(lums, reverse=True) and len(set(lums)) == len(lums)


def test_a_repaint_that_flattens_the_ladder_is_refused():
    """Two rungs at one luminance are one rung in greyscale."""
    text = (ROOT / "presentation" / "tokens.yaml").read_text(encoding="utf-8")
    flat = text.replace('"#c9d2da"', '"#f4f6f8"')
    assert flat != text
    try:
        tokens.parse(flat)
    except TokenError as exc:
        assert "monotonic" in str(exc)
        return
    raise AssertionError("a flattened ladder loaded")


def test_the_parser_names_the_construct_it_will_not_guess_at():
    """**Refused by name, and ablation is why the name is asserted.** Every
    construct below eventually failed the load anyway — as *"not a block"*, or
    as a ladder with a missing rung — so the test passed with the refusal
    removed. A palette that fails to load for the wrong stated reason sends its
    author to the wrong line."""
    cases = {
        "an inline list": 'version: v\ntokens:\n  caution_0:\n    hex: [1, 2]\naliases:\n',
        "flow style": "version: v\ntokens:\n  caution_0: {hex: 1}\naliases:\n",
        "an anchor": "version: v\ntokens:\n  caution_0: &a\naliases:\n",
        "a block scalar": "version: v\ntokens:\n  caution_0: |\naliases:\n",
    }
    for what, text in cases.items():
        try:
            tokens.parse(text)
        except TokenError as exc:
            assert "does not implement" in str(exc), f"{what}: {exc}"
            continue
        raise AssertionError(f"{what} was accepted")


def test_a_tab_is_refused_as_a_tab():
    """Without this the tab is not an error at all: `\\t` is not a space, so the
    line reads as indent zero and a token quietly becomes a top-level key."""
    try:
        tokens.parse("version: v\ntokens:\n\tcaution_0:\naliases:\n")
    except TokenError as exc:
        assert "tab" in str(exc), str(exc)
        return
    raise AssertionError("a tab-indented palette loaded")


def test_the_parser_refuses_the_rest_of_what_it_cannot_read():
    cases = {
        "an unterminated quote": 'version: "v\ntokens:\naliases:\n',
        "a bare line": "version: v\nnonsense\ntokens:\naliases:\n",
        "an odd indent": "version: v\ntokens:\n   caution_0:\naliases:\n",
        "a key with no value": "version:\ntokens:\naliases:\n",
    }
    for what, text in cases.items():
        try:
            tokens.parse(text)
        except TokenError:
            continue
        raise AssertionError(f"{what} was accepted")


def test_a_duplicate_token_is_refused_rather_than_silently_winning():
    text = ("version: v\ntokens:\n"
            "  caution_0:\n    hex: \"#ffffff\"\n    xterm256: 1\n    mono: \".\"\n"
            "  caution_0:\n    hex: \"#000000\"\n    xterm256: 2\n    mono: \"#\"\n"
            "aliases:\n")
    try:
        tokens.parse(text)
    except TokenError as exc:
        assert "twice" in str(exc)
        return
    raise AssertionError("a palette with two definitions of one token loaded")


def test_a_token_missing_a_channel_is_refused():
    """A backend missing one of the three has to render something."""
    text = ("version: v\ntokens:\n  caution_0:\n    hex: \"#ffffff\"\n"
            "aliases:\n")
    try:
        tokens.parse(text)
    except TokenError as exc:
        assert "xterm256" in str(exc) and "mono" in str(exc)
        return
    raise AssertionError("a token with no ASCII fill and no terminal colour loaded")


def test_defining_an_alias_is_refused_and_the_error_names_the_canonical_token():
    """§15's rule from the design system: aliases resolve at lookup, never at
    definition, and the refusal has to say where to make the change instead."""
    text = (ROOT / "presentation" / "tokens.yaml").read_text(encoding="utf-8")
    broken = text.replace("  page_paper:", "  refusal:\n    hex: \"#ff0000\"\n"
                          "    xterm256: 9\n    mono: \"!\"\n  page_paper:")
    try:
        tokens.parse(broken)
    except TokenError as exc:
        assert "refusal" in str(exc) and "caution_4" in str(exc)
        return
    raise AssertionError("an alias was defined as a token")


def test_an_alias_moves_with_the_token_it_names():
    """A skin that repaints `caution_4` moves the refusal badge and the
    `P5 Assumed` badge with it, and neither hardcodes the other's colour."""
    pal = _palette()
    assert pal.resolve("refusal") is pal.resolve("caution_4")
    assert pal.resolve("assumed") is pal.resolve("caution_4")
    repainted = tokens.Palette(
        pal.version,
        dict(pal.tokens, caution_4=tokens.Token("caution_4", "#123456", 17, "%")),
        pal.aliases)
    assert repainted.resolve("refusal").hex == "#123456"
    assert repainted.resolve("assumed").hex == "#123456"


def test_a_missing_palette_is_not_a_default_one():
    try:
        tokens.load(Path("/nonexistent/tokens.yaml"))
    except TokenError:
        return
    raise AssertionError("a missing palette loaded as something")


# --- render-and-diff: the named middle for the template/rendered pair -----


def test_the_committed_output_matches_its_templates_today():
    drifts = render.check()
    assert drifts == (), "\n".join(d.diff for d in drifts)


def test_a_repaint_that_is_not_regenerated_shows_as_drift():
    """The forbidden act `--check` exists for: move a token, commit the palette,
    leave the four rendered files behind."""
    pal = _palette()
    repainted = tokens.Palette(
        pal.version,
        dict(pal.tokens, caution_2=tokens.Token("caution_2", "#8fa0af", 246, "-")),
        pal.aliases)
    fresh = render.outputs(repainted)
    committed = {p.name: p.read_text(encoding="utf-8")
                 for p in (ROOT / "presentation" / "rendered").iterdir()}
    assert fresh != committed, "a repainted token produced identical output"


def test_an_unknown_template_variable_raises_rather_than_rendering_empty():
    """A stylesheet missing one rung of a five-rung ladder still looks like a
    stylesheet."""
    try:
        render.render("a {{nope}} b", {"levels": []})
    except render.TemplateError as exc:
        assert "nope" in str(exc)
        return
    raise AssertionError("an unknown variable rendered as something")


def test_a_nested_section_is_refused_as_a_nested_section():
    """Named, because the leftover-braces check catches it too and a test that
    accepted either was proving the wrong guard (found by ablation)."""
    try:
        render.render("{{#levels}}{{#levels}}y{{/levels}}{{/levels}}",
                      {"levels": [{"x": 1}]})
    except render.TemplateError as exc:
        assert "nested" in str(exc), str(exc)
        return
    raise AssertionError("a nested section rendered")


def test_an_unclosed_construct_is_refused():
    try:
        render.render("{{#levels}}x", {"levels": [{"x": 1}]})
    except render.TemplateError:
        return
    raise AssertionError("an unclosed section rendered")


def test_every_backend_has_a_committed_artifact():
    """Four doors, four rendered files. A backend whose artifact was never
    committed is a backend `--check` cannot protect."""
    rendered = {p.name for p in (ROOT / "presentation" / "rendered").iterdir()}
    templates = {p.name for p in (ROOT / "presentation" / "templates").iterdir()}
    assert rendered == templates == set(render.outputs())
    assert len(rendered) == 4, sorted(rendered)


# --- the IR: absence never renders as a result ---------------------------


def _serving(outcome, value, rung=Rung.L3, provenance="P1"):
    return Serving(outcome, value, rung, "because", provenance=provenance)


def test_an_unknown_decision_renders_the_word_and_never_a_blank():
    c = ir.cell(_serving(Outcome.UNKNOWN, None, rung=None, provenance=None),
                label="rubric")
    assert c.shown is ir.Shown.UNKNOWN
    assert c.value == "unknown" and c.value.strip()
    assert c.badges == (), "an unclassified field was given a rung to render"


def test_a_refusal_renders_one_fixed_string():
    c = ir.cell(_serving(Outcome.REFUSED, None), label="medical")
    assert c.value == ir.REFUSED_TEXT


def test_a_refusal_carrying_a_value_is_refused_by_the_ir():
    """The leak that would make §7's indistinguishability guarantee decorative."""
    for outcome in (Outcome.REFUSED, Outcome.UNKNOWN):
        try:
            ir.cell(_serving(outcome, "the diagnosis"), label="medical")
        except ValueError:
            continue
        raise AssertionError(f"{outcome} rendered a payload")


def test_a_served_decision_with_nothing_to_serve_is_refused():
    """Two guards stand here — `cell()` refuses the decision and `Cell` refuses
    the constructed row — and each is asserted by its own message, because
    ablation showed each of them passing on the strength of the other."""
    for outcome in (Outcome.PAYLOAD, Outcome.INSTRUCTION):
        try:
            ir.cell(_serving(outcome, None), label="attendance")
        except ValueError as exc:
            assert "predicate decided to serve" in str(exc), str(exc)
            continue
        raise AssertionError(f"{outcome} with no value rendered as absence")


def test_a_cell_built_by_hand_with_an_empty_value_is_refused():
    """The second guard, reached directly. A surface assembling its own row is
    the path that skips `cell()` entirely."""
    for shown in (ir.Shown.SERVED, ir.Shown.DERIVED):
        try:
            ir.Cell(label="attendance", shown=shown, value="")
        except ValueError as exc:
            assert "nothing to show" in str(exc), str(exc)
            continue
        raise AssertionError(f"a {shown.value} cell with an empty value was built")


def test_a_cell_that_renders_absence_as_a_result_is_refused():
    """*"A rubric that failed to load returns 'unavailable,' not 'no
    findings.'"* Rule 13, at the last place before a human reads it."""
    for pretending in ("no findings", "none", "", "clear"):
        try:
            ir.Cell(label="rubric", shown=ir.Shown.UNKNOWN, value=pretending)
        except ValueError as exc:
            assert "rule 13" in str(exc), str(exc)
            continue
        raise AssertionError(f"an unknown cell rendered as {pretending!r}")


def test_a_bespoke_refusal_text_is_refused():
    """A refusal that varies with what was refused is a side channel."""
    try:
        ir.Cell(label="medical", shown=ir.Shown.REFUSED, value="no medical record")
    except ValueError:
        return
    raise AssertionError("a refusal said more than the fixed string")


def test_a_cell_with_no_state_is_refused():
    try:
        ir.Cell(label="x", shown="served", value="y")
    except ValueError:
        return
    raise AssertionError("a cell with a string for a state was built")


def test_the_rung_badge_comes_from_the_decision_not_from_the_caller():
    c = ir.cell(_serving(Outcome.PAYLOAD, "present", rung=Rung.L4), label="medical")
    assert [b.text for b in c.badges] == ["L4 Restricted", "P1 Measured"]


def test_a_seal_state_carries_the_name_and_the_date():
    """§15: the seal says whether a person stood behind it; without the name it
    is a status, not evidence."""
    from records import sealing
    rec = sealing.seal(sealing.draft("student-ben", "commentary", "body"),
                       by="Dana Nguyen", at=AT)
    seal = ir.seal_of(rec)
    assert "Dana Nguyen" in seal.text and "2026-07-14" in seal.text


def test_an_open_disposition_renders_its_clock():
    """Rule 15: silence is not an answer, which only means something if the
    reader can see the date it stops being silence."""
    from records import dispositions
    req = dispositions.ask("student-ben", "fee_waiver", asked_by="guardian",
                           asked_at=AT, within=timedelta(days=14),
                           office="bursar", escalates_to="principal")
    assert ir.dated_of(req).text == "open, due 2026-07-28"


def test_the_module_is_not_broken_shut():
    pal = _palette()
    assert scales.level("L3").text == "L3 Attributed"
    assert pal.resolve("caution_0").mono == "."
    assert ir.cell(_serving(Outcome.PAYLOAD, "present"), label="attendance").value == "present"
    with tempfile.TemporaryDirectory():
        pass


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
