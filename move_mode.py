from PyQt5.QtCore import QPointF, QRectF, QTimer
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
        self.last_snapped_pos = None
        self.target_pos = None
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)
        self.move_speed = 1  # Grid units per step

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
            self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            self.target_pos = self.last_snapped_pos

    def mouseMoveEvent(self, event):
        if self.is_moving and self.moving_point:
            new_pos = event.pos()
            self.target_pos = self.canvas.snap_to_grid(new_pos)
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS

    def mouseReleaseEvent(self, event):
        self.is_moving = False
        self.moving_point = None
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.last_snapped_pos = None
        self.target_pos = None
        self.move_timer.stop()
        self.canvas.update()

    def gradual_move(self):
        if not self.is_moving or not self.target_pos or not self.last_snapped_pos:
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
        snapped_pos = self.canvas.snap_to_grid(self.moving_point)
        self.update_cursor_position(snapped_pos)
        self.last_snapped_pos = snapped_pos
        self.target_pos = snapped_pos

    def get_end_rectangle(self, strand, side):
        center = strand.start if side == 0 else strand.end
        return QRectF(center.x() - strand.width, center.y() - strand.width, strand.width*2, strand.width*2)

    def update_strand_position(self, new_pos):
        if not self.affected_strand:
            return

        self.move_strand_and_update_attached(self.affected_strand, new_pos, self.moving_side)
        self.selected_rectangle.moveCenter(new_pos)
        self.canvas.update()

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