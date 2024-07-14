# move_mode.py

from PyQt5.QtCore import QPointF, QRectF
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

    def mousePressEvent(self, event):
        pos = event.pos()
        self.handle_strand_movement(pos)

    def mouseMoveEvent(self, event):
        if self.is_moving and self.moving_point:
            new_pos = event.pos()
            self.update_strand_position(new_pos)

    def mouseReleaseEvent(self, event):
        self.is_moving = False
        self.moving_point = None
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.canvas.update()

    def handle_strand_movement(self, pos):
        for strand in self.canvas.strands:
            if self.try_move_strand(strand, pos):
                return
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    if self.try_move_strand(attached_strand, pos):
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

    def start_movement(self, strand, side, rect):
        self.moving_side = side
        self.moving_point = rect.center()
        self.affected_strand = strand
        self.selected_rectangle = rect
        self.is_moving = True

    def get_end_rectangle(self, strand, side):
        if side == 0:
            center = strand.start
        else:
            center = strand.end

        half_width = strand.width / 2
        return QRectF(center.x() - half_width, center.y() - half_width,
                      strand.width, strand.width)

    def update_strand_position(self, new_pos):
        if not self.affected_strand:
            return

        delta = new_pos - self.moving_point
        self.moving_point = new_pos

        if isinstance(self.affected_strand, AttachedStrand):
            if self.moving_side == 0:
                self.affected_strand.update_start(self.affected_strand.start + delta)
            else:
                self.affected_strand.move_end(self.affected_strand.end + delta)
        else:
            if self.moving_side == 0:
                self.affected_strand.start += delta
            else:
                self.affected_strand.end += delta
            self.affected_strand.update_shape()
        
        # Update attached strands if this is a main strand
        if hasattr(self.affected_strand, 'attached_strands'):
            for attached in self.affected_strand.attached_strands:
                attached.update_start(self.affected_strand.end)

        self.selected_rectangle.translate(delta)
        self.canvas.update()

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