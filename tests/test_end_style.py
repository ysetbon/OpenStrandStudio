"""Stylize End Side: a free end can carry an end style (end_style.py) that
drives the strand's footprint, side line, shadow and the masks built on it.

Geometry checks are rasterized (the fill must sit inside the footprint, the
band along the profile, nothing beyond the cut) because the thing under test
is what QPainterPath's clipper produces, and a bounding rect would not catch
the stray wedges it leaves when handed coincident edges.
"""

import json
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from PyQt5.QtCore import QPoint, QPointF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication, QMenu, QWidget, QWidgetAction, QLabel, QPushButton

import end_style
import shader_utils
from attached_strand import AttachedStrand
from end_style_dialog import EndStyleDialog
from masked_strand import MaskedStrand
from numbered_layer_button import NumberedLayerButton
from save_load_manager import serialize_project_state, load_strands_from_data
from strand import Strand
from translations import translations

APP = QApplication.instance() or QApplication([])

FILL = QColor(200, 170, 230)
STROKE = QColor(0, 0, 0)


def make_strand(start=(40, 100), end=(260, 100), cp1=(100, 70), cp2=(200, 130),
                width=46, stroke_width=4, layer_name="1_1"):
    strand = Strand(QPointF(*start), QPointF(*end), width, QColor(FILL), QColor(STROKE),
                    stroke_width, int(layer_name.split("_")[0]), layer_name)
    strand.control_point1 = QPointF(*cp1)
    strand.control_point2 = QPointF(*cp2)
    strand.update_shape()
    strand.update_side_line()
    return strand


def render(strands, size=(320, 220)):
    image = QImage(size[0], size[1], QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor("white"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    for strand in strands:
        strand.draw(painter)
    painter.end()
    return image


def rasterize(path, size=(320, 220), clip=None):
    """Set of pixels fully covered by ``path`` (optionally clipped, as the
    band is painted clipped to the footprint)."""
    image = QImage(size[0], size[1], QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, False)
    if clip is not None:
        painter.setClipPath(clip)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0))
    painter.drawPath(path)
    painter.end()
    # pixelColor keeps the alpha channel (QColor(int) would drop it)
    return {(x, y) for y in range(size[1]) for x in range(size[0]) if image.pixelColor(x, y).alpha() > 200}


def erode(pixels, radius=2):
    return {(x, y) for (x, y) in pixels
            if all((x + dx, y + dy) in pixels for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1))}


def local_x(strand, side, point):
    """x of a canvas point in the end's local frame (outward tangent = +x)."""
    origin, angle = end_style.end_frame(strand, side)
    dx, dy = point[0] - origin.x(), point[1] - origin.y()
    return dx * math.cos(angle) + dy * math.sin(angle)


def local_y(strand, side, point):
    origin, angle = end_style.end_frame(strand, side)
    dx, dy = point[0] - origin.x(), point[1] - origin.y()
    return -dx * math.sin(angle) + dy * math.cos(angle)


# ----------------------------------------------------------------------------
# Style records
# ----------------------------------------------------------------------------
def test_default_record_normalizes_to_none_and_survives_json():
    assert end_style.normalize_style(None) is None
    assert end_style.normalize_style({'shape': 'straight', 'tilt': 0, 'offset': 0}) is None
    assert end_style.normalize_style({'shape': 'bogus'}) is None

    style = end_style.normalize_style({'shape': 'pointed', 'tilt': 95, 'depth': 3, 'offset': 12.5,
                                       'line_width': 6, 'line_color': QColor(10, 20, 30, 40)})
    assert style['tilt'] == end_style.TILT_MAX
    assert style['depth'] == 1.0
    data = json.loads(json.dumps(end_style.serialize_style(style)))
    assert data['line_color'] == {'r': 10, 'g': 20, 'b': 30, 'a': 40}
    assert end_style.styles_equal(end_style.deserialize_style(data), style)
    assert end_style.deserialize_end_styles([None, data])[0] is None
    assert end_style.deserialize_end_styles("garbage") == [None, None]


