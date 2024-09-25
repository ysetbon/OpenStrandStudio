import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

# Configure logging before importing other modules
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_user_settings():
    from PyQt5.QtCore import QStandardPaths

    app_name = "OpenStrand Studio"
    program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    logging.info(f"Program data directory: {program_data_dir}")
    settings_dir = os.path.join(program_data_dir, app_name)
    logging.info(f"Settings directory: {settings_dir}")
    file_path = os.path.join(settings_dir, 'user_settings.txt')
    logging.info(f"Settings file path: {file_path}")

    theme_name = 'default'
    language_code = 'en'

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    if line.startswith('Theme:'):
                        theme_name = line.strip().split(':', 1)[1].strip()
                    elif line.startswith('Language:'):
                        language_code = line.strip().split(':', 1)[1].strip()
            logging.info("User settings loaded successfully.")
        except Exception as e:
            logging.error(f"Error reading user settings: {e}")
    else:
        logging.info("user_settings.txt not found in AppData. Using default settings.")

    return theme_name, language_code

if __name__ == '__main__':
    logging.info("Starting the application...")

    app = QApplication(sys.argv)

    # Load user settings
    theme, language_code = load_user_settings()

    # Initialize the main window with settings
    window = MainWindow()
    window.set_language(language_code)
    window.apply_theme(theme)
    window.show()

    sys.exit(app.exec_())