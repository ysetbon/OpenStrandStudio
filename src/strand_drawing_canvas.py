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
import traceback 
from math import radians, cos, sin, atan2, degrees
from rotate_mode import RotateMode
from PyQt5.QtWidgets import QCheckBox, QLineEdit, QPushButton
import logging
import traceback

from translations import translations
# Add this import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main_window import MainWindow  # This prevents circular imports

from save_load_manager import save_strands

class StrandDrawingCanvas(QWidget):
    # Define signals
    strand_created = pyqtSignal(object)   # Emitting the strand object
    strand_deleted = pyqtSignal(int)      # Emitting the index of deleted strand
    masked_layer_created = pyqtSignal(object)  # Emitting the masked strand object

    strand_selected = pyqtSignal(int)
    mask_created = pyqtSignal(int, int)
    angle_adjust_completed = pyqtSignal()  # Add this line
    language_changed = pyqtSignal()  # Signal to emit when language changes
    masked_layer_created = pyqtSignal(object)
    mask_edit_requested = pyqtSignal(int)  # Signal when mask editing is requested
    mask_edit_exited = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the StrandDrawingCanvas."""
        super().__init__(parent)
        self.setMinimumSize(700, 700)  # Set minimum size for the canvas
        self.initialize_properties()
        self.setup_modes()
        self.highlight_color = QColor(255, 0, 0, 255)  # Semi-transparent red
        # Add the signal if not already present
        self.setFocusPolicy(Qt.StrongFocus)  # Add this to enable key events
        angle_adjust_completed = pyqtSignal()
        self.control_points_visible = False  # Initialize control points visibility
        self.pre_rotation_state = {}     
        # Add these new attributes
        self.is_drawing_new_strand = False
        self.new_strand_set_number = None
        self.new_strand_start_point = None
        self.new_strand_end_point = None
        self.stroke_color = Qt.black
        self.strand_width = 46  # Width of strands
        self.stroke_width = 4  # Width of the black outline
        self.group_layer_manager = None
        # In strand_drawing_canvas.py
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

        self.selected_attached_strand = None
        
        self._selected_strand = None

        self.show_control_points = True  # Initialize control points visibility
        self.current_strand = None
        self.mask_edit_mode = False
        self.editing_masked_strand = None
        self.mask_edit_path = None
        self.eraser_size = 20  # Size of the eraser tool

        # Add these new attributes for mask editing
        self.mask_edit_mode = False
        self.editing_masked_strand = None
        self.mask_edit_path = None
        self.erase_start_pos = None
        self.current_erase_rect = None



    def add_strand(self, strand):
        """Add a strand to the canvas and set its canvas reference."""
        strand.canvas = self
        self.strands.append(strand)
        logging.info(f"Added strand to canvas. Show control points: {self.show_control_points}")
        self.update()

    @property
    def selected_strand(self):
        return self._selected_strand

    @selected_strand.setter
    def selected_strand(self, strand):
        if strand is None:
            logging.info(f"Selected strand set to None. Caller: {self.get_caller()}")
        else:
            logging.info(f"Selected strand set to {strand.layer_name}. Caller: {self.get_caller()}")
        self._selected_strand = strand

    def get_caller(self):
        import traceback
        stack = traceback.extract_stack()
        filename, lineno, function_name, text = stack[-3]
        return f"{filename}:{lineno} in {function_name}"


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
        """
        Called when we first begin rotating a group. 
        Preserves group data and sets rotating_group_name to group_name.
        Applicable whether the group is masked or unmasked.
        """
        if group_name not in self.groups:
            logging.warning(f"Group '{group_name}' was not found in self.groups.")
            return

        # Preserve the group data so we can restore geometry after rotation
        self.group_layer_manager.preserve_group_data(group_name)

        # Set the group as "active" so rotate_group(...) and finish_group_rotation(...) will work
        self.rotating_group_name = group_name

        # Calculate rotation center or do any other initial setup
        # e.g., self.calculate_group_center(self.groups[group_name]['strands'])
        self.rotation_center = self.calculate_group_center(self.groups[group_name]['strands'])

        logging.info(f"Start rotating group '{group_name}'. rotating_group_name set to: {self.rotating_group_name}")

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
            group_data = self.groups[group_name]
            # Store the original main strands before rotation
            self.pre_rotation_main_strands = list(group_data.get('main_strands', []))
            logging.info(f"Stored pre-rotation main strands for group {group_name}: {self.pre_rotation_main_strands}")
            
            self.rotating_group_name = group_name
            self.original_strand_positions = {}
            for strand in group_data['strands']:
                # Store all current positions
                state = {
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end)
                }
                if not isinstance(strand, MaskedStrand):
                    # For non-masked strands, also store control points if they exist
                    if hasattr(strand, 'control_point1'):
                        state['control_point1'] = QPointF(strand.control_point1)
                    if hasattr(strand, 'control_point2'):
                        state['control_point2'] = QPointF(strand.control_point2)
                else:
                    # Always store an empty list under "deletion_rectangles", so the rotation code can handle MaskedStrands consistently
                    state['deletion_rectangles'] = []
                    # If any deletion_rectangles do exist, store them now.
                    if hasattr(strand, 'deletion_rectangles') and strand.deletion_rectangles:
                        for rect in strand.deletion_rectangles:
                            rect_corners = {
                                'top_left': QPointF(*rect['top_left']),
                                'top_right': QPointF(*rect['top_right']),
                                'bottom_left': QPointF(*rect['bottom_left']),
                                'bottom_right': QPointF(*rect['bottom_right'])
                            }
                            state['deletion_rectangles'].append(rect_corners)

                self.pre_rotation_state[strand.layer_name] = state
                self.original_strand_positions[strand] = state
            # Calculate center
            self.calculate_group_center(group_data['strands'])
            logging.info(f"Started rotation for group '{group_name}'")
            self.update()
        else:
            logging.warning(f"Attempted to start rotation for non-existent group: {group_name}")

    def rotate_group(self, group_name, angle):
        """
        Rotates the entire group by 'angle' degrees around self.rotation_center.
        Also rotates MaskedStrand rectangle corners to match the rotation.
        """
        if group_name in self.groups and self.rotating_group_name == group_name:
            group_data = self.groups[group_name]
            center = self.rotation_center  # Calculated in start_group_rotation
            self.current_rotation_angle = angle

            for strand in group_data['strands']:
                original_pos = self.original_strand_positions.get(strand)
                if not original_pos:
                    continue

                # Rotate main geometry (start, end, control points)
                strand.start = self.rotate_point(original_pos['start'], center, angle)
                strand.end = self.rotate_point(original_pos['end'], center, angle)
                if hasattr(strand, "control_point1") and strand.control_point1 is not None:
                    strand.control_point1 = self.rotate_point(original_pos['control_point1'], center, angle)
                if hasattr(strand, "control_point2") and strand.control_point2 is not None:
                    strand.control_point2 = self.rotate_point(original_pos['control_point2'], center, angle)

                # Remove the MaskedStrand check so both masked and unmasked strands go through the same logic
                if 'deletion_rectangles' in original_pos:
                    for rect_idx, rect_corners in enumerate(original_pos['deletion_rectangles']):
                        tl = self.rotate_point(rect_corners['top_left'], center, angle)
                        tr = self.rotate_point(rect_corners['top_right'], center, angle)
                        bl = self.rotate_point(rect_corners['bottom_left'], center, angle)
                        br = self.rotate_point(rect_corners['bottom_right'], center, angle)

                        strand.deletion_rectangles[rect_idx]['top_left']     = (tl.x(), tl.y())
                        strand.deletion_rectangles[rect_idx]['top_right']    = (tr.x(), tr.y())
                        strand.deletion_rectangles[rect_idx]['bottom_left']  = (bl.x(), bl.y())
                        strand.deletion_rectangles[rect_idx]['bottom_right'] = (br.x(), br.y())

                # Update each strand's shape
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
        """Rotate the strand around 'center' by 'angle' degrees, including control points."""

        strand.start = self.rotate_point(strand.start, center, angle)
        strand.end   = self.rotate_point(strand.end, center, angle)



        # Rotate control points if present

        if hasattr(strand, "control_point1") and strand.control_point1 is not None:

            strand.control_point1 = self.rotate_point(strand.control_point1, center, angle)

        if hasattr(strand, "control_point2") and strand.control_point2 is not None:

            strand.control_point2 = self.rotate_point(strand.control_point2, center, angle)



        # If it's a MaskedStrand, also rotate the deletion rectangle corners

        if hasattr(strand, "deletion_rectangles"):

            for rect in strand.deletion_rectangles:

                tl = self.rotate_point(QPointF(*rect["top_left"]), center, angle)

                tr = self.rotate_point(QPointF(*rect["top_right"]), center, angle)

                bl = self.rotate_point(QPointF(*rect["bottom_left"]), center, angle)

                br = self.rotate_point(QPointF(*rect["bottom_right"]), center, angle)

                rect["top_left"]     = (tl.x(), tl.y())

                rect["top_right"]    = (tr.x(), tr.y())

                rect["bottom_left"]  = (bl.x(), bl.y())

                rect["bottom_right"] = (br.x(), br.y())



        strand.update_shape()

        if hasattr(strand, "update_side_line"):

            strand.update_side_line()




    def calculate_group_center(self, strands):
        all_points = []
        for strand in strands:
            all_points.extend([strand.start, strand.end])
            # Include strand's control points if present
            if hasattr(strand, 'control_point1') and strand.control_point1 is not None:
                all_points.append(strand.control_point1)
            if hasattr(strand, 'control_point2') and strand.control_point2 is not None:
                all_points.append(strand.control_point2)
            if hasattr(strand, 'deletion_rectangles'):
                for rect in strand.deletion_rectangles:
                    # Unpack the tuples into x,y coordinates
                    all_points.append(QPointF(*rect['top_left']))
                    all_points.append(QPointF(*rect['top_right'])) 
                    all_points.append(QPointF(*rect['bottom_left']))
                    all_points.append(QPointF(*rect['bottom_right']))
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
        """Finish rotating a group of strands."""
        logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Starting for group '{group_name}'")

        # Log initial state
        logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Current rotating_group_name: {getattr(self, 'rotating_group_name', None)}")
        logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Group exists in self.groups: {group_name in self.groups}")
        
        if hasattr(self, 'pre_rotation_main_strands'):
            logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Found pre_rotation_main_strands: {[s.layer_name if hasattr(s, 'layer_name') else 'Unknown' for s in self.pre_rotation_main_strands]}")
        else:
            logging.info("[StrandDrawingCanvas.finish_group_rotation] No pre_rotation_main_strands found")

        if hasattr(self, 'rotating_group_name') and self.rotating_group_name == group_name:
            if group_name in self.groups:
                # Log group data before restoration
                current_main_strands = self.groups[group_name].get('main_strands', [])
                logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Current main strands before restoration: {[s.layer_name if hasattr(s, 'layer_name') else 'Unknown' for s in current_main_strands]}")
                
                # Restore the original main strands
                if hasattr(self, 'pre_rotation_main_strands'):
                    self.groups[group_name]['main_strands'] = self.pre_rotation_main_strands
                    logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Restored main strands for group {group_name}: {[s.layer_name if hasattr(s, 'layer_name') else 'Unknown' for s in self.pre_rotation_main_strands]}")
                else:
                    logging.warning(f"[StrandDrawingCanvas.finish_group_rotation] No pre_rotation_main_strands to restore for group {group_name}")
                
                # Log final group data
                final_main_strands = self.groups[group_name].get('main_strands', [])
                logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Final main strands after restoration: {[s.layer_name if hasattr(s, 'layer_name') else 'Unknown' for s in final_main_strands]}")
            else:
                logging.error(f"[StrandDrawingCanvas.finish_group_rotation] Group {group_name} not found in self.groups")
                
            # Cleanup
            self.is_rotating = False
            self.rotating_group_name = None
            self.rotation_center = None
            if hasattr(self, 'pre_rotation_main_strands'):
                delattr(self, 'pre_rotation_main_strands')
                logging.info("[StrandDrawingCanvas.finish_group_rotation] Cleaned up pre_rotation_main_strands")
                
            logging.info(f"[StrandDrawingCanvas.finish_group_rotation] Finished rotation cleanup for group '{group_name}'")
            self.update()
        else:
            logging.warning(f"[StrandDrawingCanvas.finish_group_rotation] Attempted to finish rotation for inactive group: {group_name}. Current rotating group: {getattr(self, 'rotating_group_name', None)}")


    def update_original_positions_recursively(self, strand):
        strand.original_start = QPointF(strand.start)
        strand.original_end = QPointF(strand.end)
        for attached_strand in strand.attached_strands:
            self.update_original_positions_recursively(attached_strand)

             
    def create_strand(self, start, end, set_number):
        new_strand = Strand(start, end, self.strand_width, self.strand_color, self.stroke_color, self.stroke_width)
        new_strand.set_number = set_number
        new_strand.layer_name = f"{set_number}_{len([s for s in self.strands if s.set_number == set_number]) + 1}"
        self.strands.append(new_strand)
        logging.info(f"Created new strand: {new_strand.layer_name}")
        self.strand_created.emit(new_strand)
        return new_strand
    def initialize_original_positions(self, group_name):
        """
        Initialize original positions for group strands and their attached strands.
        """
        if not self.group_layer_manager:
            logging.error("GroupLayerManager not connected.")
            return
        
        group_data = self.group_layer_manager.group_panel.groups.get(group_name)
        if group_data:
            strands = group_data['strands']
            for strand in strands:
                self.initialize_strand_original_positions_recursively(strand)
        else:
            logging.warning(f"Group '{group_name}' not found in group panel")


    def initialize_strand_original_positions_recursively(self, strand):
        """
        Recursively initialize original positions for a strand and its attached strands.
        """
        if not hasattr(strand, 'original_start'):
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)
        for attached_strand in strand.attached_strands:
            if isinstance(attached_strand, MaskedStrand):
                continue
            self.initialize_strand_original_positions_recursively(attached_strand)
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

    def validate_group_data(self, group_name):
        """Validate and repair group data if necessary."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            
            # Ensure all required keys exist
            required_keys = ['layers', 'strands', 'control_points', 'main_strands']
            for key in required_keys:
                if key not in group_data:
                    group_data[key] = [] if key != 'control_points' else {}
                    
            # Validate strands exist in canvas
            group_data['strands'] = [strand for strand in group_data['strands'] 
                                if strand in self.strands]
            
            # Update layers based on valid strands
            group_data['layers'] = [strand.layer_name for strand in group_data['strands']]
            
            logging.info(f"Validated group data for {group_name}")
            return True
        return False
    def snap_group_to_grid(self, group_name):
        """
        Snaps all points of strands and attached strands (excluding masked strands)
        in the specified group to the closest points on the grid, and updates their
        original positions accordingly.
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
            snapped_start = self.snap_point_to_grid(strand.start, grid_size)
            snapped_end = self.snap_point_to_grid(strand.end, grid_size)

            strand.start = snapped_start
            strand.end = snapped_end

            # Update original positions
            strand.original_start = QPointF(snapped_start)
            strand.original_end = QPointF(snapped_end)

            strand.update_shape()

            # Update any side lines if applicable
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()

            # Snap attached strands
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    if isinstance(attached_strand, MaskedStrand):
                        continue

                    snapped_start = self.snap_point_to_grid(attached_strand.start, grid_size)
                    snapped_end = self.snap_point_to_grid(attached_strand.end, grid_size)

                    attached_strand.start = snapped_start
                    attached_strand.end = snapped_end

                    # Update original positions
                    attached_strand.original_start = QPointF(snapped_start)
                    attached_strand.original_end = QPointF(snapped_end)

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
        # Refresh group data to include any new strands
        self.refresh_group_data(group_name)
        
        # Initialize original positions for all strands in the group
        self.initialize_original_positions(group_name)
        
        # Proceed with setting up moving group
        self.moving_group = True
        self.move_group_name = group_name
        self.move_group_layers = layers
        self.move_start_pos = None
        self.setCursor(Qt.OpenHandCursor)
        logging.info(f"Started moving group '{group_name}'")

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
        self.grid_size = 28  # Size of grid cells
        self.show_grid = True  # Flag to show/hide grid
        self.should_draw_names = False  # Flag to show/hide strand names
        self.newest_strand = None  # Track the most recently created strand
        self.is_angle_adjusting = False  # Add this line
        self.mask_mode_active = False
        self.mask_selected_strands = []
        self.selected_attached_strand = None  # Add this line for selected attached strand

    def start_new_strand_mode(self, set_number):
        self.new_strand_set_number = set_number
        self.new_strand_start_point = None
        self.new_strand_end_point = None
        self.is_drawing_new_strand = True
        self.setCursor(Qt.CrossCursor)
        
        # **Add this line to ensure the color is set**
        if set_number not in self.strand_colors:
            self.strand_colors[set_number] = QColor('purple')  # Or get the color from LayerPanel
        
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

    def show_control_points(self, visible):
        """Show or hide control points on the canvas."""
        self.control_points_visible = visible
        self.update()  # Redraw the canvas to reflect changes
    def paintEvent(self, event):
        """
        Handles the painting of the canvas.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the grid, if applicable
        if self.show_grid:
            self.draw_grid(painter)

        logging.info(f"Painting {len(self.strands)} strands")

        # Draw existing strands
        for strand in self.strands:
            logging.info(f"Drawing strand '{strand.layer_name}'")
            if not hasattr(strand, 'canvas'):
                strand.canvas = self  # Ensure all strands have canvas reference
            # Only highlight selected strand if we're not in mask mode
            if strand == self.selected_strand and not isinstance(self.current_mode, MaskMode):
                logging.info(f"Drawing highlighted selected strand: {strand.layer_name}")
                self.draw_highlighted_strand(painter, strand)
            else:
                strand.draw(painter)

        # Draw the current strand being created (either first strand or attached)
        if self.current_strand:
            if not hasattr(self.current_strand, 'canvas'):
                self.current_strand.canvas = self  # Ensure current strand has canvas reference
            # For the first strand, draw with a special highlight
            if self.is_first_strand:
                painter.save()
                # Draw a preview shadow
                shadow_pen = QPen(QColor(255, 255, 0, 100), self.strand_width + 4)  # Semi-transparent yellow
                painter.setPen(shadow_pen)
                self.current_strand.draw(painter)
                
                # Draw the actual strand
                painter.setPen(QPen(self.strand_color, self.strand_width))
                self.current_strand.draw(painter)
                painter.restore()
            else:
                self.current_strand.draw(painter)

        # Draw the new strand being created
        if self.is_drawing_new_strand and self.new_strand_start_point and self.new_strand_end_point:
            # Determine the color for the new strand
            if self.new_strand_set_number in self.strand_colors:
                strand_color = self.strand_colors[self.new_strand_set_number]
            else:
                # If it's the first strand (no existing colors), use the default color
                strand_color = QColor('purple')

            # Create a temporary Strand object for drawing
            temp_strand = Strand(
                self.new_strand_start_point,
                self.new_strand_end_point,
                self.strand_width,
                color=strand_color,
                stroke_color=self.stroke_color,
                stroke_width=self.stroke_width
            )
            temp_strand.canvas = self  # Set canvas reference for the temporary strand
            temp_strand.draw(painter)

        # Only draw control points if they're enabled
        if self.show_control_points:  # Simplified check
            self.draw_control_points(painter)

        # Draw strand labels if enabled
        if self.should_draw_names:
            for strand in self.strands:
                self.draw_strand_label(painter, strand)

        # Draw selection area if in MoveMode
        if isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
            painter.save()
            painter.setBrush(QBrush(Qt.transparent))
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))

            if isinstance(self.current_mode.selected_rectangle, QPainterPath):
                painter.drawPath(self.current_mode.selected_rectangle)
            elif isinstance(self.current_mode.selected_rectangle, QRectF):
                painter.drawRect(self.current_mode.selected_rectangle)

            painter.restore()

        # Draw the angle adjustment visualization if in angle adjust mode
        if self.is_angle_adjusting and self.angle_adjust_mode and self.angle_adjust_mode.active_strand:
            self.angle_adjust_mode.draw(painter)

        # Highlight the strand being created in attach mode
        if isinstance(self.current_mode, AttachMode) and self.current_mode.affected_strand:
            affected_strand = self.current_mode.affected_strand
            painter.save()
            highlight_pen = QPen(Qt.yellow, self.strand_width + 4)  # Wider width and different color
            painter.setPen(highlight_pen)
            affected_strand.draw(painter)
            painter.restore()

        # Draw mask mode selections (this is the single implementation we want to keep)
        if isinstance(self.current_mode, MaskMode):
            self.current_mode.draw(painter)

        # Draw mask editing interface
        if self.mask_edit_mode and self.editing_masked_strand:
            # Draw the current mask path with semi-transparency
            painter.setBrush(QColor(255, 0, 0, 100))  # Semi-transparent red
            painter.setPen(Qt.NoPen)
            painter.drawPath(self.mask_edit_path)
            
            # Draw the current erase rectangle if it exists
            if self.current_erase_rect:
                painter.setBrush(QColor(255, 255, 255, 128))  # Semi-transparent white
                painter.setPen(QPen(Qt.white, 1, Qt.DashLine))
                painter.drawRect(self.current_erase_rect)
            
            # Draw the eraser cursor
            if hasattr(self, 'last_pos'):
                painter.setPen(QPen(Qt.white, 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(
                    self.last_pos.x() - self.eraser_size/2,
                    self.last_pos.y() - self.eraser_size/2,
                    self.eraser_size,
                    self.eraser_size
                )

        logging.info(
            f"Paint event completed. Selected strand: "
            f"{self.selected_strand.layer_name if self.selected_strand else 'None'}"
        )

        painter.end()

    def toggle_control_points(self):
        """Toggle the visibility of control points."""
        self.show_control_points = not self.show_control_points
        logging.info(f"Control points visibility toggled: {self.show_control_points}")
        
        # Make sure both implementations respect the toggle state
        for strand in self.strands:
            if hasattr(strand, 'show_control_points'):
                strand.show_control_points = self.show_control_points
                
        self.update()  # Force a redraw of the canvas





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
        masked_strand.set_color(strand1.color)
        
        # Update the masked strand's layer name
        masked_strand.layer_name = f"{strand1.layer_name}_{strand2.layer_name}"
        
        # Log the creation of the masked layer
        logging.info(f"Created masked layer: {masked_strand.layer_name}")
        
        # Clear any existing selection
        self.clear_selection()
        
        # Move the new masked strand to the top of the drawing order
        self.move_strand_to_top(masked_strand)
        
        # Emit the masked_layer_created signal
        self.update()
        self.masked_layer_created.emit(masked_strand)

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
        painter.save()
        highlight_pen = QPen(QColor('transparent'), strand.stroke_width + 2)
        highlight_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(highlight_pen)
        painter.setBrush(Qt.NoBrush)
        strand.draw_path(painter)  # Use the new draw_path method
        painter.restore()

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
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw the masked strand normally (filling it in, etc.)
            masked_strand.draw(painter)

            # Now call the new "masked_strand.draw_highlight" method
            masked_strand.draw_highlight(painter)

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
        """
        Update the color for strands in a set.
        Only recolors strands that start with the same set number (e.g., '1_' for set_number=1)
        """
        logging.info(f"Updating color for set {set_number} to {color.name()}")
        self.strand_colors[set_number] = color
        
        # Convert set_number to string for comparison
        set_prefix = f"{set_number}_"
        
        for strand in self.strands:
            if not hasattr(strand, 'layer_name') or not strand.layer_name:
                logging.info(f"Skipping strand without layer_name")
                continue
                
            logging.info(f"Checking strand: {strand.layer_name}")
            
            # Check if the strand's layer_name starts with our set_prefix
            if strand.layer_name.startswith(set_prefix):
                strand.set_color(color)
                logging.info(f"Updated color for strand: {strand.layer_name}")
                
            # For masked strands, only update if the first part matches our set_number
            elif isinstance(strand, MaskedStrand):
                first_part = strand.layer_name.split('_')[0]  # Get the first number only
                if first_part == str(set_number):
                    strand.set_color(color)
                    logging.info(f"Updated color for masked strand: {strand.layer_name}")
        
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

        # Set the canvas reference
        strand.canvas = self

        if hasattr(strand, 'is_being_deleted') and strand.is_being_deleted:
            logging.info("Strand is being deleted, skipping creation process")
            return

        # Determine the set number for the new strand
        if isinstance(strand, AttachedStrand):
            set_number = strand.parent.set_number
        elif self.selected_strand and not isinstance(self.selected_strand, MaskedStrand):
            set_number = self.selected_strand.set_number
        else:
            # Use the current_set from LayerPanel
            if self.layer_panel:
                set_number = self.layer_panel.current_set
            else:
                # Fallback logic if layer_panel is not available
                set_number = self.get_next_available_set_number()

        # Ensure set_number is an integer
        if not isinstance(set_number, int):
            try:
                set_number = int(set_number)
            except ValueError:
                logging.warning(f"Invalid set_number '{set_number}' encountered. Using next available integer.")
                set_number = self.get_next_available_set_number()

        strand.set_number = set_number

        # Assign color to the new strand
        if set_number not in self.strand_colors:
            if self.layer_panel and set_number in self.layer_panel.set_colors:
                self.strand_colors[set_number] = self.layer_panel.set_colors[set_number]
            else:
                self.strand_colors[set_number] = QColor('purple')
        strand.set_color(self.strand_colors[set_number])

        # Add the new strand to the strands list
        self.strands.append(strand)

        # Set this as the newest strand to ensure it's drawn on top
        self.newest_strand = strand

        # Update layer panel
        if self.layer_panel:
            # Count the number of strands in this set (excluding MaskedStrands)
            count = len([
                s for s in self.strands
                if s.set_number == set_number and not isinstance(s, MaskedStrand)
            ])
            strand.layer_name = f"{set_number}_{count}"

            if not hasattr(strand, 'is_being_deleted'):
                logging.info(f"Adding new layer button for set {set_number}, count {count}")
                self.layer_panel.add_layer_button(set_number, count)
            else:
                logging.info(f"Updating layer names for set {set_number}")
                self.layer_panel.update_layer_names(set_number)

            # Update the color in the layer panel
            self.layer_panel.on_color_changed(set_number, self.strand_colors[set_number])

        # Select the new strand if it's not an attached strand
        if not isinstance(strand, AttachedStrand):
            self.select_strand(len(self.strands) - 1)

        # Update the canvas
        self.update()

        # Notify LayerPanel that a new strand was added
        if self.layer_panel:
            self.layer_panel.update_attachable_states()

        # Inform the GroupLayerManager about the new strand
        if hasattr(self, 'group_layer_manager') and self.group_layer_manager:
            self.group_layer_manager.update_groups_with_new_strand(strand)

        logging.info("Finished on_strand_created")

        # Add this line to emit the signal
        self.strand_created.emit(strand)
    def get_next_available_set_number(self):
        existing_set_numbers = set(
            strand.set_number
            for strand in self.strands
            if hasattr(strand, 'set_number') and not isinstance(strand, MaskedStrand)
        )
        return max(existing_set_numbers, default=0) + 1
    def get_next_strand_number(self, set_number):
        """Get the next available strand number for a set."""
        # Get all existing numbers for this set
        existing_numbers = []
        for strand in self.strands:
            if strand.set_number == set_number:
                try:
                    # Extract the number after the underscore (e.g., '1_3' -> 3)
                    number = int(strand.layer_name.split('_')[1])
                    existing_numbers.append(number)
                except (IndexError, ValueError):
                    continue
        
        # If no existing numbers, start with 1
        if not existing_numbers:
            return 1
            
        # Get the next sequential number
        return max(existing_numbers) + 1

    def attach_strand(self, parent_strand, new_strand):
        """Handle group cleanup when a new strand is attached."""
        try:
            logging.info(f"\n=== ATTACH_STRAND PROCESSING ===")
            
            if not hasattr(self, 'group_layer_manager') or not self.group_layer_manager:
                return True
                
            group_panel = self.group_layer_manager.group_panel
            
            # Store affected groups and their main strands before deletion
            affected_groups = {}
            for group_name, group_data in list(self.groups.items()):  # Use self.groups instead of group_panel.groups
                if any(strand.layer_name == parent_strand.layer_name for strand in group_data['strands']):
                    logging.info(f"Found group '{group_name}' containing parent strand")
                    # Store the original main strands from the canvas groups
                    affected_groups[group_name] = list(group_data.get('main_strands', []))
                    logging.info(f"Stored original main strands for {group_name}: {affected_groups[group_name]}")
                    
                    # Delete the group
                    if group_name in self.groups:
                        del self.groups[group_name]
                    group_panel.delete_group(group_name)
            
            # Connect to the strand_created signal to recreate groups after new strand is initialized
            def recreate_groups(new_strand):
                for group_name, original_main_strands in affected_groups.items():
                    logging.info(f"Recreating group '{group_name}' with original main strands: {original_main_strands}")
                    # Pass the original main strands to recreate_group
                    self.group_layer_manager.recreate_group(group_name, new_strand, original_main_strands)
                
                # Disconnect after handling
                self.strand_created.disconnect(recreate_groups)
            
            # Connect the handler
            self.strand_created.connect(recreate_groups)
            
            return True

        except Exception as e:
            logging.error(f"Error in attach_strand: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False

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



    def select_strand(self, index, update_layer_panel=True):
        """Select a strand by index."""
        logging.info(f"Entering select_strand. Index: {index}")
        # Deselect all strands first
        for strand in self.strands:
            strand.is_selected = False
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    attached_strand.is_selected = False

        if index is not None and 0 <= index < len(self.strands):
            print(f"selected_strand = {self.strands[index]}")
            self.selected_strand = self.strands[index]
            self.selected_strand.is_selected = True
            self.selected_strand_index = index
            self.last_selected_strand_index = index
            self.is_first_strand = False

            if isinstance(self.selected_strand, AttachedStrand):
                self.selected_attached_strand = self.selected_strand
                self.selected_attached_strand.is_selected = True
            else:
                self.selected_attached_strand = None

            if update_layer_panel and self.layer_panel and self.layer_panel.get_selected_layer() != index:
                self.layer_panel.select_layer(index, emit_signal=False)

            self.current_mode = self.attach_mode
            self.current_mode.is_attaching = False
            self.current_strand = None

            # Enable delete button for masked layers
            if isinstance(self.selected_strand, MaskedStrand) and self.layer_panel:
                self.layer_panel.delete_strand_button.setEnabled(True)
            else:
                if self.layer_panel:
                    self.layer_panel.delete_strand_button.setEnabled(False)

            self.strand_selected.emit(index)
        else:
            # If no valid index is provided, ensure the strand is deselected
            logging.info(f"Deselecting all strands in select_strand")
            self.selected_strand = None
            if update_layer_panel and self.layer_panel:
                self.layer_panel.deselect_all()
                self.layer_panel.delete_strand_button.setEnabled(False)
            self.strand_selected.emit(-1)  # Emit -1 for deselection

        self.update()  # Force a redraw
        logging.info(f"Selected strand index: {index}")
        logging.info(f"Exiting select_strand. Selected strand: {self.selected_strand}")
    def delete_strand(self, index):
        if 0 <= index < len(self.strands):
            # Add this line to capture the deleted strand's layer name (optional)
            deleted_strand = self.strands.pop(index)
            
            del self.strands[index]
            self.strand_deleted.emit(index)  # Emit the signal when a strand is deleted
            self.update()
            self.strand_deleted.emit(index)

            # Optionally log the deletion
            logging.info(f"Deleted strand: {deleted_strand.layer_name}")
    def deselect_all_strands(self):
        """Deselect all strands and update the canvas."""
        def deselect_strand_recursively(strand):
            strand.is_selected = False
            strand.start_selected = False
            strand.end_selected = False
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    deselect_strand_recursively(attached_strand)

        for strand in self.strands:
            deselect_strand_recursively(strand)

        self.update()  # Redraw the canvas to reflect changes

    def mousePressEvent(self, event):
        if self.mask_edit_mode and event.button() == Qt.LeftButton:
            self.erase_start_pos = event.pos()
            logging.info(f"Started mask deletion at position: ({self.erase_start_pos.x()}, {self.erase_start_pos.y()})")
            self.current_erase_rect = None
            self.update()
            event.accept()
            return
        elif self.current_mode == "rotate":
            self.rotate_mode.mousePressEvent(event)
        elif self.moving_group:
            self.move_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif self.is_drawing_new_strand:
            self.new_strand_start_point = event.pos()

        if self.current_mode == "select":
            # Get the position from the event
            pos = event.pos()
            self.handle_strand_selection(pos)
            
        elif self.current_mode == self.mask_mode:
            self.mask_mode.handle_mouse_press(event)
        elif self.current_mode:
            self.current_mode.mousePressEvent(event)
        elif self.current_mode == self.attach_mode:
            # Create new strand
            if event.button() == Qt.LeftButton:
                pos = event.pos()
                self.current_strand = Strand(pos, pos, self.strand_width)
                self.current_strand.canvas = self  # Set canvas reference immediately
                self.is_drawing_new_strand = True
                logging.info(f"Created new strand with canvas reference. Show control points: {self.show_control_points}")
                self.update()
        else:
            super().mousePressEvent(event)

        if self.moving_group:
            self.move_group_name = self.get_group_name_at_position(event.pos())
            self.group_move_start_pos = event.pos()
            self.original_positions_initialized = False  # Will trigger re-initialization

        self.update()


    def mouseMoveEvent(self, event):
        if self.mask_edit_mode and event.buttons() & Qt.LeftButton and self.erase_start_pos:
            # Update the current erase rectangle
            self.current_erase_rect = QRectF(
                min(self.erase_start_pos.x(), event.pos().x()),
                min(self.erase_start_pos.y(), event.pos().y()),
                abs(event.pos().x() - self.erase_start_pos.x()),
                abs(event.pos().y() - self.erase_start_pos.y())
            )
            logging.info(f"Updated deletion rectangle: x={self.current_erase_rect.x():.2f}, "
                        f"y={self.current_erase_rect.y():.2f}, "
                        f"width={self.current_erase_rect.width():.2f}, "
                        f"height={self.current_erase_rect.height():.2f}")
            self.update()  # Force a redraw to show the rectangle
            event.accept()
            return
        elif self.moving_group and self.group_move_start_pos:
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
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mask_edit_mode and event.button() == Qt.LeftButton and self.current_erase_rect:
            # Save the deletion rectangle information
            if not hasattr(self.editing_masked_strand, 'deletion_rectangles'):
                self.editing_masked_strand.deletion_rectangles = []
                
            # Store the rectangle coordinates by corners instead of x/y/width/height
            rect_data = {
                'top_left': (
                    self.current_erase_rect.topLeft().x(),
                    self.current_erase_rect.topLeft().y()
                ),
                'top_right': (
                    self.current_erase_rect.topRight().x(),
                    self.current_erase_rect.topRight().y()
                ),
                'bottom_left': (
                    self.current_erase_rect.bottomLeft().x(),
                    self.current_erase_rect.bottomLeft().y()
                ),
                'bottom_right': (
                    self.current_erase_rect.bottomRight().x(),
                    self.current_erase_rect.bottomRight().y()
                )
            }
            self.editing_masked_strand.deletion_rectangles.append(rect_data)
            logging.info(f"Saved deletion rectangle by corners: {rect_data}")
            
            # Create and apply the erase path
            erase_path = QPainterPath()
            erase_path.addRect(self.current_erase_rect)
            
            if self.mask_edit_path and self.editing_masked_strand:
                self.mask_edit_path = self.mask_edit_path.subtracted(erase_path)
                self.editing_masked_strand.set_custom_mask(self.mask_edit_path)
                logging.info("Updated mask path after deletion")
            
            # Clear the current rectangle
            self.current_erase_rect = None
            self.erase_start_pos = None
            self.update()
            event.accept()
            return
        elif self.current_mode == "rotate":
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
            
            # Ensure the new strand is selected and highlighted
            new_strand.is_selected = True
            self.selected_strand = new_strand
            self.newest_strand = new_strand
            self.selected_strand_index = new_strand_index
            self.last_selected_strand_index = new_strand_index
            
            self.is_drawing_new_strand = False
            self.new_strand_start_point = None
            self.new_strand_end_point = None
            self.setCursor(Qt.ArrowCursor)
            
            # Emit signals and update UI
            self.strand_selected.emit(new_strand_index)
            if hasattr(self, 'layer_panel'):
                self.layer_panel.on_strand_created(new_strand)
                # Ensure the layer panel selection is updated
                self.layer_panel.select_layer(new_strand_index, emit_signal=False)
            
            # Force a canvas update to show the selection
            self.update()
            
            logging.info(f"Created and selected new main strand: {new_strand.layer_name}, index: {new_strand_index}")
        else:
            logging.warning("Attempted to finalize new strand without valid start and end points")
    def set_mode(self, mode):
        """
        Set the current mode of the canvas.
        
        Args:
            mode (str): The mode to set. Can be "attach", "move", "select", "mask", "angle_adjust", "new_strand", "rotate", or "new_strand".
        """
        logging.info(f"Setting mode to {mode}. Current selected strand: {self.selected_strand}")
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
            

        # Update the canvas
        self.update()

        # Log the mode change
        logging.info(f"Canvas mode changed to: {mode}")
        logging.info(f"Mode set to {mode}. Selected strand after mode change: {self.selected_strand}")



    def is_strand_involved_in_mask(self, masked_strand, strand):
        if isinstance(masked_strand, MaskedStrand):
            return (masked_strand.first_selected_strand == strand or
                    masked_strand.second_selected_strand == strand or
                    strand.layer_name in masked_strand.layer_name)
        return False

    def create_masked_strand(self, first_strand, second_strand):
        """
        Create a masked strand from two selected strands.

        Args:
            first_strand (Strand): The first selected strand.
            second_strand (Strand): The second selected strand.
        """
        logging.info(f"Attempting to create masked strand for {first_strand.layer_name} and {second_strand.layer_name}")

        # Check if a masked strand already exists for these strands
        if self.mask_exists(first_strand, second_strand):
            logging.info(f"Masked strand for {first_strand.layer_name} and {second_strand.layer_name} already exists.")
            return

        # Create the new masked strand
        masked_strand = MaskedStrand(first_strand, second_strand)

        # Add the new masked strand to the canvas
        self.add_strand(masked_strand)

        # Update the layer panel if it exists
        if self.layer_panel:
            button = self.layer_panel.add_masked_layer_button(
                self.strands.index(first_strand),
                self.strands.index(second_strand)
            )
            button.color_changed.connect(self.handle_color_change)

        # Set the color of the masked strand
        masked_strand.set_color(first_strand.color)

        # Update the masked strand's layer name
        masked_strand.layer_name = f"{first_strand.layer_name}_{second_strand.layer_name}"

        # --- Begin new code to check group consistency ---
        # Inform the GroupLayerManager about the new masked strand
        if hasattr(self, 'group_layer_manager') and self.group_layer_manager:
            self.group_layer_manager.update_groups_with_new_strand(masked_strand)
        # --- End new code ---

        # Log the creation of the masked strand
        logging.info(f"Created masked strand: {masked_strand.layer_name}")

        # Clear any existing selection
        self.clear_selection()

        # Move the new masked strand to the top of the drawing order
        self.move_strand_to_top(masked_strand)

        # Force a redraw of the canvas
        self.update()

        # Return the new masked strand in case it's needed
        return masked_strand
    def check_and_delete_group_for_new_strand(self, related_strand, new_strand):
        """Helper method to check group consistency when a new strand is added."""
        if not hasattr(self, 'group_layer_manager') or not self.group_layer_manager:
            return
        group_panel = self.group_layer_manager.group_panel
        if not group_panel:
            return
        main_set_number = str(related_strand.set_number)
        for group_name, group_data in group_panel.groups.items():
            if 'main_strands' in group_data and main_set_number in group_data['main_strands']:
                # If the new strand is not in the group, delete the group
                if new_strand.layer_name not in group_data['layers']:
                    logging.info(f"Deleting group '{group_name}' because new strand '{new_strand.layer_name}' connected to its main strand is not in the group.")
                    group_panel.delete_group(group_name)
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
        logging.info(f"Clearing selection. Current selected strand: {self.selected_strand}")
        self.selected_strand = None
        self.selected_strand_index = None
        self.selected_attached_strand = None
        self.update()
        logging.info("Selection cleared")

    def refresh_canvas(self):
        """Refresh the entire canvas, updating all strands."""
        for strand in self.strands:
            strand.update_shape()
        self.update()

    def remove_strand(self, strand):
        logging.info(f"Starting remove_strand for: {strand.layer_name}")
        logging.info(f"Removing strand {strand.layer_name}. Current selected strand: {self.selected_strand}")

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

        # Delete groups containing the strands to be removed
        self.delete_groups_containing_strands(strands_to_remove)

        # Remove collected strands and masks
        for s in strands_to_remove + masks_to_remove:
            if s in self.strands:
                self.strands.remove(s)
                logging.info(f"Removed strand/mask: {s.layer_name}")
                if not isinstance(s, MaskedStrand):
                    self.remove_strand_circles(s)

        # Update selection if the removed strand was selected
        if self.selected_strand in strands_to_remove + masks_to_remove:
            logging.info("Clearing selected strand as it's being removed")
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
            self.update_layer_panel_colors()

        logging.info(f"Strand removed. Current selected strand: {self.selected_strand}")
        logging.info("Finished remove_strand")
        return True

    def delete_groups_containing_strands(self, strands):
        """
        Deletes groups that contain any of the given strands.
        """
        if not hasattr(self, 'group_layer_manager') or not self.group_layer_manager:
            return

        group_panel = self.group_layer_manager.group_panel
        if not group_panel:
            return

        strands_layer_names = [strand.layer_name for strand in strands]

        groups_to_delete = []
        for group_name, group_data in group_panel.groups.items():
            if any(layer_name in group_data['layers'] for layer_name in strands_layer_names):
                groups_to_delete.append(group_name)

        for group_name in groups_to_delete:
            logging.info(f"Deleting group '{group_name}' because it contains a deleted strand.")
            group_panel.delete_group(group_name)
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
        
        # Add this line to update attachment states after deletion
        self.update_attachment_statuses()  # This will update has_circles for remaining strands

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

    def draw_control_points(self, painter):
        """
        Draw control points for all non-masked strands.

        Args:
            painter (QPainter): The painter used for drawing.
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        control_point_radius = 4  # Adjust as needed

        for strand in self.strands:
            # Skip masked strands and strands without control points
            if isinstance(strand, MaskedStrand) or not hasattr(strand, 'control_point1') or not hasattr(strand, 'control_point2'):
                continue
                
            if strand.control_point1 is None or strand.control_point2 is None:
                continue

            # Draw lines connecting control points
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(strand.start, strand.control_point1)
            painter.drawLine(strand.end, strand.control_point2)

            # Draw control points
            control_point_pen = QPen(QColor('green'), 2)
            painter.setPen(control_point_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(strand.control_point1, control_point_radius, control_point_radius)
            painter.drawEllipse(strand.control_point2, control_point_radius, control_point_radius)

        painter.restore()
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
        results = []
        for strand in self.strands:
            contains_start = strand.get_start_selection_path().contains(pos)
            contains_end = strand.get_end_selection_path().contains(pos)
            if contains_start or contains_end:
                results.append(strand)
        return results
        
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
        logging.info("Group layer manager set for canvas")

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
                    # Update attached strands before moving the group strand
                    self.update_attached_strands_recursively(strand, total_dx, total_dy, updated_strands, group_layers)

            # Move all group strands
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

    def update_attached_strands_recursively(self, strand, dx, dy, updated_strands, group_layers):
        """
        Recursively update all attached strands that need to be included in the movement.
        """
        for attached_strand in strand.attached_strands:
            if attached_strand not in updated_strands:
                # Check if the attached strand should be included in the group movement
                if attached_strand.layer_name not in group_layers:
                    # Include the attached strand in the group movement
                    self.move_entire_strand(attached_strand, dx, dy)
                    updated_strands.add(attached_strand)
                    logging.info(f"Moved attached strand '{attached_strand.layer_name}'")
                # Recursively update attached strands of the attached strand
                self.update_attached_strands_recursively(attached_strand, dx, dy, updated_strands, group_layers)

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

    def points_are_close(self, point1, point2, tolerance=5.0):
        """Check if two points are within a certain tolerance."""
        return (abs(point1.x() - point2.x()) <= tolerance and
                abs(point1.y() - point2.y()) <= tolerance)

    def update(self):
        self.update_attachment_statuses()
        super().update()

    def update_attachment_statuses(self):
        """Update attachment statuses and has_circles states of all strands."""
        if not hasattr(self, 'layer_state_manager') or not self.layer_state_manager:
            return

        connections = self.layer_state_manager.getConnections()
        strand_dict = {strand.layer_name: strand for strand in self.strands if not isinstance(strand, MaskedStrand)}

        # First pass: Reset all attachment states
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                continue
            strand.start_attached = False
            strand.end_attached = False
            strand.has_circles = [False, False]  # Reset circles
            logging.info(f"Reset state for {strand.layer_name}: has_circles={strand.has_circles}")

        # Second pass: Update based on actual connections
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                continue

            # Get all strands this strand is connected to
            for other_strand in self.strands:
                if isinstance(other_strand, MaskedStrand) or other_strand == strand:
                    continue

                # Check start point connections
                if self.points_are_close(strand.start, other_strand.start) or \
                   self.points_are_close(strand.start, other_strand.end):
                    strand.start_attached = True
                    strand.has_circles[0] = True
                    logging.info(f"Found start connection for {strand.layer_name} with {other_strand.layer_name}")

                # Check end point connections
                if self.points_are_close(strand.end, other_strand.start) or \
                   self.points_are_close(strand.end, other_strand.end):
                    strand.end_attached = True
                    strand.has_circles[1] = True
                    logging.info(f"Found end connection for {strand.layer_name} with {other_strand.layer_name}")

            logging.info(f"Final state for {strand.layer_name}: has_circles={strand.has_circles}")

    def set_layer_state_manager(self, layer_state_manager):
        self.layer_state_manager = layer_state_manager
        # Connect any necessary signals here












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
            strand.original_control_point1 = QPointF(strand.control_point1)
            strand.original_control_point2 = QPointF(strand.control_point2)

        # Calculate new positions based on original positions
        new_start = QPointF(strand.original_start.x() + dx, strand.original_start.y() + dy)
        new_end = QPointF(strand.original_end.x() + dx, strand.original_end.y() + dy)
        new_control_point1 = QPointF(strand.original_control_point1.x() + dx, strand.original_control_point1.y() + dy)
        new_control_point2 = QPointF(strand.original_control_point2.x() + dx, strand.original_control_point2.y() + dy)

        # Only update if the position has actually changed
        if (strand.start != new_start or strand.end != new_end or 
            strand.control_point1 != new_control_point1 or strand.control_point2 != new_control_point2):
            
            strand.start = new_start
            strand.end = new_end
            strand.control_point1 = new_control_point1
            strand.control_point2 = new_control_point2

            strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()
            updated_strands.add(strand)
            logging.info(f"Moved strand '{strand.layer_name}' to new position: start={strand.start}, end={strand.end}, "
                        f"cp1={strand.control_point1}, cp2={strand.control_point2}")
        else:
            logging.info(f"Strand '{strand.layer_name}' position unchanged")

    def update_attached_point(self, attached_strand, moved_strand, dx, dy):
        if not hasattr(attached_strand, 'original_start'):
            attached_strand.original_start = QPointF(attached_strand.start)
            attached_strand.original_end = QPointF(attached_strand.end)
            attached_strand.original_control_point1 = QPointF(attached_strand.control_point1)
            attached_strand.original_control_point2 = QPointF(attached_strand.control_point2)

        if attached_strand.start == moved_strand.start or attached_strand.start == moved_strand.end:
            attached_strand.start = QPointF(attached_strand.original_start.x() + dx, attached_strand.original_start.y() + dy)
            attached_strand.control_point1 = QPointF(attached_strand.original_control_point1.x() + dx, 
                                            attached_strand.original_control_point1.y() + dy)
        if attached_strand.end == moved_strand.start or attached_strand.end == moved_strand.end:
            attached_strand.end = QPointF(attached_strand.original_end.x() + dx, attached_strand.original_end.y() + dy)
            attached_strand.control_point2 = QPointF(attached_strand.original_control_point2.x() + dx, 
                                            attached_strand.original_control_point2.y() + dy)
        
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
        """
        Update the angle of a strand to a new specified angle.

        Args:
            strand_name (str): The name of the strand to update.
            new_angle (float): The new angle in degrees.
        """
        strand = self.find_strand_by_name(strand_name)
        if strand:
            # Calculate the current angle
            old_angle = self.calculate_angle(strand)
            angle_diff = radians(new_angle - old_angle)
            
            dx = strand.end.x() - strand.start.x()
            dy = strand.end.y() - strand.start.y()
            length = (dx**2 + dy**2)**0.5
            
            # Calculate new end point based on new angle
            new_dx = length * cos(radians(new_angle))
            new_dy = length * sin(radians(new_angle))
            
            # Update the end point
            strand.end.setX(strand.start.x() + new_dx)
            strand.end.setY(strand.start.y() + new_dy)
            
            # Update the strand's shape
            strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()
            
            # **Add these lines to update original positions**
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)
            if hasattr(strand, 'control_point1'):
                strand.original_control_point1 = QPointF(strand.control_point1)
            if hasattr(strand, 'control_point2'):
                strand.original_control_point2 = QPointF(strand.control_point2)
            
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
    def find_control_point_at_position(self, pos):
        """
        Find the strand whose control point is at the given position.

        Args:
            pos (QPointF): The position to check.

        Returns:
            Strand or None: The strand whose control point is at the position, or None if not found.
        """
        for strand in reversed(self.strands):  # Reverse to check topmost strands first
            if hasattr(strand, 'control_point'):
                control_point_rect = self.get_control_point_rectangle(strand)
                if control_point_rect.contains(pos):
                    return strand
        return None

    def get_control_point_rectangle(self, strand):
        """
        Get the rectangle around the control point for hit detection.

        Args:
            strand (Strand): The strand whose control point to get.

        Returns:
            QRectF: The rectangle around the control point.
        """
        size = 10  # Adjust as needed
        center = strand.control_point
        return QRectF(center.x() - size / 2, center.y() - size / 2, size, size)

    def handle_control_point_selection(self, pos):
        """
        Handle selection of a control point at the given position.

        Args:
            pos (QPointF): The position where the user clicked.

        Returns:
            bool: True if a control point was selected, False otherwise.
        """
        strand = self.find_control_point_at_position(pos)
        if strand:
            # Perform any selection logic here
            self.selected_strand = strand
            self.selected_point = 'control_point'
            self.update()
            return True
        return False
    
        # Add these new methods
    def enter_mask_edit_mode(self, strand_index):
        """Enter mask editing mode for the specified masked strand."""
        if 0 <= strand_index < len(self.strands):
            strand = self.strands[strand_index]
            if isinstance(strand, MaskedStrand):
                self.mask_edit_mode = True
                self.editing_masked_strand = strand
                self.mask_edit_path = strand.get_mask_path()
                self.setCursor(Qt.CrossCursor)
                self.erase_start_pos = None
                self.current_erase_rect = None
                self.setFocus()  # Explicitly set focus when entering mask edit mode
                logging.info(f"Entered mask edit mode for strand {strand_index}")
                self.update()
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape and self.mask_edit_mode:
            logging.info("ESC key pressed, exiting mask edit mode")
            self.exit_mask_edit_mode()
            event.accept()  # Accept the event to prevent it from propagating
        else:
            super().keyPressEvent(event)
    def exit_mask_edit_mode(self):
        """Exit mask editing mode."""
        if self.mask_edit_mode:
            self.mask_edit_mode = False
            self.editing_masked_strand = None
            self.mask_edit_path = None
            self.erase_start_pos = None
            self.current_erase_rect = None
            self.setCursor(Qt.ArrowCursor)
            logging.info("Exited mask edit mode")
            
            # Get the parent window directly through the stored reference
            if hasattr(self, 'parent_window'):
                self.parent_window.exit_mask_edit_mode()
            
            # Emit signal to notify layer panel
            self.mask_edit_exited.emit()
            
            self.update()



    def reset_mask(self, strand_index):
        """Reset the mask to its original intersection."""
        if 0 <= strand_index < len(self.strands):
            strand = self.strands[strand_index]
            if isinstance(strand, MaskedStrand):
                strand.reset_mask()
                logging.info(f"Reset mask for strand {strand_index}")
                self.update()

    def save_strands(self, filename):
        save_strands(self.strands, self.groups, filename, self)
# End of StrandDrawingCanvas class