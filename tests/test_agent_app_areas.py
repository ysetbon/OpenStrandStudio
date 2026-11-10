"""The agent's tools for the layer panel's right-click menu, the group panel, the
main window's buttons and the Settings dialog, run end to end: the agent's
tool, the bridge, the app's own code in a real window. Each change is checked
on the live app (and as its undo steps)."""
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
    """The tight overhand in a new tab, the agent's runner answered by the real bridge, the tab read."""
    from PyQt5.QtWidgets import QApplication
    from openstrand import agent
    from openstrand.app import AppError
    panel = window.agent_panel
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
def test_agent_folds_the_start_edge_and_recolors_through_the_layer_menu(tab):
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


def test_agent_sets_widths_ends_arrows_and_styles_as_the_menu_does(tab):
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


def test_agent_hides_shadows_and_pastes_and_is_told_when_the_app_keeps_no_step(tab):
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
def test_agent_makes_moves_rotates_and_duplicates_a_group(tab):
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


# ------------------------------------------------------------- main window
def window_op(tab, op, **more):
    return tab.runner.app_tool("app_window", dict({"tab_id": tab.id, "op": op}, **more))


def test_agent_uses_the_view_buttons_without_touching_the_design(tab):
    from PyQt5.QtCore import QPointF
    canvas, panel = tab.canvas, tab.window.layer_panel
    before, version = tab.steps(), tab.runner.workspace.tab_version
    window_op(tab, "zoom", value="reset")
    summary, text = window_op(tab, "zoom", value="in", steps=2)
    assert round(canvas.zoom_factor, 4) == 1.21 and "zoom 121 %" in text
    # A percent zooms about the middle of the view: what is there stays there.
    middle = QPointF(canvas.width() / 2, canvas.height() / 2)
    under = canvas.screen_to_canvas(middle)
    window_op(tab, "zoom", value=250)
    again = canvas.canvas_to_screen(under)
    assert canvas.zoom_factor == 2.5 and abs(again.x() - middle.x()) < 0.01 and abs(again.y() - middle.y()) < 0.01
    # Fit on one strand: up close, in the middle.
    one = live(canvas, "1_3")
    window_op(tab, "zoom", value="fit", layers=["1_3"])
    box = tab.bridge.layers_box(["1_3"])
    middle_of = canvas.canvas_to_screen(QPointF((box[0] + box[2]) / 2, (box[1] + box[3]) / 2))
    assert abs(middle_of.x() - canvas.width() / 2) < 0.5 and abs(middle_of.y() - canvas.height() / 2) < 0.5
    window_op(tab, "center")
    window_op(tab, "zoom", value="fit")
    # The toggles, as their buttons leave them.
    shown = canvas.show_grid
    window_op(tab, "grid", value=not shown)
    assert canvas.show_grid is (not shown) and tab.window.toggle_grid_button.isChecked() is shown
    window_op(tab, "grid", value=shown)
    window_op(tab, "names", value=True)
    assert canvas.should_draw_names and panel.should_draw_names
    window_op(tab, "names", value=False)
    window_op(tab, "layer_tab", value="masks")
    assert panel.layer_tab == "masks" and panel.masks_tab_button.isChecked()
    window_op(tab, "layer_tab", value="strands")
    assert panel.layer_tab == "strands" and panel.strands_tab_button.isChecked()
    window_op(tab, "mode", value="move")
    assert tab.window.current_mode == "move"
    window_op(tab, "mode", value="attach")
    summary, text = window_op(tab, "select", layer="1_2")
    assert canvas.selected_strand.layer_name == "1_2" and "selected 1_2" in text
    window_op(tab, "deselect")
    assert canvas.selected_strand is None
    # Nothing of the design changed: no step, the same version.
    assert tab.steps() == before and tab.bridge.version(tab.window.tab_manager.get_active()) == version
    assert one in canvas.strands
    from openstrand.app import AppError
    for op, more, message in [("zoom", {"value": 1000}, "10 to 500"), ("select", {"layer": "9_9"}, "no layer 9_9"),
                              ("mode", {"value": "fly"}, "mode: value"), ("grid", {"value": "yes"}, "true or false")]:
        with pytest.raises(AppError, match=message):
            window_op(tab, op, **more)


