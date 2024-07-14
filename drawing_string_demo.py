import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QColorDialog
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QRectF
import math

class Strand:
    def __init__(self, start, end, width, color, stroke_color=Qt.black, stroke_width=2):
        self.start = start
        self.end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.attached_strand = None
        self.has_circle = False
        self.update_shape()

    def update_shape(self):
        angle = math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x())
        perpendicular = angle + math.pi / 2
        half_width = self.width / 2
        dx = half_width * math.cos(perpendicular)
        dy = half_width * math.sin(perpendicular)
        self.top_left = QPointF(self.start.x() + dx, self.start.y() + dy)
        self.bottom_left = QPointF(self.start.x() - dx, self.start.y() - dy)
        self.top_right = QPointF(self.end.x() + dx, self.end.y() + dy)
        self.bottom_right = QPointF(self.end.x() - dx, self.end.y() - dy)

    def get_path(self):
        path = QPainterPath()
        path.moveTo(self.top_left)
        path.lineTo(self.top_right)
        path.lineTo(self.bottom_right)
        path.lineTo(self.bottom_left)
        path.closeSubpath()
        return path

    def draw(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.stroke_color, self.stroke_width))
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.get_path())

        if self.has_circle:
            # Draw circle at the end
            circle_radius = self.width / 2
            painter.drawEllipse(self.end, circle_radius, circle_radius)

        if self.attached_strand:
            self.attached_strand.draw(painter)

        painter.restore()

class AttachedStrand:
    def __init__(self, parent, width, color, stroke_color=Qt.black, stroke_width=2):
        self.parent = parent
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.angle = 0
        self.length = 140
        self.min_length = 40

    def update(self, mouse_pos):
        dx = mouse_pos.x() - self.parent.end.x()
        dy = mouse_pos.y() - self.parent.end.y()
        self.angle = math.degrees(math.atan2(dy, dx))
        self.length = max(self.min_length, math.hypot(dx, dy))
        
        # Round angle and length to nearest 10
        self.angle = round(self.angle / 10) * 10
        self.length = round(self.length / 10) * 10

    def draw(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Translate to the end of the parent strand
        painter.translate(self.parent.end)
        
        # Rotate
        painter.rotate(self.angle)
        
        # Draw the rectangle
        rect = QRectF(0, -self.width/2, self.length, self.width)
        painter.setPen(QPen(self.stroke_color, self.stroke_width))
        painter.setBrush(QBrush(self.color))
        painter.drawRect(rect)
        
        # Draw the purple line on the side
        painter.setPen(QPen(self.color, self.stroke_width * 2))
        painter.drawLine(QPointF(0, -self.width/2 +self.stroke_width*2-1), QPointF(0, self.width/2 -self.stroke_width*2+1))
        
        painter.restore()

class StrandDrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 700)
        self.strands = []
        self.current_strand = None
        self.strand_width = 80
        self.strand_color = QColor('purple')
        self.stroke_color = Qt.black
        self.stroke_width = 2
        self.is_attaching = False
        self.is_first_strand = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)  # Background

        for strand in self.strands:
            strand.draw(painter)

        if self.current_strand:
            self.current_strand.draw(painter)

    def mousePressEvent(self, event):
        if self.is_first_strand:
            self.current_strand = Strand(event.pos(), event.pos(), self.strand_width, self.strand_color, self.stroke_color, self.stroke_width)
        elif not self.is_attaching:
            self.strands[0].has_circle = True
            self.current_strand = AttachedStrand(self.strands[0], self.strand_width, self.strand_color, self.stroke_color, self.stroke_width)
            self.strands[0].attached_strand = self.current_strand
            self.is_attaching = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_first_strand and self.current_strand:
            self.current_strand.end = event.pos()
            self.current_strand.update_shape()
        elif self.is_attaching and self.current_strand:
            self.current_strand.update(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if self.is_first_strand:
            self.strands.append(self.current_strand)
            self.current_strand = None
            self.is_first_strand = False
        else:
            self.is_attaching = False
            self.current_strand = None
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strand Drawing Tool")
        self.setMinimumSize(720, 720)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.canvas = StrandDrawingCanvas()
        layout.addWidget(self.canvas)

        controls_layout = QHBoxLayout()
        color_button = QPushButton("Change Color")
        color_button.clicked.connect(self.change_color)
        controls_layout.addWidget(color_button)
        layout.addLayout(controls_layout)

    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.strand_color = color
            self.canvas.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())