from PyQt5.QtCore import QPointF, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math

from strand import Strand, AttachedStrand, MaskedStrand

class AttachMode(QObject):
    # Signal emitted when a new strand is created
    strand_created = pyqtSignal(object)
    strand_attached = pyqtSignal(object, object)  # New signal: parent_strand, new_strand

    def __init__(self, canvas):
        """Initialize the AttachMode."""
        super().__init__()
        self.canvas = canvas
        self.initialize_properties()
        self.setup_timer()

    def initialize_properties(self):
        """Initialize all properties used in the AttachMode."""
        self.is_attaching = False  # Flag to indicate if we're currently attaching a strand
        self.start_pos = None  # Starting position of the strand
        self.current_end = None  # Current end position of the strand
        self.target_pos = None  # Target position for gradual movement
        self.last_snapped_pos = None  # Last position snapped to grid
        self.accumulated_delta = QPointF(0, 0)  # Accumulated movement delta
        self.move_speed = 1  # Speed of movement in grid units per step

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if self.canvas.is_first_strand:
            # If it's the first strand and it has a non-zero length, create it
            if self.canvas.current_strand and self.canvas.current_strand.start != self.canvas.current_strand.end:
                self.strand_created.emit(self.canvas.current_strand)
                self.canvas.is_first_strand = False
        else:
            # If we're attaching a strand, create it
            if self.is_attaching and self.canvas.current_strand:
                self.strand_created.emit(self.canvas.current_strand)
            self.is_attaching = False
        
        # Reset all properties
        self.canvas.current_strand = None
        self.move_timer.stop()
        self.start_pos = None
        self.current_end = None
        self.target_pos = None
        self.last_snapped_pos = None
        self.accumulated_delta = QPointF(0, 0)

    def mousePressEvent(self, event):
        """Handle mouse press events."""

        # Prevent attachment if the canvas is in Move Mode
        if self.canvas.current_mode == "move":
            # Do not proceed with attachment logic
            return

        if self.canvas.is_first_strand:
            # If it's the first strand, create a new Strand object
            self.start_pos = self.canvas.snap_to_grid(event.pos())
            new_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width, 
                                self.canvas.strand_color, self.canvas.stroke_color, 
                                self.canvas.stroke_width)
            new_strand.is_first_strand = True
            self.canvas.current_strand = new_strand
            self.current_end = self.start_pos
            self.last_snapped_pos = self.start_pos
        elif self.canvas.selected_strand and not self.is_attaching:
            # If a strand is selected and we're not already attaching, try to attach
            self.handle_strand_attachment(event.pos())

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.canvas.is_first_strand and self.canvas.current_strand:
            # If it's the first strand, update the target position and start the timer
            self.target_pos = self.canvas.snap_to_grid(event.pos())
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS
        elif self.is_attaching and self.canvas.current_strand:
            # If we're attaching a strand, update the target position and start the timer
            self.target_pos = self.canvas.snap_to_grid(event.pos())
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS

    def gradual_move(self):
        """Perform gradual movement of the strand end point."""
        if not self.target_pos or not self.last_snapped_pos:
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

    def update_strand_position(self, new_pos):
        """Update the position of the current strand."""
        if self.canvas.is_first_strand:
            self.update_first_strand(new_pos)
        elif self.is_attaching:
            self.canvas.current_strand.update(new_pos)
        self.canvas.update()

    def update_first_strand(self, end_pos):
        """Update the position of the first strand, snapping to 45-degree angles."""
        if not self.canvas.current_strand:
            return

        # Calculate the angle and round it to the nearest 45 degrees
        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        angle = math.degrees(math.atan2(dy, dx))
        rounded_angle = round(angle / 45) * 45
        rounded_angle = rounded_angle % 360

        # Calculate the new end point
        length = max(self.canvas.grid_size, math.hypot(dx, dy))
        new_x = self.start_pos.x() + length * math.cos(math.radians(rounded_angle))
        new_y = self.start_pos.y() + length * math.sin(math.radians(rounded_angle))
        new_end = self.canvas.snap_to_grid(QPointF(new_x, new_y))

        # Update the strand
        self.canvas.current_strand.end = new_end
        self.canvas.current_strand.update_shape()
        self.canvas.current_strand.update_side_line()

    def update_cursor_position(self, pos):
        """Update the cursor position to match the strand end point."""
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        global_pos = self.canvas.mapToGlobal(pos)
        QCursor.setPos(global_pos)

    def handle_strand_attachment(self, pos):
        """Handle the attachment of a new strand to an existing one."""
        circle_radius = self.canvas.strand_width * 1.1

        for strand in self.canvas.strands:
            if not isinstance(strand, MaskedStrand) and strand in self.canvas.strands:
                # Check if the strand has any free sides
                if self.has_free_side(strand):
                    # Try to attach to the strand
                    if self.try_attach_to_strand(strand, pos, circle_radius):
                        return
                    # If that fails, try to attach to any of its attached strands
                    if self.try_attach_to_attached_strands(strand.attached_strands, pos, circle_radius):
                        return
            elif isinstance(strand, MaskedStrand):
                print("Cannot attach to a masked strand layer.")

    def has_free_side(self, strand):
        """Check if the strand has any free sides for attachment."""
        return not all(strand.has_circles)

    def try_attach_to_strand(self, strand, pos, circle_radius):
        """Try to attach a new strand to either end of an existing strand."""
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
        """Start the attachment of a new strand to an existing one."""
        new_strand = AttachedStrand(parent_strand, attach_point)
        new_strand.set_color(parent_strand.color)
        new_strand.set_number = parent_strand.set_number
        new_strand.is_first_strand = False
        new_strand.is_start_side = False
        parent_strand.attached_strands.append(new_strand)
        parent_strand.has_circles[side] = True
        parent_strand.update_attachable()  # Add this line
        self.canvas.current_strand = new_strand
        self.is_attaching = True
        self.last_snapped_pos = self.canvas.snap_to_grid(attach_point)
        self.target_pos = self.last_snapped_pos

        # Update the layer name for the new strand
        if self.canvas.layer_panel:
            set_number = parent_strand.set_number
            count = len([s for s in self.canvas.strands if s.set_number == set_number]) + 1
            new_strand.layer_name = f"{set_number}_{count}"

        # Emit the new signal
        self.strand_attached.emit(parent_strand, new_strand)

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        """Recursively try to attach to any of the attached strands."""
        for attached_strand in attached_strands:
            if attached_strand in self.canvas.strands and self.has_free_side(attached_strand):
                if self.try_attach_to_strand(attached_strand, pos, circle_radius):
                    return True
                if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, circle_radius):
                    return True
        return False

    def cleanup_deleted_strands(self):
        """Remove deleted strands and update references after strand deletion."""
        # Remove deleted strands from the canvas
        self.canvas.strands = [strand for strand in self.canvas.strands if not getattr(strand, 'deleted', False)]
        
        # Update attached strands for remaining strands
        for strand in self.canvas.strands:
            if isinstance(strand, Strand):
                strand.attached_strands = [attached for attached in strand.attached_strands if not getattr(attached, 'deleted', False)]
        
        # Clear selection if the selected strand was deleted
        if self.canvas.selected_strand and getattr(self.canvas.selected_strand, 'deleted', False):
            self.canvas.selected_strand = None
            self.canvas.selected_strand_index = None
        
        # Update the canvas
        self.canvas.update()
