"""Duplicating a group keeps every layer on its level.

A duplicated layer used to start with no level, like a newly drawn strand,
so it landed on the top level: duplicating a box that rests on the ground
and on Level 1 put the whole copy on Level 1. Its masks then could not be
moved down to the ground either, since a mask never sits below its two
strands.

tests/levels/box_ground_and_level1.json is the real box: 2_1 ... 1_3 and
mask 2_2_1_3 on the ground, 2_4, 1_4, 2_5, 1_5 and mask 2_4_1_5 on Level 1,
all in group "box". Its copy is sets 3 and 4 (3_x copies 1_x, 4_x copies
2_x) in group "box(1)".

Runs the real MainWindow offscreen.
"""
import contextlib
import io
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
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from masked_strand import MaskedStrand
from save_load_manager import (apply_project_state, keep_masks_on_top, mask_base_level,
                               mask_own_level, serialize_project_state, set_mask_level,
                               strand_level)

APP = QApplication.instance() or QApplication([])
DESIGN = Path(__file__).resolve().parent / "levels" / "box_ground_and_level1.json"

GROUND = ['2_1', '1_1', '2_2', '1_2', '2_3', '1_3']
LEVEL_1 = ['2_4', '1_4', '2_5', '1_5']
# Original layer -> its copy in box(1): set 1 -> 3, set 2 -> 4
COPY_OF = {name: {'1': '3', '2': '4'}[name[0]] + name[1:] for name in GROUND + LEVEL_1}
COPY_OF.update({'2_2_1_3': '4_2_3_3', '2_4_1_5': '4_4_3_5'})


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


@pytest.fixture
def window():
    win = MainWindow()
    apply_project_state(win.canvas, json.loads(DESIGN.read_text(encoding="utf-8")))
    win.canvas.selected_strand = None
    win.layer_panel.refresh()
    win.show()
    win.resize(1600, 900)
    pump(200)
    yield win
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(20)


def group_panel(win):
    return win.canvas.group_layer_manager.group_panel


def duplicate(win, group='box'):
    with contextlib.redirect_stdout(io.StringIO()):  # duplicate_group logs every layer
        group_panel(win).duplicate_group(group)
    pump(100)


def layer(win, name):
    return next(s for s in win.canvas.strands if s.layer_name == name)


def level_of(win, name):
    return strand_level(layer(win, name), win.canvas.level_count)


def levels(win):
    return {s.layer_name: strand_level(s, win.canvas.level_count) for s in win.canvas.strands}


def render(win, visible):
    """The canvas with only the layers in *visible* shown."""
    for strand in win.canvas.strands:
        strand.is_hidden = strand.layer_name not in visible
    win.canvas.update()
    pump(50)
    return win.canvas.grab().toImage()


# ------------------------------------------------------------------ the design

def test_the_design_rests_on_the_ground_and_on_level_1(window):
    assert window.canvas.level_count == 1
    assert 'box' in group_panel(window).groups
    assert {n: level_of(window, n) for n in GROUND} == dict.fromkeys(GROUND, 0)
    assert {n: level_of(window, n) for n in LEVEL_1} == dict.fromkeys(LEVEL_1, 1)
    assert level_of(window, '2_2_1_3') == 0
    assert level_of(window, '2_4_1_5') == 1


# ------------------------------------------------------- each copy's own level

@pytest.mark.parametrize('original', GROUND + LEVEL_1 + ['2_2_1_3', '2_4_1_5'])
def test_each_copy_lands_on_the_level_of_the_layer_it_copies(window, original):
    expected = level_of(window, original)
    duplicate(window)
    assert level_of(window, COPY_OF[original]) == expected


def test_the_copy_of_a_ground_layer_is_not_raised_to_level_1(window):
    duplicate(window)
    assert [level_of(window, COPY_OF[n]) for n in GROUND] == [0] * len(GROUND)


def test_every_copy_carries_a_level_of_its_own(window):
    """Not None: a layer with no level would follow wherever new strands land."""
    duplicate(window)
    for original in GROUND + LEVEL_1:
        assert layer(window, COPY_OF[original]).level == layer(window, original).level


