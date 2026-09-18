"""Regression test for canvas quality changing during a move-mode drag."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtGui import QPaintEvent
from PyQt5.QtWidgets import QApplication, QWidget

from move_mode import MoveMode


app = QApplication.instance() or QApplication([])


class PaintSpyCanvas(QWidget):
    """Minimal canvas that records calls to its canonical paint path."""

    def __init__(self):
        super().__init__()
        self.use_supersampling = True
        self.canonical_paint_calls = 0

    def paintEvent(self, event):
        self.canonical_paint_calls += 1


class MoveDragRenderQualityTest(unittest.TestCase):
    def test_supersampled_drag_uses_canonical_canvas_paint_path(self):
        canvas = PaintSpyCanvas()
        canvas.resize(320, 240)
        move_mode = MoveMode(canvas)

        move_mode._setup_optimized_paint_handler()
        canvas.paintEvent(QPaintEvent(canvas.rect()))

        self.assertEqual(canvas.canonical_paint_calls, 1)


if __name__ == "__main__":
    unittest.main()
