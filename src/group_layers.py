from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QMenu, QAction, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent, QIcon
from PyQt5.QtCore import QMimeData, QPoint
from PyQt5.QtGui import QPixmap
from strand_drawing_canvas import StrandDrawingCanvas
from strand import Strand, AttachedStrand, MaskedStrand  # Add this import
import logging
from strand_drawing_canvas import StrandDrawingCanvas   
from math import atan2, degrees
from PyQt5.QtGui import QIntValidator
from translations import translations
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
import logging
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea,
    QMenu, QAction, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QMimeData, QPoint
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent, QIcon, QPixmap, QIntValidator
from strand_drawing_canvas import StrandDrawingCanvas
from strand import Strand, AttachedStrand, MaskedStrand  # Add this import
import logging
from math import atan2, degrees
import json
from translations import translations
class GroupedLayerTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.groups = {}  # Dictionary to hold group items
        self.setColumnCount(1)
        self.setIndentation(20)
        self.setStyleSheet("""
            QTreeWidget::item {
                padding: 5px;
            }
        """)

    def add_group(self, group_name, layers):
        if group_name not in self.groups:
            group_item = QTreeWidgetItem(self)
            group_item.setText(0, group_name)
            self.addTopLevelItem(group_item)
            self.groups[group_name] = group_item
        self.update_group_display(group_name, layers)

    def update_group_display(self, group_name, layers):
        if group_name in self.groups:
            group_item = self.groups[group_name]
            # Clear existing child items
            group_item.takeChildren()

            # Extract main strand names
            main_strands = set()
            for layer_name in layers:
                main_strand = self.extract_main_strand(layer_name)
                if main_strand:
                    main_strands.add(main_strand)

            # Update group item's text to include main strands
            main_strands_text = ", ".join(sorted(main_strands))
            group_item.setText(0, f"{group_name}: {main_strands_text}")
            logging.info(f"Group '{group_name}' updated with main strands: {main_strands_text}")

            # Optionally, add child items for each main strand
            for main_strand in sorted(main_strands):
                strand_item = QTreeWidgetItem()
                strand_item.setText(0, main_strand)
                group_item.addChild(strand_item)
        else:
            logging.warning(f"Group '{group_name}' not found in GroupedLayerTree.")

    def extract_main_strand(self, layer_name):
        # Split the layer name to get the main strand (e.g., '1' from '1_1')
        parts = layer_name.split('_')
        return parts[0] if parts else layer_name

    def remove_group(self, group_name):
        if group_name in self.groups:
            group_item = self.groups[group_name]
            index = self.indexOfTopLevelItem(group_item)
            self.takeTopLevelItem(index)
            del self.groups[group_name]
            logging.info(f"Group '{group_name}' removed from GroupedLayerTree.")
        else:
            logging.warning(f"Group '{group_name}' not found in GroupedLayerTree.")

    def add_layer_to_group(self, group_name, layer_name):
        if group_name in self.groups:
            group = self.groups[group_name]
            # No need to add individual layers if we only display main strands
            # But if you want to display layers as children, implement here
            pass
        else:
            logging.warning(f"Group '{group_name}' not found in GroupedLayerTree.")

    def remove_layer_from_group(self, group_name, layer_name):
        if group_name in self.groups:
            group_item = self.groups[group_name]
            # Optionally, implement removal of layer items if displayed
            pass
        else:
            logging.warning(f"Group '{group_name}' not found in GroupedLayerTree.")
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMenu, QSizePolicy)
from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, 
                              QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QMenu, QAction, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import QMimeData, QPoint
