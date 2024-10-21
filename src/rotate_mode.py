from PyQt5.QtCore import QPointF, QRectF, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math

from strand import Strand, AttachedStrand, MaskedStrand

class RotateMode:
    def __init__(self, canvas):
        """
        Initialize the RotateMode.

        Args:
            canvas (StrandDrawingCanvas): The canvas this mode operates on.
        """
        self.canvas = canvas
        self.initialize_properties()
        self.setup_timer()

    def initialize_properties(self):
        """Initialize all properties used in the RotateMode."""
        self.rotating_point = None  # The point being rotated
        self.is_rotating = False  # Flag to indicate if we're currently rotating a point
        self.affected_strand = None  # The strand being affected by the rotation
        self.rotating_side = None  # Which side of the strand is being rotated (0 for start, 1 for end)
        self.selected_rectangle = None  # The rectangle representing the selected point
        self.last_update_pos = None  # The last position update
        self.original_length = 0  # The original length of the strand
        self.pivot_point = None  # The fixed point of the strand
        self.target_pos = None  # Target position for gradual movement

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)

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
        self.handle_strand_rotation(pos)
        if self.is_rotating:
            self.last_update_pos = pos
            self.target_pos = pos

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if self.is_rotating and self.rotating_point:
            new_pos = event.pos()
            self.target_pos = self.calculate_new_position(new_pos)
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        # Reset all properties
        self.is_rotating = False
        self.rotating_point = None
        self.affected_strand = None
        self.rotating_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.original_length = 0
        self.pivot_point = None
        self.target_pos = None
        self.move_timer.stop()
        self.canvas.update()

    def gradual_move(self):
        """Perform gradual movement of the strand end point."""
        if not self.is_rotating or not self.target_pos or getattr(self.affected_strand, 'deleted', False):
            self.move_timer.stop()
            return

        # Calculate the new position
        new_pos = self.calculate_new_position(self.target_pos)

        if new_pos != self.rotating_point:
            # Update the strand position and cursor
            self.update_strand_position(new_pos)
            self.update_cursor_position(new_pos)
            self.rotating_point = new_pos

        if new_pos == self.target_pos:
            # If we've reached the target, stop the timer
            self.move_timer.stop()

    def handle_strand_rotation(self, pos):
        """
        Handle the rotation of strands.

        Args:
            pos (QPointF): The position of the mouse click.
        """
        for strand in self.canvas.strands:
            if not getattr(strand, 'deleted', False):
                if self.try_rotate_strand(strand, pos):
                    return

    def try_rotate_strand(self, strand, pos):
        """
        Try to rotate a strand if the position is within its end rectangles and the end can have new strands attached.

        Args:
            strand (Strand): The strand to try rotating.
            pos (QPointF): The position to check.

        Returns:
            bool: True if the strand was rotated, False otherwise.
        """
        start_rect = self.get_end_rectangle(strand, 0)
        end_rect = self.get_end_rectangle(strand, 1)

        if start_rect.contains(pos) and not strand.has_circles[0]:
            self.start_rotation(strand, 0, start_rect)
            return True
        elif end_rect.contains(pos) and not strand.has_circles[1]:
            self.start_rotation(strand, 1, end_rect)
            return True
        return False

    def has_attached_strand_at_end(self, strand, side):
        """
        Check if the strand has an attached strand at the specified end.

        Args:
            strand (Strand): The strand to check.
            side (int): Which side of the strand to check (0 for start, 1 for end).

        Returns:
            bool: True if there's an attached strand at the specified end, False otherwise.
        """
        point = strand.start if side == 0 else strand.end
        for attached_strand in strand.attached_strands:
            if attached_strand.start == point:
                return True
        return False

    def start_rotation(self, strand, side, rect):
        """
        Start the rotation of a strand.

        Args:
            strand (Strand): The strand to rotate.
            side (int): Which side of the strand to rotate (0 for start, 1 for end).
            rect (QRectF): The rectangle representing the rotatable area.
        """
        self.rotating_side = side
        self.rotating_point = rect.center()
        self.affected_strand = strand
        self.selected_rectangle = rect
        self.is_rotating = True
        self.original_length = self.calculate_strand_length(strand)
        self.pivot_point = strand.end if side == 0 else strand.start
        self.update_cursor_position(self.rotating_point)
        self.target_pos = self.rotating_point

    def get_end_rectangle(self, strand, side):
        """
        Get the rectangle representing the end point of a strand.

        Args:
            strand (Strand): The strand to get the rectangle for.
            side (int): Which side of the strand (0 for start, 1 for end).

        Returns:
            QRectF: The rectangle representing the rotatable area of the strand end.
        """
        center = strand.start if side == 0 else strand.end
        return QRectF(center.x() - strand.width, center.y() - strand.width, strand.width*2, strand.width*2)

    def calculate_strand_length(self, strand):
        """
        Calculate the length of a strand.

        Args:
            strand (Strand): The strand to calculate the length for.

        Returns:
            float: The length of the strand.
        """
        return math.sqrt((strand.end.x() - strand.start.x())**2 + (strand.end.y() - strand.start.y())**2)

    def calculate_new_position(self, target_pos):
        """
        Calculate the new position for the rotating point, maintaining the original strand length.

        Args:
            target_pos (QPointF): The target position for the rotating point.

        Returns:
            QPointF: The new position for the rotating point.
        """
        dx = target_pos.x() - self.pivot_point.x()
        dy = target_pos.y() - self.pivot_point.y()
        angle = math.atan2(dy, dx)
        new_x = self.pivot_point.x() + self.original_length * math.cos(angle)
        new_y = self.pivot_point.y() + self.original_length * math.sin(angle)
        return QPointF(new_x, new_y)

    def update_strand_position(self, new_pos):
        """
        Update the position of the affected strand and its control points.

        Args:
            new_pos (QPointF): The new position for the strand end.
        """
        if not self.affected_strand:
            return

        # Calculate the rotation angle
        old_vector = self.rotating_point - self.pivot_point
        new_vector = new_pos - self.pivot_point
        rotation_angle = math.atan2(new_vector.y(), new_vector.x()) - math.atan2(old_vector.y(), old_vector.x())

        if self.rotating_side == 0:
            # Rotating the start point
            self.affected_strand.start = new_pos
            # Rotate control points
            self.rotate_control_point(self.affected_strand.control_point1, rotation_angle)
            self.rotate_control_point(self.affected_strand.control_point2, rotation_angle)
        else:
            # Rotating the end point
            self.affected_strand.end = new_pos
            # Rotate control points
            self.rotate_control_point(self.affected_strand.control_point2, rotation_angle)
            self.rotate_control_point(self.affected_strand.control_point1, rotation_angle)

        self.affected_strand.update_shape()
        self.affected_strand.update_side_line()
        self.selected_rectangle.moveCenter(new_pos)
        self.canvas.update()

    def rotate_control_point(self, control_point, angle):
        """
        Rotate a control point around the pivot point.

        Args:
            control_point (QPointF): The control point to rotate.
            angle (float): The rotation angle in radians.
        """
        # Translate to origin
        translated = control_point - self.pivot_point
        
        # Rotate
        rotated_x = translated.x() * math.cos(angle) - translated.y() * math.sin(angle)
        rotated_y = translated.x() * math.sin(angle) + translated.y() * math.cos(angle)
        
        # Translate back
        rotated = QPointF(rotated_x, rotated_y) + self.pivot_point
        
        # Update the control point
        control_point.setX(rotated.x())
        control_point.setY(rotated.y())

    def cleanup_deleted_strands(self):
        """Remove deleted strands and update references after strand deletion."""
        # Remove deleted strands from the canvas
        self.canvas.strands = [strand for strand in self.canvas.strands if not getattr(strand, 'deleted', False)]
        
        # Clear selection if the selected strand was deleted
        if self.affected_strand and getattr(self.affected_strand, 'deleted', False):
            self.affected_strand = None
            self.is_rotating = False
            self.rotating_point = None
            self.rotating_side = None
            self.selected_rectangle = None
        
        # Update the canvas
        self.canvas.update()
