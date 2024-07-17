import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtGui import QPainterPath, QPainterPathStroker
from attach_mode import AttachMode, Strand
from move_mode import MoveMode
from layer_panel import LayerPanel
from PyQt5.QtWidgets import QSplitter

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

    def set_layer_panel(self, layer_panel):
        self.layer_panel = layer_panel

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)

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
        # Save the current painter state to restore it later
        painter.save()
        # Enable antialiasing for smooth edges
        painter.setRenderHint(QPainter.Antialiasing)

        # Helper function to set up the highlight pen
        def set_highlight_pen(width_adjustment=0):
            # Create a pen with the highlight color and adjusted width
            pen = QPen(self.highlight_color, self.highlight_width + width_adjustment)
            # Set join style for sharp corners
            pen.setJoinStyle(Qt.MiterJoin)
            # Set cap style for sharp ends
            pen.setCapStyle(Qt.SquareCap)
            # Apply the pen to the painter
            painter.setPen(pen)

        # Set up and draw the highlight for the strand body
        set_highlight_pen()
        painter.drawPath(strand.get_path())

        # Set up a slightly thicker pen for the circles
        set_highlight_pen(0.5)
        # Draw highlights for the circles at the ends of the strand
        for i, has_circle in enumerate(strand.has_circles):
            if has_circle:
                # Determine the center point of the circle
                center = strand.start if i == 0 else strand.end
                # Draw the circle with radius equal to half the strand width
                painter.drawEllipse(center, strand.width / 2, strand.width / 2)

        # Restore the original painter state
        painter.restore()
        # Draw the strand normally (with its own styling)
        strand.draw(painter)

    def select_strand(self, index):
        if 0 <= index < len(self.strands):
            self.selected_strand = self.strands[index]
            self.selected_strand_index = index
            self.is_first_strand = False
            if self.layer_panel.get_selected_layer() != index:
                self.layer_panel.select_layer(index)
            self.current_mode = self.attach_mode
            self.current_mode.is_attaching = False
            self.current_strand = None
            self.update()
        else:
            self.selected_strand = None
            self.selected_strand_index = None



    def on_strand_created(self, strand):
        if strand not in self.strands:
            self.add_strand(strand)
            if self.layer_panel:
                if self.is_first_strand:
                    self.layer_panel.add_layer_button()
                    self.select_strand(0)
                    self.is_first_strand = False
                else:
                    self.layer_panel.add_layer_button()
                    self.select_strand(len(self.strands) - 1)


    def mousePressEvent(self, event):
        if self.is_first_strand or self.selected_strand:
            self.current_mode.mousePressEvent(event)
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_first_strand or (self.selected_strand and self.current_mode.is_attaching):
            self.current_mode.mouseMoveEvent(event)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_first_strand or (self.selected_strand and self.current_mode.is_attaching):
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strand Drawing Tool")
        self.setMinimumSize(900, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create buttons
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Sides Mode")
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)

        # Create canvas
        self.canvas = StrandDrawingCanvas()

        # Create layer panel
        self.layer_panel = LayerPanel()

        # Create splitter and add widgets
        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.layer_panel)

        # Hide the default splitter handle
        self.splitter.setHandleWidth(0)

        # Add splitter to main layout
        main_layout.addWidget(self.splitter)

        # Connect the custom handle to splitter movement
        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        # Set minimum sizes
        left_widget.setMinimumWidth(200)
        self.layer_panel.setMinimumWidth(100)
        # Connect signals
        self.canvas.set_layer_panel(self.layer_panel)
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(self.select_strand)
        self.layer_panel.deselect_all_requested.connect(self.deselect_all_strands)
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)

        self.set_attach_mode()
     
    def set_attach_mode(self):
        self.canvas.set_mode("attach")
        self.attach_button.setEnabled(False)
        self.move_button.setEnabled(True)

    def set_move_mode(self):
        self.canvas.set_mode("move")
        self.attach_button.setEnabled(True)
        self.move_button.setEnabled(False)

    def create_new_strand(self):
        new_strand = Strand(QPointF(100, 100), QPointF(200, 200), self.canvas.strand_width)
        self.canvas.add_strand(new_strand)
        self.layer_panel.start_new_set()
        self.layer_panel.add_layer_button()
        self.select_strand(len(self.canvas.strands) - 1)

    def select_strand(self, index):
        if self.canvas.selected_strand_index != index:
            self.canvas.select_strand(index)
            self.layer_panel.select_layer(index)
        self.canvas.is_first_strand = False
        self.set_attach_mode()
    def deselect_all_strands(self):
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()
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
