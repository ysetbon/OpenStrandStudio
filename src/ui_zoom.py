"""
Application-wide UI zoom for OpenStrand Studio.

One zoom level (like a browser's Ctrl + / Ctrl -) scales every widget size,
stylesheet dimension, font, layout gap, rich-text page and cursor in the app.
Per-area multipliers let a user nudge one kind of control (toolbar buttons,
right-click menus, ...) on top of the zoom.

How it reaches the ~1,600 hard-coded sizes without editing each one:

* ``install(app)`` wraps the Qt setters that carry a size (``setStyleSheet``,
  ``setFixedSize``, ``setMinimumWidth``, ``resize``, ``setSpacing``,
  ``QFont.setPointSize``, ``setCursor``, ``setHtml`` ...).  Each wrapper
  remembers the unscaled value on the widget and applies the scaled one.
* ``apply_all()`` re-runs those remembered calls for every live widget, so a
  zoom change takes effect immediately, no restart.
* The application font is scaled the same way, which covers every label and
  control that never sets an explicit size.

Drawing settings (strand width, stroke, grid, canvas zoom) are never touched.
Only selection handles and hit areas follow the zoom, and that is optional.

Values that are already computed from zoomed measurements (font metrics,
screen size) can opt out with ``widget.setProperty('zoomRaw', True)`` or by
calling the setter inside ``with raw():``.
"""

import re
import sys
import threading

from PyQt5.QtCore import QObject, pyqtSignal, QSize, Qt, QRect, QPoint
from PyQt5.QtGui import QFont, QCursor, QPixmap, QPainter, QPen, QColor, QPolygon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLayout, QBoxLayout, QGridLayout, QFormLayout,
    QStackedLayout, QLabel, QTextEdit, QTextBrowser, QAbstractButton,
)

# --------------------------------------------------------------------------- #
# Public constants
# --------------------------------------------------------------------------- #

# Same ladder Chrome and Firefox use for page zoom.
LADDER = [50, 67, 75, 80, 90, 100, 110, 125, 150, 175, 200, 250, 300]
MIN_ZOOM, MAX_ZOOM = 50, 300
MIN_AREA, MAX_AREA = 50, 200

# Areas a user can fine-tune.  key, settings-file key, default multiplier.
# Names and descriptions live in translations under 'zoom_area_<key>'.
AREAS = [
    'text',      # every caption, label, menu entry, layer name, tab title
    'toolbar',   # the mode buttons, State, Tabs, the settings gear
    'icons',     # the round side buttons: home, undo, redo, zoom, pan ...
    'layers',    # the coloured layer buttons and their strip, badge, chips
    'groups',    # Create Group, the group column, rail, tiles, group dialogs
    'actions',   # Draw Names, Lock Layers, New Strand ... under the layers
    'menus',     # right-click menus, submenus, colour dialog, arrow panel
    'dialogs',   # the settings dialog and every other dialog
    'tabs',      # the floating tab bar
    'canvas',    # selection squares, control points, hit areas (not strands)
    'chrome',    # tooltips, scrollbars, splitter, the small edge things
]
AREA_FILE_KEYS = {
    'text': 'ZoomText', 'toolbar': 'ZoomToolbar', 'icons': 'ZoomSideIconButtons',
    'layers': 'ZoomLayerButtons', 'groups': 'ZoomGroups', 'actions': 'ZoomPanelActionButtons',
    'menus': 'ZoomRightClickMenus', 'dialogs': 'ZoomDialogs', 'tabs': 'ZoomTabs',
    'canvas': 'ZoomCanvasHandles', 'chrome': 'ZoomChrome',
}

QWIDGETSIZE_MAX = 16777215


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #

class _ZoomState(QObject):
    """Holds the zoom and emits ``changed`` after every change."""
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.zoom = 100
        self.auto = True
        self.multipliers = {a: 100 for a in AREAS}
        self.cursor_size = 32
        self.cursor_follows_zoom = True
        self.suggested = 100
        # Windows renders point sizes through the logical DPI even with Qt's
        # DPI scaling off, so 9 pt is already twice as tall at 200 %.  Point
        # sizes are therefore scaled by zoom / this ratio; pixel sizes by zoom.
        self.point_dpi_scale = 1.0
        # False while OPENSTRAND_UI_ZOOM overrides the zoom: nothing is saved.
        self.persist = True
        self.installed = False
        self.applying = False
        self.base_font = None
        self._raw_depth = 0


state = _ZoomState()
_local = threading.local()


class raw:
    """``with raw():`` - setters inside are stored and applied unscaled."""
    def __enter__(self):
        state._raw_depth += 1
        return self

    def __exit__(self, *exc):
        state._raw_depth -= 1
        return False


