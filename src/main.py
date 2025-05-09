import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from main_window import MainWindow
from undo_redo_manager import connect_to_move_mode, connect_to_attach_mode, connect_to_mask_mode

# Configure logging before importing other modules
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Add this section for MoveMode specific logging ---
class MoveModeFilter(logging.Filter):
    """Filters log records to include only those from move_mode.py."""
    def filter(self, record):
        # Normalize path for reliable comparison across OS
        # Use 'src' + os.sep + 'move_mode.py' for better cross-platform compatibility
        move_mode_path_part = os.path.normpath(os.path.join('src', 'move_mode.py'))
        # Check if the log record's pathname ends with the target file path
        return record.pathname.endswith(move_mode_path_part)

try:
    # Define the log file name
    move_mode_log_file = 'move_mode.log'

    # Attempt to delete the log file if it exists
    try:
        if os.path.exists(move_mode_log_file):
            os.remove(move_mode_log_file)
            logging.info(f"Removed existing log file: {move_mode_log_file}")
    except OSError as e:
        logging.error(f"Error removing log file {move_mode_log_file}: {e}")

    # Create a specific handler for MoveMode logs, overwriting the file each run ('w')
    move_mode_handler = logging.FileHandler(move_mode_log_file, mode='w')

    # Optional: Use a specific format for this file, otherwise it inherits root logger's format
    # move_mode_formatter = logging.Formatter('%(asctime)s - MOVE_MODE - %(levelname)s - %(message)s')
    # move_mode_handler.setFormatter(move_mode_formatter)

    # Apply the filter to the handler
    move_mode_handler.addFilter(MoveModeFilter())

    # Add the configured handler to the root logger
    logging.getLogger().addHandler(move_mode_handler)

    logging.info("MoveMode logging configured to output to move_mode.log") # Confirmation message

except Exception as e:
    print(f"Error setting up MoveMode file logging: {e}") # Basic error handling
# --- End of MoveMode logging section ---

# --- Add this section for Undo/Redo specific logging ---
class UndoRedoFilter(logging.Filter):
    """Filters log records to include only those from undo_redo_manager.py and related to UNDO/REDO actions."""
    def filter(self, record):
        # Normalize path for reliable comparison across OS
        undo_redo_path_part = os.path.normpath(os.path.join('src', 'undo_redo_manager.py'))
        # Check if the log record's pathname ends with the target file path
        is_from_undo_redo_manager = record.pathname.endswith(undo_redo_path_part)
        # Check if the message starts with "UNDO:" or "REDO:"
        is_undo_redo_action = record.getMessage().startswith(("UNDO:", "REDO:"))
        return is_from_undo_redo_manager and is_undo_redo_action

try:
    # Define the log file name
    undo_redo_log_file = 'undo_redo.log'

    # Attempt to delete the log file if it exists
    try:
        if os.path.exists(undo_redo_log_file):
            os.remove(undo_redo_log_file)
            logging.info(f"Removed existing log file: {undo_redo_log_file}")
    except OSError as e:
        logging.error(f"Error removing log file {undo_redo_log_file}: {e}")

    # Create a specific handler for Undo/Redo logs, overwriting the file each run ('w')
    undo_redo_handler = logging.FileHandler(undo_redo_log_file, mode='w')

    # Apply the filter to the handler
    undo_redo_handler.addFilter(UndoRedoFilter())

    # Add the configured handler to the root logger
    logging.getLogger().addHandler(undo_redo_handler)

    logging.info("Undo/Redo logging configured to output to undo_redo.log") # Confirmation message

except Exception as e:
    print(f"Error setting up Undo/Redo file logging: {e}") # Basic error handling
# --- End of Undo/Redo logging section ---

# --- Add this section for Strand Creation specific logging ---
class StrandCreationFilter(logging.Filter):
    """Filters log records to include only those related to strand creation."""
    def filter(self, record):
        # Check if the message starts with "Strand Creation:"
        return record.getMessage().startswith("Strand Creation:")

