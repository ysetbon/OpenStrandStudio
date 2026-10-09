"""The Level layer: one row of the layer panel that marks a storey in the stack.

A level row looks like a layer button, as wide as one and a third lower
(146 x 27 against 146 x 40), named "Level 1", "Level 2" and so on, with a
4 px line under it that runs the whole width of the list. It sits at the
bottom of the layers it carries. Layers below the lowest level row are on the
ground and have no row.

Right-click opens Move up / Move down / Remove; dragging the row moves it
like any layer (LayerPanel.dropEvent turns the new position into levels).
"""

import re

from PyQt5.QtCore import QEvent, QMimeData, QSize, Qt
from PyQt5.QtGui import QColor, QDrag, QFont, QFontMetrics, QPainter, QPainterPath
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMenu, QPushButton, QSizePolicy,
                             QVBoxLayout, QWidget)

# Same width as NumberedLayerButton, a third less tall (40 -> 27).
LEVEL_BUTTON_SIZE = QSize(146, 27)
LEVEL_LINE_HEIGHT = 4
LEVEL_COLOR = QColor("#7a63b8")
LEVEL_COLOR_HOVER = QColor("#8b76c6")


class LevelButton(QPushButton):
    """The purple 146 x 27 button of a level row."""

    def __init__(self, row, parent=None):
        """A button of *row*, which supplies its text and its menu."""
        super().__init__(parent)
        self.row = row
        self.setFixedSize(LEVEL_BUTTON_SIZE)
        self.setCursor(Qt.PointingHandCursor)
        # Reachable with Tab, so the keyboard's menu key opens its menu
        self.setFocusPolicy(Qt.TabFocus)
        self._drag_start_position = None
        self._apply_style()

    def _apply_style(self):
        """The level purple, a little lighter on hover; the text is painted."""
        self.setStyleSheet(
            f"QPushButton {{ background-color: {LEVEL_COLOR.name()}; border: none; }}"
            f"QPushButton:hover {{ background-color: {LEVEL_COLOR_HOVER.name()}; }}"
        )

    def paintEvent(self, event):
        """The level's name, centred, as NumberedLayerButton paints a layer's."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        text = self.row.text()
        outline = QPainterPath()
        outline.addText(0, 0, font, text)
        bounds = outline.boundingRect()
        x = (self.width() - bounds.width()) / 2 - bounds.x()
        y = (self.height() - bounds.height()) / 2 - bounds.y() + 1
        path = QPainterPath()
        path.addText(x, y, font, text)
        # White letters with a black outline, like the layer buttons.
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawPath(path)
        painter.end()

    def mousePressEvent(self, event):
        """Remember where a left press began, for a possible drag."""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """The press is over: no drag can start from it any more."""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Start dragging the whole row once the mouse has moved far enough
        (Strands tab only)."""
        if not (event.buttons() & Qt.LeftButton) or self._drag_start_position is None:
            return
        if not (QApplication.mouseButtons() & Qt.LeftButton):
            self._drag_start_position = None
            return
        if (event.pos() - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        panel = self.row.layer_panel
        if getattr(panel, 'layer_tab', 'strands') == 'masks':
            # The Masks tab hides the strands a level row is moved past
            self._drag_start_position = None
            return
        index = panel.scroll_layout.indexOf(self.row)
        if index == -1:
            return
        # The same drag as a layer button: the panel's drop code moves rows
        # by their position in the list.
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-layerbutton-index", str(index).encode())
        drag.setMimeData(mime)
        drag.setPixmap(self.row.grab())
        drag.setHotSpot(event.pos())
        self._drag_start_position = None
        QApplication.instance().setProperty("layer_drag_active", True)
        try:
            drag.exec_(Qt.MoveAction)
        finally:
            QApplication.instance().setProperty("layer_drag_active", False)
        self._drag_start_position = None


class SplitButtonRow(QWidget):
    """Two buttons as the equal halves of one row: New Strand | New Level and
    New Mask | New Level.

    Each half takes half the row whatever its text. A text too long for its
    half (a long translation, a narrow panel) gets a smaller font instead of
    pushing the halves apart."""

    MAX_FONT_PX = 14  # the bottom buttons' size
    MIN_FONT_PX = 9

    def __init__(self, left, right, parent=None):
        """*left* and *right* become the two halves, in that order."""
        super().__init__(parent)
        self.buttons = (left, right)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for button in self.buttons:
            # Ignored: the width comes from the stretch, not from the text
            button.setSizePolicy(QSizePolicy.Ignored, button.sizePolicy().verticalPolicy())
            layout.addWidget(button, 1)

    def resizeEvent(self, event):
        """A new width can change the font the texts fit in."""
        super().resizeEvent(event)
        self.fit_text()

    def fit_text(self):
        """Give both halves the largest font, up to 14 px, that both texts
        fit in, so the two halves always read as one button."""
        sizes = []
        for button in self.buttons:
            room = button.width() - 6  # borders and a little air
            if room <= 0:
                return  # not laid out yet; resizeEvent comes back
            font = QFont(button.font())
            font.setBold(True)
            size = self.MAX_FONT_PX
            while size > self.MIN_FONT_PX:
                font.setPixelSize(size)
                if QFontMetrics(font).horizontalAdvance(button.text()) <= room:
                    break
                size -= 1
            sizes.append(size)
        size = min(sizes)
        for button in self.buttons:
            style = button.styleSheet()
            fitted = re.sub(r'font-size:\s*\d+px', 'font-size: {}px'.format(size), style)
            if fitted != style:
                button.setStyleSheet(fitted)


class LevelRow(QWidget):
    """A level's whole row: the button, centred, over the full-width line.

    The list's layout centres each item at its own width (layer buttons are
    a fixed 146 px), so the row would otherwise be only as wide as its
    button. It follows the list's visible width instead, through every
    resize of the layer panel and the scrollbar coming and going, and paints
    the line itself across that whole width."""

    def __init__(self, layer_panel, level, parent=None):
        """The row of *level* (1, 2, ...) in *layer_panel*'s list."""
        super().__init__(parent)
        self.layer_panel = layer_panel
        self.level = level
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(LEVEL_BUTTON_SIZE.height() + LEVEL_LINE_HEIGHT)

        self.button = LevelButton(self, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.button, 0, Qt.AlignHCenter)
        layout.addSpacing(LEVEL_LINE_HEIGHT)  # the line, painted in paintEvent

        viewport = self._viewport()
        if viewport is not None:
            viewport.installEventFilter(self)  # Qt drops it when this row is deleted
            self._fit_width(viewport.width())

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.show_menu(self.button.mapTo(self, pos)))

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

    def paintEvent(self, event):
        """The 4 px line under the button, from edge to edge."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(0, self.height() - LEVEL_LINE_HEIGHT, self.width(), LEVEL_LINE_HEIGHT, LEVEL_COLOR)
        painter.end()

    def text(self):
        """The row's name in the panel's language: "Level 1"..."""
        return self.layer_panel.level_name(self.level)

    def set_level(self, level):
        """Renumber the row (after a level below it was removed)."""
        self.level = level
        self.button.update()

    def _menu_theme(self):
        """The window's theme, for the menu's look (as the layer buttons do)."""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'current_theme'):
                return parent.current_theme
            parent = parent.parent()
        return 'default'

    def show_menu(self, pos):
        """Move up / Move down / Remove, styled like the layers' own menu.
        Move is greyed out where there is no strand to pass, and on the
        Masks tab."""
        panel = self.layer_panel
        menu = QMenu(self)
        try:
            from numbered_layer_button import build_menu_stylesheet
            menu.setStyleSheet(build_menu_stylesheet(self._menu_theme()))
        except Exception:
            pass  # keep Qt's own menu look
        if getattr(panel, 'language_code', None) == 'he':
            menu.setLayoutDirection(Qt.RightToLeft)
        up = menu.addAction(panel.level_text('level_move_up'))
        down = menu.addAction(panel.level_text('level_move_down'))
        menu.addSeparator()
        remove = menu.addAction(panel.level_text('level_remove'))
        up.setEnabled(panel.can_move_level(self.level, up=True))
        down.setEnabled(panel.can_move_level(self.level, up=False))
        chosen = menu.exec_(self.mapToGlobal(pos))
        if chosen is up:
            panel.move_level(self.level, up=True)
        elif chosen is down:
            panel.move_level(self.level, up=False)
        elif chosen is remove:
            panel.remove_level(self.level)
