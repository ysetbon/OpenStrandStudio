import sys
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QPolygonF

from attach_mode import AttachMode, Strand, AttachedStrand
from move_mode import MoveMode

# Main canvas class for drawing strands
class StrandDrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 700)  # Set minimum size for the canvas
        self.strands = []  # List to store all strands
        self.current_strand = None  # Currently active strand
        self.strand_width = 80  # Default width of strands
        self.strand_color = QColor('purple')  # Default color of strands
        self.stroke_color = Qt.black  # Default color of strand outline
        self.stroke_width = 5  # Default width of strand outline
        self.is_first_strand = True  # Flag to check if it's the first strand being drawn
        self.attach_mode = AttachMode(self)  # Instance of AttachMode
        self.move_mode = MoveMode(self)  # Instance of MoveMode
        self.current_mode = self.attach_mode  # Set default mode to attach
        self.selection_color = QColor(255, 0, 0, 128)  # Semi-transparent red for selection

    # Override paintEvent to draw strands
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smoother drawing
        painter.fillRect(self.rect(), Qt.white)  # Fill background with white

        # Draw all existing strands
        for strand in self.strands:
            strand.draw(painter)
            self.draw_attached_strands(painter, strand.attached_strands)

        # Draw the current strand being created/modified
        if self.current_strand:
            self.current_strand.draw(painter)

        # Draw selection rectangle in move mode
        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.setBrush(QBrush(self.selection_color))
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(self.current_mode.selected_rectangle)

    # Recursive function to draw attached strands
    def draw_attached_strands(self, painter, attached_strands):
        for strand in attached_strands:
            strand.draw(painter)
            self.draw_attached_strands(painter, strand.attached_strands)

    # Handle mouse press events
    def mousePressEvent(self, event):
        self.current_mode.mousePressEvent(event)
        self.update()

    # Handle mouse move events
    def mouseMoveEvent(self, event):
        self.current_mode.mouseMoveEvent(event)
        self.update()

    # Handle mouse release events
    def mouseReleaseEvent(self, event):
        self.current_mode.mouseReleaseEvent(event)
        self.update()

    # Set the current mode (attach or move)
    def set_mode(self, mode):
        if mode == "attach":
            self.current_mode = self.attach_mode
            self.setCursor(Qt.ArrowCursor)
        elif mode == "move":
            self.current_mode = self.move_mode
            self.setCursor(Qt.OpenHandCursor)

    # Add a new strand to the canvas
    def add_strand(self, strand):
        self.strands.append(strand)
        self.update()

    # Remove a strand from the canvas
    def remove_strand(self, strand):
        if strand in self.strands:
            self.strands.remove(strand)
            self.update()

    # Clear all strands from the canvas
    def clear_strands(self):
        self.strands.clear()
        self.current_strand = None
        self.is_first_strand = True
        self.update()

    # Get the strand at a specific position
    def get_strand_at_position(self, pos):
        for strand in reversed(self.strands):  # Check from top to bottom
            if strand.contains(pos):
                return strand
            attached_strand = self.get_attached_strand_at_position(strand.attached_strands, pos)
            if attached_strand:
                return attached_strand
        return None

    # Recursive function to get attached strand at a position
    def get_attached_strand_at_position(self, attached_strands, pos):
        for strand in reversed(attached_strands):
            if strand.contains(pos):
                return strand
            sub_attached = self.get_attached_strand_at_position(strand.attached_strands, pos)
            if sub_attached:
                return sub_attached
        return None

    # Set the width of strands
    def set_strand_width(self, width):
        self.strand_width = width
        self.update()

    # Set the color of strands
    def set_strand_color(self, color):
        self.strand_color = color
        self.update()

    # Set the color of strand outlines
    def set_stroke_color(self, color):
        self.stroke_color = color
        self.update()

    # Set the width of strand outlines
    def set_stroke_width(self, width):
        self.stroke_width = width
        self.update()

# Main application window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strand Drawing Tool")
        self.setMinimumSize(720, 720)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create buttons for mode selection
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Sides Mode")
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)

        # Connect buttons to mode changes
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)

        main_layout.addLayout(button_layout)

        # Create and add the drawing canvas
        self.canvas = StrandDrawingCanvas()
        main_layout.addWidget(self.canvas)

        # Set initial mode to attach
        self.set_attach_mode()

    # Set the mode to attach
    def set_attach_mode(self):
        self.canvas.set_mode("attach")
        self.attach_button.setEnabled(False)
        self.move_button.setEnabled(True)

    # Set the mode to move
    def set_move_mode(self):
        self.canvas.set_mode("move")
        self.attach_button.setEnabled(True)
        self.move_button.setEnabled(False)

# Main entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())