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
import copy
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
# ----------------------------------------------------------------------
# A small design for the order of painting (one level, two strands, one mask)
# ----------------------------------------------------------------------
COLORS = {
    1: (200, 170, 230),  # the app's default purple
    2: (111, 195, 178),
    3: (242, 193, 78),
}

_BASE = {
    "width": 46, "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255}, "stroke_width": 4,
    "width_in_grid_units": None, "elliptical_end_caps": False, "is_first_strand": False,
    "is_start_side": True, "start_line_visible": True, "end_line_visible": True, "end_styles": [None, None],
    "is_hidden": False, "start_extension_visible": False, "end_extension_visible": False,
    "start_arrow_visible": False, "end_arrow_visible": False, "full_arrow_visible": False,
    "shadow_only": False, "hide_shadow": False, "closed_connections": [False, False], "arrow_color": None,
    "arrow_transparency": 100, "arrow_texture": "none", "arrow_shaft_style": "solid",
    "arrow_head_visible": True, "arrow_casts_shadow": False, "knot_connections": {},
    "circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
    "start_circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
    "end_circle_stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
    "control_point_center_locked": False,
    "bias_control": {"triangle_bias": 0.5, "circle_bias": 0.5, "triangle_position": None, "circle_position": None},
    "triangle_has_moved": False, "control_point2_shown": False, "control_point2_activated": False,
}


def _pt(p):
    return {"x": float(p[0]), "y": float(p[1])}


def _color(set_number):
    r, g, b = COLORS[set_number]
    return {"r": r, "g": g, "b": b, "a": 255}


def strand(name, start, end, attached_to=None, level=None, controls=None):
    """A strand from *start* to *end*, straight unless *controls* gives its
    two control points. With *attached_to* it is an attached strand starting
    at the end of that strand."""
    set_number = int(name.split('_')[0])
    c1, c2 = controls or (start, end)
    data = copy.deepcopy(_BASE)
    data.update({
        "type": "AttachedStrand" if attached_to else "Strand",
        "start": _pt(start), "end": _pt(end), "color": _color(set_number),
        "layer_name": name, "set_number": set_number,
        "has_circles": [True, False] if attached_to else [True, True],
        "control_points": [_pt(c1), _pt(c2)],
        "control_point_center": _pt(((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)),
    })
    if attached_to:
        data.update({"attached_to": attached_to, "attachment_side": 1, "angle": 0, "length": 0,
                     "is_start_side": False})
    if level is not None:
        data["level"] = level
    return data


def mask(first, second, scene):
    """The mask that puts *first* over *second* where they cross."""
    a = next(s for s in scene if s["layer_name"] == first)
    data = copy.deepcopy(_BASE)
    data.update({
        "type": "MaskedStrand", "start": a["start"], "end": a["end"], "color": a["color"],
        "layer_name": f"{first}_{second}",
        "set_number": int(first.split('_')[0] + second.split('_')[0]),
        "has_circles": [False, False], "control_points": [None, None],
        "control_point_center": a["control_point_center"], "deletion_rectangles": [],
    })
    return data


def project(strands, level_count=0):
    strands = [dict(s, index=i) for i, s in enumerate(strands)]
    data = {"strands": strands, "groups": {}, "selected_strand_name": None, "locked_layers": [],
            "lock_mode": False, "shadow_enabled": True, "show_control_points": False, "shadow_overrides": {}}
    data["strand_colors"] = {str(n): _color(n) for n in {s["set_number"] for s in strands
                                                      if s["type"] != "MaskedStrand"}}
    if level_count:
        data["level_count"] = level_count
    return data



def order_design():
    """One level (Ground): 1_1 and 2_1 cross, and mask 1_1_2_1 puts 1_1 over 2_1."""
    first = strand("1_1", (90, 330), (590, 330), level=0)
    second = strand("2_1", (200, 520), (440, 140), level=0)
    # One level exists so the panel shows the Ground row; the pictures leave
    # out the empty Level 1 row above it (grab_layer_list ground_only)
    return project([first, second, mask("1_1", "2_1", [first, second])], level_count=1)


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


def grab_layer_list(win, tab='strands', scale=2, ground_only=False):
    """The layer list of *tab* as the panel shows it, cropped to its rows and
    drawn at *scale* times its size (the canvas pictures are 2x as well).
    With *ground_only*, only the ground's block: its layers and Ground row."""
    lp = win.layer_panel
    lp.set_layer_tab(tab)
    lp.refresh()
    pump(120)
    content = lp.scroll_content
    rows = [w for w in (lp.scroll_layout.itemAt(i).widget() for i in range(lp.scroll_layout.count()))
            if w is not None and w.isVisible()
            and not (ground_only and w in getattr(lp, 'level_rows', []))]
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


def grab_widget(widget, scale=2):
    """A widget exactly as it is drawn, at *scale* times its size."""
    image = QImage(widget.width() * scale, widget.height() * scale, QImage.Format_ARGB32)
    image.fill(widget.palette().window().color())
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.scale(scale, scale)
    widget.render(painter)
    painter.end()
    return image


def layer_button(win, name, tab='strands'):
    lp = win.layer_panel
    lp.set_layer_tab(tab)
    lp.refresh()
    pump(120)
    return next(b for b in lp.layer_buttons if b.text() == name and not b.isHidden())


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
        # The order of painting: the Strands and Masks tabs, and each button for the array
        load(win, order_design())
        save(grab_layer_list(win, ground_only=True), f'order_strands_panel_{theme}')
        save(grab_layer_list(win, 'masks', ground_only=True), f'order_masks_panel_{theme}')
        for name in ('1_1', '2_1'):
            save(grab_widget(layer_button(win, name)), f'order_{name}_{theme}')
        save(grab_widget(layer_button(win, '1_1_2_1', 'masks')), f'order_mask_{theme}')
        win._confirm_close_with_dirty_tabs = lambda *a, **k: True
        win.close()
        win.deleteLater()
        pump(60)


if __name__ == '__main__':
    main(tuple(sys.argv[1:]) or ('default', 'light', 'dark'))
