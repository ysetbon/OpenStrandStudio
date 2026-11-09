"""Mask tools: check_masks finds where a mask paints the wrong thing, edit_mask
fixes it with the app's own code, and tie_knot does the safe fixes itself.

The designs in tests/mask_tools/:
- three_cords: three cords crossing close together (draw.build, the design's
  over and under kept), 3_1 on top of both others. Its layers were put in
  the order that plants the problem: 3_1 lowest, lifted by masks 3_1_1_1 and
  3_1_2_1, and mask 1_1_2_1 drawn after them, so its piece paints 1_1 over
  3_1 right where 3_1 should show;
- tight_overhand, tight_triple_overhand, tight_figure_eight,
  drawn_up_triple_overhand: library knots as tie_knot draws them
  (tying.tie(key), the pulled-tight and drawn-up steps) before any fix. In the overhand and the triple overhand, crossings are
  split by a joint (part of a crossing shows the strand that should be
  under); the figure-eight has no mask problem, and its one mask, 1_1_1_7,
  checks reset, swap, delete and create.

Every result is read back the way the app reads it: loaded with
load_strands_from_data (masks.Design), named by identify, and, for the fix,
looked at in a real render of the app (AppPreview) at the place it fixed.
"""
import re
import copy
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_mask_tools_"))

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from openstrand import identify, masks, project  # noqa: E402

DESIGNS = Path(__file__).resolve().parent / "mask_tools"
THREE = DESIGNS / "three_cords.json"
OVERHAND = DESIGNS / "tight_overhand.json"
DRAWN_UP = DESIGNS / "drawn_up_triple_overhand.json"
TRIPLE = DESIGNS / "tight_triple_overhand.json"
EIGHT = DESIGNS / "tight_figure_eight.json"


def load(path):
    return project.read(path)


def planted(report):
    """The problem planted in three_cords: mask 1_1_2_1 over strand 3_1."""
    found = [p for p in report["problems"] if p["kind"] == "covers_strand"
             and p["mask"] == "1_1_2_1" and p["strand"] == "3_1"]
    return found[0] if found else None


def knot(data):
    found = identify.cords(data)
    assert len(found) == 1
    return found[0]["knot"]


# ------------------------------------------------------------- check_masks
def test_check_masks_lists_every_mask_and_finds_the_planted_problem():
    report = masks.check(load(THREE))
    assert [m["name"] for m in report["masks"]] == ["3_1_1_1", "3_1_2_1", "1_1_2_1"]
    entry = report["masks"][-1]
    assert entry["on_top"] == "1_1" and entry["under"] == "2_1" and entry["boxes"] == []
    assert entry["crossings"] == 1 and entry["centre"] is not None
    problem = planted(report)
    assert problem is not None, report["text"]
    # Located with coordinates, with the mask that lifts 3_1 there, and its fix.
    x, y = problem["at"]
    assert abs(x - 600) < 10 and abs(y - 400) < 10 and problem["area"] > 300
    assert problem["via"] == "3_1_2_1"
    assert problem["fix"] == {"op": "erase", "mask": "1_1_2_1"}
    assert "mask 1_1_2_1 paints over strand 3_1" in report["text"]
    assert report["intent"] == ["design"]  # draw.build kept the design's over and under
    # The same place is a crossing drawn the other way round from the design.
    assert any(p["kind"] == "wrong_crossing" and p["shows"] == "1_1" and p["should_show"] == "3_1"
               for p in report["problems"])


def test_a_crossing_split_by_a_joint_is_found_in_a_tight_knot():
    report = masks.check(load(OVERHAND))
    assert len(report["masks"]) == 1
    split = [p for p in report["problems"] if p["kind"] == "wrong_way"]
    assert [tuple(round(v) for v in p["at"]) for p in split] == [(579, 380)]
    assert split and all(p["source"] == "design" and len(p["at"]) == 2 and p["should_show"] for p in split)
    assert all(p["text"].startswith("part of the crossing shows the wrong strand on top at (") for p in split)


def test_a_clean_tight_knot_has_no_mask_problem():
    report = masks.check(load(EIGHT))
    assert report["problems"] == [] and "no mask problems" in report["text"]
    assert [m["name"] for m in report["masks"]] == ["1_1_1_7"]


def test_a_mask_lifting_the_wrong_strand_is_a_wrong_crossing():
    data, done = masks.edit(load(EIGHT), "swap", mask="1_1_1_7")
    kinds = {p["kind"] for p in masks.check(data)["problems"]}
    assert "wrong_crossing" in kinds


def test_a_mask_over_two_crossings_with_one_the_other_way_is_found():
    # Plant it: in three_cords, cords 1 and 3 cross once; a second cord 1
    # crossing back under 3 would be the second crossing. Instead use the
    # mask list: each mask counts the crossings its piece covers.
    data = load(THREE)
    data, _ = masks.edit(data, "delete", mask="3_1_1_1")
    data, _ = masks.edit(data, "create", first="1_1", second="3_1")
    report = masks.check(data)
    assert any(p["kind"] in ("wrong_crossing", "wrong_way") and p["should_show"] == "3_1" for p in report["problems"])


# --------------------------------------------------------------- edit_mask
def appearance(data, point, colors):
    """The colour the app paints at a canvas point, in a real render with the
    strands given their own colours and no shadows."""
    from openstrand import generators
    generators.application()
    from generate_creative_samples import AppPreview
    from PyQt5.QtGui import QImage
    data = copy.deepcopy(data)
    data["shadow_enabled"] = False
    for s in data["strands"]:
        if s["type"] != "MaskedStrand" and s["layer_name"] in colors:
            r, g, b = colors[s["layer_name"]]
            s["color"] = {"r": r, "g": g, "b": b, "a": 255}
    data["strand_colors"] = {}
    preview = AppPreview()
    try:
        out = Path(tempfile.mkdtemp()) / "render.png"
        preview.capture(data, out)
        canvas = preview.window.canvas
        bounds = canvas.get_bounding_rect()
        zoom = canvas.zoom_factor
        sx = canvas.width() / 2 + zoom * (point[0] - bounds.center().x())
        sy = canvas.height() / 2 + zoom * (point[1] - bounds.center().y())
        image = QImage(str(out))
        c = image.pixelColor(int(round(sx)), int(round(sy)))
        return c.red(), c.green(), c.blue()
    finally:
        preview.close()


