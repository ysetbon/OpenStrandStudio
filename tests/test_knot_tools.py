"""Knot tools: knot types from crossings, the cord simulation, over/under from
heights, tying steps, and reading a knot back from a design.

The judge throughout is the knot itself: every stage of every knot is checked
by its Alexander polynomial, worked out exactly from the crossings, and the
finished designs are read back from their strands the way the app draws them.
"""
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_knot_test_")

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "scripts", ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from openstrand import draw, identify, invariants, simulate, tying  # noqa: E402

W = 26
# A loose overhand knot, standing end on the left (the classic pretzel).
PRETZEL = [[150, 640], [420, 640], [500, 420], [640, 300], [760, 360], [740, 480], [600, 520], [460, 480],
           [440, 360], [560, 300], [700, 420], [780, 640], [1050, 640]]
FIGURE_8 = [[200, 200], [380, 260], [560, 380], [620, 540], [520, 660], [400, 600], [420, 450], [560, 320],
            [600, 180], [480, 120], [400, 220], [480, 420], [640, 560], [820, 620]]
ALEXANDER = {"overhand": (1, -1, 1), "figure-eight": (1, -3, 1), "double overhand": (2, -3, 2),
             "stevedore": (2, -5, 2), "triple overhand": (3, -5, 3)}


def dense(points):
    from sample_geometry import spline
    return np.array(spline(points, spacing=4.0))


def laid(points, pattern):
    poly = dense(points)
    z, _ = simulate.heights_from_pattern(poly, pattern, W)
    return np.c_[poly, z]


# ------------------------------------------------------------ invariants
def test_the_knot_type_comes_from_the_crossings():
    assert invariants.describe(laid(PRETZEL, "OUOUOU"))["knot"] == "trefoil"
    assert invariants.describe(laid(FIGURE_8, "OUOUOUOU"))["knot"] == "figure-eight"
    # The mirror image is the same knot type; one crossing the other way round undoes the knot.
    assert invariants.alexander(laid(PRETZEL, "UOUOUO")) == (1, -1, 1)
    assert invariants.describe(laid(PRETZEL, "UUOOOU"))["knot"] == "unknot"   # first crossing flipped
    circle = np.array([[600 + 200 * math.cos(t), 400 + 200 * math.sin(t), 0.0]
                       for t in np.linspace(0, 2 * math.pi, 200, endpoint=False)])
    assert invariants.alexander(circle, closed=True) == (1,)


def test_a_closed_torus_knot_is_named_from_its_heights():
    t = np.linspace(0, 2 * math.pi, 600, endpoint=False)
    r = 200 + 80 * np.cos(5 * t)
    cinquefoil = np.c_[600 + r * np.cos(2 * t), 400 + r * np.sin(2 * t), 80 * np.sin(5 * t)]
    found = invariants.describe(cinquefoil, closed=True)
    assert (found["crossings"], found["alexander"], found["knot"]) == (5, (1, -1, 1, -1, 1), "cinquefoil")


def test_crossings_say_which_part_is_on_top():
    a = np.array([[0, 0, 5], [100, 100, 5]], dtype=float)
    b = np.array([[0, 100, -5], [100, 0, -5]], dtype=float)
    (x,) = invariants.crossings([a, b])
    assert x["point"] == pytest.approx((50, 50)) and x["over"] == 0 and x["angle"] == pytest.approx(90)


# ------------------------------------------------------------ simulation
def test_the_pattern_must_give_every_crossing_one_over_and_one_under():
    poly = dense(PRETZEL)
    with pytest.raises(simulate.SimulationError, match="pattern has 4 letters"):
        simulate.heights_from_pattern(poly, "OUOU", W)
    with pytest.raises(simulate.SimulationError, match="one pass must go over"):
        simulate.heights_from_pattern(poly, "OOUUOU", W)


