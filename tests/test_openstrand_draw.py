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


def guide_examples():
    text = GUIDE.read_text(encoding="utf-8")
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S) if '"cords"' in block]


@pytest.mark.parametrize("spec", guide_examples(), ids=lambda s: s.get("name") or str(len(s["cords"])))
def test_every_example_in_the_drawing_guide_draws_without_conflicts(spec):
    data, report = draw.build(spec)
    assert "conflicts: 0" in report, report
    assert check.problems(data) == []
