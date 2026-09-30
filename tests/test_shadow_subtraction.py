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


def test_a_hairline_overlap_does_not_count_as_lying_over_a_piece():
    """A wide strand beside a mask's piece touches it by a sliver (the piece
    reaches 2 px past its second strand's outline). Its shadow on the first
    strand still belongs on the piece, so it must not be left out."""
    piece = rect(100, 100, 60, 50)
    beside = rect(159.5, 80, 60, 90)   # overlaps the piece by half a pixel
    across = rect(130, 80, 60, 90)     # runs over the piece
    assert piece.intersects(beside)
    assert not shader_utils._lies_over(beside, piece)
    assert shader_utils._lies_over(across, piece)
    assert not shader_utils._lies_over(rect(300, 300, 10, 10), piece)
