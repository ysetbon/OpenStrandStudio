# move_mode.py

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
        if side == 0:
            center = strand.start
        else:
            center = strand.end
        return QRectF(center.x() - half_width, center.y() - half_width, strand.width*2, strand.width*2)

    def update_strand_position(self, new_pos):
        if not self.affected_strand:
            return
        
        delta = new_pos - self.last_update_pos
        self.accumulated_delta += delta

        # Calculate the current angle of the accumulated delta
        current_angle = math.degrees(math.atan2(self.accumulated_delta.y(), self.accumulated_delta.x()))
        
        # Round the current angle to the nearest 5 degrees
        rounded_angle = round(current_angle / 10) * 10
        rounded_angle = rounded_angle % 360

        # Calculate the magnitude of the accumulated delta
        magnitude = self.accumulated_delta.manhattanLength()

        # Only update if the magnitude is significant (e.g., > 5 pixels)
        if magnitude > 10:
            # Calculate the new delta based on the rounded angle and magnitude
            rounded_delta = QPointF(
                magnitude * math.cos(math.radians(rounded_angle)),
                magnitude * math.sin(math.radians(rounded_angle))
            )

            old_start = self.affected_strand.start
            old_end = self.affected_strand.end

            if isinstance(self.affected_strand, AttachedStrand):
                if self.moving_side == 0:
                    new_start = self.affected_strand.start + rounded_delta
                    self.affected_strand.update_start(new_start)
                    self.affected_strand.update(self.affected_strand.end)
                else:
                    new_end = self.affected_strand.end + rounded_delta
                    self.affected_strand.move_end(new_end)
            else:
                if self.moving_side == 0:
                    self.affected_strand.start += rounded_delta
                else:
                    self.affected_strand.end += rounded_delta
                self.affected_strand.update_shape()
            
            self.update_attached_strands(self.affected_strand, old_start, old_end)
            
            # Update the selected rectangle
            if self.moving_side == 0:
                new_center = self.affected_strand.start
            else:
                new_center = self.affected_strand.end
            self.selected_rectangle.moveCenter(new_center)
            
            # Reset the accumulated delta
            self.accumulated_delta = QPointF(0, 0)
            
            self.canvas.update()

        # Always update the cursor position
        self.update_cursor_position(new_pos)

    def update_attached_strands(self, strand, old_start, old_end):
        if hasattr(strand, 'attached_strands'):
            for attached in strand.attached_strands:
                if attached.start == old_start:
                    attached.update_start(strand.start)
                elif attached.start == old_end:
                    attached.update_start(strand.end)
                self.update_attached_strands(attached, attached.start, attached.end)

    def find_parent_strand(self, attached_strand):
        for strand in self.canvas.strands:
            if attached_strand in strand.attached_strands:
                return strand
            for sub_attached in strand.attached_strands:
                if sub_attached == attached_strand:
                    return strand
        return None

    def update_strand_chain(self, strand, delta):
        strand.start += delta
        strand.end += delta
        for attached in strand.attached_strands:
            self.update_strand_chain(attached, delta)