try:
    # Define the log file name
    strand_creation_log_file = 'strand_creation.log'

    # Attempt to delete the log file if it exists
    try:
        if os.path.exists(strand_creation_log_file):
            os.remove(strand_creation_log_file)
            logging.info(f"Removed existing log file: {strand_creation_log_file}")
    except OSError as e:
        logging.error(f"Error removing log file {strand_creation_log_file}: {e}")

    # Create a specific handler for Strand Creation logs, overwriting the file each run ('w')
    strand_creation_handler = logging.FileHandler(strand_creation_log_file, mode='w')

    # Apply the filter to the handler
    strand_creation_handler.addFilter(StrandCreationFilter())

    # Add the configured handler to the root logger
    logging.getLogger().addHandler(strand_creation_handler)

    logging.info("Strand Creation logging configured to output to strand_creation.log") # Confirmation message

except Exception as e:
    print(f"Error setting up Strand Creation file logging: {e}") # Basic error handling
# --- End of Strand Creation logging section ---

# --- Add this section for Masked Strand specific logging ---
class MaskedStrandFilter(logging.Filter):
    """Filters log records to include only those from masked_strand.py OR relevant logs from shader_utils.py."""
    def filter(self, record):
        # Normalize paths for reliable comparison across OS
        masked_strand_path_part = os.path.normpath(os.path.join('src', 'masked_strand.py'))
        shader_utils_path_part = os.path.normpath(os.path.join('src', 'shader_utils.py'))
        
        # Check conditions
        from_masked_strand = record.pathname.endswith(masked_strand_path_part)
        from_shader_utils_relevant = (
            record.pathname.endswith(shader_utils_path_part) and 
            record.getMessage().startswith("DrawMaskShadow -")
        )
        
        # Allow if either condition is met
        return from_masked_strand or from_shader_utils_relevant

try:
    # Define the log file name
    masked_strand_log_file = 'masked_strand.log'

    # Attempt to delete the log file if it exists
    try:
        if os.path.exists(masked_strand_log_file):
            os.remove(masked_strand_log_file)
            logging.info(f"Removed existing log file: {masked_strand_log_file}")
    except OSError as e:
        logging.error(f"Error removing log file {masked_strand_log_file}: {e}")

    # Create a specific handler for Masked Strand logs, overwriting the file each run ('w')
    masked_strand_handler = logging.FileHandler(masked_strand_log_file, mode='w')

    # Apply the filter to the handler
    masked_strand_handler.addFilter(MaskedStrandFilter())

    # Add the configured handler to the root logger
    logging.getLogger().addHandler(masked_strand_handler)

    logging.info("Masked Strand logging configured to output to masked_strand.log") # Confirmation message

except Exception as e:
    print(f"Error setting up Masked Strand file logging: {e}") # Basic error handling
# --- End of Masked Strand logging section ---

# --- Add this section for Mask Shadow Issues logging ---
class MaskShadowIssueFilter(logging.Filter):
    """Filters log records for shadow paths in shader_utils.py."""
    def filter(self, record):
        shader_utils_path_part = os.path.normpath(os.path.join('src', 'shader_utils.py'))
        return record.pathname.endswith(shader_utils_path_part) and record.getMessage().startswith("Shadow paths for strand")

try:
    mask_shadow_issues_log_file = 'mask_shadow_issues.log'

    # Attempt to delete the log file if it exists
    try:
        if os.path.exists(mask_shadow_issues_log_file):
            os.remove(mask_shadow_issues_log_file)
            logging.info(f"Removed existing log file: {mask_shadow_issues_log_file}")
    except OSError as e:
        logging.error(f"Error removing log file {mask_shadow_issues_log_file}: {e}")

    # Create a specific handler for mask shadow issues logs, overwriting each run
    mask_shadow_issues_handler = logging.FileHandler(mask_shadow_issues_log_file, mode='w')
    mask_shadow_issues_handler.addFilter(MaskShadowIssueFilter())
    logging.getLogger().addHandler(mask_shadow_issues_handler)
    logging.info("Mask Shadow Issues logging configured to output to mask_shadow_issues.log")

