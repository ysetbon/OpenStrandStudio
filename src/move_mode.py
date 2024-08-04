from PyQt5.QtCore import QPointF, QRectF, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math

from strand import AttachedStrand

class MoveMode:
    def __init__(self, canvas):
        """
        Initialize the MoveMode.

        Args:
            canvas (StrandDrawingCanvas): The canvas this mode operates on.
        """
        self.canvas = canvas
        self.initialize_properties()
        self.setup_timer()

    def initialize_properties(self):
        """Initialize all properties used in the MoveMode."""
        self.moving_point = None  # The point being moved
        self.is_moving = False  # Flag to indicate if we're currently moving a point
        self.affected_strand = None  # The strand being affected by the move
        self.moving_side = None  # Which side of the strand is being moved (0 for start, 1 for end)
        self.selected_rectangle = None  # The rectangle representing the selected point
        self.last_update_pos = None  # The last position update
        self.accumulated_delta = QPointF(0, 0)  # Accumulated movement delta
        self.last_snapped_pos = None  # Last position snapped to grid
        self.target_pos = None  # Target position for gradual movement
        self.move_speed = 1  # Speed of movement in grid units per step
        self.locked_layers = set()  # Set of locked layer indices
        self.lock_mode_active = False  # Flag to indicate if lock mode is active

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)

    def set_locked_layers(self, locked_layers, lock_mode_active):
        """
        Set the locked layers and lock mode state.

        Args:
            locked_layers (set): Set of indices of locked layers.
            lock_mode_active (bool): Whether lock mode is active.
        """
        self.locked_layers = locked_layers
        self.lock_mode_active = lock_mode_active

    def update_cursor_position(self, pos):
        """
        Update the cursor position to match the strand end point.

        Args:
            pos (QPointF): The new position for the cursor.
        """
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        global_pos = self.canvas.mapToGlobal(pos)
        QCursor.setPos(global_pos)

    def mousePressEvent(self, event):
        """
        Handle mouse press events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        pos = event.pos()
        self.handle_strand_movement(pos)
        if self.is_moving:
            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)
            self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            self.target_pos = self.last_snapped_pos

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if self.is_moving and self.moving_point:
            new_pos = event.pos()
            self.target_pos = self.canvas.snap_to_grid(new_pos)
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        # Reset all properties
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
        """Perform gradual movement of the strand end point."""
        if not self.is_moving or not self.target_pos or not self.last_snapped_pos:
            self.move_timer.stop()
            return

        # Calculate the distance to move
        dx = self.target_pos.x() - self.last_snapped_pos.x()
        dy = self.target_pos.y() - self.last_snapped_pos.y()

        # Calculate the step size, limited by move_speed
        step_x = min(abs(dx), self.move_speed * self.canvas.grid_size) * (1 if dx > 0 else -1)
        step_y = min(abs(dy), self.move_speed * self.canvas.grid_size) * (1 if dy > 0 else -1)

        # Calculate the new position
        new_x = self.last_snapped_pos.x() + step_x
        new_y = self.last_snapped_pos.y() + step_y

        new_pos = self.canvas.snap_to_grid(QPointF(new_x, new_y))

        if new_pos != self.last_snapped_pos:
            # Update the strand position and cursor
            self.update_strand_position(new_pos)
            self.update_cursor_position(new_pos)
            self.last_snapped_pos = new_pos

        if new_pos == self.target_pos:
            # If we've reached the target, stop the timer
            self.move_timer.stop()

    def handle_strand_movement(self, pos):
        """
        Handle the movement of strands.

        Args:
            pos (QPointF): The position of the mouse click.
        """
        for i, strand in enumerate(self.canvas.strands):
            if not self.lock_mode_active or i not in self.locked_layers:
                if self.try_move_strand(strand, pos):
                    return
                if self.try_move_attached_strands(strand.attached_strands, pos):
                    return

    def try_move_strand(self, strand, pos):
        """
        Try to move a strand if the position is within its end rectangles.

        Args:
            strand (Strand): The strand to try moving.
            pos (QPointF): The position to check.

        Returns:
            bool: True if the strand was moved, False otherwise.
        """
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
        """
        Recursively try to move attached strands.

        Args:
            attached_strands (list): List of attached strands to check.
            pos (QPointF): The position to check.

        Returns:
            bool: True if an attached strand was moved, False otherwise.
        """
        for attached_strand in attached_strands:
            if self.try_move_strand(attached_strand, pos):
                return True
            if self.try_move_attached_strands(attached_strand.attached_strands, pos):
                return True
        return False

    def start_movement(self, strand, side, rect):
        """
        Start the movement of a strand.

        Args:
            strand (Strand): The strand to move.
            side (int): Which side of the strand to move (0 for start, 1 for end).
            rect (QRectF): The rectangle representing the movable area.
        """
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
        """
        Get the rectangle representing the end point of a strand.

        Args:
            strand (Strand): The strand to get the rectangle for.
            side (int): Which side of the strand (0 for start, 1 for end).

        Returns:
            QRectF: The rectangle representing the movable area of the strand end.
        """
        center = strand.start if side == 0 else strand.end
        return QRectF(center.x() - strand.width, center.y() - strand.width, strand.width*2, strand.width*2)

    def update_strand_position(self, new_pos):
        """
        Update the position of the affected strand.

        Args:
            new_pos (QPointF): The new position for the strand end.
        """
        if not self.affected_strand:
            return

        self.move_strand_and_update_attached(self.affected_strand, new_pos, self.moving_side)
        self.selected_rectangle.moveCenter(new_pos)
        self.canvas.update()

    def move_strand_and_update_attached(self, strand, new_pos, moving_side):
        """
        Move the strand and update all attached strands.

        Args:
            strand (Strand): The strand to move.
            new_pos (QPointF): The new position for the strand end.
            moving_side (int): Which side of the strand is being moved (0 for start, 1 for end).
        """
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
        """
        Recursively update parent strands.

        Args:
            strand (Strand): The strand whose parents need updating.
        """
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
        """
        Recursively update all attached strands.

        Args:
            strand (Strand): The strand whose attached strands need updating.
            old_start (QPointF): The old start position of the strand.
            old_end (QPointF): The old end position of the strand.
        """
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
        """
        Find the parent strand of an attached strand.

        Args:
            attached_strand (AttachedStrand): The attached strand to find the parent for.

        Returns:
            Strand: The parent strand, or None if not found.
        """
        for strand in self.canvas.strands:
            if attached_strand in strand.attached_strands:
                return strand
            parent = self.find_parent_in_attached(strand, attached_strand)
            if parent:
                return parent
        return None

    def find_parent_in_attached(self, strand, target):
        """
        Recursively find the parent strand in attached strands.

        Args:
            strand (Strand): The strand to search in.
            target (AttachedStrand): The attached strand to find the parent for.

        Returns:
            Strand: The parent strand, or None if not found.
        """
        for attached in strand.attached_strands:
            if attached == target:
                return strand
            parent = self.find_parent_in_attached(attached, target)
            if parent:
                return parent
        return None