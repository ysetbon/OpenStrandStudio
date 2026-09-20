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
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QListWidget, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from shrinkable_dialog import (allow_shrinking, cap_to_screen, fit_to_screen,
                               make_shrinkable, refit_floor, relax, scroll_area)

APP = QApplication.instance() or QApplication([])

from main_window import MainWindow  # noqa: E402  (needs the QApplication first)

# Every dialog built here stays referenced for the whole run: several of them
# queue work with QTimer.singleShot(0, self...), which segfaults the
# interpreter if the dialog is collected before it fires.
_KEEP = []

# Smaller than any screen the app runs on: no dialog may demand more
SMALL_SCREEN = (800, 480)


@pytest.fixture(scope='module', autouse=True)
def app_theme():
    """Run under the app's real theme stylesheet, which gives every button a
    min-width: a floor that fits the buttons unstyled can leave the last one
    off the edge once the theme is on."""
    window = keep(MainWindow())
    window.apply_theme('default')
    assert 'QPushButton' in APP.styleSheet()
    yield window
    APP.setStyleSheet('')


def keep(dialog):
    _KEEP.append(dialog)
    return dialog


def shrink(dialog):
    """Show the dialog, drag it down as far as it will go, and check that it
    got all the way to its floor and that the floor fits a small screen."""
    keep(dialog)
    dialog.show()
    APP.processEvents()
    dialog.resize(1, 1)
    APP.processEvents()
    floor = (dialog.minimumWidth(), dialog.minimumHeight())
    assert size_of(dialog) == floor
    assert floor[0] <= SMALL_SCREEN[0] and floor[1] <= SMALL_SCREEN[1], (
        "%s cannot be shrunk to fit a %dx%d screen" % ((type(dialog).__name__,) + SMALL_SCREEN))
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
    return keep(SettingsDialog(None))


def test_settings_dialog_shrinks_and_scrolls_its_pages():
    from settings_dialog import SettingsDialog

    dialog = settings_dialog()
    assert dialog.pages_scroll.widget() is dialog.stacked_widget
    assert dialog.isSizeGripEnabled()

    assert shrink(dialog) == SettingsDialog.SHRUNK_MINIMUM
    # The Settings dialog has no fixed row of its own: its floor is the one
    # it names, whatever the theme does to buttons (they scroll)
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


def test_settings_dialog_keeps_the_size_the_user_chose_when_reopened():
    from settings_dialog import SettingsDialog

    dialog = settings_dialog()
    dialog.show()
    APP.processEvents()
    opened = size_of(dialog)

    # Untouched, a language change or a re-open may re-fit it
    dialog.adjust_dialog_geometry()
    assert size_of(dialog) == opened

    # Dragged down by the user, then closed and re-opened the way
    # MainWindow does it: the size they chose survives
    chosen = (SettingsDialog.SHRUNK_MINIMUM[0] + 60, SettingsDialog.SHRUNK_MINIMUM[1] + 40)
    dialog.resize(*chosen)
    APP.processEvents()
    dialog.hide()
    dialog.adjust_dialog_geometry()
    dialog.show()
    APP.processEvents()
    assert size_of(dialog) == chosen
    dialog.reject()


def test_settings_dialog_opens_fitted_from_the_main_window(app_theme):
    """The real open path: MainWindow builds the dialog, then shows it via
    open_settings_dialog. Nothing on that path may count as the user
    resizing, so the first open is the fitted, screen-capped size."""
    window = app_theme
    window.open_settings_dialog()
    APP.processEvents()
    dialog = keep(window._settings_dialog)
    available = dialog.screen().availableGeometry()
    assert dialog.isVisible()
    assert dialog.height() <= int(available.height() * 0.9)
    assert dialog.width() <= int(available.width() * 0.9)
    assert size_of(dialog) == (dialog._fitted_size.width(), dialog._fitted_size.height())

    # Dragged down by the user, closed, reopened the same way: kept
    chosen = (dialog.minimumWidth() + 60, dialog.minimumHeight() + 40)
    dialog.resize(*chosen)
    APP.processEvents()
    dialog.hide()
    window.open_settings_dialog()
    APP.processEvents()
    assert size_of(dialog) == chosen
    dialog.hide()


def video_player_dialog():
    from settings_dialog import VideoPlayerDialog

    return keep(VideoPlayerDialog('/nonexistent/tutorial.mp4'))