def test_pulling_an_overhand_tight_keeps_the_knot_and_jams():
    started = time.monotonic()
    loose = laid(PRETZEL, "OUOUOU")
    (tight,), info = simulate.tighten([loose], W, [(0, 0, (-1, 0)), (0, 1, (1, 0))])
    assert time.monotonic() - started < 30
    assert info["jammed"] and info["retries"] <= 3
    assert invariants.describe(tight)["knot"] == "trefoil"
    assert len(info["crossings"]) == 3 and all(c["over"] is not None for c in info["crossings"])
    assert info["overlap"] < 0.1                 # parts never sink into each other
    assert info["clearance"] >= 0.9              # side by side, not on top of each other
    assert info["end_length"] < 0.7 * info["start_length"]
    # Every stage in between is the same knot too.
    for _, (cord,) in info["history"][::10]:
        assert invariants.alexander(cord) == (1, -1, 1)
    # The knot is compact: its crossings sit within a few cord widths.
    points = np.array([c["point"] for c in info["crossings"]])
    assert np.ptp(points, axis=0).max() < 4 * W


def test_a_rough_layout_is_laid_out_evenly_as_the_same_knot():
    rough = laid(tying.plat_layout(tying.LIBRARY["stevedore"]["word"], W), "OU" * 6)
    (loose,), info = simulate.tighten([rough], W * 2.6, [(0, 0, (-1, 0)), (0, 1, (1, 0))], grow_from=W)
    assert invariants.alexander(loose) == ALEXANDER["stevedore"]
    assert info["clearance"] >= 0.9 and info["overlap"] < 0.1   # parts 2.6 widths apart, evenly


def test_the_crossing_code_notices_a_different_knot():
    rope = simulate.Rope([laid(PRETZEL, "OUOUOU")], W)
    assert rope.code_matches()
    other = simulate.Rope([laid(FIGURE_8, "OUOUOUOU")], W)
    other.reference = rope.reference
    assert not other.code_matches()


# --------------------------------------------------------------- drawing
def crossing_cords(top):
    heights = ([0, 30, 0], [0, -30, 0]) if top == 1 else ([0, -30, 0], [0, 30, 0])
    return {"cords": [{"points": [[300, 300], [500, 400], [700, 500]], "heights": heights[0]},
                      {"points": [[300, 500], [500, 400], [700, 300]], "heights": heights[1]}]}


@pytest.mark.parametrize("top", [1, 2])
def test_heights_decide_which_cord_is_on_top(top):
    data, report = draw.build(crossing_cords(top))
    under = 3 - top
    assert f"cord {top} over cord {under}" in report


def test_heights_must_match_the_points():
    spec = crossing_cords(1)
    spec["cords"][0]["heights"] = [0, 1]
    with pytest.raises(draw.DrawError, match="one number per point"):
        draw.build(spec)


def test_every_design_carries_the_curve_settings_it_was_fitted_for():
    from save_load_manager import load_strands_from_data
    from project_settings import apply_project_settings
    data, _ = draw.build(crossing_cords(1))
    assert data["project_settings"] == {"version": 1, "control_point_base_fraction": 1.0,
                                        "distance_multiplier": 2.0, "curve_response_exponent": 2.0}
    # Someone with other curve settings opens it: the block switches them first.
    canvas = SimpleNamespace(control_point_base_fraction=0.2, distance_multiplier=1.0, curve_response_exponent=3.0,
                             default_shadow_color=None, shadow_enabled=False, _suppress_repaint=True,
                             update=lambda: None, selected_strand=None, strands=[])
    apply_project_settings(canvas, data["project_settings"])
    loaded, *_ = load_strands_from_data(data, canvas)
    assert {(s.control_point_base_fraction, s.distance_multiplier, s.curve_response_exponent)
            for s in loaded if hasattr(s, "distance_multiplier")} == {(1.0, 2.0, 2.0)}


def test_a_tight_knot_still_fits_closely(monkeypatch):
    (tight,), _ = simulate.tighten([laid(PRETZEL, "OUOUOU")], W, [(0, 0, (-1, 0)), (0, 1, (1, 0))])
    errors = []
    real = draw.fit_error

    def spy(scene):
        errors.append(real(scene))
        return errors[-1]
    monkeypatch.setattr(draw, "fit_error", spy)
    data, report = draw.build(tying.design(tying._trimmed(tight, W), W, "teal", "tight overhand"))
    assert errors[-1] <= draw.FIT_LIMIT                  # the strands follow the simulated cord
    assert "3 crossings in all" in report and "touch without crossing" not in report
    assert identify.cords(data)[0]["knot"] == "trefoil"


