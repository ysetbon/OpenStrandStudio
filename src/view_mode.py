from PyQt5.QtCore import QObject, Qt


class ViewMode(QObject):
    """
    View Mode - A "look only" mode that allows camera navigation without any editing or selection actions.

    What you CAN do:
    - Pan camera - Right-click drag to move the view
    - Zoom - Scroll wheel to zoom in/out

    What you CANNOT do:
    - Select strands (clicking does nothing)
    """

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def activate(self):
        """Called when view mode is activated."""
        self.canvas.setCursor(Qt.ArrowCursor)

    def deactivate(self):
        """Called when view mode is deactivated."""
        pass

    def mousePressEvent(self, event):
        """Handle mouse press - do nothing in view mode (no selection)."""
        # Intentionally do nothing - view mode doesn't allow selection
        pass

    def mouseMoveEvent(self, event):
        """Handle mouse move - do nothing in view mode (no hover effects)."""
        # Intentionally do nothing - view mode doesn't show hover effects
        pass

    def mouseReleaseEvent(self, event):
        """Handle mouse release - do nothing in view mode."""
        pass

    def draw(self, painter):
        """Draw method - nothing to draw in view mode."""
        pass
