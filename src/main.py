import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QEvent, QObject
from PyQt5.QtGui import QColor, QCursor, QGuiApplication
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

# --- Add this section for Canvas Bounds logging ---
class CanvasBoundsFilter(logging.Filter):
    """Filters log records for canvas bounds messages."""
    def filter(self, record):
        # Check if the message starts with "Canvas:"
        return record.getMessage().startswith("Canvas:")

try:
    canvas_bounds_log_file = 'canvas_bounds.log'

    # Attempt to delete the log file if it exists
    try:
        if os.path.exists(canvas_bounds_log_file):
            os.remove(canvas_bounds_log_file)
            logging.info(f"Removed existing log file: {canvas_bounds_log_file}")
    except OSError as e:
        logging.error(f"Error removing log file {canvas_bounds_log_file}: {e}")

    # Create a specific handler for canvas bounds logs, overwriting each run
    canvas_bounds_handler = logging.FileHandler(canvas_bounds_log_file, mode='w')
    canvas_bounds_handler.addFilter(CanvasBoundsFilter())
    logging.getLogger().addHandler(canvas_bounds_handler)
    logging.info("Canvas Bounds logging configured to output to canvas_bounds.log")

except Exception as e:
    print(f"Error setting up Canvas Bounds file logging: {e}") # Basic error handling
# --- End of Canvas Bounds logging section ---

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
    
    # Initialize default strand and stroke colors
    default_strand_color = QColor(200, 170, 230, 255)  # Default purple
    default_stroke_color = QColor(0, 0, 0, 255)  # Default black
    
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
                    elif line.startswith('DefaultStrandColor:'):
                        try:
                            r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                            default_strand_color = QColor(r, g, b, a)
                            logging.info(f"Found DefaultStrandColor: {r},{g},{b},{a}")
                        except Exception as e:
                            logging.error(f"Error parsing DefaultStrandColor values: {e}. Using default {default_strand_color}.")
                    elif line.startswith('DefaultStrokeColor:'):
                        try:
                            r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                            default_stroke_color = QColor(r, g, b, a)
                            logging.info(f"Found DefaultStrokeColor: {r},{g},{b},{a}")
                        except Exception as e:
                            logging.error(f"Error parsing DefaultStrokeColor values: {e}. Using default {default_stroke_color}.")
            
            if shadow_color_loaded:
                logging.info(f"User settings loaded successfully. Theme: {theme_name}, Language: {language_code}, Shadow Color: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}, Draw Only Affected Strand: {draw_only_affected_strand}, Enable Third Control Point: {enable_third_control_point}, Use Extended Mask: {use_extended_mask}, ArrowHeadLength: {arrow_head_length}, ArrowHeadWidth: {arrow_head_width}, ArrowGapLength: {arrow_gap_length}, ArrowLineLength: {arrow_line_length}, ArrowLineWidth: {arrow_line_width}")
            else:
                logging.warning(f"Shadow color not found in settings file. Using default: 0,0,0,150")
        except Exception as e:
            logging.error(f"Error reading user settings: {e}. Using default values.")
    else:
        logging.info(f"Settings file not found at {file_path}. Using default settings.")

    return theme_name, language_code, shadow_color, draw_only_affected_strand, enable_third_control_point, use_extended_mask, arrow_head_length, arrow_head_width, arrow_gap_length, arrow_line_length, arrow_line_width, use_default_arrow_color, default_arrow_fill_color, default_strand_color, default_stroke_color