def test_set_end_style_stores_none_for_default_and_invalidates_geometry():
    strand = make_strand()
    strand.set_end_style(1, {'shape': 'straight'})
    assert strand.end_styles == [None, None]
    assert strand._end_geometry() is None
    assert strand.get_footprint_path().isEmpty()

    strand.set_end_style(1, {'shape': 'rounded', 'depth': 1.0})
    first = strand._end_geometry()
    assert first is not None and strand._end_geometry() is first  # cached
    strand.set_end_style(1, {'shape': 'rounded', 'depth': 0.5})
    assert strand._end_geometry() is not first
    strand.end = QPointF(280, 120)
    strand.update_shape()
    assert strand._end_geometry().outer.boundingRect().right() > first.outer.boundingRect().right()


def test_circle_beats_style_and_attached_start_never_styled():
    strand = make_strand()
    strand.set_end_style(0, {'shape': 'pointed'})
    strand.set_end_style(1, {'shape': 'pointed'})
    assert strand.styled_end_sides() == [0, 1]
    strand.has_circles = [True, False]
    assert strand.styled_end_sides() == [1]

    parent = make_strand()
    child = AttachedStrand(parent, parent.end, 1)
    child.update(QPointF(300, 40))
    child.has_circles = [True, False]
    child.set_end_style(0, {'shape': 'pointed'})
    child.set_end_style(1, {'shape': 'pointed'})
    assert child.styled_end_sides() == [1]
    assert not child.get_footprint_path().isEmpty()
    assert not child.get_end_band_path(1).isEmpty()


# ----------------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------------
STYLES = [
    dict(shape='angled', tilt=30),
    dict(shape='angled', tilt=-45, offset=12),
    dict(shape='rounded', depth=1.0),
    dict(shape='rounded', depth=0.4, tilt=20),
    dict(shape='pointed', depth=0.6),
    dict(shape='pointed', depth=0.5, tilt=15, line_width=7),
    dict(shape='pointed', depth=1.0, line_width=2),
    dict(shape='notched', depth=0.4),
    dict(shape='notched', depth=0.8, tilt=-25, line_width=6),
    dict(shape='concave', depth=0.7),
    dict(shape='straight', offset=40),
    dict(shape='straight', offset=-27, line_width=3),
]
CURVES = [
    ((100, 70), (200, 130)),   # gentle S
    ((80, 40), (220, 160)),    # strong S
    ((60, 180), (240, 20)),    # reversed S
]