def _is_raw(obj=None):
    if state._raw_depth > 0:
        return True
    if obj is not None:
        try:
            if obj.property('zoomRaw'):
                return True
        except Exception:
            pass
    return False


# --------------------------------------------------------------------------- #
# Factors
# --------------------------------------------------------------------------- #

def zoom():
    return state.zoom


def factor(area='ui'):
    """Size multiplier for an area: zoom x that area's fine-tune."""
    f = state.zoom / 100.0
    if area and area != 'ui':
        f *= state.multipliers.get(area, 100) / 100.0
    return f


def font_factor(area='ui'):
    """Text multiplier for pixel-sized text: zoom x Text fine-tune x the area's."""
    return factor(area) * state.multipliers.get('text', 100) / 100.0


def point_factor(area='ui'):
    """Text multiplier for point-sized text (already DPI-scaled by the OS)."""
    return font_factor(area) / (state.point_dpi_scale or 1.0)


def canvas_factor():
    """Multiplier for selection handles and hit areas on the canvas."""
    return factor('canvas')


def S(value, area='ui'):
    """Scale a pixel value.  0 stays 0, a positive value never becomes 0."""
    if value is None:
        return value
    if isinstance(value, bool):
        return value
    f = factor(area)
    if isinstance(value, float):
        return value * f
    if value == 0 or value >= QWIDGETSIZE_MAX or value <= -QWIDGETSIZE_MAX:
        return value
    scaled = int(round(value * f))
    if scaled == 0:
        scaled = 1 if value > 0 else -1
    return min(scaled, QWIDGETSIZE_MAX)


def FS(value, area='ui'):
    """Scale a font size (points or pixels)."""
    if value is None or value == 0:
        return value
    f = font_factor(area)
    if isinstance(value, float):
        return value * f
    return max(1, int(round(value * f)))


# --------------------------------------------------------------------------- #
# Which area does a widget belong to?
# --------------------------------------------------------------------------- #

_CLASS_AREAS = {
    'NumberedLayerButton': 'layers',
    'GroupRail': 'groups', 'GroupPanel': 'groups', 'CollapsibleGroupWidget': 'groups',
    'TabChip': 'tabs', 'DraggableTabEdge': 'tabs', 'IconButton': 'tabs', 'DirtyDot': 'tabs', 'SnapOverlay': 'tabs',
    'QMenu': 'menus', 'QColorDialog': 'menus',
    'QToolTip': 'chrome', 'QScrollBar': 'chrome', 'SplitterHandle': 'chrome', 'CustomTooltip': 'chrome',
    'StrokeTextButton': 'icons',
}


def area_of(widget):
    """Walk up the parent chain until something names an area."""
    w = widget
    depth = 0
    while w is not None and depth < 64:
        try:
            explicit = w.property('zoomArea')
        except Exception:
            explicit = None
        if explicit:
            return str(explicit)
        name = type(w).__name__
        if name in _CLASS_AREAS:
            return _CLASS_AREAS[name]
        if isinstance(w, QWidget) and w.isWindow():
            # A top-level that is not the main window is a dialog or a popup.
            if name in ('MainWindow',):
                return 'ui'
            if w.windowFlags() & Qt.Popup:
                return 'menus'
            if name.endswith('Dialog') or name in ('QDialog', 'QMessageBox', 'QFileDialog'):
                return 'dialogs'
            return 'ui'
        try:
            w = w.parent()
        except Exception:
            w = None
        depth += 1
    return 'ui'


# --------------------------------------------------------------------------- #
# Stylesheet scaling
# --------------------------------------------------------------------------- #

_DECL_RE = re.compile(r'([\w-]+)\s*:\s*([^;{}]+)')
_NUM_RE = re.compile(r'(-?\d+(?:\.\d+)?)(px|pt)\b')


def scale_qss(qss, area='ui'):
    """Scale every px/pt number in a stylesheet.  font-size uses the text factor."""
    if not qss or ('px' not in qss and 'pt' not in qss):
        return qss
    f_dim = factor(area)
    f_font = font_factor(area)
    f_pt = point_factor(area)
    if f_dim == 1.0 and f_font == 1.0 and f_pt == 1.0:
        return qss

    def scale_value(match, f):
        num, unit = match.group(1), match.group(2)
        v = float(num)
        if v == 0:
            return match.group(0)
        if unit == 'pt' and f == f_font:
            f = f_pt
        s = v * f
        if abs(s) < 1:
            s = 1 if s > 0 else -1
        if unit == 'pt':
            return f'{s:.1f}'.rstrip('0').rstrip('.') + 'pt'
        return f'{int(round(s))}px'

    def repl(m):
        prop, value = m.group(1), m.group(2)
        if prop.lower() in ('font-size', 'font'):
            return prop + ': ' + _NUM_RE.sub(lambda mm: scale_value(mm, f_font), value)
        return prop + ': ' + _NUM_RE.sub(lambda mm: scale_value(mm, f_dim), value)

    return _DECL_RE.sub(repl, qss)


