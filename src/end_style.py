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


def _clip_polyline_y(pts, ylim):
    """The polyline restricted to |y| <= ylim (crossing points inserted)."""
    if not pts:
        return []
    out = []
    prev = None
    for p in pts:
        inside = abs(p.y()) <= ylim
        if prev is not None:
            prev_inside = abs(prev.y()) <= ylim
            if prev_inside != inside or (not prev_inside and not inside and (prev.y() > 0) != (p.y() > 0)):
                # cross one or both bounds between prev and p
                for bound in ((-ylim, ylim) if prev.y() < p.y() else (ylim, -ylim)):
                    lo, hi = min(prev.y(), p.y()), max(prev.y(), p.y())
                    if lo < bound < hi:
                        t = (bound - prev.y()) / (p.y() - prev.y())
                        out.append(QPointF(prev.x() + (p.x() - prev.x()) * t, bound))
        if inside:
            out.append(p)
        prev = p
    return out


def _runs_by_x(pts, x0, ahead):
    """Runs of consecutive points ahead of (x > x0) or behind (x < x0) the
    plane, each starting and ending on the plane."""
    runs = []
    run = []

    def cross(a, b):
        t = (x0 - a.x()) / (b.x() - a.x())
        return QPointF(x0, a.y() + (b.y() - a.y()) * t)

    prev = None
    for p in pts:
        keep = p.x() > x0 if ahead else p.x() < x0
        if prev is not None:
            prev_keep = prev.x() > x0 if ahead else prev.x() < x0
            if prev_keep != keep:
                c = cross(prev, p)
                if keep:
                    run = [c]
                else:
                    run.append(c)
                    runs.append(run)
                    run = []
        if keep:
            run.append(p)
        prev = p
    if len(run) >= 2:
        runs.append(run)
    return [r for r in runs if len(r) >= 2]


def _runs_to_polygons(runs, x0):
    """Close each run back along the plane x = x0 into a simple polygon."""
    polys = []
    for run in runs:
        poly = QPainterPath()
        poly.moveTo(QPointF(x0, run[0].y()))
        for q in run:
            poly.lineTo(q)
        poly.lineTo(QPointF(x0, run[-1].y()))
        poly.closeSubpath()
        polys.append(poly)
    return polys


def _ahead_polygons(prof, half, y_lim, x0=-1.0):
    """The region between the plane x = x0 (just behind the endpoint) and the
    profile, where the profile is ahead of it, within |y| <= y_lim: the cap
    piece that is *added* to the classic body. Built directly, one simple
    polygon per run, so no boolean operation is needed."""
    first, last = _chord_extended(prof, half, y_lim + 1.0)
    pts = _clip_polyline_y([first] + list(prof) + [last], y_lim)
    return _runs_to_polygons(_runs_by_x(pts, x0, ahead=True), x0)


