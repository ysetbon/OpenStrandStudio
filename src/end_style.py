"""Stylized free ends ("Stylize End Side").

A free end (an end with no circle) can carry an *end style*: a small record
that describes the shape of the end edge (straight, angled, rounded, pointed,
notched, concave), its tilt, its depth, how far it is extended or trimmed
along the strand's direction, and the thickness / colour of the side line
drawn along it.

Everything that is rendered at a styled end is derived from one *profile*
``P(y)`` expressed in the local frame of the end (origin at the endpoint,
``+x`` pointing outward along the curve's tangent, ``y`` across the width):

* the **outer footprint** (stroke colour) is the flat-capped body with
  everything beyond the profile removed and the region between the endpoint
  plane and the profile added;
* the **inner fill** is the fill stroker (inset by ``stroke_width`` along the
  long edges) cut back to the side line's inner edge, the profile offset
  inward by the side-line thickness;
* the **side-line band** is the strip between that inner edge and the
  profile, painted in the side-line colour clipped to the footprint;
* **shadows** use the outer footprint pushed outward by the blur radius and
  **masks** intersect the same footprint.

With the default record (straight, 0 deg, 0 px, stroke-coloured side line of
``stroke_width``) the footprint is pixel-identical to the classic flat cap plus
side line, and strands with no style keep the classic code path entirely.
"""

import math

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QPainterPath, QPainterPathStroker, QTransform


SHAPES = ('straight', 'angled', 'rounded', 'pointed', 'notched', 'concave')
DEPTH_SHAPES = ('rounded', 'pointed', 'notched', 'concave')
TILT_MAX = 60.0
MIN_LINE_WIDTH = 0.5


# ----------------------------------------------------------------------------
# Style records
# ----------------------------------------------------------------------------
def default_style():
    """The record that reproduces today's flat cap + side line."""
    return {
        'shape': 'straight',
        'tilt': 0.0,        # degrees, -TILT_MAX .. TILT_MAX, 0 = square to the strand
        'depth': 0.5,       # 0 .. 1, share of the strand width (ignored by straight/angled)
        'offset': 0.0,      # px along the tangent, + extends, - trims (the endpoint never moves)
        'line_width': None, # px, None = follow stroke_width
        'line_color': None, # QColor, None = follow stroke_color
    }


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _as_float(value, fallback):
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _as_color(value):
    if value is None:
        return None
    if isinstance(value, QColor):
        return QColor(value) if value.isValid() else None
    if isinstance(value, dict):
        try:
            return QColor(int(value.get('r', 0)), int(value.get('g', 0)),
                          int(value.get('b', 0)), int(value.get('a', 255)))
        except (TypeError, ValueError):
            return None
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            alpha = int(value[3]) if len(value) > 3 else 255
            return QColor(int(value[0]), int(value[1]), int(value[2]), alpha)
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        color = QColor(value)
        return color if color.isValid() else None
    return None


def normalize_style(style):
    """Return a clean copy of ``style`` or ``None`` when it is the default look.

    ``None`` is the fast path: a strand whose end style is ``None`` renders
    through the classic code, so a record that changes nothing is stored as
    ``None`` rather than as an explicit default.
    """
    if not style:
        return None
    clean = default_style()
    shape = style.get('shape', 'straight')
    clean['shape'] = shape if shape in SHAPES else 'straight'
    clean['tilt'] = _clamp(_as_float(style.get('tilt'), 0.0), -TILT_MAX, TILT_MAX)
    clean['depth'] = _clamp(_as_float(style.get('depth'), 0.5), 0.0, 1.0)
    clean['offset'] = _as_float(style.get('offset'), 0.0)
    line_width = style.get('line_width')
    clean['line_width'] = None if line_width is None else max(MIN_LINE_WIDTH, _as_float(line_width, 0.0))
    clean['line_color'] = _as_color(style.get('line_color'))
    if is_default_style(clean):
        return None
    return clean


def is_default_style(style):
    """True when the record draws exactly what an unstyled end draws."""
    if style is None:
        return True
    return (style.get('shape', 'straight') == 'straight'
            and abs(_as_float(style.get('tilt'), 0.0)) < 1e-9
            and abs(_as_float(style.get('offset'), 0.0)) < 1e-9
            and style.get('line_width') is None
            and style.get('line_color') is None)


