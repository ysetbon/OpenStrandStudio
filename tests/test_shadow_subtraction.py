"""A hidden shadow is kept off the strands it would land on by subtracting
them from other shadows' clips (shader_utils._clip_off_hidden_rows).

Qt's QPainterPath.subtracted() can get it wrong on strand outlines: it
returned an empty path for a strand with an end circle minus a mask piece
that barely touched it. shader_utils._subtracted_checked checks the result on
a grid of points and keeps the unsubtracted path when points outside the cut
went missing, so a bad result can only leave a shadow where it was before,
never wipe it out.
"""

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
