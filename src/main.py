# Import the sys module to access system-specific parameters and functions
import sys

# Import logging module for logging configuration
import logging

# Import QApplication from PyQt5.QtWidgets, which manages the GUI application's control flow and main settings
from PyQt5.QtWidgets import QApplication

# Import the MainWindow class from the main_window module (assumes main_window.py is in the same directory)
from main_window import MainWindow

# This conditional checks if the script is being run directly (as opposed to being imported)
if __name__ == '__main__':
    # Set up logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create a new QApplication instance
    # sys.argv is passed to allow command line arguments to control the application
    app = QApplication(sys.argv)
    
    # Create an instance of the MainWindow class
    # This will set up the main GUI window of the application
    window = MainWindow()
    
    # Make the main window visible
    window.show()
    
    # Start the application's event loop and provide an exit code when it's done
    # sys.exit() ensures a clean exit and returns the exit code to the OS.
    sys.exit(app.exec_())