def copy_style(style):
    """Deep copy (the colour is a fresh QColor)."""
    if style is None:
        return None
    result = dict(style)
    if result.get('line_color') is not None:
        result['line_color'] = QColor(result['line_color'])
    return result


def styles_equal(a, b):
    a = normalize_style(a)
    b = normalize_style(b)
    if a is None or b is None:
        return a is b
    for key in ('shape', 'tilt', 'depth', 'offset'):
        if key == 'shape':
            if a[key] != b[key]:
                return False
        elif abs(a[key] - b[key]) > 1e-6:
            return False
    if (a['line_width'] is None) != (b['line_width'] is None):
        return False
    if a['line_width'] is not None and abs(a['line_width'] - b['line_width']) > 1e-6:
        return False
    if (a['line_color'] is None) != (b['line_color'] is None):
        return False
    if a['line_color'] is not None and a['line_color'].rgba() != b['line_color'].rgba():
        return False
    return True


def serialize_style(style):
    """JSON-friendly form of a record (``None`` stays ``None``)."""
    style = normalize_style(style)
    if style is None:
        return None
    data = {
        'shape': style['shape'],
        'tilt': style['tilt'],
        'depth': style['depth'],
        'offset': style['offset'],
        'line_width': style['line_width'],
        'line_color': None,
    }
    color = style['line_color']
    if color is not None:
        data['line_color'] = {'r': color.red(), 'g': color.green(), 'b': color.blue(), 'a': color.alpha()}
    return data


def deserialize_style(data):
    if not isinstance(data, dict):
        return None
    return normalize_style(data)


def serialize_end_styles(strand):
    styles = getattr(strand, 'end_styles', None) or [None, None]
    return [serialize_style(styles[0] if len(styles) > 0 else None),
            serialize_style(styles[1] if len(styles) > 1 else None)]


def deserialize_end_styles(data):
    if not isinstance(data, (list, tuple)) or len(data) != 2:
        return [None, None]
    return [deserialize_style(data[0]), deserialize_style(data[1])]


def style_key(style):
    """Hashable signature used for geometry caching."""
    style = normalize_style(style)
    if style is None:
        return None
    color = style['line_color']
    return (style['shape'], round(style['tilt'], 4), round(style['depth'], 4),
            round(style['offset'], 4), style['line_width'],
            color.rgba() if color is not None else None)


# ----------------------------------------------------------------------------
# Profile in the local frame of the end
# ----------------------------------------------------------------------------
def profile_points(shape, half, depth, tilt_deg, base_x, steps=24):
    """The end-edge profile as local-frame points running from y=-half to
    y=+half. ``half`` is half the visible width, ``depth`` is 0..1, ``tilt_deg``
    rotates the whole profile about the endpoint and ``base_x`` is where the
    profile sits along the tangent before the tilt (side-line thickness plus
    the extend/trim offset)."""
    pts = []
    width = 2.0 * half
    if shape in ('straight', 'angled'):
        pts = [QPointF(0.0, -half), QPointF(0.0, half)]
    elif shape == 'rounded':
        r = depth * half
        for i in range(steps + 1):
            y = -half + width * i / steps
            x = r * math.sqrt(max(0.0, 1.0 - (y / half) ** 2))
            pts.append(QPointF(x, y))
    elif shape == 'pointed':
        pts = [QPointF(0.0, -half), QPointF(depth * width, 0.0), QPointF(0.0, half)]
    elif shape == 'notched':
        pts = [QPointF(0.0, -half), QPointF(-depth * width, 0.0), QPointF(0.0, half)]
    elif shape == 'concave':
        r = depth * half
        for i in range(steps + 1):
            y = -half + width * i / steps
            x = -r * math.sqrt(max(0.0, 1.0 - (y / half) ** 2))
            pts.append(QPointF(x, y))
    else:
        pts = [QPointF(0.0, -half), QPointF(0.0, half)]

    transform = QTransform()
    transform.translate(base_x, 0.0)
    transform.rotate(tilt_deg)
    return _fit_to_band([transform.map(p) for p in pts], half)


