"""The selection overlay is exact in the running app.

tests/mask_piece/mask_mode_pick.json is the reported layout: 1_1, 2_1 with
2_2 attached at its end, 3_1, and the masks 1_1_2_2 and 2_2_3_1. The real
MainWindow loads it offscreen. For each highlight the canvas paints, the
pixels the overlay changes on screen are compared with an oracle overlay
painted with the very transform the canvas used: nothing may change outside
the oracle (no spill), and nothing the oracle covers may stay unchanged (no
notch or gap).

Covered: picking the first strand in mask mode (the reported view), the
same zoomed and panned, the yellow hover on the attached strand with its
circle cap, the hover on a mask in select mode, and two positions of 1_1
where the old Boolean-built border broke in the app.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPathStroker, QTransform
from PyQt5.QtWidgets import QApplication, QFileDialog

APP = QApplication.instance() or QApplication([])

import mask_mode
import select_mode
import selection_utils
from main_window import MainWindow

DESIGN = Path(__file__).resolve().parent / "mask_piece" / "mask_mode_pick.json"


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


@pytest.fixture
def window(monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (str(DESIGN), "JSON Files (*.json)")))
    win = MainWindow()
    win.show()
    win.resize(1600, 900)
    pump(200)
    win.load_project()
    pump(300)
    yield win
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


@pytest.fixture
def recorded(monkeypatch):
    """Every overlay the modes paint, with the painter transform used."""
    calls = []

    def recorder(painter, path, fill_color, border_color=None, border_width=0, *args, **kwargs):
        calls.append(dict(transform=painter.transform(), path=path, fill=QColor(fill_color),
                          border=QColor(border_color) if border_color is not None else None,
                          width=border_width, scale=painter.device().devicePixelRatioF()))
        return selection_utils.draw_selection_overlay(
            painter, path, fill_color, border_color, border_width, *args, **kwargs)

    monkeypatch.setattr(mask_mode, "draw_selection_overlay", recorder)
    monkeypatch.setattr(select_mode, "draw_selection_overlay", recorder)
    return calls


def frame(canvas):
    canvas.update()
    pump(120)
    return canvas.grab().toImage().convertToFormat(QImage.Format_ARGB32)


def coverage(call, like, part):
    """Where the overlay's fill or border lies, one byte per screen pixel:
    255 when every sub-pixel is covered, 0 when none is, 128 otherwise.

    The canvas paints at `scale` times the screen resolution and scales
    down, so the oracle is painted at that resolution too (the border as
    the ideal ring: no Booleans) and a screen pixel counts as covered only
    when all of its sub-pixels are."""
    k = max(1, int(round(call.get("scale", 1.0) / like.devicePixelRatio())))
    width, height = like.width(), like.height()
    image = QImage(width * k, height * k, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setTransform(call["transform"] * QTransform.fromScale(k, k))
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0))
    if part == "border":
        stroker = QPainterPathStroker()
        stroker.setWidth(call["width"] * 2)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        painter.drawPath(stroker.createStroke(call["path"]))
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
    painter.drawPath(call["path"])
    painter.end()
    alpha = pixels(image.convertToFormat(QImage.Format_ARGB32))[3::4]
    out = bytearray(width * height)
    row = width * k
    for y in range(height):
        for x in range(width):
            block = [alpha[(y * k + j) * row + x * k + i] for j in range(k) for i in range(k)]
            out[y * width + x] = 255 if min(block) == 255 else (0 if max(block) == 0 else 128)
    return bytes(out)


def pixels(image):
    return bytes(image.constBits().asstring(image.sizeInBytes()))


def blend(under, color):
    """`color` painted over the opaque BGRA pixel `under`."""
    a = color.alpha() / 255.0
    return (round(color.blue() * a + under[0] * (1 - a)),
            round(color.green() * a + under[1] * (1 - a)),
            round(color.red() * a + under[2] * (1 - a)))


def _everywhere_around(alpha, width, height, value):
    """Pixel indexes whose 3x3 neighbourhood all has coverage `value`.

    The canvas paints at twice the resolution and scales down, which blends
    the pixels right on an edge; one pixel in from every edge the colour
    must be exact."""
    keep = set()
    for i in range(len(alpha)):
        if alpha[i] != value:
            continue
        x, y = i % width, i // width
        if 0 < x < width - 1 and 0 < y < height - 1 and all(
                alpha[(y + dy) * width + x + dx] == value
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
            keep.add(i)
    return keep


def check_overlay(shown, plain, call):
    """(spill, wrong, checked).

    spill: pixels that changed although the overlay does not come within a
    pixel of them.
    wrong: pixels the fill or the border fully covers whose colour is not
    that colour blended over what was there before: exactly (within 2) one
    pixel in from every edge, and within 40 right on an edge, where the
    canvas's 2x downscale blends a little. A gap, a notch or a doubled-up
    blot is off by about 127 and shows up either way; the edge tier is what
    checks a 2 px hover border.
    """
    a, b = pixels(shown), pixels(plain)
    width, height = shown.width(), shown.height()
    fill = coverage(call, shown, "fill")
    has_border = call["border"] is not None and call["width"] > 0
    border = coverage(call, shown, "border") if has_border else bytes(len(fill))
    overlay = bytes(max(f, r) for f, r in zip(fill, border))
    spill = sum(1 for i in _everywhere_around(overlay, width, height, 0)
                if a[4 * i:4 * i + 3] != b[4 * i:4 * i + 3])
    wrong = checked = 0
    for part, alpha in (("fill", fill), ("border", border if has_border else None)):
        if alpha is None:
            continue
        color = call[part]
        inner = _everywhere_around(alpha, width, height, 255)
        for i in range(len(alpha)):
            if alpha[i] != 255:
                continue
            checked += 1
            limit = 2 if i in inner else 40
            expected = blend(b[4 * i:4 * i + 3], color)
            if any(abs(x - y) > limit for x, y in zip(a[4 * i:4 * i + 3], expected)):
                wrong += 1
    return spill, wrong, checked


def assert_exact(shown, plain, calls):
    assert calls, "the mode painted no overlay"
    spill, wrong, checked = check_overlay(shown, plain, calls[-1])
    assert checked > 1000, "the overlay is not on screen"
    assert spill == 0, f"{spill} pixels changed outside the overlay"
    assert wrong == 0, f"{wrong} of {checked} overlay pixels have the wrong colour"


def by_name(canvas):
    return {s.layer_name: s for s in canvas.strands}


@pytest.mark.parametrize("view", ["reported", "zoomed"])
def test_mask_mode_pick_first_strand(window, recorded, view):
    canvas = window.canvas
    strands = by_name(canvas)
    assert list(strands) == ["1_1", "2_1", "2_2", "3_1", "1_1_2_2", "2_2_3_1"]
    if view == "zoomed":
        canvas.zoom_factor = 1.6
    canvas.center_all_strands()
    if view == "zoomed":
        canvas.pan_offset_x += 35
        canvas.pan_offset_y -= 20
    canvas.set_mode("mask")
    pump(80)
    canvas.mask_mode.selected_strands = []
    plain = frame(canvas)
    canvas.mask_mode.selected_strands = [strands["1_1"]]
    recorded.clear()
    shown = frame(canvas)
    assert recorded[-1]["width"] == strands["1_1"].stroke_width * 2
    assert_exact(shown, plain, recorded)


def test_mask_mode_hover_on_attached_strand_with_circle(window, recorded):
    canvas = window.canvas
    strands = by_name(canvas)
    canvas.center_all_strands()
    canvas.set_mode("mask")
    pump(80)
    canvas.mask_mode.hovered_strand = None
    plain = frame(canvas)
    canvas.mask_mode.hovered_strand = strands["2_2"]
    recorded.clear()
    shown = frame(canvas)
    assert_exact(shown, plain, recorded)


def test_select_mode_hover_on_a_mask(window, recorded):
    canvas = window.canvas
    strands = by_name(canvas)
    canvas.center_all_strands()
    canvas.set_mode("select")
    pump(80)
    canvas.select_mode.hovered_strand = None
    plain = frame(canvas)
    canvas.select_mode.hovered_strand = strands["1_1_2_2"]
    recorded.clear()
    shown = frame(canvas)
    assert_exact(shown, plain, recorded)


@pytest.mark.parametrize("dx, dy", [(2, 20), (4, 36)])
def test_mask_mode_pick_where_the_old_border_broke(window, recorded, dx, dy):
    """1_1 moved a few pixels and given evenly spaced control points: in the
    app, the old Boolean-built border coloured 5 286 and 620 overlay pixels
    wrong here."""
    canvas = window.canvas
    strand = by_name(canvas)["1_1"]
    start, end = QPointF(1288 + dx, 364 + dy), QPointF(1512 + dx, 616 + dy)
    strand.start, strand.end = start, end
    strand.control_point1 = start + (end - start) / 3
    strand.control_point2 = start + (end - start) * 2 / 3
    strand.control_point_center = (start + end) / 2
    strand.update_side_line()
    canvas.center_all_strands()
    canvas.set_mode("mask")
    pump(80)
    canvas.mask_mode.selected_strands = []
    plain = frame(canvas)
    canvas.mask_mode.selected_strands = [strand]
    recorded.clear()
    shown = frame(canvas)
    assert_exact(shown, plain, recorded)
