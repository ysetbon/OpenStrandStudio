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

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainterPath, QPainterPathStroker

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


def draw_selection_overlay(painter, path, fill_color, border_color=None,
                           border_width=0, join_style=Qt.MiterJoin,
                           cap_style=Qt.FlatCap):
    """Paint a selection footprint with a border around its silhouette only."""
    painter.setPen(Qt.NoPen)

    painter.setBrush(fill_color)
    painter.drawPath(path)

    if border_color is not None and border_width > 0:
        painter.setBrush(border_color)
        painter.drawPath(selection_outline_path(
            path, border_width, join_style, cap_style))


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
