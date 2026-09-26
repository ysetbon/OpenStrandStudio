"""A shadow's soft edge is stroked along the outline of the area it falls on.

Qt's intersected() with an axis-aligned rectangle clips each polygon without
repeating its first point, and stroking that open outline drops its last side:
a horizontal strand over a strand drawn from the bottom right up to the top
left lost the soft edge below it. shader_utils._closed_outline closes such
outlines before they are stroked.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF
from PyQt5.QtWidgets import QApplication

import shader_utils

APP = QApplication.instance() or QApplication([])


def polygon(*points):
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
    path.closeSubpath()
    return path


def horizontal_over_diagonal():
    """Where a horizontal strand's body covers a strand drawn up and to the
    left (the woven star's 5_1 over 3_1)."""
    horizontal = QPainterPath()
    horizontal.addRect(QRectF(445, 440.3, 710, 54))
    diagonal = polygon((1017.1, 865.7), (442.2, 448.0), (473.9, 404.3), (1048.8, 822.0))
    return horizontal.intersected(diagonal)


def open_subpaths(path):
    count, start, last = 0, None, None
    for index in range(path.elementCount()):
        element = path.elementAt(index)
        if element.type == QPainterPath.MoveToElement:
            if start is not None and (last.x, last.y) != (start.x, start.y):
                count += 1
            start = element
        last = element
    if start is not None and (last.x, last.y) != (start.x, start.y):
        count += 1
    return count


def stroked(path):
    image = QImage(1200, 900, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    pen = QPen(QColor(0, 0, 0))
    pen.setWidthF(10)
    painter.strokePath(path, pen)
    painter.end()
    return image


def test_closed_outline_closes_every_subpath():
    area = horizontal_over_diagonal()
    closed = shader_utils._closed_outline(area)
    assert open_subpaths(closed) == 0
    # Same area: filling closes subpaths anyway.
    assert closed.boundingRect() == area.boundingRect()


def test_soft_edge_runs_along_every_side():
    # The area's lower side runs along the horizontal strand's lower edge
    # (y 494.3, x 505.9 to 597.8); its soft edge is the shadow below it.
    image = stroked(shader_utils._closed_outline(horizontal_over_diagonal()))
    assert image.pixelColor(550, 498).alpha() > 0


def test_closed_path_is_returned_as_is():
    area = polygon((0, 0), (40, 0), (40, 30), (0, 30))
    assert open_subpaths(area) == 0
    assert shader_utils._closed_outline(area) is area


def test_curves_are_kept():
    path = QPainterPath(QPointF(0, 0))
    path.cubicTo(QPointF(20, -20), QPointF(40, 20), QPointF(60, 0))
    path.lineTo(QPointF(60, 40))
    closed = shader_utils._closed_outline(path)
    assert open_subpaths(closed) == 0
    types = [closed.elementAt(i).type for i in range(closed.elementCount())]
    assert QPainterPath.CurveToElement in types
    assert closed.elementCount() == path.elementCount() + 1
