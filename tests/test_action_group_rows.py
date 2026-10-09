"""The layer panel's framed New / Delete rows (src/action_group_row.py).

New [Strand | Level] and Delete [Strand | All] on the Strands tab, New [Mask |
Level] and Delete [Mask | All] on the Masks tab: a plain word, then two short
buttons, all at the panel's 14 px bold. Runs the real MainWindow offscreen.
"""
import math
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
from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton

from action_group_row import ActionGroupRow
from main_window import MainWindow
from translations import translations

APP = QApplication.instance() or QApplication([])


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


def bottom_rows(lp):
    """The visible widgets of the bottom panel, top first."""
    layout = lp.deselect_all_button.parentWidget().layout()
    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    return [w for w in widgets if w is not None and w.isVisible()]


def text_touches_edge(label):
    """True when the painted word reaches the inside edge of the label's
    contents, where Qt clips its painting (the word is cut off)."""
    # grabbed from the row: the label is transparent over the row's background
    image = label.parentWidget().grab(label.geometry()).toImage()
    inner = label.contentsRect()
    rtl = label.layoutDirection() == Qt.RightToLeft
    edge = inner.left() if rtl else inner.right()
    # the background, from the lead-in on the word's other side
    blank = image.width() - 1 if rtl else 0
    background = QColor(image.pixel(blank, image.height() // 2)).lightness()
    return any(abs(QColor(image.pixel(edge, y)).lightness() - background) > 110
               for y in range(image.height()))


def tab_rows(lp, tab):
    return ((lp.new_strand_row, lp.delete_strand_row) if tab == "strands"
            else (lp.new_mask_row, lp.delete_mask_row))


def test_strands_tab_has_five_rows_under_the_switch(window):
    lp = window.layer_panel
    lp.set_layer_tab("strands")
    pump()
    assert bottom_rows(lp) == [lp.layer_tab_row, lp.draw_names_button, lp.lock_layers_button,
                               lp.new_strand_row, lp.delete_strand_row, lp.deselect_all_button]
    lp.set_layer_tab("masks")
    pump()
    assert bottom_rows(lp) == [lp.layer_tab_row, lp.new_mask_row, lp.delete_mask_row,
                               lp.deselect_all_button]
    lp.set_layer_tab("strands")
    pump()


def test_rows_hold_the_right_buttons(window):
    lp = window.layer_panel
    assert lp.new_strand_row.buttons == (lp.add_new_strand_button, lp.new_level_button)
    assert lp.delete_strand_row.buttons == (lp.delete_strand_button, lp.delete_all_button)
    assert lp.new_mask_row.buttons == (lp.new_mask_button, lp.new_level_mask_button)
    assert lp.delete_mask_row.buttons == (lp.delete_mask_button, lp.delete_all_masks_button)
    # The word is a label, never a button
    for row in tab_rows(lp, "strands") + tab_rows(lp, "masks"):
        assert isinstance(row.label, QLabel) and not isinstance(row.label, QPushButton)
    # A row is as tall as a plain bottom button and as wide as the column
    for row in tab_rows(lp, "strands"):
        assert row.height() == lp.deselect_all_button.height()
        assert abs(row.width() - lp.deselect_all_button.width()) <= 1


@pytest.mark.parametrize("lang", sorted(translations))
@pytest.mark.parametrize("tab", ["strands", "masks"])
@pytest.mark.parametrize("theme", ["default", "dark"])
def test_words_fit_at_14px_in_every_language(window, lang, tab, theme):
    lp = window.layer_panel
    lp.set_theme(theme)  # the app applies one at startup; it restyles the panel
    window.set_language(lang)
    lp.set_layer_tab(tab)
    pump()
    _ = translations[lang]
    for row in tab_rows(lp, tab):
        assert row.isVisible()
        # the word in its 14 px bold, plus its 3 + 1 px lead-in and tail
        label_need = ActionGroupRow.text_width(row.label, row.label.text()) + 4
        assert label_need <= row.label.width(), f"{lang}: word '{row.label.text()}' clipped"
        assert "font-size: 14px" in row.label.styleSheet() and "bold" in row.label.styleSheet()
        # the 3 px lead-in sits before the word, on its reading side
        m = row.label.contentsMargins()
        assert (m.left(), m.right()) == ((0, 3) if lang == "he" else (3, 0)), lang
        assert not text_touches_edge(row.label), f"{lang}: word '{row.label.text()}' is cut off"
        for button in row.buttons:
            assert "font-size: 14px" in button.styleSheet(), f"{lang}: '{button.text()}' not 14 px"
            need = row.needed_width(button)
            assert need <= button.width(), f"{lang}: '{button.text()}' needs {need}px, has {button.width()}"
            assert button.toolTip(), f"{lang}: '{button.text()}' has no full name on hover"
    # The full names are the tooltips
    assert lp.add_new_strand_button.toolTip() == _["add_new_strand"]
    assert lp.new_level_button.toolTip() == _["new_level"]
    assert lp.delete_all_button.toolTip() == _["delete_all"]
    assert lp.new_mask_button.toolTip() == _["new_mask"]
    window.set_language("en")
    lp.set_theme("default")
    lp.set_layer_tab("strands")
    pump()


def test_hebrew_puts_the_word_on_the_right(window):
    lp = window.layer_panel
    window.set_language("he")
    pump()
    for row in (lp.new_strand_row, lp.delete_strand_row):
        word_x = row.label.mapTo(row, QPoint(0, 0)).x()
        assert all(word_x > b.mapTo(row, QPoint(0, 0)).x() for b in row.buttons)
    window.set_language("en")
    pump()
    row = lp.new_strand_row
    assert row.label.mapTo(row, QPoint(0, 0)).x() < lp.add_new_strand_button.mapTo(row, QPoint(0, 0)).x()


@pytest.mark.parametrize("theme", ["dark", "light", "default"])
def test_a_theme_keeps_the_row_look(window, theme):
    lp = window.layer_panel
    lp.set_theme(theme)
    pump()
    for row in tab_rows(lp, "strands") + tab_rows(lp, "masks"):
        for button in row.buttons:
            assert button.styleSheet().count(ActionGroupRow.MARK) == 1
            assert "font-size: 14px" in button.styleSheet()
    # The word takes the theme's text colour; the frame has no fill of its own
    from action_group_row import LABEL_COLORS
    for row in tab_rows(lp, "strands") + tab_rows(lp, "masks"):
        assert f"color: {LABEL_COLORS[theme]}" in row.label.styleSheet()
        assert "background-color: transparent" in row.styleSheet()
    # New Mask still copies New Strand's green, and keeps its pressed border
    assert "lightgreen" in ActionGroupRow.base_style(lp.new_mask_button)
    assert "QPushButton:checked" in lp.new_mask_button.styleSheet()
    lp.set_theme("default")
    pump()


def test_buttons_still_do_their_jobs(window):
    lp = window.layer_panel
    lp.add_new_strand_button.setEnabled(True)
    count = getattr(window.canvas, "level_count", 0) or 0
    lp.new_level_button.click()
    pump()
    assert window.canvas.level_count == count + 1
    assert not lp.delete_strand_button.isEnabled()  # nothing selected, as before


@pytest.mark.parametrize("theme", ["default", "light", "dark"])
def test_rows_show_the_panel_background_in_every_theme(window, theme):
    """Inside the frame, beside the word, the pixels are the panel's own
    background in each theme, and the word reads against it."""
    lp = window.layer_panel
    window.apply_theme(theme)
    lp.set_layer_tab("strands")
    pump(120)
    bottom = lp.deselect_all_button.parentWidget()
    image = bottom.grab().toImage()
    row = lp.new_strand_row
    # the panel's background: in the gap just above the row
    top = row.geometry().top()
    panel_bg = QColor(image.pixel(row.geometry().center().x(), top - 2))
    # inside the frame, under the word's top padding
    label_pos = row.label.mapTo(bottom, QPoint(0, 0))
    inside = QColor(image.pixel(label_pos.x() + 2, top + 2))
    assert abs(inside.lightness() - panel_bg.lightness()) <= 6, (theme, inside.name(), panel_bg.name())
    # and the word contrasts with that background
    text = QColor(row.label.styleSheet().split("color: ")[1][:7])
    assert abs(text.lightness() - panel_bg.lightness()) >= 120, (theme, text.name(), panel_bg.name())
    window.apply_theme("default")
    pump()


@pytest.mark.parametrize("lang", sorted(translations))
@pytest.mark.parametrize("theme", ["default", "light", "dark"])
def test_rows_follow_the_mockup_layout_to_the_pixel(window, lang, theme):
    """The layout rule the mockup uses: the word is its text plus 3 + 1 px
    padding, 1 px gaps, and the two buttons share the rest in proportion to
    what their words need (first rounded, second the remainder)."""
    from action_group_row import GAP, WORD_PADDING
    lp = window.layer_panel
    window.apply_theme(theme)
    window.set_language(lang)
    for tab in ("strands", "masks"):
        lp.set_layer_tab(tab)
        pump()
        for row in tab_rows(lp, tab):
            inner = row.width() - 4  # 1 px border and 1 px padding each side
            word = ActionGroupRow.text_width(row.label, row.label.text()) + WORD_PADDING
            assert row.label.width() == word, (lang, row.label.text())
            rest = inner - word - 2 * GAP
            needs = [row.needed_width(b) for b in row.buttons]
            first = int(math.floor(rest * needs[0] / float(sum(needs)) + 0.5))  # halves up
            assert [b.width() for b in row.buttons] == [first, rest - first], (lang, tab)
            # positions, left to right (right to left in Hebrew)
            xs = [row.label.geometry(), row.buttons[0].geometry(), row.buttons[1].geometry()]
            if row.layoutDirection() == Qt.RightToLeft:
                xs = xs[::-1]
            assert xs[0].left() == 2
            assert xs[1].left() == xs[0].right() + 1 + GAP and xs[2].left() == xs[1].right() + 1 + GAP
            assert xs[2].right() == row.width() - 3
            assert all(b.height() == row.height() - 4 for b in row.buttons)
    window.apply_theme("default")
    window.set_language("en")
    lp.set_layer_tab("strands")
    pump()
