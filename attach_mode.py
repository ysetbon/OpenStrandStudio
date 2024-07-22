from PyQt5.QtCore import QPointF, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QCursor, QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtWidgets import QWidget
import math
from PyQt5.QtGui import QPainterPath, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import QPointF

class Strand:
    def __init__(self, start, end, width, color=QColor('purple'), stroke_color=QColor(0, 0, 0), stroke_width=5):
        self.start = start
        self.end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.side_line_color = QColor('purple')
        self.attached_strands = []
        self.has_circles = [False, False]
        self.is_first_strand = False
        self.is_start_side = True
        self.set_number = None
        self.update_shape()
        self.update_side_line()

    def set_color(self, new_color):
        self.color = new_color
        self.side_line_color = new_color

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

        if not (self.is_first_strand and self.is_start_side):
            painter.setPen(QPen(self.side_line_color, self.stroke_width * 3))
            painter.drawLine(self.side_line_start, self.side_line_end)

        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)

        painter.restore()

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
        self.parent.update_side_line()
        for attached in self.attached_strands:
            if attached.start == old_end:
                attached.update_start(self.end)

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
        self.current_end = None
        self.target_pos = None
        self.last_snapped_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)
        self.move_speed = 1  # Grid units per step

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
        self.move_timer.stop()
        self.start_pos = None
        self.current_end = None
        self.target_pos = None
        self.last_snapped_pos = None
        self.accumulated_delta = QPointF(0, 0)

    def mousePressEvent(self, event):
        if self.canvas.is_first_strand:
            self.start_pos = self.canvas.snap_to_grid(event.pos())
            new_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width, 
                                self.canvas.strand_color, self.canvas.stroke_color, 
                                self.canvas.stroke_width)
            new_strand.is_first_strand = True
            self.canvas.current_strand = new_strand
            self.current_end = self.start_pos
            self.last_snapped_pos = self.start_pos
        elif self.canvas.selected_strand and not self.is_attaching:
            self.handle_strand_attachment(event.pos())

    def mouseMoveEvent(self, event):
        if self.canvas.is_first_strand and self.canvas.current_strand:
            self.target_pos = self.canvas.snap_to_grid(event.pos())
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS
        elif self.is_attaching and self.canvas.current_strand:
            self.target_pos = self.canvas.snap_to_grid(event.pos())
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS

    def gradual_move(self):
        if not self.target_pos or not self.last_snapped_pos:
            self.move_timer.stop()
            return

        dx = self.target_pos.x() - self.last_snapped_pos.x()
        dy = self.target_pos.y() - self.last_snapped_pos.y()

        step_x = min(abs(dx), self.move_speed * self.canvas.grid_size) * (1 if dx > 0 else -1)
        step_y = min(abs(dy), self.move_speed * self.canvas.grid_size) * (1 if dy > 0 else -1)

        new_x = self.last_snapped_pos.x() + step_x
        new_y = self.last_snapped_pos.y() + step_y

        new_pos = self.canvas.snap_to_grid(QPointF(new_x, new_y))

        if new_pos != self.last_snapped_pos:
            self.update_strand_position(new_pos)
            self.update_cursor_position(new_pos)
            self.last_snapped_pos = new_pos

        if new_pos == self.target_pos:
            self.move_timer.stop()

    def update_strand_position(self, new_pos):
        if self.canvas.is_first_strand:
            self.update_first_strand(new_pos)
        elif self.is_attaching:
            self.canvas.current_strand.update(new_pos)
        self.canvas.update()

    def update_first_strand(self, end_pos):
        if not self.canvas.current_strand:
            return

        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        
        angle = math.degrees(math.atan2(dy, dx))
        rounded_angle = round(angle / 45) * 45
        rounded_angle = rounded_angle % 360

        length = max(self.canvas.grid_size, math.hypot(dx, dy))

        new_x = self.start_pos.x() + length * math.cos(math.radians(rounded_angle))
        new_y = self.start_pos.y() + length * math.sin(math.radians(rounded_angle))
        new_end = self.canvas.snap_to_grid(QPointF(new_x, new_y))

        self.canvas.current_strand.end = new_end
        self.canvas.current_strand.update_shape()
        self.canvas.current_strand.update_side_line()

    def update_cursor_position(self, pos):
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        global_pos = self.canvas.mapToGlobal(pos)
        QCursor.setPos(global_pos)

    def handle_strand_attachment(self, pos):
        circle_radius = self.canvas.strand_width * 1.1

        if self.canvas.selected_strand:
            if not isinstance(self.canvas.selected_strand, MaskedStrand):
                if self.try_attach_to_strand(self.canvas.selected_strand, pos, circle_radius):
                    return
                if self.try_attach_to_attached_strands(self.canvas.selected_strand.attached_strands, pos, circle_radius):
                    return
            else:
                print("Cannot attach to a masked strand layer.")

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
        new_strand.set_color(parent_strand.color)
        new_strand.set_number = parent_strand.set_number
        new_strand.is_first_strand = False
        new_strand.is_start_side = False
        parent_strand.attached_strands.append(new_strand)
        parent_strand.has_circles[side] = True
        self.canvas.current_strand = new_strand
        self.is_attaching = True
        self.last_snapped_pos = self.canvas.snap_to_grid(attach_point)
        self.target_pos = self.last_snapped_pos

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        for attached_strand in attached_strands:
            if self.try_attach_to_strand(attached_strand, pos, circle_radius):
                return True
            if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, circle_radius):
                return True
        return False

