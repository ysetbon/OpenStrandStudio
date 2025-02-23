import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
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

    theme_name = 'default'
    language_code = 'en'

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.startswith('Theme:'):
                        theme_name = line.strip().split(':', 1)[1].strip()
                    elif line.startswith('Language:'):
                        language_code = line.strip().split(':', 1)[1].strip()
            logging.info(f"User settings loaded successfully. Theme: {theme_name}, Language: {language_code}")
        except Exception as e:
            logging.error(f"Error reading user settings: {e}")
    else:
        logging.info(f"Settings file not found at {file_path}. Using default settings.")

    return theme_name, language_code

if __name__ == '__main__':
    logging.info("Starting the application...")

    app = QApplication(sys.argv)

    # Load user settings
    theme, language_code = load_user_settings()

    # Initialize the main window with settings
    window = MainWindow()
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

    sys.exit(app.exec_())