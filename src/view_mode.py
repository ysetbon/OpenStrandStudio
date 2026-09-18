from PyQt5.QtCore import QObject, Qt


class ViewMode(QObject):
    """
    View Mode - A "look only" mode that allows camera navigation without any editing or selection actions.

    What you CAN do:
    - Pan camera - Left-click or right-click drag to move the view
    - Zoom - Scroll wheel to zoom in/out

    What you CANNOT do:
    - Select strands (clicking does nothing)
    """

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def activate(self):
        """Called when view mode is activated."""
        self.canvas.setCursor(Qt.OpenHandCursor)

    def deactivate(self):
        """Called when view mode is deactivated."""
        # Stop any temporary panning when leaving view mode.
        was_panning = (
            getattr(self.canvas, 'view_mode_panning', False)
            or getattr(self.canvas, 'right_button_panning', False)
        )
        if getattr(self.canvas, 'view_mode_panning', False):
            self.canvas.view_mode_panning = False
        if getattr(self.canvas, 'right_button_panning', False):
            self.canvas.right_button_panning = False
        if was_panning:
            self.canvas.pan_start_pos = None
            self.canvas.pan_start_offset = None
            # Discard saved cursor; the next mode's activation sets its own.
            self.canvas._pre_right_pan_cursor = None
            self.canvas._update_pan_button_icon(False)

    def mousePressEvent(self, event):
        """Temporary left/right panning is handled by the canvas."""
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
