"""Level blocks: what a level row does beyond marking a storey.

- the chevrons inside the level button fold the block above (the layers the
  level carries) and the block below; folded layers are hidden entirely
- a click on the name selects the level's block: the panel frames it and
  Move, Attach and Rotate only find its strands, unless "move only the
  selected strand" is on
- each level has a colour (the theme's purple by default, a Default Level
  Color from the settings, or one picked with Recolor), saved with the project
- the ground (level 0) can get a line under the bottom layer
- on the Masks tab, Move up / Move down and dragging move masks between
  levels, never below their two strands' level
- the level menu is built like the layers' menus

Runs the real MainWindow offscreen on tests/levels/continue_2x2.json.
"""
import json

import pytest
from PyQt5.QtCore import QMimeData, QPoint, QPointF, Qt
from PyQt5.QtGui import QColor, QDropEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMenu, QWidgetAction

from test_layer_levels import (assert_consistent, find, lift_3_4_and_2_4, list_order,  # noqa: F401
                               pump, window)
from level_button import (GroundRow, LevelRow, PANEL_BACKGROUNDS, THEME_LEVEL_COLORS,
                          contrast_ratio, legible_color, preset_color)
from masked_strand import MaskedStrand
from numbered_layer_button import HoverLabel, build_menu_stylesheet
from save_load_manager import (load_strands_from_data, mask_own_level, serialize_project_state,
                               strand_level)
from translations import translations


@pytest.fixture(autouse=True)
def no_settings_file_writes(monkeypatch):
    """Showing the ground line saves the user's settings; keep test runs
    from writing them."""
    from settings_dialog import SettingsDialog
    monkeypatch.setattr(SettingsDialog, "save_settings_to_file", lambda self: None)


def masks(win):
    return [s for s in win.canvas.strands if isinstance(s, MaskedStrand)]


def strand_levels(win):
    return {s.layer_name: s.level for s in win.canvas.strands if not isinstance(s, MaskedStrand)}


