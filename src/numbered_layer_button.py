from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QColorDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont, QPainterPath, QIcon

class NumberedLayerButton(QPushButton):
    # Signal emitted when the button's color is changed
    color_changed = pyqtSignal(int, QColor)

    def __init__(self, text, count, color=QColor('purple'), parent=None):
        """
        Initialize the NumberedLayerButton.

        Args:
            text (str): The text to display on the button.
            count (int): The count or number associated with this layer.
            color (QColor): The initial color of the button (default is purple).
            parent (QWidget): The parent widget (default is None).
        """
        super().__init__(parent)
        self._text = text  # Store the text privately
        self.count = count
        self.setFixedSize(100, 30)  # Set fixed size for the button
        self.setCheckable(True)  # Make the button checkable (can be toggled)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.color = color
        self.border_color = None
        self.masked_mode = False
        self.locked = False
        self.selectable = False
        self.set_color(color)

    def setText(self, text):
        """
        Set the text of the button and trigger a repaint.

        Args:
            text (str): The new text for the button.
        """
        self._text = text
        self.update()  # Trigger a repaint

    def text(self):
        """
        Get the text of the button.

        Returns:
            str: The button's text.
        """
        return self._text

    def set_color(self, color):
        """
        Set the color of the button and update its style.

        Args:
            color (QColor): The new color for the button.
        """
        self.color = color
        self.update_style()

    def set_border_color(self, color):
        """
        Set the border color of the button and update its style.

        Args:
            color (QColor): The new border color.
        """
        self.border_color = color
        self.update_style()

    def set_locked(self, locked):
        """
        Set the locked state of the button.

        Args:
            locked (bool): Whether the button should be locked.
        """
        self.locked = locked
        self.update()

    def set_selectable(self, selectable):
        """
        Set the selectable state of the button.

        Args:
            selectable (bool): Whether the button should be selectable.
        """
        self.selectable = selectable
        self.update_style()

    def update_style(self):
        """Update the button's style based on its current state."""
        style = f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.color.lighter().name()};
            }}
            QPushButton:checked {{
                background-color: {self.color.darker().name()};
            }}
        """
        if self.border_color:
            style += f"""
                QPushButton {{
                    border: 2px solid {self.border_color.name()};
                }}
            """
        if self.selectable:
            style += """
                QPushButton {
                    border: 2px solid blue;
                }
            """
        self.setStyleSheet(style)

    def paintEvent(self, event):
        """
        Custom paint event to draw the button with centered text and an orange lock icon if needed.

        Args:
            event (QPaintEvent): The paint event.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set up the font
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        # Get the button's rectangle
        rect = self.rect()

        # Calculate text position
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        text_height = fm.height()
        x = (rect.width() - text_width) / 2
        y = (rect.height() + text_height) / 2 - fm.descent()

        # Create text path
        path = QPainterPath()
        path.addText(x, y, font, self._text)

        # Draw text outline
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Fill text
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawPath(path)

        # Draw orange lock icon if locked
        if self.locked:
            lock_icon = QIcon.fromTheme("lock")
            if not lock_icon.isNull():
                painter.save()
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.fillRect(rect.adjusted(5, 5, -5, -5), QColor(255, 165, 0, 200))  # Semi-transparent orange
                lock_icon.paint(painter, rect.adjusted(5, 5, -5, -5))
                painter.restore()
            else:
                painter.setPen(QColor(255, 165, 0))  # Orange color
                painter.drawText(rect, Qt.AlignCenter, "🔒")

    def show_context_menu(self, pos):
        """
        Show a context menu when the button is right-clicked.

        Args:
            pos (QPoint): The position where the menu should be shown.
        """
        context_menu = QMenu(self)
        change_color_action = QAction("Change Color", self)
        change_color_action.triggered.connect(self.change_color)
        context_menu.addAction(change_color_action)
        context_menu.exec_(self.mapToGlobal(pos))

    def change_color(self):
        """Open a color dialog to change the button's color."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color(color)
            # Extract the set number from the button's text
            set_number = int(self.text().split('_')[0])
            self.color_changed.emit(set_number, color)

    def set_masked_mode(self, masked):
        """
        Set the button to masked mode or restore its original style.

        Args:
            masked (bool): Whether to set masked mode.
        """
        self.masked_mode = masked
        if masked:
            self.setStyleSheet("""
                QPushButton {
                    background-color: gray;
                    border: none;
                    font-weight: bold;
                }
            """)
        else:
            self.update_style()
        self.update()

    def darken_color(self):
        """Darken the button's color for visual feedback."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.darker().name()};
                color: white;
                font-weight: bold;
            }}
        """)

    def restore_original_style(self):
        """Restore the button's original style."""
        self.update_style()