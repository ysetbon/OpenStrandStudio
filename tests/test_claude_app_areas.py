"""Claude's tools for the layer panel's right-click menu and the group panel,
run end to end: the agent's tool, the bridge, the app's own code in a real
window. Each change is checked on the live strands, as one undo step."""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_app_areas_"))

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src", ROOT / "scripts"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

TIGHT = ROOT / "tests" / "mask_tools" / "tight_overhand.json"


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


@pytest.fixture()
def tab(window, monkeypatch, tmp_path):
    """The tight overhand in a new tab, Claude's runner answered by the real bridge, the tab read."""
    from PyQt5.QtWidgets import QApplication
    from openstrand import agent
    from openstrand.app import AppError
    panel = window.claude_panel
    run = tmp_path / "run"
    run.mkdir()
    panel.out_dir = str(run)
    design = run / "overhand.json"
    design.write_text(TIGHT.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(panel, "answer", lambda reply: None)
    panel.run_mode = "auto"
    bridge = panel.bridge
    assert bridge.handle({"id": 1, "name": "open_in_new_tab", "args": {"path": str(design), "title": "Areas"}})["ok"]
    session = window.tab_manager.get_active()
    QApplication.processEvents()

    def call(name, args):          # the agent's AppClient, answered by the real bridge
        reply = bridge.handle({"id": 100, "name": name, "args": args})
        if not reply["ok"]:
            raise AppError(reply["error"])
        return reply["result"]
    runner = agent.Agent(SimpleNamespace(), tmp_path / "out", app=SimpleNamespace(call=call))
    runner.app_tool("read_tab", {"tab_id": session.id})
    return SimpleNamespace(window=window, canvas=window.canvas, bridge=bridge, runner=runner, id=session.id,
                           steps=lambda: window.canvas.undo_redo_manager.current_step)


def live(canvas, name):
    return next(s for s in canvas.strands if s.layer_name == name and not hasattr(s, "get_mask_path"))


def layers(tab, op, names, **more):
    return tab.runner.app_tool("edit_layers_in_tab", dict({"tab_id": tab.id, "layers": names, "op": op}, **more))


def groups(tab, op, group, **more):
    return tab.runner.app_tool("edit_groups_in_tab", dict({"tab_id": tab.id, "op": op, "group": group}, **more))


# ------------------------------------------------------------------ layers
def test_claude_folds_the_start_edge_and_recolors_through_the_layer_menu(tab):
    canvas = tab.canvas
    one = live(canvas, "1_1")
    assert "start edge unfolded" in project_detail(tab)
    before = tab.steps()
    summary, text = layers(tab, "start_edge", ["1_1"], value="fold")
    assert one.start_circle_stroke_color.alpha() == 255 and tab.steps() == before + 1
    assert "folded over the start edge of 1_1" in text and "start edge folded" in project_detail(tab)
    # Gold for the whole set, as Change Color does: every layer of set 1.
    layers(tab, "color", ["1_1"], value="gold")
    assert {s.color.name() for s in canvas.strands if s.layer_name.startswith("1_") and not hasattr(s, "get_mask_path")} \
        == {"#e5a13b"}
    # This layer only, with alpha.
    layers(tab, "color", ["1_4"], value="#257d9880", scope="layer")
    assert live(canvas, "1_4").color.name() == "#257d98" and live(canvas, "1_4").color.alpha() == 0x80
    assert live(canvas, "1_3").color.name() == "#e5a13b"
    layers(tab, "stroke_color", ["1_2"], value="#112233", scope="layer")
    assert live(canvas, "1_2").stroke_color.name() == "#112233" and live(canvas, "1_3").stroke_color.name() != "#112233"


def project_detail(tab):
    from openstrand import project
    return project.detail(tab.runner.workspace.data)


def test_claude_sets_widths_ends_arrows_and_styles_as_the_menu_does(tab):
    canvas = tab.canvas
    layers(tab, "width", ["1_1"], value={"width": 20, "stroke_width": 3})
    assert {(s.width, s.stroke_width) for s in canvas.strands if s.layer_name.startswith("1_")} == {(20, 3)}
    layers(tab, "width", ["1_4"], value={"width": 30, "stroke_width": 2, "elliptical_ends": True}, scope="layer")
    four = live(canvas, "1_4")
    assert (four.width, four.stroke_width, four.elliptical_end_caps) == (30, 2, True)
    assert live(canvas, "1_3").width == 20
    # A free end: an arrow, a dash, a style.
    free = next(s for s in canvas.strands if not hasattr(s, "get_mask_path") and not s.has_circles[1])
    name = free.layer_name
    layers(tab, "arrow", [name], side="end", value=True)
    layers(tab, "dash", [name], side="end", value=True)
    assert free.end_arrow_visible and free.end_extension_visible
    before = tab.steps()
    layers(tab, "end_style", [name], side="end", value={"shape": "pointed", "depth": 0.7, "line_color": "crimson"})
    assert free.get_end_style(1)["shape"] == "pointed" and tab.steps() == before + 1
    assert f"end: arrow dash style pointed" in project_detail(tab)
    # The full arrow, then its style; the menu saves these only once it closes: one step each here.
    before = tab.steps()
    layers(tab, "full_arrow", [name], value=True)
    layers(tab, "arrow_style", [name], value={"texture": "stripes", "shaft": "dots", "head": False,
                                              "color": "teal", "transparency": 60})
    assert free.full_arrow_visible and free.arrow_texture == "stripes" and free.arrow_shaft_style == "dots"
    assert free.arrow_head_visible is False and free.arrow_transparency == 60 and free.arrow_color.name() == "#257d98"
    assert tab.steps() == before + 2
    # The same again changes nothing and says so.
    summary, text = layers(tab, "arrow", [name], side="end", value=True)
    assert "already so" in text


def test_claude_hides_shadows_and_pastes_and_is_told_when_the_app_keeps_no_step(tab):
    canvas = tab.canvas
    layers(tab, "visible", ["1_2"], value=False)
    assert live(canvas, "1_2").is_hidden
    layers(tab, "visible", ["1_2"], value=True)
    assert not live(canvas, "1_2").is_hidden
    summary, text = layers(tab, "shadow_only", ["1_3"], value=True)
    assert live(canvas, "1_3").shadow_only
    assert "keeps no undo step" in text or "in the tab" in text   # the app does not tell this change apart
    layers(tab, "shadow", ["1_4"], value={"receiver": "1_3", "visible": False, "subtract": ["1_2"]})
    store = canvas.layer_state_manager
    assert store.get_shadow_override("1_4", "1_3")["visibility"] is False
    assert store.get_subtracted_layers("1_4", "1_3") == ["1_2"]
    assert "shadow of 1_4 on 1_3: hidden, minus 1_2" in project_detail(tab)
    # Copy and paste strand data, the person's clipboard kept.
    canvas.strand_clipboard = "the person's"
    layers(tab, "width", ["1_4"], value={"width": 34, "stroke_width": 3}, scope="layer")
    layers(tab, "paste_from", ["1_3"], value={"source": "1_4", "properties": ["width"]})
    assert live(canvas, "1_3").width == 34 and canvas.strand_clipboard == "the person's"


def test_bad_layer_requests_say_what_is_wrong(tab):
    from openstrand.app import AppError
    from openstrand.errors import ToolError
    mask = next(s.layer_name for s in tab.canvas.strands if hasattr(s, "get_mask_path"))
    for op, names, more, message in [
            ("color", [mask], {"value": "gold"}, "is a mask"),
            ("color", ["1_1"], {"value": "not a color"}, "unknown color"),
            ("line", ["1_3"], {"side": "start", "value": True}, "no start line"),
            ("arrow_style", ["1_1"], {"value": {"texture": "stripes"}}, "no full arrow"),
            ("width", ["1_1"], {"value": {"width": 10}}, "stroke_width"),
            ("end_style", ["1_1"], {"side": "start", "value": {"shape": "pointed"}}, "circle covers"),
            ("start_edge", ["1_1"], {"value": "half"}, "fold"),
            ("visible", ["9_9"], {"value": True}, "no layer 9_9")]:
        with pytest.raises((AppError, ToolError), match=message):
            layers(tab, op, names, **more)


# ------------------------------------------------------------------ groups
def test_claude_makes_moves_rotates_and_duplicates_a_group(tab):
    canvas = tab.canvas
    one = live(canvas, "1_1")
    before = tab.steps()
    summary, text = groups(tab, "create", "Knot", sets=["1"])
    assert "Knot" in tab.window.group_layer_manager.group_panel.groups and tab.steps() == before + 1
    assert "group Knot: sets 1" in project_detail(tab)
    with pytest.raises(Exception, match="exists"):
        groups(tab, "create", "Knot", sets=["1"])
    groups(tab, "rename", "Knot", new_name="Overhand")
    panel = tab.window.group_layer_manager.group_panel
    assert "Overhand" in panel.groups and "Knot" not in panel.groups
    # Move: every strand of the group by the same offset, one step.
    start = (one.start.x(), one.start.y())
    before = tab.steps()
    groups(tab, "move", "Overhand", dx=40, dy=-25)
    assert (round(one.start.x() - start[0], 3), round(one.start.y() - start[1], 3)) == (40, -25)
    assert tab.steps() == before + 1
    # Rotate half a turn and back: where it started.
    groups(tab, "rotate", "Overhand", angle=180)
    assert abs(one.start.x() - (start[0] + 40)) > 1
    groups(tab, "rotate", "Overhand", angle=-180)
    assert abs(one.start.x() - (start[0] + 40)) < 0.5 and abs(one.start.y() - (start[1] - 25)) < 0.5
    # Turn an attached strand with a free end; its length stays.
    import math
    free = next(s for s in canvas.strands if not hasattr(s, "get_mask_path") and s.is_attachable()
                and not s.layer_name.endswith("_1"))
    length = math.dist((free.start.x(), free.start.y()), (free.end.x(), free.end.y()))
    groups(tab, "angles", "Overhand", angles={free.layer_name: 30})
    angle = math.degrees(math.atan2(free.end.y() - free.start.y(), free.end.x() - free.start.x()))
    assert abs(angle - 30) < 0.5
    assert abs(math.dist((free.start.x(), free.start.y()), (free.end.x(), free.end.y())) - length) < 0.5
    # Shadows of the whole group onto what is under each strand.
    groups(tab, "shadow", "Overhand", receivers="below", visible=False)
    assert canvas.layer_state_manager.get_shadow_override("1_3", "1_1")["visibility"] is False
    # Duplicate: a new group of new sets, on top of the original.
    had = set(panel.groups)
    summary, text = groups(tab, "duplicate", "Overhand")
    made = set(panel.groups) - had
    assert len(made) == 1 and any(s.layer_name.startswith("2_") for s in canvas.strands)
    copy = made.pop()
    groups(tab, "delete", copy)
    assert copy not in panel.groups and any(s.layer_name.startswith("2_") for s in canvas.strands)
    # The panel view: focus a group, fold and open the column.
    tab.runner.app_tool("show_group", {"op": "focus", "group": "Overhand"})
    tab.runner.app_tool("show_group", {"op": "panel", "collapsed": True})
    tab.runner.app_tool("show_group", {"op": "panel", "collapsed": False})


def test_bad_group_requests_say_what_is_wrong(tab):
    from openstrand.app import AppError
    groups(tab, "create", "G", sets=["1"])
    for op, more, message in [("move", {"dx": 5}, "dx and dy"), ("rotate", {}, "angle"),
                              ("angles", {"angles": {"1_1": 10}}, "cannot be turned"),
                              ("mask_grid", {"pairs": [["1_1", "9_9"]]}, "no strand 9_9"),
                              ("rename", {"new_name": "G"}, "different")]:
        with pytest.raises(AppError, match=message):
            groups(tab, op, "G", **more)
    with pytest.raises(AppError, match="no group Nope"):
        groups(tab, "delete", "Nope")
    with pytest.raises(AppError, match="no set 7"):
        groups(tab, "create", "H", sets=["7"])
