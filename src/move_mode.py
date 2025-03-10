from PyQt5.QtCore import QPointF, QRectF, QTimer, Qt
from PyQt5.QtGui import QCursor, QPen, QColor, QPainterPathStroker, QTransform
from PyQt5.QtWidgets import QApplication
import math
from PyQt5.QtGui import (
     QPainterPath
)
from strand import Strand, AttachedStrand, MaskedStrand

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
        self.originally_selected_strand = None
        self.in_move_mode = False
        self.temp_selected_strand = None

    def initialize_properties(self):
        """Initialize all properties used in the MoveMode."""
        self.moving_point = None  # The point being moved
        self.is_moving = False  # Flag to indicate if we're currently moving a point
        self.affected_strand = None  # The strand being affected by the move
        self.moving_side = None  # Which side of the strand is being moved (0 for start, 1 for end, 'control_point1', 'control_point2')
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
        
        if not self.in_move_mode:
            # Set the originally_selected_strand to the currently selected strand in the layer panel
            self.originally_selected_strand = self.canvas.selected_strand
            self.in_move_mode = True
            
            print(f"Entering move mode. self.canvas.selected_strand: {self.canvas.selected_strand}")

        # Store the current selection state
        previously_selected = self.canvas.selected_strand

        print(f"Previously selected strand: {previously_selected}")

        # Log currently selected strands before deselection
        print("Currently selected strands before deselection:")
        for strand in self.canvas.strands:
            if strand.is_selected:
                print(f"- {strand}")
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    if attached.is_selected:
                        print(f"  - Attached: {attached}")

        # Deselect all strands
        for strand in self.canvas.strands:
            strand.is_selected = False
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    attached.is_selected = False

        self.handle_strand_movement(pos)
        if self.is_moving:
            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)
            self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            self.target_pos = self.last_snapped_pos

            # Set the temporary selected strand
            self.temp_selected_strand = self.affected_strand
            if self.temp_selected_strand:
                self.temp_selected_strand.is_selected = True
                # Only set originally_selected_strand's selection if it exists
                if self.originally_selected_strand:
                    self.originally_selected_strand.is_selected = True
                self.canvas.selected_attached_strand = self.temp_selected_strand
        else:
            # If no strand was clicked, revert to the original selection
            if self.originally_selected_strand:
                self.originally_selected_strand.is_selected = True
                self.canvas.selected_attached_strand = self.originally_selected_strand
            elif previously_selected:
                self.canvas.selected_attached_strand = previously_selected

        # Update the canvas
        self.canvas.update()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.
        """
        if self.is_moving and self.moving_point:
            new_pos = event.pos()
            # 1) Move freely (no grid snap) in real time
            self.update_strand_position(new_pos)

            # 2) (Remove or comment out the pointer centering call here)
            # self.update_cursor_position(new_pos)

            # Redraw for smooth result
            self.canvas.update()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.
        """
        if self.is_moving and self.moving_point:
            # 3) Snap the final position once on release
            final_snapped_pos = self.canvas.snap_to_grid(event.pos())
            self.update_strand_position(final_snapped_pos)

            # (Optional) Finally recenter the cursor here, if you truly want it:
            # self.update_cursor_position(final_snapped_pos)

            self.canvas.update()

        # Deselect all strands
        for strand in self.canvas.strands:
            strand.is_selected = False
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    attached.is_selected = False

        # Restore the selection of the originally selected strand
        if self.originally_selected_strand:
            self.originally_selected_strand.is_selected = True
            self.canvas.selected_attached_strand = self.originally_selected_strand

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
        self.in_move_mode = False
        self.temp_selected_strand = None  # Reset temporary selection

        self.canvas.update()

    def gradual_move(self):
        """
        (Optional) No-op or minimal version if you no longer want incremental movement.
        """
        pass

    def handle_strand_movement(self, pos):
        """
        Handle the movement of strands.

        Args:
            pos (QPointF): The position of the mouse click.
        """
        self.is_moving = False  # Reset this flag at the start

        # First pass: Check all control points for all strands
        for strand in self.canvas.strands:
            if not getattr(strand, 'deleted', False):
                if self.try_move_control_points(strand, pos):
                    return
                if self.try_move_attached_strands_control_points(strand.attached_strands, pos):
                    return

        # Second pass: Check start and end points for all strands
        for i, strand in enumerate(self.canvas.strands):
            if not getattr(strand, 'deleted', False) and (not self.lock_mode_active or i not in self.locked_layers):
                if self.try_move_strand(strand, pos, i):
                    return
                if self.try_move_attached_strands_start_end(strand.attached_strands, pos):
                    return

    def try_move_attached_strands_control_points(self, attached_strands, pos):
        """
        Recursively try to move control points of attached strands.

        Args:
            attached_strands (list): List of attached strands to check.
            pos (QPointF): The position to check.

        Returns:
            bool: True if a control point of an attached strand was moved, False otherwise.
        """
        for attached_strand in attached_strands:
            if not getattr(attached_strand, 'deleted', False):
                if self.try_move_control_points(attached_strand, pos):
                    return True
                if self.try_move_attached_strands_control_points(attached_strand.attached_strands, pos):
                    return True
        return False

    def try_move_attached_strands_start_end(self, attached_strands, pos):
        """
        Recursively try to move start and end points of attached strands.

        Args:
            attached_strands (list): List of attached strands to check.
            pos (QPointF): The position to check.

        Returns:
            bool: True if a start or end point of an attached strand was moved, False otherwise.
        """
        for attached_strand in attached_strands:
            if not getattr(attached_strand, 'deleted', False):
                if self.try_move_strand(attached_strand, pos, -1):  # Pass -1 if not in main strands list
                    return True
                if self.try_move_attached_strands_start_end(attached_strand.attached_strands, pos):
                    return True
        return False

    def try_move_control_points(self, strand, pos):
        """
        Try to move a strand's control points if the position is within their selection areas.

        Args:
            strand (Strand): The strand to try moving.
            pos (QPointF): The position to check.

        Returns:
            bool: True if a control point was moved, False otherwise.
        """
        # Skip control point checks for MaskedStrands
        if isinstance(strand, MaskedStrand):
            return False

        control_point1_rect = self.get_control_point_rectangle(strand, 1)
        control_point2_rect = self.get_control_point_rectangle(strand, 2)

        if control_point1_rect.contains(pos):
            self.start_movement(strand, 'control_point1', control_point1_rect)
            return True
        elif control_point2_rect.contains(pos):
            self.start_movement(strand, 'control_point2', control_point2_rect)
            return True
        return False

    def try_move_strand(self, strand, pos, strand_index):
        """
        Try to move a strand if the position is within its selection areas.

        Args:
            strand (Strand): The strand to try moving.
            pos (QPointF): The position to check.
            strand_index (int): The index of the strand in the canvas's strand list.

        Returns:
            bool: True if the strand was moved, False otherwise.
        """
        # Get selection areas
        start_area = self.get_start_area(strand)
        end_area = self.get_end_area(strand)

        # Only check control points for non-MaskedStrands
        if not isinstance(strand, MaskedStrand):
            control_point1_rect = self.get_control_point_rectangle(strand, 1)
            control_point2_rect = self.get_control_point_rectangle(strand, 2)

            if control_point1_rect.contains(pos):
                self.start_movement(strand, 'control_point1', control_point1_rect)
                return True
            elif control_point2_rect.contains(pos):
                self.start_movement(strand, 'control_point2', control_point2_rect)
                return True

        if start_area.contains(pos) and self.can_move_side(strand, 0, strand_index):
            self.start_movement(strand, 0, start_area)
            if isinstance(strand, AttachedStrand):
                self.canvas.selected_attached_strand = strand
                strand.is_selected = True
            return True
        elif end_area.contains(pos) and self.can_move_side(strand, 1, strand_index):
            self.start_movement(strand, 1, end_area)
            return True
        return False

    def get_control_point_rectangle(self, strand, control_point_number):
        """Get the rectangle around the specified control point for hit detection."""
        size = 35  # Size of the area for control point selection
        if control_point_number == 1:
            center = strand.control_point1
        elif control_point_number == 2:
            center = strand.control_point2
        else:
            return QRectF()
        return QRectF(center.x() - size / 2, center.y() - size / 2, size, size)

    def get_start_area(self, strand):
        """
        Get the selection area for the start point of a strand.

        Args:
            strand (Strand): The strand to get the area for.

        Returns:
            QPainterPath: The selection area path.
        """
        # Define the outer rectangle (120x120 square)
        outer_size = 120
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            strand.start.x() - half_outer_size,
            strand.start.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Create the selection area as the outer rectangle only
        path = QPainterPath()
        path.addRect(outer_rect)

        return path

    def get_end_area(self, strand):
        """
        Get the selection area for the end point of a strand.

        Args:
            strand (Strand): The strand to get the area for.

        Returns:
            QPainterPath: The selection area path.
        """
        # Define the outer rectangle (120x120 square)
        outer_size = 120
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            strand.end.x() - half_outer_size,
            strand.end.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Create the selection area as the outer rectangle only
        path = QPainterPath()
        path.addRect(outer_rect)

        return path

    def can_move_side(self, strand, side, strand_index):
        """
        Check if the side of a strand can be moved.

        Args:
            strand (Strand): The strand to check.
            side (int or str): Which side of the strand to check (0 for start, 1 for end, 'control_point1', 'control_point2').
            strand_index (int): The index of the strand in the canvas's strand list.

        Returns:
            bool: True if the side can be moved, False otherwise.
        """
        if not self.lock_mode_active:
            return True

        # Check if the strand itself is locked
        if strand_index in self.locked_layers:
            return False

        if side in ('control_point1', 'control_point2'):
            return True  # Assume control points can be moved unless specific locking is needed

        # Check if the side is shared with a locked strand
        point = strand.start if side == 0 else strand.end
        for i, other_strand in enumerate(self.canvas.strands):
            if i in self.locked_layers:
                if point == other_strand.start or point == other_strand.end:
                    return False

        return True

    def start_movement(self, strand, side, area):
        """
        Start the movement of a strand's point without changing its selection state.
        """
        self.moving_side = side
        
        # For QPainterPath, get the bounding rectangle and center
        if isinstance(area, QPainterPath):
            bounding_rect = area.boundingRect()
            self.moving_point = bounding_rect.center()
        elif isinstance(area, QRectF):
            self.moving_point = area.center()
        else:
            # Default to using the strand's point
            if side == 0:
                self.moving_point = strand.start
            elif side == 1:
                self.moving_point = strand.end
            else:
                self.moving_point = QPointF(0, 0)

        self.affected_strand = strand
        self.selected_rectangle = area
        self.is_moving = True
        snapped_pos = self.canvas.snap_to_grid(self.moving_point)
        self.update_cursor_position(snapped_pos)
        self.last_snapped_pos = snapped_pos
        self.target_pos = snapped_pos

        # Find any other strands connected to this point using layer_state_manager
        moving_point = strand.start if side == 0 else strand.end
        connected_strand = self.find_connected_strand(strand, side, moving_point)

        # Set both strands as selected
        if isinstance(strand, AttachedStrand):
            self.canvas.selected_attached_strand = strand
            strand.is_selected = True
        
        if connected_strand:
            connected_strand.is_selected = True
            if isinstance(connected_strand, AttachedStrand):
                self.temp_selected_strand = connected_strand

        # Update the canvas
        self.canvas.update()

    def points_are_close(self, point1, point2, tolerance=5.0):
        """Check if two points are within a certain tolerance."""
        return (abs(point1.x() - point2.x()) <= tolerance and
                abs(point1.y() - point2.y()) <= tolerance)

    def update_strand_position(self, new_pos):
        """
        Update the position of the affected strand's point.

        Args:
            new_pos (QPointF): The new position.
        """
        if not self.affected_strand:
            return

        if self.moving_side == 'control_point1':
            # Move the first control point
            self.affected_strand.control_point1 = new_pos
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 1)
            self.canvas.update()
        elif self.moving_side == 'control_point2':
            # Move the second control point
            self.affected_strand.control_point2 = new_pos
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 2)
            self.canvas.update()
        elif self.moving_side == 0 or self.moving_side == 1:
            # Moving start or end point
            self.move_strand_and_update_attached(self.affected_strand, new_pos, self.moving_side)
            # Update the selection area
            if isinstance(self.selected_rectangle, QPainterPath):
                # Recreate the selection area at the new position
                if self.moving_side == 0:
                    self.selected_rectangle = self.get_start_area(self.affected_strand)
                else:
                    self.selected_rectangle = self.get_end_area(self.affected_strand)
            self.canvas.update()
        else:
            # Invalid moving_side
            pass  # Or handle unexpected cases

        # Ensure the affected strand remains selected
        self.affected_strand.is_selected = True
        self.canvas.selected_attached_strand = self.affected_strand

        # Force a redraw of the canvas
        self.canvas.update()

    def move_strand_and_update_attached(self, strand, new_pos, moving_side):
        """Move the strand's point and update attached strands without resetting control points.

        Args:
            strand (Strand): The strand to move.
            new_pos (QPointF): The new position.
            moving_side (int or str): Which side of the strand is being moved.
        """
        old_start, old_end = strand.start, strand.end

        if moving_side == 0:
            # Update control points if they coincide with the start point
            if hasattr(strand, 'control_point1') and strand.control_point1 == strand.start:
                strand.control_point1 = new_pos
            if hasattr(strand, 'control_point2') and strand.control_point2 == strand.start:
                strand.control_point2 = new_pos
            strand.start = new_pos

        elif moving_side == 1:
            # Update control points if they coincide with the end point
            if hasattr(strand, 'control_point1') and strand.control_point1 == strand.end:
                strand.control_point1 = new_pos
            if hasattr(strand, 'control_point2') and strand.control_point2 == strand.end:
                strand.control_point2 = new_pos
            strand.end = new_pos

        strand.update_shape()
        strand.update_side_line()

        # Update parent strands recursively
        self.update_parent_strands(strand)

        # Update all attached strands without resetting their control points
        self.update_all_attached_strands(strand, old_start, old_end)

        # If it's an AttachedStrand, update its parent's side line
        if isinstance(strand, AttachedStrand):
            strand.parent.update_side_line()

        # If it's a MaskedStrand, update both selected strands
        if isinstance(strand, MaskedStrand):
            if strand.first_selected_strand and hasattr(strand.first_selected_strand, 'update'):
                strand.first_selected_strand.update(new_pos)
            if strand.second_selected_strand and hasattr(strand.second_selected_strand, 'update'):
                # For non-AttachedStrand, manually update position
                if not hasattr(strand.second_selected_strand, 'update'):
                    if moving_side == 0:
                        strand.second_selected_strand.start = new_pos
                    else:
                        strand.second_selected_strand.end = new_pos
                    strand.second_selected_strand.update_shape()
                    strand.second_selected_strand.update_side_line()
                else:
                    strand.second_selected_strand.update(new_pos)

        # Force a redraw of the canvas
        self.canvas.update()

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
        """Recursively update all attached strands without resetting control points.

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
            # Update attached strand without resetting control points
            attached.update(attached.end, reset_control_points=False)
            attached.update_side_line()
            # Recursively update attached strands
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

    def cleanup_deleted_strands(self):
        """Remove deleted strands and update references after strand deletion."""
        # Remove deleted strands from the canvas
        self.canvas.strands = [strand for strand in self.canvas.strands if not getattr(strand, 'deleted', False)]

        # Update attached strands for remaining strands
        for strand in self.canvas.strands:
            if isinstance(strand, Strand):
                strand.attached_strands = [attached for attached in strand.attached_strands if not getattr(attached, 'deleted', False)]

        # Clear selection if the selected strand was deleted
        if self.affected_strand and getattr(self.affected_strand, 'deleted', False):
            self.affected_strand = None
            self.is_moving = False
            self.moving_point = None
            self.moving_side = None
            self.selected_rectangle = None

        # Update the canvas
        self.canvas.update()

    def draw_selected_attached_strand(self, painter):
        """
        Draw a circle around the selected attached strand or the temporary selected strand.

        Args:
            painter (QPainter): The painter object to draw with.
        """
        # Skip drawing all C-shapes if a main strand's starting point is being moved
        if self.is_moving and self.affected_strand and not isinstance(self.affected_strand, AttachedStrand) and self.moving_side == 0:
            return
            
        # Determine which strand to highlight
        strand_to_highlight = None
        if self.is_moving and self.temp_selected_strand:
            strand_to_highlight = self.temp_selected_strand
        elif not self.is_moving and self.canvas.selected_attached_strand:
            strand_to_highlight = self.canvas.selected_attached_strand
            
        # Only highlight the affected strand if it's set, selected, and we're in moving mode
        if self.is_moving and self.affected_strand and self.affected_strand.is_selected:
            self.draw_c_shape_for_strand(painter, self.affected_strand)
            
            # If the affected strand has attached strands, only draw C-shapes for selected ones
            if hasattr(self.affected_strand, 'attached_strands') and self.affected_strand.attached_strands:
                for attached_strand in self.affected_strand.attached_strands:
                    if attached_strand.is_selected:
                        self.draw_c_shape_for_strand(painter, attached_strand)

        # Only proceed if we have a strand to highlight and it's selected
        if strand_to_highlight and strand_to_highlight.is_selected:
            self.draw_c_shape_for_strand(painter, strand_to_highlight)

    def draw_c_shape_for_strand(self, painter, strand):
        """
        Draw C-shape for a specific strand.
        
        Args:
            painter (QPainter): The painter object to draw with.
            strand: The strand to draw the C-shape for.
        """
        painter.save()
        
        # Skip drawing C-shape highlights if this is the main strand that's moving
        is_main_strand = not isinstance(strand, AttachedStrand)
        is_moving_strand = self.is_moving and self.affected_strand == strand
        
        if is_main_strand and is_moving_strand:
            painter.restore()
            return
        
        # Draw the circles at connection points
        for i, has_circle in enumerate(strand.has_circles):
            # Only draw the start circle (i == 0) for all highlighted strands
            # For end circles (i == 1), don't draw them at all
            if i == 1:
                continue
                
            # Check if this is a main strand (not an attached strand)
            is_main_strand = not isinstance(strand, AttachedStrand)
            
            # Skip drawing C-shapes for main strands at attachment points
            if is_main_strand:
                # If this is a start point (i == 0) and it has an attachment, skip drawing
                if i == 0 and strand.has_circles[0]:
                    continue
                # If this is an end point (i == 1) and it has an attachment, skip drawing
                elif i == 1 and strand.has_circles[1]:
                    continue
            
            # Check if the strand has attached strands on both sides
            has_attached_on_both_sides = False
            if hasattr(strand, 'has_circles'):
                has_attached_on_both_sides = all(strand.has_circles)
            
            # Skip drawing the C-shape for the starting point of a main strand 
            # that doesn't have attached strands on both sides
            if i == 0 and is_main_strand and not has_attached_on_both_sides and not has_circle:
                continue
                
            # Draw the C-shape for the starting point if it has a circle or for attached strands
            if i == 0 or has_circle:
                # Save painter state
                painter.save()
                
                center = strand.start if i == 0 else strand.end
                
                # Calculate the proper radius for the highlight
                outer_radius = strand.width / 2 + strand.stroke_width + 4
                inner_radius = strand.width / 2 + 6
                
                # Create a full circle path for the outer circle
                outer_circle = QPainterPath()
                outer_circle.addEllipse(center, outer_radius, outer_radius)
                
                # Create a path for the inner circle
                inner_circle = QPainterPath()
                inner_circle.addEllipse(center, inner_radius, inner_radius)
                
                # Create a ring path by subtracting the inner circle from the outer circle
                ring_path = outer_circle.subtracted(inner_circle)
                
                # Get the tangent angle at the connection point
                tangent = strand.calculate_cubic_tangent(0.0 if i == 0 else 1.0)
                angle = math.atan2(tangent.y(), tangent.x())
                
                # Create a masking rectangle to create a C-shape
                mask_rect = QPainterPath()
                rect_width = (outer_radius + 5) * 2  # Make it slightly larger to ensure clean cut
                rect_height = (outer_radius + 5) * 2
                rect_x = center.x() - rect_width / 2
                rect_y = center.y()
                mask_rect.addRect(rect_x, rect_y, rect_width, rect_height)
                
                # Apply rotation transform to the masking rectangle
                transform = QTransform()
                transform.translate(center.x(), center.y())
                # Adjust angle based on whether it's start or end point
                if i == 0:
                    transform.rotate(math.degrees(angle - math.pi / 2))
                else:
                    transform.rotate(math.degrees(angle - math.pi / 2) + 180)
                transform.translate(-center.x(), -center.y())
                mask_rect = transform.map(mask_rect)
                
                # Create the C-shaped highlight by subtracting the mask from the ring
                c_shape_path = ring_path.subtracted(mask_rect)
                
                # Draw the C-shaped highlight
                # First draw the stroke (border) with the strand's stroke color
                stroke_pen = QPen(QColor(255, 0, 0, 255), strand.stroke_width)
                stroke_pen.setJoinStyle(Qt.MiterJoin)
                stroke_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(stroke_pen)
                painter.setBrush(QColor(255, 0, 0, 255))  # Fill with red color
                painter.drawPath(c_shape_path)
                
                # Restore painter state
                painter.restore()
        
        painter.restore()

    def find_connected_strand(self, strand, side, moving_point):
        """Find a strand connected to the given strand at the specified side."""
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            return None

        connections = self.canvas.layer_state_manager.getConnections()
        strand_connections = connections.get(strand.layer_name, [])

        # Get prefix of the current strand
        prefix = strand.layer_name.split('_')[0]

        for connected_layer_name in strand_connections:
            # Only check strands with the same prefix
            if not connected_layer_name.startswith(f"{prefix}_"):
                continue

            # Find the connected strand
            connected_strand = next(
                (s for s in self.canvas.strands 
                 if s.layer_name == connected_layer_name 
                 and not isinstance(s, MaskedStrand)), 
                None
            )

            if connected_strand and connected_strand != strand:
                # Check if the connection point matches the side we're moving
                if (side == 0 and self.points_are_close(connected_strand.end, moving_point)) or \
                   (side == 1 and self.points_are_close(connected_strand.start, moving_point)):
                    return connected_strand

        return None

    def draw(self, painter):
        """
        Draw method called by the canvas during paintEvent.
        
        Args:
            painter (QPainter): The painter object to draw with.
        """
        # Draw the selected attached strand with C-shaped highlights
        self.draw_selected_attached_strand(painter)








