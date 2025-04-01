from PyQt5.QtCore import QPointF, QRectF, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math
import logging

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
            
            # Start the timer if it's not already running
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if self.is_rotating:  # Only save state if we were actually rotating
            # Save state for undo/redo after rotation
            if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                self.canvas.layer_panel.undo_redo_manager.save_state()
                logging.info("Saved state after strand rotation")

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

        # Calculate the current position to target vector
        current_to_target = self.target_pos - self.rotating_point
        distance = math.sqrt(current_to_target.x() ** 2 + current_to_target.y() ** 2)
        
        # If we're close enough to the target, snap to it
        if distance < 1.0:
            new_pos = self.target_pos
            self.move_timer.stop()
        else:
            # Calculate interpolation factor (adjust for smoother/faster movement)
            factor = 0.3  # Increase for faster movement, decrease for smoother movement
            
            # Calculate the new position
            new_pos = self.calculate_new_position(QPointF(
                self.rotating_point.x() + current_to_target.x() * factor,
                self.rotating_point.y() + current_to_target.y() * factor
            ))

        if new_pos != self.rotating_point:
            # Update the strand position and cursor
            self.update_strand_position(new_pos)
            self.update_cursor_position(new_pos)
            self.rotating_point = new_pos
            self.canvas.update()

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
        # Skip if strand is masked
        if isinstance(strand, MaskedStrand):
            return False

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
        # Calculate vector from pivot to target
        dx = target_pos.x() - self.pivot_point.x()
        dy = target_pos.y() - self.pivot_point.y()
        
        # Calculate the angle
        angle = math.atan2(dy, dx)
        
        # Use the original length to maintain strand size
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

        # Store original positions
        old_start = QPointF(self.affected_strand.start)
        old_end = QPointF(self.affected_strand.end)

        if self.rotating_side == 0:
            # Rotating the start point, end point is fixed
            self.affected_strand.start = new_pos
            # End point remains fixed (it's the pivot)
            self.pivot_point = self.affected_strand.end
            
            # Update attached strands at start point
            self.update_attached_strands(old_start, new_pos)
            
        else:
            # Rotating the end point, start point is fixed
            self.affected_strand.end = new_pos
            # Start point remains fixed (it's the pivot)
            self.pivot_point = self.affected_strand.start
            
            # Update attached strands at end point
            self.update_attached_strands(old_end, new_pos)

        # Calculate the rotation angle after updating positions
        old_vector = old_start - old_end if self.rotating_side == 0 else old_end - old_start
        new_vector = self.affected_strand.start - self.affected_strand.end if self.rotating_side == 0 else self.affected_strand.end - self.affected_strand.start
        rotation_angle = math.atan2(new_vector.y(), new_vector.x()) - math.atan2(old_vector.y(), old_vector.x())

        # Update control points based on the rotation
        self.rotate_control_point(self.affected_strand.control_point1, rotation_angle)
        self.rotate_control_point(self.affected_strand.control_point2, rotation_angle)
        
        # Also rotate the control_point_center if it exists
        if hasattr(self.affected_strand, 'control_point_center'):
            self.rotate_control_point(self.affected_strand.control_point_center, rotation_angle)

        self.affected_strand.update_shape()
        self.affected_strand.update_side_line()
        self.selected_rectangle.moveCenter(new_pos)
        self.canvas.update()

    def update_control_points_proportionally(self, old_start, old_end, new_start, new_end):
        """
        Update control points maintaining their relative positions along the strand.
        
        Args:
            old_start (QPointF): Original start point
            old_end (QPointF): Original end point
            new_start (QPointF): New start point
            new_end (QPointF): New end point
        """
        # Calculate the relative positions of control points along the original strand
        old_length = math.sqrt((old_end.x() - old_start.x())**2 + (old_end.y() - old_start.y())**2)
        
        # Calculate relative distances of control points from start/end
        cp1_ratio = self.get_point_ratio(old_start, old_end, self.affected_strand.control_point1)
        cp2_ratio = self.get_point_ratio(old_end, old_start, self.affected_strand.control_point2)
        
        # Apply the same ratios to the new strand position
        self.affected_strand.control_point1 = self.interpolate_point(new_start, new_end, cp1_ratio)
        self.affected_strand.control_point2 = self.interpolate_point(new_end, new_start, cp2_ratio)

    def get_point_ratio(self, start, end, point):
        """
        Calculate the relative position of a point along a line.
        
        Args:
            start (QPointF): Start point of the line
            end (QPointF): End point of the line
            point (QPointF): Point to calculate ratio for
            
        Returns:
            float: Ratio of point position along the line (0-1)
        """
        line_length = math.sqrt((end.x() - start.x())**2 + (end.y() - start.y())**2)
        point_dist = math.sqrt((point.x() - start.x())**2 + (point.y() - start.y())**2)
        return point_dist / line_length if line_length > 0 else 0

    def interpolate_point(self, start, end, ratio):
        """
        Get a point along a line at a given ratio.
        
        Args:
            start (QPointF): Start point of the line
            end (QPointF): End point of the line
            ratio (float): Position ratio along the line (0-1)
            
        Returns:
            QPointF: Interpolated point
        """
        return QPointF(
            start.x() + (end.x() - start.x()) * ratio,
            start.y() + (end.y() - start.y()) * ratio
        )

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

    def update_attached_strands(self, old_pos, new_pos):
        """
        Update the positions of attached strands when the main strand is rotated.

        Args:
            old_pos (QPointF): The previous position of the connection point
            new_pos (QPointF): The new position of the connection point
        """
        if not hasattr(self.affected_strand, 'attached_strands'):
            return

        for attached_strand in self.affected_strand.attached_strands:
            if isinstance(attached_strand, AttachedStrand):
                # Update start point if it matches the old position
                if attached_strand.start == old_pos:
                    # Calculate the movement vector
                    delta = new_pos - old_pos
                    
                    # Move all points of the attached strand
                    attached_strand.start = new_pos
                    attached_strand.end += delta
                    attached_strand.control_point1 += delta
                    attached_strand.control_point2 += delta
                    
                    # Update the shape of the attached strand
                    attached_strand.update_shape()
                    attached_strand.update_side_line()

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





