"""Levels: storeys in the layer stack (the Level rows of the layer panel).

Everything on a higher level is drawn after everything on a lower one,
masks of the lower level included, so a mask never paints over a strand on
a higher level. tests/levels/continue_2x2.json is a real design where that
matters: 3_4 and 2_4 (19 px wide) continue 3_3 and 2_2 and run back over
them, and masks 3_3_1_2, 3_3_2_2 and 4_3_2_2 cut them at three crossings
while every mask is drawn above every strand.

Runs the real MainWindow offscreen.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QMimeData, QPoint, QPointF, Qt, QTimer
from PyQt5.QtGui import QColor, QDropEvent
from PyQt5.QtWidgets import QApplication

from level_button import LevelRow, LEVEL_BUTTON_SIZE, LEVEL_COLOR
from main_window import MainWindow
from masked_strand import MaskedStrand
from save_load_manager import (apply_loaded_strands, keep_masks_on_top, load_strands_from_data,
                               serialize_project_state, strand_level)

APP = QApplication.instance() or QApplication([])
DESIGN = Path(__file__).resolve().parent / "levels" / "continue_2x2.json"


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


@pytest.fixture
def window():
    win = MainWindow()
    data = json.loads(DESIGN.read_text(encoding="utf-8"))
    loaded = load_strands_from_data(data, win.canvas)
    win.canvas.strands = []
    apply_loaded_strands(win.canvas, loaded[0], loaded[1])
    win.canvas.selected_strand = None
    win.show()
    win.resize(1600, 900)
    pump(200)
    yield win
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


def names(strands):
    return [s.layer_name for s in strands]


def find(win, name):
    return next(s for s in win.canvas.strands if s.layer_name == name)


def list_order(lp):
    """The panel's list, top first: layer names and "Level n" for level rows."""
    out = []
    for i in range(lp.scroll_layout.count()):
        w = lp.scroll_layout.itemAt(i).widget()
        if isinstance(w, LevelRow):
            out.append(w.text())
        elif not w.isHidden():
            out.append(w.text())
    return out


def lift_3_4_and_2_4(win):
    """With the panel only: New Level, then Move down twice, which takes the
    two topmost strands of the ground (2_4, then 3_4) onto Level 1."""
    lp = win.layer_panel
    lp.new_level_button.click()
    pump()
    lp.move_level(1, up=False)
    pump()
    lp.move_level(1, up=False)
    pump()


def assert_consistent(win):
    lp = win.layer_panel
    assert [b.text() for b in lp.layer_buttons] == names(win.canvas.strands)
    rows = [w for w in (lp.scroll_layout.itemAt(i).widget() for i in range(lp.scroll_layout.count()))
            if isinstance(w, LevelRow)]
    assert len(rows) == win.canvas.level_count


def pixel(win, x, y):
    """The colour drawn at canvas point (x, y), panned to the middle of the view."""
    canvas = win.canvas
    canvas.zoom_factor = 1.0
    canvas.pan_offset_x = canvas.width() / 2 - x
    canvas.pan_offset_y = canvas.height() / 2 - y
    canvas.update()
    pump(50)
    image = canvas.grab().toImage()
    p = canvas.canvas_to_screen(QPointF(x, y))
    return QColor(image.pixel(int(round(p.x())), int(round(p.y()))))


def near(color, rgb, tolerance=40):
    return all(abs(a - b) <= tolerance for a, b in zip((color.red(), color.green(), color.blue()), rgb))


GREEN, LILAC, DARK, BLACK = (85, 170, 0), (202, 193, 221), (30, 19, 34), (0, 0, 0)


# --- ordering and saving ----------------------------------------------------

class Plain:
    def __init__(self, name, level=None):
        self.layer_name = name
        self.level = level


class Mask(MaskedStrand):
    def __init__(self, name, first, second):  # no geometry needed for ordering
        self.layer_name = name
        self.first_selected_strand = first
        self.second_selected_strand = second


