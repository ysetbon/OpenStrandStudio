"""Draggable, semi-transparent tab edge that overlays the canvas.

The edge is parented to the canvas (not the main layout) so it floats over the
drawing area without stealing canvas space. It opens bottom-center by default
and can be dragged anywhere inside the canvas. No yellow is used anywhere; all
colors come from the active theme table below.
"""

from PyQt5.QtCore import Qt, QEvent, QRectF, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy

from translations import translations


# Theme tables (see implementation brief). Every color is theme-driven; no yellow.
THEMES = {
    'default': {
        'panel_bg':     QColor(25, 25, 25, 135),
        'border':       QColor(210, 210, 210, 120),
        'active_bg':    QColor(0xE8, 0xE8, 0xE8),
        'inactive_bg':  QColor(45, 45, 45, 170),
        'active_text':  QColor(0x11, 0x11, 0x11),
        'inactive_text': QColor(0xF0, 0xF0, 0xF0),
        # Magnet/snap accent: the default-theme canvas is light, so use a dark
        # gray that stands out against it.
        'snap':         QColor(70, 70, 70),
    },
    'dark': {
        'panel_bg':     QColor(15, 15, 15, 165),
        'border':       QColor(230, 230, 230, 85),
        'active_bg':    QColor(0x4A, 0x4A, 0x4A),
        'inactive_bg':  QColor(35, 35, 35, 180),
        'active_text':  QColor(0xFF, 0xFF, 0xFF),
        'inactive_text': QColor(0xDA, 0xDA, 0xDA),
        # Lighter gray so the magnet is clearly visible on the dark theme.
        'snap':         QColor(235, 235, 235),
    },
    'light': {
        'panel_bg':     QColor(255, 255, 255, 190),
        'border':       QColor(80, 80, 80, 100),
        'active_bg':    QColor(0xFF, 0xFF, 0xFF),
        'inactive_bg':  QColor(225, 225, 225, 180),
        'active_text':  QColor(0x11, 0x11, 0x11),
        'inactive_text': QColor(0x33, 0x33, 0x33),
        # Darker gray so the magnet stands out against the light theme.
        'snap':         QColor(70, 70, 70),
    },
}


def theme_colors(name):
    return THEMES.get(name, THEMES['default'])


def snap_target_style(theme_name, active=False):
    """Theme-specific colors for magnet snap target pills."""
    if theme_name == 'dark':
        return {
            'shadow': QColor(0, 0, 0, 105 if active else 82),
            'glow': QColor(255, 255, 255, 42 if active else 30),
            'fill': QColor(255, 255, 255, 34 if active else 24),
            'outer': QColor(235, 235, 235, 175 if active else 142),
            'inner': QColor(235, 235, 235, 152 if active else 122),
        }
    if theme_name == 'light':
        return {
            'shadow': QColor(0, 0, 0, 42 if active else 32),
            'glow': QColor(255, 255, 255, 88 if active else 68),
            'fill': QColor(255, 255, 255, 118 if active else 92),
            'outer': QColor(154, 154, 154, 186 if active else 150),
            'inner': QColor(152, 152, 152, 158 if active else 126),
        }
    return {
        'shadow': QColor(0, 0, 0, 36 if active else 27),
        'glow': QColor(255, 255, 255, 82 if active else 62),
        'fill': QColor(255, 255, 255, 108 if active else 82),
        'outer': QColor(198, 198, 198, 186 if active else 150),
        'inner': QColor(190, 190, 190, 164 if active else 130),
    }


