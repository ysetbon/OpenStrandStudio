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
from PyQt5.QtCore import QMimeData, QPoint, Qt, QTimer
from PyQt5.QtGui import QDropEvent, QFontMetrics
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from masked_strand import MaskedStrand
from save_load_manager import apply_loaded_strands, load_strands_from_data
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
