"""The selection overlay (fill + border around the silhouette) is exact.

Mask mode paints the strand being picked with draw_selection_overlay, and
select mode uses it for the hover highlight. Every case here is checked pixel
by pixel against an oracle that paints the ideal border straight onto the same
device: the stroke of the footprint, twice the border width, with the
footprint itself erased. The oracle uses no Boolean path operation and no
intermediate layer, so it is correct by construction.

Covered: straight, curved and circle-capped strands, sixteen angles, thin and
thick widths, zoom 0.5x to 3x with pan, display scales 100 % to 200 %, strands
partly and fully off-screen, extreme zoom, the fill left untouched, the
border thickness, the painter's clip, and the painter state afterwards.

SCENARIOS is shared with scripts that render the cases for review.
"""
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPathStroker, QTransform
from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from attached_strand import AttachedStrand
from selection_utils import draw_selection_overlay
from strand import Strand

VIEW = 360          # logical size of the test canvas
MASK_BORDER = 8     # mask mode: stroke_width * 2
HOVER_BORDER = 2    # select/mask hover


# ---------------------------------------------------------------- strands
def straight(start, end, width=46, stroke=4):
    s = Strand(QPointF(*start), QPointF(*end), width, stroke_width=stroke)
    s.control_point1 = QPointF(start[0] + (end[0] - start[0]) / 3, start[1] + (end[1] - start[1]) / 3)
    s.control_point2 = QPointF(start[0] + 2 * (end[0] - start[0]) / 3, start[1] + 2 * (end[1] - start[1]) / 3)
    s.control_point_center = QPointF((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    s.update_side_line()
    return s


def loaded_straight(start, end, has_circles=(False, False), parent=None):
    """Straight geometry as stored in saved files: both control points at the
    start (the path-building branch the app takes for loaded designs)."""
    if parent is None:
        s = Strand(QPointF(*start), QPointF(*end), 46, stroke_width=4)
    else:
        s = AttachedStrand(parent, QPointF(*end), 1)
        s.start, s.end = QPointF(*start), QPointF(*end)
        s.width, s.stroke_width = 46, 4
        parent.attached_strands.append(s)
    s.has_circles = list(has_circles)
    s.control_point1 = QPointF(*start)
    s.control_point2 = QPointF(*start)
    s.update_control_points(reset_control_points=False)
    s.update_shape()
    s.update_side_line()
    return s


def curved(start, end, bend=90, width=46, stroke=4):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * bend, dx / length * bend
    s = Strand(QPointF(*start), QPointF(*end), width, stroke_width=stroke)
    s.control_point1 = QPointF(start[0] + dx / 3 + nx, start[1] + dy / 3 + ny)
    s.control_point2 = QPointF(start[0] + 2 * dx / 3 + nx, start[1] + 2 * dy / 3 + ny)
    s.control_point_center = QPointF((start[0] + end[0]) / 2 + nx, (start[1] + end[1]) / 2 + ny)
    s.update_side_line()
    return s


def with_circles():
    """A parent strand and its attached child: a circle cap at the joint on
    the parent's end and the child's start (real junction geometry)."""
    parent = loaded_straight((1316, 224), (1512, 420), has_circles=(False, True))
    child = loaded_straight((1512, 420), (1092, 560), has_circles=(True, False), parent=parent)
    return parent, child


def angled(degrees, length=240, origin=(1300, 500), width=46, stroke=4):
    a = math.radians(degrees)
    end = (round(origin[0] + length * math.cos(a)), round(origin[1] + length * math.sin(a)))
    return straight(origin, end, width, stroke)


USER = ((1288, 364), (1512, 616))  # strand 1_1 of the reported design


def user_strand(dx=0):
    return straight((USER[0][0] + dx, USER[0][1]), (USER[1][0] + dx, USER[1][1]))


# ---------------------------------------------------------------- rendering
def fit_transform(path, zoom=1.0, pan=(0.0, 0.0), view=VIEW):
    """Canvas-style transform: the footprint centred, then zoomed and panned
    like StrandDrawingCanvas.paintEvent (translate, pan, scale, translate)."""
    box = path.boundingRect()
    base = (view - 60) / max(box.width(), box.height())
    t = QTransform()
    t.translate(view / 2 + pan[0], view / 2 + pan[1])
    t.scale(base * zoom, base * zoom)
    t.translate(-box.center().x(), -box.center().y())
    return t


def blank(dpr, view=VIEW):
    image = QImage(int(round(view * dpr)), int(round(view * dpr)), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(dpr)
    image.fill(Qt.transparent)
    return image


def paint_actual(path, transform, dpr, border, fill=QColor(0, 0, 0, 0),
                 color=QColor(0, 0, 0), clip=None):
    image = blank(dpr)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    if clip is not None:
        painter.setClipRect(clip)
    painter.setTransform(transform)
    draw_selection_overlay(painter, path, fill, border_color=color, border_width=border)
    painter.end()
    return image


def paint_oracle(path, transform, dpr, border, color=QColor(0, 0, 0)):
    image = blank(dpr)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setTransform(transform)
    stroker = QPainterPathStroker()
    stroker.setWidth(border * 2)
    stroker.setJoinStyle(Qt.MiterJoin)
    stroker.setCapStyle(Qt.FlatCap)
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawPath(stroker.createStroke(path))
    painter.setCompositionMode(QPainter.CompositionMode_Clear)
    painter.drawPath(path)
    painter.end()
    return image


def alphas(image):
    image = image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
    data = bytes(image.constBits().asstring(image.sizeInBytes()))
    return data[3::4]


def compare(actual, oracle, tolerance=40):
    """(pixels that differ by more than `tolerance` alpha, pixels in the ring)."""
    a, b = alphas(actual), alphas(oracle)
    wrong = sum(1 for x, y in zip(a, b) if abs(x - y) > tolerance)
    ring = sum(1 for y in b if y > 127)
    return wrong, ring


# ---------------------------------------------------------------- scenarios
def _scenarios():
    cases = []
    for dx in (0, 14, 17, 23, 31, 32):
        cases.append(dict(id=f"user-1_1-moved-{dx}px", group="Reported strand, moved",
                          build=lambda dx=dx: [user_strand(dx)], border=MASK_BORDER))
    for deg in range(0, 360, 360 // 16):
        cases.append(dict(id=f"angle-{deg}", group="Angles",
                          build=lambda deg=deg: [angled(deg)], border=MASK_BORDER))
    for width, stroke in ((20, 2), (46, 4), (80, 8)):
        cases.append(dict(id=f"width-{width}-stroke-{stroke}", group="Widths",
                          build=lambda w=width, s=stroke: [angled(41, width=w, stroke=s)],
                          border=stroke * 2))
    for bend in (40, 120, -90):
        cases.append(dict(id=f"curved-bend-{bend}", group="Curved",
                          build=lambda b=bend: [curved((1300, 400), (1540, 610), b)], border=MASK_BORDER))
    cases.append(dict(id="circle-cap-parent", group="Circle caps",
                      build=lambda: [with_circles()[0]], border=MASK_BORDER))
    cases.append(dict(id="circle-cap-child", group="Circle caps",
                      build=lambda: [with_circles()[1]], border=MASK_BORDER))
    cases.append(dict(id="hover-border-2px", group="Hover border",
                      build=lambda: [user_strand(14)], border=HOVER_BORDER))
    for zoom, pan in ((0.5, (0, 0)), (1.7, (-40, 25)), (3.0, (60, -30))):
        cases.append(dict(id=f"zoom-{zoom}", group="Zoom and pan", zoom=zoom, pan=pan,
                          build=lambda: [user_strand(14)], border=MASK_BORDER))
    for dpr in (1.25, 1.5, 2.0):
        cases.append(dict(id=f"display-scale-{int(dpr * 100)}", group="Display scale", dpr=dpr,
                          build=lambda: [user_strand(14)], border=MASK_BORDER))
    cases.append(dict(id="partly-off-screen", group="Off-screen", zoom=1.0, pan=(170, 0),
                      build=lambda: [user_strand(14)], border=MASK_BORDER))
    return cases


SCENARIOS = _scenarios()


def render_case(case):
    """(path, transform, dpr, border, actual image, oracle image)."""
    path = case["build"]()[0].get_selection_path()
    transform = fit_transform(path, case.get("zoom", 1.0), case.get("pan", (0, 0)))
    dpr = case.get("dpr", 1.0)
    border = case["border"]
    return (path, transform, dpr, border,
            paint_actual(path, transform, dpr, border),
            paint_oracle(path, transform, dpr, border))


# ---------------------------------------------------------------- tests
@pytest.mark.parametrize("case", SCENARIOS, ids=[c["id"] for c in SCENARIOS])
def test_border_matches_the_ideal_ring(case):
    *_, actual, oracle = render_case(case)
    wrong, ring = compare(actual, oracle)
    assert ring > 200, "the oracle drew no ring; the case is broken"
    # Only anti-aliasing may differ, and only by a hair.
    assert wrong <= max(3, ring // 500), f"{wrong} wrong pixels of {ring}"


def test_fully_off_screen_paints_nothing():
    path = user_strand(14).get_selection_path()
    transform = QTransform.fromTranslate(-5000, -5000)
    image = paint_actual(path, transform, 1.0, MASK_BORDER)
    assert not any(alphas(image))


def test_extreme_zoom_only_works_on_the_visible_part():
    """At 40x the ring is ~70 000 px across; only the window is painted."""
    path = user_strand(14).get_selection_path()
    transform = fit_transform(path, zoom=40.0)
    started = time.perf_counter()
    actual = paint_actual(path, transform, 1.0, MASK_BORDER)
    elapsed = time.perf_counter() - started
    oracle = paint_oracle(path, transform, 1.0, MASK_BORDER)
    wrong, _ = compare(actual, oracle)
    assert wrong <= 3
    assert elapsed < 1.0


def _pixel(image, logical_point, transform):
    p = transform.map(logical_point)
    ratio = image.devicePixelRatio()
    return image.pixelColor(int(p.x() * ratio), int(p.y() * ratio))


@pytest.mark.parametrize("dpr", [1.0, 2.0])
def test_fill_is_untouched_and_the_border_sits_outside(dpr):
    strand = user_strand(14)
    path = strand.get_selection_path()
    transform = fit_transform(path)
    image = blank(dpr)
    image.fill(QColor(255, 255, 255))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setTransform(transform)
    draw_selection_overlay(painter, path, QColor(255, 0, 0, 128),
                           border_color=QColor(0, 0, 0, 128), border_width=MASK_BORDER)
    painter.end()

    along = QPointF(strand.end - strand.start)
    length = math.hypot(along.x(), along.y())
    unit = QPointF(along.x() / length, along.y() / length)
    normal = QPointF(-unit.y(), unit.x())
    half = strand.width / 2 + strand.stroke_width
    for t in (0.15, 0.5, 0.85):
        centre = strand.start + along * t
        inside = _pixel(image, centre, transform)
        assert (inside.red(), inside.green(), inside.blue()) == pytest.approx((255, 127, 127), abs=2)
        # Half a border width outside the edge, on both sides: the border only.
        for sign in (1, -1):
            out = _pixel(image, centre + normal * sign * (half + MASK_BORDER / 2), transform)
            assert (out.red(), out.green(), out.blue()) == pytest.approx((127, 127, 127), abs=2)
            # Past the border: untouched background.
            far = _pixel(image, centre + normal * sign * (half + MASK_BORDER + 3), transform)
            assert (far.red(), far.green(), far.blue()) == (255, 255, 255)


@pytest.mark.parametrize("border", [HOVER_BORDER, MASK_BORDER])
def test_border_is_as_thick_as_asked(border):
    strand = user_strand(14)
    path = strand.get_selection_path()
    zoom = 3.0
    transform = fit_transform(path, zoom=zoom)
    scale = transform.m11()
    image = paint_actual(path, transform, 1.0, border)
    along = QPointF(strand.end - strand.start)
    length = math.hypot(along.x(), along.y())
    normal = QPointF(-along.y() / length, along.x() / length)
    mid = strand.start + along * 0.5
    edge = strand.width / 2 + strand.stroke_width
    # Walk outward from just inside the edge in 0.05-unit steps, count solid ones.
    steps = [edge - 2 + i * 0.05 for i in range(int((border + 4) / 0.05))]
    solid = [d for d in steps if _pixel(image, mid + normal * d, transform).alpha() > 127]
    thickness = (max(solid) - min(solid)) if solid else 0
    assert thickness == pytest.approx(border, abs=1.5 / scale + 0.1)


def test_painter_clip_is_respected():
    path = user_strand(14).get_selection_path()
    transform = fit_transform(path)
    clip = QRectF(0, 0, VIEW / 2, VIEW)
    image = paint_actual(path, transform, 1.0, MASK_BORDER, clip=clip)
    for y in range(0, VIEW, 3):
        for x in range(VIEW // 2 + 1, VIEW, 3):
            assert image.pixelColor(x, y).alpha() == 0


def test_painter_state_is_restored():
    path = user_strand(14).get_selection_path()
    image = blank(1.0)
    painter = QPainter(image)
    transform = fit_transform(path, zoom=1.3)
    painter.setTransform(transform)
    painter.setOpacity(0.7)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    before = (painter.worldMatrixEnabled(), painter.viewTransformEnabled(),
              painter.combinedTransform())
    try:
        draw_selection_overlay(painter, path, QColor(255, 0, 0, 128),
                               border_color=QColor(0, 0, 0, 128), border_width=MASK_BORDER)
        assert painter.transform() == transform
        assert (painter.worldMatrixEnabled(), painter.viewTransformEnabled(),
                painter.combinedTransform()) == before
        assert painter.opacity() == pytest.approx(0.7)
        assert painter.compositionMode() == QPainter.CompositionMode_SourceOver
    finally:
        painter.end()
