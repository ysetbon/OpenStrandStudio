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
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMenu, QSizePolicy
)
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
       # Group button
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
        self.update_group_button_style()

        self.update_translations()
    def update_group_button_style(self):
        """Update the group button's stylesheet based on the current palette."""
        # Remove the background-color to allow the system theme to take over
        self.group_button.setStyleSheet(f"""
            QPushButton {{
                border: none;
                text-align: left;
                padding: 5px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 20%);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 40%);
            }}
        """)

    def on_theme_changed(self):
        """Handle dynamic theme changes by updating styles."""
        self.apply_theme()

    def show_context_menu(self, position):
        _ = translations[self.language_code]
        context_menu = QMenu(self)
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


        # Remove the hardcoded background color
        # self.setStyleSheet("background-color: white;")

        # Use the application's palette to set the background role
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), palette.window().color())
        self.setPalette(palette)

        self.layout = QVBoxLayout(self)
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






    def add_layer_to_group(self, layer_name, group_name, strand):
        if group_name not in self.groups:
            logging.warning(f"Group {group_name} does not exist")
            return

        group = self.groups[group_name]
        if layer_name not in group['layers']:
            group['layers'].append(layer_name)
            group['strands'].append(strand)
            group['widget'].add_layer(
                layer_name,
                color=strand.color,
                is_masked=isinstance(strand, MaskedStrand)
            )
            logging.info(f"Successfully added layer {layer_name} to group {group_name}")

            # Update the canvas's group data
            if self.canvas:
                self.canvas.update_group_data(group_name, group)
        else:
            logging.info(f"Layer {layer_name} already in group {group_name}")
    def update_group_display(self, group_name):
        logging.info(f"Updating display for group: {group_name}")
        if group_name in self.groups:
            self.groups[group_name]['widget'].update_group_display()
        else:
            logging.error(f"Attempted to update non-existent group: {group_name}")

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
            dialog = GroupMoveDialog(group_name, self)
            dialog.move_updated.connect(self.update_group_move)
            dialog.move_finished.connect(self.finish_group_move)
            dialog.exec_()
        else:
            logging.warning(f"Attempted to move non-existent group: {group_name}")

    def update_group_move(self, group_name, total_dx, total_dy):
        logging.info(f"GroupPanel: Updating group move for '{group_name}' by total_dx={total_dx}, total_dy={total_dy}")
        if self.canvas:
            self.canvas.move_group(group_name, total_dx, total_dy)
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
        group_widget = CollapsibleGroupWidget(group_name, self)  # `self` is the GroupPanel instance
        self.scroll_layout.addWidget(group_widget)
        self.groups[group_name] = {
            'widget': group_widget,
            'layers': [],
            'strands': []
        }
        for strand in strands:
            layer_name = strand.layer_name
            self.add_layer_to_group(layer_name, group_name, strand)


    def start_group_rotation(self, group_name):
        if group_name in self.groups:
            # Set the active group name
            self.active_group_name = group_name
            if self.canvas:
                # Update the group's strands before rotation
                self.update_group_strands(group_name)
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

    def update_group_rotation(self, group_name, angle):
        logging.info(f"GroupPanel: Updating group rotation for '{group_name}' by angle={angle}")
        if group_name == self.active_group_name:
            if self.canvas:
                self.canvas.rotate_group(group_name, angle)
            else:
                logging.error("Canvas not properly connected to GroupPanel")
        else:
            logging.warning(f"Attempted to rotate non-existent or inactive group: {group_name}")


    def finish_group_rotation(self, group_name):
        logging.info(f"GroupPanel: Finishing group rotation for '{group_name}'")
        if self.canvas:
            self.canvas.finish_group_rotation(group_name)
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
            # Ensure that editable_layers is correctly populated
            editable_layers = [layer for layer in self.groups[group_name]['layers'] 
                               if self.is_layer_editable(layer)]
            
            dialog = StrandAngleEditDialog(
                group_name, 
                {
                    'strands': self.groups[group_name]['strands'],
                    'layers': self.groups[group_name]['layers'],
                    'editable_layers': editable_layers  # Pass the correct editable_layers list
                }, 
                self.canvas, 
                self
            )
            dialog.exec_()

    def is_layer_editable(self, layer_name):
        # This method should check if the layer has a green rectangle
        layer_button = next((button for button in self.layer_panel.layer_buttons if button.text() == layer_name), None)
        return layer_button is not None and layer_button.isEnabled()

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class GroupMoveDialog(QDialog):
    move_updated = pyqtSignal(str, int, int)
    move_finished = pyqtSignal(str)

    def __init__(self, group_name, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None

        # Define the language code, defaulting to 'en' if not available
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        self.setWindowTitle(f"{_['move_group_strands']} {group_name}")

        self.total_dx = 0
        self.total_dy = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        # dx layout
        dx_layout = QHBoxLayout()
        dx_layout.addWidget(QLabel("dx:"))

        self.dx_slider = QSlider(Qt.Horizontal)
        self.dx_slider.setRange(-600, 600)
        self.dx_slider.setValue(0)
        self.dx_slider.valueChanged.connect(self.update_dx_from_slider)
        dx_layout.addWidget(self.dx_slider)

        self.dx_value = QLabel("0")
        dx_layout.addWidget(self.dx_value)

        # Add QLineEdit for exact dx input
        self.dx_input = QLineEdit()
        self.dx_input.setValidator(QIntValidator(-600, 600))
        self.dx_input.setFixedWidth(60)
        self.dx_input.textChanged.connect(self.update_dx_from_input)  # Connect to update method
        dx_layout.addWidget(self.dx_input)

        layout.addLayout(dx_layout)

        # dy layout
        dy_layout = QHBoxLayout()
        dy_layout.addWidget(QLabel("dy:"))

        self.dy_slider = QSlider(Qt.Horizontal)
        self.dy_slider.setRange(-600, 600)
        self.dy_slider.setValue(0)
        self.dy_slider.valueChanged.connect(self.update_dy_from_slider)
        dy_layout.addWidget(self.dy_slider)

        self.dy_value = QLabel("0")
        dy_layout.addWidget(self.dy_value)

        # Add QLineEdit for exact dy input
        self.dy_input = QLineEdit()
        self.dy_input.setValidator(QIntValidator(-600, 600))
        self.dy_input.setFixedWidth(60)
        self.dy_input.textChanged.connect(self.update_dy_from_input)  # Connect to update method
        dy_layout.addWidget(self.dy_input)

        layout.addLayout(dy_layout)

        # Snap to Grid button
        self.snap_to_grid_button = QPushButton(_['snap_to_grid'])
        self.snap_to_grid_button.clicked.connect(self.snap_to_grid)
        layout.addWidget(self.snap_to_grid_button)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_ok_clicked)
        layout.addWidget(ok_button)

    def update_dx_from_slider(self):
        new_dx = self.dx_slider.value()
        self.total_dx = new_dx
        self.dx_value.setText(str(self.total_dx))
        self.dx_input.setText(str(self.total_dx))
        self.move_updated.emit(self.group_name, self.total_dx, self.total_dy)

    def update_dy_from_slider(self):
        new_dy = self.dy_slider.value()
        self.total_dy = new_dy
        self.dy_value.setText(str(self.total_dy))
        self.dy_input.setText(str(self.total_dy))
        self.move_updated.emit(self.group_name, self.total_dx, self.total_dy)

    def update_dx_from_input(self):
        text = self.dx_input.text()
        try:
            value = int(text)
            # Clamp the value within the slider range
            value = max(min(value, 600), -600)
            self.total_dx = value
            self.dx_slider.setValue(value)  # Update the slider
            self.dx_value.setText(str(value))
            self.move_updated.emit(self.group_name, self.total_dx, self.total_dy)
        except ValueError:
            pass  # Ignore invalid input

    def update_dy_from_input(self):
        text = self.dy_input.text()
        try:
            value = int(text)
            # Clamp the value within the slider range
            value = max(min(value, 600), -600)
            self.total_dy = value
            self.dy_slider.setValue(value)  # Update the slider
            self.dy_value.setText(str(value))
            self.move_updated.emit(self.group_name, self.total_dx, self.total_dy)
        except ValueError:
            pass  # Ignore invalid input

    def on_ok_clicked(self):
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

        # Set language_code appropriately
        if self.canvas and hasattr(self.canvas, 'language_code'):
            self.language_code = self.canvas.language_code
        elif hasattr(self.parent, 'language_code'):
            self.language_code = self.parent.language_code
        else:
            self.language_code = 'en'  # Default to English

        self.language_code = 'en'  # Or dynamically set based on user settings

        if self.language_code in translations:
            _ = translations[self.language_code]
        else:
            logging.error(f"Invalid language_code: {self.language_code}. Defaulting to 'en'.")
            _ = translations['en']
            self.language_code = 'en'

        # Access the translations
        _ = translations[self.language_code]

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
        logging.info(f"Adding strand {strand.layer_name} to group {group_name}")
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            if strand.layer_name not in group_data['layers']:
                group_data['layers'].append(strand.layer_name)
                self.group_panel.add_layer_to_group(strand.layer_name, group_name, strand)
                
                if self.canvas and group_name in self.canvas.groups:
                    self.canvas.groups[group_name]['strands'].append(strand)
                    self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                
                logging.info(f"Successfully added strand {strand.layer_name} to group {group_name}")
            else:
                logging.info(f"Strand {strand.layer_name} already in group {group_name}")
        else:
            logging.warning(f"Attempted to add strand to non-existent group: {group_name}")

        # Verify that the group still exists after the operation
        if group_name not in self.group_panel.groups:
            logging.error(f"Group {group_name} was deleted after adding strand {strand.layer_name}")
        
        logging.info(f"Finished adding strand {strand.layer_name} to group {group_name}")


    def update_groups_with_new_strand(self, new_strand):
        """
        Adds a new strand to the appropriate group if its parent strand is in a group.
        """
        # Ensure new_strand has a parent
        if not hasattr(new_strand, 'parent') or not new_strand.parent:
            logging.warning(f"New strand {new_strand.layer_name} has no parent; cannot update groups.")
            return

        for group_name, group_data in self.groups.items():
            # Check if the parent strand is in this group
            parent_in_group = any(
                strand.layer_name == new_strand.parent.layer_name for strand in group_data['strands']
            )
            if parent_in_group:
                # Add the new strand to the group's 'strands' list
                group_data['strands'].append(new_strand)
                group_data['layers'].append(new_strand.layer_name)
                logging.info(f"Successfully added strand {new_strand.layer_name} to group {group_name}")

                # If the new strand is a masked strand, ensure it's added
                if isinstance(new_strand, MaskedStrand):
                    for masked_strand in new_strand.masked_strands:
                        group_data['strands'].append(masked_strand)
                        group_data['layers'].append(masked_strand.layer_name)
                        logging.info(f"Masked strand {masked_strand.layer_name} added to group {group_name}")

                break  # Assuming a strand belongs to only one group
    def extract_main_layer(self, layer_name):
        # Split the layer name by underscores
        parts = layer_name.split('_')
        # The main layer is the first numeric part
        for part in parts:
            if part.isdigit():
                return part
        return None  # Return None if no numeric part is found
    def open_main_strand_selection_dialog(self, main_strands):
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        
        dialog = QDialog(self.layer_panel)
        dialog.setWindowTitle(_['select_main_strands'])

        layout = QVBoxLayout()

        # Create the info label
        info_label = QLabel(_['select_main_strands_to_include_in_the_group'])
        
  
        # **Add the info label to the layout**
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


    def create_group(self):
        # Access the current translation dictionary
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        # Prompt the user to enter a group name with translated text
        group_name, ok = QInputDialog.getText(
            self.layer_panel, _['create_group'], _['enter_group_name']
        )
        if ok and group_name:
            # Get the available main strands
            main_strands = self.get_unique_main_strands()

            # Open a dialog to select main strands to include in the group
            selected_main_strands = self.open_main_strand_selection_dialog(main_strands)
            if not selected_main_strands:
                logging.info(_['group_creation_cancelled'])
                return

            layers_data = []
            for strand in self.canvas.strands:
                main_layer = self.extract_main_layer(strand.layer_name)
                if main_layer in selected_main_strands:
                    layers_data.append(strand)

            # Create the group in the group panel
            self.group_panel.create_group(group_name, layers_data)

            # Initialize the group in canvas.groups and save selected main strands
            self.canvas.groups[group_name] = {
                'strands': [],
                'layers': [],
                'data': layers_data,
                'main_strands': selected_main_strands  # Store selected main strands
            }
            for strand in layers_data:
                self.canvas.groups[group_name]['strands'].append(strand)
                self.canvas.groups[group_name]['layers'].append(strand.layer_name)

            logging.info(f"Created group '{group_name}' with {len(layers_data)} strands")
    def get_main_layers(self):
        return list(set([layer.split('_')[0] for layer in self.get_all_layers()]))

    def get_sub_layers(self, main_layer):
        return [layer for layer in self.get_all_layers() if layer.startswith(f"{main_layer}_")]

    def get_all_layers(self):
        return [button.text() for button in self.layer_panel.layer_buttons]

    def get_layer_index(self, layer_name):
        return self.layer_panel.layer_buttons.index(next(button for button in self.layer_panel.layer_buttons if button.text() == layer_name))
    def get_unique_main_strands(self):
        main_strands = set()
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer:
                main_strands.add(main_layer)
        return sorted(main_strands)
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
            "width": strand.width,
            "color": self.serialize_color(strand.color),
            "is_masked": isinstance(strand, MaskedStrand),
            "attached_to": [self.canvas.strands.index(attached_strand) for attached_strand in strand.attached_strands],
            "has_circles": strand.has_circles.copy()
        }

    def deserialize_strand(self, data):
        start = QPointF(data["start"]["x"], data["start"]["y"])
        end = QPointF(data["end"]["x"], data["end"]["y"])
        strand = Strand(start, end, data["width"])
        strand.color = self.deserialize_color(data["color"])
        strand.has_circles = data["has_circles"]
        strand.attached_strands = [self.canvas.strands[i] for i in data["attached_to"]]
        return strand

    def serialize_color(self, color):
        return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}

    def deserialize_color(self, data):
        return QColor(data["r"], data["g"], data["b"], data["a"])

    def get_group_data(self):
        group_data = {}
        for group_name, group_info in self.group_panel.groups.items():
            group_data[group_name] = {
                "layers": group_info["layers"],
                "strands": [self.serialize_strand(strand) for strand in group_info["strands"]]
            }
        return group_data
    def apply_group_data(self, group_data):
        for group_name, group_info in group_data.items():
            self.group_panel.create_group(group_name, group_info["strands"])
            for layer_name in group_info["layers"]:
                strand_data = next((strand for strand in group_info["strands"] if strand["layer_name"] == layer_name), None)
                self.group_panel.add_layer_to_group(layer_name, group_name, strand_data)
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
        for group_name, group_info in self.group_panel.groups.items():
            group_data[group_name] = {
                "layers": group_info["layers"],
                "strands": [self.serialize_strand(strand) for strand in group_info["strands"]]
            }
        return group_data

    def apply_group_data(self, group_data):
        for group_name, group_info in group_data.items():
            # Retrieve the corresponding Strand objects from the canvas
            strands = []
            for strand_data in group_info["strands"]:
                layer_name = strand_data["layer_name"]
                strand = next(
                    (s for s in self.canvas.strands if s.layer_name == layer_name),
                    None
                )
                if strand:
                    strands.append(strand)
                else:
                    logging.warning(f"Strand with layer_name '{layer_name}' not found in canvas.strands")
            # Pass both group_name and strands to create_group
            self.group_panel.create_group(group_name, strands)
    def move_group_strands(self, group_name, dx, dy):
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            updated_strands = []

            for i, strand_data in enumerate(group_data['strands']):
                layer_name = group_data['layers'][i]
                layer_index = self.get_layer_index(layer_name)
                if layer_index < len(self.canvas.strands):
                    strand = self.canvas.strands[layer_index]
                    # Move the entire strand
                    strand.start += QPointF(dx, dy)
                    strand.end += QPointF(dx, dy)
                    strand.update_shape()
                    if hasattr(strand, 'update_side_line'):
                        strand.update_side_line()
                    updated_strands.append(strand)

            # Update the canvas with all modified strands
            self.canvas.update_strands(updated_strands)

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
        if group_name in self.group_panel.groups:
            if self.canvas:
                self.canvas.start_group_rotation(group_name)
                dialog = GroupRotateDialog(group_name, self)
                dialog.rotation_updated.connect(self.update_group_rotation)
                dialog.rotation_finished.connect(self.finish_group_rotation)
                dialog.exec_()
            else:
                logging.error("Canvas not properly connected to GroupPanel")
        else:
            logging.warning(f"Attempted to rotate non-existent group: {group_name}")

    def update_group_rotation(self, group_name, angle):
        logging.info(f"GroupPanel: Updating group rotation for '{group_name}' by angle={angle}")
        if self.canvas:
            self.canvas.rotate_group(group_name, angle)
        else:
            logging.error("Canvas not properly connected to GroupPanel")

    def finish_group_rotation(self, group_name):
        logging.info(f"GroupPanel: Finishing group rotation for '{group_name}'")
        if self.canvas:
            self.canvas.finish_group_rotation(group_name)
        else:
            logging.error("Canvas not properly connected to GroupPanel")

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
        self.group_name = group_name
        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None

                # Define the language code, defaulting to 'en' if not available
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

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
        self.angle = self.angle_slider.value()
        self.angle_input.setText(str(self.angle))
        self.rotation_updated.emit(self.group_name, self.angle)

    def update_angle_from_input(self):
        try:
            self.angle = float(self.angle_input.text())
            self.angle_slider.setValue(int(self.angle))
            self.rotation_updated.emit(self.group_name, self.angle)
        except ValueError:
            pass  # Ignore invalid input

    # Update the group's strands rotation
    def rotate_group_strands(self):
        if self.canvas and self.group_name in self.canvas.groups:
            group_data = self.canvas.groups[self.group_name]
            rotation_center = self.calculate_group_center(group_data['strands'])
            angle_radians = radians(self.angle)
            for strand in group_data['strands']:
                self.rotate_strand_around_point(strand, rotation_center, angle_radians)
            self.canvas.update()
        else:
            logging.error(f"Group '{self.group_name}' not found in canvas.")

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

        self.adjustment_timer = QTimer(self)
        self.adjustment_timer.setInterval(10)
        self.initial_delay_timer = QTimer(self)
        self.initial_delay_timer.setSingleShot(True)
        self.initial_delay_timer.setInterval(500)
        self.current_adjustment = None

        # Adjustment values
        self.delta_plus = 1
        self.delta_minus = -1
        self.delta_plus_plus = 5
        self.delta_minus_minus = -5

        # Continuous adjustment values
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

            # Angle adjustment buttons
            angle_buttons = self.create_angle_buttons(row)
            self.table.setCellWidget(row, 2, angle_buttons)

            # Fast angle adjustment buttons
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

            # Checkboxes
            x_checkbox = QCheckBox("x")
            x_plus_180_checkbox = QCheckBox("180+x")

            # Checkboxes styles are applied via stylesheet

            self.table.setCellWidget(row, 6, x_checkbox)
            self.table.setCellWidget(row, 7, x_plus_180_checkbox)

            # 'Attachable' indicator
            attachable_text = 'X' if not is_attachable else ''
            attachable_item = QTableWidgetItem(attachable_text)
            attachable_item.setTextAlignment(Qt.AlignCenter)
            attachable_item.setFlags(attachable_item.flags() & ~Qt.ItemIsEditable)
            self.set_item_style(attachable_item, is_editable)
            self.table.setItem(row, 8, attachable_item)

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
        self.x_angle_input.setFixedWidth(100)
        self.x_angle_input.setText("0.00")
        self.x_angle_input.textChanged.connect(self.update_x_angle)
        x_angle_layout.addWidget(x_angle_label)
        x_angle_layout.addWidget(self.x_angle_input)
        x_angle_layout.addStretch()

        # Buttons
        button_layout_widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout_widget.setLayout(button_layout)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignRight)

        minus_minus_btn = QPushButton("--")
        minus_btn = QPushButton("-")
        plus_btn = QPushButton("+")
        plus_plus_btn = QPushButton("++")
        ok_btn = QPushButton("OK")

        for btn in [minus_minus_btn, minus_btn, plus_btn, plus_plus_btn, ok_btn]:
            btn.setFixedSize(50, 30)
            # Styles will be applied via stylesheet

        minus_minus_btn.clicked.connect(lambda: self.adjust_x_angle(-5))
        minus_btn.clicked.connect(lambda: self.adjust_x_angle(-1))
        plus_btn.clicked.connect(lambda: self.adjust_x_angle(1))
        plus_plus_btn.clicked.connect(lambda: self.adjust_x_angle(5))
        ok_btn.clicked.connect(self.accept)

        button_layout.addWidget(minus_minus_btn)
        button_layout.addWidget(minus_btn)
        button_layout.addWidget(plus_btn)
        button_layout.addWidget(plus_plus_btn)
        button_layout.addWidget(ok_btn)

        # Combine x_angle_widget and buttons into one layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(x_angle_widget)
        bottom_layout.addStretch()
        bottom_layout.addWidget(button_layout_widget)

        return bottom_layout

    def adjust_dialog_size(self):
        # Calculate the required width and height
        width = self.table.verticalHeader().width() + 4  # Left and right margins
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i)

        height = self.table.horizontalHeader().height() + 4  # Top and bottom margins
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)

        # Add some padding
        width += 250
        height += 300  # Extra space for the OK button and padding

        # Set the size of the dialog
        self.resize(width, height)

        # Center the dialog on the screen
        screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
        center_point = QDesktopWidget().screenGeometry(screen).center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def apply_theme(self):
        """Apply the current theme using custom stylesheets."""
        is_dark_mode = False
        if hasattr(self.canvas, 'is_dark_mode'):
            is_dark_mode = self.canvas.is_dark_mode

        if is_dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

        # Update styles of table items if necessary
        self.update_table_styles()

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
                background-color: #DDDDDD;
                color: #000000;
                padding: 4px;
                border: 1px solid #CCCCCC;
            }
            QTableCornerButton::section {
                background-color: #DDDDDD;
                border: 1px solid #CCCCCC;
            }
            QCheckBox {
                color: #000000;
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
        if self.initializing:
            return
        row = item.row()
        col = item.column()
        strand = self.group_data['strands'][row]
        if col == 1:  # Angle column
            try:
                new_angle = float(item.text())
                self.update_strand_angle(strand, new_angle)
            except ValueError:
                pass  # Invalid input, ignore

    def update_strand_angle(self, strand, new_angle):
        dx = strand.end.x() - strand.start.x()
        dy = strand.end.y() - strand.start.y()
        length = (dx**2 + dy**2)**0.5
        angle_rad = radians(new_angle)
        new_end_x = strand.start.x() + length * cos(angle_rad)
        new_end_y = strand.start.y() + length * sin(angle_rad)
        strand.end = QPointF(new_end_x, new_end_y)
        strand.update_shape()
        self.canvas.update()

    def create_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        minus_button = QPushButton("-")
        plus_button = QPushButton("+")
        minus_button.setFixedSize(28, 24)
        plus_button.setFixedSize(28, 24)

        # Styles are applied via stylesheet

        plus_button.clicked.connect(lambda: self.on_plus_clicked(row))
        minus_button.clicked.connect(lambda: self.on_minus_clicked(row))

        layout.addWidget(minus_button)
        layout.addWidget(plus_button)
        layout.setAlignment(Qt.AlignCenter)

        return widget

    def create_fast_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        minus_minus_button = QPushButton("--")
        plus_plus_button = QPushButton("++")
        minus_minus_button.setFixedSize(28, 24)
        plus_plus_button.setFixedSize(28, 24)

        # Styles are applied via stylesheet

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
                x_plus_180_checkbox = self.table.cellWidget(row, 7)
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
                angle = self.x_angle + 180  # Use x_angle + 180
                x_checkbox = self.table.cellWidget(row, 6)
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
        except ValueError:
            self.x_angle = 0.0

    def adjust_x_angle(self, delta):
        try:
            current_x_angle = float(self.x_angle_input.text())
        except ValueError:
            current_x_angle = 0.0
        new_x_angle = current_x_angle + delta
        self.x_angle_input.setText(f"{new_x_angle:.2f}")
        self.apply_x_angle_to_selected()

    def apply_x_angle_to_selected(self):
        for row in range(self.table.rowCount()):
            x_checkbox = self.table.cellWidget(row, 6)
            x_plus_180_checkbox = self.table.cellWidget(row, 7)
            if x_checkbox.isChecked():
                self.on_checkbox_changed(row, 6, Qt.Checked)
            elif x_plus_180_checkbox.isChecked():
                self.on_checkbox_changed(row, 7, Qt.Checked)

    def calculate_angle(self, strand):
        dx = strand.end.x() - strand.start.x()
        dy = strand.end.y() - strand.start.y()
        angle = degrees(atan2(dy, dx))
        return angle

    def accept(self):
        # Perform any final actions before closing the dialog
        super().accept()