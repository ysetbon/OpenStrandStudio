from PyQt5.QtCore import QPointF, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math
import logging

from strand import Strand, AttachedStrand, MaskedStrand

class AttachMode(QObject):
    # Signal emitted when a new strand is created
    strand_created = pyqtSignal(object)
    strand_attached = pyqtSignal(object, object)  # New signal: parent_strand, new_strand

    def __init__(self, canvas):
        """Initialize the AttachMode."""
        super().__init__()
        self.canvas = canvas
        self.affected_strand = None
        self.affected_point = None
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
        if self.canvas.current_strand:
            # Snap the final position to the grid once on release
            final_snapped_pos = self.canvas.snap_to_grid(event.pos())
            self.canvas.current_strand.end = final_snapped_pos
            self.canvas.current_strand.update_shape()
            self.canvas.update()

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
        
        # Reset all properties including affected_strand
        self.affected_strand = None
        self.canvas.current_strand = None
        self.move_timer.stop()
        self.start_pos = None
        self.current_end = None
        self.target_pos = None
        self.last_snapped_pos = None
        self.accumulated_delta = QPointF(0, 0)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if self.canvas.current_mode == "move":
            return

        if self.canvas.is_first_strand:
            # Get current set from layer panel, ensuring we skip masked strands
            current_set = 1
            if hasattr(self.canvas, 'layer_panel'):
                existing_sets = {int(s.layer_name.split('_')[0]) for s in self.canvas.strands 
                               if not isinstance(s, MaskedStrand) and '_' in s.layer_name}
                while current_set in existing_sets:
                    current_set += 1
                self.canvas.layer_panel.current_set = current_set
            
            self.start_pos = self.canvas.snap_to_grid(event.pos())
            new_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width,
                              self.canvas.strand_color, self.canvas.stroke_color,
                              self.canvas.stroke_width)
            new_strand.is_first_strand = True
            new_strand.set_number = current_set
            
            if hasattr(self.canvas, 'layer_panel'):
                count = 1  # First strand in the set
                new_strand.layer_name = f"{current_set}_{count}"
                self.canvas.layer_panel.set_counts[current_set] = count
                logging.info(f"Created first strand with set {current_set}, count {count}")
                
            self.canvas.current_strand = new_strand
            self.current_end = self.start_pos
            self.last_snapped_pos = self.start_pos
            self.move_timer.start(16)
        elif self.canvas.selected_strand and not self.is_attaching:
            self.handle_strand_attachment(event.pos())

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.canvas.current_strand:
            # 1) Move freely, no snap, for a smooth drag
            free_pos = event.pos()
            self.canvas.current_strand.end = free_pos
            self.canvas.current_strand.update_shape()

            if not self.move_timer.isActive():
                self.move_timer.start(16)

            self.canvas.update()

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

        # Calculate the new end point with gradual movement
        current_length = (self.canvas.current_strand.end - self.start_pos).manhattanLength()
        target_length = max(self.canvas.grid_size, math.hypot(dx, dy))
        
        # Move the length gradually
        step_size = self.canvas.grid_size * self.move_speed
        new_length = min(current_length + step_size, target_length)
        
        # Calculate the new end position
        new_x = self.start_pos.x() + new_length * math.cos(math.radians(rounded_angle))
        new_y = self.start_pos.y() + new_length * math.sin(math.radians(rounded_angle))
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
        """Start the attachment process for a new strand."""
        logging.info(f"[AttachMode.start_attachment] Starting attachment to parent strand {parent_strand.layer_name} at side {side}")
        
        # Find the parent strand's group before creating new strand
        parent_group = None
        parent_group_name = None
        if hasattr(self.canvas, 'groups'):
            for group_name, group_data in self.canvas.groups.items():
                if parent_strand.layer_name in group_data.get('layers', []):
                    parent_group = group_data
                    parent_group_name = group_name
                    logging.info(f"[AttachMode.start_attachment] Found parent strand in group: {group_name}")
                    break
        
        self.affected_strand = parent_strand
        self.affected_point = side

        new_strand = AttachedStrand(parent_strand, attach_point)
        new_strand.canvas = self.canvas
        
        # Set properties from parent strand
        new_strand.color = parent_strand.color  # Directly set color property
        new_strand.set_number = parent_strand.set_number
        new_strand.is_first_strand = False
        new_strand.is_start_side = False
        
        # Ensure the color is properly set in the canvas's color management system
        if hasattr(self.canvas, 'strand_colors'):
            self.canvas.strand_colors[new_strand.set_number] = parent_strand.color
            logging.info(f"[AttachMode.start_attachment] Set color for set {new_strand.set_number} to {parent_strand.color}")
        
        # Update parent strand
        parent_strand.attached_strands.append(new_strand)
        parent_strand.has_circles[side] = True
        parent_strand.update_attachable()
        
        # Setup canvas and position
        self.canvas.current_strand = new_strand
        self.is_attaching = True
        self.last_snapped_pos = self.canvas.snap_to_grid(attach_point)
        self.target_pos = self.last_snapped_pos

        # Update layer name
        if self.canvas.layer_panel:
            set_number = parent_strand.set_number
            count = len([s for s in self.canvas.strands if s.set_number == set_number]) + 1
            new_strand.layer_name = f"{set_number}_{count}"
            logging.info(f"Created new strand with layer name: {new_strand.layer_name}")

        # If parent was in a group, update group data
        if parent_group and parent_group_name:
            if parent_group_name not in self.canvas.groups:
                logging.warning(f"Group {parent_group_name} not found in canvas.groups")
                logging.info(f"Recreating group with data: {parent_group}")
                self.canvas.groups[parent_group_name] = parent_group
                
            logging.info(f"Group {parent_group_name} main_strands before adding new strand: {self.canvas.groups[parent_group_name].get('main_strands', [])}")
            # Add new strand to group
            self.canvas.groups[parent_group_name]['layers'].append(new_strand.layer_name)
            self.canvas.groups[parent_group_name]['strands'].append(new_strand)
            logging.info(f"Added new strand {new_strand.layer_name} to group {parent_group_name}")
            logging.info(f"Group {parent_group_name} main_strands after adding new strand: {self.canvas.groups[parent_group_name].get('main_strands', [])}")

        # Call canvas's attach_strand method
        self.canvas.attach_strand(parent_strand, new_strand)
        
        # Emit signals
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