from PyQt5.QtGui import QPixmap
from strand_drawing_canvas import StrandDrawingCanvas
from strand import Strand, AttachedStrand, MaskedStrand  # Add this import
import logging
from strand_drawing_canvas import StrandDrawingCanvas   
from math import atan2, degrees
from PyQt5.QtGui import QIntValidator
from translations import translations
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
import logging
from PyQt5.QtGui import QPalette, QColor, QPainter
from PyQt5.QtWidgets import QStyleOptionButton
from PyQt5.QtWidgets import (
     QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel,
     QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea,
     QMenu, QAction, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractScrollArea
 )
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QMimeData, QPoint
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent, QIcon, QPixmap, QIntValidator
from strand_drawing_canvas import StrandDrawingCanvas
from strand import Strand, AttachedStrand, MaskedStrand  # Add this import
import logging
from math import atan2, degrees
class CollapsibleGroupWidget(QWidget):
    def __init__(self, group_name, group_panel):
        super().__init__()
        self.group_name = group_name
        self.group_panel = group_panel
        self.canvas = self.group_panel.canvas

        self.layers = []  # List to hold layer names
        self.is_collapsed = False  # State of the collapsible content

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins
        self.layout.setSpacing(0)

        # Access the current language code
        self.language_code = 'en'
        self.update_translations()  # Call the method to set initial translations

        # Group button (collapsible header)
        self.group_button = QPushButton()
        self.layout.addWidget(self.group_button)
        self.group_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.group_button.clicked.connect(self.toggle_collapse)
        self.group_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_button.customContextMenuRequested.connect(self.show_context_menu)

        # Content widget (collapsible content)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.layout.addWidget(self.content_widget)

        # List widget to display layers
        self.layers_list = QListWidget()
        self.layers_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.layers_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layers_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.content_layout.addWidget(self.layers_list)

        # Store main strands
        self.main_strands = set()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.content_widget.setVisible(not self.is_collapsed)

        # Update styles based on the current theme
        self.apply_theme()

        # Connect to theme changed signal if available
        if self.canvas and hasattr(self.canvas, 'theme_changed'):
            self.canvas.theme_changed.connect(self.on_theme_changed)

        self.update_translations()
    def update_group_button_style(self):
        self.layers_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: rgba(35, 35, 35, 255);
                color: white;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: rgba(30, 30, 30, 230);
            }
        """)

    def on_theme_changed(self):
        """Handle dynamic theme changes by updating styles."""
        self.apply_theme()
    def apply_theme(self):
        self.layers_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: rgba(35, 35, 35, 255);
                color: white;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: rgba(30, 30, 30, 230);
            }
        """)
    def show_context_menu(self, position):
        _ = translations[self.language_code]
        context_menu = QMenu(self)

        # Apply theme-specific styles to the context menu
        self.apply_context_menu_style(context_menu)

        move_strands_action = context_menu.addAction(_['move_group_strands'])
        rotate_strands_action = context_menu.addAction(_['rotate_group_strands'])
        edit_angles_action = context_menu.addAction(_['edit_strand_angles'])
        delete_group_action = context_menu.addAction(_['delete_group'])

        action = context_menu.exec_(self.group_button.mapToGlobal(position))

        if action == move_strands_action:
            self.group_panel.start_group_move(self.group_name)
        elif action == rotate_strands_action:
            self.group_panel.start_group_rotation(self.group_name)
        elif action == edit_angles_action:
            self.group_panel.edit_strand_angles(self.group_name)
        elif action == delete_group_action:
            self.group_panel.delete_group(self.group_name)

    def apply_context_menu_style(self, menu):
        """Apply styles to the context menu based on the current theme."""
        is_dark_mode = False
        if self.canvas and hasattr(self.canvas, 'is_dark_mode'):
            is_dark_mode = self.canvas.is_dark_mode

        if is_dark_mode:
            # Dark mode styles
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2B2B2B;
                    color: #FFFFFF;
                    border: 1px solid #3C3C3C;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 5px 20px 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #3C3C3C;  /* Lighter on hover */
                }
            """)
        else:
            # Light mode styles
            menu.setStyleSheet("""
                QMenu {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 5px 20px 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #E0E0E0;  /* Darker on hover */
                }
            """)
    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        self.update_size()

    def update_translations(self):
        if self.canvas and hasattr(self.canvas, 'language_code'):
            self.language_code = self.canvas.language_code
        elif hasattr(self.group_panel, 'language_code'):
            self.language_code = self.group_panel.language_code
        else:
            self.language_code = 'en'
        _ = translations[self.language_code]
        # Update UI elements specific to CollapsibleGroupWidget
        # If there are any labels or buttons that need to be translated, update them here

        # For demonstration, suppose we have a label that says "Group: [group_name]"
        # And we have a translation key 'group_label' in our translations:
        # _['group_label'] = 'Group: {group_name}' (in both English and French)

        logging.info(f"CollapsibleGroupWidget updated to language {self.language_code}")
    def add_layer(self, layer_name, color=None, is_masked=False):
        if layer_name not in self.layers:
            self.layers.append(layer_name)
            main_strand = self.extract_main_strand(layer_name)
            if main_strand not in self.main_strands:
                self.main_strands.add(main_strand)
                item = QListWidgetItem(main_strand)
                if color:
                    item.setForeground(color)
                if is_masked:
                    item.setIcon(QIcon("path_to_mask_icon.png"))  # Replace with the actual path
                self.layers_list.addItem(item)
            self.update_size()
            self.update_group_display()
        else:
            pass  # Layer already exists

    def remove_layer(self, layer_name):
        if layer_name in self.layers:
            self.layers.remove(layer_name)
            main_strand = self.extract_main_strand(layer_name)
            if all(self.extract_main_strand(layer) != main_strand for layer in self.layers):
                self.main_strands.remove(main_strand)
                for i in range(self.layers_list.count()):
                    if self.layers_list.item(i).text() == main_strand:
                        self.layers_list.takeItem(i)
                        break
            self.update_size()
            self.update_group_display()

    def update_size(self):
        # Adjust the size of the widget to fit its contents
        self.adjustSize()
        self.setMinimumHeight(self.sizeHint().height())

    def update_group_display(self):
        main_strands_list = sorted(self.main_strands)
        max_strands_to_show = 3
        if len(main_strands_list) > max_strands_to_show:
            main_strands_text = ", ".join(main_strands_list[:max_strands_to_show]) + "..."
        else:
            main_strands_text = ", ".join(main_strands_list)
        self.group_button.setText(f"{self.group_name}: {main_strands_text}")

    def extract_main_strand(self, layer_name):
        parts = layer_name.split('_')
        return parts[0] if parts else layer_name

    def update_layer(self, layer_name, color):
        main_strand = self.extract_main_strand(layer_name)
        for i in range(self.layers_list.count()):
            item = self.layers_list.item(i)
            if item.text() == main_strand:
                item.setForeground(color)
                break


import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class GroupPanel(QWidget):
    group_operation = pyqtSignal(str, str, list)  # operation, group_name, layer_indices
    move_group_started = pyqtSignal(str, list)  # New signal

    def __init__(self, layer_panel, canvas=None):
        super().__init__()
        self.layer_panel = layer_panel
        self.canvas = canvas
        self.groups = {}  # Initialize groups dictionary
        # Initialize group_widgets as an empty dictionary
        self.group_widgets = {}
          # Initialize the layout
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        # Remove the hardcoded background color
        # self.setStyleSheet("background-color: white;")

        # Use the application's palette to set the background role
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), palette.window().color())
        self.setPalette(palette)

        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.setAcceptDrops(True)

        if self.canvas:
            logging.info(f"Canvas set on GroupPanel during initialization: {self.canvas}")
        else:
            logging.warning("GroupPanel initialized without a canvas")

        # Add a scroll area to contain the groups
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
    def create_group_widget(self, group_name, group_layers):
        pass
    def update_group_display(self, group_name):
        """Update the visual display of a group."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            # Extract main strand numbers for display
            main_strands = set()
            for layer_name in group_data['layers']:
                main_strand = layer_name.split('_')[0]
                main_strands.add(main_strand)
            main_strands_text = ", ".join(sorted(main_strands))
            
            # Update the group's display text
            if hasattr(self, 'group_tree'):
                group_item = self.group_tree.groups.get(group_name)
                if group_item:
                    group_item.setText(0, f"{group_name}: {main_strands_text}")
            logging.info(f"Updated display for group {group_name}")


    def add_layer_to_group(self, layer_name, group_name):
        """Add a layer to an existing group in the panel."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            if layer_name not in group_data['layers']:
                group_data['layers'].append(layer_name)
                if hasattr(self.canvas, 'find_strand_by_name'):
                    strand = self.canvas.find_strand_by_name(layer_name)
                    if strand:
                        group_data['strands'].append(strand)
                        # Store original positions for the new strand
                        strand.original_start = QPointF(strand.start)
                        strand.original_end = QPointF(strand.end)
                        strand.original_control_point1 = QPointF(strand.control_point1)
                        strand.original_control_point2 = QPointF(strand.control_point2)
                        logging.info(f"Stored original positions for new strand in group: {layer_name}")
                
                # Update the group's visual representation
                self.update_group_display(group_name)
                logging.info(f"Added layer {layer_name} to group {group_name}")
            else:
                logging.info(f"Layer {layer_name} already in group {group_name}")
        else:
            logging.warning(f"Group {group_name} not found in GroupPanel")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-strand-data"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        data = eval(event.mimeData().data("application/x-strand-data").decode())
        strand_id = data['strand_id']
        
        group_name, ok = QInputDialog.getText(self, "Add to Group", "Enter group name:")
        if ok and group_name:
            self.add_layer_to_group(strand_id, group_name)

    def set_canvas(self, canvas):
        self.canvas = canvas
        logging.info(f"Canvas set on GroupPanel: {self.canvas}")

    def start_group_move(self, group_name):
        if group_name in self.groups:
            # Pass self.canvas as the first parameter and group_name as the second
            dialog = GroupMoveDialog(self.canvas, group_name)
            dialog.move_updated.connect(self.update_group_move)
            dialog.move_finished.connect(self.finish_group_move)
            dialog.exec_()
        else:
            logging.warning(f"Attempted to move non-existent group: {group_name}")

    def update_group_move(self, group_name, total_dx, total_dy):
        logging.info(f"GroupPanel: Updating group move for '{group_name}' by total_dx={total_dx}, total_dy={total_dy}")
        if self.canvas:
            # Create a QPointF for the movement delta
            delta = QPointF(total_dx, total_dy)
            
            # Get the group data
            group_data = self.groups[group_name]
            
            # Move all strands in the group
            for strand in group_data['strands']:
                # Store original control points
                if not hasattr(strand, 'original_control_point1'):
                    strand.original_control_point1 = QPointF(strand.control_point1)
                    strand.original_control_point2 = QPointF(strand.control_point2)
                
                # Move all points including control points
                strand.start = strand.original_start + delta
                strand.end = strand.original_end + delta
                strand.control_point1 = strand.original_control_point1 + delta
                strand.control_point2 = strand.original_control_point2 + delta
                
                # Update the strand's shape
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
                
                # Store the updated control points
                if 'control_points' not in self.canvas.groups[group_name]:
                    self.canvas.groups[group_name]['control_points'] = {}
                
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': strand.control_point1,
                    'control_point2': strand.control_point2
                }
            
            # Update the canvas
            self.canvas.update()
        else:
            logging.error("Canvas not properly connected to GroupPanel")

    def finish_group_move(self, group_name):
        logging.info(f"GroupPanel: Finishing group move for '{group_name}'")
        if self.canvas:
            self.canvas.reset_group_move(group_name)
        else:
            logging.error("Canvas not properly connected to GroupPanel")

    def snap_to_grid(self):
        if self.canvas:
            self.canvas.snap_group_to_grid(self.group_name)
            logging.info(f"Snapped group '{self.group_name}' to grid.")
        else:
            logging.error("Canvas not properly connected to GroupMoveDialog.")
        self.move_finished.emit(self.group_name)
        self.accept()

    def update_group(self, group_name, group_data):
        if group_name in self.groups:
            self.groups[group_name] = group_data
            # Update the UI representation of the group
            group_widget = self.findChild(QWidget, f"group_{group_name}")
            if group_widget:
                # Update the widget to reflect new strand positions
                # This might involve updating labels, positions, etc.
                pass
        logging.info(f"Updated group '{group_name}' with new data")



    def create_group(self, group_name, strands):
        """Create a new group with the given strands."""
        logging.info(f"Attempting to create group '{group_name}' with {len(strands)} strands")
        logging.info(f"[GroupPanel.create_group] Starting group creation for '{group_name}' with {len(strands)} strands")
        logging.info(f"[GroupPanel.create_group] Strands to add: {[s.layer_name if hasattr(s, 'layer_name') else 'Unknown' for s in strands]}")
                
        if not strands:
            logging.warning(f"Attempted to create group '{group_name}' with no strands")
            return

        # Check if the group already exists
        if group_name in self.groups:
            logging.warning(f"Group '{group_name}' already exists. Skipping creation.")
            return

        # Identify main strands (pattern: "x_1" where x is a number)
        main_strands = set()
        for strand in strands:
            if hasattr(strand, 'layer_name'):
                parts = strand.layer_name.split('_')
                if len(parts) == 2 and parts[1] == '1':
                    main_strands.add(strand)
                    logging.info(f"[GroupPanel.create_group] Identified main strand: {strand.layer_name}")

        self.groups[group_name] = {
            'strands': strands,
            'layers': [strand.layer_name for strand in strands],
            'widget': None,
            'main_strands': main_strands,
            'control_points': {}
        }
        logging.info(f"Group '{group_name}' added to self.groups with {len(main_strands)} main strands")
        logging.info(f"[GroupPanel.create_group] Main strands identified: {[s.layer_name for s in main_strands]}")

        group_widget = CollapsibleGroupWidget(
            group_name=group_name,
            group_panel=self
        )
        logging.info(f"CollapsibleGroupWidget created for group '{group_name}'")
        logging.info(f"[GroupPanel.create_group] Group '{group_name}' added to self.groups")
        logging.info(f"[GroupPanel.create_group] Main strands stored: {[s.layer_name for s in self.groups[group_name]['main_strands']]}")

        for strand in strands:
            logging.debug(f"Processing strand '{strand.layer_name}'")
            group_widget.add_layer(
                layer_name=strand.layer_name,
                color=strand.color,
                is_masked=hasattr(strand, 'is_masked') and strand.is_masked
            )
            logging.info(f"Added layer '{strand.layer_name}' to group widget for group '{group_name}'")
            
            # Safely handle control points
            if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2'):
                cp1 = strand.control_point1 if isinstance(strand.control_point1, QPointF) else QPointF(strand.start)
                cp2 = strand.control_point2 if isinstance(strand.control_point2, QPointF) else QPointF(strand.end)
                
                self.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': cp1,
                    'control_point2': cp2
                }
                logging.info(f"Control points set for layer '{strand.layer_name}' in group '{group_name}'")

        self.groups[group_name]['widget'] = group_widget
        self.scroll_layout.addWidget(group_widget)
        logging.info(f"Group widget added to scroll layout for group '{group_name}'")

        # Additional logging to confirm the group is added to the canvas
        if self.canvas and hasattr(self.canvas, 'groups'):
            if group_name in self.canvas.groups:
                logging.info(f"Group '{group_name}' successfully added to canvas.groups")
                # Ensure main strands are properly copied to canvas groups
                self.canvas.groups[group_name]['main_strands'] = main_strands.copy()
                logging.info(f"Main strands copied to canvas.groups: {[s.layer_name for s in main_strands]}")
            else:
                logging.warning(f"Group '{group_name}' not found in canvas.groups after creation")


    def start_group_rotation(self, group_name):
        if group_name in self.groups:
            # Set the active group name
            self.active_group_name = group_name
            if self.canvas:
                # Store the current state of all strands in the group before rotation
                group_data = self.groups[group_name]
                self.pre_rotation_state = {}
                
                for strand in group_data['strands']:
                    # Store all current positions and angles
                    state = {
                        'start': QPointF(strand.start),
                        'end': QPointF(strand.end)
                    }
                    
                    # Only store control points for regular strands, not masked strands
                    if not isinstance(strand, MaskedStrand):
                        state['control_point1'] = QPointF(strand.control_point1)
                        state['control_point2'] = QPointF(strand.control_point2)
                        logging.info(f"Stored pre-rotation state for strand {strand.layer_name}")
                    else:
                        logging.info(f"Skipped storing control points for masked strand {strand.layer_name}")
                             # NEW: Store each deletion rectangle's original corners.
                        if hasattr(strand, 'deletion_rectangles'):
                            rect_corners = []
                            for rect in strand.deletion_rectangles:
                                rect_corners.append({
                                    'top_left': QPointF(*rect['top_left']),
                                    'top_right': QPointF(*rect['top_right']),
                                    'bottom_left': QPointF(*rect['bottom_left']),
                                    'bottom_right': QPointF(*rect['bottom_right'])
                                })
                            state['deletion_rectangles'] = rect_corners
                        # ------------------------------------------------------------------
                
                    self.pre_rotation_state[strand.layer_name] = state
                
                self.canvas.start_group_rotation(group_name)
                dialog = GroupRotateDialog(group_name, self)
                dialog.rotation_updated.connect(self.update_group_rotation)
                dialog.rotation_finished.connect(self.finish_group_rotation)
                dialog.exec_()
            else:
                logging.error("Canvas not properly connected to GroupPanel")
        else:
            logging.warning(f"Attempted to rotate non-existent group: {group_name}")

    def update_group_strands(self, group_name):
        """
        Refresh the group's strands to include any newly added strands.
        """
        group_data = self.groups[group_name]
        # Get all strands that belong to the group's layers
        updated_strands = []
        for strand in self.canvas.strands:
            if strand.layer_name in group_data['layers']:
                if strand not in updated_strands:
                    updated_strands.append(strand)
                # Include any attached strands
                if hasattr(strand, 'attached_strands'):
                    for attached_strand in strand.attached_strands:
                        if attached_strand not in updated_strands:
                            updated_strands.append(attached_strand)
        group_data['strands'] = updated_strands

    def start_smooth_rotation(self, group_name, final_angle, steps=1, interval=1):
        """
        Prepare a smooth rotation using small increments.
        This will rotate from the current angle to final_angle
        in 'steps' increments at 'interval' ms intervals.
        """
        if not hasattr(self, '_smooth_rotation_timer'):
            self._smooth_rotation_timer = QTimer(self)
            self._smooth_rotation_timer.timeout.connect(self._perform_smooth_rotation_step)

        # Cancel any running rotation steps
        if self._smooth_rotation_timer.isActive():
            self._smooth_rotation_timer.stop()

        # Store key info for incremental updates
        self._smooth_rotation_group = group_name
        if not hasattr(self, '_current_group_angles'):
            self._current_group_angles = {}
        # If we do not have a stored angle yet, assume 0
        current_angle = self._current_group_angles.get(group_name, 0.0)

        # Calculate how far we need to rotate
        self._smooth_angle_delta = (final_angle - current_angle) / float(steps)
        self._smooth_angle_iterations_left = steps
        self._current_group_angles[group_name] = current_angle  # Preserve for the loop

        logging.info(f"start_smooth_rotation: from {current_angle:.2f} to {final_angle:.2f}, delta={self._smooth_angle_delta:.2f} over {steps} steps")

        # Start the timer
        self._smooth_rotation_timer.start(interval)
    def _perform_smooth_rotation_step(self):
        """
        Perform one rotation step as part of a short incremental smoothing.
        """
        group_name = getattr(self, '_smooth_rotation_group', None)
        if not group_name or group_name not in self.groups:
            if self._smooth_rotation_timer.isActive():
                self._smooth_rotation_timer.stop()
            return

        if self._smooth_angle_iterations_left <= 0:
            # No more steps left
            if self._smooth_rotation_timer.isActive():
                self._smooth_rotation_timer.stop()
            return

        # Grab current stored angle
        current_angle = self._current_group_angles.get(group_name, 0.0)
        new_angle = current_angle + self._smooth_angle_delta

        # Call our own rotation method instead of super() to avoid recursion errors
        self._perform_immediate_group_rotation(group_name, new_angle)
        logging.debug(f"_perform_smooth_rotation_step: angle={new_angle:.2f} (remaining={self._smooth_angle_iterations_left})")

        # Save the partially updated angle
        self._current_group_angles[group_name] = new_angle
        self._smooth_angle_iterations_left -= 1
    def _perform_immediate_group_rotation(self, group_name, angle):
        """
        Perform an absolute rotation of the group's strands (including MaskedStrand
        deletion rectangles) around the computed center. Each time this is called,
        we restore every point (start, end, control points, rectangle corners) from
        the original, unrotated geometry in self.pre_rotation_state, then rotate
        them by 'angle' degrees. If a control point was originally identical to
        the start or end, keep it pinned to the rotated start or end.

        'angle' is expected in degrees (float).
        """

        # Only rotate if this group is currently active and we have a valid pre_rotation_state
        if group_name != self.active_group_name or not hasattr(self, 'pre_rotation_state'):
            logging.warning(
                f"Attempted to rotate group '{group_name}' without proper pre-rotation state or no active group."
            )
            return

        if not self.canvas or group_name not in self.canvas.groups:
            logging.error(
                "[_perform_immediate_group_rotation] Canvas not present or group data not found."
            )
            return

        group_data = self.canvas.groups[group_name]

        # -- 1) Compute the center of rotation from self.pre_rotation_state --
        center = QPointF(0, 0)
        num_points = 0

        for layer_name, positions in self.pre_rotation_state.items():
            # Add the strand's start/end
            center += positions['start']
            center += positions['end']
            num_points += 2

            # If there are deletion_rectangles, add their corners
            rect_corners = positions.get('deletion_rectangles', [])
            for rect_info in rect_corners:
                center += rect_info['top_left']
                center += rect_info['top_right']
                center += rect_info['bottom_left']
                center += rect_info['bottom_right']
                num_points += 4

        if num_points > 0:
            center /= num_points

        def rotate_point(point: QPointF, pivot: QPointF, angle_degrees: float) -> QPointF:
            """Rotate 'point' around 'pivot' by angle_degrees."""
            angle_radians = math.radians(angle_degrees)
            dx = point.x() - pivot.x()
            dy = point.y() - pivot.y()
            cos_a = math.cos(angle_radians)
            sin_a = math.sin(angle_radians)
            new_x = pivot.x() + dx * cos_a - dy * sin_a
            new_y = pivot.y() + dx * sin_a + dy * cos_a
            return QPointF(new_x, new_y)

        # -- 2) For each strand, restore from pre_rotation_state, then rotate. --
        for strand in group_data.get('strands', []):
            pre_rotation_pos = self.pre_rotation_state.get(strand.layer_name)
            if not pre_rotation_pos:
                continue

            # Restore main geometry
            strand.start = QPointF(pre_rotation_pos['start'])
            strand.end   = QPointF(pre_rotation_pos['end'])

            # If unmasked, restore control points (if they exist)
            if not isinstance(strand, MaskedStrand):
                cp1 = pre_rotation_pos.get('control_point1')
                cp2 = pre_rotation_pos.get('control_point2')

                # Detect if they were the same as the start/end
                pinned_cp1_to_start = (cp1 is not None and cp1 == pre_rotation_pos['start'])
                pinned_cp1_to_end   = (cp1 is not None and cp1 == pre_rotation_pos['end'])
                pinned_cp2_to_start = (cp2 is not None and cp2 == pre_rotation_pos['start'])
                pinned_cp2_to_end   = (cp2 is not None and cp2 == pre_rotation_pos['end'])

                strand.control_point1 = QPointF(cp1) if cp1 else None
                strand.control_point2 = QPointF(cp2) if cp2 else None

            # Rotate strand start/end
            strand.start = rotate_point(strand.start, center, angle)
            strand.end   = rotate_point(strand.end,   center, angle)

            if not isinstance(strand, MaskedStrand):
                # Rotate control points if they exist
                if strand.control_point1 is not None:
                    strand.control_point1 = rotate_point(strand.control_point1, center, angle)
                if strand.control_point2 is not None:
                    strand.control_point2 = rotate_point(strand.control_point2, center, angle)

                # If originally pinned to start/end, re-pin them after rotation
                # This ensures they remain exactly at the rotated strand.start/strand.end
                if pinned_cp1_to_start:
                    strand.control_point1 = strand.start
                elif pinned_cp1_to_end:
                    strand.control_point1 = strand.end

                if pinned_cp2_to_start:
                    strand.control_point2 = strand.start
                elif pinned_cp2_to_end:
                    strand.control_point2 = strand.end

                # Update the group's stored control points (if we track them)
                if 'control_points' not in self.canvas.groups[group_name]:
                    self.canvas.groups[group_name]['control_points'] = {}
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': strand.control_point1,
                    'control_point2': strand.control_point2
                }

            else:
                # For MaskedStrand, rotate each deletion rectangle corner
                original_corners = pre_rotation_pos.get('deletion_rectangles', [])
                while len(strand.deletion_rectangles) < len(original_corners):
                    # Create placeholders if needed
                    strand.deletion_rectangles.append({
                        'top_left': (0, 0),
                        'top_right': (0, 0),
                        'bottom_left': (0, 0),
                        'bottom_right': (0, 0),
                    })

                for rect, orig_corners in zip(strand.deletion_rectangles, original_corners):
                    tl = rotate_point(orig_corners['top_left'],  center, angle)
                    tr = rotate_point(orig_corners['top_right'], center, angle)
                    bl = rotate_point(orig_corners['bottom_left'],  center, angle)
                    br = rotate_point(orig_corners['bottom_right'], center, angle)

                    rect['top_left']     = (tl.x(), tl.y())
                    rect['top_right']    = (tr.x(), tr.y())
                    rect['bottom_left']  = (bl.x(), bl.y())
                    rect['bottom_right'] = (br.x(), br.y())

            # Update shapes, side lines, etc.
            strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()

        # -- 3) Repaint with updated geometry. --
        self.canvas.update()
        logging.info(f"Group '{group_name}' rotated to angle={angle}°, ensuring pinned control points track correctly.")
    def update_group_rotation(self, group_name, angle):
        """
        Public method that starts a smooth rotation toward 'angle'.
        """
        logging.info(f"GroupPanel: Updating group rotation for '{group_name}' by angle={angle}")
        self.start_smooth_rotation(group_name, angle, steps=1, interval=1)



    def finish_group_rotation(self, group_name):
        """Finish the rotation of a group and ensure data is preserved."""
        logging.info(f"GroupPanel: Starting finish_group_rotation for '{group_name}'")
        if self.canvas:
            try:
                # Get the current main strands before preserving
                current_main_strands = []
                if group_name in self.canvas.groups:
                    current_main_strands = self.canvas.groups[group_name].get('main_strands', [])
                    logging.info(f"Current main strands before preservation: {[strand.layer_name if hasattr(strand, 'layer_name') else 'Unknown' for strand in current_main_strands]}")
                
                # Preserve group data
                if self.preserve_group_data(group_name):
                    logging.info(f"Successfully preserved group data for {group_name}")
                else:
                    logging.error(f"Failed to preserve group data for {group_name}")
                    
                # Clean up rotation state
                if hasattr(self, 'pre_rotation_state'):
                    delattr(self, 'pre_rotation_state')
                    logging.info("Cleaned up pre-rotation state")
                
                # Finish rotation in canvas
                self.canvas.finish_group_rotation(group_name)
                self.canvas.update()
                
            except Exception as e:
                logging.error(f"Error during finish_group_rotation: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
        else:
            logging.error("Canvas not properly connected to GroupPanel")
        
        # Clear the active group name
        self.active_group_name = None




    def delete_group(self, group_name):
        if group_name in self.groups:
            # Remove group from canvas if applicable
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
                logging.info(f"Group '{group_name}' removed from canvas.")
            else:
                logging.warning(f"Group '{group_name}' not found in canvas.")

            self.group_operation.emit("delete", group_name, self.groups[group_name]['layers'])
            group_widget = self.groups.pop(group_name)['widget']
            self.scroll_layout.removeWidget(group_widget)
            group_widget.deleteLater()
            logging.info(f"Group '{group_name}' deleted.")
        else:
            logging.warning(f"Group '{group_name}' not found in GroupPanel.")
    def update_layer(self, index, layer_name, color):
        # Update the layer information in the groups
        for group_name, group_info in self.groups.items():
            if layer_name in group_info['layers']:
                group_widget = self.findChild(CollapsibleGroupWidget, group_name)
                if group_widget:
                    group_widget.update_layer(index, layer_name, color)

    def edit_strand_angles(self, group_name):
        if group_name in self.groups:
            # Get all strands in the group, including main strands
            group_data = self.groups[group_name]
            all_strands = []
            
            # First, add all main strands from the layers
            for layer_name in group_data['layers']:
                strand = self.canvas.find_strand_by_name(layer_name)
                if strand and strand not in all_strands:
                    all_strands.append(strand)
                    logging.info(f"Added main strand {layer_name} to angle edit list")
            
            # Then add any attached strands
            for strand in all_strands.copy():  # Use copy to avoid modifying while iterating
                if hasattr(strand, 'attached_strands'):
                    for attached_strand in strand.attached_strands:
                        if attached_strand not in all_strands:
                            all_strands.append(attached_strand)
                            logging.info(f"Added attached strand {attached_strand.layer_name} to angle edit list")
            
            # Update the group's strands list
            group_data['strands'] = all_strands
            
            # Create editable layers list
            editable_layers = [strand.layer_name for strand in all_strands 
                              if self.is_layer_editable(strand.layer_name)]
            
            dialog = StrandAngleEditDialog(
                group_name, 
                {
                    'strands': all_strands,
                    'layers': [strand.layer_name for strand in all_strands],
                    'editable_layers': editable_layers
                }, 
                self.canvas, 
                self
            )
            dialog.finished.connect(lambda: self.update_group_after_angle_edit(group_name))
            dialog.exec_()
    def finish_group_rotation(self, group_name):
        """Finish the rotation of a group and ensure data is preserved."""
        logging.info(f"GroupPanel: Starting finish_group_rotation for '{group_name}'")
        if self.canvas:
            try:
                # Get the current main strands before preserving
                current_main_strands = []
                if group_name in self.canvas.groups:
                    current_main_strands = self.canvas.groups[group_name].get('main_strands', [])
                    logging.info(f"Current main strands before preservation: {current_main_strands}")
                    # Log details of each main strand
                    for strand in current_main_strands:
                        logging.info(f"Main strand details - Name: {strand.layer_name if hasattr(strand, 'layer_name') else 'Unknown'}, "
                               f"Type: {type(strand).__name__}, "
                               f"Start: {strand.start if hasattr(strand, 'start') else 'Unknown'}, "
                               f"End: {strand.end if hasattr(strand, 'end') else 'Unknown'}")
                
                # Preserve group data
                if self.preserve_group_data(group_name):
                    # Ensure main strands are preserved
                    if current_main_strands:
                        self.canvas.groups[group_name]['main_strands'] = current_main_strands
                        # Log the preserved main strands
                        logging.info(f"Successfully preserved main strands for {group_name}:")
                        for strand in current_main_strands:
                            logging.info(f"Preserved main strand - Name: {strand.layer_name if hasattr(strand, 'layer_name') else 'Unknown'}, "
                                       f"Type: {type(strand).__name__}")
                    logging.info(f"Successfully preserved group data for {group_name}")
                    logging.info(f"Main strands after preservation: {[strand.layer_name if hasattr(strand, 'layer_name') else 'Unknown' for strand in self.canvas.groups[group_name].get('main_strands', [])]}")
                else:
                    logging.error(f"Failed to preserve group data for {group_name}")
                    
                # Clean up rotation state
                if hasattr(self, 'pre_rotation_state'):
                    delattr(self, 'pre_rotation_state')
                    logging.info("Cleaned up pre-rotation state")
                
                # Finish rotation in canvas
                self.canvas.finish_group_rotation(group_name)
                self.canvas.update()
                
                # Validate the group data
                if hasattr(self.canvas, 'validate_group_data'):
                    self.canvas.validate_group_data(group_name)
                
            except Exception as e:
                logging.error(f"Error during finish_group_rotation: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
        else:
            logging.error("Canvas not properly connected to GroupPanel")
        
        # Clear the active group name
        self.active_group_name = None
    def preserve_group_data(self, group_name):
        """Ensure group data is preserved in both GroupPanel and Canvas."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            logging.info(f"Initial group data for {group_name}: {group_data}")
            logging.info(f"Preserving group '{group_name}' data")
            logging.info(f"Main strands before preservation: {[s.layer_name for s in group_data.get('main_strands', [])]}")            
            # Update canvas groups
            if not hasattr(self.canvas, 'groups'):
                self.canvas.groups = {}
                logging.info("Created new canvas.groups dictionary")
                
            # Get all strands for this group
            group_strands = group_data.get('strands', [])
            logging.info(f"Found {len(group_strands)} strands in group {group_name}")
            
            # Log main strands before update
            logging.info(f"Main strands before update: {group_data.get('main_strands', [])}")
            
            # Create updated group data
            updated_group_data = {
                'layers': [strand.layer_name for strand in group_strands],
                'strands': group_strands,
                'control_points': {},
                'main_strands': group_data.get('main_strands', [])
            }
            
            logging.info(f"Updated group data structure: {updated_group_data}")
            logging.info(f"Preserved main strands for group {group_name}: {updated_group_data['main_strands']}")
            
            # Update control points
            for strand in group_strands:
                if hasattr(strand, 'layer_name'):
                    updated_group_data['control_points'][strand.layer_name] = {
                        'control_point1': QPointF(strand.control_point1),
                        'control_point2': QPointF(strand.control_point2)
                    }
                    logging.info(f"Added control points for strand {strand.layer_name}")
            
            # Update the canvas groups
            self.canvas.groups[group_name] = updated_group_data
            
            logging.info(f"Final preserved group data for {group_name}: {updated_group_data}")
            return True
            
        logging.warning(f"Group {group_name} not found in self.groups")
        return False 

    def rotate_any_group(self, group_name: str, new_angle: float):
        """
        Rotate the specified group by the given new_angle.
        This ensures rotating_group_name is set for both masked/unmasked groups.
        """
        if not group_name:
            return

        if not hasattr(self, 'canvas'):
            logging.error("No canvas available to rotate the group.")
            return

        # 1) Mark the group as active
        self.canvas.start_group_rotation(group_name)

        # 2) Perform actual rotation
        self.canvas.rotate_group(group_name, new_angle)

        # 3) Finish the rotation
        self.canvas.finish_group_rotation(group_name)

        logging.info(f"rotate_any_group finished for '{group_name}' with angle {new_angle}")     
    def update_group_after_angle_edit(self, group_name):
        """Update group data after angle adjustments."""
        if group_name in self.groups and self.canvas:
            group_data = self.groups[group_name]
            
            # Refresh the complete list of strands
            all_strands = []
            
            # First get all main strands
            for layer_name in group_data['layers']:
                strand = self.canvas.find_strand_by_name(layer_name)
                if strand and strand not in all_strands:
                    all_strands.append(strand)
                    logging.info(f"Updated main strand {layer_name} in group after angle edit")
            
            # Then get their attached strands
            for strand in all_strands.copy():
                if hasattr(strand, 'attached_strands'):
                    for attached_strand in strand.attached_strands:
                        if attached_strand not in all_strands:
                            all_strands.append(attached_strand)
                            logging.info(f"Updated attached strand {attached_strand.layer_name} in group after angle edit")
            
            # Update the group's strands list
            group_data['strands'] = all_strands
            
            # Update control points data
            group_data['control_points'] = {}
            for strand in all_strands:
                # Skip masked strands
                if isinstance(strand, MaskedStrand):
                    logging.info(f"Skipping control point update for masked strand {strand.layer_name}")
                    continue

                group_data['control_points'][strand.layer_name] = {
                    'control_point1': QPointF(strand.control_point1) if strand.control_point1 is not None else QPointF(strand.start),
                    'control_point2': QPointF(strand.control_point2) if strand.control_point2 is not None else QPointF(strand.end)
                }
            
            logging.info(f"Updated group '{group_name}' data after angle adjustment with {len(all_strands)} strands")
    def is_layer_editable(self, layer_name):
        # This method should check if the layer has a green rectangle
        layer_button = next((button for button in self.layer_panel.layer_buttons if button.text() == layer_name), None)
        return layer_button is not None and layer_button.isEnabled()

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class GroupMoveDialog(QDialog):
    move_updated = pyqtSignal(str, float, float)  # group_name, dx, dy
    move_finished = pyqtSignal(str)  # group_name

    def __init__(self, canvas, group_name):
        super().__init__()
        self.canvas = canvas  # Canvas instance
        self.group_name = group_name  # Group name string
        self.total_dx = 0
        self.total_dy = 0
        
        # Initialize language code
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        
        self.setWindowTitle(f"{_['move_group']}: {group_name}")
        
        # Initialize original positions
        self.initialize_original_positions()
        self.setup_ui()

    def initialize_original_positions(self):
        """Store the original positions of all strands in the group."""
        group_data = self.canvas.groups.get(self.group_name)
        if not group_data:
            logging.warning(f"No group data found for {self.group_name}")
            return

        for strand in group_data['strands']:
            # Store original positions
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)
            
            # Safely store original control points
            strand.original_control_point1 = (
                QPointF(strand.control_point1) if isinstance(strand.control_point1, QPointF) 
                else QPointF(strand.start)
            )
            strand.original_control_point2 = (
                QPointF(strand.control_point2) if isinstance(strand.control_point2, QPointF) 
                else QPointF(strand.end)
            )

            logging.debug(f"Stored original positions for strand {strand.layer_name}: "
                        f"Start: {strand.original_start}, "
                        f"End: {strand.original_end}, "
                        f"CP1: {strand.original_control_point1}, "
                        f"CP2: {strand.original_control_point2}")

    def setup_ui(self):
        _ = translations[self.language_code]
        layout = QVBoxLayout(self)

        # X movement controls
        x_layout = QHBoxLayout()
        x_label = QLabel(_['x_movement'])
        self.dx_slider = QSlider(Qt.Horizontal)
        self.dx_slider.setRange(-600, 600)
        self.dx_slider.setValue(0)
        self.dx_value = QLabel("0")
        self.dx_input = QLineEdit()
        self.dx_input.setValidator(QIntValidator(-600, 600))
        self.dx_input.setText("0")
        
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.dx_slider)
        x_layout.addWidget(self.dx_value)
        x_layout.addWidget(self.dx_input)

        # Y movement controls
        y_layout = QHBoxLayout()
        y_label = QLabel(_['y_movement'])
        self.dy_slider = QSlider(Qt.Horizontal)
        self.dy_slider.setRange(-600, 600)
        self.dy_slider.setValue(0)
        self.dy_value = QLabel("0")
        self.dy_input = QLineEdit()
        self.dy_input.setValidator(QIntValidator(-600, 600))
        self.dy_input.setText("0")
        
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.dy_slider)
        y_layout.addWidget(self.dy_value)
        y_layout.addWidget(self.dy_input)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton(_['ok'])
        cancel_button = QPushButton(_['cancel'])
        snap_button = QPushButton(_['snap_to_grid'])
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(snap_button)

        # Add all layouts to main layout
        layout.addLayout(x_layout)
        layout.addLayout(y_layout)
        layout.addLayout(button_layout)

        # Connect signals
        self.dx_slider.valueChanged.connect(self.update_dx_from_slider)
        self.dy_slider.valueChanged.connect(self.update_dy_from_slider)
        self.dx_input.textChanged.connect(self.update_dx_from_input)
        self.dy_input.textChanged.connect(self.update_dy_from_input)
        ok_button.clicked.connect(self.on_ok_clicked)
        cancel_button.clicked.connect(self.reject)
        snap_button.clicked.connect(self.snap_to_grid)

    def update_positions(self):
        """Update positions based on original positions and current deltas"""
        if self.canvas and self.group_name in self.canvas.groups:
            group_data = self.canvas.groups[self.group_name]
            
            # Create exact delta point
            delta = QPointF(self.total_dx, self.total_dy)
            logging.info(f"Moving by delta: ({self.total_dx}, {self.total_dy})")

            for strand in group_data['strands']:
                # Temporarily disable shape updates
                strand.updating_position = True  # Add this flag to Strand class if not exists
                
                # Move all points by exactly the same delta
                strand.start = strand.original_start + delta
                strand.end = strand.original_end + delta
                strand.control_point1 = strand.original_control_point1 + delta
                strand.control_point2 = strand.original_control_point2 + delta
                
                logging.info(f"Updated positions for strand {strand.layer_name}:")
                logging.info(f"  Start: {strand.start}")
                logging.info(f"  End: {strand.end}")
                logging.info(f"  Control1: {strand.control_point1}")
                logging.info(f"  Control2: {strand.control_point2}")
                
                # Update the strand's shape without updating control points
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
                
                # Re-enable shape updates
                strand.updating_position = False

            # Emit the movement signal with exact values
            self.move_updated.emit(self.group_name, float(self.total_dx), float(self.total_dy))
            # Update the canvas
            self.canvas.update()

    def update_dx_from_slider(self):
        self.total_dx = int(self.dx_slider.value())  # Ensure integer value
        self.dx_value.setText(str(self.total_dx))
        self.dx_input.setText(str(self.total_dx))
        self.update_positions()

    def update_dy_from_slider(self):
        self.total_dy = int(self.dy_slider.value())  # Ensure integer value
        self.dy_value.setText(str(self.total_dy))
        self.dy_input.setText(str(self.total_dy))
        self.update_positions()

    def update_dx_from_input(self):
        try:
            value = int(self.dx_input.text())
            value = max(min(value, 600), -600)
            self.total_dx = value
            self.dx_slider.setValue(value)
            self.dx_value.setText(str(value))
            self.update_positions()
        except ValueError:
            pass

    def update_dy_from_input(self):
        try:
            value = int(self.dy_input.text())
            value = max(min(value, 600), -600)
            self.total_dy = value
            self.dy_slider.setValue(value)
            self.dy_value.setText(str(value))
            self.update_positions()
        except ValueError:
            pass

    def on_ok_clicked(self):
        """Finalize the movement by storing current positions as new originals"""
        if self.canvas and self.group_name in self.canvas.groups:
            group_data = self.canvas.groups[self.group_name]
            for strand in group_data['strands']:
                # Store final positions as new originals
                strand.original_start = QPointF(strand.start)
                strand.original_end = QPointF(strand.end)
                strand.original_control_point1 = QPointF(strand.control_point1)
                strand.original_control_point2 = QPointF(strand.control_point2)
        self.move_finished.emit(self.group_name)
        self.accept()

    def snap_to_grid(self):
        if self.canvas:
            self.canvas.snap_group_to_grid(self.group_name)
        self.move_finished.emit(self.group_name)
        self.accept()





class LayerSelectionDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Layers for Group (Sélectionner les calques pour le groupe)")
        self.layout = QVBoxLayout(self)
        
        self.layer_list = QListWidget()
        for layer in layers:
            # Exclude masked layers (those with names following the pattern x_y_z_w)
            if len(layer.split('_')) != 4:
                item = QListWidgetItem(layer)
                item.setCheckState(Qt.Unchecked)
                self.layer_list.addItem(item)
        
        self.layout.addWidget(self.layer_list)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_selected_layers(self):
        return [self.layer_list.item(i).text() for i in range(self.layer_list.count()) 
                if self.layer_list.item(i).checkState() == Qt.Checked]

import json
import logging
from PyQt5.QtCore import QPointF, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QInputDialog, QPushButton

# group_layers.py
class GroupLayerManager:
    def __init__(self, parent, layer_panel, canvas=None):
        self.main_window = parent  # Reference to the main window
        self.parent = parent
        self.layer_panel = layer_panel
        self.canvas = canvas
        self.groups = {} 
        if self.canvas:
            self.canvas.masked_layer_created.connect(self.update_groups_with_new_strand)
        # Set language_code appropriately
        if self.canvas and hasattr(self.canvas, 'language_code'):
            self.language_code = self.canvas.language_code
        elif hasattr(self.parent, 'language_code'):
            self.language_code = self.parent.language_code
        else:
            self.language_code = 'en'  # Default to English

        if self.language_code in translations:
            _ = translations[self.language_code]
        else:
            logging.error(f"Invalid language_code: {self.language_code}. Defaulting to 'en'.")
            _ = translations['en']
            self.language_code = 'en'

        logging.info(f"GroupLayerManager initialized with language_code: {self.language_code}")

        # Initialize the group panel
        self.group_panel = GroupPanel(self.layer_panel, canvas=self.canvas)
        self.group_panel.setParent(parent)  # Set the parent to the main window or appropriate parent
        
        # Create the 'Create Group' button
        self.create_group_button = QPushButton(_['create_group'])
        self.create_group_button.clicked.connect(self.create_group)

        # Connect to language_changed signal
        if hasattr(self.parent, 'language_changed'):
            self.parent.language_changed.connect(self.update_translations)

        # Call update_translations to ensure UI is updated
        self.update_translations()
    def create_group_with_params(self, group_name, selected_main_strands, skip_dialog=False):
        """Create a group with pre-selected parameters."""
        logging.info(f"Creating group {group_name} with main strands: {selected_main_strands}")
        
        # Collect all strands that match the main_strands
        selected_strands = []
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer in selected_main_strands:
                selected_strands.append(strand)
                logging.info(f"Added strand {strand.layer_name} to group {group_name}")
        
        if not selected_strands:
            logging.warning(f"No strands found for main strands: {selected_main_strands}")
            return
        
        # Initialize the group in canvas.groups
        if self.canvas:
            self.canvas.groups[group_name] = {
                'strands': selected_strands,
                'layers': [s.layer_name for s in selected_strands],
                'main_strands': set(selected_main_strands),
                'control_points': {},
                'data': []
            }
            logging.info(f"Initialized group {group_name} in canvas.groups")
        
        # Create the group in the group panel
        if hasattr(self, 'group_panel'):
            self.group_panel.create_group(group_name, selected_strands)
            logging.info(f"Created group {group_name} in group panel with {len(selected_strands)} strands")
    def extract_main_layer(self, layer_name):
        """Extract the first main layer number from a layer name."""
        parts = layer_name.split('_')
        if parts and parts[0].isdigit():
            return parts[0]
        return None
    def recreate_group(self, group_name, new_strand, original_main_strands=None):
        """Recreate a group after a strand is attached, maintaining all original branches."""
        logging.info(f"[GroupLayerManager.recreate_group] Starting recreation of group '{group_name}'")
        logging.info(f"[GroupLayerManager.recreate_group] New strand: {new_strand.layer_name if hasattr(new_strand, 'layer_name') else 'Unknown'}")
        
        # Helper function to convert string to strand object if needed
        def ensure_strand_object(strand_id):
            if isinstance(strand_id, str):
                # If it's just a number, append "_1" to get the main strand name
                if strand_id.isdigit():
                    strand_id = f"{strand_id}_1"
                # Find the actual strand object by name
                for strand in self.canvas.strands:
                    if hasattr(strand, 'layer_name') and strand.layer_name == strand_id:
                        return strand
                logging.warning(f"Could not find strand object for {strand_id}")
                return None
            return strand_id

        # Initialize main strands set
        all_main_strands = set()
        
        # Process original main strands - this should be the primary source of main strands
        if original_main_strands:
            for strand_id in original_main_strands:
                strand_obj = ensure_strand_object(strand_id)
                if strand_obj:
                    all_main_strands.add(strand_obj)
            logging.info(f"[GroupLayerManager.recreate_group] Added original main strands: {[s.layer_name for s in all_main_strands]}")
        
        # Only if we have no main strands, check existing group data
        if not all_main_strands and self.canvas and group_name in self.canvas.groups:
            existing_group = self.canvas.groups[group_name]
            if 'main_strands' in existing_group:
                for strand in existing_group['main_strands']:
                    strand_obj = ensure_strand_object(strand)
                    if strand_obj:
                        all_main_strands.add(strand_obj)
                logging.info(f"[GroupLayerManager.recreate_group] Added existing main strands: {[s.layer_name for s in all_main_strands]}")
        
        # Only if we still have no main strands, derive from strands (last resort)
        if not all_main_strands and self.canvas:
            for strand in self.canvas.strands:
                if hasattr(strand, 'layer_name'):
                    parts = strand.layer_name.split('_')
                    if len(parts) == 2 and parts[1] == '1':  # Only add main strands (x_1 pattern)
                        all_main_strands.add(strand)
            if all_main_strands:
                logging.info(f"Derived main strands from existing strands: {[s.layer_name for s in all_main_strands]}")
        
        # Initialize the group in canvas.groups
        self.canvas.groups[group_name] = {
            'layers': [],
            'strands': [],
            'control_points': {},
            'main_strands': list(all_main_strands)
        }
        
        # Collect all strands for each branch
        all_strands = []
        for main_strand in all_main_strands:
            if hasattr(main_strand, 'layer_name'):
                branch = self.extract_main_layer(main_strand.layer_name)
                branch_strands = []
                for strand in self.canvas.strands:
                    if hasattr(strand, 'layer_name') and self.extract_main_layer(strand.layer_name) == branch:
                        branch_strands.append(strand)
                        logging.info(f"Added strand {strand.layer_name} to branch {branch}")
                logging.info(f"Found {len(branch_strands)} strands for branch {branch}")
                all_strands.extend(branch_strands)
        
        # Add all strands to the group
        for strand in all_strands:
            if hasattr(strand, 'layer_name'):
                self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                self.canvas.groups[group_name]['strands'].append(strand)
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': strand.control_point1 if hasattr(strand, 'control_point1') else None,
                    'control_point2': strand.control_point2 if hasattr(strand, 'control_point2') else None
                }
                logging.info(f"Added strand {strand.layer_name} to group {group_name}")
        
        # Create the group in the group panel
        self.group_panel.create_group(group_name, all_strands)
        logging.info(f"Created group {group_name} in group panel with {len(all_strands)} strands")
        
        # Verify final group composition
        final_branches = set()
        for strand in all_strands:
            if hasattr(strand, 'layer_name'):
                final_branches.add(self.extract_main_layer(strand.layer_name))
        logging.info(f"Final group composition - branches: {list(final_branches)}, total strands: {len(all_strands)}")
    def preserve_group_data(self, group_name):
        """Store the current group data before any transformations."""
        if self.canvas and group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            preserved_data = {
                'main_strands': list(group_data.get('main_strands', [])),
                'layers': list(group_data.get('layers', [])),
                'strands': list(group_data.get('strands', [])),
                'control_points': dict(group_data.get('control_points', {})),
                'data': list(group_data.get('data', []))
            }
            self.canvas.preserved_group_data = preserved_data
            logging.info(f"Preserved group data for {group_name}: {preserved_data}")
            return preserved_data
        return None


    def restore_group_data(self, group_name):
        """Restore preserved group data after transformations."""
        if hasattr(self.canvas, 'preserved_group_data'):
            if group_name in self.canvas.groups:
                self.canvas.groups[group_name].update(self.canvas.preserved_group_data)
                logging.info(f"Restored group data for {group_name}: {self.canvas.preserved_group_data}")
            else:
                self.canvas.groups[group_name] = self.canvas.preserved_group_data
                logging.info(f"Group '{group_name}' did not exist. Restored with preserved data.")
            delattr(self.canvas, 'preserved_group_data')
        else:
            logging.warning("No preserved group data to restore.")
    def update_translations(self):
        # Fetch the translations for the current language code
        if self.language_code in translations:
            _ = translations[self.language_code]
        else:
            logging.error(f"Invalid language_code: {self.language_code} in update_translations. Defaulting to 'en'.")
            _ = translations['en']
            self.language_code = 'en'

        logging.info(f"Updating translations for language_code: {self.language_code}")

        # Update button texts and any other UI elements
        self.create_group_button.setText(_['create_group'])
        # Update other UI elements as needed

    def set_canvas(self, canvas):
        self.canvas = canvas
        self.group_panel.set_canvas(canvas)
        logging.info(f"Canvas set on GroupLayerManager: {self.canvas}")
        # Connect the language_changed signal to update_translations
        self.canvas.language_changed.connect(self.update_translations)
        # Call update_translations to update UI
        self.update_translations()
    def on_strand_created(self, new_strand):
        logging.info(f"New strand created: {new_strand.layer_name}")
        self.update_groups_with_new_strand(new_strand)
        # Update groups with the new strand
        self.group_layer_manager.update_groups_with_new_strand(new_strand)

    def on_strand_attached(self, parent_strand, new_strand):
        logging.info(f"New strand attached: {new_strand.layer_name} to {parent_strand.layer_name}")
        self.update_groups_with_new_strand(new_strand)

    def add_strand_to_group(self, group_name, strand):
        """Add a strand to an existing group."""
        logging.info(f"Attempting to add strand {strand.layer_name} to group {group_name}")
        if group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            if strand.layer_name not in group_data['layers']:
                # Add to canvas groups
                group_data['layers'].append(strand.layer_name)
                group_data['strands'].append(strand)
                
                # Add to group panel groups
                if hasattr(self, 'group_panel'):
                    self.group_panel.add_layer_to_group(strand.layer_name, group_name)
                
                logging.info(f"Successfully added strand {strand.layer_name} to group {group_name}")
            else:
                logging.info(f"Strand {strand.layer_name} already in group {group_name}")
        else:
            logging.warning(f"Group {group_name} not found")


    def update_groups_with_new_strand(self, new_strand):
        """
        Checks all groups and deletes any that are invalidated by the addition of new_strand.
        """
        groups_to_delete = []

        # Check if this is a masked strand
        if isinstance(new_strand, MaskedStrand):
            # For masked strands, get the original layer names being masked
            original_layer_names = new_strand.layer_name.split('_')[:2]  # Gets ['1', '2'] from '1_2_2_2'
            logging.info(f"Checking groups for masked strand with original layers: {original_layer_names}")
            
            # Find any groups containing any of the masked layers
            for group_name, group_data in list(self.group_panel.groups.items()):
                for layer in group_data['layers']:
                    main_layer = self.extract_main_layer(layer)
                    if main_layer in original_layer_names:
                        logging.info(f"Group '{group_name}' will be deleted because it contains layer '{layer}' that was masked")
                        groups_to_delete.append(group_name)
                        break
        else:
            # For regular strands, check if parent strand is in any group
            for group_name, group_data in self.canvas.groups.items():
                # Get parent strand layer name based on strand type
                parent_layer_name = None
                if hasattr(new_strand, 'parent_strand'):
                    parent_layer_name = new_strand.parent_strand.layer_name
                elif hasattr(new_strand, 'attached_to'):
                    parent_layer_name = new_strand.attached_to.layer_name
                
                if parent_layer_name and any(strand.layer_name == parent_layer_name for strand in group_data['strands']):
                    logging.info(f"Found group '{group_name}' containing parent strand")
                    # Store the original main strands before deletion
                    original_main_strands = list(group_data.get('main_strands', []))
                    logging.info(f"Stored original main strands for {group_name}: {[s.layer_name for s in original_main_strands]}")
                    
                    # Delete and recreate the group with the new strand
                    self.delete_group(group_name)
                    self.recreate_group(group_name, new_strand, original_main_strands)

        # Delete the identified groups
        for group_name in groups_to_delete:
            logging.info(f"Deleting group '{group_name}' due to masked strand creation")
            self.group_panel.delete_group(group_name)
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
                logging.info(f"Group '{group_name}' deleted from canvas groups")

    def extract_main_layer(self, layer_name):
        """Extract the main layer number from a layer name (e.g., '1' from '1_1')."""
        parts = layer_name.split('_')
        return parts[0] if parts else layer_name
    def open_main_strand_selection_dialog(self, main_strands):
        # Access the current translation dictionary
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        dialog = QDialog(self.layer_panel)
        dialog.setWindowTitle(_['select_main_strands'])

        # Apply the current theme's stylesheet to the dialog
        if self.canvas and hasattr(self.canvas, 'is_dark_mode'):
            is_dark_mode = self.canvas.is_dark_mode
        else:
            is_dark_mode = False  # Default to light mode

        if is_dark_mode:
            # Dark theme stylesheet
            dark_stylesheet = """
                QDialog, QWidget {
                    background-color: #1C1C1C;
                    color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QCheckBox {
                    color: #FFFFFF;
                    background-color: transparent;
                    padding: 2px;
                }
                QCheckBox::indicator {
                    border: 1px solid #777777;
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    background-color: #2B2B2B;  /* Dark background when unchecked */
                }
                QCheckBox::indicator:checked {
                    background-color: #FFFFFF;  /* Light background when checked */
                }
                QPushButton {
                    background-color: #2B2B2B;
                    color: #FFFFFF;
                    border: 1px solid #777777;
                    border-radius: 5px;
                    min-width: 50px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                }
                QPushButton:pressed {
                    background-color: #1C1C1C;
                }
            """
            dialog.setStyleSheet(dark_stylesheet)
        else:
            # Light theme stylesheet
            light_stylesheet = """
                QDialog, QWidget {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QCheckBox {
                    color: #000000;
                    background-color: transparent;
                    padding: 2px;
                }
                QCheckBox::indicator {
                    border: 1px solid #CCCCCC;
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    background-color: #FFFFFF;  /* Light background when unchecked */
                }
                QCheckBox::indicator:checked {
                    background-color: #BBBBBB;  /* Dark background when checked */
                }
                QPushButton {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #BBBBBB;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
            """
            dialog.setStyleSheet(light_stylesheet)

        layout = QVBoxLayout()

        # Create the info label
        info_label = QLabel(_['select_main_strands_to_include_in_the_group'])
        layout.addWidget(info_label)

        checkboxes = []
        for main_strand in main_strands:
            checkbox = QCheckBox(str(main_strand))
            layout.addWidget(checkbox)
            checkboxes.append((main_strand, checkbox))

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton(_['cancel'])
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        dialog.setLayout(layout)

        selected_main_strands = []

        def on_ok():
            for main_strand, checkbox in checkboxes:
                if checkbox.isChecked():
                    selected_main_strands.append(main_strand)
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        if dialog.exec_() == QDialog.Accepted:
            return set(selected_main_strands)
        else:
            return None
    def extract_main_layers(self, layer_name):
        # Split the layer name by underscores and collect all numeric parts
        parts = layer_name.split('_')
        main_layers = set()

        for part in parts:
            if part.isdigit():
                main_layers.add(part)

        return main_layers    


    # In GroupLayerManager
    # In GroupLayerManager
    def create_group(self):
        """Create a new group with selected main strands and their control points."""
        # Access the current translation dictionary
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        # Prompt the user to enter a group name with translated text
        group_name, ok = QInputDialog.getText(
            self.layer_panel, _['create_group'], _['enter_group_name']
        )
        
        if not ok or not group_name:
            logging.info("Group creation cancelled - no name provided")
            return

        # Get the available main strands
        main_strands = self.get_unique_main_strands()

        # Open a dialog to select main strands to include in the group
        selected_main_strands = self.open_main_strand_selection_dialog(main_strands)
        if not selected_main_strands:
            logging.info(_['group_creation_cancelled'])
            return

        # Convert selected_main_strands to a set
        selected_main_strands = set(selected_main_strands)

        # Create the group in canvas.groups first
        if self.canvas:
            self.canvas.groups[group_name] = {
                'strands': [],
                'layers': [],
                'main_strands': selected_main_strands,
                'control_points': {},
                'data': []
            }
            logging.info(f"Initialized empty group '{group_name}' in canvas.groups")

        # Collect strands that match the selected main strands
        selected_strands = []
        layers_data = []
        
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer in selected_main_strands:
                selected_strands.append(strand)  # Keep original strands for group panel
                
                # Safely handle control points
                cp1 = strand.control_point1 if isinstance(strand.control_point1, QPointF) else QPointF(strand.start)
                cp2 = strand.control_point2 if isinstance(strand.control_point2, QPointF) else QPointF(strand.end)
                
                # Create a deep copy of the strand data including control points
                strand_data = {
                    'layer_name': strand.layer_name,
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end),
                    'control_point1': cp1,
                    'control_point2': cp2,
                    'width': strand.width,
                    'color': QColor(strand.color),
                    'stroke_color': QColor(strand.stroke_color),
                    'stroke_width': strand.stroke_width,
                    'has_circles': strand.has_circles.copy(),
                    'attached_strands': strand.attached_strands.copy(),
                    'is_first_strand': strand.is_first_strand,
                    'is_start_side': strand.is_start_side,
                    'set_number': strand.set_number
                }
                layers_data.append(strand_data)

                # Add to canvas groups
                if self.canvas and group_name in self.canvas.groups:
                    self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                    self.canvas.groups[group_name]['strands'].append(strand)
                    self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                        'control_point1': cp1,
                        'control_point2': cp2
                    }

        if not selected_strands:
            logging.warning(f"No strands found for selected main strands: {selected_main_strands}")
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
            return

        # Create the group in the group panel with original strand objects
        self.group_panel.create_group(group_name, selected_strands)

        # Update the group in canvas.groups with all data
        if self.canvas and group_name in self.canvas.groups:
            self.canvas.groups[group_name].update({
                'strands': selected_strands,
                'layers': [strand.layer_name for strand in selected_strands],
                'data': layers_data,
                'main_strands': selected_main_strands,
                'control_points': {
                    strand.layer_name: {
                        'control_point1': QPointF(strand.start) if strand.control_point1 is None else QPointF(strand.control_point1),
                        'control_point2': QPointF(strand.end) if strand.control_point2 is None else QPointF(strand.control_point2)
                    } for strand in selected_strands
                }
            })
            logging.info(f"Added group '{group_name}' to canvas.groups with {len(selected_strands)} strands")

        # Verify control points were saved
        for layer_name, control_points in self.canvas.groups[group_name]['control_points'].items():
            logging.debug(f"Saved control points for {layer_name}: "
                        f"CP1: {control_points['control_point1']}, "
                        f"CP2: {control_points['control_point2']}")

        logging.info(f"Created group '{group_name}' with {len(selected_strands)} strands")
        
        # Update the UI
        if hasattr(self.canvas, 'update'):
            self.canvas.update()
    def get_main_layers(self):
        return list(set([layer.split('_')[0] for layer in self.get_all_layers()]))

    def get_sub_layers(self, main_layer):
        return [layer for layer in self.get_all_layers() if layer.startswith(f"{main_layer}_")]

    def get_all_layers(self):
        return [button.text() for button in self.layer_panel.layer_buttons]

    def get_layer_index(self, layer_name):
        return self.layer_panel.layer_buttons.index(next(button for button in self.layer_panel.layer_buttons if button.text() == layer_name))
    def get_unique_main_strands(self):
        unique_main_strands = set()
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer:
                unique_main_strands.add(main_layer)
        return unique_main_strands
    def save(self, filename):
        data = {
            "groups": self.get_group_data(),  # Ensure group data is included
            "strands": [self.serialize_strand(strand) for strand in self.canvas.strands]
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved group and strand data to {filename}")
    def load(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.clear()
        self.canvas.strands = [self.deserialize_strand(strand_data) for strand_data in data["strands"]]
        self.apply_group_data(data["groups"])  # Ensure group data is applied
        logging.info(f"Loaded group and strand data from {filename}")
    def serialize_strand(self, strand):
        return {
            "layer_name": strand.layer_name,
            "start": {"x": strand.start.x(), "y": strand.start.y()},
            "end": {"x": strand.end.x(), "y": strand.end.y()},
            "control_point1": {"x": strand.control_point1.x(), "y": strand.control_point1.y()},
            "control_point2": {"x": strand.control_point2.x(), "y": strand.control_point2.y()},
            "width": strand.width,
            "color": self.serialize_color(strand.color),
            "is_masked": isinstance(strand, MaskedStrand),
            "attached_strands": [self.canvas.strands.index(attached_strand) for attached_strand in strand.attached_strands],
            "has_circles": strand.has_circles.copy()
        }

    def deserialize_strand(self, data):
        start = QPointF(data["start"]["x"], data["start"]["y"])
        end = QPointF(data["end"]["x"], data["end"]["y"])
        control_point1 = QPointF(data["control_point1"]["x"], data["control_point1"]["y"])
        control_point2 = QPointF(data["control_point2"]["x"], data["control_point2"]["y"])
        
        strand = Strand(start, end, data["width"])
        strand.control_point1 = control_point1
        strand.control_point2 = control_point2
        strand.color = self.deserialize_color(data["color"])
        strand.has_circles = data["has_circles"]
        strand.attached_strands = [self.canvas.strands[i] for i in data["attached_to"]]
        return strand

    def serialize_color(self, color):
        return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}

    def deserialize_color(self, data):
        return QColor(data["r"], data["g"], data["b"], data["a"])



    def clear(self):
        self.tree.clear()
        self.group_panel.groups.clear()
        for i in reversed(range(self.group_panel.scroll_layout.count())): 
            self.group_panel.scroll_layout.itemAt(i).widget().setParent(None)
        if self.canvas:
            self.canvas.groups.clear()

    def update_layer_color(self, index, color):
        item = self.tree.topLevelItem(index)
        if item:
            item.setData(1, Qt.UserRole, color)

    def select_layer(self, index):
        item = self.tree.topLevelItem(index)
        if item:
            self.tree.setCurrentItem(item)

    def refresh(self):
        # Instead of clearing the group panel, update existing groups and layers
        logging.info("Refreshing GroupLayerManager without clearing groups")
        for i, button in enumerate(self.layer_panel.layer_buttons):
            layer_name = button.text()
            color = button.color
            # Update existing layers in groups
            self.group_panel.update_layer(i, layer_name, color)
        # Do not call self.group_panel.clear() here

    def get_group_data(self):
        group_data = {}
        logging.info("Starting to collect group data.")
        
        for group_name, group_info in self.group_panel.groups.items():
            logging.debug(f"Processing group '{group_name}'")
            
            group_data[group_name] = {
                "layers": [strand.layer_name for strand in group_info.get('strands', [])],
                "strands": [strand.layer_name for strand in group_info.get('strands', [])],
                "main_strands": list(group_info.get('main_strands', set())),
                "control_points": {}
            }
            
            # Add control points if they exist
            if self.canvas and group_name in self.canvas.groups:
                group_data[group_name]['control_points'] = self.canvas.groups[group_name].get('control_points', {})
            
            # Log the collected data for this group
            logging.debug(f"Collected data for group '{group_name}': {group_data[group_name]}")
        
        logging.info("Finished collecting group data.")
        logging.info(f"Collected group data: {group_data}")
        return group_data



    def apply_group_data(self, group_data):
        logging.info("Starting to apply group data.")
        logging.debug(f"Group data received: {group_data}")

        # Log the contents of strand_dict
        logging.debug("Contents of strand_dict before applying group data:")
        for layer_name, strand in self.strand_dict.items():
            logging.debug(f"Layer: {layer_name}, Strand ID: {id(strand)}")

        for group_name, group_info in group_data.items():
            logging.info(f"Deserializing group '{group_name}'")
            
            strands = []
            for layer_name in group_info["strands"]:
                logging.debug(f"Attempting to retrieve strand with layer_name '{layer_name}'")
                strand = self.strand_dict.get(layer_name)
                if strand:
                    strands.append(strand)
                    logging.info(f"Strand '{layer_name}' added to group '{group_name}'")
                    logging.debug(f"Strand ID: {id(strand)}, Attributes: {dir(strand)}")
                else:
                    logging.warning(f"Strand with layer_name '{layer_name}' not found in strand_dict")

            if strands:
                self.group_panel.create_group(group_name, strands)
                logging.info(f"Group '{group_name}' created in group panel with {len(strands)} strands")
                
                self.canvas.groups[group_name] = {
                    "layers": group_info["layers"],
                    "strands": strands,
                    "main_strands": group_info.get("main_strands", set()),
                    "control_points": group_info.get("control_points", {})
                }
                logging.info(f"Group '{group_name}' applied with {len(strands)} strands")
            else:
                logging.warning(f"Group '{group_name}' has no valid strands")

        # Log the contents of strand_dict after applying group data
        logging.debug("Contents of strand_dict after applying group data:")
        for layer_name, strand in self.strand_dict.items():
            logging.debug(f"Layer: {layer_name}, Strand ID: {id(strand)}")

        logging.info("Finished applying group data.")
    def move_group_strands(self, group_name, dx, dy):
        if group_name in self.groups:
            group_data = self.groups[group_name]
            updated_strands = []

            # Create QPointF for the movement delta
            delta = QPointF(dx, dy)
            
            for strand in group_data['strands']:
                # Store original control points before moving
                original_cp1 = QPointF(strand.control_point1)
                original_cp2 = QPointF(strand.control_point2)
                
                # Move all points including control points
                strand.start += delta
                strand.end += delta
                strand.control_point1 = original_cp1 + delta  # Apply delta to original control points
                strand.control_point2 = original_cp2 + delta  # Apply delta to original control points
                
                # Update the strand's shape
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
                
                # Store the updated control points in the group data
                if 'control_points' not in self.canvas.groups[group_name]:
                    self.canvas.groups[group_name]['control_points'] = {}
                
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': strand.control_point1,
                    'control_point2': strand.control_point2
                }
                
                updated_strands.append(strand)

            # Update the canvas with all modified strands
            if self.canvas:
                self.canvas.update()
    def update_strands(self, strands):
        """Update multiple strands at once."""
        for strand in strands:
            # Ensure we're updating all strand properties including control points
            existing_strand = self.find_strand_by_name(strand.layer_name)
            if existing_strand:
                existing_strand.start = QPointF(strand.start)
                existing_strand.end = QPointF(strand.end)
                existing_strand.control_point1 = QPointF(strand.control_point1)
                existing_strand.control_point2 = QPointF(strand.control_point2)
                existing_strand.update_shape()
                if hasattr(existing_strand, 'update_side_line'):
                    existing_strand.update_side_line()
        
        self.update()
    def start_group_move(self, group_name):
        if self.canvas:
            self.canvas.start_group_move(group_name, self.group_panel.groups[group_name]['layers'])

    def update_group(self, group_name):
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            main_layers = set([layer.split('_')[0] for layer in group_data['layers']])
            
            new_layers_data = []
            for main_layer in main_layers:
                sub_layers = self.get_sub_layers(main_layer)
                for sub_layer in sub_layers:
                    if sub_layer not in group_data['layers']:
                        layer_index = self.get_layer_index(sub_layer)
                        if layer_index < len(self.canvas.strands):
                            strand = self.canvas.strands[layer_index]
                            strand_data = {
                                'start': QPointF(strand.start),
                                'end': QPointF(strand.end)
                            }
                            new_layers_data.append((sub_layer, strand_data))
            
            for layer_name, strand_data in new_layers_data:
                self.group_panel.add_layer_to_group(layer_name, group_name, strand_data)
                
                # Update canvas groups
                if self.canvas and group_name in self.canvas.groups:
                    strand = self.canvas.find_strand_by_name(layer_name)
                    if strand:
                        self.canvas.groups[group_name]['strands'].append(strand)
                        self.canvas.groups[group_name]['layers'].append(layer_name)

    def on_group_operation(self, operation, group_name, layer_indices):
        logging.info(f"Group operation: {operation} on group {group_name} with layers {layer_indices}")
        if operation == "move":
            self.start_group_move(group_name)
        elif operation == "rotate":
            self.start_group_rotation(group_name)
        elif operation == "edit_angles":
            self.edit_strand_angles(group_name)
        elif operation == "delete":
            # Remove the group from canvas groups
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
                logging.info(f"Group '{group_name}' deleted from canvas.")
            else:
                logging.warning(f"Group '{group_name}' not found in canvas.")

    def start_group_rotation(self, group_name):
        if group_name in self.groups:
            if self.canvas and hasattr(self.canvas, 'group_layer_manager'):
                # Preserve group data before starting the rotation
                self.canvas.group_layer_manager.preserve_group_data(group_name)
                logging.info(f"Starting rotation for group '{group_name}'")

                # Proceed with rotation
                if self.canvas:
                    self.canvas.start_group_rotation(group_name)
                    dialog = GroupRotateDialog(group_name, self)
                    dialog.rotation_updated.connect(self.update_group_rotation)
                    dialog.rotation_finished.connect(self.finish_group_rotation)
                    dialog.exec_()
                else:
                    logging.error("Canvas not properly connected to GroupPanel")
            else:
                logging.error("Canvas or GroupLayerManager not properly connected")
        else:
            logging.warning(f"Attempted to rotate non-existent group: {group_name}")

    def update_group_rotation(self, group_name, angle):
        """
        Update the rotation of the given group to the specified absolute angle,
        based on the group's pre-rotation snapshot. This prevents repeatedly
        stacking rotations on already-rotated geometry.
        """
        logging.info(f"GroupPanel: Updating group rotation for '{group_name}' by angle={angle}")
        
        # Ensure we only rotate if this is the currently active group
        if group_name != self.active_group_name:
            logging.warning(f"update_group_rotation called for inactive group: {group_name}")
            return

        if self.canvas and hasattr(self, '_perform_immediate_group_rotation'):
            self._perform_immediate_group_rotation(group_name, angle)
        else:
            logging.error("Canvas not properly connected or '_perform_immediate_group_rotation' not found")

    def finish_group_rotation(self, group_name):
        if self.active_group_name == group_name:
            # Restore group data after rotation
            self.group_layer_manager.restore_group_data(group_name)
            logging.info(f"Restored group data for {group_name}")
            # Clean up pre-rotation state
            self.pre_rotation_state = {}
            self.active_group_name = None
            logging.info("Cleaned up pre-rotation state")

    def edit_strand_angles(self, group_name):
        if group_name in self.groups:
            # Fetch up-to-date group data
            group_data = self.groups[group_name]

            # Update the list of strands to include any new strands added to the group
            group_data['strands'] = self.get_group_strands(group_name)

            # Ensure that editable_layers is correctly populated
            editable_layers = [layer for layer in group_data['layers'] if self.is_layer_editable(layer)]

            dialog = StrandAngleEditDialog(
                group_name,
                {
                    'strands': group_data['strands'],
                    'layers': group_data['layers'],
                    'editable_layers': editable_layers
                },
                self.canvas,
                self
            )
            dialog.exec_()
    def get_group_strands(self, group_name):
        group_layers = self.groups[group_name]['layers']
        strands = []
        for strand in self.canvas.strands:
            if strand.layer_name in group_layers:
                strands.append(strand)
        return strands
    def is_layer_editable(self, layer_name):
        # Implement the logic to determine if a layer is editable
        return True  # Placeholder implementation

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator

class GroupRotateDialog(QDialog):
    rotation_updated = pyqtSignal(str, float)
    rotation_finished = pyqtSignal(str)

    def __init__(self, group_name, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None
        # Connect our rotation_updated signal to a local slot so we can rotate immediately.
        self.group_panel = parent  # Now we can access pre_rotation_state
        # Connect the signal to our unified slot
                # Define the language code, defaulting to 'en' if not available
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        self.original_angle = self.canvas.current_rotation_angle or 0.0
        self.rotation_updated.connect(self.on_angle_changed)

        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None
        self.setWindowTitle(f"{_['rotate_group_strands']} {group_name}")
        self.angle = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        # Angle slider
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel(_['angle']))
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(-180, 180)
        self.angle_slider.setValue(0)
        self.angle_slider.valueChanged.connect(self.update_angle_from_slider)
        angle_layout.addWidget(self.angle_slider)
        layout.addLayout(angle_layout)

        # Precise angle input
        precise_angle_layout = QHBoxLayout()
        precise_angle_layout.addWidget(QLabel(_['precise_angle']))
        self.angle_input = QLineEdit()
        self.angle_input.setValidator(QDoubleValidator(-180, 180, 2))
        self.angle_input.setText("0")
        self.angle_input.textChanged.connect(self.update_angle_from_input)
        precise_angle_layout.addWidget(self.angle_input)
        precise_angle_layout.addWidget(QLabel("°"))
        layout.addLayout(precise_angle_layout)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_ok_clicked)
        layout.addWidget(ok_button)

    def update_angle_from_slider(self):
        offset = self.angle_slider.value()
        self.angle_input.setText(str(offset))
        # Emit the absolute angle
        self.rotation_updated.emit(self.group_name, offset)


    def update_angle_from_input(self):
        try:
            offset = float(self.angle_input.text())
            self.angle_slider.setValue(int(offset))
            # Emit the absolute angle
            self.rotation_updated.emit(self.group_name, offset)
        except ValueError:
            pass
    def on_angle_changed(self, group_name, new_angle):
        logging.info(f"[GroupRotateDialog] on_angle_changed: new_angle={new_angle}")
        # Call GroupPanel's update_group_rotation (which should rotate absolutely)
        if self.group_panel:
            self.group_panel.update_group_rotation(group_name, new_angle)
        else:
            logging.warning("GroupRotateDialog has no group_panel to update rotation.")


    def on_rotation_updated(self, group_name, angle):
        """
        A slot that's called whenever rotation_updated is emitted.
        Here we call the actual rotation logic (rotate_group_strands).
        """
        self.angle = angle
        self.rotate_group_strands()
    # Update the group's strands rotation
    def rotate_group_strands(self):
        """
        Similar to your existing rotation logic:
        - retrieves pre_rotation_state from self.group_panel
        - computes the group's center
        - rotates every strand's start/end and (if masked) its deletion rect corners
          around that center by `self.angle`.
        """
        if not self.canvas or not hasattr(self.canvas, 'groups') or self.group_name not in self.canvas.groups:
            logging.error("Canvas or group data not found, cannot proceed with rotation.")
            return

        group_data = self.canvas.groups[self.group_name]

        # 1) Calculate rotation center. 
        rotation_center = self.calculate_group_center(group_data['strands'])

        # 2) Convert the user-typed angle to radians
        angle_radians = math.radians(self.angle)

        # 3) Retrieve the snapshot of original geometry
        if hasattr(self.group_panel, 'pre_rotation_state'):
            pre_state = self.group_panel.pre_rotation_state
        else:
            pre_state = {}

        # 4) Rotate each strand from original positions
        for strand in group_data['strands']:
            layer_name = strand.layer_name
            if layer_name in pre_state:
                original_positions = pre_state[layer_name]

                # Rotate the main geometry (start/end)
                strand.start = self.rotate_point(original_positions['start'], rotation_center, angle_radians)
                strand.end   = self.rotate_point(original_positions['end'],   rotation_center, angle_radians)
                if 'control_point1' in original_positions:
                    strand.control_point1 = self.rotate_point(original_positions['control_point1'], rotation_center, angle_radians)
                if 'control_point2' in original_positions:
                    strand.control_point2 = self.rotate_point(original_positions['control_point2'], rotation_center, angle_radians)
                # If MaskedStrand, also rotate deletion rectangle corners
                if isinstance(strand, MaskedStrand) and 'deletion_rectangles' in original_positions:
                    for rect_idx, corners in enumerate(original_positions['deletion_rectangles']):
                        tl = self.rotate_point(corners['top_left'],     rotation_center, angle_radians)
                        tr = self.rotate_point(corners['top_right'],    rotation_center, angle_radians)
                        bl = self.rotate_point(corners['bottom_left'],  rotation_center, angle_radians)
                        br = self.rotate_point(corners['bottom_right'], rotation_center, angle_radians)

                        # Store them back as float tuples
                        strand.deletion_rectangles[rect_idx]['top_left']     = (tl.x(), tl.y())
                        strand.deletion_rectangles[rect_idx]['top_right']    = (tr.x(), tr.y())
                        strand.deletion_rectangles[rect_idx]['bottom_left']  = (bl.x(), bl.y())
                        strand.deletion_rectangles[rect_idx]['bottom_right'] = (br.x(), br.y())

                # Update the strand's shape
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()

        # 5) Redraw the canvas
        self.canvas.update()

    def rotate_point(self, point: QPointF, pivot: QPointF, angle_radians: float) -> QPointF:
        dx = point.x() - pivot.x()
        dy = point.y() - pivot.y()
        cos_a = math.cos(angle_radians)
        sin_a = math.sin(angle_radians)
        rotated_x = pivot.x() + dx * cos_a - dy * sin_a
        rotated_y = pivot.y() + dx * sin_a + dy * cos_a
        return QPointF(rotated_x, rotated_y)
    def calculate_group_center(self, strands):
        """
        Example: compute the average of all start/end points & rectangle corners
        or use your existing approach to find the center.
        """
        center_sum = QPointF(0, 0)
        total_points = 0

        if hasattr(self.group_panel, 'pre_rotation_state'):
            pre_state = self.group_panel.pre_rotation_state
        else:
            pre_state = {}

        for strand in strands:
            st = pre_state.get(strand.layer_name)
            if not st:
                continue

            # start, end
            center_sum += st['start']
            center_sum += st['end']
            total_points += 2

            # If masked, add rectangle corners
            if isinstance(strand, MaskedStrand) and 'deletion_rectangles' in st:
                for corners in st['deletion_rectangles']:
                    center_sum += corners['top_left']
                    center_sum += corners['top_right']
                    center_sum += corners['bottom_left']
                    center_sum += corners['bottom_right']
                    total_points += 4

        if total_points > 0:
            return QPointF(center_sum.x() / total_points, center_sum.y() / total_points)
        else:
            return QPointF(0, 0)  # fallback if nothing found
    def on_ok_clicked(self):
        try:
            final_angle = float(self.angle_input.text())
            self.rotation_updated.emit(self.group_name, final_angle)
        except ValueError:
            pass  # Ignore invalid input
        self.rotation_finished.emit(self.group_name)
        self.accept()
        
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from math import atan2, degrees

