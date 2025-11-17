import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QSplitter, QFileDialog, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, pyqtSignal, QTimer, QEvent
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
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
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
from PyQt5.QtCore import QPointF

# main_window.py

class MainWindow(QMainWindow):
    language_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.language_code = 'en'  # Default language
        self.current_theme = 'default'  # Default theme

        pass

        # Initialize components
        self.layer_state_manager = LayerStateManager()
        pass

        self.canvas = StrandDrawingCanvas(parent=self)  # Pass self as parent
        self.canvas.parent_window = self  # Explicitly set the parent window reference
        self.layer_panel = LayerPanel(self.canvas, parent=self)  # Pass self as parent

        # Use the GroupLayerManager from layer_panel
        self.group_layer_manager = self.layer_panel.group_layer_manager

        # Set the group_layer_manager in the canvas
        self.canvas.group_layer_manager = self.group_layer_manager

        pass

        # Create settings dialog
        # Pass the undo_redo_manager and layer_panel for refresh functionality
        undo_manager = self.layer_panel.undo_redo_manager if hasattr(self.layer_panel, 'undo_redo_manager') else None
        self.settings_dialog = SettingsDialog(parent=self, canvas=self.canvas, undo_redo_manager=undo_manager, layer_panel=self.layer_panel)

        # Initialize translations for all widgets
        self.layer_panel.update_translations()

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

        # Window will be shown and maximized from main.py
        # self.showMaximized()

        # Load user settings from file
        self.load_settings_from_file()
        # Log initial state
        self.layer_state_manager.save_initial_state()
        self.layer_state_manager.log_layer_state()

        # Set up connections for LayerStateManager
        self.layer_state_manager.canvas = self.canvas
        self.layer_state_manager.layer_panel = self.layer_panel
        self.canvas.layer_state_manager = self.layer_state_manager

        pass

        # Connect signals
        self.canvas.strand_created.connect(self.layer_state_manager.on_strand_created_in_layer_manager)
        self.canvas.strand_deleted.connect(self.layer_state_manager.on_strand_deleted_in_layer_manager)
        self.canvas.masked_layer_created.connect(self.layer_state_manager.on_masked_layer_created_in_layer_manager)
        pass

        pass

        # Install global event filter so we can intercept Space before any child widget sees it
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        # Connection will be handled in setup_connections

    def showEvent(self, event):
        """Override showEvent to ensure proper window state"""
        super().showEvent(event)
        
        # Only do initial positioning if this is the first time the window is shown
        # (not during restore from minimize)
        if not hasattr(self, '_initial_show_completed'):
            pass
            
            # Check if window has already been assigned to a specific screen by main.py
            if hasattr(self, 'windowHandle') and self.windowHandle() and self.windowHandle().screen():
                # Window already has a screen assignment - respect it
                current_screen = self.windowHandle().screen()
                screen_size = current_screen.availableGeometry()
                pass
            else:
                # Fallback to primary screen if no assignment
                screen = QApplication.primaryScreen()
                screen_size = screen.availableGeometry()
                pass
            
            # Set window to use almost all available space
            self.setGeometry(screen_size)
            
            # Then maximize
            self.setWindowState(Qt.WindowMaximized)
            
            # Mark that initial show is complete
            self._initial_show_completed = True
            pass
        else:
            pass
        
        # Ensure splitter sizes are properly set after the window is fully shown
        # Use QTimer to defer this slightly so all widgets are fully laid out
        QTimer.singleShot(100, self.set_initial_splitter_sizes)

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
        self.layer_state_button.setText(_['layer_state'])
        self.toggle_control_points_button.setText(_['toggle_control_points'])
        self.toggle_shadow_button.setText(_['toggle_shadow'])

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
        from PyQt5.QtGui import QColor

        app_name = "OpenStrand Studio"
        program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        pass
        settings_dir = os.path.join(program_data_dir, app_name)
        pass
        file_path = os.path.join(settings_dir, 'user_settings.txt')
        pass

        theme_name = 'default'
        language_code = 'en'
        # Note: Shadow color is now handled in main.py, not here

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    for line in file:
                        if line.startswith('Theme:'):
                            theme_name = line.strip().split(':', 1)[1].strip()
                        elif line.startswith('Language:'):
                            language_code = line.strip().split(':', 1)[1].strip()
                        # Note: ShadowColor handling removed from here
            except Exception as e:
                pass
        else:
            pass

        # Apply the theme and language
        self.apply_theme(theme_name)
        self.set_language(language_code)
        
        # Note: Shadow color application removed from here

    def setup_ui(self):
        pass

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
            pass
        else:
            pass

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create the horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 5, 10, 5)
        button_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align buttons to the left and center vertically

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
        # self.attach_button.setMinimumWidth(190)  # Removed to allow dynamic resizing

        # Set the gear icon or fallback to Unicode character if the image is not found
        gear_icon_path = os.path.join(base_path, 'settings_icon.png')
        pass

        if os.path.exists(gear_icon_path):
            pass
            self.settings_button.setIcon(QIcon(gear_icon_path))
            self.settings_button.setIconSize(QSize(24, 24))
        else:
            pass
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
        self.toggle_control_points_button.setChecked(True)  # Start with button pressed (points visible)

        # Create the toggle shadow button
        self.toggle_shadow_button = QPushButton("Toggle Shadow")
        self.toggle_shadow_button.setCheckable(True)
        self.toggle_shadow_button.setChecked(False)  # Shadow is disabled by default
        self.toggle_shadow_button.setToolTip("Enable/disable shadow effects for overlapping strands")
        
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
        button_layout.addWidget(self.toggle_shadow_button)

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

        button_layout.setSpacing(10)  # Ensure consistent spacing between buttons

        # Set up the splitter and layouts
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.left_widget = QWidget()  # store as instance variable
        left_layout = QVBoxLayout(self.left_widget)

        # Wrap the button layout in a container widget
        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # No vertical resizing

        # Get the button container's height and fix its height
        button_height = button_container.sizeHint().height()
        button_container.setFixedHeight(button_height)

        # Set up the scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(button_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Explicitly disable vertical scrollbar
        scroll_area.setFixedHeight(button_height + 15)  # Fixed height for scroll area
        
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QScrollArea > QWidget > QWidget {
                margin: 0px;
                padding: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                border: none;
                border-radius: 6px;
            }
        """)
        
        # Disable vertical scrolling by overriding the wheelEvent
        def disable_vertical_scroll(event):
            if event.angleDelta().y() != 0:
                event.ignore()
            else:
                QScrollArea.wheelEvent(scroll_area, event)
        scroll_area.wheelEvent = disable_vertical_scroll

        left_layout.addWidget(scroll_area)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.layer_panel)

        # Configure splitter and main layout
        self.splitter.setHandleWidth(1)  # Small but visible width instead of 0
        
        # Apply cross-platform splitter handle styling
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;  /* Light gray color */
                border: none;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
            QSplitter::handle:vertical {
                height: 1px;
            }
        """)
        
        main_layout.addWidget(self.splitter)
        
        # Set minimum widths and enforce them using size policies
        self.left_widget.setMinimumWidth(300)
        self.left_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layer_panel.setMinimumWidth(350)
        self.layer_panel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Set splitter stretch factors properly - left widget (index 0) gets more stretch, right panel (index 1) is fixed
        self.splitter.setStretchFactor(0, 1)  # Left widget can stretch
        self.splitter.setStretchFactor(1, 0)  # Right panel (layer panel) doesn't stretch


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
            self.toggle_control_points_button,
            self.toggle_shadow_button
        ]
        
        for button in buttons:
            # Change size policy to Preferred so buttons expand based on their content.
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            button.setFixedHeight(32)  # Maintain consistent height
            # Removed the fixed minimum width for all buttons here:
            # button.setMinimumWidth(100)
        
        # Special handling for buttons with longer text
        long_text_buttons = [self.save_button, self.load_button, self.save_image_button]
        for button in long_text_buttons:
            button.setMinimumWidth(120)  # Allow more width for longer text

        # Apply button styles
        self.setup_button_styles()
        pass
    def set_initial_splitter_sizes(self):
        """
        Set the initial sizes of the splitter to make the layer panel narrower.
        The layer panel is set to its minimum width, and the left widget
        takes the remaining space.
        """
        # Use the minimum width of the layer panel (should be 350)
        layer_panel_width = self.layer_panel.minimumWidth()
        total_width = self.width()
        
        # Ensure we have a reasonable total width
        if total_width < layer_panel_width + 300:  # Minimum for left widget
            total_width = layer_panel_width + 800  # Default reasonable size
        
        left_width = total_width - layer_panel_width
        self.splitter.setSizes([left_width, layer_panel_width])
        
        # Force an update to ensure the sizing takes effect
        self.splitter.update()
        
        pass
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
        self.toggle_control_points_button.clicked.connect(self.on_toggle_control_points_button_clicked)

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

        # Control points button already connected in setup_connections
        self.toggle_control_points_button.setChecked(True)  # Start with button pressed (control points visible)

        # Connect the toggle shadow button
        self.toggle_shadow_button.clicked.connect(self.canvas.toggle_shadow)
        self.toggle_shadow_button.setChecked(False)  # Start with shadows disabled

        # Connect mask edit mode signals
        self.canvas.mask_edit_exited.connect(self.layer_panel.exit_mask_edit_mode)
        
        # Make sure the canvas has focus policy set
        self.canvas.setFocusPolicy(Qt.StrongFocus)

        # Connect mask edit mode signals
        if hasattr(self.canvas, 'mask_edit_exited'):
            self.canvas.mask_edit_exited.connect(self.layer_panel.exit_mask_edit_mode)
        else:
            pass

    def open_settings_dialog(self):
        """Open the settings dialog if it's not already open."""
        if not hasattr(self, '_settings_dialog'):
            # Create the dialog only once and store it
            self._settings_dialog = self.settings_dialog
            # Remove fixed size and use expanding size policy
            self._settings_dialog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Set initial size (optional, can be adjusted based on content)
            self._settings_dialog.resize(800, 600)
            # Add margins to prevent content clipping
            self._settings_dialog.layout().setContentsMargins(10, 10, 10, 10)
            # Set the current theme
            self._settings_dialog.current_theme = self.current_theme
            # Connect theme change signal
            self._settings_dialog.theme_changed.connect(self.apply_theme)
            # Apply current theme to dialog
            self._settings_dialog.apply_dialog_theme(self.current_theme)
        
        # Show the existing dialog
        # Ensure the question mark button is removed
        self._settings_dialog.setWindowFlags(self._settings_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def apply_theme(self, theme_name):
        # Store the current theme
        self.current_theme = theme_name
        
        if theme_name == "dark":
            style_sheet = """
        QWidget {
            background-color: #2C2C2C;
            color: white;
        }
        QPushButton {
            background-color: #2C2C2C;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3D3D3D;
        }
        QPushButton:pressed {
            background-color: #2D2D2D;
        }
        QPushButton:checked {
            background-color: #505050;
            border: 2px solid #808080;
            padding: 8px 16px;
        }
        QPushButton:disabled {
            background-color: #1A1A1A;
            color: #808080;
        }
        QPushButton:checked:disabled {
            background-color: #505050;
            border: 2px solid #808080;
        }
        QPushButton:checked:disabled:hover {
            background-color: #505050;
        }
        QPushButton:checked:disabled:pressed {
            background-color: #505050;
            border: 2px solid #808080;
        }
        
        /* Dialog button styling */
        QDialog QPushButton {
            background-color: #252525;
            color: white;
            font-weight: normal;  /* Changed from bold to normal */
            border: 2px solid #000000;
            padding: 10px;
            border-radius: 4px;
            min-width: 80px;
        }
        QDialog QPushButton:hover {
            background-color: #505050;
        }
        QDialog QPushButton:pressed {
            background-color: #151515;
            border: 2px solid #000000;
        }
    
        /* Style for QScrollArea and scrolling areas in dark mode */
        QAbstractScrollArea {
            background-color: #2C2C2C;
            border: none;
        }
        QScrollArea > QWidget {
            background-color: #2C2C2C;
        }
        QScrollBar:horizontal {
            background-color: #1A1A1A;
            border: none;
            height: 12px;
        }
        QScrollBar::handle:horizontal {
            background-color: #181818;  /* Updated darker shade */
            border: none;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #4A4A4A;
        }
        QScrollBar::handle:horizontal:pressed {
            background-color: #606060;
        }
        QScrollBar:vertical {
            background-color: #1A1A1A;
            background-image: none;
            width: 10px;
            margin: 0px;
        }
        QScrollArea::corner {
            background-color: #2C2C2C;
            background-image: none;
            margin: 0;
            padding: 0;
        }
        QScrollArea::viewport {
            background-color: #2C2C2C;
            background-image: none;
            border: none;
        }
        QScrollBar::handle:vertical {
            background-color: #2D2D2D;
            border: none;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #4A4A4A;
        }
        QScrollBar::handle:vertical:pressed {
            background-color: #606060;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: none;
            border: none;
        }
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: #1A1A1A;
        }
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {
            background: #010101;
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            background: none;
            border: none;
        }
            """
            # Update create_group_button style in dark mode
            self.layer_panel.group_layer_manager.create_group_button.setStyleSheet("""
        QPushButton {
            background-color: #2A2A2A;
            color: white;
            font-weight: bold;
            border: 2px solid #000000;
            padding: 10px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
            border: 2px solid #000000;
        }
        QPushButton:default {
            background-color: #1A1A1A;
            border: 2px solid #000000;
        }
        QPushButton:default:hover {
            background-color: #252525;
        }
        QPushButton:default:pressed {
            background-color: #151515;
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
            border: 2px solid #CCCCCC;
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
            width: 16px;
            height: 16px;
            background: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            image: url(:/icons/checkbox_checked_black.png);
        }
        /* Dialog button styling (updated to match light theme) */
        QDialog QPushButton {
            background-color: #F0F0F0;
            color: black;
            font-weight: normal;
            border: 2px solid #CCCCCC;
            padding: 10px;
            border-radius: 4px;
            min-width: 80px;
        }
        QDialog QPushButton:hover {
            background-color: #E0E0E0;
        }
        QDialog QPushButton:pressed {
            background-color: #D0D0D0;
            border: 2px solid #B0B0B0;
        }

        /* Styles for scrollbars in light mode */
        QScrollBar:horizontal {
            background: #F5F5F5;
            border: none;
            height: 12px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #D4D4D4;
            border: none;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #B0B0B0;  /* Darker gray for hover in light theme */
        }
        QScrollBar::handle:horizontal:pressed {
            background: #909090;  /* Even darker gray for pressed in light theme */
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            background: none;
            border: none;
        }
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {
            background: #F5F5F5;
        }
        QScrollBar:vertical {
            background: #F5F5F5;
            border: none;
            width: 12px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #D4D4D4;
            border: none;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #B0B0B0;  /* Darker gray for hover in light theme */
        }
        QScrollBar::handle:vertical:pressed {
            background: #909090;  /* Even darker gray for pressed in light theme */
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: none;
            border: none;
        }
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: #F5F5F5;
        }
        QScrollArea::viewport {
            background-color: #FFFFFF;
            background-image: none;
            border: none;
        }
        QScrollArea {
            background-color: #FFFFFF;
            border: none;
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
        /* Dialog button styling (updated to match default theme) */
        QDialog QPushButton {
            background-color: #E8E8E8;
            color: black;
            font-weight: normal;
            border: 2px solid #B0B0B0;
            padding: 10px;
            border-radius: 4px;
            min-width: 80px;
        }
        QDialog QPushButton:hover {
            background-color: #DADADA;
        }
        QDialog QPushButton:pressed {
            background-color: #C8C8C8;
            border: 2px solid #A0A0A0;
        }

        /* Styles for scrollbars in default mode */
        QScrollBar:horizontal {
            background: #DADADA;
            border: none;
            height: 12px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #BFBFBF;
            border: none;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #A0A0A0;  /* Darker gray for hover in default theme */
        }
        QScrollBar::handle:horizontal:pressed {
            background: #808080;  /* Even darker gray for pressed in default theme */
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            background: none;
            width: 0px;
        }
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {
            background: #DADADA;
        }
        QScrollBar:vertical {
            background-color: #DADADA;
            border: none;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #BFBFBF;
            border: none;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #A0A0A0;  /* Darker gray for hover in default theme */
        }
        QScrollBar::handle:vertical:pressed {
            background: #808080;  /* Even darker gray for pressed in default theme */
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: none;
            border: none;
        }
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: #DADADA;
        }
        QScrollArea::viewport {
            background-color: #ECECEC;
            background-image: none;
            border: none;  /* Removed explicit left/right borders */
        }
        /* Remove any default borders for panels for consistency */
        QWidget, QFrame, QScrollArea, QScrollArea::viewport {
            border: none;
        }
            """
            # Style for create_group_button in default theme - ensure no borders
            self.layer_panel.group_layer_manager.create_group_button.setStyleSheet("""
        QPushButton {
            background-color: #96938F;
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
    
        # If settings dialog exists, update its theme
        if hasattr(self, '_settings_dialog'):
            self._settings_dialog.current_theme = theme_name
            self._settings_dialog.apply_dialog_theme(theme_name)
    
        # Emit the theme_changed signal
        self.theme_changed.emit(theme_name)
    def update_strand_attachable(self, set_number, attachable):
        for strand in self.canvas.strands:
            if strand.set_number == set_number:
                strand.set_attachable(attachable)
        self.canvas.update()  # Redraw the canvas to show the changes

    def unpress_angle_adjust_button(self):
        """Unpress the angle adjust button exactly like attach button - using standard mode switching"""
        pass
        pass
        pass
        
        # Always force the button to be unchecked first
        self.angle_adjust_button.setChecked(False)
        
        # Helper to pick a safe fallback mode
        def _safe(desired):
            valid = {"attach", "move", "rotate", "select", "mask"}
            return desired if desired in valid else "attach"

        # Use the standard mode switching system like attach button does
        if self.current_mode == "angle_adjust":
            previous_mode = _safe(getattr(self, 'previous_mode', 'attach'))
            pass
            self.update_mode(previous_mode)
        else:
            # If not in angle_adjust mode, ensure we're in a proper mode that won't recheck the button
            prev = getattr(self, 'previous_mode', None)
            if prev and prev != "angle_adjust":
                target = _safe(prev)
                pass
                self.update_mode(target)
            else:
                pass
                self.update_mode("attach")
        
        # Force uncheck again after mode change as safety measure
        self.angle_adjust_button.setChecked(False)
        
        pass
        pass

    def handle_angle_adjust_click(self):
        # First, ensure the button gets pressed visually
        self.angle_adjust_button.setChecked(True)
        
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                # Unpress the button since we can't use it for masked strands
                self.unpress_angle_adjust_button()
                return
            
            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
        else:
            pass
            
            # Unpress the button immediately since no strand is selected
            self.unpress_angle_adjust_button()

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
                padding: 6px 12px;
                border-radius: 8px;
                height: 35px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                padding: 6px 12px;
                height: 35px;
                min-width: 70px;
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
                "#B89EE6",    # normal (lighter blueviolet)
                "#D4C2F2",    # hover (even lighter blueviolet) 
                "#9B84C9",    # pressed
                "#7D6AA6"     # disabled                
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
                "#4CAF50",    # normal (bright green)
                "#81C784",    # hover (lighter bright green) 
                "#388E3C",    # pressed
                "#388E3C"     # disabled
            ),
            (
                self.toggle_shadow_button,
                "rgba(176, 190, 197, 0.7)",    # normal (semi-transparent #b0bec5)
                "rgba(196, 207, 212, 0.7)",    # hover (semi-transparent lighter #b0bec5)
                "rgba(156, 173, 182, 0.7)",    # pressed (semi-transparent darker #b0bec5)
                "rgba(136, 156, 167, 0.7)"     # disabled (semi-transparent darkest #b0bec5)
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
            "mask": self.mask_button,
            "angle_adjust": self.angle_adjust_button
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
        self.toggle_control_points_button.clicked.connect(self.on_toggle_control_points_button_clicked)

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

        # Control points button already connected in setup_connections
        self.toggle_control_points_button.setChecked(True)  # Start with button pressed (control points visible)

        # Connect the toggle shadow button
        self.toggle_shadow_button.clicked.connect(self.canvas.toggle_shadow)
        self.toggle_shadow_button.setChecked(False)  # Start with shadows disabled

        # Connect mask edit mode signals
        self.canvas.mask_edit_exited.connect(self.layer_panel.exit_mask_edit_mode)
        
        # Make sure the canvas has focus policy set
        self.canvas.setFocusPolicy(Qt.StrongFocus)

        # Connect mask edit mode signals
        if hasattr(self.canvas, 'mask_edit_exited'):
            self.canvas.mask_edit_exited.connect(self.layer_panel.exit_mask_edit_mode)
        else:
            pass

    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if not filename:
            return

        # Save current button states before loading
        current_control_points_state = self.toggle_control_points_button.isChecked()
        current_shadow_state = self.toggle_shadow_button.isChecked()
        
        # Store the current shadow state in canvas BEFORE any loading
        # This ensures both load paths respect the current button state
        self.canvas._preserve_shadow_state = current_shadow_state
        self.canvas._preserve_control_points_state = current_control_points_state

        # First try to treat the file as a full history export
        undo_mgr = getattr(self.layer_panel, 'undo_redo_manager', None)
        history_loaded = False
        if undo_mgr:
            try:
                history_loaded = undo_mgr.import_history(filename)
            except Exception as e:
                pass
                history_loaded = False

        if history_loaded:
            pass
            # The import_history() call already applied its current step to the canvas
            # and refreshed UI through _load_state.  We just need to ensure some
            # ancillary UI bits are correct.

            
            # Restore the original button states after history load
            self.toggle_control_points_button.setChecked(current_control_points_state)
            self.canvas.show_control_points = current_control_points_state
            self.toggle_shadow_button.setChecked(current_shadow_state)
            self.canvas.shadow_enabled = current_shadow_state
            
            # Update all strands' shadow drawing state to match the current button state
            for strand in self.canvas.strands:
                strand.should_draw_shadow = current_shadow_state
            
            # Clean up the preserve flags
            if hasattr(self.canvas, '_preserve_shadow_state'):
                delattr(self.canvas, '_preserve_shadow_state')
            if hasattr(self.canvas, '_preserve_control_points_state'):
                delattr(self.canvas, '_preserve_control_points_state')
            
            if hasattr(self.canvas, 'layer_panel'):
                self.canvas.layer_panel.refresh()
            self.canvas.update()            
            return

        # --- Fallback: load as simple snapshot (previous behaviour) ---
        try:
            strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points, shadow_overrides = load_strands(filename, self.canvas)

            # Clear existing canvas state
            self.canvas.strands = []
            self.canvas.groups = {}

            # Set canvas shadow state BEFORE applying loaded strands
            self.canvas.shadow_enabled = current_shadow_state

            # Clear the group panel's visual elements and internal state for a clean reload
            if hasattr(self.canvas, 'group_layer_manager') and hasattr(self.canvas.group_layer_manager, 'group_panel'):
                group_panel = self.canvas.group_layer_manager.group_panel

                # Clear visual elements
                if hasattr(group_panel, 'scroll_layout'):
                    while group_panel.scroll_layout.count():
                        child = group_panel.scroll_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()

                # Clear internal groups dictionary
                group_panel.groups = {}

                # Reset the JSON loading flag
                group_panel.groups_loaded_from_json = False
                pass

            # Apply the loaded strands and groups (will now use the correct shadow_enabled state)
            apply_loaded_strands(self.canvas, strands, groups, shadow_overrides)

            # Preserve the current button states instead of using loaded data
            self.toggle_control_points_button.setChecked(current_control_points_state)
            self.canvas.show_control_points = current_control_points_state
            
            self.toggle_shadow_button.setChecked(current_shadow_state)
            self.canvas.shadow_enabled = current_shadow_state
            
            # Update all strands' shadow drawing state to match the current button state
            for strand in self.canvas.strands:
                strand.should_draw_shadow = current_shadow_state
            
            # Clean up the preserve flags
            if hasattr(self.canvas, '_preserve_shadow_state'):
                delattr(self.canvas, '_preserve_shadow_state')
            if hasattr(self.canvas, '_preserve_control_points_state'):
                delattr(self.canvas, '_preserve_control_points_state')
            
            pass

            # Update the layer panel
            if hasattr(self.canvas, 'layer_panel'):
                self.canvas.layer_panel.refresh()

            # Force a canvas redraw
            self.canvas.update()

            pass

            # Reset undo history now because snapshot load discards previous history
            if undo_mgr:
                undo_mgr.clear_history(save_current=True)

            # Save initial state after loading
            self.layer_state_manager.save_initial_state()

        except Exception as e:
            pass
            # You might want to show an error dialog to the user here

    def show_layer_state_log(self):
        """Display the current layer state information."""
        # If button is not checked, just return
        if not self.layer_state_button.isChecked():
            return
            
        # Store the current mode before opening the dialog
        self._previous_state_mode = self.current_mode

        # Create a new dialog if it doesn't exist or isn't visible
        if not hasattr(self, '_layer_state_dialog') or not self._layer_state_dialog or not self._layer_state_dialog.isVisible():
            pass
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
            pass
            dialog.exec_()
        else:
            # If dialog exists and is visible, just bring it to front
            self._layer_state_dialog.raise_()
            self._layer_state_dialog.activateWindow()

    def handle_dialog_close(self, event):
        """Handle the dialog close event."""
        pass
        self.layer_state_button.setChecked(False)
        
        # Just accept the event - cleanup will be handled by on_layer_state_dialog_closed
        event.accept()

    def close_layer_state_dialog(self, dialog):
        """
        Closes the layer state dialog and ensures proper cleanup.
        """
        pass
        
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
        pass
        
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

    def set_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                return
            
            # --- SAFETY: Temporarily suppress lock mode behavior during mode switching ---
            lock_mode_was_active = False
            if hasattr(self, "layer_panel") and self.layer_panel and self.layer_panel.lock_mode:
                lock_mode_was_active = True
                self.layer_panel._suppress_lock_mode_temporarily = True

            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
            
            # Restore lock mode behavior if it was active
            if lock_mode_was_active:
                self.layer_panel._suppress_lock_mode_temporarily = False
        else:
            pass

    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
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
            pass

    def deselect_angle_adjust_button(self):
        # This method is no longer needed, but we'll keep it empty for compatibility
        self.unpress_angle_adjust_button()

    def set_mask_mode(self):
        # --- SAFETY: Temporarily suppress lock mode behavior during mode switching ---
        lock_mode_was_active = False
        if hasattr(self, "layer_panel") and self.layer_panel and self.layer_panel.lock_mode:
            lock_mode_was_active = True
            self.layer_panel._suppress_lock_mode_temporarily = True

        self.update_mode("mask")
        self.canvas.set_mode("mask")
        
        # Restore lock mode behavior if it was active
        if lock_mode_was_active:
            self.layer_panel._suppress_lock_mode_temporarily = False

    def handle_mask_created(self, strand1, strand2):
        pass

        # Verify that both strands exist in the canvas
        if strand1 not in self.canvas.strands or strand2 not in self.canvas.strands:
            pass
            return

        # Check if a mask already exists for these strands
        if self.canvas.mask_exists(strand1, strand2):
            pass
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

        pass

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
                
                # Create image 4x larger for maximum quality/crispness
                scale_factor = 4.0
                high_res_size = canvas_size * scale_factor
                
                # Create a transparent image at 4x resolution
                image = QImage(high_res_size, QImage.Format_ARGB32_Premultiplied)
                image.fill(Qt.transparent)
                
                # Create a painter for the image
                painter = QPainter(image)
                
                # Import RenderUtils for high-quality painter setup
                from render_utils import RenderUtils
                
                # Use the same high-quality settings as the canvas display
                RenderUtils.setup_painter(painter, enable_high_quality=True)
                
                # Scale everything up by 4x for high-resolution rendering
                painter.scale(scale_factor, scale_factor)
                
                # Apply zoom and pan transformation to match current canvas view
                canvas_center = QPointF(canvas_size.width() / 2, canvas_size.height() / 2)
                painter.translate(canvas_center)
                
                # Apply pan offset if it exists
                if hasattr(self.canvas, 'pan_offset_x') and hasattr(self.canvas, 'pan_offset_y'):
                    painter.translate(self.canvas.pan_offset_x, self.canvas.pan_offset_y)
                
                # Apply zoom if it's not 1.0
                if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor != 1.0:
                    painter.scale(self.canvas.zoom_factor, self.canvas.zoom_factor)
                
                painter.translate(-canvas_center)
                
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
                            strand.draw(painter, skip_painter_setup=True)
                    
                    # Draw the current strand if it exists
                    if self.canvas.current_strand:
                        self.canvas.current_strand.draw(painter, skip_painter_setup=True)
                    
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
                pass

    def handle_color_change(self, set_number, color):
        self.canvas.update_color_for_set(set_number, color)
        self.layer_panel.update_colors_for_set(set_number, color)

    def create_masked_layer(self, layer1_index, layer2_index):
        pass
        layer1 = self.canvas.strands[layer1_index]
        layer2 = self.canvas.strands[layer2_index]
        
        masked_strand = MaskedStrand(layer1, layer2)
        self.canvas.add_strand(masked_strand)
        
        button = self.layer_panel.add_masked_layer_button(layer1_index, layer2_index)
        button.color_changed.connect(self.handle_color_change)
        
        pass

        # Update the groups with the new masked strand
        pass
        self.layer_panel.group_layer_manager.update_groups_with_new_strand(masked_strand)
        
        self.canvas.update()
        self.update_mode(self.current_mode)

        pass

    def restore_selection(self):
        if self.layer_panel.last_selected_index is not None:
            self.select_strand(self.layer_panel.last_selected_index)

    def set_select_mode(self):
        # --- SAFETY: Temporarily suppress lock mode behavior during mode switching ---
        lock_mode_was_active = False
        if hasattr(self, "layer_panel") and self.layer_panel and self.layer_panel.lock_mode:
            lock_mode_was_active = True
            self.layer_panel._suppress_lock_mode_temporarily = True

        self.update_mode("select")
        self.canvas.set_mode("select")
        
        # Restore lock mode behavior if it was active
        if lock_mode_was_active:
            self.layer_panel._suppress_lock_mode_temporarily = False
        
    def update_mode(self, mode):
        # Safety guard: if someone tries to switch back to "angle_adjust" after the mode
        # has already been exited (canvas.is_angle_adjusting == False) we ignore it and
        # fall back to the previous/attach mode. This prevents the Angle/Length button
        # from getting re-checked visually after it has been deselected.
        if mode == "angle_adjust" and not getattr(self.canvas, "is_angle_adjusting", False):
            pass
            mode = getattr(self, "previous_mode", "attach")
        
        # Don't call confirm_adjustment here since it's handled by the angle adjustment dialog
        # The angle_adjust_mode itself calls update_mode when it finishes
        
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
        self.unpress_angle_adjust_button()

    def eventFilter(self, obj, event):
        """Filter events to catch Space key before it reaches child widgets (like buttons)."""
        if event.type() in (QEvent.KeyPress, QEvent.KeyRelease, QEvent.ShortcutOverride):
            if event.key() == Qt.Key_Space and event.modifiers() == Qt.NoModifier:
                # Check if the target widget (obj) belongs to this window
                if obj and hasattr(obj, 'window'):
                    target_window = obj.window()
                    if target_window is self:
                        # This event is for a widget in our window, intercept it
                        if event.type() == QEvent.KeyPress:
                            if hasattr(self, 'layer_panel') and hasattr(self.layer_panel, 'toggle_pan_mode'):
                                self.layer_panel.toggle_pan_mode()
                        event.accept()
                        return True  # Swallow all Space events so focused buttons never activate

        # Let other events pass through
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle key press events, specifically Escape to exit mask edit mode."""
        if event.key() == Qt.Key_Escape:
            # Check if we are in mask edit mode using the layer panel's flag
            if hasattr(self, 'layer_panel') and self.layer_panel.mask_editing:
                pass
                self.layer_panel.exit_mask_edit_mode()
                _ = translations[self.language_code]
                self.canvas.exit_mask_edit_mode()
                event.accept() # Indicate the event was handled
                return # Stop further processing

        # Debug key combination: Ctrl+Shift+D to clear canvas suppression flags
        elif event.key() == Qt.Key_D and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            if hasattr(self.canvas, 'clear_suppression_flags'):
                self.canvas.clear_suppression_flags()
                self.canvas.update()  # Force a repaint
                pass
                event.accept()
                return

        # Call the base class implementation for other keys
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.layer_panel.keyReleaseEvent(event)

    def set_attach_mode(self):
        # --- SAFETY: Temporarily suppress lock mode behavior during mode switching ---
        # This prevents the programmatic selection from being interpreted as a lock/unlock action
        # while preserving the lock mode state and locked layers
        lock_mode_was_active = False
        if hasattr(self, "layer_panel") and self.layer_panel and self.layer_panel.lock_mode:
            lock_mode_was_active = True
            # Temporarily suppress lock mode behavior without changing UI state
            self.layer_panel._suppress_lock_mode_temporarily = True

        # Now proceed with the normal Attach-Mode activation
        self.update_mode("attach")
        self.canvas.set_mode("attach")  # Explicitly set the canvas mode
        if self.canvas.last_selected_strand_index is not None:
            # Use emit_signal=False to prevent recursion back to layer_panel
            self.select_strand(self.canvas.last_selected_strand_index, emit_signal=False)
        
        # Restore lock mode behavior if it was active
        if lock_mode_was_active:
            self.layer_panel._suppress_lock_mode_temporarily = False
        
        # Ensure the attach button is checked and others are unchecked
        self.attach_button.setChecked(True)
        self.move_button.setChecked(False)
        self.rotate_button.setChecked(False)
        self.select_strand_button.setChecked(False)
        self.mask_button.setChecked(False)
        self.angle_adjust_button.setChecked(False)

    def set_move_mode(self):
        # --- SAFETY: Temporarily suppress lock mode behavior during mode switching ---
        lock_mode_was_active = False
        if hasattr(self, "layer_panel") and self.layer_panel and self.layer_panel.lock_mode:
            lock_mode_was_active = True
            self.layer_panel._suppress_lock_mode_temporarily = True

        self.update_mode("move")
        self.canvas.last_selected_strand_index = self.canvas.selected_strand_index
        
        # Highlight the selected attached strand immediately
        if self.canvas.selected_strand and isinstance(self.canvas.selected_strand, AttachedStrand):
            self.canvas.selected_attached_strand = self.canvas.selected_strand
            self.canvas.selected_attached_strand.start_selected = True
        else:
            self.canvas.selected_attached_strand = None
        
        # Restore lock mode behavior if it was active
        if lock_mode_was_active:
            self.layer_panel._suppress_lock_mode_temporarily = False
        
        self.canvas.update()  # Force an update of the canvas


    def create_new_strand(self):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = self.canvas.default_strand_color
        
        self.canvas.start_new_strand_mode(set_number)
        
        # Ensure UI buttons are synchronized with the zoom-consistent state
        self._sync_mode_buttons_for_new_strand()
        
        pass
        
        self.layer_state_manager.save_current_state()

    def _sync_mode_buttons_for_new_strand(self):
        """
        Synchronize UI buttons to ensure consistent state during new strand creation
        regardless of zoom level. Also saves current button states to restore later.
        """
        # Save current button states for restoration later
        self._save_button_states()
        
        # Keep control points button state as-is (don't force it OFF during creation)
        # Control points are helpful during strand creation for positioning
        # if hasattr(self, 'toggle_control_points_button'):
        #     self.toggle_control_points_button.setChecked(False)
        
        # Ensure angle adjust button is OFF
        if hasattr(self, 'angle_adjust_button'):
            self.angle_adjust_button.setChecked(False)
        
        # Ensure attach mode button is OFF
        if hasattr(self, 'attach_button'):
            self.attach_button.setChecked(False)
        
        # Ensure move mode button is OFF
        if hasattr(self, 'move_button'):
            self.move_button.setChecked(False)
        
        # Ensure mask mode button is OFF
        if hasattr(self, 'mask_button'):
            self.mask_button.setChecked(False)
        
        # Ensure rotate mode button is OFF
        if hasattr(self, 'rotate_button'):
            self.rotate_button.setChecked(False)
        
        pass

    def _save_button_states(self):
        """Save current button states for restoration after strand creation."""
        if not hasattr(self, '_pre_creation_button_states'):
            self._pre_creation_button_states = {}
        
        # Save button states (except control points which we preserve during creation)
        # Control points button state is preserved as-is during strand creation
        # if hasattr(self, 'toggle_control_points_button'):
        #     self._pre_creation_button_states['control_points'] = self.toggle_control_points_button.isChecked()
        if hasattr(self, 'angle_adjust_button'):
            self._pre_creation_button_states['angle_adjust'] = self.angle_adjust_button.isChecked()
        if hasattr(self, 'attach_button'):
            self._pre_creation_button_states['attach'] = self.attach_button.isChecked()
        if hasattr(self, 'move_button'):
            self._pre_creation_button_states['move'] = self.move_button.isChecked()
        if hasattr(self, 'mask_button'):
            self._pre_creation_button_states['mask'] = self.mask_button.isChecked()
        if hasattr(self, 'rotate_button'):
            self._pre_creation_button_states['rotate'] = self.rotate_button.isChecked()
        
        pass

    def _restore_button_states(self):
        """Restore button states that were saved before strand creation."""
        if not hasattr(self, '_pre_creation_button_states') or not self._pre_creation_button_states:
            pass
            return
        
        states = self._pre_creation_button_states
        
        # Restore button states (control points were preserved, so no need to restore)
        # Control points button state was never changed during strand creation
        # if hasattr(self, 'toggle_control_points_button') and 'control_points' in states:
        #     self.toggle_control_points_button.setChecked(states['control_points'])
        if hasattr(self, 'angle_adjust_button') and 'angle_adjust' in states:
            self.angle_adjust_button.setChecked(states['angle_adjust'])
        if hasattr(self, 'attach_button') and 'attach' in states:
            self.attach_button.setChecked(states['attach'])
        if hasattr(self, 'move_button') and 'move' in states:
            self.move_button.setChecked(states['move'])
        if hasattr(self, 'mask_button') and 'mask' in states:
            self.mask_button.setChecked(states['mask'])
        if hasattr(self, 'rotate_button') and 'rotate' in states:
            self.rotate_button.setChecked(states['rotate'])
        
        # Clear saved states
        self._pre_creation_button_states = {}
        
        pass

    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
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
            pass

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
                pass

                # Find the correct strand in the canvas based on the layer name
                strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
                
                if strand_index is not None:
                    strand = self.canvas.strands[strand_index]
                    pass

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
                                pass

                    # Remove the strands and masks
                    for s in strands_to_remove + masks_to_delete:
                        self.canvas.remove_strand(s)
                        pass

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

                    pass
                else:
                    pass
            else:
                pass

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
            # Attempt to export the full undo/redo history so that it can be
            # restored on load.  If that fails for any reason we fall back to
            # saving just the current canvas state (previous behaviour).
            undo_mgr = getattr(self.layer_panel, 'undo_redo_manager', None)
            if undo_mgr and undo_mgr.export_history(filename):
                pass
            else:
                # Fallback: save only the current snapshot
                groups = self.group_layer_manager.get_group_data()
                pass
                save_strands(self.canvas.strands, groups, filename, self.canvas)
                pass
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
        # --- SAFETY: Temporarily suppress lock mode behavior during mode switching ---
        lock_mode_was_active = False
        if hasattr(self, "layer_panel") and self.layer_panel and self.layer_panel.lock_mode:
            lock_mode_was_active = True
            self.layer_panel._suppress_lock_mode_temporarily = True

        self.update_mode("rotate")
        self.canvas.set_mode("rotate")
        
        # Restore lock mode behavior if it was active
        if lock_mode_was_active:
            self.layer_panel._suppress_lock_mode_temporarily = False

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
        self.layer_panel.set_language(language_code)

        if self.settings_dialog:
            self.settings_dialog.language_code = language_code

        # Update translations in UI elements
        self.translate_ui()
        self.canvas.update_translations()
        self.layer_panel.translate_ui()
        if self.settings_dialog.isVisible():
            self.settings_dialog.update_translations()

        pass
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
        self.toggle_shadow_button.setText(_['toggle_shadow'])

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
        Normal logic: checking the button shows control points, unchecking hides them.
        """
        # Set the canvas state to match the button state
        self.canvas.show_control_points = checked
        
        # Call the canvas toggle_control_points method to ensure undo/redo state is saved
        # But avoid double-toggling by temporarily setting the state first
        current_state = self.canvas.show_control_points
        if hasattr(self.canvas, 'toggle_control_points'):
            # Temporarily prevent the toggle from changing the state since we already set it
            # We just want the undo/redo save functionality
            if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
                # Force immediate save to capture this state change
                self.canvas.undo_redo_manager._last_save_time = 0
                self.canvas.undo_redo_manager.save_state()
                pass
        
        # Update all strands' control points visibility
        for strand in self.canvas.strands:
            if hasattr(strand, 'show_control_points'):
                strand.show_control_points = current_state
        
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
