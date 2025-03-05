import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from main_window import MainWindow

# Configure logging before importing other modules
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            
            if shadow_color_loaded:
                logging.info(f"User settings loaded successfully. Theme: {theme_name}, Language: {language_code}, Shadow Color: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}")
            else:
                logging.warning(f"Shadow color not found in settings file. Using default: 0,0,0,150")
        except Exception as e:
            logging.error(f"Error reading user settings: {e}. Using default values.")
    else:
        logging.info(f"Settings file not found at {file_path}. Using default settings.")

    return theme_name, language_code, shadow_color

if __name__ == '__main__':
    logging.info("Starting the application...")

    app = QApplication(sys.argv)

    # Load user settings
    theme, language_code, shadow_color = load_user_settings()
    logging.info(f"Loaded settings - Theme: {theme}, Language: {language_code}, Shadow Color RGBA: {shadow_color.red()},{shadow_color.green()},{shadow_color.blue()},{shadow_color.alpha()}")

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