from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from math import atan2, degrees, radians, cos, sin
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from math import atan2, degrees, radians, cos, sin

class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator())
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, float(value), Qt.EditRole)
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDesktopWidget, QWidget, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime, QTimer
from math import atan2, degrees, cos, sin, radians
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime, QTimer
from PyQt5.QtGui import QDoubleValidator, QColor, QPalette, QGuiApplication
from math import atan2, degrees, cos, sin, radians
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget, QLabel, QDesktopWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime, QTimer
from PyQt5.QtGui import QDoubleValidator, QColor, QBrush
from math import atan2, degrees, radians, cos, sin
import logging
import math

class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator())
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, float(value), Qt.EditRole)

class StrandAngleEditDialog(QDialog):
    angle_changed = pyqtSignal(str, float)

    def __init__(self, group_name, group_data, canvas, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.group_name = group_name
        self.canvas = canvas
        self.linked_strands = {}

        # Set the language code for translations
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        self.setWindowTitle(f"{_['edit_strand_angles']} {group_name}")

        self.updating = False
        self.initializing = True

        self.group_data = {
            'strands': [self.ensure_strand_object(s) for s in group_data['strands']],
            'layers': group_data['layers'],
            'editable_layers': group_data['editable_layers']
        }

        self.setup_ui()
        self.adjust_dialog_size()

        # Timers for handling continuous adjustment
        self.adjustment_timer = QTimer(self)
        self.adjustment_timer.setInterval(10)  # 10 milliseconds (0.01 seconds)
        self.initial_delay_timer = QTimer(self)
        self.initial_delay_timer.setSingleShot(True)
        self.initial_delay_timer.setInterval(500)  # 0.5 seconds
        self.current_adjustment = None

        # Define delta values for each button type
        self.delta_plus = 1
        self.delta_minus = -1
        self.delta_plus_plus = 5
        self.delta_minus_minus = -5

        # Continuous adjustment delta values
        self.delta_continuous_plus = 0.025
        self.delta_continuous_minus = -0.025
        self.delta_fast_continuous_plus = 0.4
        self.delta_fast_continuous_minus = -0.4

        self.current_button = None
        self.last_press_time = None
        self.x_angle = 0

        # Apply the current theme after setting up the UI
        self.apply_theme()

        # Connect to the theme_changed signal if available
        if self.canvas and hasattr(self.canvas, 'theme_changed'):
            self.canvas.theme_changed.connect(self.on_theme_changed)

        self.initializing = False

    def apply_theme(self):
        """Apply the current theme to the dialog."""
        # Check if the canvas has the 'is_dark_mode' attribute
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)

        if is_dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    def ensure_strand_object(self, strand):
        if isinstance(strand, dict):
            return self.canvas.find_strand_by_name(strand['layer_name'])
        return strand

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Wrap the main layout in a QWidget to apply stylesheet
        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        # Table widget
        self.table = QTableWidget()
        self.setup_table()
        main_layout.addWidget(self.table)

        self.populate_table()

        bottom_layout = self.setup_bottom_layout()
        main_layout.addLayout(bottom_layout)


        self.setLayout(main_layout)

    def setup_table(self):
        _ = translations[self.language_code]
        headers = [
            _['layer'],
            _['angle'],
            _['adjust_1_degree'],
            _['fast_adjust'],
            _['end_x'],
            _['end_y'],
            _['x'],
            _['x_plus_180'],
            _['attachable']
        ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setItemDelegate(FloatDelegate())
        self.table.itemChanged.connect(self.on_item_changed)

    def populate_table(self):
        self.table.setRowCount(len(self.group_data['strands']))
        self.initializing = True

        is_dark_mode = False
        if hasattr(self.canvas, 'is_dark_mode'):
            is_dark_mode = self.canvas.is_dark_mode

        for row, strand in enumerate(self.group_data['strands']):
            is_main_strand = strand.layer_name.endswith("_1")
            is_masked = isinstance(strand, MaskedStrand)
            is_attachable = strand.is_attachable()
            is_editable = not is_main_strand and not is_masked and is_attachable

            # Layer Name
            layer_name_item = QTableWidgetItem(str(strand.layer_name))
            self.set_item_style(layer_name_item, is_editable)
            self.table.setItem(row, 0, layer_name_item)

            # Angle
            angle = self.calculate_angle(strand)
            angle_item = QTableWidgetItem(f"{angle:.2f}")
            self.set_item_style(angle_item, is_editable)
            self.table.setItem(row, 1, angle_item)

            # Angle adjustment buttons (+/-1 degree)
            angle_buttons = self.create_angle_buttons(row)
            self.table.setCellWidget(row, 2, angle_buttons)

            # Fast angle adjustment buttons (+/-5 degrees)
            fast_angle_buttons = self.create_fast_angle_buttons(row)
            self.table.setCellWidget(row, 3, fast_angle_buttons)

            # End X coordinate
            end_x_item = QTableWidgetItem(f"{strand.end.x():.2f}")
            self.set_item_style(end_x_item, is_editable)
            self.table.setItem(row, 4, end_x_item)

            # End Y coordinate
            end_y_item = QTableWidgetItem(f"{strand.end.y():.2f}")
            self.set_item_style(end_y_item, is_editable)
            self.table.setItem(row, 5, end_y_item)

            # Checkboxes for angle syncing
            x_checkbox = QCheckBox("x")
            x_plus_180_checkbox = QCheckBox("180+x")

            # Set fixed sizes for the checkboxes
            x_checkbox.setFixedSize(60, 24)
            x_plus_180_checkbox.setFixedSize(60, 24)

            # Create container widgets for checkboxes with zero margins
            x_widget = QWidget()
            x_layout = QHBoxLayout(x_widget)
            x_layout.setContentsMargins(0, 0, 0, 0)
            x_layout.setAlignment(Qt.AlignCenter)
            x_layout.addWidget(x_checkbox)

            x_plus_180_widget = QWidget()
            x_plus_180_layout = QHBoxLayout(x_plus_180_widget)
            x_plus_180_layout.setContentsMargins(0, 0, 0, 0)
            x_plus_180_layout.setAlignment(Qt.AlignCenter)
            x_plus_180_layout.addWidget(x_plus_180_checkbox)

            self.table.setCellWidget(row, 6, x_widget)
            self.table.setCellWidget(row, 7, x_plus_180_widget)

            # 'Attachable' indicator
            if is_main_strand:
                attachable_text = 'X'
            else:
                attachable_text = '' if is_attachable else 'No'

            attachable_item = QTableWidgetItem(attachable_text)
            attachable_item.setTextAlignment(Qt.AlignCenter)
            attachable_item.setFlags(attachable_item.flags() & ~Qt.ItemIsEditable)
            self.set_item_style(attachable_item, is_editable)
            self.table.setItem(row, 8, attachable_item)

            # Connect checkbox state changes
            x_checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, 6, state))
            x_plus_180_checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, 7, state))

            # Disable interaction for non-editable strands
            if not is_editable:
                for col in [0, 1, 4, 5, 8]:
                    item = self.table.item(row, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                for col in [2, 3, 6, 7]:
                    widget = self.table.cellWidget(row, col)
                    if widget:
                        widget.setEnabled(False)

        self.initializing = False

    def set_item_style(self, item, is_editable):
        is_dark_mode = self.canvas.is_dark_mode if hasattr(self.canvas, 'is_dark_mode') else False
        if is_editable:
            if is_dark_mode:
                item.setForeground(QBrush(QColor(255, 255, 255)))
            else:
                item.setForeground(QBrush(QColor(0, 0, 0)))
        else:
            item.setForeground(QBrush(QColor(150, 150, 150)))

    def setup_bottom_layout(self):
        _ = translations[self.language_code]

        # X Angle widget
        x_angle_widget = QWidget()
        x_angle_widget.setObjectName("xAngleWidget")
        x_angle_layout = QHBoxLayout()
        x_angle_widget.setLayout(x_angle_layout)
        x_angle_layout.setContentsMargins(0, 0, 0, 0)
        x_angle_layout.setSpacing(5)

        x_angle_label = QLabel(_['X_angle'])
        self.x_angle_input = QLineEdit()
        self.x_angle_input.setFixedWidth(60)  # Reduced width
        self.x_angle_input.setText("0.00")
        self.x_angle_input.textChanged.connect(self.update_x_angle)
        x_angle_layout.addWidget(x_angle_label)
        x_angle_layout.addWidget(self.x_angle_input)
        x_angle_layout.addStretch()

        # Buttons
        button_layout_widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout_widget.setLayout(button_layout)
        button_layout.setSpacing(5)  # Reduced spacing
        button_layout.setAlignment(Qt.AlignRight)

        self.minus_minus_button = QPushButton("--")
        self.minus_button = QPushButton("-")
        self.plus_button = QPushButton("+")
        self.plus_plus_button = QPushButton("++")
        ok_btn = QPushButton("OK")

        for btn in [self.minus_minus_button, self.minus_button, self.plus_button, self.plus_plus_button, ok_btn]:
            btn.setFixedSize(30, 25)  # Reduced width
            # Styles will be applied via stylesheet

        # Connect button signals
        self.minus_minus_button.pressed.connect(lambda: self.handle_button_press('minus_minus', self.delta_minus_minus, self.start_continuous_adjustment_minus_minus))
        self.minus_minus_button.released.connect(self.stop_adjustment)
        self.minus_button.pressed.connect(lambda: self.handle_button_press('minus', self.delta_minus, self.start_continuous_adjustment_minus))
        self.minus_button.released.connect(self.stop_adjustment)
        self.plus_button.pressed.connect(lambda: self.handle_button_press('plus', self.delta_plus, self.start_continuous_adjustment_plus))
        self.plus_button.released.connect(self.stop_adjustment)
        self.plus_plus_button.pressed.connect(lambda: self.handle_button_press('plus_plus', self.delta_plus_plus, self.start_continuous_adjustment_plus_plus))
        self.plus_plus_button.released.connect(self.stop_adjustment)

        ok_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.minus_minus_button)
        button_layout.addWidget(self.minus_button)
        button_layout.addWidget(self.plus_button)
        button_layout.addWidget(self.plus_plus_button)
        button_layout.addWidget(ok_btn)

        # Combine x_angle_widget and buttons into one layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(x_angle_widget)
        bottom_layout.addStretch()
        bottom_layout.addWidget(button_layout_widget)

        return bottom_layout
    def handle_button_press(self, button_type, initial_delta, continuous_function):
        current_time = QDateTime.currentMSecsSinceEpoch()

        # Always stop any ongoing adjustments
        self.stop_adjustment()

        # Set the new current button and last press time
        self.current_button = button_type
        self.last_press_time = current_time

        # Perform initial adjustment
        self.adjust_x_angle(initial_delta)

        # Set up continuous adjustment after delay
        self.initial_delay_timer.timeout.connect(continuous_function)
        self.initial_delay_timer.start()
    def stop_adjustment(self):
        self.initial_delay_timer.stop()
        self.adjustment_timer.stop()
        self.current_adjustment = None
        self.current_button = None
        self.last_press_time = None

        # Disconnect timers to avoid multiple connections
        try:
            self.initial_delay_timer.timeout.disconnect()
        except TypeError:
            pass  # Not connected

        try:
            self.adjustment_timer.timeout.disconnect()
        except TypeError:
            pass  # Not connected
    def start_continuous_adjustment_plus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_continuous_plus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_minus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_continuous_minus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_plus_plus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_fast_continuous_plus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_minus_minus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_fast_continuous_minus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def perform_continuous_adjustment(self):
        if self.current_adjustment is not None:
            self.adjust_x_angle(self.current_adjustment)

    def adjust_dialog_size(self):
        # Calculate the required width and height
        width = self.table.verticalHeader().width() + 4  # Left and right margins
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i)

        height = self.table.horizontalHeader().height() + 4  # Top and bottom margins
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)

        # Add some padding
        width += 500
        height += 300  # Extra space for the OK button and padding

        # Set the size of the dialog
        self.resize(width, height)

        # Center the dialog on the screen
        screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
        center_point = QDesktopWidget().screenGeometry(screen).center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())


    def apply_dark_theme(self):
        """Apply dark theme styles to the dialog."""
        dark_stylesheet = """
            QDialog, QWidget {
                background-color: #1C1C1C;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #2B2B2B;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2B2B2B;
                color: #FFFFFF;
                border: 1px solid #777777;
                border-radius: 5px;
                min-width: 50px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
            QTableWidget {
                background-color: #1C1C1C;
                color: #FFFFFF;
                gridline-color: #555555;
            }
            QTableWidget::item {
                background-color: #1C1C1C;
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #3C3C3C;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #2B2B2B;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #555555;
            }
            QTableCornerButton::section {
                background-color: #2B2B2B;
                border: 1px solid #555555;
            }
            QCheckBox {
                color: #FFFFFF;
                background-color: transparent;
                padding: 2px;
            }
            QCheckBox::indicator {
                border: 1px solid #777777;
                width: 16px;
                height: 16px;
                border-radius: 3px;
                background: #2B2B2B;
            }
            QCheckBox::indicator:checked {
                background-color: #555555;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #1C1C1C;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #2B2B2B;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
            QWidget#xAngleWidget {
                background-color: #1C1C1C;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def apply_light_theme(self):
        """Apply light theme styles to the dialog."""
        light_stylesheet = """
            QDialog, QWidget {
                background-color: #FFFFFF;
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #BBBBBB;
                border-radius: 5px;
                min-width: 50px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QTableWidget {
                background-color: #FFFFFF;
                color: #000000;
                gridline-color: #CCCCCC;
            }
            QTableWidget::item {
                background-color: #FFFFFF;
                color: #000000;
            }
            QTableWidget::item:selected {
                background-color: #E0E0E0;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #000000;
                padding: 4px;
                border: 1px solid #CCCCCC;
            }
            QTableCornerButton::section {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
            }
            QCheckBox {
                color: #000000;
                background-color: transparent;
                padding: 2px;
            }
            QCheckBox::indicator {
                border: 1px solid #CCCCCC;
                width: 16px;
                height: 16px;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #BBBBBB;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #FFFFFF;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #CCCCCC;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
            QWidget#xAngleWidget {
                background-color: #FFFFFF;
            }
        """
        self.setStyleSheet(light_stylesheet)

    def update_table_styles(self):
        """Update the styles of table items based on the current theme."""
        is_dark_mode = self.canvas.is_dark_mode if hasattr(self.canvas, 'is_dark_mode') else False
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    if is_dark_mode:
                        item.setForeground(QBrush(QColor(255, 255, 255)))
                        item.setBackground(QBrush(QColor(28, 28, 28)))
                    else:
                        item.setForeground(QBrush(QColor(0, 0, 0)))
                        item.setBackground(QBrush(QColor(255, 255, 255)))

    def on_theme_changed(self, theme_name):
        """Handle theme changes."""
        self.apply_theme()

    def on_item_changed(self, item):
        if self.updating:
            return

        self.updating = True
        try:
            if item.column() == 1:  # Angle column
                row = item.row()
                strand = self.group_data['strands'][row]
                try:
                    new_angle = float(item.text())
                    self.update_strand_angle(strand, new_angle, update_linked=True)
                except ValueError:
                    self.update_table_row(row)
        finally:
            self.updating = False

    def update_table_row(self, row):
        strand = self.group_data['strands'][row]
        angle = self.calculate_angle(strand)
        end_x = strand.end.x()
        end_y = strand.end.y()

        # Update angle
        angle_item = self.table.item(row, 1)
        if angle_item is None:
            angle_item = QTableWidgetItem()
            self.table.setItem(row, 1, angle_item)
        angle_item.setText(f"{angle:.2f}")

        # Update end X
        end_x_item = self.table.item(row, 4)
        if end_x_item is None:
            end_x_item = QTableWidgetItem()
            self.table.setItem(row, 4, end_x_item)
        end_x_item.setText(f"{end_x:.2f}")

        # Update end Y
        end_y_item = self.table.item(row, 5)
        if end_y_item is None:
            end_y_item = QTableWidgetItem()
            self.table.setItem(row, 5, end_y_item)
        end_y_item.setText(f"{end_y:.2f}")


    def update_strand_angle(self, strand, new_angle, update_linked=True):
        # Skip masked strands
        if isinstance(strand, MaskedStrand):
            logging.info(f"Skipping angle update for masked strand {strand.layer_name}")
            return

        if not hasattr(strand, 'start') or not hasattr(strand, 'end'):
            return

        # Store original control points if not already stored
        if not hasattr(strand, 'pre_rotation_points'):
            strand.pre_rotation_points = {
                'start': QPointF(strand.start),
                'end': QPointF(strand.end),
                'control_point1': QPointF(strand.control_point1) if strand.control_point1 is not None else QPointF(strand.start),
                'control_point2': QPointF(strand.control_point2) if strand.control_point2 is not None else QPointF(strand.end),
                'last_angle': self.calculate_angle(strand)  # Store current angle
            }

        # Calculate the angle difference
        current_angle = self.calculate_angle(strand)
        angle_diff = new_angle - current_angle

        # Calculate the center of rotation (strand's start point)
        center = strand.start

        # Helper function to rotate a point around the center
        def rotate_point(point, angle_rad):
            if point is None:
                return None
            dx = point.x() - center.x()
            dy = point.y() - center.y()
            cos_angle = cos(angle_rad)
            sin_angle = sin(angle_rad)
            new_x = center.x() + dx * cos_angle - dy * sin_angle
            new_y = center.y() + dx * sin_angle + dy * cos_angle
            return QPointF(new_x, new_y)

        # Convert angle difference to radians
        angle_rad = radians(angle_diff)

        # Rotate end point and control points
        strand.end = rotate_point(strand.end, angle_rad)
        strand.control_point1 = rotate_point(strand.control_point1, angle_rad) if strand.control_point1 is not None else None
        strand.control_point2 = rotate_point(strand.control_point2, angle_rad) if strand.control_point2 is not None else None

        # Update the strand's shape
        strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()

        # Store the new angle as the last angle
        if hasattr(strand, 'pre_rotation_points'):
            strand.pre_rotation_points['last_angle'] = new_angle

        # Update x_angle if this is the main strand
        if strand.layer_name.endswith('_1'):
            self.x_angle = new_angle
            if hasattr(self, 'x_angle_input'):
                self.x_angle_input.setText(f"{new_angle:.2f}")

        # ---------------------------------
        # ADDED CODE: fix for attached strands
        # ---------------------------------
        if update_linked and self.canvas:
            attached_strands = self.canvas.find_attached_strands(strand)
            # If we saved the old coords, use them:
            old_coords = getattr(strand, 'pre_rotation_points', None)
            if not old_coords:
                # If there's no old geometry snapshot, nothing to do
                self.canvas.update()
                return

            # Identify old_end vs. new_end
            old_end = old_coords.get('end', strand.end)
            new_end = strand.end

            for attached_strand in attached_strands:
                # If attached_strand.start was old_end, we move it by (new_end - old_end)
                if attached_strand.start == old_end:
                    offset = new_end - old_end
                    attached_strand.start += offset
                    # If it has control_point1, also shift that
                    if attached_strand.control_point1 is not None:
                        attached_strand.control_point1 += offset
                    attached_strand.update_shape()
                    if hasattr(attached_strand, 'update_side_line'):
                        attached_strand.update_side_line()

                # Or if attached_strand.end was old_end, shift that
                elif attached_strand.end == old_end:
                    offset = new_end - old_end
                    attached_strand.end += offset
                    if attached_strand.control_point2 is not None:
                        attached_strand.control_point2 += offset
                    attached_strand.update_shape()
                    if hasattr(attached_strand, 'update_side_line'):
                        attached_strand.update_side_line()

            # Finally, update the canvas
            self.canvas.update()

    def update_linked_strands(self, current_strand=None):
        for row, strand in enumerate(self.group_data['strands']):
            if strand == current_strand:
                continue  # Skip the current strand to avoid recursive updates

            x_widget = self.table.cellWidget(row, 6)
            x_plus_180_widget = self.table.cellWidget(row, 7)

            # Check if widgets are None
            if x_widget is None and x_plus_180_widget is None:
                continue  # Skip to the next strand

            # Extract the QCheckBox from the QWidget
            x_checkbox = x_widget.findChild(QCheckBox) if x_widget else None
            x_plus_180_checkbox = x_plus_180_widget.findChild(QCheckBox) if x_plus_180_widget else None

            if x_checkbox and x_checkbox.isChecked():
                self.update_strand_angle(strand, self.x_angle, update_linked=False)
            elif x_plus_180_checkbox and x_plus_180_checkbox.isChecked():
                # Normalize the angle to be within -180 to 180 degrees
                opposite_angle = (self.x_angle + 180) % 360
                if opposite_angle > 180:
                    opposite_angle -= 360
                self.update_strand_angle(strand, opposite_angle, update_linked=False)

    def create_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        minus_button = QPushButton("-")
        plus_button = QPushButton("+")
        # Remove fixed size settings
        # minus_button.setFixedSize(14, 24)
        # plus_button.setFixedSize(14, 24)
        # Set size policy to minimum size
        minus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        plus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        # Adjust button styles to reduce padding and margins
        minus_button.setStyleSheet("padding: 0px; margin: 0px;")
        plus_button.setStyleSheet("padding: 0px; margin: 0px;")

        plus_button.clicked.connect(lambda: self.on_plus_clicked(row))
        minus_button.clicked.connect(lambda: self.on_minus_clicked(row))

        layout.addWidget(minus_button)
        layout.addWidget(plus_button)
        layout.setAlignment(Qt.AlignCenter)

        return widget
        
    def create_fast_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        minus_minus_button = QPushButton("--")
        plus_plus_button = QPushButton("++")
        # Remove fixed size settings
        # minus_minus_button.setFixedSize(14, 24)
        # plus_plus_button.setFixedSize(14, 24)
        # Set size policy to minimum size
        minus_minus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        plus_plus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        # Adjust button styles to reduce padding and margins
        minus_minus_button.setStyleSheet("padding: 0px; margin: 0px;")
        plus_plus_button.setStyleSheet("padding: 0px; margin: 0px;")

        plus_plus_button.clicked.connect(lambda: self.on_plus_plus_clicked(row))
        minus_minus_button.clicked.connect(lambda: self.on_minus_minus_clicked(row))

        layout.addWidget(minus_minus_button)
        layout.addWidget(plus_plus_button)
        layout.setAlignment(Qt.AlignCenter)

        return widget

    def on_plus_clicked(self, row):
        self.adjust_angle(row, self.delta_plus)

    def on_minus_clicked(self, row):
        self.adjust_angle(row, self.delta_minus)

    def on_plus_plus_clicked(self, row):
        self.adjust_angle(row, self.delta_plus_plus)

    def on_minus_minus_clicked(self, row):
        self.adjust_angle(row, self.delta_minus_minus)

    def adjust_angle(self, row, delta):
        strand = self.group_data['strands'][row]
        current_angle_item = self.table.item(row, 1)
        if current_angle_item:
            try:
                current_angle = float(current_angle_item.text())
            except ValueError:
                current_angle = self.calculate_angle(strand)
            new_angle = current_angle + delta
            current_angle_item.setText(f"{new_angle:.2f}")
            self.update_strand_angle(strand, new_angle)

    def on_checkbox_changed(self, row, col, state):
        strand = self.group_data['strands'][row]

        if col == 6:  # x checkbox
            if state == Qt.Checked:
                angle = self.x_angle  # Use x_angle

                # Uncheck the x_plus_180 checkbox
                x_plus_180_widget = self.table.cellWidget(row, 7)
                if x_plus_180_widget:
                    x_plus_180_checkbox = x_plus_180_widget.findChild(QCheckBox)
                    if x_plus_180_checkbox:
                        x_plus_180_checkbox.setChecked(False)
            else:
                angle = self.calculate_angle(strand)

            self.update_strand_angle(strand, angle)
            angle_item = self.table.item(row, 1)
            if angle_item:
                angle_item.setText(f"{angle:.2f}")

        elif col == 7:  # x+180 checkbox
            if state == Qt.Checked:
                angle = (self.x_angle + 180) % 360  # Use x_angle + 180
                if angle > 180:
                    angle -= 360

                # Uncheck the x checkbox
                x_widget = self.table.cellWidget(row, 6)
                if x_widget:
                    x_checkbox = x_widget.findChild(QCheckBox)
                    if x_checkbox:
                        x_checkbox.setChecked(False)
            else:
                angle = self.calculate_angle(strand)

            self.update_strand_angle(strand, angle)
            angle_item = self.table.item(row, 1)
            if angle_item:
                angle_item.setText(f"{angle:.2f}")

    def update_x_angle(self):
        try:
            self.x_angle = float(self.x_angle_input.text())
            self.update_linked_strands()
        except ValueError:
            self.x_angle = 0.0

    def adjust_x_angle(self, delta):
        try:
            current_x_angle = float(self.x_angle_input.text())
        except ValueError:
            current_x_angle = 0.0
        new_x_angle = current_x_angle + delta
        self.x_angle_input.setText(f"{new_x_angle:.2f}")
        self.update_x_angle()
        self.apply_x_angle_to_selected()

    def apply_x_angle_to_selected(self):
        for row in range(self.table.rowCount()):
            x_widget = self.table.cellWidget(row, 6)
            x_plus_180_widget = self.table.cellWidget(row, 7)

            # Extract the QCheckBox from the QWidget
            x_checkbox = x_widget.findChild(QCheckBox) if x_widget else None
            x_plus_180_checkbox = x_plus_180_widget.findChild(QCheckBox) if x_plus_180_widget else None

            # Check if checkboxes are checked
            if x_checkbox and x_checkbox.isChecked():
                self.on_checkbox_changed(row, 6, Qt.Checked)
            elif x_plus_180_checkbox and x_plus_180_checkbox.isChecked():
                self.on_checkbox_changed(row, 7, Qt.Checked)

    def calculate_angle(self, strand):
            dx = strand.end.x() - strand.start.x()
            dy = strand.end.y() - strand.start.y()

            angle = degrees(atan2(dy, dx))

            # Normalize the angle to be within -180 to 180 degrees
            if angle > 180:
                angle -= 360
            elif angle <= -180:
                angle += 360

            return angle

    def accept(self):
        # Perform any final actions before closing the dialog
        super().accept()