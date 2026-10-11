"""The Level layer: one row of the layer panel that marks a storey in the stack.

A level row looks like a layer button, as wide as one and a third lower
(146 x 27 against 146 x 40), named "Level 1", "Level 2" and so on, with a
4 px line under it that runs the whole width of the list. It sits at the
bottom of the layers it carries. Layers below the lowest level row are on the
ground (level 0), which has no row unless the ground line is shown.

Inside the button, the 30 px at each edge are chevrons: the left one folds
the block the level carries (the layers right above the row), the right one
the block under it, down to the next level row. A folded block is hidden
entirely. A click on the name selects the level's block: the panel frames it
and Move, Attach and Rotate only find its strands (see
StrandDrawingCanvas.is_strand_in_level_scope).

Right-click opens the level menu, built like the layers' own menus;
dragging the row moves it like any layer (LayerPanel.dropEvent turns the new
position into levels).
"""

from PyQt5.QtCore import QEvent, QMimeData, QPointF, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QDrag, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (QApplication, QColorDialog, QMenu, QPushButton,
                             QSizePolicy, QToolTip, QVBoxLayout, QWidget,
                             QWidgetAction)

# Same width as NumberedLayerButton, a third less tall (40 -> 27).
LEVEL_BUTTON_SIZE = QSize(146, 27)
LEVEL_LINE_HEIGHT = 4
# The Default theme's level purple (each theme has its own, see THEME_LEVEL_COLORS)
LEVEL_COLOR = QColor("#7a63b8")
# Width of the fold chevron at each edge of the level button
CHEVRON_ZONE_WIDTH = 30
# The ground line: a 4 px line in a row tall enough to click
GROUND_ROW_HEIGHT = 10
# Selection frame around a level's block
FRAME_WIDTH = 2
FRAME_RAIL_WIDTH = 3  # "Medium": 4 px of air before the buttons (LayerPanel.LAYER_LIST_SIDE_MARGIN is 7)

# ----------------------------------------------------------------------
# Colours. A level's colour is stored as "preset:<key>" (a colour family
# whose lightness each theme picks, so it stays legible when the theme
# changes) or "#rrggbb" (a custom pick). No value means the default: the
# user's Default Level Color from the settings, or the theme's purple.
# ----------------------------------------------------------------------
PANEL_BACKGROUNDS = {'default': QColor('#ececec'), 'light': QColor('#ffffff'), 'dark': QColor('#2c2c2c')}
# Purple tuned per theme: today's purple on Default, deeper on white, a
# lighter lilac on the dark panel (today's purple is only ~2.9:1 there).
THEME_LEVEL_COLORS = {'default': '#7a63b8', 'light': '#5e43a3', 'dark': '#9b83d8'}
# key, hue, saturation, fixed lightness per theme (None: the shared lightness)
LEVEL_PRESETS = (
    ('purple', None, None, None),
    ('gray', 250, 7, {'default': 47, 'light': 38, 'dark': 63}),
    ('blue', 212, 52, None),
    ('teal', 172, 42, None),
    ('green', 135, 36, None),
    ('amber', 38, 64, None),
    ('rose', 345, 48, None),
)
_PRESET_LIGHTNESS = {'default': 55, 'light': 45, 'dark': 68}
_PRESET_SATURATION_BOOST = {'default': 0, 'light': 4, 'dark': 14}
MIN_LEVEL_CONTRAST = 3.0


def theme_key(theme):
    """'dark', 'light' or 'default' for any theme name."""
    name = str(theme or 'default').lower()
    return name if name in ('dark', 'light') else 'default'


def preset_color(key, theme):
    """The colour of preset *key* in *theme* (purple when the key is unknown)."""
    theme = theme_key(theme)
    for name, hue, saturation, lightness in LEVEL_PRESETS:
        if name != key:
            continue
        if hue is None:
            return QColor(THEME_LEVEL_COLORS[theme])
        light = lightness[theme] if lightness else _PRESET_LIGHTNESS[theme]
        sat = saturation if lightness else min(saturation + _PRESET_SATURATION_BOOST[theme], 80)
        return QColor.fromHslF(hue / 360.0, sat / 100.0, light / 100.0)
    return QColor(THEME_LEVEL_COLORS[theme])


