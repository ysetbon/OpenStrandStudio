"""Erased mask boxes ride on the crossing they erase.

A mask covers every overlap of its two strands, so it can span two
crossings with a deletion box erasing one of them:
src/samples/twisted_pairs.json crosses each pair twice and erases the lower
crossing. Dragging a strand end or a control point in move mode must keep
each box on its own crossing, dragging back must put it back exactly, and
the centre a file stores for the mask must not make the first drag jump.

Before, every box moved by the shift of the edited mask's centre: on
twisted_pairs.json, dragging 2_1's start 50 px sent the box 231 px down
while its crossing stayed put.
"""

import contextlib
import io
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF
from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

import save_load_manager
from angle_adjust_mode import AngleAdjustMode
from move_mode import MoveMode
from strand_drawing_canvas import StrandDrawingCanvas

TWISTED_PAIRS = ROOT / "src" / "samples" / "twisted_pairs.json"
FIVE_RINGS = ROOT / "knot_samples" / "links" / "json" / "five_ring_chain.json"
HALF_ERASED = ROOT / "tests" / "shadow_scenes" / "erased_mask" / "half_erased_crossing.json"
CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")


def load(path, curve=None):
    """The canvas right after opening the file, in move mode."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if "states" in data:
        data = data["states"][data.get("current_step", 1) - 1]["data"]
    canvas = StrandDrawingCanvas()
    canvas._suppress_layer_panel_refresh = True
    canvas.snap_to_grid_enabled = False
    if curve:
        (canvas.control_point_base_fraction, canvas.distance_multiplier,
         canvas.curve_response_exponent) = curve
    with contextlib.redirect_stdout(io.StringIO()):
        canvas.strands = save_load_manager.load_strands_from_data(data, canvas)[0]
    mode = MoveMode(canvas)
    canvas.current_mode = mode
    return canvas, mode


def strand(canvas, name):
    return next(s for s in canvas.strands if s.layer_name == name)


def drag(canvas, mode, moved, side, points):
    """Press on a handle, move through points, release."""
    canvas.truly_moving_strands = [moved]
    with contextlib.redirect_stdout(io.StringIO()):
        mode.start_movement(moved, side, QRectF(0, 0, 10, 10))
        for x, y in points:
            mode.update_strand_position(QPointF(x, y))
        mode.reset_movement_state()


def line(start, delta, steps=20):
    return [(start.x() + delta[0] * k / steps, start.y() + delta[1] * k / steps)
            for k in range(1, steps + 1)]


def erased_share(mask, rect):
    """The largest share of one crossing of the mask that the box covers."""
    box = QPolygonF([QPointF(*rect[key]) for key in CORNERS])
    best = 0.0
    for piece in mask.get_base_mask_path().toSubpathPolygons():
        bounds = piece.boundingRect()
        inside = covered = 0
        for i in range(40):
            for j in range(40):
                point = QPointF(bounds.x() + (i + 0.5) * bounds.width() / 40,
                                bounds.y() + (j + 0.5) * bounds.height() / 40)
                if piece.containsPoint(point, Qt.OddEvenFill):
                    inside += 1
                    covered += box.containsPoint(point, Qt.OddEvenFill)
        if inside:
            best = max(best, covered / inside)
    return best


def test_start_drag_keeps_the_box_on_its_crossing():
    # 2_1's start is near the upper crossing; the box erases the lower one
    canvas, mode = load(TWISTED_PAIRS)
    mask = strand(canvas, "2_1_3_1")
    assert erased_share(mask, mask.deletion_rectangles[0]) > 0.99
    moved = strand(canvas, "2_1")
    drag(canvas, mode, moved, 0, line(QPointF(moved.start), (40, 30)))
    assert erased_share(mask, mask.deletion_rectangles[0]) > 0.99


def test_dragging_back_puts_the_box_back():
    canvas, mode = load(TWISTED_PAIRS)
    mask = strand(canvas, "2_1_3_1")
    before = [tuple(mask.deletion_rectangles[0][key]) for key in CORNERS]
    moved = strand(canvas, "2_1")
    start = QPointF(moved.start)
    out = line(start, (60, 40))
    drag(canvas, mode, moved, 0, out + out[-2::-1] + [(start.x(), start.y())])
    after = [tuple(mask.deletion_rectangles[0][key]) for key in CORNERS]
    assert max(math.dist(a, b) for a, b in zip(before, after)) < 1e-6


def test_control_point_drag_carries_the_box():
    # Half of the only crossing is erased; bending 1_1 moves that crossing
    canvas, mode = load(HALF_ERASED, curve=(3.25, 3.6, 2.6))
    mask = strand(canvas, "1_1_2_1")
    before = erased_share(mask, mask.deletion_rectangles[0])
    assert 0.45 < before < 0.55
    moved = strand(canvas, "1_1")
    drag(canvas, mode, moved, "control_point1", line(QPointF(moved.control_point1), (-60, 0)))
    assert abs(erased_share(mask, mask.deletion_rectangles[0]) - before) < 0.05


def test_first_drag_after_opening_does_not_jump():
    # The file stores 2_1's start point as the mask's centre
    canvas, mode = load(TWISTED_PAIRS)
    mask = strand(canvas, "2_1_3_1")
    before = tuple(mask.deletion_rectangles[0]["top_left"])
    moved = strand(canvas, "2_1")
    drag(canvas, mode, moved, 0, [(moved.start.x() + 0.5, moved.start.y())])
    assert math.dist(before, tuple(mask.deletion_rectangles[0]["top_left"])) < 1.0


def test_box_stays_off_a_neighbouring_crossing():
    # Mask 1_1_2_1 covers two crossings 118 px apart and the box erases the
    # upper one. Dragging 2_1's triangle makes that crossing vanish for a
    # while; the box must wait for it instead of jumping to the other one.
    canvas, mode = load(FIVE_RINGS)
    mask = strand(canvas, "1_1_2_1")
    before = [tuple(mask.deletion_rectangles[0][key]) for key in CORNERS]
    moved = strand(canvas, "2_1")
    start = QPointF(moved.control_point1)
    out = line(start, (40, 28))
    drag(canvas, mode, moved, "control_point1", out + out[-2::-1] + [(start.x(), start.y())])
    after = [tuple(mask.deletion_rectangles[0][key]) for key in CORNERS]
    assert max(math.dist(a, b) for a, b in zip(before, after)) < 1e-6


def test_angle_tool_carries_boxes_and_cancel_restores_them():
    canvas, _ = load(HALF_ERASED, curve=(3.25, 3.6, 2.6))
    mask = strand(canvas, "1_1_2_1")
    before_share = erased_share(mask, mask.deletion_rectangles[0])
    before = [tuple(mask.deletion_rectangles[0][key]) for key in CORNERS]
    tool = AngleAdjustMode(canvas)
    tool.prompt_for_adjustments = lambda: None  # the dialog's sliders call the methods below
    with contextlib.redirect_stdout(io.StringIO()):
        tool.activate(strand(canvas, "1_1"))
        for k in range(1, 11):
            tool.rotate_strand(tool.initial_angle + 1.5 * k)
        tool.set_strand_length(tool.initial_length * 1.25)
    assert abs(erased_share(mask, mask.deletion_rectangles[0]) - before_share) < 0.05
    with contextlib.redirect_stdout(io.StringIO()):
        tool.cancel_adjustment()
    after = [tuple(mask.deletion_rectangles[0][key]) for key in CORNERS]
    assert max(math.dist(a, b) for a, b in zip(before, after)) < 1e-6
