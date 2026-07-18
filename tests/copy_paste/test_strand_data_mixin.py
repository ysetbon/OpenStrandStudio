import os
import sys

import pytest


SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src")
)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

from masked_strand import MaskedStrand
from strand import Strand
from strand_data_menu import StrandDataClipboardMixin


class _StubButton:
    def __init__(self, layer_name):
        self.layer_name = layer_name
        self.updates = 0

    def update(self):
        self.updates += 1

    def set_color(self, color):
        self.color = color


class _StubUndoManager:
    def __init__(self):
        self.saves = 0
        self._last_save_time = 99

    def save_state(self):
        self.saves += 1


class _StubCanvas:
    def __init__(self, strands):
        self.strands = strands
        self.undo_redo_manager = _StubUndoManager()

    def update(self):
        pass


class _Panel(StrandDataClipboardMixin):
    def __init__(self, strands):
        self.canvas = _StubCanvas(strands)
        self.layer_buttons = [_StubButton(s.layer_name) for s in strands]
        self.locked_layers = set()
        self.multi_selected_layers = set()
        self.language_code = "en"
        self.current_theme = "light"
        self._initialize_strand_data_clipboard()


def make_strand(start, end, name):
    return Strand(
        QPointF(*start), QPointF(*end), 20, QColor("red"), QColor("black"), 4, 1, name
    )


def make_panel():
    strands = [
        make_strand((0, 0), (100, 0), "1_1"),
        make_strand((0, 50), (100, 50), "1_2"),
        make_strand((0, 100), (100, 100), "1_3"),
    ]
    masked = MaskedStrand(strands[0], strands[1])
    strands.append(masked)
    return _Panel(strands)


def test_copy_marks_source_and_enables_targets():
    panel = make_panel()
    assert panel.copy_strand_data(0)

    assert panel.is_strand_data_copy_source(panel.layer_buttons[0])
    assert not panel.is_strand_data_copy_source(panel.layer_buttons[1])
    assert panel.is_strand_data_paste_target(1)
    assert not panel.is_strand_data_paste_target(3)  # masked

    panel.locked_layers.add(2)
    assert not panel.is_strand_data_paste_target(2)  # locked


def test_chip_paste_on_unticked_layer_hits_that_layer_only():
    panel = make_panel()
    panel.copy_strand_data(0)
    panel.multi_selected_layers = {1, 2}

    assert panel.paste_strand_data_via_chip(1, "start") == 2  # ticked -> all ticked
    assert panel.paste_strand_data_via_chip(2, "end") == 2

    panel.multi_selected_layers = {1}
    assert panel.paste_strand_data_via_chip(2, "start") == 1  # unticked -> alone


def test_batch_paste_is_one_undo_step_and_keeps_clipboard():
    panel = make_panel()
    panel.copy_strand_data(0)
    panel.multi_selected_layers = {1, 2, 3}  # includes the masked layer

    manager = panel.canvas.undo_redo_manager
    saves_before = manager.saves
    assert panel.paste_copied_strand_data("start") == 2  # masked skipped
    assert manager.saves == saves_before + 1
    assert panel.canvas.strand_clipboard is not None  # survives for more pastes


def test_clear_clipboard_removes_indicators():
    panel = make_panel()
    panel.copy_strand_data(0)
    panel.clear_strand_data_clipboard()

    assert panel.canvas.strand_clipboard is None
    assert not panel.is_strand_data_copy_source(panel.layer_buttons[0])
    assert not panel.is_strand_data_paste_target(1)
    assert panel.paste_copied_strand_data("start") == 0