def test_video_player_shrinks_with_its_controls_reachable():
    dialog = video_player_dialog()
    shrink(dialog)
    for button in (dialog.play_button, dialog.pause_button, dialog.close_button):
        assert fully_inside(button, dialog)
    dialog.hide()


def layer_width_dialog():
    from numbered_layer_button import WidthConfigDialog

    strand = SimpleNamespace(width=46, stroke_width=4, width_in_grid_units=None,
                             elliptical_end_caps=False)
    layer_panel = SimpleNamespace(language_code='en')
    return keep(WidthConfigDialog(strand, layer_panel, show_elliptical=True))


def default_width_dialog():
    from settings_dialog import DefaultWidthConfigDialog

    owner = settings_dialog()
    return keep(DefaultWidthConfigDialog(owner))


WIDTH_DIALOGS = (layer_width_dialog, default_width_dialog)


@pytest.mark.parametrize('build', WIDTH_DIALOGS)
def test_width_dialogs_keep_ok_and_cancel_reachable_when_shrunk(build):
    dialog = build()
    shrink(dialog)
    assert fully_inside(dialog.ok_button, dialog)
    assert fully_inside(dialog.cancel_button, dialog)
    dialog.reject()


def stub_canvas():
    return SimpleNamespace(language_code='en', is_dark_mode=False, update=lambda: None)


def strand_shadow_editor():
    from shadow_editor_dialog import ShadowEditorDialog

    strand = SimpleNamespace(layer_name='1_1', color=QColor(200, 170, 230))
    return keep(ShadowEditorDialog(stub_canvas(), strand))


def group_shadow_editor():
    from group_shadow_editor_dialog import GroupShadowEditorDialog

    return keep(GroupShadowEditorDialog(stub_canvas(), 'group', []))


SHADOW_EDITORS = (strand_shadow_editor, group_shadow_editor)


LONG_NAME = '1_1_a_receiving_layer_with_a_name_long_enough_to_widen_the_name_column'


def populated_canvas(names):
    """A canvas whose layer state the shadow editors can read, with real
    receiving layers so their lists fill and their columns get sized."""
    strands = [SimpleNamespace(layer_name=name, color=QColor(200, 170, 230), is_hidden=False,
                               first_selected_strand=None) for name in names]
    canvas = stub_canvas()
    canvas.strands = strands
    canvas.layer_state_manager = SimpleNamespace(
        getOrder=lambda: list(names),
        get_shadow_override=lambda caster, receiver: {},
        get_shadow_visibility=lambda caster, receiver: True,
        get_subtracted_layers=lambda caster, receiver: [])
    return canvas, strands


def shadow_editor_with_long_name():
    from shadow_editor_dialog import ShadowEditorDialog

    canvas, strands = populated_canvas([LONG_NAME, '1_2', '1_3'])
    return keep(ShadowEditorDialog(canvas, strands[-1])), 'toggle_row'


def group_editor_with_long_name():
    from group_shadow_editor_dialog import GroupShadowEditorDialog

    canvas, strands = populated_canvas([LONG_NAME, '1_2', '1_3'])
    return keep(GroupShadowEditorDialog(canvas, 'group', strands)), 'global_toggle_row'


@pytest.mark.parametrize('build', (shadow_editor_with_long_name, group_editor_with_long_name))
def test_shadow_editors_refit_their_floor_once_the_columns_are_sized(build):
    """The toggle row is sized to the list's widest name on a zero-delay
    timer after the dialog is built. The floor measured before that ran
    is stale by then; the row must still be whole at the floor."""
    dialog, row_name = build()
    dialog.show()
    APP.processEvents()  # the deferred _sync_column_widths
    APP.processEvents()
    row = getattr(dialog, row_name)
    assert len(dialog.shadow_items if hasattr(dialog, 'shadow_items') else dialog.all_shadow_items) > 0
    # A floor the row does not fit under would leave it clipped
    assert row.minimumSizeHint().width() <= dialog.minimumWidth() or \
        dialog.minimumWidth() >= int(dialog.screen().availableGeometry().width() * 0.9)
    shrink(dialog)
    assert fully_inside(row, dialog)
    dialog.hide()


def test_refit_floor_is_a_no_op_for_a_dialog_without_a_floor():
    dialog = QDialog()
    QVBoxLayout(dialog).addWidget(QLabel("hi"))
    before = dialog.minimumSize()
    refit_floor(dialog)
    assert dialog.minimumSize() == before