except Exception as e:
    print(f"Error setting up Mask Shadow Issues file logging: {e}") # Basic error handling
# --- End of Mask Shadow Issues logging section ---

# At the start of your main.py
# os.environ['QT_MAC_WANTS_LAYER'] = '1'

def load_user_settings():
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
    logging.info(f"Looking for settings file at: {file_path}")

    # Initialize with default values
    theme_name = 'default'
    language_code = 'en'
    shadow_color = QColor(0, 0, 0, 150)  # Default shadow color (black with 59% opacity)
    draw_only_affected_strand = False  # Default to drawing all strands
    enable_third_control_point = False  # Default to two control points
    use_extended_mask = False  # Default exact mask
    # Initialize arrow settings defaults
    arrow_head_length = 20.0
    arrow_head_width = 10.0
    arrow_gap_length = 10.0
    arrow_line_length = 20.0
    arrow_line_width = 10.0
    # Initialize default arrow fill color and toggle for using default color
    use_default_arrow_color = False
    default_arrow_fill_color = QColor(0, 0, 0, 255)
    
    # Try to load from settings file
    shadow_color_loaded = False
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                logging.info(f"Reading settings from user_settings.txt")
                content = file.read()
                logging.info(f"File content: {content}")
                
                # Reset file position to beginning
                file.seek(0)
                
                for line in file:
                    line = line.strip()
                    logging.info(f"Processing line: '{line}'")
                    
                    if line.startswith('Theme:'):
                        theme_name = line.strip().split(':', 1)[1].strip()
                        logging.info(f"Found Theme: {theme_name}")
                    elif line.startswith('Language:'):
                        language_code = line.strip().split(':', 1)[1].strip()
                        logging.info(f"Found Language: {language_code}")
                    elif line.startswith('ShadowColor:'):
                        # Parse the RGBA values
                        rgba_str = line.strip().split(':', 1)[1].strip()
                        logging.info(f"Found ShadowColor string: {rgba_str}")
                        try:
                            r, g, b, a = map(int, rgba_str.split(','))
                            # Create a fresh QColor instance
                            shadow_color = QColor(r, g, b, a)
                            shadow_color_loaded = True
                            logging.info(f"Successfully parsed shadow color: {r},{g},{b},{a}")
                        except Exception as e:
                            logging.error(f"Error parsing shadow color values: {e}. Using default shadow color.")
                    elif line.startswith('DrawOnlyAffectedStrand:'):
                        value = line.strip().split(':', 1)[1].strip().lower()
                        draw_only_affected_strand = (value == 'true')
                        logging.info(f"Found DrawOnlyAffectedStrand: {draw_only_affected_strand}")
                    elif line.startswith('EnableThirdControlPoint:'):
                        value = line.strip().split(':', 1)[1].strip().lower()
                        enable_third_control_point = (value == 'true')
                        logging.info(f"Found EnableThirdControlPoint: {enable_third_control_point}")
                    elif line.startswith('UseExtendedMask:'):
                        value = line.strip().split(':', 1)[1].strip().lower()
                        use_extended_mask = (value == 'true')
                        logging.info(f"Found UseExtendedMask: {use_extended_mask}")
                    elif line.startswith('ArrowHeadLength:'):
                        try:
                            arrow_head_length = float(line.split(':', 1)[1].strip())
                            logging.info(f"Found ArrowHeadLength: {arrow_head_length}")
                        except ValueError:
                            logging.error(f"Error parsing ArrowHeadLength value. Using default {arrow_head_length}.")
                    elif line.startswith('ArrowHeadWidth:'):
                        try:
                            arrow_head_width = float(line.split(':', 1)[1].strip())
                            logging.info(f"Found ArrowHeadWidth: {arrow_head_width}")
                        except ValueError:
                            logging.error(f"Error parsing ArrowHeadWidth value. Using default {arrow_head_width}.")
                    elif line.startswith('ArrowGapLength:'):
                        try:
                            arrow_gap_length = float(line.split(':', 1)[1].strip())
                            logging.info(f"Found ArrowGapLength: {arrow_gap_length}")
                        except ValueError:
                            logging.error(f"Error parsing ArrowGapLength value. Using default {arrow_gap_length}.")
                    elif line.startswith('ArrowLineLength:'):
                        try:
                            arrow_line_length = float(line.split(':', 1)[1].strip())
                            logging.info(f"Found ArrowLineLength: {arrow_line_length}")
                        except ValueError:
                            logging.error(f"Error parsing ArrowLineLength value. Using default {arrow_line_length}.")
                    elif line.startswith('ArrowLineWidth:'):
                        try:
                            arrow_line_width = float(line.split(':', 1)[1].strip())
                            logging.info(f"Found ArrowLineWidth: {arrow_line_width}")
                        except ValueError:
                            logging.error(f"Error parsing ArrowLineWidth value. Using default {arrow_line_width}.")
                    elif line.startswith('UseDefaultArrowColor:'):
                        value = line.split(':', 1)[1].strip().lower()
                        use_default_arrow_color = (value == 'true')
                        logging.info(f"Found UseDefaultArrowColor: {use_default_arrow_color}")
                    elif line.startswith('DefaultArrowColor:'):
                        try:
                            r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                            default_arrow_fill_color = QColor(r, g, b, a)
                            logging.info(f"Found DefaultArrowColor: {r},{g},{b},{a}")
                        except Exception as e:
                            logging.error(f"Error parsing DefaultArrowColor values: {e}. Using default {default_arrow_fill_color}.")
            
            if shadow_color_loaded:
                logging.info(f"User settings loaded successfully. Theme: {theme_name}, Language: {language_code}, Shadow Color: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}, Draw Only Affected Strand: {draw_only_affected_strand}, Enable Third Control Point: {enable_third_control_point}, Use Extended Mask: {use_extended_mask}, ArrowHeadLength: {arrow_head_length}, ArrowHeadWidth: {arrow_head_width}, ArrowGapLength: {arrow_gap_length}, ArrowLineLength: {arrow_line_length}, ArrowLineWidth: {arrow_line_width}")
            else:
                logging.warning(f"Shadow color not found in settings file. Using default: 0,0,0,150")
        except Exception as e:
            logging.error(f"Error reading user settings: {e}. Using default values.")
    else:
        logging.info(f"Settings file not found at {file_path}. Using default settings.")

    return theme_name, language_code, shadow_color, draw_only_affected_strand, enable_third_control_point, use_extended_mask, arrow_head_length, arrow_head_width, arrow_gap_length, arrow_line_length, arrow_line_width, use_default_arrow_color, default_arrow_fill_color

