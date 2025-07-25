# Import necessary modules from PyQt5
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from render_utils import RenderUtils
import logging

class SplitterHandle(QWidget):
    """
    A custom widget that serves as a handle for resizing split views.
    """

    def __init__(self, parent=None):
        """
        Initialize the SplitterHandle.

        :param parent: The parent widget (default is None)
        """
        super().__init__(parent)
        self.setFixedHeight(10)  # Set a fixed height for the handle
        self.setCursor(Qt.SplitHCursor)  # Set the cursor to a horizontal split cursor

        # Override the parent's resize event if a parent is provided
        if parent:
            parent.resizeEvent = self.parentResizeEvent

    def paintEvent(self, event):
        """
        Handle the paint event to draw the splitter handle.

        :param event: The paint event
        """
        painter = QPainter(self)
        logging.info(f"[SplitterHandle.paintEvent] Setting up UI painter for splitter handle")
        RenderUtils.setup_ui_painter(painter)
        # Make the handle fully transparent - no visual rectangle
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # Fully transparent
        painter.end()

    def updateSize(self):
        """
        Update the size and position of the handle to match the parent widget.
        """
        if self.parent():
            self.setFixedWidth(self.parent().width())  # Match width with parent
            self.move(0, 0)  # Ensure the handle is at the top-left corner
            self.update()  # Force a repaint

    def parentResizeEvent(self, event):
        """
        Handle the resize event of the parent widget.

        :param event: The resize event
        """
        self.updateSize()  # Update the handle's size when parent is resized

        # Call the original resizeEvent of the parent if it exists
        original_resize = getattr(type(self.parent()), 'resizeEvent', None)
        if original_resize:
            original_resize(self.parent(), event)

    def resizeEvent(self, event):
        """
        Handle the resize event of the splitter handle.

        :param event: The resize event
        """
        self.updateSize()  # Update size when the handle itself is resized
        super().resizeEvent(event)  # Call the parent class's resizeEvent

    def mousePressEvent(self, event):
        """
        Handle mouse press events on the splitter handle.

        :param event: The mouse event
        """
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.SplitHCursor)  # Set cursor to split cursor on left-click

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events on the splitter handle.

        :param event: The mouse event
        """
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.SplitHCursor)  # Ensure cursor is split cursor after release

    def enterEvent(self, event):
        """
        Handle mouse enter events for the splitter handle.

        :param event: The event object
        """
        self.setCursor(Qt.SplitHCursor)  # Set cursor to split cursor when mouse enters

    def leaveEvent(self, event):
        """
        Handle mouse leave events for the splitter handle.

        :param event: The event object
        """
        self.unsetCursor()  # Reset the cursor when mouse leaves the handle