@pytest.mark.parametrize('build', SHADOW_EDITORS)
def test_shadow_editors_shrink_with_close_still_reachable(build):
    dialog = build()
    shrink(dialog)
    close = dialog.button_box.button(QDialogButtonBox.Close)
    assert fully_inside(close, dialog)
    # The toggle row lines up with the list's columns and cannot wrap: it
    # is what sets the floor width, and it is whole there
    row = dialog.toggle_row if hasattr(dialog, 'toggle_row') else dialog.global_toggle_row
    assert fully_inside(row, dialog)
    dialog.hide()


def mask_grid_dialog():
    from mask_grid_dialog import MaskGridDialog

    strands = [SimpleNamespace(layer_name='1_%d' % n, color=QColor(200, 170, 230))
               for n in range(1, 5)]
    canvas = stub_canvas()
    canvas.strands = strands
    canvas._resolve_group_strands = lambda name: {'strands': strands}
    return keep(MaskGridDialog(canvas, 'group'))


def strand_angle_dialog():
    from group_layers import StrandAngleEditDialog

    group = {'strands': [], 'layers': [], 'editable_layers': []}
    return keep(StrandAngleEditDialog('group', group, stub_canvas()))


def test_mask_grid_dialog_shrinks_with_its_grid_scrolling():
    dialog = mask_grid_dialog()
    shrink(dialog)
    assert fully_inside(dialog.apply_button, dialog)
    assert fully_inside(dialog.close_button, dialog)
    dialog.hide()


def test_strand_angle_dialog_keeps_its_x_angle_row_whole():
    dialog = strand_angle_dialog()
    shrink(dialog)
    assert fully_inside(dialog.x_angle_input, dialog)
    for button in (dialog.minus_minus_button, dialog.plus_plus_button):
        assert fully_inside(button, dialog)
    dialog.hide()


EVERY_DIALOG = ((settings_dialog, mask_grid_dialog, strand_angle_dialog, video_player_dialog) +
                WIDTH_DIALOGS + SHADOW_EDITORS)


@pytest.mark.parametrize('build', EVERY_DIALOG)
def test_no_dialog_demands_more_room_than_a_small_screen(build):
    dialog = build()
    shrink(dialog)
    assert dialog.isSizeGripEnabled(), "%s has no size grip" % type(dialog).__name__
    dialog.hide()


def popup_background(combo):
    """Open the combo box's drop-down list and report the colour its list
    paints behind the entries, as a lower-case #rrggbb string.

    Rendered onto magenta on purpose: a list whose background rule has been
    made transparent paints nothing there, so the magenta shows through
    where the user would see a black box with invisible entries."""
    combo.showPopup()
    APP.processEvents()
    view = combo.view()
    canvas = QPixmap(view.size())
    canvas.fill(QColor('magenta'))
    view.render(canvas)
    # Sample just inside the left edge, below the first entry's icon column
    colour = QColor(canvas.toImage().pixel(3, view.height() // 2 + 20)).name()
    combo.hidePopup()
    APP.processEvents()
    return colour


def test_scroll_area_leaves_its_combo_box_lists_a_background():
    """The see-through viewport must not reach into the drop-down lists.

    A stylesheet with no selector applies to every descendant, and a combo
    box's list is a child window of the combo box: the Settings dialog's
    theme and language lists came up as black boxes with their entries
    unreadable once the pages moved into the scroll area."""
    dialog = keep(QDialog())
    layout = QVBoxLayout(dialog)
    page = QWidget()
    page_layout = QVBoxLayout(page)
    combo = QComboBox()
    combo.setStyleSheet("QComboBox { padding: 8px; }")
    for name in ('Default', 'Light', 'Dark'):
        combo.addItem(name)
    page_layout.addWidget(combo)
    area = scroll_area(dialog)
    area.setWidget(page)
    layout.addWidget(area)
    dialog.show()
    APP.processEvents()
    assert popup_background(combo) != '#ff00ff'
    dialog.hide()


def test_settings_dialog_theme_and_language_lists_keep_a_background():
    dialog = settings_dialog()
    dialog.show()
    APP.processEvents()
    for combo in (dialog.theme_combobox, dialog.language_combobox):
        assert popup_background(combo) != '#ff00ff', (
            "%s drop-down list paints no background" % combo.objectName())
    dialog.hide()