def test_duplicating_leaves_the_originals_where_they_were(window):
    before = levels(window)
    duplicate(window)
    after = levels(window)
    assert {n: after[n] for n in before} == before


def test_duplicating_adds_no_level(window):
    duplicate(window)
    assert window.canvas.level_count == 1


# ------------------------------------------------------------ the copied masks

def test_the_copied_ground_mask_rests_on_the_ground(window):
    """The mask the user could not move down: 4_2_3_3, made of 4_2 and 3_3."""
    duplicate(window)
    mask = layer(window, '4_2_3_3')
    assert isinstance(mask, MaskedStrand)
    assert mask.first_selected_strand.layer_name == '4_2'
    assert mask.second_selected_strand.layer_name == '3_3'
    assert level_of(window, '4_2') == level_of(window, '3_3') == 0
    assert mask_base_level(mask, window.canvas.level_count) == 0
    assert level_of(window, '4_2_3_3') == 0


def test_the_copied_ground_mask_follows_its_strands(window):
    """On its strands' level a mask keeps no level of its own."""
    duplicate(window)
    assert mask_own_level(layer(window, '4_2_3_3')) is None


def test_the_copied_level_1_mask_stays_on_level_1(window):
    duplicate(window)
    assert level_of(window, '4_4_3_5') == 1
    assert mask_base_level(layer(window, '4_4_3_5'), 1) == 1


def test_a_raised_mask_is_copied_raised(window):
    """A ground mask raised to Level 1 on the Masks tab stays raised in the copy."""
    set_mask_level(layer(window, '2_2_1_3'), 1, 1)
    assert level_of(window, '2_2_1_3') == 1
    duplicate(window)
    assert level_of(window, '4_2') == level_of(window, '3_3') == 0
    assert mask_own_level(layer(window, '4_2_3_3')) == 1
    assert level_of(window, '4_2_3_3') == 1


def test_the_copied_ground_mask_can_be_moved_up_and_back_to_the_ground(window):
    duplicate(window)
    mask = layer(window, '4_2_3_3')
    set_mask_level(mask, 1, 1)
    assert level_of(window, '4_2_3_3') == 1
    set_mask_level(mask, 0, 1)
    assert level_of(window, '4_2_3_3') == 0


# --------------------------------------------------------------- the stack

def test_the_stack_is_ordered_by_level_after_duplicating(window):
    duplicate(window)
    names = [s.layer_name for s in window.canvas.strands]
    assert names == [
        # the ground: its strands, then its masks
        '2_1', '1_1', '2_2', '1_2', '2_3', '1_3',
        '4_1', '3_1', '4_2', '3_2', '4_3', '3_3',
        '2_2_1_3', '4_2_3_3',
        # Level 1
        '2_4', '1_4', '2_5', '1_5',
        '4_4', '3_4', '4_5', '3_5',
        '2_4_1_5', '4_4_3_5',
    ]


def test_the_stack_needs_no_reordering(window):
    duplicate(window)
    strands = window.canvas.strands
    ordered, _ = keep_masks_on_top(strands, (), window.canvas.level_count)
    assert all(a is b for a, b in zip(ordered, strands))


def test_the_layer_panel_shows_the_copies_in_the_right_blocks(window):
    duplicate(window)
    panel = window.layer_panel
    ground = {s.layer_name for s in panel._plain_strands_on(0)}
    level_1 = {s.layer_name for s in panel._plain_strands_on(1)}
    assert ground == set(GROUND) | {COPY_OF[n] for n in GROUND}
    assert level_1 == set(LEVEL_1) | {COPY_OF[n] for n in LEVEL_1}
    assert {s.layer_name for s in panel._masks_on(0)} == {'2_2_1_3', '4_2_3_3'}
    assert {s.layer_name for s in panel._masks_on(1)} == {'2_4_1_5', '4_4_3_5'}


def test_the_copy_is_drawn_exactly_like_the_original(window):
    """The copy sits where the original does: shown alone, each must give the
    same picture, crossings and masks included."""
    duplicate(window)
    original = render(window, set(COPY_OF))
    copy = render(window, set(COPY_OF.values()))
    assert original == copy


# ------------------------------------------------------------- the group