# Qt's path clipper mishandles a polygon vertex that lies exactly on an edge
# of the other operand. The body's long edges run at y = +-half and its
# outline has vertices on the endpoint plane x = 0 (where the curve meets its
# straight continuation), so the cut polygons keep this far from both.
_EDGE_CLEARANCE = 0.1


def _fit_to_band(pts, half):
    """After a tilt the profile no longer reaches y = +-half. Extend its first
    and last segments straight on until they do (a hair beyond, so the corner
    never sits exactly on the body's edge), so the cut spans the whole strand
    cross-section."""
    if len(pts) < 2:
        return pts
    half = half + _EDGE_CLEARANCE

    def hit(a, b, target_y):
        d = b - a
        if abs(d.y()) < 1e-9:
            return b
        t = (target_y - a.y()) / d.y()
        return QPointF(a.x() + d.x() * t, target_y)

    ascending = pts[0].y() < pts[-1].y()
    first = hit(pts[1], pts[0], -half if ascending else half)
    last = hit(pts[-2], pts[-1], half if ascending else -half)
    return [first] + pts[1:-1] + [last]


def _chord_extended(prof, half, ylim=None):
    """Where the profile's chord (first -> last point), continued past both
    ends, reaches |y| = ylim (1.5*half by default). The cut continues straight
    along that line through whatever part of a curved body bulges past the
    width right behind its endpoint, instead of turning square (which leaves
    a step or wedge)."""
    if ylim is None:
        ylim = 1.5 * half
    a, b = prof[0], prof[-1]
    d = b - a
    if abs(d.y()) < 1e-9:
        return QPointF(a.x(), -ylim), QPointF(b.x(), ylim)
    sgn = 1.0 if d.y() > 0 else -1.0
    ta = (-sgn * ylim - a.y()) / d.y()
    tb = (sgn * ylim - a.y()) / d.y()
    return (QPointF(a.x() + d.x() * ta, a.y() + d.y() * ta),
            QPointF(a.x() + d.x() * tb, a.y() + d.y() * tb))


def _remove_region(prof, half, x_far, y_lim):
    """Local-frame region OUTWARD of the profile, bounded by x = x_far and
    |y| = y_lim: what the end style cuts away from the (extended) body.

    The bounds are deliberately local. Everything that must go lies between
    the profile and the extended body's flat cap, within its width; a region
    reaching further would also cut a strand whose other arm passes in front
    of this end (a U shape)."""
    first, last = _chord_extended(prof, half, y_lim)
    poly = QPainterPath()
    poly.moveTo(first)
    for p in prof:
        poly.lineTo(p)
    poly.lineTo(last)
    poly.lineTo(QPointF(x_far, last.y()))
    poly.lineTo(QPointF(x_far, first.y()))
    poly.closeSubpath()
    return poly


def _band_region(prof, inner_prof, half, y_lim):
    """Local-frame strip between the profile and its inward offset (the side
    line's inner edge), both continued along their chords to |y| = y_lim."""
    first, last = _chord_extended(prof, half, y_lim)
    # The inner edge continues parallel to the profile's own continuation
    # (its own chord can point elsewhere once a steep flank has been offset,
    # and the strip's ends would then cross).
    inner_first = inner_prof[0] + (first - prof[0])
    inner_last = inner_prof[-1] + (last - prof[-1])
    poly = QPainterPath()
    poly.moveTo(first)
    for p in prof:
        poly.lineTo(p)
    poly.lineTo(last)
    poly.lineTo(inner_last)
    for p in reversed(inner_prof):
        poly.lineTo(p)
    poly.lineTo(inner_first)
    poly.closeSubpath()
    return poly


def _clear_of_endpoint_plane(pts):
    """Shift a polyline a hair backwards if any of its vertices (or its chord
    continuation) would sit on the endpoint plane x = 0, where the stroked
    body has vertices of its own (see _EDGE_CLEARANCE)."""
    xs = [p.x() for p in pts]
    if len(pts) >= 2:
        a, b = pts[0], pts[-1]
        if abs(b.y() - a.y()) > 1e-9:
            slope = (b.x() - a.x()) / (b.y() - a.y())
            for y in (-2.0 * abs(a.y()) - 1.0, 2.0 * abs(b.y()) + 1.0):
                xs.append(a.x() + slope * (y - a.y()))
    if all(abs(x) >= _EDGE_CLEARANCE for x in xs):
        return pts
    shift = -_EDGE_CLEARANCE - max(x for x in xs if abs(x) < _EDGE_CLEARANCE)
    return [QPointF(p.x() + shift, p.y()) for p in pts]