def click(widget, x):
    QTest.mouseClick(widget, Qt.LeftButton, Qt.NoModifier, QPoint(x, widget.height() // 2))
    pump()


def drop_below(lp, source_widget, target_widget):
    """Drag *source_widget* (a layer button or level row) to just under *target_widget*."""
    layout = lp.scroll_layout
    target_bottom = target_widget.mapTo(lp.scroll_content, QPoint(0, target_widget.height())).y()
    mime = QMimeData()
    mime.setData("application/x-layerbutton-index", str(layout.indexOf(source_widget)).encode())
    lp.dropEvent(QDropEvent(QPoint(20, target_bottom + 2), Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier))
    lp.refresh()
    pump(100)


# --- folding -----------------------------------------------------------------

def test_chevrons_inside_the_button_fold_the_blocks(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    before = [s.layer_name for s in window.canvas.strands]
    button = lp.level_rows[0].button
    click(button, 5)  # left chevron: the layers Level 1 carries
    assert lp.is_level_folded(1)
    assert "2_4" not in list_order(lp) and "3_4" not in list_order(lp)
    assert "2_3" in list_order(lp)
    click(button, button.width() - 5)  # right chevron: the ground under it
    assert lp.is_level_folded(0) and "2_3" not in list_order(lp)
    assert list_order(lp) == ["Level 1"]
    # Folding is only a view: nothing about the design changed
    assert [s.layer_name for s in window.canvas.strands] == before
    click(button, 5)
    click(button, button.width() - 5)
    assert not lp.folded_levels and "2_4" in list_order(lp) and "2_3" in list_order(lp)
    assert_consistent(window)


def test_selecting_a_folded_layer_unfolds_its_block(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.toggle_level_fold(1)
    pump()
    lp.select_layer(window.canvas.strands.index(find(window, "3_4")))
    pump()
    assert not lp.is_level_folded(1) and "3_4" in list_order(lp)


# --- selecting a level's block ---------------------------------------------

def test_clicking_the_name_selects_the_block_and_limits_the_tools(window):
    lp = window.layer_panel
    canvas = window.canvas
    lift_3_4_and_2_4(window)
    button = lp.level_rows[0].button
    click(button, button.width() // 2)
    assert lp.level_scope() == 1
    inside, outside = find(window, "3_4"), find(window, "2_3")
    assert canvas.is_strand_in_level_scope(inside) and not canvas.is_strand_in_level_scope(outside)
    assert canvas.move_mode._is_strand_allowed_by_selection(inside)
    assert not canvas.move_mode._is_strand_allowed_by_selection(outside)
    assert not canvas.attach_mode._is_strand_in_level_scope(outside)
    # "Move only the selected strand" wins: the level selection pauses
    canvas.move_selected_only = True
    assert canvas.is_strand_in_level_scope(outside)
    canvas.move_selected_only = False
    click(button, button.width() // 2)
    assert lp.level_scope() is None and canvas.is_strand_in_level_scope(outside)


def test_the_frame_is_drawn_in_the_level_colour(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.set_level_color(1, "preset:teal")
    lp.set_level_scope(1)
    pump(150)
    image = lp.scroll_content.grab().toImage()
    inside = find(window, "3_4")
    button = lp.layer_buttons[window.canvas.strands.index(inside)]
    y = button.mapTo(lp.scroll_content, QPoint(0, button.height() // 2)).y()
    assert QColor(image.pixel(0, y)).name() == lp.level_color(1).name()
    assert QColor(image.pixel(lp.scroll_content.width() - 1, y)).name() == lp.level_color(1).name()
    # Nothing framed outside the block
    below = lp.layer_buttons[window.canvas.strands.index(find(window, "2_3"))]
    y = below.mapTo(lp.scroll_content, QPoint(0, below.height() // 2)).y()
    assert QColor(image.pixel(0, y)).name() != lp.level_color(1).name()


def test_choosing_a_layer_outside_the_block_ends_the_selection(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.set_level_scope(1)
    lp.select_layer(window.canvas.strands.index(find(window, "2_4")))
    assert lp.level_scope() == 1
    lp.select_layer(window.canvas.strands.index(find(window, "2_3")))
    assert lp.level_scope() is None


def test_new_strands_land_on_the_selected_level(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.new_level_button.click()  # empty Level 2 on top
    pump()
    lp.set_level_scope(1)
    template = find(window, "1_1")
    new = type(template)(QPointF(1080, 532), QPointF(1424, 532), 46)
    new.layer_name, new.set_number = "5_1", 5
    window.canvas.strands.append(new)
    lp.refresh()
    pump()
    assert new.level == 1


# --- colours -----------------------------------------------------------------

@pytest.mark.parametrize("theme", ["default", "light", "dark"])
def test_default_level_colour_follows_the_theme(window, theme):
    lp = window.layer_panel
    lp.new_level_button.click()
    window.apply_theme(theme)
    pump(150)
    assert lp.level_color(1) == QColor(THEME_LEVEL_COLORS[theme])
    assert contrast_ratio(lp.level_color(1), PANEL_BACKGROUNDS[theme]) >= 4
    row = lp.level_rows[0]
    image = row.grab().toImage()
    assert QColor(image.pixel(0, row.height() - 2)) == QColor(THEME_LEVEL_COLORS[theme])


def test_recolor_is_saved_undone_and_follows_removed_levels(window):
    lp = window.layer_panel
    undo = lp.undo_redo_manager
    undo.save_state(action="test.start")
    lp.new_level_button.click()
    lp.new_level_button.click()
    pump()
    lp.set_level_color(2, "preset:rose")
    pump()
    assert lp.level_color(2) == preset_color("rose", lp.current_theme)
    data = serialize_project_state(window.canvas.strands, {}, window.canvas)
    assert data["level_colors"] == {"2": "preset:rose"}
    undo.undo()
    pump(150)
    assert lp.level_color_value(2) is None
    undo.redo()
    pump(150)
    assert lp.level_color_value(2) == "preset:rose"
    lp.remove_level(1)  # Level 2 becomes Level 1, colour and all
    pump()
    assert lp.level_color_value(1) == "preset:rose"


def test_settings_default_level_colour(window):
    lp = window.layer_panel
    dialog = window.settings_dialog
    lp.new_level_button.click()
    pump()
    dialog.set_default_level_color(QColor("#d04040"), save=False)
    assert lp.level_color(1) == legible_color(QColor("#d04040"), lp.current_theme)
    assert dialog._default_level_color_setting() == "208,64,64,255"
    lp.set_level_color(1, "preset:blue")  # a level's own colour wins
    assert lp.level_color(1) == preset_color("blue", lp.current_theme)
    lp.set_level_color(1, None)
    dialog.set_default_level_color(None, save=False)
    assert lp.level_color(1) == QColor(THEME_LEVEL_COLORS[lp._level_theme()])
    assert dialog._default_level_color_setting() == "theme"


def test_custom_colours_stay_legible_on_the_panel():
    for theme, background in PANEL_BACKGROUNDS.items():
        for color in ("#ffffff", "#f0f0f0", "#000000", "#202020", "#ffff00"):
            assert contrast_ratio(legible_color(QColor(color), theme), background) >= 3, (theme, color)


def test_every_language_has_the_level_strings():
    keys = [k for k in translations["en"] if k.startswith(("level_fold", "level_unfold", "level_select",
                                                           "level_deselect", "level_recolor", "level_color_",
                                                           "level_show_ground", "level_hide_ground",
                                                           "default_level_color"))]
    assert len(keys) == 20
    for code, texts in translations.items():
        assert all(k in texts for k in keys), code


# --- the ground line -----------------------------------------------------------

def test_ground_line_closes_the_ground_block(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.set_ground_line_shown(True)
    pump()
    layout = lp.scroll_layout
    assert isinstance(layout.itemAt(layout.count() - 1).widget(), GroundRow)
    assert_consistent(window)
    click(lp.ground_row, 20)
    assert lp.level_scope() == 0
    assert window.canvas.is_strand_in_level_scope(find(window, "2_3"))
    assert not window.canvas.is_strand_in_level_scope(find(window, "3_4"))
    # Dragging still works with the line in the list
    drop_below(lp, lp.layer_buttons[window.canvas.strands.index(find(window, "3_4"))],
               lp.layer_buttons[window.canvas.strands.index(find(window, "2_3"))])
    assert find(window, "3_4").level == 0
    assert isinstance(layout.itemAt(layout.count() - 1).widget(), GroundRow)
    assert_consistent(window)
    lp.set_ground_line_shown(False)
    pump()
    assert lp.ground_row is None and lp.level_scope() is None


def test_no_ground_line_without_levels(window):
    lp = window.layer_panel
    lp.set_ground_line_shown(True)
    pump()
    assert lp.ground_row is None
    lp.new_level_button.click()
    pump()
    assert lp.ground_row is not None
    lp.remove_level(1)
    pump()
    assert lp.ground_row is None


# --- the Masks tab -------------------------------------------------------------

def test_masks_tab_moves_masks_between_levels(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    levels_before = strand_levels(window)
    lp.set_layer_tab("masks")
    pump()
    assert not lp.can_move_level(1, up=True)  # no mask on Level 1 yet
    assert lp.can_move_level(1, up=False)
    top_mask = masks(window)[-1]  # the highest mask on the ground
    lp.move_level(1, up=False)
    pump()
    assert strand_level(top_mask, 1) == 1 and mask_own_level(top_mask) == 1
    order = list_order(lp)
    assert order.index(top_mask.layer_name) < order.index("Level 1")
    assert all(strand_level(m, 1) == 0 for m in masks(window) if m is not top_mask)
    assert strand_levels(window) == levels_before  # strands stay where they were
    strands = window.canvas.strands
    assert strands.index(top_mask) > max(strands.index(find(window, n)) for n in ("3_4", "2_4"))
    # Move up gives it back to the ground, where it follows its strands again
    assert lp.can_move_level(1, up=True)
    lp.move_level(1, up=True)
    pump()
    assert strand_level(top_mask, 1) == 0 and mask_own_level(top_mask) is None
    assert_consistent(window)


def test_a_mask_never_goes_below_its_strands(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    for name in ("3_3", "1_2"):  # both strands of 3_3_1_2 onto Level 1
        find(window, name).level = 1
    lp.refresh()
    pump()
    lp.set_layer_tab("masks")
    pump()
    mask = find(window, "3_3_1_2")
    assert strand_level(mask, 1) == 1
    lowest_on_level_1 = [m for m in masks(window) if strand_level(m, 1) == 1][0]
    assert lowest_on_level_1 is mask
    assert not lp.can_move_level(1, up=True)


def test_dragging_the_level_row_on_the_masks_tab(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    levels_before = strand_levels(window)
    lp.set_layer_tab("masks")
    pump()
    visible_masks = [b for b in lp.layer_buttons if not b.isHidden()]
    lowest = max(visible_masks, key=lambda b: lp.scroll_layout.indexOf(b))
    drop_below(lp, lp.level_rows[0], lowest)  # the row under every mask
    assert all(strand_level(m, 1) == 1 for m in masks(window))
    assert strand_levels(window) == levels_before
    assert_consistent(window)


def test_raised_masks_are_saved(window):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    lp.set_layer_tab("masks")
    pump()
    top_mask = masks(window)[-1]
    lp.move_level(1, up=False)
    pump()
    data = json.loads(json.dumps(serialize_project_state(window.canvas.strands, {}, window.canvas)))
    entry = next(s for s in data["strands"] if s["layer_name"] == top_mask.layer_name)
    assert entry["level"] == 1
    loaded = load_strands_from_data(data, window.canvas)
    again = next(s for s in loaded[0] if s.layer_name == top_mask.layer_name)
    assert mask_own_level(again) == 1


# --- the menu --------------------------------------------------------------------

def test_level_menu_is_built_like_the_layer_menus(window, monkeypatch):
    lp = window.layer_panel
    lift_3_4_and_2_4(window)
    menus = []
    monkeypatch.setattr(QMenu, "exec_", lambda self, *a, **k: menus.append(self))
    row = lp.level_rows[0]
    row.show_menu(QPoint(5, 5))
    menu = menus[0]
    theme = lp.current_theme
    assert menu.styleSheet() == build_menu_stylesheet(theme)
    rows = [a for a in menu.actions() if not a.isSeparator()]
    assert rows and all(isinstance(a, QWidgetAction) and isinstance(a.defaultWidget(), HoverLabel)
                        for a in rows)
    by_text = {a.defaultWidget().text(): a for a in rows}
    assert by_text[lp.level_text("level_move_up")].isEnabled() == lp.can_move_level(1, up=True)
    assert by_text[lp.level_text("level_move_down")].isEnabled() == lp.can_move_level(1, up=False)
    assert lp.level_text("level_recolor") in by_text
    # On the Masks tab, Move is offered whenever a mask can pass the row
    lp.set_layer_tab("masks")
    pump()
    row.show_menu(QPoint(5, 5))
    by_text = {a.defaultWidget().text(): a for a in menus[-1].actions() if not a.isSeparator()}
    assert by_text[lp.level_text("level_move_down")].isEnabled()
