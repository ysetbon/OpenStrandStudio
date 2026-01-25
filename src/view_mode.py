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
        # Stop any active view mode panning when leaving view mode
        if hasattr(self.canvas, 'view_mode_panning') and self.canvas.view_mode_panning:
            self.canvas.view_mode_panning = False
            self.canvas.pan_start_pos = None
            self.canvas.pan_start_offset = None
            self.canvas._update_pan_button_for_view_mode(False)

    def mousePressEvent(self, event):
        """Handle mouse press - right-click panning is handled by canvas."""
        # Left click does nothing in view mode (no selection)
        pass

    def mouseMoveEvent(self, event):
        """Handle mouse move - panning is handled by canvas."""
        pass

    def mouseReleaseEvent(self, event):
        """Handle mouse release - panning is handled by canvas."""
        pass

    def draw(self, painter):
        """Draw method - nothing to draw in view mode."""
        pass