def _offset_profile(prof, distance):
    """The profile moved ``distance`` inward (toward the strand body) along
    its own normals, with mitred vertices: the inner edge of the side line."""
    if distance <= 0 or len(prof) < 2:
        return list(prof)
    normals = []
    for i in range(len(prof) - 1):
        v = prof[i + 1] - prof[i]
        length = math.hypot(v.x(), v.y())
        # Walking the profile from y=-half to y=+half, the body is on the left.
        normals.append(QPointF(-v.y() / length, v.x() / length) if length > 1e-9 else None)
    result = []
    for i, p in enumerate(prof):
        n1 = normals[i - 1] if i > 0 else None
        n2 = normals[i] if i < len(normals) else None
        if n1 is None and n2 is None:
            result.append(QPointF(p))
            continue
        if n1 is None or n2 is None:
            n = n1 if n2 is None else n2
            factor = 1.0
        else:
            sx, sy = n1.x() + n2.x(), n1.y() + n2.y()
            length = math.hypot(sx, sy)
            if length < 1e-9:
                n, factor = n1, 1.0
            else:
                n = QPointF(sx / length, sy / length)
                factor = 1.0 / max(0.25, n.x() * n1.x() + n.y() * n1.y())
        result.append(QPointF(p.x() + n.x() * distance * factor, p.y() + n.y() * distance * factor))
    return result


def _edge_path(prof, half):
    """The open profile polyline, continued along its chord past the width."""
    first, last = _chord_extended(prof, half)
    edge = QPainterPath()
    edge.moveTo(first)
    for p in prof:
        edge.lineTo(p)
    edge.lineTo(last)
    return edge


def _stroke(path, width, join=Qt.MiterJoin, cap=Qt.FlatCap, miter_limit=None):
    stroker = QPainterPathStroker()
    stroker.setWidth(width)
    stroker.setJoinStyle(join)
    stroker.setCapStyle(cap)
    if miter_limit is not None:
        stroker.setMiterLimit(miter_limit)
    result = stroker.createStroke(path)
    result.setFillRule(Qt.WindingFill)
    return result


def dilate(path, radius):
    """Offset a closed footprint outward by ``radius``."""
    if radius <= 0 or path.isEmpty():
        return path
    return path.united(_stroke(path, 2.0 * radius, Qt.RoundJoin, Qt.RoundCap))


# ----------------------------------------------------------------------------
# Per-strand geometry
# ----------------------------------------------------------------------------
def end_frame(strand, side):
    """(endpoint, outward angle in radians) of the given end in canvas coords."""
    point = strand.start if side == 0 else strand.end
    if hasattr(strand, '_cap_tangent_angle'):
        angle = strand._cap_tangent_angle(side)
    else:
        tangent = strand.calculate_cubic_tangent(0.0001 if side == 0 else 0.9999)
        if tangent.manhattanLength() == 0:
            tangent = strand.end - strand.start
        angle = math.atan2(tangent.y(), tangent.x()) if tangent.manhattanLength() else 0.0
    if side == 0:
        angle += math.pi
    return point, angle


