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

class GroupedLayerTree(QTreeWidget):
    layer_selected = pyqtSignal(int)
    group_created = pyqtSignal(str)
    layer_moved = pyqtSignal(int, str)  # layer index, group name

    def __init__(self, layer_panel, canvas=None):
        super().__init__()  # Call the superclass constructor
        self.layer_panel = layer_panel
        self.canvas = canvas
        self.group_panel = GroupPanel(canvas=self.canvas)
        
        if self.canvas:
            logging.info(f"GroupLayerManager initialized with canvas: {self.canvas}")
        else:
            logging.warning("GroupLayerManager initialized without a canvas")

    def update_layer(self, index, layer_name, color):
        # Check if the layer is in any group
        for group_name, group_info in self.groups.items():
            if layer_name in group_info['layers']:
                # Update the layer in the group
                group_widget = self.findChild(CollapsibleGroupWidget, group_name)
                if group_widget:
                    group_widget.update_layer(index, layer_name, color)
                return
        
        # If the layer is not in any group, it might be a new layer
        # You can decide how to handle new layers here, for example:
        # self.add_layer_to_default_group(layer_name, color)

    def add_layer(self, layer_name, color=None, is_masked=False):
        if layer_name not in self.layers:
            self.layers.append(layer_name)
            item = QListWidgetItem(layer_name)
            if color:
                item.setForeground(color)
            if is_masked:
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor(255, 0, 0))  # Red square for masked layers
                item.setIcon(QIcon(pixmap))
            self.layers_list.addItem(item)
            self.update_size()
            logging.info(f"Added layer {layer_name} to CollapsibleGroupWidget")

    def add_group(self, group_name):
        group_item = QTreeWidgetItem(self, [group_name])
        group_item.setData(0, Qt.UserRole, "group")
        group_item.setExpanded(True)
        self.addTopLevelItem(group_item)
        self.group_created.emit(group_name)
        return group_item

    def on_item_clicked(self, item, column):
        if item.data(0, Qt.UserRole) == "layer":
            index = self.indexOfTopLevelItem(item)
            if index == -1:
                # Item is in a group, find its overall index
                parent = item.parent()
                index = self.indexOfTopLevelItem(parent)
                for i in range(parent.childCount()):
                    if parent.child(i) == item:
                        index += i + 1
                        break
            self.layer_selected.emit(index)

    def dropEvent(self, event):
        if event.source() == self:
            super().dropEvent(event)
            dropped_item = self.itemAt(event.pos())
            if dropped_item and dropped_item.data(0, Qt.UserRole) == "group":
                moved_item = self.currentItem()
                if moved_item and moved_item.data(0, Qt.UserRole) == "layer":
                    index = self.get_layer_index(moved_item)
                    self.layer_moved.emit(index, dropped_item.text(0))

    def get_layer_index(self, item):
        if self.indexOfTopLevelItem(item) != -1:
            return self.indexOfTopLevelItem(item)
        parent = item.parent()
        index = self.indexOfTopLevelItem(parent)
        for i in range(parent.childCount()):
            if parent.child(i) == item:
                return index + i + 1
        return -1
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget, 
                             QListWidgetItem, QMenu, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

