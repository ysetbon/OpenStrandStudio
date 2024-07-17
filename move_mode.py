# move_mode.py

# Import necessary modules from PyQt5
from PyQt5.QtCore import QPointF, QRectF  # For handling points and rectangles
from PyQt5.QtGui import QCursor  # For manipulating the cursor
from PyQt5.QtWidgets import QApplication  # For accessing the application instance
import math  # For mathematical operations
from attach_mode import AttachedStrand  # Import the AttachedStrand class from attach_mode.py

class MoveMode:
    def __init__(self, canvas):
        self.canvas = canvas  # Store a reference to the main canvas
        self.moving_point = None  # The point (QPointF) being moved (start or end of a strand)
        self.is_moving = False  # Boolean flag to indicate if we're currently moving a point
        self.affected_strand = None  # Reference to the strand being modified
        self.moving_side = None  # Integer indicating which side of the strand is being moved (0 for start, 1 for end)
        self.selected_rectangle = None  # QRectF representing the selected area
        self.last_update_pos = None  # QPointF storing the last position of the mouse during movement
        self.accumulated_delta = QPointF(0, 0)  # QPointF storing the accumulated change in position

    def update_cursor_position(self, pos):
        # Convert QPointF to QPoint if necessary
        if isinstance(pos, QPointF):
            pos = pos.toPoint()  # Convert QPointF to QPoint
        
        # Convert local coordinates to global screen coordinates
        global_pos = self.canvas.mapToGlobal(pos)
        
        # Set the cursor position on the screen
        QCursor.setPos(global_pos)

    def mousePressEvent(self, event):
        pos = event.pos()  # Get the position (QPoint) of the mouse click
        self.handle_strand_movement(pos)  # Check if a strand can be moved from this position
        
        if self.is_moving:
            # If we've started moving, initialize the last update position and reset accumulated delta
            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)

    def mouseMoveEvent(self, event):
        if self.is_moving and self.moving_point:
            new_pos = event.pos()  # Get the new position (QPoint) of the mouse
            self.update_strand_position(new_pos)  # Update the strand's position
            self.last_update_pos = new_pos  # Store this position for the next move event

    def mouseReleaseEvent(self, event):
        # Reset all movement-related variables when the mouse is released
        self.is_moving = False
        self.moving_point = None
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.canvas.update()  # Redraw the canvas

    def handle_strand_movement(self, pos):
        # Iterate through all strands on the canvas
        for strand in self.canvas.strands:
            # Try to move this strand
            if self.try_move_strand(strand, pos):
                return  # If successful, exit the function
            # If not, try to move its attached strands
            if self.try_move_attached_strands(strand.attached_strands, pos):
                return  # If successful, exit the function

    def try_move_strand(self, strand, pos):
        # Get rectangles representing the start and end areas of the strand
        start_rect = self.get_end_rectangle(strand, 0)  # Rectangle for start point
        end_rect = self.get_end_rectangle(strand, 1)  # Rectangle for end point

        # Check if the click position is within these rectangles
        if start_rect.contains(pos):
            self.start_movement(strand, 0, start_rect)  # Start moving the start point
            return True
        elif end_rect.contains(pos):
            self.start_movement(strand, 1, end_rect)  # Start moving the end point
            return True
        return False  # Return False if the click wasn't on either end of the strand

    def try_move_attached_strands(self, attached_strands, pos):
        # Recursively check all attached strands
        for attached_strand in attached_strands:
            if self.try_move_strand(attached_strand, pos):
                return True  # If we can move this attached strand, return True
            # Recursively check this attached strand's own attached strands
            if self.try_move_attached_strands(attached_strand.attached_strands, pos):
                return True
        return False  # Return False if no attached strand can be moved

    def start_movement(self, strand, side, rect):
        # Initialize all variables needed for strand movement
        self.moving_side = side  # 0 for start, 1 for end
        self.moving_point = rect.center()  # Center point of the selected rectangle
        self.affected_strand = strand  # The strand being moved
        self.selected_rectangle = rect  # The rectangle representing the selected area
        self.is_moving = True  # Set the moving flag to True
        self.update_cursor_position(self.moving_point)  # Update the cursor position

    def get_end_rectangle(self, strand, side):
        # Create a rectangle around the start or end point of a strand
        half_width = strand.width  # Half the width of the strand
        if side == 0:
            center = strand.start  # Use start point for side 0
        else:
            center = strand.end  # Use end point for side 1
        # Create and return a QRectF centered on the chosen point
        return QRectF(center.x() - half_width, center.y() - half_width, strand.width*2, strand.width*2)

    def update_strand_position(self, new_pos):
        if not self.affected_strand:
            return  # If there's no affected strand, do nothing
        
        # Calculate the change in position
        delta = new_pos - self.last_update_pos
        self.accumulated_delta += delta  # Add to the accumulated delta

        # Calculate the current angle of the accumulated delta
        current_angle = math.degrees(math.atan2(self.accumulated_delta.y(), self.accumulated_delta.x()))
        
        # Round the current angle to the nearest 10 degrees
        rounded_angle = round(current_angle / 10) * 10
        rounded_angle = rounded_angle % 360  # Ensure angle is between 0 and 360

        # Calculate the magnitude of the accumulated delta
        magnitude = self.accumulated_delta.manhattanLength()

        # Only update if the magnitude is significant (> 25 pixels)
        if magnitude > 25:
            # Calculate the new delta based on the rounded angle and magnitude
            rounded_delta = QPointF(
                magnitude * math.cos(math.radians(rounded_angle)),
                magnitude * math.sin(math.radians(rounded_angle))
            )

            # Store old positions for updating attached strands
            old_start = self.affected_strand.start
            old_end = self.affected_strand.end

            # Update the position of the affected strand
            if isinstance(self.affected_strand, AttachedStrand):
                if self.moving_side == 0:
                    new_start = new_pos  # Set new_start directly to new_pos
                    self.affected_strand.update_start(new_start)
                    self.affected_strand.update(self.affected_strand.end)
                else:
                    new_end = new_pos  # Set new_end directly to new_pos
                    self.affected_strand.move_end(new_end)
            else:
                if self.moving_side == 0:
                    self.affected_strand.start = new_pos  # Set start directly to new_pos
                else:
                    self.affected_strand.end = new_pos  # Set end directly to new_pos
                self.affected_strand.update_shape()
            
            # Update positions of all attached strands
            self.update_attached_strands(self.affected_strand, old_start, old_end)
            
            # Update the selected rectangle to center on the new position
            self.selected_rectangle.moveCenter(new_pos)
            
            # Reset the accumulated delta
            self.accumulated_delta = QPointF(0, 0)
            
            self.canvas.update()  # Redraw the canvas

        # Always update the cursor position to the new position
        self.update_cursor_position(new_pos)
        
        # Update the last_update_pos to the new position
        self.last_update_pos = new_pos

    def update_attached_strands(self, strand, old_start, old_end):
        # Check if the strand has attached strands
        if hasattr(strand, 'attached_strands'):
            # Iterate through all attached strands
            for attached in strand.attached_strands:
                if attached.start == old_start:
                    # If the attached strand was connected to the start point, update its start
                    attached.update_start(strand.start)
                elif attached.start == old_end:
                    # If the attached strand was connected to the end point, update its start
                    attached.update_start(strand.end)
                # Recursively update this attached strand's own attached strands
                self.update_attached_strands(attached, attached.start, attached.end)

    def find_parent_strand(self, attached_strand):
        # Iterate through all main strands on the canvas
        for strand in self.canvas.strands:
            if attached_strand in strand.attached_strands:
                return strand  # If found, return this strand as the parent
            # Check this strand's attached strands
            for sub_attached in strand.attached_strands:
                if sub_attached == attached_strand:
                    return strand  # If found, return this strand as the parent
        return None  # If not found, return None

    def update_strand_chain(self, strand, delta):
        # Update the position of a strand
        strand.start += delta
        strand.end += delta
        # Recursively update all attached strands
        for attached in strand.attached_strands:
            self.update_strand_chain(attached, delta)