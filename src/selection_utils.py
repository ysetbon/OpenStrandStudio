# src/selection_utils.py
"""Shared strand hit-testing so every mode resolves clicks the same way.

The hit areas match the exact rendered geometry of each strand:
- regular/attached strand body: centerline stroked to width + 2 * stroke_width
- endpoints: circles of the same visible radius (clipped to the body when no
  circle is drawn at that end)
- masked strand: the drawn mask (stroke layer united with fill layer)

All widths are read from the strand at call time, so per-strand or per-set
width/stroke changes are picked up automatically.
"""

from PyQt5.QtCore import QPointF, QRect, Qt
from PyQt5.QtGui import (QImage, QPainter, QPainterPath, QPainterPathStroker,
                         QPixmap, QTransform)

from masked_strand import MaskedStrand

# A click is a pixel, not an infinitesimal point. Sampling a few sub-pixel
# offsets also works around a Qt quirk: QPainterPath.contains() (and even
# intersects()) can return False exactly on internal seams of stroked
# collinear curves — e.g. every point on the centerline of a perfectly
# vertical strand.
_HIT_TOLERANCE = 0.5
_SAMPLE_OFFSETS = (
    (0.0, 0.0),
    (_HIT_TOLERANCE, 0.0), (-_HIT_TOLERANCE, 0.0),
    (0.0, _HIT_TOLERANCE), (0.0, -_HIT_TOLERANCE),
    (_HIT_TOLERANCE, _HIT_TOLERANCE), (-_HIT_TOLERANCE, _HIT_TOLERANCE),
    (_HIT_TOLERANCE, -_HIT_TOLERANCE), (-_HIT_TOLERANCE, -_HIT_TOLERANCE),
)


def _path_hit(path, pos):
    """Robust point-in-path test for hit-testing."""
    if path.isEmpty():
        return False
    for dx, dy in _SAMPLE_OFFSETS:
        if path.contains(QPointF(pos.x() + dx, pos.y() + dy)):
            return True
    return False


def _strand_footprint_hit(strand, pos):
    """Test regular-strand components without a QPainterPath Boolean union."""
    get_components = getattr(strand, 'get_selection_paths', None)
    if get_components is None:
        return _path_hit(strand.get_selection_path(), pos)
    return any(_path_hit(path, pos) for path in get_components())


def selection_outline_path(path, border_width, join_style=Qt.MiterJoin,
                           cap_style=Qt.FlatCap):
    """Return only the outside border of a composite selection footprint.

    ``path`` may contain overlapping body and endpoint-decoration subpaths.
    Stroking it directly outlines every subpath and exposes those overlaps as
    lines inside the highlight.  Removing the filled footprint from a wider
    stroke leaves only the exterior ring, without requiring the unreliable
    Boolean union used by older hit-testing code.
    """
    if path.isEmpty() or border_width <= 0:
        return QPainterPath()

    stroker = QPainterPathStroker()
    # A path stroke is centred on its boundary.  Doubling the requested width
    # leaves that full width outside after the footprint is subtracted.
    stroker.setWidth(border_width * 2)
    stroker.setJoinStyle(join_style)
    stroker.setCapStyle(cap_style)
    return stroker.createStroke(path).subtracted(path)


