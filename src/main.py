import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from main_window import MainWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = QApplication(sys.argv)
    
    # Set the icon for the entire application
    app_icon = resource_path("box_stitch.ico")
    app.setWindowIcon(QIcon(app_icon))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())