class StyledEnd:
    """The local-frame pieces of one styled end, mapped to canvas coords."""

    def __init__(self, strand, side, style, line_visible):
        self.side = side
        self.style = style
        self.line_visible = bool(line_visible)
        sw = float(strand.stroke_width)
        total = float(strand.width) + 2.0 * sw
        half = total / 2.0
        self.half = half
        self.total = total
        self.stroke_width = sw

        line_width = style.get('line_width')
        self.line_width = sw if line_width is None else float(line_width)
        self.band_width = self.line_width if self.line_visible else 0.0
        self.base_x = self.band_width + float(style.get('offset', 0.0))

        point, angle = end_frame(strand, side)
        self.point = point
        self.angle = angle
        self.transform = QTransform()
        self.transform.translate(point.x(), point.y())
        self.transform.rotate(math.degrees(angle))
        self.unit = QPointF(math.cos(angle), math.sin(angle))

        self.profile = _clear_of_endpoint_plane(
            profile_points(style['shape'], half, style.get('depth', 0.5),
                           style.get('tilt', 0.0), self.base_x))
        self.inner_profile = (_clear_of_endpoint_plane(_offset_profile(self.profile, self.band_width))
                              if self.band_width > 0 else self.profile)
        self.max_x = max(p.x() for p in self.profile)
        self.min_x = min(p.x() for p in self.profile)
        # How far the edge's farthest point sits beyond where the classic end
        # (endpoint plane + side line) would put it: decorations anchored on
        # the endpoint (dash extension, small arrow) are shifted by this.
        self.extent_shift = self.max_x - self.band_width
        # The centre line is continued straight past the endpoint by this much
        # before stroking, so the body reaches the profile (the cut then trims
        # it back). Its flat cap and long edges are then exactly aligned with
        # the profile's frame, which a polygon glued onto the stroked body is
        # not (the stroker's cap follows its own flattening of the curve).
        self.extension_length = max(0.0, self.max_x) + 2.0
        # Local x of the extended centre line's far end; set by the geometry
        # once the base path is known (the shadow base is itself longer).
        self.cap_x = self.extension_length
        self.edge = self.transform.map(_edge_path(self.profile, half))
        self.corners = (self.transform.map(self.profile[0]), self.transform.map(self.profile[-1]))
        self._cuts = {}

    def local_x(self, point):
        return ((point.x() - self.point.x()) * self.unit.x()
                + (point.y() - self.point.y()) * self.unit.y())

    def _cut(self, prof, margin):
        # Past the extended body's flat cap by half a width: at a tight bend
        # the stroker's mitred corner reaches a few pixels beyond the cap.
        x_far = self.cap_x + self.half + margin
        y_lim = 1.5 * self.half + margin
        return self.transform.map(_remove_region(prof, self.half, x_far, y_lim))

    def remove(self, margin=0.0):
        """Everything outward of the profile (the cut), for a body stroked
        ``margin`` wider than the strand."""
        key = ('remove', round(margin, 3))
        if key not in self._cuts:
            self._cuts[key] = self._cut(self.profile, margin)
        return self._cuts[key]

    def fill_cut(self):
        """Everything outward of the side line's inner edge: what the fill
        loses. With the line hidden it is the cut itself."""
        key = ('fill', 0.0)
        if key not in self._cuts:
            self._cuts[key] = self._cut(self.inner_profile, 0.0) if self.band_width > 0 else self.remove()
        return self._cuts[key]

    def zone(self, margin=0.0):
        """Local rectangle around the cap, mapped to canvas coords."""
        x_min = min(self.min_x, -1.0) - 2.0 * margin - 2.0
        x_max = self.cap_x + self.half + margin
        y = 1.5 * self.half + margin
        rect = QPainterPath()
        rect.addRect(x_min, -y, x_max - x_min, 2.0 * y)
        return self.transform.map(rect)

    def band(self):
        """The side-line band: the strip between the side line's inner edge
        and the profile, continued a little past the strand's width.

        It is a plain polygon, not clipped to the body: callers paint it with
        the outer footprint as the painter's clip path (antialiased in the
        raster engine), which is exact and never involves Qt's path clipper.
        """
        if self.band_width <= 0:
            return QPainterPath()
        key = ('band', 0.0)
        if key not in self._cuts:
            self._cuts[key] = self.transform.map(
                _band_region(self.profile, self.inner_profile, self.half, 1.5 * self.half))
        return self._cuts[key]


