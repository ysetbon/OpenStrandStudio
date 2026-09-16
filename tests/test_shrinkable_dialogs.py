"""Dialogs the user can drag down to any size.

A dialog laid out for a roomy screen used to carry a minimum size big
enough for everything inside it, so on a short screen its bottom row of
buttons sat below the edge of the display with no way to reach it. Each
dialog here now either scrolls its body (shrinkable_dialog.make_shrinkable)
or already had a scrolling body and just needed the floor dropped
(shrinkable_dialog.allow_shrinking).

The checks are geometric - resize to the floor, then ask where the buttons
ended up - because the thing under test is what the layout does with less
space than its content wants, which a size hint on its own would not show.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QListWidget, QPushButton, QScrollArea, QVBoxLayout)

from shrinkable_dialog import (allow_shrinking, cap_to_screen, fit_to_screen,
                               make_shrinkable, relax)

APP = QApplication.instance() or QApplication([])

# Dialogs stay referenced for the whole run: several of them queue work with
# QTimer.singleShot(0, self...), which aborts the interpreter if the dialog is
# collected before it fires.
_KEEP = []

# Smaller than any screen the app runs on: no dialog may demand more
SMALL_SCREEN = (800, 480)


def shrink(dialog):
    """Show the dialog and drag it down as far as it will go."""
    _KEEP.append(dialog)
    dialog.show()
    APP.processEvents()
    dialog.resize(1, 1)
    APP.processEvents()
    return size_of(dialog)


def size_of(widget):
    return (widget.width(), widget.height())


def fully_inside(widget, dialog):
    """Is ``widget`` drawn within the dialog rather than off its edge?"""
    top_left = widget.mapTo(dialog, widget.rect().topLeft())
    return (widget.isVisible() and widget.height() > 0 and
            top_left.y() >= 0 and top_left.y() + widget.height() <= dialog.height() and
            top_left.x() >= 0 and top_left.x() + widget.width() <= dialog.width())


# ----------------------------------------------------------------------
# The helpers
# ----------------------------------------------------------------------
def test_make_shrinkable_scrolls_the_body_and_pins_the_header_and_buttons():
    dialog = QDialog()
    body = QVBoxLayout(dialog)
    header = QLabel("Header")
    body.addWidget(header)
    rows = [QLabel("row %d" % index) for index in range(20)]
    for row in rows:
        body.addWidget(row)
    buttons = QHBoxLayout()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    buttons.addWidget(ok)
    buttons.addWidget(cancel)
    body.addLayout(buttons)

    area = make_shrinkable(dialog, minimum=(300, 200), header=[header], pinned=[buttons],
                           fit=False)

    # Header and buttons stayed with the dialog; the rows moved into the area
    assert isinstance(area, QScrollArea) and area.widget() is not None
    assert header.parentWidget() is dialog and ok.parentWidget() is dialog
    assert rows[0].parentWidget() is area.widget()
    assert dialog.layout().count() == 3  # header, scroll area, button row

    assert shrink(dialog) == (300, 200)
    assert fully_inside(header, dialog)
    assert fully_inside(ok, dialog) and fully_inside(cancel, dialog)
    # The rows that no longer fit are reached by scrolling, not gone
    assert area.verticalScrollBar().maximum() > 0
    dialog.reject()


def test_make_shrinkable_leaves_a_dialog_with_no_layout_alone():
    dialog = QDialog()
    assert make_shrinkable(dialog) is None


def test_relax_lets_a_wrapped_paragraph_stop_setting_the_floor():
    dialog = QDialog()
    layout = QVBoxLayout(dialog)
    paragraph = QLabel("A long explanation that wraps over several lines. " * 8)
    paragraph.setWordWrap(True)
    layout.addWidget(paragraph)
    layout.addWidget(QListWidget())

    tall = dialog.minimumSizeHint().height()
    relax(paragraph)
    assert dialog.minimumSizeHint().height() < tall
    dialog.reject()


def test_relax_rejects_a_keyword_it_does_not_know():
    with pytest.raises(TypeError):
        relax(QLabel("x"), heigth=4)


def test_cap_to_screen_opens_no_larger_than_the_screen():
    dialog = QDialog()
    QVBoxLayout(dialog).addWidget(QLabel("hi"))
    dialog.setMinimumSize(200, 150)
    available = dialog.screen().availableGeometry()

    cap_to_screen(dialog, 100000, 100000)
    assert dialog.width() <= available.width() and dialog.height() <= available.height()

    # Never smaller than the floor, however little room there is
    cap_to_screen(dialog, 10, 10)
    assert size_of(dialog) == (200, 150)

    fit_to_screen(dialog)
    assert dialog.width() <= available.width() and dialog.height() <= available.height()
    dialog.reject()


# ----------------------------------------------------------------------
# The dialogs
# ----------------------------------------------------------------------
def settings_dialog():
    from settings_dialog import SettingsDialog
    return SettingsDialog(None)


def test_settings_dialog_shrinks_and_scrolls_its_pages():
    from settings_dialog import SettingsDialog

    dialog = settings_dialog()
    assert dialog.pages_scroll.widget() is dialog.stacked_widget
    assert dialog.isSizeGripEnabled()

    assert shrink(dialog) == SettingsDialog.SHRUNK_MINIMUM
    # Both halves are still there at the floor: pick a category, read a page
    assert dialog.categories_list.width() > 0 and dialog.pages_scroll.width() > 0
    dialog.categories_list.setCurrentRow(0)
    dialog.stacked_widget.setCurrentIndex(0)
    APP.processEvents()
    assert dialog.stacked_widget.currentWidget() is not None
    dialog.reject()


def test_settings_dialog_still_opens_wide_enough_for_its_translations():
    dialog = settings_dialog()
    dialog.show()
    APP.processEvents()
    available = dialog.screen().availableGeometry()

    widest_page = max(dialog.stacked_widget.widget(index).sizeHint().width()
                      for index in range(dialog.stacked_widget.count()))
    wanted = dialog.categories_list.width() + widest_page
    assert dialog.width() >= min(wanted, int(available.width() * 0.9))
    assert dialog.width() <= available.width() and dialog.height() <= available.height()
    dialog.reject()


def layer_width_dialog():
    from numbered_layer_button import WidthConfigDialog

    strand = SimpleNamespace(width=46, stroke_width=4, width_in_grid_units=None,
                             elliptical_end_caps=False)
    layer_panel = SimpleNamespace(language_code='en')
    return WidthConfigDialog(strand, layer_panel, show_elliptical=True)


def default_width_dialog():
    from settings_dialog import DefaultWidthConfigDialog

    owner = settings_dialog()
    dialog = DefaultWidthConfigDialog(owner)
    dialog._owner = owner  # the settings dialog must outlive the one it opened
    return dialog


WIDTH_DIALOGS = (layer_width_dialog, default_width_dialog)


@pytest.mark.parametrize('build', WIDTH_DIALOGS)
def test_width_dialogs_keep_ok_and_cancel_reachable_when_shrunk(build):
    dialog = build()
    shrink(dialog)
    assert dialog.width() <= 300 and dialog.height() <= 200
    assert fully_inside(dialog.ok_button, dialog)
    assert fully_inside(dialog.cancel_button, dialog)
    dialog.reject()


def stub_canvas():
    return SimpleNamespace(language_code='en', is_dark_mode=False, update=lambda: None)


def strand_shadow_editor():
    from shadow_editor_dialog import ShadowEditorDialog

    strand = SimpleNamespace(layer_name='1_1', color=QColor(200, 170, 230))
    return ShadowEditorDialog(stub_canvas(), strand)


def group_shadow_editor():
    from group_shadow_editor_dialog import GroupShadowEditorDialog

    return GroupShadowEditorDialog(stub_canvas(), 'group', [])


SHADOW_EDITORS = (strand_shadow_editor, group_shadow_editor)


@pytest.mark.parametrize('build', SHADOW_EDITORS)
def test_shadow_editors_shrink_with_close_still_reachable(build):
    dialog = build()
    shrink(dialog)
    assert dialog.width() <= 360 and dialog.height() <= 280
    close = dialog.button_box.button(QDialogButtonBox.Close)
    assert fully_inside(close, dialog)
    dialog.hide()


def mask_grid_dialog():
    from mask_grid_dialog import MaskGridDialog

    strands = [SimpleNamespace(layer_name='1_%d' % n, color=QColor(200, 170, 230))
               for n in range(1, 5)]
    canvas = stub_canvas()
    canvas.strands = strands
    canvas._resolve_group_strands = lambda name: {'strands': strands}
    return MaskGridDialog(canvas, 'group')


def strand_angle_dialog():
    from group_layers import StrandAngleEditDialog

    group = {'strands': [], 'layers': [], 'editable_layers': []}
    return StrandAngleEditDialog('group', group, stub_canvas())


def test_mask_grid_dialog_shrinks_with_its_grid_scrolling():
    dialog = mask_grid_dialog()
    shrink(dialog)
    assert dialog.width() <= 340 and dialog.height() <= 240
    assert fully_inside(dialog.apply_button, dialog)
    assert fully_inside(dialog.close_button, dialog)
    dialog.hide()


EVERY_DIALOG = ((settings_dialog, mask_grid_dialog, strand_angle_dialog) +
                WIDTH_DIALOGS + SHADOW_EDITORS)


@pytest.mark.parametrize('build', EVERY_DIALOG)
def test_no_dialog_demands_more_room_than_a_small_screen(build):
    dialog = build()
    floor = dialog.minimumSize()
    assert (floor.width() <= SMALL_SCREEN[0] and floor.height() <= SMALL_SCREEN[1]), (
        "%s cannot be shrunk to fit a %dx%d screen" %
        (type(dialog).__name__, SMALL_SCREEN[0], SMALL_SCREEN[1]))
    assert dialog.isSizeGripEnabled(), "%s has no size grip" % type(dialog).__name__
    dialog.hide()