def _behind_polygons(prof, half, y_lim, x0=0.0):
    """The region outward of the profile but behind the plane x = x0: what a
    cut *removes* from the classic body. Nothing ahead of the endpoint plane
    is ever removed, so a body that bends back in front of its own end (a
    tight curl) keeps every pixel it has today."""
    first, last = _chord_extended(prof, half, y_lim)
    pts = [first] + list(prof) + [last]
    return _runs_to_polygons(_runs_by_x(pts, x0, ahead=False), x0)


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

    def __init__(self, strand, side, style, line_visible, frame=None):
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

        point, angle = frame if frame is not None else end_frame(strand, side)
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
        self.edge = self.transform.map(_edge_path(self.profile, half))
        self.corners = (self.transform.map(self.profile[0]), self.transform.map(self.profile[-1]))
        self._cuts = {}

    def local_x(self, point):
        return ((point.x() - self.point.x()) * self.unit.x()
                + (point.y() - self.point.y()) * self.unit.y())

    def _mapped(self, polygons):
        return [self.transform.map(poly) for poly in polygons]

    # The cut plane sits a hair ahead of the endpoint plane, so the body's
    # own flat cap (and the mitre spike a tight bend leaves along it) falls
    # cleanly inside the cut instead of straddling its edge.
    CUT_PLANE = 0.5

    def behind_cuts(self, margin=0.0, x0=CUT_PLANE):
        """Polygons removed from the classic body (outward of the profile,
        behind the endpoint plane) for a body stroked ``margin`` wider."""
        key = ('behind', round(margin, 3), round(x0, 3))
        if key not in self._cuts:
            self._cuts[key] = self._mapped(_behind_polygons(self.profile, self.half, 1.5 * self.half + margin, x0))
        return self._cuts[key]

    def behind_fill_cuts(self, x0=CUT_PLANE):
        """The same for the fill, along the side line's inner edge."""
        key = ('behind_fill', round(x0, 3))
        if key not in self._cuts:
            prof = self.inner_profile if self.band_width > 0 else self.profile
            self._cuts[key] = self._mapped(_behind_polygons(prof, self.half, 1.5 * self.half, x0))
        return self._cuts[key]

    def ahead_pieces(self, margin=0.0):
        """Polygons added ahead of the endpoint plane, to the stroke body of
        half-width ``half + margin``."""
        key = ('ahead', round(margin, 3))
        if key not in self._cuts:
            self._cuts[key] = self._mapped(_ahead_polygons(self.profile, self.half, self.half + margin))
        return self._cuts[key]

    def ahead_fill_pieces(self):
        """Polygons added ahead of the endpoint plane to the fill body."""
        key = ('ahead_fill', 0.0)
        if key not in self._cuts:
            prof = self.inner_profile if self.band_width > 0 else self.profile
            self._cuts[key] = self._mapped(_ahead_polygons(prof, self.half, self.half - self.stroke_width))
        return self._cuts[key]

    def remove(self, margin=0.0):
        """Everything outward of the profile within the cap zone, as one path
        (for the highlight and other whole-region users)."""
        key = ('remove', round(margin, 3))
        if key not in self._cuts:
            y_lim = 1.5 * self.half + margin
            first, last = _chord_extended(self.profile, self.half, y_lim)
            x_far = self.max_x + self.half + margin + 12.0
            poly = QPainterPath()
            poly.moveTo(first)
            for p in self.profile:
                poly.lineTo(p)
            poly.lineTo(last)
            poly.lineTo(QPointF(x_far, last.y()))
            poly.lineTo(QPointF(x_far, first.y()))
            poly.closeSubpath()
            self._cuts[key] = self.transform.map(poly)
        return self._cuts[key]

    def zone(self, margin=0.0):
        """Local rectangle around the cap, mapped to canvas coords."""
        x_min = min(self.min_x, -1.0) - 2.0 * margin - 2.0
        x_max = self.max_x + self.half + margin + 12.0
        y = 1.5 * self.half + margin
        rect = QPainterPath()
        rect.addRect(x_min, -y, x_max - x_min, 2.0 * y)
        return self.transform.map(rect)

    def band(self):
        """The side-line band: the strip between the side line's inner edge
        and the profile, across the strand's width.

        It is a plain polygon, not clipped to the body: callers paint it with
        the outer footprint as the painter's clip path (antialiased in the
        raster engine), which is exact and never involves Qt's path clipper.
        """
        if self.band_width <= 0:
            return QPainterPath()
        key = ('band', 0.0)
        if key not in self._cuts:
            # Exactly the strand's width, like the classic side line: a body
            # that bulges or curls past the width next to its end is body,
            # not side line.
            self._cuts[key] = self.transform.map(
                _band_region(self.profile, self.inner_profile, self.half, self.half + _EDGE_CLEARANCE))
        return self._cuts[key]


def _signed_area(path):
    area = 0.0
    for polygon in path.toSubpathPolygons():
        n = polygon.count()
        for i in range(n):
            a, b = polygon[i], polygon[(i + 1) % n]
            area += a.x() * b.y() - b.x() * a.y()
    return area


