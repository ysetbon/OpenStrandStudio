from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject
import math

class Strand:
    def __init__(self, start, end, width, color=QColor('purple'), stroke_color=Qt.black, stroke_width=5):
        self.start = start
        self.end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.attached_strands = []
        self.has_circles = [False, False]
        self.is_first_strand = False
        self.is_start_side = True
        self.update_shape()
        self.update_side_line()
      
     
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

    def update_side_line(self):
        angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        perpendicular_angle = angle + 90
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

        for i, has_circle in enumerate(self.has_circles):
            if has_circle:
                circle_radius = self.width / 2
                center = self.start if i == 0 else self.end
                painter.setBrush(QBrush(self.color))
                painter.setPen(QPen(self.stroke_color, self.stroke_width))
                painter.drawEllipse(center, circle_radius, circle_radius)

        painter.setPen(QPen(self.stroke_color, self.stroke_width))
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.get_path())

        # Draw the purple side line only if it's not the start side of a first strand
        if not (self.is_first_strand and self.is_start_side):
            painter.setPen(QPen(QColor('purple'), self.stroke_width * 3))
            painter.drawLine(self.side_line_start, self.side_line_end)

        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)

        painter.restore()

    def move_side(self, side, new_pos):
        if side == 0:
            self.start = new_pos
        else:
            self.end = new_pos
        self.update_shape()
        self.update_side_line()
        for attached_strand in self.attached_strands:
            attached_strand.update_start(self.start if side == 0 else self.end)

class AttachedStrand(Strand):
    def __init__(self, parent, start_point):
        super().__init__(start_point, start_point, parent.width, parent.color, parent.stroke_color, parent.stroke_width)
        self.parent = parent
        self.angle = 0
        self.length = 140
        self.min_length = 40
        self.has_circles = [True, False]
        self.update_end()
        self.update_side_line()

    def update_start(self, new_start):
        delta = new_start - self.start
        self.start = new_start
        self.end += delta
        self.update_shape()
        self.update_side_line()

    def update(self, new_end):
        old_end = self.end
        self.end = new_end
        self.length = math.hypot(self.end.x() - self.start.x(), self.end.y() - self.start.y())
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        self.update_shape()
        self.update_side_line()
        # Update the parent's side line as well
        self.parent.update_side_line()
        # Update attached strands
        for attached in self.attached_strands:
            if attached.start == old_end:
                attached.update_start(self.end)

    def update_side_line(self):
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        perpendicular_angle = self.angle + 90
        perpendicular_dx = math.cos(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dy = math.sin(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dx_stroke = math.cos(math.radians(perpendicular_angle)) * self.stroke_width * 2
        perpendicular_dy_stroke = math.sin(math.radians(perpendicular_angle)) * self.stroke_width * 2
        
        self.side_line_start = QPointF(self.start.x() + perpendicular_dx - perpendicular_dx_stroke, 
                                       self.start.y() + perpendicular_dy - perpendicular_dy_stroke)
        self.side_line_end = QPointF(self.start.x() - perpendicular_dx + perpendicular_dx_stroke, 
                                     self.start.y() - perpendicular_dy + perpendicular_dy_stroke)

    def update_end(self):
        angle_rad = math.radians(self.angle)
        self.end = QPointF(
            self.start.x() + self.length * math.cos(angle_rad),
            self.start.y() + self.length * math.sin(angle_rad)
        )
        self.update_shape()

class AttachMode(QObject):
    strand_created = pyqtSignal(object)

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.is_attaching = False
        self.start_pos = None

    def mouseReleaseEvent(self, event):
        if self.canvas.is_first_strand:
            if self.canvas.current_strand and self.canvas.current_strand.start != self.canvas.current_strand.end:
                self.strand_created.emit(self.canvas.current_strand)
                self.canvas.is_first_strand = False
        else:
            if self.is_attaching and self.canvas.current_strand:
                self.strand_created.emit(self.canvas.current_strand)
            self.is_attaching = False
        self.canvas.current_strand = None

    def mousePressEvent(self, event):
        if self.canvas.is_first_strand:
            self.start_pos = event.pos()
            new_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width, 
                                self.canvas.strand_color, self.canvas.stroke_color, 
                                self.canvas.stroke_width)
            new_strand.is_first_strand = True
            self.canvas.current_strand = new_strand
        elif self.canvas.selected_strand and not self.is_attaching:
            self.handle_strand_attachment(event.pos())

    def handle_strand_attachment(self, pos):
        circle_radius = self.canvas.strand_width * 1.1

        if self.canvas.selected_strand:
            if self.try_attach_to_strand(self.canvas.selected_strand, pos, circle_radius):
                return
            if self.try_attach_to_attached_strands(self.canvas.selected_strand.attached_strands, pos, circle_radius):
                return

    def mouseMoveEvent(self, event):
        if self.canvas.is_first_strand and self.canvas.current_strand:
            end_pos = event.pos()
            self.update_first_strand(end_pos)
        elif self.is_attaching and self.canvas.current_strand:
            self.canvas.current_strand.update(event.pos())

    def update_first_strand(self, end_pos):
        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        
        angle = math.degrees(math.atan2(dy, dx))
        rounded_angle = round(angle / 5) * 5
        rounded_angle = rounded_angle % 360

        length = max(25, math.hypot(dx, dy))

        new_x = self.start_pos.x() + length * math.cos(math.radians(rounded_angle))
        new_y = self.start_pos.y() + length * math.sin(math.radians(rounded_angle))
        new_end = QPointF(new_x, new_y)

        self.canvas.current_strand.end = new_end
        self.canvas.current_strand.update_shape()
        self.canvas.current_strand.update_side_line()

    def try_attach_to_strand(self, strand, pos, circle_radius):
        distance_to_start = (pos - strand.start).manhattanLength()
        distance_to_end = (pos - strand.end).manhattanLength()

        start_attachable = distance_to_start <= circle_radius and not strand.has_circles[0]
        end_attachable = distance_to_end <= circle_radius and not strand.has_circles[1]

        if start_attachable:
            self.start_attachment(strand, strand.start, 0)
            return True
        elif end_attachable:
            self.start_attachment(strand, strand.end, 1)
            return True
        return False

    def start_attachment(self, parent_strand, attach_point, side):
        new_strand = AttachedStrand(parent_strand, attach_point)
        new_strand.is_first_strand = False  # Reset for attached strands
        new_strand.is_start_side = False    # Reset for attached strands
        parent_strand.attached_strands.append(new_strand)
        parent_strand.has_circles[side] = True  # Mark this side as attached
        self.canvas.current_strand = new_strand
        self.is_attaching = True

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        for attached_strand in attached_strands:
            if self.try_attach_to_strand(attached_strand, pos, circle_radius):
                return True

            if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, circle_radius):
                return True

        return False