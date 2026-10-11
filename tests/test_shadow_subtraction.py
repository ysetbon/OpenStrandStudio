"""A hidden shadow is kept off the strands it would land on by subtracting
them from other shadows' clips (shader_utils._clip_off_hidden_rows).

Qt's QPainterPath.subtracted() can get it wrong on strand outlines: it
returned an empty path for a strand with an end circle minus a mask piece
that barely touched it. shader_utils._subtracted_checked checks the result on
a grid of points and keeps the unsubtracted path when points outside the cut
went missing, so a bad result can only leave a shadow where it was before,
never wipe it out.
"""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication

import shader_utils

APP = QApplication.instance() or QApplication([])


def rect(x, y, w, h):
    path = QPainterPath()
    path.addRect(QRectF(x, y, w, h))
    return path


def strand_with_end_circle():
    """A strand's body and its end circle, overlapping, as the canvas builds
    a receiver's outline."""
    path = rect(100, 100, 200, 54)
    path.addEllipse(QPointF(300, 127), 32, 32)
    return path


def test_a_correct_subtraction_is_kept():
    path, cut = strand_with_end_circle(), rect(180, 80, 40, 100)
    result = shader_utils._subtracted_checked(path, cut)
    assert not result.contains(QPointF(200, 127))  # inside the cut: gone
    assert result.contains(QPointF(140, 127))      # outside the cut: kept
    assert result.contains(QPointF(320, 127))      # the end circle: kept


def test_a_result_that_lost_the_strand_is_rejected():
    path, cut = strand_with_end_circle(), rect(180, 80, 40, 100)
    assert shader_utils._subtraction_ok(path, cut, path.subtracted(cut))
    assert not shader_utils._subtraction_ok(path, cut, QPainterPath())
    # Losing the end circle alone is caught too.
    assert not shader_utils._subtraction_ok(path, cut, rect(100, 100, 80, 54))


def test_a_cut_that_misses_the_strand_changes_nothing():
    path, cut = strand_with_end_circle(), rect(500, 500, 50, 50)
    result = shader_utils._subtracted_checked(path, cut)
    for x, y in ((110, 110), (200, 127), (320, 127), (290, 150)):
        assert result.contains(QPointF(x, y)) == path.contains(QPointF(x, y))


def test_a_strand_beside_a_piece_does_not_run_under_it():
    """A mask's piece covers the edge of a wide neighbour running beside the
    crossing. That neighbour keeps its shadow on the rest of the piece; only
    a strand the piece is drawn across lies below it there."""
    strand = SimpleNamespace(width=46, stroke_width=4)   # 54 px wide when drawn
    piece = rect(100, 100, 60, 50)
    for overlap in (0.5, 4, 10, 20):                     # an edge sliver, however thick
        beside = rect(160 - overlap, 60, 54, 130)
        assert piece.intersects(beside)
        assert not shader_utils._runs_under(strand, beside, piece)
    across = rect(110, 60, 54, 130)                      # crosses the piece
    assert shader_utils._runs_under(strand, across, piece)
    assert not shader_utils._runs_under(strand, rect(300, 300, 10, 10), piece)


def test_only_a_solid_strand_keeps_a_mask_piece_off():
    """A mask's piece leaves uncovered only what a strand paints solidly: a
    strand drawn as a shadow only, or see-through, would let the unlifted
    strand show through the hole. A strand paints its body in the outline
    colour under its fill, so an opaque outline makes all of it solid."""
    from PyQt5.QtGui import QColor
    footprint = rect(100, 100, 60, 200)

    def strand(fill=255, outline=255, **flags):
        return SimpleNamespace(color=QColor(200, 100, 50, fill), stroke_color=QColor(0, 0, 0, outline),
                               stroke_width=4, **flags)

    assert shader_utils._opaque_cover(strand(), footprint) is footprint
    assert shader_utils._opaque_cover(strand(shadow_only=True), footprint) is None
    assert shader_utils._opaque_cover(strand(fill=140), footprint) is footprint
    assert shader_utils._opaque_cover(strand(fill=140, outline=0), footprint) is None
    # A see-through outline: only the fill, 4 px in from each side, counts.
    fill_only = shader_utils._opaque_cover(strand(outline=0), footprint)
    assert fill_only.contains(QPointF(130, 200))
    assert not fill_only.contains(QPointF(102, 200))
    assert not fill_only.contains(QPointF(158, 200))