class CollapsibleGroupWidget(QWidget):
    def __init__(self, group_name, group_panel, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.group_panel = group_panel
        self.is_collapsed = False
        self.layers = []  # Store layer names
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Header (group name button)
        self.group_button = QPushButton(self.group_name)
        self.group_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 0px;
                padding: 5px;
                text-align: left;
            }
        """)
        self.group_button.clicked.connect(self.toggle_collapse)
        self.group_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_button.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.group_button)

        # Content (layer list)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.layout.addWidget(self.content)

        # Add QListWidget for layers
        self.layers_list = QListWidget()
        self.layers_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
            }
            QListWidget::item {
                padding: 2px;
            }
        """)
        self.content_layout.addWidget(self.layers_list)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        move_strands_action = context_menu.addAction("Move Group Strands")
        rotate_strands_action = context_menu.addAction("Rotate Group Strands")
        edit_angles_action = context_menu.addAction("Edit Strand Angles")  # New action
        
        action = context_menu.exec_(self.group_button.mapToGlobal(position))

        if action == move_strands_action:
            self.group_panel.start_group_move(self.group_name)
        elif action == rotate_strands_action:
            self.group_panel.start_group_rotation(self.group_name)
        elif action == edit_angles_action:
            self.group_panel.edit_strand_angles(self.group_name)  # New method call

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.content.setVisible(not self.is_collapsed)
        self.update_size()

    def add_layer(self, layer_name, color=None, is_masked=False):
        if layer_name not in self.layers:
            self.layers.append(layer_name)
            item = QListWidgetItem(layer_name)
            if color:
                item.setForeground(color)
            if is_masked:
                item.setIcon(QIcon("path_to_mask_icon.png"))  # Add an icon for masked layers
            self.layers_list.addItem(item)
            self.update_size()

    def update_size(self):
        if not self.is_collapsed:
            total_height = self.group_button.sizeHint().height()
            total_height += self.layers_list.sizeHintForRow(0) * self.layers_list.count()
            self.setFixedHeight(total_height)
        else:
            self.setFixedHeight(self.group_button.sizeHint().height())
        self.update_group_display()

    def update_group_display(self):
        masked_count = sum(1 for layer in self.layers if len(layer.split('_')) == 4)
        self.group_button.setText(f"{self.group_name} ({len(self.layers)}, Masked: {masked_count})")

    def update_layer(self, layer_name, color):
        for i in range(self.layers_list.count()):
            item = self.layers_list.item(i)
            if item.text() == layer_name:
                # Update the color of the layer item
                item.setForeground(color)
                break

    def remove_layer(self, layer_name):
        if layer_name in self.layers:
            self.layers.remove(layer_name)
            for i in range(self.layers_list.count()):
                if self.layers_list.item(i).text() == layer_name:
                    self.layers_list.takeItem(i)
                    break
            self.update_size()

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class GroupPanel(QWidget):
    group_operation = pyqtSignal(str, str, list)  # operation, group_name, layer_indices
    move_group_started = pyqtSignal(str, list)  # New signal

    def __init__(self, canvas=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.groups = {}
        self.setAcceptDrops(True)
        self.canvas = canvas
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

    def create_group(self, group_name, layers_data):
        group_widget = CollapsibleGroupWidget(group_name, self)
        self.scroll_layout.addWidget(group_widget)
        self.groups[group_name] = {'widget': group_widget, 'layers': [], 'strands': layers_data}

        for strand_data in layers_data:
            self.add_layer_to_group(strand_data['layer_name'], group_name, strand_data)

    def add_layer_to_group(self, layer_name, group_name, strand_data):
        if group_name not in self.groups:
            logging.error(f"Attempted to add layer to non-existent group: {group_name}")
            return

        self.groups[group_name]['layers'].append(layer_name)
        self.groups[group_name]['widget'].add_layer(
            layer_name, 
            color=strand_data.get('color'),
            is_masked=strand_data.get('is_masked', False)
        )
        self.groups[group_name]['widget'].update_group_display()
        logging.info(f"Successfully added layer {layer_name} to group {group_name}")

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

    def start_group_rotation(self, group_name):
        if group_name in self.groups:
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

    def clear(self):
        # Remove all widgets from the scroll layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        
        # Clear the groups dictionary
        self.groups.clear()

    def update_layer(self, index, layer_name, color):
        # Update the layer information in the groups
        for group_name, group_info in self.groups.items():
            if layer_name in group_info['layers']:
                group_widget = self.findChild(CollapsibleGroupWidget, group_name)
                if group_widget:
                    group_widget.update_layer(index, layer_name, color)

    def edit_strand_angles(self, group_name):
        if group_name in self.groups:
            dialog = StrandAngleEditDialog(group_name, self.groups[group_name], self.canvas, self)
            dialog.exec_()

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class GroupMoveDialog(QDialog):
    move_updated = pyqtSignal(str, int, int)
    move_finished = pyqtSignal(str)

    def __init__(self, group_name, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None
        self.setWindowTitle(f"Move Group Strands: {group_name}")
        self.total_dx = 0
        self.total_dy = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # dx slider
        dx_layout = QHBoxLayout()
        dx_layout.addWidget(QLabel("dx:"))
        self.dx_slider = QSlider(Qt.Horizontal)
        self.dx_slider.setRange(-600, 600)
        self.dx_slider.setValue(0)
        self.dx_slider.valueChanged.connect(self.update_dx)
        dx_layout.addWidget(self.dx_slider)
        self.dx_value = QLabel("0")
        dx_layout.addWidget(self.dx_value)
        layout.addLayout(dx_layout)

        # dy slider
        dy_layout = QHBoxLayout()
        dy_layout.addWidget(QLabel("dy:"))
        self.dy_slider = QSlider(Qt.Horizontal)
        self.dy_slider.setRange(-600, 600)
        self.dy_slider.setValue(0)
        self.dy_slider.valueChanged.connect(self.update_dy)
        dy_layout.addWidget(self.dy_slider)
        self.dy_value = QLabel("0")
        dy_layout.addWidget(self.dy_value)
        layout.addLayout(dy_layout)

        # Add a new button for snapping to grid
        self.snap_to_grid_button = QPushButton("Snap to Grid")
        self.snap_to_grid_button.clicked.connect(self.snap_to_grid)
        layout.addWidget(self.snap_to_grid_button)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_ok_clicked)
        layout.addWidget(ok_button)

    def update_dx(self):
        new_dx = self.dx_slider.value()
        self.total_dx = new_dx
        self.dx_value.setText(str(self.total_dx))
        self.move_updated.emit(self.group_name, self.total_dx, self.total_dy)

    def update_dy(self):
        new_dy = self.dy_slider.value()
        self.total_dy = new_dy
        self.dy_value.setText(str(self.total_dy))
        self.move_updated.emit(self.group_name, self.total_dx, self.total_dy)

    def on_ok_clicked(self):
        self.move_finished.emit(self.group_name)
        self.accept()

    def snap_to_grid(self):
        if self.canvas:
            self.canvas.snap_group_to_grid(self.group_name)
        self.move_finished.emit(self.group_name)
        self.accept()

def create_group(self, group_name, layers_data):
    group_widget = CollapsibleGroupWidget(group_name, self)
    self.scroll_layout.addWidget(group_widget)
    self.groups[group_name] = {'widget': group_widget, 'layers': [], 'strands': []}

    for layer_name, strand_data in layers_data:
        self.add_layer_to_group(layer_name, group_name, strand_data)


def add_layer_to_group(self, layer_name, group_name, strand_data):
    if group_name not in self.groups:
        return  # Group doesn't exist, can't add layer

    self.groups[group_name]['layers'].append(layer_name)
    self.groups[group_name]['strands'].append(strand_data)
    self.groups[group_name]['widget'].add_layer(layer_name)
    self.groups[group_name]['widget'].update_group_display()

def update_group_display(self, group_name):
    if group_name in self.groups:
        self.groups[group_name]['widget'].update_group_display()

def clear(self):
    # Remove all widgets from the scroll layout
    for i in reversed(range(self.scroll_layout.count())):
        widget = self.scroll_layout.itemAt(i).widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
    
    # Clear the groups dictionary
    self.groups.clear()

def update_layer(self, index, layer_name, color):
    # Check if the layer is in any group
    for group_name, group_info in self.groups.items():
        if layer_name in group_info['layers']:
            # Update the layer in the group
            group_widget = self.findChild(CollapsibleGroupWidget, group_name)
            if group_widget:
                group_widget.update_layer(layer_name, color)
            return

def start_move_mode(self, group_name):
    self.move_group_started.emit(group_name)
    self.group_operation.emit("prepare_move", group_name, self.groups[group_name]['layers'])

def delete_group(self, group_name):
    if group_name in self.groups:
        self.group_operation.emit("delete", group_name, self.groups[group_name]['layers'])
        group_widget = self.groups.pop(group_name)['widget']
        self.scroll_layout.removeWidget(group_widget)
        group_widget.deleteLater()

class LayerSelectionDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Layers for Group")
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

class GroupLayerManager:
    def __init__(self, layer_panel, canvas=None):
        self.layer_panel = layer_panel
        self.canvas = canvas
        self.group_panel = GroupPanel(canvas=self.canvas)
        self.tree = GroupedLayerTree(layer_panel, canvas=self.canvas)
        self.tree.hide()  # Hide the tree completely
        
        if self.canvas:
            logging.info(f"GroupLayerManager initialized with canvas: {self.canvas}")
            logging.info("Connecting canvas signals to GroupLayerManager")
            self.canvas.attach_mode.strand_attached.connect(self.on_strand_attached)
            self.canvas.strand_created.connect(self.on_strand_created)
            self.canvas.groups = {}  # Initialize the groups attribute in the canvas
        else:
            logging.warning("Canvas not provided to GroupLayerManager")

        self.create_group_button = QPushButton("Create Group")
        self.create_group_button.clicked.connect(self.create_group)

    def set_canvas(self, canvas):
        self.canvas = canvas
        self.group_panel.set_canvas(canvas)
        self.canvas.groups = {}  # Initialize the groups attribute in the canvas
        logging.info(f"Canvas set on GroupLayerManager: {self.canvas}")

    def on_strand_created(self, new_strand):
        logging.info(f"New strand created: {new_strand.layer_name}")
        self.update_groups_with_new_strand(new_strand)

    def on_strand_attached(self, parent_strand, new_strand):
        logging.info(f"New strand attached: {new_strand.layer_name} to {parent_strand.layer_name}")
        self.update_groups_with_new_strand(new_strand)

    def add_strand_to_group(self, group_name, strand):
        logging.info(f"Adding strand {strand.layer_name} to group {group_name}")
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            if strand.layer_name not in group_data['layers']:
                group_data['layers'].append(strand.layer_name)
                strand_data = {
                    'layer_name': strand.layer_name,
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end),
                    'color': strand.color,
                    'is_masked': isinstance(strand, MaskedStrand)
                }
                self.group_panel.add_layer_to_group(strand.layer_name, group_name, strand_data)
                
                if self.canvas and group_name in self.canvas.groups:
                    self.canvas.groups[group_name]['strands'].append(strand)
                    self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                
                logging.info(f"Successfully added strand {strand.layer_name} to group {group_name}")
            else:
                logging.info(f"Strand {strand.layer_name} already in group {group_name}")
        else:
            logging.warning(f"Attempted to add strand to non-existent group: {group_name}")

        logging.info(f"Group {group_name} layers after adding: {self.group_panel.groups[group_name]['layers']}")

    def update_groups_with_new_mask(self, masked_strand):
        logging.info(f"Updating groups with new mask: {masked_strand.layer_name}")
        logging.info(f"Current groups: {list(self.group_panel.groups.keys())}")
        for group_name, group_data in self.group_panel.groups.items():
            logging.info(f"Checking group: {group_name}")
            logging.info(f"Group layers: {group_data['layers']}")
            # Check if any of the parent strands of the mask are in the group
            if any(parent.layer_name in group_data['layers'] for parent in masked_strand.parent_strands):
                logging.info(f"Parent strand found in group {group_name}")
                logging.info(f"Adding mask {masked_strand.layer_name} to group {group_name}")
                self.add_strand_to_group(group_name, masked_strand)
        
        logging.info(f"Finished updating groups with new mask: {masked_strand.layer_name}")
        logging.info(f"Groups after update: {list(self.group_panel.groups.keys())}")


    def update_groups_with_new_strand(self, new_strand):
        logging.info(f"Updating groups with new strand: {new_strand.layer_name}")
        main_layer = new_strand.layer_name.split('_')[0]
        for group_name, group_data in self.group_panel.groups.items():
            logging.info(f"Checking group: {group_name}")
            if any(layer.startswith(f"{main_layer}_") for layer in group_data['layers']):
                logging.info(f"Adding strand {new_strand.layer_name} to group {group_name}")
                self.add_strand_to_group(group_name, new_strand)

    def create_group(self):
        group_name, ok = QInputDialog.getText(self.layer_panel, "Create Group", "Enter group name:")
        if ok and group_name:
            main_layers = self.get_main_layers()
            dialog = LayerSelectionDialog(main_layers, self.layer_panel)
            if dialog.exec_():
                selected_main_layers = dialog.get_selected_layers()
                self.tree.add_group(group_name)
                
                layers_data = []
                for main_layer in selected_main_layers:
                    sub_layers = self.get_sub_layers(main_layer)
                    for sub_layer in sub_layers:
                        layer_index = self.get_layer_index(sub_layer)
                        if layer_index < len(self.canvas.strands):
                            strand = self.canvas.strands[layer_index]
                            strand_data = {
                                'layer_name': sub_layer,
                                'start': QPointF(strand.start),
                                'end': QPointF(strand.end),
                                'width': strand.width,
                                'color': strand.color,
                                'is_masked': len(sub_layer.split('_')) == 4,  # Check if it's a masked layer
                                'attached_to': [],
                                'has_circles': strand.has_circles.copy()
                            }
                            
                            # Save information about attached strands
                            for attached_strand in strand.attached_strands:
                                attached_index = self.canvas.strands.index(attached_strand)
                                strand_data['attached_to'].append(attached_index)
                            
                            layers_data.append(strand_data)
                
                self.group_panel.create_group(group_name, layers_data)
                
                # Initialize the group in canvas.groups
                self.canvas.groups[group_name] = {
                    'strands': [],
                    'layers': [],
                    'data': layers_data
                }
                for strand_data in layers_data:
                    strand = self.canvas.find_strand_by_name(strand_data['layer_name'])
                    if strand:
                        self.canvas.groups[group_name]['strands'].append(strand)
                        self.canvas.groups[group_name]['layers'].append(strand_data['layer_name'])

                logging.info(f"Created group '{group_name}' with {len(layers_data)} strands")

    def get_main_layers(self):
        return list(set([layer.split('_')[0] for layer in self.get_all_layers()]))

    def get_sub_layers(self, main_layer):
        return [layer for layer in self.get_all_layers() if layer.startswith(f"{main_layer}_")]

    def get_all_layers(self):
        return [button.text() for button in self.layer_panel.layer_buttons]

    def get_layer_index(self, layer_name):
        return self.layer_panel.layer_buttons.index(next(button for button in self.layer_panel.layer_buttons if button.text() == layer_name))

    def on_group_created(self, group_name):
        # You can add any additional logic here when a group is created
        pass

    def on_layer_moved(self, layer_index, group_name):
        layer_name = self.layer_panel.layer_buttons[layer_index].text()
        self.group_panel.add_layer_to_group(layer_name, group_name)
        
        # Update canvas groups
        if self.canvas and group_name in self.canvas.groups:
            strand = self.canvas.find_strand_by_name(layer_name)
            if strand:
                self.canvas.groups[group_name]['strands'].append(strand)
                self.canvas.groups[group_name]['layers'].append(layer_name)

    def on_group_operation(self, operation, group_name, layer_indices):
        if operation == "move":
            self.move_group(group_name, layer_indices)

    def move_group(self, group_name, layer_indices):
        # Move all strands in the group
        offset = QPoint(50, 50)  # You can adjust this or make it user-input
        for i in layer_indices:
            strand = self.canvas.strands[i]
            strand.move(offset)

        self.canvas.update()

    def add_layer(self, layer_name, color):
        return self.tree.add_layer(layer_name, color)

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
        self.group_panel.clear()
        for i, button in enumerate(self.layer_panel.layer_buttons):
            self.group_panel.update_layer(i, button.text(), button.color)

    def get_group_data(self):
        group_data = {}
        for group_name, group_info in self.group_panel.groups.items():
            group_data[group_name] = group_info["layers"]
        return group_data

    def apply_group_data(self, group_data):
        for group_name, layer_indices in group_data.items():
            self.group_panel.create_group(group_name)
            for layer_index in layer_indices:
                self.group_panel.add_layer_to_group(layer_index, group_name)

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



        logging.info(f"Adding strand {strand.layer_name} to group {group_name}")
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            if strand.layer_name not in group_data['layers']:
                group_data['layers'].append(strand.layer_name)
                strand_data = {
                    'layer_name': strand.layer_name,
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end),
                    'color': strand.color,
                    'is_masked': isinstance(strand, MaskedStrand)
                }
                self.group_panel.add_layer_to_group(strand.layer_name, group_name, strand_data)
                
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
        self.setWindowTitle(f"Rotate Group Strands: {group_name}")
        self.angle = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Angle slider
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("Angle:"))
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(-180, 180)
        self.angle_slider.setValue(0)
        self.angle_slider.valueChanged.connect(self.update_angle_from_slider)
        angle_layout.addWidget(self.angle_slider)
        layout.addLayout(angle_layout)

        # Precise angle input
        precise_angle_layout = QHBoxLayout()
        precise_angle_layout.addWidget(QLabel("Precise Angle:"))
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

