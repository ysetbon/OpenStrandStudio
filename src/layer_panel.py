# src/layer_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QScrollArea, QLabel, QSplitter, QInputDialog, QMenu, QAction, QWidgetAction, QToolTip, QFrame  # Add QMenu, QAction and QWidgetAction here
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QStandardPaths, QMimeData  ,QRect# Added QMimeData
from PyQt5.QtGui import QColor, QPalette, QDrag, QGuiApplication, QCursor # Added QDrag and QGuiApplication
# --- Import Correct Drag/Drop Event Types --- 
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QPainter, QPen # Added Painter/Pen
from render_utils import RenderUtils
# --- End Import ---
from functools import partial
import logging
from masked_strand import MaskedStrand
from safe_logging import safe_info, safe_warning, safe_error, safe_exception
from attached_strand import AttachedStrand
from translations import translations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QLabel,
    QInputDialog, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QSplitter, QSizePolicy
)
from PyQt5.QtCore import QEventLoop          #  ← add this import

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import logging
from functools import partial
from splitter_handle import SplitterHandle
from numbered_layer_button import NumberedLayerButton, HoverLabel
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

class CustomTooltip(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.is_hebrew = False
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        # Remove translucent background to allow proper border rendering
        # self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Apply minimal global tooltip styling
        self.setStyleSheet("""
            QToolTip QLabel, QFrame QLabel {
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove all layout margins
        layout.setSpacing(0)  # Remove spacing between layout items
        self.label = QLabel(text)
        self.label.setWordWrap(False)
        self.label.setAlignment(Qt.AlignCenter)  # Center both horizontally and vertically
        # Use negative margins to counteract Qt's internal text spacing
        self.label.setStyleSheet("QLabel { margin: -2px -6px -2px -6px; padding: 0px; border: none; line-height: 1.0; text-align: center; }")
        layout.addWidget(self.label)
        
        # Auto-hide timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide)
        self.timer.setSingleShot(True)
        
        # Set text and update theme after layout is set up
        self.setText(text)
        self.updateTheme()
        
    def updateTheme(self):
        # Get the current theme from parent window
        current_theme = 'default'
        parent = self.parent()
        while parent:
            if hasattr(parent, 'current_theme'):
                current_theme = parent.current_theme
                break
            elif hasattr(parent, 'parent_window') and hasattr(parent.parent_window, 'current_theme'):
                current_theme = parent.parent_window.current_theme
                break
            parent = parent.parent()
        
        # Define theme-specific colors to match application theme
        if current_theme == "dark":
            bg_color = QColor("#2C2C2C")        # Match app's dark theme background
            text_color = QColor("#FFFFFF")      # White text
            border_color = QColor("#555555")    # Medium gray border for visibility
        elif current_theme == "light":
            bg_color = QColor("#FFFFFF")        # Pure white background
            text_color = QColor("#000000")      # Black text
            border_color = QColor("#CCCCCC")    # Light gray border
        else:  # default theme
            bg_color = QColor("#F0F0F0")        # Light gray background
            text_color = QColor("#000000")      # Black text
            border_color = QColor("#888888")    # Medium gray border
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color.name()} !important;
                border: 2px solid {border_color.name()} !important;
                border-radius: 0px !important;
                padding: 1px !important;
                margin: 0px !important;
                color: {text_color.name()} !important;
            }}
            QFrame QLabel {{
                margin: 0px !important;
                padding: 0px !important;
                border: none !important;
                background: transparent !important;
            }}
        """)
        
        # Ensure the label still has tight spacing even after theme update
        if hasattr(self, 'label'):
            self.label.setStyleSheet("QLabel { margin: 0px; padding: 0px; border: none; line-height: 1.0; text-align: center; }")
        
    def setText(self, text):
        self.text = text
        # Check if text contains Hebrew characters (for reference only)
        self.is_hebrew = any('\u0590' <= char <= '\u05FF' for char in text)
        
        if hasattr(self, 'label'):
            self.label.setText(text)
            # Center text for all languages
            self.label.setAlignment(Qt.AlignCenter)
            # Use left-to-right layout direction for consistent display
            self.label.setLayoutDirection(Qt.LeftToRight)
            self.setLayoutDirection(Qt.LeftToRight)
            # Ensure compact styling is maintained with centered text
            self.label.setStyleSheet("QLabel { margin: -2px -6px -2px -6px; padding: 0px; border: none; line-height: 1.0; text-align: center; }")
            
    def showAt(self, pos, timeout=0):
        self.updateTheme()  # Update theme colors before showing
        self.adjustSize()
        self.move(pos)
        self.show()
        self.raise_()
        if timeout > 0:
            self.timer.start(timeout)

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
            safe_info(f"[LayerPanel.paintEvent] Setting up UI painter for drag indicator")
            RenderUtils.setup_ui_painter(painter)
            pen = QPen(QColor(0, 120, 215), 2, Qt.SolidLine) # Blue indicator line
            painter.setPen(pen)
            painter.drawLine(0, self._drag_indicator_y, self.width(), self._drag_indicator_y)
            painter.end()
# --- End Custom Widget ---


class TooltipButton(QPushButton):
    """Custom button that shows tooltip on right-click instead of hover"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.custom_tooltip = ""
        # Disable default tooltip behavior
        self.setToolTip("")
        
    def set_custom_tooltip(self, text):
        """Set the custom tooltip text"""
        self.custom_tooltip = text
        # Make sure default tooltip is disabled
        self.setToolTip("")
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.RightButton:
            logging.info(f"Right-click press detected on TooltipButton. Tooltip text: '{self.custom_tooltip}'")
            
            if self.custom_tooltip:
                # Find the LayerPanel to get the panel's position and size
                layer_panel = None
                parent = self.parent()
                while parent:
                    if parent.__class__.__name__ == 'LayerPanel':
                        layer_panel = parent
                        break
                    parent = parent.parent()
                
                if layer_panel:
                    # Get the LayerPanel's position and size
                    panel_global_pos = layer_panel.mapToGlobal(QPoint(0, 0))
                    panel_size = layer_panel.size()
                    
                    # Simple 4th row calculation: 3 rows down from panel top
                    fourth_row_y = panel_global_pos.y() + 200  # 3 rows * 40px + 3 gaps * 5px
                    
                    # Find the center X based on hide button and refresh button positions
                    # Get the hide button (multi_select_button) and refresh button positions
                    hide_button = getattr(layer_panel, 'multi_select_button', None)
                    refresh_button = getattr(layer_panel, 'refresh_button', None)
                    
                    if hide_button and refresh_button:
                        # Get the global positions of both buttons
                        hide_global_pos = hide_button.mapToGlobal(QPoint(0, 0))
                        refresh_global_pos = refresh_button.mapToGlobal(QPoint(0, 0))

                        # Calculate the center between these two buttons
                        # Get the actual content area of buttons, excluding any extra spacing
                        hide_left = hide_global_pos.x()
                        hide_right = hide_global_pos.x() + hide_button.width()
                        refresh_left = refresh_global_pos.x()
                        refresh_right = refresh_global_pos.x() + refresh_button.width()
                        
                        # Calculate center point between the two button regions
                        center_x = (hide_right + refresh_left) // 2

                        # Create and show custom tooltip at exact position
                        # Always recreate the tooltip to ensure consistent styling
                        if hasattr(self, '_custom_tooltip_widget'):
                            self._custom_tooltip_widget.hide()
                            self._custom_tooltip_widget.deleteLater()
                        
                        self._custom_tooltip_widget = CustomTooltip("", None)
                        self._custom_tooltip_widget.setText(self.custom_tooltip)
                        # Force theme update to ensure proper styling
                        self._custom_tooltip_widget.updateTheme()
                        self._custom_tooltip_widget.adjustSize()
                        
                        # Position tooltip so its center aligns exactly with center_x
                        tooltip_width = self._custom_tooltip_widget.width()
                        tooltip_pos = QPoint(
                            center_x - tooltip_width // 2,
                            fourth_row_y
                        )
                        
                        self._custom_tooltip_widget.showAt(tooltip_pos, timeout=0)  # No auto-hide
                    
            event.accept()
            return
        
        # For left-click or other buttons, process normally
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.RightButton:
            # Hide tooltip immediately when right-click is released
            if hasattr(self, '_custom_tooltip_widget'):
                self._custom_tooltip_widget.hide()
            event.accept()
            return
        
        # For left-click or other buttons, process normally
        super().mouseReleaseEvent(event)
            
    def event(self, event):
        """Override event to disable hover tooltips"""
        if event.type() == event.ToolTip:
            # Ignore tooltip events
            return True
        return super().event(event)


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
        safe_info(f"LayerPanel: Base path for data determined as: {self.base_path}")

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

        # Create the home/reset button (moved from 3rd row)
        self.reset_states_button = TooltipButton("🏠")
        self.reset_states_button.setFixedSize(40, 40)
        self.reset_states_button.setStyleSheet("""
            QPushButton {
                background-color: #8A2BE2;  /* BlueViolet color */
                color: white;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #6A1B9A;
                border-radius: 20px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #DA70D6;  /* Orchid - brighter, more vibrant purple */
                border: 2px solid #8A2BE2;
                transform: scale(1.05);  /* Slight scale effect */
            }
            QPushButton:pressed {
                background-color: #663399;  /* Darker purple on press */
                border: 2px solid #6A1B9A;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        self.reset_states_button.clicked.connect(self.reset_to_current_state)
        _ = translations[self.language_code]
        self.set_button_tooltip(self.reset_states_button, _['reset_tooltip'])

        # Add the home/reset button to the top layout
        top_layout.addWidget(self.reset_states_button)
        
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
        self.zoom_in_button = TooltipButton("🔍")
        self.zoom_in_button.setFixedSize(40, 40)
        self.zoom_in_button.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;  /* Yellowish color */
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #B8860B;
                border-radius: 20px;
                padding: 0px;
                text-align: center;
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
        _ = translations[self.language_code]
        self.set_button_tooltip(self.zoom_in_button, _['zoom_in_tooltip'])
        
        # Create zoom out button
        self.zoom_out_button = TooltipButton("🔎")
        self.zoom_out_button.setFixedSize(40, 40)
        self.zoom_out_button.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;  /* Yellowish color */
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #B8860B;
                border-radius: 20px;
                padding: 0px;
                text-align: center;
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
        _ = translations[self.language_code]
        self.set_button_tooltip(self.zoom_out_button, _['zoom_out_tooltip'])
        
        # Create pan button
        self.pan_button = TooltipButton("🖐")  # Using a more modern hand emoji
        self.pan_button.setFixedSize(40, 40)
        self.pan_button.setCheckable(True)  # Make it toggleable
        self.pan_button.clicked.connect(self.toggle_pan_mode)
        _ = translations[self.language_code]
        self.set_button_tooltip(self.pan_button, _['pan_tooltip'])
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
                background-color: #DC143C;  /* Crimson - brighter, more vibrant red */
                border: 2px solid #8B0000;
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

        # Create a third row for refresh button (moved from 1st row)
        self.refresh_panel = QWidget()
        refresh_layout = QHBoxLayout(self.refresh_panel)
        refresh_layout.setContentsMargins(5, 0, 5, 5)  # No top margin since it's below the second row
        refresh_layout.setAlignment(Qt.AlignLeft)
        
        # Create the refresh button (moved from 1st row)
        self.refresh_button = TooltipButton("🔄")
        self.refresh_button.setFixedSize(40, 40)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #32CD32;  /* Lime Green color */
                color: white;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #228B22;
                border-radius: 20px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #00FF00;  /* Bright Green on hover */
                border: 2px solid #228B22;
            }
            QPushButton:pressed {
                background-color: #228B22;  /* Forest Green on press */
                border: 2px solid #228B22;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_layers)
        _ = translations[self.language_code]
        self.set_button_tooltip(self.refresh_button, _['refresh_tooltip'])
        
        # Create the center/pan button
        self.center_strands_button = TooltipButton("🎯")
        self.center_strands_button.setFixedSize(40, 40)
        self.center_strands_button.setStyleSheet("""
            QPushButton {
                background-color: #D2B48C;  /* Tan/Light brown color */
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #BC9A6A;
                border-radius: 20px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #CD853F;  /* Peru - medium brown, not too dark */
                color: black;  /* Keep black text for better readability */
                border: 2px solid #A0522D;
            }
            QPushButton:pressed {
                background-color: #654321;  /* Dark Brown - even darker on press */
                color: white;
                border: 2px solid #A0522D;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        self.center_strands_button.clicked.connect(self.center_all_strands)
        _ = translations[self.language_code]
        self.set_button_tooltip(self.center_strands_button, _['center_tooltip'])

        # Create the multi-select button
        self.multi_select_button = TooltipButton("🙉")
        self.multi_select_button.setFixedSize(40, 40)
        self.multi_select_button.setCheckable(True)  # Make it toggleable
        self.multi_select_button.setStyleSheet("""
            QPushButton {
                background-color: #D2B48C;  /* Tan/Light brown color - same as target */
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #BC9A6A;
                border-radius: 20px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #CD853F;  /* Peru - medium brown, same as target */
                color: black;
                border: 2px solid #A0522D;
            }
            QPushButton:pressed {
                background-color: #654321;  /* Dark Brown - same as target */
                color: white;
                border: 2px solid #A0522D;
            }
            QPushButton:checked {
                background-color: #654321;  /* Dark Brown when active - same as target */
                color: white;
                border: 2px solid #A0522D;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
                border: 1px solid #A9A9A9;
            }
        """)
        self.multi_select_button.clicked.connect(self.toggle_multi_select_mode)
        _ = translations[self.language_code]
        self.set_button_tooltip(self.multi_select_button, _['hide_mode_tooltip'])

        # Add buttons to refresh layout
        refresh_layout.addWidget(self.refresh_button)
        refresh_layout.addWidget(self.center_strands_button)
        refresh_layout.addWidget(self.multi_select_button)
        
        # Add refresh panel to left layout below the zoom panel
        self.left_layout.addWidget(self.refresh_panel)

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
        _ = translations[self.language_code]
        self.draw_names_button = QPushButton(_['draw_names'])
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
        self.lock_layers_button = QPushButton(_['lock_layers'])
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
        self.add_new_strand_button = QPushButton(_['add_new_strand'])
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
            QPushButton:disabled {
                background-color: #D3D3D3; /* Gray background when disabled */
                color: #666666; /* Darker gray text when disabled */
                border: 1px solid #CCCCCC; /* Light gray border when disabled */
            }
        """)
        self.add_new_strand_button.clicked.connect(self.request_new_strand)

        # Delete Strand button
        self.delete_strand_button = QPushButton(_['delete_strand'])
        self.delete_strand_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                color: black;
                background-color: #FF6B6B;
                border: 1px solid #888;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF4C4C; /* Lighter red on hover */
            }
            QPushButton:pressed {
                background-color: #FF0000; /* Darker red on click */
            }
            QPushButton:disabled {
                background-color: #D3D3D3; /* Gray background when disabled */
                color: #666666; /* Darker gray text when disabled */
                border: 1px solid #CCCCCC; /* Light gray border when disabled */
            }
        """)
        self.delete_strand_button.setEnabled(False)
        
        # Add debugging for mouse events on the button
        def debug_button_click():
            logging.info("=== DELETE BUTTON CLICKED ===")
            self.request_delete_strand()
            
        def debug_button_press(event):
            logging.info(f"=== DELETE BUTTON PRESS EVENT === at {event.pos()}")
            
        def debug_button_release(event):
            logging.info(f"=== DELETE BUTTON RELEASE EVENT === at {event.pos()}")
            
        # Override button events for debugging
        original_mousePressEvent = self.delete_strand_button.mousePressEvent
        original_mouseReleaseEvent = self.delete_strand_button.mouseReleaseEvent
        
        def new_mousePressEvent(event):
            debug_button_press(event)
            original_mousePressEvent(event)
            
        def new_mouseReleaseEvent(event):
            debug_button_release(event)
            original_mouseReleaseEvent(event)
            
        self.delete_strand_button.mousePressEvent = new_mousePressEvent
        self.delete_strand_button.mouseReleaseEvent = new_mouseReleaseEvent
        
        self.delete_strand_button.clicked.connect(debug_button_click)

        # Deselect All button
        self.deselect_all_button = QPushButton(_['deselect_all'])
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
        
        # Multi-selection state
        self.multi_select_mode = False  # Whether multi-select mode is active
        self.multi_selected_layers = set()  # Set of selected layer indices
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

        # Initialize button texts with the correct language
        self.update_translations()

        safe_info("LayerPanel initialized")

    def refresh_layers(self):
        """Refresh the drawing of the layers with zero visual flicker."""
        safe_info("Starting refresh of layer panel")
        overlay = None  # Snapshot overlay that masks flicker on Windows

        safe_info("refresh_layers called, redirecting to refresh()")
        self.refresh()
        # Reset canvas zoom and pan to original view
        self.canvas.reset_zoom()
    
    def refresh_layers_no_zoom(self):
        """Refresh the drawing of the layers without resetting zoom/pan. Used for strand attachment."""
        safe_info("[FLASH_DEBUG] refresh_layers_no_zoom: Begin")
        safe_info("refresh_layers_no_zoom called, redirecting to refresh()")
        self.refresh()
        # Intentionally not resetting zoom to preserve state during strand attachment
    
    def refresh_after_attachment(self):
        """Complete refresh after strand attachment without resetting zoom/pan.
        This function does everything refresh_layers does except the zoom reset and overlay."""
        safe_info("refresh_after_attachment called - refreshing without zoom reset and overlay")
        
        # Get the main window reference
        main_window = self.parent_window if hasattr(self, 'parent_window') and self.parent_window else self.parent()
        
        # Suppress full-window repaint only on macOS; on Windows/Linux it causes a white flash
        if sys.platform == 'darwin' and main_window:
            main_window.setUpdatesEnabled(False)
            # Suspend painting on the scroll area / its viewport only on macOS – doing this on
            # Windows/Linux produces a short blank frame (the white-flash we are chasing).
            self.scroll_area.setUpdatesEnabled(False)
            if hasattr(self.scroll_area, 'viewport'):
                self.scroll_area.viewport().setUpdatesEnabled(False)
        
        # Simplified refresh without overlay for attach mode to prevent temporary window
        # Just rebuild the layer buttons without visual effects
        removed_count = 0
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                removed_count += 1
            del item
        
        # Re-add buttons in reverse order
        added_count = 0
        valid_buttons = [btn for btn in self.layer_buttons if btn]
        for button in reversed(valid_buttons):
            self.scroll_layout.addWidget(button, 0, Qt.AlignHCenter)
            button.show()
            added_count += 1
        
        # Update layout and canvas
        self.scroll_layout.update()
        self.canvas.update()  # Just update the canvas without changing zoom/pan
        
        # Re-enable updates after refresh (only on macOS)
        if sys.platform == 'darwin':
            if hasattr(self.scroll_area, 'viewport'):
                self.scroll_area.viewport().setUpdatesEnabled(True)
            self.scroll_area.setUpdatesEnabled(True)
            if main_window:
                main_window.setUpdatesEnabled(True)

    def create_layer_button(self, index, strand, count):
        """Create a layer button for the given strand."""
        button = NumberedLayerButton(strand.layer_name, count, strand.color)
        button.clicked.connect(partial(self.select_layer, index))
        button.color_changed.connect(self.on_color_changed)
        
        # Add right-click context menu for multi-selection
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(partial(self.show_multi_select_context_menu, index))

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
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
                QPushButton:disabled {
                    background-color: #D3D3D3; /* Gray background when disabled */
                    color: #666666; /* Darker gray text when disabled */
                    border: 1px solid #CCCCCC; /* Light gray border when disabled */
                }
            """)
            # Apply theme to refresh button (now QPushButton, no set_theme method needed)
            # self.refresh_button.set_theme(theme_name)  # Commented out - QPushButton doesn't have set_theme
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
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
                QPushButton:disabled {
                    background-color: #D3D3D3; /* Gray background when disabled */
                    color: #666666; /* Darker gray text when disabled */
                    border: 1px solid #CCCCCC; /* Light gray border when disabled */
                }
            """)
            # Apply theme to refresh button (now QPushButton, no set_theme method needed)
            # self.refresh_button.set_theme(theme_name)  # Commented out - QPushButton doesn't have set_theme
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
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
                QPushButton:disabled {
                    background-color: #D3D3D3; /* Gray background when disabled */
                    color: #666666; /* Darker gray text when disabled */
                    border: 1px solid #CCCCCC; /* Light gray border when disabled */
                }
            """)
            # Apply theme to refresh button (now QPushButton, no set_theme method needed)
            # self.refresh_button.set_theme(theme_name)  # Commented out - QPushButton doesn't have set_theme
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
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
                QPushButton:disabled {
                    background-color: #D3D3D3; /* Gray background when disabled */
                    color: #666666; /* Darker gray text when disabled */
                    border: 1px solid #CCCCCC; /* Light gray border when disabled */
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
    def set_language(self, language_code):
        """Update the layer panel's language and refresh any UI elements that need translation updates"""
        self.language_code = language_code
        # Update button texts with the new language
        self.update_translations()
        # Update group layer manager language if it exists
        if hasattr(self, 'group_layer_manager') and self.group_layer_manager:
            self.group_layer_manager.language_code = language_code
            if hasattr(self.group_layer_manager, 'update_translations'):
                self.group_layer_manager.update_translations()

    def calculate_menu_width(self, menu_texts):
        """Calculate optimal menu width based on text content"""
        from PyQt5.QtGui import QFontMetrics, QFont
        
        # Create font to measure text
        font = QFont()
        font.setPointSize(8)  # Match menu font size
        metrics = QFontMetrics(font)
        
        max_width = 150  # Minimum width
        padding = 20  # Account for padding, margins, and potential icons
        
        for text in menu_texts:
            text_width = metrics.horizontalAdvance(text) + padding
            max_width = max(max_width, text_width)
        
        # Cap maximum width to prevent extremely wide menus
        return min(max_width, 350)

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
            safe_warning(f"show_layer_context_menu called with invalid index: {strand_index}")
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
        # Use screen-aware positioning for multi-monitor support
        global_pos = self.get_screen_aware_global_pos(button, position)
        menu.exec_(global_pos)
        
    def get_screen_aware_global_pos(self, widget, pos):
        """
        Get global position accounting for multi-monitor DPI differences.
        
        Args:
            widget: The widget to get position relative to
            pos (QPoint): Local position relative to the widget
            
        Returns:
            QPoint: Screen-aware global position
        """
        try:
            # Get basic global position
            basic_global = widget.mapToGlobal(pos)
            
            # Find which screen this widget is on
            widget_screen = None
            widget_global_rect = widget.geometry()
            widget_global_rect.moveTopLeft(widget.mapToGlobal(QPoint(0, 0)))
            
            screens = QGuiApplication.screens()
            for screen in screens:
                if screen.geometry().intersects(widget_global_rect):
                    widget_screen = screen
                    break
            
            if not widget_screen:
                widget_screen = QGuiApplication.primaryScreen()
            
            # For multi-monitor setups with different DPI, ensure proper positioning
            screen_rect = widget_screen.availableGeometry()
            
            # Adjust position if it would place menu outside screen bounds
            adjusted_pos = QPoint(basic_global)
            
            # If menu would go off right edge of screen, move it left
            menu_width = 250  # Estimated menu width - increased to accommodate longer text
            if adjusted_pos.x() + menu_width > screen_rect.right():
                adjusted_pos.setX(screen_rect.right() - menu_width)
            
            # If menu would go off bottom edge of screen, move it up  
            menu_height = 200  # Estimated menu height - increased for better spacing
            if adjusted_pos.y() + menu_height > screen_rect.bottom():
                adjusted_pos.setY(screen_rect.bottom() - menu_height)
                
            # Ensure position is at least within screen bounds
            if adjusted_pos.x() < screen_rect.left():
                adjusted_pos.setX(screen_rect.left())
            if adjusted_pos.y() < screen_rect.top():
                adjusted_pos.setY(screen_rect.top())
                
            return adjusted_pos
            
        except Exception as e:
            logging.warning(f"Error in screen-aware positioning: {e}, falling back to basic mapToGlobal")
            return widget.mapToGlobal(pos)

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
                self.refresh_layers_no_zoom() # Preserve zoom/pan when toggling layer visibility
            button.set_hidden(strand.is_hidden) # Call the button's method

            # Save the current state to persist visibility changes
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.save_current_state()
                logging.info(f"Updated LayerStateManager state after visibility toggle.")
            else:
                logging.warning("LayerStateManager not found on canvas, cannot update state after visibility toggle.")

            self.canvas.update() # Redraw canvas to reflect the change

        else:
            logging.warning(f"toggle_layer_visibility called with invalid index: {strand_index}")
    # --- END NEW ---

    def toggle_layer_shadow_only(self, strand_index):
        """Toggles the shadow-only mode of the strand at the given index."""
        if 0 <= strand_index < len(self.canvas.strands):
            strand = self.canvas.strands[strand_index]
            # Toggle shadow-only mode
            strand.shadow_only = not getattr(strand, 'shadow_only', False)
            logging.info(f"Toggled shadow-only for strand {strand.layer_name} to shadow_only={strand.shadow_only}")
            
            # Update button appearance to reflect shadow-only state
            button = self.layer_buttons[strand_index]
            button.set_shadow_only(strand.shadow_only)
            
            # Redraw canvas to reflect the change
            self.canvas.update()

            # Save the current state to persist shadow-only changes
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.save_current_state()
                logging.info(f"Updated LayerStateManager state after shadow-only toggle.")
            else:
                logging.warning("LayerStateManager not found on canvas, cannot update state after shadow-only toggle.")

            # Save state for undo/redo functionality
            if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
                # Force save by resetting timing check to ensure shadow-only changes are captured
                self.canvas.undo_redo_manager._last_save_time = 0
                self.canvas.undo_redo_manager.save_state()
                logging.info(f"Saved undo/redo state after shadow-only toggle for strand {strand.layer_name}")
            else:
                logging.warning("UndoRedoManager not found on canvas, cannot save undo/redo state for shadow-only toggle.")

        else:
            logging.warning(f"toggle_layer_shadow_only called with invalid index: {strand_index}")
    

    def set_button_tooltip(self, button, tooltip_text):
        """Set tooltip for custom TooltipButton with center alignment"""
        logging.info(f"Setting tooltip '{tooltip_text}' for button {button.__class__.__name__}")
        # For TooltipButton instances, use the custom tooltip method
        if isinstance(button, TooltipButton):
            button.set_custom_tooltip(tooltip_text)
            logging.info(f"Set custom tooltip for TooltipButton: '{tooltip_text}'")
        else:
            # Fallback for regular buttons (shouldn't happen)
            button.setToolTip(tooltip_text)
            logging.info(f"Set regular tooltip for button: '{tooltip_text}'")
    
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

    def update_translations(self):
        """Update the UI texts to the selected language."""
        _ = translations[self.language_code]
        
        # Update any UI elements with new translations
        self.draw_names_button.setText(_['draw_names'])
        
        # Handle lock button text based on current lock mode state
        if hasattr(self, 'lock_mode') and self.lock_mode:
            self.lock_layers_button.setText(_['exit_lock_mode'])
        else:
            self.lock_layers_button.setText(_['lock_layers'])
            
        self.add_new_strand_button.setText(_['add_new_strand'])
        self.delete_strand_button.setText(_['delete_strand'])
        
        # Handle deselect button text based on current lock mode state
        if hasattr(self, 'lock_mode') and self.lock_mode:
            self.deselect_all_button.setText(_['clear_all_locks'])
        else:
            self.deselect_all_button.setText(_['deselect_all'])
            
        # Update button tooltips
        self.set_button_tooltip(self.reset_states_button, _['reset_tooltip'])
        self.set_button_tooltip(self.refresh_button, _['refresh_tooltip'])
        self.set_button_tooltip(self.center_strands_button, _['center_tooltip'])
        self.set_button_tooltip(self.multi_select_button, _['hide_mode_tooltip'])
        self.set_button_tooltip(self.zoom_in_button, _['zoom_in_tooltip'])
        self.set_button_tooltip(self.zoom_out_button, _['zoom_out_tooltip'])
        self.set_button_tooltip(self.pan_button, _['pan_tooltip'])
        # Update other text elements as needed

        # Update the GroupLayerManager
        if self.group_layer_manager:
            self.group_layer_manager.language_code = self.language_code
            self.group_layer_manager.update_translations()

    def translate_ui(self):
        """Alias for update_translations to maintain compatibility with main window calls"""
        self.update_translations()

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

    def reset_to_current_state(self):
        """Reset the undo/redo history, keeping only the current state as the first state."""
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            logging.info("Resetting states: keeping only current state as first state")
            self.undo_redo_manager.clear_history(save_current=True)
            logging.info("Reset completed: Current state is now the only state in history")

    def center_all_strands(self):
        """Center all strands in the canvas by calculating their bounding box and adjusting pan offset."""
        if hasattr(self.canvas, 'center_all_strands'):
            logging.info("Centering all strands in canvas")
            self.canvas.center_all_strands()
        else:
            logging.warning("Canvas does not have center_all_strands method")

    def toggle_multi_select_mode(self):
        """Toggle multi-selection mode on/off"""
        self.multi_select_mode = not self.multi_select_mode
        
        if self.multi_select_mode:
            logging.info("Multi-select mode enabled")
            # Change to hide mode emoji when active
            self.multi_select_button.setText("🙈")
            # Clear any existing selections when entering multi-select mode
            self.multi_selected_layers.clear()
            self.update_layer_button_multi_select_display()
        else:
            logging.info("Multi-select mode disabled")
            # Change back to hear-no-evil emoji when inactive
            self.multi_select_button.setText("🙉")
            # Clear selections and reset display when exiting multi-select mode
            self.multi_selected_layers.clear()
            self.update_layer_button_multi_select_display()
            
        # Update button state
        self.multi_select_button.setChecked(self.multi_select_mode)

    def update_layer_button_multi_select_display(self):
        """Update the visual display of layer buttons to show multi-selection state"""
        # Find the currently selected strand
        selected_index = None
        if hasattr(self.canvas, 'selected_strand_index') and self.canvas.selected_strand_index is not None:
            selected_index = self.canvas.selected_strand_index
        elif hasattr(self.canvas, 'selected_strand') and self.canvas.selected_strand is not None:
            for i, strand in enumerate(self.canvas.strands):
                if strand == self.canvas.selected_strand:
                    selected_index = i
                    break
        if selected_index is None:
            for i, strand in enumerate(self.canvas.strands):
                if getattr(strand, 'is_selected', False):
                    selected_index = i
                    break
        
        for i, button in enumerate(self.layer_buttons):
            if i in self.multi_selected_layers:
                # Add visual indicator for multi-selected layers
                button.setProperty("multi_selected", True)
                button.style().unpolish(button)
                button.style().polish(button)
                # Add gold border styling
                current_style = button.styleSheet()
                button.setStyleSheet(current_style + """
                    QPushButton[multi_selected="true"] {
                        border: 3px solid #FFD700 !important;
                        box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
                    }
                    QPushButton[multi_selected="true"]:checked {
                        border: 3px solid #0066FF !important;
                        box-shadow: 0 0 10px rgba(0, 102, 255, 0.8) !important;
                    }
                """)
            else:
                # Remove multi-selection styling and let button use its own style
                button.setProperty("multi_selected", False)
                # Let the button handle its own styling by calling update_style()
                if hasattr(button, 'update_style'):
                    button.update_style()
            
            # Maintain selected strand appearance even in hide mode
            if i == selected_index:
                button.setChecked(True)
            else:
                button.setChecked(False)


    def show_multi_select_context_menu(self, index, position):
        """Show context menu for multi-selected layers"""
        # Only show context menu if we're in multi-select mode
        if not self.multi_select_mode:
            return
            
        # If the clicked layer is not in the selection, add it
        if index not in self.multi_selected_layers:
            self.multi_selected_layers.add(index)
            self.update_layer_button_multi_select_display()
        
        # Get translations for current language
        _ = translations[self.language_code]
        
        # Check if any selected layers are hidden to determine button text
        any_hidden = any(self.canvas.strands[i].is_hidden for i in self.multi_selected_layers 
                        if i < len(self.canvas.strands))
        
        # Check if any selected layers are in shadow-only mode to determine button text
        any_shadow_only = any(getattr(self.canvas.strands[i], 'shadow_only', False) 
                             for i in self.multi_selected_layers 
                             if i < len(self.canvas.strands))
        
        # Determine menu text items for width calculation
        if any_hidden:
            toggle_text = _['show_selected_layers']
            toggle_callback = self.show_selected_layers
        else:
            toggle_text = _['hide_selected_layers']
            toggle_callback = self.hide_selected_layers
            
        if any_shadow_only:
            shadow_text = _['disable_shadow_only_selected']
            shadow_callback = self.disable_shadow_only_selected_layers
        else:
            shadow_text = _['enable_shadow_only_selected']
            shadow_callback = self.enable_shadow_only_selected_layers
        
        # Collect all menu texts for width calculation
        menu_texts = [toggle_text, shadow_text]
        
        # Create context menu with proper theming
        context_menu = QMenu(self)
        
        # Apply RTL layout direction for Hebrew
        if self.language_code == 'he':
            context_menu.setLayoutDirection(Qt.RightToLeft)
        
        self._apply_menu_theme(context_menu, menu_texts)
        
        # Get theme for HoverLabel
        theme = self.current_theme if hasattr(self, 'current_theme') else 'light'
        
        # Add single hide/show toggle action with translations using HoverLabel
        toggle_label = HoverLabel(toggle_text, self, theme)
        if self.language_code == 'he':
            toggle_label.setLayoutDirection(Qt.RightToLeft)
            toggle_label.setAlignment(Qt.AlignLeft)
        toggle_action = QWidgetAction(self)
        toggle_action.setDefaultWidget(toggle_label)
        toggle_action.triggered.connect(toggle_callback)
        context_menu.addAction(toggle_action)
        
        context_menu.addSeparator()
        
        # Add shadow-only toggle action with translations using HoverLabel
            
        shadow_label = HoverLabel(shadow_text, self, theme)
        if self.language_code == 'he':
            shadow_label.setLayoutDirection(Qt.RightToLeft)
            shadow_label.setAlignment(Qt.AlignLeft)
        shadow_action = QWidgetAction(self)
        shadow_action.setDefaultWidget(shadow_label)
        shadow_action.triggered.connect(shadow_callback)
        context_menu.addAction(shadow_action)
        
        # Show the menu at the cursor position
        button = self.layer_buttons[index]
        context_menu.exec_(button.mapToGlobal(position))

    def _apply_menu_theme(self, menu, menu_texts=None):
        """Apply the current theme to a context menu"""
        # Calculate dynamic width if menu texts are provided
        dynamic_width = ""
        if menu_texts:
            width = self.calculate_menu_width(menu_texts)
            dynamic_width = f"min-width: {width}px;"
            
        # Determine if we're using RTL for Hebrew
        is_hebrew = self.language_code == 'he'
        # Use different padding for RTL vs LTR
        item_padding = "padding: 6px 20px 6px 6px;" if is_hebrew else "padding: 6px 20px;"
        
        if hasattr(self, 'current_theme') and self.current_theme == 'dark':
            # Dark theme styling for menu
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: #3C3C3C;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px;
                    {dynamic_width}
                }}
                QMenu::item {{
                    background-color: transparent;
                    {item_padding}
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: #555555;
                    color: white;
                }}
                QMenu::item:pressed {{
                    background-color: #666666;
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: #555555;
                    margin: 4px 0px;
                }}
            """)
        else:
            # Light theme styling for menu
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 4px;
                    {dynamic_width}
                }}
                QMenu::item {{
                    background-color: transparent;
                    {item_padding}
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: #E0E0E0;
                    color: black;
                }}
                QMenu::item:pressed {{
                    background-color: #D0D0D0;
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: #CCCCCC;
                    margin: 4px 0px;
                }}
            """)

    def hide_selected_layers(self):
        """Hide all selected layers in multi-select mode"""
        if not self.multi_selected_layers:
            return
            
        logging.info(f"Hiding layers: {list(self.multi_selected_layers)}")
        for layer_index in self.multi_selected_layers:
            if layer_index < len(self.canvas.strands):
                strand = self.canvas.strands[layer_index]
                strand.is_hidden = True
                # Update button appearance to show hidden state
                if layer_index < len(self.layer_buttons):
                    button = self.layer_buttons[layer_index]
                    button.set_hidden(True)
        
        # Update canvas
        self.canvas.update()
        
        # Save undo/redo state after hiding layers
        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            # Force save by resetting last save time to ensure this is captured as a new state
            self.canvas.undo_redo_manager._last_save_time = 0
            self.canvas.undo_redo_manager.save_state()
            logging.info(f"Saved undo/redo state after hiding {len(self.multi_selected_layers)} selected layers")
        else:
            logging.warning("Could not find undo_redo_manager to save state after hiding layers")
        
        # Clear selections after operation
        self.multi_selected_layers.clear()
        self.update_layer_button_multi_select_display()

    def show_selected_layers(self):
        """Show all selected layers in multi-select mode"""
        if not self.multi_selected_layers:
            return
            
        logging.info(f"Showing layers: {list(self.multi_selected_layers)}")
        for layer_index in self.multi_selected_layers:
            if layer_index < len(self.canvas.strands):
                strand = self.canvas.strands[layer_index]
                strand.is_hidden = False
                # Update button appearance to show visible state
                if layer_index < len(self.layer_buttons):
                    button = self.layer_buttons[layer_index]
                    button.set_hidden(False)
        
        # Update canvas
        self.canvas.update()
        
        # Save undo/redo state after showing layers
        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            # Force save by resetting last save time to ensure this is captured as a new state
            self.canvas.undo_redo_manager._last_save_time = 0
            self.canvas.undo_redo_manager.save_state()
            logging.info(f"Saved undo/redo state after showing {len(self.multi_selected_layers)} selected layers")
        else:
            logging.warning("Could not find undo_redo_manager to save state after showing layers")
        
        # Clear selections after operation
        self.multi_selected_layers.clear()
        self.update_layer_button_multi_select_display()

    def enable_shadow_only_selected_layers(self):
        """Enable shadow-only mode for selected layers"""
        if not self.multi_selected_layers:
            return
            
        logging.info(f"Enabling shadow only for layers: {list(self.multi_selected_layers)}")
        for layer_index in self.multi_selected_layers:
            if layer_index < len(self.canvas.strands):
                strand = self.canvas.strands[layer_index]
                # Set shadow_only property
                strand.shadow_only = True
                # Ensure shadow is enabled when setting shadow_only
                if hasattr(strand, 'has_shadow'):
                    strand.has_shadow = True
                else:
                    strand.has_shadow = True
                # Update button appearance to reflect shadow-only state
                if layer_index < len(self.layer_buttons):
                    button = self.layer_buttons[layer_index]
                    button.set_shadow_only(True)
        
        # Update canvas
        self.canvas.update()
        
        # Save undo/redo state after enabling shadow-only mode
        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            # Force save by resetting last save time to ensure this is captured as a new state
            self.canvas.undo_redo_manager._last_save_time = 0
            self.canvas.undo_redo_manager.save_state()
            logging.info(f"Saved undo/redo state after enabling shadow-only for {len(self.multi_selected_layers)} selected layers")
        else:
            logging.warning("Could not find undo_redo_manager to save state after enabling shadow-only")
        
        # Clear selections after operation
        self.multi_selected_layers.clear()
        self.update_layer_button_multi_select_display()

    def disable_shadow_only_selected_layers(self):
        """Disable shadow-only mode for selected layers (show full layers)"""
        if not self.multi_selected_layers:
            return
            
        logging.info(f"Disabling shadow only for layers: {list(self.multi_selected_layers)}")
        for layer_index in self.multi_selected_layers:
            if layer_index < len(self.canvas.strands):
                strand = self.canvas.strands[layer_index]
                # Disable shadow_only property
                strand.shadow_only = False
                # Update button appearance to reflect normal state
                if layer_index < len(self.layer_buttons):
                    button = self.layer_buttons[layer_index]
                    button.set_shadow_only(False)
        
        # Update canvas
        self.canvas.update()
        
        # Save undo/redo state after disabling shadow-only mode
        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            # Force save by resetting last save time to ensure this is captured as a new state
            self.canvas.undo_redo_manager._last_save_time = 0
            self.canvas.undo_redo_manager.save_state()
            logging.info(f"Saved undo/redo state after disabling shadow-only for {len(self.multi_selected_layers)} selected layers")
        else:
            logging.warning("Could not find undo_redo_manager to save state after disabling shadow-only")
        
        # Clear selections after operation
        self.multi_selected_layers.clear()
        self.update_layer_button_multi_select_display()

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
        safe_info(f"toggle_lock_mode() called - button isChecked: {self.lock_layers_button.isChecked()}")
        self.lock_mode = self.lock_layers_button.isChecked()
        safe_info(f"Set self.lock_mode to: {self.lock_mode}")
        
        _ = translations[self.language_code]
        if self.lock_mode:
            self.lock_layers_button.setText(_['exit_lock_mode'])
            self.notification_label.setText(_['select_layers_to_lock'])
            self.locked_layers = self.previously_locked_layers.copy()
            self.deselect_all_button.setText(_['clear_all_locks'])
            # Disable new strand and delete strand buttons in lock mode
            self.add_new_strand_button.setEnabled(False)
            self.delete_strand_button.setEnabled(False)
        else:
            self.lock_layers_button.setText(_['lock_layers'])
            self.notification_label.setText(_['exited_lock_mode'])
            self.previously_locked_layers = self.locked_layers.copy()
            self.locked_layers.clear()
            self.deselect_all_button.setText(_['deselect_all'])
            # Re-enable new strand and delete strand buttons when exiting lock mode
            self.add_new_strand_button.setEnabled(True)
            # Evaluate delete button state based on current selection
            self.update_delete_button_state()

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
        Handle layer selection based on current mode (normal, masked, multi-select, or lock).
        
        Args:
            index (int): The index of the layer to select.
            emit_signal (bool): Whether to emit the selection signal.
        """
        # Handle multi-selection mode
        if self.multi_select_mode:
            if index in self.multi_selected_layers:
                # Deselect if already selected
                self.multi_selected_layers.remove(index)
                logging.info(f"Removed layer {index} from multi-selection")
            else:
                # Add to selection
                self.multi_selected_layers.add(index)
                logging.info(f"Added layer {index} to multi-selection")
            
            # Update visual display
            self.update_layer_button_multi_select_display()
            # Don't change the main selected strand in multi-select mode
            return
        
        # Block layer selection if we're in mask editing mode
        if self.mask_editing:
            safe_info("Layer selection blocked: Currently in mask edit mode")
            # Optionally show a temporary notification
            self.show_notification("Please exit mask edit mode first (Press ESC)")
            return

        # In lock mode, preserve the currently selected strand before deselecting all
        previously_selected_index = None
        if self.lock_mode and self.canvas.selected_strand_index is not None:
            previously_selected_index = self.canvas.selected_strand_index

        # Deselect all strands first
        for strand in self.canvas.strands:
            strand.is_selected = False

        # Reset the user_deselected_all flag in the move mode when a strand is explicitly selected
        if hasattr(self.canvas, 'current_mode') and hasattr(self.canvas.current_mode, 'user_deselected_all'):
            self.canvas.current_mode.user_deselected_all = False

        if self.masked_mode:
            self.handle_masked_layer_selection(index)
        elif self.lock_mode:
            # In lock mode, always handle locking/unlocking regardless of current mode
            if index in self.locked_layers:
                safe_info(f"Unlocking strand at index {index}")
                self.locked_layers.remove(index)
                # When unlocking, also deselect and unhighlight the strand
                if 0 <= index < len(self.canvas.strands):
                    strand = self.canvas.strands[index]
                    strand.is_selected = False
                    safe_info(f"Set strand.is_selected = False for strand {strand.layer_name}")
                # Clear canvas selection if this was the selected strand
                if self.canvas.selected_strand_index == index:
                    safe_info(f"Clearing canvas selection for strand index {index}")
                    self.canvas.selected_strand = None
                    self.canvas.selected_strand_index = None
                    self.canvas.selected_attached_strand = None
                # Uncheck the layer button
                if 0 <= index < len(self.layer_buttons):
                    self.layer_buttons[index].setChecked(False)
                    safe_info(f"Unchecked layer button for index {index}")
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
                # Restore previous selection if it wasn't the unlocked strand
                if previously_selected_index is not None and previously_selected_index != index:
                    if 0 <= previously_selected_index < len(self.canvas.strands) and previously_selected_index not in self.locked_layers:
                        self.canvas.strands[previously_selected_index].is_selected = True
                        self.canvas.selected_strand = self.canvas.strands[previously_selected_index]
                        self.canvas.selected_strand_index = previously_selected_index
                        if 0 <= previously_selected_index < len(self.layer_buttons):
                            self.layer_buttons[previously_selected_index].setChecked(True)
                        safe_info(f"Restored selection to strand at index {previously_selected_index}")
                # Don't re-select the strand after unlocking
                return
            else:
                safe_info(f"Locking strand at index {index}")
                self.locked_layers.add(index)
                # When locking, also deselect and unhighlight the strand if it's currently selected
                if 0 <= index < len(self.canvas.strands):
                    strand = self.canvas.strands[index]
                    strand.is_selected = False
                    safe_info(f"Set strand.is_selected = False for locked strand {strand.layer_name}")
                # Clear canvas selection if this was the selected strand
                if self.canvas.selected_strand_index == index:
                    safe_info(f"Clearing canvas selection for locked strand index {index}")
                    self.canvas.selected_strand = None
                    self.canvas.selected_strand_index = None
                    self.canvas.selected_attached_strand = None
                # Uncheck the layer button
                if 0 <= index < len(self.layer_buttons):
                    self.layer_buttons[index].setChecked(False)
                    safe_info(f"Unchecked layer button for locked index {index}")
                # Update canvas to reflect deselection
                self.canvas.update()
                self.update_layer_buttons_lock_state()
                self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
                # Save state for undo/redo
                if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                    self.undo_redo_manager.save_state()
                # Restore previous selection if it wasn't the locked strand
                if previously_selected_index is not None and previously_selected_index != index:
                    if 0 <= previously_selected_index < len(self.canvas.strands) and previously_selected_index not in self.locked_layers:
                        self.canvas.strands[previously_selected_index].is_selected = True
                        self.canvas.selected_strand = self.canvas.strands[previously_selected_index]
                        self.canvas.selected_strand_index = previously_selected_index
                        if 0 <= previously_selected_index < len(self.layer_buttons):
                            self.layer_buttons[previously_selected_index].setChecked(True)
                        safe_info(f"Restored selection to strand at index {previously_selected_index} after locking")
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
                        self.refresh_layers_no_zoom()
                        
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
                safe_warning(f"request_edit_mask called with invalid index {strand_index}.")
                return

            # Ensure the strand is actually a MaskedStrand before editing.
            if not isinstance(self.canvas.strands[strand_index], MaskedStrand):
                safe_warning(f"request_edit_mask called on a non-masked strand at index {strand_index}.")
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

            safe_info(f"Entered mask edit mode for strand {strand_index}")
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
        safe_info("Exited mask edit mode")
        self.show_notification(_['mask_edit_mode_exited'])
        self.update()

        # --- ADD: Save state after exiting mask edit mode via ESC --- 
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            # Force a save by resetting the last save time so the identical-state and timing checks are bypassed
            self.undo_redo_manager._last_save_time = 0
            safe_info("Saving state after exiting mask edit mode")
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
        self.draw_names_button.setEnabled(True)
        self.lock_layers_button.setEnabled(True)
        self.deselect_all_button.setEnabled(True)
        if hasattr(self, 'group_layer_manager'):
            self.group_layer_manager.create_group_button.setEnabled(True)

    def update_delete_button_state(self):
        """Update the delete button state based on the currently selected strand's deletability."""
            
        selected_index = self.get_selected_layer()
        if (selected_index is not None and 
            selected_index < len(self.layer_buttons) and 
            selected_index < len(self.canvas.strands)):
            
            selected_strand = self.canvas.strands[selected_index]
            # Use the same criteria as in update_layer_button_states
            is_deletable = not all(selected_strand.has_circles)
            
            # Keep delete button disabled if in lock mode
            if self.lock_mode:
                self.delete_strand_button.setEnabled(False)
            else:
                self.delete_strand_button.setEnabled(is_deletable)
            # Force visual update of the button
            self.delete_strand_button.update()
        else:
            # No strand selected, disable delete button (also keep disabled in lock mode)
            self.delete_strand_button.setEnabled(False)
            self.delete_strand_button.update()

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
            
            # Find the corresponding strand in the canvas
            strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
            
            if strand_index is not None:
                strand = self.canvas.strands[strand_index]
                if isinstance(strand, MaskedStrand):
                    # Save state BEFORE deletion for proper undo/redo
                    if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                        self.undo_redo_manager.save_state()
                        logging.info("Saved state before masked layer deletion")
                    
                    # Delete only this specific masked layer
                    if self.canvas.delete_masked_layer(strand):
                        self.remove_layer_button(strand_index)
                        # Update the layer panel without affecting other masked layers
                        self.refresh()
                        self.refresh_layers_no_zoom()  # Preserve zoom/pan after masked strand deletion
                        
                        # Save state AFTER deletion to capture the "deleted" state
                        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                            self.undo_redo_manager.save_state(allow_empty=True)
                            logging.info("Saved state after masked layer deletion")

                    logging.info(f"Masked layer {strand_name} deleted successfully")
                else:
                    # Save state BEFORE deletion for proper undo/redo
                    if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                        self.undo_redo_manager.save_state()
                        logging.info("Saved state before strand deletion")
                    
                    # Handle regular strand deletion
                    self.strand_deleted.emit(strand_index)
                    # Force a complete refresh after deletion
                    self.refresh()
                    self.refresh_layers_no_zoom()
                    self.update_layer_button_states()
                    
                    # Save state AFTER deletion to capture the "deleted" state
                    if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                        self.undo_redo_manager.save_state(allow_empty=True)
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
            if deleted_set_number in self.set_colors:
                del self.set_colors[deleted_set_number]

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
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                old_set_number = strand.set_number
                if old_set_number not in new_set_numbers:
                    new_set_numbers[old_set_number] = new_count
                    new_count += 1
                new_set_number = new_set_numbers[old_set_number]
                
                # Update strand's set_number
                strand.set_number = new_set_number
                
                # Use strand's actual layer_name instead of constructing text
                button.setText(strand.layer_name)
        
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
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                set_number = strand.set_number
                
                if set_number == deleted_set_number:
                    # For affected set, just use the strand's actual layer_name
                    button.setText(strand.layer_name)
                elif set_number > deleted_set_number:
                    # Decrement set numbers greater than the deleted set
                    new_set_number = set_number - 1
                    strand.set_number = new_set_number
                    # Use strand's actual layer_name instead of constructing text
                    button.setText(strand.layer_name)
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

        # Find the strand with the matching set_number (most recently added)
        strand_index = None
        for i in range(len(self.canvas.strands) - 1, -1, -1):  # Search backwards for most recent
            strand = self.canvas.strands[i]
            if hasattr(strand, 'set_number') and strand.set_number == set_number:
                strand_index = i
                break
        
        if strand_index is None:
            logging.error(f"Could not find strand with set_number {set_number}")
            return

        # Create and add the button
        button = self.create_layer_button(strand_index, self.canvas.strands[strand_index], count)
        self.layer_buttons.append(button)  # Add to end of list

        # Add button directly to layout at the top, aligned center
        self.scroll_layout.insertWidget(0, button, 0, Qt.AlignHCenter)

        # Debug logging to trace button text issues
        logging.info(f"Added new button directly to layout at top (index 0)")
        logging.info(f"Button created with text: '{button.text()}' for strand: '{self.canvas.strands[strand_index].layer_name}'")
        logging.info(f"Total layer_buttons count: {len(self.layer_buttons)}")
        for i, btn in enumerate(self.layer_buttons):
            logging.info(f"  layer_buttons[{i}]: text='{btn.text()}'")
        logging.info("Finished add_layer_button")

        # Reset monkey button to non-hide mode when creating new layer
        if hasattr(self, 'multi_select_button') and self.multi_select_mode:
            self.multi_select_mode = False
            self.multi_select_button.setChecked(False)
            self.multi_select_button.setText("🙉")
            self.multi_selected_layers.clear()
            self.update_layer_button_multi_select_display()
            logging.info("Reset monkey button to non-hide mode after creating new layer")

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
            self.refresh_layers_no_zoom()
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
        """Deselect all layers and strands, or clear all locks if in lock mode."""
        if self.lock_mode:
            # In lock mode, this button functions as "Clear Locks"
            safe_info("Clearing all locked layers")
            self.locked_layers.clear()
            
            # Update the visual state of all layer buttons
            self.update_layer_buttons_lock_state()
            
            # Emit the signal to notify other components
            self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
            
            # Save state for undo/redo
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                self.undo_redo_manager.save_state()
            
            # Update canvas to reflect changes
            self.canvas.update()
            safe_info("All locks cleared")
        else:
            # Normal mode: deselect all layers and strands
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
            
            # Update delete button state since nothing is selected
            self.update_delete_button_state()
            
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
            logging.info("[FLASH_DEBUG] simulate_refresh_button_click: Simulating refresh button click")
            # Call the refresh_layers_no_zoom method to preserve zoom level and prevent window flash during undo/redo
            self.refresh_layers_no_zoom()
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
        
        # Check if this is a MaskedStrand - they have composite names and should use strand.set_number
        if isinstance(strand, MaskedStrand):
            # For masked strands, always use strand.set_number and don't parse layer_name
            set_number = strand.set_number
            count = self.set_counts.get(set_number, 0) + 1
            logging.info(f"STRAND_DEBUG: MaskedStrand detected, using set_number={set_number}, count={count}")
        # Extract set number and count from the strand's layer_name for regular strands
        elif hasattr(strand, 'layer_name') and strand.layer_name and '_' in strand.layer_name:
            try:
                parts = strand.layer_name.split('_')
                # Only parse if we have exactly 2 parts (set_count format)
                if len(parts) == 2:
                    set_number = int(parts[0])
                    count = int(parts[1])
                    logging.info(f"STRAND_DEBUG: Successfully extracted set_number={set_number}, count={count}")
                else:
                    # Layer name has multiple underscores, use fallback
                    set_number = strand.set_number
                    count = self.set_counts.get(set_number, 0) + 1
                    logging.info(f"STRAND_DEBUG: Layer name has {len(parts)} parts, using fallback set_number={set_number}, count={count}")
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
        
        # ------------------------------------------------------------------
        # If Lock-Mode is currently active we do NOT want the programmatic
        # selection that follows to be interpreted as a lock command.  We
        # therefore raise the same suppression flag that the MainWindow uses
        # during mode switches – the lock behaviour is skipped exactly once
        # while we add/select the freshly created strand.
        # ------------------------------------------------------------------
        temp_suppress_lock = False
        if self.lock_mode and not getattr(self, "_suppress_lock_mode_temporarily", False):
            self._suppress_lock_mode_temporarily = True
            temp_suppress_lock = True

        # Add the new layer button
        logging.info(f"Adding new layer button for set {set_number}, count {count}")
        self.add_layer_button(set_number, count)

        # Lift suppression again so manual clicks behave normally
        if temp_suppress_lock:
            self._suppress_lock_mode_temporarily = False
        
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
        
        # Refresh the layer panel
        if isinstance(strand, AttachedStrand):
            logging.info("Using refresh_after_attachment for attached strand")
            # For attached strands we still need the specialized lightweight refresh that preserves zoom/pan
            self.refresh_after_attachment()
        else:
            # Avoid the full rebuild (which causes a white-flash) – instead perform a light update:
            logging.info("Lightweight UI update – skipping costly refresh() to avoid flash")

            # 1. Ensure the new button is visually present (add_layer_button already inserted it)
            self.scroll_layout.update()

            # 2. Update button states (delete-enabled flag, attachable icons, etc.)
            self.update_layer_button_states()

            # 3. Force a canvas repaint so the new strand appears immediately
            if self.canvas:
                self.canvas.update()

            # NOTE: no call to refresh() or refresh_layers*(), so no overlay / flash occurs.
        
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
        overlay = None  # Snapshot overlay that masks flicker on Windows

        logging.info("refresh_layers called, redirecting to refresh()")
        self.refresh()
        # Reset canvas zoom and pan to original view
        self.canvas.reset_zoom()
    
    # NOTE: refresh_layers_no_zoom method already defined earlier (line 559) - removed duplicate
    
    def refresh_after_attachment(self):
        """Complete refresh after strand attachment without resetting zoom/pan.
        This function does everything refresh_layers does except the zoom reset and overlay."""
        logging.info("refresh_after_attachment called - refreshing without zoom reset and overlay")
        
        # Get the main window reference
        main_window = self.parent_window if hasattr(self, 'parent_window') and self.parent_window else self.parent()
        
        # Suppress full-window repaint only on macOS; on Windows/Linux it causes a white flash
        if sys.platform == 'darwin' and main_window:
            main_window.setUpdatesEnabled(False)
            # Suspend painting on the scroll area / its viewport only on macOS – doing this on
            # Windows/Linux produces a short blank frame (the white-flash we are chasing).
            self.scroll_area.setUpdatesEnabled(False)
            if hasattr(self.scroll_area, 'viewport'):
                self.scroll_area.viewport().setUpdatesEnabled(False)
        
        # Simplified refresh without overlay for attach mode to prevent temporary window
        # Just rebuild the layer buttons without visual effects
        removed_count = 0
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                removed_count += 1
            del item
        
        # Re-add buttons in reverse order
        added_count = 0
        valid_buttons = [btn for btn in self.layer_buttons if btn]
        for button in reversed(valid_buttons):
            self.scroll_layout.addWidget(button, 0, Qt.AlignHCenter)
            button.show()
            added_count += 1
        
        # Update layout and canvas
        self.scroll_layout.update()
        self.canvas.update()  # Just update the canvas without changing zoom/pan
        
        # Re-enable updates after refresh (only on macOS)
        if sys.platform == 'darwin':
            if hasattr(self.scroll_area, 'viewport'):
                self.scroll_area.viewport().setUpdatesEnabled(True)
            self.scroll_area.setUpdatesEnabled(True)
            if main_window:
                main_window.setUpdatesEnabled(True)

    # ---------------------------------------------------------------------------
    # LayerPanel.py
    # ---------------------------------------------------------------------------
    def refresh(self):
        """
        Rebuild the layer panel **without any visible flash**.

        Strategy
        --------
        • Win / X‑based Linux …… freeze only the viewport (never the MainWindow).  
        • macOS ………………… freeze the MainWindow *and* the viewport.

        All heavy work happens while painting is disabled; we then re‑enable
        widgets in the exact reverse order and force one final repaint.
        """
        from PyQt5.QtWidgets import QApplication

        logging.info("LayerPanel.refresh – start (no‑flash)")

        # ------------------------------------------------------------------ #
        # 0. Decide which widgets to freeze
        # ------------------------------------------------------------------ #
        # Always freeze the QScrollArea itself on every platform; additionally freeze the
        # MainWindow only on macOS where it is required to avoid compositor glitches.
        freeze_top  = sys.platform == "darwin"
        main_window = getattr(self, "parent_window", None) or self.parent()
        viewport    = self.scroll_area.viewport()

        # ------------------------------------------------------------------ #
        # 1. Freeze painting
        # ------------------------------------------------------------------ #
        if freeze_top and main_window:
            main_window.setUpdatesEnabled(False)

        viewport.setUpdatesEnabled(False)           # always safe (child only)
        self.scroll_area.setUpdatesEnabled(False)   # freeze whole scroll area (NEW)

        # Flush pending paints so we start from a clean state
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)


        try:
            # ------------------------------------------------------------------
            # 2. *** REBUILD THE PANEL ***
            # ------------------------------------------------------------------
            #
            # 2‑a  Clear current buttons
            #
            for btn in self.layer_buttons:
                btn.setParent(None)
                btn.deleteLater()
            self.layer_buttons.clear()
            self.set_counts.clear()

            #
            # 2‑b  Re‑create buttons for every strand
            #
            for i, strand in enumerate(self.canvas.strands):
                set_no = strand.set_number
                self.set_counts[set_no] = self.set_counts.get(set_no, 0) + 1

                colour = getattr(strand, "color", None) \
                        or self.canvas.strand_colors.get(set_no) \
                        or getattr(self.canvas, "default_strand_color",
                                    QColor(200, 170, 230, 255))

                btn = NumberedLayerButton(strand.layer_name,
                                        self.set_counts[set_no],
                                        colour)
                btn.layer_name = strand.layer_name          # reliable lookup
                btn.clicked.connect(partial(self.select_layer, i))
                btn.color_changed.connect(self.on_color_changed)
                
                # Add right-click context menu for multi-selection
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(partial(self.show_multi_select_context_menu, i))

                if isinstance(strand, MaskedStrand):
                    btn.set_border_color(strand.second_selected_strand.color)
                    if strand.first_selected_strand:
                        btn.set_color(strand.first_selected_strand.color)

                btn.set_hidden(strand.is_hidden)

                self.scroll_layout.insertWidget(0, btn, 0, Qt.AlignHCenter)
                self.layer_buttons.append(btn)

            #
            # 2‑c  Restore selection
            #
            sel = self.canvas.selected_strand
            if sel:
                for btn in self.layer_buttons:
                    if getattr(btn, "layer_name", "") == sel.layer_name:
                        btn.setChecked(True)
                        break

            #
            # 2‑d  Misc. book‑keeping
            #
            self.update_layer_button_states()
            self.current_set = max(
                (s.set_number for s in self.canvas.strands
                if not isinstance(s, MaskedStrand)),
                default=0
            )
            self.group_layer_manager.refresh()
            self.scroll_layout.update()

        finally:
            # ------------------------------------------------------------------
            # 3. Re‑enable painting  (reverse order!)
            # ------------------------------------------------------------------
            # Reverse the order used when freezing
            self.scroll_area.setUpdatesEnabled(True)       # un-freeze for all OS
            if freeze_top:
                # macOS only – MainWindow was frozen above
                pass
            viewport.setUpdatesEnabled(True)

            if freeze_top and main_window:
                main_window.setUpdatesEnabled(True)

        # ------------------------------------------------------------------
        # 4. One explicit repaint – a single, clean frame
        # ------------------------------------------------------------------
        viewport.update()

        logging.info("LayerPanel.refresh – done (no‑flash)")


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

    def _sync_internal_lists_from_layout(self):
        """
        After a drag‑and‑drop we already moved the real widgets inside
        self.scroll_layout.  This function rebuilds `self.layer_buttons`
        (and optionally other parallel lists) so that index i in the list
        once again corresponds to index i in `self.canvas.strands`.

        The visual order in the layout is top→bottom, whereas the logical
        order expected by the rest of the program is bottom→top, because new
        buttons are always inserted at row 0.  Therefore we just walk the
        layout, collect the buttons, then reverse the list.
        """
        ordered_buttons = []
        for row in range(self.scroll_layout.count()):
            w = self.scroll_layout.itemAt(row).widget()
            if w is not None:                       # should always be true
                ordered_buttons.append(w)

        # layout: top‑to‑bottom  →   logical list: bottom‑to‑top
        self.layer_buttons = list(reversed(ordered_buttons))

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
                
                # Restore hidden and shadow-only states from strand data
                button.set_hidden(getattr(strand, 'is_hidden', False))
                button.set_shadow_only(getattr(strand, 'shadow_only', False))
                
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
            
            # Keep delete button disabled if in lock mode
            if self.lock_mode:
                self.delete_strand_button.setEnabled(False)
            else:
                self.delete_strand_button.setEnabled(is_deletable)
            # Force visual update of the button
            self.delete_strand_button.update()
        else:
            # No valid strand selected – keep delete disabled in lock mode
            if self.lock_mode:
                self.delete_strand_button.setEnabled(False)
            else:
                self.delete_strand_button.setEnabled(False)
            self.delete_strand_button.update()
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
                QTimer.singleShot(0, lambda: (
                    self._sync_internal_lists_from_layout(),
                    self.update_layer_button_states(),
                    self.group_layer_manager.refresh(),
                    self.scroll_layout.update(),
                    self.canvas.update(),
                    self.undo_redo_manager.save_state() if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager else None
                ))
            else:
                # non‑macOS path: execute immediately
                self._sync_internal_lists_from_layout()
                self.update_layer_button_states()
                self.group_layer_manager.refresh()
                self.scroll_layout.update()
                self.canvas.update()
                if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                    self.undo_redo_manager.save_state()

            logging.info("UI refreshed after drop to show reordered layers (platform-specific logic applied).")

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