class IconButton(QWidget):
    """Small painted icon button (duplicate / close / plus). Themed pen color."""

    clicked = pyqtSignal()

    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self.kind = kind  # 'duplicate' | 'close' | 'plus'
        self._hover = False
        self._color = QColor(0xF0, 0xF0, 0xF0)
        size = 22 if kind == 'plus' else 18
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        # Consume so the click does not fall through to the chip / drag handler.
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        event.accept()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        c = QColor(self._color)
        if self._hover:
            # Slightly emphasize on hover with a faint rounded backdrop.
            bg = QColor(self._color)
            bg.setAlpha(45)
            p.setPen(Qt.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(self.rect(), 4, 4)
        pen = QPen(c)
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        r = self.rect()
        m = 5  # margin
        if self.kind == 'close':
            p.drawLine(r.left() + m, r.top() + m, r.right() - m, r.bottom() - m)
            p.drawLine(r.right() - m, r.top() + m, r.left() + m, r.bottom() - m)
        elif self.kind == 'plus':
            cx = r.center().x()
            cy = r.center().y()
            p.drawLine(cx, r.top() + m, cx, r.bottom() - m)
            p.drawLine(r.left() + m, cy, r.right() - m, cy)
        elif self.kind == 'duplicate':
            # Two overlapping squares.
            w = r.width()
            s = w - 2 * m - 3  # square side
            p.setBrush(Qt.NoBrush)
            # back square (top-right)
            p.drawRect(r.left() + m + 3, r.top() + m, s, s)
            # front square (bottom-left)
            p.drawRect(r.left() + m, r.top() + m + 3, s, s)
        p.end()


class DirtyDot(QWidget):
    """Painted unsaved-state dot (vector, so it matches the icons exactly on
    every platform instead of relying on a Unicode bullet glyph)."""

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self._color = QColor(color)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(self._color)
        p.drawEllipse(1, 1, 6, 6)
        p.end()


TAB_EDGE_HEIGHT = 53
TAB_CHIP_HEIGHT = 40
TAB_WIDTH_SCALE = 1.1
TAB_EDGE_VERTICAL_MARGIN = 6
TAB_CHIP_VERTICAL_MARGIN = 3


class TabChip(QWidget):
    """A single tab: title (+ dirty dot), duplicate icon, close X."""

    switch_requested = pyqtSignal(str)
    duplicate_requested = pyqtSignal(str)
    close_requested = pyqtSignal(str)

    def __init__(self, session, title, active, theme_name, parent=None, rtl=False):
        super().__init__(parent)
        self.tab_id = session.id
        self.active = active
        self.theme_name = theme_name
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(TAB_CHIP_HEIGHT)

        layout = QHBoxLayout(self)
        # Mirror the inner padding so the icons hug the trailing edge in RTL.
        if rtl:
            layout.setContentsMargins(7, TAB_CHIP_VERTICAL_MARGIN, 11, TAB_CHIP_VERTICAL_MARGIN)
        else:
            layout.setContentsMargins(11, TAB_CHIP_VERTICAL_MARGIN, 7, TAB_CHIP_VERTICAL_MARGIN)
        layout.setSpacing(7)

        colors = theme_colors(theme_name)
        text_color = colors['active_text'] if active else colors['inactive_text']

        # Painted (vector) unsaved-state dot, on the reading-start side.
        self.dirty_dot = DirtyDot(text_color, self) if session.dirty else None

        self.label = QLabel(title, self)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.label.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        font = QFont()
        font.setPointSize(9)
        font.setBold(active)
        self.label.setFont(font)
        # AlignAbsolute is required in the RTL branch: the label's layout
        # direction is RightToLeft (for correct Hebrew BiDi shaping), and under
        # an RTL layout direction a plain Qt.AlignRight is resolved *relative to*
        # that direction and flips to the visual left. AlignAbsolute pins it to
        # the real right edge so the text hugs the right side of the tab.
        self.label.setAlignment(
            Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter if rtl
            else Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setStyleSheet(
            "color: rgba(%d,%d,%d,%d); background: transparent;" % (
                text_color.red(), text_color.green(), text_color.blue(), text_color.alpha()))

        self.dup_btn = IconButton('duplicate', self)
        self.dup_btn.set_color(text_color)
        self.dup_btn.clicked.connect(lambda: self.duplicate_requested.emit(self.tab_id))

        self.close_btn = IconButton('close', self)
        self.close_btn.set_color(text_color)
        self.close_btn.clicked.connect(lambda: self.close_requested.emit(self.tab_id))

        # LTR: [dot] text, then icons (duplicate, close) on the right.
        # RTL (Hebrew): icons on the left, then text [dot] on the right.
        if rtl:
            layout.addWidget(self.close_btn)
            layout.addWidget(self.dup_btn)
            layout.addWidget(self.label, 1)
            if self.dirty_dot is not None:
                layout.addWidget(self.dirty_dot)
        else:
            if self.dirty_dot is not None:
                layout.addWidget(self.dirty_dot)
            layout.addWidget(self.label, 1)
            layout.addWidget(self.dup_btn)
            layout.addWidget(self.close_btn)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.switch_requested.emit(self.tab_id)
        event.accept()

    def mousePressEvent(self, event):
        # Consume so a click on the chip selects it instead of starting a drag.
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        layout = self.layout()
        if layout is not None:
            layout.setGeometry(self.rect())

    def paintEvent(self, event):
        colors = theme_colors(self.theme_name)
        bg = colors['active_bg'] if self.active else colors['inactive_bg']
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, 9, 9)
        p.end()


# The six magnet anchors the tab edge can snap to.
ANCHOR_NAMES = ("top_left", "top_center", "top_right",
                "bottom_left", "bottom_center", "bottom_right")
ANCHOR_MARGIN = 24      # px gap from the canvas edges at an anchor
SNAP_THRESHOLD = 75     # px: how close the edge must get before the magnet grabs
SNAP_MARKER_WIDTH = 128.0
SNAP_MARKER_HEIGHT = 38.0


class SnapOverlay(QWidget):
    """Transparent full-canvas overlay shown only while dragging the tab edge.

    It visualizes the six snap anchors as ghost targets and highlights the one
    the magnet is about to grab, so the user can see where it will dock.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._targets = {}   # name -> (x, y, w, h)
        self._active = None
        self._theme = 'default'

    def update_state(self, targets, active, theme='default'):
        self._targets = targets
        self._active = active
        self._theme = theme
        self.update()

    def _draw_snap_target(self, painter, rect, active):
        style = snap_target_style(self._theme, active)
        radius = min(12.0, rect.height() / 2.0)

        painter.setPen(Qt.NoPen)
        shadow_layers = (
            (-4.0, -4.0, 4.0, 4.0, 0.34),
            (-2.6, -2.6, 2.6, 2.6, 0.52),
            (-1.2, -1.2, 1.2, 1.2, 0.68),
        )
        for left, top, right, bottom, alpha_scale in shadow_layers:
            shadow = QColor(style['shadow'])
            shadow.setAlpha(int(shadow.alpha() * alpha_scale))
            shadow_rect = rect.adjusted(left, top, right, bottom)
            painter.setBrush(shadow)
            painter.drawRoundedRect(shadow_rect, radius + max(abs(left), abs(right)),
                                    radius + max(abs(top), abs(bottom)))

        glow = QColor(style['glow'])
        glow_rect = rect.adjusted(-2.0, -2.0, 2.0, 2.0)
        painter.setBrush(glow)
        painter.drawRoundedRect(glow_rect, radius + 2.0, radius + 2.0)

        painter.setBrush(style['fill'])
        painter.drawRoundedRect(rect, radius, radius)

        outer_width = 3.0 if active else 2.4
        outer_pen = QPen(style['outer'])
        outer_pen.setWidthF(outer_width)
        outer_pen.setCapStyle(Qt.RoundCap)
        outer_pen.setJoinStyle(Qt.RoundJoin)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(outer_pen)
        outer_rect = rect.adjusted(outer_width / 2.0, outer_width / 2.0,
                                   -outer_width / 2.0, -outer_width / 2.0)
        painter.drawRoundedRect(outer_rect, max(1.0, radius - outer_width / 2.0),
                                max(1.0, radius - outer_width / 2.0))

        inset = 7.0
        inner_rect = rect.adjusted(inset, inset, -inset, -inset)
        if inner_rect.width() > 0 and inner_rect.height() > 0:
            dash_pen = QPen(style['inner'])
            dash_pen.setWidthF(1.7 if active else 1.45)
            dash_pen.setCapStyle(Qt.RoundCap)
            dash_pen.setJoinStyle(Qt.RoundJoin)
            dash_pen.setDashPattern([4.0, 5.0])
            painter.setPen(dash_pen)
            inner_radius = max(1.0, inner_rect.height() / 2.0)
            painter.drawRoundedRect(inner_rect, inner_radius, inner_radius)

    def paintEvent(self, event):
        if not self._targets:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        for name, (x, y, w, h) in self._targets.items():
            cx = x + w / 2.0
            cy = y + h / 2.0
            # Dock marker sized like a single tab so all targets keep the same
            # footprint before and during the snap lock.
            mw, mh = SNAP_MARKER_WIDTH, SNAP_MARKER_HEIGHT
            marker = QRectF(cx - mw / 2.0, cy - mh / 2.0, mw, mh)
            self._draw_snap_target(p, marker, name == self._active)
        p.end()


class DraggableTabEdge(QWidget):
    """Floating, semi-transparent edge containing the tab chips and the + button."""

    GRIP_WIDTH = 26

    def __init__(self, canvas, tab_manager):
        super().__init__(canvas)
        self.canvas = canvas
        self.tab_manager = tab_manager
        self.theme_name = 'default'
        self._rtl = False
        self._dragging = False
        self._drag_offset = None
        # Position model: either docked to a named anchor (the magnet result) or
        # free-floating at a stored center ratio. Default is the bottom-center
        # anchor. Persisted across launches via get/apply_position_setting().
        self._anchor = 'bottom_center'
        self._pos_ratio = None  # (center_x_ratio, center_y_ratio) when free
        self._snap_target = None  # anchor the magnet is grabbing during a drag

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedHeight(TAB_EDGE_HEIGHT)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Track hover (no button pressed) so we can show the move cursor on grip.
        self.setMouseTracking(True)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(self.GRIP_WIDTH, TAB_EDGE_VERTICAL_MARGIN,
                                        12, TAB_EDGE_VERTICAL_MARGIN)
        self._layout.setSpacing(8)

        self.plus_btn = IconButton('plus', self)
        self.plus_btn.clicked.connect(self.tab_manager.new_tab)

        # Drag-time magnet visualization overlay (sits over the canvas).
        self._snap_overlay = SnapOverlay(self.canvas)
        self._snap_overlay.hide()

        self.tab_manager.changed.connect(self.rebuild)
        self.canvas.installEventFilter(self)

        self.rebuild()

    # -------------------------------------------------------------- theming
    def set_theme(self, theme_name):
        if theme_name not in THEMES:
            theme_name = 'default'
        self.theme_name = theme_name
        self.rebuild()

    # -------------------------------------------------------------- building
    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.plus_btn:
                w.setParent(None)
                w.deleteLater()

    def _is_rtl(self):
        mw = getattr(self.tab_manager, 'main_window', None)
        return getattr(mw, 'language_code', 'en') == 'he'

    def rebuild(self):
        self._clear_layout()
        colors = theme_colors(self.theme_name)

        rtl = self._is_rtl()
        self._rtl = rtl
        # Reserve the grip strip on the trailing side: left for LTR, right for RTL.
        if rtl:
            self._layout.setContentsMargins(12, TAB_EDGE_VERTICAL_MARGIN,
                                            self.GRIP_WIDTH, TAB_EDGE_VERTICAL_MARGIN)
        else:
            self._layout.setContentsMargins(self.GRIP_WIDTH, TAB_EDGE_VERTICAL_MARGIN,
                                            12, TAB_EDGE_VERTICAL_MARGIN)

        chips = []
        for session in self.tab_manager.tabs:
            active = (session.id == self.tab_manager.active_tab_id)
            title = self.tab_manager.title_for(session)
            chip = TabChip(session, title, active, self.theme_name, self, rtl=rtl)
            chip.switch_requested.connect(self.tab_manager.switch_to_tab)
            chip.duplicate_requested.connect(self.tab_manager.duplicate_tab)
            chip.close_requested.connect(self.tab_manager.close_tab)
            chips.append(chip)

        # Plus button uses the inactive text color so it reads on the panel.
        self.plus_btn.set_color(colors['inactive_text'])

        # In RTL the + sits on the left and tabs flow right-to-left (oldest on the
        # right, next to the grip; newest tabs appear on the left next to the +).
        if rtl:
            ordered = [self.plus_btn] + list(reversed(chips))
        else:
            ordered = chips + [self.plus_btn]
        for wdg in ordered:
            self._layout.addWidget(wdg)
            # Explicitly show: when rebuilding an already-visible edge, freshly
            # created children would otherwise stay hidden until the next event
            # loop, which makes QLayout.sizeHint() count them as zero-width.
            wdg.show()

        self._layout.invalidate()
        self._layout.activate()
        base_w = self._layout.sizeHint().width()

        for chip in chips:
            chip.setMinimumWidth(round(chip.sizeHint().width() * TAB_WIDTH_SCALE))

        self._layout.invalidate()
        self._layout.activate()
        w = max(round(base_w * TAB_WIDTH_SCALE), self._layout.sizeHint().width())
        max_w = max(120, self.canvas.width() - 20)
        w = min(w, max_w)
        self.resize(w, TAB_EDGE_HEIGHT)
        self._layout.setGeometry(self.rect())
        for chip in chips:
            chip.layout().setGeometry(chip.rect())
        if self.isVisible():
            self.reposition()
        self.update()

    # -------------------------------------------------------------- geometry
    def show_edge(self):
        self.rebuild()
        self.reposition()
        self.show()
        self.raise_()

    def _anchor_positions(self):
        """Top-left (x, y) for each of the six magnet anchors, for the current
        canvas and edge size."""
        cw = self.canvas.width()
        ch = self.canvas.height()
        w = self.width()
        h = self.height()
        m = ANCHOR_MARGIN
        left_x = m
        center_x = (cw - w) // 2
        right_x = cw - w - m
        top_y = m
        bottom_y = ch - h - m
        return {
            "top_left": (left_x, top_y),
            "top_center": (center_x, top_y),
            "top_right": (right_x, top_y),
            "bottom_left": (left_x, bottom_y),
            "bottom_center": (center_x, bottom_y),
            "bottom_right": (right_x, bottom_y),
        }

    def _snap_targets_rects(self):
        """Anchor name -> (x, y, w, h) rectangle the edge would occupy there."""
        w = self.width()
        h = self.height()
        return {name: (x, y, w, h) for name, (x, y) in self._anchor_positions().items()}

    def reposition(self):
        cw = self.canvas.width()
        ch = self.canvas.height()
        w = self.width()
        h = self.height()
        if self._anchor:
            anchors = self._anchor_positions()
            x, y = anchors.get(self._anchor, anchors["bottom_center"])
        elif self._pos_ratio is not None:
            cx, cy = self._pos_ratio
            x = int(cx * cw - w / 2.0)
            y = int(cy * ch - h / 2.0)
        else:
            x = (cw - w) // 2
            y = ch - h - ANCHOR_MARGIN
        x = max(0, min(x, max(0, cw - w)))
        y = max(0, min(y, max(0, ch - h)))
        self.move(x, y)

    # ----------------------------------------------------------- persistence
    def get_position_setting(self):
        """Serialize the current position for user settings."""
        if self._anchor:
            return "anchor:%s" % self._anchor
        if self._pos_ratio is not None:
            return "ratio:%.4f,%.4f" % (self._pos_ratio[0], self._pos_ratio[1])
        return "anchor:bottom_center"

    def apply_position_setting(self, value):
        """Restore a position saved by get_position_setting()."""
        try:
            value = (value or "").strip()
            if value.startswith("anchor:"):
                name = value.split(":", 1)[1].strip()
                if name in ANCHOR_NAMES:
                    self._anchor = name
                    self._pos_ratio = None
            elif value.startswith("ratio:"):
                parts = value.split(":", 1)[1].split(",")
                cx = max(0.0, min(1.0, float(parts[0])))
                cy = max(0.0, min(1.0, float(parts[1])))
                self._pos_ratio = (cx, cy)
                self._anchor = None
        except Exception:
            pass
        if self.isVisible():
            self.reposition()

    def _store_ratio(self):
        cw = max(1, self.canvas.width())
        ch = max(1, self.canvas.height())
        cx = (self.x() + self.width() / 2.0) / cw
        cy = (self.y() + self.height() / 2.0) / ch
        self._pos_ratio = (cx, cy)

    def eventFilter(self, obj, event):
        if obj is self.canvas and event.type() == QEvent.Resize:
            if self.isVisible():
                self.reposition()
        return False

    # -------------------------------------------------------------- dragging
    def _over_grip(self, pos):
        """Whether a point falls on the grip strip (left for LTR, right for RTL)."""
        if self._rtl:
            return pos.x() >= self.width() - self.GRIP_WIDTH
        return pos.x() <= self.GRIP_WIDTH

    def _update_hover_cursor(self, pos):
        # Open-hand over the grip signals the edge can be moved; plain arrow on
        # the rest of the panel (chips/buttons set their own pointing-hand
        # cursor). Using an explicit arrow avoids inheriting the canvas's
        # drawing crosshair over the panel background.
        if self._over_grip(pos):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _show_snap_overlay(self):
        ov = self._snap_overlay
        ov.setGeometry(0, 0, self.canvas.width(), self.canvas.height())
        ov.update_state(self._snap_targets_rects(), None, self.theme_name)
        ov.show()
        ov.raise_()
        self.raise_()  # keep the edge above the overlay while dragging

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.pos()
            self._snap_target = None
            self.setCursor(Qt.ClosedHandCursor)  # "grabbing" while dragging
            self._show_snap_overlay()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_offset is not None:
            gp = self.mapToParent(event.pos())
            top_left = gp - self._drag_offset
            cw = self.canvas.width()
            ch = self.canvas.height()
            fx = max(0, min(top_left.x(), max(0, cw - self.width())))
            fy = max(0, min(top_left.y(), max(0, ch - self.height())))

            # Magnet: find the nearest anchor and grab it if within range.
            anchors = self._anchor_positions()
            best, best_d = None, None
            for name, (ax, ay) in anchors.items():
                d = ((fx - ax) ** 2 + (fy - ay) ** 2) ** 0.5
                if best_d is None or d < best_d:
                    best, best_d = name, d
            if best is not None and best_d <= SNAP_THRESHOLD:
                ax, ay = anchors[best]
                self.move(ax, ay)
                self._snap_target = best
            else:
                self.move(fx, fy)
                self._snap_target = None
                self._store_ratio()

            self._snap_overlay.update_state(self._snap_targets_rects(), self._snap_target, self.theme_name)
            event.accept()
        else:
            self._update_hover_cursor(event.pos())

    def mouseReleaseEvent(self, event):
        was_dragging = self._dragging
        self._dragging = False
        self._drag_offset = None
        if was_dragging:
            if self._snap_target:
                # Dock to the magnet anchor (re-derives exact position on resize).
                self._anchor = self._snap_target
                self._pos_ratio = None
                self.reposition()
            else:
                # Free position: remember it as a ratio.
                self._anchor = None
                self._store_ratio()
            self._snap_target = None
            self._snap_overlay.hide()
        self._update_hover_cursor(event.pos())
        event.accept()

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def hideEvent(self, event):
        # Make sure the magnet overlay never lingers when the edge is hidden.
        if hasattr(self, '_snap_overlay'):
            self._snap_overlay.hide()
        super().hideEvent(event)

    # -------------------------------------------------------------- painting
    def paintEvent(self, event):
        colors = theme_colors(self.theme_name)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        path = QPainterPath()
        path.addRoundedRect(rect, 13, 13)

        # Panel background.
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(colors['panel_bg']))
        p.drawPath(path)

        # Neutral (non-yellow) themed border.
        pen = QPen(colors['border'])
        pen.setWidthF(1.2)
        p.setBrush(Qt.NoBrush)
        p.setPen(pen)
        p.drawPath(path)

        # Grip dots (drag handle): left side for LTR, right side for RTL.
        dot = QColor(colors['inactive_text'])
        dot.setAlpha(150)
        p.setPen(Qt.NoPen)
        p.setBrush(dot)
        gx = (self.width() - 18) if self._rtl else 11
        cy = self.height() // 2
        for row in (-9, 0, 9):
            for col in (0, 5):
                p.drawEllipse(gx + col, cy + row - 1, 2, 2)
        p.end()
