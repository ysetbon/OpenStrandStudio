from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QFont, QFontMetrics, QImage, QPolygonF, QPalette, QPainterPathStroker, QTransform
import logging
from attach_mode import AttachMode
from move_mode import MoveMode
from mask_mode import MaskMode  # Add this import
from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
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
import os
import sys
from PyQt5.QtCore import QStandardPaths

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
    deselect_all_signal = pyqtSignal()  # Signal for deselect all strands

    def __init__(self, parent=None):
        """Initialize the StrandDrawingCanvas."""
        super().__init__(parent)
        self.setMinimumSize(700, 700)  # Set minimum size for the canvas
        
        # Load shadow color from user settings if available
        shadow_color = self.load_shadow_color_from_settings()
        
        # Initialize properties
        self.initialize_properties()
        
        # If we loaded a shadow color from settings, apply it now
        if shadow_color:
            self.default_shadow_color = shadow_color
            logging.info(f"Applied shadow color from settings during canvas initialization: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}")
        
        self.setup_modes()
        self.highlight_color = QColor(255, 0, 0, 0)  # Semi-transparent red
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
        self.stroke_color = QColor(0, 0, 0, 255)
        self.strand_width = 46  # Width of strands
        self.stroke_width = 4  # Width of the black outline
        self.group_layer_manager = None
        # --- Load Shadow Blur Settings --- 
        self.num_steps = 3 # Default
        self.max_blur_radius = 29.99 # Default
        self.load_shadow_blur_settings() # Call helper to load from file
        # --- End Load Shadow Blur Settings ---
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
        
        # Add shadow rendering control
        self.shadow_enabled = True  # Enable shadows by default

        # --- Load Extension Line Settings ---
        self.load_extension_line_settings()
        # --- End Load Extension Line Settings ---

    def load_shadow_color_from_settings(self):
        """Load only the shadow color from the settings file."""
        shadow_color = None
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        logging.info(f"Canvas: Looking for settings file at: {file_path}")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    logging.info("Canvas: Reading settings from user_settings.txt")
                    for line in file:
                        line = line.strip()
                        if line.startswith('ShadowColor:'):
                            rgba_str = line.split(':', 1)[1].strip()
                            try:
                                r, g, b, a = map(int, rgba_str.split(','))
                                shadow_color = QColor(r, g, b, a)
                                logging.info(f"Canvas: Loaded shadow color from settings: {r},{g},{b},{a}")
                                break # Found the color, no need to read further
                            except Exception as e:
                                logging.error(f"Canvas: Error parsing shadow color: {e}")
                                shadow_color = None # Reset on error
                                break
            except Exception as e:
                logging.error(f"Canvas: Error reading settings file: {e}")
        else:
            logging.info("Canvas: Settings file not found. Using default shadow color.")
            
        return shadow_color

    def load_shadow_blur_settings(self):
        """Load shadow blur settings (NumSteps, MaxBlurRadius) from the settings file."""
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line.startswith('NumSteps:'):
                            try:
                                self.num_steps = int(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded NumSteps from settings: {self.num_steps}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing NumSteps value. Using default {self.num_steps}.")
                        elif line.startswith('MaxBlurRadius:'):
                            try:
                                self.max_blur_radius = float(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded MaxBlurRadius from settings: {self.max_blur_radius:.1f}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing MaxBlurRadius value. Using default {self.max_blur_radius}.")
            except Exception as e:
                logging.error(f"Canvas: Error reading settings file for blur settings: {e}")
        else:
            logging.info("Canvas: Settings file not found. Using default shadow blur settings.")

    def load_extension_line_settings(self):
        """Load extension line settings (ExtensionLength, ExtensionDashCount, ExtensionDashWidth) from user_settings.txt if available."""
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        logging.info(f"Canvas: Looking for extension line settings at: {file_path}")

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line.startswith('ExtensionLength:'):
                            try:
                                self.extension_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded ExtensionLength from settings: {self.extension_length}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing ExtensionLength. Using default {self.extension_length}")
                        elif line.startswith('ExtensionDashCount:'):
                            try:
                                self.extension_dash_count = int(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded ExtensionDashCount from settings: {self.extension_dash_count}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing ExtensionDashCount. Using default {self.extension_dash_count}")
                        elif line.startswith('ExtensionDashWidth:'):
                            try:
                                self.extension_dash_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded ExtensionDashWidth from settings: {self.extension_dash_width}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing ExtensionDashWidth. Using default {self.extension_dash_width}")
                        elif line.startswith('ArrowHeadLength:'):
                            try:
                                self.arrow_head_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded ArrowHeadLength from settings: {self.arrow_head_length}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing ArrowHeadLength. Using default {self.arrow_head_length}")
                        elif line.startswith('ArrowHeadWidth:'):
                            try:
                                self.arrow_head_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded ArrowHeadWidth from settings: {self.arrow_head_width}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing ArrowHeadWidth. Using default {self.arrow_head_width}")
                        elif line.startswith('ExtensionLineWidth:'):
                            try:
                                self.extension_dash_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"Canvas: Loaded ExtensionLineWidth (legacy): {self.extension_dash_width}")
                            except ValueError:
                                logging.error(f"Canvas: Error parsing ExtensionLineWidth. Using default {self.extension_dash_width}")
            except Exception as e:
                logging.error(f"Canvas: Error reading settings file for extension settings: {e}")
        else:
            logging.info("Canvas: Settings file not found. Using default extension settings.")

    def setup_modes(self):
        """Initialize the interaction modes."""
        # Attach mode setup
        self.attach_mode = AttachMode(self)
        self.attach_mode.strand_created.connect(self.on_strand_created)

        # Move mode setup
        self.move_mode = MoveMode(self)
        
        # Apply draw_only_affected_strand setting from user settings if available
        try:
            draw_only_setting = self.load_draw_only_affected_strand_setting()
            if draw_only_setting is not None:
                self.move_mode.draw_only_affected_strand = draw_only_setting
                logging.info(f"Applied draw_only_affected_strand setting during initialization: {draw_only_setting}")
        except Exception as e:
            logging.error(f"Error applying draw_only_affected_strand setting: {e}")

        # Mask mode setup
        # Pass the undo_redo_manager instance here
        self.mask_mode = MaskMode(self, self.undo_redo_manager if hasattr(self, 'undo_redo_manager') else None)
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

        self.rotating_group_name = group_name
        group_data = self.groups[group_name]  

        # Compute rotation center (if not already done)
        self.rotation_center = self.calculate_group_center(group_data['strands'])

        # Create or clear pre_rotation_state for fresh usage
        self.pre_rotation_state = {}

        for strand in group_data['strands']:
            # 1) Store the basic geometry
            self.pre_rotation_state[strand.layer_name] = {
                'start': QPointF(strand.start),
                'end':   QPointF(strand.end)
            }
            # Control points if available
            if hasattr(strand, "control_point1") and strand.control_point1 is not None:
                self.pre_rotation_state[strand.layer_name]['control_point1'] = QPointF(strand.control_point1)
            if hasattr(strand, "control_point2") and strand.control_point2 is not None:
                self.pre_rotation_state[strand.layer_name]['control_point2'] = QPointF(strand.control_point2)

            # 2) For MaskedStrand, store deletion_rectangles 
            if isinstance(strand, MaskedStrand) and hasattr(strand, 'deletion_rectangles'):
                self.pre_rotation_state[strand.layer_name]['deletion_rectangles'] = []
                for rect in strand.deletion_rectangles:
                    self.pre_rotation_state[strand.layer_name]['deletion_rectangles'].append({
                        'top_left':     QPointF(*rect['top_left']),
                        'top_right':    QPointF(*rect['top_right']),
                        'bottom_left':  QPointF(*rect['bottom_left']),
                        'bottom_right': QPointF(*rect['bottom_right']),
                    })

        # Done: now we have an unrotated "snapshot"
        logging.info(f"start_group_rotation: stored pre-rotation state for group '{group_name}'")

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
        This method:
          1) Restores each strand & rectangle corner from self.pre_rotation_state
          2) Calls self.rotate_strand(...) exactly once, preventing any 'double rotation'
        """
        if group_name in self.groups and self.rotating_group_name == group_name:
            group_data = self.groups[group_name]
            center = self.rotation_center  # computed in start_group_rotation
            self.current_rotation_angle = angle

            for strand in group_data['strands']:
                original_pos = self.pre_rotation_state.get(strand.layer_name)
                if not original_pos:
                    continue

                # 1) Revert geometry from pre_rotation_state
                strand.start = QPointF(original_pos['start'])
                strand.end   = QPointF(original_pos['end'])
                if 'control_point1' in original_pos:
                    strand.control_point1 = QPointF(original_pos['control_point1'])
                if 'control_point2' in original_pos:
                    strand.control_point2 = QPointF(original_pos['control_point2'])

                # If MaskedStrand, revert each corner
                if isinstance(strand, MaskedStrand) and 'deletion_rectangles' in original_pos:
                    # Ensure the strand has at least that many rectangles
                    while len(strand.deletion_rectangles) < len(original_pos['deletion_rectangles']):
                        strand.deletion_rectangles.append({
                            'top_left': (0,0), 'top_right': (0,0),
                            'bottom_left': (0,0), 'bottom_right': (0,0),
                        })

                    # Copy each corner from original
                    for i, orig_corners in enumerate(original_pos['deletion_rectangles']):
                        strand.deletion_rectangles[i]['top_left']     = (orig_corners['top_left'].x(), orig_corners['top_left'].y())
                        strand.deletion_rectangles[i]['top_right']    = (orig_corners['top_right'].x(), orig_corners['top_right'].y())
                        strand.deletion_rectangles[i]['bottom_left']  = (orig_corners['bottom_left'].x(), orig_corners['bottom_left'].y())
                        strand.deletion_rectangles[i]['bottom_right'] = (orig_corners['bottom_right'].x(), orig_corners['bottom_right'].y())

                # 2) Now perform exactly one rotation step
                #    i.e. rotate from the original baseline to 'angle' degrees
                self.rotate_strand(strand, center, angle)

            self.update()  # Trigger redraw
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
        # Set the shadow color to the default shadow color
        if hasattr(self, 'default_shadow_color') and self.default_shadow_color:
            # Create a fresh QColor instance to avoid reference issues
            new_strand.shadow_color = QColor(
                self.default_shadow_color.red(),
                self.default_shadow_color.green(), 
                self.default_shadow_color.blue(),
                self.default_shadow_color.alpha()
            )
        else:
            # Fall back to default shadow color if not set
            new_strand.shadow_color = QColor(0, 0, 0, 150)
            
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
        self.strand_color = QColor(200, 170, 230, 255)   # Default color for strands
        self.stroke_color = QColor(0, 0, 0, 255)  # Color for strand outlines
        self.stroke_width = 4  # Width of strand outlines
        self.highlight_color = Qt.red  # Color for highlighting selected strands
        self.highlight_width = 20  # Width of highlight
        self.is_first_strand = True  # Flag to indicate if it's the first strand being drawn
        self.selection_color = QColor(255, 0, 0, 255)  # Color for selection rectangle
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
        
        # Always create a fresh QColor instance for the default shadow color
        self.default_shadow_color = QColor(0, 0, 0, 150)  # Default shadow color for new strands (black at 59% opacity)
        logging.info(f"Initialized default shadow color to: {self.default_shadow_color.red()},{self.default_shadow_color.green()},{self.default_shadow_color.blue()},{self.default_shadow_color.alpha()}")
        
        # Initialize the flag for the third control point
        self.enable_third_control_point = False
        # Default extension line settings
        self.extension_length = 100.0
        self.extension_dash_count = 10
        self.extension_dash_width = 2.0
        # Default extension dash gap length (equal to half dash segment length)
        self.extension_dash_gap_length = self.extension_length/(2*self.extension_dash_count) if self.extension_dash_count > 0 else 0.0
        # --- NEW: Arrow head default settings ---
        self.arrow_head_length = 20.0  # Length of arrow head (in pixels)
        self.arrow_head_width = 10.0   # Width of arrow head base (in pixels)
        # --- END NEW ---

    def start_new_strand_mode(self, set_number):
        self.new_strand_set_number = set_number
        self.new_strand_start_point = None
        self.new_strand_end_point = None
        self.is_drawing_new_strand = True
        self.setCursor(Qt.CrossCursor)
        
        # **Add this line to ensure the color is set**
        if set_number not in self.strand_colors:
            self.strand_colors[set_number] = QColor(200, 170, 230, 255)   # Or get the color from LayerPanel
        
        logging.info(f"Entered new strand mode for set: {set_number}")
    def load_draw_only_affected_strand_setting(self):
        """Load draw_only_affected_strand setting from user_settings.txt if available."""
        try:
            import os
            import sys
            from PyQt5.QtCore import QStandardPaths
            
            # Use the appropriate directory for each OS
            app_name = "OpenStrand Studio"
            if sys.platform == 'darwin':  # macOS
                program_data_dir = os.path.expanduser('~/Library/Application Support')
                settings_dir = os.path.join(program_data_dir, app_name)
            else:
                program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
                settings_dir = program_data_dir  # AppDataLocation already includes the app name

            file_path = os.path.join(settings_dir, 'user_settings.txt')
            logging.info(f"StrandDrawingCanvas looking for draw_only_affected_strand setting at: {file_path}")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line.startswith('DrawOnlyAffectedStrand:'):
                            value = line.split(':', 1)[1].strip().lower()
                            draw_only_setting = (value == 'true')
                            logging.info(f"StrandDrawingCanvas found DrawOnlyAffectedStrand in settings: {draw_only_setting}")
                            return draw_only_setting
            else:
                logging.info(f"StrandDrawingCanvas: Settings file not found at {file_path}, will use default draw_only_affected_strand setting")
                
            return None
        except Exception as e:
            logging.error(f"StrandDrawingCanvas error loading draw_only_affected_strand from settings: {e}")
            return None

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

        # The yellow rectangle definition has been moved to the MoveMode section below

        # Draw the grid, if applicable
        if self.show_grid:
            self.draw_grid(painter)

        logging.info(f"Painting {len(self.strands)} strands")

        # Check if we're in move mode and should only draw the affected strand
        draw_all_strands = True
        if isinstance(self.current_mode, MoveMode) and self.current_mode.is_moving and self.current_mode.draw_only_affected_strand:
            draw_all_strands = False
            # In this case, the background will be handled by the cached background
            logging.info("Using optimized drawing mode - only drawing affected strands")

        # Draw ALL existing strands first (background)
        if draw_all_strands:
            for strand in self.strands:
                logging.info(f"Drawing strand '{strand.layer_name}'")
                if not hasattr(strand, 'canvas'):
                    strand.canvas = self  # Ensure all strands have canvas reference
                # --- MODIFIED: Check both selected_strand and selected_attached_strand --- 
                is_selected_for_highlight = (strand == self.selected_strand or strand == self.selected_attached_strand)
                # Only highlight selected strand if we're not in mask mode
                if is_selected_for_highlight and not isinstance(self.current_mode, MaskMode):
                    logging.info(f"Drawing highlighted selected strand: {strand.layer_name}")
                    self.draw_highlighted_strand(painter, strand)
                else:
                    strand.draw(painter)
                    logging.info(f"Drawing strand: {strand.layer_name}")
        else:
            # When optimizing, we only draw the moving strand and connected strands
            # Get the affected strand from MoveMode (the one being moved)
            affected_strand = None
            connected_strands = []
            
            if isinstance(self.current_mode, MoveMode):
                affected_strand = self.current_mode.affected_strand
                
                # If we're moving an attached strand, handle it differently
                if hasattr(self.current_mode, 'temp_selected_strand') and self.current_mode.temp_selected_strand:
                    affected_strand = self.current_mode.temp_selected_strand
                
                # If we're explicitly moving a strand that's not the selected one
                if affected_strand is None and self.current_mode.is_moving:
                    # Try to get the strand from originally_selected_strand
                    affected_strand = self.current_mode.originally_selected_strand
                
                # Final fallback to the selected strand if no other strand is being moved
                if affected_strand is None:
                    # --- MODIFIED: Check both selected_strand and selected_attached_strand for fallback ---
                    affected_strand = self.selected_strand or self.selected_attached_strand
                
                # Get any connected/attached strands that are also being affected
                # Try to get attached strands from the current move operation
                if affected_strand and self.current_mode.moving_side is not None:
                    # Find connected strands at the moving point
                    moving_point = affected_strand.start if self.current_mode.moving_side == 0 else affected_strand.end
                    for strand in self.strands:
                        if strand != affected_strand:
                            # Check if this strand is connected to the affected strand at the moving side
                            if (self.current_mode.moving_side == 0 and 
                                self.current_mode.points_are_close(strand.end, moving_point)) or \
                               (self.current_mode.moving_side == 1 and 
                                self.current_mode.points_are_close(strand.start, moving_point)):
                                connected_strands.append(strand)
            
            # Draw the affected strand if available
            if affected_strand:
                logging.info(f"Drawing affected strand in optimization mode: {affected_strand.layer_name}")
                # --- REVISED: Only draw highlight if NOT currently moving ---
                is_actively_moving = isinstance(self.current_mode, MoveMode) and self.current_mode.is_moving
                is_selected_for_highlight = (affected_strand == self.selected_strand or affected_strand == self.selected_attached_strand)
                
                if is_selected_for_highlight and not isinstance(self.current_mode, MaskMode) and not is_actively_moving:
                    # Draw with highlight ONLY if selected AND move is finished
                    self.draw_highlighted_strand(painter, affected_strand)
                else:
                    # Draw without highlight during active move or if not selected
                    self.draw_moving_strand(painter, affected_strand)
                
                # Draw any connected strands (typically without highlight during move)
                for strand in connected_strands:
                    logging.info(f"Drawing connected strand in optimization mode: {strand.layer_name}")
                    self.draw_moving_strand(painter, strand)

        # Draw the temporary strand (whether it's a new strand or an attached strand)
        if self.current_strand:
            if not hasattr(self.current_strand, 'canvas'):
                self.current_strand.canvas = self
            self.current_strand.draw(painter)
        elif self.is_drawing_new_strand and self.new_strand_start_point and self.new_strand_end_point:
            if self.new_strand_set_number in self.strand_colors:
                strand_color = self.strand_colors[self.new_strand_set_number]
            else:
                strand_color = QColor(200, 170, 230, 255)
            temp_strand = Strand(
                self.new_strand_start_point,
                self.new_strand_end_point,
                self.strand_width,
                color=strand_color,
                stroke_color=self.stroke_color,
                stroke_width=self.stroke_width
            )
            temp_strand.canvas = self
            temp_strand.draw(painter)

        # Draw the connection circle last (always on top)
        if isinstance(self.current_mode, AttachMode) and self.current_mode.affected_strand:
            if self.current_mode.affected_point == 0:
                circle_color = QColor(255, 0, 0, 60)  # Red for start point
            else:
                circle_color = QColor(0, 0, 255, 60)  # Blue for end point
                
            painter.setBrush(QBrush(circle_color))
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
            circle_size = 120
            radius = circle_size / 2
            
            point = (self.current_mode.affected_strand.start if self.current_mode.affected_point == 0 
                    else self.current_mode.affected_strand.end)
            
            circle_rect = QRectF(
                point.x() - radius,
                point.y() - radius,
                circle_size,
                circle_size
            )
            painter.drawEllipse(circle_rect)

        # Only draw control points if they're enabled
        if self.show_control_points:
            self.draw_control_points(painter)

        # Draw strand labels if enabled
        if self.should_draw_names:
            for strand in self.strands:
                self.draw_strand_label(painter, strand)

        # Draw current mode's custom visualizations (including selected attached strand)
        if hasattr(self.current_mode, 'draw'):
            self.current_mode.draw(painter)

        # Draw selection area if in MoveMode - MOVED AFTER current_mode.draw to ensure squares are painted after selected attached strand
        if isinstance(self.current_mode, MoveMode):  # Removed the selected_rectangle check
            painter.save()

            # Get the selected rectangle if it exists
            selected_rect = None
            selected_strand = None
            selected_side = None
            # Store the yellow rectangle for overlap checking
            yellow_rectangle = None
            
            if self.current_mode.selected_rectangle and self.current_mode.affected_strand and self.current_mode.moving_side is not None:
                selected_strand = self.current_mode.affected_strand
                selected_side = self.current_mode.moving_side
                
                # Create the yellow rectangle with the consistent size for overlap checking
                yellow_square_size = 120  # Size for the yellow selection square
                half_yellow_size = yellow_square_size / 2
                square_control_size = 50  # Size for control points
                half_control_size = square_control_size / 2
                
                if selected_side == 0:  # Start point
                    yellow_rectangle = QRectF(
                        selected_strand.start.x() - half_yellow_size,
                        selected_strand.start.y() - half_yellow_size,
                        yellow_square_size,
                        yellow_square_size
                    )
                elif selected_side == 1:  # End point
                    yellow_rectangle = QRectF(
                        selected_strand.end.x() - half_yellow_size,
                        selected_strand.end.y() - half_yellow_size,
                        yellow_square_size,
                        yellow_square_size
                    )
                elif selected_side == 'control_point1' and hasattr(selected_strand, 'control_point1'):
                    # Use control point size for control points
                    yellow_rectangle = QRectF(
                        selected_strand.control_point1.x() - half_control_size,
                        selected_strand.control_point1.y() - half_control_size,
                        square_control_size,
                        square_control_size
                    )
                elif selected_side == 'control_point2' and hasattr(selected_strand, 'control_point2'):
                    # Use control point size for control points
                    yellow_rectangle = QRectF(
                        selected_strand.control_point2.x() - half_control_size,
                        selected_strand.control_point2.y() - half_control_size,
                        square_control_size,
                        square_control_size
                    )
                elif selected_side == 'control_point_center' and hasattr(self, 'enable_third_control_point') and self.enable_third_control_point and hasattr(selected_strand, 'control_point_center'):
                    # Use control point size for control points
                    yellow_rectangle = QRectF(
                        selected_strand.control_point_center.x() - half_control_size,
                        selected_strand.control_point_center.y() - half_control_size, 
                        square_control_size,
                        square_control_size
                    )
                    
            elif isinstance(self.current_mode, MoveMode) and self.current_mode.selected_rectangle:
                # Fall back to using MoveMode's selected rectangle if needed
                yellow_rectangle = self.current_mode.selected_rectangle

            # Track positions where rectangles have been drawn to avoid duplicates
            drawn_rectangle_positions = []

            # Skip drawing all rectangles if in optimized drawing mode
            if isinstance(self.current_mode, MoveMode) and self.current_mode.is_moving and self.current_mode.draw_only_affected_strand:
                # When draw_only_affected_strand is enabled, don't draw any control point rectangles
                pass
            # Draw squares around each strand's start/end
            else:
                for strand in self.strands:
                    if not isinstance(strand, MaskedStrand):
                        if hasattr(strand, 'start') and hasattr(strand, 'end'):
                            # Check if a control point or strand point is being moved
                            is_moving_control_point = isinstance(self.current_mode, MoveMode) and getattr(self.current_mode, 'is_moving_control_point', False)
                            is_moving_strand_point = isinstance(self.current_mode, MoveMode) and getattr(self.current_mode, 'is_moving_strand_point', False)
                            
                            # If a control point or strand point is being moved, only draw for the affected strand
                            if (is_moving_control_point or is_moving_strand_point) and strand != self.current_mode.affected_strand:
                                continue
                                
                            # Increased square size for better visibility
                            square_size = 120
                            half_size = square_size / 2
                            square_control_size = 50
                            half_control_size = square_control_size / 2
                            yellow_square_size = 120  # Size for the yellow selection square
                            half_yellow_size = yellow_square_size / 2
                            
                            # Skip drawing only the exact selected point, not any overlapping rectangles
                            skip_start = (strand == selected_strand and selected_side == 0)
                            skip_end = (strand == selected_strand and selected_side == 1)
                            
                            # Create rectangles for checking overlap
                            start_rect = QRectF(
                                strand.start.x() - half_size,
                                strand.start.y() - half_size,
                                square_size,
                                square_size
                            )
                            
                            end_rect = QRectF(
                                strand.end.x() - half_size,
                                strand.end.y() - half_size,
                                square_size,
                                square_size
                            )
                            
                            # Check if rectangles overlap with yellow rectangle
                            start_overlaps_yellow = yellow_rectangle and self.rectangles_overlap(start_rect, yellow_rectangle)
                            end_overlaps_yellow = yellow_rectangle and self.rectangles_overlap(end_rect, yellow_rectangle)
                            
                            # Check if rectangles already drawn at these positions (to avoid duplicates at connections)
                            start_already_drawn = False
                            end_already_drawn = False
                            
                            for pos in drawn_rectangle_positions:
                                if self.points_are_close(strand.start, pos):
                                    start_already_drawn = True
                                if self.points_are_close(strand.end, pos):
                                    end_already_drawn = True
                            
                            # Draw with red color for non-selected rectangles
                            square_color = QColor(255, 0, 0, 100)  # Red with 50% transparency
                            painter.setBrush(QBrush(square_color))
                            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Solid line for better visibility
                            
                            # Draw square around start point if not selected, not overlapping with yellow, and not already drawn
                            if not skip_start and not start_overlaps_yellow and not start_already_drawn:
                                painter.drawRect(start_rect)
                                drawn_rectangle_positions.append(QPointF(strand.start))

                            # Draw square around end point if not selected, not overlapping with yellow, and not already drawn
                            if not skip_end and not end_overlaps_yellow and not end_already_drawn:
                                painter.drawRect(end_rect)
                                drawn_rectangle_positions.append(QPointF(strand.end))

                            # Draw squares around control points if present (and not MaskedStrand)
                            if not isinstance(strand, MaskedStrand):
                                # Skip drawing only the exact selected control point
                                skip_cp1 = (strand == selected_strand and selected_side == 'control_point1')
                                skip_cp2 = (strand == selected_strand and selected_side == 'control_point2')
                                skip_cp3 = (strand == selected_strand and selected_side == 'control_point_center')
                                # Check if a control point is being moved
                                is_moving_control_point = isinstance(self.current_mode, MoveMode) and getattr(self.current_mode, 'is_moving_control_point', False)
                                
                                # If moving a control point, only draw it for the current strand
                                if is_moving_control_point and strand != self.current_mode.affected_strand:
                                    continue
                                    
                                # Create control point rectangles for overlap checking
                                cp1_rect = None
                                cp2_rect = None
                                
                                if hasattr(strand, 'control_point1') and strand.control_point1 is not None:
                                    cp1_rect = QRectF(
                                        strand.control_point1.x() - half_control_size,
                                        strand.control_point1.y() - half_control_size,
                                        square_control_size,
                                        square_control_size
                                    )
                                
                                if hasattr(strand, 'control_point2') and strand.control_point2 is not None:
                                    cp2_rect = QRectF(
                                        strand.control_point2.x() - half_control_size,
                                        strand.control_point2.y() - half_control_size,
                                        square_control_size,
                                        square_control_size
                                    )
                                if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                                    cp3_rect = QRectF(
                                        strand.control_point_center.x() - half_control_size,
                                        strand.control_point_center.y() - half_control_size,
                                        square_control_size,
                                        square_control_size
                                    )
                                else:
                                    cp3_rect = None
                                # Check if control points overlap with yellow rectangle
                                cp1_overlaps_yellow = yellow_rectangle and cp1_rect and self.rectangles_overlap(cp1_rect, yellow_rectangle)
                                cp2_overlaps_yellow = yellow_rectangle and cp2_rect and self.rectangles_overlap(cp2_rect, yellow_rectangle)
                                cp3_overlaps_yellow = yellow_rectangle and cp3_rect and self.rectangles_overlap(cp3_rect, yellow_rectangle)
                                # Draw with green color for non-selected control points
                                square_color = QColor(0, 100, 0, 100)  # Green with 50% transparency
                                painter.setBrush(QBrush(square_color))
                                painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Solid line for better visibility
                                
                                # If moving a control point, only draw the specific control point being moved
                                if is_moving_control_point:
                                    if selected_side == 'control_point1' and cp1_rect and not skip_cp1 and not cp1_overlaps_yellow:
                                        painter.drawRect(cp1_rect)
                                    elif selected_side == 'control_point2' and cp2_rect and not skip_cp2 and not cp2_overlaps_yellow:
                                        painter.drawRect(cp2_rect)
                                    elif selected_side == 'control_point_center' and cp3_rect and not skip_cp3 and not cp3_overlaps_yellow and hasattr(self, 'enable_third_control_point') and self.enable_third_control_point:
                                        painter.drawRect(cp3_rect)
                                else:
                                    # Normal drawing when not moving a control point
                                    if cp1_rect and not skip_cp1 and not cp1_overlaps_yellow:
                                        painter.drawRect(cp1_rect)
                                    
                                    if cp2_rect and not skip_cp2 and not cp2_overlaps_yellow:
                                        painter.drawRect(cp2_rect)
                                    if cp3_rect and not skip_cp3 and not cp3_overlaps_yellow and hasattr(self, 'enable_third_control_point') and self.enable_third_control_point:
                                        painter.drawRect(cp3_rect)
            # Draw the selected rectangle with yellow color
            if self.current_mode.selected_rectangle:
                # Set up semi-transparent yellow color
                square_color = QColor(255, 230, 160, 140)  # Yellow with transparency
                painter.setBrush(QBrush(square_color))
                painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Solid line for better visibility
                
                # If we have a selected strand and side, create the yellow square directly
                if self.current_mode.affected_strand and self.current_mode.moving_side is not None:
                    affected_strand = self.current_mode.affected_strand
                    moving_side = self.current_mode.moving_side
                    
                    # Create a yellow square of the defined size
                    if moving_side == 0:  # Start point
                        yellow_rect = QRectF(
                            affected_strand.start.x() - half_yellow_size,
                            affected_strand.start.y() - half_yellow_size,
                            yellow_square_size,
                            yellow_square_size
                        )
                        painter.drawRect(yellow_rect)
                    elif moving_side == 1:  # End point
                        yellow_rect = QRectF(
                            affected_strand.end.x() - half_yellow_size,
                            affected_strand.end.y() - half_yellow_size,
                            yellow_square_size,
                            yellow_square_size
                        )
                        painter.drawRect(yellow_rect)
                    elif moving_side == 'control_point1' and hasattr(affected_strand, 'control_point1'):
                        # Use control point size for control points
                        yellow_rect = QRectF(
                            affected_strand.control_point1.x() - half_control_size,
                            affected_strand.control_point1.y() - half_control_size,
                            square_control_size,
                            square_control_size
                        )
                        painter.drawRect(yellow_rect)
                    elif moving_side == 'control_point2' and hasattr(affected_strand, 'control_point2'):
                        # Use control point size for control points
                        yellow_rect = QRectF(
                            affected_strand.control_point2.x() - half_control_size,
                            affected_strand.control_point2.y() - half_control_size,
                            square_control_size,
                            square_control_size
                        )
                        painter.drawRect(yellow_rect)
                    elif moving_side == 'control_point_center' and hasattr(affected_strand, 'control_point_center'):
                        # Use control point size for control points
                        yellow_rect = QRectF(
                            affected_strand.control_point_center.x() - half_control_size,
                            affected_strand.control_point_center.y() - half_control_size,
                            square_control_size,
                            square_control_size
                        )
                        painter.drawRect(yellow_rect)
                        
                # Fall back to using the selected_rectangle from MoveMode if direct creation not possible
                elif isinstance(self.current_mode.selected_rectangle, QPainterPath):
                    painter.drawPath(self.current_mode.selected_rectangle)
                elif isinstance(self.current_mode.selected_rectangle, QRectF):
                    painter.drawRect(self.current_mode.selected_rectangle)

            painter.restore()

        # Draw the angle adjustment visualization if in angle adjust mode
        if self.is_angle_adjusting and self.angle_adjust_mode and self.angle_adjust_mode.active_strand:
            self.angle_adjust_mode.draw(painter)

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
                eraser_rect = QRectF(
                    self.last_pos.x() - self.eraser_size/2,
                    self.last_pos.y() - self.eraser_size/2,
                    self.eraser_size,
                    self.eraser_size
                )
                eraser_overlaps_yellow = yellow_rectangle and self.rectangles_overlap(eraser_rect, yellow_rectangle)
                if not eraser_overlaps_yellow:
                    painter.setPen(QPen(Qt.white, 1, Qt.DashLine))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(eraser_rect)

        logging.info(
            f"Paint event completed. Selected strand: "
            f"{self.selected_strand.layer_name if self.selected_strand and hasattr(self.selected_strand, 'layer_name') else 'None'}"
        )

        painter.end()

        # ADD new painter to draw on top of everything:
        # ---------------------------------------------------------
        overlay_painter = QPainter(self)
        overlay_painter.setRenderHint(QPainter.Antialiasing)

        # Draw attach-mode circles on top
        if isinstance(self.current_mode, AttachMode):
            overlay_painter.save()
            for strand in self.strands:
                if isinstance(strand, MaskedStrand):
                    continue

                # Draw circles regardless of proximity to other points
                # Start circle
                if not strand.start_attached:  # Only check the strand's own attachment state
                    # Highlight if currently affected
                    if (getattr(self.current_mode, 'affected_strand', None) == strand and 
                        getattr(self.current_mode, 'affected_point', None) == 0):
                        circle_color = QColor(255, 255, 20, 100)  # Yellow highlight
                    else:
                        circle_color = QColor(255, 0, 0, 60)  # Default red

                    overlay_painter.setBrush(QBrush(circle_color))
                    overlay_painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
                    circle_size = 120
                    radius = circle_size / 2
                    start_ellipse = QRectF(
                        strand.start.x() - radius,
                        strand.start.y() - radius,
                        circle_size,
                        circle_size
                    )
                    overlay_painter.drawEllipse(start_ellipse)

                # End circle
                if not strand.end_attached:  # Only check the strand's own attachment state
                    # Highlight if currently affected
                    if (getattr(self.current_mode, 'affected_strand', None) == strand and 
                        getattr(self.current_mode, 'affected_point', None) == 1):
                        circle_color = QColor(255, 255, 20, 100)  # Yellow highlight
                    else:
                        circle_color = QColor(0, 0, 255, 60)  # Default blue

                    overlay_painter.setBrush(QBrush(circle_color))
                    overlay_painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
                    circle_size = 120
                    radius = circle_size / 2
                    end_ellipse = QRectF(
                        strand.end.x() - radius,
                        strand.end.y() - radius,
                        circle_size,
                        circle_size
                    )
                    overlay_painter.drawEllipse(end_ellipse)

            overlay_painter.restore()
        # ---------------------------------------------------------
        overlay_painter.end()
        # ---------------------------------------------------------

    def toggle_control_points(self):
        """Toggle the visibility of control points."""
        self.show_control_points = not self.show_control_points
        logging.info(f"Control points visibility toggled: {self.show_control_points}")
        
        # Make sure both implementations respect the toggle state
        for strand in self.strands:
            if hasattr(strand, 'show_control_points'):
                strand.show_control_points = self.show_control_points
                
        self.update()  # Force a redraw of the canvas

    def toggle_shadow(self):
        """Toggle shadow rendering on or off."""
        self.shadow_enabled = not self.shadow_enabled
        logging.info(f"Shadow rendering toggled: {self.shadow_enabled}")
        self.update()  # Force a redraw of the canvas to apply the change
        
    def set_shadow_color(self, color):
        """Set the shadow color for all strands."""
        logging.info(f"Setting shadow color: Received {color.red()},{color.green()},{color.blue()},{color.alpha()}")
        
        # Create a fresh QColor to avoid reference issues
        self.default_shadow_color = QColor(color.red(), color.green(), color.blue(), color.alpha())
        
        # Apply to all existing strands
        for strand in self.strands:
            # Create a fresh QColor for each strand to avoid reference issues
            strand.shadow_color = QColor(color.red(), color.green(), color.blue(), color.alpha())
        
        logging.info(f"Shadow color set to: {self.default_shadow_color.red()},{self.default_shadow_color.green()},{self.default_shadow_color.blue()},{self.default_shadow_color.alpha()}")
        self.update()  # Force a redraw of the canvas to apply the change





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
            
        # Check if the strands actually intersect before creating a masked layer
        # This prevents creating masked layers for non-intersecting strands
        try:
            # Create temporary MaskedStrand to use its helper method
            temp_masked = MaskedStrand(strand1, strand2)
            
            # Get the stroked paths for both strands
            path1 = temp_masked.get_stroked_path_for_strand(strand1)
            path2 = temp_masked.get_stroked_path_for_strand(strand2)
            
            # Calculate the intersection
            intersection_path = path1.intersected(path2)
            
            # If there's no intersection, don't create a masked layer
            if intersection_path.isEmpty():
                logging.info(f"No intersection between {strand1.layer_name} and {strand2.layer_name}. Skipping masked layer creation.")
                return
                
            logging.info(f"Found intersection between {strand1.layer_name} and {strand2.layer_name}. Creating masked layer.")
            
            # Use the already created temp_masked instead of creating a new one
            masked_strand = temp_masked
        except Exception as e:
            logging.error(f"Error checking intersection: {e}")
            # Create the masked strand if the intersection check fails
            masked_strand = MaskedStrand(strand1, strand2)
        
        # Set the shadow color to the default shadow color
        if hasattr(self, 'default_shadow_color') and self.default_shadow_color:
            # Create a fresh QColor instance to avoid reference issues
            masked_strand.shadow_color = QColor(
                self.default_shadow_color.red(),
                self.default_shadow_color.green(),
                self.default_shadow_color.blue(),
                self.default_shadow_color.alpha()
            )
            logging.info(f"Set masked strand shadow color to {masked_strand.shadow_color.red()},{masked_strand.shadow_color.green()},{masked_strand.shadow_color.blue()},{masked_strand.shadow_color.alpha()}")
        else:
            # Fall back to default shadow color if not set
            masked_strand.shadow_color = QColor(0, 0, 0, 150)

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
        if isinstance(strand, MaskedStrand):
            self.draw_highlighted_masked_strand(painter, strand)
        else:
            # Get the path representing the strand as a cubic Bézier curve
            path = strand.get_path()

            # Create a stroker for the stroke path with squared ends - EXACTLY like in strand.draw()
            stroke_stroker = QPainterPathStroker()
            stroke_stroker.setWidth(strand.width + strand.stroke_width * 2)
            stroke_stroker.setJoinStyle(Qt.MiterJoin)
            stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
            stroke_path = stroke_stroker.createStroke(path)

        
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)
            # Draw the regular strand
            strand.draw(painter)
            
            # Check if we're moving a control point
            is_moving_control_point = False
            if hasattr(self, 'current_mode') and self.current_mode.__class__.__name__ == 'MoveMode':
                move_mode = self.current_mode
                is_moving_control_point = move_mode.is_moving_control_point
            
            # Slightly thinner stroke for circles
            for i, has_circle in enumerate(strand.has_circles):
                # Skip drawing C-shapes when moving control points
                if has_circle and not is_moving_control_point:
                    # Save painter state
                    painter.save()
                    
                    center = strand.start if i == 0 else strand.end
                    
                    # --- NEW: Check for hidden attached strands at this connection point --- 
                    skip_c_shape = False
                    for other_strand in self.strands:
                        if isinstance(other_strand, AttachedStrand) and other_strand.is_hidden:
                            # Check if the hidden attached strand connects to the current center point AND is the selected strand
                            if (self.points_are_close(other_strand.start, center) or self.points_are_close(other_strand.end, center)) and other_strand == self.selected_strand:
                                skip_c_shape = True
                                logging.info(f"Skipping C-shape at {center} for {strand.layer_name} because the selected hidden attached strand {other_strand.layer_name} connects here.")
                                break # Found the selected hidden attached strand, no need to check further
                                
                    if skip_c_shape:
                        painter.restore() # Restore painter state
                        continue # Skip drawing C-shape for this point
                    # --- END NEW CHECK --- 

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
                    
                    # Calculate angle based on tangent or start/end points
                    angle = 0.0 # Default angle
                    if i == 0 and strand.control_point1 == strand.start and strand.control_point2 == strand.start:
                        direction_vector = strand.end - strand.start
                        if direction_vector.manhattanLength() > 1e-6:
                            angle = math.atan2(direction_vector.y(), direction_vector.x())
                    else:
                        tangent = strand.calculate_cubic_tangent(0.0 if i == 0 else 1.0)
                        if tangent.manhattanLength() > 1e-6:
                            angle = math.atan2(tangent.y(), tangent.x())

                    # Create a masking rectangle to create a C-shape
                    mask_rect = QPainterPath()
                    rect_width = (outer_radius + 5) * 2
                    rect_height = (outer_radius + 5) * 2
                    rect_x = center.x() - rect_width / 2
                    rect_y = center.y()
                    mask_rect.addRect(rect_x, rect_y, rect_width, rect_height)
                    
                    # Apply rotation transform
                    transform = QTransform()
                    transform.translate(center.x(), center.y())
                    if i == 0:
                        transform.rotate(math.degrees(angle - math.pi / 2))
                    else:
                        transform.rotate(math.degrees(angle - math.pi / 2) + 180)
                    transform.translate(-center.x(), -center.y())
                    mask_rect = transform.map(mask_rect)
                    
                    # Create the C-shaped highlight
                    c_shape_path = ring_path.subtracted(mask_rect)
                    
                    # Draw the C-shaped highlight
                    stroke_pen = QPen(QColor(255, 0, 0, 255), strand.stroke_width)
                    stroke_pen.setJoinStyle(Qt.MiterJoin)
                    stroke_pen.setCapStyle(Qt.FlatCap)
                    painter.setPen(stroke_pen)
                    painter.setBrush(QColor(255, 0, 0, 255))
                    painter.drawPath(c_shape_path)
                    
                    # Restore painter state
                    painter.restore()
            
            # This restore was likely misplaced inside the loop, moved outside
            # painter.restore()

    def draw_moving_strand(self, painter, strand):
        """Draw a moving strand without any highlights."""
        if isinstance(strand, MaskedStrand):
            # For masked strands, just draw normally without highlight
            masked_strand = strand
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Just draw the regular masked strand without any highlight
            masked_strand.draw(painter)
            
            painter.restore()
        else:
            # For regular strands, just draw normally without any highlight
            painter.save()
            
            # Temporarily set is_selected to False to prevent red highlight
            original_is_selected = strand.is_selected
            strand.is_selected = False
            
            # Draw the strand
            strand.draw(painter)
            
            # Restore the original is_selected value
            strand.is_selected = original_is_selected
            
            painter.restore()

     

    def draw_highlighted_masked_strand(self, painter, masked_strand):
        import logging
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # First check if there's an actual intersection between the strands
        path1 = masked_strand.get_stroked_path_for_strand(masked_strand.first_selected_strand)
        path2 = masked_strand.get_stroked_path_for_strand(masked_strand.second_selected_strand)
        intersection_path = path1.intersected(path2)
        
        # Initialize shadow path data to prevent 'all_shadow_paths' errors
        if hasattr(masked_strand, 'initialize_shadow_path'):
            masked_strand.initialize_shadow_path()
        
        # Log the selection state for debugging
        logging.info(f"Drawing highlighted masked strand: {masked_strand.layer_name}, is_selected={masked_strand.is_selected}")
        
        # Only proceed with drawing if there's an actual intersection
        if not intersection_path.isEmpty():
            # Always draw the masked strand normally first
            masked_strand.draw(painter)
            
            # Determine if we should draw highlight
            should_draw_highlight = masked_strand.is_selected
            
            # Check if we're in active movement (any type)
            if hasattr(self, 'current_mode') and self.current_mode.__class__.__name__ == 'MoveMode':
                move_mode = self.current_mode
                
                # Only skip highlight during active movement, not after movement is complete
                if move_mode.is_moving and move_mode.affected_strand == masked_strand:
                    logging.info(f"Active movement in progress for {masked_strand.layer_name}")
                    # Even during movement, highlight if this strand is selected
                    # This ensures proper visual feedback during movement
                    if masked_strand.is_selected:
                        logging.info(f"Strand is selected during movement, will draw highlight")
                        should_draw_highlight = True
                    else:
                        logging.info(f"Strand is not selected during movement, skipping highlight")
                        should_draw_highlight = False
            
            # Draw highlight if appropriate
            if should_draw_highlight:
                logging.info(f"Drawing highlight for masked strand: {masked_strand.layer_name}")
                masked_strand.draw_highlight(painter)
            else:
                logging.info(f"Skipping highlight for masked strand: {masked_strand.layer_name} (not selected or active movement)")
        else:
            logging.info(f"Skipping masked strand highlights: no intersection between strands for {masked_strand.layer_name}")

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
        logging.info(f"Updating color for set {set_number} to {color.name()}")
        self.strand_colors[set_number] = color
        
        # Convert set_number to string for comparison
        set_prefix = f"{set_number}_"
        
        for strand in self.strands:
            if not hasattr(strand, 'layer_name') or not strand.layer_name:
                logging.info("Skipping strand without layer_name")
                continue

            logging.info(f"Checking strand: {strand.layer_name}")

            # Check if the strand's layer_name starts with our set_prefix
            if strand.layer_name.startswith(set_prefix):
                strand.set_color(color)

                # NEW: Ensure the black stroke also respects the alpha
                if hasattr(strand, 'stroke_color') and isinstance(strand.stroke_color, QColor):
                    stroke_with_alpha = QColor(strand.stroke_color)
                    stroke_with_alpha.setAlpha(color.alpha())
                    strand.stroke_color = stroke_with_alpha

                logging.info(f"Updated color for strand: {strand.layer_name}")

            elif isinstance(strand, MaskedStrand):
                first_part = strand.layer_name.split('_')[0]  # Get the first number only
                if first_part == str(set_number):
                    strand.set_color(color)

                    # NEW: Ensure the black stroke also respects the alpha
                    if hasattr(strand, 'stroke_color') and isinstance(strand.stroke_color, QColor):
                        stroke_with_alpha = QColor(strand.stroke_color)
                        stroke_with_alpha.setAlpha(color.alpha())
                        strand.stroke_color = stroke_with_alpha

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
                self.strand_colors[set_number] = QColor(200, 170, 230, 255) 
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





    def select_strand(self, index, update_layer_panel=True):
        """Select a strand by index."""
        logging.info(f"Entering select_strand. Index: {index}")
        # Deselect all strands first
        for strand in self.strands:
            strand.is_selected = False
            if hasattr(strand, 'attached_strands'):
                for attached_strand in strand.attached_strands:
                    attached_strand.is_selected = False

        # When explicitly selecting a strand, reset the user_deselected_all flag in MoveMode
        if index is not None and 0 <= index < len(self.strands) and isinstance(self.current_mode, MoveMode):
            if hasattr(self.current_mode, 'user_deselected_all'):
                self.current_mode.user_deselected_all = False

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
            
        # Clear selected strand references
        self.selected_strand = None
        self.selected_strand_index = None
        self.selected_attached_strand = None
        
        # Emit the deselect_all signal for connected objects
        self.deselect_all_signal.emit()

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
            logging.info(f"Selecting strand at position: {event.pos()}")
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
        elif self.current_mode and not isinstance(self.current_mode, str):
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
        elif self.current_mode and not isinstance(self.current_mode, str):
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
            # Set the shadow color to the default shadow color
            new_strand.shadow_color = self.default_shadow_color
            
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
            
            # Add this line to emit the strand_created signal
            # This is crucial for updating the layer_state_manager and enabling proper shading
            self.strand_created.emit(new_strand)

            # --- ADD LOGGING FOR STRAND CREATION (Button initiated) ---
            # Check *before* accessing attributes for logging
            if new_strand:
                logging.info(f"Strand Creation: Name={new_strand.layer_name}, Start={new_strand.start}, End={new_strand.end}")
            # --- END LOGGING ---

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
        elif mode == "control_points":
            self.toggle_control_points()
            self.current_mode = "control_points"
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
        
        # Set the shadow color to the default shadow color
        masked_strand.shadow_color = self.default_shadow_color

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
        # Instead of referencing self.selected_strand directly in the f-string:
        # logging.info(f"Clearing selection. Current selected strand: {self.selected_strand}")

        # First, capture a non-logging property (like layer_name), or safely handle None:
        strand_desc = self.selected_strand.layer_name if self.selected_strand else "None"
        logging.info(f"Clearing selection. Current selected strand: {strand_desc}")

        # Then proceed with clearing selection
        self.selected_strand = None
        self.selected_strand_index = None
        
        # Emit the deselect_all signal for connected objects
        self.deselect_all_signal.emit()
        
        self.update()

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

        # Newly added step: re-check attachments via geometry
        self.refresh_geometry_based_attachments()

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
            self.angle_adjust_mode.activate(strand)  # Pass the selected strand
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
        # If control points are not enabled, don't draw anything
        if not self.show_control_points:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        control_point_radius = 11 * 1.333  # Scaled by 1.333 to enlarge control point shapes

        stroke_color = QColor('black')

        # Check MoveMode state and settings
        in_move_mode = hasattr(self, 'current_mode') and isinstance(self.current_mode, MoveMode)
        moving_control_point = in_move_mode and getattr(self.current_mode, 'is_moving_control_point', False)
        moving_strand_point = in_move_mode and getattr(self.current_mode, 'is_moving_strand_point', False) # Keep this check
        affected_strand = getattr(self.current_mode, 'affected_strand', None) if in_move_mode else None
        moving_side = getattr(self.current_mode, 'moving_side', None) if in_move_mode else None # Added to access moving_side

        draw_only_setting_on = False
        if in_move_mode and hasattr(self.current_mode, 'draw_only_affected_strand'):
            draw_only_setting_on = self.current_mode.draw_only_affected_strand

        # --- Find connected strands if moving an endpoint with Draw Only ON ---
        connected_strands_at_moving_point = set()
        if draw_only_setting_on and moving_strand_point and affected_strand:
            moving_point_coord = None
            if moving_side == 0:
                moving_point_coord = affected_strand.start
            elif moving_side == 1:
                moving_point_coord = affected_strand.end

            if moving_point_coord:
                for other_strand in self.strands:
                    if other_strand == affected_strand or isinstance(other_strand, MaskedStrand):
                        continue
                    # Check both start and end points of the other strand
                    if self.points_are_close(other_strand.start, moving_point_coord) or \
                       self.points_are_close(other_strand.end, moving_point_coord):
                        connected_strands_at_moving_point.add(other_strand)
        # --- End finding connected strands ---

        # Iterate through all strands
        for strand in self.strands:
            # Skip masked strands and strands without control points
            if isinstance(strand, MaskedStrand) or not hasattr(strand, 'control_point1') or not hasattr(strand, 'control_point2'):
                continue
            if strand.control_point1 is None or strand.control_point2 is None:
                continue

            # --- Determine if we should skip drawing CPs for this strand ---
            should_skip = False
            if draw_only_setting_on:
                if moving_control_point and strand != affected_strand:
                    # Skip if moving a CP and this isn't the affected strand
                    should_skip = True
                elif moving_strand_point and strand != affected_strand and strand not in connected_strands_at_moving_point:
                    # Skip if moving an endpoint, and this strand is not the affected one NOR connected at the moving point
                    should_skip = True

            if should_skip:
                continue
            # --- End skip logic ---

            # Draw All Points for Affected Strand (when moving CP with Draw Only ON)
            if draw_only_setting_on and moving_control_point and strand == affected_strand:
                # --- Start Replacement: Draw ALL control points/lines for the affected strand ---
                control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
                painter.setPen(control_line_pen)
                painter.drawLine(strand.start, strand.control_point1)
                # Use points_are_close for robustness
                if self.points_are_close(strand.control_point2, strand.start, tolerance=0.1):
                     painter.drawLine(strand.start, strand.control_point2)
                else:
                     painter.drawLine(strand.end, strand.control_point2)

                # Draw center control point lines if enabled
                if self.enable_third_control_point and hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                    painter.drawLine(strand.control_point_center, strand.control_point1)
                    painter.drawLine(strand.control_point_center, strand.control_point2)

                # Draw control points with stroke
                stroke_pen = QPen(stroke_color, 5)
                control_point_pen = QPen(QColor('green'), 1)
                painter.setBrush(QBrush(QColor('green')))

                # Draw control_point2 (circle)
                painter.setPen(stroke_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(strand.control_point2, control_point_radius, control_point_radius)
                painter.setPen(control_point_pen)
                painter.setBrush(QBrush(QColor('green')))
                painter.drawEllipse(strand.control_point2, control_point_radius - 1, control_point_radius - 1)
                # Draw inner circle with strand's color
                inner_radius = (control_point_radius - 1) * 0.5
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(strand.color))
                painter.drawEllipse(strand.control_point2, inner_radius, inner_radius)

                # Draw control_point1 (triangle)
                triangle = QPolygonF()
                center_x = strand.control_point1.x()
                # Adjust y slightly for better visual centering of triangle
                center_y = strand.control_point1.y() + 1.06 * 1.333

                # Create triangle vertices
                angle1 = math.radians(270)
                triangle.append(QPointF(
                    center_x + control_point_radius*1.06 * math.cos(angle1),
                    center_y + control_point_radius*1.06  * math.sin(angle1)
                ))
                angle2 = math.radians(30)
                triangle.append(QPointF(
                    center_x + control_point_radius*1.06  * math.cos(angle2),
                    center_y + control_point_radius*1.06  * math.sin(angle2)
                ))
                angle3 = math.radians(150)
                triangle.append(QPointF(
                    center_x + control_point_radius*1.06  * math.cos(angle3),
                    center_y + control_point_radius*1.06  * math.sin(angle3)
                ))

                # Draw stroke
                painter.setPen(stroke_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(triangle)

                # Draw fill
                painter.setPen(control_point_pen)
                painter.setBrush(QBrush(QColor('green')))

                # Create smaller triangle for fill
                filled_triangle = QPolygonF()
                scale_factor = (control_point_radius  - 1.06 ) / (control_point_radius* 1.06)
                for point in triangle:
                    vec_x = point.x() - center_x
                    vec_y = point.y() - center_y
                    filled_triangle.append(QPointF(
                        center_x + vec_x * scale_factor,
                        center_y + vec_y * scale_factor
                    ))
                painter.drawPolygon(filled_triangle)
                # Draw inner triangle with strand's color
                inner_triangle = QPolygonF()
                for pt in filled_triangle:
                    dx = pt.x() - center_x
                    dy = pt.y() - center_y
                    inner_triangle.append(QPointF(center_x + dx * 0.5, center_y + dy * 0.5))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(strand.color))
                painter.drawPolygon(inner_triangle)

                # Draw control_point_center (square) if enabled
                if self.enable_third_control_point and hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                    # Draw stroke square
                    painter.setPen(stroke_pen)
                    painter.setBrush(Qt.NoBrush)
                    square_size = control_point_radius * 2 * 0.7
                    square_rect = QRectF(
                        strand.control_point_center.x() - (control_point_radius * 0.7),
                        strand.control_point_center.y() - (control_point_radius * 0.7),
                        square_size,
                        square_size
                    )
                    painter.drawRect(square_rect)
                    # Draw fill
                    painter.setPen(control_point_pen)
                    painter.setBrush(QBrush(QColor('green')))
                    inner_size = square_size - 2
                    inner_rect = QRectF(
                        strand.control_point_center.x() - ((control_point_radius * 0.7) - 1),
                        strand.control_point_center.y() - ((control_point_radius * 0.7) - 1),
                        inner_size,
                        inner_size
                    )
                    painter.drawRect(inner_rect)
                    # Draw inner square with strand's color
                    inner_square_size = inner_size * 0.5
                    inner_square_rect = QRectF(
                        strand.control_point_center.x() - inner_square_size / 2,
                        strand.control_point_center.y() - inner_square_size / 2,
                        inner_square_size,
                        inner_square_size
                    )
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(strand.color))
                    painter.drawRect(inner_square_rect)
                # --- End Replacement ---

                continue # Move to the next strand after drawing the points for the affected strand

            # --- Normal Drawing Logic ---
            # Executed when:
            # 1. "Draw only" is OFF, regardless of movement.
            # 2. "Draw only" is ON, but we are NOT moving.
            # 3. "Draw only" is ON, we ARE moving a strand point, and this IS the affected strand OR a connected strand.
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(strand.start, strand.control_point1)
            if self.points_are_close(strand.control_point2, strand.start, tolerance=0.1):
                print("control_point2 is close to start") # Keep debug print?
                painter.drawLine(strand.start, strand.control_point2)
            else:
                print("control_point2 is not close to start") # Keep debug print?
                painter.drawLine(strand.end, strand.control_point2)

            # Draw center control point lines if enabled
            if self.enable_third_control_point and hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                painter.drawLine(strand.control_point_center, strand.control_point1)
                painter.drawLine(strand.control_point_center, strand.control_point2)

            # Draw control points with stroke
            stroke_pen = QPen(stroke_color, 5)
            control_point_pen = QPen(QColor('green'), 1)
            painter.setBrush(QBrush(QColor('green')))

            # Draw control_point2 (circle)
            painter.setPen(stroke_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(strand.control_point2, control_point_radius, control_point_radius)

            painter.setPen(control_point_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(strand.control_point2, control_point_radius - 1, control_point_radius - 1)
            # Draw inner circle with strand's color
            inner_radius = (control_point_radius - 1) * 0.5
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(strand.color))
            painter.drawEllipse(strand.control_point2, inner_radius, inner_radius)

            # Draw control_point1 (triangle)
            triangle = QPolygonF()
            center_x = strand.control_point1.x()
            center_y = strand.control_point1.y()+1.06

            # Create triangle vertices
            angle1 = math.radians(270)
            triangle.append(QPointF(
                center_x + control_point_radius*1.06 * math.cos(angle1),
                center_y + control_point_radius*1.06  * math.sin(angle1)
            ))
            angle2 = math.radians(30)
            triangle.append(QPointF(
                center_x + control_point_radius*1.06  * math.cos(angle2),
                center_y + control_point_radius*1.06  * math.sin(angle2)
            ))
            angle3 = math.radians(150)
            triangle.append(QPointF(
                center_x + control_point_radius*1.06  * math.cos(angle3),
                center_y + control_point_radius*1.06  * math.sin(angle3)
            ))

            # Draw stroke
            painter.setPen(stroke_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(triangle)

            # Draw fill
            painter.setPen(control_point_pen)
            painter.setBrush(QBrush(QColor('green')))

            # Create smaller triangle for fill
            filled_triangle = QPolygonF()
            scale_factor = (control_point_radius  - 1.06 ) / (control_point_radius* 1.06)
            for point in triangle:
                vec_x = point.x() - center_x
                vec_y = point.y() - center_y
                filled_triangle.append(QPointF(
                    center_x + vec_x * scale_factor,
                    center_y + vec_y * scale_factor
                ))
            painter.drawPolygon(filled_triangle)
            # Draw inner triangle with strand's color
            inner_triangle = QPolygonF()
            for pt in filled_triangle:
                dx = pt.x() - center_x
                dy = pt.y() - center_y
                inner_triangle.append(QPointF(center_x + dx * 0.5, center_y + dy * 0.5))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(strand.color))
            painter.drawPolygon(inner_triangle)

            # Draw control_point_center (square) if enabled
            if self.enable_third_control_point and hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                # Draw stroke square
                painter.setPen(stroke_pen)
                painter.setBrush(Qt.NoBrush)
                square_size = control_point_radius * 2 * 0.7  # Made 0.618 times smaller
                square_rect = QRectF(
                    strand.control_point_center.x() - (control_point_radius * 0.7),
                    strand.control_point_center.y() - (control_point_radius * 0.7),
                    square_size,
                    square_size
                )
                painter.drawRect(square_rect)

                # Draw fill with slightly smaller square
                painter.setPen(control_point_pen)
                painter.setBrush(QBrush(QColor('green')))
                inner_size = square_size - 2
                inner_rect = QRectF(
                    strand.control_point_center.x() - ((control_point_radius * 0.7) - 1),
                    strand.control_point_center.y() - ((control_point_radius * 0.7) - 1),
                    inner_size,
                    inner_size
                )
                painter.drawRect(inner_rect)
                # Draw inner square with strand's color
                inner_square_size = inner_size * 0.5
                inner_square_rect = QRectF(
                    strand.control_point_center.x() - inner_square_size / 2,
                    strand.control_point_center.y() - inner_square_size / 2,
                    inner_square_size,
                    inner_square_size
                )
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(strand.color))
                painter.drawRect(inner_square_rect)

        painter.restore()

    # Add a setter for enable_third_control_point to handle resetting control points
    @property
    def enable_third_control_point(self):
        return getattr(self, '_enable_third_control_point', False)
        
    @enable_third_control_point.setter
    def enable_third_control_point(self, value):
        old_value = getattr(self, '_enable_third_control_point', False)
        self._enable_third_control_point = value
        
        # Initialize all strands with a center control point if we're enabling third control point
        if value and not old_value:
            for strand in self.strands:
                # Skip masked strands or strands without control points
                if isinstance(strand, MaskedStrand):
                    continue
                
                if (hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2') and
                    strand.control_point1 is not None and strand.control_point2 is not None):
                    # Initialize the center control point if it doesn't exist
                    if not hasattr(strand, 'control_point_center') or strand.control_point_center is None:
                        strand.control_point_center = QPointF(
                            (strand.control_point1.x() + strand.control_point2.x()) / 2,
                            (strand.control_point1.y() + strand.control_point2.y()) / 2
                        )
                        strand.control_point_center_locked = False
                        strand.update_shape()
        
        # If the value is changing from True to False, reset the control_point_center 
        # for all strands to the default midpoint and unlock it
        elif old_value and not value:
            for strand in self.strands:
                if (hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2') and 
                    hasattr(strand, 'control_point_center') and 
                    strand.control_point1 is not None and strand.control_point2 is not None):
                    # Reset to midpoint between control_point1 and control_point2
                    strand.control_point_center = QPointF(
                        (strand.control_point1.x() + strand.control_point2.x()) / 2,
                        (strand.control_point1.y() + strand.control_point2.y()) / 2
                    )
                    # Reset the locked state
                    strand.control_point_center_locked = False
                    # Update strand shape
                    strand.update_shape()
        # Force a redraw
        self.update()

    def handle_strand_selection(self, pos):
        strands_at_point = self.find_strands_at_point(pos)
        if strands_at_point:
            selected_strand = strands_at_point[-1]  # Select the topmost strand
            index = self.strands.index(selected_strand)

            # When directly clicking on a strand, reset the user_deselected_all flag in MoveMode
            if isinstance(self.current_mode, MoveMode) and hasattr(self.current_mode, 'user_deselected_all'):
                self.current_mode.user_deselected_all = False

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
            contains_path = strand.get_selection_path().contains(pos)  # Check the main path
            if contains_start or contains_end or contains_path:  # Include path check
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
        
        # Update related masked strands if this strand is part of any masks
        for i, other_strand in enumerate(self.strands):
            # Check if this is a masked strand by looking for masked strand attributes
            if (hasattr(other_strand, 'first_selected_strand') and 
                hasattr(other_strand, 'second_selected_strand')):
                # Check if our strand is part of this masked strand
                if (other_strand.first_selected_strand == strand or 
                    other_strand.second_selected_strand == strand):
                    logging.info(f"Updating masked strand {other_strand.layer_name} related to moved strand {strand.layer_name}")
                    # Force shadow update which will transform custom masks
                    if hasattr(other_strand, 'force_shadow_update'):
                        other_strand.force_shadow_update()

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
        
        # Group strands by their prefix (e.g., "1_" or "2_")
        strand_groups = {}
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                continue
            # Get prefix (everything before the underscore)
            prefix = strand.layer_name.split('_')[0]
            if prefix not in strand_groups:
                strand_groups[prefix] = []
            strand_groups[prefix].append(strand)


        # Second pass: Update based on connections from layer_state_manager
        for prefix, strands_in_group in strand_groups.items():
            for strand in strands_in_group:
                # Get connections for this strand from layer_state_manager
                strand_connections = connections.get(strand.layer_name, [])
                
                for connected_layer_name in strand_connections:
                    # Find the connected strand in the same group
                    connected_strand = next(
                        (s for s in strands_in_group if s.layer_name == connected_layer_name), 
                        None
                    )
                    
                    if connected_strand:
                    # Check start point connections
                        if self.points_are_close(strand.start, connected_strand.start) or \
                           self.points_are_close(strand.start, connected_strand.end):
                            strand.start_attached = True
                            strand.has_circles[0] = True
                            logging.info(f"Found start connection for {strand.layer_name} with {connected_strand.layer_name}")

                    # Check end point connections
                        if self.points_are_close(strand.end, connected_strand.start) or \
                           self.points_are_close(strand.end, connected_strand.end):
                            strand.end_attached = True
                            strand.has_circles[1] = True
                            logging.info(f"Found end connection for {strand.layer_name} with {connected_strand.layer_name}")

                logging.info(f"Final state for {strand.layer_name}: has_circles={strand.has_circles}")

        # --- NEW: Re-apply manual circle visibility overrides (recursive for attached strands) ---
        def _apply_manual_circle_overrides(s):
            if hasattr(s, 'manual_circle_visibility') and isinstance(s.manual_circle_visibility, (list, tuple)):
                for idx in range(min(len(s.has_circles), len(s.manual_circle_visibility))):
                    override = s.manual_circle_visibility[idx]
                    if override is not None and s.has_circles[idx] != override:
                        logging.info(
                            f"Applying manual circle visibility override for {s.layer_name} index {idx}: {override}")
                        s.has_circles[idx] = override

            # Recurse into any attached strands
            if hasattr(s, 'attached_strands') and s.attached_strands:
                for child in s.attached_strands:
                    _apply_manual_circle_overrides(child)

        for strand in self.strands:
            _apply_manual_circle_overrides(strand)
        # --- END NEW ---

        logging.info("update_attachment_statuses completed")

    def set_layer_state_manager(self, layer_state_manager):
        self.layer_state_manager = layer_state_manager
        # Connect any necessary signals here

    def refresh_geometry_based_attachments(self):
        """
        Placeholder method to refresh attachments based on geometry.
        Currently calls update_attachment_statuses.
        """
        logging.info("Refreshing geometry-based attachments (calling update_attachment_statuses)")
        self.update_attachment_statuses()

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
        Find a control point at the given position.
        
        Args:
            pos (QPointF): The position to check for a control point.
            
        Returns:
            (strand, point_type): The strand and the type of point ('control_point1' or 'control_point2')
                                  or None if no control point is found.
        """
        tolerance = 15  # Slightly larger than the visual size of control points
        
        if not self.show_control_points:
            return None, None
            
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                continue
                
            if strand.control_point1 and strand.control_point2:
                # Check distance from pos to control_point1
                distance_to_cp1 = math.hypot(
                    pos.x() - strand.control_point1.x(), 
                    pos.y() - strand.control_point1.y()
                )
                if distance_to_cp1 <= tolerance:
                    return strand, 'control_point1'
                    
                # Check distance from pos to control_point2
                distance_to_cp2 = math.hypot(
                    pos.x() - strand.control_point2.x(), 
                    pos.y() - strand.control_point2.y()
                )
                if distance_to_cp2 <= tolerance:
                    return strand, 'control_point2'
                
                # Check for center control point if enabled
                if self.enable_third_control_point:
                    distance_to_center = math.hypot(
                        pos.x() - strand.control_point_center.x(),
                        pos.y() - strand.control_point_center.y()
                    )
                    if distance_to_center <= tolerance:
                        return strand, 'control_point_center'
                
        return None, None

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
        strand, control_point_type = self.find_control_point_at_position(pos)
        if strand and control_point_type:
            # Select the strand and store the control point type
            self.selected_strand = strand
            self.selected_point = control_point_type
            self.update()
            return True
        return False

    def rectangles_overlap(self, rect1, rect2):
        """Check if two QRectF objects overlap."""
        return rect1.intersects(rect2)

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
        """Reset the custom mask (and deletion rectangles) of the masked strand at the given index.

        This is invoked by LayerPanel and other UI components. It safely exits any
        active mask-edit mode that targets the same strand, calls the underlying
        MaskedStrand.reset_mask(), forces a canvas redraw, and records the action
        in the undo/redo manager if present.
        """
        logging.info(f"[StrandDrawingCanvas] reset_mask START for index {strand_index}")
        if not (0 <= strand_index < len(self.strands)):
            logging.warning(f"reset_mask called with invalid index: {strand_index}")
            return

        strand = self.strands[strand_index]
        if not isinstance(strand, MaskedStrand):
            logging.warning(
                f"reset_mask called for a non-masked strand at index {strand_index} ({getattr(strand, 'layer_name', 'unknown')})"
            )
            return

        # If we are currently editing this mask, exit edit mode first
        logging.info(f"[StrandDrawingCanvas] Checking if in mask edit mode for strand {strand_index}...")
        if self.mask_edit_mode and self.editing_masked_strand is strand:
            logging.info(f"[StrandDrawingCanvas] Exiting mask edit mode for strand {strand_index}")
            self.exit_mask_edit_mode()

        # --- NEW: Ensure any open context menus are closed before proceeding ---
        logging.info(f"[StrandDrawingCanvas] Attempting to close active menus...")
        from PyQt5.QtWidgets import QApplication, QMenu
        # Close the currently active popup, if any
        active_popup = QApplication.activePopupWidget()
        if active_popup:
            active_popup.close()
            logging.info(f"[StrandDrawingCanvas] Closed active popup: {active_popup}")

        # Additionally close ANY stray QMenu instances that might still be
        # visible (sometimes nested or secondary menus can remain)
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMenu) and widget.isVisible():
                widget.close()
                logging.info(f"[StrandDrawingCanvas] Closed stray menu: {widget}")
        logging.info(f"[StrandDrawingCanvas] Menu closing attempt finished.")
        # --- END NEW ---

        # Perform the reset on the MaskedStrand itself
        try:
            strand.reset_mask()
        except Exception as e:
            logging.error(f"Error resetting mask for strand {strand.layer_name}: {e}")
            return

        # Request a repaint
        logging.info(f"[StrandDrawingCanvas] Requesting repaint after reset.")
        self.update()

        # Persist in undo/redo history if available
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            # Force immediate save to capture this state change
            self.undo_redo_manager._last_save_time = 0
            self.undo_redo_manager.save_state()
            logging.info(f"Undo/redo state saved after resetting mask for {strand.layer_name}")

        logging.info(f"[StrandDrawingCanvas] reset_mask END for index {strand_index}, strand {strand.layer_name}")
        logging.info(f"Mask reset for strand {strand.layer_name}")