class StrandAngleEditDialog(QDialog):
    angle_changed = pyqtSignal(str, float)

    def __init__(self, group_name, group_data, canvas, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.canvas = canvas
        self.linked_strands = {}
        self.setWindowTitle(f"Edit Strand Angles: {group_name}")
        self.updating = False
        
        self.group_data = {
            'strands': [self.ensure_strand_object(s) for s in group_data['strands']],
            'layers': group_data['layers']
        }
        
        self.setup_ui()
        self.adjustment_timer = QTimer(self)
        self.adjustment_timer.setInterval(10)  # 10 milliseconds (0.01 seconds)
        self.initial_delay_timer = QTimer(self)
        self.initial_delay_timer.setSingleShot(True)
        self.initial_delay_timer.setInterval(500)  # 0.5 seconds
        self.current_adjustment = None

        # Define different delta values for each button type
        self.delta_plus = 1
        self.delta_minus = -1
        self.delta_plus_plus = 5
        self.delta_minus_minus = -5
        
        # Separate continuous delta values for each direction
        self.delta_continuous_plus = 0.025
        self.delta_continuous_minus = -0.025
        self.delta_fast_continuous_plus = 0.4
        self.delta_fast_continuous_minus = -0.4

        self.current_button = None
        self.last_press_time = None

    def ensure_strand_object(self, strand):
        if isinstance(strand, dict):
            return self.canvas.find_strand_by_name(strand['layer_name'])
        return strand

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        self.populate_table()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        # Set the dialog size after a short delay to ensure all widgets are properly sized
        QTimer.singleShot(0, self.adjust_dialog_size)

    def setup_table(self):
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Strand", "Angle", "+/-", "++/--", "End X", "End Y", "x", "180+x"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setItemDelegate(FloatDelegate())
        self.table.itemChanged.connect(self.on_item_changed)

    def adjust_dialog_size(self):
        # Calculate the required width and height
        width = self.table.verticalHeader().width() + 4  # Left and right margins
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i)
        
        height = self.table.horizontalHeader().height() + 4  # Top and bottom margins
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)

        # Add some padding
        width += 550
        height += 400  # Extra space for the OK button and padding

        # Set the size of the dialog
        self.resize(width, height)

        # Center the dialog on the screen
        screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
        center_point = QDesktopWidget().screenGeometry(screen).center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def populate_table(self):
        non_masked_strands = [strand for strand in self.group_data['strands'] 
                              if not isinstance(strand, MaskedStrand)]
        self.table.setRowCount(len(non_masked_strands))

        for row, strand in enumerate(non_masked_strands):
            is_main_strand = strand.layer_name.endswith("_1")
            
            self.table.setItem(row, 0, QTableWidgetItem(strand.layer_name))
            
            angle = self.calculate_angle(strand)
            angle_item = QTableWidgetItem(f"{angle:.2f}")
            self.table.setItem(row, 1, angle_item)

            angle_buttons = self.create_angle_buttons(row)
            self.table.setCellWidget(row, 2, angle_buttons)

            fast_angle_buttons = self.create_fast_angle_buttons(row)
            self.table.setCellWidget(row, 3, fast_angle_buttons)

            end_x_item = QTableWidgetItem(f"{strand.end.x():.2f}")
            self.table.setItem(row, 4, end_x_item)

            end_y_item = QTableWidgetItem(f"{strand.end.y():.2f}")
            self.table.setItem(row, 5, end_y_item)

            x_checkbox = QCheckBox("x")
            x_checkbox.setObjectName("x")
            self.table.setCellWidget(row, 6, x_checkbox)

            x_plus_180_checkbox = QCheckBox("180+x")
            x_plus_180_checkbox.setObjectName("180+x")
            self.table.setCellWidget(row, 7, x_plus_180_checkbox)

            x_checkbox.stateChanged.connect(lambda state, r=row, c=x_checkbox: self.on_checkbox_changed(r, c, state))
            x_plus_180_checkbox.stateChanged.connect(lambda state, r=row, c=x_plus_180_checkbox: self.on_checkbox_changed(r, c, state))

            for col in [1, 4, 5]:  # Angle, End X, End Y
                item = self.table.item(row, col)
                if is_main_strand:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

            if is_main_strand:
                angle_buttons.setEnabled(False)
                fast_angle_buttons.setEnabled(False)
                x_checkbox.setEnabled(False)
                x_plus_180_checkbox.setEnabled(False)

    def create_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        plus_button = QPushButton("+")
        minus_button = QPushButton("-")
        plus_button.setFixedSize(20, 20)
        minus_button.setFixedSize(20, 20)

        plus_button.pressed.connect(lambda: self.on_plus_pressed(row))
        plus_button.released.connect(self.on_plus_released)
        minus_button.pressed.connect(lambda: self.on_minus_pressed(row))
        minus_button.released.connect(self.on_minus_released)

        layout.addWidget(minus_button)
        layout.addWidget(plus_button)

        return widget

    def create_fast_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        plus_plus_button = QPushButton("++")
        minus_minus_button = QPushButton("--")
        plus_plus_button.setFixedSize(30, 20)
        minus_minus_button.setFixedSize(30, 20)

        plus_plus_button.pressed.connect(lambda: self.on_plus_plus_pressed(row))
        plus_plus_button.released.connect(self.on_plus_plus_released)
        minus_minus_button.pressed.connect(lambda: self.on_minus_minus_pressed(row))
        minus_minus_button.released.connect(self.on_minus_minus_released)

        layout.addWidget(minus_minus_button)
        layout.addWidget(plus_plus_button)

        return widget

    def on_plus_pressed(self, row):
        self.handle_button_press('plus', row, self.delta_plus, self.start_continuous_adjustment_plus)

    def on_minus_pressed(self, row):
        self.handle_button_press('minus', row, self.delta_minus, self.start_continuous_adjustment_minus)

    def on_plus_plus_pressed(self, row):
        self.handle_button_press('plus_plus', row, self.delta_plus_plus, self.start_continuous_adjustment_plus_plus)

    def on_minus_minus_pressed(self, row):
        self.handle_button_press('minus_minus', row, self.delta_minus_minus, self.start_continuous_adjustment_minus_minus)

    def handle_button_press(self, button_type, row, initial_delta, continuous_function):
        current_time = QDateTime.currentMSecsSinceEpoch()
        
        # Always stop any ongoing adjustments
        self.stop_adjustment()
        
        # Set the new current button and last press time
        self.current_button = button_type
        self.last_press_time = current_time
        
        # Perform initial adjustment
        self.adjust_angle(row, initial_delta)
        
        # Set up continuous adjustment after delay
        self.initial_delay_timer.timeout.connect(lambda: continuous_function(row))
        self.initial_delay_timer.start()

    def stop_adjustment(self):
        self.initial_delay_timer.stop()
        self.adjustment_timer.stop()
        self.current_adjustment = None
        self.current_button = None
        self.last_press_time = None
        
        # Disconnect only if there are connections
        if self.initial_delay_timer.receivers(self.initial_delay_timer.timeout) > 0:
            self.initial_delay_timer.timeout.disconnect()
        if self.adjustment_timer.receivers(self.adjustment_timer.timeout) > 0:
            self.adjustment_timer.timeout.disconnect()

    def on_plus_released(self):
        self.stop_adjustment()

    def on_minus_released(self):
        self.stop_adjustment()

    def on_plus_plus_released(self):
        self.stop_adjustment()

    def on_minus_minus_released(self):
        self.stop_adjustment()

    def start_continuous_adjustment_plus(self, row):
        self.stop_adjustment()  # Ensure previous adjustments are stopped
        self.current_adjustment = lambda: self.adjust_angle(row, self.delta_continuous_plus)
        self.adjustment_timer.timeout.connect(self.current_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_minus(self, row):
        self.stop_adjustment()  # Ensure previous adjustments are stopped
        self.current_adjustment = lambda: self.adjust_angle(row, self.delta_continuous_minus)
        self.adjustment_timer.timeout.connect(self.current_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_plus_plus(self, row):
        self.stop_adjustment()  # Ensure previous adjustments are stopped
        self.current_adjustment = lambda: self.adjust_angle(row, self.delta_fast_continuous_plus)
        self.adjustment_timer.timeout.connect(self.current_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_minus_minus(self, row):
        self.stop_adjustment()  # Ensure previous adjustments are stopped
        self.current_adjustment = lambda: self.adjust_angle(row, self.delta_fast_continuous_minus)
        self.adjustment_timer.timeout.connect(self.current_adjustment)
        self.adjustment_timer.start()

    def calculate_angle(self, strand):
        dx = strand.end.x() - strand.start.x()
        dy = strand.end.y() - strand.start.y()
        
        if dx == 0:
            return 90 if dy > 0 else -90 if dy < 0 else 0
        
        angle = degrees(atan2(dy, dx))
        
        if angle > 180:
            angle -= 360
        elif angle <= -180:
            angle += 360
        
        return angle

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
            elif item.column() in [4, 5]:  # End X or End Y
                row = item.row()
                strand = self.group_data['strands'][row]
                try:
                    value = float(item.text()) if item.text() else None
                    coordinate = 'x' if item.column() == 4 else 'y'
                    if value is not None:
                        self.update_strand_end(strand, coordinate, value)
                    self.update_table_row(row)
                    self.update_linked_strands(strand)
                except ValueError:
                    self.update_table_row(row)
        finally:
            self.updating = False

    def update_linked_strands(self, source_strand):
        if source_strand.layer_name in self.linked_strands:
            source_angle = self.calculate_angle(source_strand)
            x_strands = []
            x_plus_180_strands = []

            for linked_strand in self.linked_strands.values():
                row = self.group_data['strands'].index(linked_strand)
                x_checkbox = self.table.cellWidget(row, 6)
                x_plus_180_checkbox = self.table.cellWidget(row, 7)

                if x_checkbox and x_checkbox.isChecked():
                    x_strands.append(linked_strand)
                elif x_plus_180_checkbox and x_plus_180_checkbox.isChecked():
                    x_plus_180_strands.append(linked_strand)

            for strand in x_strands:
                self.update_strand_angle(strand, source_angle, update_linked=False)

            opposite_angle = (source_angle + 180) % 360
            if opposite_angle > 180:
                opposite_angle -= 360
            for strand in x_plus_180_strands:
                self.update_strand_angle(strand, opposite_angle, update_linked=False)

    def on_checkbox_changed(self, row, checkbox, state):
        if self.updating:
            return

        self.updating = True
        try:
            strand = self.group_data['strands'][row]
            checkbox_type = checkbox.objectName()
            
            if state == Qt.Checked:
                other_checkbox_name = "180+x" if checkbox_type == "x" else "x"
                other_checkbox = self.table.cellWidget(row, 7 if other_checkbox_name == "180+x" else 6)
                if other_checkbox:
                    other_checkbox.setChecked(False)

                self.update_strand_links(strand, checkbox_type)
                self.update_linked_strands(strand)
            else:
                self.remove_strand_link(strand)
                if self.linked_strands:
                    self.update_linked_strands(next(iter(self.linked_strands.values())))
        finally:
            self.updating = False

    def update_strand_angle(self, strand, new_angle, update_linked=False):
        while new_angle > 180:
            new_angle -= 360
        while new_angle <= -180:
            new_angle += 360
        
        dx = strand.end.x() - strand.start.x()  # Fixed: Added missing parenthesis and subtraction
        dy = strand.end.y() - strand.start.y()
        length = (dx**2 + dy**2)**0.5
        
        new_dx = length * cos(radians(new_angle))
        new_dy = length * sin(radians(new_angle))
        
        strand.end.setX(strand.start.x() + new_dx)
        strand.end.setY(strand.start.y() + new_dy)
        
        strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()

        row = self.group_data['strands'].index(strand)
        self.update_table_row(row)

        self.angle_changed.emit(strand.layer_name, new_angle)
        
        if update_linked:
            self.update_linked_strands(strand)

        self.canvas.update()

    def update_strand_end(self, strand, coordinate, value):
        if coordinate == 'x':
            strand.end.setX(value)
        else:
            strand.end.setY(value)
        
        strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()

    def update_table_row(self, row):
        strand = self.group_data['strands'][row]
        angle = self.calculate_angle(strand)
        end_x = strand.end.x()
        end_y = strand.end.y()

        angle_item = self.table.item(row, 1)
        if angle_item is None:
            angle_item = QTableWidgetItem()
            self.table.setItem(row, 1, angle_item)
        angle_item.setText(f"{angle:.2f}")

        end_x_item = self.table.item(row, 4)
        if end_x_item is None:
            end_x_item = QTableWidgetItem()
            self.table.setItem(row, 4, end_x_item)
        end_x_item.setText(f"{end_x:.2f}")

        end_y_item = self.table.item(row, 5)
        if end_y_item is None:
            end_y_item = QTableWidgetItem()
            self.table.setItem(row, 5, end_y_item)
        end_y_item.setText(f"{end_y:.2f}")

    def update_strand_links(self, strand, checkbox_type):
        self.linked_strands = {k: v for k, v in self.linked_strands.items() if v != strand}
        self.linked_strands[strand.layer_name] = strand

        for other_row, other_strand in enumerate(self.group_data['strands']):
            if other_strand != strand:
                x_checkbox = self.table.cellWidget(other_row, 6)
                x_plus_180_checkbox = self.table.cellWidget(other_row, 7)
                if (x_checkbox and x_checkbox.isChecked()) or (x_plus_180_checkbox and x_plus_180_checkbox.isChecked()):
                    self.linked_strands[other_strand.layer_name] = other_strand

    def remove_strand_link(self, strand):
        self.linked_strands = {k: v for k, v in self.linked_strands.items() if v != strand}
        
    def adjust_angle(self, row, delta):
        strand = self.group_data['strands'][row]
        current_angle = self.calculate_angle(strand)
        new_angle = current_angle + delta
        self.update_strand_angle(strand, new_angle, update_linked=True)

    def accept(self):
        self.canvas.update()
        super().accept()