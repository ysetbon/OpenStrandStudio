import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                             QColorDialog)
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPointF
import math

class Strand:
    def __init__(self, start, end, width, color, stroke_color=Qt.black, stroke_width=4):
        self.start = start
        self.end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.selected = False
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

    def erase_section(self, erase_path):
        self.erase_path = erase_path

    def draw(self, painter, erase_path=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        strand_path = self.get_path()
        if erase_path:
            strand_path = strand_path.subtracted(erase_path)
        if hasattr(self, 'erase_path'):
            strand_path = strand_path.subtracted(self.erase_path)

        # Draw the main strand
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color)))
        painter.drawPath(strand_path)

        # Draw the stroke
        if self.stroke_width > 0:
            painter.setPen(QPen(self.stroke_color, self.stroke_width))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(strand_path)

        # Draw selection highlight
        if self.selected:
            highlight_pen = QPen(QColor('red'))
            highlight_pen.setWidth(4)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(strand_path)

        painter.restore()

    def length(self):
        return math.sqrt((self.end.x() - self.start.x())**2 + (self.end.y() - self.start.y())**2)

    def contains_point(self, point):
        return self.get_path().contains(point)

class StrandDrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.strands = []
        self.current_strand = None
        self.strand_width = 30
        self.strand_color = QColor('purple')
        self.stroke_color = Qt.black
        self.stroke_width = 4
        self.selected_strand = None
        self.appending_strand = False
        self.append_start_point = None
        self.lasso_mode = False
        self.lasso_points = []
        self.current_mode = "draw"  # Modes: "draw", "lasso"
        self.current_mouse_pos = QPointF()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw white background
        painter.fillRect(self.rect(), Qt.white)

        # Draw border
        border_pen = QPen(Qt.black)
        border_pen.setWidth(2)
        painter.setPen(border_pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # Draw existing strands
        for i, strand in enumerate(self.strands):
            erase_path = QPainterPath()
            for other_strand in self.strands[i+1:]:
                erase_path.addPath(other_strand.get_path())
            strand.draw(painter, erase_path)

        # Draw current strand being created
        if self.current_strand:
            self.current_strand.draw(painter)

        # Draw lasso polygon
        if self.lasso_mode and self.lasso_points:
            lasso_path = QPainterPath()
            lasso_path.moveTo(self.lasso_points[0])
            
            for point in self.lasso_points[1:]:
                lasso_path.lineTo(point)
            
            if len(self.lasso_points) >= 3:
                # Close the path for 3 or more points
                lasso_path.lineTo(self.current_mouse_pos)
                lasso_path.closeSubpath()
                
                # Draw filled semi-transparent polygon
                painter.setBrush(QColor(128, 128, 128, 128))  # Semi-transparent gray
                painter.setPen(Qt.NoPen)
                painter.drawPath(lasso_path)
            
            # Draw the outline with dashed line
            painter.setBrush(Qt.NoBrush)
            dash_pen = QPen(Qt.black, 1, Qt.DashLine)  # Create a dashed line pen
            painter.setPen(dash_pen)
            painter.drawPath(lasso_path)
            
            # Always draw the line to the current mouse position
            painter.drawLine(self.lasso_points[-1], self.current_mouse_pos)

    def mousePressEvent(self, event):
        if self.current_mode == "lasso":
            self.lasso_points.append(event.pos())
            self.update()
        elif self.current_mode == "draw":
            if event.button() == Qt.LeftButton:
                nearest_endpoint = self.find_nearest_endpoint(event.pos())
                if nearest_endpoint:
                    self.appending_strand = True
                    self.append_start_point = nearest_endpoint
                    self.current_strand = Strand(nearest_endpoint, event.pos(), self.strand_width, 
                                                 self.strand_color, self.stroke_color, self.stroke_width)
                else:
                    self.current_strand = Strand(event.pos(), event.pos(), self.strand_width, 
                                                 self.strand_color, self.stroke_color, self.stroke_width)

    def mouseMoveEvent(self, event):
        self.current_mouse_pos = event.pos()
        if self.current_mode == "lasso":
            self.update()
        elif self.current_mode == "draw" and self.current_strand:
            self.current_strand.end = event.pos()
            self.current_strand.update_shape()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.current_mode == "draw" and event.button() == Qt.LeftButton and self.current_strand:
            if self.current_strand.length() > 0:
                self.strands.append(self.current_strand)
            self.current_strand = None
            self.appending_strand = False
            self.append_start_point = None
            self.update()

    def find_nearest_endpoint(self, pos):
        min_distance = float('inf')
        nearest_endpoint = None
        for strand in self.strands:
            for endpoint in [strand.start, strand.end]:
                distance = (pos - endpoint).manhattanLength()
                if distance < min_distance and distance < 20:  # 20 pixels threshold
                    min_distance = distance
                    nearest_endpoint = endpoint
        return nearest_endpoint

    def set_strand_width(self, width):
        self.strand_width = width

    def set_strand_color(self, color):
        self.strand_color = color

    def set_stroke_color(self, color):
        self.stroke_color = color

    def set_stroke_width(self, width):
        self.stroke_width = width

    def undo(self):
        if self.strands:
            self.strands.pop()
            self.selected_strand = None
            self.update()

    def make_vertical(self):
        if self.selected_strand:
            length = round(self.selected_strand.length())
            if self.selected_strand.end.y() >= self.selected_strand.start.y():
                self.selected_strand.end = QPointF(self.selected_strand.start.x(), 
                                                   self.selected_strand.start.y() + length)
            else:
                self.selected_strand.end = QPointF(self.selected_strand.start.x(), 
                                                   self.selected_strand.start.y() - length)
            self.selected_strand.update_shape()
            self.update()

    def make_horizontal(self):
        if self.selected_strand:
            length = round(self.selected_strand.length())
            if self.selected_strand.end.x() >= self.selected_strand.start.x():
                self.selected_strand.end = QPointF(self.selected_strand.start.x() + length, 
                                                   self.selected_strand.start.y())
            else:
                self.selected_strand.end = QPointF(self.selected_strand.start.x() - length, 
                                                   self.selected_strand.start.y())
            self.selected_strand.update_shape()
            self.update()

    def start_lasso_mode(self):
        self.current_mode = "lasso"
        self.lasso_points = []
        self.setCursor(Qt.CrossCursor)

    def apply_lasso(self):
        if self.lasso_points and len(self.lasso_points) > 2:
            lasso_path = QPainterPath()
            lasso_path.moveTo(self.lasso_points[0])
            for point in self.lasso_points[1:]:
                lasso_path.lineTo(point)
            lasso_path.closeSubpath()

            for strand in self.strands:
                strand.erase_section(lasso_path)

            self.lasso_points = []
            self.current_mode = "draw"
            self.setCursor(Qt.ArrowCursor)
            self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strand Drawing Tool")
        self.setMinimumSize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.canvas = StrandDrawingCanvas()
        layout.addWidget(self.canvas)

        controls_layout = QHBoxLayout()
        
        width_label = QLabel("Strand Width:")
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 50)
        self.width_spinbox.setValue(30)
        self.width_spinbox.valueChanged.connect(self.canvas.set_strand_width)
        
        color_button = QPushButton("Change Color")
        color_button.clicked.connect(self.change_color)

        stroke_color_button = QPushButton("Change Stroke Color")
        stroke_color_button.clicked.connect(self.change_stroke_color)

        stroke_width_label = QLabel("Stroke Width:")
        self.stroke_width_spinbox = QSpinBox()
        self.stroke_width_spinbox.setRange(0, 10)
        self.stroke_width_spinbox.setValue(4)
        self.stroke_width_spinbox.valueChanged.connect(self.canvas.set_stroke_width)

        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.canvas.undo)
        
        vertical_button = QPushButton("Make Vertical")
        vertical_button.clicked.connect(self.canvas.make_vertical)
        
        horizontal_button = QPushButton("Make Horizontal")
        horizontal_button.clicked.connect(self.canvas.make_horizontal)

        lasso_button = QPushButton("Polygon Lasso")
        lasso_button.clicked.connect(self.canvas.start_lasso_mode)

        apply_lasso_button = QPushButton("Apply Lasso")
        apply_lasso_button.clicked.connect(self.canvas.apply_lasso)

        controls_layout.addWidget(width_label)
        controls_layout.addWidget(self.width_spinbox)
        controls_layout.addWidget(color_button)
        controls_layout.addWidget(stroke_color_button)
        controls_layout.addWidget(stroke_width_label)
        controls_layout.addWidget(self.stroke_width_spinbox)
        controls_layout.addWidget(undo_button)
        controls_layout.addWidget(vertical_button)
        controls_layout.addWidget(horizontal_button)
        controls_layout.addWidget(lasso_button)
        controls_layout.addWidget(apply_lasso_button)

        layout.addLayout(controls_layout)

    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_strand_color(color)

    def change_stroke_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_stroke_color(color)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