def inside(problem_region, analysis):
    """A canvas point well inside a problem's region."""
    rows, cols = problem_region
    r, c = np.median(rows), np.median(cols)
    k = int(np.argmin((rows - r) ** 2 + (cols - c) ** 2))
    return analysis.scene.window.canvas(cols[k], rows[k])


def close(a, b, tolerance=40):
    return all(abs(x - y) <= tolerance for x, y in zip(a, b))


def test_erase_where_a_mask_covers_a_strand_fixes_it_in_the_app():
    data = load(THREE)
    analysis = masks.Analysis(data)
    problem = next(p for p in analysis.problems() if p["kind"] == "covers_strand"
                   and p["mask"] == "1_1_2_1" and p["strand"] == "3_1")
    point = inside(problem["fix"]["region"], analysis)
    fixed, done = masks.edit(data, "erase", mask="1_1_2_1", covers="3_1")
    assert done.startswith("erased mask 1_1_2_1 with")
    # Read back as the app loads it: the mask keeps the boxes, by their corners.
    reloaded = masks.Design(fixed)
    boxes = reloaded.mask("1_1_2_1").deletion_rectangles
    assert boxes and all(set(b) >= {"top_left", "top_right", "bottom_left", "bottom_right"} for b in boxes)
    report = masks.check(fixed)
    assert planted(report) is None and report["problems"] == [], report["text"]
    # identify reads every crossing as the design has it: 3_1 over both.
    found = identify.cords(fixed)
    assert [c["with_others"] for c in found] == [2, 2, 2]
    # In the app's own render, the place now shows 3_1, not 1_1.
    colors = {"3_1": (40, 180, 60), "1_1": (220, 40, 200), "2_1": (40, 80, 220)}
    before = appearance(data, point, colors)
    after = appearance(fixed, point, colors)
    assert close(before, colors["1_1"]), before
    assert close(after, colors["3_1"]), after


def test_erase_around_a_crossing_then_reset():
    data = load(EIGHT)
    centre = next(m for m in masks.check(data)["masks"] if m["name"] == "1_1_1_7")["centre"]
    erased, done = masks.edit(data, "erase", mask="1_1_1_7", around=centre)
    assert masks.Design(erased).mask("1_1_1_7").deletion_rectangles
    # Its piece gone, the crossing shows the layer order: 1_7 on top, against the design.
    assert {p["kind"] for p in masks.check(erased)["problems"]} & {"wrong_crossing", "wrong_way"}
    assert knot(erased) != "figure-eight"
    back, done = masks.edit(erased, "reset", mask="1_1_1_7")
    assert "erase box" in done and masks.Design(back).mask("1_1_1_7").deletion_rectangles == []
    assert masks.check(back)["problems"] == [] and knot(back) == "figure-eight"


def test_erase_at_a_problem_takes_out_just_that_place():
    fixed, done = masks.edit(load(THREE), "erase", mask="1_1_2_1", at=[600, 400])
    assert masks.check(fixed)["problems"] == []
    with pytest.raises(masks.MaskError, match="has no problem at"):
        masks.edit(load(THREE), "erase", mask="1_1_2_1", at=[300, 300])
    # Where an erase would cut into the rest of the piece, the check does not
    # offer one and the edit says so, rather than leave a straight cut.
    report = masks.check(load(DRAWN_UP))
    place = next(p for p in report["problems"] if p.get("mask") == "1_13_1_6")
    assert place["fix"] is None and "No single mask edit fixes it cleanly" in place["text"]
    with pytest.raises(masks.MaskError, match="without cutting into the rest"):
        masks.edit(load(DRAWN_UP), "erase", mask="1_13_1_6", at=place["at"])


def test_a_new_mask_is_trimmed_where_it_would_paint_the_wrong_way():
    data = load(OVERHAND)
    report = masks.check(data)
    split = next(p for p in report["problems"] if (p.get("fix") or {}).get("op") == "create")
    assert split["fix"] == {"op": "create", "first": "1_3", "second": "1_6"} and split["source"] == "design"
    made, done = masks.edit(data, "create", first="1_3", second="1_6")
    assert done.startswith("made mask 1_3_1_6: 1_3 over 1_6; erased it with")
    assert masks.check(made)["problems"] == []
    assert knot(made) == "trefoil"
    untrimmed, done = masks.edit(data, "create", first="1_3", second="1_6", trim=False)
    assert done == "made mask 1_3_1_6: 1_3 over 1_6"
    assert any(p["kind"] == "wrong_crossing" for p in masks.check(untrimmed)["problems"])


