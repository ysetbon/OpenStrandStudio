"""Rotate mode's canvas UI: end triangles, the compass dial and the strand where it started."""

import math
import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtCore import QEvent, QPointF, Qt
from PyQt5.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent
from PyQt5.QtWidgets import QApplication

from attached_strand import AttachedStrand
from rotate_mode import DIAL_RADIUS, FINE_SPEED, TRIANGLE_RADIUS
from strand import Strand
from strand_drawing_canvas import StrandDrawingCanvas


app = QApplication.instance() or QApplication([])


def make_canvas():
    canvas = StrandDrawingCanvas()
    canvas.resize(600, 400)
    canvas.show_control_points = False
    canvas.set_mode("rotate")
    return canvas


def add_strand(canvas, start, end, color=QColor(200, 170, 230)):
    strand = Strand(QPointF(*start), QPointF(*end), canvas.strand_width, color,
                    canvas.default_stroke_color, canvas.stroke_width)
    canvas.add_strand(strand)
    strand.update_shape()
    strand.update_side_line()
    return strand


def attach(canvas, parent, side, end):
    point = parent.end if side == 1 else parent.start
    child = AttachedStrand(parent, QPointF(point), side)
    child.canvas = canvas
    parent.attached_strands.append(child)
    parent.has_circles[side] = True
    child.update(QPointF(*end), reset_control_points=True)
    canvas.add_strand(child)
    return child


def mouse(kind, pos):
    button = Qt.LeftButton if kind != QEvent.MouseMove else Qt.NoButton
    buttons = Qt.NoButton if kind == QEvent.MouseButtonRelease else Qt.LeftButton
    return QMouseEvent(kind, QPointF(*pos), button, buttons, Qt.NoModifier)


class EndTriangleTest(unittest.TestCase):
    def setUp(self):
        self.canvas = make_canvas()
        self.mode = self.canvas.rotate_mode

    def test_triangle_is_centred_on_the_end_and_points_away_from_the_pivot(self):
        strand = add_strand(self.canvas, (100, 200), (300, 200))
        end_tip = QPointF(self.mode.get_end_triangle(strand, 1)[0])
        start_tip = QPointF(self.mode.get_end_triangle(strand, 0)[0])
        self.assertAlmostEqual(end_tip.x(), 300 + TRIANGLE_RADIUS)
        self.assertAlmostEqual(end_tip.y(), 200)
        self.assertAlmostEqual(start_tip.x(), 100 - TRIANGLE_RADIUS)
        self.assertAlmostEqual(start_tip.y(), 200)

    def test_pointer_on_a_triangle_finds_that_end(self):
        strand = add_strand(self.canvas, (100, 200), (300, 200))
        self.assertEqual(self.mode.end_at(QPointF(300 + TRIANGLE_RADIUS - 5, 200)), (strand, 1))
        self.assertEqual(self.mode.end_at(QPointF(100, 200)), (strand, 0))
        self.assertIsNone(self.mode.end_at(QPointF(200, 200)))

    def test_attached_ends_have_no_triangle_and_cannot_be_grabbed(self):
        parent = add_strand(self.canvas, (100, 300), (250, 200))
        child = attach(self.canvas, parent, 1, (400, 120))
        self.assertIsNone(self.mode.end_at(QPointF(250, 200)))
        self.mode.mousePressEvent(mouse(QEvent.MouseButtonPress, (250, 200)))
        self.assertFalse(self.mode.is_rotating)
        # The free ends of both strands still rotate
        self.assertEqual(self.mode.end_at(QPointF(400, 120)), (child, 1))
        self.assertEqual(self.mode.end_at(QPointF(100, 300)), (parent, 0))

    def test_strand_drawn_on_top_wins_where_triangles_overlap(self):
        add_strand(self.canvas, (100, 200), (300, 200))
        top = add_strand(self.canvas, (320, 260), (320, 210))
        self.assertEqual(self.mode.end_at(QPointF(318, 205)), (top, 1))

    def test_hidden_strands_are_skipped(self):
        strand = add_strand(self.canvas, (100, 200), (300, 200))
        strand.is_hidden = True
        self.assertIsNone(self.mode.end_at(QPointF(300, 200)))

    def test_hover_repaints_and_release_refreshes_hover(self):
        strand = add_strand(self.canvas, (100, 200), (300, 200))
        self.mode.mouseMoveEvent(mouse(QEvent.MouseMove, (300, 200)))
        self.assertEqual(self.mode.hovered_end, (strand, 1))
        self.mode.mousePressEvent(mouse(QEvent.MouseButtonPress, (300, 200)))
        self.mode.mouseReleaseEvent(mouse(QEvent.MouseButtonRelease, (500, 380)))
        self.assertIsNone(self.mode.hovered_end)


