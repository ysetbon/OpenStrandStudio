"""Regression test: control point visibility during a move-mode endpoint drag.

Run from anywhere:
    python tests\\control_points\\test_cp_visibility_during_drag.py

Scenario reported by the user (settings = "case #5"):
    - "Show control points only for the selected strand" (show_cp_selected_only) ON
    - "In move mode, allow only to move the selected strand" (move_selected_only) OFF
    - "Draw only affected strand when dragging" (draw_only_affected_strand) OFF
    - third control point enabled

    1_2 is the selected strand. The user grabs 1_1's start point (whose
    control points were NEVER moved - cp1/cp2 still sit on the start) and
    drags it. Expected: 1_1's start control point (green triangle) stays
    hidden, because 1_1 is not the strand the user selected and its curve
    was never shaped. Observed bug: the triangle is drawn riding the
    dragged start point, because the mouse press makes the dragged strand
    the canvas selection (move_mode.py:1411-1417) and the triangle has no
    "was it ever moved" gate (strand_drawing_canvas.py show_triangle_cp).

The test renders canvas.draw_control_points() to an offscreen image and
scans for the pure-green (#008000) triangle fill near each strand's cp1.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# This test lives in tests/control_points/ ; the source modules are in <repo>/src.
_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter
from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from strand import Strand
from strand_drawing_canvas import StrandDrawingCanvas
from move_mode import MoveMode

# --------------------------------------------------------------------------- io
_PASS = 0
_FAIL = 0


def check(name, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("[PASS] %s" % name)
    else:
        _FAIL += 1
        print("[FAIL] %s  ::  %s" % (name, detail))


# ---------------------------------------------------------------- test helpers
GREEN = QColor('green').rgb()  # the control point fill color (#008000)
W, H = 900, 700


def make_virgin_strand(start, end, set_number, layer_name):
    """A strand whose control points were never touched: cp1 == cp2 == start,
    triangle_has_moved == False (the state right after drawing a new strand)."""
    s = Strand(
        QPointF(*start), QPointF(*end), 46,
        color=QColor(200, 170, 230, 255),
        stroke_color=QColor(0, 0, 0, 255),
        stroke_width=4,
        set_number=set_number, layer_name=layer_name,
    )
    s.update_shape()
    s.update_side_line()
    return s


def render_control_points(canvas):
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(Qt.white)
    painter = QPainter(img)
    canvas.draw_control_points(painter)
    painter.end()
    return img


def green_near(img, point, radius=25):
    """True if the pure-green CP fill appears within `radius` px of point."""
    cx, cy = int(point.x()), int(point.y())
    for y in range(max(0, cy - radius), min(H, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(W, cx + radius + 1)):
            if img.pixel(x, y) == GREEN:
                return True
    return False


def build_canvas():
    canvas = StrandDrawingCanvas()
    canvas.resize(W, H)
    # --- the user's settings (case #5) ---
    canvas.show_control_points = True
    canvas.show_cp_selected_only = True
    canvas.move_selected_only = False
    canvas.enable_third_control_point = True
    canvas.enable_curvature_bias_control = False  # not part of this scenario
    canvas.use_supersampling = False  # draw directly into the test image
    return canvas


def reset_selection(canvas, mode):
    canvas.selected_strand = None
    canvas.selected_attached_strand = None
    canvas.truly_moving_strands = []
    for s in canvas.strands:
        s.is_selected = False
    mode.affected_strand = None
    mode.is_moving = False
    mode.is_moving_strand_point = False
    mode.is_moving_control_point = False
    mode.moving_side = None


# -------------------------------------------------------------------- scenario
canvas = build_canvas()
s1 = make_virgin_strand((400, 100), (450, 300), 1, "1_1")
s2 = make_virgin_strand((450, 300), (150, 350), 1, "1_2")
canvas.strands = [s1, s2]

move_mode = MoveMode(canvas)
move_mode.draw_only_affected_strand = False
canvas.current_mode = move_mode

# --- sanity: virgin strands really are in the never-moved state ---
check("1_1 cp1 sits on the start (never moved)", s1.control_point1 == s1.start)
check("1_1 triangle_has_moved is False", not s1.triangle_has_moved)

# --- 1) idle, nothing selected: filter hides every control point ---
reset_selection(canvas, move_mode)
img = render_control_points(canvas)
check("idle, no selection: 1_1 shows no triangle", not green_near(img, s1.control_point1))
check("idle, no selection: 1_2 shows no triangle", not green_near(img, s2.control_point1))

# --- 2) idle, 1_2 selected: only 1_2's triangle shows ---
reset_selection(canvas, move_mode)
s2.is_selected = True
canvas.selected_attached_strand = s2
img = render_control_points(canvas)
check("idle, 1_2 selected: 1_2 triangle shown", green_near(img, s2.control_point1))
check("idle, 1_2 selected: 1_1 triangle hidden", not green_near(img, s1.control_point1))

# --- 3) THE BUG: 1_2 selected, user drags 1_1's start point ---
# State below mirrors exactly what MoveMode leaves in place mid-drag:
#   start_movement (move_mode.py:2451-2460, 2582-2585) and
#   mousePressEvent (move_mode.py:1411-1417).
reset_selection(canvas, move_mode)
s2.is_selected = True                       # 1_2 was the selected strand
move_mode.originally_selected_strand = s2
move_mode.affected_strand = s1              # user grabbed 1_1's start
move_mode.is_moving = True
move_mode.is_moving_strand_point = True
move_mode.moving_side = 0
canvas.truly_moving_strands = [s1]
s1.is_selected = True                       # start_movement: movers get selected
move_mode.temp_selected_strand = s1
canvas.selected_attached_strand = s1        # mousePressEvent line 1417

img = render_control_points(canvas)
check(
    "drag 1_1 start (1_2 was selected): 1_1's never-moved start triangle stays hidden",
    not green_near(img, s1.control_point1),
    "green triangle rendered at the dragged start point "
    "(cp1=%.0f,%.0f)" % (s1.control_point1.x(), s1.control_point1.y()),
)
check(
    "drag 1_1 start: 1_2's triangle hidden during the drag",
    not green_near(img, s2.control_point1),
)

# --- 4) control: dragging a strand whose curve WAS shaped keeps its handles ---
reset_selection(canvas, move_mode)
s1.triangle_has_moved = True
s1.control_point1 = QPointF(500, 150)       # user actually shaped the curve
s1.update_shape()
move_mode.affected_strand = s1
move_mode.is_moving = True
move_mode.is_moving_strand_point = True
move_mode.moving_side = 0
canvas.truly_moving_strands = [s1]
s1.is_selected = True
canvas.selected_attached_strand = s1
img = render_control_points(canvas)
check("drag 1_1 start (curve was shaped): 1_1 triangle IS shown",
      green_near(img, s1.control_point1))

# ------------------------------------------------------------------------- fin
print()
print("%d passed, %d failed" % (_PASS, _FAIL))
sys.exit(1 if _FAIL else 0)
