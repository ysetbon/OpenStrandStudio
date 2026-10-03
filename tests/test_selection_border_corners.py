"""The selection border keeps its corners whole.

Mask mode (and hover) paint the picked strand with a border around its
silhouette.  The ring used to be built as ``stroke.subtracted(footprint)``,
a QPainterPath Boolean on a footprint made of overlapping pieces (the body
plus the thin side-line band at each end).  Qt's Boolean code is sensitive to
the exact coordinates, so for some positions of the very same strand it
dropped a chunk of the ring at a corner (a notch, a stray stub and a dark
blot) or put the whole body into the ring.  The border is now painted on a
layer with the footprint erased, which has no such dependence.

Strands of the user's size and angle, moved a few pixels: the original code
broke at x offsets 14, 17, 23 and 31 (see the scan in the PR).
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPathStroker
from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from selection_utils import draw_selection_overlay
from strand import Strand

SCALE = 2
BORDER = 8  # stroke_width * 2, like mask mode


def make_strand(dx):
    start = QPointF(1288 + dx, 364)
    end = QPointF(1512 + dx, 616)
    strand = Strand(start, end, 46)
    strand.stroke_width = 4
    strand.control_point1 = QPointF(start.x() + (end.x() - start.x()) / 3,
                                    start.y() + (end.y() - start.y()) / 3)
    strand.control_point2 = QPointF(start.x() + 2 * (end.x() - start.x()) / 3,
                                    start.y() + 2 * (end.y() - start.y()) / 3)
    strand.control_point_center = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
    return strand


def layer(rect):
    image = QImage(int(rect.width() * SCALE), int(rect.height() * SCALE), QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    painter.scale(SCALE, SCALE)
    painter.translate(-rect.x(), -rect.y())
    return image, painter


def ring_painted(path, rect):
    image, painter = layer(rect)
    painter.setRenderHint(QPainter.Antialiasing, True)
    draw_selection_overlay(painter, path, QColor(0, 0, 0, 0),
                           border_color=QColor(0, 0, 0), border_width=BORDER)
    painter.end()
    return image


def ring_expected(path, rect):
    """Wide stroke with the footprint erased, all by painting (no Booleans)."""
    image, painter = layer(rect)
    painter.setRenderHint(QPainter.Antialiasing, True)
    stroker = QPainterPathStroker()
    stroker.setWidth(BORDER * 2)
    stroker.setJoinStyle(Qt.MiterJoin)
    stroker.setCapStyle(Qt.FlatCap)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0))
    painter.drawPath(stroker.createStroke(path))
    painter.setCompositionMode(QPainter.CompositionMode_Clear)
    painter.drawPath(path)
    painter.end()
    return image


def differing_pixels(a, b):
    count = 0
    for y in range(a.height()):
        for x in range(a.width()):
            if (a.pixelColor(x, y).alpha() > 127) != (b.pixelColor(x, y).alpha() > 127):
                count += 1
    return count


@pytest.mark.parametrize("dx", [0, 14, 17, 23, 31, 32])
def test_the_border_is_the_whole_ring_around_the_strand(dx):
    path = make_strand(dx).get_selection_path()
    rect = path.boundingRect().adjusted(-20, -20, 20, 20)
    # Anti-aliasing alone differs by a few pixels; a lost corner is 140+.
    assert differing_pixels(ring_painted(path, rect), ring_expected(path, rect)) < 60


def test_the_border_stays_outside_the_footprint():
    path = make_strand(14).get_selection_path()
    rect = path.boundingRect().adjusted(-20, -20, 20, 20)
    image = ring_painted(path, rect)
    centre = path.boundingRect().center()
    px = int((centre.x() - rect.x()) * SCALE)
    py = int((centre.y() - rect.y()) * SCALE)
    assert image.pixelColor(px, py).alpha() == 0