def test_a_fit_that_strays_is_tried_again_with_joins_nearer_crossings(monkeypatch):
    rooms = []

    def strays_at_first(scene):
        rooms.append(scene.cords[0]["join_room"])
        return 50.0 if len(rooms) == 1 else 1.0
    monkeypatch.setattr(draw, "fit_error", strays_at_first)
    draw.build(crossing_cords(1))
    assert rooms == [1.0, draw.JOIN_ROOM[1]]


# ---------------------------------------------------------------- tying
@pytest.mark.parametrize("name, key", [
    ("Figure 8", "figure-eight"), ("figure of eight knot", "figure-eight"), ("FLEMISH", "figure-eight"),
    ("thumb knot", "overhand"), ("Overhand", "overhand"), ("double overhand knot", "double overhand"),
    ("stevedore stopper", "stevedore"), ("Triple-Overhand", "triple overhand"), ("bowline", None)])
def test_knots_are_found_by_the_names_people_use(name, key):
    assert tying.find(name) == key


@pytest.mark.parametrize("key", list(tying.LIBRARY))
def test_every_library_layout_and_shipped_shape_is_its_knot(key):
    word = tying.LIBRARY[key]["word"]
    rough = laid(tying.plat_layout(word, W), "OU" * len(word))
    assert invariants.describe(rough)["crossings"] == len(word)
    assert invariants.alexander(rough) == ALEXANDER[key]
    loose, snug, tight = tying.library_shapes(key, W)
    for cord in (loose, snug, tight):
        assert invariants.alexander(cord) == ALEXANDER[key]
    spread = lambda c: np.ptp(np.array([x["point"] for x in invariants.crossings([c])]), axis=0).max()
    assert spread(tight) < spread(snug) < spread(loose)


def test_a_plat_that_makes_two_cords_is_refused():
    with pytest.raises(tying.TyingError, match="link"):
        tying.plat_layout((2, 2, 1))


def arrows(data):
    return [s for s in data["strands"] if s.get("end_arrow_visible") or s.get("start_arrow_visible")]


def test_tying_steps_are_checked_and_the_working_end_has_an_arrow():
    made = tying.tie("figure-eight", color="#3366aa")
    assert made["ok"] and made["knot"] == "figure-eight" and made["crossings"] == 4
    steps = made["steps"]
    assert [s["title"] for s in steps] == [f"Step {n}" for n in range(1, 7)]
    assert all(s["caption"].endswith(".") for s in steps)
    stages = [c["stage"] for c in made["checks"]]
    assert stages[:3] == ["laid out", "drawn up", "pulled tight"] and len(stages) == 6
    for n, step in enumerate(steps, start=1):
        data = step["data"]
        assert data["project_settings"]["version"] == 1
        found = identify.cords(data)
        assert len(found) == 1
        if n <= 3:
            assert len(arrows(data)) == 1                  # where the end goes next
            assert found[0]["knot"] == "unknot"            # not through yet: it would slip free
            assert found[0]["crossings"] == n
        else:
            assert not arrows(data)
            assert found[0]["knot"] == "figure-eight"
    sizes = [np.ptp([[s["start"]["x"], s["start"]["y"]] for s in st["data"]["strands"]
                     if s["type"] != "MaskedStrand"], axis=0).max() for st in steps[3:]]
    assert sizes[0] > sizes[1] > sizes[2]                  # laid out, drawn up, tight


@pytest.mark.parametrize("key", ["overhand", "double overhand", "stevedore", "triple overhand"])
def test_every_library_knot_ties_and_reads_back_as_itself(key):
    made = tying.tie(key, width=20)
    assert made["ok"], made["checks"]
    assert identify.cords(made["steps"][-1]["data"])[0]["alexander"] == ALEXANDER[key]
    assert 4 <= len(made["steps"]) <= tying.MAX_MOVES + 2