class EndStyleGeometry:
    """Outer footprint / inner fill / side-line bands of a strand whose free
    end(s) carry a style. ``base_path`` defaults to ``strand.get_path()``; the
    shadow code passes ``strand.get_shadow_path()`` so the unstyled end keeps
    its classic shadow extension."""

    def __init__(self, strand, sides, base_path=None):
        self.strand = strand
        self.base_path = base_path if base_path is not None else strand.get_path()
        self.width = float(strand.width)
        self.stroke_width = float(strand.stroke_width)
        self.total = self.width + 2.0 * self.stroke_width
        self.ends = {}
        for side in sides:
            style = normalize_style(strand.end_styles[side]) if strand.end_styles[side] else None
            if style is None:
                continue
            visible = bool(strand.start_line_visible if side == 0 else strand.end_line_visible)
            self.ends[side] = StyledEnd(strand, side, style, visible)

        self.extended_path = self._extend_base_path()
        self.body = _stroke(self.extended_path, self.total, Qt.MiterJoin, Qt.FlatCap)
        outer = self.body
        for end in self.ends.values():
            outer = outer.subtracted(end.remove())
        outer.setFillRule(Qt.WindingFill)
        self.outer = outer
        self._inner = None
        self._bands = {}
        self._dilated = {}

    def _extend_base_path(self):
        """The centre line continued straight along the tangent at each styled
        end, far enough to reach the profile. Each end also learns where that
        continuation stops (its cuts reach exactly that far)."""
        path = QPainterPath(self.base_path)
        if path.isEmpty():
            return path
        if 1 in self.ends:
            end = self.ends[1]
            last = path.currentPosition()
            far = QPointF(last.x() + end.unit.x() * end.extension_length,
                          last.y() + end.unit.y() * end.extension_length)
            path.lineTo(far)
            end.cap_x = end.local_x(far)
        if 0 in self.ends:
            start = self.ends[0]
            first_element = path.elementAt(0)
            first = QPointF(first_element.x, first_element.y)
            far = QPointF(first.x() + start.unit.x() * start.extension_length,
                          first.y() + start.unit.y() * start.extension_length)
            prefix = QPainterPath()
            prefix.moveTo(far)
            prefix.lineTo(first)
            prefix.connectPath(path)
            path = prefix
            start.cap_x = start.local_x(far)
        return path

    # -- fill -------------------------------------------------------------
    def inner(self):
        """The fill: the (extended) fill stroker cut back to each side line's
        inner edge. One polygon cut per end, the same shape of operation as
        the outer footprint's cut, which the clipper handles reliably."""
        if self._inner is None:
            inner = _stroke(self.extended_path, self.width, Qt.MiterJoin, Qt.FlatCap)
            for end in self.ends.values():
                inner = inner.subtracted(end.fill_cut())
            inner.setFillRule(Qt.WindingFill)
            self._inner = inner
        return self._inner

    # -- side line ----------------------------------------------------------
    def band(self, side):
        if side not in self.ends:
            return QPainterPath()
        if side not in self._bands:
            self._bands[side] = self.ends[side].band()
        return self._bands[side]

    def extent_shift(self, side):
        end = self.ends.get(side)
        return end.extent_shift if end else 0.0

    # -- margins (shadow / mask helpers) ------------------------------------
    def dilated(self, margin, join=Qt.MiterJoin):
        """The outer footprint pushed outward by ``margin``.

        Unstyled ends keep the classic flat cap (the body is simply stroked
        wider, exactly like today's shadow and mask helpers), styled ends get
        the exact offset of their profile."""
        if margin <= 0:
            return self.outer
        key = (round(margin, 3), int(join))
        if key in self._dilated:
            return self._dilated[key]
        result = _stroke(self.extended_path, self.total + 2.0 * margin, join, Qt.FlatCap)
        for end in self.ends.values():
            result = result.subtracted(end.remove(margin))
        for end in self.ends.values():
            piece = self.outer.intersected(end.zone(margin))
            if not piece.isEmpty():
                # A hair wider than the body stroke so the union never sees
                # two coincident long edges (which the clipper mishandles).
                result = result.united(dilate(piece, margin + 0.3))
        result.setFillRule(Qt.WindingFill)
        self._dilated[key] = result
        return result


def geometry_cache_key(strand, sides, base_kind):
    """Signature of everything the geometry depends on (path compared separately)."""
    return (
        base_kind,
        tuple(sorted(sides)),
        round(float(strand.width), 4),
        round(float(strand.stroke_width), 4),
        tuple(style_key(strand.end_styles[s]) for s in (0, 1)),
        bool(strand.start_line_visible), bool(strand.end_line_visible),
    )
