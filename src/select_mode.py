from PyQt5.QtCore import QObject, pyqtSignal, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from render_utils import RenderUtils
from selection_utils import find_strands_at_point

class SelectMode(QObject):
    strand_selected = pyqtSignal(int)

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.hovered_strand = None  # Track strand being hovered for yellow highlight

    def activate(self):
        """Called when select mode is activated."""
        self.hovered_strand = None
        self.canvas.setCursor(Qt.PointingHandCursor)

    def deactivate(self):
        """Called when select mode is deactivated."""
        self.hovered_strand = None
        self.canvas.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        # Map the event position to the canvas coordinate system
        pos = event.pos()

        strands_at_point = self.find_strands_at_point(pos)

        # Deselect all strands before selecting a new one
        for strand in self.canvas.strands:
            strand.is_selected = False
            strand.start_selected = False
            strand.end_selected = False

        if len(strands_at_point) >= 1:
            selected_strand, selection_type = strands_at_point[0]
            selected_strand.is_selected = True  # Set the is_selected flag

            index = self.canvas.strands.index(selected_strand)
            self.strand_selected.emit(index)
        else:
            # Deselect if clicking on an empty area
            self.strand_selected.emit(-1)

        # Redraw the canvas to update the visual state
        self.canvas.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move to detect strand hovering and show hover highlight."""
        pos = event.pos()
        strands_at_point = self.find_strands_at_point(pos)

        old_hovered = self.hovered_strand

        if len(strands_at_point) >= 1:
            # Take the first strand found at this point
            self.hovered_strand = strands_at_point[0][0]
        else:
            self.hovered_strand = None

        # Only update if hover state changed
        if old_hovered != self.hovered_strand:
            self.canvas.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        pass

    def find_strands_at_point(self, pos):
        """Find strands at position - includes masked strands.

        Uses the shared hit-test (selection_utils) so the areas match the exact
        rendered geometry, topmost strand first. Skips hidden strands.
        """
        return find_strands_at_point(self.canvas.strands, pos, include_masked=True)

    def draw(self, painter):
        """Draw hover highlight for hovered strand."""
        # Check if hover highlights are enabled
        if not getattr(self.canvas, 'show_hover_highlights', True):
            return
        if self.hovered_strand:
            painter.save()
            try:
                RenderUtils.setup_painter(painter, enable_high_quality=True)

                strand = self.hovered_strand

                # Exact rendered footprint, same path used for hit-testing:
                # body + end circles / side lines for regular strands, and the
                # stroke+fill mask footprint for masked strands.
                highlight_path = strand.get_selection_path()

                # Yellow hover highlight (same as mask mode)
                hover_color = QColor(255, 230, 160, 170)
                painter.setBrush(hover_color)

                # Black border for visibility
                hover_pen = QPen(Qt.black, 2, Qt.SolidLine)
                hover_pen.setJoinStyle(Qt.MiterJoin)
                hover_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(hover_pen)

                # Draw the filled hover highlight path
                painter.drawPath(highlight_path)

            finally:
                painter.restore()

    def deselect_strand_recursively(self, strand):
        """Recursively deselect strand and its attached strands."""
        strand.is_selected = False
        strand.start_selected = False
        strand.end_selected = False
        if hasattr(strand, 'attached_strands'):
            for attached_strand in strand.attached_strands:
                self.deselect_strand_recursively(attached_strand)