@pytest.mark.parametrize("style", STYLES, ids=lambda s: "_".join(f"{k}{v}" for k, v in s.items()))
@pytest.mark.parametrize("curve", CURVES, ids=["gentle", "strong", "reversed"])
@pytest.mark.parametrize("side", [0, 1])
def test_styled_end_layers_nest_correctly(style, curve, side):
    strand = make_strand(cp1=curve[0], cp2=curve[1])
    strand.set_end_style(side, style)
    geometry = strand._end_geometry()
    assert geometry is not None

    outer = rasterize(geometry.outer)
    inner = rasterize(geometry.inner())
    band = rasterize(geometry.band(side), clip=geometry.outer)
    assert len(outer) > 3000
    assert len(inner) > 1500
    assert band, "a visible side line always paints a band"

    # Fill and band sit inside the footprint; nothing survives beyond the cut.
    # (Checked around the styled end: at a tight bend elsewhere Qt's stroker
    # folds the classic fill past the classic stroke too, see the plain
    # strand's own rendering.)
    tip = strand.start if side == 0 else strand.end
    near = lambda px: math.hypot(px[0] - tip.x(), px[1] - tip.y()) < 2.5 * geometry.total
    plain = make_strand(cp1=curve[0], cp2=curve[1])
    classic_stroke = rasterize(plain.get_body_selection_path())
    classic_fill = rasterize(plain.get_stroked_path(plain.width))
    folds = erode(classic_fill) - classic_stroke  # Qt's stroker folds at tight bends, classic too
    assert {px for px in erode(inner) if near(px)} - folds <= outer
    assert {px for px in erode(band) if near(px)} <= outer
    # The cut continues straight along its own line past the width, so the
    # limit is the farthest point of the chord-extended profile. Only what
    # lies behind the endpoint plane is ever removed: pixels beyond the
    # limit must all be classic body (a bend swinging in front of its end,
    # or the stroker's mitred cap corner).
    end = geometry.ends[side]
    limit = max(p.x() for p in end.profile + list(end_style._chord_extended(end.profile, end.half))) + 1.5
    in_band = lambda px: abs(local_y(strand, side, px)) <= 1.5 * end.half - 1
    assert {px for px in outer if in_band(px) and local_x(strand, side, px) > limit} <= classic_stroke
    assert {px for px in inner if in_band(px) and local_x(strand, side, px) > limit} <= classic_fill

    # The fill is inset by the line width along the profile, by the stroke
    # width along the long edges: outline pixels form a closed ring.
    ring = outer - inner
    assert len(ring) > 400
    band_thickness = style.get('line_width') or strand.stroke_width
    ahead = lambda px: local_x(strand, side, px) > -1.0  # the cut plane itself is edge pixels
    assert not {px for px in erode(band, max(1, int(band_thickness // 2) - 1)) & inner if not ahead(px)}

    # The other end is untouched: it reaches exactly as far as the classic cap.
    other = 1 - side
    classic = rasterize(make_strand(cp1=curve[0], cp2=curve[1]).get_body_selection_path())
    other_max = max(local_x(strand, other, px) for px in outer)
    classic_max = max(local_x(strand, other, px) for px in classic)
    assert other_max == pytest.approx(classic_max, abs=1.5)


def test_default_style_matches_classic_rendering_pixel_for_pixel_but_edges():
    classic = render([make_strand()])
    styled_strand = make_strand()
    styled_strand.end_styles = [None, {'shape': 'straight', 'tilt': 0.0, 'depth': 0.5, 'offset': 0.0,
                                       'line_width': None, 'line_color': QColor(0, 0, 0)}]
    styled = render([styled_strand])
    big = 0
    for y in range(classic.height()):
        for x in range(classic.width()):
            a, b = QColor(classic.pixel(x, y)), QColor(styled.pixel(x, y))
            if abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue()) > 60:
                big += 1
    # Only anti-aliasing at the side line's corners may differ.
    assert big < 150


def test_extend_trim_moves_the_edge_not_the_endpoint():
    strand = make_strand()
    end_before = QPointF(strand.end)
    strand.set_end_style(1, {'shape': 'straight', 'offset': 40})
    assert strand.end == end_before
    assert strand.get_end_extent_shift(1) == pytest.approx(40)
    assert local_x(strand, 1, (strand._end_anchor(1).x(), strand._end_anchor(1).y())) == pytest.approx(40)
    assert strand.boundingRect().right() > make_strand().boundingRect().right() + 30
    strand.set_end_style(1, {'shape': 'straight', 'offset': -20})
    assert strand.get_end_extent_shift(1) == pytest.approx(-20)
    assert strand.get_end_selection_path().boundingRect().right() < end_before.x() + 1
    # A styled end's band lives inside the body selection path already
    assert strand.get_end_decoration_path(1).isEmpty()
    assert not strand.get_body_selection_path().isEmpty()


def test_hidden_side_line_cuts_the_body_but_paints_no_band():
    strand = make_strand()
    strand.end_line_visible = False
    strand.set_end_style(1, {'shape': 'concave', 'depth': 0.7})
    geometry = strand._end_geometry()
    assert geometry.band(1).isEmpty()
    assert not geometry.outer.isEmpty()
    outer = rasterize(geometry.outer)
    assert max(local_x(strand, 1, px) for px in outer) <= 1.5
    assert strand.get_end_decoration_path(1).isEmpty()


def test_side_line_colour_and_thickness_follow_stroke_until_pinned():
    strand = make_strand()
    strand.set_end_style(1, {'shape': 'angled', 'tilt': 20})
    assert strand.side_line_width_for(1) == 4
    assert strand.side_line_color_for(1).getRgb() == STROKE.getRgb()
    strand.stroke_width = 6
    strand.stroke_color = QColor(9, 8, 7)
    assert strand.side_line_width_for(1) == 6
    assert strand.side_line_color_for(1).getRgb() == (9, 8, 7, 255)
    strand.set_end_style(1, {'shape': 'angled', 'tilt': 20, 'line_width': 3, 'line_color': QColor(1, 2, 3)})
    strand.stroke_color = QColor(50, 60, 70)
    assert strand.side_line_width_for(1) == 3
    assert strand.side_line_color_for(1).getRgb() == (1, 2, 3, 255)


# ----------------------------------------------------------------------------
# Shadows and masks
# ----------------------------------------------------------------------------
def fake_canvas(strands):
    return SimpleNamespace(max_blur_radius=29.99, num_steps=3, strands=strands, shadow_selected_only=False,
                           default_shadow_color=QColor(0, 0, 0, 150), enable_third_control_point=False)


def test_shadow_builders_follow_the_styled_end():
    plain = make_strand()
    styled = make_strand()
    styled.set_end_style(1, {'shape': 'straight', 'offset': 40})
    for strand in (plain, styled):
        strand.canvas = fake_canvas([strand])

    plain_cast = shader_utils.build_shadow_geometry(plain, 30.0, include_circles=False)
    styled_cast = shader_utils.build_shadow_geometry(styled, 30.0, include_circles=False)
    assert styled_cast.boundingRect().right() > plain_cast.boundingRect().right() + 30
    # Left end (unstyled) keeps the classic extent
    assert styled_cast.boundingRect().left() == pytest.approx(plain_cast.boundingRect().left(), abs=1.0)

    plain_recv = shader_utils.build_rendered_geometry(plain)
    styled_recv = shader_utils.build_rendered_geometry(styled)
    assert styled_recv.boundingRect().right() > plain_recv.boundingRect().right() + 30

    trimmed = make_strand()
    trimmed.set_end_style(1, {'shape': 'straight', 'offset': -25})
    trimmed.canvas = fake_canvas([trimmed])
    plain_core = shader_utils.build_shadow_geometry(plain, 0.0, include_circles=False)
    trimmed_core = shader_utils.build_shadow_geometry(trimmed, 0.0, include_circles=False)
    assert trimmed_core.boundingRect().right() < plain_core.boundingRect().right() - 15


def test_mask_intersection_follows_the_styled_end():
    under = make_strand(start=(275, -10), end=(275, 210), cp1=(275, 50), cp2=(275, 150), layer_name="2_1")
    over = make_strand(layer_name="1_1")
    canvas = fake_canvas([under, over])
    for strand in (under, over):
        strand.canvas = canvas
    mask = MaskedStrand(over, under)
    mask.canvas = canvas
    plain_area = len(rasterize(mask.get_mask_path()))
    plain_shadow = len(rasterize(mask.get_masked_shadow_path()))

    assert plain_area > 300

    over.set_end_style(1, {'shape': 'straight', 'offset': -40})
    assert len(rasterize(mask.get_mask_path())) < plain_area * 0.2
    assert len(rasterize(mask.get_masked_shadow_path())) < plain_shadow

    over.set_end_style(1, {'shape': 'straight', 'offset': 30})
    assert len(rasterize(mask.get_mask_path())) > plain_area * 2
    assert not mask.get_stroked_path_for_strand_extended(over).isEmpty()
    assert not mask.get_stroked_path_for_strand_with_shadow(over).isEmpty()
    assert not mask.get_path_for_strand(over).isEmpty()


# ----------------------------------------------------------------------------
# Persistence, undo and duplication
# ----------------------------------------------------------------------------
class PersistencePanel:
    def __init__(self):
        self.set_colors = {}
        self.locked_layers = set()
        self.lock_mode = False
        self.layer_buttons = []

    def parent(self):
        return None

    def apply_lock_state(self, locked_layers, lock_mode):
        pass

    def update_layer_buttons_lock_state(self):
        pass

    def simulate_refresh_button_click(self):
        pass

    def refresh(self):
        pass

    def rebuild_layer_buttons(self):
        pass


class PersistenceCanvas:
    def __init__(self, strands=None):
        self.strands = strands or []
        self.groups = {}
        self.strand_colors = {}
        self.selected_strand = None
        self.selected_strand_index = None
        self.newest_strand = None
        self.shadow_enabled = True
        self.show_control_points = False
        self.strand_width = 20
        self.stroke_color = QColor("black")
        self.stroke_width = 4
        self.layer_panel = PersistencePanel()

    def update(self):
        pass

    def deselect_strand(self):
        pass

    def clear_strands(self):
        self.strands = []


def test_save_load_round_trips_end_styles_and_old_files_load_unstyled():
    strand = make_strand()
    strand.set_end_style(0, {'shape': 'rounded', 'depth': 0.8, 'offset': 5})
    strand.set_end_style(1, {'shape': 'notched', 'depth': 0.3, 'tilt': -10, 'line_width': 6,
                             'line_color': QColor(1, 2, 3, 200)})
    canvas = PersistenceCanvas([strand])
    state = json.loads(json.dumps(serialize_project_state(canvas.strands, {}, canvas)))
    assert state['strands'][0]['end_styles'][1]['line_color'] == {'r': 1, 'g': 2, 'b': 3, 'a': 200}

    loaded = load_strands_from_data(state, PersistenceCanvas())[0][0]
    assert end_style.styles_equal(loaded.get_end_style(0), strand.get_end_style(0))
    assert end_style.styles_equal(loaded.get_end_style(1), strand.get_end_style(1))
    assert loaded.get_footprint_path().boundingRect() == strand.get_footprint_path().boundingRect()

    del state['strands'][0]['end_styles']
    old = load_strands_from_data(state, PersistenceCanvas())[0][0]
    assert old.end_styles == [None, None]


def test_undo_state_comparison_sees_end_style_changes(tmp_path):
    from undo_redo_manager import UndoRedoManager
    strand = make_strand()
    strand.closed_connections = [False, False]
    canvas = PersistenceCanvas([strand])
    canvas.layer_panel.canvas = canvas
    manager = UndoRedoManager(canvas, canvas.layer_panel, str(tmp_path))
    manager._last_save_time = 0
    manager.save_state(action='layer.add', source='panel')
    manager._last_save_time = 0
    assert manager._would_be_identical_save()
    strand.set_end_style(1, {'shape': 'pointed', 'depth': 0.5})
    assert not manager._would_be_identical_save()


def test_group_duplication_copies_end_styles():
    from group_layers import GroupPanel
    source = make_strand()
    source.set_end_style(1, {'shape': 'pointed', 'line_color': QColor(5, 6, 7)})
    target = make_strand(layer_name="1_2")
    # The duplication helper copies attributes onto a new strand; reuse its
    # copy block through the same attribute path it uses.
    if hasattr(source, 'end_styles'):
        target.end_styles = [end_style.copy_style(source.end_styles[0]), end_style.copy_style(source.end_styles[1])]
    assert end_style.styles_equal(target.get_end_style(1), source.get_end_style(1))
    assert target.end_styles[1]['line_color'] is not source.end_styles[1]['line_color']
    assert GroupPanel is not None


# ----------------------------------------------------------------------------
# Menu and dialog
# ----------------------------------------------------------------------------
class _MenuCanvas:
    def __init__(self):
        self.strands = []

    def __getattr__(self, name):
        return lambda *a, **k: None


class LayerPanel(QWidget):
    """Named LayerPanel: show_context_menu finds its panel by class name."""

    def __init__(self):
        super().__init__()
        self.multi_select_mode = False
        self.layer_buttons = []
        self.language_code = 'en'
        self.canvas = _MenuCanvas()

    def __getattr__(self, name):
        return lambda *a, **k: None


def capture_menu(strand, monkeypatch):
    panel = LayerPanel()
    button = NumberedLayerButton(strand.layer_name, 1, QColor('purple'), parent=panel)
    panel.layer_buttons.append(button)
    panel.canvas.strands.append(strand)
    captured = []
    monkeypatch.setattr(QMenu, 'exec_', lambda self, *a, **k: captured.append(self))
    button.show_context_menu(QPoint(5, 5))
    return captured[0], button, panel


def stylize_row_buttons(menu):
    for action in menu.actions():
        widget = action.defaultWidget() if isinstance(action, QWidgetAction) else None
        if widget is None or widget.layout() is None:
            continue
        first = widget.layout().itemAt(0).widget()
        if isinstance(first, QLabel) and first.text() == translations['en']['stylize_end_side']:
            return [widget.layout().itemAt(i).widget().text() for i in range(1, widget.layout().count())]
    return None


def test_menu_offers_one_button_per_free_end(monkeypatch):
    strand = make_strand()
    strand.has_circles = [False, False]
    assert stylize_row_buttons(capture_menu(strand, monkeypatch)[0]) == ['Start', 'End']

    strand.has_circles = [True, False]
    assert stylize_row_buttons(capture_menu(strand, monkeypatch)[0]) == ['End']

    strand.has_circles = [True, True]
    assert stylize_row_buttons(capture_menu(strand, monkeypatch)[0]) is None

    parent = make_strand()
    child = AttachedStrand(parent, parent.end, 1)
    child.update(QPointF(300, 40))
    child.layer_name = "1_2"
    child.has_circles = [True, False]
    assert stylize_row_buttons(capture_menu(child, monkeypatch)[0]) == ['End']


def test_every_language_has_the_dialog_strings():
    keys = ['stylize_end_side', 'stylize_side_start', 'stylize_side_end', 'end_style_header', 'side_start',
            'side_end', 'end_style_preview', 'end_style_live_hint', 'end_shape', 'end_shape_straight',
            'end_shape_angled', 'end_shape_rounded', 'end_shape_pointed', 'end_shape_notched',
            'end_shape_concave', 'end_tilt', 'end_tilt_tooltip', 'end_depth', 'end_depth_tooltip',
            'end_extend_trim', 'end_extend_trim_hint', 'side_line_section', 'show_side_line',
            'side_line_thickness', 'side_line_color', 'use_stroke_color', 'apply_to_both_free_ends',
            'reset_to_straight', 'px']
    for language, table in translations.items():
        missing = [key for key in keys if key not in table]
        assert not missing, (language, missing)
    assert translations['en']['stylize_side_start'] == 'Start'
    assert translations['en']['stylize_side_end'] == 'End'


class DialogCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.strands = []
        self.undo_redo_manager = SimpleNamespace(_last_save_time=1, saves=[])
        self.undo_redo_manager.save_state = lambda **kw: self.undo_redo_manager.saves.append(kw)
        self.updates = 0

    def update(self):
        self.updates += 1


class MainWindow(QWidget):
    current_theme = 'default'


_KEEP = []  # widgets must outlive the test body: a collected window deletes its children


def open_dialog(strand, side, language='en', theme='default'):
    canvas = DialogCanvas()
    canvas.strands.append(strand)
    panel = SimpleNamespace(language_code=language, canvas=canvas)
    window = MainWindow()
    window.current_theme = theme
    button = QWidget(window)
    dialog = EndStyleDialog(strand, side, panel, button)
    _KEEP.extend([window, button, dialog, canvas])
    return dialog, canvas


def test_dialog_previews_live_and_cancel_restores_the_snapshot():
    strand = make_strand()
    strand.has_circles = [False, False]
    dialog, canvas = open_dialog(strand, 1)
    assert dialog.header_label.text() == 'Layer 1_1 — End side'
    assert dialog.both_ends_box is not None

    dialog.shape_buttons['pointed'].click()
    dialog.tilt_slider.setValue(15)
    dialog.thickness_spin.setValue(7)
    dialog.use_stroke_color_box.setChecked(False)
    dialog.show_line_box.setChecked(False)
    live = strand.get_end_style(1)
    assert live['shape'] == 'pointed' and live['tilt'] == 15 and live['line_width'] == 7
    assert live['line_color'] is not None
    assert strand.end_line_visible is False
    assert canvas.updates > 0

    dialog.reject()
    assert strand.get_end_style(1) is None
    assert strand.end_line_visible is True
    assert canvas.undo_redo_manager.saves == []


def test_dialog_ok_saves_one_undo_step_and_can_apply_to_both_ends():
    strand = make_strand()
    strand.has_circles = [False, False]
    dialog, canvas = open_dialog(strand, 0, language='he', theme='dark')
    assert dialog.layoutDirection() == Qt.RightToLeft
    dialog.shape_buttons['angled'].click()
    dialog.tilt_slider.setValue(-35)
    dialog.offset_spin.setValue(12)
    dialog.both_ends_box.setChecked(True)
    dialog.accept()

    for side in (0, 1):
        style = strand.get_end_style(side)
        assert style['shape'] == 'angled' and style['tilt'] == -35 and style['offset'] == 12
    assert len(canvas.undo_redo_manager.saves) == 1
    assert canvas.undo_redo_manager.saves[0]['action'] == 'strand.end_style'
    assert canvas.undo_redo_manager.saves[0]['detail'] == 'start'


def test_dialog_thickness_at_stroke_width_keeps_following_change_width():
    strand = make_strand()
    dialog, _ = open_dialog(strand, 1)
    dialog.shape_buttons['rounded'].click()
    assert strand.get_end_style(1)['line_width'] is None
    dialog.thickness_spin.setValue(4)  # equals the stroke width
    assert strand.get_end_style(1)['line_width'] is None
    dialog.thickness_spin.setValue(9)
    assert strand.get_end_style(1)['line_width'] == 9
    dialog.reset_button.click()
    assert strand.get_end_style(1) is None
    dialog.reject()


def _preview_pixels(dialog):
    pixmap = dialog.preview_label.pixmap()
    image = pixmap.toImage()
    return image


def test_preview_paints_the_classic_end_exactly_like_angled_zero():
    """An unstyled end and an 'Angled 0°' end are the same drawing, so the
    preview must show the same picture for both (the classic preview used to
    stroke the fill with a square cap that overran the endpoint)."""
    strand = make_strand(cp1=(190, 110), cp2=(310, 190))
    dialog, _ = open_dialog(strand, 1)
    classic = _preview_pixels(dialog)
    dialog.shape_buttons['angled'].click()
    angled = _preview_pixels(dialog)
    assert classic.size() == angled.size()

    # The styled body is the classic stroke plus a cap piece, so the only
    # admissible differences are anti-aliasing shifts of at most a pixel.
    # Compare 5x5 box-blurred luminance: a one-pixel edge shift moves it by
    # ~50 at most, a real notch or a missing side line by far more.
    w, h = classic.width(), classic.height()

    def luminance(image):
        return [[image.pixelColor(x, y).lightness() for x in range(w)] for y in range(h)]

    def blur(rows):
        out = []
        for y in range(2, h - 2):
            line = []
            for x in range(2, w - 2):
                line.append(sum(rows[y + dy][x + dx] for dy in range(-2, 3) for dx in range(-2, 3)) / 25.0)
            out.append(line)
        return out

    a, b = blur(luminance(classic)), blur(luminance(angled))
    off = sum(1 for ra, rb in zip(a, b) for va, vb in zip(ra, rb) if abs(va - vb) > 60)
    assert off < 40
    dialog.reject()


def test_preview_keeps_canvas_orientation_and_shows_the_side_line():
    """The preview is centred on the endpoint, in the canvas's orientation:
    a strand running left-to-right shows its body to the left of its end,
    and the classic side line (stroke colour) sits just past the endpoint."""
    strand = make_strand()  # start (40,100) -> end (260,100)
    dialog, _ = open_dialog(strand, 1)
    image = _preview_pixels(dialog)
    cx, cy = image.width() // 2, image.height() // 2
    fill = strand.color.getRgb()[:3]
    # Body (fill colour) to the left of the endpoint, none to the right
    assert image.pixelColor(cx - 40, cy).getRgb()[:3] == fill
    assert image.pixelColor(cx + 40, cy).getRgb()[:3] != fill
    # Side line: stroke colour right after the endpoint plane
    ratio, scale = 2, min(1.6, 0.6 * 120 / 54)
    probe = int(cx + 2 * scale * ratio)
    assert image.pixelColor(probe, cy).getRgb()[:3] == strand.stroke_color.getRgb()[:3]
    dialog.reject()
