"""Strands / Masks switch in the layer panel.

Runs the real MainWindow offscreen on samples/bridge.json (8 strands,
5 masks). The switch only hides the other tab's layer buttons, so the
tests check both what is visible and that the layer order and the
layer_buttons <-> canvas.strands indices never change.
"""
import json
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
from PyQt5.QtCore import QEvent, QMimeData, QPoint, QPointF, Qt, QTimer
from PyQt5.QtGui import QDropEvent, QFontMetrics, QMouseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from masked_strand import MaskedStrand
from save_load_manager import (apply_loaded_strands, keep_masks_on_top, load_strands,
                               load_strands_from_data)
from translations import translations

APP = QApplication.instance() or QApplication([])


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


def close_window(win):
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


@pytest.fixture
def window():
    win = MainWindow()
    data = json.loads((SRC_DIR / "samples" / "bridge.json").read_text(encoding="utf-8"))
    if data.get("type") == "OpenStrandStudioHistory":
        data = data["states"][data.get("current_step", 1) - 1]["data"]
    loaded = load_strands_from_data(data, win.canvas)
    apply_loaded_strands(win.canvas, loaded[0], loaded[1])
    win.show()
    win.resize(1600, 900)
    pump(200)
    yield win
    close_window(win)


def names(strands):
    return [s.layer_name for s in strands]


def visible_layers(lp):
    return {b.text() for b in lp.layer_buttons if not b.isHidden()}


def strand_names(win):
    return {s.layer_name for s in win.canvas.strands if not isinstance(s, MaskedStrand)}


def mask_names(win):
    return {s.layer_name for s in win.canvas.strands if isinstance(s, MaskedStrand)}


def index_of(win, name):
    return names(win.canvas.strands).index(name)


def assert_indices_match(win):
    lp = win.layer_panel
    assert [b.text() for b in lp.layer_buttons] == names(win.canvas.strands)


def test_each_tab_shows_only_its_layers_and_buttons(window):
    lp = window.layer_panel
    assert lp.layer_tab == "strands"
    assert lp.strands_tab_button.isChecked() and not lp.masks_tab_button.isChecked()
    assert visible_layers(lp) == strand_names(window)
    strand_buttons = [lp.draw_names_button, lp.lock_layers_button, lp.add_new_strand_button,
                      lp.delete_strand_button, lp.deselect_all_button, lp.delete_all_button]
    mask_buttons = [lp.new_mask_button, lp.delete_mask_button, lp.deselect_all_button,
                    lp.delete_all_masks_button]
    assert all(b.isVisible() for b in strand_buttons)
    assert not any(b.isVisible() for b in mask_buttons if b is not lp.deselect_all_button)

    lp.masks_tab_button.click()
    pump()
    assert lp.layer_tab == "masks"
    assert lp.masks_tab_button.isChecked() and not lp.strands_tab_button.isChecked()
    assert visible_layers(lp) == mask_names(window)
    assert all(b.isVisible() for b in mask_buttons)
    assert not any(b.isVisible() for b in strand_buttons if b is not lp.deselect_all_button)


def test_switching_never_changes_order_or_indices(window):
    lp = window.layer_panel
    order = names(window.canvas.strands)
    for tab in ("masks", "strands", "masks", "strands"):
        lp.set_layer_tab(tab)
        pump()
        assert names(window.canvas.strands) == order
        assert len(lp.layer_buttons) == len(order)  # hidden, never removed
        assert_indices_match(window)


def test_filter_survives_rebuilds(window):
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    lp.refresh()
    pump()
    assert visible_layers(lp) == mask_names(window)
    lp.refresh_after_attachment()  # re-adds every button and show()s it
    pump()
    assert visible_layers(lp) == mask_names(window)
    lp.update_layer_button_states()
    assert visible_layers(lp) == mask_names(window)
    assert_indices_match(window)


def test_switching_drops_a_selection_it_would_hide(window):
    lp = window.layer_panel
    lp.select_layer(index_of(window, "2_1"))
    pump()
    assert lp.get_selected_layer() == index_of(window, "2_1")
    lp.toggle_multi_select_mode()
    lp.multi_selected_layers.update({index_of(window, "3_1"), index_of(window, "1_1_3_1")})

    lp.set_layer_tab("masks")
    pump()
    assert lp.layer_tab == "masks"  # the dropped strand doesn't pull it back
    assert lp.get_selected_layer() is None
    assert window.canvas.selected_strand is None
    assert lp.multi_selected_layers == {index_of(window, "1_1_3_1")}