def test_the_copy_group_holds_every_copy(window):
    duplicate(window)
    panel = group_panel(window)
    assert 'box(1)' in panel.groups
    names = {s.layer_name for s in panel.resolve_group_data('box(1)')['strands']}
    assert names == set(COPY_OF.values())


def test_a_copy_of_a_copy_keeps_the_levels_too(window):
    duplicate(window)
    duplicate(window, 'box(1)')
    assert 'box(2)' in group_panel(window).groups
    # box(2) is sets 5 and 6: 5_x copies 3_x, 6_x copies 4_x
    for original in GROUND + LEVEL_1:
        twice = {'1': '5', '2': '6'}[original[0]] + original[1:]
        assert level_of(window, twice) == level_of(window, original)
    assert level_of(window, '6_2_5_3') == 0
    assert level_of(window, '6_4_5_5') == 1


def test_a_group_on_level_1_only_is_copied_onto_level_1(window):
    for name in GROUND:
        layer(window, name).level = 1
    duplicate(window)
    assert all(level_of(window, COPY_OF[n]) == 1 for n in GROUND + LEVEL_1)
    assert level_of(window, '4_2_3_3') == 1


def test_a_group_on_the_ground_only_is_copied_onto_the_ground(window):
    for name in LEVEL_1:
        layer(window, name).level = 0
    duplicate(window)
    assert all(level_of(window, COPY_OF[n]) == 0 for n in GROUND + LEVEL_1)
    assert level_of(window, '4_4_3_5') == 0


def test_layers_spread_over_three_levels_are_copied_onto_the_same_three(window):
    window.canvas.level_count = 3
    spread = dict(zip(GROUND + LEVEL_1, [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]))
    for name, level in spread.items():
        layer(window, name).level = level
    window.layer_panel.keep_masks_on_top()
    window.layer_panel.refresh()
    pump()
    expected = {n: level_of(window, n) for n in COPY_OF}
    duplicate(window)
    assert {n: level_of(window, COPY_OF[n]) for n in COPY_OF} == expected
    assert window.canvas.level_count == 3


def test_a_selected_level_block_does_not_pull_the_copies_onto_it(window):
    """New strands land on the selected level's block; copies keep their own."""
    window.layer_panel.set_level_scope(1)
    assert window.layer_panel.level_scope() == 1
    duplicate(window)
    assert [level_of(window, COPY_OF[n]) for n in GROUND] == [0] * len(GROUND)
    assert level_of(window, '4_2_3_3') == 0


def test_a_project_without_levels_stays_without_levels(window):
    for strand in window.canvas.strands:
        if not isinstance(strand, MaskedStrand):
            strand.level = 0
    window.canvas.level_count = 0
    window.layer_panel.refresh()
    pump()
    duplicate(window)
    assert window.canvas.level_count == 0
    assert set(levels(window).values()) == {0}
    saved = serialize_project_state(window.canvas.strands, window.canvas.groups, window.canvas)
    assert 'level_count' not in saved
    assert all('level' not in s for s in saved['strands'])


# ------------------------------------------------------- saving and undoing

def test_saving_and_reopening_keeps_the_copies_on_their_levels(window):
    duplicate(window)
    expected = levels(window)
    saved = serialize_project_state(window.canvas.strands, window.canvas.groups, window.canvas)
    saved = {s['layer_name']: s.get('level') for s in saved['strands']}
    for original in GROUND + LEVEL_1:
        assert saved[COPY_OF[original]] == expected[original]
    reopened = MainWindow()
    try:
        state = serialize_project_state(window.canvas.strands, window.canvas.groups, window.canvas)
        apply_project_state(reopened.canvas, json.loads(json.dumps(state)))
        assert levels(reopened) == expected
        assert reopened.canvas.level_count == 1
    finally:
        reopened._confirm_close_with_dirty_tabs = lambda *a, **k: True
        reopened.close()
        reopened.deleteLater()


def test_undo_and_redo_of_the_duplicate_keep_the_levels(window):
    manager = window.layer_panel.undo_redo_manager
    manager.save_state()
    before = levels(window)
    duplicate(window)
    after = levels(window)
    assert after[COPY_OF['2_1']] == 0
    manager.undo()
    pump(100)
    assert levels(window) == before
    manager.redo()
    pump(100)
    assert levels(window) == after