def test_a_knot_given_as_a_path_is_named_and_tied():
    made = tying.tie(points=PRETZEL, color="gold", count=2)
    assert made["ok"] and made["knot"] == "trefoil" and made["title"] == "Overhand knot (3_1)"
    assert len(made["steps"]) == 4 and made["checks"][0]["stage"] == "as drawn"
    with pytest.raises(tying.TyingError, match="not the knot asked for"):
        tying.tie(points=PRETZEL, expect=(1, -3, 1), build=False)


def test_tying_says_what_is_wrong():
    with pytest.raises(tying.TyingError, match="not in the knot library"):
        tying.tie("bowline")
    with pytest.raises(tying.TyingError, match="never crosses itself"):
        tying.tie(points=[[100, 400], [400, 380], [700, 420], [1000, 400]], build=False)
    with pytest.raises(tying.TyingError, match="width"):
        tying.tie("overhand", width=100)


# ----------------------------------------------------------------- agent
def test_the_agent_ties_a_knot_and_checks_it(tmp_path):
    from openstrand.agent import Agent, PLAN_TOOLS, TOOLS, Workspace
    ws = Workspace(tmp_path)
    summary, text = ws.run("knot_library", {})
    assert summary == "5 knots" and "Stevedore knot" in text and "figure 8" in text
    summary, text = ws.run("tie_knot", {"knot": "overhand", "color": "gold"})
    assert summary == "Overhand knot · 5 steps"
    assert "pulled tight: trefoil" in text and "step 5 as drawn in the app: trefoil" in text
    assert "WARNING" not in text
    assert [t for t, _ in ws.steps] == [f"Step {n}" for n in range(1, 6)]
    assert all(p.exists() for _, p in ws.steps)
    summary, text = ws.run("identify_knot", {})
    assert "3 crossings with itself: overhand knot (3_1)" in text
    names = {t["name"] for t in TOOLS}
    assert {"tie_knot", "knot_library", "identify_knot"} <= names
    assert {"knot_library", "identify_knot"} <= set(PLAN_TOOLS) and "tie_knot" not in PLAN_TOOLS


def test_the_agent_is_told_to_tie_knots_with_the_tool():
    from openstrand.agent import INSTRUCTIONS
    from openstrand.app_tools import APP_INSTRUCTIONS
    assert "never draw tying steps or a tightened knot by hand" in INSTRUCTIONS
    assert "identify_knot" in INSTRUCTIONS and "tie_knot" in APP_INSTRUCTIONS


# ------------------------------------------------------------------- cli
def test_the_command_ties_lists_and_identifies(tmp_path):
    import subprocess
    run = lambda *a: subprocess.run([sys.executable, "-m", "openstrand", *a], cwd=ROOT, capture_output=True,
                                    text=True, timeout=600)
    listed = run("tie", "--list")
    assert listed.returncode == 0 and "stevedore" in listed.stdout and "figure 8" in listed.stdout
    made = run("tie", "overhand", "--color", "gold", "--out-dir", str(tmp_path))
    assert made.returncode == 0, made.stderr
    assert "checks: laid out: trefoil" in made.stdout
    files = sorted(tmp_path.glob("overhand_knot_step_*.json"))
    assert len(files) == 5
    named = run("identify", str(files[-1]))
    assert "3 crossings with itself: overhand knot (3_1)" in named.stdout
    wrong = run("tie", "bowline")
    assert wrong.returncode == 1 and "not in the knot library" in wrong.stderr


def test_the_knot_in_a_design_is_tied_as_drawn(tmp_path):
    from openstrand.agent import ToolError, Workspace
    drawn, _ = draw.build({"cords": [{"points": FIGURE_8, "width": 26, "color": "crimson"}]})
    ws = Workspace(tmp_path)
    ws.store(drawn)
    summary, text = ws.run("tie_knot", {"from_design": True})
    assert "as drawn: figure-eight" in text and "pulled tight: figure-eight" in text and "WARNING" not in text
    assert len(ws.steps) == 6
    rings, _ = draw.build({"cords": [{"shape": "circle", "center": [480, 400], "radius": 180},
                                     {"shape": "circle", "center": [720, 400], "radius": 180}]})
    ws.store(rings)
    with pytest.raises(ToolError, match="2 cords"):
        ws.run("tie_knot", {"from_design": True})
