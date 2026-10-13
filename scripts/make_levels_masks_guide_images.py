"""Render the pictures of the Settings > Levels & Masks guide with the app itself.

Every picture is a real scene drawn by the real canvas and layer panel: the
script loads the 1x1 design in scripts/guide_designs/ with every layer on the
ground, grabs the canvas and the layer list, then adds the level with the
layer panel's own New Level and Move down and grabs them again, in each
theme. So the guide shows exactly what the app draws.

Run it again after a change to how strands, masks or the layer panel look:

    python scripts/make_levels_masks_guide_images.py

The PNGs go to src/guide_images/levels_masks/: the canvas pictures once, the
layer lists once per theme. They are shown at half size (2x pixels).
"""
import json
import os
import sys
import tempfile
import types

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
# The window saves settings when it closes: keep them out of the user's own
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='oss_guide_settings_')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)
OUT = os.path.join(SRC, 'guide_images', 'levels_masks')

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QTimer  # noqa: E402
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QRegion  # noqa: E402
from PyQt5.QtWidgets import QApplication, QWidget  # noqa: E402

try:  # QtMultimedia needs system audio libraries that a headless box may lack
    import PyQt5.QtMultimedia  # noqa: F401
    import PyQt5.QtMultimediaWidgets  # noqa: F401
except ImportError:
    _mm = types.ModuleType('PyQt5.QtMultimedia')
    _mm.QMediaPlayer = type('QMediaPlayer', (), {})
    _mm.QMediaContent = type('QMediaContent', (), {})
    _mw = types.ModuleType('PyQt5.QtMultimediaWidgets')
    _mw.QVideoWidget = QWidget
    sys.modules['PyQt5.QtMultimedia'] = _mm
    sys.modules['PyQt5.QtMultimediaWidgets'] = _mw

APP = QApplication.instance() or QApplication(sys.argv)

from main_window import MainWindow  # noqa: E402
from save_load_manager import apply_loaded_strands, load_strands_from_data  # noqa: E402
from settings_dialog import SettingsDialog  # noqa: E402

SettingsDialog.save_settings_to_file = lambda self: None  # never touch the user's settings

# ----------------------------------------------------------------------
# The design
# ----------------------------------------------------------------------
# A real design: a 1x1 knot (mxn_rh_stretch_1x1_continue_k_0)
# where 1_4 continues 1_3 and runs back over it, across the crossing that
# mask 2_2_1_3 lifts. Saved here with every layer on the ground, as it was
# before its level was added.
KNOT = os.path.join(ROOT, 'scripts', 'guide_designs', 'mxn_rh_stretch_1x1_continue_k_0.json')
KNOT_VIEW = QRect(1020, 250, 370, 290)
# Where mask 2_2_1_3 cuts 1_4 when they share a level (2_2 crosses 1_3 and 1_4 there)
KNOT_CUT = QPointF(1260, 364)


def knot():
    with open(KNOT, encoding='utf-8') as f:
        return json.load(f)


def lift_1_4(win):
    """What the user does: New Level, then Move down on the Level 1 row,
    which takes the top layer of the ground (1_4) onto Level 1."""
    lp = win.layer_panel
    lp.new_level_button.click()
    pump()
    lp.move_level(1, up=False)
    pump(120)
    on_level_1 = [s.layer_name for s in win.canvas.strands if getattr(s, 'level', 0) == 1]
    assert on_level_1 == ['1_4'], on_level_1


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------
def pump(ms=60):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


def open_window(theme):
    win = MainWindow()
    win.apply_theme(theme)
    win.show()
    win.resize(1600, 1000)
    pump(200)
    return win


def load(win, data):
    canvas = win.canvas
    canvas.strands = []
    loaded = load_strands_from_data(json.loads(json.dumps(data)), canvas)
    apply_loaded_strands(canvas, loaded[0], loaded[1])
    if hasattr(win, 'set_select_mode'):
        win.set_select_mode()
    canvas.selected_strand = None
    canvas.selected_attached_strand = None
    for s in canvas.strands:
        s.is_selected = False
    canvas.show_grid = False
    canvas.show_control_points = False
    canvas.shadow_enabled = data.get('shadow_enabled', True)
    win.layer_panel.set_layer_tab('strands')
    win.layer_panel.refresh()
    pump(120)