if __name__ == '__main__':
    logging.info("Starting the application...")

    app = QApplication(sys.argv)

    # Load user settings
    theme, language_code, shadow_color, draw_only_affected_strand, enable_third_control_point, use_extended_mask, arrow_head_length, arrow_head_width, arrow_gap_length, arrow_line_length, arrow_line_width, use_default_arrow_color, default_arrow_fill_color = load_user_settings()
    logging.info(f"Loaded settings - Theme: {theme}, Language: {language_code}, Shadow Color RGBA: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}, Draw Only Affected Strand: {draw_only_affected_strand}, Enable Third Control Point: {enable_third_control_point}, Use Extended Mask: {use_extended_mask}, ArrowHeadLength: {arrow_head_length}, ArrowHeadWidth: {arrow_head_width}, ArrowGapLength: {arrow_gap_length}, ArrowLineLength: {arrow_line_length}, ArrowLineWidth: {arrow_line_width}")

    # Initialize the main window with settings
    window = MainWindow()
    
    # Set the shadow color immediately on the canvas
    if hasattr(window, 'canvas') and window.canvas:
        # Check if the canvas already has this shadow color (might have been set during initialization)
        should_set_shadow = True
        if hasattr(window.canvas, 'default_shadow_color') and window.canvas.default_shadow_color:
            current_color = window.canvas.default_shadow_color
            if (current_color.red() == shadow_color.red() and 
                current_color.green() == shadow_color.green() and 
                current_color.blue() == shadow_color.blue() and 
                current_color.alpha() == shadow_color.alpha()):
                logging.info(f"Canvas already has the correct shadow color: {current_color.red()},{current_color.green()},{current_color.blue()},{current_color.alpha()}")
                should_set_shadow = False
        
        if should_set_shadow:
            # Force it to be a new QColor instance to ensure it's correctly applied
            rgb_color = QColor(shadow_color.red(), shadow_color.green(), shadow_color.blue(), shadow_color.alpha())
            window.canvas.set_shadow_color(rgb_color)
            logging.info(f"Applied shadow color to canvas directly after initialization: {rgb_color.red()},{rgb_color.green()},{rgb_color.blue()},{rgb_color.alpha()}")
        
        # Set draw only affected strand setting
        if hasattr(window.canvas, 'move_mode'):
            window.canvas.move_mode.draw_only_affected_strand = draw_only_affected_strand
            logging.info(f"Set draw_only_affected_strand to {draw_only_affected_strand}")
            
            # Connect the move_mode's mouseReleaseEvent to the undo/redo manager if layer_panel exists
            if hasattr(window, 'layer_panel') and window.layer_panel and hasattr(window.layer_panel, 'undo_redo_manager'):
                connect_to_move_mode(window.canvas, window.layer_panel.undo_redo_manager)
                logging.info("Connected move_mode to undo/redo manager")
                
                # Also connect the attach_mode if it exists
                if hasattr(window.canvas, 'attach_mode') and window.canvas.attach_mode:
                    connect_to_attach_mode(window.canvas, window.layer_panel.undo_redo_manager)
                    logging.info("Connected attach_mode to undo/redo manager")
                
                # Also connect the mask_mode if it exists
                if hasattr(window.canvas, 'mask_mode') and window.canvas.mask_mode:
                    connect_to_mask_mode(window.canvas, window.layer_panel.undo_redo_manager)
                    logging.info("Connected mask_mode to undo/redo manager")
        
        # Set enable third control point setting
        window.canvas.enable_third_control_point = enable_third_control_point
        logging.info(f"Set enable_third_control_point to {enable_third_control_point}")

        # Set extended mask setting
        window.canvas.use_extended_mask = use_extended_mask
        logging.info(f"Set use_extended_mask to {use_extended_mask}")
        # Apply arrow settings to canvas
        window.canvas.arrow_head_length = arrow_head_length
        window.canvas.arrow_head_width = arrow_head_width
        window.canvas.arrow_gap_length = arrow_gap_length
        window.canvas.arrow_line_length = arrow_line_length
        window.canvas.arrow_line_width = arrow_line_width
        # Apply default arrow color settings to canvas
        window.canvas.use_default_arrow_color = use_default_arrow_color
        window.canvas.default_arrow_fill_color = default_arrow_fill_color
        logging.info(f"Set use_default_arrow_color to {use_default_arrow_color} and default_arrow_fill_color RGBA: {default_arrow_fill_color.red()},{default_arrow_fill_color.green()},{default_arrow_fill_color.blue()},{default_arrow_fill_color.alpha()}")
    else:
        logging.error("Canvas not available on window object")
    
    window.set_language(language_code)
    
    # Show and maximize window before applying theme to ensure all widgets exist
    window.show()
    window.setWindowState(Qt.WindowMaximized | window.windowState())
    window.raise_()
    window.activateWindow()
    
    # Apply theme after window is shown to ensure all widgets are created
    window.apply_theme(theme)
    
    # Set the initial splitter sizes to make the layer panel narrower
    window.set_initial_splitter_sizes()
    
    # Verify shadow color after everything is initialized
    if hasattr(window, 'canvas') and window.canvas:
        current_shadow = window.canvas.default_shadow_color
        logging.info(f"FINAL CHECK - Canvas shadow color is: {current_shadow.red()},{current_shadow.green()},{current_shadow.blue()},{current_shadow.alpha()}")

    sys.exit(app.exec_())