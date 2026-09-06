"""Group column collapse to the icon rail (option B3).

Runs the real MainWindow offscreen. Group creation goes through the same
code the Create Group dialogs end in, with the two dialogs stubbed where the
rail's G tile is exercised.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# user_settings.txt lives under APPDATA/OpenStrandStudio; keep the tests off
# the developer's real file.
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QPointF, QTimer
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt

from main_window import MainWindow
from strand import Strand
from group_rail import GroupRail

APP = QApplication.instance() or QApplication([])


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


def settings_path():
    return os.path.join(os.environ["APPDATA"], "OpenStrandStudio", "user_settings.txt")


@pytest.fixture
def window():
    # Each test starts from a clean settings file; a collapsed state left by
    # the previous test would otherwise be restored on launch (by design).
    if os.path.exists(settings_path()):
        os.remove(settings_path())
    win = MainWindow()
    win.show()
    pump(80)
    win.resize(1600, 900)  # wide enough to stay out of compact mode
    pump(150)
    yield win
    close_window(win)


def close_window(win):
    """Close and destroy a MainWindow while Python is still fully alive.

    Closing with unsaved work would raise the app's own confirmation
    dialog, and a window left for interpreter shutdown can receive Qt
    events after its Python attributes are gone."""
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


def add_tree_group(group_panel, name, children=("1_1",)):
    item = QTreeWidgetItem(group_panel.tree, [name])
    item.setData(0, Qt.UserRole, name)
    for child in children:
        QTreeWidgetItem(item, [child])
    group_panel.group_items[name] = item
    group_panel.groups[name] = {"strands": [], "layers": list(children),
                                "main_strands": set(), "control_points": {}}
    return item


def test_tile_label_rules():
    assert GroupRail.tile_label("braid", 3) == "B"
    assert GroupRail.tile_label("  knot", 1) == "K"
    assert GroupRail.tile_label("42 strands", 1) == "4"
    assert GroupRail.tile_label("***", 5) == "5"
    assert GroupRail.tile_label("", 2) == "2"


def test_collapse_frees_width_and_expand_restores(window):
    lp = window.layer_panel
    assert lp.right_panel.width() == lp.GROUP_PANEL_FULL_WIDTH
    assert lp.minimumWidth() == window.LAYER_PANEL_FULL_MIN_WIDTH
    canvas_before = window.canvas.width()

    lp.toggle_group_panel()
    pump(350)
    assert lp.group_panel_collapsed
    assert lp.right_panel.width() == lp.GROUP_PANEL_RAIL_WIDTH
    assert lp.minimumWidth() == window.LAYER_PANEL_FULL_MIN_WIDTH - 100
    assert window.canvas.width() == canvas_before + 100
    assert lp.group_rail.isVisible()
    assert not lp.group_layer_manager.group_panel.isVisible()
    assert lp.group_toggle_button.text() == "‹"
    assert not lp.group_toggle_button.toolTip()

    lp.toggle_group_panel()
    pump(350)
    assert lp.right_panel.width() == lp.GROUP_PANEL_FULL_WIDTH
    assert lp.minimumWidth() == window.LAYER_PANEL_FULL_MIN_WIDTH
    assert window.canvas.width() == canvas_before
    assert lp.group_toggle_button.text() == "›"


def test_rail_mirrors_the_group_tree(window):
    lp = window.layer_panel
    gp = lp.group_layer_manager.group_panel
    add_tree_group(gp, "Group 1")
    add_tree_group(gp, "braid")
    lp.set_group_panel_collapsed(True, animate=False)
    pump(60)
    tiles = lp.group_rail._tiles
    assert [t.text() for t in tiles] == ["G", "B"]
    assert [t.group_name for t in tiles] == ["Group 1", "braid"]
    assert not any(t.toolTip() for t in tiles)
    assert lp.group_rail.create_tile.text() == "G"
    assert not lp.group_rail.create_tile.toolTip()
    assert lp.group_rail.create_tile.width() == GroupRail.TILE_WIDTH

    add_tree_group(gp, "Knot 3")
    pump(60)
    assert [t.text() for t in lp.group_rail._tiles] == ["G", "B", "K"]
    gp._remove_group_from_tree("braid")
    pump(60)
    assert [t.group_name for t in lp.group_rail._tiles] == ["Group 1", "Knot 3"]

    # a tile expands the column and opens that group
    gp.group_items["Knot 3"].setExpanded(False)
    lp.group_rail._tiles[1].click()
    pump(350)
    assert not lp.group_panel_collapsed
    assert gp.group_items["Knot 3"].isExpanded()


def test_create_group_flow_with_rail(window):
    lp = window.layer_panel
    glm = lp.group_layer_manager
    gp = glm.group_panel
    window.canvas.add_strand(Strand(QPointF(100, 100), QPointF(300, 100), 46,
                                    set_number=1, layer_name="1_1"))
    pump(60)

    # the path the Create Group dialogs end in
    glm._create_group_inner("ghj", ["1"])
    pump(60)
    assert "ghj" in gp.groups
    lp.set_group_panel_collapsed(True, animate=False)
    pump(60)
    assert [(t.text(), t.group_name) for t in lp.group_rail._tiles] == [("G", "ghj")]

    # G tile creates a group while staying collapsed (dialogs stubbed)
    glm.create_custom_input_dialog = lambda *a, **k: ("knot", True)
    glm.open_main_strand_selection_dialog = lambda main_strands: ["1"]
    lp.group_rail.create_tile.click()
    pump(120)
    assert "knot" in gp.groups
    assert lp.group_panel_collapsed
    assert [t.text() for t in lp.group_rail._tiles] == ["G", "K"]

    gp.delete_group("ghj")
    pump(60)
    assert [t.text() for t in lp.group_rail._tiles] == ["K"]


def test_disable_controls_covers_the_g_tile(window):
    lp = window.layer_panel
    lp.disable_controls()
    assert not lp.group_rail.create_tile.isEnabled()
    lp.enable_controls()
    assert lp.group_rail.create_tile.isEnabled()


def test_state_persists_and_restores(window):
    lp = window.layer_panel
    lp.set_group_panel_collapsed(True, animate=False)
    pump(40)
    content = open(settings_path(), encoding="utf-8").read()
    assert "GroupPanelRail: true" in content

    second = MainWindow()
    second.show()
    pump(80)
    second.resize(1600, 900)
    pump(150)
    try:
        assert second.layer_panel.group_panel_collapsed
        assert second.layer_panel.right_panel.width() == lp.GROUP_PANEL_RAIL_WIDTH
    finally:
        close_window(second)

    lp.set_group_panel_collapsed(False, animate=False)
    pump(40)
    content = open(settings_path(), encoding="utf-8").read()
    assert "GroupPanelRail: false" in content
    assert content.count("GroupPanelRail") == 1


def test_shortcut_and_hebrew_chevron(window):
    lp = window.layer_panel
    window.group_panel_shortcut.activated.emit()
    pump(350)
    assert lp.group_panel_collapsed
    window.group_panel_shortcut.activated.emit()
    pump(350)
    assert not lp.group_panel_collapsed

    window.set_language("he")
    pump(80)
    assert lp.group_toggle_button.text() == "‹"
    lp.set_group_panel_collapsed(True, animate=False)
    pump(60)
    assert lp.group_toggle_button.text() == "›"
    window.set_language("en")
    pump(40)


def test_compact_window_keeps_rail_usable(window):
    lp = window.layer_panel
    window.resize(1280, 760)  # below COMPACT_WINDOW_WIDTH
    pump(150)
    assert lp.minimumWidth() == window.COMPACT_LAYER_PANEL_FLOOR
    lp.set_group_panel_collapsed(True, animate=False)
    pump(80)
    assert lp.right_panel.width() == lp.GROUP_PANEL_RAIL_WIDTH
    assert lp.minimumWidth() == window.LAYER_PANEL_FULL_MIN_WIDTH - 100
    lp.set_group_panel_collapsed(False, animate=False)
    pump(80)
    assert lp.minimumWidth() == window.COMPACT_LAYER_PANEL_FLOOR
    assert lp.right_panel.width() < lp.GROUP_PANEL_FULL_WIDTH