def test_a_strand_continuing_another_at_a_joint_is_joined_to_it():
    parent = SimpleNamespace(start=QPointF(0, 0), end=QPointF(100, 0))
    continuation = SimpleNamespace(start=QPointF(100, 0), end=QPointF(200, 50))
    elsewhere = SimpleNamespace(start=QPointF(100, 40), end=QPointF(200, 50))
    assert shader_utils._joined(continuation, (parent,))
    assert not shader_utils._joined(elsewhere, (parent,))


def test_a_cut_meeting_the_path_along_an_edge_removes_nothing():
    path = rect(100, 100, 200, 54)
    for cut in (rect(150, 154, 40, 60),    # below, sharing the bottom edge
                rect(300, 90, 50, 80),     # beside, sharing the right edge
                rect(150, 153.8, 40, 60)): # overlapping by a hairline
        result = shader_utils._subtracted(path, cut)
        for x, y in ((110, 110), (170, 150), (290, 127)):
            assert result.contains(QPointF(x, y))


def woven_scene():
    """tests/shadow_scenes/woven_2x2_top_diagonal.json by layer name: a 2x2
    weave with masks at its crossings and 2_4, the top layer, laid across
    it diagonally."""
    path = Path(__file__).resolve().parent / "shadow_scenes" / "woven_2x2_top_diagonal.json"
    data = json.loads(path.read_text(encoding="utf-8"))["states"][0]["data"]
    from save_load_manager import load_strands_from_data
    loader = SimpleNamespace(strands=[], groups={}, strand_colors={}, shadow_enabled=True,
                             _suppress_layer_panel_refresh=True, _suppress_repaint=True,
                             update=lambda: None)
    strands = load_strands_from_data(data, loader)[0]
    canvas = SimpleNamespace(strands=strands, shadow_enabled=True, shadow_selected_only=False,
                             enable_third_control_point=True,
                             layer_state_manager=EveryShadowShown([s.layer_name for s in strands]))
    for strand in strands:
        strand.canvas = canvas
        strand.control_point_base_fraction = 1.0
        strand.distance_multiplier = 2.0
        strand.curve_response_exponent = 2.0
    for strand in strands:
        if not hasattr(strand, "get_mask_path"):
            strand.update_shape()
    return {strand.layer_name: strand for strand in strands}


class EveryShadowShown:
    def __init__(self, order):
        self.order = order

    def getOrder(self):
        return list(self.order)

    def getConnections(self):
        return {}

    def get_shadow_override(self, casting, receiving):
        return None

    def get_shadow_visibility(self, casting, receiving):
        return True

    def get_subtracted_layers(self, casting, receiving):
        return []


def test_a_mask_in_the_next_row_leaves_the_top_strands_shadow_alone():
    """2_4 crosses 1_2 (y 337-391) between columns 3_3 and 4_3, over column
    3_2, which 1_2 lies above. Mask 3_2_2_3 lifts 3_2 over 2_3 in the next
    row down: its piece starts at y 391, on 1_2's bottom edge. Subtracting it
    from 2_4's shadow on 1_2 lost the whole piece between the two columns,
    so 2_4 cast no shadow on 1_2 there."""
    strands = woven_scene()
    collected = shader_utils.draw_strand_shadow(None, strands["2_4"], None, num_steps=2,
                                                max_blur_radius=30.0, collect_only=True, cache={})
    outline = collected["stroke_path"]
    assert outline.contains(QPointF(1090, 375))   # left of column 3_3, as before
    assert outline.contains(QPointF(1204, 385))   # over column 3_2, between the masks
    assert outline.contains(QPointF(1300, 390))   # right of column 4_3
