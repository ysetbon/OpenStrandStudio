import os
import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QSplitter, QFileDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QImage, QPainter, QColor
from PyQt5.QtWidgets import QApplication
from layer_state_manager import LayerStateManager
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
                             QSplitter, QFileDialog, QSpacerItem, QSizePolicy,
                             QDialog, QTextEdit)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from strand_drawing_canvas import StrandDrawingCanvas
from layer_panel import LayerPanel
from strand import Strand, AttachedStrand, MaskedStrand
from save_load_manager import save_strands, load_strands, apply_loaded_strands
from mask_mode import MaskMode
from group_layers import GroupLayerManager, StrandAngleEditDialog
from settings_dialog import SettingsDialog
from translations import translations
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
                             QSplitter, QFileDialog, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    # ... existing imports ...
    QLabel
)
# main_window.py

class MainWindow(QMainWindow):
    language_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.language_code = 'en'  # Default language
        self.current_theme = 'default'  # Default theme

        logging.info("Initializing MainWindow")

        # Initialize components
        self.layer_state_manager = LayerStateManager()
        logging.info("LayerStateManager initialized in MainWindow")

        self.canvas = StrandDrawingCanvas(parent=self)  # Pass self as parent
        self.canvas.parent_window = self  # Explicitly set the parent window reference
        self.layer_panel = LayerPanel(self.canvas, parent=self)  # Pass self as parent

        # Use the GroupLayerManager from layer_panel
        self.group_layer_manager = self.layer_panel.group_layer_manager

        # Set the group_layer_manager in the canvas
        self.canvas.group_layer_manager = self.group_layer_manager

        logging.info(f"Canvas set in MainWindow: {self.canvas}")

        # Create settings dialog
        self.settings_dialog = SettingsDialog(parent=self, canvas=self.canvas)

        # Proceed with the rest of your setup
        self.setup_ui()
        self.setup_connections()
        self.current_mode = None
        self.previous_mode = None
        self.set_attach_mode()
        self.selected_strand = None

        # Connect signals
        self.language_changed.connect(self.update_translations)
        self.theme_changed.connect(self.apply_theme_to_widgets)

        # Show window maximized with standard window decorations
        self.showMaximized()

        # Load user settings from file
        self.load_settings_from_file()
        # Log initial state
        self.layer_state_manager.save_initial_state()
        self.layer_state_manager.log_layer_state()

        # Set up connections for LayerStateManager
        self.layer_state_manager.canvas = self.canvas
        self.layer_state_manager.layer_panel = self.layer_panel
        self.canvas.layer_state_manager = self.layer_state_manager

        logging.info("LayerStateManager connected to canvas and layer_panel")

        # Connect signals
        self.canvas.strand_created.connect(self.layer_state_manager.on_strand_created_in_layer_manager)
        self.canvas.strand_deleted.connect(self.layer_state_manager.on_strand_deleted_in_layer_manager)
        self.canvas.masked_layer_created.connect(self.layer_state_manager.on_masked_layer_created_in_layer_manager)
        logging.info("Connected strand_created, strand_deleted, and masked_layer_created signals to LayerStateManager")

        logging.info(f"Canvas set in MainWindow: {self.canvas}")

        self.toggle_control_points_button.clicked.connect(self.on_toggle_control_points_button_clicked)

    def showEvent(self, event):
        """Override showEvent to ensure proper window state"""
        super().showEvent(event)
        # Get the screen size
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        
        # Set window to use almost all available space
        self.setGeometry(screen_size)
        
        # Then maximize
        self.setWindowState(Qt.WindowMaximized)

    # Add the update_translations method here
    def update_translations(self):
        _ = translations[self.language_code]
        self.setWindowTitle(_['main_window_title'])

        # Update button texts
        self.attach_button.setText(_['attach_mode'])
        self.move_button.setText(_['move_mode'])
        self.rotate_button.setText(_['rotate_mode'])
        self.toggle_grid_button.setText(_['toggle_grid'])
        self.angle_adjust_button.setText(_['angle_adjust_mode'])
        self.select_strand_button.setText(_['select_mode'])
        self.mask_button.setText(_['mask_mode'])
        self.save_button.setText(_['save'])
        self.load_button.setText(_['load'])
        self.save_image_button.setText(_['save_image'])

        # Update settings button tooltip or text
        self.settings_button.setToolTip(_['settings'])
        self.layer_state_manager = LayerStateManager()
        self.layer_state_manager.set_canvas(self.canvas)
        self.layer_state_manager.set_layer_panel(self.layer_panel)
        # Update other UI components
        if hasattr(self.layer_panel, 'update_translations'):
            self.layer_panel.update_translations()
        if hasattr(self.canvas, 'update_translations'):
            self.canvas.update_translations()
        if self.settings_dialog.isVisible():
            self.settings_dialog.update_translations()

    # Ensure other methods like apply_theme_to_widgets are also defined
    def apply_theme_to_widgets(self, theme_name):
        # Apply theme to child widgets
        self.canvas.set_theme(theme_name)
        self.layer_panel.set_theme(theme_name)
        # Apply theme to other widgets if necessary
    def load_settings_from_file(self):
        # Use the AppData directory
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
            except Exception as e:
                logging.error(f"Error reading user settings: {e}")
        else:
            logging.info("user_settings.txt not found in AppData. Using default settings.")

        # Apply the theme and language
        self.apply_theme(theme_name)
        self.set_language(language_code)

    def setup_ui(self):
        logging.info("Entered setup_ui")

        # Determine the base path to resources
        if getattr(sys, 'frozen', False):
            # If the application is frozen (running as an executable)
            base_path = sys._MEIPASS
        else:
            # If running from source
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Set the window icon if available
        icon_path = os.path.join(base_path, 'box_stitch.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            logging.info(f"Window icon set from: {icon_path}")
        else:
            logging.warning(f"Window icon not found at: {icon_path}")

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create the horizontal layout for buttons
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Mode")
        self.rotate_button = QPushButton("Rotate Mode")
        self.toggle_grid_button = QPushButton("Toggle Grid")
        self.angle_adjust_button = QPushButton("Angle Adjust Mode")
        self.save_button = QPushButton("Save")
        self.load_button = QPushButton("Load")
        self.save_image_button = QPushButton("Save as Image")
        self.select_strand_button = QPushButton("Select Strand")
        self.mask_button = QPushButton("Mask Mode")

        # Create the settings button
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setObjectName("settingsButton")  # Assign an object name for stylesheet targeting
        self.attach_button.setMinimumWidth(190)
        # Set the gear icon or fallback to Unicode character if the image is not found
        gear_icon_path = os.path.join(base_path, 'settings_icon.png')
        logging.info(f"Searching for gear icon at: {gear_icon_path}")

        if os.path.exists(gear_icon_path):
            logging.info("Settings icon found. Setting icon for settings_button.")
            self.settings_button.setIcon(QIcon(gear_icon_path))
            self.settings_button.setIconSize(QSize(24, 24))
        else:
            logging.warning("Settings icon not found. Using Unicode '⚙' character.")
            self.settings_button.setText('⚙')
            self.settings_button.setFont(QFont('Segoe UI Symbol', 16))  # Adjust font if necessary

        # Style the settings button to have a transparent background
        self.settings_button.setStyleSheet("""
            QPushButton#settingsButton {
                background-color: rgba(150, 150, 150, 255);
                border: none;
                border-radius: 18px;
            }
            QPushButton#settingsButton:hover {
                background-color: rgba(200, 200, 200, 50);
            }
        """)

        # Create the toggle control points button
        self.toggle_control_points_button = QPushButton("Toggle Control Points")
        self.toggle_control_points_button.setCheckable(True)
        self.toggle_control_points_button.setChecked(False)

        # Add buttons to the button layout
        button_layout.addWidget(self.mask_button)
        button_layout.addWidget(self.select_strand_button)
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.rotate_button)
        button_layout.addWidget(self.toggle_grid_button)
        button_layout.addWidget(self.angle_adjust_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_image_button)
        button_layout.addWidget(self.toggle_control_points_button)

        # Add a horizontal spacer to push the layer state button to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(spacer)

        # Create a layout for the layer state button
        layer_state_layout = QHBoxLayout()
        self.layer_state_button = QPushButton("Layer State")
        self.layer_state_button.setCheckable(True)
        self.layer_state_button.clicked.connect(self.show_layer_state_log)
        layer_state_layout.addWidget(self.layer_state_button)

        button_layout.addLayout(layer_state_layout)

        # Add the settings button
        button_layout.addWidget(self.settings_button)

        # Set up the splitter and layouts
        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.layer_panel)

        # Configure splitter and main layout
        self.splitter.setHandleWidth(0)
        main_layout.addWidget(self.splitter)

        # Set minimum widths
        left_widget.setMinimumWidth(380)
        self.layer_panel.setMinimumWidth(380)
        # After creating the buttons, set their size policy
        buttons = [
            self.attach_button,
            self.move_button,
            self.rotate_button,
            self.toggle_grid_button,
            self.angle_adjust_button,
            self.save_button,
            self.load_button,
            self.save_image_button,
            self.select_strand_button,
            self.mask_button,
            self.toggle_control_points_button
        ]
        
        for button in buttons:
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            button.setFixedHeight(32)  # Set all buttons to the same height
        # Apply button styles
        self.setup_button_styles()
        logging.info("UI setup completed")

    def setup_connections(self):
        # Layer panel handle connections
        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        # Set layer panel for canvas
        self.canvas.set_layer_panel(self.layer_panel)

        # Layer panel connections
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(lambda idx: self.select_strand(idx, emit_signal=False))
        self.layer_panel.deselect_all_requested.connect(self.canvas.deselect_all_strands)
        self.layer_panel.color_changed.connect(self.handle_color_change)
        self.layer_panel.masked_layer_created.connect(self.create_masked_layer)
        self.layer_panel.masked_mode_entered.connect(self.canvas.deselect_all_strands)
        self.layer_panel.masked_mode_exited.connect(self.restore_selection)
        self.layer_panel.lock_layers_changed.connect(self.update_locked_layers)
        self.layer_panel.strand_deleted.connect(self.delete_strand)

        # Button connections
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.angle_adjust_button.clicked.connect(self.handle_angle_adjust_click)
        self.save_button.clicked.connect(self.save_project)
        self.load_button.clicked.connect(self.load_project)
        self.save_image_button.clicked.connect(self.save_canvas_as_image)
        self.select_strand_button.clicked.connect(self.set_select_mode)
        self.mask_button.clicked.connect(self.set_mask_mode)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # Connect the toggle control points button
        self.toggle_control_points_button.clicked.connect(self.set_control_points_mode)

        # Canvas connections
        self.canvas.strand_selected.connect(self.handle_canvas_strand_selection)

        # Disconnect any existing connections for mask_created
        try:
            self.canvas.mask_created.disconnect(self.handle_mask_created)
        except TypeError:
            # This exception will be raised if there was no connection, which is fine
            pass

        # Reconnect mask_created signal
        self.canvas.mask_created.connect(self.handle_mask_created)

        # Connect the canvas to the group layer manager
        self.layer_panel.group_layer_manager.canvas = self.canvas

        # Connect group operation signal
        self.layer_panel.group_layer_manager.group_panel.group_operation.connect(
            self.layer_panel.group_layer_manager.on_group_operation
        )

        # Add this new connection
        self.canvas.angle_adjust_completed.connect(self.deselect_angle_adjust_button)

        # Connect attachable_changed signal for each layer button
        for button in self.layer_panel.layer_buttons:
            button.attachable_changed.connect(self.update_strand_attachable)


    def open_settings_dialog(self):
        """Open the settings dialog if it's not already open."""
        # Check if dialog is already open
        if self.settings_dialog.isVisible():
            # Bring existing dialog to front
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        else:
            # Connect theme change signal and show dialog
            self.settings_dialog.theme_changed.connect(self.apply_theme)
            self.settings_dialog.show()



    def apply_theme(self, theme_name):
        if theme_name == "dark":
            style_sheet = """
            QWidget {
                background-color: #2C2C2C;
                color: white;
            }
            /* Styles for labels */
            QLabel {
                color: white;
            }
            /* Styles for push buttons */
            QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
            QPushButton:pressed {
                background-color: #5D5D5D;
            }
            /* Styles for spin boxes */
            QSpinBox, QDoubleSpinBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #5D5D5D;
            }
            /* Styles for sliders */
            QSlider {
                background-color: transparent;
            }
            QSlider::groove:horizontal {
                background: #3C3C3C;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #5D5D5D;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            /* Styles for combo boxes */
            QComboBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #5D5D5D;
            }
            QComboBox QAbstractItemView {
                background-color: #3C3C3C;
                color: white;
                selection-background-color: #4D4D4D;
            }
            /* Styles for check boxes */
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                border: 1px solid #5D5D5D;
                width: 16px;
                height: 16px;
                background: #3C3C3C;
            }
            QCheckBox::indicator:checked {
                image: url(:/icons/checkbox_checked_white.png);
            }
            /* Styles for the Angle Adjust Dialog */
            QDialog#AngleAdjustDialog {
                background-color: #2C2C2C;
                color: white;
            }
            QDialog#AngleAdjustDialog QLabel {
                color: white;
            }
            QDialog#AngleAdjustDialog QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #5D5D5D;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QDialog#AngleAdjustDialog QPushButton:hover {
                background-color: #4D4D4D;
            }
            QDialog#AngleAdjustDialog QPushButton:pressed {
                background-color: #5D5D5D;
            }
            QDialog#AngleAdjustDialog QSpinBox, QDialog#AngleAdjustDialog QDoubleSpinBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #5D5D5D;
            }
            QDialog#AngleAdjustDialog QSlider {
                background-color: transparent;
            }
            QDialog#AngleAdjustDialog QSlider::groove:horizontal {
                background: #3C3C3C;
                height: 6px;
                border-radius: 3px;
            }
            QDialog#AngleAdjustDialog QSlider::handle:horizontal {
                background: #5D5D5D;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            """
            # Style for create_group_button
            self.layer_panel.group_layer_manager.create_group_button.setStyleSheet("""
                QPushButton {
                    background-color: #4A4845;
                    color: white;
                    font-weight: bold;
                    border: none;
                    padding: 10px;
                    border-radius: 0;
                }
                QPushButton:hover {
                    background-color: #62605D;
                }
                QPushButton:pressed {
                    background-color: #2C2A27;
                }
            """)
        elif theme_name == "light":
            style_sheet = """
            QWidget {
                background-color: #FFFFFF;
                color: black;
            }
            QLabel {
                color: black;
            }
            QPushButton {
                background-color: #F0F0F0;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #CCCCCC;
            }
            QSlider {
                background-color: transparent;
            }
            QSlider::groove:horizontal {
                background: #E0E0E0;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #CCCCCC;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #CCCCCC;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: black;
                selection-background-color: #E0E0E0;
            }
            QCheckBox {
                color: black;
            }
            QCheckBox::indicator {
                border: 1px solid #CCCCCC;
                width: 16px;
                height: 16px;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                image: url(:/icons/checkbox_checked_black.png);
            }
            /* Styles for the Angle Adjust Dialog */
            QDialog#AngleAdjustDialog {
                background-color: #FFFFFF;
                color: black;
            }
            QDialog#AngleAdjustDialog QLabel {
                color: black;
            }
            QDialog#AngleAdjustDialog QPushButton {
                background-color: #F0F0F0;
                color: black;
                border: 1px solid #CCCCCC;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QDialog#AngleAdjustDialog QPushButton:hover {
                background-color: #E0E0E0;
            }
            QDialog#AngleAdjustDialog QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QDialog#AngleAdjustDialog QSpinBox, QDialog#AngleAdjustDialog QDoubleSpinBox {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #CCCCCC;
            }
            QDialog#AngleAdjustDialog QSlider {
                background-color: transparent;
            }
            QDialog#AngleAdjustDialog QSlider::groove:horizontal {
                background: #E0E0E0;
                height: 6px;
                border-radius: 3px;
            }
            QDialog#AngleAdjustDialog QSlider::handle:horizontal {
                background: #CCCCCC;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            """
            # Style for create_group_button
            self.layer_panel.group_layer_manager.create_group_button.setStyleSheet("""
                QPushButton {
                    background-color: #A6A19A;
                    color: black;
                    font-weight: bold;
                    border: none;
                    padding: 10px;
                    border-radius: 0;
                }
                QPushButton:hover {
                    background-color: #B6B1AA;
                }
                QPushButton:pressed {
                    background-color: #86817A;
                }
            """)
        elif theme_name == "default":
            style_sheet = """
            QWidget {
                background-color: #ECECEC;
                color: black;
            }
            QLabel {
                color: black;
            }
            QPushButton {
                background-color: #E8E8E8;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #DADADA;
            }
            QPushButton:pressed {
                background-color: #C8C8C8;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #CCCCCC;
            }
            QSlider {
                background-color: transparent;
            }
            QSlider::groove:horizontal {
                background: #E0E0E0;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #CCCCCC;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QDialog {
                background-color: #ECECEC;
                color: black;
            }
            QDialog QLabel {
                color: black;
            }
            QDialog QPushButton {
                background-color: #E8E8E8;
                color: black;
                border: 1px solid #CCCCCC;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QDialog QPushButton:hover {
                background-color: #DADADA;
            }
            QDialog QPushButton:pressed {
                background-color: #C8C8C8;
            }
            QDialog QSpinBox, QDialog QDoubleSpinBox, QDialog QLineEdit {
                background-color: #FFFFFF;
                color: black;
                border: 1px solid #CCCCCC;
            }
            """
            # Style for create_group_button in default theme
            self.layer_panel.group_layer_manager.create_group_button.setStyleSheet("""
                QPushButton {
                    background-color: #96938F;  /* A middle-ground color between light and dark themes */
                    color: white;
                    font-weight: bold;
                    border: none;
                    padding: 10px;
                    border-radius: 0;
                }
                QPushButton:hover {
                    background-color: #A8A5A1;
                }
                QPushButton:pressed {
                    background-color: #7E7B77;
                }
            """)
        else:
            # If an unknown theme is selected, default to using no stylesheet
            style_sheet = ""

        # Apply the style sheet to the application
        QApplication.instance().setStyleSheet(style_sheet)

        # Update the canvas theme if needed
        self.canvas.set_theme(theme_name)
        self.canvas.update()

        # Update the layer panel theme
        if hasattr(self.layer_panel, 'set_theme'):
            self.layer_panel.set_theme(theme_name)

        # Update the canvas dark mode flag
        self.canvas.is_dark_mode = theme_name == "dark"

        # Emit the theme_changed signal
        self.theme_changed.emit(theme_name)
    def update_strand_attachable(self, set_number, attachable):
        for strand in self.canvas.strands:
            if strand.set_number == set_number:
                strand.set_attachable(attachable)
        self.canvas.update()  # Redraw the canvas to show the changes

    def handle_angle_adjust_click(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def setup_button_styles(self):
        button_style = """
            QPushButton {{
                background-color: {bg_color};
                color: black;
                font-weight: bold;
                border: 0px solid black;
                border-radius: 6px;
                height: 35px;
                min-width: 100px;
                position: relative;
                padding: 0px 0px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                height: 35px;
                min-width: 100px;
                margin: 1px 1px;
            }}
            QPushButton:checked {{
                background-color: {checked_color};
                border: 4px solid black;
                border-radius: 6px;
                padding: 0px 0px;
            }}
            QPushButton:checked:pressed {{
                background-color: {pressed_color};
                padding: 0px 0px;
                height: 35px;
                min-width: 100px;
                margin: 2px 2px;
                border: 4px solid #2C2C2C;
            }}
        """

        # Special style for angle adjust button with larger min-width
        angle_adjust_button_style = button_style.replace("min-width: 100px;", "min-width: 140px;")

        # Separate style for non-checkable buttons (no size change on press)
        non_checkable_button_style = """
            QPushButton {{
                background-color: {bg_color};
                color: black;
                font-weight: bold;
                border: 0px solid black;
                padding: 6px 26px;
                border-radius: 8px;
                height: 32px;
                min-width: 25px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                padding: 6px 26px;
            }}
        """

        buttons = [
            # (button_object, normal_bg, hover_bg, pressed_bg, disabled_bg)
            (
                self.mask_button,
                "#199693",    # normal (teal)
                "#4CCBC8",    # hover (much lighter teal)
                "#0F625F",    # pressed (darkest teal)
                "#0F625F"     # disabled
            ),
            (
                self.select_strand_button,
                "#F1C40F",    # normal (yellow)
                "#F9E287",    # hover (brighter yellow)
                "#BB9A0C",    # pressed
                "#BB9A0C"     # disabled
            ),
            (
                self.attach_button,
                "#9B59B6",    # normal (purple)
                "#D5A6E6",    # hover (much lighter purple)
                "#703D80",    # pressed
                "#703D80"     # disabled
            ),
            (
                self.move_button,
                "#D35400",    # normal (orange)
                "#FFA366",    # hover (much lighter orange)
                "#A84300",    # pressed
                "#A84300"     # disabled
            ),
            (
                self.rotate_button,
                "#3498DB",    # normal (blue)
                "#92C9F0",    # hover (much lighter blue)
                "#216B97",    # pressed
                "#216B97"     # disabled
            ),
            (
                self.toggle_grid_button,
                "#E93E3E",    # normal (red)
                "#FF7070",    # hover (brighter red)
                "#ab2e2e",    # pressed
                "#ab2e2e"     # disabled
            ),
            (
                self.angle_adjust_button,
                "#2ECC71",    # normal (green)
                "#86E5AD",    # hover (much lighter green)
                "#1F9F56",    # pressed
                "#1F9F56"     # disabled
            ),
            (
                self.save_button,
                "#E75480",    # normal (pink)
                "#FF9FBB",    # hover (much lighter pink)
                "#B64064",    # pressed
                "#B64064"     # disabled
            ),
            (
                self.load_button,
                "#8D6E63",    # normal (brown)
                "#BEA499",    # hover (much lighter brown)
                "#8D6E63",    # pressed
                "#8D6E63"     # disabled
            ),
            (
                self.save_image_button,
                "#7D344D",    # normal (maroon)
                "#B36E89",    # hover (much lighter maroon)
                "#7D344D",    # pressed
                "#7D344D"     # disabled
            ),
            (
                self.toggle_control_points_button,
                "#5F7A93",    # normal (blue-gray)
                "#9CB3CC",    # hover (much lighter blue-gray)
                "#45596E",    # pressed
                "#394857"     # disabled
            )
        ]

        # Apply styles to buttons
        for button, bg_color, hover_color, pressed_color, checked_color in buttons:
            if button in [self.save_button, self.load_button, self.save_image_button]:
                # Non-checkable buttons
                button.setStyleSheet(non_checkable_button_style.format(
                    bg_color=bg_color,
                    hover_color=hover_color,
                    pressed_color=pressed_color
                ))
                button.setCheckable(False)
            else:
                # Checkable buttons
                if button == self.angle_adjust_button:
                    # Use special style for angle adjust button
                    button.setStyleSheet(angle_adjust_button_style.format(
                        bg_color=bg_color,
                        hover_color=hover_color,
                        pressed_color=pressed_color,
                        checked_color=checked_color
                    ))
                else:
                    # Use standard style for other buttons
                    button.setStyleSheet(button_style.format(
                        bg_color=bg_color,
                        hover_color=hover_color,
                        pressed_color=pressed_color,
                        checked_color=checked_color
                    ))
                button.setCheckable(True)

        # Style for layer state button
        self.layer_state_button.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: black;
                font-weight: bold;
                border: none;
                padding: 8px 4px;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: #FFC200;
            }
            QPushButton:pressed {
                background-color: #FFB700;
            }
        """)

    def update_button_states(self, active_mode):
        buttons = {
            "attach": self.attach_button,
            "move": self.move_button,
            "rotate": self.rotate_button,
            "select": self.select_strand_button,
            "mask": self.mask_button
        }

        for mode, button in buttons.items():
            button.setChecked(mode == active_mode)

        self.layer_state_button.clicked.connect(self.show_layer_state_log)
    def setup_connections(self):
        # Layer panel handle connections
        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        # Set layer panel for canvas
        self.canvas.set_layer_panel(self.layer_panel)

        # Layer panel connections
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(lambda idx: self.select_strand(idx, emit_signal=False))
        self.layer_panel.deselect_all_requested.connect(self.canvas.deselect_all_strands)
        self.layer_panel.color_changed.connect(self.handle_color_change)
        self.layer_panel.masked_layer_created.connect(self.create_masked_layer)
        self.layer_panel.masked_mode_entered.connect(self.canvas.deselect_all_strands)
        self.layer_panel.masked_mode_exited.connect(self.restore_selection)
        self.layer_panel.lock_layers_changed.connect(self.update_locked_layers)
        self.layer_panel.strand_deleted.connect(self.delete_strand)

        # Button connections
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.angle_adjust_button.clicked.connect(self.handle_angle_adjust_click)
        self.save_button.clicked.connect(self.save_project)
        self.load_button.clicked.connect(self.load_project)
        self.save_image_button.clicked.connect(self.save_canvas_as_image)
        self.select_strand_button.clicked.connect(self.set_select_mode)
        self.mask_button.clicked.connect(self.set_mask_mode)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # Connect the toggle control points button
        self.toggle_control_points_button.clicked.connect(self.set_control_points_mode)

        # Canvas connections
        self.canvas.strand_selected.connect(self.handle_canvas_strand_selection)

        # Disconnect any existing connections for mask_created
        try:
            self.canvas.mask_created.disconnect(self.handle_mask_created)
        except TypeError:
            # This exception will be raised if there was no connection, which is fine
            pass

        # Reconnect mask_created signal
        self.canvas.mask_created.connect(self.handle_mask_created)

        # Connect the canvas to the group layer manager
        self.layer_panel.group_layer_manager.canvas = self.canvas

        # Connect group operation signal
        self.layer_panel.group_layer_manager.group_panel.group_operation.connect(
            self.layer_panel.group_layer_manager.on_group_operation
        )

        # Add this new connection
        self.canvas.angle_adjust_completed.connect(self.deselect_angle_adjust_button)

        # Connect attachable_changed signal for each layer button
        for button in self.layer_panel.layer_buttons:
            button.attachable_changed.connect(self.update_strand_attachable)

        # Connect toggle control points button
        self.toggle_control_points_button.clicked.connect(self.canvas.toggle_control_points)
        self.toggle_control_points_button.setChecked(False)  # Start with control points visible

        # Connect mask edit mode signals
        self.canvas.mask_edit_exited.connect(self.layer_panel.exit_mask_edit_mode)
        
        # Make sure the canvas has focus policy set
        self.canvas.setFocusPolicy(Qt.StrongFocus)

        # Connect mask edit mode signals
        if hasattr(self.canvas, 'mask_edit_exited'):
            self.canvas.mask_edit_exited.connect(self.layer_panel.exit_mask_edit_mode)
        else:
            logging.error("Canvas does not have mask_edit_exited signal")

    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if filename:
            try:
                # Load strands and groups from file
                strands, groups = load_strands(filename, self.canvas)
                
                # Clear existing canvas state
                self.canvas.strands = []
                self.canvas.groups = {}
                
                # Apply the loaded strands and groups
                apply_loaded_strands(self.canvas, strands, groups)
                
                # Ensure control points are visible after loading
                self.toggle_control_points_button.setChecked(True)
                self.canvas.show_control_points = True
                
                # Update the layer panel
                if hasattr(self.canvas, 'layer_panel'):
                    self.canvas.layer_panel.refresh()
                
                # Force a canvas redraw
                self.canvas.update()
                
                logging.info(f"Project successfully loaded from {filename}")
                
                # Save initial state after loading
                self.layer_state_manager.save_initial_state()
                
            except Exception as e:
                logging.error(f"Error loading project from {filename}: {str(e)}")
                # You might want to show an error dialog to the user here

    def open_settings_dialog(self):
        """Open the settings dialog if it's not already open."""
        # Check if dialog is already open
        if self.settings_dialog.isVisible():
            # Bring existing dialog to front
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        else:
            # Connect theme change signal and show dialog
            self.settings_dialog.theme_changed.connect(self.apply_theme)
            self.settings_dialog.show()

    def show_layer_state_log(self):
        """Display the current layer state information."""
        # If button is not checked, just return
        if not self.layer_state_button.isChecked():
            return
            
        # Store the current mode before opening the dialog
        self._previous_state_mode = self.current_mode

        # Create a new dialog if it doesn't exist or isn't visible
        if not hasattr(self, '_layer_state_dialog') or not self._layer_state_dialog or not self._layer_state_dialog.isVisible():
            logging.info("Opening layer state log dialog")
            _ = self.translations

            # Store the dialog reference
            self._layer_state_dialog = QDialog(self)
            dialog = self._layer_state_dialog
            
            # Set up dialog to handle close events properly
            dialog.closeEvent = lambda event: self.handle_dialog_close(event)
            
            # Retrieve the current state from the LayerStateManager
            order = self.layer_state_manager.getOrder()
            connections = self.layer_state_manager.getConnections()
            masked_layers = self.layer_state_manager.getMaskedLayers()
            colors = self.layer_state_manager.getColors()
            positions = self.layer_state_manager.getPositions()
            selected_strand = self.layer_state_manager.getSelectedStrand()
            newest_strand = self.layer_state_manager.getNewestStrand()
            newest_layer = self.layer_state_manager.getNewestLayer()

            state_info = f"""
{_['current_layer_state']}:

{_['order']}:
{order}

{_['connections']}:
{connections}

{_['masked_layers']}:
{masked_layers}

{_['colors']}:
{colors}

{_['positions']}:
{positions}

{_['selected_strand']}:
{selected_strand}

{_['newest_strand']}:
{newest_strand}

{_['newest_layer']}:
{newest_layer}
"""

            dialog.setWindowTitle(_['layer_state_log_title'])
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            layout = QVBoxLayout(dialog)

            title_layout = QHBoxLayout()
            title_label = QLabel(_['layer_state_log_title'])
            title_layout.addWidget(title_label)

            info_button = QPushButton("?")
            info_button.setFixedSize(40, 40)
            info_button.clicked.connect(self.show_layer_state_info)
            title_layout.addWidget(info_button)
            title_layout.addStretch()

            layout.addLayout(title_layout)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(state_info)
            layout.addWidget(text_edit)

            close_button = QPushButton(_['close'])
            close_button.clicked.connect(lambda: self.close_layer_state_dialog(dialog))
            layout.addWidget(close_button)

            default_width, default_height = 400, 600
            dialog.resize(default_width, default_height)

            canvas_geometry = self.canvas.geometry()
            canvas_top_right = self.canvas.mapToGlobal(canvas_geometry.topRight())
            dialog.move(canvas_top_right.x() - default_width, canvas_top_right.y())

            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

            dialog.finished.connect(self.on_layer_state_dialog_closed)
            logging.info("Showing layer state log dialog")
            dialog.exec_()
        else:
            # If dialog exists and is visible, just bring it to front
            self._layer_state_dialog.raise_()
            self._layer_state_dialog.activateWindow()

    def handle_dialog_close(self, event):
        """Handle the dialog close event."""
        logging.info("Handling dialog close event")
        self.layer_state_button.setChecked(False)
        
        # Just accept the event - cleanup will be handled by on_layer_state_dialog_closed
        event.accept()

    def close_layer_state_dialog(self, dialog):
        """
        Closes the layer state dialog and ensures proper cleanup.
        """
        logging.info("Closing the layer state dialog")
        
        # Uncheck the layer state button
        self.layer_state_button.setChecked(False)
        
        # Restore previous mode
        if hasattr(self, '_previous_state_mode') and self._previous_state_mode is not None:
            self.update_mode(self._previous_state_mode)
            self._previous_state_mode = None

        # Close the dialog first
        if dialog and dialog.isVisible():
            dialog.close()

        # Clean up the reference
            self._layer_state_dialog = None

    def on_layer_state_dialog_closed(self):
        """Handle cleanup when layer state dialog is closed."""
        logging.info("Layer state log dialog closed")
        
        # Ensure button is unchecked
        self.layer_state_button.setChecked(False)
        
        # Restore previous mode
        if hasattr(self, '_previous_state_mode') and self._previous_state_mode is not None:
            self.update_mode(self._previous_state_mode)
            self._previous_state_mode = None
        
        # Clean up the reference
        if hasattr(self, '_layer_state_dialog'):
            self._layer_state_dialog = None

    def show_layer_state_info(self):
        """Display information explaining each piece of layer state data."""
        info_text = self.translations['layer_state_info_text']

        # Display the information in a dialog
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle(self.translations['layer_state_info_title'])
        layout = QVBoxLayout(info_dialog)

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        close_button = QPushButton(self.translations['close'])
        close_button.clicked.connect(info_dialog.accept)
        layout.addWidget(close_button)

        info_dialog.exec_()


    def update_strand_attachable(self, set_number, attachable):
        for strand in self.canvas.strands:
            if strand.set_number == set_number:
                strand.set_attachable(attachable)
        self.canvas.update()  # Redraw the canvas to show the changes

    # Add this new method
    def handle_angle_adjust_click(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def set_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            if self.canvas.is_angle_adjusting:
                # Exit angle adjust mode
                self.canvas.angle_adjust_mode.confirm_adjustment()
                self.update_mode(self.previous_mode)  # Return to previous mode
            else:
                # Enter angle adjust mode
                self.previous_mode = self.current_mode  # Store the current mode
                self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
                self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def deselect_angle_adjust_button(self):
        self.angle_adjust_button.setChecked(False)
        self.update_mode(self.previous_mode)  # Return to the previous mode

    def set_mask_mode(self):
        self.update_mode("mask")
        self.canvas.set_mode("mask")

    def handle_mask_created(self, strand1, strand2):
        logging.info(f"Received mask_created signal for {strand1.layer_name} and {strand2.layer_name}")

        # Verify that both strands exist in the canvas
        if strand1 not in self.canvas.strands or strand2 not in self.canvas.strands:
            logging.error("One or both strands are not in the canvas. Cannot create mask.")
            return

        # Check if a mask already exists for these strands
        if self.canvas.mask_exists(strand1, strand2):
            logging.info(f"Mask already exists for {strand1.layer_name} and {strand2.layer_name}. Skipping creation.")
            return

        # Create the masked layer
        masked_strand = MaskedStrand(strand1, strand2)
        self.canvas.add_strand(masked_strand)

        # Update the groups
        self.layer_panel.group_layer_manager.update_groups_with_new_strand(masked_strand)

        # Update UI or perform any other necessary actions
        self.update_mode(self.current_mode)  # Refresh the current mode
        
        # Update the layer panel
        if self.layer_panel:
            self.layer_panel.refresh()

        logging.info(f"Processed mask creation for {strand1.layer_name} and {strand2.layer_name}")

        # Note: The actual creation of the masked strand is now handled in the StrandDrawingCanvas class


    def save_canvas_as_image(self):
            """Save the entire canvas as a PNG image with transparent background, including all layers and masks."""
            filename, _ = QFileDialog.getSaveFileName(self, "Save Canvas as Image", "", "PNG Files (*.png)")
            if filename:
                # Ensure the filename ends with .png
                if not filename.lower().endswith('.png'):
                    filename += '.png'
                
                # Get the size of the canvas
                canvas_size = self.canvas.size()
                
                # Create a transparent image of the canvas size
                image = QImage(canvas_size, QImage.Format_ARGB32)
                image.fill(Qt.transparent)
                
                # Create a painter for the image
                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Custom painting method to draw all strands and masks
                def paint_canvas(painter):
                    # Draw the grid if it's visible
                    if self.canvas.show_grid:
                        self.canvas.draw_grid(painter)
                    
                    # Draw all strands in their current order
                    for strand in self.canvas.strands:
                        if strand == self.canvas.selected_strand:
                            self.canvas.draw_highlighted_strand(painter, strand)
                        else:
                            strand.draw(painter)
                    
                    # Draw the current strand if it exists
                    if self.canvas.current_strand:
                        self.canvas.current_strand.draw(painter)
                    
                    # Draw strand names if enabled
                    if self.canvas.should_draw_names:
                        for strand in self.canvas.strands:
                            self.canvas.draw_strand_label(painter, strand)

                # Perform the custom painting
                paint_canvas(painter)
                
                # End painting
                painter.end()
                
                # Save the image
                image.save(filename)
                logging.info(f"Full canvas saved as image: {filename}")

    def handle_color_change(self, set_number, color):
        self.canvas.update_color_for_set(set_number, color)
        self.layer_panel.update_colors_for_set(set_number, color)

    def create_masked_layer(self, layer1_index, layer2_index):
        logging.info(f"Creating masked layer for layers at indices {layer1_index} and {layer2_index}")
        layer1 = self.canvas.strands[layer1_index]
        layer2 = self.canvas.strands[layer2_index]
        
        masked_strand = MaskedStrand(layer1, layer2)
        self.canvas.add_strand(masked_strand)
        
        button = self.layer_panel.add_masked_layer_button(layer1_index, layer2_index)
        button.color_changed.connect(self.handle_color_change)
        
        logging.info(f"Created masked layer: {masked_strand.layer_name}")
        
        # Update the groups with the new masked strand
        logging.info("Updating groups with new masked strand")
        self.layer_panel.group_layer_manager.update_groups_with_new_mask(masked_strand)
        
        self.canvas.update()
        self.update_mode(self.current_mode)

        logging.info("Finished creating masked layer and updating groups")

    def restore_selection(self):
        if self.layer_panel.last_selected_index is not None:
            self.select_strand(self.layer_panel.last_selected_index)

    def set_select_mode(self):
        self.update_mode("select")
        self.canvas.set_mode("select")
        
    def update_mode(self, mode):
        if self.current_mode == "angle_adjust" and mode != "angle_adjust":
            # If we're leaving angle adjust mode, confirm the adjustment
            self.canvas.angle_adjust_mode.confirm_adjustment()
        
        self.current_mode = mode
        self.canvas.set_mode(mode)
        self.update_button_states(mode)

        # Update button states based on mode
        if mode == "select":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(False)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "attach":
            self.attach_button.setEnabled(False)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "move":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(False)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "angle_adjust":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "mask":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(False)
            self.rotate_button.setEnabled(True)
        elif mode == "new_strand":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(False)
            self.rotate_button.setEnabled(True)
        elif mode == "rotate":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)  # Keep enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(False)
        elif mode == "control_points":
            self.toggle_control_points_button.setEnabled(False)

        # Always keep angle_adjust_button visible and enabled
        self.angle_adjust_button.setVisible(True)
        self.angle_adjust_button.setEnabled(True)

        if self.canvas.selected_strand_index is not None:
            self.canvas.highlight_selected_strand(self.canvas.selected_strand_index)

    def deselect_angle_adjust_button(self):
        # This method is no longer needed, but we'll keep it empty for compatibility
        pass


    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.layer_panel.keyPressEvent(event)
        
        if event.key() == Qt.Key_Escape:
            # If we're in mask edit mode, exit it
            if self.canvas.mask_edit_mode:
                self.exit_mask_edit_mode()
                # Use translated message from the current language
                _ = translations[self.language_code]
                self.statusBar().showMessage(_['mask_edit_mode_exited'], 2000)
        elif event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            if self.canvas.selected_strand and not isinstance(self.canvas.selected_strand, MaskedStrand):
                self.toggle_angle_adjust_mode()
            elif self.canvas.selected_strand and isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
        elif self.canvas.is_angle_adjusting:
            self.canvas.angle_adjust_mode.handle_key_press(event)
        elif event.key() == Qt.Key_M and event.modifiers() == Qt.ControlModifier:
            self.set_mask_mode()

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.layer_panel.keyReleaseEvent(event)

    def set_attach_mode(self):
        self.update_mode("attach")
        self.canvas.set_mode("attach")  # Explicitly set the canvas mode
        if self.canvas.last_selected_strand_index is not None:
            self.select_strand(self.canvas.last_selected_strand_index)
        
        # Ensure the attach button is checked and others are unchecked
        self.attach_button.setChecked(True)
        self.move_button.setChecked(False)
        self.rotate_button.setChecked(False)
        self.select_strand_button.setChecked(False)
        self.mask_button.setChecked(False)
        self.angle_adjust_button.setChecked(False)

    def set_move_mode(self):
        self.update_mode("move")
        self.canvas.last_selected_strand_index = self.canvas.selected_strand_index
        
        # Highlight the selected attached strand immediately
        if self.canvas.selected_strand and isinstance(self.canvas.selected_strand, AttachedStrand):
            self.canvas.selected_attached_strand = self.canvas.selected_strand
            self.canvas.selected_attached_strand.start_selected = True
        else:
            self.canvas.selected_attached_strand = None
        
        self.canvas.update()  # Force an update of the canvas


    def create_new_strand(self):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor(200, 170, 230, 255) 
        
        self.canvas.start_new_strand_mode(set_number)
        
        logging.info(f"Ready to create new main strand for set: {set_number}")
        
        self.layer_state_manager.save_current_state()


    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            if self.canvas.is_angle_adjusting:
                # Exit angle adjust mode
                self.canvas.angle_adjust_mode.confirm_adjustment()
                self.update_mode(self.previous_mode)  # Return to previous mode
            else:
                # Enter angle adjust mode
                self.previous_mode = self.current_mode  # Store the current mode
                self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
                self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def select_strand(self, index, emit_signal=True):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        
        if index is None or index == -1:
            self.canvas.clear_selection()
            if emit_signal:
                self.layer_panel.clear_selection()
        elif self.canvas.selected_strand_index != index:
            self.canvas.select_strand(index)
            if emit_signal:
                self.layer_panel.select_layer(index, emit_signal=False)
        
        self.canvas.is_first_strand = False
        # Don't call update_mode here to avoid recursion

    def handle_canvas_strand_selection(self, index):
        self.select_strand(index, emit_signal=True)
        # Update the mode after selection, if necessary
        if self.current_mode == "select":
            self.update_mode("attach")  # or any other appropriate mode


    def delete_strand(self, index):
            if 0 <= index < len(self.canvas.strands):
                strand_to_delete = self.canvas.strands[index]
                strand_name = strand_to_delete.layer_name
                logging.info(f"Attempting to delete strand: {strand_name}")

                # Find the correct strand in the canvas based on the layer name
                strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
                
                if strand_index is not None:
                    strand = self.canvas.strands[strand_index]
                    logging.info(f"Deleting strand: {strand.layer_name}")

                    set_number = strand.set_number
                    is_main_strand = strand.layer_name.split('_')[1] == '1'
                    is_attached_strand = isinstance(strand, AttachedStrand)

                    strands_to_remove = [strand]
                    if is_main_strand:
                        strands_to_remove.extend([s for s in self.canvas.strands if s.set_number == set_number and s != strand])

                    # Delete masks that are directly related to the deleted strand
                    masks_to_delete = []
                    for s in self.canvas.strands:
                        if isinstance(s, MaskedStrand):
                            if strand.layer_name in s.layer_name.split('_'):
                                masks_to_delete.append(s)
                                logging.info(f"Marking mask for deletion: {s.layer_name}")

                    # Remove the strands and masks
                    for s in strands_to_remove + masks_to_delete:
                        self.canvas.remove_strand(s)
                        logging.info(f"Removed strand/mask: {s.layer_name}")

                    # Collect indices of removed strands and masks
                    removed_indices = [i for i, s in enumerate(self.canvas.strands) if s in strands_to_remove + masks_to_delete]

                    # Update the layer panel without renumbering
                    self.layer_panel.update_after_deletion(set_number, removed_indices, is_main_strand, renumber=False)

                    # Ensure correct state of the canvas
                    self.canvas.force_redraw()

                    # Clear any selection
                    self.canvas.clear_selection()

                    # Update the mode to maintain consistency
                    self.update_mode(self.current_mode)

                    # Save the current state after deletion
                    self.layer_state_manager.save_current_state()

                    logging.info("Finished deleting strand and updating UI")
                else:
                    logging.warning(f"Strand {strand_name} not found in canvas strands")
            else:
                logging.warning(f"Invalid strand index: {index}")

    def start_resize(self, event):
        self.resize_start = event.pos()

    def do_resize(self, event):
        if hasattr(self, 'resize_start'):
            delta = event.pos().x() - self.resize_start.x()
            sizes = self.splitter.sizes()
            sizes[0] += delta
            sizes[1] -= delta
            self.splitter.setSizes(sizes)

    def stop_resize(self, event):
        if hasattr(self, 'resize_start'):
            del self.resize_start

    def update_locked_layers(self, locked_layers, lock_mode_active):
        self.canvas.move_mode.set_locked_layers(locked_layers, lock_mode_active)


    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if filename:
            # Retrieve the group data from the correct instance
            groups = self.group_layer_manager.get_group_data()
            logging.debug(f"Group data before saving: {groups}")
            # Save the strands and groups
            save_strands(self.canvas.strands, groups, filename, self.canvas)
            logging.info(f"Project saved to {filename}")
    def edit_group_angles(self, group_name):
        if group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            dialog = StrandAngleEditDialog(group_name, group_data, canvas=self.canvas)
            dialog.angle_changed.connect(self.canvas.update_strand_angle)
            dialog.exec_()
    def set_control_points_mode(self):
        # Make sure we switch to an actual mode object rather than a string.
        self.canvas.toggle_control_points() 


    def set_rotate_mode(self):
        self.update_mode("rotate")
        self.canvas.set_mode("rotate")

    def exit_mask_edit_mode(self):
        """Handle exiting mask edit mode."""
        self.update_mode("select")
        self.mask_button.setChecked(False)
        self.select_strand_button.setChecked(True)
        self.update_button_states("select")

        # NEW: Re-enable mainwindow buttons if they were disabled for mask edit
        self.enable_all_mainwindow_buttons()

    def set_language(self, language_code):
        """Set the application language and update all UI elements."""
        self.language_code = language_code

        # Update the language code in all components
        self.canvas.language_code = language_code
        self.layer_panel.language_code = language_code
        
        # Update GroupLayerManager's language code and translations
        if self.layer_panel.group_layer_manager:
            self.layer_panel.group_layer_manager.language_code = language_code
            self.layer_panel.group_layer_manager.update_translations()

        if self.settings_dialog:
            self.settings_dialog.language_code = language_code

        # Update translations in UI elements
        self.translate_ui()
        self.canvas.update_translations()
        self.layer_panel.translate_ui()
        if self.settings_dialog.isVisible():
            self.settings_dialog.update_translations()

        logging.info(f"Language set to {language_code}")
    def translate_ui(self):
        """Update the UI texts to the selected language."""
        _ = translations[self.language_code]
        self.translations = _  # Store the translations for later use

        # Update window title
        self.setWindowTitle(_['main_window_title'])

        # Update button texts
        self.attach_button.setText(_['attach_mode'])
        self.move_button.setText(_['move_mode'])
        self.rotate_button.setText(_['rotate_mode'])
        self.toggle_grid_button.setText(_['toggle_grid'])
        self.angle_adjust_button.setText(_['angle_adjust_mode'])
        self.select_strand_button.setText(_['select_mode'])
        self.mask_button.setText(_['mask_mode'])
        self.save_button.setText(_['save'])
        self.load_button.setText(_['load'])
        self.save_image_button.setText(_['save_image'])
        self.layer_state_button.setText(_['layer_state'])
        self.toggle_control_points_button.setText(_['toggle_control_points'])

        # Update settings button tooltip or text
        self.settings_button.setToolTip(_['settings'])

        # Update any other UI elements as needed
        # ...

        # Apply translations to other UI components
        if hasattr(self.layer_panel, 'translate_ui'):
            self.layer_panel.translate_ui()
        if hasattr(self.canvas, 'update_translations'):
            self.canvas.update_translations()
        if self.settings_dialog.isVisible():
            self.settings_dialog.update_translations()

    def on_toggle_control_points_button_clicked(self, checked):
        """
        The logic is inverted so that unchecking the button will show (paint) control points,
        and checking it will hide them.
        """
        if checked:
            # If button is checked => hide control points
            self.canvas.show_control_points = False
        
        else:
            # If button is unchecked => show control points
            self.canvas.show_control_points = True
        
        self.canvas.update()

    # NEW: Add these methods in MainWindow to disable/enable all buttons
    def disable_all_mainwindow_buttons(self):
        """Disable all main window buttons so they cannot be pressed."""
        for button in [
            self.attach_button,
            self.move_button,
            self.rotate_button,
            self.toggle_grid_button,
            self.angle_adjust_button,
            self.select_strand_button,
            self.mask_button,
            self.save_button,
            self.load_button,
            self.save_image_button,
            self.toggle_control_points_button,
            self.settings_button,
            self.layer_state_button
        ]:
            button.setEnabled(False)

    def enable_all_mainwindow_buttons(self):
        """Re-enable all main window buttons."""
        for button in [
            self.attach_button,
            self.move_button,
            self.rotate_button,
            self.toggle_grid_button,
            self.angle_adjust_button,
            self.select_strand_button,
            self.mask_button,
            self.save_button,
            self.load_button,
            self.save_image_button,
            self.toggle_control_points_button,
            self.settings_button,
            self.layer_state_button
        ]:
            button.setEnabled(True)