def test_masks_go_above_their_own_level_only():
    a, b = Plain("1_1", 0), Plain("2_1", 0)
    up = Plain("1_2", 1)
    m = Mask("1_1_2_1", a, b)  # both strands on the ground
    ordered, _ = keep_masks_on_top([a, up, m, b], (), 1)
    assert names(ordered) == ["1_1", "2_1", "1_1_2_1", "1_2"]
    # A mask with a strand on a higher level goes with that level
    m2 = Mask("1_2_2_1", up, b)
    ordered, _ = keep_masks_on_top([a, b, up, m2, m], (), 1)
    assert names(ordered) == ["1_1", "2_1", "1_1_2_1", "1_2", "1_2_2_1"]


def test_without_levels_nothing_changes():
    data = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert "level_count" not in data and not any("level" in s for s in data["strands"])
    loader = type("C", (), {})()
    loader.strands, loader.groups, loader.strand_colors = [], {}, {}
    loader._suppress_layer_panel_refresh = True
    loader._suppress_repaint = True
    loader.update = lambda: None
    strands = load_strands_from_data(data, loader)[0]
    assert loader.level_count == 0 and all(s.level == 0 for s in strands if not isinstance(s, MaskedStrand))
    ordered, _ = keep_masks_on_top(strands)
    plain = [s for s in strands if not isinstance(s, MaskedStrand)]
    masks = [s for s in strands if isinstance(s, MaskedStrand)]
    assert ordered == plain + masks  # all strands, then all masks, as always


def test_levels_survive_save_and_load(window):
    lift_3_4_and_2_4(window)
    data = json.loads(json.dumps(serialize_project_state(window.canvas.strands, {}, window.canvas)))
    assert data["level_count"] == 1
    saved = {s["layer_name"]: s.get("level") for s in data["strands"]}
    assert saved["3_4"] == 1 and saved["2_4"] == 1 and saved["3_3"] == 0
    assert "level" not in next(s for s in data["strands"] if s["layer_name"] == "3_3_1_2")

    window.canvas.strands = []
    loaded = load_strands_from_data(data, window.canvas)
    assert window.canvas.level_count == 1
    by_name = {s.layer_name: s for s in loaded[0]}
    assert by_name["3_4"].level == 1 and by_name["3_3"].level == 0
    assert strand_level(by_name["3_3_1_2"]) == 0


# --- the panel --------------------------------------------------------------

def test_new_level_adds_an_empty_row_on_top(window):
    lp = window.layer_panel
    before = names(window.canvas.strands)
    lp.new_level_button.click()
    pump()
    assert window.canvas.level_count == 1
    assert list_order(lp)[0] == "Level 1"  # empty, above everything
    assert names(window.canvas.strands) == before  # nothing drawn moves
    assert_consistent(window)


def _below(lp, upper, lower):
    """*lower* is the next button in the bottom panel, right under *upper*."""
    layout = lp.add_new_strand_button.parentWidget().layout()
    return layout.indexOf(lower) == layout.indexOf(upper) + 1


def _bold_14px(button):
    return "font-size: 14px" in button.styleSheet() and "font-weight: bold" in button.styleSheet()


def test_new_level_buttons_on_both_tabs(window):
    """New Level is a full-width button of its own, right under New Strand (and
    under New Mask on the Masks tab), in the panel's 14 px bold like the rest."""
    lp = window.layer_panel
    assert lp.add_new_strand_button.isVisible() and lp.new_level_button.isVisible()
    assert not lp.new_mask_button.isVisible() and not lp.new_level_mask_button.isVisible()
    assert _below(lp, lp.add_new_strand_button, lp.new_level_button)
    assert abs(lp.add_new_strand_button.width() - lp.new_level_button.width()) <= 1
    assert lp.new_level_button.width() == lp.draw_names_button.width()
    assert _bold_14px(lp.new_level_button) and _bold_14px(lp.add_new_strand_button)
    lp.set_layer_tab("masks")
    pump()
    assert lp.new_mask_button.isVisible() and lp.new_level_mask_button.isVisible()
    assert not lp.add_new_strand_button.isVisible() and not lp.new_level_button.isVisible()
    assert _below(lp, lp.new_mask_button, lp.new_level_mask_button)
    assert abs(lp.new_mask_button.width() - lp.new_level_mask_button.width()) <= 1
    lp.new_level_mask_button.click()  # a level can be made from the Masks tab too
    pump()
    assert window.canvas.level_count == 1


