# src/layer_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QScrollArea, QLabel, QSplitter, QInputDialog, QMenu  # Add QMenu here
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QStandardPaths, QMimeData  ,QRect# Added QMimeData
from PyQt5.QtGui import QColor, QPalette, QDrag # Added QDrag
# --- Import Correct Drag/Drop Event Types --- 
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QPainter, QPen # Added Painter/Pen
# --- End Import ---
from functools import partial
import logging
from masked_strand import MaskedStrand
from translations import translations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QLabel,
    QInputDialog, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import logging
from functools import partial
from splitter_handle import SplitterHandle
from numbered_layer_button import NumberedLayerButton
from group_layers import GroupPanel, GroupLayerManager
from PyQt5.QtWidgets import QWidget, QPushButton  # Example widget imports
from PyQt5.QtGui import QPalette, QColor  # Added QPalette and QColor imports
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint  # Add QPoint here
from translations import translations
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QFontMetrics, QColor
from PyQt5.QtWidgets import QPushButton, QStyle
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleOption

# Import StrokeTextButton from undo_redo_manager instead of dedicated file
from undo_redo_manager import StrokeTextButton, setup_undo_redo
import os # Import os for path manipulation
import sys # Import sys for platform check

class LayerSelectionDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Layers for Group")
        self.layout = QVBoxLayout(self)
        
        self.layer_list = QListWidget()
        for layer in layers:
            item = QListWidgetItem(layer)
            item.setCheckState(Qt.Unchecked)
            self.layer_list.addItem(item)
        
        self.layout.addWidget(self.layer_list)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        
        # Add new signal for mask editing
        self.edit_mask_requested = pyqtSignal(int)  # Signal when mask editing is requested
        
        # Create and configure the mask edit label with center alignment
        self.mask_edit_label = QLabel()
        self.mask_edit_label.setAlignment(Qt.AlignCenter)  # Center align the text
        self.mask_edit_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.9);
                padding: 15px;
                border-radius: 5px;
                font-weight: bold;
                color: #333333;
                text-align: center;
                min-width: 250px;  /* Ensure minimum width for centering */
                qproperty-alignment: AlignCenter;  /* Force center alignment */
                white-space: pre-line;  /* Preserve newlines while wrapping text */
            }
        """)
        self.mask_edit_label.hide()
        
        # Add the label to the layout with proper alignment
        self.left_layout.addWidget(self.mask_edit_label, 0, Qt.AlignHCenter | Qt.AlignTop)
    def get_selected_layers(self):
        return [self.layer_list.item(i).text() for i in range(self.layer_list.count()) 
                if self.layer_list.item(i).checkState() == Qt.Checked]

# --- Custom Widget for Drop Target Area ---
class DropTargetWidget(QWidget):
    def __init__(self, layer_panel, parent=None):
        super().__init__(parent)
        self.layer_panel = layer_panel # Reference to the main panel
        self.setAcceptDrops(True)
        self._drag_indicator_y = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        self.layer_panel.dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        self.layer_panel.dragMoveEvent(event)
        # Calculate indicator position based on event position within this widget
        self._drag_indicator_y = self.layer_panel.calculate_drop_indicator_y(event.pos())
        self.update() # Trigger repaint to show indicator

    def dragLeaveEvent(self, event):
        self.layer_panel.dragLeaveEvent(event)
        self._drag_indicator_y = None
        self.update() # Trigger repaint to hide indicator

    def dropEvent(self, event: QDropEvent):
        self.layer_panel.dropEvent(event)
        self._drag_indicator_y = None
        self.update()  # Trigger repaint to hide indicator
        # Avoid a second immediate refresh on macOS (LayerPanel.dropEvent already schedules one)
        if sys.platform != 'darwin':
            self.layer_panel.refresh()
        else:
            QTimer.singleShot(0, self.layer_panel.refresh)
        

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drag_indicator_y is not None:
            painter = QPainter(self)
            pen = QPen(QColor(0, 120, 215), 2, Qt.SolidLine) # Blue indicator line
            painter.setPen(pen)
            painter.drawLine(0, self._drag_indicator_y, self.width(), self._drag_indicator_y)
# --- End Custom Widget ---


class LayerPanel(QWidget):
    # Custom signals for various events
    new_strand_requested = pyqtSignal(int, QColor)  # Signal when a new strand is requested
    strand_selected = pyqtSignal(int)  # Signal when a strand is selected
    deselect_all_requested = pyqtSignal()  # Signal to deselect all strands
    color_changed = pyqtSignal(int, QColor)  # Signal when a strand's color is changed
    masked_layer_created = pyqtSignal(int, int)  # Signal when a masked layer is created
    draw_names_requested = pyqtSignal(bool)  # Signal to toggle drawing of strand names
    masked_mode_entered = pyqtSignal()  # Signal when masked mode is entered
    masked_mode_exited = pyqtSignal()  # Signal when masked mode is exited
    lock_layers_changed = pyqtSignal(set, bool)  # Signal when locked layers change
    strand_deleted = pyqtSignal(int)  # Signal for strand deletion
    layer_order_changed = pyqtSignal(list) # Signal when layer order changes

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.parent_window = parent
        self.language_code = parent.language_code if parent else 'en'
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.last_selected_index = None
        
        # Determine the base path for settings and temp files
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':  # macOS
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            self.base_path = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            self.base_path = program_data_dir # AppDataLocation already includes the app name
        logging.info(f"LayerPanel: Base path for data determined as: {self.base_path}")

        self.group_layer_manager = GroupLayerManager(parent=parent, layer_panel=self, canvas=self.canvas)

        # Create left panel (existing layer panel)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # **Add the splitter handle at the top of the left layout**
        self.handle = SplitterHandle(self)
        self.left_layout.addWidget(self.handle)

        # **Add the refresh button below the splitter handle**
        # Create top panel for the refresh button
        self.top_panel = QWidget()
        top_layout = QHBoxLayout(self.top_panel)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setAlignment(Qt.AlignLeft)

        # Create the refresh button
        self.refresh_button = StrokeTextButton("↻")
        self.refresh_button.clicked.connect(self.refresh_layers)

        # Add the refresh button to the top layout
        top_layout.addWidget(self.refresh_button)
        
        # Add top_panel to left_layout below the splitter handle
        self.left_layout.addWidget(self.top_panel)
        
        # Setup undo/redo manager and buttons AFTER top_panel is added to the layout
        # Pass the determined base_path to setup_undo_redo
        self.undo_redo_manager = setup_undo_redo(self.canvas, self, self.base_path)
        
        # Create a second row for zoom buttons
        self.zoom_panel = QWidget()
        zoom_layout = QHBoxLayout(self.zoom_panel)
        zoom_layout.setContentsMargins(5, 0, 5, 5)  # No top margin since it's below the first row
        zoom_layout.setAlignment(Qt.AlignLeft)
        
        # Create zoom in button
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedSize(40, 40)
        self.zoom_in_button.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;  /* Yellowish color */
                color: black;
                font-weight: bold;
                font-size: 24px;
                border: 1px solid #B8860B;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #FFA500;  /* Darker yellow/orange on hover */
                border: 2px solid #B8860B;
            }
            QPushButton:pressed {
                background-color: #FF8C00;  /* Even darker on press */
                border: 2px solid #8B6914;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        self.zoom_in_button.clicked.connect(self.canvas.zoom_in)
        
        # Create zoom out button
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setFixedSize(40, 40)
        self.zoom_out_button.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;  /* Yellowish color */
                color: black;
                font-weight: bold;
                font-size: 24px;
                border: 1px solid #B8860B;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #FFA500;  /* Darker yellow/orange on hover */
                border: 2px solid #B8860B;
            }
            QPushButton:pressed {
                background-color: #FF8C00;  /* Even darker on press */
                border: 2px solid #8B6914;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        self.zoom_out_button.clicked.connect(self.canvas.zoom_out)
        
        # Create pan button
        self.pan_button = QPushButton("🖐")  # Using a more modern hand emoji
        self.pan_button.setFixedSize(40, 40)
        self.pan_button.setCheckable(True)  # Make it toggleable
        self.pan_button.clicked.connect(self.toggle_pan_mode)
        self.pan_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;  /* Dark red color */
                color: white;
                font-weight: bold;
                font-size: 24px;
                border: 1px solid #4B0000;
                border-radius: 20px;
                padding: 0px;
                margin: 0px;
                min-width: 40px;
                min-height: 40px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #A52A2A;  /* Slightly lighter red on hover */
                border: 2px solid #4B0000;
            }
            QPushButton:pressed {
                background-color: #400000;  /* Much darker red when pressed */
                border: 2px solid #4B0000;
            }
            QPushButton:checked {
                background-color: #400000;  /* Much darker red when active */
                border: 2px solid #4B0000;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        
        # Add buttons to zoom layout
        zoom_layout.addWidget(self.zoom_in_button)
        zoom_layout.addWidget(self.zoom_out_button)
        zoom_layout.addWidget(self.pan_button)
        
        # Add zoom panel to left layout below the top panel
        self.left_layout.addWidget(self.zoom_panel)

        # Create scrollable area for layer buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Use the custom DropTargetWidget
        self.scroll_content = DropTargetWidget(self)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        # Ensure consistent vertical spacing between layer buttons across platforms
        self.scroll_layout.setSpacing(2)  # Small, uniform gap
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        self.scroll_area.setWidget(self.scroll_content)
        # --- Drag and Drop is now handled by DropTargetWidget ---
        # self.scroll_content.setAcceptDrops(True)
        # self.scroll_content.dragEnterEvent = self.dragEnterEvent
        # self.scroll_content.dragMoveEvent = self.dragMoveEvent
        # self.scroll_content.dropEvent = self.dropEvent
        # --- End Drag and Drop ---

        # Add the scroll area to the left layout
        self.left_layout.addWidget(self.scroll_area)

        # Create bottom panel for control buttons
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        # Ensure consistent gap between control buttons across platforms
        bottom_layout.setSpacing(2)
        
        # Draw Names button
        self.draw_names_button = QPushButton("Draw Names")
        self.draw_names_button.setStyleSheet("""
            QPushButton {
                background-color: #e07bdb;
                font-weight: bold;
                color: black;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px 10px; /* Added padding */
            }
            QPushButton:hover {
                background-color: #e694e2; /* lighter on hover */
            }
            QPushButton:pressed {
                background-color: #ba62b5; /* darker on press */
            }
        """)
        self.draw_names_button.clicked.connect(self.request_draw_names)

        # Lock Layers button
        self.lock_layers_button = QPushButton("Lock Layers")
        self.lock_layers_button.setStyleSheet("""
            QPushButton {
                background-color: orange;
                font-weight: bold;
                color: black;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px 10px; /* Added padding */
            }
            QPushButton:hover {
                background-color: #FFB84D; /* lighter on hover */
            }
            QPushButton:pressed {
                background-color: #E69500; /* darker on press */
            }
        """)
        self.lock_layers_button.setCheckable(True)
        self.lock_layers_button.clicked.connect(self.toggle_lock_mode)

        # Add New Strand button
        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("""
            QPushButton {
                background-color: lightgreen;
                font-weight: bold;
                color: black;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px 10px; /* Added padding */
            }
            QPushButton:hover {
                background-color: #BFFFBF; /* even lighter on hover */
            }
            QPushButton:pressed {
                background-color: #7BBF7B; /* darker on press */
            }
        """)
        self.add_new_strand_button.clicked.connect(self.request_new_strand)

        # Delete Strand button
        self.delete_strand_button = QPushButton("Delete Strand (beta)")
        self.delete_strand_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                font-weight: bold;
                color: black;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px 10px; /* Added padding */
            }
            QPushButton:hover {
                background-color: #FF4C4C; /* Lighter red on hover */
            }
            QPushButton:pressed {
                background-color: #FF0000; /* Darker red on click */
            }
        """)
        self.delete_strand_button.setEnabled(False)
        self.delete_strand_button.clicked.connect(self.request_delete_strand)

        # Deselect All button
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setStyleSheet("""
            QPushButton {
                background-color: #76acdc;
                font-weight: bold;
                color: black;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px 10px; /* Added padding */
            }
            QPushButton:hover {
                background-color: #9bc2e6; /* lighter on hover */
            }
            QPushButton:pressed {
                background-color: #5890c0; /* darker on press */
            }
        """)
        self.deselect_all_button.clicked.connect(self.deselect_all)

        # Add buttons to bottom panel in the desired order
        bottom_layout.addWidget(self.draw_names_button)
        bottom_layout.addWidget(self.lock_layers_button)
        bottom_layout.addWidget(self.add_new_strand_button)
        bottom_layout.addWidget(self.delete_strand_button)
        bottom_layout.addWidget(self.deselect_all_button)

        # Add scroll area and bottom panel to left layout
        self.left_layout.addWidget(self.scroll_area)
        self.left_layout.addWidget(bottom_panel)

        # Create right panel (group panel)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Create GroupLayerManager
        self.group_layer_manager = GroupLayerManager(parent=self, layer_panel=self, canvas=self.canvas)

        # Add the create_group_button and group_panel to right layout with left alignment
        # Create a container widget for the create_group_button to position it left
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(5, 2, 5, 2)  # Reduce padding: left, top, right, bottom
        button_layout.addWidget(self.group_layer_manager.create_group_button, 0, Qt.AlignLeft)  # Left align the button
        button_layout.addStretch()  # Right spacer only
        
        self.right_layout.addWidget(button_container)
        self.right_layout.addWidget(self.group_layer_manager.group_panel)

        # Remove fixed width from left panel so it can expand
        # self.left_panel.setFixedWidth(200)
        
        # Set a fixed width for the right panel
        self.right_panel.setFixedWidth(250)  # Set actual fixed width in pixels
        # Configure the right panel (group panel)
        self.right_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        # Configure the left panel to expand horizontally
        self.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Set minimum width for left panel so it starts with reasonable width extending 
        
        # Configure the overall LayerPanel to expand leftward
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create a splitter to separate left and right panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)

        # Disable resizing by setting the splitter handle to non-movable
        self.splitter.setChildrenCollapsible(False)  # Prevent collapsing
        self.splitter.setStretchFactor(0, 1)  # Left panel can stretch
        self.splitter.setStretchFactor(1, 0)  # Right panel does not stretch
        self.splitter.handle(1).setEnabled(False)  # Disable the splitter handle

        # Add the splitter to the main layout
        self.layout.addWidget(self.splitter)

        # Note: setSizes() doesn't work with Fixed size policy, use setFixedWidth() above instead

        # Initialize variables for managing layers
        self.layer_buttons = []  # List to store layer buttons
        self.current_set = 1  # Current set number
        self.set_counts = {}
        # Use canvas default strand color if available, otherwise fallback to purple
        default_color = QColor(200, 170, 230, 255)  # Fallback
        if canvas and hasattr(canvas, 'default_strand_color'):
            default_color = canvas.default_strand_color
        self.set_colors = {1: default_color}  # Dictionary to store colors for each set

        # Initialize masked mode variables
        self.masked_mode = False
        self.first_masked_layer = None

        # Create notification label
        self.notification_label = QLabel()
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.notification_label.hide()  # Hide initially to avoid extra spacing
        self.left_layout.addWidget(self.notification_label)

        # Initialize lock mode variables
        self.lock_mode = False
        self.locked_layers = set()
        self.previously_locked_layers = set()

        # Initialize should_draw_names attribute
        self.should_draw_names = False

        # Initialize groups
        self.groups = {}

        # Add flag to track if we're currently in mask editing mode
        self.mask_editing = False
        
        # Add a label to show mask editing status
        self.mask_edit_label = QLabel("")
        self.mask_edit_label.setStyleSheet("color: red; font-weight: bold;")
        self.left_layout.addWidget(self.mask_edit_label)
        self.mask_edit_label.hide()

        logging.info("LayerPanel initialized")

    def refresh_layers(self):
        """Refresh the drawing of the layers with zero visual flicker."""
        logging.info("refresh_layers called, redirecting to refresh()")
        self.refresh()
        # Reset canvas zoom and pan to original view
        self.canvas.reset_zoom()

    def create_layer_button(self, index, strand, count):
        """Create a layer button for the given strand."""
        button = NumberedLayerButton(strand.layer_name, count, strand.color)
        button.clicked.connect(partial(self.select_layer, index))
        button.color_changed.connect(self.on_color_changed)

        # -------------------------------------------------------------------------
        # Keep the stylesheet application
        original_hex = strand.color.name()  # Convert the QColor to hex string
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {original_hex};
                border-radius: 4px;
                border: 1px solid #888;
                color: black;
            }}
            QPushButton:hover {{
                background-color: #E0E0E0; /* Lighter on hover */
            }}
            QPushButton:pressed {{
                background-color: #C0C0C0; /* Darker on press */
            }}
            QPushButton:checked {{
                background-color: {original_hex}; /* Revert to original color when released */
            }}
        """)
        # -------------------------------------------------------------------------

        # --- COMMENT OUT Context menu setup (Handled by NumberedLayerButton.__init__) ---
        # Ensure the button handles its own context menu to avoid conflicts
        # button.setContextMenuPolicy(Qt.CustomContextMenu)
        # button.customContextMenuRequested.connect(
        #     lambda pos, idx=index: self.show_layer_context_menu(idx, pos)
        # )
        # --- END COMMENT OUT ---

        # Keep border color setting for MaskedStrand
        if isinstance(strand, MaskedStrand):
            button.set_border_color(strand.second_selected_strand.color)

        # Set initial hidden state
        button.set_hidden(strand.is_hidden)

        return button

    def set_theme(self, theme_name):
        """Set the theme of the layer panel without altering child widget styles."""
        # NEW: store current theme – used to style context menus dynamically
        self.current_theme = theme_name

        if theme_name == "dark":
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor("#2C2C2C"))
            palette.setColor(QPalette.WindowText, QColor("black"))
            self.setPalette(palette)
            self.setAutoFillBackground(True)
            # Update button styles for dark theme
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: 1px solid #888;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)
            # Apply theme to refresh button
            self.refresh_button.set_theme(theme_name)
            # Apply theme to undo/redo buttons
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                self.undo_redo_manager.set_theme(theme_name)
            # Similarly update other buttons if necessary

        elif theme_name == "light":
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor("#FFFFFF"))
            palette.setColor(QPalette.WindowText, QColor("black"))
            self.setPalette(palette)
            self.setAutoFillBackground(True)
            # Update button styles for light theme
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: 1px solid #888;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)
            # Apply theme to refresh button
            self.refresh_button.set_theme(theme_name)
            # Apply theme to undo/redo buttons
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                self.undo_redo_manager.set_theme(theme_name)
            # Similarly update other buttons if necessary

        elif theme_name == "default":
            # Clear any custom palettes to use the default theme
            self.setPalette(self.style().standardPalette())
            self.setAutoFillBackground(False)
            # Reset button styles to default
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: 1px solid #888;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)
            # Apply theme to refresh button
            self.refresh_button.set_theme(theme_name)
            # Apply theme to undo/redo buttons
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                self.undo_redo_manager.set_theme(theme_name)
            # Similarly reset other buttons if necessary

        else:
            # Handle unknown themes by reverting to default
            self.setPalette(self.style().standardPalette())
            self.setAutoFillBackground(False)
            # Reset button styles to default
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: 1px solid #888;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)
            # Apply theme to refresh button
            self.refresh_button.set_theme("default")
            # Apply theme to undo/redo buttons
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                self.undo_redo_manager.set_theme("default")
            # Similarly reset other buttons if necessary

        self.mask_edit_label.hide() # Hide initially

        # Connect the signal from the dialog to the handler in LayerPanel
        # self.layer_selection_dialog.edit_mask_requested.connect(self.request_edit_mask) # Moved from dialog init

    # NEW: helper method to provide a context menu style sheet based on the current theme
    def get_context_menu_stylesheet(self):
        if hasattr(self, "current_theme") and self.current_theme == "dark":
            # For dark theme: normal state is dark background with white text,
            # hovered items are light (#F0F0F0) with dark text.
            return "QMenu { background-color: #333333; color: white; } QMenu::item:selected { background-color: #F0F0F0; color: black; }"
        else:
            # For light/default themes: normal state is light background with dark text,
            # hovered items are dark (#333333) with white text.
            return "QMenu { background-color: #F0F0F0; color: black; } QMenu::item:selected { background-color: #333333; color: white; }"

    def show_layer_context_menu(self, strand_index, position):
        """
        Show context menu for layer buttons, with translations.
        Handles MaskedStrand specific actions and common actions like Hide/Show.
        """
        if strand_index < 0 or strand_index >= len(self.canvas.strands):
            logging.warning(f"show_layer_context_menu called with invalid index: {strand_index}")
            return

        strand = self.canvas.strands[strand_index]
        menu = QMenu(self)
        menu.setStyleSheet(self.get_context_menu_stylesheet())
        _ = translations[self.language_code]

        # --- Add actions specific to MaskedStrand ---
        if isinstance(strand, MaskedStrand):
            edit_action = menu.addAction(_['edit_mask'])
            edit_action.triggered.connect(
                lambda: self.on_edit_mask_click(menu, strand_index)
            )

            reset_action = menu.addAction(_['reset_mask'])
            reset_action.triggered.connect(
                lambda: (self.reset_mask(strand_index), menu.close())
            )
        # --- End MaskedStrand specific actions ---

        button = self.layer_buttons[strand_index]
        # Use button's mapToGlobal to get correct position
        global_pos = button.mapToGlobal(position)
        menu.exec_(global_pos)

    def on_edit_mask_click(self, menu, strand_index):
        """
        Disconnect context-menu for that button, close the menu,
        then switch to mask-edit mode.
        """
        # Close the QMenu:
        menu.close()
        # menu.hide() # close() should be sufficient

        # Disconnect the old context-menu request from this button:
        # No need to disconnect, context menu is recreated each time

        # Now actually enter mask-edit mode:
        self.request_edit_mask(strand_index)

    # --- NEW: Method to toggle visibility ---
    def toggle_layer_visibility(self, strand_index):
        """Toggles the visibility of the strand at the given index."""
        if 0 <= strand_index < len(self.canvas.strands):
            strand = self.canvas.strands[strand_index]
            strand.is_hidden = not strand.is_hidden
            logging.info(f"Toggled visibility for strand {strand.layer_name} to hidden={strand.is_hidden}")
            self.canvas.update() # Redraw canvas to reflect the change

            # Optional: Update button appearance
            button = self.layer_buttons[strand_index]
            if strand.is_hidden:
                # Add visual indication like strikethrough or different style
                # For simplicity, let's just slightly dim it for now
                button.setStyleSheet(button.styleSheet() + " QPushButton { color: gray; font-style: italic; }")
            else:
                # Restore original style - this might need refinement
                # It's safer to store the original stylesheet and restore it.
                # For now, we'll try removing the added style (might not be robust)
                current_style = button.styleSheet()
                new_style = current_style.replace(" QPushButton { color: gray; font-style: italic; }", "")
                button.setStyleSheet(new_style)
                # A better approach would be to fully reconstruct the style based on theme/state
                self.refresh_layers() # Refresh might be easier to restore styles correctly
            button.set_hidden(strand.is_hidden) # Call the button's method

            self.canvas.update() # Redraw canvas to reflect the change

        else:
            logging.warning(f"toggle_layer_visibility called with invalid index: {strand_index}")
    # --- END NEW ---
    
    def toggle_pan_mode(self):
        """Toggle pan mode on/off"""
        if self.canvas:
            self.canvas.toggle_pan_mode()
            # Update button state based on canvas pan mode
            self.pan_button.setChecked(self.canvas.pan_mode)
            # Update the button icon to indicate pan mode
            if self.canvas.pan_mode:
                self.pan_button.setText("✊")  # Closed hand emoji when active
            else:
                self.pan_button.setText("🖐")  # Open hand emoji when inactive

    def reset_mask(self, strand_index):
        """Reset the mask to its original intersection."""
        logging.info(f"[LayerPanel] reset_mask called for strand_index {strand_index}")
        if self.canvas:
            logging.info(f"Resetting mask for strand {strand_index}")
            self.canvas.reset_mask(strand_index)

    def translate_ui(self):
        """Update the UI texts to the selected language."""
        _ = translations[self.language_code]
        # Update any UI elements with new translations
        self.draw_names_button.setText(_['draw_names'])
        self.lock_layers_button.setText(_['lock_layers'])
        self.add_new_strand_button.setText(_['add_new_strand'])
        self.delete_strand_button.setText(_['delete_strand'])
        self.deselect_all_button.setText(_['deselect_all'])
        # Update other text elements as needed

        # Update the GroupLayerManager
        if self.group_layer_manager:
            self.group_layer_manager.language_code = self.language_code
            self.group_layer_manager.update_translations()

    def request_draw_names(self):
        self.should_draw_names = not self.should_draw_names
        self.draw_names_requested.emit(self.should_draw_names)


    def create_group(self):
        group_name, ok = QInputDialog.getText(self, "Create Group", "Enter group name:")
        if ok and group_name:
            # Filter out masked layers
            layers = [button.text() for button in self.layer_buttons if not self.is_masked_layer(button)]
            dialog = LayerSelectionDialog(layers, self)
            if dialog.exec_():
                selected_layers = dialog.get_selected_layers()
                for layer in selected_layers:
                    self.group_layer_manager.group_panel.add_layer_to_group(layer, group_name)

    def is_masked_layer(self, button):
        # Check if the button text follows the masked layer naming convention
        index = self.layer_buttons.index(button)
        return isinstance(self.canvas.strands[index], MaskedStrand)


    def add_group(self, group_name, layers):
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_label = QLabel(group_name)
        group_layout.addWidget(group_label)
        
        for layer in layers:
            layer_label = QLabel(layer)
            group_layout.addWidget(layer_label)
        
        self.group_scroll_layout.addWidget(group_widget)
        self.groups[group_name] = layers
        
        # Update the group display
        self.update_group_display(group_name)

    def update_group_display(self, group_name):
        if group_name in self.groups:
            group_widget = self.group_scroll_layout.itemAt(list(self.groups.keys()).index(group_name)).widget()
            group_layout = group_widget.layout()
            
            # Update the group label
            group_label = group_layout.itemAt(0).widget()
            group_label.setText(f"{group_name} ({len(self.groups[group_name])})")
            
            # Clear existing layer labels
            for i in reversed(range(group_layout.count())):
                if i > 0:  # Keep the group label
                    group_layout.itemAt(i).widget().setParent(None)
            
            # Add updated layer labels
            for layer in self.groups[group_name]:
                layer_label = QLabel(layer)
                group_layout.addWidget(layer_label)

    def request_draw_names(self):
        """Toggle the drawing of strand names and emit the corresponding signal."""
        self.should_draw_names = not self.should_draw_names
        self.draw_names_requested.emit(self.should_draw_names)

    def keyPressEvent(self, event):
        """Handle key press events, specifically for entering masked mode."""
        pass

    def keyReleaseEvent(self, event):
        """Handle key release events, specifically for exiting masked mode."""
        if event.key() == Qt.Key_Control:
            self.exit_masked_mode()

    def enter_masked_mode(self):
        """Enter masked mode, update UI, and emit relevant signal."""
        self.masked_mode = True
        self.first_masked_layer = None
        self.last_selected_index = self.get_selected_layer()
        for button in self.layer_buttons:
            button.set_masked_mode(True)
            button.setChecked(False)
        self.masked_mode_entered.emit()

    def exit_masked_mode(self):
        """Exit masked mode, update UI, and emit relevant signal."""
        self.masked_mode = False
        self.first_masked_layer = None
        for button in self.layer_buttons:
            button.set_masked_mode(False)
        self.masked_mode_exited.emit()
        self.notification_label.clear()

        # Save state after mask editing is complete
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            logging.info("Saving state after mask edit completed")
            self.undo_redo_manager.save_state()

        # --- ADD: Save state after exiting mask edit mode ---
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            # Force a save by resetting the last save time so the identical-state and timing checks are bypassed
            self.undo_redo_manager._last_save_time = 0
            logging.info("Saving state after exiting mask edit mode")
            self.undo_redo_manager.save_state()
        # --- END ADD ---

    def toggle_lock_mode(self):
        """Toggle lock mode on/off and update UI accordingly."""
        self.lock_mode = self.lock_layers_button.isChecked()
        if self.lock_mode:
            self.lock_layers_button.setText("Exit Lock Mode")
            self.notification_label.setText("Select layers to lock/unlock")
            self.locked_layers = self.previously_locked_layers.copy()
            self.deselect_all_button.setText("Clear All Locks")
        else:
            self.lock_layers_button.setText("Lock Layers")
            self.notification_label.setText("Exited lock mode")
            self.previously_locked_layers = self.locked_layers.copy()
            self.locked_layers.clear()
            self.deselect_all_button.setText("Deselect All")

        self.update_layer_buttons_lock_state()
        self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
        
        # Save state for undo/redo when entering/exiting lock mode
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            # Force save by temporarily clearing the last save time to bypass timing check
            old_last_save_time = getattr(self.undo_redo_manager, '_last_save_time', 0)
            self.undo_redo_manager._last_save_time = 0
            self.undo_redo_manager.save_state()
            # Restore the last save time
            self.undo_redo_manager._last_save_time = old_last_save_time

    def update_layer_buttons_lock_state(self):
        """Update the lock state and attachability of all layer buttons."""
        for i, button in enumerate(self.layer_buttons):
            if isinstance(button, NumberedLayerButton):
                button.set_locked(i in self.locked_layers)
                button.set_selectable(self.lock_mode)
                
                # Set attachability based on whether the strand has free sides
                if i < len(self.canvas.strands):
                    strand = self.canvas.strands[i]
                    button.set_attachable(any(not circle for circle in strand.has_circles))
                else:
                    button.set_attachable(False)

    def select_layer(self, index, emit_signal=True):
        """
        Handle layer selection based on current mode (normal, masked, or lock).
        
        Args:
            index (int): The index of the layer to select.
            emit_signal (bool): Whether to emit the selection signal.
        """
        # Block layer selection if we're in mask editing mode
        if self.mask_editing:
            logging.info("Layer selection blocked: Currently in mask edit mode")
            # Optionally show a temporary notification
            self.show_notification("Please exit mask edit mode first (Press ESC)")
            return

        # Deselect all strands first
        for strand in self.canvas.strands:
            strand.is_selected = False

        # Reset the user_deselected_all flag in the move mode when a strand is explicitly selected
        if hasattr(self.canvas, 'current_mode') and hasattr(self.canvas.current_mode, 'user_deselected_all'):
            self.canvas.current_mode.user_deselected_all = False

        if self.masked_mode:
            self.handle_masked_layer_selection(index)
        elif self.lock_mode:
            if self.canvas.current_mode == self.canvas.attach_mode:
                # If in attach mode, check if the strand has a free side
                strand = self.canvas.strands[index]
                if any(not circle for circle in strand.has_circles):
                    for i, button in enumerate(self.layer_buttons):
                        button.setChecked(i == index)
                    # Set the selected strand's is_selected to True
                    strand.is_selected = True
                    if emit_signal:
                        self.strand_selected.emit(index)
                    self.last_selected_index = index
            else:
                # Toggle lock state only if not in attach mode
                if index in self.locked_layers:
                    logging.info(f"Unlocking strand at index {index}")
                    self.locked_layers.remove(index)
                    # When unlocking, also deselect and unhighlight the strand
                    if 0 <= index < len(self.canvas.strands):
                        strand = self.canvas.strands[index]
                        strand.is_selected = False
                        logging.info(f"Set strand.is_selected = False for strand {strand.layer_name}")
                    # Clear canvas selection if this was the selected strand
                    if self.canvas.selected_strand_index == index:
                        logging.info(f"Clearing canvas selection for strand index {index}")
                        self.canvas.selected_strand = None
                        self.canvas.selected_strand_index = None
                        self.canvas.selected_attached_strand = None
                    # Uncheck the layer button
                    if 0 <= index < len(self.layer_buttons):
                        self.layer_buttons[index].setChecked(False)
                        logging.info(f"Unchecked layer button for index {index}")
                    # Update canvas to reflect deselection and unhighlighting
                    self.canvas.update()
                    self.update_layer_buttons_lock_state()
                    self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
                    # Save state for undo/redo
                    if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                        # Force save by temporarily clearing the last save time to bypass timing check
                        old_last_save_time = getattr(self.undo_redo_manager, '_last_save_time', 0)
                        self.undo_redo_manager._last_save_time = 0
                        self.undo_redo_manager.save_state()
                        # Restore the last save time
                        self.undo_redo_manager._last_save_time = old_last_save_time
                    # Don't re-select the strand after unlocking
                    return
                else:
                    logging.info(f"Locking strand at index {index}")
                    self.locked_layers.add(index)
                    # When locking, also deselect and unhighlight the strand if it's currently selected
                    if 0 <= index < len(self.canvas.strands):
                        strand = self.canvas.strands[index]
                        strand.is_selected = False
                        logging.info(f"Set strand.is_selected = False for locked strand {strand.layer_name}")
                    # Clear canvas selection if this was the selected strand
                    if self.canvas.selected_strand_index == index:
                        logging.info(f"Clearing canvas selection for locked strand index {index}")
                        self.canvas.selected_strand = None
                        self.canvas.selected_strand_index = None
                        self.canvas.selected_attached_strand = None
                    # Uncheck the layer button
                    if 0 <= index < len(self.layer_buttons):
                        self.layer_buttons[index].setChecked(False)
                        logging.info(f"Unchecked layer button for locked index {index}")
                    # Update canvas to reflect deselection
                    self.canvas.update()
                self.update_layer_buttons_lock_state()
                self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
                # Save state for undo/redo
                if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                    self.undo_redo_manager.save_state()
                # Don't re-select the strand after locking
                return
        else:
            for i, button in enumerate(self.layer_buttons):
                button.setChecked(i == index)
            # Set the selected strand's is_selected to True
            if 0 <= index < len(self.canvas.strands):
                selected_strand = self.canvas.strands[index]
                selected_strand.is_selected = True
            if emit_signal:
                self.strand_selected.emit(index)
            self.last_selected_index = index

        # Ensure the selected strand is updated in the canvas
        if 0 <= index < len(self.canvas.strands):
            self.canvas.selected_strand = self.canvas.strands[index]
            self.canvas.selected_strand_index = index
        else:
            self.canvas.selected_strand = None
            self.canvas.selected_strand_index = None

        # Update layer button states and redraw the canvas
        self.update_layer_button_states()
        self.canvas.update()

        if not self.masked_mode and not self.lock_mode:
            for i, button in enumerate(self.layer_buttons):
                button.setChecked(i == index)
            # Set the selected strand's is_selected to True
            if 0 <= index < len(self.canvas.strands):
                selected_strand = self.canvas.strands[index]
                selected_strand.is_selected = True
            if emit_signal:
                self.strand_selected.emit(index)
            self.last_selected_index = index

            # Switch to attach mode (only if not already in recursion)
            if self.parent_window and emit_signal:
                self.parent_window.set_attach_mode()

    def handle_masked_layer_selection(self, index):
        """Handle the selection of layers in masked mode."""
        if self.first_masked_layer is None:
            self.first_masked_layer = index
            self.layer_buttons[index].darken_color()
        else:
            second_layer = index
            if self.first_masked_layer != second_layer:
                self.layer_buttons[second_layer].darken_color()
                self.create_masked_layer(self.first_masked_layer, second_layer)
            self.exit_masked_mode()

    def create_masked_layer(self, layer1, layer2):
        """Create a new masked layer from two selected layers."""
        if len(self.selected_strands) == 2:
            strand1, strand2 = self.selected_strands
            logging.info(f"Attempting to create masked layer for {strand1.layer_name} and {strand2.layer_name}")
            
            if not self.mask_exists(strand1, strand2):
                # Store all existing colors before any operations
                original_colors = {}
                for strand in self.canvas.strands:
                    original_colors[strand.layer_name] = strand.color
                    if hasattr(strand, 'set_number'):
                        set_number = strand.set_number
                        if set_number not in self.set_colors:
                            self.set_colors[set_number] = strand.color
                
                # Create the masked layer
                self.mask_created.emit(strand1, strand2)
                
                # Find the newly created masked strand
                masked_strand = self.find_masked_strand(strand1, strand2)
                if masked_strand:
                    # Set colors for the masked layer
                    masked_strand.color = original_colors[strand1.layer_name]
                    if hasattr(masked_strand, 'second_selected_strand'):
                        masked_strand.second_selected_strand.color = original_colors[strand2.layer_name]
                    
                    self.clear_selection()
                    self.selected_strands.append(masked_strand)
                    
                    # Single refresh with all operations
                    if self.canvas.layer_panel:
                        # Restore all original colors
                        for strand in self.canvas.strands:
                            if strand.layer_name in original_colors:
                                strand.color = original_colors[strand.layer_name]
                            elif hasattr(strand, 'set_number'):
                                strand.color = self.set_colors.get(strand.set_number, strand.color)
                        
                        # Get the masked strand index before refresh
                        masked_strand_index = self.canvas.strands.index(masked_strand)
                        
                        # Do a single refresh
                        self.refresh_layers()
                        
                        # Select the masked layer
                        self.select_layer(masked_strand_index)
                    
                    logging.info(f"Selected newly created masked strand: {masked_strand.layer_name}")
                else:
                    logging.info(f"Mask already exists for {strand1.layer_name} and {strand2.layer_name}")
                    self.clear_selection()
                
                self.canvas.update()

    def add_masked_layer_button(self, layer1, layer2):
        """Add a new button for a masked layer."""
        button = NumberedLayerButton(f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}", 0)
        # Set the masked layer's color to match the first selected strand
        button.set_color(self.layer_buttons[layer1].color)
        # Set the border color to match the second selected strand
        button.set_border_color(self.layer_buttons[layer2].color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        
        # Store current scroll position
        scrollbar = self.scroll_area.verticalScrollBar()
        current_scroll = scrollbar.value()
        
        # Add the button to layout
        self.scroll_layout.insertWidget(0, button)
        self.layer_buttons.append(button)
        
        # Restore scroll position after a brief delay
        QTimer.singleShot(10, lambda: scrollbar.setValue(current_scroll))
        
        return button

    def request_edit_mask(self, strand_index):
        """
        Enter mask editing mode for a specific strand.

        Args:
            strand_index (int): Index of the masked strand to edit
        """
        if self.canvas:
            # Make sure the index is within bounds.
            if strand_index < 0 or strand_index >= len(self.canvas.strands):
                logging.warning(f"request_edit_mask called with invalid index {strand_index}.")
                return

            # Ensure the strand is actually a MaskedStrand before editing.
            if not isinstance(self.canvas.strands[strand_index], MaskedStrand):
                logging.warning(f"request_edit_mask called on a non-masked strand at index {strand_index}.")
                return

            self.mask_editing = True
            _ = translations[self.language_code]
            message = _['mask_edit_mode_message']
            self.mask_edit_label.setText(message)
            self.mask_edit_label.adjustSize()
            self.mask_edit_label.show()

            # Disable all layer buttons except the one being edited
            for i, button in enumerate(self.layer_buttons):
                button.setEnabled(i == strand_index)
                if i == strand_index:
                    # Temporarily disable context menu on this button
                    button.setContextMenuPolicy(Qt.NoContextMenu)
                    button.setStyleSheet("""
                        QPushButton {
                            border: 2px solid red;
                            background-color: rgba(255, 0, 0, 0.1);
                        }
                    """)
                else:
                    # Also disable context menus on the others to be safe
                    button.setContextMenuPolicy(Qt.NoContextMenu)
                    button.setStyleSheet("QPushButton { opacity: 0.5; }")

            self.disable_controls()
            if self.parent_window:
                self.parent_window.disable_all_mainwindow_buttons()

            logging.info(f"Entered mask edit mode for strand {strand_index}")
            self.canvas.enter_mask_edit_mode(strand_index)
            self.canvas.setFocus()

    def exit_mask_edit_mode(self):
        """Clean up and exit mask editing mode."""
        if not self.mask_editing:
            return
            
        self.mask_editing = False
        self.mask_edit_label.hide()
        
        # Re-enable all layer buttons
        for i, button in enumerate(self.layer_buttons):
            button.setEnabled(True)
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            if isinstance(button, NumberedLayerButton):
                button.restore_original_style()
            button.update()
            # If this strand is MaskedStrand, reconnect context menu:
            if i < len(self.canvas.strands) and isinstance(self.canvas.strands[i], MaskedStrand):
                # Reconnect our customContextMenuRequested 
                button.customContextMenuRequested.connect(
                    lambda pos, idx=i: self.show_masked_layer_context_menu(idx, pos)
                )

        self.enable_controls()
        if self.parent_window:
            self.parent_window.enable_all_mainwindow_buttons()

        if hasattr(self, 'parent_window'):
            self.parent_window.exit_mask_edit_mode()
        
        _ = translations[self.language_code]
        logging.info("Exited mask edit mode")
        self.show_notification(_['mask_edit_mode_exited'])
        self.update()

        # --- ADD: Save state after exiting mask edit mode via ESC --- 
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            # Force a save by resetting the last save time so the identical-state and timing checks are bypassed
            self.undo_redo_manager._last_save_time = 0
            logging.info("Saving state after exiting mask edit mode")
            self.undo_redo_manager.save_state()
        # --- END ADD ---

    def disable_controls(self):
        """Disable controls that shouldn't be used during mask editing."""
        self.add_new_strand_button.setEnabled(False)
        self.delete_strand_button.setEnabled(False)
        self.draw_names_button.setEnabled(False)
        self.lock_layers_button.setEnabled(False)
        self.deselect_all_button.setEnabled(False)
        if hasattr(self, 'group_layer_manager'):
            self.group_layer_manager.create_group_button.setEnabled(False)

    def enable_controls(self):
        """Re-enable controls after mask editing."""
        self.add_new_strand_button.setEnabled(True)
        self.delete_strand_button.setEnabled(True)
        self.draw_names_button.setEnabled(True)
        self.lock_layers_button.setEnabled(True)
        self.deselect_all_button.setEnabled(True)
        if hasattr(self, 'group_layer_manager'):
            self.group_layer_manager.create_group_button.setEnabled(True)

    def show_notification(self, message, duration=2000):
        """Show a temporary notification message."""
        # Show the notification label only when needed
        self.notification_label.setText(message)
        self.notification_label.show()
        # After the duration, clear and hide again to remove extra space
        QTimer.singleShot(duration, lambda: (
            self.notification_label.clear(),
            self.notification_label.hide()
        ))



    def request_new_strand(self):
        """Request a new strand to be created in the selected set."""
        logging.info("Add New Strand button clicked.")
        # Start a new set or use an existing one
        self.start_new_set()
        # Call the canvas method to start drawing a new strand
        self.canvas.start_new_strand_mode(self.current_set)
        logging.info(f"Requested new strand for set {self.current_set}")

    def request_delete_strand(self):
        """Request the deletion of the selected strand."""
        selected_button = next((button for button in self.layer_buttons if button.isChecked()), None)
        if selected_button:
            strand_name = selected_button.text()
            logging.info(f"Selected strand for deletion: {strand_name}")
            
            # Find the corresponding strand in the canvas
            strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
            
            if strand_index is not None:
                strand = self.canvas.strands[strand_index]
                if isinstance(strand, MaskedStrand):
                    # Delete only this specific masked layer
                    if self.canvas.delete_masked_layer(strand):
                        self.remove_layer_button(strand_index)
                        # Update the layer panel without affecting other masked layers
                        self.refresh()
                        self.refresh_layers()  # Add this line to refresh after masked strand deletion
                        
                        # Save state for undo/redo after masked layer deletion
                        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                            self.undo_redo_manager.save_state()
                            logging.info("Saved state after masked layer deletion")

                    logging.info(f"Masked layer {strand_name} deleted successfully")
                else:
                    # Handle regular strand deletion
                    self.strand_deleted.emit(strand_index)
                    # Force a complete refresh after deletion
                    self.refresh()
                    self.refresh_layers()
                    self.update_layer_button_states()
                    
                    # Save state for undo/redo after regular strand deletion
                    if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                        self.undo_redo_manager.save_state()
                        logging.info("Saved state after strand deletion")
            else:
                logging.warning(f"Strand {strand_name} not found in canvas strands")
        else:
            logging.warning("No strand selected for deletion")

    def remove_layer_button(self, index):
        """Remove a layer button at the specified index."""
        if 0 <= index < len(self.layer_buttons):
            button = self.layer_buttons.pop(index)
            button.setParent(None)
            button.deleteLater()
            self.scroll_layout.removeWidget(button)
            logging.info(f"Removed layer button at index {index}")

    def update_masked_layers(self, deleted_set_number, strands_removed):
        """Update masked layers after deletion, ensuring only specific masked layer is removed."""
        logging.info(f"Updating masked layers for deleted strand index: {strands_removed}")
        
        # Skip if we're deleting a masked layer - this is handled separately in request_delete_strand
        if len(strands_removed) == 1 and isinstance(self.canvas.strands[strands_removed[0]], MaskedStrand):
            logging.info("Single masked layer deletion - skipping update_masked_layers")
            return
        
        # Only proceed with regular strand deletion logic
        buttons_to_remove = []
        for i, button in enumerate(self.layer_buttons):
            if i in strands_removed:
                buttons_to_remove.append(i)
                logging.info(f"Marking layer for removal: {button.text()}")

        # Remove the marked buttons
        for index in sorted(buttons_to_remove, reverse=True):
            button = self.layer_buttons.pop(index)
            button.setParent(None)
            button.deleteLater()
            self.scroll_layout.removeWidget(button)
            logging.info(f"Removed layer button: {button.text()}")

    def update_after_deletion(self, deleted_set_number, strands_removed, is_main_strand, renumber=False):
        logging.info(f"Starting update_after_deletion: deleted_set_number={deleted_set_number}, strands_removed={strands_removed}, is_main_strand={is_main_strand}, renumber={renumber}")

        # Clear selection first to avoid any index issues during deletion
        selected_layer = self.get_selected_layer()
        if selected_layer is not None and selected_layer in strands_removed:
            self.clear_selection()
            logging.info("Cleared selection before deletion")

        # Remove the corresponding buttons
        for index in sorted(strands_removed, reverse=True):
            if 0 <= index < len(self.layer_buttons):
                button = self.layer_buttons.pop(index)
                button.setParent(None)
                button.deleteLater()
                self.scroll_layout.removeWidget(button)
                logging.info(f"Removed button at index {index}")

        if is_main_strand:
            # Update set counts and colors
            if deleted_set_number in self.set_counts:
                del self.set_counts[deleted_set_number]
                logging.info(f"Deleted set count for set {deleted_set_number}")
            if deleted_set_number in self.set_colors:
                del self.set_colors[deleted_set_number]
                logging.info(f"Deleted set color for set {deleted_set_number}")

            # Update the current set to the highest remaining set number among main strands
            existing_sets = set(
                strand.set_number
                for strand in self.canvas.strands
                if hasattr(strand, 'set_number') and not isinstance(strand, MaskedStrand)
            )
            self.current_set = max(existing_sets) if existing_sets else 0
            logging.info(f"Updated current_set to {self.current_set}")

        # Update masked layers before refreshing
        try:
            self.update_masked_layers(deleted_set_number, strands_removed)
            logging.info("Updated masked layers successfully")
        except Exception as e:
            logging.error(f"Error updating masked layers: {str(e)}")

        # Ensure button count matches strand count
        if len(self.layer_buttons) != len(self.canvas.strands):
            logging.warning(f"Button count mismatch: {len(self.layer_buttons)} buttons vs {len(self.canvas.strands)} strands")
            self.refresh()  # Force a complete refresh if counts don't match
        else:
            # Update states only if counts match
            try:
                self.update_layer_button_states()
                self.update_attachable_states()
                logging.info("Updated button states successfully")
            except Exception as e:
                logging.error(f"Error updating button states: {str(e)}")
                self.refresh()  # Fall back to complete refresh if update fails

        # Final refresh to ensure consistency
        self.refresh()
        logging.info("Finished update_after_deletion")

    def renumber_sets(self):
        new_set_numbers = {}
        new_count = 1
        for button in self.layer_buttons:
            old_set_number = int(button.text().split('_')[0])
            if old_set_number not in new_set_numbers:
                new_set_numbers[old_set_number] = new_count
                new_count += 1
            new_set_number = new_set_numbers[old_set_number]
            button.setText(f"{new_set_number}_{button.text().split('_')[1]}")
        
        # Update set_counts and set_colors
        self.set_counts = {new_set_numbers[k]: v for k, v in self.set_counts.items() if k in new_set_numbers}
        self.set_colors = {new_set_numbers[k]: v for k, v in self.set_colors.items() if k in new_set_numbers}
        
        logging.info(f"Renumbered sets: {new_set_numbers}")


    def update_button_numbering_for_set(self, set_number):
        logging.info(f"Starting update_button_numbering_for_set: set_number={set_number}")
        for button in self.layer_buttons:
            button_text = button.text()
            parts = button_text.split('_')
            if parts[0] == str(set_number):
                if len(parts) == 2:  # Regular strand
                    # Keep the original number, don't increment
                    new_text = button_text
                    logging.info(f"Kept original button text: {new_text}")
                else:  # Masked layer
                    logging.info(f"Skipping renumbering for masked layer: {button_text}")
        logging.info("Finished update_button_numbering_for_set")
    

    def update_layer_buttons_after_deletion(self, deleted_set_number, indices_to_remove):
        # Remove buttons for deleted strands
        for index in sorted(indices_to_remove, reverse=True):
            if 0 <= index < len(self.layer_buttons):
                button = self.layer_buttons.pop(index)
                button.setParent(None)
                button.deleteLater()
                self.scroll_layout.removeWidget(button)

        # Update remaining buttons
        for i, button in enumerate(self.layer_buttons):
            parts = button.text().split('_')
            set_number = int(parts[0])
            
            if set_number == deleted_set_number:
                # Update the numbering for the affected set
                new_number = i + 1 - sum(1 for b in self.layer_buttons[:i] if int(b.text().split('_')[0]) != deleted_set_number)
                new_text = f"{set_number}_{new_number}"
                button.setText(new_text)
            elif set_number > deleted_set_number:
                # Decrement set numbers greater than the deleted set
                new_set_number = set_number - 1
                new_text = f"{new_set_number}_{parts[1]}"
                button.setText(new_text)
                # Use canvas default strand color if available, otherwise fallback to purple
                default_color = QColor(200, 170, 230, 255)  # Fallback
                if self.canvas and hasattr(self.canvas, 'default_strand_color'):
                    default_color = self.canvas.default_strand_color
                button.set_color(self.set_colors.get(new_set_number, default_color))

        self.update_layer_button_states()

    def get_next_available_set_number(self):
        existing_set_numbers = set(
            strand.set_number
            for strand in self.canvas.strands
            if hasattr(strand, 'set_number') and not isinstance(strand, MaskedStrand)
        )
        max_set_number = max(existing_set_numbers, default=0)
        return max_set_number + 1

    def add_layer_button(self, set_number, count):
        """Add a new layer button directly to the layout."""
        logging.info(f"Starting add_layer_button: set_number={set_number}, count={count}")

        # Update set count
        self.set_counts[set_number] = count
        logging.info(f"Updated set count for set {set_number} to {count}")

        # Create button name
        button_name = f"{set_number}_{count}"
        logging.info(f"Created new button: {button_name}")

        # Get the strand index
        strand_index = len(self.canvas.strands) - 1

        # Create and add the button
        button = self.create_layer_button(strand_index, self.canvas.strands[strand_index], count)
        self.layer_buttons.append(button)  # Add to end of list

        # Add button directly to layout at the top, aligned center
        self.scroll_layout.insertWidget(0, button, 0, Qt.AlignHCenter)

        logging.info(f"Added new button directly to layout at top (index 0)")
        logging.info("Finished add_layer_button")

        # Select the newly created strand
        self.select_layer(strand_index)
        return button

    def on_strand_attached(self):
        """Called when a strand is attached to another strand."""
        self.update_layer_button_states()

    ### Inside LayerPanel class ###

    def start_new_set(self):
        """Start a new set of strands."""
        # Get all existing set numbers from non-masked strands
        existing_sets = set()
        for strand in self.canvas.strands:
            if not isinstance(strand, MaskedStrand):
                try:
                    # Extract set number from layer name
                    set_num = int(strand.layer_name.split('_')[0])
                    existing_sets.add(set_num)
                except (ValueError, IndexError, AttributeError):
                    continue
        
        # Find the next available set number
        next_set = 1
        while next_set in existing_sets:
            next_set += 1
        
        self.current_set = next_set
        self.set_counts[self.current_set] = 0
        # Use canvas default strand color if available, otherwise fallback to purple
        default_color = QColor(200, 170, 230, 255)  # Fallback
        if self.canvas and hasattr(self.canvas, 'default_strand_color'):
            default_color = self.canvas.default_strand_color
        self.set_colors[self.current_set] = default_color

        
        logging.info(f"Starting new set {self.current_set} (Existing sets: {sorted(existing_sets)})")

    def delete_strand(self, index):
        """
        Delete a strand and update the canvas and layer panel.

        Args:
            index (int): The index of the strand to delete.
        """
        if 0 <= index < len(self.canvas.strands):
            strand = self.canvas.strands[index]
            set_number = strand.set_number
            logging.info(f"Starting deletion of strand {strand.layer_name}")
            
            # Log states before deletion
            for i, s in enumerate(self.canvas.strands):
                logging.info(f"Before deletion - Strand {s.layer_name}: has_circles={s.has_circles}")
                if hasattr(s, 'attached_strands'):
                    logging.info(f"  Connected to: {[ast.layer_name for ast in s.attached_strands]}")

            # Remove the strand from the canvas
            self.canvas.remove_strand(strand)
            self.canvas.update()

            # Log states after deletion
            for i, s in enumerate(self.canvas.strands):
                logging.info(f"After deletion - Strand {s.layer_name}: has_circles={s.has_circles}")
                if hasattr(s, 'attached_strands'):
                    logging.info(f"  Connected to: {[ast.layer_name for ast in s.attached_strands]}")

            # Remove the corresponding layer button
            if index < len(self.layer_buttons):
                button = self.layer_buttons.pop(index)
                button.setParent(None)
                button.deleteLater()
                logging.info(f"Removed layer button for strand: {strand.layer_name}")

            # Update set_counts
            if set_number in self.set_counts:
                self.set_counts[set_number] -= 1
                if self.set_counts[set_number] <= 0:
                    del self.set_counts[set_number]
                    logging.info(f"Removed set_count entry for set {set_number}")

            # Remove set color if no strands are left in the set
            if not any(s.set_number == set_number for s in self.canvas.strands):
                if set_number in self.set_colors:
                    del self.set_colors[set_number]
                    logging.info(f"Removed set_color entry for set {set_number}")

            # Update current_set to the lowest available set number
            existing_sets = set(
                strand.set_number for strand in self.canvas.strands if hasattr(strand, 'set_number')
            )
            if existing_sets:
                self.current_set = min(existing_sets)
            else:
                self.current_set = 1
            logging.info(f"Updated current_set to {self.current_set}")
            self.refresh()
            # Do a single refresh
            self.refresh_layers()
            # Update layer button states
            self.update_layer_button_states()

        else:
            logging.warning(f"Invalid index for deleting strand: {index}")

    def clear_selection(self):
        """Clear the selection of all layer buttons."""
        for button in self.layer_buttons:
            button.setChecked(False)

    def get_selected_layer(self):
        """Get the index of the currently selected layer."""
        for i, button in enumerate(self.layer_buttons):
            if button.isChecked():
                return i
        return None


    def deselect_all(self):
        """Deselect all layers and strands."""
        # Deselect all layer buttons
        for button in self.layer_buttons:
            button.setChecked(False)

        # Deselect all strands in the canvas
        for strand in self.canvas.strands:
            strand.is_selected = False

        # Update the canvas to reflect changes
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.selected_attached_strand = None  # Also clear selected_attached_strand
        self.canvas.update()
        
        # Emit the signal for other components to react to deselection
        self.deselect_all_requested.emit()

    def on_color_changed(self, set_number, color):
        """Handle color change for a set of strands."""
        logging.info(f"Color change requested for set {set_number}")
        
        # Update color in set_colors dictionary
        self.set_colors[set_number] = color
        
        # Update colors in canvas
        self.canvas.update_color_for_set(set_number, color)
        
        # Update all related buttons
        for button in self.layer_buttons:
            button_text = button.text()
            parts = button_text.split('_')
            
            # Update main strand buttons of the same set
            if parts[0] == str(set_number):
                button.set_color(color)
                
            # Update masked layer buttons that use this set
            if len(parts) == 4:  # Masked layer format: "set1_num1_set2_num2"
                if parts[0] == str(set_number):
                    button.set_color(color)
                elif parts[2] == str(set_number):
                    button.set_border_color(color)
        
        # Emit signal for other components
        self.color_changed.emit(set_number, color)
        
        # Force canvas update
        self.canvas.update()

        # Explicitly save state after color change
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            # --- ADD: Check suppression flag --- 
            if not getattr(self.undo_redo_manager, '_suppress_intermediate_saves', False):
                logging.info(f"Saving state after color change for set {set_number}")
                # Reset last save time to force save, as color change alone might not be detected otherwise
                self.undo_redo_manager._last_save_time = 0 
                self.undo_redo_manager.save_state()
            else:
                logging.info(f"Skipping save after color change for set {set_number} due to suppression flag.")
            # --- END ADD --- 

    def update_colors_for_set(self, set_number, color):
        """
        Update colors for all strands in a specific set.
        """
        logging.info(f"LayerPanel: Updating colors for set {set_number} to {color.name()}")
        
        # Update colors in canvas strands
        for strand in self.canvas.strands:
            logging.info(f"LayerPanel: Checking strand: {strand.layer_name}")
            # Get the first number from the layer name
            first_part = strand.layer_name.split('_')[0]
            
            if first_part == str(set_number):
                # Update regular strand color
                strand.color = color
                logging.info(f"LayerPanel: Updated color for strand: {strand.layer_name} (matched set {set_number})")
                
                # If it's an attached strand, update its children
                if hasattr(strand, 'attached_strands'):
                    logging.info(f"LayerPanel: Checking attached strands for {strand.layer_name}")
                    for attached in strand.attached_strands:
                        if attached.layer_name.split('_')[0] == str(set_number):
                            attached.color = color
                            logging.info(f"LayerPanel: Updated color for attached strand: {attached.layer_name} (matched set {set_number})")
                        else:
                            logging.info(f"LayerPanel: Skipped attached strand: {attached.layer_name} (did not match set {set_number})")
            else:
                logging.info(f"LayerPanel: Skipped strand: {strand.layer_name} (did not match set {set_number})")
        
        # Update layer button colors
        for button in self.layer_buttons:
            button_text = button.text()
            parts = button_text.split('_')
            
            if len(parts) == 4:  # This is a masked layer button (format: "set1_num1_set2_num2")
                if parts[0] == str(set_number):
                    # Update main color if it's the first strand
                    button.set_color(color)
                    logging.info(f"LayerPanel: Updated masked layer main color for {button_text}")
                elif parts[2] == str(set_number):
                    # Update border color if it's the second strand
                    button.set_border_color(color)
                    logging.info(f"LayerPanel: Updated masked layer border color for {button_text}")
            else:  # Regular layer button
                if parts[0] == str(set_number):
                    button.set_color(color)
                    logging.info(f"LayerPanel: Updated button color for {button_text}")
        
        # Force canvas redraw
        self.canvas.update()
        logging.info(f"LayerPanel: Finished updating colors for set {set_number}")

    def resizeEvent(self, event):
        """Handle resize events by updating the size of the splitter handle."""
        super().resizeEvent(event)
        self.handle.updateSize()

    def simulate_refresh_button_click(self):
        """Simulate clicking the refresh button without visual feedback"""
        if hasattr(self, 'refresh_button'):
            logging.info("Simulating refresh button click")
            # Call the refresh_layers method directly instead of triggering the button click
            self.refresh_layers()
        else:
            logging.warning("Cannot simulate refresh button click - refresh_button not found")
            
    def on_strand_created(self, strand):
        """Handle strand creation event."""
        logging.info(f"Starting on_strand_created for strand: {strand.layer_name if hasattr(strand, 'layer_name') else ''}")
        
        # SUPER EXPLICIT DEBUG - log everything before processing
        logging.info(f"STRAND_DEBUG: strand.layer_name = '{strand.layer_name}'")
        logging.info(f"STRAND_DEBUG: strand.set_number = {strand.set_number}")
        logging.info(f"STRAND_DEBUG: hasattr(strand, 'layer_name') = {hasattr(strand, 'layer_name')}")
        if hasattr(strand, 'layer_name') and strand.layer_name:
            logging.info(f"STRAND_DEBUG: '_' in strand.layer_name = {'_' in strand.layer_name}")
            if '_' in strand.layer_name:
                parts = strand.layer_name.split('_')
                logging.info(f"STRAND_DEBUG: parts from split = {parts}")
        
        # Extract set number and count from the strand's layer_name
        if hasattr(strand, 'layer_name') and strand.layer_name and '_' in strand.layer_name:
            try:
                parts = strand.layer_name.split('_')
                set_number = int(parts[0])
                count = int(parts[1])
                logging.info(f"STRAND_DEBUG: Successfully extracted set_number={set_number}, count={count}")
            except (ValueError, IndexError) as e:
                logging.info(f"STRAND_DEBUG: Exception during parsing: {e}")
                # Fallback to using strand.set_number if layer_name parsing fails
                set_number = strand.set_number
                count = self.set_counts.get(set_number, 0) + 1
                logging.info(f"STRAND_DEBUG: Used fallback set_number={set_number}, count={count}")
        else:
            # Fallback to using strand.set_number if no valid layer_name
            set_number = strand.set_number
            count = self.set_counts.get(set_number, 0) + 1
            logging.info(f"STRAND_DEBUG: Used fallback (no valid layer_name) set_number={set_number}, count={count}")
        
        # Debug logging
        logging.info(f"DEBUG on_strand_created: strand.layer_name='{strand.layer_name}', extracted set_number={set_number}, count={count}")
        logging.info(f"DEBUG on_strand_created: self.set_counts={self.set_counts}")
        
        # Add the new layer button
        logging.info(f"Adding new layer button for set {set_number}, count {count}")
        self.add_layer_button(set_number, count)
        
        # Check if there are existing strands in this set with different colors
        existing_strands_in_set = [s for s in self.canvas.strands if hasattr(s, 'set_number') and s.set_number == set_number and s != strand]
        
        if existing_strands_in_set:
            # There are existing strands in this set - preserve their color
            existing_color = existing_strands_in_set[0].color  # Use the color of the first existing strand
            self.set_colors[set_number] = existing_color
            # Update the new strand to match the existing set color
            strand.color = existing_color
            logging.info(f"Set {set_number} already exists with color {existing_color.red()},{existing_color.green()},{existing_color.blue()},{existing_color.alpha()}, updated new strand to match")
        else:
            # This is a new set or first strand in set - use the strand's current color or default
            if set_number not in self.set_colors:
                # Use the strand's current color if it has one, otherwise use default
                if hasattr(strand, 'color') and strand.color:
                    self.set_colors[set_number] = strand.color
                    logging.info(f"New set {set_number}: Using strand's color {strand.color.red()},{strand.color.green()},{strand.color.blue()},{strand.color.alpha()}")
                else:
                    # Use canvas default strand color if available, otherwise fallback to purple
                    default_color = QColor(200, 170, 230, 255)  # Fallback
                    if self.canvas and hasattr(self.canvas, 'default_strand_color'):
                        default_color = self.canvas.default_strand_color
                    self.set_colors[set_number] = default_color
                    strand.color = default_color
                    logging.info(f"New set {set_number}: Using default color {default_color.red()},{default_color.green()},{default_color.blue()},{default_color.alpha()}")
            else:
                # Set color already exists, update strand to match
                strand.color = self.set_colors[set_number]
                logging.info(f"Set {set_number} color already exists, updated strand to match")
        
        # Simulate clicking the refresh button for consistency in layer display
        self.simulate_refresh_button_click()
        
        logging.info("Finished on_strand_created")

    def on_strands_deleted(self, indices):
        """Handle the deletion of multiple strands from the canvas."""
        for index in sorted(indices, reverse=True):
            self.remove_layer_button(index)
        self.update_layer_button_states()
    def update_layer_names(self, affected_set_number=None):
        logging.info(f"Starting update_layer_names: affected_set_number={affected_set_number}")
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                if affected_set_number is None or strand.set_number == affected_set_number:
                    # Keep the original layer name
                    button.setText(strand.layer_name)
                    logging.info(f"Kept original layer name for strand {i}: {button.text()}")
        self.update_layer_button_states()
        logging.info("Finished update_layer_names")
    def refresh_layers(self):
        """Refresh the drawing of the layers with zero visual flicker."""
        logging.info("Starting refresh of layer panel")
        
        # Get the main window (either the direct parent or parent's parent)
        main_window = self.parent_window if hasattr(self, 'parent_window') and self.parent_window else self.parent()
        
        # --- Platform-specific overlay snapshot (avoids macOS CoreImage crash) ---
        overlay = None
        if sys.platform != 'darwin':
            # 1. Create a screenshot of the current scroll area viewport (safe on non-macOS)
            viewport = self.scroll_area.viewport()
            pixmap = viewport.grab()

            # 2. Create a temporary overlay label with the screenshot
            overlay = QLabel(self.scroll_area)
            overlay.setPixmap(pixmap)
            overlay.setGeometry(viewport.rect())
            overlay.setStyleSheet("background-color: transparent;")
            overlay.raise_()
            overlay.show()
        else:
            logging.debug("[macOS] Skipping viewport grab overlay in refresh_layers() to prevent segfault")
        
        # 3. Disable updates on the ENTIRE application window
        if main_window:
            main_window.setUpdatesEnabled(False)
        
        # 4. Also disable updates on scroll area for redundancy
        self.scroll_area.setUpdatesEnabled(False)
        
        # 5. --- Remove widgets from layout ---
        removed_count = 0
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                removed_count += 1
            del item
        
        # 6. --- Re-add buttons in reverse order ---
        added_count = 0
        valid_buttons = [btn for btn in self.layer_buttons if btn]
        for button in reversed(valid_buttons):
            self.scroll_layout.addWidget(button, 0, Qt.AlignHCenter)
            button.show()
            added_count += 1
        
        # 7. Force layout update before re-enabling window updates
        self.scroll_layout.update()
        
        # 8. Re-enable updates in reverse order
        self.scroll_area.setUpdatesEnabled(True)
        if main_window:
            main_window.setUpdatesEnabled(True)
            
        # 9. Remove the overlay after everything is ready (if we actually created one)
        if overlay is not None:
            overlay.deleteLater()
        
        # Reset canvas zoom and pan to original view
        self.canvas.reset_zoom()
        
        logging.info(f"Refreshed layer panel: removed {removed_count}, added {added_count} buttons")
    def refresh(self):
        """Comprehensive refresh of layer panel with zero visual flicker."""
        logging.info("Starting comprehensive refresh of layer panel")
        
        # Get the main window (either the direct parent or parent's parent)
        main_window = self.parent_window if hasattr(self, 'parent_window') and self.parent_window else self.parent()
        
        # --- Platform-specific overlay snapshot (avoids macOS CoreImage crash) ---
        overlay = None
        if sys.platform != 'darwin':
            viewport = self.scroll_area.viewport()
            pixmap = viewport.grab()

            overlay = QLabel(self.scroll_area)
            overlay.setPixmap(pixmap)
            overlay.setGeometry(viewport.rect())
            overlay.setStyleSheet("background-color: transparent;")
            overlay.raise_()
            overlay.show()
        else:
            logging.debug("[macOS] Skipping viewport grab overlay in refresh() to prevent segfault")
        
        # 3. Disable updates on the ENTIRE application window
        if main_window:
            main_window.setUpdatesEnabled(False)
        
        # 4. Also disable updates on scroll area for redundancy
        self.scroll_area.setUpdatesEnabled(False)
        
        # Remove all existing buttons
        for button in self.layer_buttons:
            button.setParent(None)
            button.deleteLater()
        self.layer_buttons.clear()
        
        # Reset set counts
        self.set_counts = {}
        
        # Add buttons for all current strands
        for i, strand in enumerate(self.canvas.strands):
            set_number = strand.set_number
            
            if set_number not in self.set_counts:
                self.set_counts[set_number] = 0
            self.set_counts[set_number] += 1
            
            # Use the strand's actual color
            strand_color = strand.color if hasattr(strand, 'color') else self.canvas.strand_colors.get(set_number, 
                self.canvas.default_strand_color if hasattr(self.canvas, 'default_strand_color') else QColor(200, 170, 230, 255))
            
            # --- Store layer_name directly on button for easier lookup ---
            button = NumberedLayerButton(strand.layer_name, self.set_counts[set_number], strand_color)
            # Store the definitive layer name for matching later
            button.layer_name = strand.layer_name
            # --- End Store layer_name ---

            button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
            button.color_changed.connect(self.on_color_changed)
            
            if isinstance(strand, MaskedStrand):
                button.set_border_color(strand.second_selected_strand.color)
                # Ensure masked strand color is correct
                if strand.first_selected_strand:
                    button.set_color(strand.first_selected_strand.color)

            # Set initial hidden state during refresh
            button.set_hidden(strand.is_hidden)

            self.scroll_layout.insertWidget(0, button, 0, Qt.AlignHCenter) # Align center added
            self.layer_buttons.append(button)
        
        # Update button states
        self.update_layer_button_states()
        
        # --- Modified Selection Logic ---
        # Ensure the correct button is selected by matching the strand object
        selected_strand_object = self.canvas.selected_strand
        if selected_strand_object:
            found_button = None
            for button in self.layer_buttons:
                # Use the stored layer_name for reliable matching
                if hasattr(button, 'layer_name') and button.layer_name == selected_strand_object.layer_name:
                    found_button = button
                    break
            if found_button:
                found_button.setChecked(True)
                # Ensure canvas index is also correct (should already be, but for safety)
                try:
                    self.canvas.selected_strand_index = self.canvas.strands.index(selected_strand_object)
                except ValueError:
                     logging.warning(f"Refresh: Selected strand {selected_strand_object.layer_name} not found in canvas.strands after refresh.")
                     self.clear_selection() # Clear if inconsistent
            else:
                logging.warning(f"Refresh: Could not find button for selected strand {selected_strand_object.layer_name}")
                self.clear_selection() # Clear selection if button not found
        else:
            # No strand object selected in canvas, clear visual selection
            self.clear_selection()
        # --- End Modified Selection Logic ---

        # Update the current set
        # --- Ensure current_set uses set_number attribute ---
        existing_sets = set(
            s.set_number for s in self.canvas.strands if hasattr(s, 'set_number') and not isinstance(s, MaskedStrand)
        )
        self.current_set = max(existing_sets, default=0)
        # --- End Ensure current_set ---
        
        # Refresh the GroupLayerManager
        self.group_layer_manager.refresh()

        # Force layout update before re-enabling window updates
        self.scroll_layout.update()
        
        # Re-enable updates
        self.scroll_area.setUpdatesEnabled(True)
        if main_window:
            main_window.setUpdatesEnabled(True)
        
        # Remove the overlay after everything is ready (if we actually created one)
        if overlay is not None:
            overlay.deleteLater()
        
        logging.info(f"Finished comprehensive refresh of layer panel. Total buttons: {len(self.layer_buttons)}")

    def update_masked_strand_color(self, layer_name, color):
        for button in self.layer_buttons:
            if button.text() == layer_name:
                button.set_color(color)
                logging.info(f"Updated color for masked strand button: {layer_name} to {color.name()}")
                break    
    def get_layer_button(self, index):
        """Get the layer button at the specified index."""
        if 0 <= index < len(self.layer_buttons):
            return self.layer_buttons[index]
        return None

    def update_default_colors(self):
        """Update the set_colors dictionary to use the canvas default colors."""
        if self.canvas and hasattr(self.canvas, 'default_strand_color'):
            # Update existing set colors to use the new default
            for set_number in self.set_colors:
                # Only update if it's still the old purple default
                if self.set_colors[set_number] == QColor(200, 170, 230, 255):
                    self.set_colors[set_number] = self.canvas.default_strand_color
                    logging.info(f"Updated set_colors[{set_number}] to new default color: {self.canvas.default_strand_color.red()},{self.canvas.default_strand_color.green()},{self.canvas.default_strand_color.blue()},{self.canvas.default_strand_color.alpha()}")
            
            # Also update the canvas strand_colors dictionary for any existing sets
            if hasattr(self.canvas, 'strand_colors'):
                for set_number in self.canvas.strand_colors:
                    # Only update if it's still the old purple default
                    if self.canvas.strand_colors[set_number] == QColor(200, 170, 230, 255):
                        self.canvas.strand_colors[set_number] = self.canvas.default_strand_color
                        logging.info(f"Updated canvas strand_colors[{set_number}] to new default color: {self.canvas.default_strand_color.red()},{self.canvas.default_strand_color.green()},{self.canvas.default_strand_color.blue()},{self.canvas.default_strand_color.alpha()}")
                
                # Ensure set 1 uses the correct default color for new projects
                if 1 not in self.canvas.strand_colors:
                    self.canvas.strand_colors[1] = self.canvas.default_strand_color
                    logging.info(f"Pre-set strand_colors[1] to default color: {self.canvas.default_strand_color.red()},{self.canvas.default_strand_color.green()},{self.canvas.default_strand_color.blue()},{self.canvas.default_strand_color.alpha()}")

    def set_canvas(self, canvas):
        """Set the canvas associated with this layer panel."""
        self.canvas = canvas
        self.update_default_colors()  # Update colors when canvas is set
        self.refresh()

    def on_layer_order_changed(self, new_order):
        """Handle changes in the order of layers (DEPRECATED by drag/drop refresh)."""
        # This method might become redundant if refresh_layers() is called after drop
        # Keeping it for now in case it's needed elsewhere, but commenting out content
        logging.warning("on_layer_order_changed called - may be deprecated by drag/drop refresh logic.")
        # reordered_buttons = [self.layer_buttons[i] for i in new_order]
        # self.layer_buttons = reordered_buttons

        # # Clear the layout first
        # while self.scroll_layout.count():
        #     item = self.scroll_layout.takeAt(0)
        #     widget = item.widget()
        #     if widget:
        #         widget.setParent(None) # Remove widget from layout management

        # # Re-add buttons in the new order
        # for button in self.layer_buttons:
        #      # --- Modification: Add button container ---
        #      button_container = QWidget()
        #      button_container.setObjectName(f"container_for_{button.text()}")
        #      button_layout = QHBoxLayout(button_container)
        #      button_layout.setAlignment(Qt.AlignHCenter)
        #      button_layout.addWidget(button)
        #      button_layout.setContentsMargins(0, 0, 0, 0)
        #      self.scroll_layout.addWidget(button_container) # Add container
        #      # --- End Modification ---

        # self.update_layer_button_states()
        # self.scroll_layout.update() # Update layout


    def update_attachable_states(self):
        """Update the attachable state of all layer buttons based on strand connections."""
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                strand.update_attachable()  # Update the strand's attachable property
                button.set_attachable(strand.attachable)
            else:
                button.set_attachable(False)

    def update_layer_button_states(self):
        """Update the states of all layer buttons."""
        logging.info("Updating layer button states")
        
        # First update all button states
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                # A strand is only non-deletable if both ends have circles
                is_deletable = not all(strand.has_circles)
                
                logging.info(f"Strand {strand.layer_name}: has_circles={strand.has_circles}, is_deletable={is_deletable}")
                if hasattr(strand, 'attached_strands'):
                    logging.info(f"  Connected to: {[ast.layer_name for ast in strand.attached_strands]}")
                
                button.set_attachable(is_deletable)
                
                # Add visual indication for non-deletable strands
                if not is_deletable:
                    button.setToolTip("This layer cannot be deleted (both ends are attached)")
                else:
                    button.setToolTip("")
            else:
                button.set_attachable(False)
        
        # Then handle the selected strand separately
        selected_index = self.get_selected_layer()
        if (selected_index is not None and 
            selected_index < len(self.layer_buttons) and 
            selected_index < len(self.canvas.strands)):
            
            selected_strand = self.canvas.strands[selected_index]
            # Use the same simple criteria for the delete button
            is_deletable = not all(selected_strand.has_circles)
            
            self.delete_strand_button.setEnabled(is_deletable)
            logging.info(f"Updated delete button state for selected strand {selected_strand.layer_name}: {is_deletable}")
        else:
            self.delete_strand_button.setEnabled(False)
            logging.info("Disabled delete button - no valid selection")
        # Force canvas update instead of refresh
        self.canvas.update()

           # Update tooltips or other text properties if any
           # Example:
           # self.draw_names_button.setToolTip(_['draw_names_tooltip'])
           # Similarly update other tooltips or accessible descriptions
        # Update any other UI elements as needed

    # --- Drag and Drop Event Handlers for scroll_content ---
    # These are now called by DropTargetWidget
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept the drag if it contains the correct MIME type."""
        # Extra diagnostics for macOS
        if sys.platform == 'darwin':
            logging.info(f"[macOS] dragEnterEvent: pos={event.pos()} proposedAction={event.proposedAction()} "
                         f"possibleActions={event.possibleActions()} mimeFormats={event.mimeData().formats()}")
        if event.mimeData().hasFormat("application/x-layerbutton-index"):
            # Explicitly set drop action to Move to ensure cross-platform consistency (macOS fix)
            event.setDropAction(Qt.MoveAction)
            event.accept()
            logging.debug("Drag enter accepted (MoveAction)")
        else:
            event.ignore()
            logging.debug("Drag enter ignored - wrong mime type")

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Accept the move event. Visual indicator is handled by DropTargetWidget."""
        # Extra diagnostics for macOS during drag move
        if sys.platform == 'darwin':
            logging.info(f"[macOS] dragMoveEvent: pos={event.pos()} proposedAction={event.proposedAction()} "
                         f"possibleActions={event.possibleActions()}")
        if event.mimeData().hasFormat("application/x-layerbutton-index"):
            event.acceptProposedAction()
            # Visual feedback is now handled by DropTargetWidget.paintEvent
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leaving the drop area."""
        # Reset indicator logic might be needed if DropTargetWidget doesn't cover all cases
        logging.debug("Drag left drop area")

    def dropEvent(self, event: QDropEvent):
        """Handle the drop event to reorder layers visually and update data structures."""
        # Extra diagnostics for macOS at the start of the drop
        if sys.platform == 'darwin':
            logging.info(f"[macOS] dropEvent START: pos={event.pos()} dropAction={event.dropAction()} "
                         f"proposedAction={event.proposedAction()} mimeFormats={event.mimeData().formats()}")
        if event.mimeData().hasFormat("application/x-layerbutton-index"):
            mime_data = event.mimeData()
            source_index_bytes = mime_data.data("application/x-layerbutton-index")
            try:
                # source_index is the VISUAL index in the scroll_layout
                source_index = int(bytes(source_index_bytes).decode('utf-8'))
            except ValueError:
                logging.error("Failed to decode drop source index.")
                event.ignore()
                return

            # Ensure source_index is valid before proceeding
            if not (0 <= source_index < self.scroll_layout.count()):
                logging.error(f"Invalid source index {source_index} from drop event.")
                event.ignore()
                return

            # --- Store the selected strand object BEFORE any reordering ---
            previously_selected_strand = self.canvas.selected_strand

            # --- Create mapping from button object to strand object --- BEFORE layout change
            button_to_strand_map = {}
            if len(self.layer_buttons) == len(self.canvas.strands):
                # Assuming self.layer_buttons[i] maps to self.canvas.strands[i]
                # and visual layout index k maps to layer_buttons[len-1-k]
                for i, btn in enumerate(self.layer_buttons):
                     button_to_strand_map[btn] = self.canvas.strands[i]
            else:
                logging.error("Button/Strand count mismatch before drop! Aborting reorder.")
                event.ignore()
                self.refresh() # Refresh to fix inconsistency
                return

            # --- Determine visual target index for insertion --- 
            drop_pos = event.pos()
            target_visual_index = 0
            layout_item_count = self.scroll_layout.count()
            if layout_item_count > 0:
                target_visual_index = layout_item_count # Default to bottom
                for i in range(layout_item_count):
                    item = self.scroll_layout.itemAt(i)
                    widget = item.widget()
                    if not widget:
                        continue
                    # Use mapToGlobal and mapFromGlobal for reliable coordinates within the scroll area
                    widget_global_top_left = widget.mapToGlobal(QPoint(0, 0))
                    widget_local_top_left = self.scroll_content.mapFromGlobal(widget_global_top_left)
                    widget_rect_in_scroll = QRect(widget_local_top_left, widget.size())
                    widget_center_y = widget_rect_in_scroll.y() + widget_rect_in_scroll.height() / 2
                    if drop_pos.y() < widget_center_y:
                        target_visual_index = i # Insert before this widget
                        break

            # --- Move the widget in the layout (macOS-safe) ---
            item_to_move = self.scroll_layout.takeAt(source_index)
            if not item_to_move:
                 logging.error(f"Could not get item at source index {source_index} to move.")
                 event.ignore()
                 return

            # Extract the actual widget from the QLayoutItem *before* deleting the item.
            widget_to_move = item_to_move.widget()
            # It is critical to delete the QLayoutItem instance after extracting the widget;
            # re-using the same QLayoutItem by insertItem() can double-delete native resources
            # on some Qt platforms (observed crash on macOS).
            del item_to_move  # Prevent dangling pointer / double-free

            # --- Adjust insertion index based on drag direction ---
            final_insert_index = target_visual_index
            if source_index < target_visual_index:
                final_insert_index -= 1 # Adjust because takeAt shifted items up

            # --- Insert the widget directly (safer than re-using QLayoutItem) ---
            self.scroll_layout.insertWidget(final_insert_index, widget_to_move, 0, Qt.AlignHCenter)
            widget_to_move.show()
            logging.info(f"Moved widget from visual index {source_index} to final insert index {final_insert_index} (widget re-inserted)")

            # --- Rebuild canvas.strands based on NEW VISUAL order using the map ---
            new_canvas_strands_visual_order = []
            success = True
            for i in range(self.scroll_layout.count()):
                item = self.scroll_layout.itemAt(i)
                button = item.widget() # Get the widget directly
                if isinstance(button, NumberedLayerButton): # Check if it's the button
                    if button in button_to_strand_map:
                        new_canvas_strands_visual_order.append(button_to_strand_map[button])
                    else:
                        logging.error(f"Button {button.text()} at new visual index {i} not found in map! Aborting.")
                        success = False
                        break
                else:
                     # Log an error if the widget isn't a NumberedLayerButton
                     logging.error(f"Widget at layout index {i} is not a NumberedLayerButton (Type: {type(button)}). Aborting.")
                     success = False
                     break

            if not success:
                logging.error("Failed to rebuild canvas strands after drop. Attempting full refresh.")
                event.ignore()
                self.refresh()
                return

            # --- Commit the new order (Reverse visual order for canvas) --- 
            self.canvas.strands = new_canvas_strands_visual_order[::-1]
            logging.info(f"Reordered canvas.strands based on new visual layout. New count: {len(self.canvas.strands)}")
            # self.layer_buttons will be rebuilt correctly by refresh()

            # --- Update LayerStateManager state --- 
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.save_current_state() # Update state based on new canvas.strands order
                logging.info(f"Updated LayerStateManager state after drop.")
            else:
                logging.warning("LayerStateManager not found on canvas, cannot update state after drop.")

            # --- Update canvas selection index based on the stored object --- 
            if previously_selected_strand:
                try:
                    # Find the new index in the reordered canvas.strands list
                    new_selected_index = self.canvas.strands.index(previously_selected_strand)
                    self.canvas.selected_strand_index = new_selected_index
                    # Keep the selected_strand object consistent
                    self.canvas.selected_strand = previously_selected_strand
                    logging.info(f"Selection index updated to {new_selected_index} for strand {previously_selected_strand.layer_name} after reorder.")
                except ValueError:
                    logging.warning("Previously selected strand not found after reorder. Clearing selection.")
                    self.canvas.selected_strand = None
                    self.canvas.selected_strand_index = None
            else:
                 # No strand was selected before the drop
                 self.canvas.selected_strand = None
                 self.canvas.selected_strand_index = None
                 logging.info("No strand was selected before drop, ensuring selection is clear.")

            # --- Accept the event action FIRST ---
            event.acceptProposedAction()
            logging.info("Drop event action accepted.")
            if sys.platform == 'darwin':
                logging.info("[macOS] dropEvent: accepted proposed action, scheduling UI refresh.")

            # --- THEN, refresh the UI. On macOS, defer to the next event-loop cycle to avoid crash; on other OS refresh immediately ---
            if sys.platform == 'darwin':
                QTimer.singleShot(0, self.refresh)
            else:
                self.refresh()
            logging.info("UI refreshed after drop to show reordered layers (platform-specific logic applied).")

            # --- FINALLY, save the state AFTER refreshing ---
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                logging.info("Saving state AFTER refreshing UI post-reorder")
                self.undo_redo_manager.save_state()

        else:
            event.ignore()
            logging.info("Drop ignored - wrong mime type")

    # --- Helper to calculate indicator line position ---
    def calculate_drop_indicator_y(self, drop_pos):
        """Calculate the Y position for the drop indicator line."""
        target_y = -1
        # Iterate through layout items (button containers) to find insertion point based on vertical position
        current_y = 0
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if not widget:
                continue

            widget_rect = widget.geometry()
            widget_height = widget_rect.height()
            widget_top_y = widget_rect.y()

            # Calculate midpoint Y of the *widget* itself
            widget_center_y = widget_top_y + widget_height / 2

            if drop_pos.y() < widget_center_y:
                # Drop position is above the center of this widget, line goes above it
                target_y = widget_top_y - (self.scroll_layout.spacing() / 2)
                break
            else:
                # Drop position is below center, potential line goes below it
                target_y = widget_top_y + widget_height + (self.scroll_layout.spacing() / 2)
                # Keep iterating in case it's above the next one

        # Ensure target_y is within bounds (adjust slightly if needed)
        if target_y < 0:
             target_y = self.scroll_layout.spacing() / 2 # Line at the very top
        elif target_y > self.scroll_content.height():
             target_y = self.scroll_content.height() - self.scroll_layout.spacing() / 2 # Line at the very bottom

        return int(target_y)
    # --- End Helper ---

    def get_strand_for_button(self, button):
        """Find the canvas strand corresponding to a button."""
        try:
            index = self.layer_buttons.index(button)
            if 0 <= index < len(self.canvas.strands):
                return self.canvas.strands[index]
        except ValueError:
            pass # Button not found in list
        except IndexError:
             pass # Index out of bounds for canvas strands
        logging.warning(f"Could not find strand for button: {button.text() if button else 'None'}")
        return None

    def show_masked_layer_context_menu(self, strand_index, pos):
        """Delegate masked-layer context menu display to the corresponding button.

        This wrapper restores compatibility with older lambda connections that
        expect a LayerPanel.show_masked_layer_context_menu method.  It simply
        forwards the call to the NumberedLayerButton's own show_context_menu,
        which already handles masked-layer specific actions.
        """
        if 0 <= strand_index < len(self.layer_buttons):
            button = self.layer_buttons[strand_index]
            # Ensure the button exists and is a NumberedLayerButton
            try:
                button.show_context_menu(pos)
            except Exception as e:
                logging.error(f"Error showing context menu for masked layer button at index {strand_index}: {e}")

# End of LayerPanel class

# Note: The StrokeTextButton class has been moved to stroke_text_button.py
# to avoid circular imports