# Import necessary modules from PyQt5
from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QColorDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont, QPainterPath

class NumberedLayerButton(QPushButton):
    """
    A custom QPushButton subclass for representing numbered layers.
    Includes functionality for color changing and masked mode.
    """

    # Signal emitted when the button's color is changed
    color_changed = pyqtSignal(int, QColor)

    def __init__(self, text, count, color=QColor('purple'), parent=None):
        """
        Initialize the NumberedLayerButton.

        :param text: The text to display on the button
        :param count: The count or number associated with this layer
        :param color: The initial color of the button (default is purple)
        :param parent: The parent widget (default is None)
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
        self.set_color(color)

    def setText(self, text):
        """
        Set the text of the button and trigger a repaint.

        :param text: The new text for the button
        """
        self._text = text
        self.update()  # Trigger a repaint

    def text(self):
        """
        Get the text of the button.

        :return: The button's text
        """
        return self._text

    def set_color(self, color):
        """
        Set the color of the button and update its style.

        :param color: The new color for the button
        """
        self.color = color
        self.update_style()

    def set_border_color(self, color):
        """
        Set the border color of the button and update its style.

        :param color: The new border color
        """
        self.border_color = color
        self.update_style()

    def update_style(self):
        """
        Update the button's style based on its current color and border color.
        """
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
        self.setStyleSheet(style)

    def darken_color(self):
        """
        Darken the button's color for visual feedback.
        """
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.darker().name()};
                color: white;
                font-weight: bold;
            }}
        """)

    def restore_original_style(self):
        """
        Restore the button's original style.
        """
        self.update_style()

    def show_context_menu(self, pos):
        """
        Show a context menu when the button is right-clicked.

        :param pos: The position where the menu should be shown
        """
        context_menu = QMenu(self)
        change_color_action = QAction("Change Color", self)
        change_color_action.triggered.connect(self.change_color)
        context_menu.addAction(change_color_action)
        context_menu.exec_(self.mapToGlobal(pos))

    def change_color(self):
        """
        Open a color dialog to change the button's color.
        Emit a signal with the new color if changed.
        """
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color(color)
            self.color_changed.emit(int(self.text().split('_')[0]), color)

    def paintEvent(self, event):
        """
        Custom paint event to draw the button with a specific text style.

        :param event: The paint event
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(10)  # Set the font size to 10 points

        text = self._text
        rect = self.rect()

        # Calculate the center position for the text
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)  # Use horizontalAdvance for Qt5
        text_height = fm.height()
        x = (rect.width() - text_width) / 2
        y = (rect.height() + text_height) / 2 - fm.descent()

        # Create a path for the text
        path = QPainterPath()
        path.addText(x, y, font, text)

        # Draw the stroke (black outline)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Draw the text fill (white)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawPath(path)

    def set_masked_mode(self, masked):
        """
        Set the button to masked mode or restore its original style.

        :param masked: Boolean indicating whether to set masked mode
        """
        self.masked_mode = masked
        if masked:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: gray;
                    border: none;
                    font-weight: bold;
                }}
            """)
        else:
            self.restore_original_style()
        self.update()