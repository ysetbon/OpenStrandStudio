import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

# Configure logging before importing other modules
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_user_settings():
    settings = {}
    file_path = 'user_settings.txt'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        settings[key.strip()] = value.strip()
        except Exception as e:
            logging.error(f"Error reading user settings: {e}")
    else:
        logging.info("user_settings.txt not found. Using default settings.")
    return settings

if __name__ == '__main__':
    logging.info("Starting the application...")

    app = QApplication(sys.argv)

    # Load user settings
    user_settings = load_user_settings()
    language_code = user_settings.get('Language', 'en')
    theme = user_settings.get('Theme', 'default')

    # Initialize the main window with settings
    window = MainWindow()
    window.set_language(language_code)
    window.apply_theme(theme)
    window.show()

    sys.exit(app.exec_())