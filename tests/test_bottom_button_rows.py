"""The layer panel's bottom buttons: one row per action, each BOTTOM_BUTTON_HEIGHT tall.

Strands tab: switch, Draw Names, Lock Layers, New Strand, New Level, Delete
Strand, Deselect All, Delete All (8 rows). Masks tab: switch, New Mask, New
Level, Delete Mask, Deselect All, Delete All (6 rows). At 22 px the Strands
tab takes the same height as the 6 rows of 30 px it replaced. Runs the real
MainWindow offscreen.
"""
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
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QApplication, QPushButton

from layer_panel import LayerPanel
from main_window import MainWindow
from translations import translations

APP = QApplication.instance() or QApplication([])
HEIGHT = LayerPanel.BOTTOM_BUTTON_HEIGHT
SIDE_PADDING = 10  # the action buttons' left and right padding (the switch halves have none)


def pump(ms=60):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


@pytest.fixture(scope="module")
def window():
    win = MainWindow()
    win.show()
    win.resize(1400, 860)
    pump(300)
    yield win
    win.set_language("en")
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


def bottom_widgets(lp):
    """The visible widgets of the bottom panel, top first."""
    layout = lp.deselect_all_button.parentWidget().layout()
    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    return [w for w in widgets if w is not None and w.isVisible()]


def bold_14(widget):
    font = QFont(widget.font())
    font.setBold(True)
    font.setPixelSize(14)
    return QFontMetrics(font)


def test_strands_tab_has_eight_rows(window):
    lp = window.layer_panel
    lp.set_layer_tab("strands")
    pump()
    assert bottom_widgets(lp) == [
        lp.layer_tab_row, lp.draw_names_button, lp.lock_layers_button,
        lp.add_new_strand_button, lp.new_level_button, lp.delete_strand_button,
        lp.deselect_all_button, lp.delete_all_button]


def test_masks_tab_has_six_rows(window):
    lp = window.layer_panel
    lp.set_layer_tab("masks")
    pump()
    assert bottom_widgets(lp) == [
        lp.layer_tab_row, lp.new_mask_button, lp.new_level_mask_button,
        lp.delete_mask_button, lp.deselect_all_button, lp.delete_all_masks_button]
    lp.set_layer_tab("strands")


@pytest.mark.parametrize("tab", ["strands", "masks"])
def test_every_row_is_the_same_height(window, tab):
    lp = window.layer_panel
    lp.set_layer_tab(tab)
    pump()
    assert [w.height() for w in bottom_widgets(lp)] == [HEIGHT] * len(bottom_widgets(lp))
    lp.set_layer_tab("strands")


def test_strands_tab_is_no_taller_than_the_old_six_rows_of_30(window):
    """8 rows at BOTTOM_BUTTON_HEIGHT, 2 px apart, take at most the 6 rows of
    30 px the framed New / Delete rows used (so the layer list keeps its room)."""
    lp = window.layer_panel
    lp.set_layer_tab("strands")
    pump()
    rows = bottom_widgets(lp)
    spread = rows[-1].geometry().bottom() - rows[0].geometry().top() + 1
    assert spread <= 6 * 30 + 5 * 2


@pytest.mark.parametrize("language", sorted(translations))
def test_text_fits_its_row_in_every_language(window, language):
    """14 px bold stays: the line is shorter than the row, and the word is
    narrower than the button less its side padding."""
    window.set_language(language)
    pump()
    lp = window.layer_panel
    problems = []
    for tab in ("strands", "masks"):
        lp.set_layer_tab(tab)
        pump()
        for widget in bottom_widgets(lp):
            buttons = widget.findChildren(QPushButton) if widget is lp.layer_tab_row else [widget]
            for button in buttons:
                padding = 0 if widget is lp.layer_tab_row else SIDE_PADDING
                metrics = bold_14(button)
                if metrics.height() > button.height():
                    problems.append((tab, button.text(), "taller than the row"))
                if metrics.horizontalAdvance(button.text()) > button.width() - 2 * padding:
                    problems.append((tab, button.text(), "wider than the button"))
    lp.set_layer_tab("strands")
    window.set_language("en")
    assert not problems, problems