def test_swap_delete_and_create_do_what_they_say():
    data = load(EIGHT)
    swapped, done = masks.edit(data, "swap", mask="1_1_1_7")
    design = masks.Design(swapped)
    assert [m.layer_name for m in design.masks()] == ["1_7_1_1"]
    assert design.mask("1_7_1_1").first_selected_strand.layer_name == "1_7"
    assert knot(swapped) != "figure-eight"
    again, _ = masks.edit(swapped, "swap", mask="1_7_1_1")
    assert knot(again) == "figure-eight" and masks.check(again)["problems"] == []

    gone, done = masks.edit(data, "delete", mask="1_1_1_7")
    assert done == "deleted mask 1_1_1_7" and masks.Design(gone).masks() == []
    assert knot(gone) != "figure-eight"
    made, done = masks.edit(gone, "create", first="1_1", second="1_7")
    assert [m.layer_name for m in masks.Design(made).masks()] == ["1_1_1_7"]
    assert knot(made) == "figure-eight" and masks.check(made)["problems"] == []
    with pytest.raises(masks.MaskError, match="already have mask"):
        masks.edit(made, "create", first="1_7", second="1_1")
    with pytest.raises(masks.MaskError, match="do not overlap"):
        masks.edit(gone, "create", first="1_1", second="1_8")
    with pytest.raises(masks.MaskError, match="there is no mask"):
        masks.edit(data, "reset", mask="9_9_9_9")


def test_an_erase_box_can_be_given_by_its_corners():
    data = load(EIGHT)
    box = [[590, 370], [610, 365], [615, 385], [595, 390]]
    erased, _ = masks.edit(data, "erase", mask="1_1_1_7", box=box)
    stored = masks.Design(erased).mask("1_1_1_7").deletion_rectangles[0]
    assert [list(stored[k]) for k in ("top_left", "top_right", "bottom_right", "bottom_left")] == box
    erased, _ = masks.edit(data, "erase", mask="1_1_1_7", box=[590, 370, 610, 390])
    assert list(masks.Design(erased).mask("1_1_1_7").deletion_rectangles[0]["bottom_right"]) == [610, 390]


def test_repair_fixes_what_is_safe_and_says_what_is_left():
    data = load(THREE)
    fixed, done, left = masks.repair(data)
    assert len(done) == 1 and done[0].startswith("erased mask 1_1_2_1 at (600, 400) where it hid 3_1")
    assert left == [] and masks.check(fixed)["problems"] == []
    # A tight knot: no erase fixes it cleanly, so it is left, located, for Claude...
    data = load(OVERHAND)
    fixed, done, left = masks.repair(data)
    assert done == [] and [tuple(round(v) for v in p["at"]) for p in left] == [(579, 380)]
    assert all("region" not in p and "region" not in (p.get("fix") or {}) for p in left)
    # ...unless new masks may be made from the design's own over and under.
    fixed, done, left = masks.repair(data, create_masks=True)
    assert done[0].startswith("made mask 1_3_1_6 (1_3 over 1_6)") and left == []
    assert knot(fixed) == "trefoil"


# ----------------------------------------------------------------- tying
def test_tie_knot_checks_the_masks_of_its_finished_steps():
    from openstrand import tying
    made = tying.tie("triple overhand")
    assert made["ok"]
    tight, drawn_up = made["steps"][-1], made["steps"][-2]
    assert tight["masks"] is not None and "fixed" in tight["masks"]
    assert drawn_up["masks"]["left"], "the drawn-up triple overhand keeps one place no edit fixes cleanly"
    assert all(len(p["at"]) == 2 and p["text"] for p in drawn_up["masks"]["left"])
    assert made["steps"][0]["masks"] is None  # the first moves are loose: nothing to check


# ----------------------------------------------------------------- agent
def test_the_agent_checks_and_edits_masks(tmp_path):
    from openstrand.agent import PLAN_TOOLS, TOOLS, ToolError, Workspace
    ws = Workspace(tmp_path)
    ws.store(load(THREE))
    summary, text = ws.run("check_masks", {})
    assert summary.startswith("3 masks") and "mask 1_1_2_1 paints over strand 3_1" in text
    version = ws.version
    summary, text = ws.run("edit_mask", {"op": "erase", "mask": "1_1_2_1", "covers": "3_1", "preview": True})
    assert summary.startswith("Preview") and "Preview, not kept" in text and ws.version == version
    summary, text = ws.run("edit_mask", {"op": "erase", "mask": "1_1_2_1", "covers": "3_1"})
    assert ws.version == version + 1 and "Knot: cord 1" in text and "no mask problems" in text
    assert planted(masks.check(project.read(ws.project_path))) is None
    with pytest.raises(ToolError, match="op is one of"):
        ws.run("edit_mask", {"op": "paint"})
    assert "check_masks" in PLAN_TOOLS and "edit_mask" not in PLAN_TOOLS
    assert {"check_masks", "edit_mask"} <= {t["name"] for t in TOOLS}


def test_tie_knot_tells_claude_what_it_fixed_and_what_is_left(tmp_path):
    from openstrand.agent import INSTRUCTIONS, Workspace
    from openstrand.app_tools import APP_INSTRUCTIONS
    ws = Workspace(tmp_path)
    summary, text = ws.run("tie_knot", {"knot": "triple overhand"})
    assert "masks left: part of the crossing shows the wrong strand on top at (" in text
    assert "crowded crossing" not in text
    assert "check_masks" in INSTRUCTIONS and "edit_mask" in INSTRUCTIONS
    assert "check_masks" in APP_INSTRUCTIONS and "edit_mask_in_tab" in APP_INSTRUCTIONS
    assert "stretched MxN" in INSTRUCTIONS


def test_edit_mask_in_tab_sends_the_boxes_it_worked_out(tmp_path):
    from openstrand import agent
    from openstrand.agent import ToolError
    calls = []
    app = SimpleNamespace(call=lambda name, args: calls.append((name, args)) or {"note": "erased"})
    runner = agent.Agent(SimpleNamespace(), tmp_path, app=app)
    with pytest.raises(ToolError, match="read_tab"):
        runner.app_tool("edit_mask_in_tab", {"tab_id": "t1", "op": "reset", "mask": "1_1_2_1"})
    runner.workspace.store(load(THREE), tab="t1")
    summary, text = runner.app_tool("edit_mask_in_tab", {"tab_id": "t1", "op": "erase", "mask": "1_1_2_1",
                                                         "covers": "3_1"})
    name, args = calls[-1]
    assert name == "edit_mask" and args["op"] == "erase" and args["mask"] == "1_1_2_1"
    assert args["boxes"] and all(len(b["top_left"]) == 2 for b in args["boxes"])
    assert "one undo step" in text and runner.workspace.tab == "t1"
    assert planted(masks.check(runner.workspace.data)) is None


