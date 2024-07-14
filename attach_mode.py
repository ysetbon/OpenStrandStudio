# attach_mode.py

from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPointF
import math

class Strand:
    def __init__(self, start, end, width, color=QColor('purple'), stroke_color=Qt.black, stroke_width=2):
        self.start = start
        self.end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.attached_strands = []
        self.has_circles = [False, False]  # [start_circle, end_circle]
        self.circles_available = [True, True]  # [start_circle_available, end_circle_available]
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

        for i, has_circle in enumerate(self.has_circles):
            if has_circle:
                circle_radius = self.width / 2
                center = self.start if i == 0 else self.end
                painter.setBrush(QBrush(self.color if self.circles_available[i] else QColor('purple')))
                painter.drawEllipse(center, circle_radius, circle_radius)

        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)

        painter.restore()

    def move_side(self, side, new_pos):
        if side == 0:
            self.start = new_pos
        else:
            self.end = new_pos
        self.update_shape()
        for attached_strand in self.attached_strands:
            attached_strand.update_start(self.start if side == 0 else self.end)

class AttachedStrand:
    def __init__(self, parent, start_point):
        self.parent = parent
        self.width = parent.width
        self.color = parent.color
        self.stroke_color = parent.stroke_color
        self.stroke_width = parent.stroke_width
        self.angle = 0
        self.length = 140
        self.min_length = 40
        self.start = start_point
        self.end = self.calculate_end()
        self.attached_strands = []
        self.has_circle = False
        self.circle_available = True
        self.update_side_line()

    def update(self, mouse_pos):
        dx = mouse_pos.x() - self.start.x()
        dy = mouse_pos.y() - self.start.y()
        self.angle = math.degrees(math.atan2(dy, dx))
        self.length = max(self.min_length, math.hypot(dx, dy))
        
        self.angle = round(self.angle / 10) * 10
        self.length = round(self.length / 10) * 10
        self.end = self.calculate_end()
        self.update_side_line()

    def calculate_end(self):
        angle_rad = math.radians(self.angle)
        return QPointF(
            self.start.x() + self.length * math.cos(angle_rad),
            self.start.y() + self.length * math.sin(angle_rad)
        )

    def update_side_line(self):
        perpendicular_angle = self.angle + 90
        perpendicular_dx = math.cos(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dy = math.sin(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dx_stroke = math.cos(math.radians(perpendicular_angle)) * self.stroke_width * 2
        perpendicular_dy_stroke = math.sin(math.radians(perpendicular_angle)) * self.stroke_width * 2
        
        self.side_line_start = QPointF(self.start.x() + perpendicular_dx - perpendicular_dx_stroke, 
                                       self.start.y() + perpendicular_dy - perpendicular_dy_stroke)
        self.side_line_end = QPointF(self.start.x() - perpendicular_dx + perpendicular_dx_stroke, 
                                     self.start.y() - perpendicular_dy + perpendicular_dy_stroke)

    def draw(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the main strand
        path = QPainterPath()
      
        angle = math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x())
        perpendicular = angle + math.pi / 2
        half_width = self.width / 2
        dx = half_width * math.cos(perpendicular)
        dy = half_width * math.sin(perpendicular)
        top_start = QPointF(self.start.x() + dx, self.start.y() + dy)
        bottom_start = QPointF(self.start.x() - dx, self.start.y() - dy)
        top_end = QPointF(self.end.x() + dx, self.end.y() + dy)
        bottom_end = QPointF(self.end.x() - dx, self.end.y() - dy)
        path.moveTo(top_start)
        path.lineTo(top_end)
        path.lineTo(bottom_end)
        path.lineTo(bottom_start)
        path.closeSubpath()
        
        painter.setPen(QPen(self.stroke_color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(self.color))
        painter.drawPath(path)
        
        # Draw the colored line on the side
        painter.setPen(QPen(QColor('purple'), self.stroke_width * 3))
        painter.drawLine(self.side_line_start, self.side_line_end)

        if self.has_circle:
            # Draw circle at the end
            circle_radius = self.width / 2
            painter.setPen(QPen(self.stroke_color, self.stroke_width))
            painter.setBrush(QBrush(self.color if self.circle_available else QColor('purple')))
            painter.drawEllipse(self.end, circle_radius, circle_radius)

        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)
        
        painter.restore()

    def get_end_point(self):
        return self.end

    def move_end(self, new_end):
        self.end = new_end
        self.length = (self.end - self.start).manhattanLength()
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        self.update_side_line()

    def update_start(self, new_start):
        delta = new_start - self.start
        self.start = new_start
        self.length = (self.end - self.start).manhattanLength()
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        self.update_side_line()

class AttachMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.is_attaching = False

    def mousePressEvent(self, event):
        if self.canvas.is_first_strand:
            self.canvas.current_strand = Strand(event.pos(), event.pos(), self.canvas.strand_width, self.canvas.strand_color, self.canvas.stroke_color, self.canvas.stroke_width)
        elif not self.is_attaching:
            self.handle_strand_attachment(event.pos())

    def mouseMoveEvent(self, event):
        if self.canvas.is_first_strand and self.canvas.current_strand:
            self.canvas.current_strand.end = event.pos()
            self.canvas.current_strand.update_shape()
        elif self.is_attaching and self.canvas.current_strand:
            self.canvas.current_strand.update(event.pos())

    def mouseReleaseEvent(self, event):
        if self.canvas.is_first_strand:
            self.canvas.strands.append(self.canvas.current_strand)
            self.canvas.current_strand = None
            self.canvas.is_first_strand = False
        else:
            self.is_attaching = False
            self.canvas.current_strand = None

    def handle_strand_attachment(self, pos):
        circle_radius = self.canvas.strand_width / 2

        for strand in self.canvas.strands:
            if self.try_attach_to_strand(strand, pos, circle_radius):
                return
            if self.try_attach_to_attached_strands(strand.attached_strands, pos, circle_radius):
                return

    def try_attach_to_strand(self, strand, pos, circle_radius):
        distance_to_start = (pos - strand.start).manhattanLength()
        distance_to_end = (pos - strand.end).manhattanLength()

        if distance_to_start <= circle_radius and strand.circles_available[0]:
            strand.has_circles[0] = True
            strand.circles_available[0] = False
            self.canvas.current_strand = AttachedStrand(strand, strand.start)
            strand.attached_strands.append(self.canvas.current_strand)
            self.is_attaching = True
            return True
        elif distance_to_end <= circle_radius and strand.circles_available[1]:
            strand.has_circles[1] = True
            strand.circles_available[1] = False
            self.canvas.current_strand = AttachedStrand(strand, strand.end)
            strand.attached_strands.append(self.canvas.current_strand)
            self.is_attaching = True
            return True
        return False

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        for attached_strand in attached_strands:
            end_point = attached_strand.get_end_point()
            distance_to_end = (pos - end_point).manhattanLength()

            if distance_to_end <= circle_radius and attached_strand.circle_available:
                attached_strand.has_circle = True
                attached_strand.circle_available = False
                new_attached_strand = AttachedStrand(attached_strand, end_point)
                attached_strand.attached_strands.append(new_attached_strand)
                self.canvas.current_strand = new_attached_strand
                self.is_attaching = True
                return True

            if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, circle_radius):
                return True

        return False