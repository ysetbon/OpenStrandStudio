# Import necessary modules from PyQt5
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QFont, QFontMetrics, QImage

# Import custom modes and strand classes
from attach_mode import AttachMode
from move_mode import MoveMode
from strand import Strand, AttachedStrand, MaskedStrand

class StrandDrawingCanvas(QWidget):
    def __init__(self, parent=None):
        """Initialize the StrandDrawingCanvas."""
        super().__init__(parent)
        self.setMinimumSize(700, 700)  # Set minimum size for the canvas
        self.initialize_properties()
        self.setup_modes()

    def initialize_properties(self):
        """Initialize all properties used in the StrandDrawingCanvas."""
        self.strands = []  # List to store all strands
        self.current_strand = None  # Currently active strand
        self.strand_width = 55  # Width of strands
        self.strand_color = QColor('purple')  # Default color for strands
        self.stroke_color = Qt.black  # Color for strand outlines
        self.stroke_width = 5  # Width of strand outlines
        self.highlight_color = Qt.red  # Color for highlighting selected strands
        self.highlight_width = 20  # Width of highlight
        self.is_first_strand = True  # Flag to indicate if it's the first strand being drawn
        self.selection_color = QColor(255, 0, 0, 128)  # Color for selection rectangle
        self.selected_strand_index = None  # Index of the currently selected strand
        self.layer_panel = None  # Reference to the layer panel
        self.selected_strand = None  # Currently selected strand
        self.last_selected_strand_index = None  # Index of the last selected strand
        self.strand_colors = {}  # Dictionary to store colors for each strand set
        self.grid_size = 30  # Size of grid cells
        self.show_grid = True  # Flag to show/hide grid
        self.should_draw_names = False  # Flag to show/hide strand names

    def setup_modes(self):
        """Set up attach and move modes."""
        self.attach_mode = AttachMode(self)
        self.attach_mode.strand_created.connect(self.on_strand_created)
        self.move_mode = MoveMode(self)
        self.current_mode = self.attach_mode  # Set initial mode to attach

    def paintEvent(self, event):
        """Handle paint events to draw the canvas contents."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.show_grid:
            self.draw_grid(painter)

        for strand in self.strands:
            if strand == self.selected_strand:
                self.draw_highlighted_strand(painter, strand)
            else:
                strand.draw(painter)

            if self.should_draw_names:
                self.draw_strand_label(painter, strand)

        if self.current_strand:
            self.current_strand.draw(painter)

        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.setBrush(QBrush(self.selection_color))
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(self.current_mode.selected_rectangle)

    def draw_grid(self, painter):
        """Draw the grid on the canvas."""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)

    def draw_strand_label(self, painter, strand):
        """Draw the label for a strand."""
        text = getattr(strand, 'layer_name', f"{strand.set_number}_1")
        mid_point = (strand.start + strand.end) / 2
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        text_width = metrics.width(text)
        text_height = metrics.height()

        text_rect = QRectF(mid_point.x() - text_width / 2, mid_point.y() - text_height / 2, text_width, text_height)

        text_path = QPainterPath()
        text_path.addText(text_rect.center().x() - text_width / 2, text_rect.center().y() + text_height / 4, font, text)

        painter.setPen(QPen(Qt.white, 6, Qt.SolidLine))
        painter.drawPath(text_path)

        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.fillPath(text_path, QBrush(Qt.black))
        painter.drawPath(text_path)

    def draw_highlighted_strand(self, painter, strand):
        """Draw a highlighted version of a strand."""
        if isinstance(strand, MaskedStrand):
            self.draw_highlighted_masked_strand(painter, strand)
        else:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            def set_highlight_pen(width_adjustment=0):
                pen = QPen(self.highlight_color, self.highlight_width + width_adjustment)
                pen.setJoinStyle(Qt.MiterJoin)
                pen.setCapStyle(Qt.SquareCap)
                painter.setPen(pen)

            set_highlight_pen()
            painter.drawPath(strand.get_path())

            set_highlight_pen(0.5)
            for i, has_circle in enumerate(strand.has_circles):
                if has_circle:
                    center = strand.start if i == 0 else strand.end
                    painter.drawEllipse(center, strand.width / 2, strand.width / 2)

            painter.restore()
            strand.draw(painter)

    def draw_highlighted_masked_strand(self, painter, masked_strand):
        """Draw a highlighted version of a masked strand."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        masked_strand.draw(temp_painter)

        highlight_pen = QPen(self.highlight_color, self.stroke_width+4)
        highlight_pen.setJoinStyle(Qt.MiterJoin)
        highlight_pen.setCapStyle(Qt.SquareCap)
        temp_painter.setPen(highlight_pen)
        temp_painter.drawPath(masked_strand.get_mask_path())

        temp_painter.end()

        painter.drawImage(0, 0, temp_image)

        painter.restore()

    def set_layer_panel(self, layer_panel):
        """Set the layer panel and connect signals."""
        self.layer_panel = layer_panel
        self.layer_panel.draw_names_requested.connect(self.toggle_name_drawing)

    def toggle_name_drawing(self, should_draw):
        """Toggle the drawing of strand names."""
        self.should_draw_names = should_draw
        self.update()

    def enable_name_drawing(self):
        """Enable the drawing of strand names."""
        self.should_draw_names = True
        self.update()

    def deselect_all_strands(self):
        """Deselect all strands."""
        self.selected_strand = None
        self.selected_strand_index = None
        self.update()

    def update_color_for_set(self, set_number, color):
        """Update the color for a set of strands."""
        self.strand_colors[set_number] = color
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                if strand.set_number.startswith(f"{set_number}_"):
                    strand.set_color(color)
                    self.update_attached_strands_color(strand, color)
            elif isinstance(strand, Strand) and strand.set_number == set_number:
                strand.set_color(color)
                self.update_attached_strands_color(strand, color)
        self.update()

    def update_attached_strands_color(self, parent_strand, color):
        """Recursively update the color of attached strands."""
        for attached_strand in parent_strand.attached_strands:
            attached_strand.set_color(color)
            self.update_attached_strands_color(attached_strand, color)

    def on_strand_created(self, strand):
        """Handle the creation of a new strand."""
        if isinstance(strand, AttachedStrand):
            set_number = strand.parent.set_number
        elif self.selected_strand:
            set_number = self.selected_strand.set_number
        else:
            set_number = max(self.strand_colors.keys(), default=0) + 1

        strand.set_number = set_number

        if set_number not in self.strand_colors:
            self.strand_colors[set_number] = QColor('purple')
        strand.set_color(self.strand_colors[set_number])

        self.strands.append(strand)

        if self.layer_panel:
            set_number = strand.set_number
            count = len([s for s in self.strands if s.set_number == set_number])
            strand.layer_name = f"{set_number}_{count}"
            self.layer_panel.add_layer_button(set_number)
            self.layer_panel.on_color_changed(set_number, self.strand_colors[set_number])

        if not isinstance(strand, AttachedStrand):
            self.select_strand(len(self.strands) - 1)
        
        self.update()
        
        # Notify LayerPanel that a new strand was added
        if self.layer_panel:
            self.layer_panel.update_attachable_states()

    def attach_strand(self, parent_strand, new_strand):
        """Attach a new strand to a parent strand."""
        parent_strand.attached_strands.append(new_strand)
        new_strand.parent = parent_strand
        self.strands.append(new_strand)
        
        # Notify LayerPanel that a strand was attached
        if self.layer_panel:
            self.layer_panel.on_strand_attached()

    def add_strand(self, strand):
        """Add a strand to the canvas."""
        self.strands.append(strand)
        self.update()

    def select_strand(self, index):
        """Select a strand by index."""
        if 0 <= index < len(self.strands):
            self.selected_strand = self.strands[index]
            self.selected_strand_index = index
            self.last_selected_strand_index = index
            self.is_first_strand = False
            if self.layer_panel and self.layer_panel.get_selected_layer() != index:
                self.layer_panel.select_layer(index, emit_signal=False)
            self.current_mode = self.attach_mode
            self.current_mode.is_attaching = False
            self.current_strand = None
            self.update()
        else:
            self.selected_strand = None
            self.selected_strand_index = None

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        self.current_mode.mousePressEvent(event)
        self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        self.current_mode.mouseMoveEvent(event)
        self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        self.current_mode.mouseReleaseEvent(event)
        self.update()

    def set_mode(self, mode):
        """Set the current mode (attach or move)."""
        if mode == "attach":
            self.current_mode = self.attach_mode
            self.setCursor(Qt.ArrowCursor)
        elif mode == "move":
            self.current_mode = self.move_mode
            self.setCursor(Qt.OpenHandCursor)
        self.update()

    def remove_strand(self, strand):
        """Remove a strand from the canvas."""
        if strand in self.strands:
            self.strands.remove(strand)
            self.update()

    def clear_strands(self):
        """Clear all strands from the canvas."""
        self.strands.clear()
        self.current_strand = None
        self.is_first_strand = True
        self.selected_strand_index = None
        self.update()

    def snap_to_grid(self, point):
        """Snap a point to the nearest grid intersection."""
        return QPointF(
            round(point.x() / self.grid_size) * self.grid_size,
            round(point.y() / self.grid_size) * self.grid_size
        )

    def toggle_grid(self):
        """Toggle the visibility of the grid."""
        self.show_grid = not self.show_grid
        self.update()