@pytest.mark.parametrize("code", ["es", "fr", "de", "it", "pt", "he", "ru", "fi", "sv", "ja", "zh"])
def test_new_level_text_fits_in_every_language(window, code):
    """No text in the New Strand / New Level pair needs a smaller font."""
    from PyQt5.QtGui import QFont, QFontMetrics
    lp = window.layer_panel
    lp.language_code = code
    lp.update_translations()
    pump()
    for button in (lp.add_new_strand_button, lp.new_level_button):
        font = QFont(button.font())
        font.setBold(True)
        font.setPixelSize(14)
        assert QFontMetrics(font).horizontalAdvance(button.text()) <= button.width() - 8, (code, button.text())


def test_level_row_sits_under_the_layers_it_carries(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    order = list_order(lp)
    assert order[:3] == ["2_4", "3_4", "Level 1"]
    assert find(window, "3_4").level == 1 and find(window, "2_4").level == 1
    assert find(window, "3_3").level == 0
    # Every mask (all on the ground) is now drawn before 3_4 and 2_4
    strands = window.canvas.strands
    last_mask = max(i for i, s in enumerate(strands) if isinstance(s, MaskedStrand))
    assert last_mask < names(strands).index("3_4")
    assert_consistent(window)


def test_level_row_looks_like_a_shorter_layer(window):
    lp = window.layer_panel
    lp.new_level_button.click()
    pump()
    row = lp.level_rows[0]
    assert row.button.size() == LEVEL_BUTTON_SIZE  # 146 x 27
    assert LEVEL_BUTTON_SIZE.width() == lp.LAYER_LIST_BUTTON_WIDTH
    assert LEVEL_BUTTON_SIZE.height() == round(40 * 2 / 3)
    # The line runs the whole list, at any panel width
    viewport = lp.scroll_area.viewport()
    assert row.width() == viewport.width()
    image = row.grab().toImage()
    line_y = row.height() - 2
    assert QColor(image.pixel(0, line_y)) == LEVEL_COLOR
    assert QColor(image.pixel(row.width() - 1, line_y)) == LEVEL_COLOR


def test_masks_stop_cutting_3_4_and_2_4(window):
    # Today: the 46 px pieces of 4_3_2_2 and 3_3_1_2 are drawn over the thin strands
    assert near(pixel(window, 1260, 476), LILAC)  # 4_3 over 2_4
    assert near(pixel(window, 1160, 364), DARK)   # 3_3 over 3_4's outline
    lift_3_4_and_2_4(window)
    assert near(pixel(window, 1260, 476), GREEN)  # 2_4 whole again
    assert near(pixel(window, 1160, 364), BLACK)  # 3_4's outline back on top


def test_move_up_gives_the_strand_back(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    assert lp.can_move_level(1, up=True)
    lp.move_level(1, up=True)  # the lowest strand of Level 1 (3_4) goes down
    pump()
    assert find(window, "3_4").level == 0 and find(window, "2_4").level == 1
    assert list_order(lp)[:2] == ["2_4", "Level 1"]
    assert_consistent(window)


def test_remove_renumbers_the_levels_above(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.new_level_button.click()  # Level 2, then 2_4 onto it
    pump()
    lp.move_level(2, up=False)
    pump()
    assert find(window, "2_4").level == 2 and find(window, "3_4").level == 1
    lp.remove_level(1)
    pump()
    assert window.canvas.level_count == 1
    assert find(window, "2_4").level == 1 and find(window, "3_4").level == 0
    assert [r.text() for r in lp.level_rows] == ["Level 1"]
    lp.remove_level(1)
    pump()
    assert window.canvas.level_count == 0 and not lp.level_rows
    strands = window.canvas.strands
    masks_at = [i for i, s in enumerate(strands) if isinstance(s, MaskedStrand)]
    assert min(masks_at) > max(i for i, s in enumerate(strands) if not isinstance(s, MaskedStrand))
    assert_consistent(window)


def test_masks_tab_offers_only_remove(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.set_layer_tab("masks")
    pump()
    assert not lp.can_move_level(1, up=True) and not lp.can_move_level(1, up=False)
    assert "Level 1" in list_order(lp)


def test_both_tabs_share_one_set_of_levels(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    # A mask takes the higher level of its two strands
    from masked_strand import MaskedStrand as M
    on_level_1 = M(find(window, "3_4"), find(window, "1_2"))
    assert strand_level(on_level_1, 1) == 1
    assert strand_level(find(window, "3_3_1_2"), 1) == 0
    # Removing the level on the Masks tab removes it on the Strands tab too
    lp.set_layer_tab("masks")
    pump()
    assert "Level 1" in list_order(lp)
    lp.remove_level(1)
    pump()
    lp.set_layer_tab("strands")
    pump()
    assert "Level 1" not in list_order(lp) and window.canvas.level_count == 0
    assert_consistent(window)


def test_dragging_a_strand_under_the_row_moves_it_down_a_level(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    layout = lp.scroll_layout
    source = next(b for b in lp.layer_buttons if b.text() == "3_4")
    target = next(b for b in lp.layer_buttons if b.text() == "2_3")  # first strand under the row
    drop = QPoint(20, target.mapTo(lp.scroll_content, QPoint(0, 0)).y() + 3)
    mime = QMimeData()
    mime.setData("application/x-layerbutton-index", str(layout.indexOf(source)).encode())
    lp.dropEvent(QDropEvent(drop, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier))
    lp.refresh()
    pump(100)
    assert find(window, "3_4").level == 0 and find(window, "2_4").level == 1
    assert list_order(lp)[:3] == ["2_4", "Level 1", "3_4"]
    assert_consistent(window)


def test_dragging_the_row_moves_the_boundary(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    layout = lp.scroll_layout
    row = lp.level_rows[0]
    target = next(b for b in lp.layer_buttons if b.text() == "1_3")  # two strands under 2_3
    drop = QPoint(20, target.mapTo(lp.scroll_content, QPoint(0, 0)).y() + 3)
    mime = QMimeData()
    mime.setData("application/x-layerbutton-index", str(layout.indexOf(row)).encode())
    lp.dropEvent(QDropEvent(drop, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier))
    lp.refresh()
    pump(100)
    assert find(window, "2_3").level == 1 and find(window, "1_3").level == 0
    assert list_order(lp)[:4] == ["2_4", "3_4", "2_3", "Level 1"]
    assert_consistent(window)


def test_new_strands_land_on_the_top_level(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.new_level_button.click()  # empty Level 2
    pump()
    template = find(window, "1_1")
    new = type(template)(QPointF(1080, 532), QPointF(1424, 532), 46)
    new.layer_name, new.set_number = "5_1", 5
    window.canvas.strands.append(new)
    lp.refresh()
    pump()
    assert new.level == 2
    saved = serialize_project_state(window.canvas.strands, {}, window.canvas)
    assert next(s for s in saved["strands"] if s["layer_name"] == "5_1")["level"] == 2


def test_undo_and_redo_level_steps(window):
    lp = window.layer_panel
    undo = lp.undo_redo_manager
    undo.save_state(action="test.start")
    lp.new_level_button.click()
    pump()
    lp.move_level(1, up=False)
    pump()
    assert find(window, "2_4").level == 1
    undo.undo()  # back to an empty Level 1
    pump(150)
    assert window.canvas.level_count == 1 and find(window, "2_4").level == 0
    undo.undo()  # back to no levels
    pump(150)
    assert window.canvas.level_count == 0 and not lp.level_rows
    undo.redo()
    pump(150)
    assert window.canvas.level_count == 1
    undo.redo()
    pump(150)
    assert find(window, "2_4").level == 1
    assert_consistent(window)


def test_delete_all_removes_the_levels(window, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    monkeypatch.setattr(QMessageBox, "exec_", lambda self: None)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self.buttons()[0])  # Yes
    lp.request_delete_all()
    pump()
    assert window.canvas.level_count == 0 and not lp.level_rows