from PyQt5.QtGui import QPainterPath, QPainter, QColor, QPen, QBrush, QPainterPathStroker, QImage
from PyQt5.QtCore import QPointF, Qt, QRectF, QSize
class MaskedStrand(Strand):
    def __init__(self, first_selected_strand, second_selected_strand):
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        super().__init__(first_selected_strand.start, first_selected_strand.end, first_selected_strand.width)
        self.set_number = f"{first_selected_strand.set_number}_{second_selected_strand.set_number}"
        self.color = first_selected_strand.color
        self.stroke_color = first_selected_strand.stroke_color
        self.stroke_width = first_selected_strand.stroke_width
        self.update_shape()

    def update_shape(self):
        print("Updating shape")
        self.start = self.first_selected_strand.start
        self.end = self.first_selected_strand.end
        super().update_shape()

    def get_mask_path(self):
        path1 = QPainterPath(self.first_selected_strand.get_path())
        stroker1 = QPainterPathStroker()
        stroker1.setWidth(self.first_selected_strand.stroke_width)
        path1 = stroker1.createStroke(path1).united(path1)

        path2 = QPainterPath(self.second_selected_strand.get_path())
        stroker2 = QPainterPathStroker()
        stroker2.setWidth(self.second_selected_strand.stroke_width * 2)
        path2 = stroker2.createStroke(path2).united(path2)

        return path1.intersected(path2)


    def draw(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        def get_set_numbers(strand):
            if isinstance(strand.set_number, str):
                return [int(n) for n in strand.set_number.split('_')]
            return [strand.set_number]

        set_numbers1 = get_set_numbers(self.first_selected_strand)
        set_numbers2 = get_set_numbers(self.second_selected_strand)
        
        print(f"First selected strand set number: {self.first_selected_strand.set_number}")
        print(f"Second selected strand set number: {self.second_selected_strand.set_number}")
        print(f"Set numbers1: {set_numbers1}")
        print(f"Set numbers2: {set_numbers2}")
        
        if set_numbers1[0] == set_numbers2[0]:
            print(f"Shared first number. Expected to draw first strand.")
            strand_to_draw = self.first_selected_strand
        else:
            print(f"Different first number. Expected to draw second strand.")
            strand_to_draw = self.first_selected_strand

        print(f"Strand to draw set number: {strand_to_draw.set_number}")
        # Draw the stroke line
        temp_painter.setPen(QPen(strand_to_draw.stroke_color, strand_to_draw.width+strand_to_draw.stroke_width))
        temp_painter.drawLine(strand_to_draw.start, strand_to_draw.end)
        # Draw a simple line for testing purposes
        
        temp_painter.setPen(QPen(QBrush(strand_to_draw.color), strand_to_draw.width-strand_to_draw.stroke_width))
        temp_painter.drawLine(strand_to_draw.start, strand_to_draw.end)
       

        mask_path = self.get_mask_path()
        inverse_path = QPainterPath()
        inverse_path.addRect(QRectF(temp_image.rect()))
        inverse_path = inverse_path.subtracted(mask_path)

        temp_painter.setCompositionMode(QPainter.CompositionMode_Clear)
        temp_painter.setBrush(Qt.transparent)
        temp_painter.setPen(Qt.NoPen)
        temp_painter.drawPath(inverse_path)

        temp_painter.end()
        painter.drawImage(0, 0, temp_image)
        painter.restore()

        # Additional debug print statement
        print(f"Drawing masked strand: {self.set_number}, drawn strand: {strand_to_draw}")


    def update(self, new_end):
        self.first_selected_strand.update(new_end)
        self.second_selected_strand.update(new_end)
        self.update_shape()

    def set_color(self, new_color):
        self.color = new_color
        self.first_selected_strand.set_color(new_color)

    # Override these methods to ensure they use the intersected path
    def get_top_left(self):
        return self.get_mask_path().boundingRect().topLeft()

    def get_bottom_right(self):
        return self.get_mask_path().boundingRect().bottomRight()

    # Add this method to handle potential attribute access
    def __getattr__(self, name):
        print(f"Accessing attribute {name}")
        if name in ['top_left', 'bottom_left', 'top_right', 'bottom_right']:
            return getattr(self.first_selected_strand, name)
        raise AttributeError(f"'MaskedStrand' object has no attribute '{name}'")