# ------------------------------------------------------------------- cli
def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "openstrand", *args], cwd=ROOT, capture_output=True,
                          text=True, timeout=600)


def test_the_masks_and_edit_mask_commands(tmp_path):
    copy_ = tmp_path / "three.json"
    copy_.write_text(THREE.read_text(encoding="utf-8"), encoding="utf-8")
    listed = run_cli("masks", str(copy_))
    assert listed.returncode == 0, listed.stderr
    assert "3 masks:" in listed.stdout and "mask 1_1_2_1 paints over strand 3_1" in listed.stdout
    as_json = json.loads(run_cli("masks", str(copy_), "--json").stdout)
    assert len(as_json["masks"]) == 3 and as_json["problems"]
    preview = run_cli("edit-mask", str(copy_), "erase", "--mask", "1_1_2_1", "--covers", "3_1", "--preview")
    assert preview.returncode == 0 and "preview (nothing written)" in preview.stdout
    assert copy_.read_text(encoding="utf-8") == THREE.read_text(encoding="utf-8")
    out = tmp_path / "fixed.json"
    done = run_cli("edit-mask", str(copy_), "erase", "--mask", "1_1_2_1", "--covers", "3_1", "--out", str(out))
    assert done.returncode == 0 and "no mask problems" in done.stdout
    assert planted(masks.check(project.read(out))) is None
    repaired = run_cli("masks", str(copy_), "--repair", "--out", str(tmp_path / "repaired.json"))
    assert repaired.returncode == 0 and "fixed: erased mask 1_1_2_1" in repaired.stdout
    swapped = run_cli("edit-mask", str(copy_), "swap", "--mask", "1_1_2_1", "--preview")
    assert swapped.returncode == 0 and "now 2_1_1_1" in swapped.stdout
    wrong = run_cli("edit-mask", str(copy_), "reset", "--mask", "nope")
    assert wrong.returncode == 1 and "there is no mask nope" in wrong.stderr


def test_an_edit_leaves_its_input_alone_and_keeps_the_rest_of_the_project():
    data = load(EIGHT)
    data["shadow_enabled"] = False
    data["show_control_points"] = True
    data["something_else"] = {"kept": True}
    names = [s["layer_name"] for s in data["strands"]]
    data["locked_layers"] = [names.index("1_3"), names.index("1_1_1_7")]
    data["level_count"] = 1
    for s in data["strands"]:
        if s["layer_name"] in ("1_2", "1_3"):
            s["level"] = 1
    before = json.dumps(data, sort_keys=True)
    erased, _ = masks.edit(data, "erase", mask="1_1_1_7", box=[590, 370, 610, 390])
    swapped, _ = masks.edit(erased, "swap", mask="1_1_1_7")
    assert json.dumps(data, sort_keys=True) == before          # the input is untouched
    for out in (erased, swapped):
        assert out["shadow_enabled"] is False and out["show_control_points"] is True
        assert out["something_else"] == {"kept": True} and out["level_count"] == 1
        assert out["groups"] == data["groups"] and out["design_crossings"] == data["design_crossings"]
        levels = {s["layer_name"]: s.get("level") for s in out["strands"]}
        assert levels["1_2"] == 1 and levels["1_3"] == 1
    # Locks follow their layers by name; the swapped mask is a new layer.
    after = [s["layer_name"] for s in erased["strands"]]
    assert sorted(after[i] for i in erased["locked_layers"]) == ["1_1_1_7", "1_3"]
    after = [s["layer_name"] for s in swapped["strands"]]
    assert [after[i] for i in swapped["locked_layers"]] == ["1_3"]
    # A preview through the agent keeps the current design as it was.
    from openstrand.agent import Workspace
    ws = Workspace(Path(tempfile.mkdtemp()))
    ws.store(load(EIGHT))
    kept = json.dumps(ws.data, sort_keys=True)
    ws.run("edit_mask", {"op": "erase", "mask": "1_1_1_7", "box": [590, 370, 610, 390], "preview": True})
    assert json.dumps(ws.data, sort_keys=True) == kept


# --------------------------------------------------------- the app's tab
@pytest.fixture(scope="module")
def window(tmp_path_factory):
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    old_appdata = os.environ.get("APPDATA")
    os.environ["APPDATA"] = str(tmp_path_factory.mktemp("appdata"))
    cwd = os.getcwd()
    os.chdir(ROOT / "src")
    try:
        from main_window import MainWindow
        w = MainWindow()
    finally:
        os.chdir(cwd)
    w.resize(1400, 900)
    w.show()
    app.processEvents()
    yield w
    w._confirm_close_with_dirty_tabs = lambda *a, **k: True
    w.close()
    if old_appdata is None:
        os.environ.pop("APPDATA", None)
    else:
        os.environ["APPDATA"] = old_appdata


def live_mask(window, name):
    return next((s for s in window.canvas.strands if s.layer_name == name and hasattr(s, "get_mask_path")), None)


