from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QFont, QFontMetrics, QImage
import logging
from attach_mode import AttachMode
from move_mode import MoveMode
from mask_mode import MaskMode  # Add this import
from strand import Strand, AttachedStrand, MaskedStrand
from PyQt5.QtCore import QTimer
from angle_adjust_mode import AngleAdjustMode
from PyQt5.QtWidgets import QWidget, QMenu, QAction
import math
from math import radians, cos, sin, atan2, degrees
from rotate_mode import RotateMode
from translations import translations
class StrandDrawingCanvas(QWidget):
    strand_selected = pyqtSignal(int)  # New signal to emit when a strand is selected
    strand_created = pyqtSignal(object)
    strand_selected = pyqtSignal(int)
    mask_created = pyqtSignal(int, int)
    angle_adjust_completed = pyqtSignal()  # Add this line
    language_changed = pyqtSignal()  # Signal to emit when language changes

    def __init__(self, parent=None):
        """Initialize the StrandDrawingCanvas."""
        super().__init__(parent)
        self.setMinimumSize(700, 700)  # Set minimum size for the canvas
        self.initialize_properties()
        self.setup_modes()
        self.highlight_color = QColor(255, 0, 0, 255)  # Semi-transparent red
        angle_adjust_completed = pyqtSignal()
    
        # Add these new attributes
        self.is_drawing_new_strand = False
        self.new_strand_set_number = None
        self.new_strand_start_point = None
        self.new_strand_end_point = None
        self.stroke_color = Qt.black
        self.strand_width = 46  # Width of strands
        self.stroke_width = 4  # Width of the black outline
        self.group_layer_manager = None
        
        # Add new attributes for group moving
        self.moving_group = False
        self.move_group_name = None
        self.move_group_layers = None
        self.move_start_pos = None
        
        self.groups = {}  # Add this line to initialize the groups attribute
        self.rotating_group = None
        self.rotation_center = None
        self.original_strand_positions = {}
        
        self.rotate_mode = RotateMode(self)

        self.parent_window = parent  # Keep a reference to the main window
        # Initialize language_code
        self.language_code = 'en'  # Default to English
        if hasattr(self.parent_window, 'language_code'):
            self.language_code = self.parent_window.language_code

    def update_translations(self):
        """Update any text elements in the canvas that require translation."""
        _ = translations[self.language_code]
        # If the canvas has text elements that need updating, implement them here.
        # For example, if you have tooltips or context menus:
        # self.some_action.setToolTip(_['some_tooltip'])
        pass  # Remove or replace this line with actual translation updates

       
    def set_language(self, language_code):
        self.language_code = language_code
        self.language_changed.emit(language_code)
    def set_theme(self, theme_name):
        if theme_name == "Dark":
            self.setStyleSheet("""
                background-color: #2C2C2C;
                /* Add styles specific to the canvas if needed */
            """)
        else:
            self.setStyleSheet("""
                background-color: #FFFFFF;
                /* Add styles specific to the canvas if needed */
            """)
        self.update()
    def start_group_rotation(self, group_name):
        if self.group_layer_manager and self.group_layer_manager.group_panel:
            # Synchronize group data from GroupPanel
            group_data = self.group_layer_manager.group_panel.groups.get(group_name)
            if group_data:
                self.groups[group_name] = group_data
            else:
                logging.warning(f"Group '{group_name}' not found in GroupPanel")
        else:
            logging.error("GroupLayerManager or GroupPanel not properly connected to StrandDrawingCanvas")
            return

        if group_name in self.groups:
            self.rotating_group = group_name
            group_data = self.groups[group_name]
            self.original_strand_positions = {}
            for strand in group_data['strands']:
                self.original_strand_positions[strand] = {
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end)
                }
            # Calculate center
            self.calculate_group_center(group_data['strands'])
            logging.info(f"Started rotation for group '{group_name}'")
            self.update()
        else:
            logging.warning(f"Attempted to start rotation for non-existent group: {group_name}")

    def rotate_group(self, group_name, angle):
        if group_name in self.groups and self.rotating_group == group_name:
            group_data = self.groups[group_name]
            center = self.rotation_center  # Use the center calculated during start
            angle_delta = angle - self.current_rotation_angle  # Calculate delta angle
            self.current_rotation_angle = angle  # Update the current rotation angle

            for strand in group_data['strands']:
                original_pos = self.original_strand_positions.get(strand)
                if original_pos:
                    strand.start = self.rotate_point(original_pos['start'], center, angle)
                    strand.end = self.rotate_point(original_pos['end'], center, angle)
                    strand.update_shape()
                    if hasattr(strand, 'update_side_line'):
                        strand.update_side_line()
            self.update()
        else:
            logging.warning(f"Attempted to rotate non-existent or inactive group: {group_name}")


    def rotate_point(self, point, center, angle):
        angle_rad = math.radians(angle)
        s = math.sin(angle_rad)
        c = math.cos(angle_rad)

        # Translate point to origin
        translated_x = point.x() - center.x()
        translated_y = point.y() - center.y()

        # Rotate point
        rotated_x = translated_x * c - translated_y * s
        rotated_y = translated_x * s + translated_y * c

        # Translate point back
        new_x = rotated_x + center.x()
        new_y = rotated_y + center.y()

        return QPointF(new_x, new_y)


    def rotate_strand(self, strand, center, angle):
        strand.start = self.rotate_point(strand.start, center, angle)
        strand.end = self.rotate_point(strand.end, center, angle)

    def calculate_group_center(self, strands):
        all_points = []
        for strand in strands:
            all_points.extend([strand.start, strand.end])
        if all_points:
            center_x = sum(point.x() for point in all_points) / len(all_points)
            center_y = sum(point.y() for point in all_points) / len(all_points)
            self.rotation_center = QPointF(center_x, center_y)
        else:
            self.rotation_center = QPointF(0, 0)
        self.current_rotation_angle = 0  # Initialize rotation angle
    def update_group_data(self, group_name, group_data):
        self.groups[group_name] = group_data.copy()
        logging.info(f"Canvas group data updated for group '{group_name}'")
    def finish_group_rotation(self, group_name):
        if self.rotating_group == group_name:
            self.rotating_group = None
            self.rotation_center = None
            self.current_rotation_angle = 0
            self.original_strand_positions.clear()
            logging.info(f"Finished rotation for group '{group_name}'")
            self.update()
        else:
            logging.warning(f"Attempted to finish rotation for inactive group: {group_name}")

             
    def create_strand(self, start, end, set_number):
        new_strand = Strand(start, end, self.strand_width, self.strand_color, self.stroke_color, self.stroke_width)
        new_strand.set_number = set_number
        new_strand.layer_name = f"{set_number}_{len([s for s in self.strands if s.set_number == set_number]) + 1}"
        self.strands.append(new_strand)
        logging.info(f"Created new strand: {new_strand.layer_name}")
        self.strand_created.emit(new_strand)
        return new_strand
    def initialize_original_positions(self, group_name):
        if self.group_layer_manager is None:
            return
        group_data = self.group_layer_manager.group_panel.groups.get(group_name)
        if group_data:
            # Initialize original positions for all strands in group_data['strands']
            for strand in group_data['strands']:
                if not hasattr(strand, 'original_start'):
                    strand.original_start = QPointF(strand.start)
                if not hasattr(strand, 'original_end'):
                    strand.original_end = QPointF(strand.end)


    def extract_main_layer(self, layer_name):
        """Extract the main layer number from a layer name."""
        parts = layer_name.split('_')
        if parts:
            return parts[0]  # Assuming the main layer is the first part
        return None

    def find_attached_strands(self, strand):
        attached = []
        for other_strand in self.strands:
            if other_strand != strand:
                if self.is_strand_attached(strand, other_strand):
                    attached.append(other_strand)
        return attached

    def is_strand_attached(self, strand1, strand2):
        return (strand1.start == strand2.start or
                strand1.start == strand2.end or
                strand1.end == strand2.start or
                strand1.end == strand2.end)

 









    def reset_group_move(self, group_name):
        """
        Resets the group move operation by deleting temporary attributes
        used during the movement.
        """
        if group_name not in self.groups:
            logging.error(f"Group '{group_name}' not found in canvas.")
            return

        strands = self.groups[group_name]['strands']

        for strand in strands:
            if isinstance(strand, MaskedStrand):
                # Skip masked strands
                continue

            # Delete temporary attributes if they exist
            if hasattr(strand, 'original_start'):
                del strand.original_start
            if hasattr(strand, 'original_end'):
                del strand.original_end

            # Reset attached strands
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    if isinstance(attached_strand, MaskedStrand):
                        continue

                    if hasattr(attached_strand, 'original_start'):
                        del attached_strand.original_start
                    if hasattr(attached_strand, 'original_end'):
                        del attached_strand.original_end

        self.update()
    def snap_group_to_grid(self, group_name):
        """
        Snaps all points of strands and attached strands (excluding masked strands)
        in the specified group to the closest points on the grid.
        """
        if group_name not in self.groups:
            logging.error(f"Group '{group_name}' not found in canvas.")
            return

        grid_size = self.grid_size  # Ensure grid_size is defined in your class

        strands = self.groups[group_name]['strands']

        for strand in strands:
            if isinstance(strand, MaskedStrand):
                # Skip masked strands
                continue

            # Snap start and end points of the strand
            strand.start = self.snap_point_to_grid(strand.start, grid_size)
            strand.end = self.snap_point_to_grid(strand.end, grid_size)
            strand.update_shape()

            # Update any side lines if applicable
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()

            # Snap attached strands
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    if isinstance(attached_strand, MaskedStrand):
                        continue

                    attached_strand.start = self.snap_point_to_grid(attached_strand.start, grid_size)
                    attached_strand.end = self.snap_point_to_grid(attached_strand.end, grid_size)
                    attached_strand.update_shape()

                    if hasattr(attached_strand, 'update_side_line'):
                        attached_strand.update_side_line()

        self.update()
    def snap_group_to_grid(self, group_name):
        """
        Snaps all points of strands and attached strands (excluding masked strands)
        in the specified group to the closest points on the grid.
        """
        if group_name not in self.groups:
            logging.error(f"Group '{group_name}' not found in canvas.")
            return

        grid_size = self.grid_size  # Ensure grid_size is defined in your class

        strands = self.groups[group_name]['strands']

        for strand in strands:
            if isinstance(strand, MaskedStrand):
                # Skip masked strands
                continue

            # Snap start and end points of the strand
            strand.start = self.snap_point_to_grid(strand.start, grid_size)
            strand.end = self.snap_point_to_grid(strand.end, grid_size)
            strand.update_shape()

            # Update any side lines if applicable
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()

            # Snap attached strands
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    if isinstance(attached_strand, MaskedStrand):
                        continue

                    attached_strand.start = self.snap_point_to_grid(attached_strand.start, grid_size)
                    attached_strand.end = self.snap_point_to_grid(attached_strand.end, grid_size)
                    attached_strand.update_shape()

                    if hasattr(attached_strand, 'update_side_line'):
                        attached_strand.update_side_line()

        self.update()

    def snap_point_to_grid(self, point, grid_size):
        """
        Snaps a QPointF to the closest grid point based on the grid size.
        """
        x = round(point.x() / grid_size) * grid_size
        y = round(point.y() / grid_size) * grid_size
        return QPointF(x, y)

    def update_strands(self, strands):
        for strand in strands:
            strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()
        self.update()



    def start_group_move(self, group_name, layers):
        # Refresh group data
        self.refresh_group_data(group_name)
        # Proceed with setting up moving group
        self.moving_group = True
        self.move_group_name = group_name
        self.move_group_layers = layers
        self.move_start_pos = None
        self.setCursor(Qt.OpenHandCursor)

    def refresh_group_data(self, group_name):
        if hasattr(self, 'group_layer_manager') and self.group_layer_manager.group_panel:
            group_data = self.group_layer_manager.group_panel.groups.get(group_name)
            if not group_data:
                logging.warning(f"Group '{group_name}' not found in GroupPanel")
                return
            # Get main set numbers from group data
            main_set_numbers = group_data.get('main_set_numbers', [])
            # Clear current group layers and strands
            group_data['layers'] = []
            group_data['strands'] = []
            # Iterate over all strands to find those that belong to the group
            for strand in self.strands:
                if strand.layer_name:
                    if str(strand.set_number) in main_set_numbers:
                        # Add the strand to group data
                        if strand.layer_name not in group_data['layers']:
                            group_data['layers'].append(strand.layer_name)
                            group_data['strands'].append(strand)
                            logging.info(f"Added strand '{strand.layer_name}' to group '{group_name}' during refresh")
        else:
            logging.error("GroupLayerManager or GroupPanel not properly connected to StrandDrawingCanvas")


    def move_group_strands(self, group_name, dx, dy):
        logging.info(f"Moving group '{group_name}' by dx={dx}, dy={dy}")
        if hasattr(self, 'group_layer_manager') and self.group_layer_manager:
            group_data = self.group_layer_manager.group_panel.groups.get(group_name)
            if group_data:
                updated_strands = set()
                group_strands = []
                original_points = {}
                affected_strands = []

                # First pass: Collect all group strands from group_data['layers']
                for layer_name in group_data['layers']:
                    strand = self.find_strand_by_name(layer_name)
                    if strand:
                        group_strands.append(strand)
                        original_points[strand.start] = QPointF(strand.start)
                        original_points[strand.end] = QPointF(strand.end)

                # Additional logic: Find all strands that start with the same set number as the main strands
                main_set_numbers = group_data.get('main_strands', [])

                # Now find all strands that belong to these main set numbers and add if not already in group_strands
                for strand in self.strands:
                    if strand not in group_strands:
                        if strand.layer_name:
                            parts = strand.layer_name.split('_')
                            if len(parts) >= 2 and parts[0] in main_set_numbers:
                                group_strands.append(strand)
                                original_points[strand.start] = QPointF(strand.start)
                                original_points[strand.end] = QPointF(strand.end)

                                # Also add to group_data to keep it updated
                                group_data['strands'].append(strand)
                                group_data['layers'].append(strand.layer_name)
                                logging.info(f"Added new strand '{strand.layer_name}' to group '{group_name}' during move")

                # Second pass: Move group strands and update all connected strands
                for strand in self.strands:
                    if strand in group_strands:
                        self.move_strand_and_update(strand, dx, dy, updated_strands)
                        affected_strands.append(strand)
                    else:
                        # Check if this strand is connected to any group strand
                        start_updated = False
                        end_updated = False

                        for original_point, new_point in original_points.items():
                            if self.points_are_close(strand.start, original_point):
                                strand.start = QPointF(strand.start.x() + dx, strand.start.y() + dy)
                                start_updated = True
                            if self.points_are_close(strand.end, original_point):
                                strand.end = QPointF(strand.end.x() + dx, strand.end.y() + dy)
                                end_updated = True

                        if start_updated or end_updated:
                            strand.update_shape()
                            if hasattr(strand, 'update_side_line'):
                                strand.update_side_line()
                            updated_strands.add(strand)
                            affected_strands.append(strand)
                            logging.info(f"Updated connected strand '{strand.layer_name}' that shares points with group strands")

                # Update group_data with new positions of all affected strands
                for strand in affected_strands:
                    strand_data = {
                        'start': QPointF(strand.start),
                        'end': QPointF(strand.end)
                    }
                    if strand.layer_name in group_data['layers']:
                        index = group_data['layers'].index(strand.layer_name)
                        group_data['strands'][index] = strand

                # Update the group panel
                self.group_layer_manager.group_panel.update_group(group_name, group_data)

                # Force a redraw of the canvas
                self.update()
            else:
                logging.warning(f"No group data found for group '{group_name}'")
        else:
            logging.error("GroupLayerManager not properly connected to StrandDrawingCanvas")

    def mousePressEvent(self, event):
        if self.group_layer_manager and self.group_layer_manager.move_mode:
            self.group_layer_manager.start_group_move(event.pos())
        else:
            super().mousePressEvent(event)

    def initialize_properties(self):
        """Initialize all properties used in the StrandDrawingCanvas."""
        self.strands = []  # List to store all strands
        self.current_strand = None  # Currently active strand
        self.strand_width = 46  # Width of strands
        self.strand_color = QColor('purple')  # Default color for strands
        self.stroke_color = Qt.black  # Color for strand outlines
        self.stroke_width = 4  # Width of strand outlines
        self.highlight_color = Qt.red  # Color for highlighting selected strands
        self.highlight_width = 20  # Width of highlight
        self.is_first_strand = True  # Flag to indicate if it's the first strand being drawn
        self.selection_color = QColor(255, 0, 0, 128)  # Color for selection rectangle
        self.selected_strand_index = None  # Index of the currently selected strand
        self.layer_panel = None  # Reference to the layer panel
        self.selected_strand = None  # Currently selected strand
        self.last_selected_strand_index = None  # Index of the last selected strand
        self.strand_colors = {}  # Dictionary to store colors for each strand set
        self.grid_size = 26  # Size of grid cells
        self.show_grid = True  # Flag to show/hide grid
        self.should_draw_names = False  # Flag to show/hide strand names
        self.newest_strand = None  # Track the most recently created strand
        self.is_angle_adjusting = False  # Add this line
        self.mask_mode_active = False
        self.mask_selected_strands = []
    def start_new_strand_mode(self, set_number):
        self.new_strand_set_number = set_number
        self.new_strand_start_point = None
        self.new_strand_end_point = None
        self.is_drawing_new_strand = True
        self.setCursor(Qt.CrossCursor)
        # Keep the current mode, don't set it to None
        logging.info(f"Entered new strand mode for set: {set_number}")
    def setup_modes(self):
        """Set up attach, move, and mask modes."""
        # Attach mode setup
        self.attach_mode = AttachMode(self)
        self.attach_mode.strand_created.connect(self.on_strand_created)

        # Move mode setup
        self.move_mode = MoveMode(self)

        # Mask mode setup
        self.mask_mode = MaskMode(self)
        self.mask_mode.mask_created.connect(self.create_masked_layer)

        # Angle adjust mode setup (if used)
        self.angle_adjust_mode = AngleAdjustMode(self)

        # Set initial mode to attach
        self.current_mode = self.attach_mode

        # Connect mode-specific signals (if any)
        # For example:
        # self.move_mode.strand_moved.connect(self.on_strand_moved)
        # self.angle_adjust_mode.angle_adjusted.connect(self.on_angle_adjusted)

        # Initialize mode-specific properties
        self.is_angle_adjusting = False
        self.mask_mode_active = False


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.show_grid:
            self.draw_grid(painter)

        # Create a temporary image for all strands
        temp_image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        logging.info(f"Painting {len(self.strands)} strands")
        # Draw all strands in their current order
        for strand in self.strands:
            logging.info(f"Drawing strand '{strand.layer_name}' at ({strand.start.x()}, {strand.start.y()}) to ({strand.end.x()}, {strand.end.y()})")
            if strand == self.selected_strand:
                logging.info(f"Drawing highlighted selected strand: {strand.layer_name}")
                self.draw_highlighted_strand(temp_painter, strand)
            else:
                strand.draw(temp_painter)

        # Draw the temporary image with all strands onto the main painter
        temp_painter.end()
        painter.drawImage(0, 0, temp_image)

        if self.current_strand:
            self.current_strand.draw(painter)

        if self.should_draw_names:
            for strand in self.strands:
                self.draw_strand_label(painter, strand)

        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.setBrush(QBrush(self.selection_color))
            painter.setPen(QPen(Qt.red, 5))
            painter.drawRect(self.current_mode.selected_rectangle)

        # Draw the angle adjustment visualization if in angle adjust mode
        if hasattr(self, 'is_angle_adjusting') and self.is_angle_adjusting and hasattr(self, 'angle_adjust_mode'):
            self.angle_adjust_mode.draw(painter)

        # Draw mask mode selections
        if self.current_mode == self.mask_mode:
            for strand in self.mask_mode.selected_strands:
                self.draw_highlighted_strand(painter, strand)

        # Draw the new strand being created
        if self.is_drawing_new_strand and self.new_strand_start_point and self.new_strand_end_point:
            # Determine the color for the new strand
            if self.new_strand_set_number in self.strand_colors:
                strand_color = self.strand_colors[self.new_strand_set_number]
            else:
                # If it's the first strand (no existing colors), use the default color
                strand_color = QColor('purple')

     
            # Draw the colored strand
            painter.setPen(QPen(QColor('black'),self.stroke_width, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            painter.drawLine(self.new_strand_start_point, self.new_strand_end_point)

        logging.info(f"Paint event completed. Selected strand: {self.selected_strand.layer_name if self.selected_strand else 'None'}, "
                     f"Newest strand: {self.newest_strand.layer_name if self.newest_strand else 'None'}")
    def create_masked_layer(self, strand1, strand2):
        """
        Create a masked layer from two selected strands.

        Args:
            strand1 (Strand): The first strand to be masked.
            strand2 (Strand): The second strand to be masked.
        """
        logging.info(f"Attempting to create masked layer for {strand1.layer_name} and {strand2.layer_name}")

        # Check if a masked layer already exists for these strands
        if self.mask_exists(strand1, strand2):
            logging.info(f"Masked layer for {strand1.layer_name} and {strand2.layer_name} already exists.")
            return

        # Create the new masked strand
        masked_strand = MaskedStrand(strand1, strand2)
        
        # Add the new masked strand to the canvas
        self.add_strand(masked_strand)
        
        # Update the layer panel if it exists
        if self.layer_panel:
            button = self.layer_panel.add_masked_layer_button(
                self.strands.index(strand1),
                self.strands.index(strand2)
            )
            button.color_changed.connect(self.handle_color_change)
        
        # Set the color of the masked strand
        # You might want to adjust this based on your color scheme
        masked_strand.set_color(strand1.color)
        
        # Update the masked strand's layer name
        masked_strand.layer_name = f"{strand1.layer_name}_{strand2.layer_name}"
        
        # Log the creation of the masked layer
        logging.info(f"Created masked layer: {masked_strand.layer_name}")
        
        # Clear any existing selection
        self.clear_selection()
        
        # Move the new masked strand to the top of the drawing order
        self.move_strand_to_top(masked_strand)
        
        # Force a redraw of the canvas
        self.update()
        
        # Emit a signal if needed (e.g., to update other parts of the UI)
        # self.mask_created.emit(masked_strand)  # Uncomment if you have this signal
        
        # If you're using an undo stack, you might want to add this action to it
        # self.undo_stack.push(CreateMaskCommand(self, strand1, strand2, masked_strand))
        
        # Return the new masked strand in case it's needed
        return masked_strand

    def mask_exists(self, strand1, strand2):
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                if (strand.first_selected_strand == strand1 and strand.second_selected_strand == strand2) or \
                (strand.first_selected_strand == strand2 and strand.second_selected_strand == strand1):
                    return True
        return False
    
    def handle_color_change(self, set_number, color):
        """Handle color change for a set of strands."""
        self.update_color_for_set(set_number, color)
        if self.layer_panel:
            self.layer_panel.update_colors_for_set(set_number, color)
        self.update()
    def draw_grid(self, painter):
        """Draw the grid on the canvas."""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        # Vertical lines
        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
        # Horizontal lines
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)
    def draw_strand_label(self, painter, strand):
        """Draw the label for a strand."""
        if isinstance(strand, MaskedStrand):
            mask_path = strand.get_mask_path()
            center = mask_path.boundingRect().center()
        else:
            center = (strand.start + strand.end) / 2

        text = getattr(strand, 'layer_name', f"{strand.set_number}_1")
        font = painter.font()
        font.setPointSize(12)  # You can adjust this value to change the font size
        painter.setFont(font)

        metrics = painter.fontMetrics()
        text_width = metrics.width(text)
        text_height = metrics.height()

        text_rect = QRectF(center.x() - text_width / 2, center.y() - text_height / 2, text_width, text_height)

        text_path = QPainterPath()
        text_path.addText(text_rect.center().x() - text_width / 2, text_rect.center().y() + text_height / 4, font, text)

        if isinstance(strand, MaskedStrand):
            painter.setClipPath(mask_path)

        # Draw white outline
        painter.setPen(QPen(Qt.white, 6, Qt.SolidLine))
        painter.drawPath(text_path)

        # Draw black text
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.fillPath(text_path, QBrush(Qt.black))
        painter.drawPath(text_path)

        if isinstance(strand, MaskedStrand):
            painter.setClipping(False)

    def draw_highlighted_strand(self, painter, strand):
        """Draw a highlighted version of a strand."""
        if isinstance(strand, MaskedStrand):
            self.draw_highlighted_masked_strand(painter, strand)
        else:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            def set_highlight_pen(width_adjustment=0):
                pen = QPen(self.highlight_color, self.highlight_width + width_adjustment)
                pen.setJoinStyle(Qt.MiterJoin)
                pen.setCapStyle(Qt.SquareCap)
                painter.setPen(pen)

            set_highlight_pen()
            painter.drawPath(strand.get_path())

            set_highlight_pen(0.5)
            for i, has_circle in enumerate(strand.has_circles):
                if has_circle:
                    center = strand.start if i == 0 else strand.end
                    painter.drawEllipse(center, strand.width / 2, strand.width / 2)

            painter.restore()
            strand.draw(painter)

    def draw_highlighted_masked_strand(self, painter, masked_strand):
        """Draw a highlighted version of a masked strand."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        masked_strand.draw(temp_painter)

        highlight_pen = QPen(self.highlight_color, self.stroke_width+4)
        highlight_pen.setJoinStyle(Qt.MiterJoin)
        highlight_pen.setCapStyle(Qt.SquareCap)
        temp_painter.setPen(highlight_pen)
        temp_painter.drawPath(masked_strand.get_mask_path())

        temp_painter.end()

        painter.drawImage(0, 0, temp_image)

        painter.restore()

    def set_layer_panel(self, layer_panel):
        """Set the layer panel and connect signals."""
        self.layer_panel = layer_panel
        if hasattr(self.layer_panel, 'draw_names_requested'):
            self.layer_panel.draw_names_requested.connect(self.toggle_name_drawing)

    def toggle_name_drawing(self, should_draw):
        """Toggle the drawing of strand names."""
        self.should_draw_names = should_draw
        self.update()

    def enable_name_drawing(self):
        """Enable the drawing of strand names."""
        self.should_draw_names = True
        self.update()


    def update_color_for_set(self, set_number, color):
        """Update the color for a set of strands."""
        logging.info(f"Updating color for set {set_number} to {color.name()}")
        self.strand_colors[set_number] = color
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                # For masked strands, only update if the set_number is the first part
                mask_parts = strand.layer_name.split('_')
                if mask_parts[0] == str(set_number):
                    strand.set_color(color)
                    logging.info(f"Updated color for masked strand: {strand.layer_name}")
            elif isinstance(strand, Strand):
                # For regular strands, only update if the set_number matches exactly
                if strand.set_number == set_number:
                    strand.set_color(color)
                    logging.info(f"Updated color for strand: {strand.layer_name}")
                    self.update_attached_strands_color(strand, color)
        self.update()
        logging.info(f"Finished updating color for set {set_number}")

    def update_attached_strands_color(self, parent_strand, color):
        """Recursively update the color of attached strands."""
        for attached_strand in parent_strand.attached_strands:
            attached_strand.set_color(color)
            logging.info(f"Updated color for attached strand: {attached_strand.layer_name}")
            self.update_attached_strands_color(attached_strand, color)

    def on_strand_created(self, strand):
        """Handle the creation of a new strand."""
        logging.info(f"Starting on_strand_created for strand: {strand.layer_name}")
        
        if hasattr(strand, 'is_being_deleted') and strand.is_being_deleted:
            logging.info("Strand is being deleted, skipping creation process")
            return

        # Determine the set number for the new strand
        if isinstance(strand, AttachedStrand):
            set_number = strand.parent.set_number
        elif self.selected_strand:
            set_number = self.selected_strand.set_number
        else:
            set_number = max(self.strand_colors.keys(), default=0) + 1

        strand.set_number = set_number

        # Assign color to the new strand
        if set_number not in self.strand_colors:
            self.strand_colors[set_number] = QColor('purple')
        strand.set_color(self.strand_colors[set_number])

        # Add the new strand to the strands list
        self.strands.append(strand)
        
        # Set this as the newest strand to ensure it's drawn on top
        self.newest_strand = strand

        # Update layer panel
        if self.layer_panel:
            set_number = int(strand.set_number) if isinstance(strand.set_number, str) else strand.set_number
            count = len([s for s in self.strands if s.set_number == set_number])
            strand.layer_name = f"{set_number}_{count}"
            
            if not hasattr(strand, 'is_being_deleted'):
                logging.info(f"Adding new layer button for set {set_number}, count {count}")
                self.layer_panel.add_layer_button(set_number, count)
            else:
                logging.info(f"Updating layer names for set {set_number}")
                self.layer_panel.update_layer_names(set_number)
            
            self.layer_panel.on_color_changed(set_number, self.strand_colors[set_number])

        # Select the new strand if it's not an attached strand
        if not isinstance(strand, AttachedStrand):
            self.select_strand(len(self.strands) - 1)
        
        self.update()
        
        # Notify LayerPanel that a new strand was added
        if self.layer_panel:
            self.layer_panel.update_attachable_states()
        
        # --- Begin new code to update group data ---
        # Update group data if the new strand belongs to an existing group
        if hasattr(self, 'group_layer_manager') and self.group_layer_manager:
            group_panel = self.group_layer_manager.group_panel
            if group_panel:
                main_set_number = str(strand.set_number)
                for group_name, group_data in group_panel.groups.items():
                    # Assuming 'main_strands' stores main set numbers associated with the group
                    if 'main_strands' in group_data:
                        if main_set_number in group_data['main_strands']:
                            # Add the new strand to the group if not already present
                            if strand.layer_name not in group_data['layers']:
                                group_data['layers'].append(strand.layer_name)
                                group_data['strands'].append(strand)
                                logging.info(f"Added new strand '{strand.layer_name}' to group '{group_name}'")
                                # Update the group panel display
                                group_panel.update_group_display(group_name, group_data['layers'])
        # --- End new code ---

        logging.info("Finished on_strand_created")




    def attach_strand(self, parent_strand, new_strand):
        """Attach a new strand to a parent strand."""
        parent_strand.attached_strands.append(new_strand)
        new_strand.parent = parent_strand
        
        # Set the set_number for the new strand
        new_strand.set_number = parent_strand.set_number
        
        # Append the new strand to the strands list
        self.strands.append(new_strand)
        
        # Set this as the newest strand to ensure it's drawn on top
        self.newest_strand = new_strand
        
        # Calculate the correct count for the new strand
        count = len([s for s in self.strands if s.set_number == new_strand.set_number])
        new_strand.layer_name = f"{new_strand.set_number}_{count}"
        
        # Set the color for the new strand
        if new_strand.set_number in self.strand_colors:
            new_strand.set_color(self.strand_colors[new_strand.set_number])
        
        # Update the layer panel
        if self.layer_panel:
            if not hasattr(new_strand, 'is_being_deleted'):
                self.layer_panel.add_layer_button(new_strand.set_number, count)
            else:
                self.layer_panel.update_layer_names(new_strand.set_number)
            self.layer_panel.on_strand_attached()
        
        # Update the canvas
        self.update()
        
        logging.info(f"Attached new strand: {new_strand.layer_name} to parent: {parent_strand.layer_name}")

    def move_strand_to_top(self, strand):
        """Move a strand to the top of the drawing order and update the layer panel."""
        if strand in self.strands:
            # Remove the strand from its current position
            self.strands.remove(strand)
            # Add the strand to the end of the list (top of the drawing order)
            self.strands.append(strand)
            
            # Update the layer panel to reflect the new order
            if self.layer_panel:
                # Get the current index of the strand in the layer panel
                current_index = self.layer_panel.layer_buttons.index(
                    next(button for button in self.layer_panel.layer_buttons if button.text() == strand.layer_name)
                )
                
                # Move the corresponding button to the top of the layer panel
                button = self.layer_panel.layer_buttons.pop(current_index)
                self.layer_panel.layer_buttons.insert(0, button)
                
                # Refresh the layer panel UI
                self.layer_panel.refresh()
            
            # Update the canvas
            self.update()
            
            logging.info(f"Moved strand {strand.layer_name} to top")
        else:
            logging.warning(f"Attempted to move non-existent strand to top: {strand.layer_name}")
    def add_strand(self, strand):
        """Add a strand to the canvas."""
        self.strands.append(strand)
        self.update()

    def select_strand(self, index, update_layer_panel=True):
        if index is not None and 0 <= index < len(self.strands):
            self.selected_strand = self.strands[index]
            self.selected_strand_index = index
            self.last_selected_strand_index = index
            self.is_first_strand = False
            if update_layer_panel and self.layer_panel and self.layer_panel.get_selected_layer() != index:
                self.layer_panel.select_layer(index, emit_signal=False)
            self.current_mode = self.attach_mode
            self.current_mode.is_attaching = False
            self.current_strand = None
            self.strand_selected.emit(index)
            # Enable delete button for masked layers
            if isinstance(self.selected_strand, MaskedStrand) and self.layer_panel:
                self.layer_panel.delete_strand_button.setEnabled(True)
        else:
            self.selected_strand = None
            self.selected_strand_index = None
            self.strand_selected.emit(-1)  # Emit -1 for deselection
            # Disable delete button when no strand is selected
            if self.layer_panel:
                self.layer_panel.delete_strand_button.setEnabled(False)
        self.update()  # Force a redraw
        logging.info(f"Selected strand index: {index}")

    def deselect_all_strands(self):
        """Deselect all strands."""
        self.selected_strand = None
        self.selected_strand_index = None
        self.update()

    def mousePressEvent(self, event):
        if self.current_mode == "rotate":
            self.rotate_mode.mousePressEvent(event)
        elif self.moving_group:
            self.move_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif self.is_drawing_new_strand:
            self.new_strand_start_point = event.pos()
        elif self.current_mode == "select":
            self.handle_strand_selection(event.pos())
        elif self.current_mode == self.mask_mode:
            self.mask_mode.handle_mouse_press(event)
        elif self.current_mode:
            self.current_mode.mousePressEvent(event)
        else:
            super().mousePressEvent(event)

        if self.moving_group:
            self.move_group_name = self.get_group_name_at_position(event.pos())
            self.group_move_start_pos = event.pos()
            self.original_positions_initialized = False  # Will trigger re-initialization

        self.update()


    def mouseMoveEvent(self, event):
        if self.moving_group and self.group_move_start_pos:
            # Calculate total dx and dy from the initial movement start position
            total_dx = event.pos().x() - self.group_move_start_pos.x()
            total_dy = event.pos().y() - self.group_move_start_pos.y()
            self.move_group(self.move_group_name, total_dx, total_dy)
        elif self.is_drawing_new_strand and self.new_strand_start_point:
            self.new_strand_end_point = event.pos()
            self.update()
        elif self.current_mode == "rotate":
            self.rotate_mode.mouseMoveEvent(event)
        elif self.current_mode:
            self.current_mode.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_mode == "rotate":
            self.rotate_mode.mouseReleaseEvent(event)
        elif self.moving_group:
            self.moving_group = False
            self.move_group_name = None
            self.move_group_layers = None
            self.move_start_pos = None
            self.group_move_start_pos = None
            self.original_positions_initialized = False  # Reset for next movement
            self.setCursor(Qt.ArrowCursor)
        elif self.is_drawing_new_strand and self.new_strand_start_point:
            self.new_strand_end_point = event.pos()
            self.finalize_new_strand()
        elif self.current_mode:
            self.current_mode.mouseReleaseEvent(event)
        self.update()





    def finalize_new_strand(self):
        if self.new_strand_start_point and self.new_strand_end_point:
            new_strand = Strand(self.new_strand_start_point, self.new_strand_end_point, self.strand_width)
            new_strand.set_number = self.new_strand_set_number
            new_strand.set_color(self.strand_colors[self.new_strand_set_number])
            new_strand.layer_name = f"{self.new_strand_set_number}_1"  # Main strand
            new_strand.is_first_strand = True
            new_strand.is_start_side = True
            
            self.add_strand(new_strand)
            new_strand_index = len(self.strands) - 1
            
            self.selected_strand = new_strand
            self.newest_strand = new_strand
            self.selected_strand_index = new_strand_index
            
            self.is_drawing_new_strand = False
            self.new_strand_start_point = None
            self.new_strand_end_point = None
            self.setCursor(Qt.ArrowCursor)
            
            # Emit signals or call methods to update UI
            self.strand_selected.emit(new_strand_index)
            if hasattr(self, 'layer_panel'):
                self.layer_panel.on_strand_created(new_strand)
            
            logging.info(f"Created new main strand: {new_strand.layer_name}, index: {new_strand_index}")
        else:
            logging.warning("Attempted to finalize new strand without valid start and end points")
    def set_mode(self, mode):
        """
        Set the current mode of the canvas.
        
        Args:
            mode (str): The mode to set. Can be "attach", "move", "select", "mask", "angle_adjust", "new_strand", "rotate", or "new_strand".
        """
        # Deactivate the current mode if it has a deactivate method
        if hasattr(self.current_mode, 'deactivate'):
            self.current_mode.deactivate()

        # Reset any mode-specific flags
        self.is_angle_adjusting = False
        self.mask_mode_active = False
        self.is_drawing_new_strand = False

        # Set the new mode
        if mode == "attach":
            self.current_mode = self.attach_mode
            self.setCursor(Qt.CrossCursor)
        elif mode == "move":
            self.current_mode = self.move_mode
            self.setCursor(Qt.OpenHandCursor)
        elif mode == "select":
            self.current_mode = "select"  # This is a string, not an object
            self.setCursor(Qt.PointingHandCursor)
        elif mode == "mask":
            self.current_mode = self.mask_mode
            self.mask_mode_active = True
            self.setCursor(Qt.CrossCursor)
        elif mode == "angle_adjust":
            self.current_mode = self.angle_adjust_mode
            self.is_angle_adjusting = True
            self.setCursor(Qt.SizeAllCursor)
        elif mode == "new_strand":
            self.is_drawing_new_strand = True
            self.current_mode = None  # or you could set it to a default mode like self.attach_mode
            self.setCursor(Qt.CrossCursor)
        elif mode == "rotate":
            self.current_mode = self.rotate_mode
            self.setCursor(Qt.SizeAllCursor)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # If the new mode has an activate method, call it
        # For angle_adjust mode, we'll activate it separately with the selected strand
        if hasattr(self.current_mode, 'activate') and mode != "angle_adjust":
            self.current_mode.activate()

        # Clear any existing selection if switching to a different mode
        if mode != "select":
            self.clear_selection()

        # Update the canvas
        self.update()

        # Log the mode change
        logging.info(f"Canvas mode changed to: {mode}")



    def is_strand_involved_in_mask(self, masked_strand, strand):
        if isinstance(masked_strand, MaskedStrand):
            return (masked_strand.first_selected_strand == strand or
                    masked_strand.second_selected_strand == strand or
                    strand.layer_name in masked_strand.layer_name)
        return False


    def remove_related_masked_layers(self, strand):
        """
        Remove all masked layers associated with the given main strand and its attachments.
        """
        masked_layers_before = len(self.strands)
        self.strands = [s for s in self.strands if not (isinstance(s, MaskedStrand) and self.is_strand_involved_in_mask(s, strand))]
        masked_layers_removed = masked_layers_before - len(self.strands)
        logging.info(f"Removed related masked layers. Total masked layers removed: {masked_layers_removed}")
        
    def remove_strand_circles(self, strand):
        """
        Remove any circles associated with the given strand.
        """
        if hasattr(strand, 'has_circles'):
            if strand.has_circles[0]:
                strand.has_circles[0] = False
                logging.info(f"Removed start circle for strand: {strand.layer_name}")
            if strand.has_circles[1]:
                strand.has_circles[1] = False
                logging.info(f"Removed end circle for strand: {strand.layer_name}")

    def get_all_related_masked_strands(self, strand):
        """
        Get all masked strands that involve the given strand.
        This includes masks directly involving the main strand or any of its attached strands.
        """
        related_masked_strands = []
        for s in self.strands:
            if isinstance(s, MaskedStrand) and self.is_strand_involved_in_mask(s, strand):
                related_masked_strands.append(s)
        return related_masked_strands





















    def is_related_strand(self, strand, set_number):
        layer_name = strand.layer_name
        parts = layer_name.split('_')
        
        # Direct relationship: starts with set_number_
        if parts[0] == str(set_number):
            return True
        
        # Check for masked layers involving the set_number
        if len(parts) > 2 and str(set_number) in parts:
            return True
        
        return False
    def update_layer_names_for_attached_strand_deletion(self, set_number):
        logging.info(f"Updating layer names for attached strand deletion in set {set_number}")
        # Do nothing here to keep original names
        if self.layer_panel:
            self.layer_panel.update_layer_names(set_number)

    def remove_attached_strands(self, parent_strand):
        """Recursively remove all attached strands."""
        attached_strands = parent_strand.attached_strands.copy()  # Create a copy to iterate over
        for attached_strand in attached_strands:
            if attached_strand in self.strands:
                self.strands.remove(attached_strand)
                self.remove_attached_strands(attached_strand)
        parent_strand.attached_strands.clear()  # Clear the list of attached strands

    def find_parent_strand(self, attached_strand):
        for strand in self.strands:
            if attached_strand in strand.attached_strands:
                return strand
        return None

    def clear_strands(self):
        """Clear all strands from the canvas."""
        self.strands.clear()
        self.current_strand = None
        self.is_first_strand = True
        self.selected_strand_index = None
        self.update()

    def snap_to_grid(self, point):
        """Snap a point to the nearest grid intersection."""
        return QPointF(
            round(point.x() / self.grid_size) * self.grid_size,
            round(point.y() / self.grid_size) * self.grid_size
        )

    def toggle_grid(self):
        """Toggle the visibility of the grid."""
        self.show_grid = not self.show_grid
        self.update()

    def set_grid_size(self, size):
        """Set the size of the grid cells and refresh the canvas."""
        self.grid_size = size
        self.update()  # Redraw the canvas to reflect the new grid size

    def get_strand_at_position(self, pos):
        """Get the strand at the given position."""
        for strand in reversed(self.strands):  # Check from top to bottom
            if strand.get_path().contains(pos):
                return strand
        return None

    def get_strand_index(self, strand):
        """Get the index of a given strand."""
        try:
            return self.strands.index(strand)
        except ValueError:
            return -1

    def move_strand_to_front(self, strand):
        """Move a strand to the front (top) of the drawing order."""
        if strand in self.strands:
            self.strands.remove(strand)
            self.strands.append(strand)
            self.update()

    def move_strand_to_back(self, strand):
        """Move a strand to the back (bottom) of the drawing order."""
        if strand in self.strands:
            self.strands.remove(strand)
            self.strands.insert(0, strand)
            self.update()

    def get_bounding_rect(self):
        """Get the bounding rectangle of all strands."""
        if not self.strands:
            return QRectF()

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for strand in self.strands:
            rect = strand.get_path().boundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())

        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

    def zoom_to_fit(self):
        """Zoom and center the view to fit all strands."""
        rect = self.get_bounding_rect()
        if not rect.isNull():
            self.fitInView(rect, Qt.KeepAspectRatio)
            self.update()

    def export_to_image(self, file_path):
        """Export the current canvas to an image file."""
        image = QImage(self.size(), QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QPainter(image)
        self.render(painter)
        painter.end()

        image.save(file_path)

    def import_from_data(self, data):
        """Import strands from serialized data."""
        self.clear_strands()
        for strand_data in data:
            strand = Strand.from_dict(strand_data)
            self.add_strand(strand)
        self.update()

    def export_to_data(self):
        """Export strands to serializable data."""
        return [strand.to_dict() for strand in self.strands]

    def undo_last_action(self):
        """Undo the last action performed on the canvas."""
        # This method would require implementing an action history system
        pass

    def redo_last_action(self):
        """Redo the last undone action on the canvas."""
        # This method would require implementing an action history system
        pass

    def set_strand_width(self, width):
        """Set the width for new strands."""
        self.strand_width = width

    def set_default_strand_color(self, color):
        """Set the default color for new strands."""
        self.strand_color = color

    def set_highlight_color(self, color):
        """Set the highlight color for selected strands."""
        self.highlight_color = color
        self.update()

    def toggle_snap_to_grid(self):
        """Toggle snap-to-grid functionality."""
        self.snap_to_grid_enabled = not self.snap_to_grid_enabled

    def get_strand_count(self):
        """Get the total number of strands on the canvas."""
        return len(self.strands)

    def get_selected_strand(self):
        """Get the currently selected strand."""
        return self.selected_strand

    def clear_selection(self):
        """Clear the current strand selection."""
        self.selected_strand = None
        self.selected_strand_index = None
        self.update()

    def refresh_canvas(self):
        """Refresh the entire canvas, updating all strands."""
        for strand in self.strands:
            strand.update_shape()
        self.update()

    def remove_strand(self, strand):
        logging.info(f"Starting remove_strand for: {strand.layer_name}")

        if strand not in self.strands:
            logging.warning(f"Strand {strand.layer_name} not found in self.strands")
            return False

        set_number = strand.set_number
        is_main_strand = strand.layer_name.split('_')[1] == '1'
        is_attached_strand = isinstance(strand, AttachedStrand)

        if self.newest_strand == strand:
            self.newest_strand = None

        # Collect strands to remove
        strands_to_remove = [strand]
        if is_main_strand:
            strands_to_remove.extend(self.get_all_attached_strands(strand))

        # Collect masks to remove
        masks_to_remove = []
        for s in self.strands:
            if isinstance(s, MaskedStrand):
                if is_attached_strand:
                    # For attached strands, remove masks that involve this strand at either start or end
                    mask_parts = s.layer_name.split('_')
                    if len(mask_parts) == 4 and (strand.layer_name == mask_parts[0] + '_' + mask_parts[1] or 
                                                strand.layer_name == mask_parts[2] + '_' + mask_parts[3]):
                        masks_to_remove.append(s)
                else:
                    # For main strands, remove masks related to this strand and its attachments
                    if any(self.is_strand_involved_in_mask(s, remove_strand) for remove_strand in strands_to_remove):
                        masks_to_remove.append(s)

        # Log strands and masks to be removed
        logging.info(f"Strands to be removed: {[s.layer_name for s in strands_to_remove]}")
        logging.info(f"Masks to be removed: {[m.layer_name for m in masks_to_remove]}")

        # Collect indices before removing strands
        indices_to_remove = []
        for s in strands_to_remove + masks_to_remove:
            if s in self.strands:
                indices_to_remove.append(self.strands.index(s))

        # Remove collected strands and masks
        for s in strands_to_remove + masks_to_remove:
            if s in self.strands:
                self.strands.remove(s)
                logging.info(f"Removed strand/mask: {s.layer_name}")
                if not isinstance(s, MaskedStrand):
                    self.remove_strand_circles(s)

        # Update selection if the removed strand was selected
        if self.selected_strand in strands_to_remove + masks_to_remove:
            self.selected_strand = None
            self.selected_strand_index = None
            logging.info("Cleared selected strand")

        # Clear mask mode selection if active
        if self.current_mode == self.mask_mode:
            self.mask_mode.clear_selection()
        # Update parent strand's attached_strands list and remove circle if it's an attached strand
        if is_attached_strand:
            parent_strand = self.find_parent_strand(strand)
            if parent_strand:
                parent_strand.attached_strands = [s for s in parent_strand.attached_strands if s != strand]
                logging.info(f"Updated parent strand {parent_strand.layer_name} attached_strands list")
                self.remove_parent_circle(parent_strand, strand)

        # Update layer names and set numbers
        if is_main_strand:
            self.update_layer_names_for_set(set_number)
            self.update_set_numbers_after_main_strand_deletion(set_number)
        elif is_attached_strand:
            self.update_layer_names_for_attached_strand_deletion(set_number)

        # Force a complete redraw of the canvas
        self.update()
        QTimer.singleShot(0, self.update)

        # Update the layer panel
        if self.layer_panel:
            self.layer_panel.update_after_deletion(set_number, indices_to_remove, is_main_strand)
            self.update_layer_panel_colors()  # Add this line

        logging.info("Finished remove_strand")
        return True
    def update_layer_panel_colors(self):
        if self.layer_panel:
            for strand in self.strands:
                if isinstance(strand, MaskedStrand):
                    self.layer_panel.update_masked_strand_color(strand.layer_name, strand.color)
    def remove_parent_circle(self, parent_strand, attached_strand):
        """
        Remove the circle associated with the attached strand from the parent strand.
        """
        if parent_strand.end == attached_strand.start:
            # Check if there are other strands attached to the end
            other_attachments = [s for s in parent_strand.attached_strands if s != attached_strand and s.start == parent_strand.end]
            if not other_attachments:
                parent_strand.has_circles[1] = False
                logging.info(f"Removed circle from the end of parent strand: {parent_strand.layer_name}")
        elif parent_strand.start == attached_strand.start:
            # Check if there are other strands attached to the start
            other_attachments = [s for s in parent_strand.attached_strands if s != attached_strand and s.start == parent_strand.start]
            if not other_attachments:
                parent_strand.has_circles[0] = False
                logging.info(f"Removed circle from the start of parent strand: {parent_strand.layer_name}")



    def remove_main_strand(self, strand, set_number):
        logging.info(f"Removing main strand and related strands for set {set_number}")
        
        # Get all directly attached strands
        attached_strands = self.get_all_attached_strands(strand)
        
        # Collect all strands to remove (main strand + attached strands)
        strands_to_remove = [strand] + attached_strands
        
        # Collect all masks related to the main strand and its attachments
        masks_to_remove = []
        for s in self.strands:
            if isinstance(s, MaskedStrand):
                if any(self.is_strand_involved_in_mask(s, remove_strand) for remove_strand in strands_to_remove):
                    masks_to_remove.append(s)
        
        # Add masks to the list of strands to remove
        strands_to_remove.extend(masks_to_remove)
        
        logging.info(f"Strands to remove: {[s.layer_name for s in strands_to_remove]}")

        # Remove all collected strands
        for s in strands_to_remove:
            if s in self.strands:
                self.strands.remove(s)
                logging.info(f"Removed strand: {s.layer_name}")
                if not isinstance(s, MaskedStrand):
                    self.remove_strand_circles(s)

        self.update_layer_names_for_set(set_number)
        self.update_set_numbers_after_main_strand_deletion(set_number)

    def update_layer_names_for_set(self, set_number):
        logging.info(f"Updating layer names for set {set_number}")
        # Do nothing here, as we want to keep original names
        if self.layer_panel:
            self.layer_panel.update_layer_names(set_number)
            
    def is_strand_involved_in_mask(self, masked_strand, strand):
        if isinstance(masked_strand, MaskedStrand):
            mask_parts = masked_strand.layer_name.split('_')
            strand_name = strand.layer_name
            return (masked_strand.first_selected_strand == strand or
                    masked_strand.second_selected_strand == strand or
                    strand_name == mask_parts[0] + '_' + mask_parts[1] or
                    strand_name == mask_parts[2] + '_' + mask_parts[3])
        return False

    def get_all_attached_strands(self, strand):
        attached = []
        for attached_strand in strand.attached_strands:
            attached.append(attached_strand)
            attached.extend(self.get_all_attached_strands(attached_strand))
        return attached

    def update_set_numbers_after_main_strand_deletion(self, deleted_set_number):
        logging.info(f"Updating set numbers after deleting main strand of set {deleted_set_number}")
        
        # Remove the deleted set from strand_colors
        if deleted_set_number in self.strand_colors:
            del self.strand_colors[deleted_set_number]
        
        logging.info(f"Updated strand_colors: {self.strand_colors}")
        
        # Update layer names for all strands
        self.update_layer_names()

        # Reset the current set to the highest remaining set number
        if self.strand_colors:
            self.current_set = max(self.strand_colors.keys())
        else:
            self.current_set = 0
        logging.info(f"Reset current_set to {self.current_set}")

    def update_layer_names(self):
        logging.info("Starting update_layer_names")
        set_counts = {}
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                # Skip renaming masked strands
                continue
            set_number = strand.set_number
            if set_number not in set_counts:
                set_counts[set_number] = 0
            set_counts[set_number] += 1
            new_name = f"{set_number}_{set_counts[set_number]}"
            if new_name != strand.layer_name:
                logging.info(f"Updated layer name from {strand.layer_name} to {new_name}")
                strand.layer_name = new_name
        
        # Update the layer panel for all sets
        if self.layer_panel:
            logging.info("Updating LayerPanel for all sets")
            self.layer_panel.refresh()
        logging.info("Finished update_layer_names")
    def toggle_angle_adjust_mode(self, strand):
        if not hasattr(self, 'angle_adjust_mode'):
            self.angle_adjust_mode = AngleAdjustMode(self)
        
        self.is_angle_adjusting = not self.is_angle_adjusting
        if self.is_angle_adjusting:
            self.angle_adjust_mode.activate(strand)
        else:
            self.angle_adjust_mode.confirm_adjustment()
            self.angle_adjust_completed.emit()  # Add this line
        self.update()


    def handle_strand_selection(self, pos):
        strands_at_point = self.find_strands_at_point(pos)
        
        if strands_at_point:
            selected_strand = strands_at_point[-1]  # Select the topmost strand
            index = self.strands.index(selected_strand)
            
            if self.current_mode == self.mask_mode:
                self.mask_mode.handle_strand_selection(selected_strand)
            else:
                self.select_strand(index)
                self.strand_selected.emit(index)
        else:
            # Deselect if clicking on an empty area
            if self.current_mode == self.mask_mode:
                self.mask_mode.clear_selection()
            else:
                self.select_strand(None)
                self.strand_selected.emit(-1)  # Emit -1 to indicate deselection


    def find_strands_at_point(self, pos):
        return [strand for strand in self.strands if strand.get_path().contains(pos)]
    
    def exit_select_mode(self):
        if self.current_mode == "select" or self.current_mode == self.mask_mode:
            self.current_mode = self.attach_mode
            self.setCursor(Qt.ArrowCursor)
        self.update()
    def highlight_selected_strand(self, index):
        """Highlight the selected strand."""
        if index is not None and 0 <= index < len(self.strands):
            self.selected_strand = self.strands[index]
            self.selected_strand_index = index
        else:
            self.selected_strand = None
            self.selected_strand_index = None
        self.update()  # Trigger a repaint to show the highlight


    def force_redraw(self):
        """Force a complete redraw of the canvas."""
        logging.info("Forcing redraw of the canvas")
        self.update()
        QTimer.singleShot(0, self.update)  # Schedule another update on the next event loop

    def set_group_layer_manager(self, group_layer_manager):
        self.group_layer_manager = group_layer_manager
        logging.info(f"GroupLayerManager set on StrandDrawingCanvas: {self.group_layer_manager}")

    def move_group(self, group_name, total_dx, total_dy):
        logging.info(f"Moving group '{group_name}' by total_dx={total_dx}, total_dy={total_dy}")

        # Initialize original positions if not already initialized
        if not hasattr(self, 'original_positions_initialized') or not self.original_positions_initialized:
            self.initialize_original_positions(group_name)
            self.original_positions_initialized = True

        if self.group_layer_manager is None:
            logging.error("group_layer_manager not set in StrandDrawingCanvas")
            return

        group_data = self.group_layer_manager.group_panel.groups.get(group_name)

        if group_data:
            updated_strands = set()
            group_layers = group_data['layers']

            for layer_name in group_layers:
                strand = self.find_strand_by_name(layer_name)
                if strand:
                    # First, update attached strands before moving the group strand
                    self.update_non_group_attached_strands(strand, total_dx, total_dy, updated_strands, group_layers)

            # Now, move the group strands
            for layer_name in group_layers:
                strand = self.find_strand_by_name(layer_name)
                if strand:
                    self.move_entire_strand(strand, total_dx, total_dy)
                    updated_strands.add(strand)
                    logging.info(f"Moved group strand '{strand.layer_name}' to new position: start={strand.start}, end={strand.end}")

            # Force a redraw of the canvas
            self.update()
        else:
            logging.warning(f"No group data found for group '{group_name}'")

    def move_entire_strand(self, strand, dx, dy):
        # Initialize original positions if they are not already initialized
        if not hasattr(strand, 'original_start'):
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)
        
        # Use the original positions
        new_start = QPointF(strand.original_start.x() + dx, strand.original_start.y() + dy)
        new_end = QPointF(strand.original_end.x() + dx, strand.original_end.y() + dy)

        # Update positions
        strand.start = new_start
        strand.end = new_end

        strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()
        logging.info(f"Moved entire strand '{strand.layer_name}' to new position: start={strand.start}, end={strand.end}")

    def move_strand_and_update(self, strand, dx, dy, updated_strands):
        if not hasattr(strand, 'original_start'):
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)

        # Calculate new positions based on original positions
        new_start = QPointF(strand.original_start.x() + dx, strand.original_start.y() + dy)
        new_end = QPointF(strand.original_end.x() + dx, strand.original_end.y() + dy)

        # Update positions
        strand.start = new_start
        strand.end = new_end

        strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()
        updated_strands.add(strand)
        logging.info(f"Moved strand '{strand.layer_name}' to new position: start={strand.start}, end={strand.end}")

    def points_are_close(self, point1, point2):
        tolerance = self.strand_width if hasattr(self, 'strand_width') else 10  # Default to 10 if strand_width is not defined
        return (abs(point1.x() - point2.x()) < tolerance and
                abs(point1.y() - point2.y()) < tolerance)












    def update_non_group_attached_strands(self, strand, dx, dy, updated_strands, group_layers):
        attached_strands = self.find_attached_strands(strand)
        for attached_strand in attached_strands:
            if attached_strand not in updated_strands and attached_strand.layer_name not in group_layers:
                # **Move the entire attached strand**
                self.move_strand_and_update(attached_strand, dx, dy, updated_strands)
                updated_strands.add(attached_strand)
                logging.info(f"Moved entire attached strand '{attached_strand.layer_name}'")
                # Recursively update strands attached to this attached strand
                self.update_non_group_attached_strands(attached_strand, dx, dy, updated_strands, group_layers)

    def move_strand_and_update(self, strand, dx, dy, updated_strands):
        print(f"Moving strand {strand.layer_name} by dx={dx}, dy={dy}")

        if not hasattr(strand, 'original_start'):
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)

        # Calculate new positions based on original positions
        new_start = QPointF(strand.original_start.x() + dx, strand.original_start.y() + dy)
        new_end = QPointF(strand.original_end.x() + dx, strand.original_end.y() + dy)

        # Only update if the position has actually changed
        if strand.start != new_start or strand.end != new_end:
            strand.start = new_start
            strand.end = new_end

            strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()
            updated_strands.add(strand)
            logging.info(f"Moved strand '{strand.layer_name}' to new position: start={strand.start}, end={strand.end}")
        else:
            logging.info(f"Strand '{strand.layer_name}' position unchanged")

    def update_attached_point(self, attached_strand, moved_strand, dx, dy):
        if not hasattr(attached_strand, 'original_start'):
            attached_strand.original_start = QPointF(attached_strand.start)
            attached_strand.original_end = QPointF(attached_strand.end)

        if attached_strand.start == moved_strand.start or attached_strand.start == moved_strand.end:
            attached_strand.start = QPointF(attached_strand.original_start.x() + dx, attached_strand.original_start.y() + dy)
        if attached_strand.end == moved_strand.start or attached_strand.end == moved_strand.end:
            attached_strand.end = QPointF(attached_strand.original_end.x() + dx, attached_strand.original_end.y() + dy)
        
        attached_strand.update_shape()
        if hasattr(attached_strand, 'update_side_line'):
            attached_strand.update_side_line()
        logging.info(f"Updated attached strand '{attached_strand.layer_name}' to match moved strand '{moved_strand.layer_name}'")




    def set_grid_size(self, grid_size):
        """Set the grid size and refresh the canvas."""
        self.grid_size = grid_size
        self.update()  # Refresh the canvas to reflect the new grid size

    def find_strand_by_name(self, layer_name):
        for strand in self.strands:
            if strand.layer_name == layer_name:
                return strand
        return None


    def apply_group_rotation(self, group_name):
        if group_name in self.groups:
            group_data = self.groups[group_name]
            for strand in group_data['strands']:
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
            self.update()


    def update_language_code(self, language_code):
        self.language_code = language_code
        if self.angle_adjust_mode:
            self.angle_adjust_mode.language_code = language_code

    def update_strand_angle(self, strand_name, new_angle):
        strand = self.find_strand_by_name(strand_name)
        if strand:
            old_angle = self.calculate_angle(strand)
            angle_diff = radians(new_angle - old_angle)
            
            dx = strand.end.x() - strand.start.x()
            dy = strand.end.y() - strand.start.y()
            length = (dx**2 + dy**2)**0.5
            
            new_dx = length * cos(radians(new_angle))
            new_dy = length * sin(radians(new_angle))
            
            strand.end.setX(strand.start.x() + new_dx)
            strand.end.setY(strand.start.y() + new_dy)
            
            strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()
            
            self.update()  # Trigger a repaint of the canvas

    def calculate_angle(self, strand):
        dx = strand.end.x() - strand.start.x()
        dy = strand.end.y() - strand.start.y()
        return degrees(atan2(dy, dx))

    def delete_masked_layer(self, masked_strand):
        if isinstance(masked_strand, MaskedStrand) and masked_strand in self.strands:
            logging.info(f"Deleting masked layer: {masked_strand.layer_name}")
            
            # Remove the masked strand from the strands list
            self.strands.remove(masked_strand)
            
            # Get the index of the masked strand in the layer panel
            index = next((i for i, button in enumerate(self.layer_panel.layer_buttons) 
                        if button.text() == masked_strand.layer_name), None)
            
            # Update the layer panel
            if index is not None and self.layer_panel:
                self.layer_panel.remove_layer_button(index)
            
            # Clear selection if the deleted masked strand was selected
            if self.selected_strand == masked_strand:
                self.clear_selection()
            
            # Force a redraw of the canvas
            self.update()
            
            logging.info(f"Masked layer {masked_strand.layer_name} deleted successfully")
            return True
        else:
            logging.warning(f"Attempted to delete non-existent or non-masked layer")
            return False

# End of StrandDrawingCanvas class