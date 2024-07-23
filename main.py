import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject  # Included QRectF here
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QPainterPathStroker, QImage
from attach_mode import AttachMode, Strand, AttachedStrand, MaskedStrand
from move_mode import MoveMode
from layer_panel import LayerPanel

class StrandDrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 700)
        self.strands = []
        self.current_strand = None
        self.strand_width = 60
        self.strand_color = QColor('purple')
        self.stroke_color = Qt.black
        self.stroke_width = 5
        self.highlight_color = Qt.red
        self.highlight_width = 20
        self.is_first_strand = True
        self.attach_mode = AttachMode(self)
        self.attach_mode.strand_created.connect(self.on_strand_created)
        self.move_mode = MoveMode(self)
        self.current_mode = self.attach_mode
        self.selection_color = QColor(255, 0, 0, 128)
        self.selected_strand_index = None
        self.layer_panel = None
        self.selected_strand = None
        self.last_selected_strand_index = None
        self.strand_colors = {}
        self.grid_size = 30
        self.show_grid = True
        self.should_draw_names = False  # Initialize here to avoid AttributeError

    def set_layer_panel(self, layer_panel):
        self.layer_panel = layer_panel
        self.layer_panel.draw_names_requested.connect(self.toggle_name_drawing)

    def toggle_name_drawing(self, should_draw):
        self.should_draw_names = should_draw
        self.update()  # Redraw the canvas to reflect name drawing state

    def enable_name_drawing(self):
        self.should_draw_names = True
        self.update()  # Forces the canvas to redraw
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the grid
        if self.show_grid:
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            for x in range(0, self.width(), self.grid_size):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), self.grid_size):
                painter.drawLine(0, y, self.width(), y)

        # Draw each strand appropriately
        for strand in self.strands:
            if strand == self.selected_strand:
                self.draw_highlighted_strand(painter, strand)  # Draw with highlighting if selected
            else:
                strand.draw(painter)  # Normal draw call

            if self.should_draw_names:
                self.draw_strand_label(painter, strand)

        # Draw any currently manipulated strand
        if self.current_strand:
            self.current_strand.draw(painter)

        # Draw a rectangle around the move mode's selected rectangle if applicable
        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.setBrush(QBrush(self.selection_color))
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(self.current_mode.selected_rectangle)


    def draw_strand_label(self, painter, strand):
        # Use the layer_name attribute if it exists, otherwise fall back to a default
        text = getattr(strand, 'layer_name', f"{strand.set_number}_1")

        mid_point = (strand.start + strand.end) / 2
        font = painter.font()
        font.setPointSize(12)  # Adjust font size as needed
        painter.setFont(font)

        # Calculate text width and height to center it around the midpoint
        metrics = painter.fontMetrics()
        text_width = metrics.width(text)
        text_height = metrics.height()

        # Create a QRect centered around the midpoint for the text
        text_rect = QRectF(mid_point.x() - text_width / 2, mid_point.y() - text_height / 2, text_width, text_height)

        # Draw text as path for stroking
        text_path = QPainterPath()
        text_path.addText(text_rect.center().x() - text_width / 2, text_rect.center().y() + text_height / 4, font, text)

        # Draw the outline using a thicker white pen
        painter.setPen(QPen(Qt.white, 6, Qt.SolidLine))  # White outline
        painter.drawPath(text_path)

        # Draw the text with a thinner black pen
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Black text color
        painter.fillPath(text_path, QBrush(Qt.black))  # Fill the path with black color
        painter.drawPath(text_path)

    def draw_highlighted_strand(self, painter, strand):
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

    def update_color_for_set(self, set_number, color):
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
        for attached_strand in parent_strand.attached_strands:
            attached_strand.set_color(color)
            self.update_attached_strands_color(attached_strand, color)

    def on_color_changed(self, set_number, color):
        self.update_color_for_set(set_number, color)

    def select_strand(self, index):
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

    def on_strand_created(self, strand):
        # Determine the set number for the new strand
        if isinstance(strand, AttachedStrand):
            set_number = strand.parent.set_number
        elif self.selected_strand:
            set_number = self.selected_strand.set_number
        else:
            # If no strand is selected and it's a new strand, increment the set number
            set_number = max(self.strand_colors.keys(), default=0) + 1

        strand.set_number = set_number

        # Set color from existing set or default to a predefined color if not set
        if set_number not in self.strand_colors:
            self.strand_colors[set_number] = QColor('purple')
        strand.set_color(self.strand_colors[set_number])

        # Add strand to the canvas
        self.strands.append(strand)

        # Update or add the layer button in the layer panel
        if self.layer_panel:
            # This assumes there is a method in LayerPanel to handle the creation of new layer buttons
            self.layer_panel.add_layer_button(set_number)
            # Assuming LayerPanel emits a signal when the color changes which is connected back to the canvas
            self.layer_panel.on_color_changed(set_number, self.strand_colors[set_number])

        # Get the selected layer's index to assign the correct layer name
        selected_layer_index = self.layer_panel.get_selected_layer()
        if selected_layer_index is not None:
            layer_button = self.layer_panel.layer_buttons[selected_layer_index]
            strand.layer_name = layer_button.text()  # Ensure the strand gets the name from the UI

        # Select the strand in the interface if it's a primary strand and not an attached type
        if not isinstance(strand, AttachedStrand):
            self.select_strand(len(self.strands) - 1)

        # Trigger a canvas update to redraw all strands including the new one
        self.update()


    def add_strand(self, strand):
        # Add a new strand to the list of strands
        self.strands.append(strand)
        self.update()  # Redraw the canvas

    def select_strand(self, index):
        # Deselect all other strands
        for s in self.strands:
            s.is_selected = False
        # Select the new strand
        self.strands[index].is_selected = True
        self.selected_strand = self.strands[index]
        self.selected_strand_index = index
        self.update()  # Redraw the canvas




    def mousePressEvent(self, event):
        self.current_mode.mousePressEvent(event)
        self.update()

    def mouseMoveEvent(self, event):
        self.current_mode.mouseMoveEvent(event)
        self.update()

    def mouseReleaseEvent(self, event):
        self.current_mode.mouseReleaseEvent(event)
        self.update()



    def set_mode(self, mode):
        if mode == "attach":
            self.current_mode = self.attach_mode
            self.setCursor(Qt.ArrowCursor)
        elif mode == "move":
            self.current_mode = self.move_mode
            self.setCursor(Qt.OpenHandCursor)
        self.update()

    def remove_strand(self, strand):
        if strand in self.strands:
            self.strands.remove(strand)
            self.update()

    def clear_strands(self):
        self.strands.clear()
        self.current_strand = None
        self.is_first_strand = True
        self.selected_strand_index = None
        self.update()

    def snap_to_grid(self, point):
        return QPointF(
            round(point.x() / self.grid_size) * self.grid_size,
            round(point.y() / self.grid_size) * self.grid_size
        )

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strand Drawing Tool")
        self.setMinimumSize(900, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Sides Mode")
        self.toggle_grid_button = QPushButton("Toggle Grid")
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.toggle_grid_button)

        self.canvas = StrandDrawingCanvas()
        self.layer_panel = LayerPanel()

        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.layer_panel)

        self.splitter.setHandleWidth(0)
        main_layout.addWidget(self.splitter)

        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        left_widget.setMinimumWidth(200)
        self.layer_panel.setMinimumWidth(100)

        self.canvas.set_layer_panel(self.layer_panel)
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(lambda idx: self.select_strand(idx, emit_signal=False))
        self.layer_panel.deselect_all_requested.connect(self.deselect_all_strands)
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.layer_panel.color_changed.connect(self.handle_color_change)
        self.layer_panel.masked_layer_created.connect(self.create_masked_layer)

        self.current_mode = "attach"
        self.set_attach_mode()

    def handle_color_change(self, set_number, color):
        self.canvas.update_color_for_set(set_number, color)
        self.layer_panel.update_colors_for_set(set_number, color)

    def create_masked_layer(self, layer1_index, layer2_index):
        layer1 = self.canvas.strands[layer1_index]
        layer2 = self.canvas.strands[layer2_index]
        
        # Create MaskedStrand with layers in the order they were selected
        masked_strand = MaskedStrand(layer1, layer2)
        self.canvas.add_strand(masked_strand)
        
        button = self.layer_panel.add_masked_layer_button(layer1_index, layer2_index)
        button.color_changed.connect(self.handle_color_change)
        
        print(f"Created masked layer: {masked_strand.set_number}")
        
        self.canvas.update()
        self.update_mode(self.current_mode)

    def update_mode(self, mode):
        self.current_mode = mode
        self.canvas.set_mode(mode)
        if mode == "attach":
            self.attach_button.setEnabled(False)
            self.move_button.setEnabled(True)
        else:  # move mode
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(False)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.layer_panel.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.layer_panel.keyReleaseEvent(event)

    def set_attach_mode(self):
        self.update_mode("attach")
        if self.canvas.last_selected_strand_index is not None:
            self.select_strand(self.canvas.last_selected_strand_index)

    def set_move_mode(self):
        self.update_mode("move")
        self.canvas.last_selected_strand_index = self.canvas.selected_strand_index
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()

    def create_new_strand(self):
        new_strand = Strand(QPointF(100, 100), QPointF(200, 200), self.canvas.strand_width)
        new_strand.is_first_strand = True
        new_strand.is_start_side = True
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        new_strand.set_number = set_number
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor('purple')
        new_strand.set_color(self.canvas.strand_colors[set_number])
        
        # Set the layer name for the new strand
        new_strand.layer_name = f"{set_number}_1"
        
        self.canvas.add_strand(new_strand)
        self.layer_panel.add_layer_button(set_number)
        self.select_strand(len(self.canvas.strands) - 1)
        
        # Maintain the current mode
        self.update_mode(self.current_mode)
    def select_strand(self, index, emit_signal=True):
            if self.canvas.selected_strand_index != index:
                self.canvas.select_strand(index)
                if emit_signal:
                    self.layer_panel.select_layer(index, emit_signal=False)
            self.canvas.is_first_strand = False
            
            # Maintain the current mode when selecting a strand
            self.update_mode(self.current_mode)

    def deselect_all_strands(self):
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()
        
        # Maintain the current mode when deselecting all strands
        self.update_mode(self.current_mode)

    def start_resize(self, event):
        self.resize_start = event.pos()

    def do_resize(self, event):
        if hasattr(self, 'resize_start'):
            delta = event.pos().x() - self.resize_start.x()
            sizes = self.splitter.sizes()
            sizes[0] += delta
            sizes[1] -= delta
            self.splitter.setSizes(sizes)

    def stop_resize(self, event):
        if hasattr(self, 'resize_start'):
            del self.resize_start

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())