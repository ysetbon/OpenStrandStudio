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

from PyQt5.QtCore import QPointF

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
        elif _path_hit(strand.get_selection_path(), pos):
            results.append((strand, 'strand'))
    return results
