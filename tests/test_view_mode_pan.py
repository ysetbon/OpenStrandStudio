"""Regression tests for primary-button panning in View mode."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtCore import QEvent, QPointF, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication, QPushButton

from strand_drawing_canvas import StrandDrawingCanvas


app = QApplication.instance() or QApplication([])


class PanButtonPanel:
    def __init__(self):
        self.pan_button = QPushButton()
        self.pan_button.setCheckable(True)
        self.icon_name = None

    def set_layer_panel_button_icon(self, button, name, fallback_text=""):
        self.icon_name = name
        button.setText(fallback_text)


def mouse_event(event_type, pos, button, buttons):
    return QMouseEvent(
        event_type, QPointF(*pos), button, buttons, Qt.NoModifier)


class ViewModePanTest(unittest.TestCase):
    def setUp(self):
        self.canvas = StrandDrawingCanvas()
        self.canvas.resize(800, 600)
        self.canvas.layer_panel = PanButtonPanel()
        self.canvas.set_mode("view")

    def test_left_drag_pans_and_updates_cursor_and_pan_button(self):
        press = mouse_event(
            QEvent.MouseButtonPress, (100, 120),
            Qt.LeftButton, Qt.LeftButton)
        self.canvas.mousePressEvent(press)

        self.assertTrue(self.canvas.view_mode_panning)
        self.assertEqual(self.canvas.cursor().shape(), Qt.ClosedHandCursor)
        self.assertTrue(self.canvas.layer_panel.pan_button.isChecked())
        self.assertEqual(self.canvas.layer_panel.icon_name, "pan_closed.png")

        move = mouse_event(
            QEvent.MouseMove, (145, 150),
            Qt.NoButton, Qt.LeftButton)
        self.canvas.mouseMoveEvent(move)

        self.assertEqual(self.canvas.pan_offset_x, 45)
        self.assertEqual(self.canvas.pan_offset_y, 30)

        release = mouse_event(
            QEvent.MouseButtonRelease, (145, 150),
            Qt.LeftButton, Qt.NoButton)
        self.canvas.mouseReleaseEvent(release)

        self.assertFalse(self.canvas.view_mode_panning)
        self.assertEqual(self.canvas.cursor().shape(), Qt.OpenHandCursor)
        self.assertFalse(self.canvas.layer_panel.pan_button.isChecked())
        self.assertEqual(self.canvas.layer_panel.icon_name, "pan_open.png")

    def test_leaving_view_mode_clears_active_left_pan(self):
        press = mouse_event(
            QEvent.MouseButtonPress, (100, 120),
            Qt.LeftButton, Qt.LeftButton)
        self.canvas.mousePressEvent(press)

        self.canvas.set_mode("select")

        self.assertFalse(self.canvas.view_mode_panning)
        self.assertIsNone(self.canvas.pan_start_pos)
        self.assertFalse(self.canvas.layer_panel.pan_button.isChecked())
        self.assertEqual(self.canvas.cursor().shape(), Qt.PointingHandCursor)


if __name__ == "__main__":
    unittest.main()