def test_agent_draws_undoes_deletes_and_locks_with_the_window_buttons(tab):
    from openstrand.app import AppError
    canvas, panel = tab.canvas, tab.window.layer_panel
    before = tab.steps()
    summary, text = window_op(tab, "new_strand", start=[100, 100], end=[300, 140])
    made = next(s for s in canvas.strands if s.layer_name.endswith("_1") and s.layer_name != "1_1")
    # Saved as the app saves a strand drawn by hand (its step comes a moment after the strand;
    # the app records it twice, and one Undo takes back both, as for the person).
    assert tab.steps() > before and made.layer_name in text
    assert any(s["layer_name"] == made.layer_name for s in tab.runner.workspace.data["strands"])  # read back
    window_op(tab, "undo")
    assert made not in canvas.strands and tab.steps() == before
    window_op(tab, "redo")
    assert any(s.layer_name == made.layer_name for s in canvas.strands) and tab.steps() > before
    # The toolbar's Points and Shadow, their buttons following.
    window_op(tab, "points", value=False)
    assert canvas.show_control_points is False and not tab.window.toggle_control_points_button.isChecked()
    window_op(tab, "points", value=True)
    window_op(tab, "shadow", value=not canvas.shadow_enabled)
    assert tab.window.toggle_shadow_button.isChecked() is bool(canvas.shadow_enabled)
    # Lock 1_1: lock mode on, that layer locked; then off.
    window_op(tab, "lock", value=True, layers=["1_1"])
    one = canvas.strands.index(live(canvas, "1_1"))
    assert panel.lock_mode and panel.locked_layers == {one}
    with pytest.raises(AppError, match="locked"):
        window_op(tab, "delete", layers=["1_1"])
    window_op(tab, "lock", value=False)
    assert not panel.lock_mode
    # Delete the new set; a strand joined at both ends cannot be deleted.
    window_op(tab, "delete", layers=[made.layer_name])
    assert not any(s.layer_name.split("_")[0] == made.layer_name.split("_")[0] for s in canvas.strands)
    joined = next(s for s in canvas.strands if not hasattr(s, "get_mask_path") and all(s.has_circles)
                  and not getattr(s, "knot_connections", None))
    with pytest.raises(AppError, match="cannot be deleted"):
        window_op(tab, "delete", layers=[joined.layer_name])
    levels = canvas.level_count
    window_op(tab, "new_level")
    assert canvas.level_count == levels + 1
    # Delete All on the Masks tab, answered Yes; one undo brings them back.
    masks = [s.layer_name for s in canvas.strands if hasattr(s, "get_mask_path")]
    assert masks
    window_op(tab, "delete_all", value="masks")
    assert not any(hasattr(s, "get_mask_path") for s in canvas.strands)
    window_op(tab, "undo")
    assert sorted(s.layer_name for s in canvas.strands if hasattr(s, "get_mask_path")) == sorted(masks)
    # The person changes the tab: the agent's next edit is refused until it reads again.
    live(canvas, "1_1").start.setX(live(canvas, "1_1").start.x() + 5)
    with pytest.raises(AppError, match="changed since you read it"):
        window_op(tab, "new_level")
    tab.runner.app_tool("read_tab", {"tab_id": tab.id})
    window_op(tab, "undo")