_HTML_FONT_RE = re.compile(r'(font-size\s*:\s*)(\d+(?:\.\d+)?)(px|pt)', re.I)


def scale_html(html, area='ui'):
    """Scale ``font-size:Npx`` inside rich text (the What's New / guide pages)."""
    if not html or 'font-size' not in html:
        return html
    f = font_factor(area)
    fp = point_factor(area)
    if f == 1.0 and fp == 1.0:
        return html

    def repl(m):
        if m.group(3) == 'px':
            return f'{m.group(1)}{int(round(float(m.group(2)) * f))}px'
        return f'{m.group(1)}{float(m.group(2)) * fp:.1f}pt'
    return _HTML_FONT_RE.sub(repl, html)


# --------------------------------------------------------------------------- #
# Cursors
# --------------------------------------------------------------------------- #

_cursor_cache = {}


def cursor_pixel_size():
    size = state.cursor_size
    if state.cursor_follows_zoom:
        size = int(round(size * state.zoom / 100.0))
    return max(8, size)


def _draw_arrow(p, s):
    k = s / 32.0
    pts = [(6, 3), (6, 25), (11.5, 20), (15.5, 29), (19.5, 27.3), (15.6, 18.6), (23, 18.6)]
    poly = QPolygon([QPoint(int(x * k), int(y * k)) for x, y in pts])
    p.setPen(QPen(QColor(0, 0, 0), max(1.0, 1.6 * k), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QColor(255, 255, 255))
    p.drawPolygon(poly)


def _draw_cross(p, s):
    c = s / 2.0
    arm = s * 0.42
    gap = max(2.0, s * 0.08)
    p.setPen(QPen(QColor(255, 255, 255), max(2.0, s * 0.11), Qt.SolidLine, Qt.FlatCap))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p.drawLine(QPoint(int(c + dx * gap), int(c + dy * gap)), QPoint(int(c + dx * arm), int(c + dy * arm)))
    p.setPen(QPen(QColor(0, 0, 0), max(1.0, s * 0.05), Qt.SolidLine, Qt.FlatCap))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p.drawLine(QPoint(int(c + dx * gap), int(c + dy * gap)), QPoint(int(c + dx * arm), int(c + dy * arm)))


def _draw_hand(p, s, closed):
    k = s / 32.0
    p.setPen(QPen(QColor(0, 0, 0), max(1.0, 1.4 * k), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QColor(255, 255, 255))
    # palm
    p.drawRoundedRect(int(8 * k), int(13 * k), int(16 * k), int(13 * k), 4 * k, 4 * k)
    if closed:
        for i in range(4):
            p.drawRoundedRect(int((9 + i * 4) * k), int(10 * k), int(3.5 * k), int(6 * k), 1.5 * k, 1.5 * k)
    else:
        for i, h in enumerate((7, 9, 8, 6)):
            p.drawRoundedRect(int((9 + i * 4) * k), int((13 - h) * k), int(3.5 * k), int((h + 3) * k), 1.5 * k, 1.5 * k)
    p.drawRoundedRect(int(4 * k), int(15 * k), int(5 * k), int(8 * k), 2 * k, 2 * k)


def _draw_size_all(p, s):
    c = s / 2.0
    arm = s * 0.44
    head = s * 0.16
    p.setPen(QPen(QColor(0, 0, 0), max(1.5, s * 0.08), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QColor(255, 255, 255))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p.drawLine(QPoint(int(c), int(c)), QPoint(int(c + dx * arm), int(c + dy * arm)))
        tip = QPoint(int(c + dx * arm), int(c + dy * arm))
        a = QPoint(int(c + dx * (arm - head) + dy * head * 0.7), int(c + dy * (arm - head) + dx * head * 0.7))
        b = QPoint(int(c + dx * (arm - head) - dy * head * 0.7), int(c + dy * (arm - head) - dx * head * 0.7))
        p.drawPolygon(QPolygon([tip, a, b]))


def _draw_split_h(p, s):
    c = s / 2.0
    p.setPen(QPen(QColor(0, 0, 0), max(1.5, s * 0.08), Qt.SolidLine, Qt.RoundCap))
    p.setBrush(QColor(255, 255, 255))
    p.drawLine(QPoint(int(c), int(s * 0.15)), QPoint(int(c), int(s * 0.85)))
    arm = s * 0.4
    head = s * 0.14
    for dx in (1, -1):
        p.drawLine(QPoint(int(c + dx * s * 0.08), int(c)), QPoint(int(c + dx * arm), int(c)))
        tip = QPoint(int(c + dx * arm), int(c))
        p.drawPolygon(QPolygon([tip, QPoint(int(c + dx * (arm - head)), int(c - head * 0.7)), QPoint(int(c + dx * (arm - head)), int(c + head * 0.7))]))


def _draw_pointing(p, s):
    k = s / 32.0
    p.setPen(QPen(QColor(0, 0, 0), max(1.0, 1.4 * k), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QColor(255, 255, 255))
    p.drawRoundedRect(int(9 * k), int(14 * k), int(15 * k), int(12 * k), 4 * k, 4 * k)
    p.drawRoundedRect(int(12 * k), int(3 * k), int(4 * k), int(14 * k), 2 * k, 2 * k)
    for i in range(3):
        p.drawRoundedRect(int((16 + i * 3) * k), int(12 * k), int(3 * k), int(6 * k), 1.5 * k, 1.5 * k)


_SHAPE_PAINTERS = {
    Qt.ArrowCursor: (_draw_arrow, (0.19, 0.09)),
    Qt.CrossCursor: (_draw_cross, (0.5, 0.5)),
    Qt.OpenHandCursor: (lambda p, s: _draw_hand(p, s, False), (0.5, 0.5)),
    Qt.ClosedHandCursor: (lambda p, s: _draw_hand(p, s, True), (0.5, 0.5)),
    Qt.SizeAllCursor: (_draw_size_all, (0.5, 0.5)),
    Qt.SplitHCursor: (_draw_split_h, (0.5, 0.5)),
    Qt.PointingHandCursor: (_draw_pointing, (0.42, 0.1)),
}


def cursor_for(shape):
    """A QCursor for a Qt.CursorShape at the configured size."""
    size = cursor_pixel_size()
    if size == 32 and shape not in _SHAPE_PAINTERS:
        return QCursor(shape)
    if shape not in _SHAPE_PAINTERS:
        return QCursor(shape)
    if size == 32 and state.cursor_size == 32 and not _cursor_cache.get('force'):
        # Default size: keep the native cursor so it matches the OS.
        return QCursor(shape)
    key = (int(shape), size)
    if key in _cursor_cache:
        return _cursor_cache[key]
    painter_fn, hot = _SHAPE_PAINTERS[shape]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    painter_fn(p, size)
    p.end()
    cur = QCursor(pm, int(size * hot[0]), int(size * hot[1]))
    _cursor_cache[key] = cur
    return cur


def cursor_preview_pixmap(shape=Qt.ArrowCursor):
    size = cursor_pixel_size()
    painter_fn, _ = _SHAPE_PAINTERS[shape]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    painter_fn(p, size)
    p.end()
    return pm


# --------------------------------------------------------------------------- #
# Remembered operations on widgets
# --------------------------------------------------------------------------- #

def _ops(obj):
    try:
        ops = obj.__dict__.get('_zoom_ops')
    except AttributeError:
        return None
    if ops is None:
        try:
            ops = obj._zoom_ops = []
        except Exception:
            return None
    return ops


def _remember(obj, name, args):
    ops = _ops(obj)
    if ops is None:
        return
    for i, (n, _a) in enumerate(ops):
        if n == name:
            ops[i] = (name, args)
            return
    ops.append((name, args))


def _forget(obj, *names):
    ops = _ops(obj)
    if not ops:
        return
    obj._zoom_ops = [(n, a) for (n, a) in ops if n not in names]


def _scale_args(args, area):
    out = []
    for a in args:
        if isinstance(a, QSize):
            out.append(QSize(S(a.width(), area), S(a.height(), area)))
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            out.append(S(a, area))
        else:
            out.append(a)
    return tuple(out)


_ORIG = {}


def _wrap_size_setter(cls, name, forget=()):
    orig = getattr(cls, name)
    _ORIG[(cls, name)] = orig

    def wrapper(self, *args):
        if not state.installed or _is_raw(self) or state.applying:
            return orig(self, *args)
        if forget:
            _forget(self, *forget)
        _remember(self, name, args)
        return orig(self, *_scale_args(args, area_of(self)))
    wrapper.__name__ = name
    setattr(cls, name, wrapper)


def _wrap_resize(cls):
    orig = cls.resize
    _ORIG[(cls, 'resize')] = orig

    def wrapper(self, *args):
        if not state.installed or _is_raw(self) or state.applying:
            return orig(self, *args)
        w = self
        try:
            top = w.isWindow()
        except Exception:
            top = False
        if not top:
            # Child widgets are positioned by layouts; scaling their explicit
            # resize is harmless but usually pointless, keep it consistent.
            _remember(self, 'resize', args)
            return orig(self, *_scale_args(args, area_of(self)))
        # Top-level windows: scale, then clamp to the available screen.
        _remember(self, 'resize', args)
        scaled = _scale_args(args, area_of(self))
        size = scaled[0] if len(scaled) == 1 and isinstance(scaled[0], QSize) else QSize(scaled[0], scaled[1])
        avail = _available_size(self)
        if avail is not None:
            size = QSize(min(size.width(), avail.width()), min(size.height(), avail.height()))
        return orig(self, size)
    setattr(cls, 'resize', wrapper)


def _available_size(widget):
    try:
        screen = widget.screen() if hasattr(widget, 'screen') else None
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry().size()
    except Exception:
        return None


def _wrap_min_size_top(cls):
    """setMinimumSize on a window is clamped so it always fits the screen."""
    orig = cls.setMinimumSize
    _ORIG[(cls, 'setMinimumSize')] = orig

    def wrapper(self, *args):
        if not state.installed or _is_raw(self) or state.applying:
            return orig(self, *args)
        _forget(self, 'setMinimumWidth', 'setMinimumHeight')
        _remember(self, 'setMinimumSize', args)
        scaled = _scale_args(args, area_of(self))
        try:
            top = self.isWindow()
        except Exception:
            top = False
        if top:
            size = scaled[0] if len(scaled) == 1 and isinstance(scaled[0], QSize) else QSize(scaled[0], scaled[1])
            avail = _available_size(self)
            if avail is not None:
                size = QSize(min(size.width(), avail.width()), min(size.height(), avail.height()))
            return orig(self, size)
        return orig(self, *scaled)
    setattr(cls, 'setMinimumSize', wrapper)


def _wrap_stylesheet(cls):
    orig = cls.setStyleSheet
    _ORIG[(cls, 'setStyleSheet')] = orig

    def wrapper(self, qss):
        if not state.installed or state.applying:
            return orig(self, qss)
        if _is_raw(self):
            try:
                self._zoom_qss_raw = True
            except Exception:
                pass
            return orig(self, qss)
        # Code that does ``w.setStyleSheet(w.styleSheet() + more)`` would
        # otherwise scale the old part twice; swap the scaled text back for
        # the unscaled base before remembering the new sheet.
        try:
            prev_scaled = self.__dict__.get('_zoom_scaled_qss')
            prev_base = self.__dict__.get('_zoom_base_qss')
            if prev_scaled and prev_base and prev_scaled != prev_base and prev_scaled in qss:
                qss = qss.replace(prev_scaled, prev_base)
        except Exception:
            pass
        area = 'ui' if isinstance(self, QApplication) else area_of(self)
        scaled = scale_qss(qss, area)
        try:
            self._zoom_base_qss = qss
            self._zoom_scaled_qss = scaled
        except Exception:
            return orig(self, qss)
        return orig(self, scaled)
    setattr(cls, 'setStyleSheet', wrapper)

    # Reading the stylesheet back gives the unscaled text, so appending to it
    # and setting it again scales exactly once.
    getter = getattr(cls, 'styleSheet', None)
    if getter is not None:
        _ORIG[(cls, 'styleSheet')] = getter

        def get_wrapper(self):
            try:
                base = self.__dict__.get('_zoom_base_qss')
            except AttributeError:
                base = None
            if base is not None and state.installed:
                return base
            return getter(self)
        setattr(cls, 'styleSheet', get_wrapper)


def _wrap_font():
    o_pt = QFont.setPointSize
    o_ptf = QFont.setPointSizeF
    o_px = QFont.setPixelSize
    _ORIG[(QFont, 'setPointSize')] = o_pt
    _ORIG[(QFont, 'setPointSizeF')] = o_ptf
    _ORIG[(QFont, 'setPixelSize')] = o_px

    def set_point(self, v):
        if not state.installed or state._raw_depth > 0:
            return o_pt(self, v)
        return o_ptf(self, max(1.0, v * point_factor()))

    def set_point_f(self, v):
        if not state.installed or state._raw_depth > 0:
            return o_ptf(self, v)
        return o_ptf(self, max(1.0, v * point_factor()))

    def set_pixel(self, v):
        if not state.installed or state._raw_depth > 0:
            return o_px(self, v)
        return o_px(self, max(1, int(round(v * font_factor()))))

    QFont.setPointSize = set_point
    QFont.setPointSizeF = set_point_f
    QFont.setPixelSize = set_pixel

    # QFont('Segoe UI', 16): the constructor takes the size directly.
    o_init = QFont.__init__

    def init2(self, *args, **kwargs):
        if state.installed and state._raw_depth == 0 and len(args) >= 2 and isinstance(args[0], str) \
                and isinstance(args[1], (int, float)) and not isinstance(args[1], bool) and args[1] > 0:
            size = float(args[1])
            o_init(self, *((args[0], -1) + tuple(args[2:])), **kwargs)
            o_ptf(self, max(1.0, size * point_factor()))
            return
        return o_init(self, *args, **kwargs)

    QFont.__init__ = init2



def _wrap_widget_font():
    orig = QWidget.setFont
    _ORIG[(QWidget, 'setFont')] = orig

    def wrapper(self, font):
        if not state.installed or state.applying:
            return orig(self, font)
        try:
            resolved = font.resolve()
        except Exception:
            resolved = 0
        # QFont::SizeResolved == 0x0004.  Only fonts with an explicit size are
        # remembered; the rest inherit the (already scaled) application font.
        if resolved & 0x0004:
            try:
                if font.pixelSize() > 0:
                    self._zoom_font_base = ('px', font.pixelSize() / font_factor(), font)
                else:
                    self._zoom_font_base = ('pt', font.pointSizeF() / point_factor(), font)
            except Exception:
                pass
        return orig(self, font)
    QWidget.setFont = wrapper


def _reapply_font(widget):
    base = widget.__dict__.get('_zoom_font_base')
    if not base:
        return
    unit, size, font = base
    area = area_of(widget)
    new = QFont(font)
    if unit == 'px':
        _ORIG[(QFont, 'setPixelSize')](new, max(1, int(round(size * font_factor(area)))))
    else:
        _ORIG[(QFont, 'setPointSizeF')](new, max(1.0, size * point_factor(area)))
    _ORIG[(QWidget, 'setFont')](widget, new)


def _wrap_cursor():
    orig = QWidget.setCursor
    _ORIG[(QWidget, 'setCursor')] = orig

    def wrapper(self, cur):
        if not state.installed or state.applying:
            return orig(self, cur)
        if isinstance(cur, QCursor):
            _forget(self, 'setCursor')
            return orig(self, cur)
        try:
            shape = Qt.CursorShape(int(cur))
        except Exception:
            return orig(self, cur)
        _remember(self, 'setCursor', (shape,))
        return orig(self, cursor_for(shape))
    QWidget.setCursor = wrapper


def _wrap_html():
    for cls, name in ((QTextEdit, 'setHtml'), (QTextBrowser, 'setHtml'), (QLabel, 'setText')):
        orig = getattr(cls, name)
        _ORIG[(cls, name)] = orig

        def make(orig, name):
            def wrapper(self, text):
                if not state.installed or state.applying or not isinstance(text, str) or 'font-size' not in text:
                    if name == 'setText':
                        try:
                            if '_zoom_base_html' in self.__dict__:
                                del self._zoom_base_html
                        except Exception:
                            pass
                    return orig(self, text)
                try:
                    self._zoom_base_html = (name, text)
                except Exception:
                    pass
                return orig(self, scale_html(text, area_of(self)))
            wrapper.__name__ = name
            return wrapper
        setattr(cls, name, make(orig, name))


# --------------------------------------------------------------------------- #
# Install and apply
# --------------------------------------------------------------------------- #

def install(app):
    """Wrap the Qt setters.  Call once, right after QApplication is created."""
    if state.installed:
        return
    state.base_font = QFont(app.font())

    for name in ('setFixedSize', 'setFixedWidth', 'setFixedHeight',
                 'setMinimumWidth', 'setMinimumHeight',
                 'setMaximumSize', 'setMaximumWidth', 'setMaximumHeight',
                 'setIconSize', 'setContentsMargins'):
        if hasattr(QWidget, name):
            _wrap_size_setter(QWidget, name)
    _wrap_min_size_top(QWidget)
    _wrap_resize(QWidget)
    _wrap_stylesheet(QWidget)
    _wrap_stylesheet(QApplication)
    for cls in (QLayout, QBoxLayout, QGridLayout, QFormLayout, QStackedLayout):
        for name in ('setSpacing', 'setContentsMargins', 'setHorizontalSpacing', 'setVerticalSpacing'):
            if name in cls.__dict__ or (cls is QLayout and hasattr(cls, name)):
                try:
                    _wrap_size_setter(cls, name)
                except AttributeError:
                    pass
    _wrap_font()
    _wrap_widget_font()
    _wrap_cursor()
    _wrap_html()

    state.installed = True
    _apply_app_font(app)
    app.installEventFilter(_ShowFilter(app))


class _ShowFilter(QObject):
    """Widgets shown after a zoom change get their area multipliers applied."""
    def eventFilter(self, obj, event):
        try:
            if event.type() == 17 and isinstance(obj, QWidget) and obj.isWindow():  # QEvent.Show
                if not obj.__dict__.get('_zoom_applied_at') == _stamp():
                    apply_to(obj)
        except Exception:
            pass
        return False


def _stamp():
    return (state.zoom, tuple(sorted(state.multipliers.items())), state.cursor_size, state.cursor_follows_zoom)


def _apply_app_font(app):
    if state.base_font is None:
        return
    f = QFont(state.base_font)
    if f.pixelSize() > 0:
        _ORIG[(QFont, 'setPixelSize')](f, max(1, int(round(f.pixelSize() * font_factor()))))
    else:
        _ORIG[(QFont, 'setPointSizeF')](f, max(1.0, f.pointSizeF() * point_factor()))
    app.setFont(f)


def _layouts_of(widget):
    try:
        lay = QWidget.layout(widget)   # some widgets shadow .layout with an attribute
    except Exception:
        lay = None
    if lay is None:
        return
    stack = [lay]
    while stack:
        l = stack.pop()
        yield l
        for i in range(l.count()):
            item = l.itemAt(i)
            sub = item.layout() if item is not None else None
            if sub is not None:
                stack.append(sub)


def _reapply_obj(obj, area):
    ops = obj.__dict__.get('_zoom_ops')
    if ops:
        for name, args in list(ops):
            key = None
            for cls in type(obj).__mro__:
                if (cls, name) in _ORIG:
                    key = (cls, name)
                    break
            if key is None:
                continue
            orig = _ORIG[key]
            try:
                if name == 'setCursor':
                    orig(obj, cursor_for(args[0]))
                elif name in ('resize', 'setMinimumSize') and isinstance(obj, QWidget) and obj.isWindow():
                    scaled = _scale_args(args, area)
                    size = scaled[0] if len(scaled) == 1 and isinstance(scaled[0], QSize) else QSize(scaled[0], scaled[1])
                    avail = _available_size(obj)
                    if avail is not None:
                        size = QSize(min(size.width(), avail.width()), min(size.height(), avail.height()))
                    orig(obj, size)
                else:
                    orig(obj, *_scale_args(args, area))
            except Exception:
                pass
    base_qss = obj.__dict__.get('_zoom_base_qss')
    if base_qss is not None and not obj.__dict__.get('_zoom_qss_raw'):
        try:
            scaled = scale_qss(base_qss, area)
            obj._zoom_scaled_qss = scaled
            _ORIG[(QApplication if isinstance(obj, QApplication) else QWidget, 'setStyleSheet')](obj, scaled)
        except Exception:
            pass
    html = obj.__dict__.get('_zoom_base_html')
    if html:
        name, text = html
        for cls in type(obj).__mro__:
            if (cls, name) in _ORIG:
                try:
                    _ORIG[(cls, name)](obj, scale_html(text, area))
                except Exception:
                    pass
                break
    if isinstance(obj, QWidget):
        _reapply_font(obj)


def apply_to(top):
    """Re-apply remembered sizes to one window and everything inside it."""
    state.applying = True
    try:
        widgets = [top] + top.findChildren(QWidget)
        for w in widgets:
            try:
                area = area_of(w)
                _reapply_obj(w, area)
                for lay in _layouts_of(w):
                    _reapply_obj(lay, area)
            except RuntimeError:
                continue
        try:
            top._zoom_applied_at = _stamp()
        except Exception:
            pass
    finally:
        state.applying = False


def apply_all():
    """Re-apply everything after a zoom change.  Emits ``changed`` at the end."""
    app = QApplication.instance()
    if app is None or not state.installed:
        return
    _cursor_cache.clear()
    state.applying = True
    try:
        _apply_app_font(app)
        base = app.__dict__.get('_zoom_base_qss') if hasattr(app, '__dict__') else None
        if base is not None:
            _ORIG[(QApplication, 'setStyleSheet')](app, scale_qss(base, 'ui'))
    finally:
        state.applying = False
    seen = set()
    for w in app.topLevelWidgets():
        try:
            if id(w) in seen:
                continue
            seen.add(id(w))
            apply_to(w)
        except RuntimeError:
            continue
    # Widgets without a window (not yet shown) still get their sizes.
    state.applying = True
    try:
        for w in app.allWidgets():
            try:
                if w.window() is w and id(w) not in seen:
                    seen.add(id(w))
                    state.applying = False
                    apply_to(w)
                    state.applying = True
            except RuntimeError:
                continue
    finally:
        state.applying = False
    for w in app.allWidgets():
        try:
            w.updateGeometry()
        except RuntimeError:
            pass
    state.changed.emit()
    schedule_save()


# --------------------------------------------------------------------------- #
# Changing the zoom
# --------------------------------------------------------------------------- #

def clamp_zoom(z):
    return max(MIN_ZOOM, min(MAX_ZOOM, int(round(z))))


def set_zoom(z, apply=True):
    z = clamp_zoom(z)
    if z == state.zoom:
        return False
    state.zoom = z
    if apply:
        apply_all()
    return True


def step(direction):
    """Move one step along the browser ladder. direction is +1 or -1."""
    z = state.zoom
    if direction > 0:
        nxt = [v for v in LADDER if v > z]
        target = nxt[0] if nxt else LADDER[-1]
    else:
        prv = [v for v in LADDER if v < z]
        target = prv[-1] if prv else LADDER[0]
    return set_zoom(target)


def set_multiplier(area, value, apply=True):
    value = max(MIN_AREA, min(MAX_AREA, int(round(value))))
    if state.multipliers.get(area) == value:
        return False
    state.multipliers[area] = value
    if apply:
        apply_all()
    return True


def set_cursor(size=None, follows=None, apply=True):
    changed = False
    if size is not None:
        size = max(16, min(96, int(size)))
        if size != state.cursor_size:
            state.cursor_size = size
            changed = True
    if follows is not None and bool(follows) != state.cursor_follows_zoom:
        state.cursor_follows_zoom = bool(follows)
        changed = True
    if changed and apply:
        apply_all()
    return changed


def reset_fine_tune(apply=True):
    for a in AREAS:
        state.multipliers[a] = 100
    if apply:
        apply_all()


# --------------------------------------------------------------------------- #
# Settings file
# --------------------------------------------------------------------------- #

def settings_lines():
    """Lines to write into user_settings.txt."""
    lines = [f"UIZoom: {state.zoom}", f"UIZoomAuto: {str(state.auto).lower()}"]
    for a in AREAS:
        lines.append(f"{AREA_FILE_KEYS[a]}: {state.multipliers[a]}")
    lines.append(f"CursorSize: {state.cursor_size}")
    lines.append(f"CursorFollowsZoom: {str(state.cursor_follows_zoom).lower()}")
    info = getattr(state, 'screen_info', None)
    if info:
        lines.append(f"DetectedScreen: {info['width']}x{info['height']}@{info['os_scale']}")
    return lines


_save_timer = None


def schedule_save(delay_ms=400):
    """Write the zoom keys to user_settings.txt shortly after the last change."""
    global _save_timer
    path = getattr(state, 'settings_path', None)
    if not path or not state.persist:
        return
    from PyQt5.QtCore import QTimer
    if _save_timer is None:
        _save_timer = QTimer()
        _save_timer.setSingleShot(True)
        _save_timer.timeout.connect(lambda: save_to_file(getattr(state, 'settings_path', None)))
    _save_timer.start(delay_ms)


def save_to_file(file_path):
    """Rewrite only the zoom keys in user_settings.txt, keeping every other line."""
    import os
    if not file_path:
        return
    lines = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as fh:
                lines = [ln.rstrip('\n') for ln in fh
                         if ln.split(':', 1)[0].strip() not in SETTINGS_KEYS]
        except Exception:
            lines = []
    lines.extend(settings_lines())
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:
        pass


SETTINGS_KEYS = ('UIZoom', 'UIZoomAuto', 'CursorSize', 'CursorFollowsZoom', 'DetectedScreen') + tuple(AREA_FILE_KEYS.values())


def read_settings(file_path):
    """Read the zoom keys from user_settings.txt into ``state``. Returns the
    keys that were present, so a caller can tell a first run from a saved one."""
    found = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                if ':' not in line:
                    continue
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                if key in SETTINGS_KEYS:
                    found[key] = value
    except Exception:
        return found
    try:
        if 'UIZoom' in found:
            state.zoom = clamp_zoom(float(found['UIZoom']))
        if 'UIZoomAuto' in found:
            state.auto = found['UIZoomAuto'].lower() == 'true'
        for a in AREAS:
            k = AREA_FILE_KEYS[a]
            if k in found:
                state.multipliers[a] = max(MIN_AREA, min(MAX_AREA, int(float(found[k]))))
        if 'CursorSize' in found:
            state.cursor_size = max(16, min(96, int(float(found['CursorSize']))))
        if 'CursorFollowsZoom' in found:
            state.cursor_follows_zoom = found['CursorFollowsZoom'].lower() == 'true'
    except Exception:
        pass
    return found