def test_claude_edits_a_mask_in_the_tab_itself_as_one_undo_step(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QUrl
    from PyQt5.QtWidgets import QApplication
    from openstrand import agent
    from openstrand.app_tools import AppError
    panel, tm = window.claude_panel, window.tab_manager
    bridge = panel.bridge
    run = tmp_path / "run"
    run.mkdir()
    panel.out_dir = str(run)
    design = run / "three.json"
    design.write_text(THREE.read_text(encoding="utf-8"), encoding="utf-8")
    replies = []
    monkeypatch.setattr(panel, "answer", replies.append)
    panel.run_mode = "auto"
    assert bridge.handle({"id": 1, "name": "open_in_new_tab",
                          "args": {"path": str(design), "title": "Three"}})["ok"]
    tab = tm.get_active()
    QApplication.processEvents()

    def call(name, args):          # the agent's AppClient, answered by the real bridge
        reply = bridge.handle({"id": 100, "name": name, "args": args})
        if not reply["ok"]:
            raise AppError(reply["error"])
        return reply["result"]
    runner = agent.Agent(SimpleNamespace(), tmp_path / "out", app=SimpleNamespace(call=call))
    runner.app_tool("read_tab", {"tab_id": tab.id})
    # read_tab carries the tab's curve settings: Claude's copy has the same paths.
    assert runner.workspace.data["project_settings"]["distance_multiplier"] == window.canvas.distance_multiplier
    assert planted(masks.check(runner.workspace.data)) is not None

    summary, text = runner.app_tool("edit_mask_in_tab", {"tab_id": tab.id, "op": "erase", "mask": "1_1_2_1",
                                                         "covers": "3_1"})
    mask = live_mask(window, "1_1_2_1")
    assert mask.deletion_rectangles and summary.startswith("In the tab")
    # The tab now draws what Claude's copy says: nothing hides 3_1 any more.
    # (A tab keeps no "design_crossings": the crossings' own masks say which strand is on top.)
    assert "design_crossings" not in runner.workspace.data
    snapshot = dict(window.claude_canvas_snapshot(), project_settings=runner.workspace.data["project_settings"])
    assert planted(masks.check(snapshot)) is None
    # One undo step takes it back.
    window.canvas.undo_redo_manager.undo()
    QApplication.processEvents()
    assert live_mask(window, "1_1_2_1").deletion_rectangles == []
    window.canvas.undo_redo_manager.redo()
    QApplication.processEvents()
    assert live_mask(window, "1_1_2_1").deletion_rectangles

    # Reset, swap, delete and create, each with the canvas's own code.
    assert bridge.handle({"id": 3, "name": "edit_mask",
                          "args": {"tab_id": tab.id, "op": "reset", "mask": "1_1_2_1"}})["ok"]
    assert live_mask(window, "1_1_2_1").deletion_rectangles == []
    assert bridge.handle({"id": 4, "name": "edit_mask",
                          "args": {"tab_id": tab.id, "op": "swap", "mask": "1_1_2_1"}})["ok"]
    assert live_mask(window, "1_1_2_1") is None and live_mask(window, "2_1_1_1") is not None
    assert bridge.handle({"id": 5, "name": "edit_mask",
                          "args": {"tab_id": tab.id, "op": "delete", "mask": "2_1_1_1"}})["ok"]
    assert live_mask(window, "2_1_1_1") is None
    made = bridge.handle({"id": 6, "name": "edit_mask",
                          "args": {"tab_id": tab.id, "op": "create", "first": "1_1", "second": "2_1"}})
    assert made["ok"] and live_mask(window, "1_1_2_1") is not None
    names = [b.text() for b in window.layer_panel.layer_buttons]
    assert "1_1_2_1" in names and "2_1_1_1" not in names       # the layer panel follows

    # Ask mode: the change waits for the person's Allow or Deny.
    panel.run_mode = "ask"
    box = {"top_left": [590, 390], "top_right": [610, 390], "bottom_right": [610, 410], "bottom_left": [590, 410]}
    assert bridge.handle({"id": 7, "name": "edit_mask", "args": {"tab_id": tab.id, "op": "erase",
                                                                  "mask": "1_1_2_1", "boxes": [box]}}) is None
    confirm = panel.entries[-1]
    assert confirm["kind"] == "confirm" and "change a mask in the tab “Three”" in panel.transcript.toPlainText()
    assert live_mask(window, "1_1_2_1").deletion_rectangles == []
    panel.follow_link(QUrl(f"os:deny/{panel.entries.index(confirm)}"))
    assert not replies[-1]["ok"] and live_mask(window, "1_1_2_1").deletion_rectangles == []
    assert bridge.handle({"id": 8, "name": "edit_mask", "args": {"tab_id": tab.id, "op": "erase",
                                                                  "mask": "1_1_2_1", "boxes": [box]}}) is None
    panel.follow_link(QUrl(f"os:allow/{panel.entries.index(panel.entries[-1])}"))
    assert replies[-1]["ok"] and len(live_mask(window, "1_1_2_1").deletion_rectangles) == 1

    # Plan mode only looks; a bad call says what is wrong; only the tab showing changes.
    panel.run_mode = "plan"
    refused = bridge.handle({"id": 9, "name": "edit_mask",
                             "args": {"tab_id": tab.id, "op": "reset", "mask": "1_1_2_1"}})
    assert not refused["ok"] and "plan mode" in refused["error"]
    panel.run_mode = "auto"
    for args, error in (({"op": "reset", "mask": "nope"}, "no mask nope"),
                        ({"op": "paint", "mask": "1_1_2_1"}, "op is one of"),
                        ({"op": "erase", "mask": "1_1_2_1", "boxes": [[1, 2]]}, "four corners"),
                        ({"op": "create", "first": "1_1", "second": "9_9"}, "no strand 9_9")):
        reply = bridge.handle({"id": 11, "name": "edit_mask", "args": dict(args, tab_id=tab.id)})
        assert not reply["ok"] and error in reply["error"], reply
    other = next(s for s in tm.tabs if s.id != tab.id)
    reply = bridge.handle({"id": 12, "name": "edit_mask", "args": {"tab_id": other.id, "op": "reset",
                                                                    "mask": "1_1_2_1"}})
    assert not reply["ok"] and "switch_tab to it first" in reply["error"]


# ------------------------------------------------------ Claude, end to end
class FakeAPI:
    """A local Messages API, reached through the real SDK. Each request gets
    the reply script(n, body) returns: n counts the requests from 0."""

    def __init__(self, script):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        self.requests = []
        api = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                api.requests.append(body)
                reply = script(len(api.requests) - 1, body)
                out = json.dumps({"id": f"msg_{len(api.requests)}", "type": "message", "role": "assistant",
                                  "model": body["model"], "stop_sequence": None,
                                  "usage": {"input_tokens": 1000, "output_tokens": 100,
                                            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                                  **reply}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def result(self, n):
        """What the tools answered before request n: the text of each result."""
        out = []
        for block in self.requests[n]["messages"][-1]["content"]:
            if block.get("type") == "tool_result":
                content = block.get("content")
                if isinstance(content, list):
                    content = " ".join(b.get("text", f"<{b.get('type')}>") for b in content)
                out.append(str(content))
        return "\n".join(out)

    def close(self):
        self.server.shutdown()


def use(id_, name, **args):
    return {"content": [{"type": "tool_use", "id": id_, "name": name, "input": args}], "stop_reason": "tool_use"}


def say(text):
    return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"}


def test_claude_checks_and_fixes_masks_then_ties_a_tight_knot(tmp_path, monkeypatch):
    """The whole loop through the real SDK and the openstrand agent command,
    from a design with a planted problem: check_masks, a preview, the fix, the
    check again; then tie_knot, a refused edit, a preview and a render."""
    script = [
        use("t1", "check_masks"),
        use("t2", "edit_mask", op="erase", mask="1_1_2_1", at=[600, 400], preview=True),
        use("t3", "edit_mask", op="erase", mask="1_1_2_1", covers="3_1"),
        use("t4", "check_masks"),
        use("t5", "tie_knot", knot="overhand"),
        use("t6", "check_masks"),
        use("t7", "edit_mask", op="create", first="1_3", second="1_6"),
        use("t8", "edit_mask", op="delete", mask="1_3_1_6", preview=True),
        use("t9", "render"),
        say("Fixed the cut red strand, then tied the overhand; one place by a joint is left as it is."),
    ]
    api = FakeAPI(lambda n, body: script[min(n, len(script) - 1)])
    try:
        env = dict(os.environ, ANTHROPIC_API_KEY="sk-ant-test-key", OPENSTRAND_TEST_API=api.url,
                   NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost",
                   APPDATA=str(tmp_path / "appdata"), QT_QPA_PLATFORM="offscreen")
        out = tmp_path / "out"
        run = subprocess.run([sys.executable, "-m", "openstrand", "agent", "the red strand is cut, fix it",
                              "--start", str(THREE), "--model", "haiku", "--no-web", "--out-dir", str(out),
                              "--json-events"],
                             cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
    finally:
        api.close()
    events = [json.loads(line) for line in run.stdout.splitlines() if line.startswith("{")]
    done = events[-1]
    assert run.returncode == 0 and done["type"] == "done" and done["ok"], run.stdout[-3000:] + run.stderr[-3000:]
    # The mask tools were offered, with the instructions to use them.
    offered = {t["name"] for t in api.requests[0]["tools"]}
    assert {"check_masks", "edit_mask", "tie_knot"} <= offered
    system = api.requests[0]["system"][0]["text"]
    assert "After tie_knot (and after drawing or loading anything crowded), call" in system
    # check_masks found the planted problem, with its place and its fix.
    checked = api.result(1)
    assert "3 masks:" in checked and "mask 1_1_2_1 paints over strand 3_1" in checked
    assert "Fix: edit_mask erase, mask 1_1_2_1, covers 3_1." in checked
    preview = api.result(2)
    assert preview.startswith("Preview, not kept: erased mask 1_1_2_1") and "no mask problems" in preview
    fixed = api.result(3)
    assert fixed.startswith("erased mask 1_1_2_1 with") and "now the current design" in fixed
    assert "no mask problems" in api.result(4)
    # tie_knot fixed what was safe in the tight knot and said what is left, with coordinates.
    tied = api.result(5)
    assert "masks fixed: made mask 1_3_1_6 (1_3 over 1_6)" in tied
    assert "crowded crossing" not in tied
    assert "2 masks:" in api.result(6) and "no mask problems" in api.result(6)
    # A wrong edit goes back to Claude as an error; a preview changes nothing.
    refused = api.requests[7]["messages"][-1]["content"][0]
    assert refused["is_error"] and "already have mask 1_3_1_6" in refused["content"]
    preview = api.result(8)
    assert preview.startswith("Preview, not kept: deleted mask 1_3_1_6")
    assert "Fix: edit_mask create, first 1_3, second 1_6." in preview
    assert "<image>" in api.result(9)
    # The design Claude leaves is the tight knot with its fix, as the app loads it.
    final = project.read(out / "design.json")
    assert masks.Design(final).mask("1_3_1_6").deletion_rectangles
    assert knot(final) == "trefoil"
    ends = [(e["name"], e["ok"]) for e in events if e["type"] == "tool_end"]
    assert ends == [("check_masks", True), ("edit_mask", True), ("edit_mask", True), ("check_masks", True),
                    ("tie_knot", True), ("check_masks", True), ("edit_mask", False), ("edit_mask", True),
                    ("render", True)]


def test_claude_fixes_a_mask_in_the_person_s_own_tab(window, monkeypatch, tmp_path):
    """From the app's Claude panel: Claude lists the tabs, reads the one with
    the problem, checks its masks and fixes the mask in that tab itself."""
    import claude_settings
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", model="claude-haiku-5-5", web=False)
    panel, tm = window.claude_panel, window.tab_manager
    # The person's tab: the three cords, a mask hiding 3_1.
    path = tmp_path / "mine.json"
    path.write_text(THREE.read_text(encoding="utf-8"), encoding="utf-8")
    assert window.open_claude_design(str(path))
    mine = tm.get_active()
    tm.changed.emit()
    QApplication.processEvents()

    def script(n, body):
        if n == 0:
            return use("t1", "list_tabs")
        if n == 1:
            tabs = json.loads(body["messages"][-1]["content"][0]["content"])
            active = next(t for t in tabs if t["active"])
            script.tab = active["id"]
            return use("t2", "read_tab", tab_id=active["id"])
        if n == 2:
            return use("t3", "check_masks")
        if n == 3:
            return use("t4", "edit_mask_in_tab", tab_id=script.tab, op="erase", mask="1_1_2_1", covers="3_1")
        return say("Mask 1_1_2_1 no longer covers 3_1 in your tab; Undo puts it back.")
    api = FakeAPI(script)
    monkeypatch.setenv("OPENSTRAND_TEST_API", api.url)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    try:
        panel.set_mode("auto")
        panel.prompt_edit.setText("the red strand is cut where the three cross, fix that mask in my tab")
        panel.send()
        deadline = time.time() + 300
        while panel.running() and time.time() < deadline:
            QApplication.processEvents()
            time.sleep(0.05)
        QApplication.processEvents()
    finally:
        api.close()
    shown = panel.transcript.toPlainText()
    assert "no longer covers 3_1" in shown, shown
    assert script.tab == mine.id and tm.active_tab_id == mine.id
    assert "mask 1_1_2_1 paints over strand 3_1" in api.result(3)
    assert "in the tab (one undo step there)" in api.result(4) and "no mask problems" in api.result(4)
    # The person's own tab changed, in place, through the app's code.
    mask = live_mask(window, "1_1_2_1")
    assert mask is not None and mask.deletion_rectangles
    window.canvas.undo_redo_manager.undo()
    QApplication.processEvents()
    assert live_mask(window, "1_1_2_1").deletion_rectangles == []


def test_claude_reads_the_tab_as_it_is_now_its_history_and_moves_a_strand(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QPointF
    from PyQt5.QtWidgets import QApplication
    from openstrand import agent, project
    from openstrand.app_tools import AppError
    panel, tm, canvas = window.claude_panel, window.tab_manager, window.canvas
    bridge = panel.bridge
    run = tmp_path / "run"
    run.mkdir()
    panel.out_dir = str(run)
    design = run / "overhand.json"
    design.write_text((ROOT / "tests" / "mask_tools" / "tight_overhand.json").read_text(encoding="utf-8"),
                      encoding="utf-8")
    monkeypatch.setattr(panel, "answer", lambda reply: None)
    panel.run_mode = "auto"
    assert bridge.handle({"id": 1, "name": "open_in_new_tab", "args": {"path": str(design), "title": "Overhand"}})["ok"]
    tab = tm.get_active()
    QApplication.processEvents()

    def call(name, args):          # the agent's AppClient, answered by the real bridge
        reply = bridge.handle({"id": 100, "name": name, "args": args})
        if not reply["ok"]:
            raise AppError(reply["error"])
        return reply["result"]
    runner = agent.Agent(SimpleNamespace(), tmp_path / "out", app=SimpleNamespace(call=call))
    listed = next(t for t in call("list_tabs", {})["tabs"] if t["id"] == tab.id)
    assert listed["version"] and "undo_steps" in listed

    # read_tab: the tab as it is now, every strand's points, its version and undo history.
    _, text = runner.app_tool("read_tab", {"tab_id": tab.id})
    ws = runner.workspace
    assert ws.tab_version == listed["version"] and f"version {ws.tab_version}" in text
    assert "undo history (at step" in text and re.search(r"strand 1_\d+: start \[[-\d.]+, [-\d.]+\]", text)
    child = next(s for s in ws.data["strands"] if s.get("attached_to") and s.get("attachment_side") == 1
                 and s.get("type") != "MaskedStrand")
    live = lambda name: next(s for s in canvas.strands if s.layer_name == name and not hasattr(s, "get_mask_path"))
    parent = live(child["attached_to"])
    before_step = canvas.undo_redo_manager.current_step

    # The person moves a handle meanwhile: Claude's edit, worked out on its old copy, is refused.
    assert bridge.handle({"id": 2, "name": "edit_strand", "args": {
        "tab_id": tab.id, "strand": parent.layer_name,
        "points": {"control_point1": [parent.control_point1.x() + 6, parent.control_point1.y()]}}})["ok"]
    end = [parent.end.x() + 9.0, parent.end.y() - 7.0]
    with pytest.raises(AppError, match="changed since you read it"):
        runner.app_tool("edit_strand_in_tab", {"tab_id": tab.id, "strand": parent.layer_name, "points": {"end": end}})
    assert parent.end != QPointF(*end)

    # Read again, then the edit goes through with Move mode's code: the attached strand follows.
    runner.app_tool("read_tab", {"tab_id": tab.id})
    summary, text = runner.app_tool("edit_strand_in_tab", {"tab_id": tab.id, "strand": parent.layer_name,
                                                           "points": {"end": end}})
    assert summary.startswith("In the tab") and "Knot:" in text
    assert abs(parent.end.x() - end[0]) < 0.6 and abs(parent.end.y() - end[1]) < 0.6
    follower = live(child["layer_name"])
    assert abs(follower.start.x() - parent.end.x()) < 0.6 and abs(follower.start.y() - parent.end.y()) < 0.6
    assert ws.tab_version == bridge.version(tab)  # the copy is the tab again
    after_step = canvas.undo_redo_manager.current_step
    assert after_step == before_step + 2  # the person's move and Claude's: one undo step each

    # Past steps: the tab before Claude's edit, read without changing the tab.
    _, text = runner.app_tool("read_tab_step", {"tab_id": tab.id, "step": after_step - 1})
    old = next(s for s in ws.data["strands"] if s["layer_name"] == parent.layer_name)
    assert abs(old["end"]["x"] - (end[0] - 9.0)) < 0.6 and ws.tab is None  # a copy: no tab edits from it
    assert f"undo step {after_step - 1}" in text
    with pytest.raises(agent.ToolError, match="read_tab this tab first"):
        runner.app_tool("edit_strand_in_tab", {"tab_id": tab.id, "strand": parent.layer_name, "points": {"end": end}})
    # Undo: the tab goes back, its version changes, and the undone step can still be read.
    canvas.undo_redo_manager.undo()
    QApplication.processEvents()
    assert call("list_tabs", {})["tabs"][-1]["at_step"] == after_step - 1
    runner.app_tool("read_tab_step", {"tab_id": tab.id, "step": after_step})
    redone = next(s for s in ws.data["strands"] if s["layer_name"] == parent.layer_name)
    assert abs(redone["end"]["x"] - end[0]) < 0.6
    # Bad requests say what is wrong.
    for args, message in [({"points": {"middle": [1, 2]}}, "not a point"), ({"points": {"end": "x"}}, "give"),
                          ({"strand": "9_9", "points": {"end": [1, 2]}}, "no strand 9_9")]:
        reply = bridge.handle({"id": 9, "name": "edit_strand",
                               "args": dict({"tab_id": tab.id, "strand": parent.layer_name}, **args)})
        assert not reply["ok"] and message in reply["error"]


def test_a_strand_edit_ends_like_a_drop_and_the_layer_panel_still_selects(window, monkeypatch, tmp_path):
    """After Claude moved a strand, clicking a layer raised "argument of type 'NoneType' is not
    iterable": the edit left canvas.truly_moving_strands = None where the app expects no attribute
    or a list. An edit must leave the canvas as a mouse release leaves it, the selection included."""
    from PyQt5.QtWidgets import QApplication
    panel, tm, canvas = window.claude_panel, window.tab_manager, window.canvas
    bridge = panel.bridge
    run = tmp_path / "run"
    run.mkdir()
    panel.out_dir = str(run)
    design = run / "overhand.json"
    design.write_text((ROOT / "tests" / "mask_tools" / "tight_overhand.json").read_text(encoding="utf-8"),
                      encoding="utf-8")
    monkeypatch.setattr(panel, "answer", lambda reply: None)
    panel.run_mode = "auto"
    assert bridge.handle({"id": 1, "name": "open_in_new_tab", "args": {"path": str(design), "title": "Fresh"}})["ok"]
    tab = tm.get_active()
    QApplication.processEvents()
    transient = ("truly_moving_strands", "affected_strands_for_drawing", "active_strand_update_rect")
    for name in transient:   # as in an app where nothing has been dragged yet
        if hasattr(canvas, name):
            delattr(canvas, name)
    live = {s.layer_name: s for s in canvas.strands if not hasattr(s, "get_mask_path")}
    index = lambda name: canvas.strands.index(live[name])
    window.layer_panel.select_layer(index("1_2"))   # the person has 1_2 selected
    selected = (canvas.selected_strand, canvas.selected_attached_strand)
    assert live["1_2"] in selected and live["1_2"].is_selected

    def edit(strand, points):
        return bridge.handle({"id": 7, "name": "edit_strand", "args": {
            "tab_id": tab.id, "strand": strand, "points": points, "version": bridge.version(tab)}})

    cp = live["1_6"].control_point1
    assert edit("1_6", {"control_point1": [cp.x() + 5, cp.y() - 4]})["ok"]
    # Nothing a drag leaves behind is left on the canvas, and the selection is the person's.
    for name in transient:
        assert not hasattr(canvas, name), name
    assert (canvas.selected_strand, canvas.selected_attached_strand) == selected
    assert live["1_2"].is_selected and not live["1_6"].is_selected
    assert canvas.move_mode.affected_strand is None and not canvas.move_mode.is_moving
    # The layer panel selects as before (this raised TypeError).
    window.layer_panel.select_layer(index("1_4"))
    assert live["1_4"] in (canvas.selected_strand, canvas.selected_attached_strand)
    canvas.update()
    QApplication.processEvents()   # and the canvas paints

    # A joint moved from the attached strand's side: the parent's end follows it.
    start = live["1_4"].start
    assert edit("1_4", {"start": [start.x() - 6, start.y() + 5]})["ok"]
    assert abs(live["1_3"].end.x() - live["1_4"].start.x()) < 0.6 and abs(live["1_3"].end.y() - live["1_4"].start.y()) < 0.6

    # Move mode's rules: not mid-drag, not a hidden strand, not an end shared with a locked layer.
    canvas.move_mode.is_moving = True
    reply = edit("1_6", {"control_point1": [cp.x(), cp.y()]})
    canvas.move_mode.is_moving = False
    assert not reply["ok"] and "dragging" in reply["error"]
    live["1_5"].is_hidden = True
    reply = edit("1_5", {"control_point1": [cp.x(), cp.y()]})
    live["1_5"].is_hidden = False
    assert not reply["ok"] and "hidden" in reply["error"]
    canvas.move_mode.set_locked_layers({index("1_3")}, True)
    try:
        reply = edit("1_4", {"start": [start.x(), start.y()]})   # 1_4's start is 1_3's end: locked
        assert not reply["ok"] and "cannot move" in reply["error"]
        assert edit("1_4", {"control_point1": [live["1_4"].control_point1.x() + 1,
                                               live["1_4"].control_point1.y()]})["ok"]   # its handles still move
    finally:
        canvas.move_mode.set_locked_layers(set(), False)
