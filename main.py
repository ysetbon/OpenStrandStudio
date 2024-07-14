import sys
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF

from attach_mode import AttachMode, Strand, AttachedStrand
from move_mode import MoveMode
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QPolygonF

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
        self.is_first_strand = True
        self.attach_mode = AttachMode(self)
        self.move_mode = MoveMode(self)
        self.current_mode = self.attach_mode
        self.selection_color = QColor(255, 0, 0, 128)  # Semi-transparent red

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)

        for strand in self.strands:
            strand.draw(painter)
            self.draw_attached_strands(painter, strand.attached_strands)

        if self.current_strand:
            self.current_strand.draw(painter)

        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.setBrush(QBrush(self.selection_color))
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(self.current_mode.selected_rectangle)

    def draw_attached_strands(self, painter, attached_strands):
        for strand in attached_strands:
            strand.draw(painter)
            self.draw_attached_strands(painter, strand.attached_strands)

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

    def add_strand(self, strand):
        self.strands.append(strand)
        self.update()

    def remove_strand(self, strand):
        if strand in self.strands:
            self.strands.remove(strand)
            self.update()

    def clear_strands(self):
        self.strands.clear()
        self.current_strand = None
        self.is_first_strand = True
        self.update()

    def get_strand_at_position(self, pos):
        for strand in reversed(self.strands):  # Check from top to bottom
            if strand.contains(pos):
                return strand
            attached_strand = self.get_attached_strand_at_position(strand.attached_strands, pos)
            if attached_strand:
                return attached_strand
        return None

    def get_attached_strand_at_position(self, attached_strands, pos):
        for strand in reversed(attached_strands):
            if strand.contains(pos):
                return strand
            sub_attached = self.get_attached_strand_at_position(strand.attached_strands, pos)
            if sub_attached:
                return sub_attached
        return None

    def set_strand_width(self, width):
        self.strand_width = width
        self.update()

    def set_strand_color(self, color):
        self.strand_color = color
        self.update()

    def set_stroke_color(self, color):
        self.stroke_color = color
        self.update()

    def set_stroke_width(self, width):
        self.stroke_width = width
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strand Drawing Tool")
        self.setMinimumSize(720, 720)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create buttons
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Sides Mode")
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)

        # Connect buttons to mode changes
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)

        main_layout.addLayout(button_layout)

        self.canvas = StrandDrawingCanvas()
        main_layout.addWidget(self.canvas)

        # Set initial mode
        self.set_attach_mode()

    def set_attach_mode(self):
        self.canvas.set_mode("attach")
        self.attach_button.setEnabled(False)
        self.move_button.setEnabled(True)

    def set_move_mode(self):
        self.canvas.set_mode("move")
        self.attach_button.setEnabled(True)
        self.move_button.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())