class EndStyleGeometry:
    """Outer footprint / inner fill / side-line bands of a strand whose free
    end(s) carry a style. ``base_path`` defaults to ``strand.get_path()``; the
    shadow code passes ``strand.get_shadow_path()`` so the unstyled end keeps
    its classic shadow extension.

    The body is the classic stroke of the centre line, plus polygons built
    directly for whatever the profile adds ahead of the endpoint plane, minus
    polygons for whatever it removes behind that plane. Nothing ahead of the
    plane is ever removed from the classic body, so a strand that bends back
    in front of its own end keeps every pixel it has today, and with the
    default record the drawing is the classic one."""

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
        self._strokes = {}

        # Paint bodies: winding-filled multi-subpath paths, no boolean ops
        self.body = self._paint_body(self.total, [p for e in self.ends.values() for p in e.ahead_pieces()])
        self._fill_body = None
        # Boolean footprint for selection, shadows and masks
        self.outer = self._boolean_footprint(
            self.total, Qt.MiterJoin,
            [p for e in self.ends.values() for p in e.ahead_pieces()],
            [p for e in self.ends.values() for p in e.behind_cuts()])
        self._inner = None
        self._bands = {}
        self._dilated = {}

    # -- bodies -------------------------------------------------------------
    def _classic(self, width, join=Qt.MiterJoin):
        key = (round(width, 3), int(join))
        if key not in self._strokes:
            self._strokes[key] = _stroke(self.base_path, width, join, Qt.FlatCap)
        return self._strokes[key]

    def _paint_body(self, width, pieces, join=Qt.MiterJoin):
        body = QPainterPath()
        body.setFillRule(Qt.WindingFill)
        body.addPath(self._classic(width, join))
        for piece in pieces:
            body.addPath(piece)
        return body

    def _boolean_footprint(self, width, join, pieces, cuts):
        """(classic − cuts) ∪ pieces, for the path consumers."""
        result = self._classic(width, join)
        for cut in cuts:
            result = result.subtracted(cut)
        for piece in pieces:
            result = result.united(piece)
        result.setFillRule(Qt.WindingFill)
        return result

    # -- painting without the clipper ------------------------------------
    # What the canvas paints never goes through QPainterPath's boolean ops:
    # the classic body plus the cap pieces are drawn with the painter
    # clipped to everything but the cut polygons. Clip paths honour fill
    # rules and are antialiased, so this is exact where the clipper is not.
    def fill_body(self):
        """The uncut fill body (paint it under keep_inner_clip)."""
        if self._fill_body is None:
            self._fill_body = self._paint_body(
                self.width, [p for e in self.ends.values() for p in e.ahead_fill_pieces()])
        return self._fill_body

    def _keep_clip(self, polygons):
        """Winding-filled clip: a big rectangle (+1) minus the cut polygons
        (oriented against the rectangle)."""
        rect_path = QPainterPath()
        pad = 6.0 * self.total + 20.0
        rect_path.addRect(self.body.boundingRect().adjusted(-pad, -pad, pad, pad))
        rect_sign = _signed_area(rect_path) >= 0
        clip = QPainterPath()
        clip.setFillRule(Qt.WindingFill)
        clip.addPath(rect_path)
        for polygon in polygons:
            if (_signed_area(polygon) >= 0) == rect_sign:
                polygon = polygon.toReversed()
            clip.addPath(polygon)
        return clip

    def keep_outer_clip(self):
        """Everything but the cuts: clip for painting the stroke body."""
        return self._keep_clip([p for e in self.ends.values() for p in e.behind_cuts()])

    def keep_inner_clip(self):
        """Everything but the fill cuts: clip for painting the fill body."""
        return self._keep_clip([p for e in self.ends.values() for p in e.behind_fill_cuts()])

    # -- boolean footprints -------------------------------------------------
    def inner(self):
        """The fill footprint: the fill body cut back to each side line's
        inner edge."""
        if self._inner is None:
            self._inner = self._boolean_footprint(
                self.width, Qt.MiterJoin,
                [p for e in self.ends.values() for p in e.ahead_fill_pieces()],
                [p for e in self.ends.values() for p in e.behind_fill_cuts()])
        return self._inner

    def band(self, side):
        if side not in self.ends:
            return QPainterPath()
        if side not in self._bands:
            self._bands[side] = self.ends[side].band()
        return self._bands[side]

    def extent_shift(self, side):
        end = self.ends.get(side)
        return end.extent_shift if end else 0.0

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
        result = self._boolean_footprint(
            self.total + 2.0 * margin, join,
            [p for e in self.ends.values() for p in e.ahead_pieces(margin)],
            [p for e in self.ends.values() for p in e.behind_cuts(margin)])
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
