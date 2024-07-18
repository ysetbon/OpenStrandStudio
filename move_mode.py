from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math
from attach_mode import AttachedStrand

class MoveMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.moving_point = None
        self.is_moving = False
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)

    def update_cursor_position(self, pos):
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        global_pos = self.canvas.mapToGlobal(pos)
        QCursor.setPos(global_pos)

    def mousePressEvent(self, event):
        pos = event.pos()
        self.handle_strand_movement(pos)
        if self.is_moving:
            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)

    def mouseMoveEvent(self, event):
        if self.is_moving and self.moving_point:
            new_pos = event.pos()
            self.update_strand_position(new_pos)
            self.last_update_pos = new_pos

    def mouseReleaseEvent(self, event):
        self.is_moving = False
        self.moving_point = None
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.canvas.update()

    def handle_strand_movement(self, pos):
        for strand in self.canvas.strands:
            if self.try_move_strand(strand, pos):
                return
            if self.try_move_attached_strands(strand.attached_strands, pos):
                return

    def try_move_strand(self, strand, pos):
        start_rect = self.get_end_rectangle(strand, 0)
        end_rect = self.get_end_rectangle(strand, 1)

        if start_rect.contains(pos):
            self.start_movement(strand, 0, start_rect)
            return True
        elif end_rect.contains(pos):
            self.start_movement(strand, 1, end_rect)
            return True
        return False

    def try_move_attached_strands(self, attached_strands, pos):
        for attached_strand in attached_strands:
            if self.try_move_strand(attached_strand, pos):
                return True
            if self.try_move_attached_strands(attached_strand.attached_strands, pos):
                return True
        return False

    def start_movement(self, strand, side, rect):
        self.moving_side = side
        self.moving_point = rect.center()
        self.affected_strand = strand
        self.selected_rectangle = rect
        self.is_moving = True
        self.update_cursor_position(self.moving_point)

    def get_end_rectangle(self, strand, side):
        half_width = strand.width
        center = strand.start if side == 0 else strand.end
        return QRectF(center.x() - half_width, center.y() - half_width, strand.width*2, strand.width*2)

    def update_strand_position(self, new_pos):
        if not self.affected_strand:
            return

        delta = new_pos - self.last_update_pos
        self.accumulated_delta += delta

        current_angle = math.degrees(math.atan2(self.accumulated_delta.y(), self.accumulated_delta.x()))
        rounded_angle = round(current_angle / 10) * 10
        rounded_angle = rounded_angle % 360

        magnitude = self.accumulated_delta.manhattanLength()

        if magnitude > 25:
            rounded_delta = QPointF(
                magnitude * math.cos(math.radians(rounded_angle)),
                magnitude * math.sin(math.radians(rounded_angle))
            )

            self.move_strand_and_update_attached(self.affected_strand, new_pos, self.moving_side)

            self.selected_rectangle.moveCenter(new_pos)
            self.accumulated_delta = QPointF(0, 0)
            self.canvas.update()

        self.update_cursor_position(new_pos)
        self.last_update_pos = new_pos

    def move_strand_and_update_attached(self, strand, new_pos, moving_side):
        old_start, old_end = strand.start, strand.end
        if moving_side == 0:
            strand.start = new_pos
        else:
            strand.end = new_pos
        strand.update_shape()
        strand.update_side_line()

        # Update parent strands recursively
        self.update_parent_strands(strand)

        # Update all attached strands
        self.update_all_attached_strands(strand, old_start, old_end)

        # If it's an AttachedStrand, update its parent's side line
        if isinstance(strand, AttachedStrand):
            strand.parent.update_side_line()

    def update_parent_strands(self, strand):
        if isinstance(strand, AttachedStrand):
            parent = self.find_parent_strand(strand)
            if parent:
                if strand.start == parent.start:
                    parent.start = strand.start
                else:
                    parent.end = strand.start
                parent.update_shape()
                parent.update_side_line()
                # Recursively update the parent's parent
                self.update_parent_strands(parent)

    def update_all_attached_strands(self, strand, old_start, old_end):
        for attached in strand.attached_strands:
            if attached.start == old_start:
                attached.start = strand.start
            elif attached.start == old_end:
                attached.start = strand.end
            attached.update(attached.end)
            attached.update_side_line()
            # Recursively update attached strands of this attached strand
            self.update_all_attached_strands(attached, attached.start, attached.end)

    def find_parent_strand(self, attached_strand):
        for strand in self.canvas.strands:
            if attached_strand in strand.attached_strands:
                return strand
            parent = self.find_parent_in_attached(strand, attached_strand)
            if parent:
                return parent
        return None

    def find_parent_in_attached(self, strand, target):
        for attached in strand.attached_strands:
            if attached == target:
                return strand
            parent = self.find_parent_in_attached(attached, target)
            if parent:
                return parent
        return None