if __name__ == '__main__':
    logging.info("Starting the application...")

    app = QApplication(sys.argv)

    # Load user settings
    theme, language_code, shadow_color, draw_only_affected_strand, enable_third_control_point, use_extended_mask, arrow_head_length, arrow_head_width, arrow_gap_length, arrow_line_length, arrow_line_width, use_default_arrow_color, default_arrow_fill_color, default_strand_color, default_stroke_color = load_user_settings()
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
        # Apply default strand and stroke colors to canvas
        window.canvas.default_strand_color = default_strand_color
        window.canvas.default_stroke_color = default_stroke_color
        logging.info(f"Set use_default_arrow_color to {use_default_arrow_color} and default_arrow_fill_color RGBA: {default_arrow_fill_color.red()},{default_arrow_fill_color.green()},{default_arrow_fill_color.blue()},{default_arrow_fill_color.alpha()}")
        logging.info(f"Set default_strand_color RGBA: {default_strand_color.red()},{default_strand_color.green()},{default_strand_color.blue()},{default_strand_color.alpha()}")
        logging.info(f"Set default_stroke_color RGBA: {default_stroke_color.red()},{default_stroke_color.green()},{default_stroke_color.blue()},{default_stroke_color.alpha()}")
        
        # Update LayerPanel's default colors to match the canvas
        if hasattr(window, 'layer_panel') and window.layer_panel:
            window.layer_panel.update_default_colors()
            logging.info("Updated LayerPanel default colors to match canvas settings")
    else:
        logging.error("Canvas not available on window object")
    
    window.set_language(language_code)
    
    # Apply theme before window is shown
    window.apply_theme(theme)
    
    # ================== ENHANCED MULTI-MONITOR WINDOW POSITIONING ==================
    
    logging.info("="*80)
    logging.info("STARTING MULTI-MONITOR WINDOW POSITIONING")
    logging.info("="*80)
    
    # STEP 1: Ensure window is completely hidden during setup
    window.setVisible(False)
    window.hide()
    window.setAttribute(Qt.WA_DontShowOnScreen, True)  # Extra insurance
    logging.info("✓ STEP 1: Window completely hidden during setup")
    
    # STEP 2: Find screen where cursor is currently located
    cursor_pos = QCursor.pos()
    logging.info(f"✓ STEP 2: Cursor position: ({cursor_pos.x()}, {cursor_pos.y()})")
    
    # Debug: Log all available screens first
    try:
        screens = QGuiApplication.screens()
        logging.info(f"\nDETECTED SCREENS: {len(screens)} total")
        for i, screen in enumerate(screens):
            screen_rect = screen.geometry()
            available_rect = screen.availableGeometry()
            logging.info(f"\n  Screen {i}: {screen.name()}")
            logging.info(f"    - Full geometry: x={screen_rect.x()}, y={screen_rect.y()}, w={screen_rect.width()}, h={screen_rect.height()}")
            logging.info(f"    - Available area: x={available_rect.x()}, y={available_rect.y()}, w={available_rect.width()}, h={available_rect.height()}")
            logging.info(f"    - Device pixel ratio: {screen.devicePixelRatio()}")
            logging.info(f"    - Logical DPI: {screen.logicalDotsPerInch()}")
            logging.info(f"    - Physical DPI: {screen.physicalDotsPerInch()}")
            
            # Check if cursor is on this screen
            if screen_rect.contains(cursor_pos):
                logging.info(f"    *** CURSOR IS ON THIS SCREEN ***")
    except Exception as e:
        logging.error(f"Error detecting screens: {e}")
    
    try:
        # Find which screen contains the cursor
        target_screen = None
        target_screen_index = -1
        for i, screen in enumerate(screens):
            screen_rect = screen.geometry()
            if screen_rect.contains(cursor_pos):
                target_screen = screen
                target_screen_index = i
                logging.info(f"\n✓ CURSOR FOUND ON SCREEN: {screen.name()} (Screen {i})")
                break
        
        # Fallback to primary screen if cursor position doesn't match any screen
        if not target_screen:
            target_screen = QGuiApplication.primaryScreen()
            target_screen_index = 0
            logging.warning(f"\n⚠ Cursor not found on any screen! Using primary screen as fallback: {target_screen.name()}")
        
        # Get the available geometry (excluding taskbar/dock)
        available_rect = target_screen.availableGeometry()
        full_rect = target_screen.geometry()
        
        logging.info(f"\n✓ TARGET SCREEN DETAILS:")
        logging.info(f"  - Full screen area: ({full_rect.x()}, {full_rect.y()}) size: {full_rect.width()} x {full_rect.height()}")
        logging.info(f"  - Available area: ({available_rect.x()}, {available_rect.y()}) size: {available_rect.width()} x {available_rect.height()}")
        
        # STEP 3: Create window handle and assign to correct screen BEFORE any geometry changes
        window.setAttribute(Qt.WA_NativeWindow, True)
        window_id = window.winId()  # Force native window creation
        logging.info(f"\n✓ STEP 3: Native window created with ID: {window_id}")
        
        # Ensure we have a window handle before proceeding
        if not window.windowHandle():
            logging.error("✗ Failed to create window handle!")
            raise Exception("Window handle creation failed")
        
        # Assign window to the target screen
        window.windowHandle().setScreen(target_screen)
        logging.info(f"✓ Window assigned to screen: {target_screen.name()}")
        
        # STEP 4: Set minimum size constraints
        window.setMinimumSize(677, 820)
        logging.info("\n✓ STEP 4: Minimum size set: 677x820")
        
        # STEP 5: Set window flags for better multi-monitor support
        # Remove any flags that might interfere with proper screen placement
        window.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | 
                            Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        # STEP 6: DO NOT manually position - let Qt handle it when maximized
        logging.info("\n✓ STEP 5-6: Window flags set for proper multi-monitor support")
        
        # STEP 7: Process pending events
        app.processEvents()
        logging.info("\n✓ STEP 7: All pending events processed")
        
        # Remove the attribute that was keeping window off-screen
        window.setAttribute(Qt.WA_DontShowOnScreen, False)
        
        # STEP 8: Show window with explicit positioning
        def show_window_on_target_screen():
            logging.info("\n" + "="*60)
            logging.info("SHOWING WINDOW ON TARGET SCREEN")
            logging.info("="*60)
            
            try:
                # Ensure window is assigned to correct screen
                if window.windowHandle():
                    window.windowHandle().setScreen(target_screen)
                
                # First, show window in normal state at a specific position on target screen
                # This helps ensure it appears on the correct screen
                center_x = available_rect.x() + available_rect.width() // 2
                center_y = available_rect.y() + available_rect.height() // 2
                window.move(center_x - 400, center_y - 300)
                window.resize(800, 600)
                
                # Show the window
                window.show()
                
                # Process events to ensure window is created on correct screen
                app.processEvents()
                
                # Now move to full screen position and maximize
                def maximize_on_correct_screen():
                    # Verify we're on the right screen
                    current_screen = window.windowHandle().screen() if window.windowHandle() else None
                    if current_screen != target_screen:
                        logging.warning(f"Window on {current_screen.name() if current_screen else 'Unknown'}, forcing to {target_screen.name()}")
                        window.windowHandle().setScreen(target_screen)
                    
                    # Method 1: Try standard maximization
                    window.showMaximized()
                    app.processEvents()
                    
                    # Check if maximization worked correctly
                    QTimer.singleShot(50, lambda: verify_and_fix_maximization())
                
                def verify_and_fix_maximization():
                    current_screen = window.windowHandle().screen() if window.windowHandle() else None
                    frame_geom = window.frameGeometry()
                    
                    # Check if window is on correct screen with correct size
                    correct_screen = current_screen == target_screen
                    correct_size = (
                        abs(frame_geom.width() - available_rect.width()) < 50 and
                        abs(frame_geom.height() - available_rect.height()) < 50
                    )
                    
                    if not correct_screen or not correct_size:
                        logging.warning("Maximization failed, using manual positioning")
                        
                        # Method 2: Manual fullscreen positioning
                        window.setWindowState(Qt.WindowNoState)  # Clear maximized state
                        window.setGeometry(available_rect)  # Set to exact screen dimensions
                        
                        # Try maximizing again after positioning
                        QTimer.singleShot(50, lambda: window.showMaximized())
                    
                    # Log final state
                    actual_screen = window.windowHandle().screen() if window.windowHandle() else None
                    actual_geom = window.geometry()
                    frame_geom = window.frameGeometry()
                    
                    logging.info(f"\n✓ WINDOW POSITIONING COMPLETE!")
                    logging.info(f"  - Target screen: {target_screen.name()}")
                    logging.info(f"  - Actual screen: {actual_screen.name() if actual_screen else 'Unknown'}")
                    logging.info(f"  - Window geometry: {actual_geom}")
                    logging.info(f"  - Frame geometry: {frame_geom}")
                    logging.info(f"  - Is maximized: {window.isMaximized()}")
                    
                    if actual_screen and actual_screen != target_screen:
                        logging.error(f"\n✗ WINDOW ON WRONG SCREEN!")
                        logging.error(f"  Expected: {target_screen.name()}")
                        logging.error(f"  Got: {actual_screen.name()}")
                
                # Ensure window is on top and focused
                window.raise_()
                window.activateWindow()
                window.setFocus(Qt.OtherFocusReason)
                
                # Start maximization process
                QTimer.singleShot(100, maximize_on_correct_screen)
                
            except Exception as e:
                logging.error(f"✗ Error showing window: {e}")
                logging.error(traceback.format_exc())
                # Emergency fallback
                window.show()
                window.showMaximized()
        
        # Show window
        show_window_on_target_screen()
        
        # Additional aggressive correction if needed
        def force_correct_screen_placement():
            """Force window to correct screen with proper dimensions"""
            try:
                if window.isVisible() and window.windowHandle():
                    current_screen = window.windowHandle().screen()
                    frame_geom = window.frameGeometry()
                    
                    # Check if we need correction
                    wrong_screen = current_screen != target_screen
                    wrong_size = (
                        abs(frame_geom.width() - available_rect.width()) > 100 or
                        abs(frame_geom.height() - available_rect.height()) > 100
                    )
                    
                    if wrong_screen or wrong_size:
                        logging.warning(f"AGGRESSIVE CORRECTION NEEDED:")
                        logging.warning(f"  - Wrong screen: {wrong_screen}")
                        logging.warning(f"  - Wrong size: {wrong_size}")
                        logging.warning(f"  - Current: {current_screen.name() if current_screen else 'Unknown'} @ {frame_geom}")
                        logging.warning(f"  - Target: {target_screen.name()} @ {available_rect}")
                        
                        # Clear all window states
                        window.setWindowState(Qt.WindowNoState)
                        window.hide()
                        
                        # Force to target screen
                        window.windowHandle().setScreen(target_screen)
                        
                        # Set exact geometry
                        window.setGeometry(available_rect)
                        
                        # Show and maximize
                        window.show()
                        window.showMaximized()
                        
                        # Force raise and activate
                        window.raise_()
                        window.activateWindow()
                        
                        logging.info("AGGRESSIVE CORRECTION APPLIED")
                    
                    # Log final state
                    final_screen = window.windowHandle().screen()
                    final_geom = window.frameGeometry()
                    logging.info(f"\nAfter aggressive correction:")
                    logging.info(f"  - Screen: {final_screen.name() if final_screen else 'Unknown'}")
                    logging.info(f"  - Frame geometry: {final_geom}")
                    logging.info(f"  - Maximized: {window.isMaximized()}")
                    
            except Exception as e:
                logging.error(f"Error in force_correct_screen_placement: {e}")
        
        # Apply aggressive correction after a delay
        QTimer.singleShot(300, force_correct_screen_placement)
        
        # Final verification
        def verify_window_placement():
            logging.info("\n" + "="*60)
            logging.info("FINAL VERIFICATION (500ms later)")
            logging.info("="*60)
            
            try:
                if window.isVisible() and window.windowHandle():
                    current_screen = window.windowHandle().screen()
                    current_geom = window.geometry()
                    frame_geom = window.frameGeometry()
                    cursor_now = QCursor.pos()
                    
                    logging.info(f"FINAL WINDOW STATE:")
                    logging.info(f"  - Window visible: {window.isVisible()}")
                    logging.info(f"  - Current screen: {current_screen.name() if current_screen else 'Unknown'}")
                    logging.info(f"  - Window geometry: {current_geom}")
                    logging.info(f"  - Frame geometry: {frame_geom}")
                    logging.info(f"  - Is maximized: {window.isMaximized()}")
                    logging.info(f"  - Cursor now at: ({cursor_now.x()}, {cursor_now.y()})")
                    
                    # Check screen
                    screen_correct = current_screen == target_screen
                    if not screen_correct:
                        logging.error(f"\n✗ WINDOW ENDED UP ON WRONG SCREEN!")
                        logging.error(f"  Expected: {target_screen.name()}")
                        logging.error(f"  Got: {current_screen.name()}")
                    
                    # Check if properly maximized
                    expected_area = target_screen.availableGeometry()
                    
                    # For maximized windows, check if frame is near the expected area
                    position_correct = (
                        abs(frame_geom.x() - expected_area.x()) <= 10 and
                        abs(frame_geom.y() - expected_area.y()) <= 50  # Allow more tolerance for title bar
                    )
                    
                    size_correct = (
                        abs(frame_geom.width() - expected_area.width()) <= 50 and
                        abs(frame_geom.height() - expected_area.height()) <= 50
                    )
                    
                    if not position_correct or not size_correct:
                        logging.warning(f"\n⚠ Window not properly positioned/sized!")
                        logging.warning(f"  Expected area: {expected_area}")
                        logging.warning(f"  Actual frame: {frame_geom}")
                        logging.warning(f"  Position correct: {position_correct}")
                        logging.warning(f"  Size correct: {size_correct}")
                        
                        # One final correction attempt
                        if not screen_correct or not size_correct:
                            logging.info("\nAttempting final correction...")
                            window.hide()
                            window.setWindowState(Qt.WindowNoState)
                            window.windowHandle().setScreen(target_screen)
                            window.setGeometry(available_rect)
                            window.show()
                            window.showMaximized()
                            
                            # Check again after correction
                            QTimer.singleShot(200, lambda: log_final_state())
                    else:
                        logging.info("\n✓ Window properly positioned and sized")
                    
                    if screen_correct and window.isMaximized() and position_correct and size_correct:
                        logging.info("\n✓ WINDOW PLACEMENT VERIFIED SUCCESSFULLY!")
                        logging.info("✓ Window controls (minimize/maximize/close) should be accessible")
                    else:
                        logging.error("\n✗ WINDOW PLACEMENT VERIFICATION FAILED!")
                
                def log_final_state():
                    final_screen = window.windowHandle().screen() if window.windowHandle() else None
                    final_frame = window.frameGeometry()
                    logging.info(f"\nFINAL STATE AFTER CORRECTION:")
                    logging.info(f"  - Screen: {final_screen.name() if final_screen else 'Unknown'}")
                    logging.info(f"  - Frame: {final_frame}")
                    logging.info(f"  - Target was: {target_screen.name()} @ {available_rect}")
                        
            except Exception as e:
                logging.error(f"✗ Error during placement verification: {e}")
                logging.error(traceback.format_exc())
        
        # Verify after window settles
        QTimer.singleShot(500, verify_window_placement)
        
    except Exception as e:
        logging.error(f"\n✗ CRITICAL ERROR IN WINDOW POSITIONING: {e}")
        logging.error(traceback.format_exc())
        
        # Emergency fallback
        try:
            logging.info("\nATTEMPTING EMERGENCY FALLBACK...")
            window.setAttribute(Qt.WA_DontShowOnScreen, False)
            window.setMinimumSize(677, 820)
            window.showMaximized()
            window.raise_()
            window.activateWindow()
            logging.info("✓ Emergency fallback: Window shown maximized")
        except Exception as e2:
            logging.error(f"✗ Even emergency fallback failed: {e2}")
    
    logging.info("\n" + "="*80)
    logging.info("WINDOW POSITIONING SEQUENCE COMPLETE")
    logging.info("="*80 + "\n")
    
    # Add event filter to handle minimize/restore properly
    class ScreenKeeper(QObject):
        """Ensures window stays on correct screen when minimized/restored"""
        def __init__(self, window, target_screen):
            super().__init__()
            self.window = window
            self.target_screen = target_screen
            self.last_geometry = None
            self.was_maximized = False
            
        def eventFilter(self, obj, event):
            try:
                # Window state is about to change
                if event.type() == QEvent.WindowStateChange:
                    old_state = self.window.windowState()
                    
                    # Store state before minimizing
                    if old_state & Qt.WindowMinimized == 0:  # Not minimized yet
                        self.last_geometry = self.window.geometry()
                        self.was_maximized = bool(old_state & Qt.WindowMaximized)
                        if self.window.windowHandle():
                            current_screen = self.window.windowHandle().screen()
                            if current_screen:
                                # Always update to the current screen - respect user's choice
                                self.target_screen = current_screen
                        logging.info(f"Storing window state before minimize: maximized={self.was_maximized}, screen={self.target_screen.name()}")
                
                # Window is being shown/restored
                elif event.type() == QEvent.Show or event.type() == QEvent.WindowActivate:
                    # Check if we need to restore to correct screen
                    QTimer.singleShot(100, self.check_and_restore_screen)
                    
            except Exception as e:
                logging.error(f"Error in ScreenKeeper event filter: {e}")
            
            return False  # Don't consume the event
        
        def check_and_restore_screen(self):
            """Check if window is on correct screen after restore"""
            try:
                if not self.window.isMinimized() and self.window.isVisible():
                    current_screen = self.window.windowHandle().screen() if self.window.windowHandle() else None
                    
                    if current_screen and current_screen != self.target_screen:
                        logging.info(f"Window restored to wrong screen: {current_screen.name()}, moving to {self.target_screen.name()}")
                        
                        # Get the target screen's available area
                        available_rect = self.target_screen.availableGeometry()
                        
                        # Restore to correct screen
                        if self.was_maximized:
                            # For maximized windows
                            self.window.setWindowState(Qt.WindowNoState)
                            self.window.windowHandle().setScreen(self.target_screen)
                            self.window.setGeometry(available_rect)
                            self.window.showMaximized()
                        else:
                            # For normal windows, restore last position
                            self.window.windowHandle().setScreen(self.target_screen)
                            if self.last_geometry:
                                # Adjust position to be within target screen bounds
                                x = max(available_rect.x(), min(self.last_geometry.x(), available_rect.x() + available_rect.width() - self.last_geometry.width()))
                                y = max(available_rect.y(), min(self.last_geometry.y(), available_rect.y() + available_rect.height() - self.last_geometry.height()))
                                self.window.move(x, y)
                        
                        logging.info(f"Window restored to correct screen: {self.target_screen.name()}")
                    
            except Exception as e:
                logging.error(f"Error in check_and_restore_screen: {e}")
    
    # Install the event filter
    screen_keeper = ScreenKeeper(window, target_screen)
    window.installEventFilter(screen_keeper)
    logging.info("Screen keeper event filter installed to handle minimize/restore")
    
    # Set the initial splitter sizes to make the layer panel narrower
    window.set_initial_splitter_sizes()
    
    # Verify shadow color after everything is initialized
    if hasattr(window, 'canvas') and window.canvas:
        current_shadow = window.canvas.default_shadow_color
        logging.info(f"FINAL CHECK - Canvas shadow color is: {current_shadow.red()},{current_shadow.green()},{current_shadow.blue()},{current_shadow.alpha()}")

    sys.exit(app.exec_())