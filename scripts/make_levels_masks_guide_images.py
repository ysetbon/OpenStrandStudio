"""Render the pictures of the Settings > Levels & Masks guide with the app itself.

Every picture is a real scene drawn by the real canvas and layer panel: the
script builds each design as a project (strands, an attached strand, a mask,
a level), loads it into an offscreen MainWindow, and grabs the canvas and the
layer list in each theme. So the guide shows exactly what the app draws.

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

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QTimer, Qt  # noqa: E402
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
# The designs
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


# A straight 1_1 across, and 2_1 + 2_2 (attached at its end) making a peak
# that crosses 1_1 twice. Mask 1_1_2_2 lifts 1_1 at the right-hand crossing.
ACROSS = strand("1_1", (90, 330), (590, 330))
UP = strand("2_1", (190, 520), (330, 150))
DOWN = strand("2_2", (330, 150), (470, 520), attached_to="2_1")


def hook(level=None):
    """2_3 continues 2_2 at its end and loops back up over the masked
    crossing (400, 330). It is joined to one of the mask's strands, so the
    mask's piece is drawn over it unless 2_3 is on a higher level."""
    return strand("2_3", (470, 520), (580, 190), attached_to="2_2", level=level,
                  controls=((340, 560), (240, 380)))


def scenes():
    weave = [ACROSS, UP, DOWN]
    lift = mask("1_1", "2_2", weave)
    # 2_2 now has 2_3 attached at its end: a circle shows there
    looped = [ACROSS, UP, dict(DOWN, has_circles=[True, True])]
    return {
        'stack': project([strand("1_1", (90, 330), (590, 330)),
                          strand("2_1", (120, 520), (330, 140)),
                          strand("3_1", (330, 140), (540, 520))]),
        'mask_before': project(weave),
        'mask_after': project(weave + [lift]),
        'level_same': project(looped + [hook(), lift]),
        'level_up': project([dict(s, level=0) for s in looped] + [hook(level=1), lift], level_count=1),
    }


# The part of the canvas each picture shows (canvas coordinates)
CANVAS_VIEW = QRect(60, 105, 560, 460)


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
    canvas.shadow_enabled = True
    win.layer_panel.set_layer_tab('strands')
    win.layer_panel.refresh()
    pump(120)


def grab_canvas(win, view=CANVAS_VIEW):
    canvas = win.canvas
    canvas.zoom_factor = 1.0
    canvas.pan_offset_x = canvas.width() / 2 - view.center().x()
    canvas.pan_offset_y = canvas.height() / 2 - view.center().y()
    canvas.update()
    pump(80)
    image = canvas.grab().toImage()
    top_left = canvas.canvas_to_screen(QPointF(view.left(), view.top()))
    image = image.copy(int(round(top_left.x())), int(round(top_left.y())), view.width(), view.height())
    # A thin grey frame, so the white canvas stands out on a white page too
    painter = QPainter(image)
    painter.setPen(QPen(QColor('#BDBDBD'), 2))
    painter.drawRect(QRectF(1, 1, image.width() - 2, image.height() - 2))
    painter.end()
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
    designs = scenes()
    for number, theme in enumerate(themes):
        win = open_window(theme)
        if number == 0:
            # The canvas paints the same ground in every theme: one picture each
            for name, data in designs.items():
                load(win, data)
                save(grab_canvas(win), f'{name}_canvas')
        load(win, designs['stack'])
        save(grab_layer_list(win), f'stack_panel_{theme}')
        load(win, designs['mask_after'])
        save(grab_layer_list(win), f'weave_panel_{theme}')
        save(grab_layer_list(win, 'masks'), f'mask_panel_{theme}')
        load(win, designs['level_up'])
        save(grab_layer_list(win), f'levels_panel_{theme}')
        win._confirm_close_with_dirty_tabs = lambda *a, **k: True
        win.close()
        win.deleteLater()
        pump(60)


if __name__ == '__main__':
    main(tuple(sys.argv[1:]) or ('default', 'light', 'dark'))