def grab_canvas(win, view, zoom=1.0, ring=None):
    """The part *view* of the canvas (canvas coordinates) at *zoom*, framed.
    *ring* circles a canvas point, to point at what the caption talks about."""
    canvas = win.canvas
    # Big enough for the whole view (the offscreen screen is small), like
    # json_to_png_exporter does
    canvas.setFixedSize(int(view.width() * zoom) + 80, int(view.height() * zoom) + 80)
    pump(80)
    canvas.zoom_factor = zoom
    centre = QPointF(view.center())
    canvas.pan_offset_x = 0
    canvas.pan_offset_y = 0
    here = canvas.canvas_to_screen(centre)
    canvas.pan_offset_x = canvas.width() / 2 - here.x()
    canvas.pan_offset_y = canvas.height() / 2 - here.y()
    canvas.update()
    pump(80)
    image = canvas.grab().toImage()
    top_left = canvas.canvas_to_screen(QPointF(view.left(), view.top()))
    image = image.copy(int(round(top_left.x())), int(round(top_left.y())),
                       int(round(view.width() * zoom)), int(round(view.height() * zoom)))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    if ring is not None:
        centre = QPointF((ring.x() - view.left()) * zoom, (ring.y() - view.top()) * zoom)
        painter.setPen(QPen(QColor('#E5484D'), 5))
        painter.drawEllipse(centre, 38 * zoom, 38 * zoom)
    # A thin grey frame, so the white canvas stands out on a white page too
    painter.setPen(QPen(QColor('#BDBDBD'), 2))
    painter.drawRect(QRectF(1, 1, image.width() - 2, image.height() - 2))
    painter.end()
    canvas.zoom_factor = 1.0
    canvas.setMinimumSize(0, 0)
    canvas.setMaximumSize(16777215, 16777215)
    return image


def grab_layer_list(win, tab='strands', scale=2):
    """The layer list of *tab* as the panel shows it, cropped to its rows and
    drawn at *scale* times its size (the canvas pictures are 2x as well)."""
    lp = win.layer_panel
    lp.set_layer_tab(tab)
    lp.refresh()
    pump(120)
    content = lp.scroll_content
    rows = [w for w in (lp.scroll_layout.itemAt(i).widget() for i in range(lp.scroll_layout.count()))
            if w is not None and w.isVisible()]
    pad = 6
    top = min(w.geometry().top() for w in rows) if rows else 0
    bottom = max(w.geometry().bottom() for w in rows) + 1 if rows else content.height()
    image = QImage(content.width() * scale, (bottom - top + 2 * pad) * scale, QImage.Format_ARGB32)
    image.fill(content.palette().window().color())
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.scale(scale, scale)
    content.render(painter, QPoint(0, pad), QRegion(0, top, content.width(), bottom - top))
    painter.end()
    return image


def save(image, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.png')
    image.save(path, 'PNG')
    print('wrote', os.path.relpath(path, ROOT), image.width(), 'x', image.height())


def main(themes=('default', 'light', 'dark')):
    for number, theme in enumerate(themes):
        win = open_window(theme)
        load(win, knot())
        if number == 0:
            # The canvas paints the same ground in every theme: one picture each
            save(grab_canvas(win, KNOT_VIEW, zoom=2, ring=KNOT_CUT), 'level_same_canvas')
        save(grab_layer_list(win), f'ground_panel_{theme}')
        lift_1_4(win)
        if number == 0:
            save(grab_canvas(win, KNOT_VIEW, zoom=2), 'level_up_canvas')
        save(grab_layer_list(win), f'levels_panel_{theme}')
        win._confirm_close_with_dirty_tabs = lambda *a, **k: True
        win.close()
        win.deleteLater()
        pump(60)


if __name__ == '__main__':
    main(tuple(sys.argv[1:]) or ('default', 'light', 'dark'))
