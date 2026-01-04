from PyQt5.QtCore import QObject, pyqtSignal, QPointF, Qt
from PyQt5.QtGui import QColor, QPainterPathStroker, QPen
from render_utils import RenderUtils
from masked_strand import MaskedStrand

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

        Checks strands in reverse order so topmost strands (drawn last) are found first.
        Skips hidden strands.
        """
        results = []
        # Reverse order so topmost strands are checked first
        for strand in reversed(self.canvas.strands):
            # Skip hidden strands
            if getattr(strand, 'is_hidden', False):
                continue

            # For MaskedStrand, check the actual mask path
            if isinstance(strand, MaskedStrand):
                # Use get_mask_path() which returns the actual visible mask shape
                mask_path = strand.get_mask_path()
                if mask_path.contains(pos):
                    results.append((strand, 'strand'))
            else:
                # Regular strand detection
                contains_start = strand.get_start_selection_path().contains(pos)
                contains_end = strand.get_end_selection_path().contains(pos)
                if contains_start:
                    results.append((strand, 'start'))
                elif contains_end:
                    results.append((strand, 'end'))
                elif strand.get_selection_path().contains(pos):
                    results.append((strand, 'strand'))
        return results

    def draw(self, painter):
        """Draw hover highlight for hovered strand."""
        if self.hovered_strand:
            painter.save()
            RenderUtils.setup_painter(painter, enable_high_quality=True)

            strand = self.hovered_strand

            # For MaskedStrand, use the actual mask path
            if isinstance(strand, MaskedStrand):
                # get_mask_path() returns the actual visible mask shape
                highlight_path = strand.get_mask_path()
            else:
                # For regular strands, create a stroked path
                path = strand.get_path()
                stroke_stroker = QPainterPathStroker()
                stroke_stroker.setWidth(strand.width + strand.stroke_width * 2)
                stroke_stroker.setJoinStyle(Qt.MiterJoin)
                stroke_stroker.setCapStyle(Qt.FlatCap)
                highlight_path = stroke_stroker.createStroke(path)

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

            painter.restore()

    def deselect_strand_recursively(self, strand):
        """Recursively deselect strand and its attached strands."""
        strand.is_selected = False
        strand.start_selected = False
        strand.end_selected = False
        if hasattr(strand, 'attached_strands'):
            for attached_strand in strand.attached_strands:
                self.deselect_strand_recursively(attached_strand)
