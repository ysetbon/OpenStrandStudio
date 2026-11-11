"""openstrand draw: designs from cords given as points, x(t)/y(t) curves or shapes.

Every worked example in the drawing guide is built here too, so the guide the
agent learns from can never hold a design that does not draw.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openstrand import check, draw, project  # noqa: E402

GUIDE = ROOT / ".claude" / "skills" / "openstrand-designer" / "drawing.md"


# ------------------------------------------------------------ expressions
def test_expressions_compute_with_math_functions():
    f = draw.expression("600 + 95*(sin(t) + 2*sin(2*t)) - abs(-1) + pi**0")
    assert f(t=0) == pytest.approx(600.0)
    assert draw.expression("2*pi", variables=())() == pytest.approx(6.283185307)
    assert draw.expression(42)() == 42.0


@pytest.mark.parametrize("text", [
    "__import__('os').system('echo hi')", "t.real", "(lambda: 1)()", "open('x')", "x + 1",
    "[1, 2][0]", "t if t else 1", "sin(t, key=1)", "'a' * 3", "True + 1",
])
def test_expressions_refuse_anything_but_arithmetic(text):
    with pytest.raises(draw.DrawError):
        draw.expression(text)


def test_yes_no_settings_accept_text_but_not_nonsense():
    assert draw._flag("false", "closed") is False and draw._flag("True", "closed") is True
    assert draw._flag(1, "closed") is True and draw._flag(False, "closed") is False
    with pytest.raises(draw.DrawError, match="true or false"):
        draw._flag("maybe", "closed")
    poly, closed = draw.centerline({"points": [[0, 0], [100, 50], [200, 0]], "closed": "false"}, 0)
    assert closed is False


def test_a_function_called_wrongly_is_a_drawing_error():
    with pytest.raises(draw.DrawError, match="cannot be computed"):
        draw.expression("min(t)")(t=1)


def test_huge_or_undefined_values_fail_fast_with_the_place():
    started = time.monotonic()
    with pytest.raises(draw.DrawError, match="cannot be computed"):
        draw.expression("10**10**10")(t=1)
    assert time.monotonic() - started < 1
    with pytest.raises(draw.DrawError, match="t=0"):
        draw.expression("1/t")(t=0)


# ------------------------------------------------------------- centerlines
@pytest.mark.parametrize("cord, message", [
    ({"points": [[0, 0]]}, "2 to"),
    ({"points": [[0, 0], [0, 0], [10, 10]]}, "the same"),
    ({"x": "t"}, 'both "x" and "y"'),
    ({"x": "t", "y": "t", "t0": 3, "t1": 1}, "t1 must be larger"),
    ({"shape": "star", "center": [0, 0]}, "unknown shape"),
    ({"shape": "circle", "center": [600, 400]}, "radius"),
    ({"points": [[0, 0], [9000, 0]]}, "keep every point"),
    ({"points": [[0, 0], [10, 0]], "shape": "circle"}, "exactly one"),
])
def test_bad_cords_say_what_to_change(cord, message):
    with pytest.raises(draw.DrawError, match=message):
        draw.centerline(cord, 0)


@pytest.mark.parametrize("cords, message", [
    ([{"x": "600", "y": "400", "t1": "2*pi"}], "only 0 px long"),
    ([{"points": [[600, 400], [603, 401]]}], "at least three times"),
    ([{"x": "600+150*cos(t)", "y": "400+150*sin(t)", "t1": "4*pi", "closed": True}], "runs along itself"),
])
def test_degenerate_cords_are_refused_with_a_reason(cords, message):
    with pytest.raises(draw.DrawError, match=message):
        draw.build({"cords": cords})


def test_a_closed_cord_that_crosses_nothing_is_named():
    with pytest.raises(draw.DrawError, match=r"cord 2 \(Lonely\) is closed but crosses nothing"):
        draw.build({"cords": [
            {"points": [[100, 100], [300, 300]]},
            {"shape": "circle", "center": [900, 400], "radius": 100, "label": "Lonely"}]})


def test_drawn_rings_link_and_load_cleanly():
    data, report = draw.build({"cords": [
        {"shape": "circle", "center": [480, 400], "radius": 180, "color": "teal", "label": "Left ring"},
        {"shape": "circle", "center": [720, 400], "radius": 180, "color": "gold", "label": "Right ring"}]})
    assert "2 crossings in all" in report and "conflicts: 0" in report
    assert re.search(r"cord 1 over cord 2", report) and re.search(r"cord 2 over cord 1", report)
    info = project.describe(data)
    assert len(info["sets"]) == 2 and info["masks"] >= 1
    assert set(info["groups"]) == {"Left ring", "Right ring"}
    assert check.problems(data) == []


def test_shallow_crossings_are_reported():
    _, report = draw.build({"cords": [
        {"shape": "heart", "center": [600, 400], "size": 460, "color": "crimson"},
        {"shape": "circle", "center": [600, 330], "radius": 205, "color": "gold"}]})
    assert "shallow crossing" in report


def test_a_second_color_that_cannot_be_placed_is_reported():
    data, report = draw.build({"cords": [{
        "x": "600 + 330*cos(t)/(1 + sin(t)**2)", "y": "400 + 330*sin(t)*cos(t)/(1 + sin(t)**2)",
        "t1": "2*pi", "closed": True, "color": "rose", "second_color": "violet"}]})
    assert "stayed one color" in report


def test_the_draw_command_writes_a_project_and_a_report(tmp_path):
    spec = tmp_path / "rings.json"
    spec.write_text(json.dumps({"cords": [
        {"shape": "circle", "center": [480, 400], "radius": 180},
        {"shape": "circle", "center": [720, 400], "radius": 180}]}), encoding="utf-8")
    out = tmp_path / "rings.out.json"
    result = subprocess.run([sys.executable, "-m", "openstrand", "draw", str(spec), "--out", str(out)],
                            cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("wrote") and "crossings in all" in result.stdout
    assert len(project.describe(project.read(out))["sets"]) == 2


# ------------------------------------------------------ over and under by hand
PRETZEL = [[420, 640], [500, 420], [640, 300], [760, 360], [740, 480], [600, 520],
           [460, 480], [440, 360], [560, 300], [700, 420], [780, 640]]
HOOKED = [{"points": [[200, 400], [1000, 400]], "color": "teal"},
          {"points": [[400, 250], [600, 520], [800, 250]], "color": "gold"}]


def knot_of(data):
    from openstrand import identify
    return identify.cords(data)[0]["knot"]


def patterns(report):
    return re.findall(r"^cord \d+ .*, pattern ([OU]+)$", report, re.M)


@pytest.mark.parametrize("pattern, knot", [
    ("OUOUOU", "trefoil"), ("UOUOUO", "trefoil"),      # over and under in turn: an overhand knot, either hand
    ("UUOOOU", "unknot"),                              # its first crossing the other way round: it slips free
    ("O-----", "trefoil"), ("ou ou ou", "trefoil"), ("O,U,O,U,O,U", "trefoil")])
def test_a_pattern_says_which_part_is_on_top_at_each_crossing(pattern, knot):
    data, report = draw.build({"cords": [{"points": PRETZEL, "pattern": pattern, "width": 26}]})
    assert knot_of(data) == knot
    letters = [ch for ch in pattern.upper() if ch in "OU-"]
    drawn = patterns(report)[0]
    assert all(want in ("-", got) for want, got in zip(letters, drawn))
    assert "conflicts: 0" in report and "mask check: no problems" in report
    assert check.problems(data) == []


def test_the_report_lists_each_cords_crossings_in_order_and_its_pattern_draws_the_same_again():
    data, report = draw.build({"cords": HOOKED})
    assert patterns(report) == ["OU", "UO"]                 # the same two crossings, seen from each cord
    assert "cord 1 passes, from its start: 1 over cord 2 (" in report and "2 under cord 2 (" in report
    assert "cord 2 passes, from its start: 1 under cord 1 (" in report
    assert "to turn a crossing the other way" in report
    # Fed back, the patterns give the same design; one letter changed turns that crossing over, and only it.
    again, report_2 = draw.build({"cords": [dict(HOOKED[0], pattern="OU"), dict(HOOKED[1], pattern="UO")]})
    assert patterns(report_2) == ["OU", "UO"]
    turned, report_3 = draw.build({"cords": [dict(HOOKED[0], pattern="UU"), HOOKED[1]]})
    assert patterns(report_3) == ["UU", "OO"] and report_3.count("cord 2 over cord 1") == 2
    crossings = lambda r: sorted(re.findall(r"crossing at \((\d+), (\d+)\)", r))
    assert crossings(report) == crossings(report_2) == crossings(report_3)


def test_one_cords_pattern_is_enough_and_a_dash_leaves_a_crossing_to_the_other():
    said_by_two, report = draw.build({"cords": [dict(HOOKED[0], pattern="U-"), dict(HOOKED[1], pattern="-O")]})
    assert patterns(report) == ["UU", "OO"]
    left_to_weave, report = draw.build({"cords": [dict(HOOKED[0], pattern="U-"), HOOKED[1]]})
    assert patterns(report)[0][0] == "U" and "conflicts: 0" in report


def test_a_closed_cord_takes_a_pattern_from_the_point_it_is_drawn_from():
    rings = [{"shape": "circle", "center": [480, 400], "radius": 180, "color": "teal"},
             {"shape": "circle", "center": [720, 400], "radius": 180, "color": "gold"}]
    linked, report = draw.build({"cords": rings})
    first = patterns(report)[0]
    assert first in ("OU", "UO")
    # The link the other way round: the first ring's two letters swapped.
    other = first[::-1]
    turned, report = draw.build({"cords": [dict(rings[0], pattern=other), rings[1]]})
    assert patterns(report)[0] == other and "conflicts: 0" in report and check.problems(turned) == []
    # Over at both crossings, a closed cord has nowhere to hide its join: said plainly.
    with pytest.raises(draw.DrawError, match="cord 1 is closed and goes over at every crossing it passes"):
        draw.build({"cords": [dict(rings[0], pattern="OO"), rings[1]]})
    # A closed cord that crosses itself: the trefoil's own pattern, whichever crossing its join hides under.
    trefoil = {"x": "600 + 95*(sin(t) + 2*sin(2*t))", "y": "400 + 95*(cos(t) - 2*cos(2*t))", "t1": "2*pi",
               "closed": True, "width": 28}
    _, report = draw.build({"cords": [trefoil]})
    as_drawn = patterns(report)[0]
    assert as_drawn in ("OUOUOU", "UOUOUO")
    other = "".join("U" if ch == "O" else "O" for ch in as_drawn)
    _, report = draw.build({"cords": [dict(trefoil, pattern=other)]})
    assert patterns(report)[0] == other


@pytest.mark.parametrize("cords, message", [
    ([{"points": PRETZEL, "pattern": "OUOU"}],
     r"cord 1 passes 6 crossings but its pattern has 4 letters \(a crossing of the cord with itself is passed "
     r"twice.*Its crossings in order from its start: 1 itself at \(\d+, \d+\); 2 itself"),
    ([{"points": PRETZEL, "pattern": "OOUUOU"}], r"letters 2 and 5 of its pattern are both O"),
    ([{"points": PRETZEL, "pattern": "OUOXOU"}], r'has "X" in it'),
    ([{"points": PRETZEL, "pattern": 7}], r'"pattern" is text such as "OUUO"'),
    ([dict(HOOKED[0], pattern="OU"), dict(HOOKED[1], pattern="OO")],
     r"is letter 1 of cord 1's pattern \(O\) and letter 1 of cord 2's \(O\): one cord goes over"),
    ([dict(HOOKED[0], pattern="O"), HOOKED[1]],
     r"cord 1 passes 2 crossings but its pattern has 1 letter\. Its crossings in order from its start: "
     r"1 cord 2 at \(\d+, \d+\); 2 cord 2 at"),
    ([{"points": [[300, 300], [500, 400], [700, 500]], "heights": [0, 1, 0], "pattern": "O"},
      {"points": [[300, 500], [500, 400], [700, 300]]}], r'give "pattern" or "heights", not both'),
])
def test_a_pattern_that_does_not_fit_says_what_to_change(cords, message):
    with pytest.raises(draw.DrawError, match=message):
        draw.build({"cords": cords})


def test_a_design_without_a_pattern_is_woven_as_before():
    data, report = draw.build({"cords": [{"points": PRETZEL, "width": 26}]})
    assert patterns(report) == ["OUOUOU"] and "mask check" not in report
    assert knot_of(data) == "trefoil"


def guide_examples():
    text = GUIDE.read_text(encoding="utf-8")
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S) if '"cords"' in block]


@pytest.mark.parametrize("spec", guide_examples(), ids=lambda s: s.get("name") or str(len(s["cords"])))
def test_every_example_in_the_drawing_guide_draws_without_conflicts(spec):
    data, report = draw.build(spec)
    assert "conflicts: 0" in report, report
    assert check.problems(data) == []