def test_selecting_a_layer_of_the_other_tab_opens_that_tab(window):
    lp = window.layer_panel
    lp.select_layer(index_of(window, "1_1_4_1"))
    pump()
    assert lp.layer_tab == "masks"
    assert visible_layers(lp) == mask_names(window)
    lp.select_layer(index_of(window, "5_1"))
    pump()
    assert lp.layer_tab == "strands"


def test_new_mask_starts_and_cancels_mask_mode(window):
    lp = window.layer_panel
    hint = translations["en"]["new_mask_hint"]
    lp.set_layer_tab("masks")
    lp.new_mask_button.click()
    pump()
    assert window.current_mode == "mask"
    assert lp.new_mask_button.isChecked()
    assert lp.notification_label.text() == hint

    lp.new_mask_button.click()  # pressed again: cancel
    pump()
    assert window.current_mode == "attach"
    assert not lp.new_mask_button.isChecked()
    assert lp.notification_label.text() != hint

    # Leaving the Masks tab also leaves mask mode and its half-made pick
    lp.new_mask_button.click()
    pump()
    window.canvas.mask_mode.selected_strands = [window.canvas.strands[index_of(window, "3_1")]]
    lp.set_layer_tab("strands")
    pump()
    assert window.current_mode == "attach"
    assert window.canvas.mask_mode.selected_strands == []
    assert not lp.new_mask_button.isChecked()


def test_any_mode_change_releases_new_mask(window):
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    lp.new_mask_button.click()
    pump()
    window.set_move_mode()
    pump()
    assert not lp.new_mask_button.isChecked()


def test_creating_a_mask_lands_in_the_masks_tab(window):
    lp = window.layer_panel
    by_name = {s.layer_name: s for s in window.canvas.strands}
    count = len(window.canvas.strands)
    lp.set_layer_tab("masks")
    lp.new_mask_button.click()
    pump()

    mask_mode = window.canvas.mask_mode
    mask_mode.selected_strands = [by_name["3_1"]]
    mask_mode.handle_strand_selection(by_name["1_1"])  # the app's own creation path
    pump(200)

    assert len(window.canvas.strands) == count + 1
    assert "3_1_1_1" in mask_names(window)
    assert lp.layer_tab == "masks"
    assert visible_layers(lp) == mask_names(window)
    assert lp.layer_buttons[lp.get_selected_layer()].text() == "3_1_1_1"
    assert window.current_mode != "mask"
    assert not lp.new_mask_button.isChecked()
    assert_indices_match(window)


def test_delete_mask_acts_only_on_a_selected_mask(window):
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    pump()
    assert not lp.delete_mask_button.isEnabled()  # nothing selected

    lp.select_layer(index_of(window, "1_1_5_1"))
    pump()
    assert lp.delete_mask_button.isEnabled()
    strands_before = strand_names(window)
    lp.delete_mask_button.click()
    pump(150)
    assert "1_1_5_1" not in mask_names(window)
    assert strand_names(window) == strands_before
    assert lp.layer_tab == "masks"
    assert visible_layers(lp) == mask_names(window)
    assert_indices_match(window)


def test_delete_all_on_masks_tab_keeps_the_strands(window, monkeypatch):
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    pump()
    asked = []
    monkeypatch.setattr(lp, "_ask_yes_no", lambda title, text: asked.append(text) or False)
    lp.delete_all_masks_button.click()
    assert asked == [translations["en"]["delete_all_masks_confirm"]]
    assert len(mask_names(window)) == 5  # "No" changes nothing

    monkeypatch.setattr(lp, "_ask_yes_no", lambda title, text: True)
    strands_before = names([s for s in window.canvas.strands if not isinstance(s, MaskedStrand)])
    lp.delete_all_masks_button.click()
    pump(150)
    assert mask_names(window) == set()
    assert names(window.canvas.strands) == strands_before
    assert visible_layers(lp) == set()
    assert_indices_match(window)