def test_agent_saves_the_tab_and_the_view_as_files(tab, tmp_path):
    import json
    from openstrand.app import AppError
    from PyQt5.QtGui import QImage
    session = tab.window.tab_manager.get_active()
    path = tmp_path / "saved.json"
    summary, text = window_op(tab, "save", path=str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["type"] == "OpenStrandStudioHistory" and session.file_path == str(path)
    window_op(tab, "save")  # its own file now: no path, no overwrite needed
    image = tmp_path / "view"
    summary, text = window_op(tab, "save_image", path=str(image))
    picture = QImage(str(image) + ".png")
    assert picture.width() == tab.canvas.width() * 4 and picture.height() == tab.canvas.height() * 4
    other = tmp_path / "other.json"
    other.write_text("{}", encoding="utf-8")
    for more, message in [({"path": str(other)}, "exists: give overwrite"), ({"path": "saved.json"}, "full path"),
                          ({"path": str(tmp_path / "nope" / "a.json")}, "no folder"),
                          ({"path": str(tmp_path / "a.txt")}, "ending in .json")]:
        with pytest.raises(AppError, match=message):
            window_op(tab, "save", **more)
    window_op(tab, "save", path=str(other), overwrite=True)
    assert json.loads(other.read_text(encoding="utf-8"))["type"] == "OpenStrandStudioHistory"


# ---------------------------------------------------------------- settings
@pytest.fixture()
def kept_settings(tab):
    """The settings as they were, and the repo's copy of the settings file, put back after."""
    copy = ROOT / "user_settings.txt"
    text = copy.read_bytes() if copy.exists() else None
    dialog = tab.window.settings_dialog
    keys = ("theme", "control_points_selected_only", "shadow_color", "default_strand_width", "sounds",
            "curve_shape", "language")
    old = {key: tab.bridge.setting_value(key) for key in keys}
    yield old
    reply = tab.bridge.handle({"id": 9, "name": "settings", "args": {"values": old}})  # the old values set back
    dialog.hide()
    assert reply["ok"], reply
    assert {key: tab.bridge.setting_value(key) for key in keys} == old
    if text is not None:
        copy.write_bytes(text)


def test_agent_reads_and_changes_settings_as_the_dialog_does(tab, kept_settings):
    from PyQt5.QtGui import QColor
    canvas, dialog = tab.canvas, tab.window.settings_dialog
    summary, text = tab.runner.app_tool("read_settings", {})
    assert "control_points_selected_only = " in text and "[selected_strand]" in text and "theme = " in text
    steps = tab.steps()
    # Control points of the selected strand only: the checkbox and the canvas, as OK leaves them.
    summary, text = tab.runner.app_tool("app_settings", {"op": "set", "values": {"control_points_selected_only": True}})
    assert canvas.show_cp_selected_only and dialog.show_cp_selected_only_checkbox.isChecked()
    assert "Old values" in text and tab.steps() == steps
    # Dark mode: the window, the canvas and the dialog's own combobox.
    tab.runner.app_tool("app_settings", {"op": "set", "values": {"theme": "dark"}})
    assert tab.window.current_theme == "dark" and dialog.theme_combobox.currentData() == "dark"
    # A color through its chooser: every strand's shadow too.
    tab.runner.app_tool("app_settings", {"op": "set", "values": {"shadow_color": "#11223344"}})
    assert canvas.default_shadow_color == QColor(0x11, 0x22, 0x33, 0x44)
    assert all(s.shadow_color == QColor(0x11, 0x22, 0x33, 0x44) for s in canvas.strands if hasattr(s, "shadow_color"))
    # Default Strand Width: 6 grid squares, half of it the color.
    tab.runner.app_tool("app_settings", {"op": "set", "values": {"default_strand_width": {"squares": 6,
                                                                                          "color_percent": 50}}})
    assert (canvas.strand_width, canvas.stroke_width) == (69, 34)
    from openstrand.app import AppError
    for values, message in [({"third_control_point": False, "curvature_bias": True}, "needs third_control_point"),
                            ({"nope": 1}, "no setting nope"), ({"shadow_blur_steps": 1000}, "1..100"),
                            ({"theme": "pink"}, "default / light / dark"), ({"sounds": "on"}, "true/false")]:
        with pytest.raises((AppError, Exception), match=message):
            tab.runner.app_tool("app_settings", {"op": "set", "values": values})
    tab.runner.app_tool("app_settings", {"op": "show", "page": "selected_strand"})
    assert dialog.isVisible() and dialog.categories_list.currentRow() == 2


def test_settings_and_window_changes_wait_for_the_person_in_ask_mode(tab, kept_settings):
    panel, bridge = tab.window.agent_panel, tab.bridge
    sounds = tab.bridge.setting_value("sounds")
    panel.run_mode = "ask"
    try:
        assert bridge.handle({"id": 41, "name": "settings", "args": {"values": {"sounds": not sounds}}}) is None
        card = panel.entries[-1]
        assert card["kind"] == "confirm" and card["what"][0] == "settings" and "sounds" in card["what"][2]
        assert tab.bridge.setting_value("sounds") is sounds  # nothing yet
        assert bridge.decide(41, True)["ok"] and tab.bridge.setting_value("sounds") is (not sounds)
        version = tab.runner.workspace.tab_version
        call = {"id": 42, "name": "window", "args": {"tab_id": tab.id, "op": "new_level", "version": version}}
        assert bridge.handle(call) is None and panel.entries[-1]["what"][0] == "window"
        assert "add a new level" in panel.entries[-1]["what"][2]
        assert bridge.decide(42, False)["error"] == "the person declined this change"
        # The view needs no Allow: it changes nothing of the design.
        assert bridge.handle({"id": 43, "name": "window_view", "args": {"op": "zoom", "value": "reset"}})["ok"]
    finally:
        panel.run_mode = "auto"


def test_settings_restyle_after_a_color_dialog(window):
    """A color chooser leaves its QColorDialog under Settings; Qt made its spin boxes, so their
    Python side (the -/+ buttons' layout) is gone by the next restyle. Changing the theme then
    raised AttributeError: '_segmented_layout' (and in a slot, aborted the app)."""
    import gc
    from PyQt5.QtWidgets import QColorDialog
    from segmented_spin_box import upgrade_and_style_all
    dialog = window.settings_dialog
    left = QColorDialog(dialog)  # what a chooser leaves behind
    try:
        upgrade_and_style_all(dialog, "dark")
        gc.collect()
        upgrade_and_style_all(dialog, "default")
    finally:
        left.setParent(None)
        left.deleteLater()