def _luminance(color):
    def channel(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(color.red()) + 0.7152 * channel(color.green()) + 0.0722 * channel(color.blue())


def contrast_ratio(a, b):
    """WCAG contrast ratio of two colours (1 to 21)."""
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def legible_color(color, theme, minimum=MIN_LEVEL_CONTRAST):
    """*color*, its lightness nudged away from the panel until it stands out
    against the panel of *theme* (custom picks only; presets already do)."""
    background = PANEL_BACKGROUNDS[theme_key(theme)]
    color = QColor(color)
    color.setAlpha(255)
    step = -0.02 if _luminance(background) > 0.5 else 0.02
    h, s, l, _ = color.getHslF()
    h = max(h, 0.0)  # achromatic colours report -1
    for _ in range(50):
        if contrast_ratio(color, background) >= minimum:
            break
        l = min(max(l + step, 0.05), 0.95)
        color = QColor.fromHslF(h, s, l)
    return color


def resolve_level_color(value, theme, default=None):
    """The colour to paint for a stored level colour *value* in *theme*.
    *default* is the user's Default Level Color (a QColor) or None."""
    if isinstance(value, str) and value.startswith('preset:'):
        return preset_color(value.split(':', 1)[1], theme)
    if isinstance(value, str) and QColor.isValidColor(value):
        return legible_color(QColor(value), theme)
    if default is not None and QColor(default).isValid():
        return legible_color(QColor(default), theme)
    return QColor(THEME_LEVEL_COLORS[theme_key(theme)])


def _theme_of(widget):
    """The window's theme, as the layer buttons find it."""
    parent = widget
    while parent is not None:
        if hasattr(parent, 'current_theme'):
            return parent.current_theme
        parent = parent.parent()
    return 'default'


def _draw_outlined_text(painter, rect, text, pixel_size):
    """White bold letters with a black outline, centred in *rect*, like the
    layer buttons' names."""
    font = QFont(painter.font())
    font.setBold(True)
    font.setPixelSize(pixel_size)
    outline = QPainterPath()
    outline.addText(0, 0, font, text)
    bounds = outline.boundingRect()
    x = rect.x() + (rect.width() - bounds.width()) / 2 - bounds.x()
    y = rect.y() + (rect.height() - bounds.height()) / 2 - bounds.y()
    path = QPainterPath()
    path.addText(x, y, font, text)
    painter.setPen(QPen(Qt.black, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)
    painter.setPen(Qt.NoPen)
    painter.setBrush(Qt.white)
    painter.drawPath(path)


def _draw_chevron(painter, center, pointing_up):
    """A white chevron with a black outline, 10 px wide."""
    dy = -2.5 if pointing_up else 2.5
    path = QPainterPath()
    path.moveTo(center.x() - 5, center.y() - dy)
    path.lineTo(center.x(), center.y() + dy)
    path.lineTo(center.x() + 5, center.y() - dy)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(Qt.black, 4.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)
    painter.setPen(QPen(Qt.white, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)


class LevelButton(QPushButton):
    """The 146 x 27 button of a level row: fold chevrons at both edges, the
    level's name in between, filled with the level's colour."""

    def __init__(self, row, parent=None):
        """A button of *row*, which supplies its text, colour and menu."""
        super().__init__(parent)
        self.row = row
        self.setFixedSize(LEVEL_BUTTON_SIZE)
        self.setCursor(Qt.PointingHandCursor)
        # Reachable with Tab, so the keyboard's menu key opens its menu
        self.setFocusPolicy(Qt.TabFocus)
        self.setMouseTracking(True)
        self._drag_start_position = None
        self._press_zone = None
        self._hover_zone = None
        # Everything is painted in paintEvent; keep the theme's QPushButton
        # look (background, border) off this button.
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def zone_at(self, x):
        """'above' (left chevron), 'below' (right chevron) or 'name'."""
        if x < CHEVRON_ZONE_WIDTH:
            return 'above'
        if x >= self.width() - CHEVRON_ZONE_WIDTH:
            return 'below'
        return 'name'

    def zone_tooltip(self, zone):
        panel, level = self.row.layer_panel, self.row.level
        if zone == 'above':
            key = 'level_unfold_above' if panel.is_level_folded(level) else 'level_fold_above'
        elif zone == 'below':
            key = 'level_unfold_below' if panel.is_level_folded(level - 1) else 'level_fold_below'
        else:
            key = 'level_deselect_block' if panel.level_scope() == level else 'level_select_block'
        return panel.level_text(key)

    def paintEvent(self, event):
        panel, level = self.row.layer_panel, self.row.level
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        color = self.row.color()
        painter.fillRect(self.rect(), color.lighter(112) if self.underMouse() else color)
        if self._hover_zone in ('above', 'below'):
            x = 0 if self._hover_zone == 'above' else self.width() - CHEVRON_ZONE_WIDTH
            painter.fillRect(x, 0, CHEVRON_ZONE_WIDTH, self.height(), QColor(255, 255, 255, 55))
        mid_y = self.height() / 2.0
        # Left: folds the block above (points up while it shows, down once folded)
        _draw_chevron(painter, QPointF(CHEVRON_ZONE_WIDTH / 2.0, mid_y),
                      pointing_up=not panel.is_level_folded(level))
        # Right: folds the block below (points down while it shows)
        _draw_chevron(painter, QPointF(self.width() - CHEVRON_ZONE_WIDTH / 2.0, mid_y),
                      pointing_up=panel.is_level_folded(level - 1))
        name_rect = self.rect().adjusted(CHEVRON_ZONE_WIDTH, 1, -CHEVRON_ZONE_WIDTH, 1)
        _draw_outlined_text(painter, name_rect, self.row.text(), 14)
        if self.hasFocus():
            painter.setPen(QPen(Qt.white, 1, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect().adjusted(1, 1, -2, -2))
        painter.end()

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            QToolTip.showText(event.globalPos(), self.zone_tooltip(self.zone_at(event.pos().x())), self)
            return True
        return super().event(event)

    def leaveEvent(self, event):
        self._hover_zone = None
        self.update()
        super().leaveEvent(event)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def mousePressEvent(self, event):
        """Remember where a left press began, for a click or a drag."""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
            self._press_zone = self.zone_at(event.pos().x())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """A click (no drag) runs its zone: fold above, fold below, or
        select the level's block."""
        clicked_zone = None
        if (event.button() == Qt.LeftButton and self._drag_start_position is not None
                and self.rect().contains(event.pos())
                and self.zone_at(event.pos().x()) == self._press_zone):
            clicked_zone = self._press_zone
        self._drag_start_position = None
        self._press_zone = None
        super().mouseReleaseEvent(event)
        if clicked_zone is None:
            return
        panel, level = self.row.layer_panel, self.row.level
        if clicked_zone == 'above':
            panel.toggle_level_fold(level)
        elif clicked_zone == 'below':
            panel.toggle_level_fold(level - 1)
        else:
            panel.toggle_level_scope(level)

    def mouseMoveEvent(self, event):
        """Track the hovered chevron; start dragging the whole row once a
        held mouse has moved far enough."""
        zone = self.zone_at(event.pos().x())
        if zone != self._hover_zone:
            self._hover_zone = zone
            self.update()
        if not (event.buttons() & Qt.LeftButton) or self._drag_start_position is None:
            return
        if not (QApplication.mouseButtons() & Qt.LeftButton):
            self._drag_start_position = None
            return
        if (event.pos() - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        panel = self.row.layer_panel
        index = panel.scroll_layout.indexOf(self.row)
        if index == -1:
            return
        # The same drag as a layer button: the panel's drop code moves rows
        # by their position in the list (on the Masks tab it moves masks).
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-layerbutton-index", str(index).encode())
        drag.setMimeData(mime)
        drag.setPixmap(self.row.grab())
        drag.setHotSpot(event.pos())
        self._drag_start_position = None
        self._press_zone = None
        QApplication.instance().setProperty("layer_drag_active", True)
        try:
            drag.exec_(Qt.MoveAction)
        finally:
            QApplication.instance().setProperty("layer_drag_active", False)
        self._drag_start_position = None


class _FullWidthRow(QWidget):
    """A row of the layer list as wide as its visible part.

    The list's layout centres each item at its own width (layer buttons are
    a fixed 146 px), so the row would otherwise be only as wide as its
    content. It follows the list's visible width instead, through every
    resize of the layer panel and the scrollbar coming and going."""

    def __init__(self, layer_panel, level, parent=None):
        super().__init__(parent)
        self.layer_panel = layer_panel
        self.level = level
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        viewport = self._viewport()
        if viewport is not None:
            viewport.installEventFilter(self)  # Qt drops it when this row is deleted
            self._fit_width(viewport.width())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

    def _viewport(self):
        """The visible part of the layer list, whose width the row follows."""
        scroll_area = getattr(self.layer_panel, 'scroll_area', None)
        return scroll_area.viewport() if scroll_area is not None else None

    def _fit_width(self, width):
        """Be exactly as wide as the visible list (never under the button)."""
        self.setFixedWidth(max(int(width), LEVEL_BUTTON_SIZE.width()))

    def eventFilter(self, obj, event):
        """Follow every resize of the list: panel dragged, scrollbar shown."""
        if event.type() == QEvent.Resize and obj is self._viewport():
            self._fit_width(event.size().width())
        return False

    def color(self):
        """The level's colour in the panel's theme."""
        return self.layer_panel.level_color(self.level)

    def show_menu(self, pos):
        show_level_menu(self.layer_panel, self.level, self, self.mapToGlobal(pos))


class LevelRow(_FullWidthRow):
    """A level's whole row: the button, centred, over the full-width line."""

    def __init__(self, layer_panel, level, parent=None):
        """The row of *level* (1, 2, ...) in *layer_panel*'s list."""
        super().__init__(layer_panel, level, parent)
        self.setFixedHeight(LEVEL_BUTTON_SIZE.height() + LEVEL_LINE_HEIGHT)

        self.button = LevelButton(self, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.button, 0, Qt.AlignHCenter)
        layout.addSpacing(LEVEL_LINE_HEIGHT)  # the line, painted in paintEvent

        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.show_menu(self.button.mapTo(self, pos)))

    def paintEvent(self, event):
        """The 4 px line under the button, from edge to edge."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(0, self.height() - LEVEL_LINE_HEIGHT, self.width(), LEVEL_LINE_HEIGHT, self.color())
        painter.end()

    def text(self):
        """The row's name in the panel's language: "Level 1"..."""
        return self.layer_panel.level_name(self.level)

    def set_level(self, level):
        """Renumber the row (after a level below it was removed)."""
        self.level = level
        self.update()
        self.button.update()

    def restyle(self):
        """Repaint in the current colour (theme or level colour changed)."""
        self.update()
        self.button.update()


class GroundRow(_FullWidthRow):
    """Level 0, the ground, as a single 4 px line under the bottom layer.

    Shown only when the user turns the ground line on (and some level
    exists). A click selects the ground's block like a level row's name;
    right-click opens the level menu."""

    def __init__(self, layer_panel, parent=None):
        super().__init__(layer_panel, 0, parent)
        self.setFixedHeight(GROUND_ROW_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def line_rect(self):
        """Where the 4 px line is drawn: the middle of the row."""
        top = (self.height() - LEVEL_LINE_HEIGHT) // 2
        return self.rect().adjusted(0, top, 0, -(self.height() - LEVEL_LINE_HEIGHT - top))

    def paintEvent(self, event):
        painter = QPainter(self)
        color = self.color()
        painter.fillRect(self.line_rect(), color.lighter(118) if self.underMouse() else color)
        painter.end()

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            panel = self.layer_panel
            key = 'level_deselect_block' if panel.level_scope() == 0 else 'level_select_block'
            QToolTip.showText(event.globalPos(),
                              '{} · {}'.format(panel.level_name(0), panel.level_text(key)), self)
            return True
        if event.type() in (QEvent.HoverEnter, QEvent.HoverLeave):
            self.update()
        return super().event(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.layer_panel.toggle_level_scope(0)
        super().mouseReleaseEvent(event)

    def text(self):
        return self.layer_panel.level_name(0)

    def restyle(self):
        self.update()


# ----------------------------------------------------------------------
# The level menu, built like the layer buttons' menu: HoverLabel rows in
# QWidgetActions under the shared menu stylesheet.
# ----------------------------------------------------------------------
def _new_menu(panel, parent, theme):
    menu = QMenu(parent)
    if getattr(panel, 'language_code', None) == 'he':
        menu.setLayoutDirection(Qt.RightToLeft)
    try:
        from numbered_layer_button import build_menu_stylesheet
        menu.setStyleSheet(build_menu_stylesheet(theme))
    except Exception:
        pass  # keep Qt's own menu look
    return menu


def _add_row(menu, panel, text, theme, callback, enabled=True):
    """One menu row: a HoverLabel in a QWidgetAction, as in the layer menus.
    A disabled row is greyed and does nothing."""
    from numbered_layer_button import HoverLabel
    label = HoverLabel(text, menu, theme)
    label.setMinimumHeight(35)
    if getattr(panel, 'language_code', None) == 'he':
        label.setLayoutDirection(Qt.RightToLeft)
        label.setAlignment(Qt.AlignLeft)
    action = QWidgetAction(menu)
    action.setDefaultWidget(label)
    if enabled:
        action.triggered.connect(callback)
    else:
        background = '#333333' if theme == 'dark' else '#F0F0F0'
        label.setStyleSheet(f"background-color: {background}; color: #909090; padding: 5px 25px 5px 5px;")
        label.setEnabled(False)
        action.setEnabled(False)
    menu.addAction(action)
    return action


def show_level_menu(panel, level, widget, global_pos):
    """The right-click menu of level *level* (0 is the ground line)."""
    theme = _theme_of(widget)
    t = panel.level_text
    menu = _new_menu(panel, widget, theme)
    chosen = []

    def pick(fn):
        return lambda: chosen.append(fn)

    scoped = panel.level_scope() == level
    _add_row(menu, panel, t('level_deselect_block' if scoped else 'level_select_block'), theme,
             pick(lambda: panel.toggle_level_scope(level)))
    menu.addSeparator()
    _add_row(menu, panel, t('level_unfold_above' if panel.is_level_folded(level) else 'level_fold_above'),
             theme, pick(lambda: panel.toggle_level_fold(level)))
    if level > 0:
        _add_row(menu, panel, t('level_unfold_below' if panel.is_level_folded(level - 1) else 'level_fold_below'),
                 theme, pick(lambda: panel.toggle_level_fold(level - 1)))
        menu.addSeparator()
        _add_row(menu, panel, t('level_move_up'), theme, pick(lambda: panel.move_level(level, up=True)),
                 enabled=panel.can_move_level(level, up=True))
        _add_row(menu, panel, t('level_move_down'), theme, pick(lambda: panel.move_level(level, up=False)),
                 enabled=panel.can_move_level(level, up=False))
    menu.addSeparator()
    _add_row(menu, panel, t('level_recolor'), theme,
             pick(lambda: show_level_color_menu(panel, level, widget, global_pos)))
    _add_row(menu, panel, t('level_hide_ground_line' if panel.ground_line_shown() else 'level_show_ground_line'),
             theme, pick(lambda: panel.set_ground_line_shown(not panel.ground_line_shown())))
    if level > 0:
        menu.addSeparator()
        _add_row(menu, panel, t('level_remove'), theme, pick(lambda: panel.remove_level(level)))
    menu.exec_(global_pos)
    # Run the choice once the menu is gone (a Recolor menu opens in its place)
    for fn in chosen:
        fn()


def show_level_color_menu(panel, level, widget, global_pos):
    """Recolor: the colour families, a custom colour, or back to the default."""
    theme = _theme_of(widget)
    t = panel.level_text
    menu = _new_menu(panel, widget, theme)
    current = panel.level_color_value(level)
    chosen = []
    for key, _, _, _ in LEVEL_PRESETS:
        value = 'preset:' + key
        swatch = preset_color(key, theme).name()
        mark = '✓ ' if current == value else ''
        text = (f"<span style='color:{swatch}'>■■</span>&nbsp;&nbsp;"
                f"{mark}{t('level_color_' + key)}")
        _add_row(menu, panel, text, theme, (lambda v=value: chosen.append(lambda: panel.set_level_color(level, v))))
    menu.addSeparator()
    custom_mark = '✓ ' if isinstance(current, str) and current.startswith('#') else ''
    _add_row(menu, panel, custom_mark + t('level_color_custom'), theme,
             lambda: chosen.append(lambda: _pick_custom_level_color(panel, level, widget)))
    _add_row(menu, panel, t('level_color_reset'), theme,
             lambda: chosen.append(lambda: panel.set_level_color(level, None)), enabled=current is not None)
    menu.exec_(global_pos)
    for fn in chosen:
        fn()


def _pick_custom_level_color(panel, level, widget):
    dialog = QColorDialog(panel.level_color(level), widget)
    dialog.setOption(QColorDialog.DontUseNativeDialog)
    if dialog.exec_():
        color = dialog.currentColor()
        if color.isValid():
            panel.set_level_color(level, color.name())