def test_drop_ignores_hidden_buttons(window):
    """A drop lands next to the visible button under the cursor, even when a
    hidden mask between the visible strands still has an old position."""
    lp = window.layer_panel
    # Move a mask between the strands: 1_1 ... 4_1, 1_1_3_1, 5_1 ... 8_1
    mask = window.canvas.strands[index_of(window, "1_1_3_1")]
    window.canvas.strands.remove(mask)
    window.canvas.strands.insert(index_of(window, "5_1"), mask)
    lp.refresh()
    lp.set_layer_tab("strands")
    pump(150)

    layout = lp.scroll_layout
    hidden_mask = next(b for b in lp.layer_buttons if b.text() == "1_1_3_1")
    assert hidden_mask.isHidden()
    # Where it sat while the Masks tab was open: far below the strands
    hidden_mask.setGeometry(0, lp.scroll_content.height() + 200, 146, 40)

    source = next(b for b in lp.layer_buttons if b.text() == "1_1")
    target = next(b for b in lp.layer_buttons if b.text() == "2_1")
    target_top = target.mapTo(lp.scroll_content, QPoint(0, 0)).y()
    drop = QPoint(20, target_top + 3)  # top edge of 2_1
    indicator = lp.calculate_drop_indicator_y(drop)
    assert abs(indicator - target_top) <= lp.scroll_layout.spacing() + 1

    mime = QMimeData()
    mime.setData("application/x-layerbutton-index", str(layout.indexOf(source)).encode())
    event = QDropEvent(drop, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
    lp.dropEvent(event)
    pump(100)

    visible_order = [layout.itemAt(i).widget().text() for i in range(layout.count())
                     if not layout.itemAt(i).widget().isHidden()]
    assert visible_order.index("1_1") == visible_order.index("2_1") - 1
    order = names(window.canvas.strands)
    assert order.index("1_1_3_1") > order.index("4_1")  # the hidden mask didn't move
    assert_indices_match(window)


def test_drop_below_the_last_mask_keeps_it_above_the_strands(window):
    """On the Masks tab the strands are hidden under the masks. A mask
    dropped below the lowest visible mask lands right after it, not under
    every hidden strand, where it would stop covering its crossing."""
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    pump(150)

    layout = lp.scroll_layout
    source = next(b for b in lp.layer_buttons if b.text() == "5_1_8_1")  # top mask
    lowest = next(b for b in lp.layer_buttons if b.text() == "1_1_3_1")  # bottom mask
    lowest_bottom = lowest.mapTo(lp.scroll_content, QPoint(0, 0)).y() + lowest.height()
    drop = QPoint(20, lowest_bottom + 1)  # just under the lowest mask
    mime = QMimeData()
    mime.setData("application/x-layerbutton-index", str(layout.indexOf(source)).encode())
    lp.dropEvent(QDropEvent(drop, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier))
    pump(100)

    order = names(window.canvas.strands)
    masks_at = [i for i, s in enumerate(window.canvas.strands) if isinstance(s, MaskedStrand)]
    strands_at = [i for i, s in enumerate(window.canvas.strands) if not isinstance(s, MaskedStrand)]
    assert min(masks_at) > max(strands_at), order  # every mask still above every strand
    assert order.index("5_1_8_1") == order.index("1_1_3_1") - 1  # now just below 1_1_3_1
    assert_indices_match(window)


def test_mask_editing_locks_the_switch(window):
    lp = window.layer_panel
    lp.disable_controls()
    assert not lp.strands_tab_button.isEnabled() and not lp.masks_tab_button.isEnabled()
    assert not lp.new_mask_button.isEnabled() and not lp.delete_all_masks_button.isEnabled()
    lp.enable_controls()
    assert lp.strands_tab_button.isEnabled() and lp.new_mask_button.isEnabled()


def test_toolbar_has_no_mask_button(window):
    assert not hasattr(window, "mask_button")
    toolbar = [b.text() for b in window._toolbar_row_widgets() if hasattr(b, "text")]
    assert translations["en"]["mask_mode"] not in toolbar


@pytest.mark.parametrize("lang", sorted(translations))
def test_labels_fit_the_panel(window, lang):
    lp = window.layer_panel
    window.set_language(lang)
    pump(80)
    for half in (lp.strands_tab_button, lp.masks_tab_button):
        need = QFontMetrics(half.font()).horizontalAdvance(half.text())
        assert need <= half.width() - 4, f"{lang}: '{half.text()}' needs {need}px"
    assert abs(lp.strands_tab_button.width() - lp.masks_tab_button.width()) <= 1
    column = lp.deselect_all_button.width()
    for button in (lp.new_mask_button, lp.delete_mask_button, lp.delete_all_masks_button):
        need = QFontMetrics(button.font()).horizontalAdvance(button.text())
        assert need <= column - 22, f"{lang}: '{button.text()}' needs {need}px"
    hint = translations[lang]["new_mask_hint"]
    assert QFontMetrics(lp.notification_label.font()).horizontalAdvance(hint) <= lp.left_panel.width()


def test_hebrew_puts_strands_on_the_right(window):
    lp = window.layer_panel
    window.set_language("he")
    pump(80)
    strands_x = lp.strands_tab_button.mapTo(lp.left_panel, QPoint(0, 0)).x()
    masks_x = lp.masks_tab_button.mapTo(lp.left_panel, QPoint(0, 0)).x()
    assert strands_x > masks_x
    assert lp.strands_tab_button.text() == translations["he"]["layer_tab_strands"]


# --- Masks always sit above every strand -------------------------------------
# A mask only says which of its two strands is on top where they cross, so its
# place among the strands must not matter. It works from anywhere above both of
# them and stops working under either, so the app keeps every mask above every
# strand: after loading, after drawing a new strand, after a drag.

def masks_above_strands(win):
    kinds = [isinstance(s, MaskedStrand) for s in win.canvas.strands]
    return kinds == sorted(kinds)  # all strands (False) first, then all masks


def test_keep_masks_on_top_moves_locks_with_their_layers():
    class S:
        def __init__(self, name):
            self.layer_name = name

    class M(MaskedStrand):
        def __init__(self, name):  # no geometry needed for ordering
            self.layer_name = name

    a, m, b, c = S("1_1"), M("1_1_2_1"), S("2_1"), S("3_1")
    ordered, locked = keep_masks_on_top([a, m, b, c], {1, 3})  # lock the mask and 3_1
    assert [x.layer_name for x in ordered] == ["1_1", "2_1", "3_1", "1_1_2_1"]
    assert locked == {3, 2}  # the mask is now 3, 3_1 is now 2
    same, same_locked = keep_masks_on_top([a, b, m], {0})
    assert [x.layer_name for x in same] == ["1_1", "2_1", "1_1_2_1"] and same_locked == {0}


def test_loading_a_file_puts_the_masks_above_every_strand(window):
    # thick_and_thin keeps strands 11_1 and 12_1 above its masks
    path = SRC_DIR / "samples" / "thick_and_thin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data = data["states"][data.get("current_step", 1) - 1]["data"]
    saved = [s["layer_name"] for s in data["strands"]]
    assert saved.index("12_1") > saved.index("1_1_6_1")

    state_file = Path(tempfile.mkdtemp()) / "state.json"  # the file's current undo state
    state_file.write_text(json.dumps(data), encoding="utf-8")
    strands = load_strands(str(state_file), window.canvas)[0]
    window.canvas.strands = []
    apply_loaded_strands(window.canvas, strands, {})
    pump(150)
    assert masks_above_strands(window)
    order = names(window.canvas.strands)
    plain = [n for n in saved if n.count("_") == 1]
    masks = [n for n in saved if n.count("_") == 3]
    assert order == plain + masks  # each group keeps its own order
    assert_indices_match(window)


def draw_new_strand(win, x0, y0, x1, y1):
    canvas = win.canvas
    win.layer_panel.add_new_strand_button.click()
    pump(80)
    QTest.mousePress(canvas, Qt.LeftButton, Qt.NoModifier, QPoint(x0, y0))
    for i in range(1, 7):
        p = QPointF(x0 + (x1 - x0) * i / 6, y0 + (y1 - y0) * i / 6)
        QApplication.sendEvent(canvas, QMouseEvent(QEvent.MouseMove, p, Qt.LeftButton,
                                                   Qt.LeftButton, Qt.NoModifier))
        pump(15)
    QTest.mouseRelease(canvas, Qt.LeftButton, Qt.NoModifier, QPoint(x1, y1))
    pump(200)


def test_a_new_strand_is_drawn_under_the_masks(window):
    lp = window.layer_panel
    count = len(window.canvas.strands)
    w, h = window.canvas.width(), window.canvas.height()
    draw_new_strand(window, int(w * 0.2), int(h * 0.2), int(w * 0.7), int(h * 0.6))

    assert len(window.canvas.strands) == count + 1
    assert masks_above_strands(window)
    new = [s for s in window.canvas.strands if s.layer_name == "9_1"]
    assert new, names(window.canvas.strands)
    selected = lp.get_selected_layer()
    assert selected is not None and lp.layer_buttons[selected].text() == "9_1"
    assert window.canvas.selected_strand is new[0]
    assert lp.layer_tab == "strands"
    assert_indices_match(window)


def test_dragging_a_strand_to_the_top_keeps_it_under_the_masks(window):
    lp = window.layer_panel
    lp.set_layer_tab("strands")
    pump(150)
    layout = lp.scroll_layout
    source = next(b for b in lp.layer_buttons if b.text() == "1_1")
    top = next(b for b in lp.layer_buttons if b.text() == "8_1")  # top visible strand
    drop = QPoint(20, top.mapTo(lp.scroll_content, QPoint(0, 0)).y() + 2)
    mime = QMimeData()
    mime.setData("application/x-layerbutton-index", str(layout.indexOf(source)).encode())
    lp.dropEvent(QDropEvent(drop, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier))
    pump(100)
    lp.refresh()  # what DropTargetWidget does after a drop
    pump(100)

    order = names(window.canvas.strands)
    assert masks_above_strands(window), order
    plain = [n for n in order if n.count("_") == 1]
    assert plain[-1] == "1_1"  # top of the strands, still under every mask
    assert_indices_match(window)


# --- Same behaviour as the old toolbar Mask button and mask menu --------------
# Compared against main (old Mask button) with the same clicks: every step of
# the flow and every mask menu item matched.

def canvas_point_on(win, name):
    from selection_utils import find_strands_at_point
    strand = next(s for s in win.canvas.strands if s.layer_name == name)
    path = strand.get_path()
    for i in range(5, 96, 3):
        point = path.pointAtPercent(i / 100)
        hits = find_strands_at_point(win.canvas.strands, point, include_masked=False)
        if hits and hits[0][0] is strand:
            screen = win.canvas.canvas_to_screen(point)
            return QPoint(int(round(screen.x())), int(round(screen.y())))
    raise AssertionError(f"no clickable point on {name}")


def test_new_mask_with_real_canvas_clicks(window):
    lp = window.layer_panel
    canvas = window.canvas
    lp.set_layer_tab("masks")
    lp.new_mask_button.click()
    pump()
    assert window.current_mode == "mask" and canvas.current_mode is canvas.mask_mode

    QTest.mouseClick(canvas, Qt.LeftButton, Qt.NoModifier, canvas_point_on(window, "3_1"))
    pump(200)
    assert [s.layer_name for s in canvas.mask_mode.selected_strands] == ["3_1"]
    assert window.current_mode == "mask"

    QTest.mouseClick(canvas, Qt.LeftButton, Qt.NoModifier, canvas_point_on(window, "1_1"))
    pump(250)
    assert names(canvas.strands)[-1] == "3_1_1_1"  # on top, like every mask
    assert getattr(canvas.selected_strand, "layer_name", None) == "3_1_1_1"
    assert window.current_mode == "attach" and not lp.new_mask_button.isChecked()
    assert lp.layer_tab == "masks"
    assert_indices_match(window)


def test_mask_right_click_menu_on_the_masks_tab(window, monkeypatch):
    from PyQt5.QtWidgets import QMenu, QWidgetAction
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    pump()
    shown = []
    monkeypatch.setattr(QMenu, "exec_", lambda self, *a, **k: shown.append(self))
    button = next(b for b in lp.layer_buttons if b.text() == "1_1_3_1")
    button.customContextMenuRequested.emit(QPoint(20, 10))
    pump(80)
    assert shown, "no menu opened"
    labels = []
    for act in shown[-1].actions():
        widget = act.defaultWidget() if isinstance(act, QWidgetAction) else None
        labels.append("---" if act.isSeparator() else
                      widget.text() if widget is not None and hasattr(widget, "text") else act.text())
    _ = translations["en"]
    assert labels == [_["hide_layer"], _["shadow_only"], _["hide_shadow"], _["edit_shadows"], "---",
                      _["edit_mask"], _["reset_mask"]], labels
