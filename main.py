import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QPainterPathStroker
from attach_mode import AttachMode, Strand, AttachedStrand
from move_mode import MoveMode
from layer_panel import LayerPanel

class StrandDrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 700)
        self.strands = []
        self.current_strand = None
        self.strand_width = 80
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
        self.grid_size = 15  # Size of each grid square in pixels

    def set_layer_panel(self, layer_panel):
        self.layer_panel = layer_panel
        self.layer_panel.color_changed.connect(self.on_color_changed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw grid
        painter.setPen(QPen(QColor(200, 200, 200), 1))  # Light gray color for grid
        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)

        for index, strand in enumerate(self.strands):
            if index == self.selected_strand_index:
                self.draw_highlighted_strand(painter, strand)
            else:
                strand.draw(painter)

        if self.current_strand:
            self.current_strand.draw(painter)

        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.setBrush(QBrush(self.selection_color))
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(self.current_mode.selected_rectangle)

    def draw_highlighted_strand(self, painter, strand):
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

    def on_color_changed(self, set_number, color):
        self.strand_colors[set_number] = color
        for strand in self.strands:
            if isinstance(strand, Strand) and strand.set_number == set_number:
                strand.set_color(color)
                self.update_attached_strands_color(strand, color)
        self.update()

    def update_attached_strands_color(self, parent_strand, color):
        for attached_strand in parent_strand.attached_strands:
            attached_strand.set_color(color)
            self.update_attached_strands_color(attached_strand, color)

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
        if strand not in self.strands:
            if isinstance(strand, AttachedStrand):
                # For attached strands, use the parent's set number
                set_number = strand.parent.set_number
            elif self.selected_strand:
                # For new strands in an existing set, use the selected strand's set number
                set_number = self.selected_strand.set_number
            else:
                # For new strands in a new set, use the next set number
                set_number = max(self.strand_colors.keys(), default=0) + 1

            strand.set_number = set_number
            
            if set_number not in self.strand_colors:
                self.strand_colors[set_number] = QColor('purple')
            
            strand.set_color(self.strand_colors[set_number])
            self.add_strand(strand)
            
            if self.layer_panel:
                self.layer_panel.add_layer_button(set_number)
                self.layer_panel.on_color_changed(set_number, self.strand_colors[set_number])
            
            if not isinstance(strand, AttachedStrand):
                self.select_strand(len(self.strands) - 1)

    def mousePressEvent(self, event):
        self.current_mode.mousePressEvent(event)
        self.update()

    def mouseMoveEvent(self, event):
        self.current_mode.mouseMoveEvent(event)
        self.update()

    def mouseReleaseEvent(self, event):
        self.current_mode.mouseReleaseEvent(event)
        self.update()

    def add_strand(self, strand):
        self.strands.append(strand)
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
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)

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
        self.layer_panel.color_changed.connect(self.canvas.on_color_changed)

        self.current_mode = "attach"
        self.set_attach_mode()

    def set_attach_mode(self):
        self.canvas.set_mode("attach")
        self.attach_button.setEnabled(False)
        self.move_button.setEnabled(True)
        self.current_mode = "attach"
        if self.canvas.last_selected_strand_index is not None:
            self.select_strand(self.canvas.last_selected_strand_index)

    def set_move_mode(self):
        self.canvas.set_mode("move")
        self.attach_button.setEnabled(True)
        self.move_button.setEnabled(False)
        self.current_mode = "move"
        self.canvas.last_selected_strand_index = self.canvas.selected_strand_index
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()

    def create_new_strand(self):
        new_strand = Strand(QPointF(100, 100), QPointF(200, 200), self.canvas.strand_width)
        new_strand.is_first_strand = True
        new_strand.is_start_side = True
        
        # Always create a new set number for a new strand
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        new_strand.set_number = set_number
        
        # Set the color for the new strand
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor('purple')
        new_strand.set_color(self.canvas.strand_colors[set_number])
        
        self.canvas.add_strand(new_strand)
        self.layer_panel.add_layer_button(set_number)
        self.select_strand(len(self.canvas.strands) - 1)
        
        if self.current_mode == "move":
            self.set_move_mode()
        else:
            self.set_attach_mode()
            
    def select_strand(self, index, emit_signal=True):
        if self.canvas.selected_strand_index != index:
            self.canvas.select_strand(index)
            if emit_signal:
                self.layer_panel.select_layer(index, emit_signal=False)
        self.canvas.is_first_strand = False

    def deselect_all_strands(self):
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()
        if self.current_mode == "move":
            self.set_move_mode()
        else:
            self.set_attach_mode()

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