class DialTest(unittest.TestCase):
    def setUp(self):
        self.canvas = make_canvas()
        self.mode = self.canvas.rotate_mode
        self.strand = add_strand(self.canvas, (100, 200), (300, 200))
        self.mode.mousePressEvent(mouse(QEvent.MouseButtonPress, (300, 200)))

    def angle_of(self, point):
        return math.atan2(point.y() - 200, point.x() - 100)

    def test_grab_records_the_start_angle_and_the_strand(self):
        self.assertTrue(self.mode.is_rotating)
        self.assertAlmostEqual(self.mode.start_angle, 0.0)
        self.assertEqual(self.mode.total_delta, 0.0)
        self.assertIsNotNone(self.mode.before_picture)

    def test_outside_the_dial_the_end_follows_the_pointer(self):
        target = self.mode.target_from_pointer(QPointF(100, 0))  # straight up from the pivot
        self.assertFalse(self.mode.fine)
        self.assertAlmostEqual(self.angle_of(target), -math.pi / 2)
        self.assertAlmostEqual(math.hypot(target.x() - 100, target.y() - 200), 200)

    def test_inside_the_dial_the_end_turns_at_a_quarter_of_the_pointer(self):
        r = DIAL_RADIUS * 0.5
        self.mode.target_from_pointer(QPointF(100 + r, 200))
        self.assertTrue(self.mode.fine)
        target = None
        for i in range(1, 41):
            a = math.radians(-i)  # pointer turns 40 degrees
            target = self.mode.target_from_pointer(QPointF(100 + r * math.cos(a), 200 + r * math.sin(a)))
        self.assertAlmostEqual(math.degrees(self.angle_of(target)), -40 * FINE_SPEED, places=6)

    def test_inside_the_dial_the_end_jumps_to_its_target_without_easing(self):
        r = DIAL_RADIUS * 0.5
        self.mode.mouseMoveEvent(mouse(QEvent.MouseMove, (100 + r, 200)))
        a = math.radians(-20)
        self.mode.mouseMoveEvent(mouse(QEvent.MouseMove, (100 + r * math.cos(a), 200 + r * math.sin(a))))
        self.mode.gradual_move()
        self.assertAlmostEqual(math.degrees(self.angle_of(self.strand.end)), -20 * FINE_SPEED, places=6)
        self.assertAlmostEqual(math.degrees(self.mode.total_delta), -20 * FINE_SPEED, places=6)

    def test_total_turn_adds_up_across_moves(self):
        for degrees in (10, 25, 40):
            a = math.radians(degrees)
            self.mode.update_strand_position(QPointF(100 + 200 * math.cos(a), 200 + 200 * math.sin(a)))
        self.assertAlmostEqual(math.degrees(self.mode.total_delta), 40)

    def test_release_clears_the_rotation(self):
        self.mode.mouseReleaseEvent(mouse(QEvent.MouseButtonRelease, (300, 200)))
        self.assertFalse(self.mode.is_rotating)
        self.assertIsNone(self.mode.before_picture)
        self.assertFalse(self.mode.fine)
        self.assertEqual(self.mode.total_delta, 0.0)

    def test_draw_paints_without_errors_in_every_state(self):
        image = QImage(600, 400, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        painter = QPainter(image)
        try:
            self.mode.draw(painter)                      # rotating
            self.mode.fine = True
            self.mode.total_delta = math.radians(400)    # more than a full turn
            self.mode.draw(painter)
            self.mode.mouseReleaseEvent(mouse(QEvent.MouseButtonRelease, (300, 200)))
            self.mode.mouseMoveEvent(mouse(QEvent.MouseMove, (300, 200)))
            self.mode.draw(painter)                      # hovering
        finally:
            painter.end()


class BeforeStrandTest(unittest.TestCase):
    """The grabbed strand is shown where it started, at half opacity, under the strands."""

    def paint(self, canvas):
        canvas._paintEventInner(QPaintEvent(canvas.rect()))
        factor = canvas.supersampling_factor if canvas.use_supersampling else 1
        return canvas.render_buffer, factor

    def test_original_position_is_painted_at_half_opacity_in_the_supersampled_buffer(self):
        canvas = make_canvas()
        canvas.show_grid = False
        self.assertTrue(canvas.use_supersampling)
        mode = canvas.rotate_mode
        strand = add_strand(canvas, (100, 200), (400, 200))
        mode.mousePressEvent(mouse(QEvent.MouseButtonPress, (400, 200)))
        a = math.radians(-30)
        new_end = QPointF(100 + 300 * math.cos(a), 200 + 300 * math.sin(a))
        mode.update_strand_position(new_end)
        mode.rotating_point = new_end          # as gradual_move does
        canvas.show_move_highlights = False   # keep the triangles out of the sampled pixels
        buffer, f = self.paint(canvas)

        before = QColor.fromRgba(buffer.pixel(int(330 * f), int(212 * f)))   # on the old body, away from the new one
        self.assertGreater(before.alpha(), 100)
        self.assertLess(before.alpha(), 160)
        # on the new body, beside the green direction line along its centre
        lx, ly = 100 + 200 * math.cos(a) - 12 * math.sin(a), 200 + 200 * math.sin(a) + 12 * math.cos(a)
        live = QColor.fromRgba(buffer.pixel(int(lx * f), int(ly * f)))
        self.assertEqual(live.alpha(), 255)
        self.assertEqual((live.red(), live.green(), live.blue()), (200, 170, 230))

        mode.mouseReleaseEvent(mouse(QEvent.MouseButtonRelease, (0, 0)))
        buffer, f = self.paint(canvas)
        self.assertEqual(QColor.fromRgba(buffer.pixel(int(330 * f), int(212 * f))).alpha(), 0)


if __name__ == "__main__":
    unittest.main()