def _paint_selection_border(painter, path, color, border_width, join_style, cap_style):
    """Paint the ring around ``path`` without any Boolean path operation.

    ``selection_outline_path`` subtracts the footprint from a wider stroke with
    QPainterPath.subtracted().  On a footprint made of overlapping pieces whose
    edges nearly coincide (a body plus the thin side-line band at each end)
    Qt's Boolean code can drop pieces of the result, which left notches and
    missing chunks in the border at the strand's corners.  Here the wide stroke
    is painted on a small transparent layer and the very footprint the fill
    uses is erased from it, so the ring is exact for any footprint.
    """
    if path.isEmpty() or border_width <= 0:
        return
    stroker = QPainterPathStroker()
    # The stroke is centred on the boundary; doubling the width leaves the full
    # requested width outside once the footprint is erased.
    stroker.setWidth(border_width * 2)
    stroker.setJoinStyle(join_style)
    stroker.setCapStyle(cap_style)
    ring = stroker.createStroke(path)

    # Work in the device's physical pixels so the layer lands exactly on the
    # pixel grid at any zoom and display scale (125 %, 150 %, 200 % ...).
    # The world transform maps to logical device coordinates; Qt adds the
    # display scale on top (in the view transform for images, in the backing
    # store for widgets), so the world transform times the ratio gives pixels.
    device = painter.device()
    ratio = device.devicePixelRatioF() if device is not None else 1.0
    if ratio <= 0:
        ratio = 1.0
    to_pixels = painter.transform() * QTransform.fromScale(ratio, ratio)
    bounds = to_pixels.mapRect(ring.controlPointRect()).toAlignedRect().adjusted(-2, -2, 2, 2)
    # Only the part that can be seen needs a layer (the strand may be zoomed
    # far past the window).
    if device is not None:
        width, height = device.width(), device.height()
        if not isinstance(device, (QImage, QPixmap)):
            # Widgets report logical sizes; images and pixmaps report pixels.
            width, height = width * ratio, height * ratio
        bounds = bounds.intersected(QRect(0, 0, int(width + 0.999), int(height + 0.999)))
    if bounds.isEmpty():
        return

    layer = QImage(bounds.width(), bounds.height(), QImage.Format_ARGB32_Premultiplied)
    layer.fill(Qt.transparent)
    layer_painter = QPainter(layer)
    try:
        layer_painter.setRenderHint(QPainter.Antialiasing, True)
        layer_painter.setTransform(
            to_pixels * QTransform.fromTranslate(-bounds.x(), -bounds.y()))
        layer_painter.setPen(Qt.NoPen)
        layer_painter.setBrush(color)
        layer_painter.drawPath(ring)
        layer_painter.setCompositionMode(QPainter.CompositionMode_Clear)
        layer_painter.drawPath(path)
    finally:
        layer_painter.end()
    layer.setDevicePixelRatio(ratio)

    world_enabled = painter.worldMatrixEnabled()
    painter.save()
    try:
        # Place the layer in logical device space: drop only the world
        # transform; the display scale still applies and maps it 1:1 to pixels.
        painter.setWorldMatrixEnabled(False)
        painter.drawImage(QPointF(bounds.x() / ratio, bounds.y() / ratio), layer)
    finally:
        painter.setWorldMatrixEnabled(world_enabled)
        painter.restore()


def draw_selection_overlay(painter, path, fill_color, border_color=None,
                           border_width=0, join_style=Qt.MiterJoin,
                           cap_style=Qt.FlatCap):
    """Paint a selection footprint with a border around its silhouette only."""
    painter.setPen(Qt.NoPen)

    painter.setBrush(fill_color)
    painter.drawPath(path)

    if border_color is not None and border_width > 0:
        _paint_selection_border(painter, path, border_color, border_width,
                                join_style, cap_style)


def find_strands_at_point(strands, pos, include_masked=True):
    """Hit-test strands at pos against their exact rendered geometry.

    Iterates top-to-bottom (last drawn checked first), so the topmost strand
    is first in the returned list. Hidden and deleted strands are skipped.

    Args:
        strands: iterable of strands in draw order (bottom to top).
        pos (QPointF): position in canvas coordinates.
        include_masked (bool): when False, MaskedStrand instances are skipped
            entirely (mask mode can't use masks as mask components).

    Returns:
        list of (strand, selection_type) tuples, topmost strand first, where
        selection_type is 'start', 'end' or 'strand'.
    """
    pos = QPointF(pos)
    results = []
    for strand in reversed(list(strands)):
        if getattr(strand, 'is_hidden', False) or getattr(strand, 'deleted', False):
            continue

        if isinstance(strand, MaskedStrand):
            if include_masked and _path_hit(strand.get_selection_path(), pos):
                results.append((strand, 'strand'))
            continue

        if _path_hit(strand.get_start_selection_path(), pos):
            results.append((strand, 'start'))
        elif _path_hit(strand.get_end_selection_path(), pos):
            results.append((strand, 'end'))
        elif _strand_footprint_hit(strand, pos):
            results.append((strand, 'strand'))
    return results
