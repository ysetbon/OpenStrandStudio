"""The selection outline of a strand above a mask's crossing stays whole.

Masks are drawn after every strand. A strand above both of a mask's strands
lies above their crossing, and the mask's piece already keeps clear of its
body (test_mask_piece_cover.py), but the red selection outline reaches
5 px past the body: the mask's lift shadow, its piece and the shadows put
back on it painted over that part, so the outline broke where the selected
strand passed over a masked crossing.

tests/mask_piece/selected_over_crossing.json is the user's design: 1_1, 2_1,
3_1 and 4_1, masks 2_1_3_1 and 1_1_2_1 above them, and 4_1 across the
crossing 1_1_2_1 lifts. Runs the real MainWindow offscreen.
"""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath, QPainterPathStroker
from PyQt5.QtWidgets import QApplication, QFileDialog

import shader_utils
from main_window import MainWindow

APP = QApplication.instance() or QApplication([])
DESIGN = Path(__file__).resolve().parent / "mask_piece" / "selected_over_crossing.json"


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
    if not win.canvas.shadow_enabled:
        win.toggle_shadow_button.click()
    yield win
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


def red_pixels(image):
    """Pixels painted in the pure selection red."""
    image = image.convertToFormat(QImage.Format_ARGB32)
    return {(x, y) for y in range(image.height()) for x in range(image.width())
            if QColor(image.pixel(x, y)).getRgb()[:3] == (255, 0, 0)}


def frame(canvas):
    canvas.update()
    pump(120)
    return canvas.grab().toImage()


@pytest.mark.parametrize("view", ["plain", "zoomed"])
def test_the_outline_over_a_masked_crossing_is_whole(window, view):
    canvas = window.canvas
    by_name = {s.layer_name: s for s in canvas.strands}
    assert list(by_name) == ["1_1", "2_1", "3_1", "4_1", "2_1_3_1", "1_1_2_1"]
    canvas.select_strand(list(by_name).index("4_1"))
    pump(100)
    if view == "plain":
        # Strand.draw's usual path
        canvas.zoom_factor, canvas.pan_offset_x, canvas.pan_offset_y = 1.0, 0, 0
    else:
        # The direct-drawing path, taken when zoomed or panned
        canvas.zoom_factor = 0.9
        canvas.center_all_strands()

    shown = red_pixels(frame(canvas))
    for name in ("2_1_3_1", "1_1_2_1"):
        by_name[name].is_hidden = True
    whole = red_pixels(frame(canvas))
    for name in ("2_1_3_1", "1_1_2_1"):
        by_name[name].is_hidden = False

    assert len(whole) > 1000
    assert not whole - shown


def ring():
    """A selection outline like Strand._draw_unified_highlight's: a stroke of
    a stroke, which overlaps itself (QPainterPath.simplified() and the
    boolean operations drop one side of it)."""
    line = QPainterPath()
    line.moveTo(438, 55)
    line.lineTo(494, 529)
    body = QPainterPathStroker()
    body.setWidth(54)
    outline = QPainterPathStroker()
    outline.setWidth(10)
    outline.setJoinStyle(Qt.MiterJoin)
    return outline.createStroke(body.createStroke(line))


def layers(*names):
    strands = {name: SimpleNamespace(layer_name=name, start=None, end=None) for name in names}
    canvas = SimpleNamespace(layer_state_manager=SimpleNamespace(getOrder=lambda: list(names)))
    mask = SimpleNamespace(first_selected_strand=strands["a"], second_selected_strand=strands["b"],
                           canvas=canvas, layer_name="mask")
    return strands, mask


@pytest.mark.parametrize("zoom, pan, ratio", [(1.0, (0, 0), 1.0), (1.7, (-120, 40), 1.0),
                                              (0.6, (55.5, 13.25), 1.0), (1.0, (0, 0), 1.5),
                                              (0.9, (20.5, -7), 1.25)])
def test_the_mask_paints_everywhere_but_on_the_outline(monkeypatch, zoom, pan, ratio):
    """clip_painted_highlights leaves out exactly the pixels the outline
    painted, at any zoom and display scale: the mask paints all the others
    (here the whole canvas is within the mask's reach)."""
    monkeypatch.setattr(shader_utils, "_mask_reach", lambda mask, cache: QRectF(-5000, -5000, 10000, 10000))
    strands, mask = layers("a", "b", "top", "mask")
    outline = ring()

    def paint(with_mask):
        image = QImage(700, 700, QImage.Format_ARGB32)
        image.setDevicePixelRatio(ratio)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(*pan)
        painter.scale(zoom, zoom)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.red)
        painter.drawPath(outline)
        shader_utils.note_painted_highlight(painter, strands["top"], outline)
        if with_mask:
            painter.save()
            shader_utils.clip_painted_highlights(painter, mask)
            painter.fillRect(-2000, -2000, 5000, 5000, QColor(0, 0, 255))
            painter.restore()
        painter.end()
        return image

    alone, masked = paint(False), paint(True)
    white, blue = QColor(Qt.white).rgb(), QColor(0, 0, 255).rgb()
    outline_pixels = 0
    for y in range(700):
        for x in range(700):
            if alone.pixel(x, y) != white:
                outline_pixels += 1
                assert masked.pixel(x, y) == alone.pixel(x, y), (x, y)
            else:
                assert masked.pixel(x, y) == blue, (x, y)
    assert outline_pixels > 1000


def test_only_outlines_above_the_crossing_are_kept():
    """Below either of the mask's strands, or itself one of them, the
    outline is covered like the strand; so is a strand that continues one of
    them at a joint (the piece hides the joint)."""
    strands, mask = layers("below", "a", "between", "b", "top", "joined", "mask")
    strands["a"].start, strands["a"].end = "a0", "a1"
    strands["b"].start, strands["b"].end = "b0", "b1"
    image = QImage(10, 10, QImage.Format_ARGB32)
    painter = QPainter(image)
    for name in ("below", "a", "between", "b", "top", "joined"):
        path = QPainterPath()
        path.addRect(0, 0, 1, 1)
        shader_utils.note_painted_highlight(painter, strands[name], path)
    original = shader_utils._joined
    shader_utils._joined = lambda item, ends: item is strands["joined"]
    try:
        kept = shader_utils._highlights_above(mask, shader_utils._frame_cache(painter))
    finally:
        shader_utils._joined = original
        painter.end()
    assert len(kept) == 1


def test_nothing_is_clipped_without_a_selected_strand_above():
    strands, mask = layers("a", "b", "top", "mask")
    image = QImage(10, 10, QImage.Format_ARGB32)
    painter = QPainter(image)
    try:
        assert shader_utils._highlight_region(painter, mask).isEmpty()
    finally:
        painter.end()
