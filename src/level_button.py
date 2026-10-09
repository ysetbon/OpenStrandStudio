"""The Level layer: one row of the layer panel that marks a storey in the stack.

A level row looks like a layer button, as wide as one and a third lower
(146 x 27 against 146 x 40), named "Level 1", "Level 2" and so on, with a
4 px line under it that runs the whole width of the list. It sits at the
bottom of the layers it carries. Layers below the lowest level row are on the
ground and have no row.

Right-click opens Move up / Move down / Remove; dragging the row moves it
like any layer (LayerPanel.dropEvent turns the new position into levels).
"""

from PyQt5.QtCore import QMimeData, QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QDrag, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication, QMenu, QPushButton, QSizePolicy, QVBoxLayout, QWidget

# Same width as NumberedLayerButton, a third less tall (40 -> 27).
LEVEL_BUTTON_SIZE = QSize(146, 27)
LEVEL_LINE_HEIGHT = 4
LEVEL_COLOR = QColor("#7a63b8")
LEVEL_COLOR_HOVER = QColor("#8b76c6")


class LevelButton(QPushButton):
    """The purple 146 x 27 button of a level row."""

    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.setFixedSize(LEVEL_BUTTON_SIZE)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self._drag_start_position = None
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            f"QPushButton {{ background-color: {LEVEL_COLOR.name()}; border: none; }}"
            f"QPushButton:hover {{ background-color: {LEVEL_COLOR_HOVER.name()}; }}"
        )

    def paintEvent(self, event):
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
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_position = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
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


class LevelRow(QWidget):
    """A level's whole row: the button, centred, over the full-width line."""

    def __init__(self, layer_panel, level, parent=None):
        super().__init__(parent)
        self.layer_panel = layer_panel
        self.level = level
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(LEVEL_BUTTON_SIZE.height() + LEVEL_LINE_HEIGHT)

        self.button = LevelButton(self, self)
        self.line = QWidget(self)
        self.line.setFixedHeight(LEVEL_LINE_HEIGHT)
        self.line.setStyleSheet(f"background-color: {LEVEL_COLOR.name()};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.button, 0, Qt.AlignHCenter)
        layout.addWidget(self.line)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.show_menu(self.button.mapTo(self, pos)))

    def text(self):
        return self.layer_panel.level_name(self.level)

    def set_level(self, level):
        self.level = level
        self.button.update()

    def show_menu(self, pos):
        panel = self.layer_panel
        menu = QMenu(self)
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
